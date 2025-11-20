#!/usr/bin/env python3
"""
Benchmark Enhanced Re-ID Performance (Feature 009 Phase 5)

Measures inference time and throughput for:
- Original ResNet50 extraction
- Multi-scale ResNet50 extraction
- EfficientNet-B0 extraction
- Ensemble matching
- Database query performance

Usage:
    docker-compose exec worker python3 /app/scripts/benchmark_enhanced_reid.py [--samples N]

Options:
    --samples N    Number of test samples (default: 100)
"""

import sys
import time
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, '/app')

from backend.core.database import SessionLocal
from backend.models.detection import Detection
from backend.models.image import Image
from worker.tasks.reidentification import (
    extract_deer_crop,
    extract_feature_vector,
    extract_multiscale_features,
    extract_efficientnet_features,
    extract_all_features,
    DEVICE
)


def benchmark_feature_extraction(crops: List, num_iterations: int = 10) -> Dict:
    """
    Benchmark feature extraction time.

    Args:
        crops: List of PIL Image crops
        num_iterations: Number of iterations per crop

    Returns:
        dict: Timing statistics
    """
    print("\n" + "=" * 80)
    print("FEATURE EXTRACTION BENCHMARK")
    print("=" * 80)

    results = {
        'resnet50': [],
        'multiscale': [],
        'efficientnet': [],
        'all_features': []
    }

    # Warmup (load models and compile)
    print("\n[INFO] Warming up models...")
    for crop in crops[:5]:
        extract_feature_vector(crop)
        extract_multiscale_features(crop)
        extract_efficientnet_features(crop)

    print(f"[INFO] Running benchmark with {len(crops)} crops, {num_iterations} iterations each")
    print(f"[INFO] Device: {DEVICE}")

    # Benchmark ResNet50
    print("\n[1/4] Benchmarking ResNet50...")
    for crop in crops:
        times = []
        for _ in range(num_iterations):
            start = time.perf_counter()
            features = extract_feature_vector(crop)
            elapsed = time.perf_counter() - start
            if features is not None:
                times.append(elapsed * 1000)  # Convert to ms
        if times:
            results['resnet50'].extend(times)

    # Benchmark Multi-scale
    print("[2/4] Benchmarking Multi-scale ResNet50...")
    for crop in crops:
        times = []
        for _ in range(num_iterations):
            start = time.perf_counter()
            features = extract_multiscale_features(crop)
            elapsed = time.perf_counter() - start
            if features is not None:
                times.append(elapsed * 1000)
        if times:
            results['multiscale'].extend(times)

    # Benchmark EfficientNet
    print("[3/4] Benchmarking EfficientNet-B0...")
    for crop in crops:
        times = []
        for _ in range(num_iterations):
            start = time.perf_counter()
            features = extract_efficientnet_features(crop)
            elapsed = time.perf_counter() - start
            if features is not None:
                times.append(elapsed * 1000)
        if times:
            results['efficientnet'].extend(times)

    # Benchmark all features (ensemble)
    print("[4/4] Benchmarking combined extraction...")
    for crop in crops:
        times = []
        for _ in range(num_iterations):
            start = time.perf_counter()
            features = extract_all_features(crop)
            elapsed = time.perf_counter() - start
            times.append(elapsed * 1000)
        if times:
            results['all_features'].extend(times)

    return results


def print_timing_stats(name: str, times: List[float]):
    """Print timing statistics."""
    times_arr = np.array(times)
    print(f"\n{name}:")
    print(f"  Samples: {len(times)}")
    print(f"  Mean: {np.mean(times_arr):.2f} ms")
    print(f"  Median: {np.median(times_arr):.2f} ms")
    print(f"  Std: {np.std(times_arr):.2f} ms")
    print(f"  Min: {np.min(times_arr):.2f} ms")
    print(f"  Max: {np.max(times_arr):.2f} ms")
    print(f"  P95: {np.percentile(times_arr, 95):.2f} ms")
    print(f"  P99: {np.percentile(times_arr, 99):.2f} ms")
    print(f"  Throughput: {1000/np.mean(times_arr):.1f} extractions/sec")


