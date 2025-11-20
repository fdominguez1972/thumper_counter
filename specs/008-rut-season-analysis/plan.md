# Implementation Plan: Rut Season Analysis & Buck Detection Validation

**Branch**: `008-rut-season-analysis` | **Date**: 2025-11-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-rut-season-analysis/spec.md`

## Summary

Implement seasonal analysis and reporting system for rut season (Sept 1 - Jan 31) wildlife activity. This feature adds backend API endpoints for date-based filtering, aggregated statistical reports, and PDF/ZIP export capabilities. Frontend provides visual query interface with date picker, side-by-side period comparison, interactive charts, and drill-down image galleries. System enables non-technical wildlife researchers to analyze 6,115 rut season images across 5 months to validate mature buck detection accuracy (target: >70% confidence) and identify peak activity periods.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.x (frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.104+, SQLAlchemy 2.0+, Pandas 2.x (data aggregation), ReportLab/WeasyPrint (PDF generation)
- Frontend: React 18+, Material-UI v5, Recharts (charts), react-date-picker, jsPDF (PDF export)
- Worker: Celery 5.3+ (async ZIP generation)

**Storage**: PostgreSQL 15 (existing database with images, detections tables)
**Testing**: pytest (backend), Jest/React Testing Library (frontend)
**Target Platform**: Linux Docker containers (backend/worker), modern browsers (frontend)
**Project Type**: Web application (existing React frontend + FastAPI backend)

**Performance Goals**:
- Date range queries: <2 seconds for 12-month spans
- Report aggregation: <5 seconds for full-year analysis
- Chart rendering: <1 second for 5,000 data points
- PDF generation: <10 seconds per report

**Constraints**:
- No new database tables (use existing images, detections, deer)
- Must support 35,251 total images without performance degradation
- Frontend must work at 1280x720 minimum resolution
- PDF reports <5MB file size

**Scale/Scope**:
- Dataset: 6,115 rut season images (Sept-Jan), 35,251 total
- Expected detections: ~8,500 buck detections during rut season
- Users: 2-5 wildlife researchers (low concurrency)
- Reports: 20-50 generated reports per month

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle 1: Wildlife Conservation First ✅ PASS
- **Requirement**: No real-time location broadcasting, delay public data by 48+ hours
- **Implementation**: Date range queries do not expose real-time locations. All data historical. PDF reports aggregate data without specific coordinates.
- **Status**: COMPLIANT

### Principle 2: Data Sovereignty ✅ PASS
- **Requirement**: Ranch data remains under local control, no required internet
- **Implementation**: All processing on-premises. Export functions create local files. No cloud services required.
- **Status**: COMPLIANT

### Principle 3: Operational Simplicity ✅ PASS
- **Requirement**: Operable by non-technical personnel with minimal training
- **Implementation**: Visual date picker eliminates manual date entry. Side-by-side comparison requires no SQL knowledge. PDF reports in plain language.
- **Status**: COMPLIANT (FR-012 through FR-018 specifically designed for non-technical users)

### Principle 4: Scientific Rigor ✅ PASS
- **Requirement**: Documented confidence levels, manual verification support
- **Implementation**: All reports include confidence scores per classification. Export function provides raw data for validation. SC-006 validates rut season accuracy >70%.
- **Status**: COMPLIANT

### Principle 5: Modular Architecture ✅ PASS
- **Requirement**: Independently deployable, testable, replaceable components
- **Implementation**: Backend API endpoints decoupled from frontend. Report generation uses standard REST patterns. PDF/ZIP export via async worker tasks.
- **Status**: COMPLIANT

### Principle 6: Performance Efficiency ✅ PASS
- **Requirement**: Process 35,000+ images within 24 hours
- **Implementation**: No new image processing required (uses existing detections). Query optimization via database indexes. Async export for large datasets.
- **Status**: COMPLIANT (NFR-001 through NFR-005 define performance targets)

### Principle 7: Open Development ✅ PASS
- **Requirement**: Use open-source components, document methods
- **Implementation**: All libraries open-source (FastAPI, React, Recharts, ReportLab). Analysis methods documented in PDF reports.
- **Status**: COMPLIANT

**GATE RESULT**: ✅ ALL PRINCIPLES SATISFIED - Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/008-rut-season-analysis/
├── plan.md              # This file
├── research.md          # Phase 0: Technology choices and best practices
├── data-model.md        # Phase 1: Entity definitions (virtual entities only)
├── quickstart.md        # Phase 1: Developer guide
├── contracts/           # Phase 1: API contracts
│   ├── seasonal-queries.yaml    # Date filtering and detection queries
│   ├── reports.yaml             # Seasonal report aggregation
│   └── exports.yaml             # PDF and ZIP export
└── tasks.md             # Phase 2: Task breakdown (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/src/
├── api/
│   ├── seasonal.py           # NEW: Date filtering, seasonal reports
│   └── exports.py            # NEW: PDF report and ZIP export endpoints
├── services/
│   ├── seasonal_analysis.py  # NEW: Date range logic, aggregation
│   ├── report_generator.py   # NEW: PDF generation (ReportLab)
│   └── export_service.py     # NEW: ZIP creation, CSV generation
├── models/
│   # NO NEW MODELS - uses existing Image, Detection, Deer
└── schemas/
    ├── seasonal.py           # NEW: Pydantic models for seasonal queries
    ├── report.py             # NEW: Report response schemas
    └── export.py             # NEW: Export job schemas

frontend/src/
├── pages/
│   └── SeasonalAnalysis.tsx  # NEW: Main analysis page
├── components/
│   ├── DateRangePicker.tsx   # NEW: Visual calendar picker
│   ├── ComparisonView.tsx    # NEW: Side-by-side period display
│   ├── ActivityChart.tsx     # NEW: Recharts timeline
│   ├── ImageGallery.tsx      # NEW: Filterable gallery with icons
│   └── StatCard.tsx          # NEW: Clickable metric cards
└── services/
    └── seasonalApi.ts        # NEW: API integration layer

worker/src/tasks/
└── export_tasks.py           # NEW: Async ZIP generation

tests/
├── backend/
│   ├── test_seasonal_api.py      # NEW: API endpoint tests
│   ├── test_seasonal_analysis.py # NEW: Aggregation logic tests
│   └── test_report_generator.py  # NEW: PDF generation tests
└── frontend/
    └── SeasonalAnalysis.test.tsx  # NEW: React component tests
```

