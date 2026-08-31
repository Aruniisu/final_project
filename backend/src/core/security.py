import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
import re
import hashlib
import secrets

class Security:
    """Security utilities"""
    
    @staticmethod
    def hash_password(password):
        """Hash password with bcrypt"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def generate_token(user_id, expires_in=86400):
        """Generate JWT token"""
        payload = {
            'user_id': str(user_id),
            'exp': datetime.now() + timedelta(seconds=expires_in),
            'iat': datetime.now()
        }
        return jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_token(token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            return payload.get('user_id')
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def generate_api_key():
        """Generate secure API key"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_otp():
        """Generate OTP code"""
        return ''.join(secrets.choice('0123456789') for _ in range(6))
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        return True, "Password is strong"
    
    @staticmethod
    def sanitize_input(data):
        """Sanitize input data"""
        if isinstance(data, str):
            # Remove potentially dangerous characters
            return re.sub(r'[<>{}]', '', data)
        elif isinstance(data, dict):
            return {k: Security.sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [Security.sanitize_input(item) for item in data]
        return data
    
    @staticmethod
    def mask_sensitive_data(data, fields=['password', 'token', 'secret', 'api_key']):
        """Mask sensitive fields in data"""
        if isinstance(data, dict):
            masked = {}
            for k, v in data.items():
                if any(field in k.lower() for field in fields):
                    masked[k] = '***MASKED***'
                else:
                    masked[k] = Security.mask_sensitive_data(v, fields)
            return masked
        elif isinstance(data, list):
            return [Security.mask_sensitive_data(item, fields) for item in data]
        return data


class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self, redis_url=None):
        self.redis = redis.from_url(redis_url or current_app.config['REDIS_URL'])
    
    def is_allowed(self, key, limit, window):
        """
        Check if request is allowed
        key: identifier (IP, user_id, etc.)
        limit: max requests per window
        window: time window in seconds
        """
        current = self.redis.get(key)
        if current is None:
            self.redis.setex(key, window, 1)
            return True, limit - 1
        
        current = int(current)
        if current >= limit:
            ttl = self.redis.ttl(key)
            return False, ttl
        
        self.redis.incr(key)
        return True, limit - current - 1