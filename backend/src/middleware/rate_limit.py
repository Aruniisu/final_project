from functools import wraps
from flask import request, jsonify, current_app, g
import time
import redis
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Rate limiter using Redis for distributed rate limiting.
    """
    
    def __init__(self, redis_url=None):
        self.redis_url = redis_url or current_app.config.get('REDIS_URL', 'redis://localhost:6379')
        self.redis = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis"""
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            self.redis.ping()
            logger.info("Rate limiter connected to Redis")
        except Exception as e:
            logger.warning(f"Rate limiter Redis connection failed: {e}")
            self.redis = None
    
    def _get_client(self):
        """Get Redis client"""
        if self.redis is None:
            self._connect()
        return self.redis
    
    def is_allowed(self, key, limit, window, cost=1):
        """
        Check if request is allowed.
        
        Args:
            key: Unique identifier (IP, user_id, etc.)
            limit: Max requests per window
            window: Time window in seconds
            cost: Cost of the request (default 1)
        
        Returns:
            tuple: (allowed, remaining, reset_time)
        """
        client = self._get_client()
        if client is None:
            # If Redis is unavailable, allow all requests (fail open)
            logger.warning("Rate limiter unavailable - allowing request")
            return True, limit, int(time.time()) + window
        
        try:
            current_time = int(time.time())
            window_start = current_time - window
            
            # Use Redis sorted set for sliding window
            key = f"ratelimit:{key}"
            window_key = f"{key}:window"
            
            # Remove old entries
            client.zremrangebyscore(window_key, 0, window_start)
            
            # Count current requests
            count = client.zcard(window_key)
            
            if count >= limit:
                # Get oldest entry time
                oldest = client.zrange(window_key, 0, 0, withscores=True)
                reset_time = int(oldest[0][1]) + window if oldest else current_time + window
                return False, 0, reset_time
            
            # Add current request
            client.zadd(window_key, {str(current_time): current_time})
            client.expire(window_key, window * 2)  # Keep for 2 windows
            
            remaining = limit - count - 1
            reset_time = current_time + window
            
            return True, remaining, reset_time
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # Fail open
            return True, limit, int(time.time()) + window
    
    def get_remaining(self, key, limit, window):
        """
        Get remaining requests for a key.
        """
        client = self._get_client()
        if client is None:
            return limit
        
        try:
            current_time = int(time.time())
            window_start = current_time - window
            key = f"ratelimit:{key}:window"
            
            count = client.zcount(key, window_start, current_time)
            return max(0, limit - count)
            
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return limit
    
    def reset(self, key):
        """
        Reset rate limit for a key.
        """
        client = self._get_client()
        if client is None:
            return False
        
        try:
            key = f"ratelimit:{key}:window"
            client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Rate limiter reset error: {e}")
            return False


def rate_limit(limit, window, key_prefix='ratelimit', key_func=None, cost=1):
    """
    Decorator for rate limiting endpoints.
    
    Args:
        limit: Max requests per window
        window: Time window in seconds
        key_prefix: Prefix for Redis key
        key_func: Function to generate rate limit key
        cost: Cost of the request (default 1)
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Generate rate limit key
            if key_func:
                key = key_func()
            else:
                # Default: use IP address and endpoint path
                ip = request.remote_addr
                path = request.path
                user_id = getattr(g, 'user_id', 'anonymous')
                key = f"{key_prefix}:{path}:{user_id}:{ip}"
            
            limiter = RateLimiter()
            allowed, remaining, reset_time = limiter.is_allowed(key, limit, window, cost)
            
            # Add rate limit headers to response
            response = f(*args, **kwargs)
            
            # If response is a tuple, handle accordingly
            if isinstance(response, tuple):
                data, status = response
                if isinstance(data, dict):
                    data['rate_limit'] = {
                        'limit': limit,
                        'remaining': max(0, remaining),
                        'window': window,
                        'reset_at': datetime.fromtimestamp(reset_time).isoformat() if reset_time else None
                    }
                return data, status
            
            return response
        
        return decorated
    return decorator


def rate_limit_ip(limit, window, cost=1):
    """
    Rate limit by IP address.
    """
    def key_func():
        return request.remote_addr
    
    return rate_limit(limit, window, key_prefix='ratelimit:ip', key_func=key_func, cost=cost)


def rate_limit_user(limit, window, cost=1):
    """
    Rate limit by authenticated user ID.
    """
    def key_func():
        user_id = getattr(g, 'user_id', 'anonymous')
        return f"user:{user_id}"
    
    return rate_limit(limit, window, key_prefix='ratelimit:user', key_func=key_func, cost=cost)


def rate_limit_endpoint(limit, window, cost=1):
    """
    Rate limit by endpoint path.
    """
    def key_func():
        return request.path
    
    return rate_limit(limit, window, key_prefix='ratelimit:endpoint', key_func=key_func, cost=cost)


def global_rate_limit(limit, window, cost=1):
    """
    Global rate limit for all requests.
    """
    def key_func():
        return 'global'
    
    return rate_limit(limit, window, key_prefix='ratelimit:global', key_func=key_func, cost=cost)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


def rate_limit_middleware(next_func):
    """
    Middleware for rate limiting all requests.
    """
    def wrapper(request):
        try:
            # Get rate limit config from request
            limit = getattr(request, 'rate_limit', 100)
            window = getattr(request, 'rate_limit_window', 60)
            
            limiter = RateLimiter()
            key = f"ratelimit:global:{request.remote_addr}"
            allowed, remaining, reset_time = limiter.is_allowed(key, limit, window)
            
            if not allowed:
                return {
                    'error': 'Rate limit exceeded',
                    'retry_after': reset_time - int(time.time())
                }, 429
            
            response = next_func(request)
            
            # Add rate limit headers
            response['X-RateLimit-Limit'] = limit
            response['X-RateLimit-Remaining'] = remaining
            response['X-RateLimit-Reset'] = reset_time
            
            return response
            
        except RateLimitExceeded:
            return {
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.'
            }, 429
        
        except Exception as e:
            logger.error(f"Rate limit middleware error: {e}")
            return next_func(request)
    
    return wrapper