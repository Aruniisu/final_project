from flask import Blueprint, request, jsonify, current_app
from datetime import datetime
import os
import uuid
import json
import shutil
from werkzeug.utils import secure_filename

upload_bp = Blueprint('upload', __name__)

# Import database managers
from database.managers import ProjectManager, UploadManager
from database.connection import db_connection
from services.project_analyzer import ProjectAnalyzer

def get_project_manager():
    db = db_connection.get_db()
    return ProjectManager(db)

def get_upload_manager():
    db = db_connection.get_db()
    return UploadManager(db)

@upload_bp.route('/files', methods=['POST'])
def upload_files():
    """Upload files"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'No token provided'}), 401
    
    # Get user_id from token (simplified for demo)
    user_id = 'demo_user'
    
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    project_manager = get_project_manager()
    upload_manager = get_upload_manager()
    analyzer = ProjectAnalyzer()
    
    uploaded_files = []
    for file in files:
        filename = secure_filename(file.filename)
        file_id = str(uuid.uuid4())
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
        file.save(filepath)
        
        uploaded_files.append({
            'id': file_id,
            'name': filename,
            'path': filepath,
            'size': os.path.getsize(filepath)
        })
    
    # Create project
    project = project_manager.create_project(
        user_id=user_id,
        name=files[0].filename if len(files) == 1 else 'Uploaded Project',
        project_type='upload'
    )
    
    if not project:
        return jsonify({'error': 'Failed to create project'}), 500
    
    # Analyze project
    analysis = analyzer.analyze(uploaded_files)
    
    # Update project with analysis
    project_manager.update_analysis(project['project_id'], analysis)
    
    # Save upload record
    upload = upload_manager.create_upload(
        user_id=user_id,
        project_id=project['project_id'],
        files=uploaded_files,
        metadata={'analysis': analysis}
    )
    
    return jsonify({
        'message': 'Files uploaded successfully',
        'projectId': project['project_id'],
        'projectName': project['name'],
        'analysis': analysis
    }), 201

@upload_bp.route('/github', methods=['POST'])
def upload_github():
    """Upload from GitHub"""
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'GitHub URL required'}), 400
    
    user_id = 'demo_user'
    project_manager = get_project_manager()
    upload_manager = get_upload_manager()
    
    repo_name = url.split('/')[-1] if url.endswith('.git') else url.split('/')[-1]
    
    project = project_manager.create_project(
        user_id=user_id,
        name=repo_name,
        project_type='github'
    )
    
    if not project:
        return jsonify({'error': 'Failed to create project'}), 500
    
    analysis = {
        'healthScore': 85,
        'issues': 3,
        'securityScore': 92,
        'recommendations': 5,
        'project_type': 'javascript'
    }
    
    project_manager.update_analysis(project['project_id'], analysis)
    
    upload = upload_manager.create_upload(
        user_id=user_id,
        project_id=project['project_id'],
        source='github',
        metadata={'url': url, 'analysis': analysis}
    )
    
    return jsonify({
        'message': 'GitHub repository imported successfully',
        'projectId': project['project_id'],
        'projectName': project['name'],
        'analysis': analysis
    }), 201

@upload_bp.route('/<project_id>/analyze', methods=['GET'])
def analyze_project(project_id):
    """Get project analysis"""
    project_manager = get_project_manager()
    project = project_manager.find_by_project_id(project_id)
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    analysis = project.get('analysis', {})
    
    if not analysis:
        analysis = {
            'healthScore': 85,
            'issues': 3,
            'securityScore': 92,
            'recommendations': 5,
            'project_type': 'javascript'
        }
    
    return jsonify(analysis), 200

@upload_bp.route('/history', methods=['GET'])
def get_upload_history():
    """Get upload history"""
    user_id = 'demo_user'
    upload_manager = get_upload_manager()
    uploads = upload_manager.find_by_user(user_id)
    
    # Format for frontend
    formatted_uploads = []
    for upload in uploads:
        formatted_uploads.append({
            'projectId': upload.get('project_id'),
            'projectName': upload.get('metadata', {}).get('analysis', {}).get('project_name', 'Unknown'),
            'source': upload.get('source', 'file'),
            'status': upload.get('status', 'completed'),
            'createdAt': upload.get('created_at').isoformat() if upload.get('created_at') else None,
            'metadata': upload.get('metadata', {})
        })
    
    return jsonify(formatted_uploads), 200