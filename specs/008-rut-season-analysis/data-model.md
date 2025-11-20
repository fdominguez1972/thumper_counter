# Data Model: Rut Season Analysis

**Feature**: 008-rut-season-analysis
**Phase**: Phase 1 (Design)
**Date**: 2025-11-08
**Status**: Design Complete

## Overview

This feature **does NOT create new database tables**. All data uses existing schema from previous sprints. This document defines:

1. **Existing Tables** - Used by this feature (no modifications)
2. **Virtual Entities** - Application-level data structures (not stored in database)
3. **Database Indexes** - Performance optimizations to add
4. **Entity Relationships** - How data flows through the system

---

## Existing Database Tables (No Changes)

### Table: `images`

**Purpose**: Store trail camera image metadata
**Existing Columns Used by This Feature:**
- `id` (UUID, PK) - Unique image identifier
- `filename` (VARCHAR) - Original filename
- `path` (VARCHAR) - Filesystem path
- `timestamp` (TIMESTAMP) - When photo was taken (indexed)
- `location_id` (UUID, FK -> locations.id) - Camera location
- `processing_status` (ENUM) - pending, processing, completed, failed
- `created_at` (TIMESTAMP) - When image was uploaded

**Query Patterns:**
```sql
-- Date range filtering (core query for seasonal analysis)
SELECT * FROM images
WHERE timestamp BETWEEN '2024-09-01' AND '2025-01-31'
ORDER BY timestamp DESC;

-- Count images by month
SELECT DATE_TRUNC('month', timestamp) AS month, COUNT(*)
FROM images
WHERE timestamp BETWEEN '2024-09-01' AND '2025-01-31'
GROUP BY month
ORDER BY month;
```

**Index Required**: `idx_images_timestamp` (see Database Indexes section)

---

### Table: `detections`

**Purpose**: Store YOLOv8 deer detection results
**Existing Columns Used by This Feature:**
- `id` (UUID, PK) - Unique detection identifier
- `image_id` (UUID, FK -> images.id) - Parent image
- `bbox_x1`, `bbox_y1`, `bbox_x2`, `bbox_y2` (FLOAT) - Bounding box coordinates
- `confidence` (FLOAT) - Detection confidence score (0.0 - 1.0)
- `classification` (VARCHAR) - Sex/age class: 'doe', 'fawn', 'mature', 'mid', 'young', 'cattle', 'pig', 'raccoon'
- `deer_id` (UUID, FK -> deer.id, NULLABLE) - Re-identified deer profile
- `created_at` (TIMESTAMP) - When detection was created

**Query Patterns:**
```sql
-- Buck detections during rut season
SELECT d.*
FROM detections d
JOIN images i ON d.image_id = i.id
WHERE i.timestamp BETWEEN '2024-09-01' AND '2025-01-31'
  AND d.classification IN ('mature', 'mid', 'young')
ORDER BY d.confidence DESC;

-- Average confidence by classification and month
SELECT
  DATE_TRUNC('month', i.timestamp) AS month,
  d.classification,
  COUNT(*) AS detection_count,
  AVG(d.confidence) AS avg_confidence
FROM detections d
JOIN images i ON d.image_id = i.id
WHERE i.timestamp BETWEEN '2024-09-01' AND '2025-01-31'
GROUP BY month, d.classification
ORDER BY month, d.classification;
```

**Index Required**: `idx_detections_classification_confidence` (see Database Indexes section)

---

### Table: `deer`

**Purpose**: Store individual deer profiles from re-identification
**Existing Columns Used by This Feature:**
- `id` (UUID, PK) - Unique deer identifier
- `name` (VARCHAR, NULLABLE) - User-assigned name
- `sex` (ENUM) - 'male', 'female', 'unknown'
- `species` (VARCHAR) - 'whitetail', 'mule', 'unknown'
- `first_seen` (TIMESTAMP) - First detection timestamp
- `last_seen` (TIMESTAMP) - Most recent detection timestamp
- `sighting_count` (INTEGER) - Total number of detections

