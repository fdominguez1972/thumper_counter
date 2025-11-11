#!/usr/bin/env python3
"""
Export Corrected Classifications for Model Retraining

This script exports corrected/reviewed detections to create an improved training dataset.
Use this to retrain the YOLOv8 model with your manually verified classifications.

Usage:
    python3 scripts/export_training_data.py [options]

Options:
    --output-dir DIR    Output directory (default: /mnt/training_data/corrected)
    --min-confidence    Minimum confidence for ML predictions (default: 0.5)
    --reviewed-only     Only export human-reviewed detections (default: True)
    --format FORMAT     Export format: yolo, csv, or both (default: both)
"""

import os
import sys
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# Add backend to path
sys.path.insert(0, '/app')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from backend.models.detection import Detection
from backend.models.image import Image
from backend.models.deer import Deer
from backend.models.location import Location


# Class mapping for YOLOv8
# Simplified for male/female counting: buck, doe, unknown (no fawn since it contains both sexes)
CLASS_MAPPING = {
    'doe': 3,      # Female deer
    'buck': 5,     # All male deer (any age)
    'mature': 5,   # Mature buck -> buck
    'mid': 5,      # Mid-age buck -> buck
    'young': 5,    # Young buck -> buck
    'fawn': 4,     # Young deer -> unknown (contains both male/female)
    'unknown': 4,  # Unknown sex
    'cattle': 0,   # Cattle
    'pig': 1,      # Pig/feral hog
    'raccoon': 2,  # Raccoon
}

SEX_TO_CLASS = {
    'female': 'doe',
    'male': 'buck',
    'unknown': 'unknown',
}


def get_database_session():
    """Create database session."""
    db_url = f"postgresql://{os.getenv('POSTGRES_USER', 'deertrack')}:" \
             f"{os.getenv('POSTGRES_PASSWORD', 'secure_password_here')}@" \
             f"{os.getenv('POSTGRES_HOST', 'db')}:" \
             f"{os.getenv('POSTGRES_PORT', '5432')}/" \
             f"{os.getenv('POSTGRES_DB', 'deer_tracking')}"

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    return Session()


def export_to_yolo_format(detections: List[Tuple], output_dir: Path, image_dir: Path) -> Dict:
    """
    Export detections to YOLOv8 training format.

    Directory structure:
        output_dir/
            images/
                train/
                val/
            labels/
                train/
                val/
            data.yaml

    Returns:
        Statistics dictionary
    """
    # Create directory structure
    images_train = output_dir / 'images' / 'train'
    images_val = output_dir / 'images' / 'val'
    labels_train = output_dir / 'labels' / 'train'
    labels_val = output_dir / 'labels' / 'val'

    for dir_path in [images_train, images_val, labels_train, labels_val]:
        dir_path.mkdir(parents=True, exist_ok=True)

    stats = {
        'total': 0,
        'train': 0,
        'val': 0,
        'by_class': {},
        'skipped': 0,
        'errors': [],
    }

    # Split 80/20 train/val
    val_split = 0.2

    for idx, (det, img, classification) in enumerate(detections):
        stats['total'] += 1

        # Determine class
        class_name = classification.lower()
        if class_name not in CLASS_MAPPING:
            stats['skipped'] += 1
            stats['errors'].append(f"Unknown class: {class_name}")
            continue

        class_id = CLASS_MAPPING[class_name]
        stats['by_class'][class_name] = stats['by_class'].get(class_name, 0) + 1

        # Check if image file exists
        image_path = Path(img.path)
        if not image_path.exists():
            stats['skipped'] += 1
            stats['errors'].append(f"Image not found: {image_path}")
            continue

        # Determine train/val split
        is_val = (idx % int(1/val_split)) == 0
        dest_images = images_val if is_val else images_train
        dest_labels = labels_val if is_val else labels_train

        if is_val:
            stats['val'] += 1
        else:
            stats['train'] += 1

        # Copy image
        image_filename = f"{img.id}.jpg"
        dest_image_path = dest_images / image_filename
        try:
            shutil.copy2(image_path, dest_image_path)
        except Exception as e:
            stats['skipped'] += 1
            stats['errors'].append(f"Failed to copy {image_path}: {e}")
            continue

        # Create YOLO label file
        # Format: class_id center_x center_y width height (normalized 0-1)
        # Need image dimensions to normalize bbox
        try:
            from PIL import Image as PILImage
            with PILImage.open(image_path) as pil_img:
                img_width, img_height = pil_img.size
        except Exception as e:
            stats['skipped'] += 1
            stats['errors'].append(f"Failed to read image dimensions: {e}")
            continue

        # Calculate normalized YOLO format
        # bbox is stored as {x, y, width, height} - convert to normalized center format
        bbox = det.bbox
        x_center = (bbox['x'] + bbox['width'] / 2) / img_width
        y_center = (bbox['y'] + bbox['height'] / 2) / img_height
        width = bbox['width'] / img_width
        height = bbox['height'] / img_height

        # Write label file
        label_filename = f"{img.id}.txt"
        label_path = dest_labels / label_filename
        with open(label_path, 'w') as f:
            f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

    # Create data.yaml
    yaml_content = f"""# Corrected Training Data (Simplified for Male/Female Counting)
# Exported: {datetime.now().isoformat()}
# Total images: {stats['total']}
# Note: All buck age classes (young, mid, mature) combined into 'buck'
# Note: Fawn maps to 'unknown' since it contains both male and female

path: {output_dir.absolute()}
train: images/train
val: images/val

names:
  0: cattle
  1: pig
  2: raccoon
  3: doe
  4: unknown
  5: buck

# Class distribution:
"""
    for class_name, count in stats['by_class'].items():
        yaml_content += f"#   {class_name}: {count}\n"

    with open(output_dir / 'data.yaml', 'w') as f:
        f.write(yaml_content)

    return stats


