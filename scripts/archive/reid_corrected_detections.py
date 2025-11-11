#!/usr/bin/env python3
"""
Re-identify corrected detections to update deer profiles.

This script queues re-ID tasks for all valid detections that have been
manually corrected by the user. This updates deer profiles to reflect
the corrected classifications.

Usage:
    python3 scripts/reid_corrected_detections.py
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from celery import Celery

from backend.models.detection import Detection


# Database connection
POSTGRES_USER = os.getenv("POSTGRES_USER", "deertrack")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secure_password_here")
POSTGRES_DB = os.getenv("POSTGRES_DB", "deer_tracking")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Redis/Celery connection
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Create Celery app for task queueing
celery_app = Celery("thumper_counter", broker=REDIS_URL, backend=REDIS_URL)

# Deer classifications (exclude non-deer like cattle, pig, etc.)
DEER_CLASSIFICATIONS = ["buck", "doe", "fawn", "unknown", "mature", "mid", "young"]


def main():
    """Queue re-ID tasks for all corrected deer detections."""

    print("=" * 70)
    print("[INFO] Re-Identification: Corrected Detections")
    print("=" * 70)

    # Create database session
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Query for corrected deer detections
        print("\n[INFO] Querying corrected deer detections...")
        detections = db.query(Detection).filter(
            and_(
                Detection.corrected_classification.isnot(None),
                Detection.is_valid == True,
                Detection.corrected_classification.in_(DEER_CLASSIFICATIONS)
            )
        ).all()

        total_detections = len(detections)
        print(f"[OK] Found {total_detections} corrected deer detections")

        if total_detections == 0:
            print("[INFO] No detections to process. Exiting.")
            return

        # Show breakdown by classification
        from collections import Counter
        classification_counts = Counter(det.corrected_classification for det in detections)
        print("\n[INFO] Breakdown by corrected classification:")
        for classification, count in classification_counts.most_common():
            print(f"  - {classification}: {count}")

        # Ask for confirmation
        print(f"\n[INFO] This will queue {total_detections} re-ID tasks")
        print("[INFO] Existing deer_id assignments will be recalculated")
        print("[INFO] Deer profiles may be merged or split based on corrected data")
        response = input("\n[PROMPT] Continue? (y/n): ").strip().lower()

        if response != "y":
            print("[INFO] Aborted by user")
            return

        # Queue re-ID tasks
        print(f"\n[INFO] Queueing {total_detections} re-ID tasks...")
        queued_count = 0
        failed_count = 0

        for i, detection in enumerate(detections, 1):
            try:
                # Queue Celery task for re-identification
                task = celery_app.send_task(
                    "worker.tasks.reidentification.reidentify_deer_task",
                    args=[str(detection.id)],
                    queue="ml_processing"
                )
                queued_count += 1

                # Progress indicator every 100 detections
                if i % 100 == 0:
                    print(f"[INFO] Queued {i}/{total_detections} tasks...")

            except Exception as e:
                print(f"[ERROR] Failed to queue detection {detection.id}: {e}")
                failed_count += 1

        print("\n" + "=" * 70)
        print("[OK] Batch Re-ID Queueing Complete")
        print("=" * 70)
        print(f"Total detections: {total_detections}")
        print(f"Successfully queued: {queued_count}")
        print(f"Failed: {failed_count}")

        if queued_count > 0:
            print(f"\n[INFO] Estimated processing time: {queued_count * 2 / 60:.1f} minutes")
            print("[INFO] Monitor progress:")
            print("  - Flower UI: http://localhost:5555")
            print("  - Worker logs: docker-compose logs -f worker")
            print("\n[INFO] Deer profiles will update as tasks complete")
            print("[INFO] Refresh frontend to see updated classifications and groupings")

    except Exception as e:
        print(f"[ERROR] Script failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
