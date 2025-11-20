#!/usr/bin/env python3
"""Queue antler detection tasks from a file of detection IDs."""

import sys
from celery import Celery
import os

# Celery setup
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

celery_app = Celery('thumper_counter', broker=REDIS_URL, backend=REDIS_URL)

# Read detection IDs from file
if len(sys.argv) < 2:
    print("Usage: python3 queue_from_file.py <file_with_detection_ids>")
    sys.exit(1)

filename = sys.argv[1]

print(f"[INFO] Reading detection IDs from {filename}")

with open(filename, 'r') as f:
    detection_ids = [line.strip() for line in f if line.strip()]

print(f"[INFO] Found {len(detection_ids)} detection IDs")
print(f"[INFO] Queuing antler detection tasks...")

queued = 0
for detection_id in detection_ids:
    celery_app.send_task(
        'worker.tasks.antler_detection.detect_antler_keypoints',
        args=[detection_id],
        queue='ml_processing'
    )
    queued += 1

    if queued % 100 == 0:
        print(f"[OK] Queued {queued}/{len(detection_ids)} tasks")

print(f"\n[OK] Successfully queued {queued} antler detection tasks")
print(f"[INFO] Estimated processing time: ~{(queued * 12) / 3600:.1f} hours")
