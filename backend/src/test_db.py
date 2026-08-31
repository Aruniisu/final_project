import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'src'))

from database.connection import DatabaseConnection

def test_connection():
    print("🔍 Testing database connection...")
    
    conn = DatabaseConnection()
    
    # Test connection with config
    config = {
        'MONGO_URI': os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'),
        'MONGODB_DB': os.getenv('MONGODB_DB', 'smart_devops')
    }
    
    success = conn.init_from_config(config)
    
    if success:
        print("✅ Database connected successfully!")
        print(f"  Database: {conn.database_name}")
        print(f"  Collections: {conn.get_db().list_collection_names()}")
    else:
        print("❌ Database connection failed!")
        print("Please make sure MongoDB is running.")
        
    return success

if __name__ == '__main__':
    test_connection()