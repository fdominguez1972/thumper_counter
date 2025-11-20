# Tasks: Rut Season Analysis & Buck Detection Validation

**Input**: Design documents from `/specs/008-rut-season-analysis/`
**Prerequisites**: plan.md (complete), spec.md (complete), research.md (complete), data-model.md (complete), contracts/ (complete)

**Tests**: Tests are NOT included in this feature - focus on implementation and manual validation via quickstart.md scenarios

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4, US5)
- Include exact file paths in descriptions

## Path Conventions

This project uses web app structure:
- Backend: `src/backend/`
- Frontend: `frontend/src/`
- Worker: `src/worker/`
- Database: PostgreSQL 15 (existing)

---

## Phase 1: Setup (Dependencies & Configuration)

**Purpose**: Install required libraries and verify environment readiness

- [ ] T001 [P] Add ReportLab and Pandas to backend requirements.txt
- [ ] T002 [P] Install @mui/x-date-pickers and dayjs in frontend/package.json (verify already installed from Sprint 10)
- [ ] T003 [P] Verify Recharts installed in frontend (from Sprint 10)
- [ ] T004 Rebuild backend Docker container with new dependencies
- [ ] T005 [P] Verify ReportLab import in backend container: `docker-compose exec backend python3 -c "import reportlab; print(reportlab.Version)"`

**Checkpoint**: All dependencies installed and verified

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Database indexes and shared schemas that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create database migration script `migrations/010_add_seasonal_indexes.sql`
  - CREATE INDEX idx_images_timestamp ON images(timestamp)
  - CREATE INDEX idx_detections_classification_confidence ON detections(classification, confidence DESC)
- [ ] T007 Run database migration: `docker-compose exec db psql -U deertrack deer_tracking < migrations/010_add_seasonal_indexes.sql`
- [ ] T008 [P] Verify indexes created: `docker-compose exec db psql -U deertrack deer_tracking -c "\di idx_images_timestamp"`
- [ ] T009 [P] Create SeasonalFilter enum in `src/backend/models/seasonal.py`
  - Define RUT_SEASON (Sept 1 - Jan 31, crosses_year=True)
  - Define SPRING, SUMMER, FALL presets
  - Add get_date_range(season, year) static method
- [ ] T010 [P] Create Pydantic schemas in `src/backend/schemas/seasonal.py`
  - SeasonalImagesResponse (images, total_count, page_metadata)
  - SeasonalDetectionsResponse (detections, total_count, page_metadata)
  - PageMetadata (page, page_size, total_pages, has_next, has_previous)
- [ ] T011 [P] Create Pydantic schemas in `src/backend/schemas/report.py`
  - PeriodStats (period_label, period_start, period_end, detection_counts_by_classification, avg_confidence_by_classification, sex_ratio, total_images, total_detections)
  - SeasonalReport (periods, summary, comparisons, generated_at, date_range)
  - ComparisonPeriod (label, start_date, end_date, stats)
  - ComparisonDifference (metric, period_1_value, period_2_value, absolute_change, percent_change, interpretation)
  - ComparisonResult (period_stats, differences, highlights, generated_at)
  - Comparison (comparison_type, baseline_value, current_value, percent_change, statistical_significance, interpretation)
- [ ] T012 [P] Create Pydantic schemas in `src/backend/schemas/export.py`
  - PDFReportRequest (report_type, start_date, end_date, comparison_periods, include_charts, include_tables, include_insights, group_by, classifications, title)
  - PDFReportResponse (job_id, status, message, estimated_completion)
  - PDFStatusResponse (job_id, status, download_url, file_size_bytes, error_message, created_at, completed_at, expires_at)
  - ZIPExportRequest (detection_ids, include_crops, include_metadata_csv, crop_size)
  - ZIPExportResponse (job_id, status, total_detections, message, estimated_completion)
  - ZIPStatusResponse (job_id, status, total_detections, processed_count, progress_percent, download_url, file_size_bytes, error_message, created_at, completed_at, estimated_completion, expires_at)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Filter Images by Rut Season (Priority: P1) 🎯 MVP

**Goal**: Enable date range filtering of trail camera images via API endpoint

