# 🚀 Generative Copilot - Complete Setup Guide

## 📋 Prerequisites

1. **Python 3.10+**
2. **MongoDB** (local or Atlas)
3. **CUDA** (optional, for GPU acceleration)

## 🔧 Installation Steps

### 1. Clone and Setup Environment

```bash
# Create virtual environment
python -m venv myenv

# Activate (Windows)
myenv\Scripts\activate

# Activate (Linux/Mac)
source myenv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup MongoDB

**Option A: Local MongoDB**
```bash
# Download and install MongoDB Community Edition
# https://www.mongodb.com/try/download/community

# Start MongoDB service
mongod --dbpath=./data/mongodb
```

**Option B: MongoDB Atlas (Cloud)**
```bash
# Sign up at https://www.mongodb.com/cloud/atlas
# Create a free cluster
# Get connection string
```

### 4. Configure Environment

```bash
# Copy environment template
copy .env.example .env

# Edit .env with your settings
notepad .env
```

**Key configurations:**
```env
MONGODB_URI=mongodb://localhost:27017/
# OR for Atlas:
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/

DEVICE=cuda  # or cpu
```

### 5. Test the Pipeline

```bash
python test_pipeline.py
```

Expected output:
```
🧪 Starting Pipeline Test...
1️⃣ Testing Database Connections...
✅ SQLite connected
✅ MongoDB connected
✅ RAG Engine initialized
...
✅ Pipeline Test Complete!
```

### 6. Run the Application

```bash
python app.py
```

The API will be available at: `http://localhost:8000`

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎯 Quick Test

### Generate Text Content

```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "modality": "text",
    "prompt": "Write a blog post about AI",
    "style": "blog_post",
    "use_rag": true
  }'
```

### Submit Feedback

```bash
curl -X POST "http://localhost:8000/feedback/explicit" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo_user",
    "generation_id": "your_generation_id",
    "content_id": "your_content_id",
    "modality": "text",
    "rating": 5,
    "comment": "Great content!"
  }'
```

## 🔍 Troubleshooting

### MongoDB Connection Issues

```bash
# Check if MongoDB is running
mongosh

# Or check service status (Windows)
sc query MongoDB

# Or check service status (Linux)
systemctl status mongod
```

### CUDA/GPU Issues

```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# If False, set DEVICE=cpu in .env
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 📊 Project Structure

```
generative-copilot/
├── app.py                    # Main application
├── config.py                 # Configuration
├── test_pipeline.py          # Testing script
├── requirements.txt          # Dependencies
├── .env                      # Environment variables
│
├── core/                     # Core functionality
│   ├── database.py           # SQLite manager
│   ├── mongodb_manager.py    # MongoDB manager
│   └── rag_engine.py         # RAG system
│
├── generators/               # Content generators
│   ├── image_generator.py    # Image generation
│   ├── music_generator.py    # Music generation
│   └── text_generator.py     # Text generation
│
└── Fine-tuning/              # Model fine-tuning
    ├── implicit_feedback_collector.py
    ├── feedback_dataset_builder.py
    └── model_finetuner.py
```

## 🎨 Features

✅ **Multi-Modal Generation**
- Images (FLUX.1-schnell)
- Music (MusicGen)
- Text (Mistral-7B)

✅ **RAG Enhancement**
- Retrieves similar high-quality content
- Enhances prompts automatically
- Learns from user preferences

✅ **Feedback System**
- Explicit ratings (1-5 stars)
- Implicit actions (download, save, regenerate)
- Automatic quality tracking

✅ **Model Fine-Tuning**
- Adapts to user preferences
- Uses feedback data
- Improves over time

## 🚀 Next Steps

1. Generate some content
2. Provide feedback (ratings or actions)
3. Generate more content (RAG will enhance prompts)
4. After 20+ feedback items, start fine-tuning
5. Use fine-tuned models for personalized content

## 📞 Support

For issues or questions:
1. Check logs in console
2. Review MongoDB connection
3. Verify all dependencies installed
4. Check .env configuration

## 🎉 You're Ready!

Start generating amazing content with AI! 🚀
