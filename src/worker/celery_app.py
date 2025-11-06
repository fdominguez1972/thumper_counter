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
import sys
from pathlib import Path
from celery import Celery
from kombu import Queue


# Model file validation (FR-011)
def validate_model_files():
    """
    Validate that required ML model files exist and are valid.

    This function is called at worker startup to ensure the worker doesn't
    start without the required model files. This prevents confusing errors
    later when tasks try to load models.

    Raises:
        SystemExit: If any required model file is missing or invalid

    Requirements:
        - FR-011: System MUST validate YOLOv8 model file exists at startup
    """
    # Define required model files
    # Path is relative to project root when running in Docker
    model_files = {
        'yolov8n_deer.pt': 'src/models/yolov8n_deer.pt',
    }

    errors = []

    for model_name, model_path in model_files.items():
        full_path = Path(model_path)

        # Check if file exists
        if not full_path.exists():
            errors.append(
                f"[FAIL] Model file not found: {model_path}\n"
                f"       Expected location: {full_path.absolute()}\n"
                f"       Please copy model file from original project or download from source."
            )
            continue

        # Check if file size is reasonable (corruption check)
        # YOLOv8n model should be ~20-25MB
        file_size_mb = full_path.stat().st_size / (1024 * 1024)
        if file_size_mb < 20:
            errors.append(
                f"[FAIL] Model file appears corrupted: {model_path}\n"
                f"       File size: {file_size_mb:.2f}MB (expected >20MB)\n"
                f"       Please re-download or copy the model file."
            )
            continue

        print(f"[OK] Model file validated: {model_name} ({file_size_mb:.2f}MB)")

    # If any errors, print all and exit
    if errors:
        print("\n" + "=" * 80)
        print("[FAIL] Worker startup failed: Required model files missing or invalid")
        print("=" * 80)
        for error in errors:
            print(error)
        print("=" * 80)
        print("\n[INFO] Worker will not start. Please fix the above errors and try again.\n")
        sys.exit(1)


# Validate model files before starting worker
print("[INFO] Validating model files...")
validate_model_files()
print("[OK] All model files validated successfully\n")


# NOTE: With threads pool, we DON'T preload the model
# WHY: Threads pool uses threading instead of fork(), so CUDA works without preloading
# Each thread will load its own model instance on-demand (thread-safe)
print("[INFO] Using threads pool - models will be loaded on-demand per thread")
print()


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
        'worker.tasks.process_images',
        'worker.tasks.detection',
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
        'worker.tasks.process_images.*': {'queue': 'ml_processing'},
        'worker.tasks.detection.*': {'queue': 'ml_processing'},
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
    'worker.tasks.process_images.detect_deer': {
        'rate_limit': '10/m',  # WHY: Prevent GPU overload
        'time_limit': 300,  # 5 minutes
    },
    'worker.tasks.process_images.classify_deer': {
        'rate_limit': '20/m',  # WHY: Lighter than detection
        'time_limit': 180,  # 3 minutes
    },
    'worker.tasks.process_images.reidentify_deer': {
        'rate_limit': '20/m',
        'time_limit': 180,  # 3 minutes
    },
}


# Autodiscover tasks
app.autodiscover_tasks(['worker.tasks'])


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
