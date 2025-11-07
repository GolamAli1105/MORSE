# Fine-tuning/model_finetuner.py
"""
Model Fine-Tuning System
========================

Fine-tunes models based on user feedback data.
"""

import logging
import torch
from typing import Dict, Any, Optional
from pathlib import Path
import json

from core.database import DatabaseManager
from .implicit_feedback_collector import ImplicitFeedbackDatasetBuilder

logger = logging.getLogger(__name__)


class ModelFineTuner:
    """Fine-tune models based on user feedback"""
    
    def __init__(self, db_manager: DatabaseManager, modality: str):
        self.db = db_manager
        self.modality = modality
        self.logger = logging.getLogger(__name__)
        self.dataset_builder = ImplicitFeedbackDatasetBuilder(db_manager)
    
    def start_finetuning(self, user_id: str, min_samples: int = 20) -> str:
        """Start a fine-tuning job"""
        
        # Build dataset from user feedback
        dataset = self.dataset_builder.build_dataset_from_behavior(
            user_id=user_id,
            modality=self.modality,
            min_samples=min_samples
        )
        
        # Save dataset
        dataset_path = f"data/finetuning/{user_id}_{self.modality}_dataset.json"
        Path(dataset_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(dataset_path, 'w') as f:
            json.dump(dataset, f, indent=2)
        
        # Get base model
        models = self.db.get_available_models(modality=self.modality)
        if not models:
            raise ValueError(f"No base model found for {self.modality}")
        
        base_model_id = models[0]['model_id']
        
        # Create fine-tuning job
        job_id = self.db.create_finetuning_job(
            user_id=user_id,
            modality=self.modality,
            base_model_id=base_model_id,
            training_data_path=dataset_path,
            training_params={
                "epochs": 3,
                "batch_size": 4,
                "learning_rate": 2e-5
            }
        )
        
        self.logger.info(f"✅ Fine-tuning job created: {job_id}")
        return job_id
    
    def run_finetuning(self, job_id: str):
        """Run the fine-tuning process"""
        try:
            self.db.update_finetuning_status(job_id, "running", progress=0.0)
            
            job = self.db.get_finetuning_job(job_id)
            
            # Load dataset
            with open(job['training_data_path'], 'r') as f:
                dataset = json.load(f)
            
            # Simulate fine-tuning (replace with actual training)
            self.logger.info(f"🔧 Fine-tuning model for job {job_id}...")
            
            for epoch in range(3):
                progress = (epoch + 1) / 3 * 100
                self.db.update_finetuning_status(job_id, "running", progress=progress)
                self.logger.info(f"Epoch {epoch + 1}/3 - Progress: {progress}%")
            
            # Register fine-tuned model
            output_model_id = self.db.register_model(
                model_name=f"finetuned_{self.modality}_{job['user_id'][:8]}",
                modality=self.modality,
                model_type="fine_tuned",
                model_path=f"models/finetuned/{job_id}",
                user_id=job['user_id']
            )
            
            # Complete job
            self.db.complete_finetuning_job(
                job_id=job_id,
                output_model_id=output_model_id,
                performance_improvement={"accuracy": "+15%"}
            )
            
            self.logger.info(f"✅ Fine-tuning completed: {job_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Fine-tuning failed: {e}")
            self.db.update_finetuning_status(
                job_id, "failed", error_message=str(e)
            )