import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path correctly
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'src'))

from database.connection import DatabaseConnection


def run_migrations():
    """Run database migrations"""
    print("🔄 Running database migrations...")
    
    # Initialize database connection directly
    conn = DatabaseConnection()
    
    # Use init_from_config method instead of init_app with dict
    config = {
        'MONGO_URI': os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'),
        'MONGODB_DB': os.getenv('MONGODB_DB', 'smart_devops')
    }
    
    # Try to connect
    success = conn.init_from_config(config)
    
    if not success:
        print("❌ Failed to connect to database")
        print("Please make sure MongoDB is running:")
        print("  Windows: net start MongoDB")
        print("  Mac: brew services start mongodb-community")
        print("  Linux: sudo systemctl start mongod")
        return False
    
    db = conn.get_db()
    print(f"✅ Connected to database: {conn.database_name}")
    
    # Create collections if they don't exist
    collections = [
        'users',
        'projects',
        'pipelines',
        'deployments',
        'uploads',
        'trainings',
        'audit_logs',
        'notifications',
        'chat_history',
        'feedback',
        'settings'
    ]
    
    existing_collections = db.list_collection_names()
    
    created = []
    for collection in collections:
        if collection not in existing_collections:
            db.create_collection(collection)
            created.append(collection)
    
    if created:
        print(f"✅ Created collections: {', '.join(created)}")
    else:
        print("✅ All collections already exist")
    
    # Create indexes
    print("📊 Creating indexes...")
    
    # Users indexes
    db.users.create_index('email', unique=True)
    db.users.create_index('username', unique=True, sparse=True)
    print("  ✅ users indexes")
    
    # Projects indexes
    db.projects.create_index('project_id', unique=True)
    db.projects.create_index('user_id')
    db.projects.create_index('created_at')
    print("  ✅ projects indexes")
    
    # Pipelines indexes
    db.pipelines.create_index('pipeline_id', unique=True)
    db.pipelines.create_index('user_id')
    db.pipelines.create_index('status')
    db.pipelines.create_index('created_at')
    print("  ✅ pipelines indexes")
    
    # Deployments indexes
    db.deployments.create_index('deployment_id', unique=True)
    db.deployments.create_index('user_id')
    db.deployments.create_index('project_id')
    db.deployments.create_index('status')
    print("  ✅ deployments indexes")
    
    # Uploads indexes
    db.uploads.create_index('upload_id', unique=True)
    db.uploads.create_index('user_id')
    db.uploads.create_index('project_id')
    print("  ✅ uploads indexes")
    
    # Trainings indexes
    db.trainings.create_index('training_id', unique=True)
    db.trainings.create_index('user_id')
    db.trainings.create_index('status')
    print("  ✅ trainings indexes")
    
    # Audit logs indexes
    db.audit_logs.create_index('user_id')
    db.audit_logs.create_index('action')
    db.audit_logs.create_index('timestamp')
    print("  ✅ audit_logs indexes")
    
    # Notifications indexes
    db.notifications.create_index('user_id')
    db.notifications.create_index('read')
    db.notifications.create_index('created_at')
    print("  ✅ notifications indexes")
    
    # Chat history indexes
    db.chat_history.create_index('user_id')
    db.chat_history.create_index('timestamp')
    print("  ✅ chat_history indexes")
    
    # Feedback indexes
    db.feedback.create_index('message_id')
    db.feedback.create_index('created_at')
    print("  ✅ feedback indexes")
    
    # Settings indexes
    db.settings.create_index('user_id', unique=True)
    print("  ✅ settings indexes")
    
    print("✅ All migrations completed successfully!")
    
    # Print summary
    print("\n📊 Database Summary:")
    print(f"  Database: {conn.database_name}")
    print(f"  Collections: {len(db.list_collection_names())}")
    print(f"  Collections List: {', '.join(db.list_collection_names())}")
    
    return True


if __name__ == '__main__':
    run_migrations()