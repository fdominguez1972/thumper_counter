#!/usr/bin/env python3
"""
Consolidate old age-based buck classifications into simplified 'buck' classification.

This script updates all detections with old model classifications:
  - young → buck (young bucks)
  - mid → buck (mid-age bucks)
  - mature → buck (mature bucks)

This cleanup aligns the database with the new simplified buck/doe model
which doesn't distinguish buck ages.

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


def consolidate_buck_classifications():
    """
    Consolidate old buck age classifications into simplified 'buck'.

    Updates:
    - young → buck
    - mid → buck
    - mature → buck

    This only affects the 'classification' field (ML model output).
    Manual corrections ('corrected_classification') are preserved.
    """
    db = SessionLocal()

    try:
        print("=" * 70)
        print("Buck Classification Consolidation")
        print("=" * 70)
        print()

        # Get current counts
        print("[INFO] Current classification counts:")
        current_counts = db.execute(text("""
            SELECT classification, COUNT(*) as count
            FROM detections
            WHERE classification IN ('young', 'mid', 'mature', 'buck')
            GROUP BY classification
            ORDER BY classification
        """)).fetchall()

        for row in current_counts:
            print(f"  {row[0]:10s}: {row[1]:6,d} detections")

        print()

        # Update young → buck
        print("[INFO] Updating young → buck...")
        young_updated = db.execute(text("""
            UPDATE detections
            SET classification = 'buck'
            WHERE classification = 'young'
            RETURNING id
        """)).rowcount
        print(f"  [OK] Updated {young_updated:,d} detections")

        # Update mid → buck
        print("[INFO] Updating mid → buck...")
        mid_updated = db.execute(text("""
            UPDATE detections
            SET classification = 'buck'
            WHERE classification = 'mid'
            RETURNING id
        """)).rowcount
        print(f"  [OK] Updated {mid_updated:,d} detections")

        # Update mature → buck
        print("[INFO] Updating mature → buck...")
        mature_updated = db.execute(text("""
            UPDATE detections
            SET classification = 'buck'
            WHERE classification = 'mature'
            RETURNING id
        """)).rowcount
        print(f"  [OK] Updated {mature_updated:,d} detections")

        # Commit changes
        db.commit()
        print()
        print("[INFO] All updates committed successfully")

        # Get new counts
        print()
        print("[INFO] New classification counts:")
        new_counts = db.execute(text("""
            SELECT classification, COUNT(*) as count
            FROM detections
            WHERE classification IN ('young', 'mid', 'mature', 'buck')
            GROUP BY classification
            ORDER BY classification
        """)).fetchall()

        for row in new_counts:
            print(f"  {row[0]:10s}: {row[1]:6,d} detections")

        total_updated = young_updated + mid_updated + mature_updated
        print()
        print("=" * 70)
        print(f"[SUMMARY] Total detections consolidated: {total_updated:,d}")
        print("=" * 70)
        print()
        print("[OK] Buck classification consolidation complete!")
        print()
        print("NOTE: This only updated ML classifications (classification field).")
        print("      Manual corrections (corrected_classification) were preserved.")

    except Exception as e:
        db.rollback()
        print(f"\n[FAIL] Error during consolidation: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    consolidate_buck_classifications()
