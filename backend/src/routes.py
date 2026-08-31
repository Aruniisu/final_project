from flask import Blueprint, jsonify

routes_bp = Blueprint('routes', __name__)

@routes_bp.route('/')
def index():
    return jsonify({
        'name': 'Smart DevOps Assistant API',
        'version': '2.3.1',
        'status': 'running',
        'endpoints': {
            'auth': '/api/auth',
            'assistant': '/api/assistant',
            'upload': '/api/upload',
            'pipelines': '/api/pipelines',
            'infrastructure': '/api/infrastructure',
            'monitoring': '/api/monitoring',
            'training': '/api/training',
            'settings': '/api/settings',
        }
    })