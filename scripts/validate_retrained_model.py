#!/usr/bin/env python3
"""
Validate retrained YOLOv8 model against audit dataset.
Compares old vs new model performance on corrected detections.
"""

import sys
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultralytics import YOLO
import torch
from PIL import Image
import numpy as np

# Model paths
OLD_MODEL = "src/models/yolov8n_deer.pt"
NEW_MODEL = "src/models/runs/deer_balanced_20251116/weights/best.pt"

# Audit data location
AUDIT_DIR = Path("src/models/training_data/audit_corrected_20251116")

# Class mapping
CLASS_NAMES = {
    0: 'buck',
    1: 'doe',
    2: 'fawn',
    3: 'cattle',
    4: 'pig',
    5: 'raccoon'
}

CLASS_TO_ID = {v: k for k, v in CLASS_NAMES.items()}


def load_ground_truth(labels_dir: Path) -> Dict[str, List[Tuple[int, List[float]]]]:
    """Load ground truth labels from YOLO format files."""
    ground_truth = {}

    for label_file in labels_dir.glob("*.txt"):
        image_name = label_file.stem
        detections = []

        with open(label_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    class_id = int(parts[0])
                    bbox = [float(x) for x in parts[1:5]]
                    detections.append((class_id, bbox))

        ground_truth[image_name] = detections

    return ground_truth


def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """Calculate IoU between two YOLO format bboxes (x_center, y_center, w, h)."""
    # Convert to corner coordinates
    def to_corners(box):
        x, y, w, h = box
        x1 = x - w/2
        y1 = y - h/2
        x2 = x + w/2
        y2 = y + h/2
        return x1, y1, x2, y2

    x1_1, y1_1, x2_1, y2_1 = to_corners(box1)
    x1_2, y1_2, x2_2, y2_2 = to_corners(box2)

    # Calculate intersection
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)

    if x2_i < x1_i or y2_i < y1_i:
        return 0.0

    intersection = (x2_i - x1_i) * (y2_i - y1_i)

    # Calculate union
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def evaluate_model(model_path: str, images_dir: Path, ground_truth: Dict) -> Dict:
    """Evaluate a model on the audit dataset."""
    print(f"\nLoading model: {model_path}")
    model = YOLO(model_path)

    # Move to GPU if available
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")

    results = {
        'total_images': 0,
        'total_detections': 0,
        'correct_detections': 0,
        'by_class': defaultdict(lambda: {'total': 0, 'correct': 0, 'predictions': []}),
        'confidence_ranges': {
            '0.40-0.51': {'total': 0, 'correct': 0},
            '0.51-0.60': {'total': 0, 'correct': 0},
            '0.60-0.80': {'total': 0, 'correct': 0},
            '0.80-1.00': {'total': 0, 'correct': 0},
        },
        'confusion_matrix': defaultdict(lambda: defaultdict(int)),
        'detections': []
    }

    # Process each image
    for image_name, gt_detections in ground_truth.items():
        image_path = images_dir / f"{image_name}.jpg"

        if not image_path.exists():
            print(f"Warning: Image not found: {image_path}")
            continue

        results['total_images'] += 1

        # Run inference
        predictions = model.predict(
            source=str(image_path),
            conf=0.40,  # Match production threshold
            verbose=False
        )[0]

        # Match predictions to ground truth
        matched_gt = set()

        for pred_box in predictions.boxes:
            pred_class = int(pred_box.cls[0])
            pred_conf = float(pred_box.conf[0])

            # Convert xyxy to xywh normalized
            xyxy = pred_box.xyxy[0].cpu().numpy()
            img_h, img_w = predictions.orig_shape

            x_center = ((xyxy[0] + xyxy[2]) / 2) / img_w
            y_center = ((xyxy[1] + xyxy[3]) / 2) / img_h
            width = (xyxy[2] - xyxy[0]) / img_w
            height = (xyxy[3] - xyxy[1]) / img_h

            pred_bbox = [x_center, y_center, width, height]

            # Find best matching ground truth
            best_iou = 0.0
            best_gt_idx = -1

            for gt_idx, (gt_class, gt_bbox) in enumerate(gt_detections):
                if gt_idx in matched_gt:
                    continue

                iou = calculate_iou(pred_bbox, gt_bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = gt_idx

            # Consider it a match if IoU > 0.5
            if best_iou > 0.5 and best_gt_idx >= 0:
                matched_gt.add(best_gt_idx)
                gt_class = gt_detections[best_gt_idx][0]

                results['total_detections'] += 1
                is_correct = (pred_class == gt_class)

                if is_correct:
                    results['correct_detections'] += 1

                # Track by class
                gt_class_name = CLASS_NAMES[gt_class]
                pred_class_name = CLASS_NAMES[pred_class]

                results['by_class'][gt_class_name]['total'] += 1
                results['by_class'][gt_class_name]['predictions'].append({
                    'confidence': pred_conf,
                    'predicted': pred_class_name,
                    'correct': is_correct
                })

                if is_correct:
                    results['by_class'][gt_class_name]['correct'] += 1

                # Track by confidence range
                if pred_conf < 0.51:
                    conf_range = '0.40-0.51'
                elif pred_conf < 0.60:
                    conf_range = '0.51-0.60'
                elif pred_conf < 0.80:
                    conf_range = '0.60-0.80'
                else:
                    conf_range = '0.80-1.00'

                results['confidence_ranges'][conf_range]['total'] += 1
                if is_correct:
                    results['confidence_ranges'][conf_range]['correct'] += 1

                # Confusion matrix
                results['confusion_matrix'][gt_class_name][pred_class_name] += 1

                # Store detection details
                results['detections'].append({
                    'image': image_name,
                    'gt_class': gt_class_name,
                    'pred_class': pred_class_name,
                    'confidence': pred_conf,
                    'correct': is_correct,
                    'iou': best_iou
                })

    return results


def print_results(model_name: str, results: Dict):
    """Print formatted results."""
    print(f"\n{'='*80}")
    print(f"RESULTS: {model_name}")
    print(f"{'='*80}")

    # Overall accuracy
    total = results['total_detections']
    correct = results['correct_detections']
    accuracy = (correct / total * 100) if total > 0 else 0

    print(f"\n[OVERALL PERFORMANCE]")
    print(f"  Images Processed: {results['total_images']}")
    print(f"  Total Detections: {total}")
    print(f"  Correct: {correct}")
    print(f"  Incorrect: {total - correct}")
    print(f"  Accuracy: {accuracy:.2f}%")

    # By class
    print(f"\n[ACCURACY BY CLASS]")
    for class_name in ['buck', 'doe', 'fawn', 'cattle']:
        stats = results['by_class'].get(class_name, {'total': 0, 'correct': 0})
        if stats['total'] > 0:
            class_acc = (stats['correct'] / stats['total'] * 100)
            print(f"  {class_name:10s}: {stats['correct']:3d}/{stats['total']:3d} = {class_acc:6.2f}%")

    # By confidence range
    print(f"\n[ACCURACY BY CONFIDENCE RANGE]")
    for range_name in ['0.40-0.51', '0.51-0.60', '0.60-0.80', '0.80-1.00']:
        stats = results['confidence_ranges'][range_name]
        if stats['total'] > 0:
            range_acc = (stats['correct'] / stats['total'] * 100)
            print(f"  {range_name}: {stats['correct']:3d}/{stats['total']:3d} = {range_acc:6.2f}%")

    # Confusion matrix
    print(f"\n[CONFUSION MATRIX]")
    print(f"  {'Ground Truth':<12s} -> Predicted (counts)")
    for gt_class in ['buck', 'doe', 'fawn', 'cattle']:
        if gt_class in results['confusion_matrix']:
            predictions = results['confusion_matrix'][gt_class]
            pred_str = ', '.join([f"{pred}:{count}" for pred, count in predictions.items()])
            print(f"  {gt_class:<12s} -> {pred_str}")


def compare_models(old_results: Dict, new_results: Dict):
    """Print comparison between old and new model."""
    print(f"\n{'='*80}")
    print(f"MODEL COMPARISON")
    print(f"{'='*80}")

    # Overall improvement
    old_acc = (old_results['correct_detections'] / old_results['total_detections'] * 100)
    new_acc = (new_results['correct_detections'] / new_results['total_detections'] * 100)
    improvement = new_acc - old_acc

    print(f"\n[OVERALL ACCURACY]")
    print(f"  Old Model: {old_acc:.2f}%")
    print(f"  New Model: {new_acc:.2f}%")
    print(f"  Improvement: {improvement:+.2f}% {'[BETTER]' if improvement > 0 else '[WORSE]' if improvement < 0 else '[SAME]'}")

    # By class comparison
    print(f"\n[ACCURACY BY CLASS]")
    print(f"  {'Class':<12s} {'Old Model':>12s} {'New Model':>12s} {'Change':>12s}")
    print(f"  {'-'*12} {'-'*12} {'-'*12} {'-'*12}")

    for class_name in ['buck', 'doe', 'fawn', 'cattle']:
        old_stats = old_results['by_class'].get(class_name, {'total': 0, 'correct': 0})
        new_stats = new_results['by_class'].get(class_name, {'total': 0, 'correct': 0})

        if old_stats['total'] > 0:
            old_class_acc = (old_stats['correct'] / old_stats['total'] * 100)
            new_class_acc = (new_stats['correct'] / new_stats['total'] * 100)
            change = new_class_acc - old_class_acc

            print(f"  {class_name:<12s} {old_class_acc:11.2f}% {new_class_acc:11.2f}% {change:+11.2f}%")

    # Confidence range comparison (most important: 0.40-0.51)
    print(f"\n[ACCURACY BY CONFIDENCE RANGE]")
    print(f"  {'Range':<12s} {'Old Model':>12s} {'New Model':>12s} {'Change':>12s}")
    print(f"  {'-'*12} {'-'*12} {'-'*12} {'-'*12}")

    for range_name in ['0.40-0.51', '0.51-0.60', '0.60-0.80', '0.80-1.00']:
        old_stats = old_results['confidence_ranges'][range_name]
        new_stats = new_results['confidence_ranges'][range_name]

        if old_stats['total'] > 0:
            old_range_acc = (old_stats['correct'] / old_stats['total'] * 100)
            new_range_acc = (new_stats['correct'] / new_stats['total'] * 100)
            change = new_range_acc - old_range_acc

            marker = ""
            if range_name == '0.40-0.51':
                marker = " [CRITICAL]"

            print(f"  {range_name:<12s} {old_range_acc:11.2f}% {new_range_acc:11.2f}% {change:+11.2f}%{marker}")

    # Buck over-classification analysis
    print(f"\n[BUCK OVER-CLASSIFICATION ANALYSIS]")

    # Count doe -> buck errors in low confidence range
    def count_doe_to_buck_errors(results):
        errors = 0
        total_does_low_conf = 0

        for det in results['detections']:
            if det['gt_class'] == 'doe' and det['confidence'] < 0.51:
                total_does_low_conf += 1
                if det['pred_class'] == 'buck':
                    errors += 1

        return errors, total_does_low_conf

    old_errors, old_total = count_doe_to_buck_errors(old_results)
    new_errors, new_total = count_doe_to_buck_errors(new_results)

    if old_total > 0:
        old_error_rate = (old_errors / old_total * 100)
        new_error_rate = (new_errors / new_total * 100) if new_total > 0 else 0

        print(f"  Does misclassified as bucks at <51% confidence:")
        print(f"    Old Model: {old_errors}/{old_total} = {old_error_rate:.1f}%")
        print(f"    New Model: {new_errors}/{new_total} = {new_error_rate:.1f}%")
        print(f"    Improvement: {old_error_rate - new_error_rate:+.1f}%")


def main():
    """Main validation workflow."""
    print("="*80)
    print("YOLOV8 MODEL VALIDATION - Old vs New Comparison")
    print("="*80)

    # Check model files exist
    if not Path(OLD_MODEL).exists():
        print(f"[FAIL] Old model not found: {OLD_MODEL}")
        return 1

    if not Path(NEW_MODEL).exists():
        print(f"[FAIL] New model not found: {NEW_MODEL}")
        return 1

    # Load ground truth from validation set
    print("\n[OK] Loading ground truth labels...")
    val_labels = AUDIT_DIR / "labels" / "val"
    val_images = AUDIT_DIR / "images" / "val"

    if not val_labels.exists():
        print(f"[FAIL] Validation labels not found: {val_labels}")
        return 1

    ground_truth = load_ground_truth(val_labels)
    print(f"[OK] Loaded {len(ground_truth)} validation images")

    # Evaluate old model
    print("\n" + "="*80)
    print("EVALUATING OLD MODEL")
    print("="*80)
    old_results = evaluate_model(OLD_MODEL, val_images, ground_truth)
    print_results("OLD MODEL", old_results)

    # Evaluate new model
    print("\n" + "="*80)
    print("EVALUATING NEW MODEL")
    print("="*80)
    new_results = evaluate_model(NEW_MODEL, val_images, ground_truth)
    print_results("NEW MODEL", new_results)

    # Compare models
    compare_models(old_results, new_results)

    # Save detailed results
    output_file = "model_validation_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'old_model': {
                'path': OLD_MODEL,
                'results': old_results
            },
            'new_model': {
                'path': NEW_MODEL,
                'results': new_results
            }
        }, f, indent=2, default=str)

    print(f"\n[OK] Detailed results saved to: {output_file}")

    # Final recommendation
    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}")

    old_acc = (old_results['correct_detections'] / old_results['total_detections'] * 100)
    new_acc = (new_results['correct_detections'] / new_results['total_detections'] * 100)

    # Focus on critical range (0.40-0.51)
    old_critical = old_results['confidence_ranges']['0.40-0.51']
    new_critical = new_results['confidence_ranges']['0.40-0.51']

    old_critical_acc = (old_critical['correct'] / old_critical['total'] * 100) if old_critical['total'] > 0 else 0
    new_critical_acc = (new_critical['correct'] / new_critical['total'] * 100) if new_critical['total'] > 0 else 0

    if new_acc > old_acc and new_critical_acc > 80:
        print("[DEPLOY] New model shows improvement. Ready for deployment.")
        print(f"  Overall accuracy improved: {old_acc:.2f}% -> {new_acc:.2f}%")
        print(f"  Critical range (0.40-0.51): {old_critical_acc:.2f}% -> {new_critical_acc:.2f}%")
    elif new_acc > old_acc:
        print("[CAUTION] New model shows improvement but critical range <80% accuracy.")
        print(f"  Overall accuracy improved: {old_acc:.2f}% -> {new_acc:.2f}%")
        print(f"  Critical range (0.40-0.51): {new_critical_acc:.2f}% (target: >80%)")
        print("  Consider raising confidence threshold instead of deploying.")
    else:
        print("[DO NOT DEPLOY] New model does not show improvement.")
        print(f"  Overall accuracy: {old_acc:.2f}% -> {new_acc:.2f}%")
        print("  Keep current model and consider alternative training strategies.")

    print(f"{'='*80}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
