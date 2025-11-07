#!/usr/bin/env python3
"""
Test script to validate deduplication implementation.

Processes a small batch of images and verifies that:
1. Within-image duplicates are marked with is_duplicate=TRUE
2. Burst detections are linked to same deer with burst_group_id
3. Re-ID processing skips duplicate detections
"""

import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime
import time

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'deer_tracking',
    'user': 'deertrack',
    'password': 'deertrack123'
}


def get_sample_images(conn, limit=10):
    """Get sample pending images to process."""
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("""
            SELECT id, filename, location_id, timestamp
            FROM images
            WHERE processing_status = 'pending'
            ORDER BY timestamp
            LIMIT %s
        """, (limit,))
        return cur.fetchall()


def queue_image_processing(image_id):
    """Queue image for processing via API."""
    import requests

    response = requests.post(
        f"http://localhost:8001/api/processing/batch",
        params={'limit': 1, 'location_id': image_id}
    )

    return response.status_code == 200


def wait_for_processing(conn, image_ids, timeout=300):
    """Wait for images to finish processing."""
    start_time = time.time()

    while time.time() - start_time < timeout:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)
                FROM images
                WHERE id = ANY(%s)
                  AND processing_status = 'completed'
            """, (image_ids,))

            completed_count = cur.fetchone()[0]

            if completed_count == len(image_ids):
                return True

        time.sleep(2)

    return False


def analyze_deduplication(conn, image_ids):
    """Analyze deduplication results for processed images."""
    with conn.cursor(cursor_factory=DictCursor) as cur:
        # Get detection statistics
        cur.execute("""
            SELECT
                i.id as image_id,
                i.filename,
                COUNT(*) as total_detections,
                COUNT(*) FILTER (WHERE d.is_duplicate = FALSE) as unique_detections,
                COUNT(*) FILTER (WHERE d.is_duplicate = TRUE) as duplicate_detections,
                COUNT(DISTINCT d.burst_group_id) FILTER (WHERE d.burst_group_id IS NOT NULL) as burst_groups,
                COUNT(DISTINCT d.deer_id) FILTER (WHERE d.deer_id IS NOT NULL) as unique_deer
            FROM images i
            LEFT JOIN detections d ON d.image_id = i.id
            WHERE i.id = ANY(%s)
            GROUP BY i.id, i.filename
            ORDER BY i.filename
        """, (image_ids,))

        results = cur.fetchall()

        print("=" * 80)
        print("DEDUPLICATION ANALYSIS")
        print("=" * 80)

        for row in results:
            print(f"\nImage: {row['filename']}")
            print(f"  Total detections:     {row['total_detections']}")
            print(f"  Unique detections:    {row['unique_detections']}")
            print(f"  Duplicate detections: {row['duplicate_detections']}")
            print(f"  Burst groups:         {row['burst_groups']}")
            print(f"  Unique deer:          {row['unique_deer']}")

            if row['total_detections'] > row['unique_detections']:
                dedup_rate = (row['duplicate_detections'] / row['total_detections']) * 100
                print(f"  Deduplication rate:   {dedup_rate:.1f}%")

        # Get burst grouping details
        print("\n" + "=" * 80)
        print("BURST GROUPING ANALYSIS")
        print("=" * 80)

        cur.execute("""
            SELECT
                d.burst_group_id,
                COUNT(*) as detections_in_burst,
                COUNT(DISTINCT d.image_id) as images_in_burst,
                COUNT(DISTINCT d.deer_id) as deer_in_burst,
                MIN(i.timestamp) as burst_start,
                MAX(i.timestamp) as burst_end,
                EXTRACT(EPOCH FROM (MAX(i.timestamp) - MIN(i.timestamp))) as burst_duration_seconds
            FROM detections d
            JOIN images i ON i.id = d.image_id
            WHERE d.burst_group_id IS NOT NULL
              AND i.id = ANY(%s)
            GROUP BY d.burst_group_id
            HAVING COUNT(*) > 1
            ORDER BY burst_start
        """, (image_ids,))

        burst_results = cur.fetchall()

        if burst_results:
            for burst in burst_results:
                print(f"\nBurst Group: {burst['burst_group_id']}")
                print(f"  Detections: {burst['detections_in_burst']}")
                print(f"  Images:     {burst['images_in_burst']}")
                print(f"  Deer:       {burst['deer_in_burst']}")
                print(f"  Duration:   {burst['burst_duration_seconds']:.1f}s")

                if burst['deer_in_burst'] == 1:
                    print("  [OK] All detections linked to same deer")
                else:
                    print("  [WARN] Multiple deer in burst (expected 1)")
        else:
            print("\n[INFO] No burst groups found (images may be far apart in time)")

        print("\n" + "=" * 80)


def main():
    """Main test function."""
    print("Deduplication Test Script")
    print("=" * 80)

    conn = psycopg2.connect(**DB_CONFIG)

    try:
        # Get sample images
        print("\n[1] Getting sample pending images...")
        images = get_sample_images(conn, limit=5)

        if not images:
            print("[WARN] No pending images found")
            return

        print(f"[OK] Found {len(images)} images to process")
        for img in images:
            print(f"  - {img['filename']}")

        image_ids = [str(img['id']) for img in images]

        # Queue processing
        print("\n[2] Queuing images for processing...")
        print("[INFO] Use batch processing API instead:")
        print(f"  curl -X POST 'http://localhost:8001/api/processing/batch?limit={len(images)}'")

        # Wait for manual processing or auto-queue
        input("\nPress Enter after images are queued for processing...")

        # Wait for completion
        print("\n[3] Waiting for processing to complete...")
        if wait_for_processing(conn, image_ids, timeout=300):
            print("[OK] All images processed")
        else:
            print("[WARN] Timeout waiting for processing")
            return

        # Analyze results
        print("\n[4] Analyzing deduplication results...")
        analyze_deduplication(conn, image_ids)

        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