**Independent Test**:
```bash
curl "http://localhost:8001/api/seasonal/images?start_date=2024-09-01&end_date=2025-01-31&page=1&page_size=10" | jq '.total_count'
# Expected: 6115 images
```

### Implementation for User Story 1

- [ ] T013 [P] [US1] Create seasonal analysis service in `src/backend/services/seasonal_analysis.py`
  - Implement async get_seasonal_images(session, start_date, end_date, location_id, processing_status, page, page_size)
  - Use raw SQL with text() for performance (as per research.md decision)
  - Count query for total_count
  - Paginated query with LIMIT/OFFSET
  - Return dict with images, total_count, page_metadata
- [ ] T014 [US1] Create seasonal queries router in `src/backend/api/seasonal.py`
  - Import seasonal_analysis service
  - Define router with prefix="/api/seasonal"
  - Implement GET /api/seasonal/images endpoint
  - Parameters: start_date (required), end_date (required), season (optional), year (optional), location_id (optional), processing_status (optional), page (default 1), page_size (default 100, max 1000)
  - Validate: end_date >= start_date (raise HTTPException 400 if invalid)
  - Handle season parameter: call SeasonalFilter.get_date_range() if provided
  - Call seasonal_analysis.get_seasonal_images()
  - Return SeasonalImagesResponse
- [ ] T015 [US1] Register seasonal router in `src/backend/app/main.py`
  - Import seasonal router: from ..api import seasonal
  - Add: app.include_router(seasonal.router)
- [ ] T016 [US1] Restart backend container: `docker-compose restart backend`
- [ ] T017 [US1] Test seasonal images endpoint with curl (rut season query)
  - Query: start_date=2024-09-01, end_date=2025-01-31
  - Verify: total_count matches expected 6115
  - Verify: page_metadata.total_pages = 62 (at page_size=100)
- [ ] T018 [P] [US1] Test with seasonal preset: `curl "http://localhost:8001/api/seasonal/images?season=rut_season&year=2024&page_size=1" | jq`
- [ ] T019 [P] [US1] Test invalid date range (should return 400): `curl -i "http://localhost:8001/api/seasonal/images?start_date=2025-01-31&end_date=2024-09-01"`

**Checkpoint**: At this point, seasonal image filtering should be fully functional and independently testable

---

## Phase 4: User Story 2 - Query Buck Detections by Season (Priority: P1)

**Goal**: Enable querying of buck detections filtered by date range and classification

**Independent Test**:
```bash
curl "http://localhost:8001/api/seasonal/detections?start_date=2024-09-01&end_date=2025-01-31&classifications=mature&classifications=mid&classifications=young&page_size=1" | jq '.total_count'
# Expected: ~3214 buck detections
```

### Implementation for User Story 2

- [ ] T020 [P] [US2] Add get_seasonal_detections() to `src/backend/services/seasonal_analysis.py`
  - Parameters: session, start_date, end_date, classifications (list), min_confidence (float), location_id, deer_id, page, page_size
  - JOIN detections with images on image_id
  - Filter by image timestamp (use idx_images_timestamp)
  - Filter by classification IN (classifications) if provided (use idx_detections_classification_confidence)
  - Filter by confidence >= min_confidence if provided
  - Include deer_name in SELECT (LEFT JOIN deer table)
  - Return dict with detections, total_count, page_metadata
- [ ] T021 [US2] Add GET /api/seasonal/detections endpoint to `src/backend/api/seasonal.py`
  - Parameters: start_date, end_date, season, year, classifications (array), min_confidence (default 0.0), location_id, deer_id, page, page_size
  - Validate: classifications must be valid enum values
  - Validate: min_confidence between 0.0 and 1.0
  - Handle season parameter if provided
  - Call seasonal_analysis.get_seasonal_detections()
  - Return SeasonalDetectionsResponse
- [ ] T022 [US2] Test detections endpoint with all buck classifications
  - Query: start_date=2024-09-01, end_date=2025-01-31, classifications=['mature', 'mid', 'young']
  - Verify: total_count > 0
  - Verify: all returned detections have classification in ['mature', 'mid', 'young']