def export_to_csv(detections: List[Tuple], output_path: Path) -> Dict:
    """Export detections to CSV for analysis."""
    import csv

    stats = {'total': 0, 'by_class': {}}

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'detection_id', 'image_id', 'image_path', 'timestamp', 'location',
            'ml_classification', 'corrected_classification', 'final_classification',
            'confidence', 'is_reviewed', 'reviewed_by', 'bbox_x1', 'bbox_y1',
            'bbox_x2', 'bbox_y2', 'notes'
        ])

        for det, img, classification in detections:
            stats['total'] += 1
            stats['by_class'][classification] = stats['by_class'].get(classification, 0) + 1

            # Get location name from relationship
            location_name = img.location.name if img.location else 'Unknown'

            # Extract bbox coordinates
            bbox = det.bbox
            x1 = bbox['x']
            y1 = bbox['y']
            x2 = bbox['x'] + bbox['width']
            y2 = bbox['y'] + bbox['height']

            writer.writerow([
                str(det.id),
                str(img.id),
                img.path,
                img.timestamp.isoformat(),
                location_name,
                det.classification,
                det.corrected_classification,
                classification,
                f"{det.confidence:.3f}" if det.confidence else '',
                det.is_reviewed,
                det.reviewed_by or '',
                x1,
                y1,
                x2,
                y2,
                det.correction_notes or '',
            ])

    return stats


