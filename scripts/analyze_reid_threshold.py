#!/usr/bin/env python3
"""
REID Threshold Optimization Analysis

This script analyzes the current deer profile distribution and detection assignments
to recommend an optimal REID_THRESHOLD value.

Usage:
    docker-compose exec backend python3 /app/scripts/analyze_reid_threshold.py
"""

import os
import sys
from sqlalchemy import create_engine, text
from collections import defaultdict
import statistics

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://deertrack:secure_password_here@db:5432/deer_tracking')
engine = create_engine(DATABASE_URL)

def analyze_deer_profiles():
    """Analyze deer profile distribution and assignment rates."""
    print("=" * 80)
    print("DEER PROFILE ANALYSIS")
    print("=" * 80)

    with engine.connect() as conn:
        # Total deer profiles
        result = conn.execute(text("""
            SELECT
                sex,
                COUNT(*) as profile_count,
                SUM(sighting_count) as total_sightings,
                AVG(sighting_count) as avg_sightings,
                MIN(sighting_count) as min_sightings,
                MAX(sighting_count) as max_sightings
            FROM deer
            GROUP BY sex
            ORDER BY profile_count DESC
        """))

        profiles = list(result)
        total_profiles = sum(p[1] for p in profiles)
        total_sightings = sum(p[2] for p in profiles)

        print(f"\nTotal Deer Profiles: {total_profiles}")
        print(f"Total Sightings: {total_sightings}")
        print(f"\nBy Sex:")
        print(f"  {'Sex':<10} {'Profiles':>10} {'Sightings':>12} {'Avg':>8} {'Min':>6} {'Max':>6}")
        print(f"  {'-'*10} {'-'*10} {'-'*12} {'-'*8} {'-'*6} {'-'*6}")

        for row in profiles:
            sex, count, sightings, avg, min_s, max_s = row
            print(f"  {sex:<10} {count:>10} {sightings:>12} {avg:>8.1f} {min_s:>6} {max_s:>6}")

    return total_profiles, total_sightings


def analyze_low_sighting_profiles():
    """Find deer profiles with very few sightings (likely false positives)."""
    print("\n" + "=" * 80)
    print("LOW SIGHTING PROFILES (Likely False Positives)")
    print("=" * 80)

    with engine.connect() as conn:
        # Profiles with 1-5 sightings
        for threshold in [1, 2, 3, 5, 10]:
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM deer
                WHERE sighting_count <= :threshold
            """), {"threshold": threshold})

            count = result.fetchone()[0]
            print(f"\nProfiles with <={threshold:2} sightings: {count:3} profiles")

        # Show sample of low-sighting profiles
        print("\nSample of profiles with <=5 sightings:")
        result = conn.execute(text("""
            SELECT id, name, sex, sighting_count, first_seen, last_seen
            FROM deer
            WHERE sighting_count <= 5
            ORDER BY sighting_count ASC, first_seen DESC
            LIMIT 20
        """))

        print(f"\n  {'ID':<36} {'Sex':<10} {'Sightings':>10} {'First Seen':<20} {'Last Seen':<20}")
        print(f"  {'-'*36} {'-'*10} {'-'*10} {'-'*20} {'-'*20}")

        for row in result:
            deer_id, name, sex, sightings, first_seen, last_seen = row
            name_display = name if name else str(deer_id)[:8]
            print(f"  {deer_id} {sex:<10} {sightings:>10} {str(first_seen):<20} {str(last_seen):<20}")


def analyze_detection_assignment():
    """Analyze how many detections are assigned vs unassigned."""
    print("\n" + "=" * 80)
    print("DETECTION ASSIGNMENT ANALYSIS")
    print("=" * 80)

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(deer_id) as assigned,
                COUNT(*) - COUNT(deer_id) as unassigned
            FROM detections
            WHERE classification IN ('buck', 'doe', 'fawn', 'mature', 'mid', 'young')
        """))

        row = result.fetchone()
        total, assigned, unassigned = row

        print(f"\nTotal Detections: {total:,}")
        print(f"Assigned to Deer: {assigned:,} ({assigned/total*100:.1f}%)")
        print(f"Unassigned:       {unassigned:,} ({unassigned/total*100:.1f}%)")

        # Assignment rate by classification
        print("\nAssignment Rate by Classification:")
        result = conn.execute(text("""
            SELECT
                classification,
                COUNT(*) as total,
                COUNT(deer_id) as assigned,
                CAST(COUNT(deer_id) * 100.0 / COUNT(*) AS DECIMAL(5,1)) as assignment_rate
            FROM detections
            WHERE classification IN ('buck', 'doe', 'fawn', 'mature', 'mid', 'young')
            GROUP BY classification
            ORDER BY total DESC
        """))

        print(f"\n  {'Classification':<15} {'Total':>10} {'Assigned':>10} {'Rate':>8}")
        print(f"  {'-'*15} {'-'*10} {'-'*10} {'-'*8}")

        for row in result:
            classification, total, assigned, rate = row
            print(f"  {classification:<15} {total:>10,} {assigned:>10,} {rate:>7}%")


