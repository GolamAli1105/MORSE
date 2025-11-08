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
    from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline, FluxPipeline
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
            "runwayml/stable-diffusion-v1-5"
        )
        
        # Detect model type
        self.is_flux = "flux" in self.model_id.lower()
        self.is_sdxl = "stable-diffusion-xl" in self.model_id.lower() or "sdxl" in self.model_id.lower()
        self.is_sd15 = "stable-diffusion-v1" in self.model_id.lower() or "sd-v1" in self.model_id.lower()
        
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
        
        # Generation defaults optimized for speed
        if self.is_flux:
            self.default_steps = 2  # FLUX: 1-2 steps for maximum speed
            self.default_guidance_scale = 0.0  # FLUX doesn't use guidance
        elif self.is_sd15:
            self.default_steps = 15  # SD 1.5: Lighter, faster
            self.default_guidance_scale = 7.5  # SD 1.5: Standard guidance
        else:
            self.default_steps = 20  # SDXL: Reduced from 30 for speed
            self.default_guidance_scale = 5.0  # SDXL: Reduced from 7.5 for speed
        
        # Performance settings
        self.default_width = 512  # Reduced from 1024 for 4x speed
        self.default_height = 512
        
        self.logger.info(f"✅ Optimized Image Generator initialized (model: {self.model_id})")
        self.logger.info(f"⚡ Speed optimizations: FP16, attention slicing, reduced resolution")
    
    def load_model(self):
        """
        Load the image generation pipeline with aggressive optimizations
        
        Optimizations applied:
        - FP16 precision (2x faster on GPU)
        - Attention slicing (lower memory)
        - VAE slicing (faster decoding)
        - xformers (20-30% faster if available)
        - Torch compile (PyTorch 2.0+)
        """
        if not DIFFUSERS_AVAILABLE:
            raise ImportError("diffusers library not available. Install with: pip install diffusers")
        
        if self.is_loaded:
            self.logger.info("✅ Model already loaded")
            return
        
        try:
            self.logger.info(f"📥 Loading optimized model: {self.model_id}...")
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
                    token=hf_token,
                    low_cpu_mem_usage=True
                )
            elif self.is_sd15:
                # Use lighter SD 1.5 for CPU compatibility
                from diffusers import StableDiffusionPipeline
                self.pipeline = StableDiffusionPipeline.from_pretrained(
                    self.model_id,
                    torch_dtype=self.torch_dtype,
                    safety_checker=None,
                    token=hf_token,
                    low_cpu_mem_usage=True
                )
            else:
                # Use SDXL or other Stable Diffusion models
                self.pipeline = StableDiffusionXLPipeline.from_pretrained(
                    self.model_id,
                    torch_dtype=self.torch_dtype,
                    use_safetensors=True,
                    token=hf_token,
                    variant="fp16" if self.torch_dtype == torch.float16 else None,
                    low_cpu_mem_usage=True
                )
            
            # Move to device
            if self.device == "cuda":
                self.pipeline = self.pipeline.to(self.device)
                
                # AGGRESSIVE PERFORMANCE OPTIMIZATIONS
                
                # 1. Enable attention slicing (reduces memory, slight speed boost)
                self.pipeline.enable_attention_slicing(slice_size=1)
                self.logger.info("⚡ Attention slicing enabled")
                
                # 2. Enable VAE slicing (faster VAE decoding)
                if hasattr(self.pipeline, 'enable_vae_slicing'):
                    self.pipeline.enable_vae_slicing()
                    self.logger.info("⚡ VAE slicing enabled")
                
                # 3. Enable VAE tiling for lower memory (optional)
                if hasattr(self.pipeline, 'enable_vae_tiling'):
                    self.pipeline.enable_vae_tiling()
                    self.logger.info("⚡ VAE tiling enabled")
                
                # 4. Try to enable xformers (20-30% faster)
                try:
                    self.pipeline.enable_xformers_memory_efficient_attention()
                    self.logger.info("⚡ xformers enabled (20-30% faster)")
                except Exception as e:
                    self.logger.warning(f"xformers not available: {e}")
                
                # 5. Compile UNet for faster inference (PyTorch 2.0+)
                if hasattr(torch, 'compile') and hasattr(self.pipeline, 'unet'):
                    try:
                        self.pipeline.unet = torch.compile(
                            self.pipeline.unet,
                            mode="reduce-overhead",
                            fullgraph=True
                        )
                        self.logger.info("⚡ UNet compiled (faster inference)")
                    except Exception as e:
                        self.logger.warning(f"Could not compile UNet: {e}")
                
                # 6. Enable CUDA graphs for even faster inference
                if hasattr(self.pipeline, 'enable_cuda_graphs'):
                    try:
                        self.pipeline.enable_cuda_graphs()
                        self.logger.info("⚡ CUDA graphs enabled")
                    except Exception as e:
                        self.logger.warning(f"CUDA graphs not available: {e}")
                
                # Optional: Enable CPU offload for lower VRAM usage
                if self.enable_cpu_offload:
                    self.pipeline.enable_model_cpu_offload()
                    self.logger.info("🔄 CPU offload enabled")
            else:
                # CPU optimizations
                self.pipeline = self.pipeline.to(self.device)
                self.logger.info("💻 Running on CPU (slower)")
            
            load_time = time.time() - start_time
            self.is_loaded = True
            
            self.logger.info(f"✅ Model loaded with optimizations in {load_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load model: {e}")
            raise
    
    async def generate(
        self,
        prompt: str,
        style: str = "auto",
        width: int = 512,  # Reduced default for speed
        height: int = 512,  # Reduced default for speed
        num_inference_steps: int = 4,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate an image with aggressive speed optimizations
        
        Args:
            prompt: Text description of the image to generate
            style: Style preset or "auto" for auto-detection
            width: Image width (default: 512 for speed, max: 1024)
            height: Image height (default: 512 for speed, max: 1024)
            num_inference_steps: Denoising steps (1-4 for speed, 20+ for quality)
            seed: Random seed for reproducibility (optional)
            **kwargs: Additional generation parameters
        
        Returns:
            Dictionary containing image data and metadata
        """
        # Ensure model is loaded
        if not self.is_loaded:
            self.load_model()
        
        start_time = time.time()
        
        try:
            # Auto-detect style if set to "auto"
            if style == "auto":
                style = self._detect_style(prompt)
            
            # Enhance prompt based on style
            enhanced_prompt = self._enhance_prompt(prompt, style)
            
            # SPEED OPTIMIZATION: Cap resolution for faster generation
            # 512x512 is 4x faster than 1024x1024
            max_dimension = 1024
            width = min((width // 8) * 8, max_dimension)
            height = min((height // 8) * 8, max_dimension)
            
            # SPEED OPTIMIZATION: Use minimal steps for fast generation
            if self.is_flux:
                # FLUX: 1-4 steps (1 is fastest)
                num_inference_steps = max(1, min(num_inference_steps, 4))
                if num_inference_steps > 2:
                    self.logger.info(f"⚡ Reducing steps from {num_inference_steps} to 2 for faster generation")
                    num_inference_steps = 2
            else:
                # SDXL: Reduce to minimum for speed
                num_inference_steps = max(10, min(num_inference_steps, 50))
                if num_inference_steps > 20:
                    self.logger.info(f"⚡ Reducing steps from {num_inference_steps} to 20 for faster generation")
                    num_inference_steps = 20
            
            self.logger.info(f"🎨 Generating {width}x{height} image ({num_inference_steps} steps)...")
            
            # Set up generator for reproducibility
            generator = None
            if seed is not None:
                generator = torch.Generator(device=self.device).manual_seed(seed)
            
            # SPEED OPTIMIZATION: Use torch.inference_mode for faster inference
            with torch.inference_mode():
                # SPEED OPTIMIZATION: Use autocast for mixed precision
                if self.device == "cuda":
                    with torch.cuda.amp.autocast():
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
                            # SDXL: Use lower guidance for speed
                            guidance_scale = kwargs.get('guidance_scale', 5.0)  # Reduced from 7.5
                            if guidance_scale > 5.0:
                                self.logger.info(f"⚡ Reducing guidance from {guidance_scale} to 5.0 for speed")
                                guidance_scale = 5.0
                            
                            result = self.pipeline(
                                prompt=enhanced_prompt,
                                width=width,
                                height=height,
                                num_inference_steps=num_inference_steps,
                                guidance_scale=guidance_scale,
                                generator=generator
                            )
                else:
                    # CPU generation (slower)
                    if self.is_flux:
                        result = self.pipeline(
                            prompt=enhanced_prompt,
                            width=width,
                            height=height,
                            num_inference_steps=num_inference_steps,
                            generator=generator,
                            output_type="pil"
                        )
                    else:
                        guidance_scale = kwargs.get('guidance_scale', 5.0)
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
            
            # SPEED OPTIMIZATION: Convert to base64 efficiently
            image_base64 = self._image_to_base64_fast(image)
            
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
                "model_used": self.model_id.split('/')[-1],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Image generation failed: {e}")
            raise
    
    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """
        Intelligently enhance the prompt based on content and style
        
        This method:
        1. Detects user intent (logo, product, text, scene, etc.)
        2. Optimizes prompt for best results
        3. Adds style-specific enhancements
        """
        # First, intelligently optimize the base prompt
        optimized_prompt = self._optimize_user_prompt(prompt)
        
        # Then apply style enhancements
        style_enhancements = {
            "photorealistic": f"{optimized_prompt}, photorealistic, highly detailed, 8k uhd, professional photography, natural lighting, sharp focus, dslr quality",
            
            "artistic": f"{optimized_prompt}, artistic, creative composition, vibrant colors, expressive, masterpiece, trending on artstation, digital art",
            
            "cinematic": f"{optimized_prompt}, cinematic lighting, dramatic atmosphere, film grain, depth of field, professional color grading, movie poster quality",
            
            "anime": f"{optimized_prompt}, anime style, detailed anime art, vibrant colors, clean lines, studio quality, manga inspired",
            
            "fantasy": f"{optimized_prompt}, fantasy art, magical atmosphere, ethereal lighting, highly detailed, concept art, epic composition",
            
            "minimalist": f"{optimized_prompt}, minimalist design, clean composition, simple, elegant, modern aesthetic, flat design",
            
            "vintage": f"{optimized_prompt}, vintage style, retro aesthetic, nostalgic atmosphere, film photography, aged paper texture",
            
            "abstract": f"{optimized_prompt}, abstract art, creative interpretation, bold colors, unique composition, modern art",
            
            "sketch": f"{optimized_prompt}, detailed sketch, pencil drawing, artistic linework, hand-drawn quality, traditional art",
            
            "3d_render": f"{optimized_prompt}, 3d render, octane render, highly detailed, professional 3d modeling, ray tracing, unreal engine",
            
            "logo": f"{optimized_prompt}, professional logo design, clean vector style, modern branding, minimalist, iconic, memorable design, white background",
            
            "product": f"{optimized_prompt}, professional product photography, studio lighting, clean background, commercial quality, high resolution, advertising style",
            
            "default": optimized_prompt
        }
        
        return style_enhancements.get(style, optimized_prompt)
    
    def _detect_style(self, prompt: str) -> str:
        """
        Auto-detect the best style based on prompt content
        """
        prompt_lower = prompt.lower()
        
        # Check for specific style indicators
        if 'logo' in prompt_lower or 'brand' in prompt_lower:
            return 'logo'
        elif any(word in prompt_lower for word in ['product', 'commercial', 'advertising']):
            return 'product'
        elif any(word in prompt_lower for word in ['photo', 'realistic', 'real']):
            return 'photorealistic'
        elif any(word in prompt_lower for word in ['anime', 'manga', 'cartoon']):
            return 'anime'
        elif any(word in prompt_lower for word in ['art', 'painting', 'artistic']):
            return 'artistic'
        elif any(word in prompt_lower for word in ['cinematic', 'movie', 'film']):
            return 'cinematic'
        elif any(word in prompt_lower for word in ['3d', 'render', 'cgi']):
            return '3d_render'
        else:
            return 'default'
    
    def _optimize_user_prompt(self, prompt: str) -> str:
        """
        Intelligently optimize user prompt based on detected intent
        
        Handles cases like:
        - "BurgerBomba" -> burger with text
        - "Nike logo" -> logo design
        - "sunset beach" -> scenic photo
        - "happy dog" -> subject photo
        """
        import re
        
        prompt_lower = prompt.lower()
        
        # Detect if prompt contains text that should appear in image
        # Pattern: word with capital letters or quoted text
        has_brand_name = bool(re.search(r'\b[A-Z][a-z]*[A-Z][a-z]*\b', prompt))
        has_quotes = '"' in prompt or "'" in prompt
        
        # Extract brand/text if present
        brand_match = re.search(r'\b([A-Z][a-z]*[A-Z][a-z]*|[A-Z]{2,})\b', prompt)
        brand_name = brand_match.group(1) if brand_match else None
        
        # LOGO DETECTION
        if 'logo' in prompt_lower:
            if brand_name:
                return f"professional logo design for '{brand_name}', modern, clean, minimalist, vector style, iconic symbol, memorable branding"
            return f"{prompt}, professional logo design, modern, clean, minimalist, vector style, iconic symbol"
        
        # PRODUCT WITH TEXT DETECTION (like "BurgerBomba")
        if brand_name and any(word in prompt_lower for word in ['burger', 'pizza', 'food', 'drink', 'product', 'package', 'bottle', 'can']):
            # Extract the product type
            product_type = None
            for word in ['burger', 'pizza', 'sandwich', 'taco', 'hotdog', 'drink', 'soda', 'beer', 'coffee']:
                if word in prompt_lower:
                    product_type = word
                    break
            
            if product_type:
                return (f"a large, appetizing {product_type} as the main focus, "
                       f"with bold text '{brand_name}' prominently displayed, "
                       f"professional food photography, studio lighting, vibrant colors, "
                       f"commercial advertising style, mouth-watering presentation, "
                       f"high resolution, clean composition, brand identity visible")
            else:
                return (f"professional product shot featuring '{brand_name}' branding, "
                       f"clean composition, studio lighting, commercial quality, "
                       f"text clearly visible and readable")
        
        # TEXT/TYPOGRAPHY DETECTION
        if has_brand_name or has_quotes or any(word in prompt_lower for word in ['text', 'word', 'typography', 'lettering', 'sign']):
            if brand_name:
                return (f"bold, eye-catching text displaying '{brand_name}', "
                       f"professional typography, modern font, high contrast, "
                       f"clean background, graphic design quality, readable and impactful")
            return f"{prompt}, professional typography, bold lettering, high contrast, clean design, readable text"
        
        # FOOD PHOTOGRAPHY
        if any(word in prompt_lower for word in ['burger', 'pizza', 'food', 'meal', 'dish', 'cuisine', 'restaurant']):
            return (f"{prompt}, professional food photography, appetizing presentation, "
                   f"studio lighting, vibrant colors, mouth-watering, high resolution, "
                   f"commercial quality, detailed texture, fresh ingredients")
        
        # PORTRAIT/PERSON
        if any(word in prompt_lower for word in ['person', 'man', 'woman', 'child', 'face', 'portrait', 'people']):
            return (f"{prompt}, professional portrait photography, natural lighting, "
                   f"sharp focus, detailed features, high quality, photorealistic, "
                   f"8k resolution, professional composition")
        
        # LANDSCAPE/SCENE
        if any(word in prompt_lower for word in ['landscape', 'mountain', 'beach', 'forest', 'city', 'sunset', 'nature', 'sky']):
            return (f"{prompt}, stunning landscape photography, golden hour lighting, "
                   f"dramatic sky, vivid colors, high resolution, professional composition, "
                   f"breathtaking view, nature photography")
        
        # ANIMAL/PET
        if any(word in prompt_lower for word in ['dog', 'cat', 'animal', 'pet', 'bird', 'wildlife']):
            return (f"{prompt}, professional wildlife photography, natural behavior, "
                   f"sharp focus, detailed fur/feathers, natural lighting, high quality, "
                   f"photorealistic, beautiful composition")
        
        # OBJECT/PRODUCT
        if any(word in prompt_lower for word in ['product', 'object', 'item', 'gadget', 'device', 'tool']):
            return (f"{prompt}, professional product photography, clean white background, "
                   f"studio lighting, commercial quality, high resolution, detailed, "
                   f"e-commerce style, sharp focus")
        
        # ABSTRACT/ARTISTIC
        if any(word in prompt_lower for word in ['abstract', 'artistic', 'creative', 'colorful', 'pattern']):
            return (f"{prompt}, creative artistic composition, vibrant colors, "
                   f"unique perspective, high quality, detailed, visually striking, "
                   f"modern art style")
        
        # DEFAULT: Add general quality enhancers
        return (f"{prompt}, high quality, detailed, professional composition, "
               f"vibrant colors, sharp focus, well-lit, visually appealing")
    
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
    
    def _image_to_base64_fast(self, image: Image.Image) -> str:
        """
        Fast base64 conversion with JPEG compression for speed
        
        Uses JPEG with quality=85 for 3-5x faster encoding than PNG
        """
        buffered = io.BytesIO()
        # Use JPEG for faster encoding (3-5x faster than PNG)
        image.save(buffered, format="JPEG", quality=85, optimize=True)
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
