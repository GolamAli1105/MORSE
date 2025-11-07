import torch
import logging
import time
import base64
import io
import numpy as np
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import required libraries
try:
    from transformers import AutoProcessor, MusicgenForConditionalGeneration
    import scipy.io.wavfile as wavfile
    AUDIO_LIBS_AVAILABLE = True
except ImportError:
    AUDIO_LIBS_AVAILABLE = False
    logger.warning("Audio libraries not available - SongBloom will use fallback")


class MusicGenerator:
    """
    SongBloom Music Generator
    
    Key Features:
    - Text-to-music generation
    - Lyrics-to-music generation
    - Multiple genre support
    - Controllable duration
    - High-quality audio output
    
    Model: CypressYang/SongBloom
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        """
        Initialize SongBloom music generator
        
        Args:
            model_config: Configuration dictionary containing:
                - model_id: HuggingFace model ID (default: CypressYang/SongBloom)
                - device: 'cuda' or 'cpu'
                - sample_rate: Audio sample rate (default: 32000)
                - max_duration: Maximum audio duration in seconds
        """
        self.logger = logging.getLogger(__name__)
        
        # Model configuration
        self.model_id = model_config.get(
            "model_id",
            "facebook/musicgen-small"  # Fallback to musicgen if SongBloom not available
        )
        
        # Try SongBloom first, fall back to MusicGen
        self.songbloom_id = "CypressYang/SongBloom"
        
        # Device setup
        if torch.cuda.is_available():
            self.device = model_config.get("device", "cuda")
            self.torch_dtype = torch.float16
            self.logger.info("🎮 Using GPU for music generation")
        else:
            self.device = "cpu"
            self.torch_dtype = torch.float32
            self.logger.info("💻 Using CPU for music generation")
        
        # Audio settings
        self.sample_rate = model_config.get("sample_rate", 32000)
        self.max_duration = model_config.get("max_duration", 50)
        
        # Model components
        self.model = None
        self.processor = None
        self.is_loaded = False
        
        self.logger.info(f"✅ SongBloom Music Generator initialized")
    
    def load_model(self):
        """
        Load the SongBloom/MusicGen model
        
        Attempts to load SongBloom first, falls back to MusicGen if unavailable.
        """
        if not AUDIO_LIBS_AVAILABLE:
            raise ImportError(
                "Audio libraries not available. Install with: "
                "pip install transformers scipy"
            )
        
        if self.is_loaded:
            self.logger.info("Model already loaded")
            return
        
        try:
            self.logger.info(f"📥 Loading music generation model...")
            start_time = time.time()
            
            # Try to load SongBloom, fall back to MusicGen
            try:
                self.logger.info(f"Attempting to load {self.songbloom_id}...")
                self.processor = AutoProcessor.from_pretrained(self.songbloom_id)
                self.model = MusicgenForConditionalGeneration.from_pretrained(
                    self.songbloom_id,
                    torch_dtype=self.torch_dtype
                )
                self.model_name = "SongBloom"
                self.logger.info("✅ SongBloom model loaded")
            except Exception as e:
                self.logger.warning(f"SongBloom not available ({e}), using MusicGen")
                self.processor = AutoProcessor.from_pretrained(self.model_id)
                self.model = MusicgenForConditionalGeneration.from_pretrained(
                    self.model_id,
                    torch_dtype=self.torch_dtype
                )
                self.model_name = "MusicGen"
            
            # Move to device
            self.model = self.model.to(self.device)
            
            # Set to evaluation mode
            self.model.eval()
            
            load_time = time.time() - start_time
            self.is_loaded = True
            
            self.logger.info(f"✅ Music model loaded in {load_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load music model: {e}")
            raise
    
    async def generate(
        self,
        prompt: str,
        style: str = "default",
        duration: int = 15,
        temperature: float = 1.0,
        top_k: int = 250,
        top_p: float = 0.0,
        guidance_scale: float = 3.0,
        seed: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate music from text description
        
        Args:
            prompt: Text description of the music to generate
            style: Musical style/genre (pop, rock, jazz, classical, etc.)
            duration: Duration in seconds (max 30s for memory efficiency)
            temperature: Sampling temperature (higher = more random)
            top_k: Top-k sampling parameter
            top_p: Top-p (nucleus) sampling parameter
            guidance_scale: Classifier-free guidance scale
            seed: Random seed for reproducibility
            **kwargs: Additional parameters
        
        Returns:
            Dictionary containing:
                - audio_data: Base64 encoded audio (WAV format)
                - audio_array: NumPy array of audio samples
                - prompt: Original prompt
                - enhanced_prompt: Style-enhanced prompt
                - generation_time: Time taken
                - parameters: Generation parameters
        """
        # Ensure model is loaded
        if not self.is_loaded:
            self.load_model()
        
        start_time = time.time()
        
        try:
            # Enhance prompt based on style
            enhanced_prompt = self._enhance_music_prompt(prompt, style)
            
            # Clamp duration
            duration = min(duration, self.max_duration)
            
            self.logger.info(f"🎵 Generating music: {enhanced_prompt[:50]}...")
            
            # Prepare inputs
            inputs = self.processor(
                text=[enhanced_prompt],
                padding=True,
                return_tensors="pt"
            ).to(self.device)
            
            # Calculate max new tokens based on duration
            # MusicGen generates at ~50 tokens per second
            max_new_tokens = int(duration * 50)
            
            # Set up generator for reproducibility
            if seed is not None:
                torch.manual_seed(seed)
                if torch.cuda.is_available():
                    torch.cuda.manual_seed(seed)
            
            # Generate audio
            with torch.no_grad():
                audio_values = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=True,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p,
                    guidance_scale=guidance_scale
                )
            
            # Convert to numpy array
            audio_array = audio_values[0, 0].cpu().numpy()
            
            # Normalize audio
            audio_array = self._normalize_audio(audio_array)
            
            # Convert to base64
            audio_base64 = self._audio_to_base64(audio_array, self.sample_rate)
            
            generation_time = time.time() - start_time
            
            self.logger.info(f"✅ Music generated in {generation_time:.2f}s")
            
            return {
                "audio_data": audio_base64,
                "audio_array": audio_array,
                "sample_rate": self.sample_rate,
                "prompt": prompt,
                "enhanced_prompt": enhanced_prompt,
                "style": style,
                "generation_time": generation_time,
                "parameters": {
                    "duration": duration,
                    "temperature": temperature,
                    "top_k": top_k,
                    "top_p": top_p,
                    "guidance_scale": guidance_scale,
                    "seed": seed,
                    "model": self.model_name
                },
                "model_used": self.model_name,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Music generation failed: {e}")
            raise
    
    async def generate_from_lyrics(
        self,
        lyrics: str,
        style: str = "pop",
        duration: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate music from lyrics
        
        This creates a musical accompaniment based on the provided lyrics.
        """
        # Create a prompt that incorporates the lyrics
        prompt = f"A {style} song with the following lyrics: {lyrics[:200]}"
        
        return await self.generate(
            prompt=prompt,
            style=style,
            duration=duration,
            **kwargs
        )
    
    def _enhance_music_prompt(self, prompt: str, style: str) -> str:
        """
        Enhance the music prompt based on style
        
        Music models benefit from detailed descriptions of:
        - Genre/style
        - Instruments
        - Mood/atmosphere
        - Tempo
        """
        style_enhancements = {
            "pop": f"{prompt}, upbeat pop music, catchy melody, modern production, electronic drums, synthesizers",
            
            "rock": f"{prompt}, energetic rock music, electric guitars, powerful drums, bass guitar, dynamic",
            
            "jazz": f"{prompt}, smooth jazz music, saxophone, piano, double bass, drums, improvised solos, sophisticated",
            
            "classical": f"{prompt}, classical orchestral music, strings, woodwinds, brass, elegant composition, concert hall",
            
            "electronic": f"{prompt}, electronic music, synthesizers, electronic beats, ambient pads, modern production",
            
            "folk": f"{prompt}, folk music, acoustic guitar, natural instruments, storytelling, organic sound",
            
            "country": f"{prompt}, country music, acoustic guitar, fiddle, steel guitar, heartfelt, traditional",
            
            "ambient": f"{prompt}, ambient music, atmospheric soundscape, ethereal pads, peaceful, meditative, slow tempo",
            
            "hip_hop": f"{prompt}, hip hop beat, rhythmic drums, bass, urban sound, modern production",
            
            "blues": f"{prompt}, blues music, guitar, harmonica, soulful, emotional, traditional blues structure",
            
            "metal": f"{prompt}, heavy metal music, distorted guitars, aggressive drums, powerful, intense",
            
            "reggae": f"{prompt}, reggae music, offbeat rhythm, bass guitar, relaxed groove, island vibes",
            
            "default": f"{prompt}, high quality music, well-produced, clear instruments"
        }
        
        return style_enhancements.get(style, style_enhancements["default"])
    
    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """
        Normalize audio to prevent clipping
        
        Scales audio to use the full dynamic range without distortion.
        """
        max_val = np.abs(audio).max()
        if max_val > 0:
            audio = audio / max_val * 0.95  # Leave some headroom
        return audio
    
    def _audio_to_base64(self, audio: np.ndarray, sample_rate: int) -> str:
        """
        Convert audio array to base64 encoded WAV
        
        This allows storing/transmitting audio data easily.
        """
        # Convert float32 to int16
        audio_int16 = (audio * 32767).astype(np.int16)
        
        # Write to bytes buffer
        buffer = io.BytesIO()
        wavfile.write(buffer, sample_rate, audio_int16)
        
        # Encode to base64
        audio_bytes = buffer.getvalue()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        return audio_base64
    
    def save_audio(self, audio: np.ndarray, filepath: str):
        """Save generated audio to file"""
        audio_int16 = (audio * 32767).astype(np.int16)
        wavfile.write(filepath, self.sample_rate, audio_int16)
        self.logger.info(f"💾 Audio saved to {filepath}")
    
    def unload_model(self):
        """Unload model to free memory"""
        if self.model is not None:
            del self.model
            del self.processor
            self.model = None
            self.processor = None
            self.is_loaded = False
            
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            self.logger.info("🗑️ Music model unloaded")
