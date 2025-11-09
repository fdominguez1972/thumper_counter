#!/usr/bin/env python3
"""
Verify rut season images exist on disk, queue them, and clean up missing records.
"""

import os
import sys
sys.path.insert(0, '/app')

import requests
from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://deertrack:Hopkins2019@db:5432/deer_tracking'
API_URL = 'http://backend:8000'

print("=" * 60)
print("Rut Season Image Verification & Cleanup")
print("=" * 60)

engine = create_engine(DATABASE_URL)

# Query for pending rut season images
query = text("""
    SELECT id, path, filename
    FROM images
    WHERE EXTRACT(MONTH FROM timestamp) IN (9, 10, 11, 12, 1)
      AND processing_status = 'pending'
    ORDER BY timestamp
""")

print("\n[INFO] Querying database for rut season images (Sept-Jan)...")

with engine.connect() as conn:
    result = conn.execute(query)
    images = [{'id': str(row.id), 'path': row.path, 'filename': row.filename} for row in result]

total = len(images)
print(f"[INFO] Found {total} pending rut season images in database\n")

if total == 0:
    print("[INFO] No rut season images pending!")
    sys.exit(0)

# Verify which images exist on disk
print("[INFO] Verifying files on disk...")
existing = []
missing = []

for img in images:
    # The path in DB is like /mnt/images/Location/filename.jpg
    if os.path.exists(img['path']):
        existing.append(img)
    else:
        missing.append(img)

print(f"[OK] Files found: {len(existing)}")
print(f"[WARN] Files missing: {len(missing)}\n")

# Queue existing images
if existing:
    print(f"[INFO] Queueing {len(existing)} images that exist on disk...")

    batch_size = 1000
    image_ids = [img['id'] for img in existing]
    batches = [image_ids[i:i+batch_size] for i in range(0, len(image_ids), batch_size)]

    queued_total = 0
    for i, batch in enumerate(batches, 1):
        print(f"  Batch {i}/{len(batches)} ({len(batch)} images)...", end=" ", flush=True)

        try:
            response = requests.post(
                f'{API_URL}/api/processing/batch',
                json={'image_ids': batch},
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                queued = data.get('queued_count', 0)
                queued_total += queued
                print(f"[OK] Queued {queued}")
            else:
                print(f"[FAIL] HTTP {response.status_code}")

        except Exception as e:
            print(f"[FAIL] {e}")

    print(f"\n[SUCCESS] Queued {queued_total} rut season images!\n")

# Clean up missing images from database
if missing:
    print(f"[INFO] Cleaning up {len(missing)} missing image records from database...")

    delete_query = text("""
        DELETE FROM images
        WHERE id = ANY(:image_ids)
    """)

    missing_ids = [img['id'] for img in missing]

    with engine.begin() as conn:
        result = conn.execute(delete_query, {'image_ids': missing_ids})
        deleted = result.rowcount
        print(f"[OK] Deleted {deleted} records\n")

    # Show some examples of what was deleted
    print("[INFO] Examples of deleted files (first 10):")
    for img in missing[:10]:
        print(f"  - {img['filename']}")

    if len(missing) > 10:
        print(f"  ... and {len(missing) - 10} more\n")
else:
    print("[INFO] No missing files to clean up\n")

print("[DONE] Verification and cleanup complete!")
print(f"\nSummary:")
print(f"  Rut season images found in DB: {total}")
print(f"  Files existing on disk: {len(existing)}")
print(f"  Files missing (deleted): {len(missing)}")
print(f"  Images queued for processing: {queued_total if existing else 0}\n")
