"""
MongoDB Manager for RAG Content Storage
========================================

Stores and retrieves generated content for RAG-enhanced generation.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)


class MongoDBManager:
    """Manages MongoDB operations for content storage and retrieval"""
    
    def __init__(self, mongodb_uri: str, database_name: str = "generative_copilot"):
        """
        Initialize MongoDB connection
        
        Args:
            mongodb_uri: MongoDB connection string
            database_name: Database name
        """
        self.logger = logging.getLogger(__name__)
        
        try:
            self.client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[database_name]
            
            # Collections
            self.images_collection = self.db['generated_images']
            self.music_collection = self.db['generated_music']
            self.text_collection = self.db['generated_text']
            self.embeddings_collection = self.db['content_embeddings']
            
            # Create indexes for efficient retrieval
            self._create_indexes()
            
            self.logger.info(f"✅ MongoDB connected: {database_name}")
            
        except ConnectionFailure as e:
            self.logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    
    def _create_indexes(self):
        """Create indexes for efficient querying"""
        # Text search indexes
        self.images_collection.create_index([("prompt", "text"), ("style", 1)])
        self.music_collection.create_index([("prompt", "text"), ("style", 1)])
        self.text_collection.create_index([("prompt", "text"), ("style", 1)])
        
        # User and timestamp indexes
        for collection in [self.images_collection, self.music_collection, self.text_collection]:
            collection.create_index([("user_id", 1), ("timestamp", -1)])
            collection.create_index([("rating", -1)])
        
        # Vector search index for embeddings
        self.embeddings_collection.create_index([("modality", 1), ("user_id", 1)])
    
    def store_generated_content(
        self,
        user_id: str,
        modality: str,
        prompt: str,
        content: Any,
        metadata: Dict[str, Any]
    ) -> str:
        """Store generated content in MongoDB"""
        
        document = {
            "user_id": user_id,
            "prompt": prompt,
            "content": content,
            "style": metadata.get('style', 'default'),
            "parameters": metadata.get('parameters', {}),
            "model_used": metadata.get('model_used'),
            "generation_time": metadata.get('generation_time'),
            "timestamp": datetime.utcnow(),
            "rating": None,  # Will be updated with feedback
            "feedback_count": 0
        }
        
        # Select collection based on modality
        if modality == "image":
            result = self.images_collection.insert_one(document)
        elif modality == "music":
            result = self.music_collection.insert_one(document)
        elif modality == "text":
            result = self.text_collection.insert_one(document)
        else:
            raise ValueError(f"Unknown modality: {modality}")
        
        content_id = str(result.inserted_id)
        self.logger.info(f"✅ Content stored in MongoDB: {content_id}")
        
        return content_id
    
    def retrieve_similar_content(
        self,
        user_id: str,
        modality: str,
        prompt: str,
        style: Optional[str] = None,
        limit: int = 5,
        min_rating: float = 4.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve similar high-quality content for RAG
        
        This finds previously generated content that:
        - Matches the modality
        - Has similar prompts
        - Has high user ratings
        - Optionally matches style
        """
        
        # Select collection
        if modality == "image":
            collection = self.images_collection
        elif modality == "music":
            collection = self.music_collection
        elif modality == "text":
            collection = self.text_collection
        else:
            return []
        
        # Build query
        query = {
            "user_id": user_id,
            "$text": {"$search": prompt},
            "rating": {"$gte": min_rating}
        }
        
        if style:
            query["style"] = style
        
        # Retrieve and sort by relevance
        results = collection.find(query).sort([
            ("rating", pymongo.DESCENDING),
            ("timestamp", pymongo.DESCENDING)
        ]).limit(limit)
        
        similar_content = []
        for doc in results:
            doc['_id'] = str(doc['_id'])
            similar_content.append(doc)
        
        self.logger.info(f"📚 Retrieved {len(similar_content)} similar content items")
        
        return similar_content
    
    def update_content_rating(self, content_id: str, modality: str, rating: float):
        """Update content rating based on feedback"""
        
        if modality == "image":
            collection = self.images_collection
        elif modality == "music":
            collection = self.music_collection
        elif modality == "text":
            collection = self.text_collection
        else:
            return
        
        from bson.objectid import ObjectId
        
        collection.update_one(
            {"_id": ObjectId(content_id)},
            {
                "$set": {"rating": rating},
                "$inc": {"feedback_count": 1}
            }
        )
        
        self.logger.info(f"✅ Updated rating for {content_id}: {rating}")
    
    def get_user_best_content(
        self,
        user_id: str,
        modality: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user's highest-rated content"""
        
        if modality == "image":
            collection = self.images_collection
        elif modality == "music":
            collection = self.music_collection
        elif modality == "text":
            collection = self.text_collection
        else:
            return []
        
        results = collection.find({
            "user_id": user_id,
            "rating": {"$gte": 4.0}
        }).sort("rating", pymongo.DESCENDING).limit(limit)
        
        best_content = []
        for doc in results:
            doc['_id'] = str(doc['_id'])
            best_content.append(doc)
        
        return best_content
    
    def store_embedding(
        self,
        content_id: str,
        modality: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ):
        """Store content embedding for vector search"""
        
        document = {
            "content_id": content_id,
            "modality": modality,
            "user_id": metadata.get('user_id'),
            "embedding": embedding,
            "prompt": metadata.get('prompt'),
            "timestamp": datetime.utcnow()
        }
        
        self.embeddings_collection.insert_one(document)
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed")
