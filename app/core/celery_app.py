from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Celery app
app = Celery('auction_intelligence')

# Configure Celery
app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_default_queue='default',
    task_queues={
        'default': {
            'exchange': 'default',
            'routing_key': 'default',
        },
        'shipping': {
            'exchange': 'shipping',
            'routing_key': 'shipping',
        },
        'listing': {
            'exchange': 'listing',
            'routing_key': 'listing',
        }
    },
    task_routes={
        'shipping.*': {'queue': 'shipping'},
        'listing.*': {'queue': 'listing'},
    },
    beat_schedule={
        'shipping-train-model': {
            'task': 'shipping.train_risk_model',
            'schedule': crontab(hour='*/12'),  # Every 12 hours
        },
        'shipping-stats': {
            'task': 'shipping.get_shipping_stats',
            'schedule': crontab(minute='*/30'),  # Every 30 minutes
        },
        'listing-optimization': {
            'task': 'listing.optimize_listing',
            'schedule': crontab(hour='*/6'),  # Every 6 hours
        },
        'listing-stats': {
            'task': 'listing.get_listing_stats',
            'schedule': crontab(minute='*/15'),  # Every 15 minutes
        }
    }
)

# Auto-discover tasks
app.autodiscover_tasks([
    'src.services.tasks.shipping_tasks',
    'src.services.tasks.listing_tasks'
])

if __name__ == "__main__":
    app.start() 