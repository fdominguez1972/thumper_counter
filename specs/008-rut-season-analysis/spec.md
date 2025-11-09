# Feature Specification: Rut Season Analysis & Buck Detection Validation

**Feature Branch**: `008-rut-season-analysis`
**Created**: 2025-11-08
**Status**: Draft
**Input**: Analyze rut season images (Sept-Jan) to validate mature buck detection accuracy and provide seasonal wildlife activity insights

## Rut Season Definition *(official)*

**Study Period**: September 1 through January 31

This date range represents the whitetail deer breeding season (rut) specific to Hopkins Ranch, Texas. This period encompasses:
- **Pre-rut**: September (bucks establishing territory, increasing activity)
- **Peak rut**: October - November (peak breeding activity, highest buck visibility)
- **Post-rut**: December - January (declining activity, recovery period)

**Geographic Specificity**: These dates are calibrated for Texas whitetail deer populations and do not require regional customization for this study.

**Timezone**: All seasonal boundaries use UTC time alignment with ranch trail camera timestamps.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Filter Images by Rut Season (Priority: P1)

As a wildlife researcher, I need to filter trail camera images by rut season date ranges so that I can analyze buck activity during peak breeding periods.

**Why this priority**: Establishes the foundation for all rut season analysis. Must identify the correct subset of images before any analysis can occur.

**Independent Test**: Query API with date range September 1 - January 31. Verify returned images match rut season period and count matches expected 6,115 images from rut months.

**Acceptance Scenarios**:

1. **Given** 35,251 total images in database with timestamps, **When** filtering by date range 2024-09-01 to 2025-01-31, **Then** system returns only images within rut season period
2. **Given** rut season filter applied, **When** counting results, **Then** total matches documented 6,115 rut season images
3. **Given** user requests seasonal breakdown, **When** grouping by month, **Then** system shows image counts for Sept, Oct, Nov, Dec, Jan separately

---

### User Story 2 - Query Buck Detections by Season (Priority: P1)

As a wildlife researcher, I need to query all buck detections (mature, mid, young classifications) from rut season images so that I can validate model accuracy during critical breeding periods.

**Why this priority**: Core functionality for model validation. Enables assessment of detection accuracy on the most important seasonal dataset.

**Independent Test**: Query detections with classification in ('mature', 'mid', 'young') and image timestamp in rut season range. Verify all returned detections are bucks from rut season images.

**Acceptance Scenarios**:

1. **Given** rut season images processed, **When** querying for buck detections (mature/mid/young), **Then** system returns only male deer detections from Sept-Jan images
2. **Given** buck detections returned, **When** checking confidence scores, **Then** each detection includes confidence value and classification
3. **Given** detection results, **When** requesting deer profile linkage, **Then** each detection shows associated deer_id if re-identified

---

### User Story 3 - Generate Seasonal Activity Reports (Priority: P2)

As a wildlife researcher, I need to generate comparative reports showing buck detection counts and confidence levels across rut season months so that I can identify peak activity periods and model performance patterns.

**Why this priority**: Provides actionable insights from the data. Helps validate model performance varies by season and identifies biological patterns.

**Independent Test**: Request seasonal report API endpoint. Verify response includes monthly breakdown of buck detections, average confidence per month, and detection count trends.

**Acceptance Scenarios**:

1. **Given** processed rut season images, **When** requesting seasonal activity report, **Then** system returns detection counts grouped by month (Sept, Oct, Nov, Dec, Jan)
2. **Given** seasonal report, **When** analyzing confidence scores, **Then** report shows average confidence per classification (mature/mid/young) per month
3. **Given** detection data, **When** comparing to non-rut months, **Then** report highlights statistical differences in buck detection rates

---

### User Story 4 - Ad-Hoc Query Interface for Wildlife Researchers (Priority: P2)

As a wildlife researcher, I need to run ad-hoc queries from the web front end using a user-friendly visual interface so that I can analyze specific date ranges and statistics without knowing database query syntax.

**Why this priority**: Empowers non-technical wildlife researchers to perform custom analysis without database knowledge. Essential for flexible herd management decision-making.

**Independent Test**: Access 3 separate date ranges from the defined Rut Season (Sept 1 - Jan 31) via visual date picker. Retrieve statistics relevant to herd management (detection counts, sex ratios, activity patterns) without writing SQL queries. Verify each date range returns accurate statistics and visual charts.

**Acceptance Scenarios**:

