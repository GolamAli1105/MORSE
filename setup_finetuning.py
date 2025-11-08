"""
Setup Script for Automated Fine-Tuning System
==============================================

Run this script to set up the automated fine-tuning system.
"""

import sys
import subprocess
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    dependencies = [
        "schedule",
        "pymongo",
        "motor"
    ]
    
    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"✅ Installed {dep}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
            return False
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "data/finetuning",
        "models/finetuned"
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created {dir_path}")

def show_integration_instructions():
    """Show integration instructions"""
    print("\n" + "="*60)
    print("🎯 INTEGRATION INSTRUCTIONS")
    print("="*60)
    
    print("""
1. Add to app.py imports:
   
   from Fine_tuning.automated_finetuning_system import get_finetuning_system

2. Initialize after other components:
   
   # Initialize automated fine-tuning system
   finetuning_system = get_finetuning_system(mongo, db)

3. Add Pydantic model:
   
   class FeedbackRequest(BaseModel):
       generation_id: str
       user_id: str
       feedback_type: str
       rating: Optional[int] = None
       comment: Optional[str] = None
       action: Optional[str] = None
       metadata: Optional[Dict[str, Any]] = None

4. Modify /generate endpoint to store outputs:
   
   # After successful generation
   generation_id = await finetuning_system.store_generation_output(
       user_id=request.user_id or "anonymous",
       session_id=request.session_id or "default",
       modality=content_type,
       prompt=prompt,
       enhanced_prompt=result.get('enhanced_prompt', prompt),
       output_data=result.get('image_data') or result.get('audio_data'),
       style=style,
       model_used=result.get('model_used', 'unknown'),
       generation_params=result.get('parameters', {}),
       generation_time=result.get('generation_time', 0)
   )
   result['generation_id'] = generation_id

5. Add feedback endpoint:
   
   @app.post("/feedback")
   async def submit_feedback(feedback: FeedbackRequest):
       await finetuning_system.store_user_feedback(
           generation_id=feedback.generation_id,
           user_id=feedback.user_id,
           feedback_type=feedback.feedback_type,
           rating=feedback.rating,
           comment=feedback.comment,
           action=feedback.action,
           metadata=feedback.metadata
       )
       return {"status": "success"}

6. Add status endpoint:
   
   @app.get("/finetuning/status")
   async def get_finetuning_status():
       return {
           "scheduler_running": finetuning_system.is_running,
           "interval_minutes": finetuning_system.interval_minutes,
           "last_finetuning": finetuning_system.last_finetuning,
           "finetuned_models": finetuning_system.finetuned_models
       }

7. Add shutdown handler:
   
   @app.on_event("shutdown")
   async def shutdown_event():
       finetuning_system.stop_scheduler()
       mongo.close()

See Fine_tuning/app_integration.py for complete code!
See AUTOMATED_FINETUNING_GUIDE.md for full documentation!
""")

def main():
    """Main setup function"""
    print("🚀 Setting up Automated Fine-Tuning System")
    print("="*60)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Failed to install dependencies")
        return
    
    # Create directories
    create_directories()
    
    # Show instructions
    show_integration_instructions()
    
    print("\n" + "="*60)
    print("✅ Setup complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Follow the integration instructions above")
    print("2. Restart your backend server")
    print("3. The fine-tuning scheduler will start automatically")
    print("4. Check status at: GET /finetuning/status")
    print("\n📚 Read AUTOMATED_FINETUNING_GUIDE.md for full documentation")

if __name__ == "__main__":
    main()
