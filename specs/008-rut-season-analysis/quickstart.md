# Quickstart Guide: Rut Season Analysis Feature

**Feature**: 008-rut-season-analysis
**Audience**: Backend and frontend developers implementing this feature
**Prerequisites**: Completed Sprint 6 (core pipeline operational)

## Overview

This guide walks you through:
1. Setting up the development environment
2. Running your first seasonal query
3. Generating a PDF report
4. Testing the frontend date picker
5. Common workflows and examples

**Time to complete**: 30 minutes

---

## Prerequisites

### System Requirements
- Docker Compose environment running (backend, worker, db, redis)
- PostgreSQL database with existing images and detections
- Python 3.11+ (backend development)
- Node.js 18+ (frontend development)

### Verify Existing Data
```bash
# Check image count and date range
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT
     COUNT(*) AS total_images,
     MIN(timestamp) AS earliest,
     MAX(timestamp) AS latest
   FROM images;"

# Expected output:
# total_images | earliest            | latest
# -------------|---------------------|--------------------
# 35251        | 2023-06-15 08:23:11 | 2024-12-20 16:45:33

# Check rut season image count (Sept 1 - Jan 31)
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT COUNT(*) FROM images
   WHERE timestamp BETWEEN '2024-09-01' AND '2025-01-31';"

# Expected: 6115 images
```

---

## Step 1: Install Dependencies

### Backend (Python)
```bash
# Add new dependencies to requirements.txt
cat >> requirements.txt <<EOF
reportlab>=4.0.0       # PDF generation
pandas>=2.0.0          # Data aggregation (if not already installed)
EOF

# Rebuild backend container
docker-compose up -d --build backend

# Verify ReportLab installation
docker-compose exec backend python3 -c "import reportlab; print(reportlab.Version)"
# Expected output: 4.x.x
```

### Frontend (React)
```bash
# Navigate to frontend directory
cd frontend

# Install date picker and charting dependencies (likely already installed from Sprint 10)
npm install @mui/x-date-pickers dayjs recharts

# Verify installation
npm list @mui/x-date-pickers recharts
# Expected: Both packages listed with versions
```

---

## Step 2: Create Database Indexes

```bash
# Create performance indexes for seasonal queries
docker-compose exec db psql -U deertrack deer_tracking <<EOF
-- Index for fast date range filtering
CREATE INDEX IF NOT EXISTS idx_images_timestamp ON images(timestamp);

-- Index for classification filtering
CREATE INDEX IF NOT EXISTS idx_detections_classification_confidence
  ON detections(classification, confidence DESC);

-- Verify indexes created
\di idx_images_timestamp idx_detections_classification_confidence
EOF

# Test query performance (should use idx_images_timestamp)
docker-compose exec db psql -U deertrack deer_tracking -c \
  "EXPLAIN ANALYZE
   SELECT COUNT(*) FROM images
   WHERE timestamp BETWEEN '2024-09-01' AND '2025-01-31';"

# Look for "Index Scan using idx_images_timestamp" in output
# Execution time should be <500ms
```

---

## Step 3: Implement Backend Service Layer

### Create Seasonal Analysis Service

Create file: `src/backend/services/seasonal_analysis.py`

```python
from sqlalchemy import text
from datetime import date
from typing import Dict, List, Any

async def get_seasonal_images(
    session,
    start_date: date,
    end_date: date,
    page: int = 1,
    page_size: int = 100
) -> Dict[str, Any]:
    """
    Query images by date range with pagination.

    Args:
        session: SQLAlchemy async session
        start_date: Start date (inclusive)
        end_date: End date (inclusive)
        page: Page number (1-indexed)
        page_size: Results per page

    Returns:
        Dict with 'images', 'total_count', 'page_metadata'
    """
    # Count total matching images
    count_query = text("""
        SELECT COUNT(*)
        FROM images
        WHERE timestamp BETWEEN :start_date AND :end_date
    """)

    result = await session.execute(count_query, {
        "start_date": start_date,
        "end_date": end_date
    })
    total_count = result.scalar()

    # Paginated query
    offset = (page - 1) * page_size
    data_query = text("""
        SELECT
            id, filename, path, timestamp, location_id, processing_status
        FROM images
        WHERE timestamp BETWEEN :start_date AND :end_date
        ORDER BY timestamp DESC
        LIMIT :limit OFFSET :offset
    """)

    result = await session.execute(data_query, {
        "start_date": start_date,
        "end_date": end_date,
        "limit": page_size,
        "offset": offset
    })

    images = [dict(row._mapping) for row in result]

    return {
        "images": images,
        "total_count": total_count,
        "page_metadata": {
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
            "has_next": page * page_size < total_count,
            "has_previous": page > 1
        }
    }

# Test function
if __name__ == "__main__":
    # Quick test with mock data
    print("[OK] seasonal_analysis.py service created")
```

