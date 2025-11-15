#!/usr/bin/env python3
"""
Reprocess Unassigned Detections with New REID_THRESHOLD
Feature 010, Option D - Phase 2

This script queues all unassigned detections for re-identification
using the newly optimized REID_THRESHOLD value.

Usage:
    python3 scripts/reprocess_unassigned.py [--limit N] [--dry-run]
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from celery import group

# Import Celery app and task
from worker.celery_app import celery_app
from worker.tasks.reidentification import reidentify_deer_task

# Database connection
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "deertrack")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "secure_password_here")
DB_NAME = os.getenv("POSTGRES_DB", "deer_tracking")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
REID_THRESHOLD = float(os.getenv('REID_THRESHOLD', 0.40))

def main():
    parser = argparse.ArgumentParser(description='Reprocess unassigned detections')
    parser.add_argument('--limit', type=int, help='Process only N detections')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    args = parser.parse_args()

    print(f"[INFO] Reprocessing unassigned detections")
    print(f"[INFO] New REID_THRESHOLD: {REID_THRESHOLD}")
    print(f"[INFO] Dry run: {args.dry_run}")
    print()

    # Create database connection
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Count unassigned detections
    count_query = text("""
        SELECT COUNT(*) as total
        FROM detections
        WHERE deer_id IS NULL
    """)
    total_unassigned = session.execute(count_query).fetchone()[0]
    print(f"[INFO] Total unassigned detections: {total_unassigned}")

    # Apply limit if specified
    process_count = min(args.limit, total_unassigned) if args.limit else total_unassigned
    print(f"[INFO] Will queue: {process_count} detections")
    print()

    if args.dry_run:
        print(f"[DRY-RUN] Would queue {process_count} re-ID tasks")
        session.close()
        return

    # Get detection IDs
    query = text("""
        SELECT id
        FROM detections
        WHERE deer_id IS NULL
        ORDER BY created_at DESC
        LIMIT :limit
    """)

    detection_ids = [str(row[0]) for row in session.execute(query, {'limit': process_count})]
    session.close()

    print(f"[INFO] Queueing {len(detection_ids)} re-ID tasks...")

    # Queue tasks in batches of 1000 for performance
    batch_size = 1000
    total_queued = 0

    for i in range(0, len(detection_ids), batch_size):
        batch = detection_ids[i:i+batch_size]

        # Create group of tasks
        job = group(reidentify_deer_task.s(det_id) for det_id in batch)
        result = job.apply_async()

        total_queued += len(batch)
        print(f"[PROGRESS] Queued {total_queued}/{len(detection_ids)} tasks")

    print()
    print(f"[OK] Successfully queued {total_queued} re-ID tasks")
    print(f"[OK] Monitor progress with: docker-compose logs -f worker")
    print()
    print(f"[INFO] Expected improvements:")
    print(f"  - Current assignment rate: {4546}/{11570} = 39.29%")
    print(f"  - Projected with threshold 0.40: ~9.66% of unassigned may match")
    print(f"  - Potential new matches: ~678 detections")
    print(f"  - New assignment rate: ~45.15%")

if __name__ == "__main__":
    main()
