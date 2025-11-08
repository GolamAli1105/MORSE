"""
Generative Copilot with RAG and MongoDB
========================================

Complete pipeline with:
- Multi-modal generation (Image, Music, Text)
- RAG-enhanced prompts from MongoDB
- Feedback collection (explicit + implicit)
- Model fine-tuning
"""

import asyncio
import logging
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uvicorn
import json
from datetime import datetime

# Configuration
from config import Config

# Core components
from core import DatabaseManager, MongoDBManager, RAGEngine

# Generators
from generators import ImageGenerator, MusicGenerator, TextGenerator

# Fine-tuning
from Fine_tuning import ImplicitFeedbackCollector, ModelFineTuner

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Generative Copilot API",
    description="Multi-modal content generation with RAG and fine-tuning",
    version="2.0.0"
)

# CORS - Properly configured for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default dev server
        "http://localhost:3000",  # Alternative React port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "*"  # Allow all for development (remove in production)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Initialize components
logger.info("🚀 Initializing Generative Copilot...")

# Databases
db = DatabaseManager(Config.SQLITE_DB_PATH)
mongo = MongoDBManager(Config.MONGODB_URI, Config.MONGODB_DB_NAME)
rag_engine = RAGEngine(mongo)

# Feedback system
feedback_collector = ImplicitFeedbackCollector(db)

# Generators
image_gen = ImageGenerator(Config.get_model_config("image"))
music_gen = MusicGenerator(Config.get_model_config("music"))
text_gen = TextGenerator(Config.get_model_config("text"))

logger.info("✅ All components initialized")

# Preload all models at startup
logger.info("📥 Preloading all models...")

# Load Text Generator first (smallest and fastest)
try:
    logger.info("Loading Text Generator...")
    text_gen.load_model()
    logger.info("✅ Text Generator loaded")
except Exception as e:
    logger.error(f"❌ Failed to load Text Generator: {e}")

# Load Music Generator second
try:
    logger.info("Loading Music Generator...")
    music_gen.load_model()
    logger.info("✅ Music Generator loaded")
except Exception as e:
    logger.error(f"❌ Failed to load Music Generator: {e}")

# Load Image Generator last (largest)
try:
    logger.info("Loading Image Generator (SDXL)...")
    image_gen.load_model()
    logger.info("✅ Image Generator loaded")
except Exception as e:
    logger.error(f"❌ Failed to load Image Generator: {e}")

logger.info("🎉 All models preloaded and ready!")


# WebSocket Connection Manager for Real-time Updates
class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"✅ WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"❌ WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()


# Request/Response Models
class GenerateRequest(BaseModel):
    user_id: str
    modality: str  # 'image', 'music', 'text'
    prompt: str
    style: Optional[str] = "default"
    use_rag: Optional[bool] = True  # Enable RAG by default
    parameters: Optional[Dict[str, Any]] = {}


class FeedbackRequest(BaseModel):
    user_id: str
    generation_id: str
    content_id: str  # MongoDB ID
    modality: str
    rating: int  # 1-5
    comment: Optional[str] = None


class ImplicitFeedbackRequest(BaseModel):
    user_id: str
    generation_id: str
    content_id: str
    modality: str
    action_type: str
    metadata: Optional[Dict[str, Any]] = {}


