#!/usr/bin/env python3
"""
Register Copied Images Script
Scans Hopkins_Ranch_Trail_Cam_Pics for images not yet in database and registers them.
Runs inside backend container where /mnt/i is mounted via docker-compose.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import re

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PIL import Image as PILImage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.image import Image
from backend.models.location import Location

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Database connection from environment
POSTGRES_USER = os.getenv('POSTGRES_USER', 'deertrack')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'secure_password_here')
POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'db')
POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')
POSTGRES_DB = os.getenv('POSTGRES_DB', 'deer_tracking')

DATABASE_URL = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def extract_exif_timestamp(image_path):
    """Extract timestamp from EXIF (tags 36867, 306, 36868)."""
    try:
        img = PILImage.open(image_path)
        exif = img._getexif()
        if exif:
            for tag in [36867, 306, 36868]:  # DateTimeOriginal, DateTime, DateTimeDigitized
                if tag in exif:
                    return datetime.strptime(exif[tag], '%Y:%m:%d %H:%M:%S'), 'exif'
    except:
        pass
    return None, None


def extract_filename_timestamp(filename):
    """Extract timestamp from filename pattern: Location_YYYYMMDD_HHMMSS_seq.jpg"""
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
    """Get timestamp with fallback: EXIF -> filename -> current UTC."""
    timestamp, source = extract_exif_timestamp(image_path)
    if timestamp:
        return timestamp, source

    timestamp, source = extract_filename_timestamp(filename)
    if timestamp:
        return timestamp, source

    logger.warning(f"No timestamp for {filename}, using current time")
    return datetime.utcnow(), 'current'


def main():
    # Target base is mounted in container at /mnt/images
    # But we can also access the Windows path directly if mounted
    pics_dir = Path('/mnt/i/Hopkins_Ranch_Trail_Cam_Pics')

    if not pics_dir.exists():
        # Fallback to container mount point
        pics_dir = Path('/mnt/images')

    logger.info("=== Registering Copied Images ===")
    logger.info(f"Scanning directory: {pics_dir}")

    db = SessionLocal()

    # Get location mappings (handle case-insensitive)
    locations_db = {loc.name.upper(): str(loc.id) for loc in db.query(Location).all()}
    logger.info(f"Found {len(locations_db)} locations in database")

    # Location directories to process (match actual directory names)
    location_dirs = {
        '270_JASON': '270_Jason',   # Directory name -> DB location name
        'HAYFIELD': 'Hayfield',
        'Sanctuary': 'Sanctuary'
    }

    total_imported = 0
    total_duplicates = 0
    total_errors = 0
    timestamp_stats = {'exif': 0, 'filename': 0, 'current': 0}

    for dir_name, loc_name in location_dirs.items():
        loc_dir = pics_dir / dir_name
        if not loc_dir.exists():
            logger.warning(f"Directory not found: {loc_dir}")
            continue

        # Get location ID (case-insensitive match)
        location_id = locations_db.get(loc_name.upper())
        if not location_id:
            logger.error(f"Location '{loc_name}' not in database")
            continue

        logger.info(f"\n=== Processing: {loc_name} ({dir_name}) ===")

        # Find all JPG files
        images = list(loc_dir.glob('*.jpg')) + list(loc_dir.glob('*.JPG'))
        logger.info(f"Found {len(images)} total images in directory")

        # Get existing filenames for this location
        existing_filenames = set(
            row[0] for row in db.query(Image.filename).filter(
                Image.location_id == location_id
            ).all()
        )
        logger.info(f"Already have {len(existing_filenames)} images in database")

        imported = 0
        duplicates = 0
        errors = 0

        for idx, img_path in enumerate(images, 1):
            try:
                filename = img_path.name

                # Check if already in database
                if filename in existing_filenames:
                    duplicates += 1
                    if idx % 1000 == 0:
                        logger.info(f"  [{idx}/{len(images)}] Progress: {imported} new, {duplicates} existing")
                    continue

                # Get timestamp
                timestamp, source = get_timestamp(str(img_path), filename)
                timestamp_stats[source] += 1

                # Create DB record
                image = Image(
                    filename=filename,
                    path=str(img_path),
                    timestamp=timestamp,
                    location_id=location_id,
                    exif_data={'timestamp_source': source},
                    processing_status='pending'
                )
                db.add(image)
                imported += 1

                # Commit every 100 images
                if idx % 100 == 0:
                    db.commit()
                    logger.info(f"  [{idx}/{len(images)}] Imported: {imported}, Existing: {duplicates}")

            except Exception as e:
                errors += 1
                logger.error(f"  Error: {filename}: {e}")

        # Final commit for location
        db.commit()

        logger.info(f"Location: {loc_name}")
        logger.info(f"  Total files: {len(images)}")
        logger.info(f"  New imports: {imported}")
        logger.info(f"  Already existed: {duplicates}")
        logger.info(f"  Errors: {errors}")

        total_imported += imported
        total_duplicates += duplicates
        total_errors += errors

    # Summary
    logger.info("\n" + "="*60)
    logger.info("REGISTRATION COMPLETE")
    logger.info("="*60)
    logger.info(f"Total new imports: {total_imported}")
    logger.info(f"Total already existed: {total_duplicates}")
    logger.info(f"Total errors: {total_errors}")
    logger.info(f"\nTimestamp sources (new imports only):")
    logger.info(f"  EXIF: {timestamp_stats['exif']}")
    logger.info(f"  Filename: {timestamp_stats['filename']}")
    logger.info(f"  Fallback: {timestamp_stats['current']}")

    db.close()


if __name__ == '__main__':
    main()
