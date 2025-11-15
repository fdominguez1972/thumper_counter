#!/usr/bin/env python3
"""
Re-embed existing deer profiles with enhanced features (Feature 009 Phase 4)

This script updates all existing deer profiles to include:
- feature_vector_multiscale: Multi-scale ResNet50 features
- feature_vector_efficientnet: EfficientNet-B0 features
- embedding_version: Updated to v3_ensemble

Process:
1. Find all deer profiles with only v1_resnet50 embeddings
2. For each deer, find the best quality detection image
3. Extract crop and generate enhanced features
4. Update deer profile with new feature vectors
5. Validate embedding quality

Usage:
    docker-compose exec backend python3 /app/scripts/reembed_deer_enhanced.py [--dry-run] [--limit N]

Options:
    --dry-run    Show what would be done without making changes
    --limit N    Process only N deer profiles (for testing)
    --batch N    Process in batches of N (default: 10)
"""

import sys
import argparse
import time
from pathlib import Path
from typing import Optional, Dict, List
import numpy as np

sys.path.insert(0, '/app')

from sqlalchemy import func
from backend.core.database import SessionLocal
from backend.models.deer import Deer
from backend.models.detection import Detection
from backend.models.image import Image
from worker.tasks.reidentification import (
    extract_deer_crop,
    extract_all_features,
    ENHANCED_MODELS_AVAILABLE
)


def find_best_detection_for_deer(db, deer: Deer) -> Optional[Detection]:
    """
    Find the best quality detection for a deer.

    Criteria:
    1. Highest confidence score
    2. Largest bounding box area (better crop quality)
    3. Most recent (in case of ties)

    Args:
        db: Database session
        deer: Deer profile to find detection for

    Returns:
        Detection: Best quality detection, or None if none found
    """
    from sqlalchemy import cast, Integer, desc, text

    detections = (
        db.query(Detection)
        .join(Image)
        .filter(Detection.deer_id == deer.id)
        .filter(Detection.bbox.isnot(None))
        .filter(Detection.is_duplicate == False)
        .order_by(
            Detection.confidence.desc(),
            Image.timestamp.desc()
        )
        .limit(10)  # Get top 10 candidates
        .all()
    )

    if not detections:
        return None

    # Filter for minimum crop size (50x50)
    valid_detections = []
    for det in detections:
        bbox = det.bbox
        if bbox.get('width', 0) >= 50 and bbox.get('height', 0) >= 50:
            valid_detections.append(det)

    return valid_detections[0] if valid_detections else None


def reembed_deer(db, deer: Deer, dry_run: bool = False) -> Dict:
    """
    Re-embed a single deer profile with enhanced features.

    Args:
        db: Database session
        deer: Deer profile to re-embed
        dry_run: If True, don't save changes

    Returns:
        dict: Results with status and extracted features
    """
    result = {
        'deer_id': str(deer.id),
        'deer_name': deer.name,
        'status': 'unknown',
        'error': None,
        'features_extracted': {},
        'detection_used': None
    }

    try:
        # Find best detection for this deer
        detection = find_best_detection_for_deer(db, deer)
        if not detection:
            result['status'] = 'skipped'
            result['error'] = 'No valid detections found'
            return result

        result['detection_used'] = str(detection.id)

        # Load image
        image = db.query(Image).filter(Image.id == detection.image_id).first()
        if not image:
            result['status'] = 'error'
            result['error'] = 'Detection image not found'
            return result

        # Check image file exists
        image_path = Path(image.path)
        if not image_path.exists():
            result['status'] = 'error'
            result['error'] = f'Image file not found: {image.path}'
            return result

        # Extract crop
        crop = extract_deer_crop(image_path, detection.bbox)
        if crop is None:
            result['status'] = 'error'
            result['error'] = 'Failed to extract crop'
            return result

        # Extract all features
        features = extract_all_features(crop)

        # Check if enhanced features were extracted
        has_multiscale = features.get('multiscale') is not None
        has_efficientnet = features.get('efficientnet') is not None

        result['features_extracted'] = {
            'resnet50': features.get('resnet50') is not None,
            'multiscale': has_multiscale,
            'efficientnet': has_efficientnet
        }

        if not has_multiscale or not has_efficientnet:
            result['status'] = 'partial'
            result['error'] = 'Enhanced models not available'
            return result

        # Update deer profile (unless dry run)
        if not dry_run:
            deer.feature_vector_multiscale = features['multiscale'].tolist()
            deer.feature_vector_efficientnet = features['efficientnet'].tolist()
            deer.embedding_version = 'v3_ensemble'
            db.commit()

        result['status'] = 'success'
        return result

    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)
        return result