**Query Patterns:**
```sql
-- Deer active during rut season
SELECT DISTINCT deer.*
FROM deer
JOIN detections d ON deer.id = d.deer_id
JOIN images i ON d.image_id = i.id
WHERE i.timestamp BETWEEN '2024-09-01' AND '2025-01-31';

-- Sex ratio during rut season
SELECT
  deer.sex,
  COUNT(DISTINCT deer.id) AS unique_deer,
  COUNT(d.id) AS total_sightings
FROM deer
JOIN detections d ON deer.id = d.deer_id
JOIN images i ON d.image_id = i.id
WHERE i.timestamp BETWEEN '2024-09-01' AND '2025-01-31'
GROUP BY deer.sex;
```

---

### Table: `locations`

**Purpose**: Store trail camera locations
**Existing Columns Used by This Feature:**
- `id` (UUID, PK) - Unique location identifier
- `name` (VARCHAR) - Location name (e.g., "Sanctuary", "North Ridge")
- `description` (TEXT, NULLABLE) - Location notes
- `image_count` (INTEGER) - Total images at this location

**Query Patterns:**
```sql
-- Images by location during rut season
SELECT l.name, COUNT(i.id) AS rut_season_images
FROM locations l
JOIN images i ON l.id = i.location_id
WHERE i.timestamp BETWEEN '2024-09-01' AND '2025-01-31'
GROUP BY l.id, l.name
ORDER BY rut_season_images DESC;
```

---

## Virtual Entities (Application-Level Only)

### Entity 1: SeasonalFilter

**Purpose**: Predefined date range constants for common seasonal queries
**Storage**: Application constants (Python enum or dict)
**Lifecycle**: Immutable, defined at application startup

**Structure:**
```python
from enum import Enum
from datetime import date

class SeasonalFilter(Enum):
    """Predefined seasonal date ranges for Hopkins Ranch, Texas."""

    RUT_SEASON = {
        "name": "Rut Season",
        "description": "Whitetail deer breeding season (Sept 1 - Jan 31)",
        "start_month": 9,
        "start_day": 1,
        "end_month": 1,
        "end_day": 31,
        "crosses_year": True  # September 2024 to January 2025
    }

    SPRING = {
        "name": "Spring",
        "description": "Fawn birthing season (Mar 1 - May 31)",
        "start_month": 3,
        "start_day": 1,
        "end_month": 5,
        "end_day": 31,
        "crosses_year": False
    }

    SUMMER = {
        "name": "Summer",
        "description": "Antler growth period (Jun 1 - Aug 31)",
        "start_month": 6,
        "start_day": 1,
        "end_month": 8,
        "end_day": 31,
        "crosses_year": False
    }

    FALL = {
        "name": "Fall",
        "description": "Pre-rut and rut activity (Sept 1 - Nov 30)",
        "start_month": 9,
        "start_day": 1,
        "end_month": 11,
        "end_day": 30,
        "crosses_year": False
    }

    @staticmethod
    def get_date_range(season: "SeasonalFilter", year: int) -> tuple[date, date]:
        """
        Convert seasonal filter to actual start/end dates for a given year.

        Args:
            season: SeasonalFilter enum value
            year: Target year (e.g., 2024)

        Returns:
            (start_date, end_date) tuple

        Example:
            >>> SeasonalFilter.get_date_range(SeasonalFilter.RUT_SEASON, 2024)
            (date(2024, 9, 1), date(2025, 1, 31))
        """
        config = season.value
        start_date = date(year, config["start_month"], config["start_day"])

        if config["crosses_year"]:
            end_date = date(year + 1, config["end_month"], config["end_day"])
        else:
            end_date = date(year, config["end_month"], config["end_day"])

        return start_date, end_date
```

**Usage in API:**
```python
# User requests rut season for 2024
start_date, end_date = SeasonalFilter.get_date_range(SeasonalFilter.RUT_SEASON, 2024)
# Returns: (2024-09-01, 2025-01-31)
```

---

### Entity 2: SeasonalReport

