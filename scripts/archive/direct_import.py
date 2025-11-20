#!/usr/bin/env python3
"""
Direct bulk import via database connection.
Runs on host machine with direct filesystem and database access.
"""

import os
import psycopg2
from pathlib import Path
from datetime import datetime
import re
import shutil
from PIL import Image as PILImage

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'deer_tracking',
    'user': 'deertrack',
    'password': 'secure_password_here'
}

def extract_exif_timestamp(image_path):
    """Extract timestamp from EXIF."""
    try:
        img = PILImage.open(image_path)
        exif = img._getexif()
        if exif:
            for tag in [36867, 306, 36868]:
                if tag in exif:
                    return datetime.strptime(exif[tag], '%Y:%m:%d %H:%M:%S'), 'exif'
    except:
        pass
    return None, None

def extract_filename_timestamp(filename):
    """Extract timestamp from filename pattern."""
    match = re.search(r'(\d{8})_(\d{6})', filename)
    if match:
        try:
            dt = datetime.strptime(f"{match.group(1)}_{match.group(2)}", '%Y%m%d_%H%M%S')
            if 1990 <= dt.year <= 2030:
                return dt, 'filename'
        except:
            pass
    return None, None

def get_timestamp(image_path, filename):
    """Get timestamp with fallback."""
    timestamp, source = extract_exif_timestamp(image_path)
    if timestamp:
        return timestamp, source

    timestamp, source = extract_filename_timestamp(filename)
    if timestamp:
        return timestamp, source

    print(f"[WARN] No timestamp for {filename}, using current time")
    return datetime.utcnow(), 'current'

def main():
    source_base = Path('/mnt/i/Hopkins_Ranch_Trail_Cam_Dumps')
    target_base = Path('/mnt/i/Hopkins_Ranch_Trail_Cam_Pics')

    print("[INFO] Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Get location mappings
    cur.execute("SELECT id, name FROM locations")
    locations = {name: loc_id for loc_id, name in cur.fetchall()}
    print(f"[INFO] Found {len(locations)} locations: {list(locations.keys())}")

    location_dirs = {
        '270_Jason': '270_Jason',
        'Hayfield': 'Hayfield',
        'Sanctuary': 'Sanctuary'
    }

    total_imported = 0
    total_duplicates = 0
    total_errors = 0
    timestamp_stats = {'exif': 0, 'filename': 0, 'current': 0}

    for dir_name, loc_name in location_dirs.items():
        loc_dir = source_base / dir_name
        if not loc_dir.exists():
            print(f"[WARN] Directory not found: {loc_dir}")
            continue

        location_id = locations.get(loc_name)
        if not location_id:
            print(f"[ERROR] Location '{loc_name}' not in database")
            continue

        print(f"\n=== Processing: {loc_name} ===")

        # Find all JPG files
        images = list(loc_dir.rglob('*.jpg')) + list(loc_dir.rglob('*.JPG'))
        print(f"[INFO] Found {len(images)} images")

        # Target directory
        target_dir = target_base / loc_name
        target_dir.mkdir(parents=True, exist_ok=True)

        imported = 0
        duplicates = 0
        errors = 0

        for idx, img_path in enumerate(images, 1):
            try:
                filename = img_path.name

                # Check duplicate
                cur.execute(
                    "SELECT id FROM images WHERE filename = %s AND location_id = %s",
                    (filename, location_id)
                )
                if cur.fetchone():
                    duplicates += 1
                    if idx % 100 == 0:
                        print(f"  [{idx}/{len(images)}] Imported: {imported}, Duplicates: {duplicates}")
                    continue

                # Get timestamp
                timestamp, source = get_timestamp(str(img_path), filename)
                timestamp_stats[source] += 1

                # Copy file
                target_path = target_dir / filename
                shutil.copy2(str(img_path), str(target_path))

                # Insert DB record
                cur.execute("""
                    INSERT INTO images (filename, file_path, timestamp, location_id, exif_data, processing_status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    filename,
                    str(target_path),
                    timestamp,
                    location_id,
                    f'{{"timestamp_source": "{source}"}}',
                    'pending'
                ))
                imported += 1

                # Commit every 100 images
                if idx % 100 == 0:
                    conn.commit()
                    print(f"  [{idx}/{len(images)}] Imported: {imported}, Duplicates: {duplicates}")

            except Exception as e:
                errors += 1
                print(f"  [ERROR] {filename}: {e}")

        # Final commit for location
        conn.commit()

        print(f"[OK] Location: {loc_name}")
        print(f"  Imported: {imported}")
        print(f"  Duplicates: {duplicates}")
        print(f"  Errors: {errors}")

        total_imported += imported
        total_duplicates += duplicates
        total_errors += errors

    # Summary
    print("\n" + "="*60)
    print("IMPORT COMPLETE")
    print("="*60)
    print(f"Total imported: {total_imported}")
    print(f"Total duplicates: {total_duplicates}")
    print(f"Total errors: {total_errors}")
    print(f"\nTimestamp sources:")
    print(f"  EXIF: {timestamp_stats['exif']}")
    print(f"  Filename: {timestamp_stats['filename']}")
    print(f"  Fallback: {timestamp_stats['current']}")

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
