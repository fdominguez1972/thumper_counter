#!/usr/bin/env python3
"""
Reprocess entire dataset with newly trained YOLOv8 model.

This script provides detailed control over the reprocessing workflow:
1. Optionally clear old detections
2. Reset image processing status
3. Queue images for processing
4. Monitor progress with real-time statistics

TURBO MODE: Use --turbo flag for non-interactive batch execution
  python3 reprocess_with_new_model.py --turbo --clear-mode all

Created: 2025-11-11
Author: Claude Code
"""
import os
import sys
import time
import argparse
import requests
from datetime import datetime
from typing import Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# API base URL
API_BASE = os.getenv('API_BASE_URL', 'http://localhost:8001')

# Database connection
pg_user = os.getenv('POSTGRES_USER', 'deertrack')
pg_pass = os.getenv('POSTGRES_PASSWORD', 'secure_password_here')
pg_host = os.getenv('POSTGRES_HOST', 'db')
pg_port = os.getenv('POSTGRES_PORT', '5432')
pg_db = os.getenv('POSTGRES_DB', 'deer_tracking')

DATABASE_URL = f'postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def print_header():
    """Print script header."""
    print("=" * 70)
    print("FULL DATASET REPROCESSING WITH NEW MODEL")
    print("=" * 70)
    print()
    print("This script will reprocess all images with the newly trained model:")
    print("  - Model: corrected_final_buck_doe")
    print("  - Accuracy: mAP50=0.851 (85.1%)")
    print("  - Classes: buck, doe, fawn, cattle, pig, raccoon")
    print("  - Training Data: 779 manually corrected images")
    print()
    print("=" * 70)
    print()