1. **Given** user accesses query interface, **When** selecting date range using visual calendar picker, **Then** system displays preview of selected range and estimated image count before running query
2. **Given** user selects first date range (Sept 1-30), **When** clicking "Run Analysis", **Then** system returns detection counts, sex ratio breakdown, and activity timeline chart without requiring SQL knowledge
3. **Given** user completes first query, **When** selecting second date range (Oct 1-31) and re-running, **Then** system displays comparison view showing statistics for both periods side-by-side
4. **Given** user selects third date range (Nov 1-30), **When** analyzing, **Then** system adds third period to comparison and highlights statistical differences (e.g., peak buck activity in November)
5. **Given** query results displayed, **When** user clicks on detection count metric, **Then** system shows filterable image gallery with visual indicators (deer icons, color-coded by sex/class)
6. **Given** herd management statistics displayed, **When** user requests export, **Then** system generates PDF report with charts, statistics table, and summary insights in plain language

---

### User Story 5 - Export Buck Detection Dataset (Priority: P3)

As a wildlife researcher, I need to export rut season buck detections with image crops and metadata so that I can create training datasets for model improvement or share with wildlife biologists.

**Why this priority**: Enables model refinement and data sharing. Nice-to-have for iterative improvement but not required for initial validation.

**Independent Test**: Request export of mature buck detections from November. Verify ZIP file contains image crops, CSV metadata with filenames/timestamps/confidence/bbox coordinates.

**Acceptance Scenarios**:

1. **Given** filtered buck detections, **When** requesting export, **Then** system generates ZIP archive with detection crops and metadata CSV
2. **Given** export package, **When** examining contents, **Then** each crop filename matches detection_id and CSV contains corresponding metadata row
3. **Given** large export request (1000+ detections), **When** processing, **Then** system handles async export with download link notification

---

### Edge Cases

- What happens when no images exist in requested date range? [Return empty result set with count=0, HTTP 200]
- How does system handle images with timestamp=NULL? [Exclude from seasonal queries, log warning if >1% have NULL timestamps]
- What if buck detection has NULL classification? [Include in results with classification='unknown', flag for manual review]
- How to handle timezone differences in timestamps? [All timestamps stored as UTC, seasonal filters use UTC boundaries]
- What about images from multiple years? [Support year parameter, default to most recent year with rut season data]

## Requirements *(mandatory)*

### Functional Requirements

#### Core Seasonal Filtering

- **FR-001**: System MUST define rut season as September 1 through January 31 as the official study period for Texas whitetail deer breeding season analysis
- **FR-002**: System MUST provide API endpoint to filter images by date range with parameters: start_date, end_date, format YYYY-MM-DD
- **FR-003**: System MUST support predefined seasonal filters: rut_season (Sept 1 - Jan 31), spring (Mar 1 - May 31), summer (Jun 1 - Aug 31)
- **FR-004**: System MUST query detections filtered by classification list (e.g., ['mature', 'mid', 'young'] for all bucks)
- **FR-005**: System MUST combine date range and classification filters in single query (e.g., mature bucks in November)

#### Reporting and Analysis

- **FR-006**: System MUST provide seasonal activity report endpoint showing detection counts grouped by month and classification
- **FR-007**: System MUST calculate and return average confidence score per classification per month in seasonal reports
- **FR-008**: System MUST support comparison queries between rut season and non-rut season detection rates
- **FR-009**: System MUST calculate sex ratios (bucks to does) for specified date ranges and include in analysis reports

#### Data Export

- **FR-010**: System MUST export detection dataset as ZIP containing: cropped images, metadata CSV (detection_id, image_id, filename, timestamp, classification, confidence, bbox coordinates, deer_id)
- **FR-011**: System MUST generate PDF reports containing: charts, statistics tables, summary insights in plain language suitable for non-technical wildlife researchers

#### Frontend Query Interface

- **FR-012**: System MUST provide visual calendar date picker interface for selecting custom date ranges without requiring manual date entry
- **FR-013**: System MUST display preview of selected date range showing estimated image count before executing query
- **FR-014**: System MUST support side-by-side comparison view for displaying statistics from multiple date ranges simultaneously (minimum 3 periods)
- **FR-015**: System MUST generate interactive timeline charts showing detection activity patterns over selected periods
- **FR-016**: System MUST provide filterable image gallery with visual indicators (color-coded icons) for sex and classification
- **FR-017**: System MUST allow drill-down from summary statistics to detailed image gallery by clicking on metric values
- **FR-018**: System MUST highlight statistical differences between compared periods (e.g., "November shows 45% increase in mature buck detections vs September")

#### Input Validation

- **FR-019**: System MUST validate date range inputs and reject invalid formats or impossible ranges with HTTP 400
- **FR-020**: System MUST handle large result sets (1000+ detections) with pagination (default page_size=100, max=1000)

### Non-Functional Requirements

