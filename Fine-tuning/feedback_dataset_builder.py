import json 
import logging 
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import base64
from PIL import Image
import io


logger = logging.getLogger(__name__)

class UnifiedFeedbackDatasetBuilder:
    """
    A class to build a unified feedback dataset from various sources.
    """

    def __init__(self):
        self.dataset: List[Dict[str, Any]] = []

    def add_entry(self, source: str, feedback: str, metadata: Optional[Dict[str, Any]] = None):
        entry = {
            "source": source,
            "feedback": feedback,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
        if metadata:
            entry["metadata"] = metadata
        self.dataset.append(entry)
        logger.debug(f"Added entry from source: {source}")

    def save_to_json(self, file_path: str):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.dataset, f, ensure_ascii=False, indent=4)
        logger.info(f"Dataset saved to {file_path}")

    def load_from_json(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            self.dataset = json.load(f)
        logger.info(f"Dataset loaded from {file_path}")