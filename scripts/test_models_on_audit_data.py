#!/usr/bin/env python3
"""
Test old vs new model on actual audit images from database.
Uses the low-confidence detections we manually audited.
"""

import sys
import os
from pathlib import Path
from collections import defaultdict
import psycopg2
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ultralytics import YOLO
import torch

# Model paths
OLD_MODEL = "src/models/yolov8n_deer.pt"
NEW_MODEL = "src/models/runs/deer_balanced_20251116/weights/best.pt"

# Database config (use 'db' hostname when running in Docker)
DB_CONFIG = {
    'dbname': os.environ.get('POSTGRES_DB', 'deer_tracking'),
    'user': os.environ.get('POSTGRES_USER', 'deertrack'),
    'password': os.environ.get('POSTGRES_PASSWORD', 'secure_password_here'),
    'host': os.environ.get('DB_HOST', 'db'),  # 'db' in Docker, 'localhost' outside
    'port': int(os.environ.get('POSTGRES_PORT', 5432))
}

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


def load_audit_detections(limit=100):
    """Load audited detections from database (confidence 0.50-0.60)."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    query = """
        SELECT
            d.id,
            d.classification,
            d.confidence,
            d.bbox,
            i.path
        FROM detections d
        JOIN images i ON d.image_id = i.id
        WHERE d.confidence >= 0.50
          AND d.confidence <= 0.60
          AND d.classification IN ('buck', 'doe', 'fawn', 'cattle')
          AND d.is_reviewed = true
        ORDER BY d.confidence ASC
        LIMIT %s
    """

    cur.execute(query, (limit,))
    results = cur.fetchall()

    detections = []
    for row in results:
        det_id, classification, confidence, bbox_json, image_path = row

        # Parse bbox from JSON
        import json
        if isinstance(bbox_json, str):
            bbox = json.loads(bbox_json)
        else:
            bbox = bbox_json

        # Convert xywh to xyxy format
        x, y, w, h = bbox['x'], bbox['y'], bbox['width'], bbox['height']
        x1, y1, x2, y2 = x, y, x + w, y + h

        detections.append({
            'id': det_id,
            'ground_truth': classification,
            'confidence': float(confidence),
            'bbox': [float(x1), float(y1), float(x2), float(y2)],
            'filepath': image_path  # Use full path from database
        })

    cur.close()
    conn.close()

    return detections


def calculate_iou_xyxy(box1, box2):
    """Calculate IoU between two xyxy boxes."""
    x1_i = max(box1[0], box2[0])
    y1_i = max(box1[1], box2[1])
    x2_i = min(box1[2], box2[2])
    y2_i = min(box1[3], box2[3])

    if x2_i < x1_i or y2_i < y1_i:
        return 0.0

    intersection = (x2_i - x1_i) * (y2_i - y1_i)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def test_model_on_detections(model_path: str, detections: List[Dict], base_path: Path) -> Dict:
    """Test a model on the audit detections."""
    print(f"\n[*] Loading model: {model_path}")
    model = YOLO(model_path)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"[*] Using device: {device}")

    results = {
        'total': 0,
        'correct': 0,
        'by_class': defaultdict(lambda: {'total': 0, 'correct': 0}),
        'confidence_ranges': {
            '0.50-0.52': {'total': 0, 'correct': 0},
            '0.52-0.55': {'total': 0, 'correct': 0},
            '0.55-0.58': {'total': 0, 'correct': 0},
            '0.58-0.60': {'total': 0, 'correct': 0},
        },
        'confusion': defaultdict(lambda: defaultdict(int)),
        'errors': []
    }

    print(f"[*] Testing on {len(detections)} detections...")

    for i, det in enumerate(detections):
        if (i + 1) % 20 == 0:
            print(f"  Progress: {i+1}/{len(detections)}")

        # Use path directly from database (already absolute path in container)
        image_path = Path(det['filepath'])

        if not image_path.exists():
            print(f"  [WARN] Image not found: {image_path}")
            continue

        # Run inference
        preds = model.predict(
            source=str(image_path),
            conf=0.30,  # Lower threshold to catch more detections
            verbose=False
        )[0]

        # Find prediction that matches our ground truth bbox
        gt_bbox = det['bbox']
        best_match = None
        best_iou = 0.0

        for pred_box in preds.boxes:
            pred_bbox = pred_box.xyxy[0].cpu().numpy().tolist()
            iou = calculate_iou_xyxy(gt_bbox, pred_bbox)

            if iou > best_iou:
                best_iou = iou
                best_match = pred_box

        # Only count if we found a matching detection (IoU > 0.3)
        if best_match is not None and best_iou > 0.3:
            pred_class_id = int(best_match.cls[0])
            pred_class = CLASS_NAMES[pred_class_id]
            pred_conf = float(best_match.conf[0])

            gt_class = det['ground_truth']

            results['total'] += 1
            is_correct = (pred_class == gt_class)

            if is_correct:
                results['correct'] += 1

            # Track by class
            results['by_class'][gt_class]['total'] += 1
            if is_correct:
                results['by_class'][gt_class]['correct'] += 1

            # Track by confidence range (use original detection confidence)
            orig_conf = det['confidence']
            if orig_conf < 0.52:
                conf_range = '0.50-0.52'
            elif orig_conf < 0.55:
                conf_range = '0.52-0.55'
            elif orig_conf < 0.58:
                conf_range = '0.55-0.58'
            else:
                conf_range = '0.58-0.60'

            results['confidence_ranges'][conf_range]['total'] += 1
            if is_correct:
                results['confidence_ranges'][conf_range]['correct'] += 1

            # Confusion matrix
            results['confusion'][gt_class][pred_class] += 1

            # Track errors
            if not is_correct:
                results['errors'].append({
                    'filepath': str(det['filepath']),
                    'ground_truth': gt_class,
                    'predicted': pred_class,
                    'pred_confidence': pred_conf,
                    'orig_confidence': orig_conf,
                    'iou': best_iou
                })

    return results


def print_model_results(model_name: str, results: Dict):
    """Print formatted results."""
    print(f"\n{'='*80}")
    print(f"{model_name} RESULTS")
    print(f"{'='*80}")

    total = results['total']
    correct = results['correct']
    accuracy = (correct / total * 100) if total > 0 else 0

    print(f"\n[OVERALL PERFORMANCE]")
    print(f"  Total Detections Matched: {total}")
    print(f"  Correct Classifications: {correct}")
    print(f"  Incorrect Classifications: {total - correct}")
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
    for range_name in ['0.50-0.52', '0.52-0.55', '0.55-0.58', '0.58-0.60']:
        stats = results['confidence_ranges'][range_name]
        if stats['total'] > 0:
            range_acc = (stats['correct'] / stats['total'] * 100)
            print(f"  {range_name}: {stats['correct']:3d}/{stats['total']:3d} = {range_acc:6.2f}%")

    # Confusion matrix
    print(f"\n[CONFUSION MATRIX]")
    for gt_class in ['buck', 'doe', 'fawn', 'cattle']:
        if gt_class in results['confusion']:
            preds = results['confusion'][gt_class]
            pred_str = ', '.join([f"{p}:{c}" for p, c in preds.items()])
            print(f"  {gt_class:10s} -> {pred_str}")

    # Show sample errors
    if results['errors']:
        print(f"\n[SAMPLE ERRORS] (showing first 5)")
        for i, err in enumerate(results['errors'][:5]):
            print(f"  {i+1}. {Path(err['filepath']).name}")
            print(f"     GT: {err['ground_truth']:10s} | Pred: {err['predicted']:10s} | Conf: {err['pred_confidence']:.2f}")


def main():
    """Main validation workflow."""
    print("="*80)
    print("MODEL COMPARISON ON AUDIT DATA (Confidence 0.50-0.60)")
    print("="*80)

    # Check models exist
    if not Path(OLD_MODEL).exists():
        print(f"[FAIL] Old model not found: {OLD_MODEL}")
        return 1

    if not Path(NEW_MODEL).exists():
        print(f"[FAIL] New model not found: {NEW_MODEL}")
        return 1

    # Load audit data
    print("\n[*] Loading audit detections from database...")
    detections = load_audit_detections(limit=200)
    print(f"[OK] Loaded {len(detections)} audited detections")

    # Test old model
    print("\n" + "="*80)
    print("TESTING OLD MODEL")
    print("="*80)
    old_results = test_model_on_detections(OLD_MODEL, detections, None)  # base_path not needed
    print_model_results("OLD MODEL", old_results)

    # Test new model
    print("\n" + "="*80)
    print("TESTING NEW MODEL")
    print("="*80)
    new_results = test_model_on_detections(NEW_MODEL, detections, None)  # base_path not needed
    print_model_results("NEW MODEL", new_results)

    # Comparison
    print(f"\n{'='*80}")
    print("COMPARISON SUMMARY")
    print(f"{'='*80}")

    old_acc = (old_results['correct'] / old_results['total'] * 100) if old_results['total'] > 0 else 0
    new_acc = (new_results['correct'] / new_results['total'] * 100) if new_results['total'] > 0 else 0
    improvement = new_acc - old_acc

    print(f"\n[OVERALL ACCURACY]")
    print(f"  Old Model: {old_acc:.2f}%")
    print(f"  New Model: {new_acc:.2f}%")
    print(f"  Change: {improvement:+.2f}%")

    # Class comparison
    print(f"\n[CLASS ACCURACY COMPARISON]")
    print(f"  {'Class':<10s} {'Old':>10s} {'New':>10s} {'Change':>10s}")
    print(f"  {'-'*10} {'-'*10} {'-'*10} {'-'*10}")

    for class_name in ['buck', 'doe', 'fawn', 'cattle']:
        old_stats = old_results['by_class'].get(class_name, {'total': 0, 'correct': 0})
        new_stats = new_results['by_class'].get(class_name, {'total': 0, 'correct': 0})

        if old_stats['total'] > 0 or new_stats['total'] > 0:
            old_class_acc = (old_stats['correct'] / old_stats['total'] * 100) if old_stats['total'] > 0 else 0
            new_class_acc = (new_stats['correct'] / new_stats['total'] * 100) if new_stats['total'] > 0 else 0
            change = new_class_acc - old_class_acc

            status = "[BETTER]" if change > 5 else "[WORSE]" if change < -5 else ""
            print(f"  {class_name:<10s} {old_class_acc:9.2f}% {new_class_acc:9.2f}% {change:+9.2f}% {status}")

    # Recommendation
    print(f"\n{'='*80}")
    print("RECOMMENDATION")
    print(f"{'='*80}")

    if new_acc > old_acc + 5:
        print("[DEPLOY] New model shows significant improvement (+5% or more)")
    elif new_acc > old_acc:
        print("[MARGINAL] New model shows minor improvement (<5%)")
        print("  Consider additional testing before deployment")
    else:
        print("[DO NOT DEPLOY] New model does not improve accuracy")
        print("  Keep current model")

    print(f"\n{'='*80}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
