#!/usr/bin/env python3
"""
Simple timestamp fixer - runs on host, connects to Docker database.

Extracts true timestamps from original filenames and updates database.
"""

import psycopg2
from pathlib import Path
from datetime import datetime
import re
from collections import defaultdict

# Database connection (Docker exposed on localhost:5433)
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'deer_tracking',
    'user': 'deertrack',
    'password': 'deertrack123'
}

# Paths
ORIGINAL_BASE = Path('/mnt/i/projects/thumper_counter/cifs/Hopkins_Ranch_Trail_Cam_Pics')
RENAMED_BASE = Path('/mnt/i/Hopkins_Ranch_Trail_Cam_Pics')

# Location name mappings (database name -> original folder name)
LOCATION_MAPPING = {
    '270_Jason': '270_JASON',
    'TinMan': 'TinMan',
    'Camphouse': 'Camphouse',
    'Phils_Secret_Spot': 'Phils_Secret_Spot',
    'Hayfield': 'HAYFIELD',
    'Sanctuary': 'Sanctuary'
}

# Pattern: YYYY_MM_DD_HH_MM_SS_LOCATION_CAMERA.JPG
TIMESTAMP_PATTERN = re.compile(r'^(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_')


def parse_timestamp(filename):
    """Extract timestamp from original filename."""
    match = TIMESTAMP_PATTERN.match(filename)
    if not match:
        return None

    try:
        year, month, day, hour, minute, second = map(int, match.groups())
        return datetime(year, month, day, hour, minute, second)
    except ValueError:
        return None


def build_mapping(location_db_name):
    """Map renamed files to original timestamps for a location."""
    orig_folder = LOCATION_MAPPING.get(location_db_name)
    if not orig_folder:
        return {}

    orig_dir = ORIGINAL_BASE / orig_folder
    renamed_dir = RENAMED_BASE / location_db_name

    if not orig_dir.exists() or not renamed_dir.exists():
        print(f"  [WARN] Directory not found for {location_db_name}")
        return {}

    # Get original files with timestamps
    originals = []
    for f in orig_dir.glob('*.[Jj][Pp][Gg]'):
        ts = parse_timestamp(f.name)
        if ts:
            originals.append((f.name, ts))

    # Sort by timestamp
    originals.sort(key=lambda x: x[1])

    # Get renamed files (sequentially numbered)
    renamed = sorted(renamed_dir.glob('*.jpg'))

    # Build mapping
    mapping = {}
    min_len = min(len(originals), len(renamed))

    for i in range(min_len):
        orig_name, orig_ts = originals[i]
        renamed_file = renamed[i]
        mapping[renamed_file.name] = {
            'original': orig_name,
            'timestamp': orig_ts
        }

    return mapping


def main(dry_run=True):
    print("=" * 70)
    print("TIMESTAMP CORRECTION FROM ORIGINAL FILENAMES")
    print("=" * 70)

    if dry_run:
        print("[DRY RUN] - Preview mode, no changes will be made\n")

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    try:
        # Get all locations
        cur.execute("SELECT id, name FROM locations ORDER BY name")
        locations = cur.fetchall()

        total_images = 0
        total_updated = 0
        stats_by_location = defaultdict(lambda: {'checked': 0, 'updated': 0, 'missing': 0})

        for location_id, location_name in locations:
            print(f"\n[INFO] Processing: {location_name}")

            # Build filename mapping
            mapping = build_mapping(location_name)

            if not mapping:
                print(f"  [SKIP] No mapping available")
                continue

            print(f"  [OK] Mapped {len(mapping)} files")

            # Get images for this location
            cur.execute("""
                SELECT id, filename, timestamp
                FROM images
                WHERE location_id = %s
                ORDER BY filename
            """, (location_id,))

            images = cur.fetchall()

            for image_id, filename, current_ts in images:
                total_images += 1
                stats_by_location[location_name]['checked'] += 1

                if filename not in mapping:
                    stats_by_location[location_name]['missing'] += 1
                    continue

                correct_ts = mapping[filename]['timestamp']

                # Check if needs updating (tolerance: 1 second)
                if current_ts and abs((current_ts.replace(tzinfo=None) - correct_ts).total_seconds()) < 1:
                    continue  # Already correct

                if dry_run:
                    if total_updated < 10:  # Show first 10 examples
                        print(f"  [PREVIEW] {filename}")
                        print(f"    Current: {current_ts}")
                        print(f"    Correct: {correct_ts} (from {mapping[filename]['original']})")
                else:
                    cur.execute("""
                        UPDATE images
                        SET timestamp = %s
                        WHERE id = %s
                    """, (correct_ts, image_id))

                total_updated += 1
                stats_by_location[location_name]['updated'] += 1

            if not dry_run:
                conn.commit()

        # Print summary
        print("\n" + "=" * 70)
        print("SUMMARY BY LOCATION")
        print("=" * 70)

        for loc_name in sorted(stats_by_location.keys()):
            stats = stats_by_location[loc_name]
            print(f"\n{loc_name}:")
            print(f"  Checked:  {stats['checked']}")
            print(f"  Updated:  {stats['updated']}")
            print(f"  Missing:  {stats['missing']}")

        print("\n" + "=" * 70)
        print(f"TOTAL IMAGES: {total_images}")
        print(f"TOTAL UPDATED: {total_updated}")
        print("=" * 70)

        if dry_run:
            print("\n[INFO] Run with --apply to make changes")
        else:
            print("\n[OK] Database updated successfully!")

    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    import sys

    dry_run = '--apply' not in sys.argv

    main(dry_run=dry_run)
