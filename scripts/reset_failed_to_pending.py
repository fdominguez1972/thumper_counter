#!/usr/bin/env python3
"""
Reset failed images to pending status for retry processing.
Based on reprocess_with_new_model.py database connection approach.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
pg_user = os.getenv('POSTGRES_USER', 'deertrack')
pg_pass = os.getenv('POSTGRES_PASSWORD', 'secure_password_here')
pg_host = os.getenv('POSTGRES_HOST', 'localhost')  # Connect via host port
pg_port = os.getenv('POSTGRES_PORT', '5433')  # External port
pg_db = os.getenv('POSTGRES_DB', 'deer_tracking')

DATABASE_URL = f'postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}'

def reset_failed_images(limit=100):
    """Reset failed images to pending status."""

    print("=" * 70)
    print(f"RESET FAILED IMAGES - Test Batch ({limit} images)")
    print("=" * 70)

    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        # Get count of failed images
        result = db.execute(text("""
            SELECT COUNT(*) FROM images WHERE processing_status = 'failed'
        """)).fetchone()
        failed_count = result[0]

        print(f"\nTotal failed images: {failed_count}")

        # Reset specified number
        print(f"Resetting {limit} failed images to 'pending'...")

        result = db.execute(text("""
            UPDATE images
            SET processing_status = 'pending',
                error_message = NULL,
                updated_at = NOW()
            WHERE id IN (
                SELECT id FROM images
                WHERE processing_status = 'failed'
                ORDER BY created_at ASC
                LIMIT :limit
            )
        """), {"limit": limit})

        db.commit()
        reset_count = result.rowcount

        print(f"[OK] Successfully reset {reset_count} images")

        # Get updated counts
        result = db.execute(text("""
            SELECT processing_status, COUNT(*) as count
            FROM images
            GROUP BY processing_status
            ORDER BY processing_status
        """)).fetchall()

        print("\nUpdated status distribution:")
        for row in result:
            print(f"  {row[0]:12s}: {row[1]:6d}")

        db.close()

        print("\n" + "=" * 70)
        print("NEXT STEPS:")
        print("=" * 70)
        print(f"1. Queue the {reset_count} pending images:")
        print(f"   curl -X POST 'http://localhost:8001/api/processing/batch?limit={reset_count}'")
        print("2. Monitor: curl -s http://localhost:8001/api/processing/status")
        print("3. If successful, reset remaining:")
        print(f"   python3 scripts/reset_failed_to_pending.py {failed_count - reset_count}")
        print("=" * 70)

        return reset_count

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    reset_failed_images(limit)
