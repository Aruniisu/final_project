import json
import redis
from functools import wraps
from flask import request, current_app
from datetime import timedelta
import hashlib
import pickle

class Cache:
    """Redis cache wrapper"""
    
    def __init__(self, redis_url=None):
        self.redis = redis.from_url(redis_url or current_app.config['REDIS_URL'])
    
    def get(self, key):
        """Get value from cache"""
        data = self.redis.get(key)
        if data:
            return pickle.loads(data)
        return None
    
    def set(self, key, value, timeout=300):
        """Set value in cache"""
        self.redis.setex(key, timeout, pickle.dumps(value))
    
    def delete(self, key):
        """Delete from cache"""
        self.redis.delete(key)
    
    def clear_pattern(self, pattern):
        """Clear all keys matching pattern"""
        keys = self.redis.keys(pattern)
        if keys:
            self.redis.delete(*keys)
    
    def exists(self, key):
        """Check if key exists"""
        return self.redis.exists(key)
    
    def increment(self, key, amount=1):
        """Increment counter"""
        return self.redis.incrby(key, amount)
    
    def get_counter(self, key):
        """Get counter value"""
        value = self.redis.get(key)
        return int(value) if value else 0


def cached(timeout=300, key_prefix=None):
    """Decorator to cache function results"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Generate cache key
            if key_prefix:
                cache_key = f"{key_prefix}:{request.path}"
            else:
                # Generate key from function name and arguments
                key_parts = [f.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}:{v}" for k, v in kwargs.items())
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            cache = Cache()
            
            # Try to get from cache
            if current_app.config.get('CACHE_ENABLED', True):
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
            
            # Execute function
            result = f(*args, **kwargs)
            
            # Cache result
            if current_app.config.get('CACHE_ENABLED', True):
                cache.set(cache_key, result, timeout)
            
            return result
        return decorated
    return decorator


def invalidate_cache(pattern):
    """Decorator to invalidate cache after function execution"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            result = f(*args, **kwargs)
            cache = Cache()
            cache.clear_pattern(pattern)
            return result
        return decorated
    return decorator