def estimate_optimal_profiles():
    """Estimate how many profiles we should have based on detection patterns."""
    print("\n" + "=" * 80)
    print("OPTIMAL PROFILE ESTIMATION")
    print("=" * 80)

    with engine.connect() as conn:
        # Get image count and detection count
        result = conn.execute(text("""
            SELECT
                COUNT(DISTINCT i.id) as image_count,
                COUNT(d.id) as detection_count,
                COUNT(DISTINCT d.deer_id) as current_profiles
            FROM images i
            LEFT JOIN detections d ON d.image_id = i.id
            WHERE i.processing_status = 'completed'
                AND d.classification IN ('buck', 'doe', 'fawn', 'mature', 'mid', 'young')
        """))

        row = result.fetchone()
        image_count, detection_count, current_profiles = row

        print(f"\nCurrent State:")
        print(f"  Completed Images: {image_count:,}")
        print(f"  Deer Detections:  {detection_count:,}")
        print(f"  Deer Profiles:    {current_profiles:,}")
        print(f"  Detections/Image: {detection_count/image_count:.2f}")
        print(f"  Detections/Profile: {detection_count/current_profiles:.1f}")

        # Estimate realistic profile count based on trail camera best practices
        print(f"\nEstimated Optimal Profiles:")
        print(f"  Conservative (1 per 1000 images): {image_count // 1000}")
        print(f"  Moderate (1 per 500 images):      {image_count // 500}")
        print(f"  Aggressive (1 per 250 images):    {image_count // 250}")
        print(f"\n  Target Range: 30-100 profiles for {image_count:,} images")
        print(f"  Current:      {current_profiles} profiles")

        if current_profiles > 100:
            print(f"\n  [RECOMMENDATION] Reduce by {current_profiles - 50} profiles")
            print(f"  This indicates REID_THRESHOLD is too conservative")
        elif current_profiles < 30:
            print(f"\n  [RECOMMENDATION] Increase by {50 - current_profiles} profiles")
            print(f"  This indicates REID_THRESHOLD may be too aggressive")
        else:
            print(f"\n  [OK] Profile count is within acceptable range")


