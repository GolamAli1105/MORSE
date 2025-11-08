"""
FLUX.1-schnell Image Generator
==============================

Fast image generation using Black Forest Labs' FLUX.1-schnell model.
FLUX.1-schnell is optimized for speed (1-4 steps) while maintaining quality.
"""

import torch
import logging
import time
import base64
import io
from typing import Dict, Any, Optional
from datetime import datetime
from PIL import Image

logger = logging.getLogger(__name__)

# Try to import diffusers, fall back gracefully
try:
    from diffusers import StableDiffusionXLPipeline, FluxPipeline
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logger.warning("Diffusers not available - Image generator will use fallback")


class ImageGenerator:
    """
    FLUX.1-schnell Image Generator
    
    Key Features:
    - Ultra-fast generation (1-4 steps vs 20-50 for other models)
    - High quality outputs
    - Efficient memory usage
    - CPU and GPU support
    
    Model: black-forest-labs/FLUX.1-schnell
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize FLUX image generator
        
        Args:
            model_config: Configuration dictionary containing:
                - model_id: HuggingFace model ID (default: black-forest-labs/FLUX.1-schnell)
                - device: 'cuda' or 'cpu' (auto-detected if not specified)
                - torch_dtype: torch.float16 or torch.float32
                - enable_cpu_offload: Whether to use CPU offload for memory efficiency
        """
        self.logger = logging.getLogger(__name__)
        
        # Model configuration
        self.model_id = model_config.get(
            "model_id", 
            "stabilityai/stable-diffusion-xl-base-1.0"
        )
        
        # Detect model type
        self.is_flux = "flux" in self.model_id.lower()
        self.is_sdxl = "stable-diffusion-xl" in self.model_id.lower() or "sdxl" in self.model_id.lower()
        
        # Device setup - auto-detect if not specified
        if torch.cuda.is_available():
            self.device = model_config.get("device", "cuda")
            self.torch_dtype = model_config.get("torch_dtype", torch.float16)
            self.logger.info("🎮 Using GPU for FLUX generation")
        else:
            self.device = "cpu"
            self.torch_dtype = torch.float32
            self.logger.info("💻 Using CPU for FLUX generation (slower)")
        
        # Memory optimization settings
        self.enable_cpu_offload = model_config.get("enable_cpu_offload", False)
        
        # Pipeline will be loaded lazily
        self.pipeline = None
        self.is_loaded = False
        
        # Generation defaults based on model type
        if self.is_flux:
            self.default_steps = 4  # FLUX.1-schnell is optimized for 1-4 steps
            self.default_guidance_scale = 0.0  # FLUX.1-schnell doesn't use guidance
        else:
            self.default_steps = 30  # SDXL uses more steps
            self.default_guidance_scale = 7.5  # SDXL uses guidance
        
        self.logger.info(f"✅ FLUX Image Generator initialized (model: {self.model_id})")
    
    def load_model(self):
        """
        Load the FLUX pipeline
        
        This is done lazily to avoid loading the model until it's actually needed.
        The model is ~24GB, so this can take a few minutes on first load.
        """
        if not DIFFUSERS_AVAILABLE:
            raise ImportError("diffusers library not available. Install with: pip install diffusers")
        
        if self.is_loaded:
            self.logger.info("Model already loaded")
            return
        
        try:
            self.logger.info(f"📥 Loading FLUX.1-schnell model from {self.model_id}...")
            self.logger.info("⏳ This may take a few minutes on first run...")
            
            start_time = time.time()
            
            # Get HuggingFace token from environment
            import os
            hf_token = os.getenv("HUGGINGFACE_TOKEN")
            
            # Load the appropriate pipeline based on model type
            if self.is_flux:
                self.pipeline = FluxPipeline.from_pretrained(
                    self.model_id,
                    torch_dtype=self.torch_dtype,
                    use_safetensors=True,
                    token=hf_token
                )
            else:
                # Use SDXL or other Stable Diffusion models
                self.pipeline = StableDiffusionXLPipeline.from_pretrained(
                    self.model_id,
                    torch_dtype=self.torch_dtype,
                    use_safetensors=True,
                    token=hf_token,
                    variant="fp16" if self.torch_dtype == torch.float16 else None
                )
            
            # Move to device
            if self.device == "cuda":
                self.pipeline = self.pipeline.to(self.device)
                
                # Enable memory optimizations for GPU
                self.pipeline.enable_attention_slicing()
                
                # Optional: Enable CPU offload for lower VRAM usage
                if self.enable_cpu_offload:
                    self.pipeline.enable_model_cpu_offload()
                    self.logger.info("🔄 CPU offload enabled for memory efficiency")
            else:
                # CPU optimizations
                self.pipeline = self.pipeline.to(self.device)
            
            load_time = time.time() - start_time
            self.is_loaded = True
            
            self.logger.info(f"✅ FLUX model loaded in {load_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load FLUX model: {e}")
            raise
    
    async def generate(
        self,
        prompt: str,
        style: str = "default",
        width: int = 1024,
        height: int = 1024,
        num_inference_steps: int = 4,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate an image using FLUX.1-schnell
        
        Args:
            prompt: Text description of the image to generate
            style: Style preset (photorealistic, artistic, etc.)
            width: Image width (default: 1024, must be multiple of 8)
            height: Image height (default: 1024, must be multiple of 8)
            num_inference_steps: Number of denoising steps (1-4 recommended for schnell)
            seed: Random seed for reproducibility (optional)
            **kwargs: Additional generation parameters
        
        Returns:
            Dictionary containing:
                - image_data: Base64 encoded image
                - image_pil: PIL Image object
                - prompt: Original prompt
                - enhanced_prompt: Style-enhanced prompt
                - generation_time: Time taken to generate
                - parameters: Generation parameters used
        """
        # Ensure model is loaded
        if not self.is_loaded:
            self.load_model()
        
        start_time = time.time()
        
        try:
            # Enhance prompt based on style
            enhanced_prompt = self._enhance_prompt(prompt, style)
            
            # Validate dimensions (must be multiples of 8)
            width = (width // 8) * 8
            height = (height // 8) * 8
            
            # Clamp steps based on model type
            if self.is_flux:
                num_inference_steps = max(1, min(num_inference_steps, 4))
            else:
                num_inference_steps = max(10, min(num_inference_steps, 50))
            
            self.logger.info(f"🎨 Generating image: {enhanced_prompt[:50]}...")
            
            # Set up generator for reproducibility
            generator = None
            if seed is not None:
                generator = torch.Generator(device=self.device).manual_seed(seed)
            
            # Generate image with appropriate parameters
            if self.is_flux:
                # FLUX doesn't use guidance_scale
                result = self.pipeline(
                    prompt=enhanced_prompt,
                    width=width,
                    height=height,
                    num_inference_steps=num_inference_steps,
                    generator=generator,
                    output_type="pil"
                )
            else:
                # SDXL and other models use guidance_scale
                guidance_scale = kwargs.get('guidance_scale', self.default_guidance_scale)
                result = self.pipeline(
                    prompt=enhanced_prompt,
                    width=width,
                    height=height,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    generator=generator
                )
            
            # Get the generated image
            image = result.images[0]
            
            # Convert to base64 for storage/transmission
            image_base64 = self._image_to_base64(image)
            
            generation_time = time.time() - start_time
            
            self.logger.info(f"✅ Image generated in {generation_time:.2f}s")
            
            return {
                "image_data": image_base64,
                "image_pil": image,
                "prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "style": style,
                "generation_time": generation_time,
                "parameters": {
                    "width": width,
                    "height": height,
                    "num_inference_steps": num_inference_steps,
                    "seed": seed,
                    "model": self.model_id
                },
                "model_used": "FLUX.1-schnell",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Image generation failed: {e}")
            raise
    
    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """
        Enhance the prompt based on the selected style
        
        FLUX models respond well to detailed, descriptive prompts.
        This method adds style-specific enhancements.
        """
        style_enhancements = {
            "photorealistic": f"{prompt}, photorealistic, highly detailed, 8k uhd, professional photography, natural lighting, sharp focus",
            
            "artistic": f"{prompt}, artistic, creative composition, vibrant colors, expressive, masterpiece, trending on artstation",
            
            "cinematic": f"{prompt}, cinematic lighting, dramatic atmosphere, film grain, depth of field, professional color grading",
            
            "anime": f"{prompt}, anime style, detailed anime art, vibrant colors, clean lines, studio quality",
            
            "fantasy": f"{prompt}, fantasy art, magical atmosphere, ethereal lighting, highly detailed, concept art",
            
            "minimalist": f"{prompt}, minimalist design, clean composition, simple, elegant, modern aesthetic",
            
            "vintage": f"{prompt}, vintage style, retro aesthetic, nostalgic atmosphere, film photography",
            
            "abstract": f"{prompt}, abstract art, creative interpretation, bold colors, unique composition",
            
            "sketch": f"{prompt}, detailed sketch, pencil drawing, artistic linework, hand-drawn quality",
            
            "3d_render": f"{prompt}, 3d render, octane render, highly detailed, professional 3d modeling, ray tracing",
            
            "default": prompt
        }
        
        return style_enhancements.get(style, prompt)
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """
        Convert PIL Image to base64 string
        
        This is useful for storing images in databases or sending via APIs.
        """
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_bytes = buffered.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        return img_base64
    
    def save_image(self, image: Image.Image, filepath: str):
        """Save generated image to file"""
        image.save(filepath)
        self.logger.info(f"💾 Image saved to {filepath}")
    
    def unload_model(self):
        """Unload model to free memory"""
        if self.pipeline is not None:
            del self.pipeline
            self.pipeline = None
            self.is_loaded = False
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.logger.info("🗑️ FLUX model unloaded")
