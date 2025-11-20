#!/usr/bin/env python3
"""
Queue all unassigned detections for Re-ID processing with optimized threshold.

This script:
1. Finds all detections where deer_id IS NULL
2. Filters to deer classifications (buck, doe, fawn)
3. Queues each detection for reidentify_deer_task
4. Monitors queuing progress

Usage:
    docker-compose exec -T backend python3 /app/scripts/queue_all_reid.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import time
from datetime import datetime

# Database connection
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'deertrack')}:{os.getenv('POSTGRES_PASSWORD', 'secure_password_here')}@{os.getenv('POSTGRES_HOST', 'db')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'deer_tracking')}"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Import Celery app
from src.worker.celery_app import celery_app
from src.worker.tasks.reidentification import reidentify_deer_task

def queue_all_detections():
    """Queue all unassigned detections for Re-ID processing."""

    session = Session()

    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting Re-ID queue process...")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] REID_THRESHOLD={os.getenv('REID_THRESHOLD', '0.50')}")

        # Get all unassigned detections with deer classifications
        query = text("""
            SELECT d.id, i.filename, d.classification
            FROM detections d
            JOIN images i ON d.image_id = i.id
            WHERE d.deer_id IS NULL
            AND d.classification IN ('buck', 'doe', 'fawn')
            ORDER BY i.timestamp ASC
        """)

        result = session.execute(query)
        detections = result.fetchall()

        total = len(detections)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Found {total} detections to process")

        if total == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] No detections to queue. Exiting.")
            return

        # Queue detections in batches
        batch_size = 100
        queued = 0
        start_time = time.time()

        for i, (detection_id, filename, classification) in enumerate(detections):
            # Queue the Re-ID task
            reidentify_deer_task.apply_async(
                args=[str(detection_id)],
                queue='ml_processing'
            )

            queued += 1

            # Progress update every batch
            if (i + 1) % batch_size == 0 or (i + 1) == total:
                elapsed = time.time() - start_time
                rate = queued / elapsed if elapsed > 0 else 0
                remaining = total - queued
                eta_seconds = remaining / rate if rate > 0 else 0
                eta_minutes = eta_seconds / 60

                print(f"[{datetime.now().strftime('%H:%M:%S')}] Queued {queued}/{total} ({queued*100.0/total:.1f}%) - {rate:.1f} tasks/sec - ETA: {eta_minutes:.1f} min")

        elapsed = time.time() - start_time
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] [COMPLETE] Queued {queued} detections in {elapsed:.1f}s")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Queue rate: {queued/elapsed:.1f} tasks/sec")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Workers will now process with REID_THRESHOLD=0.50")

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [ERROR] {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    queue_all_detections()
