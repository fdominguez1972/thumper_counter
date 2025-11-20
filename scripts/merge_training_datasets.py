#!/usr/bin/env python3
"""
Merge audit-corrected dataset with previous training dataset.
Creates a combined dataset for retraining.
"""

import shutil
from pathlib import Path
from datetime import datetime

# Source datasets
AUDIT_DATASET = Path("src/models/training_data/audit_corrected_20251116")
PREVIOUS_DATASET = Path("src/models/training_data/corrected_final_20251111")

# Output merged dataset
MERGED_DATASET = Path(f"src/models/training_data/merged_corrected_{datetime.now().strftime('%Y%m%d')}")

def merge_datasets():
    """Merge two YOLO datasets into one."""
    print("="*80)
    print("MERGING TRAINING DATASETS")
    print("="*80)

    # Create output directory structure
    print(f"\n[1/5] Creating output directory: {MERGED_DATASET}")
    for split in ['train', 'val']:
        (MERGED_DATASET / 'images' / split).mkdir(parents=True, exist_ok=True)
        (MERGED_DATASET / 'labels' / split).mkdir(parents=True, exist_ok=True)

    stats = {
        'train': {'images': 0, 'labels': 0},
        'val': {'images': 0, 'labels': 0}
    }

    # Copy files from both datasets
    for split in ['train', 'val']:
        print(f"\n[{2 if split == 'train' else 3}/5] Processing {split} split...")

        # Copy from previous dataset
        prev_img_dir = PREVIOUS_DATASET / 'images' / split
        prev_lbl_dir = PREVIOUS_DATASET / 'labels' / split

        if prev_img_dir.exists():
            print(f"  Copying from {PREVIOUS_DATASET.name}/{split}...")
            for img_file in prev_img_dir.glob('*.jpg'):
                # Copy image
                dest_img = MERGED_DATASET / 'images' / split / img_file.name
                shutil.copy2(img_file, dest_img)
                stats[split]['images'] += 1

                # Copy corresponding label
                lbl_file = prev_lbl_dir / f"{img_file.stem}.txt"
                if lbl_file.exists():
                    dest_lbl = MERGED_DATASET / 'labels' / split / lbl_file.name
                    shutil.copy2(lbl_file, dest_lbl)
                    stats[split]['labels'] += 1

        # Copy from audit dataset
        audit_img_dir = AUDIT_DATASET / 'images' / split
        audit_lbl_dir = AUDIT_DATASET / 'labels' / split

        if audit_img_dir.exists():
            print(f"  Copying from {AUDIT_DATASET.name}/{split}...")
            for img_file in audit_img_dir.glob('*.jpg'):
                # Check if file already exists (avoid duplicates)
                dest_img = MERGED_DATASET / 'images' / split / img_file.name

                if dest_img.exists():
                    print(f"    [SKIP] Duplicate: {img_file.name}")
                    continue

                # Copy image
                shutil.copy2(img_file, dest_img)
                stats[split]['images'] += 1

                # Copy corresponding label
                lbl_file = audit_lbl_dir / f"{img_file.stem}.txt"
                if lbl_file.exists():
                    dest_lbl = MERGED_DATASET / 'labels' / split / lbl_file.name
                    shutil.copy2(lbl_file, dest_lbl)
                    stats[split]['labels'] += 1

    # Create data.yaml
    print(f"\n[4/5] Creating data.yaml...")
    data_yaml = f"""# Merged Training Dataset
# Created: {datetime.now().isoformat()}
# Source datasets:
#   - {PREVIOUS_DATASET.name}: 779 images
#   - {AUDIT_DATASET.name}: 28 images (vision audit corrections)

path: /app/{MERGED_DATASET}
train: images/train
val: images/val

names:
  0: buck
  1: doe
  2: fawn
  3: cattle
  4: pig
  5: raccoon

# Dataset statistics:
#   Train: {stats['train']['images']} images
#   Val: {stats['val']['images']} images
#   Total: {stats['train']['images'] + stats['val']['images']} images
"""

    with open(MERGED_DATASET / 'data.yaml', 'w') as f:
        f.write(data_yaml)

    # Print summary
    print(f"\n[5/5] Merge complete!")
    print("="*80)
    print("DATASET SUMMARY")
    print("="*80)
    print(f"\nOutput directory: {MERGED_DATASET}")
    print(f"\nTrain split:")
    print(f"  Images: {stats['train']['images']}")
    print(f"  Labels: {stats['train']['labels']}")
    print(f"\nValidation split:")
    print(f"  Images: {stats['val']['images']}")
    print(f"  Labels: {stats['val']['labels']}")
    print(f"\nTotal: {stats['train']['images'] + stats['val']['images']} images")
    print("\n" + "="*80)

    # Verify counts match
    if stats['train']['images'] != stats['train']['labels']:
        print(f"\n[WARN] Train image/label count mismatch!")
    if stats['val']['images'] != stats['val']['labels']:
        print(f"\n[WARN] Val image/label count mismatch!")

    print(f"\n[OK] Merged dataset ready at: {MERGED_DATASET}")
    print(f"[OK] Use this path in training script: /app/{MERGED_DATASET}")
    print("\n" + "="*80 + "\n")

    return MERGED_DATASET


if __name__ == "__main__":
    merged_path = merge_datasets()
