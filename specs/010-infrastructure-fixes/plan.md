# Implementation Plan: Critical Infrastructure Fixes

**Branch**: `010-infrastructure-fixes` | **Date**: 2025-11-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-infrastructure-fixes/spec.md`

## Summary

This feature implements three critical infrastructure fixes identified in the November 12, 2025 code audit:

1. **Export Job Status Tracking (Option A)**: Implement Redis-based job status tracking so worker tasks can update completion status and API can poll for results. Fixes CRITICAL-2 where export jobs complete successfully but remain stuck in "processing" status forever.

2. **Export Request Validation (Option B)**: Add comprehensive validation to export endpoints (date ranges, group_by values, future dates) before queueing worker tasks. Fixes CRITICAL-3 where invalid requests cause silent worker failures.

3. **Re-ID Performance Optimization (Option D)**: Create analysis scripts to investigate 9.5% assignment rate by examining similarity score distribution, testing threshold variations, and identifying optimal matching parameters. Addresses high-priority performance issue.

**Technical Approach**: Modify existing export worker tasks to write status to Redis with 1-hour TTL, update export API endpoints to poll Redis and add validation logic, create standalone Python analysis scripts for Re-ID performance investigation.

## Technical Context

**Language/Version**: Python 3.11 (backend + worker)
**Primary Dependencies**: FastAPI (backend), Celery (worker), Redis (job tracking), redis-py (Redis client), PostgreSQL 15 (data), matplotlib/seaborn (visualization)
**Storage**: Redis (temporary job status, 1-hour TTL), PostgreSQL (detections, deer profiles, similarity scores)
**Testing**: pytest (unit tests), curl/httpie (API endpoint testing), manual validation (Re-ID analysis)
**Target Platform**: Linux containers via Docker (backend, worker services)
**Project Type**: Web application (existing backend + worker architecture)
**Performance Goals**:
  - Export status queries: <1 second response time
  - Export validation: <100ms rejection time
  - Re-ID analysis: Complete 11,570 detections within 5 minutes

**Constraints**:
  - Must not break existing export functionality
  - Redis TTL must be 1 hour (matches audit recommendation)
  - Analysis scripts must run without modifying production data
  - All changes must be backward compatible with existing worker tasks

**Scale/Scope**:
  - Current dataset: 11,570 detections, 20 deer profiles
  - Export endpoints: 2 (PDF, ZIP)
  - Validation rules: 4 per endpoint
  - Analysis scripts: 2 (similarity distribution, threshold testing)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Article I: Core Principles

- **Principle 2 (Data Sovereignty)**: PASS - Redis runs locally in Docker, no cloud dependencies
- **Principle 3 (Operational Simplicity)**: PASS - Validation provides clear error messages to users
- **Principle 4 (Scientific Rigor)**: PASS - Re-ID analysis maintains confidence tracking and supports threshold tuning
- **Principle 5 (Modular Architecture)**: PASS - Changes isolated to export module and analysis scripts
- **Principle 6 (Performance Efficiency)**: PASS - Analysis scripts optimize Re-ID assignment rate without breaking existing processing

### Article II: Technical Standards

- **Mandatory Requirements**: PASS
  - Python 3.11+ (existing)
  - PostgreSQL 15+ (existing)
  - Docker (Redis already in docker-compose.yml)
  - Git with branching (using 010-infrastructure-fixes branch)
  - ASCII-only output (validation error messages use ASCII format)

- **Prohibited Practices**: PASS
  - No credentials in code (Redis connection via environment variables)
  - No direct database access from frontend (backend API only)
  - No synchronous ML in API (exports already async via Celery)
  - No hardcoded paths (using environment variables)
  - No Unicode/emoji (ASCII-only error messages)

### Article III: Data Governance

- **Data Retention**: PASS - Export job status expires after 1 hour (temporary data only)
- **Privacy Protection**: PASS - No PII in export data or Re-ID analysis

### Article IV: Development Governance

- **Change Management**: PASS - Specification created before implementation
- **Version Control**: PASS - Using conventional commit format
- **Documentation Standards**: PASS - API changes will update OpenAPI, scripts will have docstrings

### Violations Requiring Justification

NONE - All constitution requirements satisfied.

## Project Structure

### Documentation (this feature)

```text
specs/010-infrastructure-fixes/
├── plan.md              # This file
├── research.md          # Phase 0: Redis patterns, validation strategies, analysis libraries
├── data-model.md        # Phase 1: Export job entity, validation rules
├── quickstart.md        # Phase 1: How to test fixes
├── contracts/           # Phase 1: Updated OpenAPI specs for export endpoints
│   ├── export-status.yaml
│   └── export-validation.yaml
└── tasks.md             # Phase 2: Created by /speckit.tasks command
```

### Source Code (repository root)

```text
# Backend API modifications
src/backend/api/exports.py          # Add validation, Redis polling
src/backend/schemas/export.py       # Add validation rules to Pydantic schemas

