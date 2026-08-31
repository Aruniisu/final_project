import os
import logging
from flask import Flask, current_app, g
from flask_pymongo import PyMongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from datetime import datetime

logger = logging.getLogger(__name__)

# Global MongoDB instance
mongo = None
db = None


class DatabaseConnection:
    """Database connection manager"""
    
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.connected = False
        self.connection_string = None
        self.database_name = None
    
    def init_app(self, app):
        """Initialize database connection with Flask app or config dict"""
        try:
            # Handle both Flask app and config dict
            if hasattr(app, 'config'):
                # It's a Flask app
                self.connection_string = app.config.get('MONGO_URI')
                self.database_name = app.config.get('MONGODB_DB', 'smart_devops')
            else:
                # It's a config dict
                self.connection_string = app.get('MONGO_URI')
                self.database_name = app.get('MONGODB_DB', 'smart_devops')
            
            if not self.connection_string:
                self.connection_string = 'mongodb://localhost:27017/'
            
            # Create MongoDB client
            self._client = MongoClient(
                self.connection_string,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test connection
            self._client.admin.command('ping')
            
            # Get database
            self._db = self._client[self.database_name]
            
            # Set global variables
            global mongo, db
            mongo = self._client
            db = self._db
            
            self.connected = True
            
            # Create indexes
            self._create_indexes()
            
            logger.info(f"✅ Connected to MongoDB: {self.database_name}")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
            self.connected = False
            return False
    
    def init_from_config(self, config):
        """Initialize database from config dict (for migrations)"""
        return self.init_app(config)
    
    def _create_indexes(self):
        """Create necessary database indexes"""
        try:
            # Users collection indexes
            self._db.users.create_index('email', unique=True)
            self._db.users.create_index('username', unique=True, sparse=True)
            
            # Projects collection indexes
            self._db.projects.create_index('project_id', unique=True)
            self._db.projects.create_index('user_id')
            self._db.projects.create_index('created_at')
            
            # Pipelines collection indexes
            self._db.pipelines.create_index('pipeline_id', unique=True)
            self._db.pipelines.create_index('user_id')
            self._db.pipelines.create_index('status')
            self._db.pipelines.create_index('created_at')
            
            # Deployments collection indexes
            self._db.deployments.create_index('deployment_id', unique=True)
            self._db.deployments.create_index('user_id')
            self._db.deployments.create_index('project_id')
            self._db.deployments.create_index('status')
            
            # Uploads collection indexes
            self._db.uploads.create_index('upload_id', unique=True)
            self._db.uploads.create_index('user_id')
            self._db.uploads.create_index('project_id')
            
            # Training collection indexes
            self._db.trainings.create_index('training_id', unique=True)
            self._db.trainings.create_index('user_id')
            self._db.trainings.create_index('status')
            
            # Audit logs collection indexes
            self._db.audit_logs.create_index('user_id')
            self._db.audit_logs.create_index('action')
            self._db.audit_logs.create_index('timestamp')
            
            # Notifications collection indexes
            self._db.notifications.create_index('user_id')
            self._db.notifications.create_index('read')
            self._db.notifications.create_index('created_at')
            
            # Chat history collection indexes
            self._db.chat_history.create_index('user_id')
            self._db.chat_history.create_index('timestamp')
            
            # Feedback collection indexes
            self._db.feedback.create_index('message_id')
            self._db.feedback.create_index('created_at')
            
            # Settings collection indexes
            self._db.settings.create_index('user_id', unique=True)
            
            logger.info("✅ Database indexes created successfully")
            
        except Exception as e:
            logger.error(f"❌ Index creation failed: {e}")
    
    def get_client(self):
        """Get MongoDB client"""
        return self._client
    
    def get_db(self):
        """Get MongoDB database"""
        return self._db
    
    def close(self):
        """Close database connection"""
        if self._client:
            self._client.close()
            self.connected = False
            logger.info("Database connection closed")
    
    def is_connected(self):
        """Check if database is connected"""
        if not self.connected or not self._client:
            return False
        try:
            self._client.admin.command('ping')
            return True
        except:
            return False
    
    def get_collection(self, collection_name):
        """Get collection by name"""
        if not self._db:
            return None
        return self._db[collection_name]
    
    def get_stats(self):
        """Get database statistics"""
        if not self.is_connected():
            return {'status': 'disconnected'}
        
        try:
            stats = {
                'status': 'connected',
                'database': self.database_name,
                'collections': len(self._db.list_collection_names()),
                'collections_list': self._db.list_collection_names()
            }
            return stats
        except Exception as e:
            return {'status': 'error', 'error': str(e)}


# Global database connection instance
db_connection = DatabaseConnection()


def get_db():
    """Get database instance for Flask app context"""
    if 'db' not in g:
        g.db = db_connection
    return g.db


def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db(app):
    """Initialize database with Flask app"""
    return db_connection.init_app(app)


# Export db variable for direct import
db = db_connection.get_db()