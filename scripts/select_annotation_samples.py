#!/usr/bin/env python3
"""
Select 100 high-quality sample images for antler detection annotation.

Selection Criteria:
- 50 bucks with clear antlers (high confidence, large bbox)
- 25 does with clear features (high confidence)
- 25 mixed (fawns, challenging cases, various conditions)

Feature: Phase 2B - Antler Detection Annotation
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, '/app')

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from backend.models.detection import Detection
from backend.models.image import Image
from backend.core.database import DATABASE_URL

# Configuration
OUTPUT_DIR = Path("/app/src/models/training_data/antler_annotation_samples")
TARGET_BUCKS = 50
TARGET_DOES = 25
TARGET_MIXED = 25

# Quality thresholds
MIN_CONFIDENCE = 0.65  # High confidence only
MIN_BBOX_SIZE = 15000  # pixels (e.g., 150x100 minimum)


def calculate_bbox_area(bbox: dict) -> int:
    """Calculate bbox area in pixels."""
    return bbox['width'] * bbox['height']


def setup_directories():
    """Create output directory structure."""
    print("[INFO] Setting up directories...")

    (OUTPUT_DIR / "bucks").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "does").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "mixed").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "metadata").mkdir(parents=True, exist_ok=True)

    print(f"[OK] Output: {OUTPUT_DIR}")


def select_bucks(db) -> List[Dict]:
    """
    Select 50 high-quality buck images.

    Criteria:
    - Classification = 'buck'
    - High confidence (>0.65)
    - Large bbox (good visibility)
    - Diverse locations and times
    """
    print(f"\n[INFO] Selecting {TARGET_BUCKS} buck images...")

    # Query high-quality buck detections
    results = db.query(
        Detection.id.label('detection_id'),
        Detection.confidence,
        Detection.bbox,
        Image.id.label('image_id'),
        Image.path,
        Image.filename,
        Image.timestamp,
        Image.location_id
    ).join(
        Image, Detection.image_id == Image.id
    ).filter(
        Detection.classification == 'buck',
        Detection.confidence >= MIN_CONFIDENCE,
        Detection.bbox.isnot(None),
        Image.path.isnot(None)
    ).order_by(
        Detection.confidence.desc()
    ).limit(TARGET_BUCKS * 3).all()  # Get 3x for filtering

    # Filter by bbox size and diversify
    selected = []
    locations_seen = set()

    for row in results:
        if len(selected) >= TARGET_BUCKS:
            break

        bbox_area = calculate_bbox_area(row.bbox)

        if bbox_area < MIN_BBOX_SIZE:
            continue

        # Prefer diversity in locations
        if len(selected) > TARGET_BUCKS // 2:
            if row.location_id in locations_seen and len(locations_seen) < 3:
                continue  # Skip if we have too many from this location

        selected.append({
            'detection_id': str(row.detection_id),
            'image_id': str(row.image_id),
            'path': row.path,
            'filename': row.filename,
            'confidence': float(row.confidence),
            'bbox': row.bbox,
            'bbox_area': bbox_area,
            'classification': 'buck',
            'timestamp': row.timestamp.isoformat(),
            'location_id': str(row.location_id) if row.location_id else None
        })

        locations_seen.add(row.location_id)

    print(f"[OK] Selected {len(selected)} bucks from {len(locations_seen)} locations")
    print(f"    Avg confidence: {sum(s['confidence'] for s in selected) / len(selected):.3f}")
    print(f"    Avg bbox area: {sum(s['bbox_area'] for s in selected) / len(selected):.0f} px")

    return selected


def select_does(db) -> List[Dict]:
    """
    Select 25 high-quality doe images.

    Criteria:
    - Classification = 'doe'
    - High confidence
    - Good visibility
    """
    print(f"\n[INFO] Selecting {TARGET_DOES} doe images...")

    results = db.query(
        Detection.id.label('detection_id'),
        Detection.confidence,
        Detection.bbox,
        Image.id.label('image_id'),
        Image.path,
        Image.filename,
        Image.timestamp,
        Image.location_id
    ).join(
        Image, Detection.image_id == Image.id
    ).filter(
        Detection.classification == 'doe',
        Detection.confidence >= MIN_CONFIDENCE,
        Detection.bbox.isnot(None),
        Image.path.isnot(None)
    ).order_by(
        Detection.confidence.desc()
    ).limit(TARGET_DOES * 2).all()

    selected = []
    for row in results:
        if len(selected) >= TARGET_DOES:
            break

        bbox_area = calculate_bbox_area(row.bbox)

        if bbox_area < MIN_BBOX_SIZE:
            continue

        selected.append({
            'detection_id': str(row.detection_id),
            'image_id': str(row.image_id),
            'path': row.path,
            'filename': row.filename,
            'confidence': float(row.confidence),
            'bbox': row.bbox,
            'bbox_area': bbox_area,
            'classification': 'doe',
            'timestamp': row.timestamp.isoformat(),
            'location_id': str(row.location_id) if row.location_id else None
        })

    print(f"[OK] Selected {len(selected)} does")
    print(f"    Avg confidence: {sum(s['confidence'] for s in selected) / len(selected):.3f}")

    return selected


def select_mixed(db) -> List[Dict]:
    """
    Select 25 mixed/challenging images.

    Includes:
    - Fawns
    - Medium confidence (challenging cases)
    - Various conditions
    """
    print(f"\n[INFO] Selecting {TARGET_MIXED} mixed/challenging images...")

    # Get fawns
    fawns = db.query(
        Detection.id.label('detection_id'),
        Detection.confidence,
        Detection.bbox,
        Detection.classification,
        Image.id.label('image_id'),
        Image.path,
        Image.filename,
        Image.timestamp,
        Image.location_id
    ).join(
        Image, Detection.image_id == Image.id
    ).filter(
        Detection.classification == 'fawn',
        Detection.confidence >= 0.50,  # Lower threshold for fawns
        Detection.bbox.isnot(None),
        Image.path.isnot(None)
    ).order_by(
        Detection.confidence.desc()
    ).limit(10).all()

    # Get challenging bucks/does (medium confidence)
    challenging = db.query(
        Detection.id.label('detection_id'),
        Detection.confidence,
        Detection.bbox,
        Detection.classification,
        Image.id.label('image_id'),
        Image.path,
        Image.filename,
        Image.timestamp,
        Image.location_id
    ).join(
        Image, Detection.image_id == Image.id
    ).filter(
        Detection.classification.in_(['buck', 'doe']),
        Detection.confidence >= 0.55,
        Detection.confidence < 0.65,  # Medium confidence range
        Detection.bbox.isnot(None),
        Image.path.isnot(None)
    ).order_by(
        Detection.confidence.desc()
    ).limit(15).all()

    selected = []
    for row in list(fawns) + list(challenging):
        if len(selected) >= TARGET_MIXED:
            break

        bbox_area = calculate_bbox_area(row.bbox)

        if bbox_area < MIN_BBOX_SIZE // 2:  # Lower threshold for mixed
            continue

        selected.append({
            'detection_id': str(row.detection_id),
            'image_id': str(row.image_id),
            'path': row.path,
            'filename': row.filename,
            'confidence': float(row.confidence),
            'bbox': row.bbox,
            'bbox_area': bbox_area,
            'classification': row.classification,
            'timestamp': row.timestamp.isoformat(),
            'location_id': str(row.location_id) if row.location_id else None
        })

    print(f"[OK] Selected {len(selected)} mixed images")
    fawn_count = sum(1 for s in selected if s['classification'] == 'fawn')
    print(f"    Fawns: {fawn_count}, Challenging: {len(selected) - fawn_count}")

    return selected


def copy_images(selections: List[Dict], category: str):
    """Copy selected images to output directory."""
    print(f"\n[INFO] Copying {len(selections)} {category} images...")

    output_cat_dir = OUTPUT_DIR / category
    copied = 0

    for item in selections:
        src_path = item['path']

        # Create unique filename with detection ID
        dest_filename = f"{item['detection_id']}_{Path(src_path).name}"
        dest_path = output_cat_dir / dest_filename

        try:
            shutil.copy2(src_path, dest_path)
            item['annotation_path'] = str(dest_path)
            copied += 1
        except Exception as e:
            print(f"  [WARN] Failed to copy {src_path}: {e}")
            continue

    print(f"[OK] Copied {copied}/{len(selections)} images")


def save_metadata(bucks, does, mixed):
    """Save metadata JSON for all selected images."""
    print("\n[INFO] Saving metadata...")

    metadata = {
        'total_images': len(bucks) + len(does) + len(mixed),
        'bucks': bucks,
        'does': does,
        'mixed': mixed,
        'statistics': {
            'buck_count': len(bucks),
            'doe_count': len(does),
            'mixed_count': len(mixed),
            'avg_confidence': {
                'bucks': sum(b['confidence'] for b in bucks) / len(bucks) if bucks else 0,
                'does': sum(d['confidence'] for d in does) / len(does) if does else 0,
                'mixed': sum(m['confidence'] for m in mixed) / len(mixed) if mixed else 0
            }
        }
    }

    metadata_path = OUTPUT_DIR / "metadata" / "sample_selection.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"[OK] Metadata saved: {metadata_path}")

    # Create summary file
    summary_path = OUTPUT_DIR / "SELECTION_SUMMARY.txt"
    summary = f"""Antler Detection Annotation - Sample Selection

