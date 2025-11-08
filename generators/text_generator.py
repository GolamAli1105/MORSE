# generators/text_generator.py
"""
Advanced Text Generator for Content Creation
Uses ContentTextGenerator for professional content creation
"""

import torch
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available")


class TextGenerator:
    """
    Advanced text generation for content creators
    
    Wrapper around ContentTextGenerator for backward compatibility
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        
        # Use Phi-3-mini (lightweight, fast, compatible)
        self.model_id = model_config.get(
            "model_id",
            "microsoft/Phi-3-mini-4k-instruct"
        )
        
        if torch.cuda.is_available():
            self.device = model_config.get("device", "cuda")
            self.torch_dtype = torch.float16
        else:
            self.device = "cpu"
            self.torch_dtype = torch.float32
        
        self.tokenizer = None
        self.model = None
        self.is_loaded = False
        
        self.logger.info(f"✅ Text Generator initialized")
    
    def load_model(self):
        """Load the language model"""
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers not available")
        
        if self.is_loaded:
            return
        
        try:
            self.logger.info(f"📥 Loading {self.model_id}...")
            
            # Get HuggingFace token from environment
            import os
            hf_token = os.getenv("HUGGINGFACE_TOKEN")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, token=hf_token)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype=self.torch_dtype,
                token=hf_token
            )
            
            # Move model to device
            self.model = self.model.to(self.device)
            
            self.is_loaded = True
            self.logger.info(f"✅ Text model loaded")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load model: {e}")
            raise
    
    async def generate(
        self,
        prompt: str,
        style: str = "default",
        content_type: str = "general",
        language: str = "english",
        max_length: int = 500,
        temperature: float = 0.7,
        top_p: float = 0.9,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate text from prompt with content creation templates
        
        Args:
            prompt: Content topic/description
            style: Style (kept for compatibility)
            content_type: Type of content (instagram_caption, youtube_script, etc.)
            language: Output language (english, hindi, hinglish)
            max_length: Maximum tokens
            temperature: Creativity level
            top_p: Nucleus sampling
            seed: Random seed
        """
        
        if not self.is_loaded:
            self.load_model()
        
        try:
            # Build content-specific prompt
            enhanced_prompt = self._build_content_prompt(prompt, content_type, language)
            
            inputs = self.tokenizer(
                enhanced_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=1024
            ).to(self.device)
            
            if seed is not None:
                torch.manual_seed(seed)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.1
                )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only generated content
            generated_text = self._extract_content(generated_text, enhanced_prompt)
            
            return {
                "text": generated_text,
                "prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "style": style,
                "parameters": {
                    "max_length": max_length,
                    "temperature": temperature,
                    "top_p": top_p,
                    "seed": seed
                },
                "model_used": self.model_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Text generation failed: {e}")
            raise
    
    def _build_content_prompt(self, prompt: str, content_type: str, language: str) -> str:
        """Build content-specific prompt with templates"""
        
        # Language instructions
        lang_map = {
            "english": "Write in clear, professional English.",
            "hindi": "हिंदी में लिखें।",
            "hinglish": "Write in Hinglish (mix of Hindi and English)."
        }
        lang_inst = lang_map.get(language, lang_map["english"])
        
        # Content templates
        templates = {
            "instagram_caption": f"""[INST] You are a social media expert. {lang_inst}

Write an engaging Instagram caption for: {prompt}

Include:
- Attention-grabbing first line
- Storytelling or value
- Call-to-action
- Relevant hashtags (10-15)

Caption: [/INST]""",
            
            "youtube_script": f"""[INST] You are a YouTube scriptwriter. {lang_inst}

Create a YouTube video script for: {prompt}

Include:
- Catchy hook
- Main content
- Call-to-action

Script: [/INST]""",
            
            "youtube_description": f"""[INST] You are a YouTube SEO expert. {lang_inst}

Write a YouTube description for: {prompt}

Include:
- Summary
- Keywords
- Hashtags

Description: [/INST]""",
            
            "general": f"""[INST] You are a professional content creator. {lang_inst}

Create engaging content about: {prompt}

Make it creative and informative.

Content: [/INST]"""
        }
        
        return templates.get(content_type, templates["general"])
    
    def _extract_content(self, full_text: str, prompt: str) -> str:
        """Extract generated content from full output"""
        if "[/INST]" in full_text:
            parts = full_text.split("[/INST]")
            if len(parts) > 1:
                return parts[1].strip()
        return full_text.strip()
    
    def _enhance_text_prompt(self, prompt: str, style: str) -> str:
        """Legacy method for compatibility"""
        return self._build_content_prompt(prompt, "general", "english")
    
    def unload_model(self):
        """Unload model to free memory"""
        if self.model is not None:
            del self.model
            del self.tokenizer
            self.model = None
            self.tokenizer = None
            self.is_loaded = False
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
