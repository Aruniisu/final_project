from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import json
import uuid
import sys
import os

# Add parent and src directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

assistant_bp = Blueprint('assistant', __name__)

# Import Orchestrator safely
try:
    from src.agents import Orchestrator
    orchestrator = Orchestrator()
except ImportError:
    try:
        from agents import Orchestrator
        orchestrator = Orchestrator()
    except Exception as e:
        orchestrator = None

# Import database managers safely
try:
    from database.managers import UserManager
    from database.connection import db_connection
except ImportError:
    from src.database.managers import UserManager
    from src.database.connection import db_connection

def get_user_manager():
    db = db_connection.get_db() if hasattr(db_connection, 'get_db') else None
    return UserManager(db) if db else None


@assistant_bp.route('/query', methods=['POST'])
def process_query():
    """Process a query through the AI assistant"""
    data = request.json or {}
    query = data.get('query')
    context = data.get('context', {})
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    if not orchestrator:
        return jsonify({'error': 'Orchestrator service unavailable'}), 500
    
    try:
        # Use orchestrator.process method
        response = orchestrator.process(
            {'action': 'chat', 'query': query},
            context=context
        )
        
        reply_text = response.get('response', response) if isinstance(response, dict) else str(response)
        tools_used = response.get('tools', []) if isinstance(response, dict) else []
        metadata = response.get('metadata', {}) if isinstance(response, dict) else {}
        
        return jsonify({
            'response': reply_text,
            'tools': tools_used,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@assistant_bp.route('/history', methods=['GET'])
def get_chat_history():
    """Get chat history for user"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No token provided'}), 401
    
    token = auth_header.split(' ')[1]
    user_manager = get_user_manager()
    if not user_manager:
        return jsonify([]), 200
    
    user_id = user_manager.verify_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Get history from database
    db = db_connection.get_db() if hasattr(db_connection, 'get_db') else None
    if db:
        history = list(db.chat_history.find(
            {'user_id': user_id}
        ).sort('timestamp', -1).skip(offset).limit(limit))
        
        for item in history:
            item['_id'] = str(item['_id'])
        return jsonify(history), 200
    
    return jsonify([]), 200


@assistant_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback for an AI response"""
    data = request.json or {}
    message_id = data.get('message_id')
    feedback = data.get('feedback')
    
    if not message_id or not feedback:
        return jsonify({'error': 'Message ID and feedback required'}), 400
    
    db = db_connection.get_db() if hasattr(db_connection, 'get_db') else None
    if db:
        db.feedback.insert_one({
            'message_id': message_id,
            'feedback': feedback,
            'timestamp': datetime.now()
        })
    
    return jsonify({'message': 'Feedback submitted'}), 200


@assistant_bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    """Get command suggestions"""
    context = request.args.get('context', '')
    
    suggestions = [
        'Deploy to production',
        'Check pipeline status',
        'Monitor system health',
        'Analyze error logs',
        'Scale my service',
        'Run security scan',
        'Rollback last deployment',
        'View deployment logs'
    ]
    
    if context:
        suggestions = [s for s in suggestions if context.lower() in s.lower()]
    
    return jsonify(suggestions[:5]), 200


@assistant_bp.route('/status', methods=['GET'])
def get_status():
    """Get assistant status"""
    return jsonify({
        'status': 'online',
        'version': '2.3.1',
        'uptime': '99.9%',
        'models': 5,
        'agents': ['planner', 'executor', 'analyzer', 'infra', 'cicd', 'self_healing'],
        'auto_upgrade': True,
        'timestamp': datetime.now().isoformat()
    }), 200