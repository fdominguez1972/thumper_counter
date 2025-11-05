#!/usr/bin/env python3
"""
Multithreaded image ingestion script for Thumper Counter.

Scans the IMAGE_PATH directory for trail camera images organized in location
folders, extracts EXIF metadata, and adds them to the database with status=PENDING.

Directory structure expected:
    IMAGE_PATH/
        Hayfield/
            IMG_0001.JPG
            IMG_0002.JPG
        Sanctuary/
            IMG_0003.JPG
        ...

Usage:
    python3 scripts/ingest_images.py [--workers N] [--batch-size N] [--dry-run]

Arguments:
    --workers N       Number of worker threads (default: 10)
    --batch-size N    Database commit batch size (default: 100)
    --dry-run        Scan and report without inserting to database
    --location NAME   Process only specific location folder

Environment:
    IMAGE_PATH: Root directory containing location folders (from .env)
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PIL import Image
from PIL.ExifTags import TAGS
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.core.database import get_db, test_connection
from backend.models.image import Image as ImageModel, ProcessingStatus
from backend.models.location import Location


# Thread-safe counters
class ProgressTracker:
    """Thread-safe progress tracking."""

    def __init__(self):
        self.lock = Lock()
        self.found = 0
        self.processed = 0
        self.inserted = 0
        self.skipped = 0
        self.failed = 0
        self.errors: List[str] = []

    def increment_found(self):
        with self.lock:
            self.found += 1

    def increment_processed(self):
        with self.lock:
            self.processed += 1

    def increment_inserted(self):
        with self.lock:
            self.inserted += 1

    def increment_skipped(self):
        with self.lock:
            self.skipped += 1

    def increment_failed(self):
        with self.lock:
            self.failed += 1

    def add_error(self, error: str):
        with self.lock:
            self.errors.append(error)

    def get_stats(self) -> Dict[str, int]:
        with self.lock:
            return {
                "found": self.found,
                "processed": self.processed,
                "inserted": self.inserted,
                "skipped": self.skipped,
                "failed": self.failed,
                "errors": len(self.errors)
            }


# Global progress tracker
progress = ProgressTracker()


def load_env_config() -> Dict[str, str]:
    """
    Load configuration from .env file.

    Returns:
        dict: Configuration values
    """
    env_path = Path(__file__).parent.parent / ".env"
    config = {}

    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()

    return config


def get_image_path() -> Path:
    """
    Get IMAGE_PATH from environment or .env file.

    Returns:
        Path: Image directory path

    Raises:
        ValueError: If IMAGE_PATH not configured
    """
    # Try environment variable first
    image_path = os.getenv('IMAGE_PATH')

    # Fall back to .env file
    if not image_path:
        config = load_env_config()
        image_path = config.get('IMAGE_PATH')

    if not image_path:
        raise ValueError("IMAGE_PATH not set in environment or .env file")

    # Convert Windows path to WSL path if needed
    path = Path(image_path)
    if not path.exists() and image_path.startswith('I:/'):
        # Try WSL mount point
        wsl_path = Path('/mnt/i') / image_path[3:]
        if wsl_path.exists():
            path = wsl_path

    if not path.exists():
        raise ValueError(f"IMAGE_PATH does not exist: {image_path}")

    return path


def extract_exif_data(image_path: Path) -> Tuple[Optional[datetime], Optional[Dict[str, Any]]]:
    """
    Extract EXIF metadata from image file.

    Args:
        image_path: Path to image file

    Returns:
        tuple: (timestamp, exif_dict) - timestamp from EXIF or file mtime, full EXIF data
    """
    try:
        # Open image and extract EXIF
        with Image.open(image_path) as img:
            exif_data = img._getexif()

            if not exif_data:
                # No EXIF data, use file modification time
                mtime = datetime.fromtimestamp(image_path.stat().st_mtime)
                return mtime, {}

            # Convert EXIF tags to readable names
            exif_dict = {
                TAGS.get(tag, tag): value
                for tag, value in exif_data.items()
            }

            # Extract timestamp from EXIF
            timestamp = None
            for date_tag in ['DateTimeOriginal', 'DateTime', 'DateTimeDigitized']:
                if date_tag in exif_dict:
                    try:
                        # EXIF date format: "2024:01:15 14:30:45"
                        timestamp = datetime.strptime(
                            exif_dict[date_tag],
                            "%Y:%m:%d %H:%M:%S"
                        )
                        break
                    except (ValueError, TypeError):
                        continue

            # Fall back to file mtime if no EXIF timestamp
            if not timestamp:
                timestamp = datetime.fromtimestamp(image_path.stat().st_mtime)

            # Convert non-serializable EXIF values to strings
            clean_exif = {}
            for key, value in exif_dict.items():
                try:
                    # Test if value is JSON serializable
                    json.dumps(value)
                    clean_exif[key] = value
                except (TypeError, ValueError):
                    # Convert to string if not serializable
                    clean_exif[key] = str(value)

            return timestamp, clean_exif

    except Exception as e:
        # If EXIF extraction fails, use file mtime
        try:
            mtime = datetime.fromtimestamp(image_path.stat().st_mtime)
            return mtime, {"error": f"EXIF extraction failed: {str(e)}"}
        except Exception:
            return None, {"error": f"Failed to get timestamp: {str(e)}"}


def find_images(root_path: Path, location_filter: Optional[str] = None) -> List[Tuple[Path, str]]:
    """
    Scan directory for images organized in location folders.

    Args:
        root_path: Root directory containing location folders
        location_filter: Optional location name to filter by

    Returns:
        list: List of (image_path, database_location_name) tuples
    """
    valid_extensions = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
    images = []

    print("[INFO] Scanning directory structure...")

    # Scan all subdirectories in root path
    if not root_path.exists():
        print(f"[FAIL] Root path does not exist: {root_path}")
        return images

    # Get all directories in root path
    all_folders = [d for d in root_path.iterdir() if d.is_dir()]

    print(f"[INFO] Found {len(all_folders)} folders in {root_path}")
    for folder in sorted(all_folders):
        print(f"       - {folder.name}")
    print()

    # Expected location mappings (database name -> possible folder names)
    location_mappings = {
        'Hayfield': ['Hayfield', 'HAYFIELD', 'hayfield'],
        '270_Jason': ['270_Jason', '270_JASON', '270_jason'],
        'Sanctuary': ['Sanctuary', 'SANCTUARY', 'sanctuary'],
        'TinMan': ['TinMan', 'TINMAN', 'tinman', 'Tinman'],
        'Camphouse': ['Camphouse', 'CAMPHOUSE', 'camphouse'],
        'Phils_Secret_Spot': ['Phils_Secret_Spot', 'PHILS_SECRET_SPOT', 'phils_secret_spot'],
    }

    # Filter if requested
    if location_filter:
        if location_filter not in location_mappings:
            print(f"[WARN] Unknown location: {location_filter}")
            print(f"[INFO] Valid locations: {', '.join(location_mappings.keys())}")
            return images
        location_mappings = {location_filter: location_mappings[location_filter]}

    # Process each location
    for db_location_name, possible_folder_names in location_mappings.items():
        folder_found = False

        # Try to find matching folder (case-insensitive)
        for folder_name in possible_folder_names:
            location_path = root_path / folder_name

            if location_path.exists() and location_path.is_dir():
                folder_found = True
                print(f"[INFO] Scanning: {folder_name} -> {db_location_name}")

                # Find all images in location folder (including subdirectories)
                folder_count = 0
                for image_path in location_path.rglob('*'):
                    if image_path.is_file() and image_path.suffix in valid_extensions:
                        # Use database location name for mapping
                        images.append((image_path, db_location_name))
                        progress.increment_found()
                        folder_count += 1

                print(f"[INFO] Found {folder_count} images in {folder_name}")
                break

        if not folder_found:
            print(f"[WARN] Location folder not found: {db_location_name} (tried: {', '.join(possible_folder_names)})")

    return images


def process_image(
    image_info: Tuple[Path, str],
    location_map: Dict[str, str],
    dry_run: bool = False
) -> bool:
    """
    Process a single image: extract metadata and insert to database.

    Args:
        image_info: (image_path, location_name) tuple
        location_map: Mapping of location name -> location UUID
        dry_run: If True, don't insert to database

    Returns:
        bool: True if successful, False otherwise
    """
    image_path, location_name = image_info

    try:
        # Get location UUID
        location_id = location_map.get(location_name)
        if not location_id:
            progress.add_error(f"Unknown location: {location_name} for {image_path.name}")
            progress.increment_failed()
            return False

        # Extract EXIF metadata
        timestamp, exif_data = extract_exif_data(image_path)

        if not timestamp:
            progress.add_error(f"No timestamp for {image_path}")
            progress.increment_failed()
            return False

        # Prepare image record
        filename = image_path.name
        path_str = str(image_path.resolve())

        # Skip if dry run
        if dry_run:
            progress.increment_processed()
            return True

        # Insert to database
        db = next(get_db())
        try:
            # Check if already exists (by path - unique constraint)
            existing = db.query(ImageModel).filter(ImageModel.path == path_str).first()

            if existing:
                progress.increment_skipped()
                return True

            # Create new image record
            image = ImageModel(
                filename=filename,
                path=path_str,
                timestamp=timestamp,
                location_id=location_id,
                exif_data=exif_data if exif_data else None,
                processing_status=ProcessingStatus.PENDING
            )

            db.add(image)
            db.commit()

            progress.increment_inserted()
            progress.increment_processed()
            return True

        except IntegrityError as e:
            db.rollback()
            # Likely duplicate path - count as skipped
            progress.increment_skipped()
            return True

        except Exception as e:
            db.rollback()
            progress.add_error(f"Database error for {filename}: {str(e)}")
            progress.increment_failed()
            return False

        finally:
            db.close()

    except Exception as e:
        progress.add_error(f"Processing error for {image_path}: {str(e)}")
        progress.increment_failed()
        return False


def load_location_map(db: Session) -> Dict[str, str]:
    """
    Load mapping of location names to UUIDs.

    Args:
        db: Database session

    Returns:
        dict: Mapping of location name -> UUID string
    """
    locations = db.query(Location).all()
    return {loc.name: str(loc.id) for loc in locations}


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Ingest trail camera images into Thumper Counter database"
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=10,
        help="Number of worker threads (default: 10)"
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help="Database commit batch size (default: 100)"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Scan and report without inserting to database"
    )
    parser.add_argument(
        '--location',
        type=str,
        help="Process only specific location folder"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("THUMPER COUNTER - Image Ingestion Script")
    print("=" * 70)
    print()

    if args.dry_run:
        print("[INFO] DRY RUN MODE - No database changes will be made")
        print()

    # Get image path
    try:
        image_path = get_image_path()
        print(f"[INFO] Image directory: {image_path}")
    except ValueError as e:
        print(f"[FAIL] {e}")
        sys.exit(1)

    # Test database connection
    print("[INFO] Testing database connection...")
    if not test_connection():
        print("[FAIL] Database connection failed")
        print("[INFO] Make sure the database is running:")
        print("       docker-compose up -d db")
        sys.exit(1)
    print("[OK] Database connected")
    print()

    # Load location mapping
    print("[INFO] Loading location mapping...")
    db = next(get_db())
    try:
        location_map = load_location_map(db)
        print(f"[OK] Loaded {len(location_map)} locations:")
        for name in sorted(location_map.keys()):
            print(f"     - {name}")
    except Exception as e:
        print(f"[FAIL] Failed to load locations: {e}")
        sys.exit(1)
    finally:
        db.close()
    print()

    # Scan for images
    print("[INFO] Scanning for images...")
    try:
        images = find_images(image_path, args.location)
    except Exception as e:
        print(f"[FAIL] Failed to scan directory: {e}")
        sys.exit(1)

    if not images:
        print("[WARN] No images found")
        sys.exit(0)

    print(f"[OK] Found {len(images)} images")
    print()

    # Process images with multithreading
    print(f"[INFO] Processing images with {args.workers} workers...")
    print(f"[INFO] Batch size: {args.batch_size}")
    print()

    start_time = datetime.now()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(process_image, img_info, location_map, args.dry_run): img_info
            for img_info in images
        }

        # Process results as they complete
        completed = 0
        for future in as_completed(futures):
            completed += 1

            # Show progress every 100 images
            if completed % 100 == 0:
                stats = progress.get_stats()
                print(f"[INFO] Progress: {completed}/{len(images)} "
                      f"(Inserted: {stats['inserted']}, "
                      f"Skipped: {stats['skipped']}, "
                      f"Failed: {stats['failed']})")

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Final summary
    stats = progress.get_stats()

    print()
    print("=" * 70)
    print("INGESTION COMPLETE")
    print("=" * 70)
    print(f"Duration:        {duration:.2f} seconds")
    print(f"Images found:    {stats['found']}")
    print(f"Processed:       {stats['processed']}")
    print(f"Inserted:        {stats['inserted']}")
    print(f"Skipped:         {stats['skipped']} (already in database)")
    print(f"Failed:          {stats['failed']}")

    if stats['inserted'] > 0:
        rate = stats['inserted'] / duration
        print(f"Insertion rate:  {rate:.2f} images/second")

    print()

    # Show errors if any
    if progress.errors:
        print("[WARN] Errors occurred during processing:")
        # Show first 10 errors
        for error in progress.errors[:10]:
            print(f"  - {error}")
        if len(progress.errors) > 10:
            print(f"  ... and {len(progress.errors) - 10} more errors")
        print()

    # Summary status
    if stats['failed'] > 0:
        print("[WARN] Some images failed to process")
    else:
        print("[OK] All images processed successfully!")

    print("=" * 70)


if __name__ == "__main__":
    main()
