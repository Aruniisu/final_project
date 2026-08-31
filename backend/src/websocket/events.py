from flask_socketio import emit, join_room, leave_room
from flask import request, current_app
import json
from datetime import datetime

def register_events(socketio):
    """Register all WebSocket events"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        print(f"Client connected: {request.sid}")
        
        # Send initial data
        emit('connected', {
            'message': 'Connected to Smart DevOps WebSocket',
            'timestamp': datetime.now().isoformat(),
            'sid': request.sid
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print(f"Client disconnected: {request.sid}")
    
    @socketio.on('join_pipeline')
    def handle_join_pipeline(data):
        """Join pipeline room"""
        pipeline_id = data.get('pipeline_id')
        if pipeline_id:
            room = f"pipeline_{pipeline_id}"
            join_room(room)
            emit('joined_pipeline', {
                'pipeline_id': pipeline_id,
                'message': f'Joined pipeline: {pipeline_id}'
            })
    
    @socketio.on('leave_pipeline')
    def handle_leave_pipeline(data):
        """Leave pipeline room"""
        pipeline_id = data.get('pipeline_id')
        if pipeline_id:
            room = f"pipeline_{pipeline_id}"
            leave_room(room)
            emit('left_pipeline', {
                'pipeline_id': pipeline_id,
                'message': f'Left pipeline: {pipeline_id}'
            })
    
    @socketio.on('join_deployment')
    def handle_join_deployment(data):
        """Join deployment room"""
        deployment_id = data.get('deployment_id')
        if deployment_id:
            room = f"deployment_{deployment_id}"
            join_room(room)
            emit('joined_deployment', {
                'deployment_id': deployment_id,
                'message': f'Joined deployment: {deployment_id}'
            })
    
    @socketio.on('leave_deployment')
    def handle_leave_deployment(data):
        """Leave deployment room"""
        deployment_id = data.get('deployment_id')
        if deployment_id:
            room = f"deployment_{deployment_id}"
            leave_room(room)
            emit('left_deployment', {
                'deployment_id': deployment_id,
                'message': f'Left deployment: {deployment_id}'
            })
    
    @socketio.on('chat_message')
    def handle_chat_message(data):
        """Handle chat message"""
        message = data.get('message', '')
        user = data.get('user', 'Anonymous')
        room = data.get('room', 'chat')
        
        # Process message with AI
        from agents.orchestrator import orchestrator
        response = orchestrator.process_query(message)
        
        # Broadcast to room
        emit('chat_response', {
            'user': user,
            'message': message,
            'response': response.get('response', ''),
            'timestamp': datetime.now().isoformat()
        }, room=room)
    
    @socketio.on('typing')
    def handle_typing(data):
        """Handle typing indicator"""
        user = data.get('user', 'Anonymous')
        room = data.get('room', 'chat')
        is_typing = data.get('is_typing', False)
        
        emit('user_typing', {
            'user': user,
            'is_typing': is_typing
        }, room=room)
    
    @socketio.on('notification_read')
    def handle_notification_read(data):
        """Handle notification read"""
        notification_id = data.get('notification_id')
        user_id = data.get('user_id')
        
        if notification_id and user_id:
            # Update in database
            from app import mongo
            mongo.db.notifications.update_one(
                {'notification_id': notification_id, 'user_id': user_id},
                {'$set': {'read': True, 'read_at': datetime.now()}}
            )
            
            emit('notification_read_ack', {
                'notification_id': notification_id,
                'message': 'Notification marked as read'
            }, room=f"user_{user_id}")