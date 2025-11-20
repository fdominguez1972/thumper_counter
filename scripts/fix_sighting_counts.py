#!/usr/bin/env python3
"""
Fix Sighting Counts - Recalculate correct sighting_count for all deer

Problem: sighting_count doesn't match actual detections because update_sighting()
         isn't called when detections are linked via burst companions.

Solution: Recalculate sighting_count as:
          - Number of unique burst_group_ids (one sighting per burst)
          - For detections without burst_group_id, count each as 1 sighting

Usage:
    python3 scripts/fix_sighting_counts.py [--dry-run]
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from backend.core.database import get_db
from backend.models import Deer, Detection
from sqlalchemy import func, distinct
import argparse


def analyze_sighting_counts(db):
    """
    Analyze all deer and compare stored vs calculated sighting counts.

    Returns dict with statistics and deer needing fixes.
    """
    print("[INFO] Analyzing all deer sighting counts...")

    deer_list = db.query(Deer).all()

    results = {
        'total_deer': len(deer_list),
        'correct_count': 0,
        'incorrect_count': 0,
        'deer_to_fix': []
    }

    for deer in deer_list:
        # Calculate correct sighting count
        # Count unique burst_group_ids + detections without burst_group_id
        burst_count = db.query(func.count(distinct(Detection.burst_group_id))).\
            filter(Detection.deer_id == deer.id).\
            filter(Detection.burst_group_id != None).\
            scalar() or 0

        non_burst_count = db.query(func.count(Detection.id)).\
            filter(Detection.deer_id == deer.id).\
            filter(Detection.burst_group_id == None).\
            scalar() or 0

        correct_count = burst_count + non_burst_count
        stored_count = deer.sighting_count

        if correct_count != stored_count:
            results['incorrect_count'] += 1
            results['deer_to_fix'].append({
                'deer_id': deer.id,
                'sex': deer.sex.value,
                'stored_count': stored_count,
                'correct_count': correct_count,
                'difference': correct_count - stored_count,
                'burst_groups': burst_count,
                'non_burst_detections': non_burst_count
            })
        else:
            results['correct_count'] += 1

    return results


def fix_sighting_counts(db, deer_to_fix, dry_run=False):
    """
    Fix sighting counts for all deer with incorrect counts.

    Args:
        db: Database session
        deer_to_fix: List of deer data from analyze_sighting_counts()
        dry_run: If True, don't actually update database

    Returns:
        List of changes made
    """
    changes = []

    print(f"\n[INFO] Fixing {len(deer_to_fix)} deer sighting counts...")

    for deer_data in deer_to_fix:
        deer_id = deer_data['deer_id']
        old_count = deer_data['stored_count']
        new_count = deer_data['correct_count']
        difference = deer_data['difference']

        print(f"  [FIX] {deer_id}: {old_count} -> {new_count} ({difference:+d})")

        if not dry_run:
            deer = db.query(Deer).filter(Deer.id == deer_id).first()
            deer.sighting_count = new_count

        changes.append({
            'deer_id': str(deer_id),
            'old_count': old_count,
            'new_count': new_count,
            'difference': difference
        })

    if not dry_run:
        db.commit()
        print(f"\n[OK] Updated {len(changes)} deer sighting counts")
    else:
        print(f"\n[DRY RUN] Would update {len(changes)} deer sighting counts")

    return changes


def main():
    parser = argparse.ArgumentParser(description='Fix sighting counts for all deer')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying them')
    args = parser.parse_args()

    print("=" * 70)
    print("SIGHTING COUNT FIX")
    print("=" * 70)
    print()

    if args.dry_run:
        print("[DRY RUN MODE] No changes will be made")
        print()

    db = next(get_db())

    try:
        # Analyze all deer
        analysis = analyze_sighting_counts(db)

        print("\n" + "=" * 70)
        print("ANALYSIS RESULTS")
        print("=" * 70)
        print(f"Total deer: {analysis['total_deer']}")
        print(f"Correct counts: {analysis['correct_count']}")
        print(f"Incorrect counts: {analysis['incorrect_count']}")
        print()

        if analysis['incorrect_count'] == 0:
            print("[OK] All sighting counts are correct!")
            return 0

        # Show top 10 deer with largest discrepancies
        print("\nTOP 10 DEER WITH LARGEST DISCREPANCIES:")
        sorted_deer = sorted(analysis['deer_to_fix'], key=lambda x: abs(x['difference']), reverse=True)
        for deer in sorted_deer[:10]:
            print(f"  - {deer['deer_id']}: {deer['stored_count']} -> {deer['correct_count']} ({deer['difference']:+d})")
            print(f"    Burst groups: {deer['burst_groups']}, Non-burst: {deer['non_burst_detections']}")

        if len(sorted_deer) > 10:
            print(f"  ... and {len(sorted_deer) - 10} more")

        # Fix counts
        changes = fix_sighting_counts(db, analysis['deer_to_fix'], dry_run=args.dry_run)

        # Summary
        print("\n" + "=" * 70)
        print("FIX SUMMARY")
        print("=" * 70)
        total_diff = sum(c['difference'] for c in changes)
        print(f"Deer updated: {len(changes)}")
        print(f"Total count adjustment: {total_diff:+d}")
        print(f"Average adjustment per deer: {total_diff/len(changes):+.1f}")
        print()

        if args.dry_run:
            print("[DRY RUN] No changes were actually made")
        else:
            print("[OK] Fix complete!")

        return 0

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
