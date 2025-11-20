#!/usr/bin/env python3
"""
Queue antler detection tasks for all bucks that don't have antler keypoints yet.
Bypasses API to avoid timeout issues.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "src"))

from sqlalchemy import create_engine, func, or_
from sqlalchemy.orm import sessionmaker
from celery import Celery

# Database connection
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5433')
DB_USER = os.getenv('DB_USER', 'deertrack')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'deertrack123')
DB_NAME = os.getenv('DB_NAME', 'deer_tracking')

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Celery connection
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

# Import models
from backend.models import Detection, AntlerKeypoint

# Create database session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Create Celery app
celery_app = Celery('thumper_counter', broker=REDIS_URL, backend=REDIS_URL)


def get_bucks_without_antlers(db, limit=None):
    """
    Get all buck detections that don't have antler keypoints yet.

    Args:
        db: Database session
        limit: Optional limit on number of detections to return

    Returns:
        List of detection IDs
    """
    # Subquery to get detection IDs that have antler keypoints
    detections_with_antlers = db.query(AntlerKeypoint.detection_id).distinct().subquery()

    # Query for buck detections without antler keypoints
    query = db.query(Detection.id).filter(
        or_(
            Detection.corrected_classification == 'buck',
            Detection.classification == 'buck'
        )
    ).filter(
        ~Detection.id.in_(detections_with_antlers)
    )

    if limit:
        query = query.limit(limit)

    detections = query.all()
    return [str(d.id) for d in detections]


def queue_antler_detection_tasks(detection_ids, batch_size=100):
    """
    Queue antler detection tasks for a list of detection IDs.

    Args:
        detection_ids: List of detection ID strings
        batch_size: Number of tasks to queue per batch (for progress reporting)

    Returns:
        Number of tasks queued
    """
    total_queued = 0

    for i in range(0, len(detection_ids), batch_size):
        batch = detection_ids[i:i + batch_size]

        for detection_id in batch:
            celery_app.send_task(
                'worker.tasks.antler_detection.detect_antler_keypoints',
                args=[detection_id],
                queue='ml_processing'
            )
            total_queued += 1

        print(f"[OK] Queued {total_queued}/{len(detection_ids)} antler detection tasks")

    return total_queued


def main():
    """Main execution."""
    # Parse command line arguments
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"[INFO] Limiting to {limit} detections (from command line argument)")
        except ValueError:
            print(f"[WARN] Invalid limit '{sys.argv[1]}', processing all bucks without antlers")

    # Create database session
    db = SessionLocal()

    try:
        # Get statistics
        total_bucks = db.query(Detection).filter(
            or_(
                Detection.corrected_classification == 'buck',
                Detection.classification == 'buck'
            )
        ).count()

        bucks_with_antlers = db.query(AntlerKeypoint.detection_id).distinct().count()
        bucks_without_antlers = total_bucks - bucks_with_antlers

        print("\n" + "=" * 60)
        print("ANTLER DETECTION QUEUE STATUS")
        print("=" * 60)
        print(f"Total buck detections: {total_bucks}")
        print(f"Bucks with antler data: {bucks_with_antlers}")
        print(f"Bucks needing processing: {bucks_without_antlers}")
        print("=" * 60 + "\n")

        if bucks_without_antlers == 0:
            print("[OK] All bucks already have antler keypoint data!")
            return

        # Get detection IDs to process
        detection_ids = get_bucks_without_antlers(db, limit=limit)

        if not detection_ids:
            print("[OK] No bucks found needing antler detection")
            return

        print(f"[INFO] Found {len(detection_ids)} bucks to process\n")

        # Queue tasks
        queued = queue_antler_detection_tasks(detection_ids)

        print(f"\n[OK] Successfully queued {queued} antler detection tasks")
        print(f"[INFO] Processing time estimate: ~{(queued * 12) / 3600:.1f} hours")

    finally:
        db.close()


if __name__ == '__main__':
    main()
