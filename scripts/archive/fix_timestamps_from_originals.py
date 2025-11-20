#!/usr/bin/env python3
"""
Fix Timestamps from Original Filenames

Problem: Database timestamps are based on file modification times from the
rename operation (Jan 27, 2024), not actual camera timestamps.

Solution: Parse original filenames which contain embedded timestamps:
  Format: YYYY_MM_DD_HH_MM_SS_LOCATION_CAMERA.JPG
  Example: 2022_03_01_16_56_17_TIN_MAN_RUB_SYFR1401.JPG

This script:
1. Maps renamed files (270_JASON_00001.jpg) to originals (2022_03_01_16_56_17_270_JASON_SYFR1773.JPG)
2. Extracts true camera timestamps from original filenames
3. Updates database Image.timestamp with correct values
4. Reports statistics on changes made

Usage:
  python3 scripts/fix_timestamps_from_originals.py --dry-run  # Preview changes
  python3 scripts/fix_timestamps_from_originals.py            # Apply changes
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, Optional
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from backend.core.database import SessionLocal
from backend.models.image import Image
from backend.models.location import Location
from sqlalchemy import func


# Paths
ORIGINAL_BASE = Path('/mnt/i/projects/thumper_counter/cifs/Hopkins_Ranch_Trail_Cam_Pics')
RENAMED_BASE = Path('/mnt/i/Hopkins_Ranch_Trail_Cam_Pics')

# Filename pattern for original files: YYYY_MM_DD_HH_MM_SS_LOCATION_CAMERA.JPG
ORIGINAL_PATTERN = re.compile(r'^(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(.+)_([A-Z0-9]+)\.(JPG|jpg)$')


def parse_original_timestamp(filename: str) -> Optional[datetime]:
    """
    Extract timestamp from original filename.

    Args:
        filename: Original filename like "2022_03_01_16_56_17_TIN_MAN_RUB_SYFR1401.JPG"

    Returns:
        datetime object or None if parse fails
    """
    match = ORIGINAL_PATTERN.match(filename)
    if not match:
        return None

    year, month, day, hour, minute, second = map(int, match.groups()[:6])

    try:
        return datetime(year, month, day, hour, minute, second)
    except ValueError as e:
        print(f"[WARN] Invalid date in filename {filename}: {e}")
        return None


def build_filename_mapping(location_name: str) -> Dict[str, Tuple[str, datetime]]:
    """
    Build mapping from renamed files to original filenames and timestamps.

    Args:
        location_name: Location folder name (e.g., "270_Jason")

    Returns:
        Dict mapping renamed_filename -> (original_filename, timestamp)
    """
    mapping = {}

    # Get original files
    original_dir = ORIGINAL_BASE / location_name.upper().replace(' ', '_')

    if not original_dir.exists():
        print(f"[WARN] Original directory not found: {original_dir}")
        return mapping

    # Get list of original files with timestamps
    original_files = []
    for f in original_dir.glob('*.[Jj][Pp][Gg]'):
        ts = parse_original_timestamp(f.name)
        if ts:
            original_files.append((f.name, ts))
        else:
            print(f"[WARN] Could not parse timestamp from: {f.name}")

    # Sort by timestamp (this should match the sequential numbering order)
    original_files.sort(key=lambda x: x[1])

    # Map to renamed files (which are sequentially numbered)
    renamed_dir = RENAMED_BASE / location_name
    if not renamed_dir.exists():
        print(f"[WARN] Renamed directory not found: {renamed_dir}")
        return mapping

    renamed_files = sorted(renamed_dir.glob('*.jpg'))

    # Match by position in sorted lists
    if len(original_files) != len(renamed_files):
        print(f"[WARN] File count mismatch for {location_name}:")
        print(f"  Original: {len(original_files)}")
        print(f"  Renamed:  {len(renamed_files)}")
        print(f"  Using minimum count for mapping")

    min_count = min(len(original_files), len(renamed_files))

    for i in range(min_count):
        orig_name, orig_ts = original_files[i]
        renamed_file = renamed_files[i]
        mapping[renamed_file.name] = (orig_name, orig_ts)

    return mapping


def update_timestamps(dry_run: bool = False):
    """
    Update database timestamps from original filenames.

    Args:
        dry_run: If True, only show what would be changed without updating
    """
    db = SessionLocal()

    try:
        # Get all locations
        locations = db.query(Location).all()

        total_images = 0
        total_updated = 0
        total_failed = 0

        print("=" * 70)
        print("TIMESTAMP CORRECTION FROM ORIGINAL FILENAMES")
        print("=" * 70)

        if dry_run:
            print("[DRY RUN MODE] - No database changes will be made\n")

        for location in locations:
            print(f"\n[INFO] Processing location: {location.name}")

            # Build filename mapping for this location
            mapping = build_filename_mapping(location.name)

            if not mapping:
                print(f"  [SKIP] No mapping available")
                continue

            print(f"  [OK] Built mapping for {len(mapping)} files")

            # Get all images for this location
            images = db.query(Image).filter(Image.location_id == location.id).all()

            updated = 0
            failed = 0

            for image in images:
                total_images += 1

                if image.filename not in mapping:
                    failed += 1
                    total_failed += 1
                    continue

                orig_name, orig_ts = mapping[image.filename]

                # Check if timestamp needs updating
                if image.timestamp and abs((image.timestamp.replace(tzinfo=None) - orig_ts).total_seconds()) < 1:
                    # Already correct (within 1 second tolerance)
                    continue

                old_ts = image.timestamp

                if dry_run:
                    print(f"  [PREVIEW] {image.filename}")
                    print(f"    Old: {old_ts}")
                    print(f"    New: {orig_ts} (from {orig_name})")
                else:
                    image.timestamp = orig_ts
                    updated += 1
                    total_updated += 1

            if not dry_run and updated > 0:
                db.commit()
                print(f"  [OK] Updated {updated} timestamps")

            if failed > 0:
                print(f"  [WARN] {failed} files not found in mapping")

        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total images processed:  {total_images}")
        print(f"Timestamps updated:      {total_updated}")
        print(f"Files not in mapping:    {total_failed}")

        if dry_run:
            print("\n[INFO] This was a dry run. Run without --dry-run to apply changes.")
        else:
            print("\n[OK] Database updated successfully!")

            # Show example of corrected timestamps
            print("\n[INFO] Verifying a few corrected timestamps...")
            sample = db.query(Image).filter(Image.location_id == locations[0].id).limit(5).all()
            for img in sample:
                print(f"  {img.filename}: {img.timestamp}")

    except Exception as e:
        print(f"\n[FAIL] Error during update: {e}")
        db.rollback()
        raise

    finally:
        db.close()


def analyze_timing_patterns():
    """
    Analyze timing patterns after timestamp correction.

    Shows distribution of gaps between consecutive photos to understand
    if cameras were using burst mode or single shot.
    """
    db = SessionLocal()

    try:
        print("\n" + "=" * 70)
        print("TIMING PATTERN ANALYSIS (After Correction)")
        print("=" * 70)

        # Query consecutive image pairs with time gaps
        query = """
        WITH timing_analysis AS (
          SELECT
            i.filename,
            i.timestamp,
            l.name as location,
            EXTRACT(EPOCH FROM (i.timestamp - LAG(i.timestamp)
              OVER (PARTITION BY i.location_id ORDER BY i.timestamp))) as gap_seconds
          FROM images i
          JOIN locations l ON i.location_id = l.id
          WHERE i.processing_status = 'completed'
        )
        SELECT
          CASE
            WHEN gap_seconds IS NULL THEN 'first_image'
            WHEN gap_seconds < 1 THEN 'rapid_burst (<1s)'
            WHEN gap_seconds < 5 THEN 'burst (1-5s)'
            WHEN gap_seconds < 30 THEN 'short_gap (5-30s)'
            WHEN gap_seconds < 120 THEN 'medium_gap (30-120s)'
            WHEN gap_seconds < 600 THEN 'long_gap (2-10min)'
            ELSE 'very_long (>10min)'
          END as timing_category,
          COUNT(*) as photo_count,
          ROUND(MIN(gap_seconds)::numeric, 1) as min_gap,
          ROUND(AVG(gap_seconds)::numeric, 1) as avg_gap,
          ROUND(MAX(gap_seconds)::numeric, 1) as max_gap,
          ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER ())::numeric, 1) as percent
        FROM timing_analysis
        GROUP BY timing_category
        ORDER BY photo_count DESC;
        """

        result = db.execute(query)

        print("\nGap Distribution:")
        print(f"{'Category':<20} {'Count':<10} {'Min':<10} {'Avg':<10} {'Max':<10} {'%'}")
        print("-" * 70)

        for row in result:
            cat, count, min_gap, avg_gap, max_gap, pct = row
            min_str = f"{min_gap:.1f}s" if min_gap else "N/A"
            avg_str = f"{avg_gap:.1f}s" if avg_gap else "N/A"
            max_str = f"{max_gap:.1f}s" if max_gap else "N/A"
            print(f"{cat:<20} {count:<10} {min_str:<10} {avg_str:<10} {max_str:<10} {pct}%")

        print("\n[INFO] Use this data to set burst grouping window")

    finally:
        db.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Fix timestamps from original filenames')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview changes without updating database')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze timing patterns after correction')

    args = parser.parse_args()

    if args.analyze:
        analyze_timing_patterns()
    else:
        update_timestamps(dry_run=args.dry_run)

        if not args.dry_run:
            print("\nRunning timing analysis on corrected data...\n")
            analyze_timing_patterns()
