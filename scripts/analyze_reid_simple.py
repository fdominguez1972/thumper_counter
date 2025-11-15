#!/usr/bin/env python3
"""
Simplified Re-ID Performance Analysis

Analyzes current deer assignment patterns and provides threshold recommendations
based on the 9.5% assignment rate observed.

Feature 010 - Option D
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from datetime import datetime

# Database connection from environment
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "deertrack")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "secure_password_here")
DB_NAME = os.getenv("POSTGRES_DB", "deer_tracking")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def analyze_current_state(engine):
    """Analyze current Re-ID state."""
    print("[INFO] Analyzing current Re-ID assignment state...")

    queries = {
        'total_detections': "SELECT COUNT(*) FROM detections",
        'assigned_detections': "SELECT COUNT(*) FROM detections WHERE deer_id IS NOT NULL",
        'unique_deer': "SELECT COUNT(*) FROM deer",
        'detections_by_sex': """
            SELECT
                classification,
                COUNT(*) as count,
                COUNT(CASE WHEN deer_id IS NOT NULL THEN 1 END) as assigned,
                ROUND(100.0 * COUNT(CASE WHEN deer_id IS NOT NULL THEN 1 END) / COUNT(*), 1) as assignment_rate
            FROM detections
            WHERE classification IN ('buck', 'doe', 'fawn', 'mature', 'mid', 'young')
            GROUP BY classification
            ORDER BY count DESC
        """
    }

    results = {}
    with engine.connect() as conn:
        for key, query in queries.items():
            result = conn.execute(text(query))
            if key == 'detections_by_sex':
                results[key] = result.fetchall()
            else:
                results[key] = result.scalar()

    total = results['total_detections']
    assigned = results['assigned_detections']
    assignment_rate = (assigned / total * 100) if total > 0 else 0

    print(f"\n[OK] Current State:")
    print(f"  Total Detections: {total:,}")
    print(f"  Assigned to Deer: {assigned:,} ({assignment_rate:.1f}%)")
    print(f"  Unassigned: {total - assigned:,} ({100 - assignment_rate:.1f}%)")
    print(f"  Unique Deer Profiles: {results['unique_deer']}")

    print(f"\n[INFO] Assignment by Classification:")
    for row in results['detections_by_sex']:
        print(f"  {row[0]:10s}: {row[1]:6,} total, {row[2]:6,} assigned ({row[3]:5.1f}%)")

    return results


def generate_recommendations(results):
    """Generate threshold recommendations."""
    print("\n" + "=" * 80)
    print("ANALYSIS & RECOMMENDATIONS")
    print("=" * 80)

    total = results['total_detections']
    assigned = results['assigned_detections']
    unique_deer = results['unique_deer']
    assignment_rate = (assigned / total * 100) if total > 0 else 0

    print(f"\nCurrent Assignment Rate: {assignment_rate:.1f}%")
    print(f"Current REID_THRESHOLD: 0.70")

    print("\nDIAGNOSTICS:")

    # Calculate detections per deer
    avg_detections_per_deer = assigned / unique_deer if unique_deer > 0 else 0
    print(f"1. Average detections per deer: {avg_detections_per_deer:.1f}")

    if avg_detections_per_deer < 10:
        print("   [WARN] Low average suggests many single-detection deer profiles")
        print("   This could indicate:")
        print("   - Threshold too low (creating too many deer profiles)")
        print("   - Burst linking not working effectively")
        print("   - Feature extraction variability high")

    # Analyze unassigned rate
    if assignment_rate < 15:
        print(f"\n2. Low assignment rate ({assignment_rate:.1f}%) suggests:")
        print("   - REID_THRESHOLD (0.70) may be too conservative")
        print("   - Many detections not matching existing deer profiles")
        print("   - Consider lowering threshold to 0.65 or 0.60")

    # Check deer profile count
    expected_deer = total / 20  # Rough estimate: 20 sightings per deer
    if unique_deer > expected_deer * 2:
        print(f"\n3. High deer count ({unique_deer}) relative to detections suggests:")
        print("   - Threshold may be creating too many unique profiles")
        print("   - Consider INCREASING threshold to consolidate")
    elif unique_deer < expected_deer / 2:
        print(f"\n3. Low deer count ({unique_deer}) relative to detections suggests:")
        print("   - Good consolidation, threshold working well")

    print("\nRECOMMENDATIONS:")

    # Primary recommendation
    if assignment_rate < 15:
        print("\nPRIMARY: Lower REID_THRESHOLD to improve assignment rate")
        print("  Current: 0.70")
        print("  Recommended: 0.65")
        print("  Expected improvement: +5-10% assignment rate")
        print("  Rationale: Low assignment rate suggests threshold too conservative")
    elif assignment_rate > 50:
        print("\nPRIMARY: Current threshold appears optimal")
        print("  Assignment rate > 50% indicates good matching")
    else:
        print("\nPRIMARY: Threshold adjustment may help")
        print("  Current: 0.70")
        print("  Consider testing: 0.68 or 0.65")

    # Secondary recommendations
    print("\nSECONDARY RECOMMENDATIONS:")
    print("  1. Verify burst linking is working (check burst_group_id assignments)")
    print("  2. Review feature extraction quality (check feature vector consistency)")
    print("  3. Analyze sex-based filtering effectiveness")
    print("  4. Consider manual review of deer profiles with < 5 detections")

    print("\nNEXT STEPS:")
    print("  1. Update REID_THRESHOLD in .env file")
    print("  2. Test new threshold on sample batch (100-200 unassigned detections)")
    print("  3. Monitor assignment rate improvement")
    print("  4. Check for false positive increases")
    print("  5. Adjust threshold if needed based on results")


def save_report(results, output_path="reid_analysis_report_simple.txt"):
    """Save analysis report."""
    print(f"\n[INFO] Saving report to {output_path}...")

    total = results['total_detections']
    assigned = results['assigned_detections']
    unique_deer = results['unique_deer']
    assignment_rate = (assigned / total * 100) if total > 0 else 0

    with open(output_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("Re-ID Performance Analysis Report (Simplified)\n")
        f.write("Feature 010 - Option D\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        f.write("CURRENT STATE\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total Detections: {total:,}\n")
        f.write(f"Assigned to Deer: {assigned:,} ({assignment_rate:.1f}%)\n")
        f.write(f"Unassigned: {total - assigned:,} ({100 - assignment_rate:.1f}%)\n")
        f.write(f"Unique Deer Profiles: {unique_deer}\n")
        f.write(f"Average Detections per Deer: {assigned / unique_deer if unique_deer > 0 else 0:.1f}\n\n")

        f.write("ASSIGNMENT BY CLASSIFICATION\n")
        f.write("-" * 80 + "\n")
        for row in results['detections_by_sex']:
            f.write(f"{row[0]:10s}: {row[1]:6,} total, {row[2]:6,} assigned ({row[3]:5.1f}%)\n")

        f.write("\nCONCLUSIONS\n")
        f.write("-" * 80 + "\n")
        if assignment_rate < 15:
            f.write("Low assignment rate suggests REID_THRESHOLD (0.70) is too conservative.\n")
            f.write("RECOMMENDATION: Lower threshold to 0.65 and retest.\n")
        elif assignment_rate > 50:
            f.write("Assignment rate > 50% indicates good threshold performance.\n")
        else:
            f.write("Moderate assignment rate suggests threshold may need tuning.\n")

    print(f"[OK] Report saved to {output_path}")


def main():
    """Main analysis workflow."""
    print("=" * 80)
    print("Re-ID Performance Analysis - Feature 010 Option D (Simplified)")
    print("=" * 80)
    print()

    print("[INFO] Connecting to database...")
    engine = create_engine(DATABASE_URL)

    try:
        results = analyze_current_state(engine)
        generate_recommendations(results)
        save_report(results)

        print("\n" + "=" * 80)
        print("Analysis complete!")
        print("=" * 80)
        print(f"Report saved to: reid_analysis_report_simple.txt")
        print()

    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