def benchmark_database_queries(db) -> Dict:
    """
    Benchmark database query performance.

    Args:
        db: Database session

    Returns:
        dict: Query timing statistics
    """
    print("\n" + "=" * 80)
    print("DATABASE QUERY BENCHMARK")
    print("=" * 80)

    from backend.models.deer import Deer
    import random

    # Get a sample deer with all embeddings
    deer_with_enhanced = (
        db.query(Deer)
        .filter(Deer.feature_vector_multiscale.isnot(None))
        .filter(Deer.feature_vector_efficientnet.isnot(None))
        .limit(10)
        .all()
    )

    if not deer_with_enhanced:
        print("\n[WARN] No deer with enhanced embeddings found")
        return {}

    print(f"\n[INFO] Testing with {len(deer_with_enhanced)} deer profiles")

    results = {
        'original_query': [],
        'multiscale_query': [],
        'efficientnet_query': [],
        'ensemble_query': []
    }

    num_iterations = 20

    for deer in deer_with_enhanced:
        # Benchmark original vector query
        query_vector = deer.feature_vector
        for _ in range(num_iterations):
            start = time.perf_counter()
            matches = (
                db.query(Deer)
                .filter(Deer.feature_vector.isnot(None))
                .filter(Deer.sex == deer.sex)
                .order_by(Deer.feature_vector.cosine_distance(query_vector))
                .limit(10)
                .all()
            )
            elapsed = time.perf_counter() - start
            results['original_query'].append(elapsed * 1000)

        # Benchmark multi-scale query
        query_vector_ms = deer.feature_vector_multiscale
        for _ in range(num_iterations):
            start = time.perf_counter()
            matches = (
                db.query(Deer)
                .filter(Deer.feature_vector_multiscale.isnot(None))
                .filter(Deer.sex == deer.sex)
                .order_by(Deer.feature_vector_multiscale.cosine_distance(query_vector_ms))
                .limit(10)
                .all()
            )
            elapsed = time.perf_counter() - start
            results['multiscale_query'].append(elapsed * 1000)

        # Benchmark EfficientNet query
        query_vector_en = deer.feature_vector_efficientnet
        for _ in range(num_iterations):
            start = time.perf_counter()
            matches = (
                db.query(Deer)
                .filter(Deer.feature_vector_efficientnet.isnot(None))
                .filter(Deer.sex == deer.sex)
                .order_by(Deer.feature_vector_efficientnet.cosine_distance(query_vector_en))
                .limit(10)
                .all()
            )
            elapsed = time.perf_counter() - start
            results['efficientnet_query'].append(elapsed * 1000)

        # Benchmark ensemble query (query both and combine)
        for _ in range(num_iterations):
            start = time.perf_counter()
            # Query both vectors
            matches_ms = (
                db.query(
                    Deer,
                    (1 - Deer.feature_vector_multiscale.cosine_distance(query_vector_ms)).label('sim_ms'),
                    (1 - Deer.feature_vector_efficientnet.cosine_distance(query_vector_en)).label('sim_en')
                )
                .filter(Deer.feature_vector_multiscale.isnot(None))
                .filter(Deer.feature_vector_efficientnet.isnot(None))
                .filter(Deer.sex == deer.sex)
                .all()
            )
            # Compute ensemble similarity in Python (this is what the real code does)
            for d, sim_ms, sim_en in matches_ms:
                ensemble_sim = 0.6 * sim_ms + 0.4 * sim_en
            elapsed = time.perf_counter() - start
            results['ensemble_query'].append(elapsed * 1000)

    return results


def main():
    """Main benchmark process."""
    parser = argparse.ArgumentParser(description='Benchmark enhanced Re-ID performance')
    parser.add_argument('--samples', type=int, default=100, help='Number of test samples')
    args = parser.parse_args()

    print("[FEATURE009] Enhanced Re-ID Performance Benchmark")
    print("=" * 80)

    db = SessionLocal()

    try:
        # Load sample detections
        print(f"\n[INFO] Loading {args.samples} sample detections...")

        detections = (
            db.query(Detection)
            .join(Image)
            .filter(Detection.bbox.isnot(None))
            .filter(Detection.classification.in_(['doe', 'buck']))
            .order_by(Detection.confidence.desc())
            .limit(args.samples)
            .all()
        )

        if len(detections) < 10:
            print(f"[FAIL] Not enough detections found (need at least 10, found {len(detections)})")
            return 1

        print(f"[OK] Loaded {len(detections)} detections")

        # Extract crops
        print("\n[INFO] Extracting crops...")
        crops = []
        for detection in detections:
            image = db.query(Image).filter(Image.id == detection.image_id).first()
            if not image:
                continue

            image_path = Path(image.path)
            if not image_path.exists():
                continue

            crop = extract_deer_crop(image_path, detection.bbox)
            if crop is not None:
                crops.append(crop)

        print(f"[OK] Extracted {len(crops)} valid crops")

        if len(crops) < 10:
            print("[FAIL] Not enough valid crops for benchmarking")
            return 1

        # Benchmark feature extraction
        extraction_results = benchmark_feature_extraction(crops[:50], num_iterations=10)

        # Print extraction results
        print("\n" + "=" * 80)
        print("FEATURE EXTRACTION RESULTS")
        print("=" * 80)

        for model_name in ['resnet50', 'multiscale', 'efficientnet', 'all_features']:
            if extraction_results[model_name]:
                print_timing_stats(model_name.upper(), extraction_results[model_name])

        # Benchmark database queries
        query_results = benchmark_database_queries(db)

        if query_results:
            print("\n" + "=" * 80)
            print("DATABASE QUERY RESULTS")
            print("=" * 80)

            for query_type in ['original_query', 'multiscale_query', 'efficientnet_query', 'ensemble_query']:
                if query_results.get(query_type):
                    print_timing_stats(query_type.upper(), query_results[query_type])

        # Summary
        print("\n" + "=" * 80)
        print("PERFORMANCE SUMMARY")
        print("=" * 80)

        if extraction_results['all_features']:
            total_time = np.mean(extraction_results['all_features'])
            print(f"\nTotal extraction time (all 3 models): {total_time:.2f} ms")
            print(f"Throughput: {1000/total_time:.1f} detections/sec")

            # Compare to original
            if extraction_results['resnet50']:
                orig_time = np.mean(extraction_results['resnet50'])
                overhead = total_time - orig_time
                overhead_pct = (overhead / orig_time) * 100
                print(f"\nOverhead vs original ResNet50:")
                print(f"  Original: {orig_time:.2f} ms")
                print(f"  Enhanced: {total_time:.2f} ms")
                print(f"  Overhead: +{overhead:.2f} ms ({overhead_pct:+.1f}%)")

        if query_results.get('ensemble_query'):
            query_time = np.mean(query_results['ensemble_query'])
            print(f"\nEnsemble query time: {query_time:.2f} ms")
            print(f"Query throughput: {1000/query_time:.1f} queries/sec")

        print("\n" + "=" * 80)
        print("[BENCHMARK COMPLETE]")
        print("=" * 80)

        return 0

    except Exception as e:
        print(f"\n[FAIL] Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == '__main__':
    sys.exit(main())
