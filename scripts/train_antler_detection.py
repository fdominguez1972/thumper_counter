#!/usr/bin/env python3
"""
YOLOv8-Pose Antler Detection Training
Phase 2B: Train model to detect antler keypoints
Date: November 16, 2025

Dataset: 73 annotated images from Label Studio
- 60 bucks with antler keypoints
- 35 does
- 4 fawns
- 16 keypoint labels per buck

Keypoints:
  Left antler: main_beam, brow_tine, g2, g3, g4, tip, bez_tine, royal_tine
  Right antler: main_beam, brow_tine, g2, g3, g4, tip, bez_tine, royal_tine
"""
import sys
from pathlib import Path
from ultralytics import YOLO
import torch
import yaml

# Configuration
DATA_YAML = "/app/src/models/training_data/antler_yolo_20251116/data.yaml"
OUTPUT_DIR = "/app/models/runs"
MODEL_NAME = "antler_detection_20251116"

print("="*70)
print("YOLOV8-POSE ANTLER DETECTION TRAINING")
print("Phase 2B: Antler Keypoint Detection")
print("="*70)
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"Data: {DATA_YAML}")
print(f"Output: {OUTPUT_DIR}/{MODEL_NAME}")
print("="*70)
print()

# Load data config
with open(DATA_YAML, 'r') as f:
    data_config = yaml.safe_load(f)
    print("Dataset configuration:")
    print(f"  Classes: {data_config['nc']}")
    print(f"  Keypoints: {data_config['kpt_shape'][0]}")
    print(f"  Train images: {data_config.get('train_images', 'N/A')}")
    print(f"  Val images: {data_config.get('val_images', 'N/A')}")

print()
print("[INFO] Training Strategy:")
print("  - Model: YOLOv8n-pose (lightweight for production)")
print("  - Keypoint detection: 16 antler points")
print("  - Epochs: 200 (early stopping patience=20)")
print("  - Batch: 8 (stable for keypoint training)")
print("  - Image size: 640x640")
print("  - OKS (Object Keypoint Similarity) metric")
print()

# Load pretrained YOLOv8n-pose model
print("[INFO] Loading YOLOv8n-pose pretrained model...")
model = YOLO('yolov8n-pose.pt')

print("[OK] Model loaded - starting training...")
print("[INFO] Estimated time: 2-3 hours (smaller dataset)")
print("[INFO] Progress will be displayed below")
print("[INFO] Press Ctrl+C to stop (checkpoint will be saved)")
print()

# Training hyperparameters for keypoint detection
try:
    results = model.train(
        # Data
        data=DATA_YAML,

        # Training parameters
        epochs=200,
        batch=8,            # Smaller batch for keypoint training
        imgsz=640,
        device=0,           # RTX 4080 Super

        # Optimization
        patience=20,        # Early stopping
        optimizer='AdamW',
        lr0=0.001,          # Learning rate
        lrf=0.01,           # Final LR

        # Augmentation (moderate for keypoints)
        hsv_h=0.01,         # Hue
        hsv_s=0.5,          # Saturation
        hsv_v=0.3,          # Value
        degrees=5.0,        # Rotation (less than detection - preserve keypoints)
        translate=0.05,     # Translation
        scale=0.3,          # Scaling
        shear=1.0,          # Shearing
        perspective=0.0,    # No perspective (distorts keypoints)
        flipud=0.0,         # No vertical flip
        fliplr=0.5,         # Horizontal flip (antlers are symmetric)
        mosaic=0.5,         # Moderate mosaic
        mixup=0.0,          # No mixup (confuses keypoints)

        # Loss weights
        box=7.5,            # Bounding box loss
        cls=0.5,            # Classification loss
        dfl=1.5,            # Distribution focal loss
        pose=12.0,          # Keypoint loss weight (IMPORTANT)
        kobj=2.0,           # Keypoint objectness

        # Output
        project=OUTPUT_DIR,
        name=MODEL_NAME,
        exist_ok=True,
        verbose=True,

        # Performance
        amp=True,           # Mixed precision
        plots=True,         # Generate plots
        save=True,
        save_period=20,     # Save every 20 epochs

        # Validation
        val=True,
    )

    print()
    print("="*70)
    print("[OK] TRAINING COMPLETE!")
    print()
    print(f"Best model: {OUTPUT_DIR}/{MODEL_NAME}/weights/best.pt")
    print(f"Last model: {OUTPUT_DIR}/{MODEL_NAME}/weights/last.pt")
    print()
    print("Metrics to check:")
    print("  - pose/OKS: Object Keypoint Similarity (higher is better)")
    print("  - box/mAP50: Bounding box detection accuracy")
    print("  - pose/mAP50: Keypoint detection accuracy")
    print()
    print("Next Steps:")
    print("1. Validate keypoint accuracy on test images")
    print("2. Visualize predictions: scripts/visualize_antler_predictions.py")
    print("3. If OKS >0.7: integrate into Re-ID pipeline")
    print("4. Expand dataset to 500+ images for production")
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
