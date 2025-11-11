#!/usr/bin/env python3
"""
Simple bulk image import for trail camera images.
Imports from Hopkins_Ranch_Trail_Cam_Dumps into database with EXIF extraction.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
import re
import shutil

# Configure for container environment
sys.path.insert(0, '/app/src')

from PIL import Image as PILImage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.image import Image
from backend.models.location import Location

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Database connection
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
    source_dir = Path('/mnt/i/Hopkins_Ranch_Trail_Cam_Dumps')
    target_base = Path('/mnt/images')

    logger.info("Starting bulk import...")
    logger.info(f"Source: {source_dir}")
    logger.info(f"Target: {target_base}")

    db = SessionLocal()

    # Get location mappings
    locations = {loc.name: str(loc.id) for loc in db.query(Location).all()}
    logger.info(f"Found {len(locations)} locations: {list(locations.keys())}")

    # Process each location directory
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
        loc_dir = source_dir / dir_name
        if not loc_dir.exists():
            logger.warning(f"Directory not found: {loc_dir}")
            continue

        location_id = locations.get(loc_name)
        if not location_id:
            logger.error(f"Location '{loc_name}' not in database")
            continue

        logger.info(f"\n=== Processing: {loc_name} ===")

        # Find all JPG files
        images = list(loc_dir.rglob('*.jpg')) + list(loc_dir.rglob('*.JPG'))
        logger.info(f"Found {len(images)} images")

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
                existing = db.query(Image).filter(
                    Image.filename == filename,
                    Image.location_id == location_id
                ).first()

                if existing:
                    duplicates += 1
                    continue

                # Get timestamp
                timestamp, source = get_timestamp(str(img_path), filename)
                timestamp_stats[source] += 1

                # Copy file
                target_path = target_dir / filename
                shutil.copy2(str(img_path), str(target_path))

                # Create DB record
                image = Image(
                    filename=filename,
                    file_path=str(target_path),
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
                    logger.info(f"  [{idx}/{len(images)}] Imported: {imported}, Duplicates: {duplicates}")

            except Exception as e:
                errors += 1
                logger.error(f"  Error: {filename}: {e}")

        # Final commit for location
        db.commit()

        logger.info(f"Location: {loc_name}")
        logger.info(f"  Imported: {imported}")
        logger.info(f"  Duplicates: {duplicates}")
        logger.info(f"  Errors: {errors}")

        total_imported += imported
        total_duplicates += duplicates
        total_errors += errors

    # Summary
    logger.info("\n" + "="*60)
    logger.info("IMPORT COMPLETE")
    logger.info("="*60)
    logger.info(f"Total imported: {total_imported}")
    logger.info(f"Total duplicates: {total_duplicates}")
    logger.info(f"Total errors: {total_errors}")
    logger.info(f"\nTimestamp sources:")
    logger.info(f"  EXIF: {timestamp_stats['exif']}")
    logger.info(f"  Filename: {timestamp_stats['filename']}")
    logger.info(f"  Fallback: {timestamp_stats['current']}")

    db.close()


if __name__ == '__main__':
    main()
