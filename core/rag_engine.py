"""
RAG (Retrieval-Augmented Generation) Engine
============================================

Enhances generation with relevant past content.
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np

from core.mongodb_manager import MongoDBManager

logger = logging.getLogger(__name__)


class RAGEngine:
    """
    Retrieval-Augmented Generation Engine
    
    Retrieves relevant past content to enhance new generations
    """
    
    def __init__(self, mongodb_manager: MongoDBManager):
        self.mongo = mongodb_manager
        self.logger = logging.getLogger(__name__)
    
    def enhance_prompt_with_rag(
        self,
        user_id: str,
        modality: str,
        prompt: str,
        style: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhance prompt with relevant past content
        
        Returns:
            Enhanced prompt and reference content
        """
        
        # Retrieve similar high-quality content
        similar_content = self.mongo.retrieve_similar_content(
            user_id=user_id,
            modality=modality,
            prompt=prompt,
            style=style,
            limit=3,
            min_rating=4.0
        )
        
        if not similar_content:
            self.logger.info("No similar content found, using original prompt")
            return {
                "enhanced_prompt": prompt,
                "references": [],
                "rag_used": False
            }
        
        # Build enhanced prompt based on modality
        if modality == "image":
            enhanced_prompt = self._enhance_image_prompt(prompt, similar_content)
        elif modality == "music":
            enhanced_prompt = self._enhance_music_prompt(prompt, similar_content)
        elif modality == "text":
            enhanced_prompt = self._enhance_text_prompt(prompt, similar_content)
        else:
            enhanced_prompt = prompt
        
        self.logger.info(f"✨ Prompt enhanced with {len(similar_content)} references")
        
        return {
            "enhanced_prompt": enhanced_prompt,
            "references": similar_content,
            "rag_used": True,
            "reference_count": len(similar_content)
        }
    
    def _enhance_image_prompt(self, prompt: str, references: List[Dict]) -> str:
        """Enhance image generation prompt with successful past generations"""
        
        # Extract successful elements from past generations
        successful_elements = []
        for ref in references:
            ref_prompt = ref.get('prompt', '')
            rating = ref.get('rating', 0)
            
            if rating >= 4.5:
                # Extract key descriptive words
                successful_elements.append(ref_prompt)
        
        if successful_elements:
            # Add context from successful generations
            context = f"Building on successful past generations with similar themes. "
            enhanced = f"{context}{prompt}"
            return enhanced
        
        return prompt
    
    def _enhance_music_prompt(self, prompt: str, references: List[Dict]) -> str:
        """Enhance music generation prompt with successful past generations"""
        
        # Analyze successful music generations
        successful_styles = []
        for ref in references:
            style = ref.get('style', '')
            rating = ref.get('rating', 0)
            
            if rating >= 4.0 and style:
                successful_styles.append(style)
        
        if successful_styles:
            # Incorporate successful style elements
            most_common_style = max(set(successful_styles), key=successful_styles.count)
            enhanced = f"{prompt}, incorporating elements from your preferred {most_common_style} style"
            return enhanced
        
        return prompt
    
    def _enhance_text_prompt(self, prompt: str, references: List[Dict]) -> str:
        """Enhance text generation prompt with successful past content"""
        
        # Extract successful writing patterns
        successful_examples = []
        for ref in references:
            if ref.get('rating', 0) >= 4.0:
                content_snippet = ref.get('content', '')[:200]  # First 200 chars
                successful_examples.append(content_snippet)
        
        if successful_examples:
            examples_text = "\n\n".join([f"Example {i+1}: {ex}" for i, ex in enumerate(successful_examples[:2])])
            enhanced = f"{prompt}\n\nReference your previous successful content style:\n{examples_text}"
            return enhanced
        
        return prompt
    
    def get_content_insights(
        self,
        user_id: str,
        modality: str
    ) -> Dict[str, Any]:
        """Get insights from user's content history"""
        
        best_content = self.mongo.get_user_best_content(
            user_id=user_id,
            modality=modality,
            limit=20
        )
        
        if not best_content:
            return {"insights": "No content history available"}
        
        # Analyze patterns
        styles = [c.get('style') for c in best_content if c.get('style')]
        avg_rating = np.mean([c.get('rating', 0) for c in best_content if c.get('rating')])
        
        most_successful_style = max(set(styles), key=styles.count) if styles else "default"
        
        return {
            "total_high_quality_content": len(best_content),
            "average_rating": round(avg_rating, 2),
            "most_successful_style": most_successful_style,
            "style_distribution": {style: styles.count(style) for style in set(styles)}
        }
