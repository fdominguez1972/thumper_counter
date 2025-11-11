#!/usr/bin/env python3
"""
YOLOv8 Multi-Class Model Evaluation
Sprint 4: Comprehensive test set evaluation
"""
import sys
from pathlib import Path
from ultralytics import YOLO
import torch

# Configuration (container paths)
model_path = "/app/src/models/runs/deer_multiclass/weights/best.pt"
data_yaml = "/app/src/models/training_data/deer_multiclass.yaml"
output_dir = "/app/src/models/runs/deer_multiclass/evaluation"

print("="*70)
print("YOLOV8 MULTI-CLASS MODEL EVALUATION")
print("="*70)
print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"Model: {model_path}")
print(f"Data: {data_yaml}")
print(f"Output: {output_dir}")
print("="*70)
print()

# Load trained model
print("[INFO] Loading trained model...")
model = YOLO(model_path)

print("[OK] Model loaded - running evaluation on test set...")
print()

# Evaluate on test set
try:
    metrics = model.val(
        data=data_yaml,
        split='test',  # Use test set (347 images)
        imgsz=640,
        device=0,
        verbose=True,
        plots=True,
        save_json=True,
        conf=0.7,  # Match detection threshold
        iou=0.45,  # Match NMS threshold
        project=output_dir,
        name='test_results',
        exist_ok=True,
    )

    print()
    print("="*70)
    print("[OK] EVALUATION COMPLETE!")
    print("="*70)

    # Print detailed metrics
    print()
    print("OVERALL METRICS:")
    print(f"  mAP50:     {metrics.box.map50:.4f}")
    print(f"  mAP50-95:  {metrics.box.map:.4f}")
    print(f"  Precision: {metrics.box.mp:.4f}")
    print(f"  Recall:    {metrics.box.mr:.4f}")
    print()

    print("DEER CLASS METRICS (Sex/Age Classification):")
    print(f"  doe (female):  mAP50={metrics.box.maps[3]:.4f}")
    print(f"  fawn (unknown): mAP50={metrics.box.maps[4]:.4f}")
    print(f"  mature (male):  mAP50={metrics.box.maps[5]:.4f}")
    print(f"  mid (male):     mAP50={metrics.box.maps[6]:.4f}")
    print(f"  young (male):   mAP50={metrics.box.maps[10]:.4f}")
    print()

    print("OUTPUTS:")
    print(f"  Confusion matrix: {output_dir}/test_results/confusion_matrix.png")
    print(f"  PR curves: {output_dir}/test_results/PR_curve.png")
    print(f"  Predictions: {output_dir}/test_results/val_batch*_pred.jpg")
    print("="*70)

except Exception as e:
    print()
    print(f"[FAIL] Evaluation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
