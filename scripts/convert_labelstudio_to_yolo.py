#!/usr/bin/env python3
"""
Convert Label Studio Annotations to YOLOv8-Pose Format
Processes antler keypoint annotations for Phase 2B training
Date: November 16, 2025
"""
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

# Paths
LABELSTUDIO_EXPORT = Path("src/models/training_data/antler_annotation_samples/antler_annotations_phase2b.json")
SOURCE_IMAGES = Path("src/models/training_data/antler_annotation_samples")
OUTPUT_BASE = Path("src/models/training_data/antler_yolo_20251116")

# YOLOv8-Pose keypoint order (16 antler keypoints)
KEYPOINT_ORDER = [
    'left_main_beam',
    'left_brow_tine',
    'left_g2',
    'left_g3',
    'left_g4',
    'left_tip',
    'left_bez_tine',
    'left_royal_tine',
    'right_main_beam',
    'right_brow_tine',
    'right_g2',
    'right_g3',
    'right_g4',
    'right_tip',
    'right_bez_tine',
    'right_royal_tine',
]

# Class mapping
CLASS_MAP = {
    'buck': 0,
    'doe': 1,
    'fawn': 2,
}

def load_labelstudio_export(path: Path) -> List[Dict]:
    """Load Label Studio JSON export"""
    with open(path, 'r') as f:
        return json.load(f)

def get_image_filename(task: Dict) -> str:
    """Extract image filename from task"""
    # Try different possible fields
    filename = task.get('file_upload')
    if not filename:
        filename = task.get('data', {}).get('image')
    if not filename:
        raise ValueError(f"Could not find filename in task: {task.get('id')}")

    # Remove any path prefix
    return Path(filename).name

def find_source_image(filename: str, source_dir: Path) -> Path:
    """Find source image file in subdirectories"""
    # Label Studio may have added UUID prefix - try exact match first
    for subdir in ['bucks', 'does', 'mixed']:
        filepath = source_dir / subdir / filename
        if filepath.exists():
            return filepath

    # Try matching by suffix (Label Studio adds UUIDs)
    # Example: bc0df27e-05a1a900-... becomes just 05a1a900-...
    # Extract the actual filename part after first UUID
    if '_' in filename:
        # Get everything after the first UUID (format: UUID-UUID_actual_filename)
        parts = filename.split('_', 1)
        if len(parts) == 2:
            # Get the second part
            suffix = '_' + parts[1]

            for subdir in ['bucks', 'does', 'mixed']:
                subdir_path = source_dir / subdir
                for img_file in subdir_path.glob('*'):
                    if img_file.name.endswith(suffix):
                        return img_file

    # Try without subdirectories
    filepath = source_dir / filename
    if filepath.exists():
        return filepath

    raise FileNotFoundError(f"Could not find image: {filename}")

def convert_bbox_to_yolo(bbox: Dict, img_width: int, img_height: int) -> Tuple[float, float, float, float]:
    """Convert Label Studio bbox to YOLO format (x_center, y_center, width, height)"""
    # Label Studio uses percentage coordinates
    x = bbox['x'] / 100.0
    y = bbox['y'] / 100.0
    w = bbox['width'] / 100.0
    h = bbox['height'] / 100.0

    # Convert to center coordinates
    x_center = x + w / 2.0
    y_center = y + h / 2.0

    return x_center, y_center, w, h

def extract_keypoints(results: List[Dict], img_width: int, img_height: int) -> Dict[str, Tuple[float, float]]:
    """Extract keypoints from annotation results"""
    keypoints = {}

    for result in results:
        if result.get('type') == 'keypointlabels':
            value = result.get('value', {})
            labels = value.get('keypointlabels', [])

            if labels:
                label = labels[0]
                x = value['x'] / 100.0  # Convert from percentage
                y = value['y'] / 100.0
                keypoints[label] = (x, y)

    return keypoints

def format_yolo_keypoints(keypoints: Dict[str, Tuple[float, float]]) -> List[float]:
    """Format keypoints in YOLO order with visibility flags"""
    yolo_keypoints = []

    for kp_name in KEYPOINT_ORDER:
        if kp_name in keypoints:
            x, y = keypoints[kp_name]
            yolo_keypoints.extend([x, y, 2])  # 2 = visible
        else:
            yolo_keypoints.extend([0, 0, 0])  # 0 = not labeled

    return yolo_keypoints

