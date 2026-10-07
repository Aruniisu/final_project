"""@require_auth decorator for protected endpoints."""
from functools import wraps
from flask import request, jsonify
from database.managers.user_manager import UserManager
from database.connection import db_connection


def _get_token():
    token = request.cookies.get('access_token')
    if not token:
        auth = request.headers.get('Authorization')
        if auth and auth.startswith('Bearer '):
            token = auth.split(' ')[1]
    return token


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = _get_token()
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        db = db_connection.get_db()
        um = UserManager(db)
        user_id = um.verify_token(token)
        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401
        request.user_id = user_id
        return f(*args, **kwargs)
    return wrapper