**Purpose**: Aggregated statistics structure for seasonal analysis reports
**Storage**: Generated on-demand from database queries, returned as API response
**Lifecycle**: Ephemeral (not stored, cached for 5 minutes in Redis)

**Pydantic Schema:**
```python
from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime

class PeriodStats(BaseModel):
    """Statistics for a single time period (month/week/day)."""
    period_label: str = Field(..., description="Human-readable period (e.g., '2024-11')")
    period_start: datetime = Field(..., description="Period start timestamp")
    period_end: datetime = Field(..., description="Period end timestamp")
    detection_counts_by_classification: Dict[str, int] = Field(
        ...,
        description="Detections per class (e.g., {'mature': 245, 'doe': 189})"
    )
    avg_confidence_by_classification: Dict[str, float] = Field(
        ...,
        description="Average confidence per class (e.g., {'mature': 0.78})"
    )
    sex_ratio: float = Field(
        ...,
        description="Bucks to does ratio (bucks / does), null if no does"
    )
    total_images: int = Field(..., description="Images captured in this period")
    total_detections: int = Field(..., description="Total detections in this period")

class SeasonalReport(BaseModel):
    """Complete seasonal activity report."""
    periods: List[PeriodStats] = Field(..., description="Time series data")
    summary: Dict[str, any] = Field(
        ...,
        description="Overall summary (total_detections, total_bucks, total_does, overall_sex_ratio)"
    )
    comparisons: List[Dict[str, any]] = Field(
        default=[],
        description="Statistical comparisons (e.g., rut vs non-rut)"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    date_range: Dict[str, str] = Field(
        ...,
        description="Query range (e.g., {'start': '2024-09-01', 'end': '2025-01-31'})"
    )
```

**Example JSON Response:**
```json
{
  "periods": [
    {
      "period_label": "September 2024",
      "period_start": "2024-09-01T00:00:00Z",
      "period_end": "2024-09-30T23:59:59Z",
      "detection_counts_by_classification": {
        "mature": 123,
        "mid": 45,
        "young": 67,
        "doe": 234,
        "fawn": 12
      },
      "avg_confidence_by_classification": {
        "mature": 0.76,
        "mid": 0.72,
        "young": 0.68,
        "doe": 0.81,
        "fawn": 0.59
      },
      "sex_ratio": 1.00,
      "total_images": 987,
      "total_detections": 481
    }
  ],
  "summary": {
    "total_detections": 8543,
    "total_bucks": 3214,
    "total_does": 4129,
    "total_fawns": 1200,
    "overall_sex_ratio": 0.78
  },
  "comparisons": [
    {
      "comparison_type": "rut_vs_non_rut",
      "baseline_value": 1245,
      "current_value": 3214,
      "percent_change": 158.0,
      "statistical_significance": "p < 0.001"
    }
  ],
  "generated_at": "2025-11-08T12:34:56Z",
  "date_range": {
    "start": "2024-09-01",
    "end": "2025-01-31"
  }
}
```

---

### Entity 3: ComparisonResult

**Purpose**: Multi-period comparison data for side-by-side analysis
**Storage**: Generated on-demand, returned as API response
**Lifecycle**: Ephemeral (not stored)

**Pydantic Schema:**
```python
class ComparisonPeriod(BaseModel):
    """Single period in a comparison."""
    label: str = Field(..., description="User-defined label (e.g., 'September')")
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")
    stats: PeriodStats = Field(..., description="Statistics for this period")

class ComparisonDifference(BaseModel):
    """Notable statistical difference between periods."""
    metric: str = Field(..., description="Metric name (e.g., 'mature_buck_detections')")
    period_1_value: float
    period_2_value: float
    absolute_change: float
    percent_change: float
    interpretation: str = Field(
        ...,
        description="Plain language summary (e.g., 'November shows 45% increase')"
    )

class ComparisonResult(BaseModel):
    """Side-by-side comparison of multiple periods."""
    period_stats: List[ComparisonPeriod] = Field(
        ...,
        min_items=2,
        max_items=5,
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
```

