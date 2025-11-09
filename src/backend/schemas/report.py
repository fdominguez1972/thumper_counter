"""
Pydantic schemas for seasonal reports and comparisons.
Feature: 008-rut-season-analysis
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


class PeriodStats(BaseModel):
    """Statistics for a single time period (month/week/day)."""

    period_label: str = Field(..., description="Human-readable period (e.g., 'November 2024')")
    period_start: datetime = Field(..., description="Period start timestamp (UTC)")
    period_end: datetime = Field(..., description="Period end timestamp (UTC)")
    detection_counts_by_classification: Dict[str, int] = Field(
        ...,
        description="Detection count per classification (e.g., {'mature': 356, 'doe': 412})"
    )
    avg_confidence_by_classification: Dict[str, float] = Field(
        ...,
        description="Average confidence per classification (e.g., {'mature': 0.78})"
    )
    sex_ratio: Optional[float] = Field(
        None,
        description="Bucks per doe ratio (null if no doe detections)"
    )
    total_images: int = Field(..., ge=0, description="Images captured in this period")
    total_detections: int = Field(..., ge=0, description="Total detections in this period")


class Comparison(BaseModel):
    """Statistical comparison between periods."""

    comparison_type: str = Field(..., description="Type of comparison (e.g., 'rut_vs_non_rut')")
    baseline_value: float = Field(..., description="Baseline period metric value")
    current_value: float = Field(..., description="Current period metric value")
    percent_change: float = Field(..., description="Percent change from baseline")
    statistical_significance: Optional[str] = Field(
        None,
        description="Statistical test result (e.g., 'p < 0.001')"
    )
    interpretation: str = Field(
        ...,
        description="Plain language summary (e.g., 'Mature buck detections increased 158% during rut')"
    )


class SeasonalReport(BaseModel):
    """Complete seasonal activity report."""

    periods: List[PeriodStats] = Field(..., description="Time series data")
    summary: Dict[str, Any] = Field(
        ...,
        description="Overall summary (total_detections, total_bucks, total_does, overall_sex_ratio, etc.)"
    )
    comparisons: List[Comparison] = Field(
        default=[],
        description="Statistical comparisons (e.g., rut vs non-rut)"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    date_range: Dict[str, str] = Field(
        ...,
        description="Query range (e.g., {'start': '2024-09-01', 'end': '2025-01-31'})"
    )


class ComparisonPeriod(BaseModel):
    """Single period in a comparison query."""

    label: str = Field(..., description="User-defined label (e.g., 'September')")
    start_date: str = Field(..., description="YYYY-MM-DD format")
    end_date: str = Field(..., description="YYYY-MM-DD format")
    stats: PeriodStats = Field(..., description="Statistics for this period")


class ComparisonDifference(BaseModel):
    """Notable statistical difference between periods."""

    metric: str = Field(..., description="Metric name (e.g., 'mature_buck_detections')")
    period_1_label: str
    period_2_label: str
    period_1_value: float
    period_2_value: float
    absolute_change: float
    percent_change: float
    interpretation: str = Field(
        ...,
        description="Plain language summary (e.g., 'November shows 189% increase vs September')"
    )


class ComparisonResult(BaseModel):
    """Side-by-side comparison of multiple periods."""

    period_stats: List[ComparisonPeriod] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="Up to 5 periods for comparison"
    )
    differences: List[ComparisonDifference] = Field(
        ...,
        description="Notable differences detected"
    )
    highlights: List[str] = Field(
        ...,
        description="Key insights (e.g., 'Peak activity in November')"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)
