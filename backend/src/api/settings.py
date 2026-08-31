from flask import Blueprint, request, jsonify, current_app
from datetime import datetime

settings_bp = Blueprint('settings', __name__)

from middleware.auth import token_required
from middleware.rate_limit import rate_limit

@settings_bp.route('/', methods=['GET'])
@token_required
def get_settings(user):
    """Get user settings"""
    # Get settings from database
    settings = current_app.mongo.db.settings.find_one({'user_id': user['_id']})
    
    if not settings:
        settings = {
            'general': {
                'language': 'en',
                'timezone': 'UTC',
                'dateFormat': 'MM/DD/YYYY'
            },
            'appearance': {
                'theme': 'dark',
                'compactMode': False,
                'animations': True
            },
            'notifications': {
                'emailNotifications': True,
                'slackNotifications': False,
                'alertSeverity': 'high'
            },
            'security': {
                'twoFactorAuth': False,
                'sessionTimeout': 30,
                'passwordExpiry': 90
            },
            'integrations': {
                'github': {'connected': True, 'repo': 'org/devops-assistant'},
                'google': {'connected': False},
                'aws': {'connected': True, 'region': 'us-west-2'},
                'docker': {'connected': False}
            }
        }
        settings['_id'] = str(settings.get('_id', ''))
    
    return jsonify(settings), 200

@settings_bp.route('/', methods=['PUT'])
@token_required
def update_settings(user):
    """Update user settings"""
    data = request.json
    
    # Update in database
    result = current_app.mongo.db.settings.update_one(
        {'user_id': user['_id']},
        {'$set': data},
        upsert=True
    )
    
    return jsonify({
        'message': 'Settings updated successfully',
        'settings': data
    }), 200

@settings_bp.route('/audit-logs', methods=['GET'])
@token_required
def get_audit_logs(user):
    """Get audit logs"""
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Get logs from database
    logs = list(current_app.mongo.db.audit_logs.find(
        {'user_id': user['_id']}
    ).sort('timestamp', -1).skip(offset).limit(limit))
    
    for log in logs:
        log['_id'] = str(log['_id'])
    
    return jsonify(logs), 200

@settings_bp.route('/integrations/<provider>', methods=['POST'])
@token_required
def connect_integration(user, provider):
    """Connect an integration"""
    data = request.json
    
    # Update integration settings
    current_app.mongo.db.settings.update_one(
        {'user_id': user['_id']},
        {'$set': {f'integrations.{provider}': data}},
        upsert=True
    )
    
    return jsonify({
        'message': f'{provider} integration connected',
        'provider': provider,
        'status': 'connected'
    }), 200

@settings_bp.route('/integrations/<provider>', methods=['DELETE'])
@token_required
def disconnect_integration(user, provider):
    """Disconnect an integration"""
    current_app.mongo.db.settings.update_one(
        {'user_id': user['_id']},
        {'$set': {f'integrations.{provider}': {'connected': False}}}
    )
    
    return jsonify({
        'message': f'{provider} integration disconnected',
        'provider': provider,
        'status': 'disconnected'
    }), 200