- [ ] T023 [P] [US2] Test with min_confidence filter: `curl "http://localhost:8001/api/seasonal/detections?start_date=2024-09-01&end_date=2025-01-31&min_confidence=0.7" | jq '.detections[0].confidence'`
- [ ] T024 [P] [US2] Test November mature bucks only: `curl "http://localhost:8001/api/seasonal/detections?start_date=2024-11-01&end_date=2024-11-30&classifications=mature&page_size=10" | jq '.total_count'`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Seasonal Activity Reports (Priority: P2)

**Goal**: Generate aggregated statistical reports with month-by-month breakdown and comparisons

**Independent Test**:
```bash
curl "http://localhost:8001/api/seasonal/reports/activity?start_date=2024-09-01&end_date=2025-01-31&group_by=month" | jq '.summary.total_detections, .periods | length'
# Expected: 8543 detections, 5 periods (Sept, Oct, Nov, Dec, Jan)
```

### Implementation for User Story 3

- [ ] T025 [P] [US3] Add get_seasonal_activity() to `src/backend/services/seasonal_analysis.py`
  - Parameters: session, start_date, end_date, group_by ('month'|'week'|'day'), classifications, location_id, include_comparison
  - Raw SQL query with DATE_TRUNC(group_by, timestamp) for period grouping
  - GROUP BY period, classification
  - Aggregate: COUNT(*) as detection_count, AVG(confidence) as avg_confidence
  - Calculate sex_ratio per period: (mature + mid + young) / doe
  - Build summary dict: total_detections, total_bucks, total_does, total_fawns, overall_sex_ratio, peak_activity_period
  - If include_comparison=true: query baseline period (non-seasonal months) and compute statistical comparisons
  - Return SeasonalReport object
- [ ] T026 [P] [US3] Add compare_periods() to `src/backend/services/seasonal_analysis.py`
  - Parameters: session, periods (list of {start_date, end_date, label}), classifications, location_id
  - For each period: call get_seasonal_activity() without comparison
  - Compute differences between consecutive periods
  - Generate highlights (e.g., "Peak activity in November", "Sex ratio shifted from 1.00 to 1.92")
  - Return ComparisonResult object
- [ ] T027 [US3] Create reports router in `src/backend/api/reports.py`
  - Define router with prefix="/api/seasonal/reports"
  - Implement GET /api/seasonal/reports/activity endpoint
  - Parameters: start_date (required), end_date (required), group_by (default 'month'), classifications (optional), location_id (optional), include_comparison (default false)
  - Call seasonal_analysis.get_seasonal_activity()
  - Return SeasonalReport
- [ ] T028 [US3] Add POST /api/seasonal/reports/comparison endpoint to `src/backend/api/reports.py`
  - Request body: periods (2-5 objects with start_date, end_date, label), classifications, location_id
  - Validate: periods array has 2-5 items
  - Validate: all dates are valid
  - Call seasonal_analysis.compare_periods()
  - Return ComparisonResult
- [ ] T029 [US3] Register reports router in `src/backend/app/main.py`
  - Import reports router: from ..api import reports
  - Add: app.include_router(reports.router)
- [ ] T030 [US3] Restart backend: `docker-compose restart backend`
- [ ] T031 [US3] Test activity report endpoint (rut season monthly)
  - Query: start_date=2024-09-01, end_date=2025-01-31, group_by=month
  - Verify: periods array has 5 objects (Sept, Oct, Nov, Dec, Jan)
  - Verify: summary.total_detections matches expected
  - Verify: each period has detection_counts_by_classification dict
- [ ] T032 [P] [US3] Test comparison endpoint with 3 periods (Sept, Nov, Jan)
  - POST body with 3 period objects
  - Verify: period_stats array has 3 objects
  - Verify: differences array shows comparisons
  - Verify: highlights array contains peak activity insight
- [ ] T033 [P] [US3] Test with include_comparison=true: `curl "http://localhost:8001/api/seasonal/reports/activity?start_date=2024-09-01&end_date=2025-01-31&group_by=month&include_comparison=true" | jq '.comparisons'`

**Checkpoint**: All backend API endpoints (US1, US2, US3) should now be functional and independently testable

---

