#!/usr/bin/env python3
"""
YOLOv8 Multi-Class Deer Training
Sprint 4: Sex/Age Classification
"""
import sys
import argparse
from pathlib import Path
from ultralytics import YOLO
import torch

# Parse arguments
parser = argparse.ArgumentParser(description='Train YOLOv8 multiclass deer model')
parser.add_argument('--data', type=str, default='/app/src/models/training_data/deer_multiclass.yaml',
                    help='Path to data.yaml file')
parser.add_argument('--epochs', type=int, default=200,
                    help='Number of training epochs')
parser.add_argument('--batch', type=int, default=32,
                    help='Batch size')
parser.add_argument('--patience', type=int, default=20,
                    help='Early stopping patience (epochs)')
parser.add_argument('--name', type=str, default='deer_multiclass',
                    help='Experiment name')
parser.add_argument('--project', type=str, default='/app/src/models/runs',
                    help='Project directory')
args = parser.parse_args()

# Configuration
data_yaml = args.data
output_dir = args.project
epochs = args.epochs
batch = args.batch
patience = args.patience
name = args.name

print("="*70)
print("YOLOV8 MULTI-CLASS DEER TRAINING")
print("="*70)
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"Data: {data_yaml}")
print(f"Epochs: {epochs}")
print(f"Batch: {batch}")
print(f"Patience: {patience} (early stopping)")
print(f"Output: {output_dir}/{name}")
print("="*70)
print()

# Load model
print("[INFO] Loading YOLOv8n pretrained model...")
model = YOLO('yolov8n.pt')

print("[OK] Model loaded - starting training...")
print(f"[INFO] This will take approximately {epochs * 45 / 3600:.1f}-{epochs * 60 / 3600:.1f} hours")
print("[INFO] Progress will be displayed below")
print()

# Train
try:
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch,
        imgsz=640,
        device=0,
        patience=patience,
        project=output_dir,
        name=name,
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
    print(f"Best model: {output_dir}/{name}/weights/best.pt")
    print(f"Last model: {output_dir}/{name}/weights/last.pt")
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
