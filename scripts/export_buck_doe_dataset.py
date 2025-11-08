#!/usr/bin/env python3
"""
Export Binary Buck/Doe Classification Dataset

Simple binary classification for sex determination:
- Class 0: Doe (female)
- Class 1: Buck (male, any age)

Usage:
    python3 scripts/export_buck_doe_dataset.py

Output:
    Creates YOLOv8 dataset structure:
    /mnt/i/projects/thumper_counter/training_data/buck_doe/
        train/
            images/
            labels/
        val/
            images/
            labels/
        test/
            images/
            labels/
        dataset.yaml
        metadata.json
"""

import os
import sys
import json
import random
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from PIL import Image

# Add backend to path
sys.path.insert(0, '/app')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://deertrack:Hopkins2019@db:5432/deer_tracking'
)

IMAGE_BASE = Path('/mnt/i/Hopkins_Ranch_Trail_Cam_Pics')
OUTPUT_BASE = Path('/mnt/i/projects/thumper_counter/training_data/buck_doe')

# Binary classification mapping
CLASS_MAPPING = {
    'doe': 0,           # Female
    'buck': 1,          # Male (generic)
    'mature': 1,        # Mature male
    'mid': 1,           # Mid-age male
    'young': 1,         # Young male
}

# Training splits
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

random.seed(42)  # Reproducible splits


def get_reviewed_detections(engine) -> List[Dict]:
    """Get all reviewed, valid detections for buck/doe classification."""
    
    query = text("""
        SELECT
            d.id as detection_id,
            d.bbox,
            d.confidence,
            COALESCE(d.corrected_classification, d.classification) as classification,
            i.id as image_id,
            i.filename,
            i.path as image_path,
            l.name as location_name
        FROM detections d
        JOIN images i ON d.image_id = i.id
        JOIN locations l ON i.location_id = l.id
        WHERE d.is_reviewed = true
          AND d.is_valid = true
          AND COALESCE(d.corrected_classification, d.classification) IN 
              ('doe', 'buck', 'mature', 'mid', 'young')
        ORDER BY l.name, i.filename
    """)
    
    with engine.connect() as conn:
        result = conn.execute(query)
        detections = []
        
        for row in result:
            bbox = json.loads(row.bbox) if isinstance(row.bbox, str) else row.bbox
            
            detections.append({
                'detection_id': str(row.detection_id),
                'bbox': bbox,
                'confidence': row.confidence,
                'classification': row.classification,
                'image_id': str(row.image_id),
                'filename': row.filename,
                'image_path': row.image_path,
                'location': row.location_name,
            })
    
    return detections


def map_to_binary_class(classification: str) -> int:
    """Map classification to binary class (0=doe, 1=buck)."""
    return CLASS_MAPPING.get(classification, -1)


def normalize_bbox(bbox: Dict, img_width: int, img_height: int) -> Tuple[float, float, float, float]:
    """Convert absolute bbox to YOLO normalized format (center_x, center_y, width, height)."""
    x1, y1 = bbox['x1'], bbox['y1']
    x2, y2 = bbox['x2'], bbox['y2']
    
    # Calculate center and dimensions
    width = x2 - x1
    height = y2 - y1
    center_x = x1 + width / 2
    center_y = y1 + height / 2
    
    # Normalize to [0, 1]
    norm_center_x = center_x / img_width
    norm_center_y = center_y / img_height
    norm_width = width / img_width
    norm_height = height / img_height
    
    return norm_center_x, norm_center_y, norm_width, norm_height


