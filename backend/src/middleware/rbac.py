from functools import wraps
from flask import request, jsonify, current_app
import jwt
from models.user import User

def require_permission(permission):
    """Decorator to check if user has specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'No token provided'}), 401
            
            token = auth_header.split(' ')[1]
            user_model = User(current_app.mongo)
            user_id = user_model.verify_token(token)
            
            if not user_id:
                return jsonify({'error': 'Invalid token'}), 401
            
            user = user_model.find_by_id(user_id)
            if not user:
                return jsonify({'error': 'User not found'}), 401
            
            # Admin has all permissions
            if user['role'] == 'admin':
                return f(*args, **kwargs)
            
            # Check specific permission
            if permission not in user.get('permissions', []):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator

# Role definitions
ROLES = {
    'admin': {
        'permissions': ['*'],
        'description': 'Full system access'
    },
    'engineer': {
        'permissions': ['deploy', 'monitor', 'manage_pipelines', 'view_logs'],
        'description': 'DevOps engineer access'
    },
    'developer': {
        'permissions': ['view_deployments', 'view_logs', 'trigger_pipeline'],
        'description': 'Developer access'
    },
    'viewer': {
        'permissions': ['view_dashboard', 'view_monitoring'],
        'description': 'Read-only access'
    }
}