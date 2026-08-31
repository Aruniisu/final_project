from functools import wraps
from flask import request, jsonify, current_app
import time
import logging

logger = logging.getLogger(__name__)

def timeit(f):
    """Decorator to measure execution time"""
    @wraps(f)
    def decorated(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        end = time.time()
        logger.info(f"{f.__name__} took {end - start:.2f}s")
        return result
    return decorated

def log_request(f):
    """Decorator to log request details"""
    @wraps(f)
    def decorated(*args, **kwargs):
        logger.info(f"Request: {request.method} {request.path} - IP: {request.remote_addr}")
        return f(*args, **kwargs)
    return decorated

def validate_json(schema):
    """Decorator to validate JSON request body"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            
            # Validate required fields
            if 'required' in schema:
                for field in schema['required']:
                    if field not in data:
                        return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # Validate field types
            if 'properties' in schema:
                for field, rules in schema['properties'].items():
                    if field in data:
                        if 'type' in rules:
                            expected_type = rules['type']
                            if expected_type == 'string' and not isinstance(data[field], str):
                                return jsonify({'error': f'Field {field} must be a string'}), 400
                            elif expected_type == 'number' and not isinstance(data[field], (int, float)):
                                return jsonify({'error': f'Field {field} must be a number'}), 400
                            elif expected_type == 'integer' and not isinstance(data[field], int):
                                return jsonify({'error': f'Field {field} must be an integer'}), 400
                            elif expected_type == 'boolean' and not isinstance(data[field], bool):
                                return jsonify({'error': f'Field {field} must be a boolean'}), 400
                            elif expected_type == 'array' and not isinstance(data[field], list):
                                return jsonify({'error': f'Field {field} must be an array'}), 400
                            elif expected_type == 'object' and not isinstance(data[field], dict):
                                return jsonify({'error': f'Field {field} must be an object'}), 400
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def handle_exceptions(f):
    """Decorator to handle exceptions globally"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({
                'error': str(e),
                'type': type(e).__name__
            }), 500
    return decorated