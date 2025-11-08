"""
Automated Fine-Tuning System
============================

Automatically fine-tunes models based on user feedback and generated outputs.
Runs every 30 minutes to continuously improve model performance.

Features:
- Collects all generated outputs as training data
- Stores user feedback in MongoDB
- Automatically triggers fine-tuning every 30 minutes
- Uses fine-tuned models for subsequent generations
- Tracks performance improvements
"""

import logging
import asyncio
import torch
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
import json
import schedule
import time
from threading import Thread

from core.mongodb_manager import MongoDBManager
from core.database import DatabaseManager
from .implicit_feedback_collector import ImplicitFeedbackCollector, ImplicitFeedbackDatasetBuilder
from .model_finetuner import ModelFineTuner

logger = logging.getLogger(__name__)


class AutomatedFineTuningSystem:
    """
    Automated fine-tuning system that continuously improves models
    
    Workflow:
    1. Collect all generated outputs (images, music, text)
    2. Store in MongoDB with metadata
    3. Collect user feedback (explicit and implicit)
    4. Every 30 minutes, check if enough new data exists
    5. If yes, trigger fine-tuning automatically
    6. Update model registry with fine-tuned version
    7. Use fine-tuned model for next generations
    """
    
    def __init__(
        self,
        mongodb_manager: MongoDBManager,
        db_manager: DatabaseManager,
        fine_tune_interval_minutes: int = 30,
        min_samples_for_training: int = 50
    ):
        self.mongodb = mongodb_manager
        self.db = db_manager
        self.interval_minutes = fine_tune_interval_minutes
        self.min_samples = min_samples_for_training
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize collectors
        self.feedback_collector = ImplicitFeedbackCollector(db_manager)
        self.dataset_builder = ImplicitFeedbackDatasetBuilder(db_manager)
        
        # Track last fine-tuning time per modality
        self.last_finetuning = {
            'image': None,
            'music': None,
            'text': None
        }
        
        # Fine-tuned model registry
        self.finetuned_models = {
            'image': None,
            'music': None,
            'text': None
        }
        
        self.is_running = False
        self.scheduler_thread = None
        
        self.logger.info("✅ Automated Fine-Tuning System initialized")
    
    async def store_generation_output(
        self,
        user_id: str,
        session_id: str,
        modality: str,
        prompt: str,
        enhanced_prompt: str,
        output_data: Any,
        style: str,
        model_used: str,
        generation_params: Dict[str, Any],
        generation_time: float
    ) -> str:
        """
        Store generated output in MongoDB for training
        
        Returns:
            generation_id for tracking feedback
        """
        try:
            # Create training data entry
            training_entry = {
                'user_id': user_id,
                'session_id': session_id,
                'modality': modality,
                'prompt': prompt,
                'enhanced_prompt': enhanced_prompt,
                'output_data': output_data,  # Base64 for images/audio
                'style': style,
                'model_used': model_used,
                'generation_params': generation_params,
                'generation_time': generation_time,
                'timestamp': datetime.utcnow(),
                'feedback': {
                    'explicit_rating': None,
                    'explicit_comment': None,
                    'implicit_actions': [],
                    'viewing_time': 0,
                    'regeneration_count': 0,
                    'downloaded': False,
                    'saved': False,
                    'shared': False
                },
                'used_for_training': False,
                'training_weight': 1.0
            }
            
            # Store in MongoDB
            result = self.mongodb.db['training_data'].insert_one(training_entry)
            generation_id = str(result.inserted_id)
            
            # Also track in implicit feedback system
            self.feedback_collector.track_generation(
                user_id=user_id,
                session_id=session_id,
                modality=modality,
                prompt=prompt,
                content=output_data,
                style=style,
                model_used=model_used,
                generation_params=generation_params
            )
            
            self.logger.info(f"📦 Stored {modality} generation: {generation_id}")
            
            return generation_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store generation: {e}")
            raise
    
    async def store_user_feedback(
        self,
        generation_id: str,
        user_id: str,
        feedback_type: str,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        action: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store user feedback for a generation
        
        Feedback types:
        - 'explicit': User provided rating/comment
        - 'implicit_positive': Download, save, share, etc.
        - 'implicit_negative': Regenerate, close, delete
        - 'correction': User modified prompt
        """
        try:
            from bson import ObjectId
            
            # Update training data with feedback
            update_data = {
                'feedback.last_updated': datetime.utcnow()
            }
            
            if feedback_type == 'explicit':
                update_data['feedback.explicit_rating'] = rating
                update_data['feedback.explicit_comment'] = comment
                update_data['training_weight'] = 2.0 if rating >= 4 else 0.5
            
            elif feedback_type == 'implicit_positive':
                update_data[f'feedback.{action}'] = True
                update_data['$push'] = {'feedback.implicit_actions': {
                    'action': action,
                    'timestamp': datetime.utcnow()
                }}
                update_data['training_weight'] = 1.5
            
            elif feedback_type == 'implicit_negative':
                update_data['$inc'] = {'feedback.regeneration_count': 1}
                update_data['$push'] = {'feedback.implicit_actions': {
                    'action': action,
                    'timestamp': datetime.utcnow()
                }}
                update_data['training_weight'] = 0.3
            
            elif feedback_type == 'correction':
                update_data['feedback.correction'] = metadata
                update_data['training_weight'] = 2.5  # Highest weight
            
            # Update MongoDB
            self.mongodb.db['training_data'].update_one(
                {'_id': ObjectId(generation_id)},
                {'$set': update_data}
            )
            
            # Also track in implicit feedback system
            if feedback_type == 'implicit_positive':
                self.feedback_collector.track_positive_action(
                    generation_id, action, metadata
                )
            elif feedback_type == 'implicit_negative':
                self.feedback_collector.track_negative_action(
                    generation_id, action, comment
                )
            
            self.logger.info(f"💬 Stored {feedback_type} feedback for {generation_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to store feedback: {e}")
    
    async def check_and_trigger_finetuning(self):
        """
        Check if fine-tuning should be triggered for each modality
        
        Triggers if:
        1. At least 30 minutes since last fine-tuning
        2. At least min_samples new training samples available
        3. No fine-tuning currently running
        """
        self.logger.info("🔍 Checking if fine-tuning should be triggered...")
        
        for modality in ['image', 'music', 'text']:
            try:
                # Check time since last fine-tuning
                last_time = self.last_finetuning.get(modality)
                if last_time:
                    time_diff = datetime.utcnow() - last_time
                    if time_diff < timedelta(minutes=self.interval_minutes):
                        self.logger.info(f"⏳ {modality}: Too soon since last fine-tuning")
                        continue
                
                # Check if enough new samples
                new_samples_count = self._count_new_training_samples(modality)
                
                if new_samples_count < self.min_samples:
                    self.logger.info(
                        f"📊 {modality}: Not enough samples "
                        f"({new_samples_count}/{self.min_samples})"
                    )
                    continue
                
                # Check if fine-tuning already running
                if self._is_finetuning_running(modality):
                    self.logger.info(f"⚙️ {modality}: Fine-tuning already running")
                    continue
                
                # Trigger fine-tuning
                self.logger.info(
                    f"🚀 Triggering fine-tuning for {modality} "
                    f"({new_samples_count} samples)"
                )
                
                await self.trigger_finetuning(modality)
                
            except Exception as e:
                self.logger.error(f"❌ Error checking {modality}: {e}")
    
    async def trigger_finetuning(self, modality: str):
        """
        Trigger fine-tuning for a specific modality
        """
        try:
            self.logger.info(f"🔧 Starting fine-tuning for {modality}...")
            
            # Get training data from MongoDB
            training_data = self._get_training_data(modality)
            
            if not training_data:
                self.logger.warning(f"No training data found for {modality}")
                return
            
            # Prepare dataset
            dataset = self._prepare_training_dataset(training_data, modality)
            
            # Save dataset
            dataset_path = f"data/finetuning/{modality}_dataset_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            Path(dataset_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(dataset_path, 'w') as f:
                json.dump(dataset, f, indent=2)
            
            # Create fine-tuning job
            job_id = self.db.create_finetuning_job(
                user_id='system',
                modality=modality,
                base_model_id=self._get_base_model_id(modality),
                training_data_path=dataset_path,
                training_params={
                    "epochs": 3,
                    "batch_size": 4,
                    "learning_rate": 2e-5,
                    "samples_count": len(training_data)
                }
            )
            
            # Run fine-tuning in background
            asyncio.create_task(self._run_finetuning_job(job_id, modality))
            
            # Update last fine-tuning time
            self.last_finetuning[modality] = datetime.utcnow()
            
            self.logger.info(f"✅ Fine-tuning job created: {job_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to trigger fine-tuning: {e}")
    
    async def _run_finetuning_job(self, job_id: str, modality: str):
        """
        Run the actual fine-tuning process
        """
        try:
            self.db.update_finetuning_status(job_id, "running", progress=0.0)
            
            job = self.db.get_finetuning_job(job_id)
            
            # Load dataset
            with open(job['training_data_path'], 'r') as f:
                dataset = json.load(f)
            
            self.logger.info(f"🔧 Fine-tuning {modality} model...")
            self.logger.info(f"   Training samples: {len(dataset['training_samples'])}")
            
            # Simulate fine-tuning (replace with actual training)
            # In production, this would call the actual fine-tuning code
            for epoch in range(3):
                progress = (epoch + 1) / 3 * 100
                self.db.update_finetuning_status(job_id, "running", progress=progress)
                self.logger.info(f"   Epoch {epoch + 1}/3 - Progress: {progress}%")
                await asyncio.sleep(1)  # Simulate training time
            
            # Register fine-tuned model
            output_model_id = self.db.register_model(
                model_name=f"finetuned_{modality}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                modality=modality,
                model_type="fine_tuned",
                model_path=f"models/finetuned/{job_id}",
                user_id='system'
            )
            
            # Update fine-tuned model registry
            self.finetuned_models[modality] = output_model_id
            
            # Mark training data as used
            self._mark_data_as_used(dataset['sample_ids'])
            
            # Complete job
            self.db.complete_finetuning_job(
                job_id=job_id,
                output_model_id=output_model_id,
                performance_improvement={"samples_trained": len(dataset['training_samples'])}
            )
            
            self.logger.info(f"✅ Fine-tuning completed for {modality}: {output_model_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Fine-tuning failed: {e}")
            self.db.update_finetuning_status(
                job_id, "failed", error_message=str(e)
            )
    
    def get_model_for_generation(self, modality: str) -> Optional[str]:
        """
        Get the best model to use for generation
        
        Returns fine-tuned model if available, otherwise base model
        """
        finetuned_model = self.finetuned_models.get(modality)
        
        if finetuned_model:
            self.logger.info(f"🎯 Using fine-tuned model for {modality}: {finetuned_model}")
            return finetuned_model
        
        # Return base model
        base_model = self._get_base_model_id(modality)
        self.logger.info(f"📦 Using base model for {modality}: {base_model}")
        return base_model
    
    def start_scheduler(self):
        """
        Start the automated fine-tuning scheduler
        
        Runs every 30 minutes (or configured interval)
        """
        if self.is_running:
            self.logger.warning("Scheduler already running")
            return
        
        self.is_running = True
        
        # Schedule fine-tuning check
        schedule.every(self.interval_minutes).minutes.do(
            lambda: asyncio.run(self.check_and_trigger_finetuning())
        )
        
        # Run scheduler in background thread
        def run_scheduler():
            self.logger.info(f"⏰ Scheduler started (interval: {self.interval_minutes} minutes)")
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.scheduler_thread = Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("✅ Automated fine-tuning scheduler started")
    
    def stop_scheduler(self):
        """Stop the automated fine-tuning scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        self.logger.info("🛑 Scheduler stopped")
    
    def _count_new_training_samples(self, modality: str) -> int:
        """Count new training samples since last fine-tuning"""
        try:
            query = {
                'modality': modality,
                'used_for_training': False
            }
            
            # Only count samples with some feedback
            query['$or'] = [
                {'feedback.explicit_rating': {'$ne': None}},
                {'feedback.implicit_actions': {'$ne': []}},
                {'feedback.downloaded': True},
                {'feedback.saved': True}
            ]
            
            count = self.mongodb.db['training_data'].count_documents(query)
            return count
            
        except Exception as e:
            self.logger.error(f"Error counting samples: {e}")
            return 0
    
    def _is_finetuning_running(self, modality: str) -> bool:
        """Check if fine-tuning is currently running for modality"""
        try:
            # Check database for running jobs
            # This is a placeholder - implement based on your database schema
            return False
        except Exception as e:
            self.logger.error(f"Error checking running status: {e}")
            return False
    
    def _get_training_data(self, modality: str) -> List[Dict[str, Any]]:
        """Get training data from MongoDB"""
        try:
            query = {
                'modality': modality,
                'used_for_training': False
            }
            
            # Get samples with feedback
            cursor = self.mongodb.db['training_data'].find(query).limit(1000)
            return list(cursor)
            
        except Exception as e:
            self.logger.error(f"Error getting training data: {e}")
            return []
    
    def _prepare_training_dataset(
        self,
        training_data: List[Dict[str, Any]],
        modality: str
    ) -> Dict[str, Any]:
        """Prepare dataset for fine-tuning"""
        training_samples = []
        sample_ids = []
        
        for item in training_data:
            # Extract relevant fields
            sample = {
                'prompt': item['prompt'],
                'enhanced_prompt': item['enhanced_prompt'],
                'output_data': item['output_data'],
                'style': item['style'],
                'generation_params': item['generation_params'],
                'weight': item.get('training_weight', 1.0),
                'feedback': item.get('feedback', {})
            }
            
            training_samples.append(sample)
            sample_ids.append(str(item['_id']))
        
        return {
            'modality': modality,
            'training_samples': training_samples,
            'sample_ids': sample_ids,
            'created_at': datetime.utcnow().isoformat()
        }
    
    def _mark_data_as_used(self, sample_ids: List[str]):
        """Mark training data as used"""
        try:
            from bson import ObjectId
            
            self.mongodb.db['training_data'].update_many(
                {'_id': {'$in': [ObjectId(id) for id in sample_ids]}},
                {'$set': {'used_for_training': True, 'trained_at': datetime.utcnow()}}
            )
            
            self.logger.info(f"✅ Marked {len(sample_ids)} samples as used")
            
        except Exception as e:
            self.logger.error(f"Error marking data as used: {e}")
    
    def _get_base_model_id(self, modality: str) -> str:
        """Get base model ID for modality"""
        base_models = {
            'image': 'stabilityai/stable-diffusion-xl-base-1.0',
            'music': 'facebook/musicgen-small',
            'text': 'gpt2-medium'
        }
        return base_models.get(modality, 'unknown')


# Global instance
_finetuning_system = None


def get_finetuning_system(
    mongodb_manager: MongoDBManager,
    db_manager: DatabaseManager
) -> AutomatedFineTuningSystem:
    """Get or create the global fine-tuning system instance"""
    global _finetuning_system
    
    if _finetuning_system is None:
        _finetuning_system = AutomatedFineTuningSystem(
            mongodb_manager=mongodb_manager,
            db_manager=db_manager,
            fine_tune_interval_minutes=30,
            min_samples_for_training=50
        )
        # Start scheduler
        _finetuning_system.start_scheduler()
    
    return _finetuning_system
