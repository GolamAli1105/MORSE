"""
LangSmith Integration for Model Monitoring
==========================================

Tracks and monitors all model generations:
- Text, Image, Music generation
- Performance metrics
- User feedback
- Fine-tuning data
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# Try to import LangSmith
try:
    from langsmith import Client
    from langsmith.run_helpers import traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    logger.warning("LangSmith not available. Install with: pip install langsmith")


class LangSmithMonitor:
    """
    LangSmith integration for monitoring model performance
    
    Features:
    - Track all generations
    - Monitor performance metrics
    - Collect user feedback
    - Analyze model behavior
    - Support fine-tuning decisions
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.enabled = False
        self.client = None
        
        # Check if LangSmith is configured
        if LANGSMITH_AVAILABLE and os.getenv("LANGCHAIN_TRACING_V2") == "true":
            try:
                self.client = Client()
                self.enabled = True
                self.project_name = os.getenv("LANGCHAIN_PROJECT", "generative-copilot")
                self.logger.info("✅ LangSmith monitoring enabled")
            except Exception as e:
                self.logger.warning(f"LangSmith initialization failed: {e}")
                self.enabled = False
        else:
            self.logger.info("ℹ️ LangSmith monitoring disabled (set LANGCHAIN_TRACING_V2=true to enable)")
    
    def track_generation(
        self,
        modality: str,
        prompt: str,
        output: Any,
        metadata: Dict[str, Any]
    ) -> Optional[str]:
        """
        Track a generation event
        
        Args:
            modality: Type (text, image, music)
            prompt: Input prompt
            output: Generated output
            metadata: Additional info (model, params, etc.)
        
        Returns:
            Run ID for tracking
        """
        if not self.enabled:
            return None
        
        try:
            # Create run
            run = self.client.create_run(
                name=f"{modality}_generation",
                run_type="llm" if modality == "text" else "chain",
                inputs={"prompt": prompt},
                outputs={"result": str(output)[:1000]},  # Truncate large outputs
                project_name=self.project_name,
                extra={
                    "modality": modality,
                    "model": metadata.get("model_used", "unknown"),
                    "generation_time": metadata.get("generation_time", 0),
                    "parameters": metadata.get("parameters", {}),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            self.logger.info(f"📊 Tracked {modality} generation: {run.id}")
            return str(run.id)
            
        except Exception as e:
            self.logger.error(f"Failed to track generation: {e}")
            return None
    
    def track_feedback(
        self,
        run_id: str,
        feedback_type: str,
        score: Optional[float] = None,
        comment: Optional[str] = None
    ):
        """
        Track user feedback for a generation
        
        Args:
            run_id: Run ID from track_generation
            feedback_type: Type of feedback
            score: Numerical score (0-1)
            comment: Text feedback
        """
        if not self.enabled or not run_id:
            return
        
        try:
            self.client.create_feedback(
                run_id=run_id,
                key=feedback_type,
                score=score,
                comment=comment
            )
            
            self.logger.info(f"💬 Tracked feedback for run: {run_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to track feedback: {e}")
    
    def get_run_stats(self, modality: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for runs
        
        Args:
            modality: Filter by modality (optional)
        
        Returns:
            Statistics dictionary
        """
        if not self.enabled:
            return {"error": "LangSmith not enabled"}
        
        try:
            # Get runs from project
            runs = list(self.client.list_runs(
                project_name=self.project_name,
                limit=100
            ))
            
            # Filter by modality if specified
            if modality:
                runs = [r for r in runs if r.extra.get("modality") == modality]
            
            # Calculate stats
            total_runs = len(runs)
            avg_time = sum(r.extra.get("generation_time", 0) for r in runs) / total_runs if total_runs > 0 else 0
            
            return {
                "total_runs": total_runs,
                "average_generation_time": avg_time,
                "modality": modality or "all"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}


# Global instance
_langsmith_monitor = None


def get_langsmith_monitor() -> LangSmithMonitor:
    """Get or create global LangSmith monitor instance"""
    global _langsmith_monitor
    
    if _langsmith_monitor is None:
        _langsmith_monitor = LangSmithMonitor()
    
    return _langsmith_monitor


# Decorator for tracking functions
def track_generation(modality: str):
    """
    Decorator to automatically track generation functions
    
    Usage:
        @track_generation("text")
        async def generate_text(...):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            monitor = get_langsmith_monitor()
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Track if enabled
            if monitor.enabled and isinstance(result, dict):
                prompt = result.get("prompt", "")
                output = result.get("text") or result.get("image_data") or result.get("audio_data")
                metadata = {
                    "model_used": result.get("model_used", "unknown"),
                    "generation_time": result.get("generation_time", 0),
                    "parameters": result.get("parameters", {})
                }
                
                run_id = monitor.track_generation(modality, prompt, output, metadata)
                result["langsmith_run_id"] = run_id
            
            return result
        
        return wrapper
    return decorator