## Phase 6: User Story 4 - Ad-Hoc Query Interface for Wildlife Researchers (Priority: P2)

**Goal**: Build React frontend for visual date selection, comparison views, and interactive charts

**Independent Test**:
1. Open http://localhost:3000/seasonal-analysis
2. Use date picker to select Sept 1 - Jan 31
3. Click "Run Analysis"
4. Verify detection counts and charts display
5. Add second period (Nov 1 - Nov 30)
6. Verify side-by-side comparison displays

### Implementation for User Story 4

- [ ] T034 [P] [US4] Create API service in `frontend/src/api/seasonalApi.ts`
  - getSeasonalImages(startDate, endDate, page, pageSize) -> Promise<SeasonalImagesResponse>
  - getSeasonalDetections(startDate, endDate, classifications, minConfidence, page, pageSize) -> Promise<SeasonalDetectionsResponse>
  - getActivityReport(startDate, endDate, groupBy) -> Promise<SeasonalReport>
  - comparePerio ds(periods) -> Promise<ComparisonResult>
  - Use axios for HTTP requests
  - Handle errors with try/catch
- [ ] T035 [P] [US4] Create TypeScript types in `frontend/src/types/seasonal.ts`
  - SeasonalImagesResponse, SeasonalDetectionsResponse
  - SeasonalReport, PeriodStats, ComparisonResult
  - Copy structure from backend Pydantic schemas
- [ ] T036 [P] [US4] Create DateRangePicker component in `frontend/src/components/DateRangePicker.tsx`
  - Use @mui/x-date-pickers DateRangePicker
  - LocalizationProvider with dayjs
  - Props: value (tuple), onChange callback
  - Display selected range preview with image count estimate
  - Apply MUI theme colors (olive green for selected dates)
- [ ] T037 [P] [US4] Create StatCard component in `frontend/src/components/StatCard.tsx`
  - Props: title, value, subtitle, icon, onClick (optional)
  - Material-UI Card with hover effect
  - Clickable if onClick provided (navigate to filtered view)
  - Typography for title, large value, small subtitle
- [ ] T038 [P] [US4] Create ActivityChart component in `frontend/src/components/ActivityChart.tsx`
  - Use Recharts LineChart or BarChart
  - Props: data (array of PeriodStats), xAxisKey ('period_label'), yAxisKey ('total_detections' or classification)
  - Responsive container
  - Tooltip showing detection counts
  - Legend for multiple classifications
  - onClick handler for drill-down (optional)
- [ ] T039 [P] [US4] Create ComparisonView component in `frontend/src/components/ComparisonView.tsx`
  - Props: periods (array of ComparisonPeriod), differences, highlights
  - Layout: Grid with one column per period
  - Each period shows: label, date range, stats (total detections, bucks, does, sex ratio)
  - Differences section below with arrows showing increases/decreases
  - Highlights section with plain language insights
- [ ] T040 [P] [US4] Create ImageGallery component in `frontend/src/components/ImageGallery.tsx`
  - Props: images (array), onImageClick
  - Grid layout with lazy loading (IntersectionObserver or react-window)
  - Thumbnail for each image
  - Badge showing detection count
  - Click to open lightbox (future enhancement)
- [ ] T041 [US4] Create SeasonalAnalysis page in `frontend/src/pages/SeasonalAnalysis.tsx`
  - State: dateRange (start/end), selectedPeriods (array), comparisonMode (boolean), activityReport, comparisonResult
  - UI Layout:
    - Header with title "Seasonal Analysis"
    - DateRangePicker for primary date range
    - Button "Run Analysis" (calls getActivityReport)
    - Button "Add Period" (adds to selectedPeriods array for comparison)
    - Button "Compare Periods" (calls comparePeriods if selectedPeriods.length >= 2)
    - StatCard grid (total detections, total bucks, total does, sex ratio)
    - ActivityChart showing detection timeline
    - ComparisonView (conditional render if comparisonMode=true)
    - ImageGallery showing filtered images from getSeasonalImages
  - React Query for data fetching with 5-minute cache
  - Error handling with MUI Alert
  - Loading state with MUI CircularProgress
