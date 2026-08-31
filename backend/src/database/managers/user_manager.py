from .base_manager import BaseManager
from datetime import datetime
import bcrypt
import jwt
import os


class UserManager(BaseManager):
    """Manager for user operations"""
    
    def __init__(self, db):
        super().__init__(db, 'users')
    
    def create_user(self, name, email, password, role='user'):
        """Create a new user"""
        # Check if user exists
        if self.find_one({'email': email}):
            return None, 'User already exists'
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_data = {
            'user_id': self._generate_id('user'),
            'name': name,
            'email': email,
            'password': hashed_password.decode('utf-8'),
            'role': role,
            'is_active': True,
            'is_verified': False,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'last_login': None,
            'preferences': {
                'theme': 'dark',
                'language': 'en',
                'notifications': True
            },
            'permissions': []
        }
        
        result = self.collection.insert_one(user_data)
        user_data['_id'] = str(result.inserted_id)
        return user_data, None
    
    def find_by_email(self, email):
        """Find user by email"""
        return self.find_one({'email': email})
    
    def find_by_user_id(self, user_id):
        """Find user by user_id"""
        return self.find_by_id(user_id, 'user_id')
    
    def verify_password(self, user, password):
        """Verify user password"""
        return bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8'))
    
    def update_last_login(self, user_id):
        """Update last login timestamp"""
        return self.update(user_id, {'last_login': datetime.now()}, 'user_id')
    
    def generate_token(self, user_id):
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'exp': datetime.now() + timedelta(days=1)
        }
        secret = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
        return jwt.encode(payload, secret, algorithm='HS256')
    
    def verify_token(self, token):
        """Verify JWT token"""
        try:
            secret = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
            payload = jwt.decode(token, secret, algorithms=['HS256'])
            return payload.get('user_id')
        except:
            return None
    
    def update_profile(self, user_id, data):
        """Update user profile"""
        allowed_fields = ['name', 'preferences']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        return self.update(user_id, update_data, 'user_id')
    
    def change_password(self, user_id, new_password):
        """Change user password"""
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        return self.update(user_id, {'password': hashed.decode('utf-8')}, 'user_id')
    
    def get_all_users(self, limit=50, skip=0):
        """Get all users"""
        return self.find_many({}, sort=[('created_at', -1)], limit=limit, skip=skip)
    
    def get_user_stats(self):
        """Get user statistics"""
        total = self.count()
        active = self.count({'is_active': True})
        
        return {
            'total_users': total,
            'active_users': active,
            'inactive_users': total - active
        }