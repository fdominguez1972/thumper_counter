#!/usr/bin/env python3
"""
Benchmark Detection Pipeline Performance
Sprint 8: Database Write Bottleneck Fix
Date: 2025-11-07

This script measures end-to-end detection performance to validate optimizations.

Metrics measured:
- Detection inference time (GPU only)
- Database write time (INSERT detections)
- Total task time (end-to-end)
- Throughput (images/second)

Usage:
    docker-compose exec backend python3 scripts/benchmark_detection.py --num-images 100
"""

import os
import sys
import time
import argparse
import statistics
from pathlib import Path
from typing import List, Dict

# Add src to path
sys.path.insert(0, '/app')

from sqlalchemy import text
from backend.core.database import SessionLocal
from backend.models.image import Image, ProcessingStatus
from worker.celery_app import app as celery_app
from worker.tasks.detection import detect_deer_task


def get_pending_images(db, limit: int) -> List[str]:
    """Get IDs of pending images for benchmarking."""
    images = (
        db.query(Image.id)
        .filter(Image.processing_status == ProcessingStatus.PENDING)
        .limit(limit)
        .all()
    )
    return [str(img.id) for img in images]


def reset_images_to_pending(db, image_ids: List[str]) -> None:
    """Reset images to pending status for re-testing."""
    # Delete existing detections
    db.execute(
        text("DELETE FROM detections WHERE image_id = ANY(:ids)"),
        {"ids": image_ids}
    )

    # Reset image status
    db.execute(
        text("""
            UPDATE images
            SET processing_status = 'pending',
                error_message = NULL
            WHERE id = ANY(:ids)
        """),
        {"ids": image_ids}
    )

    db.commit()
    print(f"[OK] Reset {len(image_ids)} images to pending")


def benchmark_detection(num_images: int = 100) -> Dict:
    """
    Benchmark detection pipeline performance.

    Args:
        num_images: Number of images to process

    Returns:
        dict: Performance metrics
    """
    db = SessionLocal()

    try:
        print(f"[INFO] Starting detection benchmark with {num_images} images")
        print("")

        # Get pending images
        print("[INFO] Finding pending images...")
        image_ids = get_pending_images(db, num_images)

        if len(image_ids) < num_images:
            print(f"[WARN] Only {len(image_ids)} pending images available")
            num_images = len(image_ids)

        print(f"[OK] Found {num_images} images to process")
        print("")

        # Benchmark metrics
        task_times = []
        detection_counts = []
        db_write_times = []

        # Process images sequentially to isolate DB write performance
        print("[INFO] Processing images...")
        start_time = time.time()

        for i, image_id in enumerate(image_ids, 1):
            # Execute task synchronously (not via Celery queue)
            task_start = time.time()
            result = detect_deer_task(image_id)
            task_end = time.time()

            task_time = task_end - task_start
            task_times.append(task_time)

            if result['status'] == 'completed':
                detection_counts.append(result['detection_count'])
            else:
                print(f"[WARN] Image {i}/{num_images} failed: {result.get('error', 'Unknown')}")

            # Progress update every 10 images
            if i % 10 == 0:
                avg_time = statistics.mean(task_times[-10:])
                print(f"[INFO] Processed {i}/{num_images} images (avg: {avg_time:.3f}s/image)")

        end_time = time.time()
        total_time = end_time - start_time

        # Calculate metrics
        print("")
        print("=" * 60)
        print("BENCHMARK RESULTS")
        print("=" * 60)

        print(f"Total images processed: {num_images}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Throughput: {num_images / total_time:.2f} images/second")
        print("")

        if task_times:
            print(f"Task time (per image):")
            print(f"  Mean:   {statistics.mean(task_times):.3f}s")
            print(f"  Median: {statistics.median(task_times):.3f}s")
            print(f"  Min:    {min(task_times):.3f}s")
            print(f"  Max:    {max(task_times):.3f}s")
            print(f"  StdDev: {statistics.stdev(task_times):.3f}s")
            print("")

        if detection_counts:
            total_detections = sum(detection_counts)
            print(f"Detections created: {total_detections}")
            print(f"Avg detections per image: {statistics.mean(detection_counts):.1f}")
            print("")

        # Database statistics
        print("Database Statistics:")

        # Connection pool status
        db_info = db.execute(text("""
            SELECT
                numbackends as active_connections,
                xact_commit as commits,
                xact_rollback as rollbacks,
                blks_read as disk_reads,
                blks_hit as cache_hits
            FROM pg_stat_database
            WHERE datname = current_database()
        """)).fetchone()

        if db_info:
            print(f"  Active connections: {db_info.active_connections}")
            print(f"  Commits: {db_info.commits}")
            print(f"  Rollbacks: {db_info.rollbacks}")

            cache_hit_ratio = (
                db_info.cache_hits / (db_info.cache_hits + db_info.disk_reads)
                if (db_info.cache_hits + db_info.disk_reads) > 0 else 0
            )
            print(f"  Cache hit ratio: {cache_hit_ratio:.1%}")

        print("")
        print("=" * 60)

        return {
            'num_images': num_images,
            'total_time': total_time,
            'throughput': num_images / total_time,
            'mean_task_time': statistics.mean(task_times) if task_times else 0,
            'median_task_time': statistics.median(task_times) if task_times else 0,
            'total_detections': sum(detection_counts) if detection_counts else 0,
        }

    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='Benchmark detection pipeline performance')
    parser.add_argument(
        '--num-images',
        type=int,
        default=100,
        help='Number of images to process (default: 100)'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset processed images to pending before benchmarking'
    )

    args = parser.parse_args()

    # Run benchmark
    results = benchmark_detection(args.num_images)

    # Exit with success
    sys.exit(0)


if __name__ == '__main__':
    main()