# Worker task modifications
src/worker/tasks/exports.py         # Add Redis status updates
src/worker/celery_app.py            # Verify Redis client availability

# Analysis scripts (new)
scripts/analyze_reid_performance.py # Similarity score distribution analysis
scripts/test_reid_thresholds.py     # Threshold variation testing
scripts/plot_reid_scores.py         # Visualization generation

# Tests (new)
tests/api/test_export_validation.py # Validation rule tests
tests/worker/test_export_status.py  # Redis status update tests
tests/scripts/test_reid_analysis.py # Analysis script tests

# Documentation updates
docs/EXPORT_STATUS_TRACKING.md      # Option A implementation guide
docs/EXPORT_VALIDATION.md           # Option B validation rules
docs/REID_OPTIMIZATION_ANALYSIS.md  # Option D analysis results
```

**Structure Decision**: Existing web application structure (backend/ + worker/ split). Modifications to existing files + new analysis scripts in scripts/ directory. No new services required - uses existing Redis container.

## Complexity Tracking

> No violations requiring justification.

---

# Phase 0: Research & Investigation

## Research Tasks

### Task 1: Redis Job Status Patterns
**Question**: What is the best practice for storing temporary job status in Redis with automatic expiry?

**Investigation**:
- Redis SETEX command for atomic set-with-expiry
- Key naming conventions: `export_job:{job_id}` pattern
- JSON serialization for complex status objects
- Error handling for Redis connection failures

**Decision**: Use `redis_client.setex(key, ttl_seconds, json.dumps(status))` pattern with 3600 second TTL (1 hour).

**Rationale**: SETEX is atomic (prevents race conditions), TTL automatically cleans up old jobs, JSON format allows flexible status fields.

### Task 2: FastAPI Validation Strategies
**Question**: Should validation be in Pydantic schema validators or endpoint logic?

**Investigation**:
- Pydantic field validators for simple constraints
- Custom endpoint validation for multi-field logic
- HTTPException with 400 status for validation failures
- Error message formatting for user clarity

**Decision**: Combine both - use Pydantic validators for single-field rules (date format), endpoint logic for multi-field rules (start < end, date range).

**Rationale**: Pydantic handles type validation automatically, endpoint logic provides context-specific error messages.

### Task 3: Re-ID Similarity Analysis Libraries
**Question**: What Python libraries are best for analyzing similarity score distributions?

**Investigation**:
- pandas for data manipulation (DataFrame operations)
- matplotlib for histogram visualization
- seaborn for enhanced statistical plots
- scipy for clustering analysis
- SQLAlchemy for database queries

**Decision**: Use pandas + matplotlib + seaborn stack with SQLAlchemy for data extraction.

**Rationale**: Industry-standard stack, already installed in worker environment, excellent visualization capabilities.

### Task 4: Threshold Testing Methodology
**Question**: How to test multiple threshold values without modifying production data?

**Investigation**:
- Query-only analysis (no database writes)
- In-memory threshold application to existing similarity scores
- Confusion matrix calculation for false positive rate
- Assignment rate calculation: (assigned / total) * 100

**Decision**: Load all similarity scores into pandas DataFrame, apply thresholds in-memory, calculate metrics, no database modifications.

**Rationale**: Safe (read-only), fast (in-memory), repeatable (no side effects).

---

# Phase 1: Design Artifacts

## Data Model

See [data-model.md](data-model.md) for complete entity definitions.

**Key Entities**:

### Export Job Status (Redis)
- **Storage**: Redis with 1-hour TTL
- **Key Format**: `export_job:{job_id}`
- **Value**: JSON with fields: status, filename, download_url, completed_at, error
- **States**: processing → completed | failed

### Export Request Validation
- **Input**: PDFExportRequest | ZIPExportRequest Pydantic schemas
- **Rules**:
  - start_date < end_date
  - (end_date - start_date).days <= 365
  - group_by in ["day", "week", "month"]
  - start_date <= today
- **Output**: 400 HTTPException with clear error message

### Re-ID Similarity Score
- **Table**: detections (existing)
- **Fields**: detection_id, deer_id, feature_vector, classification
- **Analysis**: Compute pairwise cosine similarity, store in DataFrame
- **Metrics**: assignment_rate, false_positive_rate, optimal_threshold

## API Contracts

See [contracts/](contracts/) directory for OpenAPI specifications.

**Modified Endpoints**:

### GET /api/exports/pdf/{job_id}
- **Change**: Poll Redis instead of in-memory state
- **Response 200**: `{"status": "completed", "filename": "report.pdf", "download_url": "/api/static/exports/report.pdf"}`
- **Response 404**: `{"detail": "Job not found or expired"}`

### POST /api/exports/pdf
- **Change**: Add validation before queueing task
- **Response 400**: `{"detail": "start_date must be before end_date"}`
- **Response 202**: `{"job_id": "uuid", "status": "processing"}`

### GET /api/exports/zip/{job_id}
- **Change**: Poll Redis instead of in-memory state
- **Response**: Same as PDF endpoint

### POST /api/exports/zip
- **Change**: Add validation before queueing task
- **Response**: Same as PDF endpoint

## Quick Start

See [quickstart.md](quickstart.md) for detailed testing instructions.

**Option A - Test Export Status Tracking**:
```bash
# 1. Create export job
curl -X POST http://localhost:8001/api/exports/pdf \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2023-09-01", "end_date": "2024-01-31", "group_by": "month"}'

