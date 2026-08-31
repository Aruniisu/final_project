import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Database
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    MONGODB_DB = os.getenv('MONGODB_DB', 'smart_devops')
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # Celery
    CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # Upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 104857600))
    ALLOWED_EXTENSIONS = {
        'zip', 'tar', 'gz', 'tgz', 'rar', '7z',
        'js', 'jsx', 'ts', 'tsx', 'py', 'java', 'go', 'rs',
        'json', 'yaml', 'yml', 'toml', 'xml',
        'txt', 'md', 'rst', 'html', 'css', 'scss',
        'png', 'jpg', 'jpeg', 'svg', 'gif', 'ico'
    }
    
    # Rate Limiting
    RATELIMIT_DEFAULT = "100/hour"
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')
    
    # GitHub
    GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID', '')
    GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET', '')
    GITHUB_ACCESS_TOKEN = os.getenv('GITHUB_ACCESS_TOKEN', '')
    
    # Google Drive
    GOOGLE_DRIVE_CLIENT_ID = os.getenv('GOOGLE_DRIVE_CLIENT_ID', '')
    GOOGLE_DRIVE_CLIENT_SECRET = os.getenv('GOOGLE_DRIVE_CLIENT_SECRET', '')
    
    # AWS
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET', 'smart-devops-uploads')
    
    # Docker
    DOCKER_HOST = os.getenv('DOCKER_HOST', 'unix:///var/run/docker.sock')
    
    # Kubernetes
    KUBE_CONFIG_PATH = os.getenv('KUBE_CONFIG_PATH', '~/.kube/config')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # Performance
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Pagination
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 100
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    
    # Feature Flags
    ENABLE_AUTO_UPGRADE = os.getenv('ENABLE_AUTO_UPGRADE', 'true').lower() == 'true'
    ENABLE_AI_AGENTS = os.getenv('ENABLE_AI_AGENTS', 'true').lower() == 'true'
    ENABLE_WEBSOCKET = os.getenv('ENABLE_WEBSOCKET', 'true').lower() == 'true'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    CACHE_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    CACHE_ENABLED = True


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = False
    TESTING = True
    MONGODB_URI = 'mongodb://localhost:27017/smart_devops_test'
    CACHE_ENABLED = False


def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'development')
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    return configs.get(env, DevelopmentConfig)()