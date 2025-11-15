# Feature Specification: Critical Infrastructure Fixes

**Feature Branch**: `010-infrastructure-fixes`
**Created**: 2025-11-12
**Status**: Draft
**Input**: User description: "Implement critical infrastructure fixes from code audit: (A) Export job status tracking with Redis for PDF/ZIP exports - worker tasks must update Redis with completion status so API can poll and provide download URLs instead of jobs being stuck in 'processing' forever, (B) Export request validation - add comprehensive validation for date ranges (start before end, max 365 days, valid group_by values, no future dates) before queueing worker tasks, and (D) Re-ID performance optimization - analyze 9.5% assignment rate by investigating similarity score distribution, testing threshold variations from 0.70, and identifying optimal matching parameters. These fixes address CRITICAL-2, CRITICAL-3 from November 12 audit, and high-priority re-identification performance issues."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export Job Lifecycle Tracking (Priority: P1)

A user requests PDF or ZIP export of seasonal deer activity data. The system generates the report in the background and notifies the user when the file is ready to download.

**Why this priority**: Exports currently complete successfully but remain stuck in "processing" status forever. Users cannot access completed files even though they exist on disk. This is a CRITICAL blocker (CRITICAL-2 from audit).

**Independent Test**: Can be fully tested by requesting a PDF export, waiting for completion, and verifying the status changes from "processing" to "completed" with a download URL provided.

**Acceptance Scenarios**:

1. **Given** user requests PDF export via API, **When** worker completes report generation, **Then** job status updates to "completed" with download URL
2. **Given** user requests ZIP export via API, **When** worker completes archive creation, **Then** job status updates to "completed" with download URL
3. **Given** export job completed, **When** user polls job status endpoint, **Then** API returns "completed" status with file path
4. **Given** export job completed 1 hour ago, **When** user polls job status endpoint, **Then** API returns 404 "Job not found or expired"
5. **Given** export job fails during processing, **When** user polls job status endpoint, **Then** API returns "failed" status with error message

---

### User Story 2 - Export Request Validation (Priority: P1)

A user submits export request with invalid parameters (date range, grouping options). The system immediately rejects the request with clear error message instead of queueing a task that will fail silently.

**Why this priority**: No validation currently exists, causing worker tasks to fail silently with no user feedback. This is a CRITICAL issue (CRITICAL-3 from audit) that wastes system resources and confuses users.

**Independent Test**: Can be fully tested by submitting various invalid export requests and verifying immediate rejection with clear error messages before any worker task is created.

**Acceptance Scenarios**:

1. **Given** user submits export request with start_date after end_date, **When** API validates request, **Then** request rejected with 400 error "start_date must be before end_date"
2. **Given** user submits export request with date range exceeding 365 days, **When** API validates request, **Then** request rejected with 400 error "Date range cannot exceed 1 year"
3. **Given** user submits export request with invalid group_by value, **When** API validates request, **Then** request rejected with 400 error listing valid options
4. **Given** user submits export request with start_date in the future, **When** API validates request, **Then** request rejected with 400 error "start_date cannot be in the future"
5. **Given** user submits valid export request, **When** API validates request, **Then** request accepted and worker task queued

---

### User Story 3 - Re-ID Performance Analysis (Priority: P2)

System administrator investigates why only 9.5% of deer detections are assigned to deer profiles. Administrator runs analysis script to examine similarity score distribution and identify optimal matching threshold.

**Why this priority**: Current 9.5% assignment rate suggests REID_THRESHOLD of 0.70 may be too conservative, or other matching issues exist. This is high-priority performance optimization but does not block core functionality.

**Independent Test**: Can be fully tested by running analysis script on existing detection data, reviewing similarity score histogram, and verifying threshold recommendations are data-driven.

**Acceptance Scenarios**:

1. **Given** 11,570 detections in database, **When** administrator runs similarity analysis script, **Then** system generates histogram of all similarity scores
2. **Given** similarity score distribution available, **When** administrator reviews clustering patterns, **Then** natural score groupings are identified
3. **Given** multiple threshold values tested (0.65, 0.60, 0.55), **When** administrator reviews assignment rates, **Then** optimal threshold balancing assignment rate and false positive rate is identified
4. **Given** threshold analysis complete, **When** administrator reviews recommendations, **Then** data-driven threshold value is suggested with expected assignment rate improvement
5. **Given** new threshold identified, **When** administrator applies threshold and reprocesses sample batch, **Then** assignment rate improves without significant increase in false positives

---

### Edge Cases

- What happens when Redis connection fails during export job status update?
- How does system handle concurrent export requests from same user?
- What happens when worker crashes mid-export and never updates status?
- How does system handle very old job_id requests (beyond 1 hour expiry)?
- What happens when date range validation receives non-date input?
- How does system handle zero detections found during Re-ID analysis?
- What happens when similarity scores are all below threshold (no matches)?

## Requirements *(mandatory)*

### Functional Requirements

**Option A: Export Job Status Tracking**

- **FR-001**: Worker tasks MUST update Redis with job completion status including "completed" or "failed" state
- **FR-002**: Worker tasks MUST store job status with 1-hour TTL (time-to-live) in Redis
- **FR-003**: Worker tasks MUST include download URL in completion status for successful exports
- **FR-004**: Worker tasks MUST include error message in status for failed exports
- **FR-005**: API endpoints MUST poll Redis for job status using job_id as key
- **FR-006**: API endpoints MUST return 404 "Job not found or expired" when job_id not found in Redis
- **FR-007**: API endpoints MUST return job status JSON including status, filename, download_url, and timestamp fields