- [ ] T042 [US4] Add route to `frontend/src/App.tsx`
  - Import SeasonalAnalysis component
  - Add route: <Route path="/seasonal-analysis" element={<SeasonalAnalysis />} />
- [ ] T043 [US4] Add navigation link in `frontend/src/components/Layout.tsx` or sidebar
  - Add "Seasonal Analysis" menu item linking to /seasonal-analysis
- [ ] T044 [US4] Test frontend workflow:
  - Navigate to http://localhost:3000/seasonal-analysis
  - Select date range (Sept 1 - Jan 31) using date picker
  - Click "Run Analysis"
  - Verify: Stat cards populate with correct values
  - Verify: ActivityChart displays 5 months (Sept, Oct, Nov, Dec, Jan)
  - Verify: Image gallery displays paginated images
- [ ] T045 [P] [US4] Test comparison workflow:
  - Add second period (Nov 1 - Nov 30)
  - Click "Compare Periods"
  - Verify: ComparisonView displays side-by-side stats
  - Verify: Highlights show "Peak activity in November"
- [ ] T046 [P] [US4] Test stat card click navigation (if implemented)
  - Click "Total Bucks" stat card
  - Verify: Navigates to filtered deer gallery or image browser

**Checkpoint**: Frontend should now provide complete visual query interface for wildlife researchers

---

## Phase 7: User Story 5 - Export Buck Detection Dataset (Priority: P3)

**Goal**: Enable PDF report generation and ZIP export of detection crops with metadata

**Independent Test**:
```bash
# Test 1: PDF export
curl -X POST "http://localhost:8001/api/exports/pdf" \
  -H "Content-Type: application/json" \
  -d '{"report_type": "seasonal_activity", "start_date": "2024-09-01", "end_date": "2025-01-31", "title": "Rut Season 2024"}' \
  | jq '.job_id'
# Poll status until completed, then download

# Test 2: ZIP export (get detection IDs from US2 endpoint first)
curl -X POST "http://localhost:8001/api/exports/zip" \
  -H "Content-Type: application/json" \
  -d '{"detection_ids": ["det-uuid-1", "det-uuid-2"], "include_crops": true, "include_metadata_csv": true}' \
  | jq '.job_id'
```

### Implementation for User Story 5

- [ ] T047 [P] [US5] Create report generator service in `src/backend/services/report_generator.py`
  - Import ReportLab: SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
  - Implement generate_seasonal_pdf(report_data: dict) -> bytes
  - Input: report_data with summary, periods, date_range
  - Layout: Title, summary statistics, period statistics table, footer with timestamp
  - Apply TableStyle: header background grey, grid borders, centered text
  - Return PDF as bytes (using io.BytesIO buffer)
  - Target file size: <5MB (compress chart images to JPEG quality 85)
- [ ] T048 [P] [US5] Create export service in `src/backend/services/export_service.py`
  - Implement create_detection_crops_zip(detection_ids: list, include_crops: bool, include_metadata_csv: bool, crop_size: int) -> tuple[bytes, dict]
  - Query detections by IDs with JOIN to images
  - For each detection: load image from filesystem, crop using bbox coordinates, resize to crop_size x crop_size
  - Create metadata CSV with columns: detection_id, image_id, filename, timestamp, classification, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2, deer_id, deer_name
  - Create ZIP archive in memory (io.BytesIO)
  - Add crops to ZIP: {detection_id}.jpg
  - Add metadata.csv to ZIP
  - Return ZIP bytes and metadata dict (total_detections, file_size)
- [ ] T049 [P] [US5] Create Celery task in `src/worker/tasks/pdf_export.py`
  - @shared_task(bind=True) def generate_pdf_report(self, report_data: dict, job_id: str) -> dict
  - Call seasonal_analysis.get_seasonal_activity() or compare_periods() to get report_data
  - Call report_generator.generate_seasonal_pdf(report_data)
  - Save PDF to /tmp/reports/{job_id}.pdf
  - Update task progress: self.update_state(state='PROCESSING', meta={'status': 'generating'})
  - Return dict with download_url, file_size_bytes
  - On exception: update state to FAILURE, log error