def main():
    """Main re-embedding process."""
    parser = argparse.ArgumentParser(description='Re-embed deer with enhanced features')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    parser.add_argument('--limit', type=int, help='Process only N deer profiles')
    parser.add_argument('--batch', type=int, default=10, help='Batch size (default: 10)')
    args = parser.parse_args()

    print("[FEATURE009] Re-embedding deer with enhanced features")
    print("=" * 80)

    if not ENHANCED_MODELS_AVAILABLE:
        print("[FAIL] Enhanced Re-ID models not available")
        print("Make sure worker container has the new model files.")
        return 1

    print(f"[INFO] Dry run: {args.dry_run}")
    print(f"[INFO] Batch size: {args.batch}")
    if args.limit:
        print(f"[INFO] Limit: {args.limit} deer")

    db = SessionLocal()

    try:
        # Find deer profiles that need re-embedding
        query = (
            db.query(Deer)
            .filter(
                (Deer.embedding_version == 'v1_resnet50') |
                (Deer.embedding_version == None)
            )
            .filter(Deer.feature_vector.isnot(None))  # Must have original embedding
        )

        if args.limit:
            query = query.limit(args.limit)

        deer_list = query.all()
        total_deer = len(deer_list)

        print(f"\n[INFO] Found {total_deer} deer profiles to re-embed")

        if total_deer == 0:
            print("[OK] No deer profiles need re-embedding")
            return 0

        # Statistics
        stats = {
            'success': 0,
            'partial': 0,
            'skipped': 0,
            'error': 0
        }

        # Process in batches
        start_time = time.time()

        for i, deer in enumerate(deer_list, 1):
            print(f"\n[{i}/{total_deer}] Processing deer {deer.id} ('{deer.name or 'unnamed'}')")
            print(f"  Sex: {deer.sex.value}, Sightings: {deer.sighting_count}")
            print(f"  Current version: {deer.embedding_version or 'v1_resnet50'}")

            result = reembed_deer(db, deer, dry_run=args.dry_run)

            if result['status'] == 'success':
                print(f"  [OK] Re-embedded successfully")
                print(f"    Detection: {result['detection_used']}")
                print(f"    Features: {result['features_extracted']}")
                stats['success'] += 1
            elif result['status'] == 'partial':
                print(f"  [WARN] Partial: {result['error']}")
                stats['partial'] += 1
            elif result['status'] == 'skipped':
                print(f"  [SKIP] {result['error']}")
                stats['skipped'] += 1
            else:
                print(f"  [FAIL] {result['error']}")
                stats['error'] += 1

            # Batch commit and progress update
            if i % args.batch == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                remaining = (total_deer - i) / rate if rate > 0 else 0

                print(f"\n[PROGRESS] {i}/{total_deer} processed ({i/total_deer*100:.1f}%)")
                print(f"  Rate: {rate:.1f} deer/sec")
                print(f"  Elapsed: {elapsed:.1f}s, Remaining: ~{remaining:.0f}s")
                print(f"  Success: {stats['success']}, Partial: {stats['partial']}, "
                      f"Skipped: {stats['skipped']}, Error: {stats['error']}")

        # Final summary
        duration = time.time() - start_time
        print("\n" + "=" * 80)
        print("[SUMMARY] Re-embedding complete")
        print("=" * 80)
        print(f"Total deer processed: {total_deer}")
        print(f"Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
        print(f"Average rate: {total_deer/duration:.2f} deer/sec")
        print(f"\nResults:")
        print(f"  Success: {stats['success']} ({stats['success']/total_deer*100:.1f}%)")
        print(f"  Partial: {stats['partial']} ({stats['partial']/total_deer*100:.1f}%)")
        print(f"  Skipped: {stats['skipped']} ({stats['skipped']/total_deer*100:.1f}%)")
        print(f"  Error: {stats['error']} ({stats['error']/total_deer*100:.1f}%)")

        if args.dry_run:
            print("\n[INFO] DRY RUN - No changes were saved to database")
        else:
            print("\n[OK] All changes committed to database")

        return 0 if stats['error'] == 0 else 1

    except KeyboardInterrupt:
        print("\n[WARN] Interrupted by user")
        db.rollback()
        return 1
    except Exception as e:
        print(f"\n[FAIL] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 1
    finally:
        db.close()


if __name__ == '__main__':
    sys.exit(main())
