#!/usr/bin/env python3
"""
Direct Filesystem Audit - No downloading, access images directly
Much faster - just query DB and read from filesystem
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Configuration
BATCH_SIZE = 20
IMAGE_BASE_PATH = Path("I:/Hopkins_Ranch_Trail_Cam_Pics")

# Subdirectory mappings (camera locations)
SUBDIRS = [
    "270_JASON",
    "Camphouse",
    "HAYFIELD",
    "Jason1",
    "Sanctuary2",
    "SANCTUARY",
    "TinMan"
]

def find_image_file(filename: str) -> Path:
    """Find image file in subdirectories"""
    for subdir in SUBDIRS:
        filepath = IMAGE_BASE_PATH / subdir / filename
        if filepath.exists():
            return filepath

    # If not found in known subdirs, search
    for filepath in IMAGE_BASE_PATH.rglob(filename):
        return filepath

    return None

def get_batch_data(batch_num: int, batch_size: int) -> List[Dict]:
    """Get batch data from database using OFFSET"""
    offset = (batch_num - 1) * batch_size

    import tempfile
    import os

    query = f"""SELECT d.id, i.filename, d.classification, ROUND(d.confidence::numeric, 4), i.id
FROM detections d
JOIN images i ON d.image_id = i.id
WHERE d.classification IN ('buck', 'doe', 'fawn')
  AND d.confidence >= 0.50 AND d.confidence < 0.60
ORDER BY d.confidence ASC
LIMIT {batch_size} OFFSET {offset};"""

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as f:
        f.write(query)
        query_file = f.name

    try:
        cmd = f'docker-compose exec -T db psql -U deertrack deer_tracking -f - -t -A < "{query_file}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    finally:
        os.unlink(query_file)

    lines = [l.strip() for l in result.stdout.split('\n') if l.strip() and '|' in l]

    detections = []
    img_num = (batch_num - 1) * batch_size + 1
    for line in lines:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 5:
            detections.append({
                'num': img_num,
                'detection_id': parts[0],
                'filename': parts[1],
                'db_class': parts[2],
                'confidence': float(parts[3]),
                'image_id': parts[4]
            })
            img_num += 1

    return detections

def save_batch_metadata(batch_num: int, detections: List[Dict]):
    """Save metadata for Claude Code"""
    metadata_file = Path(f"batch_{batch_num}_metadata.txt")

    content = f"""BATCH {batch_num} METADATA (DIRECT FILESYSTEM ACCESS)
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Images: {len(detections)}
Method: Direct filesystem access (no download needed)

IMAGES TO REVIEW:
"""

    for det in detections:
        filepath = find_image_file(det['filename'])
        if filepath:
            content += f"\n{det['num']:03d}|{det['detection_id']}|{det['filename']}|{det['db_class']}|{det['confidence']:.4f}|{filepath}"
        else:
            content += f"\n{det['num']:03d}|{det['detection_id']}|{det['filename']}|{det['db_class']}|{det['confidence']:.4f}|NOT_FOUND"

    metadata_file.write_text(content)
    return metadata_file

def main():
    import sys

    batch_num = int(sys.argv[1]) if len(sys.argv) > 1 else 6

    print("=" * 70)
    print(f"DIRECT FILESYSTEM AUDIT - BATCH {batch_num}")
    print("=" * 70)
    print(f"Method: Reading images directly from {IMAGE_BASE_PATH}")
    print(f"No download needed - instant access!")
    print("=" * 70)

    # Get detections
    print(f"\n[1/2] Fetching batch data...")
    detections = get_batch_data(batch_num, BATCH_SIZE)

    if not detections:
        print(f"[INFO] No detections found for batch {batch_num}")
        return

    print(f"[OK] Found {len(detections)} detections")
    print(f"  Confidence range: {detections[0]['confidence']:.4f} - {detections[-1]['confidence']:.4f}")

    # Verify images exist
    print(f"\n[2/2] Locating images on filesystem...")
    found = 0
    for det in detections:
        filepath = find_image_file(det['filename'])
        if filepath:
            found += 1

    print(f"[OK] Found {found}/{len(detections)} images on filesystem")

    # Save metadata
    metadata_file = save_batch_metadata(batch_num, detections)
    print(f"[OK] Metadata saved: {metadata_file}")

    print(f"\n{'='*70}")
    print(f"READY FOR CLAUDE CODE REVIEW!")
    print(f"{'='*70}")
    print(f"Images: Accessible directly from {IMAGE_BASE_PATH}")
    print(f"Metadata: {metadata_file}")
    print(f"Next: Claude Code will read images directly from filesystem")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