def analyze_similarity_scores():
    """
    Analyze similarity scores from re-ID matches.
    Note: This requires the similarity_score column to exist in detections table.
    """
    print("\n" + "=" * 80)
    print("SIMILARITY SCORE ANALYSIS")
    print("=" * 80)

    with engine.connect() as conn:
        # Check if similarity_score column exists
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'detections'
                AND column_name = 'similarity_score'
        """))

        if not result.fetchone():
            print("\n[INFO] similarity_score column not found in detections table")
            print("Cannot analyze actual similarity scores without logging them.")
            print("\nRECOMMENDATION: Add similarity_score logging to re-ID task:")
            print("  1. Add 'similarity_score' column to detections table")
            print("  2. Log score when deer_id is assigned in reidentification.py")
            print("  3. Reprocess subset to gather score distribution data")
            return

        # Analyze similarity scores
        result = conn.execute(text("""
            SELECT
                COUNT(*) as count,
                MIN(similarity_score) as min_score,
                MAX(similarity_score) as max_score,
                AVG(similarity_score) as avg_score,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY similarity_score) as p25,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY similarity_score) as p50,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY similarity_score) as p75,
                PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY similarity_score) as p90,
                PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY similarity_score) as p95
            FROM detections
            WHERE similarity_score IS NOT NULL
        """))

        row = result.fetchone()
        if row and row[0] > 0:
            count, min_s, max_s, avg_s, p25, p50, p75, p90, p95 = row

            print(f"\nSimilarity Score Distribution ({count:,} detections with scores):")
            print(f"  Min:  {min_s:.4f}")
            print(f"  P25:  {p25:.4f}")
            print(f"  P50:  {p50:.4f}")
            print(f"  P75:  {p75:.4f}")
            print(f"  P90:  {p90:.4f}")
            print(f"  P95:  {p95:.4f}")
            print(f"  Max:  {max_s:.4f}")
            print(f"  Avg:  {avg_s:.4f}")

            # Score distribution by threshold
            print(f"\nDetections by Threshold:")
            for threshold in [0.45, 0.50, 0.55, 0.60, 0.65, 0.70]:
                result = conn.execute(text("""
                    SELECT COUNT(*)
                    FROM detections
                    WHERE similarity_score >= :threshold
                """), {"threshold": threshold})
                count = result.fetchone()[0]
                print(f"  >={threshold:.2f}: {count:6,} detections")
        else:
            print("\n[INFO] No similarity scores found in database")


def recommend_threshold():
    """Provide threshold recommendations based on analysis."""
    print("\n" + "=" * 80)
    print("THRESHOLD RECOMMENDATIONS")
    print("=" * 80)

    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM deer
        """))
        current_profiles = result.fetchone()[0]

        result = conn.execute(text("""
            SELECT COUNT(*) FROM images WHERE processing_status = 'completed'
        """))
        completed_images = result.fetchone()[0]

        current_threshold = float(os.getenv('REID_THRESHOLD', '0.60'))

        print(f"\nCurrent Configuration:")
        print(f"  REID_THRESHOLD: {current_threshold}")
        print(f"  Deer Profiles:  {current_profiles}")
        print(f"  Target Profiles: 30-50")
        print(f"  Completed Images: {completed_images:,}")

        # Calculate profile creation rate
        profile_rate = current_profiles / completed_images * 1000
        print(f"\n  Profile Creation Rate: {profile_rate:.2f} profiles per 1,000 images")

        # Expected rate for mature system
        expected_rate = 0.10  # 1 profile per 1000 images
        print(f"  Expected Rate (mature): {expected_rate:.2f} profiles per 1,000 images")

        if profile_rate > expected_rate * 2:
            print(f"\n  [ISSUE] Creating profiles {profile_rate/expected_rate:.1f}x faster than expected")
            print(f"  This indicates threshold is TOO CONSERVATIVE")

            # Recommend lowering threshold
            if current_threshold >= 0.65:
                recommended = 0.55
            elif current_threshold >= 0.60:
                recommended = 0.50
            elif current_threshold >= 0.55:
                recommended = 0.45
            else:
                recommended = current_threshold - 0.05

            print(f"\n  RECOMMENDATION:")
            print(f"    1. Lower REID_THRESHOLD from {current_threshold} to {recommended}")
            print(f"    2. Reset deer_id assignments for all detections")
            print(f"    3. Reprocess all completed images")
            print(f"    4. Monitor resulting profile count (target: 30-50)")

            print(f"\n  To apply:")
            print(f"    # Edit .env file")
            print(f"    REID_THRESHOLD={recommended}")
            print(f"    ")
            print(f"    # Restart worker")
            print(f"    docker-compose restart worker")
            print(f"    ")
            print(f"    # Reset and reprocess")
            print(f"    bash scripts/reprocess_all_images.sh")

        elif profile_rate < expected_rate * 0.5:
            print(f"\n  [ISSUE] Creating profiles {expected_rate/profile_rate:.1f}x slower than expected")
            print(f"  This indicates threshold may be TOO AGGRESSIVE")
            print(f"\n  RECOMMENDATION: Raise REID_THRESHOLD by 0.05")

        else:
            print(f"\n  [OK] Profile creation rate is acceptable")


def main():
    """Run all analyses."""
    try:
        print("\nREID THRESHOLD OPTIMIZATION ANALYSIS")
        print("Generated:", sys.argv[0] if len(sys.argv) > 0 else __file__)
        print()

        # Run analyses
        analyze_deer_profiles()
        analyze_low_sighting_profiles()
        analyze_detection_assignment()
        estimate_optimal_profiles()
        analyze_similarity_scores()
        recommend_threshold()

        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE")
        print("=" * 80)
        print()

    except Exception as e:
        print(f"\n[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