**Example JSON Response:**
```json
{
  "period_stats": [
    {
      "label": "September 2024",
      "start_date": "2024-09-01",
      "end_date": "2024-09-30",
      "stats": { /* PeriodStats object */ }
    },
    {
      "label": "November 2024",
      "start_date": "2024-11-01",
      "end_date": "2024-11-30",
      "stats": { /* PeriodStats object */ }
    }
  ],
  "differences": [
    {
      "metric": "mature_buck_detections",
      "period_1_value": 123,
      "period_2_value": 356,
      "absolute_change": 233,
      "percent_change": 189.4,
      "interpretation": "November shows 189% increase in mature buck detections vs September"
    }
  ],
  "highlights": [
    "Peak rut activity observed in November (356 mature buck detections)",
    "Sex ratio shifted from 1.00 (Sept) to 1.52 (Nov) - more bucks visible",
    "Average confidence remained consistent (0.76 vs 0.78)"
  ],
  "generated_at": "2025-11-08T12:34:56Z"
}
```

---

### Entity 4: PDFReport

**Purpose**: Metadata for generated PDF reports
**Storage**: Temporary filesystem storage (auto-delete after 24 hours)
**Lifecycle**: Created on export, deleted after download or 24-hour expiry

**Pydantic Schema:**
```python
from uuid import UUID, uuid4

class PDFReport(BaseModel):
    """Metadata for a generated PDF report."""
    report_id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., description="Report title")
    date_ranges: List[Dict[str, str]] = Field(
        ...,
        description="Date ranges included in report"
    )
    charts_included: int = Field(..., description="Number of charts embedded")
    file_size_bytes: int = Field(..., description="PDF file size in bytes")
    file_path: str = Field(..., description="Filesystem path to PDF")
    download_url: str = Field(..., description="API download URL")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(
        ...,
        description="Auto-delete timestamp (24 hours from generated_at)"
    )
    status: str = Field(
        default="completed",
        description="'processing', 'completed', 'failed', 'expired'"
    )
```

**Storage Location:**
- `/tmp/reports/{report_id}.pdf` (container filesystem)
- Auto-cleanup via cron job: delete files where `expires_at < NOW()`

---

### Entity 5: ExportJob

**Purpose**: Track async ZIP export task status
**Storage**: Celery task metadata (stored in Redis via Celery backend)
**Lifecycle**: Created when export requested, expires after 7 days

**Pydantic Schema:**
```python
class ExportJob(BaseModel):
    """Async export job status."""
    job_id: str = Field(..., description="Celery task ID")
    status: str = Field(
        ...,
        description="'pending', 'processing', 'completed', 'failed'"
    )
    total_detections: int = Field(..., description="Total detections to export")
    processed_count: int = Field(default=0, description="Detections processed so far")
    download_url: str | None = Field(
        None,
        description="Download URL (available when status='completed')"
    )
    error_message: str | None = Field(None, description="Error details if failed")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = Field(None)
    estimated_completion: datetime | None = Field(
        None,
        description="Estimated finish time based on current progress"
    )

    @property
    def progress_percent(self) -> float:
        """Calculate completion percentage."""
        if self.total_detections == 0:
            return 0.0
        return (self.processed_count / self.total_detections) * 100
```

**Celery Task Integration:**
```python
from celery import shared_task

@shared_task(bind=True)
def export_detection_crops(self, detection_ids: List[str]):
    """
    Async task to generate ZIP archive with detection crops.

    Args:
        detection_ids: List of detection UUIDs to export

    Returns:
        dict with download_url
    """
    # Update progress: self.update_state(state='PROCESSING', meta={'processed': N})
    # Generate ZIP: create crops, add metadata CSV
    # Upload to /tmp/exports/{job_id}.zip
    # Return download URL
```

**API Polling:**
```python
# Frontend polls GET /api/exports/zip/{job_id}
# Backend queries Celery: AsyncResult(job_id).state and .info
```

---

### Entity 6: QuerySession

**Purpose**: Frontend state tracking for user's analysis session
**Storage**: React Context API (browser memory, not persisted)
**Lifecycle**: Exists during browser session, lost on refresh

