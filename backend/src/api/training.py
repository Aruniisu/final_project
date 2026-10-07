"""Training API — Real ML training + Level 3 learning."""
from flask import Blueprint, request, jsonify
from ml.trainer import (
    list_models, start_training, get_job, list_jobs,
    stop_job, deploy_model,
)
from ml.feedback import stats as feedback_stats, count_samples
from ml.model_manager import progress as learning_progress

training_bp = Blueprint('training', __name__)


@training_bp.route('/models', methods=['GET', 'OPTIONS'])
def get_models():
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify(list_models()), 200


@training_bp.route('/models/<model_id>', methods=['GET', 'OPTIONS'])
def get_model(model_id):
    if request.method == 'OPTIONS':
        return '', 204
    for m in list_models():
        if m['id'] == model_id:
            return jsonify(m), 200
    return jsonify({'error': 'Not found'}), 404


@training_bp.route('/versions', methods=['GET', 'OPTIONS'])
def get_versions():
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify(list_models()), 200


@training_bp.route('/train', methods=['POST', 'OPTIONS'])
def train():
    if request.method == 'OPTIONS':
        return '', 204
    config = request.get_json() or {}
    config.setdefault('model_type', 'log_classifier')
    config.setdefault('dataset', config['model_type'])
    config.setdefault('epochs', 10)
    config.setdefault('n_samples', 1000)
    config.setdefault('delay_seconds', 0.4)
    config.setdefault('name', f"Manual Model {int(__import__('time').time())}")
    job = start_training(config)
    return jsonify({'success': True, 'job': job}), 200


@training_bp.route('/jobs', methods=['GET', 'OPTIONS'])
def get_jobs():
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify(list_jobs()), 200


@training_bp.route('/<job_id>/status', methods=['GET', 'OPTIONS'])
def job_status(job_id):
    if request.method == 'OPTIONS':
        return '', 204
    job = get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job), 200


@training_bp.route('/<job_id>/stop', methods=['POST', 'OPTIONS'])
def stop(job_id):
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify(stop_job(job_id)), 200


@training_bp.route('/deploy', methods=['POST', 'OPTIONS'])
def deploy():
    if request.method == 'OPTIONS':
        return '', 204
    data = request.get_json() or {}
    mid = data.get('model_id')
    if not mid:
        return jsonify({'success': False, 'error': 'model_id required'}), 400
    return jsonify(deploy_model(mid)), 200


# ⭐ Level 3 — Learning endpoints
@training_bp.route('/learning', methods=['GET', 'OPTIONS'])
def learning_status():
    if request.method == 'OPTIONS':
        return '', 204
    return jsonify({
        'feedback': feedback_stats(),
        'progress': learning_progress(),
        'samples_needed': max(0, 10 - count_samples()),
    }), 200