**Structure Decision**: Using existing web application structure (backend/ + frontend/). This feature adds new API routers and React pages without modifying existing infrastructure.

## Complexity Tracking

No violations detected. All constitutional principles satisfied. No complexity justification required.

---

## Phase 0: Research & Technical Decisions

**Status**: Research needed for PDF library selection and chart library integration.

### Research Questions

1. **PDF Generation Library**: ReportLab vs WeasyPrint for statistical reports
   - Need: Generate multi-page reports with charts (PNG embeds), tables, plain text insights
   - Constraints: Must produce <5MB files for 50 charts + 1000 rows
   - Decision criteria: Ease of use, chart embedding, file size optimization

2. **Frontend Chart Library**: Recharts vs Chart.js for timeline visualizations
   - Need: Interactive timeline charts with 5,000+ data points, responsive rendering
   - Constraints: <1 second render time, supports drill-down clicks
   - Decision criteria: React integration, performance, customization

3. **Date Picker Component**: Material-UI DatePicker vs react-date-picker
   - Need: Range selection, month-level granularity, visual calendar
   - Constraints: Must support min screen resolution 1280x720
   - Decision criteria: MUI integration, accessibility, range selection UX

4. **Aggregation Strategy**: Raw SQL vs Pandas vs SQLAlchemy ORM
   - Need: Month-by-month detection counts, average confidence by classification
   - Constraints: <5 seconds for full-year aggregation
   - Decision criteria: Performance, maintainability, type safety

**Output**: research.md documenting final technology choices with rationale

---

## Phase 1: Design & Contracts

### Data Model (Existing Entities Only - No New Tables)

**No new database tables required.** This feature uses existing schema:

```sql
-- EXISTING (no changes)
images (id, filename, path, timestamp, location_id, processing_status, ...)
detections (id, image_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2, confidence, classification, deer_id, ...)
deer (id, name, sex, species, ...)
```

**Virtual Entities** (application-level only):

1. **SeasonalFilter** - Predefined date range constants
2. **SeasonalReport** - Aggregated statistics structure
3. **ComparisonResult** - Multi-period comparison data
4. **PDFReport** - Generated report metadata
5. **ExportJob** - Async export task status
6. **QuerySession** - Frontend state (React context)

**Database Indexes** (performance optimization):

```sql
-- Ensure timestamp index exists for fast date queries
CREATE INDEX IF NOT EXISTS idx_images_timestamp ON images(timestamp);

-- Composite index for common query pattern
CREATE INDEX IF NOT EXISTS idx_detections_classification_confidence
  ON detections(classification, confidence);
```

**Output**: data-model.md with entity definitions and index requirements

### API Contracts

#### Contract 1: Seasonal Queries (`contracts/seasonal-queries.yaml`)

```yaml
GET /api/seasonal/images:
  parameters:
    - start_date: string (YYYY-MM-DD)
    - end_date: string (YYYY-MM-DD)
    - season: enum (rut_season, spring, summer, fall) [optional]
    - year: integer [optional, default: current year]
    - page: integer [default: 1]
    - page_size: integer [default: 100, max: 1000]
  response:
    - images: array of Image objects
    - total_count: integer
    - page_metadata: {page, page_size, total_pages, has_next}

GET /api/seasonal/detections:
  parameters:
    - start_date: string
    - end_date: string
    - classifications: array of strings [e.g., ['mature', 'mid', 'young']]
    - min_confidence: float [optional, default: 0.0]
    - page: integer
    - page_size: integer
  response:
    - detections: array of Detection objects
    - total_count: integer
    - page_metadata: object
```

#### Contract 2: Reports (`contracts/reports.yaml`)

