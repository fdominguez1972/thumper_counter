#!/usr/bin/env python3
"""Queue September-November (rut season) images for priority processing."""

import sys
sys.path.insert(0, '/app')

import requests
from sqlalchemy import create_engine, text

DATABASE_URL = 'postgresql://deertrack:Hopkins2019@db:5432/deer_tracking'
API_URL = 'http://backend:8000'

print("=" * 60)
print("Queueing Rut Season Images (Sept-Nov)")
print("=" * 60)

engine = create_engine(DATABASE_URL)

query = text("""
    SELECT id
    FROM images
    WHERE EXTRACT(MONTH FROM timestamp) IN (9, 10, 11)
      AND processing_status = 'pending'
    ORDER BY timestamp
""")

with engine.connect() as conn:
    result = conn.execute(query)
    image_ids = [str(row.id) for row in result]

total = len(image_ids)
print(f"\n[INFO] Found {total} rut season images to process\n")

if total == 0:
    print("[INFO] No rut season images pending!")
    sys.exit(0)

batch_size = 1000
batches = [image_ids[i:i+batch_size] for i in range(0, len(image_ids), batch_size)]

print(f"[INFO] Queueing {len(batches)} batches...\n")

for i, batch in enumerate(batches, 1):
    print(f"Batch {i}/{len(batches)} ({len(batch)} images)...", end=" ", flush=True)
    
    try:
        response = requests.post(
            f'{API_URL}/api/processing/batch',
            json={'image_ids': batch},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Queued {data.get('queued_count', 0)}")
        else:
            print(f"[FAIL] HTTP {response.status_code}")
    
    except Exception as e:
        print(f"[FAIL] {e}")

print(f"\n[SUCCESS] Queued {total} rut season images!\n")
