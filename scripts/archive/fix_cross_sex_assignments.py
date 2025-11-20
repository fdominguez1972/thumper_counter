#!/usr/bin/env python3
"""
Fix cross-sex deer profile contamination.

This script identifies and fixes cases where detections of different sexes
were incorrectly assigned to the same deer profile due to burst linking bugs.

Example:
    "Chip" (buck) has detections classified as doe and young - this script
    will unlink the doe detections so only same-sex detections remain.

Created: 2025-11-11
Author: Claude Code
"""
import os
import sys
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import sessionmaker
from backend.models.deer import Deer
from backend.models.detection import Detection

# Database connection
pg_user = os.getenv('POSTGRES_USER', 'deertrack')
pg_pass = os.getenv('POSTGRES_PASSWORD', 'secure_password_here')
pg_host = os.getenv('POSTGRES_HOST', 'db')
pg_port = os.getenv('POSTGRES_PORT', '5432')
pg_db = os.getenv('POSTGRES_DB', 'deer_tracking')

DATABASE_URL = f'postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def get_sex_from_classification(classification: str) -> str:
    """Map detection classification to deer sex."""
    if classification in ('buck', 'young', 'mid', 'mature'):
        return 'buck'
    elif classification == 'doe':
        return 'doe'
    elif classification == 'fawn':
        return 'fawn'
    else:
        return 'unknown'


def fix_cross_sex_assignments():
    """
    Fix deer profiles with cross-sex detection contamination.

    Strategy:
    1. Find deer profiles with multiple sex classifications
    2. For each contaminated profile:
       a. Count detections by classification
       b. Keep the MAJORITY classification (deer's true sex)
       c. Unlink (set deer_id=NULL) for minority sex detections

    This preserves the most likely correct assignments while removing
    incorrect cross-sex contamination from burst linking bugs.
    """
    db = SessionLocal()

    try:
        print("[INFO] Finding deer profiles with cross-sex contamination...")

        # Query deer with multiple sex classifications
        contaminated = db.execute(text("""
            SELECT
                det.deer_id,
                deer.name as deer_name,
                deer.sex as deer_sex,
                STRING_AGG(DISTINCT det.classification, ', ' ORDER BY det.classification) as classifications,
                COUNT(*) as total_detections,
                COUNT(DISTINCT det.classification) as unique_classifications
            FROM detections det
            JOIN deer ON deer.id = det.deer_id
            WHERE det.deer_id IS NOT NULL
            GROUP BY det.deer_id, deer.name, deer.sex
            HAVING COUNT(DISTINCT det.classification) > 1
            ORDER BY deer.name
        """)).fetchall()

        print(f"[INFO] Found {len(contaminated)} contaminated deer profiles\n")

        total_unlinked = 0

        for row in contaminated:
            deer_id = row[0]
            deer_name = row[1] or f"Unnamed-{str(deer_id)[:8]}"
            deer_sex = row[2]
            classifications = row[3]
            total_detections = row[4]

            print(f"[DEER] {deer_name} (sex={deer_sex})")
            print(f"  Total detections: {total_detections}")
            print(f"  Classifications found: {classifications}")

            # Get detection counts by classification
            counts = db.execute(text("""
                SELECT classification, COUNT(*) as count
                FROM detections
                WHERE deer_id = :deer_id
                GROUP BY classification
                ORDER BY count DESC
            """), {'deer_id': deer_id}).fetchall()

            print("  Breakdown:")
            for cls, count in counts:
                sex = get_sex_from_classification(cls)
                match = "[MATCH]" if sex == deer_sex else "[WRONG]"
                print(f"    {cls}: {count} detections {match}")

            # Determine which classifications to KEEP based on deer.sex
            if deer_sex == 'buck':
                keep_classifications = ['buck', 'young', 'mid', 'mature', 'unknown']
            elif deer_sex == 'doe':
                keep_classifications = ['doe', 'unknown']
            elif deer_sex == 'fawn':
                keep_classifications = ['fawn', 'unknown']
            else:  # unknown
                # For unknown sex, keep the majority classification
                majority_classification = counts[0][0]
                keep_classifications = [majority_classification, 'unknown']

            # Unlink detections that don't match deer's sex
            unlinked = db.execute(text("""
                UPDATE detections
                SET deer_id = NULL
                WHERE deer_id = :deer_id
                  AND classification NOT IN :keep_classifications
                RETURNING id
            """), {
                'deer_id': deer_id,
                'keep_classifications': tuple(keep_classifications)
            }).rowcount

            if unlinked > 0:
                print(f"  [FIX] Unlinked {unlinked} cross-sex detections")
                total_unlinked += unlinked
            else:
                print(f"  [OK] No cross-sex detections to unlink")

            print()

        db.commit()

        print(f"\n[SUMMARY]")
        print(f"  Deer profiles fixed: {len(contaminated)}")
        print(f"  Total detections unlinked: {total_unlinked}")
        print(f"\n[OK] Cross-sex assignment cleanup complete!")
        print(f"\nNOTE: Unlinked detections can be re-processed by setting their")
        print(f"      image.processing_status back to 'pending' and re-queuing.")

    except Exception as e:
        db.rollback()
        print(f"\n[FAIL] Error during cleanup: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    print("=" * 70)
    print("Cross-Sex Deer Profile Assignment Cleanup")
    print("=" * 70)
    print()

    fix_cross_sex_assignments()