- [ ] T050 [P] [US5] Create Celery task in `src/worker/tasks/zip_export.py`
  - @shared_task(bind=True) def export_detection_crops(self, detection_ids: list, include_crops: bool, include_metadata_csv: bool, crop_size: int, job_id: str) -> dict
  - Call export_service.create_detection_crops_zip()
  - Save ZIP to /tmp/exports/{job_id}.zip
  - Update task progress periodically: self.update_state(state='PROCESSING', meta={'processed_count': N})
  - Return dict with download_url, file_size_bytes, total_detections
  - On exception: log error, update state to FAILURE
- [ ] T051 [US5] Create exports router in `src/backend/api/exports.py`
  - Define router with prefix="/api/exports"
  - Implement POST /api/exports/pdf endpoint
  - Request body: PDFReportRequest schema
  - Validate: report_type in ['seasonal_activity', 'comparison']
  - Validate: if comparison, comparison_periods has 2-5 items
  - Generate report_data by calling seasonal_analysis service
  - Queue Celery task: pdf_export.generate_pdf_report.delay(report_data, job_id)
  - Return PDFReportResponse with job_id, status='processing'
- [ ] T052 [P] [US5] Add GET /api/exports/pdf/{job_id} endpoint to `src/backend/api/exports.py`
  - Query Celery task status: AsyncResult(job_id)
  - Map Celery states: PENDING -> 'pending', SUCCESS -> 'completed', FAILURE -> 'failed'
  - If completed: include download_url, file_size_bytes
  - If failed: include error_message
  - Return PDFStatusResponse
- [ ] T053 [P] [US5] Add GET /api/exports/pdf/{job_id}/download endpoint to `src/backend/api/exports.py`
  - Check if PDF file exists at /tmp/reports/{job_id}.pdf
  - If not exists: return 404
  - Return FileResponse with application/pdf content type
  - Set Content-Disposition header: attachment; filename="rut_season_report.pdf"
- [ ] T054 [P] [US5] Add POST /api/exports/zip endpoint to `src/backend/api/exports.py`
  - Request body: ZIPExportRequest schema
  - Validate: detection_ids array has 1-10000 items
  - Validate: all UUIDs are valid
  - Queue Celery task: zip_export.export_detection_crops.delay(detection_ids, include_crops, include_metadata_csv, crop_size, job_id)
  - Return ZIPExportResponse with job_id, status='processing', total_detections
- [ ] T055 [P] [US5] Add GET /api/exports/zip/{job_id} endpoint to `src/backend/api/exports.py`
  - Query Celery task status and progress (AsyncResult.info for processed_count)
  - Calculate progress_percent: (processed_count / total_detections) * 100
  - Estimate completion time based on processing rate
  - Return ZIPStatusResponse
- [ ] T056 [P] [US5] Add GET /api/exports/zip/{job_id}/download endpoint to `src/backend/api/exports.py`
  - Check if ZIP file exists at /tmp/exports/{job_id}.zip
  - Return FileResponse with application/zip content type
  - Set Content-Disposition header with filename
- [ ] T057 [US5] Register exports router in `src/backend/app/main.py`
  - Import exports router
  - Add: app.include_router(exports.router)
- [ ] T058 [US5] Restart backend and worker: `docker-compose restart backend worker`
- [ ] T059 [US5] Test PDF export workflow:
  - POST to /api/exports/pdf with seasonal_activity report
  - Capture job_id from response
  - Poll GET /api/exports/pdf/{job_id} every 2 seconds
  - When status='completed', download PDF from /download endpoint
  - Verify PDF opens correctly, contains summary and table
  - Verify file size <5MB
- [ ] T060 [P] [US5] Test ZIP export workflow:
  - Query detections endpoint to get 10 detection IDs
  - POST to /api/exports/zip with detection_ids
  - Poll status endpoint for progress
  - Download ZIP when completed
  - Extract ZIP, verify crops and metadata.csv present
  - Verify CSV has correct columns and row count matches detection count
- [ ] T061 [P] [US5] Test comparison PDF export:
  - POST to /api/exports/pdf with report_type='comparison' and 3 periods
  - Verify generated PDF has comparison tables and highlights

**Checkpoint**: All user stories (US1-US5) should now be functional and independently testable

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements that affect multiple user stories

