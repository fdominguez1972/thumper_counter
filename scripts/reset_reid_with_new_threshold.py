#!/usr/bin/env python3
"""
Reset Re-ID with New Threshold (0.70)

This script prepares the database for re-ID reprocessing with the new threshold:
1. Clears deer_id from all detections
2. Deletes all auto-created deer profiles (keeps manual ones)
3. Resets deer table for fresh re-ID processing

Created: 2025-11-12
Author: Claude Code
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import time

# Database connection
DB_URL = "postgresql://deertrack:secure_password_here@localhost:5433/deer_tracking"

def reset_reid():
    """Reset re-ID assignments and deer profiles"""

    print("="*70)
    print("RE-ID RESET FOR NEW THRESHOLD (0.70)")
    print("="*70)
    print()

    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Step 1: Count current state
        result = db.execute(text("""
            SELECT
                COUNT(*) as total_detections,
                COUNT(deer_id) as assigned_detections,
                (SELECT COUNT(*) FROM deer) as total_deer_profiles
            FROM detections
        """)).fetchone()

        print(f"[INFO] Current State:")
        print(f"  Total detections: {result.total_detections:,d}")
        print(f"  Detections with deer_id: {result.assigned_detections:,d}")
        print(f"  Total deer profiles: {result.total_deer_profiles:,d}")
        print()

        # Step 2: Clear deer_id from all detections
        print("[ACTION] Clearing deer_id from all detections...")
        result = db.execute(text("UPDATE detections SET deer_id = NULL"))
        db.commit()
        print(f"[OK] Cleared deer_id from {result.rowcount:,d} detections")
        print()

        # Step 3: Delete all deer profiles (re-ID will recreate them)
        # Note: This deletes ALL deer profiles. If you have manually created ones you want to keep,
        # add a filter here (e.g., WHERE name IS NULL or WHERE created_by = 'system')
        print("[ACTION] Deleting all deer profiles...")
        result = db.execute(text("DELETE FROM deer"))
        db.commit()
        print(f"[OK] Deleted {result.rowcount:,d} deer profiles")
        print()

        # Step 4: Verify reset
        result = db.execute(text("""
            SELECT
                COUNT(*) as total_detections,
                COUNT(deer_id) as assigned_detections,
                (SELECT COUNT(*) FROM deer) as total_deer_profiles
            FROM detections
        """)).fetchone()

        print(f"[INFO] After Reset:")
        print(f"  Total detections: {result.total_detections:,d}")
        print(f"  Detections with deer_id: {result.assigned_detections:,d}")
        print(f"  Total deer profiles: {result.total_deer_profiles:,d}")
        print()

        print("="*70)
        print("RESET COMPLETE")
        print("="*70)
        print()
        print("[INFO] Next Steps:")
        print("  1. Restart worker: docker-compose restart worker")
        print("  2. Queue re-ID tasks for all detections")
        print("  3. Monitor re-ID processing progress")
        print()

    except Exception as e:
        print(f"[FAIL] Error during reset: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == '__main__':
    reset_reid()