### Test the Service

Create file: `scripts/test_seasonal_query.py`

```python
import asyncio
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.backend.services.seasonal_analysis import get_seasonal_images

async def test_seasonal_query():
    # Database connection
    DATABASE_URL = "postgresql+asyncpg://deertrack:deerpassword@localhost:5432/deer_tracking"
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Query rut season 2024
        result = await get_seasonal_images(
            session,
            start_date=date(2024, 9, 1),
            end_date=date(2025, 1, 31),
            page=1,
            page_size=10
        )

        print("[INFO] Rut Season Query Results:")
        print(f"  Total images: {result['total_count']}")
        print(f"  Page: {result['page_metadata']['page']}/{result['page_metadata']['total_pages']}")
        print(f"  First 10 images:")
        for img in result['images'][:10]:
            print(f"    - {img['filename']} @ {img['timestamp']}")

        # Verify expected count
        if result['total_count'] == 6115:
            print("[OK] Image count matches expected (6,115)")
        else:
            print(f"[WARN] Expected 6,115 images, got {result['total_count']}")

if __name__ == "__main__":
    asyncio.run(test_seasonal_query())
```

**Run test:**
```bash
cd /mnt/i/projects/thumper_counter
docker-compose exec backend python3 scripts/test_seasonal_query.py

# Expected output:
# [INFO] Rut Season Query Results:
#   Total images: 6115
#   Page: 1/612
#   First 10 images:
#     - SANCTUARY_20250131_165432.jpg @ 2025-01-31 16:54:32
#     ...
# [OK] Image count matches expected (6,115)
```

---

## Step 4: Create API Endpoints

### Seasonal Queries Router

Create file: `src/backend/api/seasonal.py`

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from typing import List, Optional
from ..core.database import get_db
from ..services import seasonal_analysis
from ..schemas.seasonal import SeasonalImagesResponse

router = APIRouter(prefix="/api/seasonal", tags=["Seasonal Queries"])

