#!/usr/bin/env python3
"""
Extract triplet training dataset for fine-tuned Re-ID model.

This script extracts detection crops organized for triplet loss training:
- Anchor: A detection of deer A
- Positive: Different detection of same deer A
- Negative: Detection of different deer B

Only includes deer with 10+ detections for quality training data.

Feature: 009-reid-enhancement / Phase 2A
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
import random

# Add backend to path for imports
sys.path.insert(0, '/app')

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from backend.models.deer import Deer
from backend.models.detection import Detection
from backend.core.database import DATABASE_URL


# Configuration
MIN_DETECTIONS_PER_DEER = 10  # Minimum detections needed for training
OUTPUT_DIR = Path("/app/src/models/training_data/reid_triplet_20251116")
CROPS_DIR = Path("/app/data/crops")  # Where detection crops are stored

# Training/validation split
TRAIN_RATIO = 0.8  # 80% train, 20% validation


def setup_output_directories():
    """Create output directory structure for triplet dataset."""
    print("[INFO] Setting up output directories...")

    # Create main directories
    (OUTPUT_DIR / "train").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "val").mkdir(parents=True, exist_ok=True)

    print(f"[OK] Output directory: {OUTPUT_DIR}")


def get_deer_with_detections(db) -> List[Tuple[str, str, int]]:
    """
    Get all deer with sufficient detections for training.

    Returns:
        List of tuples: (deer_id, deer_name, detection_count)
    """
    print(f"[INFO] Querying deer with >={MIN_DETECTIONS_PER_DEER} detections...")

    results = db.query(
        Deer.id,
        Deer.name,
        func.count(Detection.id).label('detection_count')
    ).join(
        Detection, Deer.id == Detection.deer_id
    ).group_by(
        Deer.id, Deer.name
    ).having(
        func.count(Detection.id) >= MIN_DETECTIONS_PER_DEER
    ).order_by(
        func.count(Detection.id).desc()
    ).all()

    print(f"[OK] Found {len(results)} deer with sufficient detections")
    return results


def get_detection_crops_for_deer(db, deer_id: str) -> List[str]:
    """
    Get all detection crop paths for a specific deer.

    Args:
        deer_id: UUID of the deer

    Returns:
        List of crop file paths
    """
    detections = db.query(Detection.id).filter(
        Detection.deer_id == deer_id
    ).all()

    crop_paths = []
    for det in detections:
        crop_path = CROPS_DIR / f"{det.id}.jpg"
        if crop_path.exists():
            crop_paths.append(str(crop_path))

    return crop_paths


def split_train_val(deer_list: List[Tuple], train_ratio: float = 0.8) -> Tuple[List, List]:
    """
    Split deer into training and validation sets.

    Args:
        deer_list: List of (deer_id, deer_name, detection_count) tuples
        train_ratio: Fraction for training (default 0.8)

    Returns:
        Tuple of (train_deer, val_deer) lists
    """
    random.seed(42)  # For reproducibility
    shuffled = deer_list.copy()
    random.shuffle(shuffled)

    split_idx = int(len(shuffled) * train_ratio)
    train_deer = shuffled[:split_idx]
    val_deer = shuffled[split_idx:]

    return train_deer, val_deer


def copy_deer_crops(db, deer_list: List[Tuple], output_subdir: str):
    """
    Copy detection crops for each deer to organized directory structure.

    Args:
        deer_list: List of (deer_id, deer_name, detection_count) tuples
        output_subdir: 'train' or 'val'
    """
    output_path = OUTPUT_DIR / output_subdir

    total_crops = 0
    total_deer = len(deer_list)

    for idx, (deer_id, deer_name, detection_count) in enumerate(deer_list, 1):
        # Create directory for this deer
        deer_dir_name = f"{deer_id}"  # Use UUID as folder name
        deer_dir = output_path / deer_dir_name
        deer_dir.mkdir(exist_ok=True)

        # Get and copy all crop files
        crop_paths = get_detection_crops_for_deer(db, deer_id)

        if len(crop_paths) < MIN_DETECTIONS_PER_DEER:
            print(f"  [WARN] Deer {deer_id} has only {len(crop_paths)} valid crops (expected {detection_count})")

        for crop_path in crop_paths:
            crop_filename = Path(crop_path).name
            dest_path = deer_dir / crop_filename
            shutil.copy2(crop_path, dest_path)

        total_crops += len(crop_paths)

        deer_display = deer_name if deer_name else str(deer_id)[:8]
        print(f"  [{idx}/{total_deer}] {deer_display}: {len(crop_paths)} crops -> {deer_dir_name}/")

    print(f"[OK] Copied {total_crops} crops for {total_deer} deer to {output_subdir}/")
    return total_crops


def create_metadata_file(train_deer: List, val_deer: List, train_crops: int, val_crops: int):
    """Create metadata file documenting the dataset."""
    metadata = f"""# Re-ID Triplet Training Dataset
