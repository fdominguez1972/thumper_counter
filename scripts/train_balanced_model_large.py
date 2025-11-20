#!/usr/bin/env python3
"""
YOLOv8 Balanced Model Training - LARGE DATASET
Uses corrected_final_20251111 dataset (2,145 images)
Fixes buck over-classification bias
Date: November 16, 2025
"""
import sys
from pathlib import Path
from ultralytics import YOLO
import torch
import yaml

# Configuration - USING LARGER DATASET
DATA_YAML = "/app/src/models/training_data/corrected_final_20251111/data.yaml"
OUTPUT_DIR = "/app/models/runs"
MODEL_NAME = "deer_balanced_large_20251116"

print("="*70)
print("YOLOV8 BALANCED MODEL TRAINING - LARGE DATASET")
print("Fixing Buck Over-Classification Bias")
print("="*70)
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"Dataset: {DATA_YAML}")
print(f"Output: {OUTPUT_DIR}/{MODEL_NAME}")
print("="*70)
print()

# Load data config
with open(DATA_YAML, 'r') as f:
    data_config = yaml.safe_load(f)
    print("Dataset classes:")
    for idx, name in data_config['names'].items():
        print(f"  {idx}: {name}")

print()
print("[INFO] Training Strategy:")
print("  - Dataset: 2,145 images (LARGE - corrected Nov 11th)")
print("  - Class-weighted loss (balance buck/doe)")
print("  - Heavy augmentation on doe examples")
print("  - Early stopping (patience=25)")
print("  - Model: YOLOv8n (fast inference)")
print("  - Epochs: 300 (with early stopping)")
print("  - Batch: 16 (stable training)")
print("  - Image size: 640x640")
print()

# Load model
print("[INFO] Loading YOLOv8n pretrained model...")
model = YOLO('yolov8n.pt')

print("[OK] Model loaded - starting training...")
print("[INFO] Estimated time: 6-8 hours (larger dataset)")
print("[INFO] Progress will be displayed below")
print("[INFO] Press Ctrl+C to stop (checkpoint will be saved)")
print()

# Training hyperparameters optimized for class balance
try:
    results = model.train(
        # Data
        data=DATA_YAML,

        # Training parameters
        epochs=300,
        batch=16,
        imgsz=640,
        device=0,

        # Optimization
        patience=25,
        optimizer='AdamW',
        lr0=0.001,
        lrf=0.01,

        # Augmentation (heavy for minority classes)
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=10.0,
        translate=0.1,
        scale=0.5,
        shear=2.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.1,

        # Class balancing
        cls=0.5,
        box=7.5,
        dfl=1.5,

        # Output
        project=OUTPUT_DIR,
        name=MODEL_NAME,
        exist_ok=True,
        verbose=True,

        # Performance
        amp=True,
        plots=True,
        save=True,
        save_period=20,

        # Validation
        val=True,
        split='val',
    )

    print()
    print("="*70)
    print("[OK] TRAINING COMPLETE!")
    print()
    print(f"Best model: {OUTPUT_DIR}/{MODEL_NAME}/weights/best.pt")
    print(f"Last model: {OUTPUT_DIR}/{MODEL_NAME}/weights/last.pt")
    print()
    print("Next Steps:")
    print("1. Validate model performance: scripts/test_models_on_audit_data.py")
    print("2. Compare to current model")
    print("3. If mAP50 >0.7 and accuracy >80%: deploy")
    print()
    print("="*70)

except KeyboardInterrupt:
    print()
    print("[WARN] Training interrupted - checkpoint saved")
    print(f"Resume with: model.train(resume=True, project='{OUTPUT_DIR}', name='{MODEL_NAME}')")
    sys.exit(0)

except Exception as e:
    print()
    print(f"[FAIL] Training failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