**TypeScript Interface:**
```typescript
interface QuerySession {
  // Selected date ranges for comparison
  selectedPeriods: Array<{
    id: string;
    label: string;
    startDate: string;  // YYYY-MM-DD
    endDate: string;    // YYYY-MM-DD
  }>;

  // Active filters
  activeFilters: {
    classifications: string[];  // ['mature', 'doe']
    locations: string[];        // [location_id_1, location_id_2]
    minConfidence: number;      // 0.0 - 1.0
  };

  // UI state
  comparisonMode: boolean;      // Side-by-side view enabled
  chartType: 'line' | 'bar';    // Chart visualization type
  groupBy: 'month' | 'week' | 'day';  // Aggregation granularity

  // Last query result (cached)
  lastReport: SeasonalReport | null;
  lastFetchedAt: Date | null;
}
```

**React Context Provider:**
```typescript
import React, { createContext, useState } from 'react';

export const QuerySessionContext = createContext<QuerySession | null>(null);

export const QuerySessionProvider: React.FC = ({ children }) => {
  const [session, setSession] = useState<QuerySession>({
    selectedPeriods: [],
    activeFilters: {
      classifications: [],
      locations: [],
      minConfidence: 0.5
    },
    comparisonMode: false,
    chartType: 'line',
    groupBy: 'month',
    lastReport: null,
    lastFetchedAt: null
  });

  return (
    <QuerySessionContext.Provider value={session}>
      {children}
    </QuerySessionContext.Provider>
  );
};
```

---

## Database Indexes (Performance Optimization)

### Index 1: `idx_images_timestamp`

**Purpose**: Optimize date range queries on images table
**Impact**: 95% query speed improvement (full table scan -> indexed lookup)

**Creation SQL:**
```sql
-- Create index on timestamp column for fast date filtering
CREATE INDEX IF NOT EXISTS idx_images_timestamp ON images(timestamp);

-- Performance test query (should use index)
EXPLAIN ANALYZE
SELECT id, filename, timestamp, location_id
FROM images
WHERE timestamp BETWEEN '2024-09-01' AND '2025-01-31';

-- Expected EXPLAIN output:
-- Index Scan using idx_images_timestamp on images
-- (cost=0.29..123.45 rows=6115 width=100)
```

**Query Performance:**
- Without index: 2-3 seconds (full table scan of 35,251 rows)
- With index: <500ms (indexed scan of 6,115 matching rows)

---

### Index 2: `idx_detections_classification_confidence`

**Purpose**: Optimize classification filtering and confidence-based sorting
**Impact**: Faster queries for buck detections with confidence thresholds

**Creation SQL:**
```sql
-- Composite index for classification filtering with confidence ordering
CREATE INDEX IF NOT EXISTS idx_detections_classification_confidence
  ON detections(classification, confidence DESC);

-- Performance test query (should use index)
EXPLAIN ANALYZE
SELECT *
FROM detections
WHERE classification IN ('mature', 'mid', 'young')
  AND confidence >= 0.7
ORDER BY confidence DESC;

-- Expected EXPLAIN output:
-- Index Scan using idx_detections_classification_confidence on detections
-- (cost=0.42..567.89 rows=3214 width=150)
```

**Query Performance:**
- Without index: 1-2 seconds (filter + sort on 29,735 rows)
- With index: <300ms (indexed scan with early termination)

---

### Index Maintenance

**Creation Script** (`migrations/010_add_seasonal_indexes.sql`):
```sql
-- Seasonal analysis performance indexes
-- Run after Sprint 8 (008-rut-season-analysis)

BEGIN;

-- Index 1: Image timestamp for date range queries
CREATE INDEX IF NOT EXISTS idx_images_timestamp ON images(timestamp);

-- Index 2: Detection classification and confidence
CREATE INDEX IF NOT EXISTS idx_detections_classification_confidence
  ON detections(classification, confidence DESC);

-- Verify indexes were created
SELECT
  tablename,
  indexname,
  indexdef
FROM pg_indexes
WHERE indexname IN ('idx_images_timestamp', 'idx_detections_classification_confidence');

COMMIT;
```

