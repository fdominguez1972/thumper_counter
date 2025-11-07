#!/usr/bin/env python3
"""
Test Re-Identification Pipeline
Sprint 5: Verify ResNet50 feature extraction and matching
"""
import sys
import requests
import time
from pathlib import Path

# API configuration
API_URL = "http://localhost:8001"

print("="*70)
print("RE-IDENTIFICATION PIPELINE TEST")
print("="*70)
print(f"API: {API_URL}")
print("="*70)
print()

# Step 1: Get some recent detections with deer
print("[INFO] Finding detections to test re-ID...")
print()

response = requests.get(
    f"{API_URL}/api/images",
    params={
        "status": "completed",
        "page_size": 10
    }
)

if response.status_code != 200:
    print(f"[FAIL] Failed to get images: {response.text}")
    sys.exit(1)

images = response.json()["images"]

# Filter to images with detections
images_with_deer = [img for img in images if img.get("detections", [])]

if not images_with_deer:
    print("[WARN] No images with detections found")
    print("[INFO] Try processing some images first with batch processing")
    sys.exit(0)

print(f"[OK] Found {len(images_with_deer)} images with deer detections")
print()

# Step 2: Get detection IDs to test
test_detections = []
for img in images_with_deer[:5]:  # Test first 5 images
    response = requests.get(f"{API_URL}/api/images/{img['id']}")
    if response.status_code == 200:
        image_data = response.json()
        detections = image_data.get("detections", [])
        for det in detections:
            test_detections.append({
                "detection_id": det["id"],
                "image": img["filename"],
                "classification": det.get("classification", "unknown"),
                "confidence": det.get("confidence", 0.0)
            })

if not test_detections:
    print("[WARN] No valid detections found")
    sys.exit(0)

print(f"[OK] Found {len(test_detections)} detections to test")
print()

# Step 3: Queue re-ID tasks manually
print("[INFO] Queuing re-ID tasks...")
print()

from celery import Celery

# Connect to Celery
celery_app = Celery(
    'test',
    broker='redis://localhost:6380/0',
    backend='redis://localhost:6380/0'
)

# Queue re-ID tasks
task_ids = []
for det in test_detections[:3]:  # Test first 3 detections
    result = celery_app.send_task(
        'worker.tasks.reidentification.reidentify_deer_task',
        args=[det['detection_id']],
        queue='ml_processing'
    )
    task_ids.append(result.id)
    print(f"[OK] Queued re-ID for detection {det['detection_id'][:8]}... "
          f"(image: {det['image']}, class: {det['classification']})")

print()
print(f"[OK] Queued {len(task_ids)} re-ID tasks")
print()

# Step 4: Wait for results
print("[INFO] Waiting for re-ID tasks to complete...")
print()

time.sleep(5)  # Give worker time to process

# Step 5: Check results
print("[INFO] Checking results...")
print()

success_count = 0
match_count = 0
new_profile_count = 0

for i, task_id in enumerate(task_ids):
    result = celery_app.AsyncResult(task_id)

    if result.ready():
        task_result = result.result
        status = task_result.get("status", "unknown")

        if status == "matched":
            success_count += 1
            match_count += 1
            deer_id = task_result.get("deer_id", "unknown")
            similarity = task_result.get("similarity", 0.0)
            print(f"[OK] Task {i+1}: MATCHED to deer {deer_id[:8]}... "
                  f"(similarity: {similarity:.3f})")

        elif status == "new_profile":
            success_count += 1
            new_profile_count += 1
            deer_id = task_result.get("deer_id", "unknown")
            print(f"[OK] Task {i+1}: NEW PROFILE created (deer: {deer_id[:8]}...)")

        else:
            print(f"[WARN] Task {i+1}: {status}")
    else:
        print(f"[WARN] Task {i+1}: Still processing...")

print()
print("="*70)
print("RE-ID TEST RESULTS")
print("="*70)
print(f"Total tasks: {len(task_ids)}")
print(f"Successful: {success_count}")
print(f"Matched to existing deer: {match_count}")
print(f"New profiles created: {new_profile_count}")
print()

if success_count > 0:
    print("[OK] Re-identification pipeline is working!")
    print()
    print("Next steps:")
    print("1. Integrate re-ID into detection pipeline")
    print("2. Process full dataset with re-ID")
    print("3. Analyze deer profile creation and matching")
else:
    print("[WARN] No successful re-ID tasks")
    print("Check worker logs for errors:")
    print("  docker-compose logs worker | grep reidentification")

print("="*70)
