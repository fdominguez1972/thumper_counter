#!/usr/bin/env python3
"""Debug new model to see what it's detecting."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultralytics import YOLO
import torch

# Models
OLD_MODEL = "src/models/yolov8n_deer.pt"
NEW_MODEL = "src/models/runs/deer_balanced_20251116/weights/best.pt"

# Test image (from database)
TEST_IMAGE = "/mnt/images/Sanctuary/SANCTUARY_01496.jpg"

print("="*80)
print("MODEL DEBUGGING - Single Image Test")
print("="*80)

device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"\nDevice: {device}")
print(f"Test Image: {TEST_IMAGE}")

# Test old model
print("\n" + "="*80)
print("OLD MODEL")
print("="*80)
old_model = YOLO(OLD_MODEL)

for conf_thresh in [0.30, 0.40, 0.50, 0.60]:
    results = old_model.predict(source=TEST_IMAGE, conf=conf_thresh, verbose=False)[0]
    print(f"\nConfidence Threshold: {conf_thresh}")
    print(f"  Detections: {len(results.boxes)}")

    if len(results.boxes) > 0:
        for i, box in enumerate(results.boxes[:3]):  # Show first 3
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            class_names = {0: 'buck', 1: 'doe', 2: 'fawn', 3: 'cattle', 4: 'pig', 5: 'raccoon'}
            print(f"    [{i+1}] Class: {class_names.get(cls, cls)}, Conf: {conf:.4f}")

# Test new model
print("\n" + "="*80)
print("NEW MODEL")
print("="*80)
new_model = YOLO(NEW_MODEL)

for conf_thresh in [0.10, 0.20, 0.30, 0.40, 0.50]:
    results = new_model.predict(source=TEST_IMAGE, conf=conf_thresh, verbose=False)[0]
    print(f"\nConfidence Threshold: {conf_thresh}")
    print(f"  Detections: {len(results.boxes)}")

    if len(results.boxes) > 0:
        for i, box in enumerate(results.boxes[:3]):  # Show first 3
            cls = int(box.cls[0])
            conf = float(box.conf[0])
            class_names = {0: 'buck', 1: 'doe', 2: 'fawn', 3: 'cattle', 4: 'pig', 5: 'raccoon'}
            print(f"    [{i+1}] Class: {class_names.get(cls, cls)}, Conf: {conf:.4f}")

print("\n" + "="*80)
print("DIAGNOSIS")
print("="*80)

if len(old_model.predict(source=TEST_IMAGE, conf=0.30, verbose=False)[0].boxes) == 0:
    print("\n[WARN] Old model also detects nothing at 0.30 threshold")
    print("  This image may not contain detectable objects")
else:
    new_detections = len(new_model.predict(source=TEST_IMAGE, conf=0.10, verbose=False)[0].boxes)
    if new_detections == 0:
        print("\n[FAIL] New model detects NOTHING even at 0.10 confidence")
        print("  Possible issues:")
        print("    - Model is broken/corrupted")
        print("    - Model trained on wrong image size")
        print("    - Model overfitted to training data")
        print("    - Class mapping mismatch")
    else:
        print(f"\n[INFO] New model detects {new_detections} objects at 0.10 threshold")
        print("  Model requires lower confidence threshold than old model")

print("\n" + "="*80 + "\n")