Generated: 2025-11-16
Feature: 009-reid-enhancement / Phase 2A

## Dataset Statistics

Training Set:
- Deer: {len(train_deer)}
- Total Crops: {train_crops}
- Avg Crops/Deer: {train_crops / len(train_deer):.1f}

Validation Set:
- Deer: {len(val_deer)}
- Total Crops: {val_crops}
- Avg Crops/Deer: {val_crops / len(val_deer):.1f}

Total:
- Deer: {len(train_deer) + len(val_deer)}
- Total Crops: {train_crops + val_crops}

## Directory Structure

```
reid_triplet_20251116/
├── train/
│   ├── <deer_id_1>/
│   │   ├── <detection_id_1>.jpg
│   │   ├── <detection_id_2>.jpg
│   │   └── ...
│   ├── <deer_id_2>/
│   └── ...
├── val/
│   └── (same structure)
└── metadata.txt (this file)
```

## Triplet Loss Training

For each iteration:
1. Select anchor: Random crop from deer A
2. Select positive: Different crop from same deer A
3. Select negative: Crop from different deer B

Loss: L = max(0, d(anchor, positive) - d(anchor, negative) + margin)

## Usage

```python
from scripts.train_triplet_reid import train_triplet_model

model = train_triplet_model(
    data_dir="src/models/training_data/reid_triplet_20251116",
    epochs=100,
    batch_size=32,
    margin=0.2
)
```
"""

    metadata_path = OUTPUT_DIR / "metadata.txt"
    metadata_path.write_text(metadata)
    print(f"[OK] Metadata written to {metadata_path}")


def main():
    """Main extraction workflow."""
    print("=" * 70)
    print("Re-ID Triplet Dataset Extraction")
    print("=" * 70)

    # Setup
    setup_output_directories()

    # Connect to database
    print("[INFO] Connecting to database...")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Get deer with sufficient detections
        all_deer = get_deer_with_detections(db)

        if len(all_deer) < 10:
            print(f"[ERROR] Only {len(all_deer)} deer found. Need at least 10 for training.")
            return 1

        # Split into train/val
        print(f"[INFO] Splitting into train ({TRAIN_RATIO:.0%}) and val ({1-TRAIN_RATIO:.0%})...")
        train_deer, val_deer = split_train_val(all_deer, TRAIN_RATIO)

        print(f"[OK] Train: {len(train_deer)} deer, Val: {len(val_deer)} deer")

        # Copy crops to organized structure
        print("\n[INFO] Copying training crops...")
        train_crops = copy_deer_crops(db, train_deer, "train")

        print("\n[INFO] Copying validation crops...")
        val_crops = copy_deer_crops(db, val_deer, "val")

        # Create metadata
        print("\n[INFO] Creating metadata file...")
        create_metadata_file(train_deer, val_deer, train_crops, val_crops)

        # Summary
        print("\n" + "=" * 70)
        print("EXTRACTION COMPLETE")
        print("=" * 70)
        print(f"Output Directory: {OUTPUT_DIR}")
        print(f"Training Deer: {len(train_deer)} ({train_crops} crops)")
        print(f"Validation Deer: {len(val_deer)} ({val_crops} crops)")
        print(f"Total: {len(all_deer)} deer, {train_crops + val_crops} crops")
        print("\nNext step: Run train_triplet_reid.py to fine-tune the model")

        return 0

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