class FineTuneRequest(BaseModel):
    user_id: str
    modality: str
    min_samples: Optional[int] = 20


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint - Welcome page"""
    return {
        "message": "🚀 Welcome to Generative Copilot API",
        "version": "2.0.0",
        "status": "running",
        "documentation": "/docs",
        "endpoints": {
            "health": "/health",
            "config": "/config",
            "generate": "/generate",
            "feedback": {
                "explicit": "/feedback/explicit",
                "implicit": "/feedback/implicit"
            },
            "finetune": {
                "start": "/finetune/start",
                "status": "/finetune/status/{job_id}"
            },
            "user": {
                "stats": "/user/{user_id}/stats",
                "best_content": "/user/{user_id}/best-content/{modality}"
            },
            "streaming": {
                "generate": "/generate/stream",
                "websocket": "/ws"
            }
        },
        "features": ["RAG", "MongoDB", "Fine-tuning", "Multi-modal", "WebSocket", "Streaming"]
    }


@app.post("/generate")
async def generate_content(request: GenerateRequest):
    """
    Generate content with RAG enhancement
    
    Flow:
    1. Retrieve similar high-quality content from MongoDB
    2. Enhance prompt with RAG
    3. Generate new content
    4. Store in both SQLite and MongoDB
    5. Track for feedback
    """
    try:
        logger.info(f"📝 Generation request: {request.modality} - {request.prompt[:50]}...")
        
        # Step 1: RAG Enhancement
        rag_result = None
        enhanced_prompt = request.prompt
        
        if request.use_rag:
            rag_result = rag_engine.enhance_prompt_with_rag(
                user_id=request.user_id,
                modality=request.modality,
                prompt=request.prompt,
                style=request.style
            )
            enhanced_prompt = rag_result['enhanced_prompt']
            logger.info(f"✨ RAG enhanced prompt (refs: {rag_result.get('reference_count', 0)})")
        
        # Step 2: Generate content
        if request.modality == "image":
            result = await image_gen.generate(
                prompt=enhanced_prompt,
                style=request.style,
                **request.parameters
            )
        elif request.modality == "music":
            result = await music_gen.generate(
                prompt=enhanced_prompt,
                style=request.style,
                **request.parameters
            )
        elif request.modality == "text":
            result = await text_gen.generate(
                prompt=enhanced_prompt,
                style=request.style,
                **request.parameters
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid modality")
        
        # Step 3: Store in MongoDB
        content_id = mongo.store_generated_content(
            user_id=request.user_id,
            modality=request.modality,
            prompt=request.prompt,
            content=result.get('image_data') or result.get('audio_data') or result.get('text'),
            metadata={
                'style': request.style,
                'parameters': result.get('parameters', {}),
                'model_used': result.get('model_used'),
                'generation_time': result.get('generation_time'),
                'rag_used': request.use_rag,
                'rag_references': rag_result.get('reference_count', 0) if rag_result else 0
            }
        )
        
        # Step 4: Create session and track in SQLite
        session_id = db.create_chat_session(
            request.user_id,
            f"{request.modality} generation"
        )
        
        generation_id = feedback_collector.track_generation(
            user_id=request.user_id,
            session_id=session_id,
            modality=request.modality,
            prompt=request.prompt,
            content=result.get('image_data') or result.get('audio_data') or result.get('text'),
            style=request.style,
            model_used=result.get('model_used'),
            generation_params=result.get('parameters', {})
        )
        
        # Step 5: Prepare response (remove non-serializable objects)
        response = {
            **result,
            "generation_id": generation_id,
            "content_id": content_id,
            "session_id": session_id,
            "rag_enhanced": request.use_rag,
            "rag_info": rag_result if rag_result else None
        }
        
        # Remove PIL Image object if present (not JSON serializable)
        if 'image_pil' in response:
            del response['image_pil']
        
        # Remove numpy arrays if present (not JSON serializable)
        if 'audio_array' in response:
            del response['audio_array']
        
        logger.info(f"✅ Generation complete: {generation_id}")
        return response
        
    except Exception as e:
        logger.error(f"❌ Generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback/explicit")
async def submit_explicit_feedback(request: FeedbackRequest):
    """Submit explicit user feedback and update MongoDB"""
    try:
        # Save to SQLite
        feedback_id = db.save_feedback(
            message_id=request.generation_id,
            user_id=request.user_id,
            rating=request.rating,
            comment=request.comment,
            feedback_type="explicit"
        )
        
        # Update MongoDB rating
        mongo.update_content_rating(
            content_id=request.content_id,
            modality=request.modality,
            rating=float(request.rating)
        )
        
        logger.info(f"✅ Feedback saved: {feedback_id} (rating: {request.rating})")
        
        return {
            "feedback_id": feedback_id,
            "message": "Feedback saved successfully",
            "rating": request.rating
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to save feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback/implicit")
async def submit_implicit_feedback(request: ImplicitFeedbackRequest):
    """Track implicit user actions"""
    try:
        # Track in SQLite
        if request.action_type in ['download', 'save', 'share', 'use']:
            feedback_collector.track_positive_action(
                generation_id=request.generation_id,
                action_type=request.action_type,
                metadata=request.metadata
            )
            # Update MongoDB with high rating
            mongo.update_content_rating(
                content_id=request.content_id,
                modality=request.modality,
                rating=5.0
            )
            
        elif request.action_type in ['regenerate', 'delete', 'skip']:
            feedback_collector.track_negative_action(
                generation_id=request.generation_id,
                action_type=request.action_type,
                reason=request.metadata.get('reason')
            )
            # Update MongoDB with low rating
            mongo.update_content_rating(
                content_id=request.content_id,
                modality=request.modality,
                rating=2.0
            )
        
        logger.info(f"✅ Implicit feedback tracked: {request.action_type}")
        
        return {"message": "Implicit feedback tracked", "action": request.action_type}
        
    except Exception as e:
        logger.error(f"❌ Failed to track implicit feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/finetune/start")
async def start_finetuning(request: FineTuneRequest, background_tasks: BackgroundTasks):
    """Start model fine-tuning based on user feedback"""
    try:
        finetuner = ModelFineTuner(db, request.modality)
        
        job_id = finetuner.start_finetuning(
            user_id=request.user_id,
            min_samples=request.min_samples
        )
        
        # Run in background
        background_tasks.add_task(finetuner.run_finetuning, job_id)
        
        logger.info(f"🔧 Fine-tuning job started: {job_id}")
        
        return {
            "job_id": job_id,
            "status": "started",
            "message": "Fine-tuning job started in background"
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to start fine-tuning: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/finetune/status/{job_id}")
async def get_finetuning_status(job_id: str):
    """Get fine-tuning job status"""
    try:
        job = db.get_finetuning_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return {
            "job_id": job_id,
            "status": job['job_status'],
            "progress": job['progress'],
            "started_at": job['started_at'],
            "completed_at": job['completed_at'],
            "error_message": job['error_message']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}/stats")
async def get_user_stats(user_id: str):
    """Get comprehensive user statistics"""
    try:
        user = db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        feedback_stats = db.get_user_feedback_stats(user_id)
        finetuning_stats = db.get_finetuning_stats(user_id)
        
        # Get RAG insights from MongoDB
        image_insights = rag_engine.get_content_insights(user_id, "image")
        music_insights = rag_engine.get_content_insights(user_id, "music")
        text_insights = rag_engine.get_content_insights(user_id, "text")
        
        return {
            "user": user,
            "feedback": feedback_stats,
            "finetuning": finetuning_stats,
            "content_insights": {
                "image": image_insights,
                "music": music_insights,
                "text": text_insights
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get user stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/user/{user_id}/best-content/{modality}")
async def get_best_content(user_id: str, modality: str, limit: int = 10):
    """Get user's best content from MongoDB"""
    try:
        best_content = mongo.get_user_best_content(
            user_id=user_id,
            modality=modality,
            limit=limit
        )
        
        return {
            "user_id": user_id,
            "modality": modality,
            "count": len(best_content),
            "content": best_content
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get best content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/config")
async def get_config():
    """Get application configuration"""
    return Config.to_dict()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": ["RAG", "MongoDB", "Fine-tuning", "Multi-modal", "WebSocket", "Streaming"]
    }


