"""
Pydantic schemas for export services (PDF reports and ZIP archives).
Feature: 008-rut-season-analysis
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


# PDF Export Schemas

class ComparisonPeriodRequest(BaseModel):
    """Period definition for comparison reports."""

    start_date: str = Field(..., description="YYYY-MM-DD format")
    end_date: str = Field(..., description="YYYY-MM-DD format")
    label: str = Field(..., description="User-defined label (e.g., 'November (Peak Rut)')")


class PDFReportRequest(BaseModel):
    """Request schema for PDF report generation."""

    report_type: str = Field(
        ...,
        description="Report template type: 'seasonal_activity', 'comparison', or 'custom'"
    )
    start_date: str = Field(..., description="Report start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="Report end date (YYYY-MM-DD)")
    comparison_periods: Optional[List[ComparisonPeriodRequest]] = Field(
        None,
        min_length=2,
        max_length=5,
        description="Required if report_type='comparison'. Define 2-5 periods."
    )
    include_charts: bool = Field(True, description="Embed timeline charts (PNG images)")
    include_tables: bool = Field(True, description="Include statistics tables")
    include_insights: bool = Field(True, description="Include plain language summary")
    group_by: str = Field("month", description="Chart granularity: 'month', 'week', or 'day'")
    classifications: Optional[List[str]] = Field(
        None,
        description="Filter to specific classifications (default: all deer classes)"
    )
    title: Optional[str] = Field(
        None,
        description="Report title (default: auto-generated from date range)"
    )


class PDFReportResponse(BaseModel):
    """Response schema for PDF report generation request."""

    job_id: str = Field(..., description="Use this ID to poll status endpoint")
    status: str = Field(..., description="'pending' or 'processing'")
    message: str = Field(..., description="Human-readable status message")
    estimated_completion: Optional[datetime] = Field(
        None,
        description="Estimated finish time (usually 5-10 seconds from now)"
    )


class PDFStatusResponse(BaseModel):
    """Response schema for PDF generation status query."""

    job_id: str
    status: str = Field(..., description="'pending', 'processing', 'completed', 'failed', or 'expired'")
    filename: Optional[str] = Field(
        None,
        description="Generated filename (available when status='completed')"
    )
    download_url: Optional[str] = Field(
        None,
        description="Available when status='completed'"
    )
    file_size_bytes: Optional[int] = Field(
        None,
        description="PDF file size (available when completed)"
    )
    error_message: Optional[str] = Field(
        None,
        description="Error details (only if status='failed')"
    )
    created_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: datetime = Field(..., description="Auto-delete timestamp (24 hours from creation)")


# ZIP Export Schemas

class ZIPExportRequest(BaseModel):
    """Request schema for ZIP archive export."""

    detection_ids: List[UUID] = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="List of detection UUIDs to export (max 10,000)"
    )
    include_crops: bool = Field(True, description="Include cropped detection images")
    include_metadata_csv: bool = Field(True, description="Include metadata.csv file")
    crop_size: int = Field(
        300,
        ge=128,
        le=1024,
        description="Crop image size in pixels (square)"
    )


class ZIPExportResponse(BaseModel):
    """Response schema for ZIP export request."""

    job_id: str = Field(..., description="Use this ID to poll status endpoint")
    status: str = Field(..., description="'pending' or 'processing'")
    total_detections: int = Field(..., ge=0, description="Total detections to export")
    message: str = Field(..., description="Human-readable status message")
    estimated_completion: Optional[datetime] = Field(
        None,
        description="Estimated finish time based on detection count"
    )


class ZIPStatusResponse(BaseModel):
    """Response schema for ZIP export status query."""

    job_id: str
    status: str = Field(..., description="'pending', 'processing', 'completed', 'failed', or 'expired'")
    total_detections: int = Field(..., ge=0)
    processed_count: int = Field(default=0, ge=0, description="Detections processed so far")
    progress_percent: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="(processed_count / total_detections) * 100"
    )
    filename: Optional[str] = Field(
        None,
        description="Generated filename (available when status='completed')"
    )
    download_url: Optional[str] = Field(
        None,
        description="Available when status='completed'"
    )
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = Field(
        None,
        description="Based on current processing rate"
    )
    expires_at: datetime = Field(..., description="Auto-delete timestamp (7 days from creation)")
