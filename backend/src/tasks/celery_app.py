from celery import Celery
from celery.schedules import crontab
import os

def make_celery(app_name=__name__):
    """Create Celery app"""
    celery = Celery(
        app_name,
        broker=os.getenv('REDIS_URL', 'redis://localhost:6379'),
        backend=os.getenv('REDIS_URL', 'redis://localhost:6379')
    )
    
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=3600,
        task_soft_time_limit=3000,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=100,
        task_acks_late=True
    )
    
    # Scheduled tasks
    celery.conf.beat_schedule = {
        'cleanup-old-logs': {
            'task': 'tasks.scheduled_tasks.cleanup_old_logs',
            'schedule': crontab(hour=0, minute=0),
        },
        'check-system-health': {
            'task': 'tasks.scheduled_tasks.check_system_health',
            'schedule': crontab(minute='*/5'),
        },
        'auto-upgrade-models': {
            'task': 'tasks.scheduled_tasks.auto_upgrade_models',
            'schedule': crontab(hour=2, minute=0),
        },
        'send-daily-reports': {
            'task': 'tasks.scheduled_tasks.send_daily_reports',
            'schedule': crontab(hour=9, minute=0),
        }
    }
    
    return celery

celery = make_celery()