```yaml
GET /api/seasonal/reports/activity:
  parameters:
    - start_date: string
    - end_date: string
    - group_by: enum (month, week, day) [default: month]
  response:
    - periods: array of {period_label, detection_counts_by_classification, avg_confidence_by_classification, sex_ratio}
    - summary: {total_detections, total_bucks, total_does, overall_sex_ratio}
    - comparisons: array of {comparison_type, baseline_value, current_value, percent_change, statistical_significance}

GET /api/seasonal/reports/comparison:
  parameters:
    - periods: array of {start_date, end_date, label}
  response:
    - period_stats: array of period-specific statistics
    - differences: array of notable statistical differences
    - highlights: array of insights (e.g., "November shows 45% increase")
```

#### Contract 3: Exports (`contracts/exports.yaml`)

```yaml
POST /api/exports/pdf:
  body:
    - report_type: enum (seasonal_activity, comparison, custom)
    - start_date: string
    - end_date: string
    - include_charts: boolean [default: true]
    - include_tables: boolean [default: true]
  response:
    - job_id: string
    - status: "processing"
    - estimated_completion: datetime

GET /api/exports/pdf/{job_id}:
  response:
    - job_id: string
    - status: enum (processing, completed, failed)
    - download_url: string [if completed]
    - error_message: string [if failed]

POST /api/exports/zip:
  body:
    - detection_ids: array of UUIDs
    - include_crops: boolean
    - include_metadata_csv: boolean
  response:
    - job_id: string
    - status: "processing"
```

**Output**: 3 YAML contract files in `contracts/` directory

### Quickstart Guide

**Output**: quickstart.md with:
- Environment setup (Python deps: reportlab, pandas)
- Running seasonal query example
- Generating first PDF report
- Frontend date picker usage
- Testing seasonal endpoints

---

## Implementation Phases

### Phase 0 Deliverables (Research)
- ✅ research.md (technology decisions documented)

### Phase 1 Deliverables (Design)
- ✅ data-model.md (virtual entities, no new tables)
- ✅ contracts/seasonal-queries.yaml
- ✅ contracts/reports.yaml
- ✅ contracts/exports.yaml
- ✅ quickstart.md (developer guide)
- ✅ Agent context updated

### Phase 2 Deliverables (Task Planning - via `/speckit.tasks`)
- tasks.md with granular implementation tasks

---

## Dependencies

### External Dependencies (Already Installed)
- FastAPI, SQLAlchemy, PostgreSQL (existing backend)
- React, Material-UI (existing frontend)
- Celery, Redis (existing worker infrastructure)

### New Dependencies Required
**Backend:**
- `reportlab` or `weasyprint` (PDF generation)
- `pandas` (data aggregation)
- `pillow` (chart image embedding in PDFs)

**Frontend:**
- `recharts` (charts)
- `react-date-picker` or MUI DateRangePicker (date selection)
- `jspdf` (optional: client-side PDF export)

### Internal Dependencies
- Existing Image, Detection, Deer models
- Existing Celery infrastructure for async tasks
- Existing API authentication/authorization

---

## Risks and Mitigations

### Risk 1: PDF File Size Exceeds 5MB
**Likelihood**: Medium
**Impact**: High (violates NFR-008)
**Mitigation**: Compress chart images to PNG with optimization, limit charts to 50 per report, paginate large tables

### Risk 2: Date Range Queries Timeout on Large Datasets
**Likelihood**: Low
**Impact**: High (violates NFR-001: <2 seconds)
**Mitigation**: Database indexes on timestamp column, query optimization with EXPLAIN ANALYZE, consider materialized views for common aggregations

### Risk 3: Frontend Chart Rendering Performance
**Likelihood**: Medium
**Impact**: Medium (violates NFR-007: <1 second)
**Mitigation**: Data sampling for large datasets (5000+ points), lazy rendering with virtualization, debounce comparison updates

### Risk 4: Timezone Confusion in Date Filtering
**Likelihood**: Medium
**Impact**: Medium (incorrect season boundaries)
**Mitigation**: All timestamps UTC in database, explicit timezone handling in API, user documentation clarifies UTC boundaries

---

## Success Metrics

**After Implementation:**
1. All 6 backend success criteria met (SC-001 through SC-006)
2. All 5 frontend success criteria met (SC-007 through SC-011)
3. Wildlife researcher completes 3-period analysis in <5 minutes without SQL knowledge
4. November correctly identified as peak rut month with >30% increase vs September

**Performance Benchmarks:**
- Date query: <2 seconds for 12-month range (measured with 35,251 images)
- Report generation: <5 seconds for full year (measured with real dataset)
- PDF export: <10 seconds for single period
- Chart render: <1 second for 5,000 detections

---

## Next Steps

1. ✅ Complete Phase 0 research (technology selections)
2. ✅ Complete Phase 1 design (contracts, data model, quickstart)
3. Run `/speckit.tasks` to generate granular task breakdown
4. Begin implementation following tasks.md

**Current Status**: Plan complete. Ready for Phase 0 research execution.
