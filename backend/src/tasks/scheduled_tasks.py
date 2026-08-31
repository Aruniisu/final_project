from datetime import datetime, timedelta
import logging

from .celery_app import celery

logger = logging.getLogger(__name__)

@celery.task(name='tasks.scheduled_tasks.cleanup_old_logs')
def cleanup_old_logs():
    """Clean up old logs"""
    logger.info("Cleaning up old logs")
    
    try:
        from app import mongo
        threshold = datetime.now() - timedelta(days=30)
        
        # Delete old audit logs
        result = mongo.db.audit_logs.delete_many({
            'timestamp': {'$lt': threshold}
        })
        logger.info(f"Deleted {result.deleted_count} old audit logs")
        
        # Delete old pipeline logs
        result = mongo.db.pipelines.update_many(
            {},
            {'$pull': {'logs': {'timestamp': {'$lt': threshold.isoformat()}}}}
        )
        logger.info(f"Cleaned pipeline logs")
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")

@celery.task(name='tasks.scheduled_tasks.check_system_health')
def check_system_health():
    """Check system health"""
    logger.info("Checking system health")
    
    try:
        from app import mongo
        
        # Check database connection
        mongo.db.command('ping')
        
        # Get system stats
        stats = {
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'pipelines_running': mongo.db.pipelines.count_documents({'status': 'running'}),
            'deployments_today': mongo.db.deployments.count_documents({
                'created_at': {'$gte': datetime.now().replace(hour=0, minute=0, second=0)}
            })
        }
        
        logger.info(f"System health: {stats}")
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")

@celery.task(name='tasks.scheduled_tasks.auto_upgrade_models')
def auto_upgrade_models():
    """Auto upgrade AI models"""
    logger.info("Checking for model upgrades")
    
    try:
        from agents.auto_upgrader import auto_upgrader
        if auto_upgrader.config.get('auto_update', True):
            result = auto_upgrader.trigger_manual_update()
            logger.info(f"Auto upgrade result: {result}")
        
    except Exception as e:
        logger.error(f"Auto upgrade failed: {str(e)}")

@celery.task(name='tasks.scheduled_tasks.send_daily_reports')
def send_daily_reports():
    """Send daily reports to users"""
    logger.info("Sending daily reports")
    
    try:
        from app import mongo
        from models.user import User
        from models.notification import Notification
        
        user_model = User(mongo)
        notification_model = Notification(mongo)
        
        # Get all users
        users = user_model.get_all()
        
        for user in users:
            # Get daily stats
            stats = {
                'deployments': mongo.db.deployments.count_documents({
                    'user_id': user['_id'],
                    'created_at': {'$gte': datetime.now().replace(hour=0, minute=0, second=0)}
                }),
                'pipelines': mongo.db.pipelines.count_documents({
                    'user_id': user['_id'],
                    'status': 'success'
                })
            }
            
            # Create notification
            notification_model.create(
                user['_id'],
                'Daily Report 📊',
                f"Today's summary: {stats['deployments']} deployments, {stats['pipelines']} successful pipelines",
                'info'
            )
            
        logger.info(f"Sent daily reports to {len(users)} users")
        
    except Exception as e:
        logger.error(f"Daily reports failed: {str(e)}")