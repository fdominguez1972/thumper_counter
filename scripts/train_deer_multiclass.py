#!/usr/bin/env python3
"""
YOLOv8 Multi-Class Deer Training
Sprint 4: Sex/Age Classification
"""
import sys
from pathlib import Path
from ultralytics import YOLO
import torch

# Configuration (container paths)
data_yaml = "/app/src/models/training_data/deer_multiclass.yaml"
output_dir = "/app/src/models/runs"

print("="*70)
print("YOLOV8 MULTI-CLASS DEER TRAINING")
print("="*70)
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"Data: {data_yaml}")
print(f"Epochs: 200")
print(f"Batch: 32")
print(f"Patience: 20 (early stopping)")
print(f"Output: {output_dir}")
print("="*70)
print()

# Load model
print("[INFO] Loading YOLOv8n pretrained model...")
model = YOLO('yolov8n.pt')

print("[OK] Model loaded - starting training...")
print("[INFO] This will take 3-5 hours")
print("[INFO] Progress will be displayed below")
print()

# Train
try:
    results = model.train(
        data=data_yaml,
        epochs=200,
        batch=32,
        imgsz=640,
        device=0,
        patience=20,
        project=output_dir,
        name='deer_multiclass',
        exist_ok=True,
        verbose=True,
        amp=True,
        plots=True,
        save=True,
        save_period=10,
    )

    print()
    print("="*70)
    print("[OK] TRAINING COMPLETE!")
    print(f"Best model: {output_dir}/deer_multiclass/weights/best.pt")
    print(f"Last model: {output_dir}/deer_multiclass/weights/last.pt")
    print("="*70)

except KeyboardInterrupt:
    print()
    print("[WARN] Training interrupted - checkpoint saved")
    sys.exit(0)

except Exception as e:
    print()
    print(f"[FAIL] Training failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