def main():
    parser = argparse.ArgumentParser(description='Export corrected classifications for retraining')
    parser.add_argument('--output-dir', default='/mnt/training_data/corrected',
                       help='Output directory for training data')
    parser.add_argument('--min-confidence', type=float, default=0.5,
                       help='Minimum confidence for ML predictions')
    parser.add_argument('--reviewed-only', action='store_true', default=True,
                       help='Only export human-reviewed detections')
    parser.add_argument('--include-invalid', action='store_true', default=False,
                       help='Include detections marked as invalid')
    parser.add_argument('--format', choices=['yolo', 'csv', 'both'], default='both',
                       help='Export format')

    args = parser.parse_args()

    print("[INFO] Exporting corrected training data...")
    print(f"[INFO] Output directory: {args.output_dir}")

    # Get database session
    db = get_database_session()

    # Query detections with eager loading of location
    query = db.query(Detection, Image).join(Image, Detection.image_id == Image.id).options(joinedload(Image.location))

    # Filter criteria
    if not args.include_invalid:
        query = query.filter(Detection.is_valid == True)

    if args.reviewed_only:
        query = query.filter(Detection.is_reviewed == True)

    if args.min_confidence:
        query = query.filter(Detection.confidence >= args.min_confidence)

    results = query.all()

    print(f"[INFO] Found {len(results)} detections matching criteria")

    if len(results) == 0:
        print("[WARN] No detections found. Try adjusting filters.")
        return

    # Prepare data
    detections = []
    for det, img in results:
        # Use corrected classification if available, otherwise ML classification
        classification = det.corrected_classification or det.classification or 'unknown'
        detections.append((det, img, classification))

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export based on format
    if args.format in ['yolo', 'both']:
        print("[INFO] Exporting to YOLOv8 format...")
        stats = export_to_yolo_format(detections, output_dir, Path('/mnt/images'))

        print(f"[OK] YOLOv8 export complete:")
        print(f"     Train: {stats['train']} images")
        print(f"     Val: {stats['val']} images")
        print(f"     Skipped: {stats['skipped']}")
        print(f"     Class distribution:")
        for class_name, count in sorted(stats['by_class'].items()):
            print(f"       {class_name}: {count}")

        if stats['errors']:
            print(f"[WARN] {len(stats['errors'])} errors occurred:")
            for error in stats['errors'][:10]:  # Show first 10
                print(f"       {error}")

    if args.format in ['csv', 'both']:
        print("[INFO] Exporting to CSV...")
        csv_path = output_dir / 'corrected_detections.csv'
        stats = export_to_csv(detections, csv_path)

        print(f"[OK] CSV export complete: {csv_path}")
        print(f"     Total: {stats['total']} detections")
        print(f"     Class distribution:")
        for class_name, count in sorted(stats['by_class'].items()):
            print(f"       {class_name}: {count}")

    # Create README
    readme_path = output_dir / 'README.md'
    with open(readme_path, 'w') as f:
        f.write(f"""# Corrected Training Data Export

Exported: {datetime.now().isoformat()}

## Summary
- Total detections: {len(detections)}
- Reviewed only: {args.reviewed_only}
- Include invalid: {args.include_invalid}
- Min confidence: {args.min_confidence}

## Next Steps

### Retrain YOLOv8 Model
```bash
# From worker container
python3 scripts/train_deer_multiclass.py \\
    --data /mnt/training_data/corrected/data.yaml \\
    --epochs 100 \\
    --batch 16 \\
    --name corrected_model
```

### Evaluate Model
```bash
python3 scripts/evaluate_multiclass_model.py \\
    --model /app/src/models/runs/corrected_model/weights/best.pt
```

### Deploy Improved Model
```bash
# Replace current model
cp /app/src/models/runs/corrected_model/weights/best.pt \\
   /app/src/models/yolov8n_deer.pt

# Restart worker to load new model
docker-compose restart worker
```

## Class Mapping (Simplified for Male/Female Counting)
- doe (3): Female deer
- buck (5): Male deer (all ages - young/mid/mature combined)
- unknown (4): Unknown sex (includes fawn which contains both male/female)
- cattle (0): Cattle
- pig (1): Pig/feral hog
- raccoon (2): Raccoon

## Notes
- All buck age classes (young, mid, mature) combined into single 'buck' class
- Fawn class merged into 'unknown' since young deer can be either male or female
- This allows accurate male vs female population counting
- Mature buck classifier can be built later from collected images
- Review the corrected_detections.csv file for detailed analysis of your corrections.
""")

    print(f"[OK] Export complete! See {readme_path} for next steps.")
    print("\n[INFO] To retrain the model with your corrections:")
    print("      docker-compose exec worker python3 scripts/train_deer_multiclass.py \\")
    print(f"          --data {output_dir}/data.yaml --epochs 100 --batch 16")


if __name__ == '__main__':
    main()