@router.get("/images", response_model=SeasonalImagesResponse)
async def get_seasonal_images(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: date = Query(..., description="End date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """
    Query images by date range.

    Example:
        GET /api/seasonal/images?start_date=2024-09-01&end_date=2025-01-31&page=1&page_size=100
    """
    # Validate date range
    if end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail=f"end_date ({end_date}) cannot be before start_date ({start_date})"
        )

    result = await seasonal_analysis.get_seasonal_images(
        db, start_date, end_date, page, page_size
    )

    return result

# Add to main.py router registration:
# from .api import seasonal
# app.include_router(seasonal.router)
```

### Register Router

Edit `src/backend/app/main.py`:
```python
from src.backend.api import seasonal

# Add after existing routers
app.include_router(seasonal.router)
```

### Restart Backend
```bash
docker-compose restart backend

# Check logs for successful startup
docker-compose logs backend | tail -20
```

---

## Step 5: Test API Endpoints

### Test with curl

```bash
# Test 1: Query rut season images
curl "http://localhost:8001/api/seasonal/images?start_date=2024-09-01&end_date=2025-01-31&page=1&page_size=10" \
  | jq '.total_count, .page_metadata'

# Expected output:
# 6115
# {
#   "page": 1,
#   "page_size": 10,
#   "total_pages": 612,
#   "has_next": true,
#   "has_previous": false
# }

# Test 2: Query November only (peak rut)
curl "http://localhost:8001/api/seasonal/images?start_date=2024-11-01&end_date=2024-11-30&page=1&page_size=1" \
  | jq '.total_count'

# Expected: ~1500-2000 images

# Test 3: Invalid date range (should return 400 error)
curl -i "http://localhost:8001/api/seasonal/images?start_date=2025-01-31&end_date=2024-09-01"

# Expected: HTTP 400 with error message
```

### Test with Frontend

Navigate to frontend directory and start dev server:
```bash
cd frontend
npm run dev

# Open browser: http://localhost:3000/seasonal-analysis (to be created)
```

---

## Step 6: Frontend Date Picker Integration

### Create Seasonal Analysis Page

Create file: `frontend/src/pages/SeasonalAnalysis.tsx`

```typescript
import React, { useState } from 'react';
import { Box, Typography, Button } from '@mui/material';
import { DateRangePicker } from '@mui/x-date-pickers-pro/DateRangePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import dayjs, { Dayjs } from 'dayjs';

export const SeasonalAnalysis: React.FC = () => {
  const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null]>([
    dayjs('2024-09-01'),  // Rut season start
    dayjs('2025-01-31')   // Rut season end
  ]);

  const handleRunQuery = async () => {
    const [startDate, endDate] = dateRange;
    if (!startDate || !endDate) return;

    const response = await fetch(
      `/api/seasonal/images?start_date=${startDate.format('YYYY-MM-DD')}&end_date=${endDate.format('YYYY-MM-DD')}&page=1&page_size=100`
    );
    const data = await response.json();

    console.log('[INFO] Query results:', data.total_count, 'images');
    console.log('[INFO] Page metadata:', data.page_metadata);
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Seasonal Analysis
        </Typography>

        <DateRangePicker
          value={dateRange}
          onChange={setDateRange}
          localeText={{ start: 'Start Date', end: 'End Date' }}
        />

        <Button
          variant="contained"
          onClick={handleRunQuery}
          sx={{ mt: 2 }}
          disabled={!dateRange[0] || !dateRange[1]}
        >
          Run Analysis
        </Button>

        <Typography variant="body2" sx={{ mt: 2 }}>
          Selected range: {dateRange[0]?.format('YYYY-MM-DD')} to {dateRange[1]?.format('YYYY-MM-DD')}
        </Typography>
      </Box>
    </LocalizationProvider>
  );
};
```

### Add Route

Edit `frontend/src/App.tsx`:
```typescript
import { SeasonalAnalysis } from './pages/SeasonalAnalysis';

// Add route
<Route path="/seasonal-analysis" element={<SeasonalAnalysis />} />
```

### Test Frontend
1. Open browser: `http://localhost:3000/seasonal-analysis`
2. Verify date picker displays (Sept 1, 2024 - Jan 31, 2025)
3. Click "Run Analysis" button
4. Check browser console for query results

---

## Step 7: Generate First PDF Report

### Create PDF Generation Service

Create file: `src/backend/services/report_generator.py`

```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
from typing import Dict, Any
import io

def generate_seasonal_pdf(report_data: Dict[str, Any]) -> bytes:
    """
    Generate PDF report from seasonal analysis data.

    Args:
        report_data: Dict with 'summary', 'periods', 'date_range'

    Returns:
        PDF file as bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title = Paragraph(
        f"Seasonal Activity Report: {report_data['date_range']['start']} to {report_data['date_range']['end']}",
        styles['Title']
    )
    story.append(title)
    story.append(Spacer(1, 0.3 * inch))

    # Summary statistics
    summary = report_data['summary']
    summary_text = f"""
    <b>Summary Statistics:</b><br/>
    Total Detections: {summary['total_detections']}<br/>
    Total Bucks: {summary['total_bucks']}<br/>
    Total Does: {summary['total_does']}<br/>
    Sex Ratio: {summary['overall_sex_ratio']:.2f} bucks per doe<br/>
    """
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))

    # Period statistics table
    table_data = [['Period', 'Total Detections', 'Mature Bucks', 'Does', 'Sex Ratio']]
    for period in report_data['periods']:
        table_data.append([
            period['period_label'],
            str(period['total_detections']),
            str(period['detection_counts_by_classification'].get('mature', 0)),
            str(period['detection_counts_by_classification'].get('doe', 0)),
            f"{period['sex_ratio']:.2f}" if period['sex_ratio'] else 'N/A'
        ])

    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    story.append(Spacer(1, 0.3 * inch))

    # Footer
    footer = Paragraph(
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC<br/>"
        f"Thumper Counter - Hopkins Ranch Wildlife Tracking",
        styles['Italic']
    )
    story.append(footer)

    # Build PDF
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes

# Test function
if __name__ == "__main__":
    # Mock data for testing
    test_data = {
        "date_range": {"start": "2024-09-01", "end": "2025-01-31"},
        "summary": {
            "total_detections": 8543,
            "total_bucks": 3214,
            "total_does": 4129,
            "overall_sex_ratio": 0.78
        },
        "periods": [
            {
                "period_label": "September 2024",
                "total_detections": 481,
                "detection_counts_by_classification": {"mature": 123, "doe": 234},
                "sex_ratio": 1.00
            }
        ]
    }

    pdf_bytes = generate_seasonal_pdf(test_data)

    # Save to file for inspection
    with open("/tmp/test_report.pdf", "wb") as f:
        f.write(pdf_bytes)

    print(f"[OK] PDF generated: {len(pdf_bytes)} bytes")
    print("[INFO] Saved to /tmp/test_report.pdf")
