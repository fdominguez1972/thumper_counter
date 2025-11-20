#!/usr/bin/env python3
"""
TURBO MODE: Classification Audit - All-in-one workflow
Downloads images, saves metadata, ready for Claude Code vision analysis
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Configuration
BATCH_SIZE = 20
API_URL = "http://localhost:8001"

def get_batch_data(min_conf: float, limit: int, batch_num: int, offset: int = 0) -> List[Dict]:
    """Get batch data from database by confidence range"""
    # Use temp file to avoid shell escaping issues
    import tempfile
    import os

    query = f"""SELECT d.id, i.filename, d.classification, ROUND(d.confidence::numeric, 4), i.id
FROM detections d
JOIN images i ON d.image_id = i.id
WHERE d.classification IN ('buck', 'doe', 'fawn')
  AND d.confidence >= {min_conf} AND d.confidence < 0.60
ORDER BY d.confidence ASC
LIMIT {limit} OFFSET {offset};"""

    # Save query to temp file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as f:
        f.write(query)
        query_file = f.name

    try:
        cmd = f'docker-compose exec -T db psql -U deertrack deer_tracking -f - -t -A < "{query_file}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    finally:
        os.unlink(query_file)

    # Debug
    if not result.stdout.strip():
        print(f"[DEBUG] No output from query. stderr: {result.stderr[:200]}")
        return []

    lines = [l.strip() for l in result.stdout.split('\n') if l.strip() and '|' in l]
    print(f"[DEBUG] Found {len(lines)} lines with pipes")

    detections = []
    img_num = (batch_num - 1) * BATCH_SIZE + 1
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

def download_images(detections: List[Dict], output_dir: Path) -> Dict[str, Path]:
    """Download all images for batch"""
    output_dir.mkdir(exist_ok=True)
    image_paths = {}

    print(f"\n[DOWNLOAD] Getting {len(detections)} images...")
    for det in detections:
        image_path = output_dir / f"{det['num']:03d}_{det['filename']}"
        cmd = f'curl -s {API_URL}/api/static/images/{det["image_id"]} -o "{image_path}"'
        result = subprocess.run(cmd, shell=True)

        if result.returncode == 0 and image_path.exists():
            image_paths[det['detection_id']] = image_path
        else:
            print(f"  [WARN] Failed: {det['filename']}")

    print(f"[OK] Downloaded {len(image_paths)}/{len(detections)} images")
    return image_paths

def save_metadata(batch_num: int, detections: List[Dict], image_paths: Dict[str, Path]):
    """Save batch metadata for Claude Code"""
    metadata_file = Path(f"batch_{batch_num}_metadata.txt")

    content = f"""BATCH {batch_num} METADATA
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Images: {len(detections)}
Downloaded: {len(image_paths)}

IMAGES TO REVIEW:
"""

    for det in detections:
        image_path = image_paths.get(det['detection_id'], 'MISSING')
        content += f"\n{det['num']:03d}|{det['detection_id']}|{det['filename']}|{det['db_class']}|{det['confidence']:.4f}|{image_path}"

    metadata_file.write_text(content)
    print(f"[OK] Metadata: {metadata_file}")
    return metadata_file

def main():
    """Turbo workflow - download everything, ready for Claude Code"""
    import sys

    # Batch confidence ranges (batches 1-5 are hardcoded, rest are sequential)
    batch_ranges = {
        1: 0.50,      # Batch 1
        2: 0.5009,    # Batch 2
        3: 0.5023,    # Batch 3
        4: 0.5033,    # Batch 4
        5: 0.5045,    # Batch 5
    }

    batch_num = int(sys.argv[1]) if len(sys.argv) > 1 else 4

    # For batch 6+, use sequential querying (get next 20 after batch 5's max)
    if batch_num >= 6:
        # Query by skipping previous batches
        min_conf = 0.50  # Start from beginning
        offset = (batch_num - 1) * BATCH_SIZE  # Skip previous batches
    else:
        min_conf = batch_ranges.get(batch_num, 0.50)
        offset = 0

    print("=" * 70)
    print(f"TURBO AUDIT - BATCH {batch_num}")
    print("=" * 70)

    # Step 1: Get detections
    print(f"\n[1/3] Fetching detections (confidence >= {min_conf})...")
    detections = get_batch_data(min_conf, BATCH_SIZE, batch_num)

    if not detections:
        print(f"[ERROR] No detections found")
        return

    conf_range = f"{detections[0]['confidence']:.4f} - {detections[-1]['confidence']:.4f}"
    print(f"[OK] Found {len(detections)} detections (confidence: {conf_range})")

    # Step 2: Download images
    print(f"\n[2/3] Downloading images...")
    output_dir = Path(f"audit_batch_{batch_num}_images")
    image_paths = download_images(detections, output_dir)

    # Step 3: Save metadata
    print(f"\n[3/3] Saving metadata...")
    metadata_file = save_metadata(batch_num, detections, image_paths)

    print(f"\n{'=' * 70}")
    print(f"READY FOR CLAUDE CODE REVIEW!")
    print(f"{'=' * 70}")
    print(f"Images: {output_dir}/")
    print(f"Metadata: {metadata_file}")
    print(f"\nNext: Ask Claude Code to review images and save results")
    print(f"{'=' * 70}")

if __name__ == "__main__":
    main()
