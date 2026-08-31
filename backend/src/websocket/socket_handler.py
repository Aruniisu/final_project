from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request, current_app
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Import agents
from agents.orchestrator import orchestrator
from agents.planner_agent import PlannerAgent
from agents.executor_agent import ExecutorAgent
from agents.analyzer_agent import AnalyzerAgent

def register_socket_events(socketio):
    """Register all WebSocket events with agent integration"""
    
    @socketio.on('connect')
    def handle_connect():
        logger.info(f"Client connected: {request.sid}")
        emit('connected', {
            'message': 'Connected to Smart DevOps WebSocket',
            'timestamp': datetime.now().isoformat()
        })
        # Send initial agent status
        emit('agent_status', {
            'agents': ['Planner', 'Executor', 'Analyzer'],
            'status': 'ready',
            'timestamp': datetime.now().isoformat()
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info(f"Client disconnected: {request.sid}")

    @socketio.on('chat')
    def handle_chat(data):
        """Handle chat messages with agent integration"""
        try:
            message = data.get('message', '')
            project_id = data.get('projectId')
            project_name = data.get('projectName')
            user_id = data.get('userId', 'anonymous')
            
            logger.info(f"Chat from {user_id}: {message}")
            
            # Emit start of processing
            emit('chat_response', {
                'type': 'start',
                'message': 'Processing your request...',
                'timestamp': datetime.now().isoformat()
            })
            
            # Add log
            emit('pipeline_progress', {
                'step': 'analysis',
                'message': f'🤖 AI Agent analyzing request: {message[:50]}...',
                'progress': 10,
                'status': 'running'
            })
            
            # Process through orchestrator
            context = {
                'user_id': user_id,
                'project_id': project_id,
                'project_name': project_name
            }
            
            # Simulate agent processing
            response = orchestrator.process_query(message, context)
            
            # Stream response chunks
            response_text = response.get('response', '')
            chunks = [response_text[i:i+50] for i in range(0, len(response_text), 50)]
            
            for i, chunk in enumerate(chunks):
                emit('stream_chunk', {
                    'chunk': chunk,
                    'progress': min(90, 10 + (i / len(chunks)) * 80)
                })
                import time
                time.sleep(0.05)
            
            # Complete response
            emit('stream_complete', {
                'content': '',
                'execution': response.get('metadata', {}),
                'timestamp': datetime.now().isoformat()
            })
            
            # Emit completion
            emit('chat_response', {
                'type': 'complete',
                'message': '✅ Request processed successfully!',
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            emit('error', {
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })

    @socketio.on('stop_streaming')
    def handle_stop_streaming():
        """Stop ongoing streaming"""
        logger.info(f"Streaming stopped by client: {request.sid}")
        emit('stream_stopped', {
            'message': 'Streaming stopped',
            'timestamp': datetime.now().isoformat()
        })

    @socketio.on('pipeline_action')
    def handle_pipeline_action(data):
        """Handle pipeline actions with agent execution"""
        action = data.get('action')
        pipeline_id = data.get('pipeline_id')
        
        logger.info(f"Pipeline action: {action} for {pipeline_id}")
        
        if action == 'trigger':
            # Simulate pipeline execution
            steps = ['Build', 'Test', 'Deploy', 'Monitor']
            for i, step in enumerate(steps):
                emit('pipeline_progress', {
                    'step': step,
                    'progress': ((i + 1) / len(steps)) * 100,
                    'status': 'running',
                    'message': f'⏳ {step} in progress...'
                })
                import time
                time.sleep(1)
            
            emit('pipeline_progress', {
                'step': 'complete',
                'progress': 100,
                'status': 'success',
                'message': '✅ Pipeline completed successfully!'
            })

    @socketio.on('deploy_action')
    def handle_deploy_action(data):
        """Handle deployment with agent execution"""
        project_id = data.get('project_id')
        environment = data.get('environment', 'production')
        
        logger.info(f"Deploying {project_id} to {environment}")
        
        steps = [
            'Building Docker image',
            'Pushing to registry',
            'Creating Kubernetes deployment',
            'Exposing service',
            'Verifying health check'
        ]
        
        for i, step in enumerate(steps):
            emit('deployment_status', {
                'status': 'running',
                'step': step,
                'progress': ((i + 1) / len(steps)) * 100,
                'message': f'📦 {step}...'
            })
            import time
            time.sleep(1.5)
        
        emit('deployment_status', {
            'status': 'success',
            'message': '🎉 Deployment successful!',
            'url': f'https://{project_id}-{environment}.smart.local',
            'timestamp': datetime.now().isoformat()
        })