#!/usr/bin/env python3
"""
Backfill Similarity Scores for Existing Detections
Feature 010, Option D - Hybrid Approach (Phase 2)

This script re-calculates similarity scores for all existing detections that
have been assigned to deer profiles. This provides immediate analysis data
without waiting for new detections to accumulate.

Purpose:
1. Extract all detections with deer_id assignments
2. For each detection, calculate similarity vs all deer of same sex
3. Log results to reid_similarity_scores table
4. Provide data for immediate threshold analysis

Usage:
    python3 scripts/backfill_similarity_scores.py

Options:
    --limit N         Process only N detections (for testing)
    --start-offset N  Skip first N detections
    --batch-size N    Process N detections per batch (default: 100)
    --dry-run         Show what would be done without logging

Performance:
    - Expected: 59,077 detections × 50 deer profiles = 2.95M comparisons
    - Processing time: 6-8 hours on RTX 4080 Super
    - GPU memory: ~3-4GB
    - Disk space: ~500MB for similarity scores table
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import time
from datetime import datetime
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import torch

# Import re-ID components
from worker.tasks.reidentification import get_reid_model, extract_deer_crop
from backend.models.detection import Detection
from backend.models.deer import Deer
from backend.models.image import Image


# Database connection
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "deertrack")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "secure_password_here")
DB_NAME = os.getenv("POSTGRES_DB", "deer_tracking")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

REID_THRESHOLD = float(os.getenv('REID_THRESHOLD', 0.85))
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'


def extract_features_for_detection(detection, image_path, model, transform):
    """
    Extract feature vector for a single detection.

    Args:
        detection: Detection record
        image_path: Path to image file
        model: Re-ID model
        transform: Image transform

    Returns:
        np.ndarray: 512-dim L2-normalized feature vector, or None
    """
    try:
        # Extract crop
        crop = extract_deer_crop(Path(image_path), detection.bbox)
        if crop is None:
            return None

        # Transform and move to device
        img_tensor = transform(crop).unsqueeze(0).to(DEVICE)

        # Extract features
        with torch.no_grad():
            features = model(img_tensor)

        # Convert to numpy and normalize
        features_np = features.cpu().numpy()[0]
        norm = np.linalg.norm(features_np)
        if norm == 0:
            return None

        return features_np / norm

    except Exception as e:
        print(f"[WARN] Feature extraction failed for detection {detection.id}: {e}")
        return None


def calculate_similarities(feature_vector, all_deer, sex_filter=None):
    """
    Calculate cosine similarity between detection and all deer profiles.

    Args:
        feature_vector: Detection feature vector (512-dim numpy array)
        all_deer: List of Deer records with feature_vectors
        sex_filter: Optional sex to filter deer (e.g., DeerSex.BUCK)

    Returns:
        List of tuples: (deer_id, similarity_score, sex_match, matched)
    """
    results = []

    for deer in all_deer:
        if deer.feature_vector is None:
            continue

        # Apply sex filter if provided
        sex_match = (sex_filter is None) or (deer.sex == sex_filter)

        # Calculate cosine similarity
        deer_vector = np.array(deer.feature_vector)
        similarity = np.dot(feature_vector, deer_vector)

        # Determine if this would result in a match
        matched = bool((similarity >= REID_THRESHOLD) and sex_match)

        results.append((deer.id, float(similarity), bool(sex_match), matched))

    return results


def backfill_detection_similarities(db_session, detection_id, dry_run=False):
    """
    Backfill similarity scores for a single detection.

    Args:
        db_session: Database session
        detection_id: UUID of detection to process
        dry_run: If True, don't write to database

    Returns:
        int: Number of similarity scores logged
    """
    # Load detection
    detection = db_session.query(Detection).filter(Detection.id == detection_id).first()
    if not detection:
        print(f"[WARN] Detection not found: {detection_id}")
        return 0

    # Load image
    image = db_session.query(Image).filter(Image.id == detection.image_id).first()
    if not image or not Path(image.path).exists():
        print(f"[WARN] Image not found for detection {detection_id}")
        return 0

    # Load re-ID model
    model, transform = get_reid_model()

    # Extract features for this detection
    feature_vector = extract_features_for_detection(detection, image.path, model, transform)
    if feature_vector is None:
        print(f"[WARN] Failed to extract features for detection {detection_id}")
        return 0

    # Get all deer profiles
    all_deer = db_session.query(Deer).filter(Deer.feature_vector.isnot(None)).all()
    if not all_deer:
        print(f"[INFO] No deer profiles with feature vectors found")
        return 0

    # Map classification to sex for filtering
    from backend.models.deer import DeerSex
    sex_mapping = {
        'doe': DeerSex.DOE,
        'buck': DeerSex.BUCK,
        'fawn': DeerSex.FAWN,
        'mature': DeerSex.BUCK,
        'mid': DeerSex.BUCK,
        'young': DeerSex.BUCK,
        'unknown': DeerSex.UNKNOWN
    }
    deer_sex = sex_mapping.get(detection.classification, DeerSex.UNKNOWN)

    # Calculate similarities against all deer of same sex
    similarities = calculate_similarities(feature_vector, all_deer, sex_filter=deer_sex)

    if dry_run:
        print(f"[DRY-RUN] Would log {len(similarities)} similarity scores for detection {detection_id}")
        return len(similarities)

    # Log all similarities
    logged_count = 0
    for deer_id, similarity_score, sex_match, matched in similarities:
        try:
            db_session.execute(
                text("""
                    INSERT INTO reid_similarity_scores
                    (detection_id, deer_id, similarity_score, sex_match, matched,
                     threshold_used, detection_classification, deer_sex)
                    VALUES (:detection_id, :deer_id, :similarity_score, :sex_match,
                            :matched, :threshold_used, :detection_classification, :deer_sex)
                    ON CONFLICT (detection_id, deer_id) DO NOTHING
                """),
                {
                    'detection_id': detection_id,
                    'deer_id': deer_id,
                    'similarity_score': similarity_score,
                    'sex_match': sex_match,
                    'matched': matched,
                    'threshold_used': float(REID_THRESHOLD),
                    'detection_classification': detection.classification,
                    'deer_sex': deer_sex.value
                }
            )
            logged_count += 1
        except Exception as e:
            print(f"[WARN] Failed to log similarity for detection={detection_id}, deer={deer_id}: {e}")

    db_session.commit()
    return logged_count


def main():
    parser = argparse.ArgumentParser(description='Backfill similarity scores for existing detections')
    parser.add_argument('--limit', type=int, help='Process only N detections')
    parser.add_argument('--start-offset', type=int, default=0, help='Skip first N detections')
    parser.add_argument('--batch-size', type=int, default=100, help='Detections per batch')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    args = parser.parse_args()

    print(f"[INFO] Backfilling similarity scores")
    print(f"[INFO] REID_THRESHOLD: {REID_THRESHOLD}")
    print(f"[INFO] Device: {DEVICE}")
    print(f"[INFO] Dry run: {args.dry_run}")
    print()

    # Create database connection
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Count total detections with deer_id
    total_query = text("""
        SELECT COUNT(*) as total
        FROM detections
        WHERE deer_id IS NOT NULL
    """)
    total_detections = session.execute(total_query).fetchone()[0]
    print(f"[INFO] Total detections with deer_id: {total_detections}")

    # Apply limit if specified
    process_count = min(args.limit, total_detections) if args.limit else total_detections
    print(f"[INFO] Will process: {process_count} detections")
    print()

    # Get detection IDs in batches
    query = text("""
        SELECT id
        FROM detections
        WHERE deer_id IS NOT NULL
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """)

    start_time = time.time()
    processed = 0
    total_scores_logged = 0

    for offset in range(args.start_offset, process_count, args.batch_size):
        batch_limit = min(args.batch_size, process_count - offset)
        batch_ids = [row[0] for row in session.execute(query, {'limit': batch_limit, 'offset': offset})]

        print(f"[INFO] Processing batch {offset//args.batch_size + 1} ({len(batch_ids)} detections)")

        batch_start = time.time()
        for detection_id in batch_ids:
            scores_logged = backfill_detection_similarities(session, detection_id, dry_run=args.dry_run)
            total_scores_logged += scores_logged
            processed += 1

            if processed % 10 == 0:
                elapsed = time.time() - start_time
                rate = processed / elapsed
                remaining = process_count - processed
                eta = remaining / rate if rate > 0 else 0
                print(f"[PROGRESS] {processed}/{process_count} ({100*processed/process_count:.1f}%) "
                      f"| Rate: {rate:.1f} det/s | ETA: {eta/3600:.1f}h | Scores: {total_scores_logged}")

        batch_time = time.time() - batch_start
        print(f"[OK] Batch complete in {batch_time:.1f}s")
        print()

    total_time = time.time() - start_time
    print()
    print(f"[OK] Backfill complete!")
    print(f"[OK] Processed: {processed} detections")
    print(f"[OK] Logged: {total_scores_logged} similarity scores")
    print(f"[OK] Time: {total_time/3600:.2f} hours")
    print(f"[OK] Rate: {processed/total_time:.2f} detections/second")

    session.close()


if __name__ == "__main__":
    main()
