from datetime import datetime
from flask_pymongo import PyMongo
from bson import ObjectId
import bcrypt
import jwt
import os
from datetime import datetime, timedelta

class User:
    def __init__(self, mongo):
        self.mongo = mongo
        self.collection = mongo.db.users

    def create(self, name, email, password, role='user'):
        """Create a new user"""
        # Check if user exists
        if self.collection.find_one({'email': email}):
            return None, 'User already exists'
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_data = {
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
        user = self.collection.find_one({'email': email})
        if user:
            user['_id'] = str(user['_id'])
        return user

    def find_by_id(self, user_id):
        """Find user by ID"""
        try:
            user = self.collection.find_one({'_id': ObjectId(user_id)})
            if user:
                user['_id'] = str(user['_id'])
            return user
        except:
            return None

    def verify_password(self, user, password):
        """Verify user password"""
        return bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8'))

    def update_last_login(self, user_id):
        """Update last login timestamp"""
        self.collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'last_login': datetime.now()}}
        )

    def update(self, user_id, data):
        """Update user data"""
        data['updated_at'] = datetime.now()
        result = self.collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': data}
        )
        return result.modified_count > 0

    def delete(self, user_id):
        """Delete user"""
        result = self.collection.delete_one({'_id': ObjectId(user_id)})
        return result.deleted_count > 0

    def generate_token(self, user_id):
        """Generate JWT token"""
        payload = {
            'user_id': str(user_id),
            'exp': datetime.now() + timedelta(days=1)
        }
        return jwt.encode(payload, os.getenv('JWT_SECRET_KEY', 'jwt-secret-key'), algorithm='HS256')

    def verify_token(self, token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY', 'jwt-secret-key'), algorithms=['HS256'])
            return payload.get('user_id')
        except:
            return None

    def get_all(self, limit=50, offset=0):
        """Get all users with pagination"""
        users = list(self.collection.find().skip(offset).limit(limit))
        for user in users:
            user['_id'] = str(user['_id'])
            user.pop('password', None)
        return users

    def count(self):
        """Get total user count"""
        return self.collection.count_documents({})