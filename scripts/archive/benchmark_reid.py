#!/usr/bin/env python3
"""
Benchmark Re-Identification Performance
Sprint 9: Re-ID GPU Optimization
Date: 2025-11-07

Tests ResNet50 feature extraction performance with different optimizations.

Usage:
    docker-compose exec worker python3 scripts/benchmark_reid.py --mode single
    docker-compose exec worker python3 scripts/benchmark_reid.py --mode batch --batch-size 16
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import List

import torch
import numpy as np
from PIL import Image as PILImage

# Add src to path
sys.path.insert(0, '/app')

from worker.tasks.reidentification import get_reid_model, extract_feature_vector
from backend.core.database import SessionLocal
from backend.models.detection import Detection
from backend.models.image import Image


def load_test_crops(db, num_crops: int = 50) -> List[PILImage.Image]:
    """
    Load real deer crops from database for testing.

    Args:
        db: Database session
        num_crops: Number of crops to load

    Returns:
        List of PIL Images
    """
    # Get detections with good-sized bounding boxes
    from sqlalchemy import text
    detections = (
        db.query(Detection, Image)
        .join(Image, Detection.image_id == Image.id)
        .filter(text("(bbox->>'width')::int >= 80"))
        .filter(text("(bbox->>'height')::int >= 80"))
        .filter(Detection.is_duplicate == False)
        .limit(num_crops)
        .all()
    )

    crops = []

    for detection, image in detections:
        try:
            # Load image
            img_path = Path(image.path)
            if not img_path.exists():
                continue

            pil_img = PILImage.open(img_path)

            # Extract crop
            bbox = detection.bbox
            x = bbox['x']
            y = bbox['y']
            width = bbox['width']
            height = bbox['height']

            crop = pil_img.crop((x, y, x + width, y + height))
            crops.append(crop)

            if len(crops) >= num_crops:
                break

        except Exception as e:
            print(f"[WARN] Failed to load crop: {e}")
            continue

    return crops


def benchmark_single(crops: List[PILImage.Image], fp16: bool = False) -> dict:
    """
    Benchmark single-image feature extraction.

    Args:
        crops: List of PIL images
        fp16: Use FP16 mixed precision

    Returns:
        dict: Performance metrics
    """
    print(f"[INFO] Benchmarking single-image processing (FP16: {fp16})")

    model, transform = get_reid_model()

    if fp16:
        model = model.half()

    times = []
    device = next(model.parameters()).device

    # Warm-up
    for i in range(5):
        crop = crops[i % len(crops)]
        img_tensor = transform(crop).unsqueeze(0).to(device)
        if fp16:
            img_tensor = img_tensor.half()

        with torch.no_grad():
            _ = model(img_tensor)

    # Benchmark
    for i, crop in enumerate(crops[:50]):
        img_tensor = transform(crop).unsqueeze(0).to(device)
        if fp16:
            img_tensor = img_tensor.half()

        torch.cuda.synchronize()
        start = time.time()

        with torch.no_grad():
            features = model(img_tensor)

        torch.cuda.synchronize()
        end = time.time()

        times.append(end - start)

    return {
        'mode': 'single',
        'fp16': fp16,
        'mean_time': np.mean(times),
        'median_time': np.median(times),
        'min_time': np.min(times),
        'max_time': np.max(times),
        'throughput': 1.0 / np.mean(times)
    }


def benchmark_batch(crops: List[PILImage.Image], batch_size: int = 16, fp16: bool = False) -> dict:
    """
    Benchmark batch feature extraction.

    Args:
        crops: List of PIL images
        batch_size: Batch size for processing
        fp16: Use FP16 mixed precision

    Returns:
        dict: Performance metrics
    """
    print(f"[INFO] Benchmarking batch processing (batch_size={batch_size}, FP16={fp16})")

    model, transform = get_reid_model()

    if fp16:
        model = model.half()

    times = []
    device = next(model.parameters()).device

    # Create batches
    num_batches = len(crops) // batch_size

    # Warm-up
    batch_crops = crops[:batch_size]
    batch_tensor = torch.stack([transform(crop) for crop in batch_crops]).to(device)
    if fp16:
        batch_tensor = batch_tensor.half()

    for _ in range(3):
        with torch.no_grad():
            _ = model(batch_tensor)

    # Benchmark
    for i in range(num_batches):
        batch_crops = crops[i * batch_size:(i + 1) * batch_size]

        batch_tensor = torch.stack([transform(crop) for crop in batch_crops]).to(device)
        if fp16:
            batch_tensor = batch_tensor.half()

        torch.cuda.synchronize()
        start = time.time()

        with torch.no_grad():
            features = model(batch_tensor)

        torch.cuda.synchronize()
        end = time.time()

        batch_time = end - start
        per_image_time = batch_time / batch_size
        times.append(per_image_time)

    return {
        'mode': 'batch',
        'batch_size': batch_size,
        'fp16': fp16,
        'mean_time': np.mean(times),
        'median_time': np.median(times),
        'min_time': np.min(times),
        'max_time': np.max(times),
        'throughput': 1.0 / np.mean(times)
    }


def main():
    parser = argparse.ArgumentParser(description='Benchmark re-ID performance')
    parser.add_argument('--mode', choices=['single', 'batch', 'both'], default='both')
    parser.add_argument('--batch-size', type=int, default=16)
    parser.add_argument('--fp16', action='store_true', help='Test FP16 mixed precision')
    parser.add_argument('--num-crops', type=int, default=100)

    args = parser.parse_args()

    # Load test data
    db = SessionLocal()
    print(f"[INFO] Loading {args.num_crops} test crops...")
    crops = load_test_crops(db, args.num_crops)
    db.close()

    if len(crops) == 0:
        print("[FAIL] No crops loaded. Cannot benchmark.")
        return

    print(f"[OK] Loaded {len(crops)} crops")
    print(f"[INFO] GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
    print('')

    results = []

    # Single-image benchmark
    if args.mode in ['single', 'both']:
        result_fp32 = benchmark_single(crops, fp16=False)
        results.append(result_fp32)

        if args.fp16:
            result_fp16 = benchmark_single(crops, fp16=True)
            results.append(result_fp16)

    # Batch benchmark
    if args.mode in ['batch', 'both']:
        result_batch_fp32 = benchmark_batch(crops, batch_size=args.batch_size, fp16=False)
        results.append(result_batch_fp32)

        if args.fp16:
            result_batch_fp16 = benchmark_batch(crops, batch_size=args.batch_size, fp16=True)
            results.append(result_batch_fp16)

    # Print results
    print('')
    print('=' * 70)
    print('RE-ID BENCHMARK RESULTS')
    print('=' * 70)

    for result in results:
        mode_label = f"{result['mode']}"
        if result.get('batch_size'):
            mode_label += f" (batch={result['batch_size']})"
        if result.get('fp16'):
            mode_label += " [FP16]"
        else:
            mode_label += " [FP32]"

        print(f"\n{mode_label}:")
        print(f"  Mean time:   {result['mean_time']*1000:.2f} ms/image")
        print(f"  Median time: {result['median_time']*1000:.2f} ms/image")
        print(f"  Throughput:  {result['throughput']:.1f} images/second")

    print('=' * 70)


if __name__ == '__main__':
    main()
