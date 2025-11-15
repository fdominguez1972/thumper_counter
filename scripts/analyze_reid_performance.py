#!/usr/bin/env python3
"""
Re-ID Performance Analysis Script

Analyzes similarity score distribution and provides threshold recommendations
to improve deer assignment rate from current 9.5%.

Implements FR-014 through FR-019 for Feature 010 Option D.

Usage:
    python3 scripts/analyze_reid_performance.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd


# Database connection from environment (Docker defaults)
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "deertrack")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "secure_password_here")
DB_NAME = os.getenv("POSTGRES_DB", "deer_tracking")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_similarity_scores(engine):
    """
    Query all similarity scores from re-identification matching.

    FR-014: System MUST provide analysis script to query all similarity scores.

    Returns:
        DataFrame with columns: detection_id, deer_id, similarity_score, sex_match
    """
    print("[INFO] Querying similarity scores from database...")

    query = text("""
        SELECT
            d.id as detection_id,
            d.deer_id,
            d.classification,
            deer.sex,
            -- Calculate cosine similarity from stored feature vectors
            1 - (d.feature_vector <=> deer.feature_vector) as similarity_score
        FROM detections d
        INNER JOIN deer ON deer.id = d.deer_id
        WHERE d.feature_vector IS NOT NULL
          AND deer.feature_vector IS NOT NULL
          AND d.deer_id IS NOT NULL
        ORDER BY similarity_score DESC
    """)

    with engine.connect() as conn:
        result = conn.execute(query)
        data = result.fetchall()

    if not data:
        print("[WARN] No similarity scores found - no detections have been assigned")
        return pd.DataFrame(columns=['detection_id', 'deer_id', 'classification', 'sex', 'similarity_score'])

    df = pd.DataFrame(data, columns=['detection_id', 'deer_id', 'classification', 'sex', 'similarity_score'])
    print(f"[OK] Found {len(df)} detection-deer pairs with similarity scores")

    return df


def generate_histogram(scores_df, output_path="reid_similarity_histogram.png"):
    """
    Generate histogram visualization of similarity score distribution.

    FR-015: Analysis script MUST generate histogram visualization.

    Args:
        scores_df: DataFrame with similarity_score column
        output_path: Path to save histogram image
    """
    print(f"[INFO] Generating similarity score histogram...")

    if scores_df.empty:
        print("[WARN] No data to visualize")
        return

    scores = scores_df['similarity_score'].values

    # Create figure with multiple views
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Re-ID Similarity Score Distribution Analysis', fontsize=16, fontweight='bold')

    # 1. Histogram with KDE
    ax1 = axes[0, 0]
    ax1.hist(scores, bins=50, alpha=0.7, color='steelblue', edgecolor='black')
    ax1.axvline(0.70, color='red', linestyle='--', linewidth=2, label='Current Threshold (0.70)')
    ax1.set_xlabel('Similarity Score')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Similarity Score Distribution (Histogram)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. KDE Plot
    ax2 = axes[0, 1]
    sns.kdeplot(scores, ax=ax2, fill=True, color='steelblue')
    ax2.axvline(0.70, color='red', linestyle='--', linewidth=2, label='Current Threshold (0.70)')
    ax2.set_xlabel('Similarity Score')
    ax2.set_ylabel('Density')
    ax2.set_title('Similarity Score Density (KDE)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. Cumulative Distribution
    ax3 = axes[1, 0]
    sorted_scores = np.sort(scores)
    cumulative = np.arange(1, len(sorted_scores) + 1) / len(sorted_scores) * 100
    ax3.plot(sorted_scores, cumulative, linewidth=2, color='steelblue')
    ax3.axvline(0.70, color='red', linestyle='--', linewidth=2, label='Current Threshold (0.70)')
    ax3.set_xlabel('Similarity Score')
    ax3.set_ylabel('Cumulative Percentage')
    ax3.set_title('Cumulative Distribution')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 4. Box Plot
    ax4 = axes[1, 1]
    ax4.boxplot(scores, vert=False, widths=0.5, patch_artist=True,
                boxprops=dict(facecolor='steelblue', alpha=0.7),
                medianprops=dict(color='red', linewidth=2))
    ax4.axvline(0.70, color='red', linestyle='--', linewidth=2, label='Current Threshold (0.70)')
    ax4.set_xlabel('Similarity Score')
    ax4.set_title('Similarity Score Box Plot')
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved histogram to {output_path}")

    return output_path


def calculate_assignment_rates(engine, thresholds=[0.70, 0.65, 0.60, 0.55]):
    """
    Calculate assignment rate for multiple threshold values.

    FR-016: Analysis script MUST calculate assignment rate for multiple threshold values.

    Args:
        engine: SQLAlchemy engine
        thresholds: List of threshold values to test

    Returns:
        DataFrame with threshold analysis results
    """
    print(f"[INFO] Calculating assignment rates for thresholds: {thresholds}")

    # Get total detections
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM detections WHERE feature_vector IS NOT NULL"))
        total_detections = result.scalar()

        result = conn.execute(text("SELECT COUNT(*) FROM detections WHERE deer_id IS NOT NULL"))
        current_assigned = result.scalar()

    print(f"[INFO] Total detections with feature vectors: {total_detections}")
    print(f"[INFO] Currently assigned (threshold 0.70): {current_assigned}")
    print(f"[INFO] Current assignment rate: {current_assigned / total_detections * 100:.1f}%")

    results = []

    for threshold in thresholds:
        # Count potential matches at this threshold
        query = text("""
            WITH potential_matches AS (
                SELECT
                    d.id as detection_id,
                    deer.id as deer_id,
                    1 - (d.feature_vector <=> deer.feature_vector) as similarity_score,
                    d.classification,
                    deer.sex
                FROM detections d
                CROSS JOIN deer
                WHERE d.feature_vector IS NOT NULL
                  AND deer.feature_vector IS NOT NULL
                  AND d.deer_id IS NULL
                  -- Sex-based filtering
                  AND (
                      (d.classification = 'doe' AND deer.sex = 'doe')
                      OR (d.classification IN ('buck', 'mature', 'mid', 'young') AND deer.sex = 'buck')
                      OR (d.classification = 'fawn' AND deer.sex = 'fawn')
                      OR (d.classification = 'unknown')
                  )
            ),
            best_matches AS (
                SELECT
                    detection_id,
                    MAX(similarity_score) as best_score
                FROM potential_matches
                WHERE similarity_score >= :threshold
                GROUP BY detection_id
            )
            SELECT COUNT(*) as potential_assignments
            FROM best_matches
        """)

        with engine.connect() as conn:
            result = conn.execute(query, {"threshold": threshold})
            potential_assignments = result.scalar() or 0

        total_assignable = current_assigned + potential_assignments
        assignment_rate = (total_assignable / total_detections * 100) if total_detections > 0 else 0
        improvement = assignment_rate - (current_assigned / total_detections * 100)

        results.append({
            'threshold': threshold,
            'current_assigned': current_assigned,
            'potential_new': potential_assignments,
            'total_assigned': total_assignable,
            'assignment_rate_pct': assignment_rate,
            'improvement_pct': improvement
        })

        print(f"[OK] Threshold {threshold:.2f}: {total_assignable} assignments ({assignment_rate:.1f}%), +{improvement:.1f}% improvement")

    return pd.DataFrame(results)


def identify_clustering(scores_df):
    """
    Identify natural clustering in similarity scores.

    FR-017: Analysis script MUST identify natural clustering in similarity scores.

    Args:
        scores_df: DataFrame with similarity_score column

    Returns:
        Dict with clustering analysis results
    """
    print("[INFO] Analyzing natural clustering patterns...")

    if scores_df.empty:
        print("[WARN] No data for clustering analysis")
        return {}

    scores = scores_df['similarity_score'].values

    # Calculate statistics
    stats = {
        'mean': np.mean(scores),
        'median': np.median(scores),
        'std': np.std(scores),
        'min': np.min(scores),
        'max': np.max(scores),
        'q25': np.percentile(scores, 25),
        'q75': np.percentile(scores, 75)
    }

    # Identify natural breaks (gaps in distribution)
    sorted_scores = np.sort(scores)
    gaps = np.diff(sorted_scores)
    large_gaps = gaps[gaps > np.percentile(gaps, 90)]

    print(f"[INFO] Score statistics:")
    print(f"  Mean: {stats['mean']:.3f}")
    print(f"  Median: {stats['median']:.3f}")
    print(f"  Std Dev: {stats['std']:.3f}")
    print(f"  Range: [{stats['min']:.3f}, {stats['max']:.3f}]")
    print(f"  IQR: [{stats['q25']:.3f}, {stats['q75']:.3f}]")

    if len(large_gaps) > 0:
        print(f"[INFO] Found {len(large_gaps)} large gaps in distribution")
        print(f"  Gap size threshold: {np.percentile(gaps, 90):.3f}")
    else:
        print("[INFO] No significant clustering gaps detected")

    return stats


def recommend_threshold(scores_df, rates_df):
    """
    Recommend optimal threshold based on data analysis.

    FR-018: Analysis script MUST recommend optimal threshold based on data analysis.

    Args:
        scores_df: DataFrame with similarity scores
        rates_df: DataFrame with threshold analysis

    Returns:
        Dict with recommendation and rationale
    """
    print("[INFO] Generating threshold recommendation...")

    if rates_df.empty:
        print("[WARN] No threshold data for recommendation")
        return {}

    # Find threshold with best balance of improvement and safety
    # Prefer threshold that improves assignment rate by at least 20%
    # while staying above 0.55 (reasonable similarity floor)

    target_improvement = 20.0  # 20% improvement from 9.5% baseline

    viable = rates_df[rates_df['improvement_pct'] >= target_improvement]

    if viable.empty:
        # No threshold meets target, recommend best available
        best_idx = rates_df['improvement_pct'].idxmax()
        recommended = rates_df.loc[best_idx]
        rationale = f"No threshold achieves {target_improvement}% improvement. Best available: {recommended['threshold']:.2f}"
    else:
        # Recommend highest threshold that meets target (most conservative)
        best_idx = viable['threshold'].idxmax()
        recommended = viable.loc[best_idx]
        rationale = f"Threshold {recommended['threshold']:.2f} achieves target {target_improvement}% improvement while maintaining high confidence"

    recommendation = {
        'recommended_threshold': recommended['threshold'],
        'expected_assignment_rate': recommended['assignment_rate_pct'],
        'expected_improvement': recommended['improvement_pct'],
        'potential_new_assignments': recommended['potential_new'],
        'rationale': rationale
    }

    print(f"[OK] Recommended threshold: {recommendation['recommended_threshold']:.2f}")
    print(f"     Expected assignment rate: {recommendation['expected_assignment_rate']:.1f}%")
    print(f"     Expected improvement: +{recommendation['expected_improvement']:.1f}%")
    print(f"     Potential new assignments: {recommendation['potential_new_assignments']}")
    print(f"     Rationale: {recommendation['rationale']}")

    return recommendation


def save_report(scores_df, rates_df, stats, recommendation, output_path="reid_analysis_report.txt"):
    """
    Save comprehensive analysis report to text file.

    Args:
        scores_df: DataFrame with similarity scores
        rates_df: DataFrame with threshold analysis
        stats: Dict with clustering statistics
        recommendation: Dict with threshold recommendation
        output_path: Path to save report
    """
    print(f"[INFO] Saving analysis report to {output_path}...")

    with open(output_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("Re-ID Performance Analysis Report\n")
        f.write("Feature 010 - Option D: Re-ID Performance Optimization\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Current State
        f.write("CURRENT STATE\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total assigned detections: {len(scores_df)}\n")
        f.write(f"Current REID_THRESHOLD: 0.70\n\n")

        # Score Statistics
        f.write("SIMILARITY SCORE STATISTICS\n")
        f.write("-" * 80 + "\n")
        if stats:
            f.write(f"Mean:     {stats['mean']:.3f}\n")
            f.write(f"Median:   {stats['median']:.3f}\n")
            f.write(f"Std Dev:  {stats['std']:.3f}\n")
            f.write(f"Min:      {stats['min']:.3f}\n")
            f.write(f"Max:      {stats['max']:.3f}\n")
            f.write(f"Q1 (25%): {stats['q25']:.3f}\n")
            f.write(f"Q3 (75%): {stats['q75']:.3f}\n\n")

        # Threshold Analysis
        f.write("THRESHOLD ANALYSIS\n")
        f.write("-" * 80 + "\n")
        if not rates_df.empty:
            f.write(rates_df.to_string(index=False))
            f.write("\n\n")

        # Recommendation
        f.write("RECOMMENDATION\n")
        f.write("-" * 80 + "\n")
        if recommendation:
            f.write(f"Recommended Threshold: {recommendation['recommended_threshold']:.2f}\n")
            f.write(f"Expected Assignment Rate: {recommendation['expected_assignment_rate']:.1f}%\n")
            f.write(f"Expected Improvement: +{recommendation['expected_improvement']:.1f}%\n")
            f.write(f"Potential New Assignments: {recommendation['potential_new_assignments']}\n")
            f.write(f"\nRationale:\n{recommendation['rationale']}\n\n")

        # Next Steps
        f.write("NEXT STEPS\n")
        f.write("-" * 80 + "\n")
        f.write("1. Review histogram visualization (reid_similarity_histogram.png)\n")
        f.write("2. Validate recommendation with sample batch test\n")
        f.write("3. Update REID_THRESHOLD environment variable if approved\n")
        f.write("4. Reprocess unassigned detections with new threshold\n")
        f.write("5. Monitor assignment rate and false positive rate\n\n")

    print(f"[OK] Saved report to {output_path}")


def main():
    """
    Main analysis workflow.

    Implements FR-014 through FR-018 for Option D.
    """
    print("=" * 80)
    print("Re-ID Performance Analysis - Feature 010 Option D")
    print("=" * 80)
    print()

    # Connect to database
    print("[INFO] Connecting to database...")
    engine = create_engine(DATABASE_URL)

    try:
        # FR-014: Query similarity scores
        scores_df = get_similarity_scores(engine)

        if scores_df.empty:
            print("[WARN] No similarity scores found. Cannot perform analysis.")
            print("[INFO] Ensure re-identification has run on some detections first.")
            return

        # FR-015: Generate histogram
        histogram_path = generate_histogram(scores_df)

        # FR-016: Calculate assignment rates
        rates_df = calculate_assignment_rates(engine)

        # FR-017: Identify clustering
        stats = identify_clustering(scores_df)

        # FR-018: Recommend threshold
        recommendation = recommend_threshold(scores_df, rates_df)

        # Save comprehensive report
        save_report(scores_df, rates_df, stats, recommendation)

        print()
        print("=" * 80)
        print("Analysis complete!")
        print("=" * 80)
        print(f"Results saved to:")
        print(f"  - reid_analysis_report.txt (text report)")
        print(f"  - reid_similarity_histogram.png (visualizations)")
        print()

    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
