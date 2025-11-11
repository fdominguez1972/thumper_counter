#!/usr/bin/env python3
"""
Batch Re-Identification Script
Sprint 6: Process existing detections with re-ID

This script queues re-ID tasks for all existing detections that:
1. Have no deer_id assigned yet (not yet re-identified)
2. Have bbox size >= min_crop_size (50x50 pixels by default)
3. Have valid classification (doe, fawn, mature, mid, young)

Usage:
    python3 scripts/batch_reidentify.py [--limit N] [--min-size SIZE] [--dry-run]

Options:
    --limit N         Only process first N detections (default: all)
    --min-size SIZE   Minimum bbox dimension in pixels (default: 50)
    --dry-run         Show what would be done without queuing tasks
    --help            Show this help message
"""

import sys
import argparse
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from celery import Celery
from backend.core.database import SessionLocal
from backend.models.detection import Detection

# Celery configuration
# Use internal Redis service name when running from container
REDIS_HOST = 'redis'  # Docker service name
REDIS_PORT = 6379     # Internal port
REDIS_DB = 0
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

# Valid deer classifications
DEER_CLASSES = {'doe', 'fawn', 'mature', 'mid', 'young'}


def get_reidentifiable_detections(db, min_size=50, limit=None):
    """
    Get detections that can be re-identified.

    Filters:
    - No deer_id assigned (not yet re-identified)
    - Bbox width and height >= min_size
    - Valid deer classification

    Args:
        db: Database session
        min_size: Minimum bbox dimension (pixels)
        limit: Maximum number to return (None = all)

    Returns:
        List of Detection records
    """
    query = (
        db.query(Detection)
        .filter(Detection.deer_id.is_(None))
        .filter(Detection.classification.in_(DEER_CLASSES))
        .filter(Detection.bbox.isnot(None))
    )

    # Get all detections and filter by bbox size in Python
    # (SQLAlchemy JSON ops are complex, easier to filter in Python)
    all_detections = query.all()

    filtered = []
    for det in all_detections:
        if det.bbox:
            width = det.bbox.get('width', 0)
            height = det.bbox.get('height', 0)
            if width >= min_size and height >= min_size:
                filtered.append(det)
                if limit and len(filtered) >= limit:
                    break

    return filtered


def queue_reid_tasks(detections, dry_run=False):
    """
    Queue re-ID tasks for detections.

    Args:
        detections: List of Detection records
        dry_run: If True, don't actually queue tasks

    Returns:
        List of task IDs (empty if dry_run=True)
    """
    if dry_run:
        print(f"[DRY RUN] Would queue {len(detections)} re-ID tasks")
        return []

    # Connect to Celery
    celery_app = Celery(
        'batch_reid',
        broker=REDIS_URL,
        backend=REDIS_URL
    )

    task_ids = []
    batch_size = 100
    total = len(detections)

    print(f"[INFO] Queuing {total} re-ID tasks...")

    for i, detection in enumerate(detections, 1):
        # Queue re-ID task
        result = celery_app.send_task(
            'worker.tasks.reidentification.reidentify_deer_task',
            args=[str(detection.id)],
            queue='ml_processing'
        )
        task_ids.append(result.id)

        # Progress update
        if i % batch_size == 0 or i == total:
            percent = (i / total) * 100
            print(f"[OK] Queued {i}/{total} tasks ({percent:.1f}%)")

    return task_ids


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Batch re-identify existing detections',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Only process first N detections (default: all)'
    )
    parser.add_argument(
        '--min-size',
        type=int,
        default=50,
        help='Minimum bbox dimension in pixels (default: 50)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without queuing tasks'
    )

    args = parser.parse_args()

    print("=" * 70)
    print("BATCH RE-IDENTIFICATION")
    print("=" * 70)
    print(f"Min bbox size: {args.min_size}x{args.min_size} pixels")
    print(f"Limit: {args.limit or 'none (process all)'}")
    print(f"Dry run: {args.dry_run}")
    print("=" * 70)
    print()

    # Get database session
    db = SessionLocal()

    try:
        # Get detections to process
        print("[INFO] Finding detections to re-identify...")
        detections = get_reidentifiable_detections(
            db,
            min_size=args.min_size,
            limit=args.limit
        )

        if not detections:
            print("[WARN] No detections found matching criteria")
            print()
            print("Criteria:")
            print(f"  - No deer_id assigned")
            print(f"  - Bbox size >= {args.min_size}x{args.min_size}")
            print(f"  - Classification in {DEER_CLASSES}")
            return 0

        print(f"[OK] Found {len(detections)} detections to process")
        print()

        # Show sample detections
        print("Sample detections:")
        for i, det in enumerate(detections[:5], 1):
            width = det.bbox.get('width', 0)
            height = det.bbox.get('height', 0)
            print(f"  {i}. {str(det.id)[:8]}... "
                  f"class={det.classification}, "
                  f"size={width}x{height}, "
                  f"conf={det.confidence:.2f}")

        if len(detections) > 5:
            print(f"  ... and {len(detections) - 5} more")
        print()

        # Queue tasks
        start_time = time.time()
        task_ids = queue_reid_tasks(detections, dry_run=args.dry_run)
        duration = time.time() - start_time

        if not args.dry_run:
            print()
            print("=" * 70)
            print("[OK] BATCH QUEUING COMPLETE")
            print("=" * 70)
            print(f"Detections queued: {len(detections)}")
            print(f"Task IDs created: {len(task_ids)}")
            print(f"Queuing duration: {duration:.2f}s")
            print()
            print("Monitor progress with:")
            print("  docker-compose logs -f worker | grep 're-ID'")
            print("  http://localhost:5555 (Flower)")
            print()
            print("Check results:")
            print("  SELECT COUNT(*) FROM detections WHERE deer_id IS NOT NULL;")
            print("  SELECT COUNT(*) FROM deer;")
            print("=" * 70)
        else:
            print("[DRY RUN] No tasks queued")

        return 0

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()


if __name__ == '__main__':
    sys.exit(main())
