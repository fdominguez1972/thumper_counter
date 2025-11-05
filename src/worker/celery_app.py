"""
Celery Application Configuration
Version: 1.0.0
Date: 2025-11-04

WHY Celery: Heavy ML processing must not block API responses. Celery provides
retry logic, monitoring via Flower, and horizontal scaling.

WHY Redis: Fast, lightweight message broker and result backend suitable for
our queue volumes. Supports task result expiration and priority queues.

This module sets up the Celery worker for asynchronous image processing tasks:
- Detection: YOLOv8n deer detection and bounding box extraction
- Classification: Buck/Doe/Fawn classification with ResNet50 backbone
- Re-identification: Individual deer tracking with metric learning embeddings

Environment Variables:
    REDIS_HOST: Redis server hostname (default: redis)
    REDIS_PORT: Redis server port (default: 6379)
    REDIS_DB: Redis database number (default: 0)
    POSTGRES_*: Database connection settings
"""

import os
from celery import Celery
from kombu import Queue


# Redis connection configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'


# Create Celery application
app = Celery(
    'thumper_counter',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        'src.worker.tasks.process_images',
    ]
)


# Celery Configuration
# WHY: Optimize for ML workload characteristics
app.conf.update(
    # Task serialization
    # WHY: JSON is safe and widely compatible
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',

    # Timezone
    timezone='America/Chicago',  # WHY: Hopkins Ranch is in Texas
    enable_utc=True,

    # Task routing
    task_routes={
        'src.worker.tasks.process_images.*': {'queue': 'ml_processing'},
    },

    # Queue definitions
    # WHY: Separate queues allow priority control and resource allocation
    task_queues=(
        Queue('ml_processing', routing_key='ml.#'),
        Queue('default', routing_key='default'),
    ),
    task_default_queue='default',
    task_default_exchange='tasks',
    task_default_exchange_type='topic',
    task_default_routing_key='default',

    # Result backend settings
    # WHY: Store results for status tracking via API
    result_backend=REDIS_URL,
    result_expires=3600,  # 1 hour - WHY: Results needed for UI display
    result_persistent=True,  # WHY: Survive Redis restart
    result_extended=True,  # WHY: Store additional metadata for debugging

    # Task execution settings
    # WHY: ML tasks are long-running, need longer timeouts
    task_track_started=True,
    task_time_limit=600,  # 10 minutes hard limit
    task_soft_time_limit=540,  # 9 minutes soft limit for cleanup

    # Task acknowledgment
    # WHY: Late ack ensures task retried if worker crashes during processing
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # WHY: GPU tasks should not prefetch

    # Worker settings
    # WHY: Prevent memory leaks from GPU operations
    worker_max_tasks_per_child=100,
    worker_disable_rate_limits=False,

    # Monitoring
    # WHY: Enable Flower monitoring interface
    worker_send_task_events=True,
    task_send_sent_event=True,

    # Retry policy
    # WHY: Transient GPU errors should be retried
    task_autoretry_for=(Exception,),
    task_retry_kwargs={'max_retries': 3},
    task_retry_backoff=True,
    task_retry_backoff_max=600,  # 10 minutes max backoff
    task_retry_jitter=True,  # WHY: Prevent thundering herd
)


# Task annotations for specific behaviors
# WHY: Different tasks have different resource requirements
app.conf.task_annotations = {
    'src.worker.tasks.process_images.detect_deer': {
        'rate_limit': '10/m',  # WHY: Prevent GPU overload
        'time_limit': 300,  # 5 minutes
    },
    'src.worker.tasks.process_images.classify_deer': {
        'rate_limit': '20/m',  # WHY: Lighter than detection
        'time_limit': 180,  # 3 minutes
    },
    'src.worker.tasks.process_images.reidentify_deer': {
        'rate_limit': '20/m',
        'time_limit': 180,  # 3 minutes
    },
}


# Autodiscover tasks
app.autodiscover_tasks(['src.worker.tasks'])


@app.task(bind=True)
def debug_task(self):
    """
    Debug task to test Celery configuration.

    Usage:
        from src.worker.celery_app import debug_task
        result = debug_task.delay()
        print(result.get())

    Returns:
        dict: Status information including worker hostname and task ID
    """
    print(f'[INFO] Request: {self.request!r}')
    return {
        'status': 'ok',
        'worker': self.request.hostname,
        'task_id': self.request.id
    }


if __name__ == '__main__':
    app.start()
