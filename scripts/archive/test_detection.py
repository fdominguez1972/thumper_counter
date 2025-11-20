#!/usr/bin/env python3
"""
YOLOv8 Detection Test Script
Version: 1.0.0
Date: 2025-11-04

Purpose: Test the trained YOLOv8 deer detection model on sample images.

WHY: Verify that the copied model loads correctly and produces expected
detections with class labels and confidence scores.

Usage:
    python3 scripts/test_detection.py
    python3 scripts/test_detection.py --image path/to/image.jpg
    python3 scripts/test_detection.py --sample-dir /path/to/images/ --num-samples 5
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict
import random

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def print_banner():
    """Print ASCII banner"""
    print("=" * 70)
    print("YOLOv8 Deer Detection Test")
    print("=" * 70)
    print()


def load_model(model_path: Path):
    """
    Load YOLOv8 model.

    Args:
        model_path: Path to model file

    Returns:
        Loaded YOLO model
    """
    try:
        from ultralytics import YOLO

        print(f"[INFO] Loading model from: {model_path}")

        if not model_path.exists():
            print(f"[FAIL] Model file not found: {model_path}")
            print(f"[INFO] Run: ./scripts/copy_models.sh")
            sys.exit(1)

        model = YOLO(str(model_path))
        print(f"[OK] Model loaded successfully")
        print(f"[INFO] Model classes ({len(model.names)}): {list(model.names.values())}")
        print()

        return model

    except ImportError:
        print("[FAIL] ultralytics package not installed")
        print("[INFO] Install with: pip install ultralytics")
        sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Error loading model: {e}")
        sys.exit(1)


def get_sample_images(sample_dir: Path, num_samples: int = 3) -> List[Path]:
    """
    Get random sample images from directory.

    Args:
        sample_dir: Directory containing images
        num_samples: Number of random samples to select

    Returns:
        List of image paths
    """
    if not sample_dir.exists():
        print(f"[FAIL] Sample directory not found: {sample_dir}")
        sys.exit(1)

    # Find all image files
    image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
    images = []
    for ext in image_extensions:
        images.extend(sample_dir.glob(f'*{ext}'))

    if not images:
        print(f"[FAIL] No images found in: {sample_dir}")
        sys.exit(1)

    # Select random samples
    num_samples = min(num_samples, len(images))
    samples = random.sample(images, num_samples)

    print(f"[INFO] Found {len(images)} images in {sample_dir}")
    print(f"[INFO] Selected {num_samples} random samples")
    print()

    return samples


def run_detection(model, image_path: Path, conf_threshold: float = 0.5) -> Dict:
    """
    Run detection on a single image.

    Args:
        model: YOLO model
        image_path: Path to image
        conf_threshold: Confidence threshold for detections

    Returns:
        Dictionary with detection results
    """
    print("-" * 70)
    print(f"Image: {image_path.name}")
    print("-" * 70)

    try:
        # Run detection
        results = model.predict(
            str(image_path),
            conf=conf_threshold,
            verbose=False
        )

        if not results or len(results) == 0:
            print("[WARN] No results returned")
            return {'detections': [], 'error': 'No results'}

        result = results[0]

        # Check if any detections
        if result.boxes is None or len(result.boxes) == 0:
            print(f"[INFO] No detections (confidence threshold: {conf_threshold})")
            print()
            return {'detections': [], 'num_detections': 0}

        # Process detections
        detections = []
        print(f"[OK] Found {len(result.boxes)} detections")
        print()

        # Group by class for summary
        class_counts = {}

        for idx, box in enumerate(result.boxes):
            # Extract box data
            xyxy = box.xyxy[0].cpu().numpy()
            conf = float(box.conf[0].cpu().numpy())
            cls_id = int(box.cls[0].cpu().numpy())
            cls_name = model.names[cls_id]

            # Store detection
            detection = {
                'bbox': [float(x) for x in xyxy],
                'confidence': conf,
                'class_id': cls_id,
                'class_name': cls_name
            }
            detections.append(detection)

            # Count classes
            class_counts[cls_name] = class_counts.get(cls_name, 0) + 1

            # Print detection details
            x1, y1, x2, y2 = xyxy
            width = x2 - x1
            height = y2 - y1

            print(f"  Detection #{idx + 1}:")
            print(f"    Class:      {cls_name}")
            print(f"    Confidence: {conf:.3f}")
            print(f"    BBox:       [{x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f}]")
            print(f"    Size:       {width:.1f} x {height:.1f} pixels")
            print()

        # Print summary
        print("  Summary:")
        for cls_name, count in sorted(class_counts.items()):
            print(f"    {cls_name}: {count}")
        print()

        return {
            'detections': detections,
            'num_detections': len(detections),
            'class_counts': class_counts,
            'image_path': str(image_path)
        }

    except Exception as e:
        print(f"[FAIL] Detection failed: {e}")
        print()
        return {'detections': [], 'error': str(e)}


def print_overall_summary(results: List[Dict]):
    """
    Print overall summary across all images.

    Args:
        results: List of detection results
    """
    print("=" * 70)
    print("Overall Summary")
    print("=" * 70)
    print()

    total_images = len(results)
    total_detections = sum(r.get('num_detections', 0) for r in results)
    images_with_detections = sum(1 for r in results if r.get('num_detections', 0) > 0)

    # Aggregate class counts
    all_class_counts = {}
    for result in results:
        class_counts = result.get('class_counts', {})
        for cls_name, count in class_counts.items():
            all_class_counts[cls_name] = all_class_counts.get(cls_name, 0) + count

    print(f"Images processed:        {total_images}")
    print(f"Images with detections:  {images_with_detections}")
    print(f"Total detections:        {total_detections}")
    print()

    if all_class_counts:
        print("Detections by class:")
        for cls_name, count in sorted(all_class_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cls_name:12s} {count:4d}")
        print()

    # Calculate detection rate
    if total_images > 0:
        detection_rate = (images_with_detections / total_images) * 100
        print(f"Detection rate: {detection_rate:.1f}%")

        if total_detections > 0:
            avg_detections = total_detections / images_with_detections
            print(f"Avg detections per image (when detected): {avg_detections:.1f}")

    print()


def map_to_simplified_classes(class_name: str) -> str:
    """
    Map YOLOv8 11 classes to simplified buck/doe/fawn categories.

    Args:
        class_name: Original YOLO class name

    Returns:
        Simplified category
    """
    mapping = {
        'doe': 'doe',
        'fawn': 'fawn',
        'mature': 'buck (mature)',
        'mid': 'buck (mid-age)',
        'young': 'buck (young)',
        'coyote': 'coyote',
        'cow': 'cow',
        'raccoon': 'raccoon',
        'turkey': 'turkey',
        'person': 'person',
        'UTV': 'vehicle',
    }
    return mapping.get(class_name, 'unknown')


def main():
    """Main test function"""
    parser = argparse.ArgumentParser(
        description='Test YOLOv8 deer detection model',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--image',
        type=str,
        help='Path to single image to test'
    )

    parser.add_argument(
        '--sample-dir',
        type=str,
        default='/mnt/i/Hopkins_Ranch_Trail_Cam_Pics/Sanctuary',
        help='Directory to sample images from (default: Sanctuary)'
    )

    parser.add_argument(
        '--num-samples',
        type=int,
        default=3,
        help='Number of random samples to test (default: 3)'
    )

    parser.add_argument(
        '--conf',
        type=float,
        default=0.5,
        help='Confidence threshold (default: 0.5)'
    )

    parser.add_argument(
        '--model',
        type=str,
        default='src/models/yolov8n_deer.pt',
        help='Path to model file (default: src/models/yolov8n_deer.pt)'
    )

    args = parser.parse_args()

    # Print banner
    print_banner()

    # Load model
    model_path = PROJECT_ROOT / args.model
    model = load_model(model_path)

    # Get images to test
    if args.image:
        image_paths = [Path(args.image)]
        print(f"[INFO] Testing single image: {args.image}")
        print()
    else:
        sample_dir = Path(args.sample_dir)
        image_paths = get_sample_images(sample_dir, args.num_samples)

    # Run detection on all images
    results = []
    for image_path in image_paths:
        result = run_detection(model, image_path, conf_threshold=args.conf)
        results.append(result)

    # Print overall summary
    if len(results) > 1:
        print_overall_summary(results)

    # Print class mapping info
    print("=" * 70)
    print("Class Mapping Information")
    print("=" * 70)
    print()
    print("YOLOv8 model has 11 classes that can be mapped to simplified categories:")
    print()
    print("  Deer (5 classes):")
    print("    doe       -> doe")
    print("    fawn      -> fawn")
    print("    mature    -> buck (mature)")
    print("    mid       -> buck (mid-age)")
    print("    young     -> buck (young)")
    print()
    print("  Other (6 classes):")
    print("    coyote, cow, raccoon, turkey, person, UTV")
    print()
    print("[OK] Detection test completed")


if __name__ == '__main__':
    main()
