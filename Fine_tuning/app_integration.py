"""
Integration code for app.py
===========================

Add this code to app.py to enable automated fine-tuning
"""

# ADD TO IMPORTS SECTION:
"""
from Fine_tuning.automated_finetuning_system import get_finetuning_system
"""

# ADD AFTER INITIALIZING OTHER COMPONENTS:
"""
# Initialize automated fine-tuning system
logger.info("🔧 Initializing automated fine-tuning system...")
finetuning_system = get_finetuning_system(mongo, db)
logger.info("✅ Automated fine-tuning system initialized and scheduler started")
"""

# ADD NEW PYDANTIC MODELS:
"""
class FeedbackRequest(BaseModel):
    generation_id: str
    user_id: str
    feedback_type: str  # 'explicit', 'implicit_positive', 'implicit_negative', 'correction'
    rating: Optional[int] = None
    comment: Optional[str] = None
    action: Optional[str] = None  # 'download', 'save', 'share', 'regenerate', etc.
    metadata: Optional[Dict[str, Any]] = None
"""

# MODIFY THE /generate ENDPOINT TO STORE OUTPUTS:
"""
@app.post("/generate")
async def generate_content(request: GenerateRequest):
    # ... existing code ...
    
    # After successful generation, store in MongoDB for training
    try:
        generation_id = await finetuning_system.store_generation_output(
            user_id=request.user_id or "anonymous",
            session_id=request.session_id or "default",
            modality=content_type,
            prompt=prompt,
            enhanced_prompt=result.get('enhanced_prompt', prompt),
            output_data=result.get('image_data') or result.get('audio_data') or result.get('text'),
            style=style,
            model_used=result.get('model_used', 'unknown'),
            generation_params=result.get('parameters', {}),
            generation_time=result.get('generation_time', 0)
        )
        
        # Add generation_id to response
        result['generation_id'] = generation_id
        
    except Exception as e:
        logger.error(f"Failed to store generation for training: {e}")
    
    return result
"""

# ADD NEW FEEDBACK ENDPOINT:
"""
@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    '''
    Submit user feedback for a generation
    
    This feedback is used to improve the models through fine-tuning
    '''
    try:
        await finetuning_system.store_user_feedback(
            generation_id=feedback.generation_id,
            user_id=feedback.user_id,
            feedback_type=feedback.feedback_type,
            rating=feedback.rating,
            comment=feedback.comment,
            action=feedback.action,
            metadata=feedback.metadata
        )
        
        return {
            "status": "success",
            "message": "Feedback stored successfully",
            "generation_id": feedback.generation_id
        }
        
    except Exception as e:
        logger.error(f"Failed to store feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))
"""

# ADD FINE-TUNING STATUS ENDPOINT:
"""
@app.get("/finetuning/status")
async def get_finetuning_status():
    '''Get status of automated fine-tuning system'''
    try:
        status = {
            "scheduler_running": finetuning_system.is_running,
            "interval_minutes": finetuning_system.interval_minutes,
            "min_samples_required": finetuning_system.min_samples,
            "last_finetuning": finetuning_system.last_finetuning,
            "finetuned_models": finetuning_system.finetuned_models,
            "training_data_counts": {
                "image": finetuning_system._count_new_training_samples("image"),
                "music": finetuning_system._count_new_training_samples("music"),
                "text": finetuning_system._count_new_training_samples("text")
            }
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get fine-tuning status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
"""

# ADD MANUAL FINE-TUNING TRIGGER:
"""
@app.post("/finetuning/trigger/{modality}")
async def trigger_manual_finetuning(modality: str):
    '''Manually trigger fine-tuning for a specific modality'''
    try:
        if modality not in ['image', 'music', 'text']:
            raise HTTPException(status_code=400, detail="Invalid modality")
        
        await finetuning_system.trigger_finetuning(modality)
        
        return {
            "status": "success",
            "message": f"Fine-tuning triggered for {modality}",
            "modality": modality
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger fine-tuning: {e}")
        raise HTTPException(status_code=500, detail=str(e))
"""

# ADD SHUTDOWN HANDLER:
"""
@app.on_event("shutdown")
async def shutdown_event():
    '''Cleanup on shutdown'''
    logger.info("🛑 Shutting down...")
    
    # Stop fine-tuning scheduler
    finetuning_system.stop_scheduler()
    
    # Close database connections
    mongo.close()
    
    logger.info("✅ Shutdown complete")
"""
