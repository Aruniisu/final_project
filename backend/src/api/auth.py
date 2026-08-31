from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import jwt
import bcrypt
import os
from functools import wraps

auth_bp = Blueprint('auth', __name__)

# Import database managers instead of old models
from database.managers import UserManager
from database.connection import db_connection

def get_user_manager():
    """Get UserManager instance"""
    db = db_connection.get_db()
    return UserManager(db)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json
    
    required_fields = ['name', 'email', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    user_manager = get_user_manager()
    user, error = user_manager.create_user(
        name=data['name'],
        email=data['email'],
        password=data['password']
    )
    
    if error:
        return jsonify({'error': error}), 400
    
    return jsonify({
        'message': 'User registered successfully',
        'user': {
            'id': user['user_id'],
            'name': user['name'],
            'email': user['email'],
            'role': user['role']
        }
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    data = request.json
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    user_manager = get_user_manager()
    user = user_manager.find_by_email(data['email'])
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user_manager.verify_password(user, data['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Update last login
    user_manager.update_last_login(user['user_id'])
    
    # Generate token
    token = user_manager.generate_token(user['user_id'])
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': user['user_id'],
            'name': user['name'],
            'email': user['email'],
            'role': user['role']
        }
    }), 200

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user info"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No token provided'}), 401
    
    token = auth_header.split(' ')[1]
    user_manager = get_user_manager()
    user_id = user_manager.verify_token(token)
    
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    user = user_manager.find_by_user_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'id': user['user_id'],
        'name': user['name'],
        'email': user['email'],
        'role': user['role'],
        'created_at': user['created_at'].isoformat() if user.get('created_at') else None
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user"""
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Update user profile"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No token provided'}), 401
    
    token = auth_header.split(' ')[1]
    user_manager = get_user_manager()
    user_id = user_manager.verify_token(token)
    
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    data = request.json
    if user_manager.update_profile(user_id, data):
        return jsonify({'message': 'Profile updated successfully'}), 200
    
    return jsonify({'error': 'Failed to update profile'}), 400

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No token provided'}), 401
    
    token = auth_header.split(' ')[1]
    user_manager = get_user_manager()
    user_id = user_manager.verify_token(token)
    
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Current and new password required'}), 400
    
    user = user_manager.find_by_user_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not user_manager.verify_password(user, current_password):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    if user_manager.change_password(user_id, new_password):
        return jsonify({'message': 'Password changed successfully'}), 200
    
    return jsonify({'error': 'Failed to change password'}), 400