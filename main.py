# generators/text_generator.py
"""
Text Generator using Llama or GPT models
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
    """Text generation using language models"""
    
    def __init__(self, model_config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        
        self.model_id = model_config.get(
            "model_id",
            "meta-llama/Llama-2-7b-chat-hf"
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
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype=self.torch_dtype,
                device_map="auto"
            )
            
            self.is_loaded = True
            self.logger.info(f"✅ Text model loaded")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load model: {e}")
            raise
    
    async def generate(
        self,
        prompt: str,
        style: str = "default",
        max_length: int = 500,
        temperature: float = 0.7,
        top_p: float = 0.9,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text from prompt"""
        
        if not self.is_loaded:
            self.load_model()
        
        try:
            enhanced_prompt = self._enhance_text_prompt(prompt, style)
            
            inputs = self.tokenizer(enhanced_prompt, return_tensors="pt").to(self.device)
            
            if seed is not None:
                torch.manual_seed(seed)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_length=max_length,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
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
    
    def _enhance_text_prompt(self, prompt: str, style: str) -> str:
        """Enhance prompt based on style"""
        style_templates = {
            "creative": f"Write a creative and imaginative response: {prompt}",
            "professional": f"Write a professional and formal response: {prompt}",
            "casual": f"Write a casual and friendly response: {prompt}",
            "technical": f"Write a detailed technical response: {prompt}",
            "default": prompt
        }
        return style_templates.get(style, prompt)
    
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