def convert_task(task: Dict, output_labels_dir: Path, output_images_dir: Path, source_images_dir: Path):
    """Convert single Label Studio task to YOLO format"""
    filename = get_image_filename(task)

    # Find source image
    try:
        source_image = find_source_image(filename, source_images_dir)
    except FileNotFoundError:
        print(f"[WARN] Image not found: {filename} - skipping")
        return False

    # Copy image to output directory
    dest_image = output_images_dir / filename
    shutil.copy2(source_image, dest_image)

    # Process annotations
    if not task.get('annotations'):
        print(f"[WARN] No annotations for {filename} - skipping")
        return False

    annotation = task['annotations'][0]  # Use first annotation
    results = annotation.get('result', [])

    # Get image dimensions
    img_width = results[0].get('original_width', 3840) if results else 3840
    img_height = results[0].get('original_height', 2160) if results else 2160

    # Create YOLO label file
    label_path = output_labels_dir / f"{Path(filename).stem}.txt"

    with open(label_path, 'w') as f:
        # Group results by bbox
        bboxes = {}

        for result in results:
            if result.get('type') == 'rectanglelabels':
                result_id = result.get('id')
                value = result.get('value', {})
                labels = value.get('rectanglelabels', [])

                if labels:
                    class_name = labels[0].lower()
                    if class_name in CLASS_MAP:
                        bboxes[result_id] = {
                            'class': CLASS_MAP[class_name],
                            'bbox': value,
                            'keypoints': {}
                        }

        # Extract keypoints (for buck class only)
        keypoints = extract_keypoints(results, img_width, img_height)

        # Write YOLO annotations
        for bbox_id, bbox_data in bboxes.items():
            class_id = bbox_data['class']
            bbox = bbox_data['bbox']

            # Convert bbox to YOLO format
            x_center, y_center, w, h = convert_bbox_to_yolo(bbox, img_width, img_height)

            # Format keypoints (only for bucks)
            if class_id == 0:  # buck
                kp_values = format_yolo_keypoints(keypoints)
                kp_str = ' '.join(map(str, kp_values))
                f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f} {kp_str}\n")
            else:
                # Does and fawns: no keypoints
                f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")

    return True

def create_dataset_yaml(output_dir: Path, train_count: int, val_count: int):
    """Create dataset.yaml for YOLOv8"""
    yaml_content = f"""# Antler Detection Dataset - Phase 2B
# Converted from Label Studio annotations
# Date: 2025-11-16

path: {output_dir.absolute()}
train: images/train
val: images/val

# Classes
nc: 3
names:
  0: buck
  1: doe
  2: fawn

# Keypoints (16 antler points - bucks only)
kpt_shape: [16, 3]  # 16 keypoints, 3 values each (x, y, visibility)

# Keypoint names (for reference)
keypoint_names:
  - left_main_beam
  - left_brow_tine
  - left_g2
  - left_g3
  - left_g4
  - left_tip
  - left_bez_tine
  - left_royal_tine
  - right_main_beam
  - right_brow_tine
  - right_g2
  - right_g3
  - right_g4
  - right_tip
  - right_bez_tine
  - right_royal_tine

# Dataset statistics
train_images: {train_count}
val_images: {val_count}
total_images: {train_count + val_count}

# Annotation source
source: Label Studio (manual annotation)
annotator: User
export_date: 2025-11-16
"""

    yaml_path = output_dir / "data.yaml"
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)

    print(f"[OK] Created {yaml_path}")

def main():
    print("="*70)
    print("LABEL STUDIO TO YOLO CONVERSION - ANTLER DETECTION")
    print("="*70)
    print()

    # Load Label Studio export
    print(f"[INFO] Loading Label Studio export: {LABELSTUDIO_EXPORT}")
    tasks = load_labelstudio_export(LABELSTUDIO_EXPORT)
    print(f"[OK] Loaded {len(tasks)} tasks")
    print()

    # Create output directories
    train_images_dir = OUTPUT_BASE / "images" / "train"
    val_images_dir = OUTPUT_BASE / "images" / "val"
    train_labels_dir = OUTPUT_BASE / "labels" / "train"
    val_labels_dir = OUTPUT_BASE / "labels" / "val"

    for dir_path in [train_images_dir, val_images_dir, train_labels_dir, val_labels_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Split train/val (80/20)
    split_idx = int(len(tasks) * 0.8)
    train_tasks = tasks[:split_idx]
    val_tasks = tasks[split_idx:]

    print(f"[INFO] Train/val split: {len(train_tasks)}/{len(val_tasks)}")
    print()

    # Convert training set
    print(f"[INFO] Converting {len(train_tasks)} training tasks...")
    train_success = 0
    for task in train_tasks:
        if convert_task(task, train_labels_dir, train_images_dir, SOURCE_IMAGES):
            train_success += 1

    print(f"[OK] Converted {train_success}/{len(train_tasks)} training tasks")
    print()

    # Convert validation set
    print(f"[INFO] Converting {len(val_tasks)} validation tasks...")
    val_success = 0
    for task in val_tasks:
        if convert_task(task, val_labels_dir, val_images_dir, SOURCE_IMAGES):
            val_success += 1

    print(f"[OK] Converted {val_success}/{len(val_tasks)} validation tasks")
    print()

    # Create dataset.yaml
    create_dataset_yaml(OUTPUT_BASE, train_success, val_success)

    # Summary
    print("="*70)
    print("[OK] CONVERSION COMPLETE")
    print("="*70)
    print()
    print(f"Output directory: {OUTPUT_BASE}")
    print(f"Train images: {train_success}")
    print(f"Val images: {val_success}")
    print(f"Total: {train_success + val_success}")
    print()
    print("Next steps:")
    print("1. Review annotations: check labels in images/train/")
    print("2. Train YOLOv8-pose model: python3 scripts/train_antler_model.py")
    print("3. Validate results on test set")
    print()
    print("="*70)

if __name__ == "__main__":
    main()