- [ ] T062 [P] Create automated cleanup script for expired reports in `scripts/cleanup_exports.sh`
  - Delete PDFs older than 24 hours from /tmp/reports/
  - Delete ZIPs older than 7 days from /tmp/exports/
  - Log cleanup actions
- [ ] T063 [P] Add cron job or systemd timer to run cleanup script daily
- [ ] T064 [P] Performance validation: run quickstart.md test scenarios
  - Verify: Date range query <2 seconds for 12-month span
  - Verify: Report generation <5 seconds for full year
  - Verify: PDF generation <10 seconds
  - Verify: Chart rendering <1 second for 5,000 points
  - Document actual performance in quickstart.md
- [ ] T065 [P] Error handling review across all endpoints
  - Verify all 400 errors have descriptive messages
  - Verify all 500 errors are logged with stack traces
  - Verify database connection errors are handled gracefully
- [ ] T066 [P] Add API endpoint documentation strings (docstrings)
  - All endpoints have description, parameters, response examples
  - Swagger UI at http://localhost:8001/docs displays complete documentation
- [ ] T067 [P] Frontend error handling improvements
  - Add error boundaries to SeasonalAnalysis page
  - Display user-friendly error messages (not raw API errors)
  - Add retry buttons for failed requests
- [ ] T068 [P] Accessibility review for frontend components
  - Date picker keyboard navigation works
  - Charts have alt text or aria-labels
  - Buttons have descriptive labels
  - Color contrast meets WCAG AA standards
- [ ] T069 Validate all success criteria from spec.md
  - SC-001: Date range returns 6,115 images for rut season
  - SC-003: November shows statistically significant increase in mature bucks
  - SC-004: Export generates complete ZIP with 100% of crops
  - SC-005: Query performance <2 seconds
  - SC-006: Model confidence >70% for rut season bucks
  - SC-007: Wildlife researcher completes 3-period analysis in <5 minutes
  - SC-008: Side-by-side comparison loads in <3 seconds
  - SC-009: PDF generates in <10 seconds
  - SC-010: Image gallery loads 100 thumbnails in <2 seconds
  - SC-011: November correctly identified as peak (>30% increase vs Sept)
- [ ] T070 [P] Update CLAUDE.md with feature implementation notes
  - Add rut season analysis to completed features section
  - Document new API endpoints
  - Note performance benchmarks achieved

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational - No dependencies on other stories
- **User Story 2 (Phase 4)**: Depends on Foundational - No dependencies on other stories (can run parallel with US1)
- **User Story 3 (Phase 5)**: Depends on Foundational - No dependencies on other stories (can run parallel with US1/US2)
- **User Story 4 (Phase 6)**: Depends on US1, US2, US3 being complete (frontend needs backend APIs)
- **User Story 5 (Phase 7)**: Depends on US2, US3 (uses detections and reports for export)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Independent - can start immediately after Foundational
- **US2 (P1)**: Independent - can start immediately after Foundational (parallel with US1)
- **US3 (P2)**: Independent - can start immediately after Foundational (parallel with US1/US2)
- **US4 (P2)**: Depends on US1, US2, US3 (needs backend APIs operational)
- **US5 (P3)**: Depends on US2, US3 (uses detection queries and reports)

### Within Each User Story

**User Story 1:**
- T013 (service) can start first
- T014 (endpoint) depends on T013
- T015 (router registration) depends on T014
- T016 (restart) depends on T015
- T017-T019 (tests) depend on T016

**User Story 2:**
- T020 (service) can start first
- T021 (endpoint) depends on T020
- T022-T024 (tests) depend on T021

**User Story 3:**
- T025, T026 (services) can run in parallel
- T027, T028 (endpoints) depend on T025/T026
- T029 (router registration) depends on T027/T028
- T030 (restart) depends on T029
- T031-T033 (tests) depend on T030

**User Story 4:**
- T034, T035, T036, T037, T038, T039, T040 (components) can all run in parallel
- T041 (page) depends on all components
- T042, T043 (routing) can run in parallel with T041
- T044-T046 (tests) depend on T041/T042/T043

