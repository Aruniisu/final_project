import os
import sys
from datetime import datetime, timedelta
import bcrypt

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from database.connection import DatabaseConnection
from database.managers import (
    UserManager,
    ProjectManager,
    PipelineManager,
    DeploymentManager
)


def seed_data():
    """Seed initial data"""
    print("🌱 Seeding initial data...")
    
    # Initialize database connection
    conn = DatabaseConnection()
    conn.init_app({
        'MONGO_URI': os.getenv('MONGODB_URI', 'mongodb://localhost:27017/'),
        'MONGODB_DB': os.getenv('MONGODB_DB', 'smart_devops')
    })
    
    if not conn.is_connected():
        print("❌ Failed to connect to database")
        return False
    
    db = conn.get_db()
    
    # Seed users
    user_manager = UserManager(db)
    
    # Check if admin exists
    admin = user_manager.find_by_email('admin@example.com')
    if not admin:
        user_manager.create_user(
            name='Admin User',
            email='admin@example.com',
            password='Admin@123',
            role='admin'
        )
        print("✅ Created admin user")
    
    # Check if test user exists
    test_user = user_manager.find_by_email('test@example.com')
    if not test_user:
        user_manager.create_user(
            name='Test User',
            email='test@example.com',
            password='Test@123',
            role='engineer'
        )
        print("✅ Created test user")
    
    # Get user IDs
    admin = user_manager.find_by_email('admin@example.com')
    test_user = user_manager.find_by_email('test@example.com')
    
    # Seed projects
    project_manager = ProjectManager(db)
    projects = [
        {
            'user_id': admin['user_id'],
            'name': 'Frontend Application',
            'description': 'React.js frontend application',
            'type': 'web'
        },
        {
            'user_id': admin['user_id'],
            'name': 'Backend API',
            'description': 'Python Flask REST API',
            'type': 'api'
        },
        {
            'user_id': test_user['user_id'],
            'name': 'Mobile App',
            'description': 'React Native mobile app',
            'type': 'mobile'
        }
    ]
    
    for project_data in projects:
        existing = project_manager.find_one({'name': project_data['name']})
        if not existing:
            project_manager.create_project(**project_data)
            print(f"✅ Created project: {project_data['name']}")
    
    # Seed pipelines
    pipeline_manager = PipelineManager(db)
    
    # Get projects
    frontend = project_manager.find_one({'name': 'Frontend Application'})
    backend = project_manager.find_one({'name': 'Backend API'})
    
    if frontend:
        pipeline_manager.create_pipeline(
            user_id=admin['user_id'],
            name='Frontend CI/CD',
            repo='org/frontend-app',
            branch='main'
        )
        print("✅ Created frontend pipeline")
    
    if backend:
        pipeline_manager.create_pipeline(
            user_id=admin['user_id'],
            name='Backend CI/CD',
            repo='org/backend-api',
            branch='main'
        )
        print("✅ Created backend pipeline")
    
    # Seed deployments
    deployment_manager = DeploymentManager(db)
    
    if frontend:
        deployment_manager.create_deployment(
            user_id=admin['user_id'],
            project_id=frontend['project_id'],
            environment='production',
            config={'replicas': 3, 'memory': '512Mi'}
        )
        print("✅ Created frontend deployment")
    
    print("✅ Data seeding completed!")
    return True


if __name__ == '__main__':
    seed_data()