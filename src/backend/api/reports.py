"""
Seasonal reports API for wildlife activity analysis.
Feature: 008-rut-season-analysis

Provides endpoints for generating seasonal activity reports and period comparisons.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from uuid import UUID
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from pydantic import BaseModel, Field

from backend.core.database import get_db
from backend.models.image import Image
from backend.models.detection import Detection
from backend.models.location import Location
from backend.models.seasonal import SeasonalFilter
from backend.schemas.report import (
    PeriodStats,
    SeasonalReport,
    ComparisonPeriod,
    ComparisonResult,
    ComparisonDifference,
    Comparison,
)


# Request schemas for comparison endpoint
class PeriodDefinition(BaseModel):
    """Period definition for comparison."""
    label: str = Field(..., description="User-defined label (e.g., 'November 2023')")
    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")


class ComparisonRequest(BaseModel):
    """Request schema for period comparison."""
    periods: List[PeriodDefinition] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="2-5 periods to compare"
    )
    location_id: Optional[UUID] = Field(None, description="Optional location filter")
    classifications: Optional[str] = Field(None, description="Comma-separated classifications")


router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"],
)


def calculate_period_stats(
    db: Session,
    start_date: datetime,
    end_date: datetime,
    location_id: Optional[UUID] = None,
    classifications: Optional[List[str]] = None
) -> PeriodStats:
    """
    Calculate statistics for a single time period.

    Args:
        db: Database session
        start_date: Period start (inclusive)
        end_date: Period end (inclusive)
        location_id: Optional location filter
        classifications: Optional classification filter

    Returns:
        PeriodStats: Aggregated statistics for the period
    """
    # Build base query for detections in this period
    query = (
        db.query(Detection)
        .join(Image, Detection.image_id == Image.id)
        .filter(
            and_(
                Image.timestamp >= start_date,
                Image.timestamp <= end_date,
                Detection.is_valid == True
            )
        )
    )

    # Apply location filter
    if location_id:
        query = query.filter(Image.location_id == location_id)

    # Apply classification filter
    if classifications:
        query = query.filter(
            func.coalesce(Detection.corrected_classification, Detection.classification).in_(
                [c.lower() for c in classifications]
            )
        )

    # Get all detections for this period
    detections = query.all()

    # Count detections by classification (use corrected if available)
    detection_counts = defaultdict(int)
    confidence_sums = defaultdict(float)
    confidence_counts = defaultdict(int)

    for det in detections:
        classification = det.corrected_classification if det.corrected_classification else det.classification
        detection_counts[classification] += 1
        confidence_sums[classification] += det.confidence
        confidence_counts[classification] += 1

    # Calculate average confidence by classification
    avg_confidence = {}
    for classification in detection_counts.keys():
        if confidence_counts[classification] > 0:
            avg_confidence[classification] = round(
                confidence_sums[classification] / confidence_counts[classification],
                3
            )

    # Calculate sex ratio (bucks per doe)
    # Buck classifications: buck, mature, mid, young
    # Doe classifications: doe
    buck_count = sum(
        detection_counts[c] for c in ['buck', 'mature', 'mid', 'young']
        if c in detection_counts
    )
    doe_count = detection_counts.get('doe', 0)
    sex_ratio = round(buck_count / doe_count, 2) if doe_count > 0 else None

    # Count total images in period
    image_query = db.query(Image).filter(
        and_(
            Image.timestamp >= start_date,
            Image.timestamp <= end_date
        )
    )
    if location_id:
        image_query = image_query.filter(Image.location_id == location_id)

    total_images = image_query.count()

    # Build period label
    period_label = f"{start_date.strftime('%B %Y')} - {end_date.strftime('%B %Y')}"
    if start_date.year == end_date.year and start_date.month == end_date.month:
        period_label = start_date.strftime('%B %Y')

    return PeriodStats(
        period_label=period_label,
        period_start=start_date,
        period_end=end_date,
        detection_counts_by_classification=dict(detection_counts),
        avg_confidence_by_classification=avg_confidence,
        sex_ratio=sex_ratio,
        total_images=total_images,
        total_detections=len(detections)
    )


@router.get(
    "/seasonal/activity",
    response_model=SeasonalReport,
    summary="Generate seasonal activity report",
    description="Generate comprehensive activity report for a seasonal period with detection statistics"
)
def get_seasonal_activity_report(
    season: str = Query(
        ...,
        description="Seasonal filter: RUT_SEASON, SPRING, SUMMER, or FALL"
    ),
    year: int = Query(
        ...,
        ge=2020,
        le=2030,
        description="Target year (e.g., 2024)"
    ),
    group_by: str = Query(
        "month",
        description="Grouping granularity: month, week, or day"
    ),
    location_id: Optional[UUID] = Query(
        None,
        description="Filter by specific camera location"
    ),
    classifications: Optional[str] = Query(
        None,
        description="Comma-separated classifications to include (e.g., 'mature,mid,young')"
    ),
    compare_to_non_season: bool = Query(
        False,
        description="Include comparison to non-seasonal period (e.g., rut vs non-rut)"
    ),
    db: Session = Depends(get_db)
) -> SeasonalReport:
    """
    Generate seasonal activity report with time-series data.

    **Example**: Rut season activity for 2024
    ```
    GET /api/reports/seasonal/activity?season=RUT_SEASON&year=2024&group_by=month
    ```

    Args:
        season: Seasonal filter name
        year: Target year
        group_by: Time grouping (month, week, day)
        location_id: Optional location filter
        classifications: Optional classification filter
        compare_to_non_season: Whether to add seasonal comparison
        db: Database session

    Returns:
        SeasonalReport: Activity report with periods, summary, and comparisons
    """
    # Validate seasonal filter
    try:
        seasonal_filter = SeasonalFilter[season.upper()]
    except KeyError:
        valid_seasons = [s.name for s in SeasonalFilter]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid season: {season}. Valid values: {', '.join(valid_seasons)}"
        )

    # Validate group_by
    if group_by not in ['month', 'week', 'day']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid group_by: {group_by}. Valid values: month, week, day"
        )

    # Parse classifications
    classification_list = None
    if classifications:
        classification_list = [c.strip() for c in classifications.split(',')]

    # Get date range for season
    start_date, end_date = SeasonalFilter.get_date_range(seasonal_filter, year)

    # Convert to datetime with timezone
    date_from = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0, tzinfo=timezone.utc)
    date_to = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=timezone.utc)

    # Generate time periods based on group_by
    periods = []
    current_date = date_from

    if group_by == 'month':
        # Group by month
        while current_date <= date_to:
            # Calculate month end
            if current_date.month == 12:
                month_end = datetime(current_date.year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc) - timedelta(seconds=1)
            else:
                month_end = datetime(current_date.year, current_date.month + 1, 1, 0, 0, 0, tzinfo=timezone.utc) - timedelta(seconds=1)

            # Don't exceed period end
            period_end = min(month_end, date_to)

            # Calculate stats for this month
            stats = calculate_period_stats(
                db, current_date, period_end, location_id, classification_list
            )
            periods.append(stats)

            # Move to next month
            if current_date.month == 12:
                current_date = datetime(current_date.year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            else:
                current_date = datetime(current_date.year, current_date.month + 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    elif group_by == 'week':
        # Group by week (7 days)
        while current_date <= date_to:
            week_end = current_date + timedelta(days=6, hours=23, minutes=59, seconds=59)
            period_end = min(week_end, date_to)

            stats = calculate_period_stats(
                db, current_date, period_end, location_id, classification_list
            )
            periods.append(stats)

            current_date = current_date + timedelta(days=7)

    else:  # day
        # Group by day
        while current_date <= date_to:
            day_end = current_date.replace(hour=23, minute=59, second=59)

            stats = calculate_period_stats(
                db, current_date, day_end, location_id, classification_list
            )
            periods.append(stats)

            current_date = current_date + timedelta(days=1)

    # Calculate overall summary
    total_detections = sum(p.total_detections for p in periods)
    total_images = sum(p.total_images for p in periods)

    # Aggregate classification counts
    overall_counts = defaultdict(int)
    for period in periods:
        for classification, count in period.detection_counts_by_classification.items():
            overall_counts[classification] += count

    # Calculate overall sex ratio
    overall_bucks = sum(
        overall_counts[c] for c in ['buck', 'mature', 'mid', 'young']
        if c in overall_counts
    )
    overall_does = overall_counts.get('doe', 0)
    overall_sex_ratio = round(overall_bucks / overall_does, 2) if overall_does > 0 else None

    summary = {
        "total_detections": total_detections,
        "total_images": total_images,
        "total_bucks": overall_bucks,
        "total_does": overall_does,
        "overall_sex_ratio": overall_sex_ratio,
        "detection_counts_by_classification": dict(overall_counts),
        "period_count": len(periods),
        "group_by": group_by
    }

    # Build comparisons if requested
    comparisons = []
    if compare_to_non_season and season.upper() == 'RUT_SEASON':
        # Compare rut season to non-rut (Feb-Aug for rut starting Sept)
        non_rut_start = datetime(year, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        non_rut_end = datetime(year, 8, 31, 23, 59, 59, tzinfo=timezone.utc)

        non_rut_stats = calculate_period_stats(
            db, non_rut_start, non_rut_end, location_id, classification_list
        )

        # Calculate mature buck change
        rut_mature = overall_counts.get('mature', 0)
        non_rut_mature = non_rut_stats.detection_counts_by_classification.get('mature', 0)

        if non_rut_mature > 0:
            # Can calculate percent change
            percent_change = round(((rut_mature - non_rut_mature) / non_rut_mature) * 100, 1)
            comparisons.append(Comparison(
                comparison_type="rut_vs_non_rut_mature_bucks",
                baseline_value=float(non_rut_mature),
                current_value=float(rut_mature),
                percent_change=percent_change,
                interpretation=f"Mature buck detections {'increased' if percent_change > 0 else 'decreased'} {abs(percent_change):.1f}% during rut season"
            ))
        elif rut_mature > 0:
            # Baseline is 0, but rut has detections - show as new activity
            comparisons.append(Comparison(
                comparison_type="rut_vs_non_rut_mature_bucks",
                baseline_value=0.0,
                current_value=float(rut_mature),
                percent_change=999.9,  # Use large number instead of infinity for JSON compatibility
                statistical_significance="N/A (baseline zero)",
                interpretation=f"Mature buck detections appeared during rut season ({rut_mature} detections vs 0 in non-rut period)"
            ))

    return SeasonalReport(
        periods=periods,
        summary=summary,
        comparisons=comparisons,
        generated_at=datetime.utcnow(),
        date_range={
            "start": date_from.isoformat(),
            "end": date_to.isoformat()
        }
    )


@router.post(
    "/seasonal/comparison",
    response_model=ComparisonResult,
    summary="Compare multiple time periods",
    description="Side-by-side comparison of 2-5 custom time periods (e.g., Nov 2023 vs Nov 2024)"
)
def compare_periods(
    request: ComparisonRequest = Body(...),
    db: Session = Depends(get_db)
) -> ComparisonResult:
    """
    Compare multiple custom time periods side-by-side.

    **Example request body:**
    ```json
    {
        "periods": [
            {"label": "November 2023", "start_date": "2023-11-01", "end_date": "2023-11-30"},
            {"label": "November 2024", "start_date": "2024-11-01", "end_date": "2024-11-30"}
        ]
    }
    ```

    Args:
        request: Comparison request with periods and filters
        db: Database session

    Returns:
        ComparisonResult: Side-by-side comparison with differences and highlights
    """
    # Parse classifications
    classification_list = None
    if request.classifications:
        classification_list = [c.strip() for c in request.classifications.split(',')]

    # Calculate stats for each period
    period_stats = []
    for period_def in request.periods:
        try:
            start_date = datetime.fromisoformat(period_def.start_date).replace(tzinfo=timezone.utc)
            end_date = datetime.fromisoformat(period_def.end_date).replace(tzinfo=timezone.utc)
            label = period_def.label
        except (ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid period definition: {e}"
            )

        stats = calculate_period_stats(db, start_date, end_date, request.location_id, classification_list)

        period_stats.append(ComparisonPeriod(
            label=label,
            start_date=period_def.start_date,
            end_date=period_def.end_date,
            stats=stats
        ))

    # Calculate differences between periods
    differences = []
    highlights = []

    # Compare first period to all others
    baseline = period_stats[0]
    for i, current in enumerate(period_stats[1:], 1):
        # Total detections comparison
        baseline_total = baseline.stats.total_detections
        current_total = current.stats.total_detections

        if baseline_total > 0:
            percent_change = round(((current_total - baseline_total) / baseline_total) * 100, 1)
            differences.append(ComparisonDifference(
                metric="total_detections",
                period_1_label=baseline.label,
                period_2_label=current.label,
                period_1_value=float(baseline_total),
                period_2_value=float(current_total),
                absolute_change=float(current_total - baseline_total),
                percent_change=percent_change,
                interpretation=f"{current.label} shows {abs(percent_change):.1f}% {'increase' if percent_change > 0 else 'decrease'} vs {baseline.label}"
            ))

        # Sex ratio comparison
        if baseline.stats.sex_ratio and current.stats.sex_ratio:
            ratio_change = round(((current.stats.sex_ratio - baseline.stats.sex_ratio) / baseline.stats.sex_ratio) * 100, 1)
            differences.append(ComparisonDifference(
                metric="sex_ratio",
                period_1_label=baseline.label,
                period_2_label=current.label,
                period_1_value=baseline.stats.sex_ratio,
                period_2_value=current.stats.sex_ratio,
                absolute_change=round(current.stats.sex_ratio - baseline.stats.sex_ratio, 2),
                percent_change=ratio_change,
                interpretation=f"Buck/doe ratio {'increased' if ratio_change > 0 else 'decreased'} {abs(ratio_change):.1f}% in {current.label}"
            ))

    # Generate highlights (most significant changes)
    if differences:
        # Sort by absolute percent change
        sorted_diffs = sorted(differences, key=lambda d: abs(d.percent_change), reverse=True)
        for diff in sorted_diffs[:3]:  # Top 3 highlights
            highlights.append(diff.interpretation)

    return ComparisonResult(
        period_stats=period_stats,
        differences=differences,
        highlights=highlights if highlights else ["No significant differences detected"],
        generated_at=datetime.utcnow()
    )
