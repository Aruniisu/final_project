from celery import Task
from datetime import datetime
import time
import random
import logging

from .celery_app import celery

logger = logging.getLogger(__name__)

class BaseTask(Task):
    """Base task with retry logic"""
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 300
    retry_jitter = True

@celery.task(base=BaseTask, name='tasks.async_tasks.run_pipeline')
def run_pipeline(pipeline_id):
    """Run a pipeline asynchronously"""
    logger.info(f"Starting pipeline: {pipeline_id}")
    
    try:
        # Simulate pipeline steps
        steps = ['build', 'test', 'deploy', 'monitor']
        
        for i, step in enumerate(steps):
            logger.info(f"Running step: {step}")
            # Simulate work
            time.sleep(random.randint(1, 5))
            
            # Update progress
            progress = int((i + 1) / len(steps) * 100)
            
            # Emit progress via WebSocket
            from websocket.socket_handler import socketio
            socketio.emit('pipeline_progress', {
                'pipeline_id': pipeline_id,
                'step': step,
                'progress': progress,
                'status': 'running'
            })
        
        # Update pipeline status
        from models.pipeline import Pipeline
        from app import mongo
        pipeline_model = Pipeline(mongo)
        pipeline_model.update_status(pipeline_id, 'success', 100)
        
        logger.info(f"Pipeline {pipeline_id} completed successfully")
        return {'pipeline_id': pipeline_id, 'status': 'success'}
        
    except Exception as e:
        logger.error(f"Pipeline {pipeline_id} failed: {str(e)}")
        from models.pipeline import Pipeline
        from app import mongo
        pipeline_model = Pipeline(mongo)
        pipeline_model.update_status(pipeline_id, 'failed')
        raise

@celery.task(base=BaseTask, name='tasks.async_tasks.retry_pipeline')
def retry_pipeline(pipeline_id):
    """Retry a failed pipeline"""
    logger.info(f"Retrying pipeline: {pipeline_id}")
    return run_pipeline.delay(pipeline_id)

@celery.task(base=BaseTask, name='tasks.async_tasks.train_model')
def train_model(training_id):
    """Train a model asynchronously"""
    logger.info(f"Starting training: {training_id}")
    
    try:
        from models.training import Training
        from app import mongo
        training_model = Training(mongo)
        training_model.update_status(training_id, 'running', 0)
        
        # Simulate training
        total_epochs = 10
        for epoch in range(total_epochs):
            # Simulate training work
            time.sleep(random.randint(2, 5))
            
            progress = int((epoch + 1) / total_epochs * 100)
            accuracy = 0.7 + (epoch / total_epochs) * 0.25
            
            training_model.update_status(
                training_id,
                'running',
                progress,
                {'accuracy': accuracy, 'loss': 1 - accuracy}
            )
        
        training_model.update_status(
            training_id,
            'completed',
            100,
            {'accuracy': 0.95, 'loss': 0.05}
        )
        
        logger.info(f"Training {training_id} completed")
        return {'training_id': training_id, 'status': 'completed'}
        
    except Exception as e:
        logger.error(f"Training {training_id} failed: {str(e)}")
        from models.training import Training
        from app import mongo
        training_model = Training(mongo)
        training_model.update_status(training_id, 'failed')
        raise

@celery.task(name='tasks.async_tasks.analyze_project')
def analyze_project(project_id):
    """Analyze a project asynchronously"""
    logger.info(f"Analyzing project: {project_id}")
    
    # Simulate analysis
    time.sleep(random.randint(5, 15))
    
    analysis = {
        'project_id': project_id,
        'healthScore': random.randint(70, 95),
        'issues': random.randint(0, 10),
        'securityScore': random.randint(70, 95),
        'recommendations': random.randint(0, 10)
    }
    
    # Save analysis results
    from models.project import Project
    from app import mongo
    project_model = Project(mongo)
    project_model.update(project_id, {'analysis': analysis})
    
    return analysis

@celery.task(name='tasks.async_tasks.send_notification')
def send_notification(user_id, title, message, type='info'):
    """Send notification to user"""
    from models.notification import Notification
    from app import mongo
    notification_model = Notification(mongo)
    notification_model.create(user_id, title, message, type)
    
    # Send email if enabled
    # send_email.delay(user_id, title, message)
    
    return {'status': 'sent', 'user_id': user_id}