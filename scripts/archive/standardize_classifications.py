#!/usr/bin/env python3
"""
Standardize detection classifications across the database.

This script consolidates classification variants and plural forms:
  - Birds/birds/bird → bird
  - Horses/horses/horse → horse
  - "no animal" variants → "no animals"
  - Remove "no human" (not relevant for wildlife tracking)

Created: 2025-11-11
Author: Claude Code
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
pg_user = os.getenv('POSTGRES_USER', 'deertrack')
pg_pass = os.getenv('POSTGRES_PASSWORD', 'secure_password_here')
pg_host = os.getenv('POSTGRES_HOST', 'db')
pg_port = os.getenv('POSTGRES_PORT', '5432')
pg_db = os.getenv('POSTGRES_DB', 'deer_tracking')

DATABASE_URL = f'postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}'
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def standardize_classifications():
    """
    Standardize classification values across both 'classification' and 'corrected_classification' fields.

    Standardizations:
    - Birds/birds → bird
    - Horses/horses → horse
    - "no animal detected", "no animal" → "no animals"
    - Remove "no human" → NULL (not relevant)

    Operates on BOTH fields to ensure consistency.
    """
    db = SessionLocal()

    try:
        print("=" * 70)
        print("Classification Standardization")
        print("=" * 70)
        print()

        # Get current counts BEFORE standardization
        print("[INFO] Current classification counts:")
        current_counts = db.execute(text("""
            SELECT
                COALESCE(classification, corrected_classification, 'NULL') as value,
                COUNT(*) as count,
                CASE
                    WHEN classification IS NOT NULL AND corrected_classification IS NOT NULL
                        THEN 'both'
                    WHEN classification IS NOT NULL THEN 'classification'
                    ELSE 'corrected_only'
                END as source
            FROM detections
            WHERE classification IS NOT NULL OR corrected_classification IS NOT NULL
            GROUP BY value, source
            ORDER BY value, source
        """)).fetchall()

        for row in current_counts:
            print(f"  {row[0]:30s}: {row[1]:6,d} ({row[2]})")

        print()
        print("-" * 70)
        print("Starting standardization...")
        print("-" * 70)
        print()

        total_updated = 0

        # === STANDARDIZE: Birds/birds → bird ===
        print("[1] Standardizing bird classifications...")

        # classification field
        birds_class = db.execute(text("""
            UPDATE detections
            SET classification = 'bird'
            WHERE classification IN ('Birds', 'birds', 'Bird')
            RETURNING id
        """)).rowcount
        print(f"  classification field: {birds_class:,d} detections")

        # corrected_classification field
        birds_corrected = db.execute(text("""
            UPDATE detections
            SET corrected_classification = 'bird'
            WHERE corrected_classification IN ('Birds', 'birds', 'Bird')
            RETURNING id
        """)).rowcount
        print(f"  corrected_classification field: {birds_corrected:,d} detections")

        birds_total = birds_class + birds_corrected
        print(f"  [OK] Total: {birds_total:,d} bird standardizations")
        total_updated += birds_total
        print()

        # === STANDARDIZE: Horses/horses → horse ===
        print("[2] Standardizing horse classifications...")

        # classification field
        horses_class = db.execute(text("""
            UPDATE detections
            SET classification = 'horse'
            WHERE classification IN ('Horses', 'horses', 'Horse')
            RETURNING id
        """)).rowcount
        print(f"  classification field: {horses_class:,d} detections")

        # corrected_classification field
        horses_corrected = db.execute(text("""
            UPDATE detections
            SET corrected_classification = 'horse'
            WHERE corrected_classification IN ('Horses', 'horses', 'Horse')
            RETURNING id
        """)).rowcount
        print(f"  corrected_classification field: {horses_corrected:,d} detections")

        horses_total = horses_class + horses_corrected
        print(f"  [OK] Total: {horses_total:,d} horse standardizations")
        total_updated += horses_total
        print()

        # === STANDARDIZE: "no animal" variants → "no animals" ===
        print("[3] Standardizing 'no animal' variants...")

        # classification field
        no_animal_class = db.execute(text("""
            UPDATE detections
            SET classification = 'no animals'
            WHERE classification IN ('no animal', 'no animal detected')
            RETURNING id
        """)).rowcount
        print(f"  classification field: {no_animal_class:,d} detections")

        # corrected_classification field
        no_animal_corrected = db.execute(text("""
            UPDATE detections
            SET corrected_classification = 'no animals'
            WHERE corrected_classification IN ('no animal', 'no animal detected')
            RETURNING id
        """)).rowcount
        print(f"  corrected_classification field: {no_animal_corrected:,d} detections")

        no_animal_total = no_animal_class + no_animal_corrected
        print(f"  [OK] Total: {no_animal_total:,d} 'no animal' standardizations")
        total_updated += no_animal_total
        print()

        # === REMOVE: "no human" → NULL ===
        print("[4] Removing 'no human' classifications...")

        # classification field
        no_human_class = db.execute(text("""
            UPDATE detections
            SET classification = NULL
            WHERE classification = 'no human'
            RETURNING id
        """)).rowcount
        print(f"  classification field: {no_human_class:,d} detections")

        # corrected_classification field
        no_human_corrected = db.execute(text("""
            UPDATE detections
            SET corrected_classification = NULL
            WHERE corrected_classification = 'no human'
            RETURNING id
        """)).rowcount
        print(f"  corrected_classification field: {no_human_corrected:,d} detections")

        no_human_total = no_human_class + no_human_corrected
        print(f"  [OK] Total: {no_human_total:,d} 'no human' removals")
        total_updated += no_human_total
        print()

        # Commit changes
        db.commit()
        print("[INFO] All updates committed successfully")

        # Get new counts AFTER standardization
        print()
        print("[INFO] New classification counts:")
        new_counts = db.execute(text("""
            SELECT
                COALESCE(classification, corrected_classification, 'NULL') as value,
                COUNT(*) as count
            FROM detections
            WHERE classification IS NOT NULL OR corrected_classification IS NOT NULL
            GROUP BY value
            ORDER BY value
        """)).fetchall()

        for row in new_counts:
            print(f"  {row[0]:30s}: {row[1]:6,d}")

        print()
        print("=" * 70)
        print(f"[SUMMARY] Total field updates: {total_updated:,d}")
        print("=" * 70)
        print()
        print("[OK] Classification standardization complete!")
        print()

    except Exception as e:
        db.rollback()
        print(f"\n[FAIL] Error during standardization: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    standardize_classifications()
