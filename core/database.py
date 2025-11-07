"""
Database Management System
=========================

Handles user-specific chat storage, model tracking, and fine-tuning data.
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import hashlib
import uuid

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all database operations for the AI engine"""
    
    def __init__(self, db_path: str = "data/ai_engine.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Users table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        username TEXT UNIQUE,
                        email TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        preferences TEXT,  -- JSON string
                        total_chats INTEGER DEFAULT 0,
                        total_feedback INTEGER DEFAULT 0
                    )
                """)
                
                # Chat sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_sessions (
                        session_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        title TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        message_count INTEGER DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # Chat messages table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        message_id TEXT PRIMARY KEY,
                        session_id TEXT,
                        user_id TEXT,
                        modality TEXT,
                        role TEXT,  -- 'user' or 'assistant'
                        content TEXT,
                        prompt TEXT,
                        style TEXT,
                        generation_params TEXT,  -- JSON string
                        model_used TEXT,
                        generation_time REAL,
                        quality_score REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES chat_sessions (session_id),
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # Feedback table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS feedback (
                        feedback_id TEXT PRIMARY KEY,
                        message_id TEXT,
                        user_id TEXT,
                        rating INTEGER,
                        comment TEXT,
                        feedback_type TEXT,  -- 'rating', 'correction', 'preference'
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        processed_for_training BOOLEAN DEFAULT FALSE,
                        FOREIGN KEY (message_id) REFERENCES chat_messages (message_id),
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                # Models table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS models (
                        model_id TEXT PRIMARY KEY,
                        model_name TEXT,
                        modality TEXT,
                        model_type TEXT,  -- 'base', 'fine_tuned', 'user_specific'
                        model_path TEXT,
                        download_url TEXT,
                        file_size INTEGER,
                        download_status TEXT,  -- 'pending', 'downloading', 'completed', 'failed'
                        download_progress REAL DEFAULT 0.0,
                        is_active BOOLEAN DEFAULT FALSE,
                        user_id TEXT,  -- NULL for global models
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_used TIMESTAMP,
                        usage_count INTEGER DEFAULT 0,
                        performance_metrics TEXT  -- JSON string
                    )
                """)
                
                # Fine-tuning jobs table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS finetuning_jobs (
                        job_id TEXT PRIMARY KEY,
                        user_id TEXT,
                        modality TEXT,
                        base_model_id TEXT,
                        training_data_path TEXT,
                        job_status TEXT,  -- 'pending', 'running', 'completed', 'failed'
                        progress REAL DEFAULT 0.0,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        error_message TEXT,
                        output_model_id TEXT,
                        training_params TEXT,  -- JSON string
                        performance_improvement TEXT,  -- JSON string
                        FOREIGN KEY (user_id) REFERENCES users (user_id),
                        FOREIGN KEY (base_model_id) REFERENCES models (model_id)
                    )
                """)
                
                # Model downloads table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS model_downloads (
                        download_id TEXT PRIMARY KEY,
                        model_id TEXT,
                        user_id TEXT,
                        download_url TEXT,
                        file_path TEXT,
                        file_size INTEGER,
                        downloaded_bytes INTEGER DEFAULT 0,
                        download_speed REAL,
                        status TEXT,  -- 'pending', 'downloading', 'completed', 'failed', 'paused'
                        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        error_message TEXT,
                        FOREIGN KEY (model_id) REFERENCES models (model_id),
                        FOREIGN KEY (user_id) REFERENCES users (user_id)
                    )
                """)
                
                conn.commit()
                logger.info("✅ Database initialized successfully")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    # User Management
    def create_user(self, username: str, email: str = None, preferences: Dict = None) -> str:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (user_id, username, email, preferences)
                    VALUES (?, ?, ?, ?)
                """, (user_id, username, email, json.dumps(preferences or {})))
                conn.commit()
                
                logger.info(f"✅ User created: {username} ({user_id})")
                return user_id
                
        except Exception as e:
            logger.error(f"❌ Failed to create user: {e}")
            raise
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM users WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    user_data = dict(zip(columns, row))
                    user_data['preferences'] = json.loads(user_data['preferences'] or '{}')
                    return user_data
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get user: {e}")
            return None
    
    def update_user_activity(self, user_id: str):
        """Update user's last activity timestamp"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (user_id,))
                conn.commit()
                
        except Exception as e:
            logger.error(f"❌ Failed to update user activity: {e}")
    
    # Chat Management
    def create_chat_session(self, user_id: str, title: str = None) -> str:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        
        if not title:
            title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO chat_sessions (session_id, user_id, title)
                    VALUES (?, ?, ?)
                """, (session_id, user_id, title))
                conn.commit()
                
                logger.info(f"✅ Chat session created: {session_id}")
                return session_id
                
        except Exception as e:
            logger.error(f"❌ Failed to create chat session: {e}")
            raise
    
    def save_chat_message(
        self,
        session_id: str,
        user_id: str,
        modality: str,
        role: str,
        content: str,
        prompt: str = None,
        style: str = None,
        generation_params: Dict = None,
        model_used: str = None,
        generation_time: float = None,
        quality_score: float = None
    ) -> str:
        """Save a chat message"""
        message_id = str(uuid.uuid4())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO chat_messages (
                        message_id, session_id, user_id, modality, role, content,
                        prompt, style, generation_params, model_used,
                        generation_time, quality_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    message_id, session_id, user_id, modality, role, content,
                    prompt, style, json.dumps(generation_params or {}),
                    model_used, generation_time, quality_score
                ))
                
                # Update session message count
                cursor.execute("""
                    UPDATE chat_sessions 
                    SET message_count = message_count + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE session_id = ?
                """, (session_id,))
                
                # Update user chat count
                cursor.execute("""
                    UPDATE users SET total_chats = total_chats + 1
                    WHERE user_id = ?
                """, (user_id,))
                
                conn.commit()
                return message_id
                
        except Exception as e:
            logger.error(f"❌ Failed to save chat message: {e}")
            raise
    
    def get_user_chat_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's chat history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT cm.*, cs.title as session_title
                    FROM chat_messages cm
                    JOIN chat_sessions cs ON cm.session_id = cs.session_id
                    WHERE cm.user_id = ?
                    ORDER BY cm.timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
                
                columns = [desc[0] for desc in cursor.description]
                messages = []
                
                for row in cursor.fetchall():
                    message = dict(zip(columns, row))
                    message['generation_params'] = json.loads(message['generation_params'] or '{}')
                    messages.append(message)
                
                return messages
                
        except Exception as e:
            logger.error(f"❌ Failed to get chat history: {e}")
            return []
    
    def get_chat_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's chat sessions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM chat_sessions
                    WHERE user_id = ?
                    ORDER BY updated_at DESC
                """, (user_id,))
                
                columns = [desc[0] for desc in cursor.description]
                sessions = []
                
                for row in cursor.fetchall():
                    session = dict(zip(columns, row))
                    sessions.append(session)
                
                return sessions
                
        except Exception as e:
            logger.error(f"❌ Failed to get chat sessions: {e}")
            return []
    
    # Feedback Management
    def save_feedback(
        self,
        message_id: str,
        user_id: str,
        rating: int,
        comment: str = None,
        feedback_type: str = "rating"
    ) -> str:
        """Save user feedback"""
        feedback_id = str(uuid.uuid4())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO feedback (feedback_id, message_id, user_id, rating, comment, feedback_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (feedback_id, message_id, user_id, rating, comment, feedback_type))
                
                # Update user feedback count
                cursor.execute("""
                    UPDATE users SET total_feedback = total_feedback + 1
                    WHERE user_id = ?
                """, (user_id,))
                
                conn.commit()
                return feedback_id
                
        except Exception as e:
            logger.error(f"❌ Failed to save feedback: {e}")
            raise
    
    def get_user_feedback_stats(self, user_id: str) -> Dict[str, Any]:
        """Get user's feedback statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get basic stats
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_feedback,
                        AVG(rating) as avg_rating,
                        COUNT(CASE WHEN rating >= 4 THEN 1 END) as high_ratings,
                        COUNT(CASE WHEN rating <= 2 THEN 1 END) as low_ratings
                    FROM feedback
                    WHERE user_id = ?
                """, (user_id,))
                
                stats = dict(zip([desc[0] for desc in cursor.description], cursor.fetchone()))
                
                # Get modality breakdown
                cursor.execute("""
                    SELECT cm.modality, COUNT(*) as count, AVG(f.rating) as avg_rating
                    FROM feedback f
                    JOIN chat_messages cm ON f.message_id = cm.message_id
                    WHERE f.user_id = ?
                    GROUP BY cm.modality
                """, (user_id,))
                
                modality_stats = {}
                for row in cursor.fetchall():
                    modality_stats[row[0]] = {"count": row[1], "avg_rating": row[2]}
                
                stats['modality_breakdown'] = modality_stats
                stats['satisfaction_rate'] = (stats['high_ratings'] / max(stats['total_feedback'], 1)) * 100
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Failed to get feedback stats: {e}")
            return {}
    
    # Model Management
    def register_model(
        self,
        model_name: str,
        modality: str,
        model_type: str,
        model_path: str = None,
        download_url: str = None,
        user_id: str = None
    ) -> str:
        """Register a new model"""
        model_id = str(uuid.uuid4())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO models (
                        model_id, model_name, modality, model_type,
                        model_path, download_url, user_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (model_id, model_name, modality, model_type, model_path, download_url, user_id))
                conn.commit()
                
                logger.info(f"✅ Model registered: {model_name} ({model_id})")
                return model_id
                
        except Exception as e:
            logger.error(f"❌ Failed to register model: {e}")
            raise    

    def get_available_models(self, modality: str = None, user_id: str = None) -> List[Dict[str, Any]]:
        """Get available models, optionally filtered by modality and user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM models WHERE 1=1"
                params = []
                
                if modality:
                    query += " AND modality = ?"
                    params.append(modality)
                
                if user_id:
                    query += " AND (user_id = ? OR user_id IS NULL)"
                    params.append(user_id)
                
                query += " ORDER BY created_at DESC"
                
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                models = []
                
                for row in cursor.fetchall():
                    model = dict(zip(columns, row))
                    model['performance_metrics'] = json.loads(model['performance_metrics'] or '{}')
                    models.append(model)
                
                return models
                
        except Exception as e:
            logger.error(f"❌ Failed to get available models: {e}")
            return []
    
    # Fine-tuning Management
    def create_finetuning_job(
        self,
        user_id: str,
        modality: str,
        base_model_id: str,
        training_data_path: str,
        training_params: Dict = None
    ) -> str:
        """Create a new fine-tuning job"""
        job_id = str(uuid.uuid4())
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO finetuning_jobs (
                        job_id, user_id, modality, base_model_id,
                        training_data_path, job_status, training_params
                    ) VALUES (?, ?, ?, ?, ?, 'pending', ?)
                """, (job_id, user_id, modality, base_model_id, training_data_path, 
                      json.dumps(training_params or {})))
                conn.commit()
                
                logger.info(f"✅ Fine-tuning job created: {job_id}")
                return job_id
                
        except Exception as e:
            logger.error(f"❌ Failed to create fine-tuning job: {e}")
            raise
    
    def update_finetuning_status(
        self,
        job_id: str,
        status: str,
        progress: float = None,
        error_message: str = None
    ) -> bool:
        """Update fine-tuning job status and progress"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build update query dynamically
                updates = ["job_status = ?"]
                params = [status]
                
                if progress is not None:
                    updates.append("progress = ?")
                    params.append(progress)
                
                if error_message:
                    updates.append("error_message = ?")
                    params.append(error_message)
                
                if status == 'running' and not self.get_finetuning_job(job_id).get('started_at'):
                    updates.append("started_at = CURRENT_TIMESTAMP")
                elif status in ['completed', 'failed']:
                    updates.append("completed_at = CURRENT_TIMESTAMP")
                
                params.append(job_id)
                
                cursor.execute(f"""
                    UPDATE finetuning_jobs 
                    SET {', '.join(updates)}
                    WHERE job_id = ?
                """, params)
                
                conn.commit()
                logger.info(f"✅ Fine-tuning job {job_id} status updated to: {status}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to update fine-tuning status: {e}")
            return False
    
    def get_finetuning_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get fine-tuning job details"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT fj.*, m.model_name as base_model_name
                    FROM finetuning_jobs fj
                    LEFT JOIN models m ON fj.base_model_id = m.model_id
                    WHERE fj.job_id = ?
                """, (job_id,))
                
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    job = dict(zip(columns, row))
                    job['training_params'] = json.loads(job['training_params'] or '{}')
                    job['performance_improvement'] = json.loads(job['performance_improvement'] or '{}')
                    return job
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get fine-tuning job: {e}")
            return None
    
    def get_user_finetuning_jobs(self, user_id: str, status: str = None) -> List[Dict[str, Any]]:
        """Get user's fine-tuning jobs, optionally filtered by status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT fj.*, m.model_name as base_model_name
                    FROM finetuning_jobs fj
                    LEFT JOIN models m ON fj.base_model_id = m.model_id
                    WHERE fj.user_id = ?
                """
                params = [user_id]
                
                if status:
                    query += " AND fj.job_status = ?"
                    params.append(status)
                
                query += " ORDER BY fj.started_at DESC"
                
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                jobs = []
                
                for row in cursor.fetchall():
                    job = dict(zip(columns, row))
                    job['training_params'] = json.loads(job['training_params'] or '{}')
                    job['performance_improvement'] = json.loads(job['performance_improvement'] or '{}')
                    jobs.append(job)
                
                return jobs
                
        except Exception as e:
            logger.error(f"❌ Failed to get user fine-tuning jobs: {e}")
            return []
    
    def is_finetuning_done(self, job_id: str) -> Tuple[bool, str]:
        """Check if fine-tuning job is completed (returns status and job state)"""
        job = self.get_finetuning_job(job_id)
        if not job:
            return False, "job_not_found"
        
        status = job['job_status']
        if status == 'completed':
            return True, "completed"
        elif status == 'failed':
            return True, "failed"
        elif status in ['pending', 'running']:
            return False, status
        else:
            return False, "unknown"
    
    def is_finetuning_working(self, job_id: str) -> Tuple[bool, float]:
        """Check if fine-tuning job is currently running (returns working status and progress)"""
        job = self.get_finetuning_job(job_id)
        if not job:
            return False, 0.0
        
        is_working = job['job_status'] == 'running'
        progress = job['progress'] or 0.0
        
        return is_working, progress
    
    def get_finetuning_stats(self, user_id: str = None) -> Dict[str, Any]:
        """Get fine-tuning statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                base_query = "FROM finetuning_jobs"
                params = []
                
                if user_id:
                    base_query += " WHERE user_id = ?"
                    params.append(user_id)
                
                # Get overall stats
                cursor.execute(f"""
                    SELECT 
                        COUNT(*) as total_jobs,
                        COUNT(CASE WHEN job_status = 'completed' THEN 1 END) as completed_jobs,
                        COUNT(CASE WHEN job_status = 'failed' THEN 1 END) as failed_jobs,
                        COUNT(CASE WHEN job_status = 'running' THEN 1 END) as running_jobs,
                        COUNT(CASE WHEN job_status = 'pending' THEN 1 END) as pending_jobs,
                        AVG(CASE WHEN job_status = 'running' THEN progress END) as avg_progress
                    {base_query}
                """, params)
                
                stats = dict(zip([desc[0] for desc in cursor.description], cursor.fetchone()))
                
                # Calculate success rate
                total = stats['total_jobs']
                if total > 0:
                    stats['success_rate'] = (stats['completed_jobs'] / total) * 100
                    stats['failure_rate'] = (stats['failed_jobs'] / total) * 100
                else:
                    stats['success_rate'] = 0
                    stats['failure_rate'] = 0
                
                # Get modality breakdown
                cursor.execute(f"""
                    SELECT modality, COUNT(*) as count, 
                           COUNT(CASE WHEN job_status = 'completed' THEN 1 END) as completed
                    {base_query}
                    GROUP BY modality
                """, params)
                
                modality_stats = {}
                for row in cursor.fetchall():
                    modality_stats[row[0]] = {
                        "total": row[1],
                        "completed": row[2],
                        "success_rate": (row[2] / row[1]) * 100 if row[1] > 0 else 0
                    }
                
                stats['modality_breakdown'] = modality_stats
                return stats
                
        except Exception as e:
            logger.error(f"❌ Failed to get fine-tuning stats: {e}")
            return {}
    
    def complete_finetuning_job(
        self,
        job_id: str,
        output_model_id: str,
        performance_improvement: Dict = None
    ) -> bool:
        """Mark fine-tuning job as completed with results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE finetuning_jobs 
                    SET job_status = 'completed',
                        progress = 100.0,
                        completed_at = CURRENT_TIMESTAMP,
                        output_model_id = ?,
                        performance_improvement = ?
                    WHERE job_id = ?
                """, (output_model_id, json.dumps(performance_improvement or {}), job_id))
                
                conn.commit()
                logger.info(f"✅ Fine-tuning job {job_id} marked as completed")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to complete fine-tuning job: {e}")
            return False 
   
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM users WHERE username = ?
                """, (username,))
                
                row = cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    user_data = dict(zip(columns, row))
                    user_data['preferences'] = json.loads(user_data['preferences'] or '{}')
                    return user_data
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to get user by username: {e}")
            return None