@app.get("/favicon.ico")
async def favicon():
    """Favicon endpoint to prevent 404 errors"""
    return JSONResponse(content={}, status_code=204)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates
    
    Sends real-time updates about:
    - Generation progress
    - Fine-tuning status
    - System notifications
    """
    await manager.connect(websocket)
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Echo back with timestamp
            response = {
                "type": "echo",
                "data": message,
                "timestamp": datetime.now().isoformat()
            }
            await manager.send_personal_message(response, websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.post("/generate/stream")
async def generate_content_stream(request: GenerateRequest):
    """
    Generate content with streaming response for real-time updates
    
    Returns a stream of JSON objects showing generation progress
    """
    async def generate_stream():
        try:
            # Send start event
            yield json.dumps({
                "event": "start",
                "message": "Starting generation...",
                "timestamp": datetime.now().isoformat()
            }) + "\n"
            
            # RAG Enhancement
            if request.use_rag:
                yield json.dumps({
                    "event": "rag",
                    "message": "Enhancing prompt with RAG...",
                    "timestamp": datetime.now().isoformat()
                }) + "\n"
                
                rag_result = rag_engine.enhance_prompt_with_rag(
                    user_id=request.user_id,
                    modality=request.modality,
                    prompt=request.prompt,
                    style=request.style
                )
                enhanced_prompt = rag_result['enhanced_prompt']
                
                yield json.dumps({
                    "event": "rag_complete",
                    "message": f"RAG enhanced with {rag_result.get('reference_count', 0)} references",
                    "timestamp": datetime.now().isoformat()
                }) + "\n"
            else:
                enhanced_prompt = request.prompt
            
            # Generation
            yield json.dumps({
                "event": "generating",
                "message": f"Generating {request.modality} content...",
                "timestamp": datetime.now().isoformat()
            }) + "\n"
            
            # Generate based on modality
            if request.modality == "image":
                result = await image_gen.generate(
                    prompt=enhanced_prompt,
                    style=request.style,
                    **request.parameters
                )
            elif request.modality == "music":
                result = await music_gen.generate(
                    prompt=enhanced_prompt,
                    style=request.style,
                    **request.parameters
                )
            elif request.modality == "text":
                result = await text_gen.generate(
                    prompt=enhanced_prompt,
                    style=request.style,
                    **request.parameters
                )
            else:
                raise ValueError("Invalid modality")
            
            # Store in MongoDB
            yield json.dumps({
                "event": "storing",
                "message": "Storing content...",
                "timestamp": datetime.now().isoformat()
            }) + "\n"
            
            content_id = mongo.store_generated_content(
                user_id=request.user_id,
                modality=request.modality,
                prompt=request.prompt,
                content=result.get('image_data') or result.get('audio_data') or result.get('text'),
                metadata={
                    'style': request.style,
                    'parameters': result.get('parameters', {}),
                    'model_used': result.get('model_used'),
                    'generation_time': result.get('generation_time'),
                    'rag_used': request.use_rag
                }
            )
            
            # Track in SQLite
            session_id = db.create_chat_session(request.user_id, f"{request.modality} generation")
            generation_id = feedback_collector.track_generation(
                user_id=request.user_id,
                session_id=session_id,
                modality=request.modality,
                prompt=request.prompt,
                content=result.get('image_data') or result.get('audio_data') or result.get('text'),
                style=request.style,
                model_used=result.get('model_used'),
                generation_params=result.get('parameters', {})
            )
            
            # Send complete event with result
            yield json.dumps({
                "event": "complete",
                "message": "Generation complete!",
                "data": {
                    **result,
                    "generation_id": generation_id,
                    "content_id": content_id,
                    "session_id": session_id
                },
                "timestamp": datetime.now().isoformat()
            }) + "\n"
            
        except Exception as e:
            yield json.dumps({
                "event": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }) + "\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    mongo.close()
    logger.info("Application shutdown complete")


if __name__ == "__main__":
    # Create default user if not exists
    existing_user = db.get_user("demo_user")
    if not existing_user:
        try:
            user_id = db.create_user("demo_user", "demo@example.com")
            logger.info(f"✅ Created demo user: {user_id}")
        except Exception as e:
            logger.warning(f"Could not create demo user: {e}")
    else:
        logger.info("✅ Demo user ready")
    
    # Start server
    logger.info("🚀 Starting Generative Copilot API...")
    uvicorn.run(
        app,
        host=Config.API_HOST,
        port=Config.API_PORT,
        log_level="info"
    )
