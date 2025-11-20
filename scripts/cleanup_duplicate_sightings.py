#!/usr/bin/env python3
"""
Clean up duplicate sightings (same deer_id + image_id).
Keeps only the highest confidence detection for each deer+image pair.
"""

import psycopg2
import os

DB_CONFIG = {
    'dbname': os.environ.get('POSTGRES_DB', 'deer_tracking'),
    'user': os.environ.get('POSTGRES_USER', 'deertrack'),
    'password': os.environ.get('POSTGRES_PASSWORD', 'secure_password_here'),
    'host': os.environ.get('DB_HOST', 'db'),  # 'db' in Docker, 'localhost' outside
    'port': int(os.environ.get('POSTGRES_PORT', 5432))
}

def find_duplicates(conn):
    """Find all duplicate sightings (same deer + image)."""
    cur = conn.cursor()

    query = """
        SELECT deer_id, image_id, COUNT(*) as count
        FROM detections
        WHERE deer_id IS NOT NULL
        GROUP BY deer_id, image_id
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
    """

    cur.execute(query)
    duplicates = cur.fetchall()
    cur.close()

    return duplicates


def cleanup_duplicates(conn, dry_run=True):
    """Remove duplicate detections, keeping only the highest confidence one."""
    cur = conn.cursor()

    # Find all duplicate groups
    find_query = """
        SELECT deer_id, image_id
        FROM detections
        WHERE deer_id IS NOT NULL
        GROUP BY deer_id, image_id
        HAVING COUNT(*) > 1
    """

    cur.execute(find_query)
    duplicate_groups = cur.fetchall()

    total_deleted = 0

    for deer_id, image_id in duplicate_groups:
        # Get all detections for this deer+image combo
        get_dets = """
            SELECT id, confidence, classification
            FROM detections
            WHERE deer_id = %s AND image_id = %s
            ORDER BY confidence DESC, created_at ASC
        """

        cur.execute(get_dets, (deer_id, image_id))
        detections = cur.fetchall()

        # Keep the first (highest confidence, oldest if tied)
        keep_id = detections[0][0]
        delete_ids = [det[0] for det in detections[1:]]

        if dry_run:
            print(f"[DRY RUN] Would keep detection {keep_id} (conf={detections[0][1]:.2f}) and delete {len(delete_ids)} duplicates")
        else:
            # Delete duplicates
            delete_query = """
                DELETE FROM detections
                WHERE id = ANY(%s)
            """
            cur.execute(delete_query, (delete_ids,))
            total_deleted += len(delete_ids)

            if total_deleted % 100 == 0:
                print(f"  Deleted {total_deleted} duplicates so far...")

    cur.close()

    if not dry_run:
        conn.commit()
        print(f"\n[OK] Deleted {total_deleted} duplicate detections")
    else:
        print(f"\n[DRY RUN] Would delete {total_deleted} duplicate detections")

    return total_deleted


def main():
    print("="*80)
    print("DUPLICATE SIGHTINGS CLEANUP")
    print("="*80)

    # Connect to database
    print("\n[1/3] Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    print("[OK] Connected")

    # Find duplicates
    print("\n[2/3] Finding duplicates...")
    duplicates = find_duplicates(conn)
    print(f"[OK] Found {len(duplicates)} deer+image pairs with duplicates")

    if duplicates:
        print("\nTop 10 worst offenders:")
        for deer_id, image_id, count in duplicates[:10]:
            print(f"  Deer {deer_id[:8]}... in image {image_id[:8]}...: {count} detections")

    # Dry run first
    print("\n[3/3] Running cleanup (DRY RUN)...")
    total = cleanup_duplicates(conn, dry_run=True)

    if total > 0:
        print("\n" + "="*80)
        print("CONFIRMATION REQUIRED")
        print("="*80)
        response = input(f"\nDelete {total} duplicate detections? (yes/no): ")

        if response.lower() == 'yes':
            print("\n[INFO] Running actual cleanup...")
            cleanup_duplicates(conn, dry_run=False)
            print("\n[OK] Cleanup complete!")

            # Verify
            remaining = find_duplicates(conn)
            if remaining:
                print(f"\n[WARN] Still have {len(remaining)} duplicates - may need another pass")
            else:
                print("\n[OK] No duplicates remaining!")
        else:
            print("\n[INFO] Cleanup cancelled")

    conn.close()
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
