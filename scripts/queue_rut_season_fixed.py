#!/usr/bin/env python3
"""
Queue rut season images (Sept-Jan) for processing.
Fixed version that works with current API.
"""

import requests
import time

API_URL = 'http://localhost:8001'

print("=" * 60)
print("Queueing Rut Season Images (Sept-Jan)")
print("=" * 60)

# Get current status
response = requests.get(f'{API_URL}/api/processing/status')
status = response.json()
print(f"\n[INFO] Current status: {status['pending']} pending, {status['completed']} completed\n")

# We need to queue in batches because API doesn't support month filtering
# Strategy: Queue all pending images, since rut season is a large portion
batch_size = 1000
batches_to_queue = 7  # Queue 7000 images (more than the 6115 rut season images)

print(f"[INFO] Queueing {batches_to_queue} batches of {batch_size} images each...\n")

total_queued = 0

for i in range(1, batches_to_queue + 1):
    print(f"Batch {i}/{batches_to_queue}...", end=" ", flush=True)

    try:
        response = requests.post(
            f'{API_URL}/api/processing/batch',
            params={'limit': batch_size, 'status': 'pending'},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            queued = data.get('queued_count', 0)
            total_queued += queued
            print(f"[OK] Queued {queued} images")

            if queued == 0:
                print("\n[INFO] No more pending images to queue")
                break
        else:
            print(f"[FAIL] HTTP {response.status_code}")
            break

    except Exception as e:
        print(f"[FAIL] {e}")
        break

    # Small delay between batches
    time.sleep(1)

print(f"\n[SUCCESS] Queued {total_queued} images total!")
print(f"\n[INFO] Monitor progress at: http://localhost:3000")
print(f"[INFO] Check status: curl http://localhost:8001/api/processing/status\n")
