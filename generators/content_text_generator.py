"""
Advanced Content Creation Text Generator
=========================================

Specialized text generation for content creators:
- Directors, Producers, YouTubers
- Script writing, video descriptions, social media
- Regional language support (Hindi, English, Hinglish)
- Multiple content types and styles
- Fine-tuning support

Model: mistralai/Mistral-7B-Instruct-v0.2 (Best open-source for content)
"""

import torch
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import re

logger = logging.getLogger(__name__)

try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("Transformers not available")


class ContentTextGenerator:
    """
    Advanced text generator for content creators
    
    Features:
    - Multiple content types (scripts, descriptions, captions)
    - Regional language support (English, Hindi, Hinglish)
    - Creator-specific templates (YouTube, Instagram, TikTok)
    - SEO-optimized content
    - Fast generation with quality
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        
        # Use Mistral-7B-Instruct (best open-source for content creation)
        self.model_id = model_config.get(
            "model_id",
            "mistralai/Mistral-7B-Instruct-v0.2"  # Excellent for creative content
        )
        
        # Device setup
        if torch.cuda.is_available():
            self.device = model_config.get("device", "cuda")
            self.torch_dtype = torch.float16  # FP16 for speed
            self.logger.info("🎮 Using GPU for text generation")
        else:
            self.device = "cpu"
            self.torch_dtype = torch.float32
            self.logger.info("💻 Using CPU for text generation")
        
        # Model components
        self.tokenizer = None
        self.model = None
        self.is_loaded = False
        
        # Content creation settings
        self.max_length = 2048  # Longer for scripts
        self.default_temperature = 0.7  # Balanced creativity
        
        self.logger.info(f"✅ Content Text Generator initialized")
        self.logger.info(f"   Model: {self.model_id}")
    
    def load_model(self):
        """Load the language model with optimizations"""
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers not available. Install with: pip install transformers")
        
        if self.is_loaded:
            self.logger.info("✅ Model already loaded")
            return
        
        try:
            self.logger.info(f"📥 Loading {self.model_id}...")
            start_time = time.time()
            
            # Get HuggingFace token
            import os
            hf_token = os.getenv("HUGGINGFACE_TOKEN")
            
            # Load tokenizer
            self.logger.info("   Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                token=hf_token
            )
            
            # Load model with optimizations
            self.logger.info("   Loading model...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype=self.torch_dtype,
                token=hf_token,
                low_cpu_mem_usage=True
            )
            
            # Move to device
            self.model = self.model.to(self.device)
            self.model.eval()
            
            # Enable optimizations
            if self.device == "cuda":
                # Enable attention slicing
                if hasattr(self.model, 'enable_attention_slicing'):
                    self.model.enable_attention_slicing()
                    self.logger.info("⚡ Attention slicing enabled")
            
            load_time = time.time() - start_time
            self.is_loaded = True
            
            self.logger.info(f"✅ Model loaded in {load_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load model: {e}")
            raise
    
    async def generate(
        self,
        prompt: str,
        content_type: str = "general",
        language: str = "english",
        creator_type: str = "general",
        max_length: int = 500,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate content for creators
        
        Args:
            prompt: Content description/topic
            content_type: Type of content (script, description, caption, etc.)
            language: Output language (english, hindi, hinglish)
            creator_type: Type of creator (youtuber, director, producer, etc.)
            max_length: Maximum tokens to generate
            temperature: Creativity (0.1-1.5)
            top_p: Nucleus sampling
            top_k: Top-k sampling
            seed: Random seed for reproducibility
        
        Returns:
            Dictionary with generated content and metadata
        """
        if not self.is_loaded:
            self.load_model()
        
        start_time = time.time()
        
        try:
            # Build optimized prompt
            enhanced_prompt = self._build_content_prompt(
                prompt=prompt,
                content_type=content_type,
                language=language,
                creator_type=creator_type
            )
            
            self.logger.info(f"📝 Generating {content_type} content in {language}...")
            
            # Tokenize
            inputs = self.tokenizer(
                enhanced_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=1024
            ).to(self.device)
            
            # Set seed for reproducibility
            if seed is not None:
                torch.manual_seed(seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed(seed)
            
            # Generate with optimizations
            with torch.no_grad():
                if self.device == "cuda":
                    with torch.cuda.amp.autocast():
                        outputs = self.model.generate(
                            **inputs,
                            max_new_tokens=max_length,
                            temperature=temperature,
                            top_p=top_p,
                            top_k=top_k,
                            do_sample=True,
                            pad_token_id=self.tokenizer.eos_token_id,
                            repetition_penalty=1.1
                        )
                else:
                    outputs = self.model.generate(
                        **inputs,
                        max_new_tokens=max_length,
                        temperature=temperature,
                        top_p=top_p,
                        top_k=top_k,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id,
                        repetition_penalty=1.1
                    )
            
            # Decode
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the generated part (remove prompt)
            generated_text = self._extract_generated_content(generated_text, enhanced_prompt)
            
            # Post-process based on content type
            generated_text = self._post_process_content(generated_text, content_type, language)
            
            generation_time = time.time() - start_time
            
            self.logger.info(f"✅ Content generated in {generation_time:.2f}s")
            
            return {
                "text": generated_text,
                "prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "content_type": content_type,
                "language": language,
                "creator_type": creator_type,
                "generation_time": generation_time,
                "parameters": {
                    "max_length": max_length,
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "seed": seed
                },
                "model_used": self.model_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Content generation failed: {e}")
            raise
    
    def _build_content_prompt(
        self,
        prompt: str,
        content_type: str,
        language: str,
        creator_type: str
    ) -> str:
        """
        Build optimized prompt for content creation
        
        Uses specialized templates for different content types and creators
        """
        # Language instructions
        language_instructions = {
            "english": "Write in clear, professional English.",
            "hindi": "हिंदी में लिखें। स्पष्ट और पेशेवर भाषा का उपयोग करें।",
            "hinglish": "Write in Hinglish (mix of Hindi and English). Use casual, relatable language."
        }
        
        lang_instruction = language_instructions.get(language, language_instructions["english"])
        
        # Content type templates
        templates = {
            "youtube_script": f"""[INST] You are a professional YouTube scriptwriter. {lang_instruction}

Create an engaging YouTube video script for: {prompt}

Include:
- Catchy hook/intro
- Main content with storytelling
- Call-to-action
- Engaging language

Script: [/INST]""",
            
            "youtube_description": f"""[INST] You are a YouTube SEO expert. {lang_instruction}

Write an optimized YouTube video description for: {prompt}

Include:
- Compelling summary
- Relevant keywords
- Timestamps (if applicable)
- Social media links placeholder
- Hashtags

Description: [/INST]""",
            
            "instagram_caption": f"""[INST] You are a social media expert. {lang_instruction}

Write an engaging Instagram caption for: {prompt}

Include:
- Attention-grabbing first line
- Storytelling or value
- Call-to-action
- Relevant hashtags (10-15)

Caption: [/INST]""",
            
            "video_script": f"""[INST] You are a professional video scriptwriter. {lang_instruction}

Write a compelling video script for: {prompt}

Include:
- Scene descriptions
- Dialogue
- Visual cues
- Pacing notes

Script: [/INST]""",
            
            "film_script": f"""[INST] You are a professional screenwriter. {lang_instruction}

Write a film script scene for: {prompt}

Format:
- Scene heading
- Action lines
- Character dialogue
- Camera directions

Script: [/INST]""",
            
            "social_media_post": f"""[INST] You are a social media content creator. {lang_instruction}

Create an engaging social media post about: {prompt}

Make it:
- Attention-grabbing
- Shareable
- Platform-appropriate
- Include relevant hashtags

Post: [/INST]""",
            
            "blog_post": f"""[INST] You are a professional content writer. {lang_instruction}

Write a blog post about: {prompt}

Include:
- Catchy title
- Introduction
- Main points with subheadings
- Conclusion
- SEO-friendly

Post: [/INST]""",
            
            "product_description": f"""[INST] You are a copywriter. {lang_instruction}

Write a compelling product description for: {prompt}

Include:
- Key features
- Benefits
- Unique selling points
- Call-to-action

Description: [/INST]""",
            
            "general": f"""[INST] You are a professional content creator. {lang_instruction}

Create engaging content about: {prompt}

Make it creative, informative, and engaging.

Content: [/INST]"""
        }
        
        # Get template or use general
        template = templates.get(content_type, templates["general"])
        
        return template
    
    def _extract_generated_content(self, full_text: str, prompt: str) -> str:
        """Extract only the generated content, removing the prompt"""
        # Try to find where the actual content starts
        if "[/INST]" in full_text:
            parts = full_text.split("[/INST]")
            if len(parts) > 1:
                return parts[1].strip()
        
        # Fallback: return everything after the prompt
        if prompt in full_text:
            return full_text.replace(prompt, "").strip()
        
        return full_text.strip()
    
    def _post_process_content(self, text: str, content_type: str, language: str) -> str:
        """Post-process generated content for better quality"""
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove incomplete sentences at the end
        if text and not text[-1] in '.!?।':
            # Find last complete sentence
            last_punct = max(
                text.rfind('.'),
                text.rfind('!'),
                text.rfind('?'),
                text.rfind('।')  # Hindi full stop
            )
            if last_punct > len(text) * 0.7:  # Only if we're not cutting too much
                text = text[:last_punct + 1]
        
        return text.strip()
    
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
            
            self.logger.info("🗑️ Text model unloaded")