def get_current_stats(db) -> Dict:
    """Get current database statistics."""
    stats = {}

    # Image counts by status
    result = db.execute(text("""
        SELECT processing_status, COUNT(*) as count
        FROM images
        GROUP BY processing_status
    """)).fetchall()

    stats['images'] = {row[0]: row[1] for row in result}
    stats['total_images'] = sum(stats['images'].values())

    # Detection counts
    result = db.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN is_reviewed = true THEN 1 END) as reviewed,
            COUNT(CASE WHEN is_valid = true THEN 1 END) as valid,
            COUNT(CASE WHEN is_valid = false THEN 1 END) as invalid
        FROM detections
    """)).fetchone()

    stats['detections'] = {
        'total': result[0],
        'reviewed': result[1],
        'valid': result[2],
        'invalid': result[3]
    }

    # Classification breakdown
    result = db.execute(text("""
        SELECT
            COALESCE(corrected_classification, classification) as class,
            COUNT(*) as count
        FROM detections
        WHERE classification IS NOT NULL
        GROUP BY class
        ORDER BY count DESC
    """)).fetchall()

    stats['classifications'] = {row[0]: row[1] for row in result}

    return stats


def print_stats(stats: Dict, title: str = "Current Statistics"):
    """Print formatted statistics."""
    print(f"[INFO] {title}")
    print()

    # Image stats
    print("Images:")
    for status, count in sorted(stats['images'].items()):
        pct = (count / stats['total_images'] * 100) if stats['total_images'] > 0 else 0
        print(f"  {status:15s}: {count:6,d} ({pct:5.1f}%)")
    print(f"  {'TOTAL':15s}: {stats['total_images']:6,d}")
    print()

    # Detection stats
    print("Detections:")
    print(f"  {'Total':15s}: {stats['detections']['total']:6,d}")
    print(f"  {'Reviewed':15s}: {stats['detections']['reviewed']:6,d}")
    print(f"  {'Valid':15s}: {stats['detections']['valid']:6,d}")
    print(f"  {'Invalid':15s}: {stats['detections']['invalid']:6,d}")
    print()

    # Classification breakdown
    if stats['classifications']:
        print("Classifications:")
        for cls, count in sorted(stats['classifications'].items(), key=lambda x: x[1], reverse=True)[:10]:
            pct = (count / stats['detections']['total'] * 100) if stats['detections']['total'] > 0 else 0
            print(f"  {cls:15s}: {count:6,d} ({pct:5.1f}%)")
        print()


def clear_detections(db, mode: str) -> int:
    """
    Clear detections based on mode.

    Args:
        db: Database session
        mode: 'all', 'unreviewed', or 'none'

    Returns:
        Number of detections deleted
    """
    if mode == 'none':
        return 0

    if mode == 'all':
        print("[INFO] Clearing ALL detections...")
        result = db.execute(text("""
            DELETE FROM detections
            RETURNING id
        """))
        count = result.rowcount

        # Reset deer sighting counts
        db.execute(text("UPDATE deer SET sighting_count = 0"))

    elif mode == 'unreviewed':
        print("[INFO] Clearing unreviewed detections...")
        result = db.execute(text("""
            DELETE FROM detections
            WHERE is_reviewed = false OR is_reviewed IS NULL
            RETURNING id
        """))
        count = result.rowcount

        # Update deer sighting counts
        db.execute(text("""
            UPDATE deer d
            SET sighting_count = (
                SELECT COUNT(*)
                FROM detections det
                WHERE det.deer_id = d.id AND det.is_valid = true
            )
        """))

    db.commit()
    print(f"[OK] Deleted {count:,d} detections")
    print()
    return count


def reset_image_status(db) -> Tuple[int, int]:
    """
    Reset completed/failed images to pending.

    Returns:
        Tuple of (completed_reset, failed_reset)
    """
    print("[INFO] Resetting image processing status...")

    # Reset completed images
    completed = db.execute(text("""
        UPDATE images
        SET processing_status = 'pending'
        WHERE processing_status = 'completed'
        RETURNING id
    """)).rowcount

    # Reset failed images
    failed = db.execute(text("""
        UPDATE images
        SET processing_status = 'pending',
            error_message = NULL
        WHERE processing_status = 'failed'
        RETURNING id
    """)).rowcount

    db.commit()
    print(f"[OK] Reset {completed:,d} completed + {failed:,d} failed = {completed + failed:,d} total images")
    print()

    return completed, failed


def queue_images_for_processing(batch_size: int = 10000, turbo: bool = False) -> int:
    """
    Queue all pending images for processing.

    Args:
        batch_size: Number of images per batch
        turbo: If True, queue batches in parallel for maximum speed

    Returns:
        Total number of images queued
    """
    print("[INFO] Queuing images for processing...")
    print(f"[INFO] Batch size: {batch_size:,d} images")
    if turbo:
        print("[TURBO] Parallel batch queueing enabled")
    print()

    if not turbo:
        # Sequential queueing (original behavior)
        return _queue_sequential(batch_size)
    else:
        # Parallel queueing (turbo mode)
        return _queue_parallel(batch_size)


def _queue_sequential(batch_size: int) -> int:
    """Queue images sequentially (original behavior)."""
    total_queued = 0
    batch_num = 1

    while True:
        print(f"[INFO] Queueing batch {batch_num}...")

        try:
            response = requests.post(
                f"{API_BASE}/api/processing/batch",
                params={'limit': batch_size},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            queued = data.get('queued_count', 0)
            total_queued += queued

            print(f"  [OK] Queued: {queued:,d} images (Total: {total_queued:,d})")

            if queued == 0:
                print("[INFO] No more images to queue")
                break

            batch_num += 1
            time.sleep(2)  # Brief pause between batches

        except requests.exceptions.RequestException as e:
            print(f"[WARN] Failed to queue batch {batch_num}: {e}")
            break

    print()
    print(f"[OK] Queued {total_queued:,d} images total")
    print()

    return total_queued


def _queue_parallel(batch_size: int, max_workers: int = 6) -> int:
    """
    Queue images in parallel using ThreadPoolExecutor.

    Args:
        batch_size: Images per batch
        max_workers: Number of parallel requests (default 6)

    Returns:
        Total images queued
    """
    def queue_batch(batch_num: int) -> Tuple[int, int]:
        """Queue a single batch, returns (batch_num, queued_count)."""
        try:
            response = requests.post(
                f"{API_BASE}/api/processing/batch",
                params={'limit': batch_size},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            queued = data.get('queued_count', 0)
            return (batch_num, queued)
        except requests.exceptions.RequestException as e:
            print(f"[WARN] Failed to queue batch {batch_num}: {e}")
            return (batch_num, 0)

    # Estimate number of batches needed (4 batches for 35,251 images)
    max_batches = 6  # Allow up to 6 batches

    total_queued = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all batch jobs
        print(f"[TURBO] Submitting {max_batches} batch jobs in parallel...")
        futures = {executor.submit(queue_batch, i): i for i in range(1, max_batches + 1)}

        # Process results as they complete
        for future in as_completed(futures):
            batch_num, queued = future.result()
            if queued > 0:
                total_queued += queued
                print(f"  [OK] Batch {batch_num}: Queued {queued:,d} images (Total: {total_queued:,d})")
            else:
                print(f"  [INFO] Batch {batch_num}: No images to queue")

    print()
    print(f"[TURBO] Queued {total_queued:,d} images total using {max_workers} parallel workers")
    print()

    return total_queued


def get_processing_status() -> Dict:
    """Get current processing status from API."""
    try:
        response = requests.get(f"{API_BASE}/api/processing/status", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[WARN] Failed to get processing status: {e}")
        return {}


def print_processing_status():
    """Print current processing status."""
    print("=" * 70)
    print("PROCESSING STATUS")
    print("=" * 70)
    print()

    status = get_processing_status()

    if not status:
        print("[WARN] Could not retrieve processing status")
        return

    print(f"Total Images: {status.get('total_images', 0):,d}")
    print(f"Completed: {status.get('completed_images', 0):,d} ({status.get('completion_rate', 0):.1f}%)")
    print(f"Pending: {status.get('pending_images', 0):,d}")
    print(f"Processing: {status.get('processing_images', 0):,d}")
    print(f"Failed: {status.get('failed_images', 0):,d}")
    print()

    queue = status.get('queue_status', {})
    print("Queue Status:")
    print(f"  Total Tasks: {queue.get('total_tasks', 0):,d}")
    print(f"  Active Tasks: {queue.get('active_tasks', 0):,d}")
    print()

    # Estimate completion time
    if status.get('completion_rate', 0) > 0:
        remaining = status.get('pending_images', 0)
        throughput = 840  # images/minute from previous session
        eta_minutes = remaining / throughput
        eta_hours = eta_minutes / 60

        print(f"Estimated Time Remaining: {eta_hours:.1f} hours ({eta_minutes:.0f} minutes)")
        print(f"  (Based on 840 images/min throughput)")

    print()


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Reprocess entire dataset with newly trained YOLOv8 model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Interactive mode (default)
  python3 reprocess_with_new_model.py

  # Turbo mode - non-interactive, clear all, parallel queueing
  python3 reprocess_with_new_model.py --turbo --clear-mode all

  # Turbo mode - keep detections, parallel queueing
  python3 reprocess_with_new_model.py --turbo --clear-mode none

  # Turbo mode - preserve manual corrections
  python3 reprocess_with_new_model.py --turbo --clear-mode unreviewed
        '''
    )

    parser.add_argument(
        '--turbo',
        action='store_true',
        help='Enable turbo mode (non-interactive, parallel queueing)'
    )

    parser.add_argument(
        '--clear-mode',
        choices=['none', 'all', 'unreviewed'],
        default=None,
        help='Detection cleanup mode: none (keep all), all (delete all), unreviewed (delete non-reviewed)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=10000,
        help='Number of images per batch (default: 10000)'
    )

    parser.add_argument(
        '--no-stats',
        action='store_true',
        help='Skip detailed statistics display (faster for turbo mode)'
    )

    return parser.parse_args()


def main():
    """Main reprocessing workflow."""
    args = parse_args()

    # Turbo mode: non-interactive execution
    if args.turbo:
        print("=" * 70)
        print("TURBO MODE: Non-Interactive Reprocessing")
        print("=" * 70)
        print()
        if args.clear_mode is None:
            print("[ERROR] --clear-mode required in turbo mode")
            print("  Use: --clear-mode all|none|unreviewed")
            sys.exit(1)
        print(f"Clear Mode: {args.clear_mode}")
        print(f"Batch Size: {args.batch_size:,d}")
        print(f"Parallel Queueing: ENABLED")
        print()
    else:
        print_header()

    # Get database session
    db = SessionLocal()

    try:
        # Step 1: Show current stats (unless --no-stats)
        if not args.no_stats:
            print("[STEP 1] Current Database Statistics")
            print("-" * 70)
            stats_before = get_current_stats(db)
            print_stats(stats_before, "Before Reprocessing")
        else:
            stats_before = None

        # Step 2: Determine clear mode
        if args.turbo:
            clear_mode = args.clear_mode
        else:
            print("[STEP 2] Detection Cleanup Options")
            print("-" * 70)
            print()
            print("Options:")
            print("  1. Keep all detections (new detections will be added)")
            print("  2. Clear ALL detections (recommended for clean comparison)")
            print("  3. Clear only unreviewed detections (preserve manual corrections)")
            print()

            choice = input("Choose option [1-3]: ").strip()
            print()

            mode_map = {
                '1': 'none',
                '2': 'all',
                '3': 'unreviewed'
            }

            clear_mode = mode_map.get(choice, 'none')

        deleted = clear_detections(db, clear_mode)

        # Step 3: Reset image status
        print("[STEP 3] Reset Image Processing Status")
        print("-" * 70)
        completed, failed = reset_image_status(db)

        # Step 4: Show updated stats (unless --no-stats)
        if not args.no_stats:
            print("[STEP 4] Updated Database Statistics")
            print("-" * 70)
            stats_after = get_current_stats(db)
            print_stats(stats_after, "After Reset")
            total_to_queue = stats_after['images'].get('pending', 0)
        else:
            total_to_queue = completed + failed

        # Step 5: Confirm before queuing (skip in turbo mode)
        if not args.turbo:
            print("[STEP 5] Queue Images for Processing")
            print("-" * 70)
            print()
            print(f"Ready to queue {total_to_queue:,d} images for processing")
            print()

            confirm = input("Continue with queueing? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("[INFO] Aborted by user")
                return

            print()

        # Step 6: Queue images
        queued = queue_images_for_processing(
            batch_size=args.batch_size,
            turbo=args.turbo
        )

        # Step 7: Show processing status
        if not args.turbo:
            print("[STEP 6] Processing Status")
            print("-" * 70)
        else:
            print("[TURBO] Processing Status")
            print("-" * 70)
        print_processing_status()

        # Print monitoring instructions
        print("=" * 70)
        print("MONITORING")
        print("=" * 70)
        print()
        print("Monitor processing progress:")
        print("  1. API Status:")
        print("     curl http://localhost:8001/api/processing/status")
        print()
        print("  2. Worker Logs:")
        print("     docker-compose logs -f worker | grep 'Detection complete'")
        print()
        print("  3. Flower UI:")
        print("     http://localhost:5555")
        print()
        print("  4. GPU Usage:")
        print("     docker stats worker")
        print()
        print("Expected Throughput:")
        print("  - 840 images/minute (14 images/second)")
        print(f"  - Full dataset ({total_to_queue:,d} images): ~{total_to_queue/840:.0f} minutes")
        print()
        print("[OK] Reprocessing started successfully!")
        print()

    except KeyboardInterrupt:
        print()
        print("[INFO] Interrupted by user")
        db.rollback()
    except Exception as e:
        print(f"[FAIL] Error during reprocessing: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    main()
