#!/usr/bin/env python3
"""
Test antler keypoint detection on a sample buck.

Usage:
    python3 scripts/test_antler_detection.py
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from backend.core.database import get_db
from backend.models import Detection
from worker.tasks.antler_detection import detect_antler_keypoints


def main():
    print("=" * 70)
    print("ANTLER DETECTION TEST")
    print("=" * 70)
    print()

    db = next(get_db())

    try:
        # Find a buck detection to test
        buck = db.query(Detection).filter(
            Detection.classification == 'buck'
        ).first()

        if not buck:
            print("[FAIL] No buck detections found in database")
            print("Please process some images with bucks first")
            return 1

        print(f"[INFO] Testing on detection: {buck.id}")
        print(f"       Image: {buck.image.filename}")
        print(f"       Classification: {buck.classification}")
        print(f"       Confidence: {buck.confidence:.3f}")
        print()

        # Run antler detection task
        print("[INFO] Running antler keypoint detection...")
        result = detect_antler_keypoints(str(buck.id))

        print()
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(f"Status: {result['status']}")
        print(f"Keypoints detected: {result.get('keypoints_detected', 0)}")
        print()

        # Query keypoints from database
        from backend.models import AntlerKeypoint

        keypoints = db.query(AntlerKeypoint).filter(
            AntlerKeypoint.detection_id == buck.id
        ).all()

        if keypoints:
            print(f"[OK] Successfully stored {len(keypoints)} keypoints in database")
            print()
            print("Keypoints:")
            for kpt in keypoints:
                print(f"  {kpt.keypoint_index:2d}. {kpt.keypoint_name:20s} "
                      f"({kpt.x:6.1f}, {kpt.y:6.1f}) "
                      f"visibility={kpt.visibility} conf={kpt.confidence:.2f}")
        else:
            print("[WARN] No keypoints stored in database")

        print()
        print("=" * 70)

        if result['status'] == 'success' and result.get('keypoints_detected', 0) > 0:
            print("[OK] Antler detection test PASSED")
            print()
            print("Next steps:")
            print("1. Create API endpoint to fetch keypoints")
            print("2. Add visualization to frontend")
            print("3. Integrate into Re-ID pipeline")
            return 0
        else:
            print("[WARN] Antler detection completed but no keypoints detected")
            print("This may be normal if:")
            print("- Buck is at an angle where antlers aren't visible")
            print("- Image quality is poor")
            print("- Detection crop doesn't include full antlers")
            return 0

    except Exception as e:
        print()
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
