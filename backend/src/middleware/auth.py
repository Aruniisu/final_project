from functools import wraps
from flask import request, jsonify, current_app
import jwt
from models.user import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No token provided'}), 401
        
        token = auth_header.split(' ')[1]
        user_model = User(current_app.mongo)
        user_id = user_model.verify_token(token)
        
        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        user = user_model.find_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        return f(user, *args, **kwargs)
    
    return decorated

def role_required(allowed_roles):
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
            
            if user['role'] not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(user, *args, **kwargs)
        
        return decorated
    return decorator