# 2. Poll status (should show "processing" then "completed")
curl http://localhost:8001/api/exports/pdf/{job_id}

# 3. Download file
curl -o report.pdf http://localhost:8001/api/static/exports/{filename}

# 4. Wait 1 hour, verify expiry
curl http://localhost:8001/api/exports/pdf/{job_id}  # Should return 404
```

**Option B - Test Export Validation**:
```bash
# Test 1: Invalid date range
curl -X POST http://localhost:8001/api/exports/pdf \
  -d '{"start_date": "2024-12-31", "end_date": "2024-01-01", "group_by": "day"}'
# Expected: 400 "start_date must be before end_date"

# Test 2: Range too large
curl -X POST http://localhost:8001/api/exports/pdf \
  -d '{"start_date": "2020-01-01", "end_date": "2025-01-01", "group_by": "day"}'
# Expected: 400 "Date range cannot exceed 1 year"

# Test 3: Invalid group_by
curl -X POST http://localhost:8001/api/exports/pdf \
  -d '{"start_date": "2024-01-01", "end_date": "2024-06-01", "group_by": "hour"}'
# Expected: 400 error listing valid options
```

**Option D - Run Re-ID Analysis**:
```bash
# 1. Analyze similarity scores
docker-compose exec worker python3 /app/scripts/analyze_reid_performance.py

# 2. Test thresholds
docker-compose exec worker python3 /app/scripts/test_reid_thresholds.py \
  --thresholds 0.70,0.65,0.60,0.55

# 3. Generate visualizations
docker-compose exec worker python3 /app/scripts/plot_reid_scores.py \
  --output /app/docs/reid_analysis.png
```

---

# Phase 2: Task Generation

Tasks will be generated by the `/speckit.tasks` command. Expected task structure:

**Option A Tasks** (Export Status Tracking):
1. Add Redis status update to `generate_pdf_report_task` worker
2. Add Redis status update to `create_zip_archive_task` worker
3. Modify `get_pdf_export_status` API to poll Redis
4. Modify `get_zip_export_status` API to poll Redis
5. Add error handling for Redis connection failures
6. Write unit tests for status updates
7. Write integration tests for full export lifecycle

**Option B Tasks** (Export Validation):
1. Add validation function to `src/backend/api/exports.py`
2. Update `PDFExportRequest` schema with validators
3. Update `ZIPExportRequest` schema with validators
4. Add validation tests for each rule
5. Update OpenAPI documentation

**Option D Tasks** (Re-ID Analysis):
1. Create `analyze_reid_performance.py` script
2. Create `test_reid_thresholds.py` script
3. Create `plot_reid_scores.py` visualization script
4. Write analysis documentation in `docs/REID_OPTIMIZATION_ANALYSIS.md`
5. Run analysis on current dataset
6. Generate recommendations based on results

---

# Implementation Notes

## Option A: Redis Integration

**Existing Redis Setup**:
- Redis container already running (docker-compose.yml)
- Port 6380 external, 6379 internal
- Redis client available in worker environment

**Implementation Pattern**:
```python
# Worker task (exports.py)
from celery import current_task
import json
from datetime import datetime

