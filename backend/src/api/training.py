from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import uuid
import random

training_bp = Blueprint('training', __name__)

from models.training import Training
from middleware.auth import token_required
from middleware.rate_limit import rate_limit

def get_training_model():
    return Training(current_app.mongo)

@training_bp.route('/models', methods=['GET'])
@token_required
def get_models(user):
    """Get all models"""
    models = [
        {
            'id': '1',
            'name': 'DevOps Assistant v2',
            'version': '2.3.1',
            'status': 'active',
            'accuracy': 0.947,
            'f1': 0.945,
            'parameters': '1.2M',
            'size': '234 MB',
            'createdAt': '2024-01-15',
            'favorite': True
        },
        {
            'id': '2',
            'name': 'DevOps Assistant v1',
            'version': '2.3.0',
            'status': 'deprecated',
            'accuracy': 0.932,
            'f1': 0.928,
            'parameters': '1.1M',
            'size': '210 MB',
            'createdAt': '2024-01-12',
            'favorite': False
        },
        {
            'id': '3',
            'name': 'Security Scanner Model',
            'version': '1.0.0',
            'status': 'active',
            'accuracy': 0.965,
            'f1': 0.962,
            'parameters': '890K',
            'size': '160 MB',
            'createdAt': '2024-01-14',
            'favorite': True
        }
    ]
    
    return jsonify(models), 200

@training_bp.route('/train', methods=['POST'])
@token_required
def start_training(user):
    """Start model training"""
    data = request.json
    
    training_model = get_training_model()
    training = training_model.create(
        user_id=user['_id'],
        name=data.get('name', 'New Training'),
        model_type=data.get('model_type', 'default'),
        config=data.get('config', {})
    )
    
    # Start async training
    from tasks.async_tasks import train_model
    train_model.delay(training['training_id'])
    
    return jsonify({
        'message': 'Training started',
        'training_id': training['training_id'],
        'status': 'pending'
    }), 201

@training_bp.route('/<training_id>/status', methods=['GET'])
@token_required
def get_training_status(user, training_id):
    """Get training status"""
    training_model = get_training_model()
    training = training_model.find_by_id(training_id)
    
    if not training:
        return jsonify({'error': 'Training not found'}), 404
    
    return jsonify({
        'training_id': training['training_id'],
        'status': training['status'],
        'progress': training.get('progress', 0),
        'metrics': training.get('metrics', {})
    }), 200

@training_bp.route('/<training_id>/stop', methods=['POST'])
@token_required
def stop_training(user, training_id):
    """Stop training"""
    training_model = get_training_model()
    training = training_model.find_by_id(training_id)
    
    if not training:
        return jsonify({'error': 'Training not found'}), 404
    
    training_model.update_status(training_id, 'cancelled')
    
    return jsonify({
        'message': 'Training stopped',
        'training_id': training_id
    }), 200

@training_bp.route('/deploy', methods=['POST'])
@token_required
def deploy_model(user):
    """Deploy a model"""
    data = request.json
    model_id = data.get('model_id')
    
    if not model_id:
        return jsonify({'error': 'model_id required'}), 400
    
    return jsonify({
        'message': f'Model {model_id} deployed successfully',
        'model_id': model_id,
        'status': 'deployed'
    }), 200

@training_bp.route('/versions', methods=['GET'])
@token_required
def get_versions(user):
    """Get model versions"""
    versions = [
        {'version': 'v2.3.1', 'accuracy': 94.7, 'date': '2024-01-15', 'status': 'current'},
        {'version': 'v2.3.0', 'accuracy': 93.2, 'date': '2024-01-12', 'status': 'archived'},
        {'version': 'v2.2.9', 'accuracy': 92.8, 'date': '2024-01-10', 'status': 'archived'},
        {'version': 'v2.2.8', 'accuracy': 89.5, 'date': '2024-01-08', 'status': 'archived'}
    ]
    
    return jsonify(versions), 200