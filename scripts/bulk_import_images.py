#!/usr/bin/env python3
"""
Bulk Image Import Script
Feature: 009-bulk-image-upload (manual import phase)

Imports trail camera images from Hopkins_Ranch_Trail_Cam_Dumps/ into the database
with EXIF timestamp extraction and duplicate detection.

Usage:
    python3 scripts/bulk_import_images.py --source-dir /mnt/i/Hopkins_Ranch_Trail_Cam_Dumps
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import re

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PIL import Image as PILImage
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from backend.models.image import Image
from backend.models.location import Location

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def get_database_session() -> Session:
    """Create database session from environment."""
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'postgresql://deertrack:deertrack@localhost:5433/deer_tracking'
    )
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def extract_exif_timestamp(image_path: str) -> Optional[datetime]:
    """
    Extract timestamp from EXIF metadata with 3-level fallback.

    Priority:
    1. EXIF DateTimeOriginal (tag 36867)
    2. EXIF DateTime (tag 306)
    3. EXIF DateTimeDigitized (tag 36868)

    Returns:
        datetime object or None if no EXIF found
    """
    try:
        img = PILImage.open(image_path)
        exif = img._getexif()

        if exif:
            # Try DateTimeOriginal (preferred)
            if 36867 in exif:
                return datetime.strptime(exif[36867], '%Y:%m:%d %H:%M:%S')
            # Try DateTime
            if 306 in exif:
                return datetime.strptime(exif[306], '%Y:%m:%d %H:%M:%S')
            # Try DateTimeDigitized
            if 36868 in exif:
                return datetime.strptime(exif[36868], '%Y:%m:%d %H:%M:%S')

        return None
    except Exception as e:
        logger.debug(f"EXIF extraction failed for {image_path}: {e}")
        return None


def extract_timestamp_from_filename(filename: str) -> Optional[datetime]:
    """
    Extract timestamp from filename pattern: Location_YYYYMMDD_HHMMSS_seq.jpg

    Examples:
        Sanctuary_20251031_143022_001.jpg -> 2025-10-31 14:30:22
        Jason1_20250831_131847_001.jpg -> 2025-08-31 13:18:47

    Returns:
        datetime object or None if pattern doesn't match
    """
    # Pattern: 8 digits (YYYYMMDD) _ 6 digits (HHMMSS)
    pattern = r'(\d{8})_(\d{6})'
    match = re.search(pattern, filename)

    if match:
        date_str = match.group(1)  # YYYYMMDD
        time_str = match.group(2)  # HHMMSS

        try:
            timestamp = datetime.strptime(f"{date_str}_{time_str}", '%Y%m%d_%H%M%S')

            # Validate year range (1990-2030)
            if 1990 <= timestamp.year <= 2030:
                return timestamp
        except ValueError as e:
            logger.debug(f"Filename timestamp parse failed for {filename}: {e}")

    return None


def get_image_timestamp(image_path: str, filename: str) -> Tuple[datetime, str]:
    """
    Get timestamp with 3-level fallback strategy.

    Returns:
        (timestamp, source) where source is 'exif', 'filename', or 'current'
    """
    # Try EXIF first
    timestamp = extract_exif_timestamp(image_path)
    if timestamp:
        return timestamp, 'exif'

    # Try filename pattern
    timestamp = extract_timestamp_from_filename(filename)
    if timestamp:
        return timestamp, 'filename'

    # Fallback to current UTC time
    logger.warning(f"No EXIF or filename timestamp for {filename}, using current time")
    return datetime.utcnow(), 'current'


def get_location_id_by_directory(db: Session, directory_name: str) -> Optional[str]:
    """
    Map directory name to location ID in database.

    Handles variations:
        - 270_Jason directory -> 270_Jason location
        - Hayfield directory -> Hayfield location
        - Sanctuary directory -> Sanctuary location
    """
    # Clean directory name (remove trailing numbers/prefixes)
    clean_name = directory_name.split('_')[0]  # "Sanctuary2" -> "Sanctuary"

    # Try exact match first
    location = db.query(Location).filter(Location.name == directory_name).first()
    if location:
        return str(location.id)

    # Try cleaned name
    location = db.query(Location).filter(Location.name == clean_name).first()
    if location:
        return str(location.id)

    # Try case-insensitive match
    location = db.query(Location).filter(Location.name.ilike(directory_name)).first()
    if location:
        return str(location.id)

    return None


def check_duplicate(db: Session, filename: str, location_id: str) -> bool:
    """Check if image already exists in database."""
    existing = db.query(Image).filter(
        Image.filename == filename,
        Image.location_id == location_id
    ).first()
    return existing is not None


def find_images_in_directory(directory: Path) -> List[Path]:
    """Recursively find all JPG/JPEG files in directory."""
    image_files = []
    for ext in ['*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
        image_files.extend(directory.rglob(ext))
    return sorted(image_files)


def import_images_from_location(
    db: Session,
    source_dir: Path,
    location_name: str,
    target_base: Path,
    dry_run: bool = False
) -> Dict:
    """
    Import all images from a location directory.

    Args:
        db: Database session
        source_dir: Source directory containing images
        location_name: Name of location
        target_base: Base directory for image storage (/mnt/images)
        dry_run: If True, only simulate import

    Returns:
        Statistics dict with counts
    """
    stats = {
        'total': 0,
        'imported': 0,
        'duplicates': 0,
        'errors': 0,
        'exif_timestamps': 0,
        'filename_timestamps': 0,
        'fallback_timestamps': 0
    }

    # Get location ID
    location_id = get_location_id_by_directory(db, location_name)
    if not location_id:
        logger.error(f"Location '{location_name}' not found in database")
        return stats

    logger.info(f"Importing images for location: {location_name} (ID: {location_id})")

    # Find all images
    image_files = find_images_in_directory(source_dir)
    stats['total'] = len(image_files)

    logger.info(f"Found {stats['total']} images in {source_dir}")

    # Target directory
    target_dir = target_base / location_name
    target_dir.mkdir(parents=True, exist_ok=True)

    # Process each image
    for idx, image_path in enumerate(image_files, 1):
        try:
            filename = image_path.name

            # Check duplicate
            if check_duplicate(db, filename, location_id):
                stats['duplicates'] += 1
                logger.debug(f"[{idx}/{stats['total']}] Duplicate: {filename}")
                continue

            # Get timestamp
            timestamp, source = get_image_timestamp(str(image_path), filename)

            # Track timestamp source
            if source == 'exif':
                stats['exif_timestamps'] += 1
            elif source == 'filename':
                stats['filename_timestamps'] += 1
            else:
                stats['fallback_timestamps'] += 1

            # Target path
            target_path = target_dir / filename

            if not dry_run:
                # Copy file (don't move, preserve source)
                import shutil
                shutil.copy2(str(image_path), str(target_path))

                # Create database record
                image = Image(
                    filename=filename,
                    file_path=str(target_path),
                    timestamp=timestamp,
                    location_id=location_id,
                    exif_data={'timestamp_source': source},
                    processing_status='pending'
                )
                db.add(image)

                # Commit every 100 images
                if idx % 100 == 0:
                    db.commit()
                    logger.info(f"[{idx}/{stats['total']}] Imported {stats['imported']} images...")

            stats['imported'] += 1

        except Exception as e:
            stats['errors'] += 1
            logger.error(f"[{idx}/{stats['total']}] Error importing {image_path.name}: {e}")

    # Final commit
    if not dry_run:
        db.commit()

    return stats


def main():
    parser = argparse.ArgumentParser(description='Bulk import trail camera images')
    parser.add_argument(
        '--source-dir',
        type=str,
        required=True,
        help='Source directory containing location subdirectories'
    )
    parser.add_argument(
        '--target-dir',
        type=str,
        default='/mnt/i/Hopkins_Ranch_Trail_Cam_Pics',
        help='Target directory for image storage (default: /mnt/i/Hopkins_Ranch_Trail_Cam_Pics)'
    )
    parser.add_argument(
        '--locations',
        type=str,
        nargs='+',
        help='Specific locations to import (default: all)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate import without writing to database or filesystem'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Validate directories
    source_dir = Path(args.source_dir)
    if not source_dir.exists():
        logger.error(f"Source directory not found: {source_dir}")
        return 1

    target_dir = Path(args.target_dir)
    if not target_dir.exists():
        logger.warning(f"Target directory not found, will create: {target_dir}")
        if not args.dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)

    # Connect to database
    logger.info("Connecting to database...")
    db = get_database_session()

    # Get list of location directories to process
    location_dirs = []
    if args.locations:
        # User specified locations
        for loc in args.locations:
            loc_dir = source_dir / loc
            if loc_dir.exists() and loc_dir.is_dir():
                location_dirs.append((loc, loc_dir))
            else:
                logger.warning(f"Location directory not found: {loc_dir}")
    else:
        # Auto-detect all location directories
        for item in source_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name != 'scripts':
                location_dirs.append((item.name, item))

    if not location_dirs:
        logger.error("No location directories found to import")
        return 1

    logger.info(f"Found {len(location_dirs)} location directories to process")
    if args.dry_run:
        logger.info("[DRY RUN MODE] No changes will be made")

    # Import each location
    total_stats = {
        'total': 0,
        'imported': 0,
        'duplicates': 0,
        'errors': 0,
        'exif_timestamps': 0,
        'filename_timestamps': 0,
        'fallback_timestamps': 0
    }

    for location_name, location_dir in location_dirs:
        logger.info(f"\n=== Processing: {location_name} ===")

        stats = import_images_from_location(
            db=db,
            source_dir=location_dir,
            location_name=location_name,
            target_base=target_dir,
            dry_run=args.dry_run
        )

        # Aggregate stats
        for key in total_stats:
            total_stats[key] += stats[key]

        # Print location summary
        logger.info(f"Location: {location_name}")
        logger.info(f"  Total found: {stats['total']}")
        logger.info(f"  Imported: {stats['imported']}")
        logger.info(f"  Duplicates: {stats['duplicates']}")
        logger.info(f"  Errors: {stats['errors']}")
        logger.info(f"  EXIF timestamps: {stats['exif_timestamps']}")
        logger.info(f"  Filename timestamps: {stats['filename_timestamps']}")
        logger.info(f"  Fallback timestamps: {stats['fallback_timestamps']}")

    # Print overall summary
    logger.info("\n" + "="*60)
    logger.info("IMPORT SUMMARY")
    logger.info("="*60)
    logger.info(f"Total images found: {total_stats['total']}")
    logger.info(f"Successfully imported: {total_stats['imported']}")
    logger.info(f"Duplicates skipped: {total_stats['duplicates']}")
    logger.info(f"Errors: {total_stats['errors']}")
    logger.info(f"\nTimestamp Sources:")
    logger.info(f"  EXIF: {total_stats['exif_timestamps']} ({100*total_stats['exif_timestamps']/max(1,total_stats['imported']):.1f}%)")
    logger.info(f"  Filename: {total_stats['filename_timestamps']} ({100*total_stats['filename_timestamps']/max(1,total_stats['imported']):.1f}%)")
    logger.info(f"  Fallback: {total_stats['fallback_timestamps']} ({100*total_stats['fallback_timestamps']/max(1,total_stats['imported']):.1f}%)")

    if args.dry_run:
        logger.info("\n[DRY RUN] No changes were made to database or filesystem")
    else:
        logger.info(f"\nImages stored in: {target_dir}")

    db.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