```

**Test PDF generation:**
```bash
docker-compose exec backend python3 src/backend/services/report_generator.py

# Expected output:
# [OK] PDF generated: 45678 bytes
# [INFO] Saved to /tmp/test_report.pdf

# Copy PDF to host for inspection
docker cp $(docker-compose ps -q backend):/tmp/test_report.pdf ./test_report.pdf

# Open test_report.pdf in PDF viewer
```

---

## Common Workflows

### Workflow 1: Wildlife Researcher Analyzes Rut Season

```bash
# Step 1: Query rut season images
curl "http://localhost:8001/api/seasonal/images?start_date=2024-09-01&end_date=2025-01-31" \
  | jq '.total_count'
# Output: 6115

# Step 2: Get buck detections during rut
curl "http://localhost:8001/api/seasonal/detections?start_date=2024-09-01&end_date=2025-01-31&classifications=mature&classifications=mid&classifications=young&page_size=1" \
  | jq '.total_count'
# Output: ~3214

# Step 3: Generate monthly activity report
curl "http://localhost:8001/api/seasonal/reports/activity?start_date=2024-09-01&end_date=2025-01-31&group_by=month" \
  | jq '.summary'

# Step 4: Export PDF report
curl -X POST "http://localhost:8001/api/exports/pdf" \
  -H "Content-Type: application/json" \
  -d '{
    "report_type": "seasonal_activity",
    "start_date": "2024-09-01",
    "end_date": "2025-01-31",
    "title": "Rut Season 2024 Analysis"
  }' | jq '.job_id'
# Output: "pdf-12345678-1234-1234-1234-123456789012"

# Step 5: Poll for completion
curl "http://localhost:8001/api/exports/pdf/pdf-12345678-1234-1234-1234-123456789012" \
  | jq '.status, .download_url'

# Step 6: Download PDF
curl -o rut_season_2024.pdf \
  "http://localhost:8001/api/exports/pdf/pdf-12345678-1234-1234-1234-123456789012/download"
```

### Workflow 2: Compare Three Rut Season Months

```typescript
// Frontend React component
const comparePeriods = async () => {
  const response = await fetch('/api/seasonal/reports/comparison', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      periods: [
        { start_date: '2024-09-01', end_date: '2024-09-30', label: 'September' },
        { start_date: '2024-11-01', end_date: '2024-11-30', label: 'November' },
        { start_date: '2025-01-01', end_date: '2025-01-31', label: 'January' }
      ],
      classifications: ['mature', 'mid', 'young']
    })
  });

  const data = await response.json();
  console.log('[INFO] Peak activity:', data.highlights[0]);
  // Output: "Peak rut activity observed in November (356 mature buck detections)"
};
```

---

## Troubleshooting

### Issue: Query returns 0 images
**Cause**: Database timestamps may be in different timezone
**Fix**:
```sql
-- Check actual timestamp values
SELECT MIN(timestamp), MAX(timestamp) FROM images;

-- Adjust date range if needed
```

### Issue: PDF generation fails with "missing module"
**Cause**: ReportLab not installed in backend container
**Fix**:
```bash
docker-compose exec backend pip install reportlab
docker-compose restart backend
```

### Issue: Date picker not displaying
**Cause**: Missing MUI X Date Pickers dependency
**Fix**:
```bash
cd frontend
npm install @mui/x-date-pickers dayjs
npm run dev
```

---

## Next Steps

1. Implement remaining API endpoints (reports, exports)
2. Add Celery tasks for async PDF/ZIP generation
3. Build complete React frontend with charts
4. Write unit tests for aggregation logic
5. Run `/speckit.tasks` to get granular task breakdown

---

## Useful Commands Reference

```bash
# Backend Development
docker-compose exec backend python3 scripts/test_seasonal_query.py
docker-compose logs -f backend | grep seasonal
docker-compose restart backend

# Frontend Development
cd frontend && npm run dev
cd frontend && npm run build

# Database Queries
docker-compose exec db psql -U deertrack deer_tracking -c "SELECT ..."

# API Testing
curl -X GET "http://localhost:8001/api/seasonal/images?..." | jq
curl -X POST "http://localhost:8001/api/exports/pdf" -d '{...}' | jq

# Documentation
open http://localhost:8001/docs  # Swagger UI (once endpoints registered)
```

---

**Quickstart Complete!** You now have:
- [OK] Database indexes created
- [OK] Backend service layer tested
- [OK] API endpoints operational
- [OK] Frontend date picker integrated
- [OK] PDF generation working

**Estimated time spent**: 30 minutes
**Ready for**: Phase 2 implementation (run `/speckit.tasks` next)