#### Backend Performance

- **NFR-001**: Date range query MUST return results within 2 seconds for queries spanning 12 months (e.g., full rut season)
- **NFR-002**: Seasonal report generation MUST complete within 5 seconds for full year analysis with database aggregation
- **NFR-003**: Export ZIP generation MUST handle up to 10,000 detections with progress tracking (async job queue)
- **NFR-004**: All date filtering MUST use database indexes on timestamp columns to ensure query performance
- **NFR-005**: API responses MUST include total result count and pagination metadata (page, page_size, total_pages, has_next)

#### Frontend Performance & Usability

- **NFR-006**: Date picker interface MUST be responsive and usable on desktop browsers (Chrome, Firefox, Safari) with minimum screen resolution 1280x720
- **NFR-007**: Chart rendering MUST complete within 1 second for datasets containing up to 5,000 detections
- **NFR-008**: PDF report generation MUST produce files under 5MB for reports containing up to 50 charts and 1,000 data rows
- **NFR-009**: Image gallery thumbnails MUST lazy-load with progressive rendering to maintain UI responsiveness with 1,000+ images
- **NFR-010**: Side-by-side comparison view MUST maintain synchronized scrolling and alignment across all displayed periods

### Key Entities

- **SeasonalFilter**: Virtual entity defining predefined date ranges (rut_season: Sept 1 - Jan 31, spring: Mar 1 - May 31, summer: Jun 1 - Aug 31, fall: Sept 1 - Nov 30)
- **SeasonalReport**: Aggregated data structure containing monthly detection counts, average confidence by classification, total buck detections, sex ratios, comparison to baseline, statistical differences
- **QuerySession**: Frontend state object tracking user's active analysis session (selected_periods: array of date ranges, active_filters: classification/location/confidence, comparison_mode: boolean)
- **ComparisonResult**: Data structure for side-by-side period analysis (period_1_stats, period_2_stats, period_3_stats, differences: array of statistical comparisons, highlights: array of notable findings)
- **PDFReport**: Generated document entity (report_id, title, date_ranges, charts: array of chart images, statistics_tables, insights_text, generated_at, file_size, download_url)
- **ExportJob**: Async task tracking ZIP generation progress (job_id, status, total_detections, processed_count, download_url, created_at, completed_at)

## Success Criteria *(mandatory)*

### Measurable Outcomes

#### Backend API Performance

- **SC-001**: Date range filtering returns exactly 6,115 images for 2024-09-01 to 2025-01-31 (documented rut season image count)
- **SC-002**: Buck detection query returns all detections with classification in ('mature', 'mid', 'young') with zero misclassified doe/fawn/unknown in results
- **SC-003**: Seasonal activity report shows statistically significant increase in mature buck detections during November (expected peak rut activity) compared to September baseline
- **SC-004**: Export functionality generates complete ZIP with 100% of requested detection crops and matching CSV rows for datasets up to 1,000 detections within 30 seconds
- **SC-005**: API query performance remains under 2 seconds for date range queries even with 35,251 total images in database
- **SC-006**: Validation analysis confirms model detection confidence for mature bucks during rut season averages >70% (comparable to overall model performance of 76%)

#### Frontend User Experience

- **SC-007**: Wildlife researcher can successfully analyze 3 different rut season date ranges (Sept 1-30, Oct 1-31, Nov 1-30) using visual date picker without database knowledge, completing task in under 5 minutes
- **SC-008**: Side-by-side comparison view displays accurate statistics for all 3 selected periods with visual charts loaded in under 3 seconds
- **SC-009**: PDF report export generates complete document with charts, tables, and plain language insights in under 10 seconds for single-period analysis
- **SC-010**: Interactive image gallery displays detection thumbnails with color-coded sex/class indicators, loading 100 images in under 2 seconds with infinite scroll capability
- **SC-011**: Statistical difference highlighting correctly identifies and displays November as peak rut activity month with quantified percentage increase (target: >30% increase vs September baseline)

## Assumptions

- **ASSUMPTION-001**: All images have valid timestamps (NULL timestamps represent <1% of dataset)
- **ASSUMPTION-002**: Rut season dates (Sept 1 - Jan 31) are specific to Texas whitetail deer and do not require geographic customization
- **ASSUMPTION-003**: Buck classifications (mature/mid/young) from multi-class model are sufficiently accurate for seasonal analysis (validated in Sprint 4 at 80.4% mAP50)
- **ASSUMPTION-004**: Wildlife researcher will manually validate a sample of exported detections for model performance confirmation
- **ASSUMPTION-005**: Seasonal comparison baseline uses Feb-Aug period as "non-rut" comparison group
