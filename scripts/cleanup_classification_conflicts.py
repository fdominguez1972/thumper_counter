#!/usr/bin/env python3
"""
Cleanup Script: Fix Sex Classification Conflicts in Re-ID Data

Purpose: Fix deer profiles with mismatched sex classifications due to
         Re-ID bug that ignored manual classification corrections.

Date: November 19, 2025
Bug: Re-ID used detection.classification instead of corrected_classification

Actions:
1. Fix CRITICAL cases: Update deer.sex for profiles that are clearly wrong
2. Reassign detections: Move wrong-sex detections to correct profiles
3. Generate report: Document all changes made

Usage:
    python3 scripts/cleanup_classification_conflicts.py [--dry-run] [--auto]

Options:
    --dry-run    Show what would be changed without making changes
    --auto       Automatically fix all cases without prompts
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Tuple
from uuid import UUID

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from backend.core.database import get_db
from backend.models import Deer, Detection, DeerSex
from sqlalchemy import func

import argparse


def get_final_classification(detection: Detection) -> str:
    """Get the final classification (corrected if available, else ML)."""
    return (
        detection.corrected_classification
        if detection.corrected_classification
        else detection.classification
    )


def analyze_deer_classifications(db) -> Dict:
    """
    Analyze all deer profiles and identify sex conflicts.

    Returns dict with:
    - critical_cases: Deer where profile sex is clearly wrong
    - moderate_cases: Deer with >10% wrong-sex detections
    - minor_cases: Deer with <10% wrong-sex detections
    """
    results = {
        'critical_cases': [],
        'moderate_cases': [],
        'minor_cases': [],
        'stats': {}
    }

    print("[INFO] Analyzing all deer profiles...")

    deer_list = db.query(Deer).all()

    for deer in deer_list:
        detections = db.query(Detection).filter(Detection.deer_id == deer.id).all()

        if not detections:
            continue

        # Count classifications
        buck_count = 0
        doe_count = 0
        fawn_count = 0
        other_count = 0

        for det in detections:
            final_class = get_final_classification(det)
            if final_class == 'buck':
                buck_count += 1
            elif final_class == 'doe':
                doe_count += 1
            elif final_class == 'fawn':
                fawn_count += 1
            else:
                other_count += 1

        total = len(detections)

        # Check for conflicts
        has_conflict = False
        severity = None
        issue = None

        if deer.sex == DeerSex.BUCK:
            if doe_count > buck_count:
                # CRITICAL: Buck profile but mostly does
                severity = 'CRITICAL'
                issue = f"Buck profile but {doe_count}/{total} are does ({doe_count*100//total}%)"
                has_conflict = True
            elif doe_count > 0 and doe_count / total > 0.1:
                # MODERATE: >10% does
                severity = 'MODERATE'
                issue = f"Buck profile with {doe_count}/{total} does ({doe_count*100//total}%)"
                has_conflict = True
            elif doe_count > 0:
                # MINOR: <10% does
                severity = 'MINOR'
                issue = f"Buck profile with {doe_count}/{total} does ({doe_count*100//total}%)"
                has_conflict = True

        elif deer.sex == DeerSex.DOE:
            if buck_count > doe_count:
                # CRITICAL: Doe profile but mostly bucks
                severity = 'CRITICAL'
                issue = f"Doe profile but {buck_count}/{total} are bucks ({buck_count*100//total}%)"
                has_conflict = True
            elif buck_count > 0 and buck_count / total > 0.1:
                # MODERATE: >10% bucks
                severity = 'MODERATE'
                issue = f"Doe profile with {buck_count}/{total} bucks ({buck_count*100//total}%)"
                has_conflict = True
            elif buck_count > 0:
                # MINOR: <10% bucks
                severity = 'MINOR'
                issue = f"Doe profile with {buck_count}/{total} bucks ({buck_count*100//total}%)"
                has_conflict = True

        if has_conflict:
            deer_data = {
                'deer_id': deer.id,
                'deer_sex': deer.sex,
                'sighting_count': total,
                'buck_count': buck_count,
                'doe_count': doe_count,
                'fawn_count': fawn_count,
                'other_count': other_count,
                'issue': issue
            }

            if severity == 'CRITICAL':
                results['critical_cases'].append(deer_data)
            elif severity == 'MODERATE':
                results['moderate_cases'].append(deer_data)
            else:
                results['minor_cases'].append(deer_data)

    results['stats'] = {
        'total_deer': len(deer_list),
        'critical_count': len(results['critical_cases']),
        'moderate_count': len(results['moderate_cases']),
        'minor_count': len(results['minor_cases']),
        'total_conflicts': len(results['critical_cases']) + len(results['moderate_cases']) + len(results['minor_cases'])
    }

    return results


def fix_critical_cases(db, critical_cases: List[Dict], dry_run: bool = False) -> List[Dict]:
    """
    Fix CRITICAL cases by updating deer.sex to match majority classification.

    Returns list of changes made.
    """
    changes = []

    print(f"\n[INFO] Processing {len(critical_cases)} CRITICAL cases...")

    for case in critical_cases:
        deer_id = case['deer_id']
        current_sex = case['deer_sex']
        buck_count = case['buck_count']
        doe_count = case['doe_count']

        # Determine correct sex based on majority
        if buck_count > doe_count:
            correct_sex = DeerSex.BUCK
        elif doe_count > buck_count:
            correct_sex = DeerSex.DOE
        else:
            # Equal - can't determine, skip
            print(f"  [SKIP] {deer_id}: Equal buck/doe count, cannot determine correct sex")
            continue

        if correct_sex != current_sex:
            print(f"  [FIX] {deer_id}: {current_sex.value} -> {correct_sex.value} ({case['issue']})")

            if not dry_run:
                deer = db.query(Deer).filter(Deer.id == deer_id).first()
                deer.sex = correct_sex
                db.commit()

            changes.append({
                'deer_id': str(deer_id),
                'action': 'update_sex',
                'from': current_sex.value,
                'to': correct_sex.value,
                'reason': case['issue']
            })

    return changes


def reassign_wrong_sex_detections(db, cases: List[Dict], dry_run: bool = False) -> List[Dict]:
    """
    Reassign wrong-sex detections to NULL (for re-processing by Re-ID).

    Only reassigns minority-sex detections (<50% of total).
    """
    changes = []

    print(f"\n[INFO] Processing wrong-sex detections in {len(cases)} profiles...")

    for case in cases:
        deer_id = case['deer_id']
        deer_sex = case['deer_sex']
        buck_count = case['buck_count']
        doe_count = case['doe_count']
        total = case['sighting_count']

        # Determine which detections to reassign (minority sex)
        if deer_sex == DeerSex.BUCK and doe_count > 0 and buck_count >= doe_count:
            # Buck profile - reassign does
            wrong_sex = 'doe'
            wrong_count = doe_count
        elif deer_sex == DeerSex.DOE and buck_count > 0 and doe_count >= buck_count:
            # Doe profile - reassign bucks
            wrong_sex = 'buck'
            wrong_count = buck_count
        else:
            # Skip if majority is wrong (should be fixed by fix_critical_cases first)
            continue

        print(f"  [INFO] {deer_id}: Reassigning {wrong_count} {wrong_sex} detections...")

        # Get wrong-sex detections
        detections = db.query(Detection).filter(Detection.deer_id == deer_id).all()
        reassigned = 0

        for det in detections:
            final_class = get_final_classification(det)
            if final_class == wrong_sex:
                if not dry_run:
                    det.deer_id = None  # Unassign - will be re-processed
                reassigned += 1

        if not dry_run:
            # Update deer sighting count
            deer = db.query(Deer).filter(Deer.id == deer_id).first()
            deer.sighting_count = total - reassigned
            db.commit()

        print(f"  [OK] Reassigned {reassigned} detections from {deer_id}")

        changes.append({
            'deer_id': str(deer_id),
            'action': 'reassign_detections',
            'count': reassigned,
            'classification': wrong_sex,
            'reason': f"Wrong sex for {deer_sex.value} profile"
        })

    return changes


def main():
    parser = argparse.ArgumentParser(description='Fix sex classification conflicts in Re-ID data')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without applying them')
    parser.add_argument('--auto', action='store_true', help='Automatically fix all cases')
    args = parser.parse_args()

    print("=" * 70)
    print("CLASSIFICATION CONFLICT CLEANUP")
    print("=" * 70)
    print()

    if args.dry_run:
        print("[DRY RUN MODE] No changes will be made")
        print()

    db = next(get_db())

    try:
        # Analyze all deer profiles
        analysis = analyze_deer_classifications(db)

        print("\n" + "=" * 70)
        print("ANALYSIS RESULTS")
        print("=" * 70)
        print(f"Total deer profiles: {analysis['stats']['total_deer']}")
        print(f"Profiles with conflicts: {analysis['stats']['total_conflicts']}")
        print(f"  - CRITICAL: {analysis['stats']['critical_count']}")
        print(f"  - MODERATE: {analysis['stats']['moderate_count']}")
        print(f"  - MINOR: {analysis['stats']['minor_count']}")
        print()

        if analysis['stats']['total_conflicts'] == 0:
            print("[OK] No conflicts found! Data is clean.")
            return 0

        # Show critical cases
        if analysis['critical_cases']:
            print("\nCRITICAL CASES:")
            for case in analysis['critical_cases']:
                print(f"  - {case['deer_id']}: {case['issue']}")

        # Show moderate cases
        if analysis['moderate_cases']:
            print("\nMODERATE CASES:")
            for case in analysis['moderate_cases'][:5]:  # Show first 5
                print(f"  - {case['deer_id']}: {case['issue']}")
            if len(analysis['moderate_cases']) > 5:
                print(f"  ... and {len(analysis['moderate_cases']) - 5} more")

        # Confirm before proceeding
        if not args.auto and not args.dry_run:
            print()
            response = input("Proceed with fixes? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("[INFO] Cancelled by user")
                return 0

        all_changes = []

        # Fix critical cases (update deer.sex)
        if analysis['critical_cases']:
            critical_changes = fix_critical_cases(db, analysis['critical_cases'], dry_run=args.dry_run)
            all_changes.extend(critical_changes)

        # Reassign wrong-sex detections for moderate/minor cases
        all_cases = analysis['moderate_cases'] + analysis['minor_cases']
        if all_cases:
            reassign_changes = reassign_wrong_sex_detections(db, all_cases, dry_run=args.dry_run)
            all_changes.extend(reassign_changes)

        # Summary
        print("\n" + "=" * 70)
        print("CLEANUP SUMMARY")
        print("=" * 70)
        print(f"Total changes: {len(all_changes)}")
        print(f"  - Deer sex updated: {sum(1 for c in all_changes if c['action'] == 'update_sex')}")
        print(f"  - Detections reassigned: {sum(c.get('count', 0) for c in all_changes if c['action'] == 'reassign_detections')}")
        print()

        if args.dry_run:
            print("[DRY RUN] No changes were actually made")
        else:
            print("[OK] Cleanup complete!")
            print()
            print("NEXT STEPS:")
            print("1. Restart worker: docker-compose restart worker")
            print("2. Reprocess unassigned detections: curl -X POST http://localhost:8001/api/processing/reprocess_reid")
            print("3. Verify results in frontend")

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