def split_dataset(detections: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Split detections into train/val/test, stratified by binary class."""
    
    # Group by binary class
    does = [d for d in detections if map_to_binary_class(d['classification']) == 0]
    bucks = [d for d in detections if map_to_binary_class(d['classification']) == 1]
    
    random.shuffle(does)
    random.shuffle(bucks)
    
    # Split each class
    def split_list(lst):
        n = len(lst)
        n_train = int(n * TRAIN_RATIO)
        n_val = int(n * VAL_RATIO)
        return lst[:n_train], lst[n_train:n_train + n_val], lst[n_train + n_val:]
    
    does_train, does_val, does_test = split_list(does)
    bucks_train, bucks_val, bucks_test = split_list(bucks)
    
    train = does_train + bucks_train
    val = does_val + bucks_val
    test = does_test + bucks_test
    
    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)
    
    return train, val, test


def export_split(detections: List[Dict], split_name: str, output_base: Path) -> Dict:
    """Export one split (train/val/test) in YOLOv8 format."""
    
    images_dir = output_base / split_name / 'images'
    labels_dir = output_base / split_name / 'labels'
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    
    stats = {'total': 0, 'doe': 0, 'buck': 0, 'skipped': 0}
    
    # Group by image to handle multiple detections
    by_image = {}
    for det in detections:
        image_id = det['image_id']
        if image_id not in by_image:
            by_image[image_id] = {
                'filename': det['filename'],
                'location': det['location'],
                'detections': []
            }
        by_image[image_id]['detections'].append(det)
    
    # Export each image
    for image_id, img_data in by_image.items():
        filename = img_data['filename']
        location = img_data['location']
        image_path = IMAGE_BASE / location / filename
        
        if not image_path.exists():
            print(f"[WARN] Image not found: {image_path}")
            stats['skipped'] += 1
            continue
        
        try:
            # Copy image
            output_image_path = images_dir / filename
            shutil.copy2(image_path, output_image_path)
            
            # Get image dimensions
            with Image.open(image_path) as img:
                img_width, img_height = img.size
            
            # Create YOLO label file
            label_path = labels_dir / filename.replace('.jpg', '.txt').replace('.JPG', '.txt')
            
            with open(label_path, 'w') as f:
                for det in img_data['detections']:
                    class_id = map_to_binary_class(det['classification'])
                    
                    if class_id < 0:
                        continue
                    
                    # Normalize bbox
                    cx, cy, w, h = normalize_bbox(det['bbox'], img_width, img_height)
                    
                    # Write YOLO format: class_id center_x center_y width height
                    f.write(f"{class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")
                    
                    stats['total'] += 1
                    if class_id == 0:
                        stats['doe'] += 1
                    else:
                        stats['buck'] += 1
        
        except Exception as e:
            print(f"[FAIL] Error processing {image_path}: {e}")
            stats['skipped'] += 1
            continue
    
    return stats


def create_dataset_yaml(output_base: Path, splits: Dict):
    """Create YOLOv8 dataset.yaml configuration file."""
    
    yaml_content = f"""# Buck/Doe Binary Classification Dataset
# Generated from manually reviewed detections

path: {output_base.absolute()}  # dataset root dir
train: train/images  # train images (relative to 'path')
val: val/images      # val images (relative to 'path')
test: test/images    # test images (relative to 'path')

# Classes
names:
  0: doe   # Female deer
  1: buck  # Male deer (any age)

# Dataset info
nc: 2  # number of classes
"""
    
    yaml_path = output_base / 'dataset.yaml'
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)
    
    print(f"[OK] Created dataset.yaml at {yaml_path}")


def main():
    print("[INFO] Connecting to database...")
    engine = create_engine(DATABASE_URL)
    
    print("[INFO] Querying reviewed detections...")
    detections = get_reviewed_detections(engine)
    print(f"[OK] Found {len(detections)} reviewed, valid detections")
    
    # Show class distribution
    does = sum(1 for d in detections if map_to_binary_class(d['classification']) == 0)
    bucks = sum(1 for d in detections if map_to_binary_class(d['classification']) == 1)
    
    print(f"\n[INFO] Binary class distribution:")
    print(f"  Does (female): {does}")
    print(f"  Bucks (male):  {bucks}")
    
    # Check balance
    if does < 10 or bucks < 10:
        print(f"\n[WARN] Very few examples! Need at least 10 per class.")
        print(f"[WARN] Current: {does} does, {bucks} bucks")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("[INFO] Exiting. Review more images and try again.")
            return
    
    if abs(does - bucks) > max(does, bucks) * 0.5:
        print(f"\n[WARN] Imbalanced dataset: {does} does vs {bucks} bucks")
        print(f"[WARN] Recommend getting more examples of minority class")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("[INFO] Exiting. Review more images to balance dataset.")
            return
    
    # Split dataset
    print("\n[INFO] Splitting dataset (70% train, 15% val, 15% test)...")
    train, val, test = split_dataset(detections)
    print(f"[OK] Train: {len(train)}, Val: {len(val)}, Test: {len(test)}")
    
    # Clean output directory
    if OUTPUT_BASE.exists():
        print(f"\n[WARN] Output directory exists: {OUTPUT_BASE}")
        response = input("Delete and recreate? (y/n): ")
        if response.lower() == 'y':
            shutil.rmtree(OUTPUT_BASE)
        else:
            print("[INFO] Exiting to avoid overwriting data.")
            return
    
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
    
    # Export splits
    print("\n[INFO] Exporting training data...")
    all_stats = {}
    
    for split_name, split_data in [('train', train), ('val', val), ('test', test)]:
        print(f"\n[INFO] Exporting {split_name} split...")
        stats = export_split(split_data, split_name, OUTPUT_BASE)
        all_stats[split_name] = stats
        
        print(f"[OK] {split_name}: {stats['total']} detections")
        print(f"  Does: {stats['doe']}, Bucks: {stats['buck']}, Skipped: {stats['skipped']}")
    
    # Create dataset.yaml
    create_dataset_yaml(OUTPUT_BASE, all_stats)
    
    # Export metadata
    metadata = {
        'total_detections': len(detections),
        'class_counts': {'doe': does, 'buck': bucks},
        'splits': {
            'train': len(train),
            'val': len(val),
            'test': len(test),
        },
        'stats': all_stats,
        'class_mapping': CLASS_MAPPING,
    }
    
    metadata_path = OUTPUT_BASE / 'metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n[OK] Metadata saved to {metadata_path}")
    print(f"\n[SUCCESS] Dataset exported to: {OUTPUT_BASE}")
    print("\n[INFO] Next steps:")
    print("  1. Verify dataset: Check train/val/test directories")
    print("  2. Train model: python3 scripts/train_buck_doe_model.py")
    print("  3. Evaluate: Check mAP scores and confusion matrix")


if __name__ == '__main__':
    main()
