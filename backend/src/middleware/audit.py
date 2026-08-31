from functools import wraps
from flask import request, current_app, g
from datetime import datetime
import json

def audit_log(action):
    """Decorator to log user actions"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Execute function
            response = f(*args, **kwargs)
            
            # Get user info
            user_id = g.get('user_id', 'anonymous')
            ip = request.remote_addr
            user_agent = request.headers.get('User-Agent', '')
            
            # Create audit log
            audit_entry = {
                'user_id': user_id,
                'action': action,
                'method': request.method,
                'path': request.path,
                'ip': ip,
                'user_agent': user_agent,
                'timestamp': datetime.now(),
                'status': response[1] if isinstance(response, tuple) else 200
            }
            
            # Store in database
            try:
                current_app.mongo.db.audit_logs.insert_one(audit_entry)
            except Exception as e:
                current_app.logger.error(f"Failed to log audit: {e}")
            
            return response
        return decorated
    return decorator


def audit_request(f):
    """Log all requests for auditing"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = g.get('user_id', 'anonymous')
        ip = request.remote_addr
        
        # Log request
        current_app.logger.info(
            f"Request: {request.method} {request.path}",
            extra={
                'request_id': request.headers.get('X-Request-ID'),
                'user_id': user_id,
                'ip': ip
            }
        )
        
        return f(*args, **kwargs)
    return decorated