**Monitoring:**
```sql
-- Check index usage statistics
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan AS scans,
  idx_tup_read AS tuples_read,
  idx_tup_fetch AS tuples_fetched
FROM pg_stat_user_indexes
WHERE indexname IN ('idx_images_timestamp', 'idx_detections_classification_confidence');
```

---

## Entity Relationships & Data Flow

### Flow 1: Seasonal Image Query

```
User Request (Frontend)
  |
  v
GET /api/seasonal/images?start_date=2024-09-01&end_date=2025-01-31
  |
  v
SeasonalFilter.RUT_SEASON (if using predefined season)
  |
  v
Database Query (uses idx_images_timestamp)
  |
  v
SELECT * FROM images WHERE timestamp BETWEEN ... ORDER BY timestamp
  |
  v
Pydantic ImageResponse schemas
  |
  v
JSON Response to frontend
```

### Flow 2: Seasonal Activity Report

```
User Request (Frontend)
  |
  v
GET /api/seasonal/reports/activity?start_date=...&group_by=month
  |
  v
seasonal_analysis.py service (raw SQL aggregation)
  |
  v
JOIN images + detections + deer (uses both indexes)
  |
  v
GROUP BY DATE_TRUNC('month', timestamp), classification
  |
  v
Map SQL results to SeasonalReport Pydantic model
  |
  v
Cache in Redis (5 minutes TTL)
  |
  v
JSON Response to frontend (periods, summary, comparisons)
```

### Flow 3: PDF Export

```
User clicks "Export PDF" (Frontend)
  |
  v
POST /api/exports/pdf (with report config)
  |
  v
Create PDFReport entity (metadata only)
  |
  v
Queue Celery task: generate_pdf_report.delay(report_id)
  |
  v
Worker generates PDF with ReportLab
  |
  v
Embed Recharts PNG images (pre-rendered)
  |
  v
Save to /tmp/reports/{report_id}.pdf
  |
  v
Update PDFReport.status = 'completed', set download_url
  |
  v
Frontend polls GET /api/exports/pdf/{report_id}
  |
  v
User downloads PDF from download_url
```

### Flow 4: ZIP Export

```
User selects detections, clicks "Export ZIP" (Frontend)
  |
  v
POST /api/exports/zip (with detection_ids list)
  |
  v
Create ExportJob entity (status='pending')
  |
  v
Queue Celery task: export_detection_crops.delay(detection_ids)
  |
  v
Worker processes detections:
  - Load image crops from filesystem
  - Generate metadata CSV
  - Create ZIP archive
  - Update ExportJob.processed_count in real-time
  |
  v
Save to /tmp/exports/{job_id}.zip
  |
  v
Update ExportJob.status = 'completed', set download_url
  |
  v
Frontend polls GET /api/exports/zip/{job_id} (shows progress bar)
  |
  v
User downloads ZIP from download_url
```

---

## Summary

**Database Changes**: NONE (no new tables, only 2 indexes added)
**Virtual Entities**: 6 application-level data structures
**Indexes**: 2 performance optimizations (required for <2 second query goal)

**Key Design Decisions:**
1. **No new tables**: Reuse existing schema (images, detections, deer, locations)
2. **Virtual entities**: Keep seasonal logic in application layer (flexible, no migrations)
3. **Indexes**: Critical for performance (date range queries must be <2 seconds)
4. **Ephemeral reports**: PDF/ZIP files auto-delete (no database clutter)
5. **Async exports**: Celery handles long-running ZIP generation (user experience)

**Next Steps:**
1. Create database migration script: `migrations/010_add_seasonal_indexes.sql`
2. Implement Pydantic schemas in `src/backend/schemas/report.py`
3. Create SQL aggregation functions in `src/backend/services/seasonal_analysis.py`
4. Build React Context provider in `frontend/src/contexts/QuerySessionContext.tsx`

---

**Phase 1 Design**: Data model complete - ready for API contract definition
