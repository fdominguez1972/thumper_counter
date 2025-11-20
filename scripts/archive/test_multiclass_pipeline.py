#!/usr/bin/env python3
"""
Test Multi-Class Detection + Classification Pipeline
Sprint 4: Verify sex/age classification is working correctly
"""
import sys
import requests
import time
from pathlib import Path

# API configuration
API_URL = "http://localhost:8001"
LOCATION_NAME = "Sanctuary"

# Sample images for testing (from Hopkins Ranch dataset)
SAMPLE_IMAGES = [
    "/mnt/i/Hopkins_Ranch_Trail_Cam_Pics/Sanctuary/*.jpg"
]

print("="*70)
print("MULTI-CLASS DETECTION + CLASSIFICATION TEST")
print("="*70)
print(f"API: {API_URL}")
print(f"Location: {LOCATION_NAME}")
print("="*70)
print()

# Step 1: Process a small batch of images
print("[INFO] Processing sample images...")
print()

# Get unprocessed images from database
response = requests.get(
    f"{API_URL}/api/images",
    params={
        "status": "pending",
        "page_size": 10
    }
)

if response.status_code != 200:
    print(f"[FAIL] Failed to get images: {response.text}")
    sys.exit(1)

images = response.json()["images"]
total = response.json()["total"]

if not images:
    print("[WARN] No pending images found. All images already processed.")
    print()
    print("[INFO] Fetching recently completed images instead...")

    # Get recently completed images
    response = requests.get(
        f"{API_URL}/api/images",
        params={
            "status": "completed",
            "page_size": 10
        }
    )

    if response.status_code != 200:
        print(f"[FAIL] Failed to get completed images: {response.text}")
        sys.exit(1)

    images = response.json()["images"]
    total = response.json()["total"]

print(f"[OK] Found {len(images)} images to analyze (total: {total})")
print()

# Step 2: Check detections for classification data
print("[INFO] Analyzing detections for sex/age classification...")
print()

classification_counts = {
    "doe": 0,
    "fawn": 0,
    "mature": 0,
    "mid": 0,
    "young": 0,
    "unknown": 0
}

total_detections = 0
images_with_deer = 0

for img in images[:10]:  # Analyze first 10 images
    image_id = img["id"]
    filename = img["filename"]

    # Get detections for this image
    response = requests.get(f"{API_URL}/api/images/{image_id}")

    if response.status_code != 200:
        print(f"[WARN] Failed to get image details: {image_id}")
        continue

    image_data = response.json()
    detections = image_data.get("detections", [])

    if detections:
        images_with_deer += 1
        total_detections += len(detections)

        print(f"[OK] {filename}: {len(detections)} deer detected")

        for det in detections:
            classification = det.get("classification", "unknown")
            confidence = det.get("confidence", 0.0)

            # Count classifications
            classification_counts[classification] = classification_counts.get(classification, 0) + 1

            # Print detection details
            bbox = det.get("bbox", {})
            print(f"     - {classification} (conf: {confidence:.2f}, bbox: {bbox.get('width')}x{bbox.get('height')})")
    else:
        print(f"[INFO] {filename}: No deer detected")

print()
print("="*70)
print("CLASSIFICATION RESULTS")
print("="*70)
print(f"Images analyzed: {len(images[:10])}")
print(f"Images with deer: {images_with_deer}")
print(f"Total deer detections: {total_detections}")
print()

print("Sex/Age Distribution:")
print(f"  doe (female):   {classification_counts['doe']}")
print(f"  fawn (unknown): {classification_counts['fawn']}")
print(f"  mature (male):  {classification_counts['mature']}")
print(f"  mid (male):     {classification_counts['mid']}")
print(f"  young (male):   {classification_counts['young']}")
print(f"  unknown:        {classification_counts['unknown']}")
print()

# Calculate sex ratios
total_classified = sum(classification_counts.values())
bucks = classification_counts['mature'] + classification_counts['mid'] + classification_counts['young']
does = classification_counts['doe']
fawns = classification_counts['fawn']

if total_classified > 0:
    print("Sex Ratios:")
    print(f"  Bucks: {bucks} ({100 * bucks / total_classified:.1f}%)")
    print(f"  Does:  {does} ({100 * does / total_classified:.1f}%)")
    print(f"  Fawns: {fawns} ({100 * fawns / total_classified:.1f}%)")

print()
print("="*70)

if classification_counts['unknown'] > 0:
    print("[WARN] Some detections still have 'unknown' classification")
    print("       This indicates the old model may still be in use")
    print("       or images were processed before Sprint 4 update")
else:
    print("[OK] All detections have sex/age classifications!")
    print("[OK] Multi-class detection pipeline is working correctly")

print("="*70)