Total Images: {metadata['total_images']}
- Bucks: {len(bucks)}
- Does: {len(does)}
- Mixed: {len(mixed)}

Quality Metrics:
- Min Confidence: {MIN_CONFIDENCE}
- Min Bbox Size: {MIN_BBOX_SIZE} px
- Avg Buck Confidence: {metadata['statistics']['avg_confidence']['bucks']:.3f}
- Avg Doe Confidence: {metadata['statistics']['avg_confidence']['does']:.3f}

Output Directory: {OUTPUT_DIR}

Next Steps:
1. Set up Label Studio annotation tool
2. Import images from {OUTPUT_DIR}/bucks, does, mixed
3. Annotate antler points (bucks) and body markings (all)
4. Export annotations in YOLOv8-pose format
5. Train initial antler detection model

Schema: docs/ANTLER_DETECTION_ANNOTATION_SCHEMA.md
"""

    summary_path.write_text(summary)
    print(f"[OK] Summary saved: {summary_path}")


def main():
    """Main selection workflow."""
    print("=" * 70)
    print("Antler Detection - Sample Image Selection")
    print("=" * 70)

    setup_directories()

    # Connect to database
    print("\n[INFO] Connecting to database...")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Select images
        bucks = select_bucks(db)
        does = select_does(db)
        mixed = select_mixed(db)

        total = len(bucks) + len(does) + len(mixed)
        print(f"\n[OK] Selected {total} total images")

        # Copy images
        copy_images(bucks, "bucks")
        copy_images(does, "does")
        copy_images(mixed, "mixed")

        # Save metadata
        save_metadata(bucks, does, mixed)

        # Summary
        print("\n" + "=" * 70)
        print("SELECTION COMPLETE")
        print("=" * 70)
        print(f"Output: {OUTPUT_DIR}")
        print(f"Bucks: {len(bucks)}")
        print(f"Does: {len(does)}")
        print(f"Mixed: {len(mixed)}")
        print(f"Total: {total}")
        print("\nNext: Set up Label Studio and begin annotation")

        return 0

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
