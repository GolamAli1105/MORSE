# src/ai_engine/finetuning/implicit_feedback_collector.py

"""
Implicit Feedback Collection System
===================================

Learns from user behavior instead of explicit ratings:
- Regeneration requests = User didn't like it
- Saved/Downloaded content = User liked it
- Edit/Modification requests = User wants changes
- Time spent viewing = Engagement indicator
- Repeated similar prompts = User preference pattern
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from core.database import DatabaseManager

logger = logging.getLogger(__name__)


class ImplicitFeedbackCollector:
    """
    Collect implicit feedback from user actions
    
    Feedback signals:
    1. POSITIVE (User liked it):
       - Downloaded/Saved the output
       - Used it in their project
       - Didn't regenerate
       - Spent time viewing it
    
    2. NEGATIVE (User didn't like it):
       - Clicked "Regenerate"
       - Closed immediately
       - Generated again with modified prompt
    
    3. CORRECTIONS (User wants changes):
       - Modified the prompt and regenerated
       - Provided specific change requests
       - Used "Edit" or "Refine" features
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def track_generation(
        self,
        user_id: str,
        session_id: str,
        modality: str,
        prompt: str,
        content: str,
        style: str,
        model_used: str,
        generation_params: Dict[str, Any]
    ) -> str:
        """
        Track a generation event
        
        Returns:
            Generation ID for tracking subsequent actions
        """
        generation_id = str(uuid.uuid4())
        
        # Save to database with initial neutral feedback
        message_id = self.db.save_chat_message(
            session_id=session_id,
            user_id=user_id,
            modality=modality,
            role="assistant",
            content=content,
            prompt=prompt,
            style=style,
            generation_params=generation_params,
            model_used=model_used
        )
        
        # Initialize implicit feedback tracking
        self._init_feedback_tracking(message_id, generation_id)
        
        return generation_id
    
    def track_positive_action(
        self,
        generation_id: str,
        action_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track positive user actions
        
        Action types:
        - 'download': User downloaded the content
        - 'save': User saved to their collection
        - 'share': User shared the content
        - 'use': User used it in their project
        - 'view_extended': User spent significant time viewing
        """
        self.logger.info(f"✅ Positive action: {action_type} for {generation_id}")
        
        # Calculate implicit rating based on action
        action_scores = {
            'download': 5,
            'save': 5,
            'share': 5,
            'use': 5,
            'view_extended': 4,
            'no_regenerate': 4
        }
        
        implicit_rating = action_scores.get(action_type, 4)
        
        # Save as feedback
        self.db.save_feedback(
            message_id=generation_id,
            user_id=self._get_user_from_generation(generation_id),
            rating=implicit_rating,
            comment=f"Implicit: {action_type}",
            feedback_type="implicit_positive"
        )
    
    def track_negative_action(
        self,
        generation_id: str,
        action_type: str,
        reason: Optional[str] = None
    ):
        """
        Track negative user actions
        
        Action types:
        - 'regenerate': User clicked regenerate
        - 'close_immediate': User closed within 5 seconds
        - 'delete': User deleted the output
        - 'skip': User skipped to next generation
        """
        self.logger.info(f"Negative action: {action_type} for {generation_id}")
        
        action_scores = {
            'regenerate': 2,
            'close_immediate': 1,
            'delete': 1,
            'skip': 2
        }
        
        implicit_rating = action_scores.get(action_type, 2)
        
        # Save as feedback with reason
        self.db.save_feedback(
            message_id=generation_id,
            user_id=self._get_user_from_generation(generation_id),
            rating=implicit_rating,
            comment=f"Implicit: {action_type}" + (f" - {reason}" if reason else ""),
            feedback_type="implicit_negative"
        )
    
    def track_correction(
        self,
        original_generation_id: str,
        new_prompt: str,
        change_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track when user modifies prompt and regenerates
        
        This is the most valuable feedback - shows exactly what user wants changed
        """
        self.logger.info(f"🔄 Correction tracked for {original_generation_id}")
        
        # Get original generation
        original = self._get_generation_details(original_generation_id)
        
        if not original:
            return {}
        
        # Analyze what changed
        changes = self._analyze_prompt_changes(
            original['prompt'],
            new_prompt,
            change_description
        )
        
        # Save as correction feedback
        self.db.save_feedback(
            message_id=original_generation_id,
            user_id=original['user_id'],
            rating=3,  # Neutral - user wants changes
            comment=f"Correction: {changes['description']}",
            feedback_type="correction"
        )
        
        return {
            'original_prompt': original['prompt'],
            'new_prompt': new_prompt,
            'changes': changes,
            'original_style': original.get('style'),
            'modality': original.get('modality')
        }
    
    def track_viewing_time(
        self,
        generation_id: str,
        viewing_seconds: int
    ):
        """
        Track how long user viewed the content
        
        Longer viewing time = more interest
        """
        # Classify viewing time
        if viewing_seconds < 3:
            # Very short - likely didn't like it
            self.track_negative_action(generation_id, 'close_immediate')
        elif viewing_seconds > 30:
            # Extended viewing - likely interested
            self.track_positive_action(generation_id, 'view_extended')
        # 3-30 seconds = neutral, no action needed
    
    def track_regeneration_request(
        self,
        generation_id: str,
        reason: Optional[str] = None,
        keep_prompt: bool = True
    ):
        """
        Track when user clicks "Regenerate"
        
        Args:
            generation_id: Original generation ID
            reason: Optional reason for regeneration
            keep_prompt: Whether user kept the same prompt
        """
        if keep_prompt:
            # Same prompt = wants different variation
            self.track_negative_action(
                generation_id,
                'regenerate',
                reason or "wants_variation"
            )
        else:
            # Different prompt = correction
            # Will be tracked separately in track_correction
            pass
    
    def _analyze_prompt_changes(
        self,
        original_prompt: str,
        new_prompt: str,
        change_description: Optional[str]
    ) -> Dict[str, Any]:
        """
        Analyze what changed between prompts
        
        This helps understand user preferences
        """
        original_lower = original_prompt.lower()
        new_lower = new_prompt.lower()
        
        changes = {
            'description': change_description or 'User modified prompt',
            'additions': [],
            'removals': [],
            'modifications': []
        }
        
        # Find added words
        original_words = set(original_lower.split())
        new_words = set(new_lower.split())
        
        added = new_words - original_words
        removed = original_words - new_words
        
        if added:
            changes['additions'] = list(added)
            changes['description'] += f" | Added: {', '.join(list(added)[:3])}"
        
        if removed:
            changes['removals'] = list(removed)
            changes['description'] += f" | Removed: {', '.join(list(removed)[:3])}"
        
        # Detect common modification patterns
        if 'more' in new_lower and 'more' not in original_lower:
            changes['modifications'].append('wants_more_of_something')
        if 'less' in new_lower and 'less' not in original_lower:
            changes['modifications'].append('wants_less_of_something')
        if 'without' in new_lower or 'no' in new_lower:
            changes['modifications'].append('wants_removal')
        
        return changes
    
    def _init_feedback_tracking(self, message_id: str, generation_id: str):
        """Initialize feedback tracking for a generation"""
        # This would store initial tracking data
        # For now, we'll just log it
        self.logger.debug(f"Initialized tracking for {generation_id}")
    
    def _get_user_from_generation(self, generation_id: str) -> str:
        """Get user ID from generation ID"""
        # This would query the database
        # For now, return a placeholder
        return "user_id"
    
    def _get_generation_details(self, generation_id: str) -> Optional[Dict[str, Any]]:
        """Get generation details from database"""
        # This would query the database
        # For now, return a placeholder
        return {
            'generation_id': generation_id,
            'user_id': 'user_id',
            'prompt': 'original prompt',
            'modality': 'text',
            'style': 'default'
        }


class ImplicitFeedbackDatasetBuilder:
    """
    Build training datasets from implicit feedback
    
    No ratings needed - learns from user behavior
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def build_dataset_from_behavior(
        self,
        user_id: str,
        modality: str,
        min_samples: int = 20
    ) -> Dict[str, Any]:
        """
        Build training dataset from user behavior
        
        Positive examples:
        - Downloaded/saved outputs
        - Outputs user didn't regenerate
        - Outputs with long viewing time
        
        Negative examples:
        - Immediately regenerated outputs
        - Quickly closed outputs
        
        Corrections:
        - Modified prompts that led to better results
        """
        self.logger.info(f"📊 Building dataset from user behavior...")
        
        # Get all user's generations
        chat_history = self.db.get_user_chat_history(user_id, limit=1000)
        
        # Filter by modality
        generations = [msg for msg in chat_history if msg.get('modality') == modality]
        
        # Categorize based on implicit feedback
        positive_examples = []
        negative_examples = []
        correction_examples = []
        
        for gen in generations:
            # Get feedback for this generation
            feedback = self._get_implicit_feedback(gen['message_id'])
            
            if not feedback:
                continue
            
            feedback_type = feedback.get('feedback_type', '')
            
            if 'positive' in feedback_type:
                positive_examples.append({
                    'prompt': gen['prompt'],
                    'content': gen['content'],
                    'style': gen.get('style', 'default'),
                    'action': feedback.get('comment', ''),
                    'weight': 1.5  # Higher weight for explicit positive actions
                })
            
            elif 'negative' in feedback_type:
                negative_examples.append({
                    'prompt': gen['prompt'],
                    'content': gen['content'],
                    'style': gen.get('style', 'default'),
                    'issue': feedback.get('comment', ''),
                    'weight': 0.3  # Low weight - learn what to avoid
                })
            
            elif feedback_type == 'correction':
                # Extract correction from comment
                correction_info = self._parse_correction_comment(feedback.get('comment', ''))
                if correction_info:
                    correction_examples.append({
                        'original_prompt': gen['prompt'],
                        'corrected_prompt': correction_info.get('new_prompt', gen['prompt']),
                        'changes': correction_info.get('changes', {}),
                        'style': gen.get('style', 'default'),
                        'weight': 2.0  # Highest weight - direct user guidance
                    })
        
        total_samples = len(positive_examples) + len(correction_examples)
        
        if total_samples < min_samples:
            raise ValueError(
                f"Insufficient behavioral data. Need {min_samples}, got {total_samples}. "
                f"Generate more content and interact with it (download, save, regenerate, etc.)"
            )
        
        self.logger.info(f"✅ Dataset built from behavior:")
        self.logger.info(f"   Positive: {len(positive_examples)}")
        self.logger.info(f"   Corrections: {len(correction_examples)}")
        self.logger.info(f"   Negative: {len(negative_examples)}")
        
        return {
            'positive': positive_examples,
            'corrections': correction_examples,
            'negative': negative_examples,
            'total_samples': total_samples
        }
    
    def _get_implicit_feedback(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get implicit feedback for a message"""
        # This would query the feedback table
        # For now, return None
        return None
    
    def _parse_correction_comment(self, comment: str) -> Optional[Dict[str, Any]]:
        """Parse correction information from comment"""
        if not comment or 'Correction:' not in comment:
            return None
        
        # Extract correction details
        parts = comment.split('Correction:')
        if len(parts) > 1:
            return {
                'description': parts[1].strip(),
                'changes': {}
            }
        
        return None