**Option B: Export Request Validation**

- **FR-008**: Export endpoints MUST validate start_date is before end_date
- **FR-009**: Export endpoints MUST reject date ranges exceeding 365 days
- **FR-010**: Export endpoints MUST validate group_by value is one of: "day", "week", "month"
- **FR-011**: Export endpoints MUST reject start_date values in the future
- **FR-012**: Export endpoints MUST return 400 status code with clear error message for all validation failures
- **FR-013**: Export endpoints MUST only queue worker tasks after all validation passes

**Option D: Re-ID Performance Optimization**

- **FR-014**: System MUST provide analysis script to query all similarity scores from re-identification matching
- **FR-015**: Analysis script MUST generate histogram visualization of similarity score distribution
- **FR-016**: Analysis script MUST calculate assignment rate for multiple threshold values (0.70, 0.65, 0.60, 0.55)
- **FR-017**: Analysis script MUST identify natural clustering in similarity scores
- **FR-018**: Analysis script MUST recommend optimal threshold based on data analysis
- **FR-019**: System MUST allow testing threshold changes on sample batch before full deployment

### Key Entities

- **Export Job**: Background task generating PDF or ZIP file
  - Key attributes: job_id, status (processing/completed/failed), filename, download_url, error message, completion timestamp, expiry time
  - Stored in: Redis with 1-hour TTL

- **Export Request**: User-submitted parameters for report generation
  - Key attributes: start_date, end_date, group_by (day/week/month), report_type (pdf/zip)
  - Validation rules: start < end, range <= 365 days, group_by in allowed values, start not in future

- **Re-ID Similarity Score**: Cosine similarity between detection feature vector and deer profile feature vector
  - Key attributes: detection_id, deer_id, similarity_score (0.0-1.0), sex_match (boolean)
  - Analysis target: Distribution patterns, natural clustering, optimal threshold identification

- **Deer Detection**: Individual deer detection from ML model
  - Key attributes: detection_id, deer_id (nullable), feature_vector (512-dim), classification (buck/doe/fawn), confidence
  - Current state: 11,570 detections, 1,100 assigned (9.5%), 10,470 unassigned (90.5%)

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Option A: Export Job Status Tracking**

- **SC-001**: Users can poll export job status and receive accurate state (processing/completed/failed) within 1 second
- **SC-002**: Completed export jobs provide download URL that allows file access within 5 seconds
- **SC-003**: Failed export jobs provide clear error message explaining failure reason
- **SC-004**: Export job status automatically expires after 1 hour, returning 404 for old job_id requests
- **SC-005**: 100% of export jobs that complete successfully update their status from "processing" to "completed"

**Option B: Export Request Validation**

- **SC-006**: Invalid export requests are rejected within 100ms with clear error message
- **SC-007**: Zero worker tasks are queued for requests with invalid date ranges
- **SC-008**: Users receive immediate feedback on validation errors without waiting for background processing
- **SC-009**: Error messages clearly specify which validation rule failed and what values are acceptable
- **SC-010**: 100% of validation failures return 400 status code with JSON error response

**Option D: Re-ID Performance Optimization**

- **SC-011**: Analysis script completes similarity score analysis on 11,570 detections within 5 minutes
- **SC-012**: Similarity score histogram clearly shows distribution and natural clustering patterns
- **SC-013**: Threshold recommendations are data-driven with predicted assignment rate improvement
- **SC-014**: Optimal threshold increases assignment rate by at least 20% (from 9.5% to 11.4% minimum)
- **SC-015**: False positive rate remains below 5% with recommended threshold
- **SC-016**: Analysis results are documented with visualizations and recommendations for decision-making

## Constraints & Assumptions *(if applicable)*

### Technical Constraints

- Redis must be running and accessible to both worker and backend services
- Worker tasks must have access to Redis client library (redis-py)
- Export files must be stored in /mnt/exports directory accessible to API for downloads
- Re-ID analysis requires PostgreSQL access to query detections and deer tables
- Similarity scores must already exist in database from previous re-identification runs

### Assumptions

- Redis is already configured in docker-compose.yml (port 6380 external, 6379 internal)
- Redis client is already available in worker environment
- Export worker tasks (generate_pdf_report_task, create_zip_archive_task) are already implemented
- Re-identification similarity scoring is already implemented and storing scores
- Feature vectors are normalized L2 vectors enabling cosine similarity comparison
- Current REID_THRESHOLD of 0.70 is stored in environment variable
- Sex-based filtering is already implemented in re-ID matching logic

### Dependencies

- Option A depends on: Redis running, redis-py installed, export worker tasks operational
- Option B depends on: Pydantic schemas for export requests, FastAPI validation framework
- Option D depends on: PostgreSQL access, matplotlib/seaborn for visualization, pandas for analysis
- All options depend on: Docker environment operational, database accessible

## Out of Scope

- Frontend UI changes for export status display (handled in separate frontend feature)
- Reprocessing entire dataset with new Re-ID threshold (manual operational task)
- Database migration to store job status persistently (Redis temporary storage sufficient)
- Email notifications when export jobs complete (future enhancement)
- Export job queuing priority or scheduling (all exports processed FIFO)
- Re-ID model retraining with new feature extraction (separate ML optimization effort)
- Burst linking optimization (separate performance issue)
- Creating new export endpoints beyond PDF and ZIP (focus on fixing existing ones)
