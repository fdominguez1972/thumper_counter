"""
Celery client for backend API.

WHY separate file: Avoids circular imports between main.py and API modules.
Backend uses this to queue tasks without importing worker code.
"""

import os
from celery import Celery

# Redis configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

# Create Celery client for sending tasks
celery_app = Celery(
    'thumper_counter',
    broker=REDIS_URL,
    backend=REDIS_URL,
)

__all__ = ['celery_app']