@app.task(bind=True)
def generate_pdf_report_task(self, ...):
    try:
        # ... generate PDF ...

        # Update Redis
        redis_client.setex(
            f"export_job:{self.request.id}",
            3600,  # 1 hour
            json.dumps({
                "status": "completed",
                "filename": filename,
                "download_url": f"/api/static/exports/{filename}",
                "completed_at": datetime.utcnow().isoformat()
            })
        )
    except Exception as e:
        redis_client.setex(
            f"export_job:{self.request.id}",
            3600,
            json.dumps({"status": "failed", "error": str(e)})
        )
```

## Option B: Validation Logic

**Validation Function**:
```python
def validate_export_request(start_date, end_date, group_by):
    # Rule 1: start < end
    if start_date > end_date:
        raise HTTPException(400, "start_date must be before end_date")

    # Rule 2: range <= 365 days
    delta = end_date - start_date
    if delta.days > 365:
        raise HTTPException(400, "Date range cannot exceed 1 year")

    # Rule 3: valid group_by
    valid_group_by = ["day", "week", "month"]
    if group_by not in valid_group_by:
        raise HTTPException(
            400,
            f"group_by must be one of: {', '.join(valid_group_by)}"
        )

    # Rule 4: no future dates
    if start_date > datetime.utcnow().date():
        raise HTTPException(400, "start_date cannot be in the future")
```

## Option D: Analysis Approach

**Similarity Score Distribution**:
```python
# Query all similarity scores from re-identification
scores = session.query(
    Detection.id,
    Detection.deer_id,
    Detection.classification,
    # Compute cosine similarity from feature vectors
).all()

# Create DataFrame
df = pd.DataFrame(scores, columns=['detection_id', 'deer_id', 'classification', 'similarity'])

# Plot histogram
plt.figure(figsize=(10, 6))
plt.hist(df['similarity'], bins=50, alpha=0.7)
plt.xlabel('Similarity Score')
plt.ylabel('Frequency')
plt.title('Re-ID Similarity Score Distribution')
plt.savefig('reid_similarity_distribution.png')
```

**Threshold Testing**:
```python
thresholds = [0.70, 0.65, 0.60, 0.55]
results = []

for threshold in thresholds:
    # Apply threshold in-memory
    assigned = df[df['similarity'] >= threshold]

    # Calculate metrics
    assignment_rate = len(assigned) / len(df) * 100

    results.append({
        'threshold': threshold,
        'assignment_rate': assignment_rate,
        'assigned_count': len(assigned)
    })

# Print recommendations
print("Threshold Analysis Results:")
for r in results:
    print(f"Threshold {r['threshold']}: {r['assignment_rate']:.1f}% assignment rate")
```

---

# Success Metrics

**Option A**:
- 100% of completed exports update status to "completed" (currently 0%)
- Export status queries return result within 1 second (target: <1s)
- Jobs expire after 1 hour as verified by 404 response

**Option B**:
- 100% of invalid requests rejected before worker queue (currently 0% validation)
- Validation response time <100ms (target: <100ms)
- Zero worker task failures due to invalid input (currently: silent failures occur)

**Option D**:
- Similarity analysis completes within 5 minutes on 11,570 detections
- Clear histogram visualization shows score distribution
- Optimal threshold identified with predicted assignment rate improvement >=20%
- False positive rate remains <5% with recommended threshold

---

# Dependencies & Prerequisites

**All Options**:
- Docker environment operational
- PostgreSQL database accessible
- Redis container running

**Option A Specific**:
- redis-py installed in worker environment (verify: `pip list | grep redis`)
- Export worker tasks operational (verify: `docker-compose logs worker | grep export`)

**Option B Specific**:
- FastAPI >=0.104 with HTTPException support
- Pydantic validation framework functional

**Option D Specific**:
- matplotlib, seaborn, pandas installed (add to requirements.txt if missing)
- PostgreSQL query access for detections and deer tables
- Write access to docs/ directory for output files

---

# Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Redis connection failure during status update | Low | Medium | Worker catches exception, logs error, completes task anyway |
| Validation breaks existing valid requests | Low | High | Comprehensive test suite with real historical request data |
| Re-ID analysis incorrect conclusions | Medium | Low | Analysis is read-only, recommendations require manual approval before deployment |
| Export job TTL too short (1 hour) | Low | Medium | Document TTL in API response, users must download within window |

---

**Plan Status**: COMPLETE - Ready for Phase 2 task generation via `/speckit.tasks`