**User Story 5:**
- T047, T048, T049, T050 (services and tasks) can run in parallel
- T051-T056 (endpoints) depend on T047-T050
- T057 (router registration) depends on T051-T056
- T058 (restart) depends on T057
- T059-T061 (tests) depend on T058

### Parallel Opportunities

- **Setup**: T001, T002, T003, T005 can run in parallel (different files)
- **Foundational**: T008, T009, T010, T011, T012 can run in parallel after T006/T007
- **US1**: T018, T019 (tests) can run in parallel
- **US2**: T020 (service) and T023, T024 (tests) can run in parallel after T021
- **US3**: T025, T026 (services) can run in parallel; T027, T028 (endpoints) can run in parallel; T032, T033 (tests) can run in parallel
- **US4**: All component tasks (T034-T040) can run in parallel
- **US5**: T047-T050 (services/tasks) can run in parallel; T052-T056 (endpoints) can run in parallel; T060, T061 (tests) can run in parallel
- **Polish**: All tasks T062-T070 can run in parallel

---

## Parallel Example: User Story 4 (Frontend Components)

```bash
# Launch all component tasks together:
Task T034: "Create API service in frontend/src/api/seasonalApi.ts"
Task T035: "Create TypeScript types in frontend/src/types/seasonal.ts"
Task T036: "Create DateRangePicker component"
Task T037: "Create StatCard component"
Task T038: "Create ActivityChart component"
Task T039: "Create ComparisonView component"
Task T040: "Create ImageGallery component"

# Once components complete, create the page:
Task T041: "Create SeasonalAnalysis page"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only - Backend)

1. Complete Phase 1: Setup (~30 minutes)
2. Complete Phase 2: Foundational (~1-2 hours)
3. Complete Phase 3: User Story 1 (~3-4 hours)
4. Complete Phase 4: User Story 2 (~2-3 hours)
5. **STOP and VALIDATE**: Test both endpoints with curl
6. **Result**: Backend API operational for seasonal queries

**Estimated Time (MVP)**: 8-10 hours
**Deliverable**: Wildlife researchers can query rut season data via API

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Backend date filtering works
3. Add User Story 2 → Test independently → Backend detection queries work
4. Add User Story 3 → Test independently → Backend reports work
5. Add User Story 4 → Test independently → Frontend visual interface works (full experience!)
6. Add User Story 5 → Test independently → Export functionality works
7. Polish → Production ready

**Estimated Time (Full Feature)**:
- Backend (US1-US3, US5): ~15-20 hours
- Frontend (US4): ~20-25 hours
- Polish: ~3-5 hours
- **Total**: ~40-50 hours (5-7 days)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (~2 hours)
2. Once Foundational is done:
   - **Developer A**: User Story 1 (3-4 hours)
   - **Developer B**: User Story 2 (2-3 hours)
   - **Developer C**: User Story 3 (4-5 hours)
3. Stories complete independently
4. **Developer D**: User Story 4 - Frontend (20-25 hours, can start after US1-US3)
5. **Developer E**: User Story 5 - Exports (6-8 hours, can start after US2-US3)
6. Team completes Polish together (~3-5 hours)

**Total Time (Parallel 5 devs)**: ~30-35 hours wall-clock time (4-5 days)

---

## Critical Path

```
Setup (0.5h) → Foundational (2h) → US1 (4h) → US4 (25h) → Polish (4h)
Total Sequential: 35.5 hours (~5 days)

Setup (0.5h) → Foundational (2h) → [US1 | US2 | US3] (5h max) → [US4 | US5] (25h max) → Polish (4h)
Total Parallel: 36.5 hours wall-clock (~5 days with team)
```

**Recommendation**: Implement backend stories (US1-US3) first sequentially, then frontend (US4) and exports (US5) can proceed in parallel.

---

## Notes

- [P] tasks = different files/logic, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All file paths are absolute from repository root
- Frontend tasks assume existing Material-UI setup from Sprint 10
- Backend tasks reuse existing FastAPI, SQLAlchemy, Celery infrastructure
- Database migrations are manual SQL (no Alembic in this project yet)
- Tests are manual validation via curl and browser (no automated tests in this feature)
- Follow ASCII-only rule from constitution (no emojis in code/comments)
