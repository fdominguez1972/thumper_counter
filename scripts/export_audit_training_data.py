#!/usr/bin/env python3
"""
Export Audit-Corrected Training Data
Creates training dataset from manually audited low-confidence detections
Date: November 16, 2025
"""
import subprocess
import json
import shutil
from pathlib import Path
from datetime import datetime

# Configuration
IMAGE_BASE_PATH = Path("I:/Hopkins_Ranch_Trail_Cam_Pics")
OUTPUT_BASE = Path("I:/projects/thumper_counter/src/models/training_data/audit_corrected_20251116")
SUBDIRS = ["100", "270", "HAYFIELD", "S2_SANCTUARY2", "S5_SANCTUARY5", "WATERHOLE"]

# Class mapping (YOLOv8 format)
CLASS_MAP = {
    'buck': 0,
    'doe': 1,
    'fawn': 2,
    'cattle': 3,
    'pig': 4,
    'raccoon': 5,
}

def query_database(sql: str) -> list:
    """Execute SQL query and return results"""
    # Write SQL to temp file to avoid shell escaping issues
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as f:
        f.write(sql)
        query_file = f.name

    cmd = f'docker-compose exec -T db psql -U deertrack deer_tracking -t -A -f -'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, input=sql, cwd="I:/projects/thumper_counter")

    if result.returncode != 0:
        print(f"[FAIL] Database query failed: {result.stderr}")
        return []

    return [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]

def find_image_file(filename: str) -> Path:
    """Find image file in subdirectories"""
    for subdir in SUBDIRS:
        filepath = IMAGE_BASE_PATH / subdir / filename
        if filepath.exists():
            return filepath
    return None

def export_audited_detections():
    """Export all audited detections with corrected classifications"""
    print("="*70)
    print("AUDIT-CORRECTED TRAINING DATA EXPORT")
    print("="*70)

    # Get all reviewed detections
    sql = """
    SELECT d.id, i.filename, d.classification, d.bbox
    FROM detections d
    JOIN images i ON d.image_id = i.id
    WHERE d.is_reviewed = true
      AND d.classification IN ('buck', 'doe', 'fawn', 'cattle', 'pig')
    ORDER BY d.classification;
    """

    print("[INFO] Querying database for audited detections...")
    rows = query_database(sql)
    print(f"[OK] Found {len(rows)} audited detections")

    # Parse results
    detections = []
    for row in rows:
        parts = row.split('|')
        if len(parts) >= 4:
            det_id, filename, classification, bbox_str = parts[0], parts[1], parts[2], parts[3]

            # Parse bbox (x, y, width, height format from database)
            try:
                bbox = json.loads(bbox_str) if bbox_str else None
            except:
                bbox = None

            detections.append({
                'id': det_id,
                'filename': filename,
                'classification': classification,
                'bbox': bbox
            })

    # Create output directories
    train_images_dir = OUTPUT_BASE / "images" / "train"
    val_images_dir = OUTPUT_BASE / "images" / "val"
    train_labels_dir = OUTPUT_BASE / "labels" / "train"
    val_labels_dir = OUTPUT_BASE / "labels" / "val"

    for dir_path in [train_images_dir, val_images_dir, train_labels_dir, val_labels_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Split train/val (80/20)
    split_idx = int(len(detections) * 0.8)

    # Group by image (multiple detections per image)
    image_detections = {}
    for det in detections:
        if det['filename'] not in image_detections:
            image_detections[det['filename']] = []
        image_detections[det['filename']].append(det)

    image_files = list(image_detections.keys())
    train_files = image_files[:int(len(image_files) * 0.8)]
    val_files = image_files[int(len(image_files) * 0.8):]

    # Export train set
    print(f"[INFO] Exporting {len(train_files)} training images...")
    export_count = 0
    for filename in train_files:
        # Find source image
        src_path = find_image_file(filename)
        if not src_path:
            continue

        # Copy image
        dst_path = train_images_dir / filename
        shutil.copy2(src_path, dst_path)

        # Create YOLO label file
        label_path = train_labels_dir / f"{src_path.stem}.txt"
        with open(label_path, 'w') as f:
            for det in image_detections[filename]:
                if det['bbox'] and det['classification'] in CLASS_MAP:
                    # Convert bbox to YOLO format (class x_center y_center width height)
                    # bbox from DB is {x, y, width, height} in pixels
                    # YOLO needs normalized coordinates
                    # We'll need image dimensions - assume 4000x3000 for trail cameras
                    img_width = 4000
                    img_height = 3000

                    x = det['bbox']['x']
                    y = det['bbox']['y']
                    w = det['bbox']['width']
                    h = det['bbox']['height']

                    # Convert to YOLO format (x_center, y_center normalized)
                    x_center = (x + w/2) / img_width
                    y_center = (y + h/2) / img_height
                    w_norm = w / img_width
                    h_norm = h / img_height

                    class_id = CLASS_MAP[det['classification']]
                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}\n")

        export_count += 1

    print(f"[OK] Exported {export_count} training images")

    # Export validation set
    print(f"[INFO] Exporting {len(val_files)} validation images...")
    export_count = 0
    for filename in val_files:
        src_path = find_image_file(filename)
        if not src_path:
            continue

        dst_path = val_images_dir / filename
        shutil.copy2(src_path, dst_path)

        label_path = val_labels_dir / f"{src_path.stem}.txt"
        with open(label_path, 'w') as f:
            for det in image_detections[filename]:
                if det['bbox'] and det['classification'] in CLASS_MAP:
                    img_width = 4000
                    img_height = 3000

                    x = det['bbox']['x']
                    y = det['bbox']['y']
                    w = det['bbox']['width']
                    h = det['bbox']['height']

                    x_center = (x + w/2) / img_width
                    y_center = (y + h/2) / img_height
                    w_norm = w / img_width
                    h_norm = h / img_height

                    class_id = CLASS_MAP[det['classification']]
                    f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}\n")

        export_count += 1

    print(f"[OK] Exported {export_count} validation images")

    # Count class distribution
    class_counts = {}
    for det in detections:
        cls = det['classification']
        class_counts[cls] = class_counts.get(cls, 0) + 1

    print()
    print("Class Distribution:")
    for cls, count in sorted(class_counts.items()):
        print(f"  {cls}: {count}")

    # Create data.yaml
    yaml_content = f"""# Audit-Corrected Training Data
# Exported: {datetime.now().isoformat()}
# Total detections: {len(detections)}
# Source: Manual vision audit (96.8% accuracy)

path: {OUTPUT_BASE}
train: images/train
val: images/val

names:
  0: buck
  1: doe
  2: fawn
  3: cattle
  4: pig
  5: raccoon

# Class distribution:
{chr(10).join(f'#   {cls}: {count}' for cls, count in sorted(class_counts.items()))}
"""

    yaml_path = OUTPUT_BASE / "data.yaml"
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)

    print(f"[OK] Created {yaml_path}")
    print("="*70)
    print("[OK] Export complete!")
    print(f"Dataset: {OUTPUT_BASE}")
    print("="*70)

if __name__ == "__main__":
    export_audited_detections()
