from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import json
import random

infrastructure_bp = Blueprint('infrastructure', __name__)

from middleware.auth import token_required
from middleware.rate_limit import rate_limit
from core.cache import cached

@infrastructure_bp.route('/clusters', methods=['GET'])
@token_required
@rate_limit(100, 60)
@cached(timeout=30, key_prefix='clusters')
def get_clusters(user):
    """Get all clusters"""
    # Mock data for demo
    clusters = [
        {
            'id': '1',
            'name': 'Production Cluster',
            'provider': 'aws',
            'status': 'healthy',
            'nodes': 12,
            'pods': 45,
            'cpuUsage': 68,
            'memoryUsage': 72,
            'diskUsage': 45,
            'uptime': '99.97%',
            'version': 'v1.28.0',
            'region': 'us-west-2',
            'cost': '$2,340.00'
        },
        {
            'id': '2',
            'name': 'Staging Cluster',
            'provider': 'gcp',
            'status': 'healthy',
            'nodes': 6,
            'pods': 20,
            'cpuUsage': 45,
            'memoryUsage': 55,
            'diskUsage': 30,
            'uptime': '99.5%',
            'version': 'v1.27.0',
            'region': 'us-central1',
            'cost': '$890.00'
        },
        {
            'id': '3',
            'name': 'Development Cluster',
            'provider': 'azure',
            'status': 'warning',
            'nodes': 3,
            'pods': 8,
            'cpuUsage': 85,
            'memoryUsage': 88,
            'diskUsage': 72,
            'uptime': '98.2%',
            'version': 'v1.26.0',
            'region': 'east-us',
            'cost': '$450.00'
        }
    ]
    
    return jsonify(clusters), 200

@infrastructure_bp.route('/clusters/<cluster_id>', methods=['GET'])
@token_required
@cached(timeout=30)
def get_cluster(user, cluster_id):
    """Get cluster details"""
    # Mock data
    cluster = {
        'id': cluster_id,
        'name': 'Production Cluster',
        'provider': 'aws',
        'status': 'healthy',
        'nodes': 12,
        'pods': 45,
        'cpuUsage': 68,
        'memoryUsage': 72,
        'diskUsage': 45,
        'uptime': '99.97%',
        'version': 'v1.28.0',
        'region': 'us-west-2',
        'cost': '$2,340.00'
    }
    
    return jsonify(cluster), 200

@infrastructure_bp.route('/scale', methods=['POST'])
@token_required
def scale_cluster(user):
    """Scale a cluster"""
    data = request.json
    cluster_id = data.get('cluster_id')
    replicas = data.get('replicas')
    
    if not cluster_id or not replicas:
        return jsonify({'error': 'cluster_id and replicas required'}), 400
    
    # Mock scaling
    return jsonify({
        'message': f'Cluster {cluster_id} scaled to {replicas} replicas',
        'cluster_id': cluster_id,
        'replicas': replicas,
        'status': 'scaling'
    }), 200

@infrastructure_bp.route('/resources', methods=['GET'])
@token_required
def get_resources(user):
    """Get resource usage"""
    return jsonify({
        'cpu': random.randint(20, 80),
        'memory': random.randint(30, 90),
        'disk': random.randint(10, 70),
        'network': random.randint(10, 50)
    }), 200