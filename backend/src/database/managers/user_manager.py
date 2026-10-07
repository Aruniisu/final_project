"""UserManager — Premium single-user auth with bcrypt + JWT"""
import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from bson import ObjectId


class UserManager:
    def __init__(self, db):
        self.db = db
        self.collection = db.users

    def count_users(self):
        return self.collection.count_documents({})

    def create_user(self, name, email, password, role='admin'):
        if self.collection.find_one({'email': email}):
            return None, 'User already exists'
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
        user_data = {
            'user_id': str(ObjectId()),
            'name': name,
            'email': email,
            'password_hash': hashed.decode('utf-8'),
            'role': role,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'last_login': None,
            'profile': {'avatar': None},
            'tokens': {},
            'settings': {
                'language': 'en',
                'timezone': 'UTC',
                'dateFormat': 'MM/DD/YYYY',
                'theme': 'dark',
                'compactMode': False,
                'animations': True,
                'emailNotifications': True,
                'slackNotifications': False,
                'alertSeverity': 'high',
                'sessionTimeout': 30,
                'passwordExpiry': 90,
            }
        }
        result = self.collection.insert_one(user_data)
        user_data['_id'] = str(result.inserted_id)
        return user_data, None

    def find_by_email(self, email):
        user = self.collection.find_one({'email': email.lower()})
        if user:
            user['_id'] = str(user['_id'])
        return user

    def find_by_user_id(self, user_id):
        user = self.collection.find_one({'user_id': user_id})
        if user:
            user['_id'] = str(user['_id'])
        return user

    def verify_password(self, user, password):
        stored = user.get('password_hash') or user.get('password')
        if not stored:
            return False
        try:
            return bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8'))
        except Exception:
            return False

    def change_password(self, user_id, new_password):
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(rounds=12))
        result = self.collection.update_one(
            {'user_id': user_id},
            {'$set': {'password_hash': hashed.decode('utf-8'), 'updated_at': datetime.now()}}
        )
        return result.modified_count > 0

    def update_last_login(self, user_id):
        self.collection.update_one(
            {'user_id': user_id},
            {'$set': {'last_login': datetime.now()}}
        )

    def update_profile(self, user_id, data):
        allowed = ['name', 'email', 'profile']
        update_data = {k: v for k, v in data.items() if k in allowed}
        update_data['updated_at'] = datetime.now()
        result = self.collection.update_one(
            {'user_id': user_id},
            {'$set': update_data}
        )
        return result.modified_count >= 0

    def update_settings(self, user_id, settings):
        result = self.collection.update_one(
            {'user_id': user_id},
            {'$set': {'settings': settings, 'updated_at': datetime.now()}}
        )
        return result.modified_count >= 0

    def update_tokens(self, user_id, tokens):
        update = {}
        for k, v in tokens.items():
            update[f'tokens.{k}'] = v
        update['updated_at'] = datetime.now()
        result = self.collection.update_one(
            {'user_id': user_id},
            {'$set': update}
        )
        return result.modified_count >= 0

    def generate_token(self, user_id, expires_minutes=15):
        payload = {
            'user_id': str(user_id),
            'exp': datetime.utcnow() + timedelta(minutes=expires_minutes),
            'iat': datetime.utcnow(),
            'type': 'access',
        }
        return jwt.encode(payload, os.getenv('JWT_SECRET_KEY', 'jwt-secret-key'), algorithm='HS256')

    def generate_refresh_token(self, user_id):
        payload = {
            'user_id': str(user_id),
            'exp': datetime.utcnow() + timedelta(days=7),
            'iat': datetime.utcnow(),
            'type': 'refresh',
        }
        return jwt.encode(payload, os.getenv('JWT_REFRESH_SECRET', 'jwt-refresh-key'), algorithm='HS256')

    def verify_token(self, token, token_type='access'):
        secret = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
        if token_type == 'refresh':
            secret = os.getenv('JWT_REFRESH_SECRET', 'jwt-refresh-key')
        try:
            payload = jwt.decode(token, secret, algorithms=['HS256'])
            return payload.get('user_id')
        except Exception:
            return None