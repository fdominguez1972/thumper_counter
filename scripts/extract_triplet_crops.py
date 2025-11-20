#!/usr/bin/env python3
"""
Extract detection crops from source images for triplet training.

This script:
1. Queries detections with bbox coordinates and image paths
2. Loads source images and crops detection regions
3. Organizes crops by deer ID for triplet loss training

Feature: 009-reid-enhancement / Phase 2A
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Tuple
import random
from PIL import Image
import numpy as np

# Add backend to path
sys.path.insert(0, '/app')

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from backend.models.deer import Deer
from backend.models.detection import Detection
from backend.models.image import Image as DBImage
from backend.core.database import DATABASE_URL

# Configuration
MIN_DETECTIONS_PER_DEER = 10
OUTPUT_DIR = Path("/app/src/models/training_data/reid_triplet_20251116")
TRAIN_RATIO = 0.8

def setup_directories():
    """Create output directory structure."""
    print("[INFO] Setting up directories...")
    (OUTPUT_DIR / "train").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "val").mkdir(parents=True, exist_ok=True)
    print(f"[OK] Output: {OUTPUT_DIR}")

def get_qualified_deer(db) -> List[Tuple[str, str, int]]:
    """Get deer with sufficient detections."""
    print(f"[INFO] Finding deer with >={MIN_DETECTIONS_PER_DEER} detections...")

    results = db.query(
        Deer.id,
        Deer.name,
        func.count(Detection.id).label('count')
    ).join(
        Detection, Deer.id == Detection.deer_id
    ).group_by(
        Deer.id, Deer.name
    ).having(
        func.count(Detection.id) >= MIN_DETECTIONS_PER_DEER
    ).order_by(
        func.count(Detection.id).desc()
    ).all()

    print(f"[OK] Found {len(results)} qualified deer")
    return results

def extract_crop_from_bbox(image_path: str, bbox_json: dict) -> Image.Image:
    """
    Extract crop from image using bbox coordinates.

    Args:
        image_path: Path to source image
        bbox_json: Dict with keys {x, y, width, height} in pixel coordinates

    Returns:
        PIL Image of cropped region
    """
    img = Image.open(image_path)

    # Extract bbox coordinates (already in pixels)
    x = bbox_json['x']
    y = bbox_json['y']
    width = bbox_json['width']
    height = bbox_json['height']

    # Calculate crop box (x_min, y_min, x_max, y_max)
    x_min = x
    y_min = y
    x_max = x + width
    y_max = y + height

    # Crop and return
    crop = img.crop((x_min, y_min, x_max, y_max))
    return crop

def process_deer_detections(db, deer_id: str, deer_name: str, output_subdir: str) -> int:
    """
    Extract and save all crops for one deer.

    Args:
        deer_id: Deer UUID
        deer_name: Deer name for logging
        output_subdir: 'train' or 'val'

    Returns:
        Number of crops extracted
    """
    # Query all detections for this deer with image paths
    detections = db.query(
        Detection.id,
        Detection.bbox,
        DBImage.path
    ).join(
        DBImage, Detection.image_id == DBImage.id
    ).filter(
        Detection.deer_id == deer_id,
        Detection.bbox.isnot(None),
        DBImage.path.isnot(None)
    ).all()

    if not detections:
        return 0

    # Create deer directory
    deer_dir = OUTPUT_DIR / output_subdir / str(deer_id)
    deer_dir.mkdir(exist_ok=True)

    # Extract crops
    crop_count = 0
    for detection_id, bbox, image_path in detections:
        try:
            # Extract crop
            crop = extract_crop_from_bbox(image_path, bbox)

            # Save crop
            crop_path = deer_dir / f"{detection_id}.jpg"
            crop.save(crop_path, format='JPEG', quality=95)
            crop_count += 1

        except Exception as e:
            print(f"    [WARN] Failed to extract {detection_id}: {e}")
            continue

    return crop_count

def main():
    """Main extraction workflow."""
    print("=" * 70)
    print("Re-ID Triplet Dataset Extraction (Full)")
    print("=" * 70)

    setup_directories()

    # Connect to database
    print("[INFO] Connecting to database...")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Get qualified deer
        all_deer = get_qualified_deer(db)

        if len(all_deer) < 10:
            print(f"[ERROR] Only {len(all_deer)} deer. Need at least 10.")
            return 1

        # Split train/val
        random.seed(42)
        shuffled = all_deer.copy()
        random.shuffle(shuffled)
        split_idx = int(len(shuffled) * TRAIN_RATIO)
        train_deer = shuffled[:split_idx]
        val_deer = shuffled[split_idx:]

        print(f"[OK] Train: {len(train_deer)} deer, Val: {len(val_deer)} deer")

        # Process training deer
        print("\n[INFO] Extracting training crops...")
        train_crops = 0
        for idx, (deer_id, deer_name, count) in enumerate(train_deer, 1):
            display = deer_name if deer_name else str(deer_id)[:8]
            crops = process_deer_detections(db, deer_id, deer_name, "train")
            train_crops += crops
            print(f"  [{idx}/{len(train_deer)}] {display}: {crops} crops")

        print(f"[OK] Extracted {train_crops} training crops")

        # Process validation deer
        print("\n[INFO] Extracting validation crops...")
        val_crops = 0
        for idx, (deer_id, deer_name, count) in enumerate(val_deer, 1):
            display = deer_name if deer_name else str(deer_id)[:8]
            crops = process_deer_detections(db, deer_id, deer_name, "val")
            val_crops += crops
            print(f"  [{idx}/{len(val_deer)}] {display}: {crops} crops")

        print(f"[OK] Extracted {val_crops} validation crops")

        # Create metadata
        metadata = f"""# Re-ID Triplet Training Dataset
Generated: 2025-11-16
Feature: 009-reid-enhancement / Phase 2A

Training: {len(train_deer)} deer, {train_crops} crops
Validation: {len(val_deer)} deer, {val_crops} crops
Total: {len(all_deer)} deer, {train_crops + val_crops} crops

Directory: {OUTPUT_DIR}
"""
        (OUTPUT_DIR / "metadata.txt").write_text(metadata)

        # Summary
        print("\n" + "=" * 70)
        print("EXTRACTION COMPLETE")
        print("=" * 70)
        print(f"Training: {len(train_deer)} deer, {train_crops} crops")
        print(f"Validation: {len(val_deer)} deer, {val_crops} crops")
        print(f"Total: {train_crops + val_crops} crops")
        print("\nNext: Run train_triplet_reid.py")

        return 0

    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(main())
