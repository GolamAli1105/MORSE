"""
Configuration Management
========================

Centralized configuration for the entire application.
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""
    
    # Application
    APP_NAME = "Generative Copilot"
    APP_VERSION = "2.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    # Database
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "data/copilot.db")
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "generative_copilot")
    
    # Models
    IMAGE_MODEL = os.getenv("IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell")
    MUSIC_MODEL = os.getenv("MUSIC_MODEL", "facebook/musicgen-small")
    TEXT_MODEL = os.getenv("TEXT_MODEL", "mistralai/Mistral-7B-Instruct-v0.2")
    
    # Device
    DEVICE = os.getenv("DEVICE", "cuda" if os.getenv("CUDA_AVAILABLE") else "cpu")
    
    # RAG Settings
    RAG_ENABLED = os.getenv("RAG_ENABLED", "True").lower() == "true"
    RAG_MIN_RATING = float(os.getenv("RAG_MIN_RATING", "4.0"))
    RAG_MAX_REFERENCES = int(os.getenv("RAG_MAX_REFERENCES", "5"))
    
    # Fine-tuning
    FINETUNING_MIN_SAMPLES = int(os.getenv("FINETUNING_MIN_SAMPLES", "20"))
    FINETUNING_EPOCHS = int(os.getenv("FINETUNING_EPOCHS", "3"))
    FINETUNING_BATCH_SIZE = int(os.getenv("FINETUNING_BATCH_SIZE", "4"))
    FINETUNING_LEARNING_RATE = float(os.getenv("FINETUNING_LEARNING_RATE", "2e-5"))
    
    # Paths
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    MODELS_DIR = BASE_DIR / "models"
    FINETUNING_DIR = DATA_DIR / "finetuning"
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.MODELS_DIR.mkdir(exist_ok=True)
        cls.FINETUNING_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def get_model_config(cls, modality: str) -> Dict[str, Any]:
        """Get model configuration for a specific modality"""
        configs = {
            "image": {
                "model_id": cls.IMAGE_MODEL,
                "device": cls.DEVICE
            },
            "music": {
                "model_id": cls.MUSIC_MODEL,
                "device": cls.DEVICE
            },
            "text": {
                "model_id": cls.TEXT_MODEL,
                "device": cls.DEVICE
            }
        }
        return configs.get(modality, {})
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "app_name": cls.APP_NAME,
            "version": cls.APP_VERSION,
            "debug": cls.DEBUG,
            "rag_enabled": cls.RAG_ENABLED,
            "models": {
                "image": cls.IMAGE_MODEL,
                "music": cls.MUSIC_MODEL,
                "text": cls.TEXT_MODEL
            }
        }


# Initialize directories on import
Config.ensure_directories()
