# Follow-Up Tasks for Feature 010: Infrastructure Fixes

**Date Created:** 2025-11-13
**Parent Feature:** 010-infrastructure-fixes
**Status:** PARTIALLY COMPLETE (F01, F02, F03 completed in Option A scope)

These tasks were identified during Option A implementation. Tasks F01, F02, and F03 were completed as part of the expanded Option A scope per user request. Tasks F04 and F05 remain for future work.

---

## TASK-010-F01: Complete Redis Migration for POST Endpoints [COMPLETED]

**Priority:** HIGH
**Category:** Technical Debt
**Estimated Effort:** 1-2 hours
**Status:** COMPLETED in Option A scope
**Completed:** 2025-11-13

### Description

POST endpoints (`/api/exports/pdf` and `/api/exports/zip`) currently use in-memory `export_jobs` dictionary while GET endpoints read from Redis. This creates dual storage and inconsistency.

### Current Behavior

```python
# POST endpoint (exports.py lines 86-142)
export_jobs[job_id] = {
    "job_id": job_id,
    "status": "pending",
    "created_at": now,
    # ... stored in memory
}
```

```python
# GET endpoint (exports.py lines 153-218)
status_json = redis_client.get(f"export_job:{job_id}")
# ... reads from Redis
```

### Required Changes

1. **Remove in-memory dict:**
   ```python
   # DELETE THIS LINE (exports.py:45)
   export_jobs = {}
   ```

2. **Update POST /api/exports/pdf:**
   ```python
   # Replace dict operations with Redis (lines 105-125)
   key = f"export_job:{job_id}"
   initial_status = {
       "status": "processing",
       "job_id": job_id,
       "created_at": datetime.utcnow().isoformat()
   }
   redis_client.setex(key, 3600, json.dumps(initial_status))
   ```

3. **Update POST /api/exports/zip:**
   ```python
   # Replace dict operations with Redis (lines 245-267)
   key = f"export_job:{job_id}"
   initial_status = {
       "status": "processing",
       "job_id": job_id,
       "created_at": datetime.utcnow().isoformat(),
       "total_detections": detection_count,
       "processed_count": 0
   }
   redis_client.setex(key, 3600, json.dumps(initial_status))
   ```

### Files to Modify

- `src/backend/api/exports.py`
  - Lines 45: Remove `export_jobs = {}`
  - Lines 105-125: Update PDF POST handler
  - Lines 245-267: Update ZIP POST handler

### Success Criteria

- [x] No references to `export_jobs` dict in exports.py
- [x] POST endpoints initialize Redis status
- [x] GET endpoints continue to work unchanged
- [x] Integration test passes

### Testing

```bash
# Test POST creates Redis key
curl -X POST http://localhost:8001/api/exports/pdf \
  -H "Content-Type: application/json" \
  -d '{"report_type": "seasonal_activity", "start_date": "2023-09-01", "end_date": "2024-01-31", "group_by": "month"}'

# Verify Redis key exists
docker-compose exec redis redis-cli --scan --pattern "export_job:*"
```

---

## TASK-010-F02: Update DELETE Endpoint for Redis Cleanup [COMPLETED]

**Priority:** MEDIUM
**Category:** Technical Debt
**Estimated Effort:** 30 minutes
**Status:** COMPLETED in Option A scope
**Completed:** 2025-11-13

### Description

DELETE `/{job_id}` endpoint currently tries to delete from in-memory dict but doesn't clean up Redis keys.

### Current Behavior

```python
# exports.py lines 389-404
if job_id not in export_jobs:
    raise HTTPException(404, "Export job not found")

# ... Celery revoke, file cleanup ...

del export_jobs[job_id]  # Dict delete only
```

### Required Changes

```python
@router.delete("/{job_id}")
def delete_export_job(job_id: str):
    key = f"export_job:{job_id}"

    # Check if job exists in Redis
    if not redis_client.exists(key):
        raise HTTPException(404, "Export job not found")

    # Get job data for cleanup
    job_data = json.loads(redis_client.get(key))

    # Cancel Celery task if processing
    if job_data.get("status") in ["pending", "processing"]:
        # ... existing Celery revoke code ...

    # Delete file if exists
    filename = job_data.get("filename")
    if filename:
        file_path = EXPORT_DIR / filename
        if file_path.exists():
            file_path.unlink()

    # Delete Redis key
    redis_client.delete(key)

    return None  # 204 No Content
```

### Files to Modify

- `src/backend/api/exports.py` (lines 389-404)

### Success Criteria

- [x] DELETE removes Redis key
- [x] DELETE handles missing jobs (404)
- [x] DELETE cancels Celery tasks (warning logged if task_id not stored)
- [x] DELETE removes export files

### Testing

```bash
# Create job
JOB_ID=$(curl -X POST http://localhost:8001/api/exports/pdf ...)

# Verify Redis key exists
docker-compose exec redis redis-cli EXISTS "export_job:$JOB_ID"

# Delete job
curl -X DELETE http://localhost:8001/api/exports/$JOB_ID

# Verify Redis key removed
docker-compose exec redis redis-cli EXISTS "export_job:$JOB_ID"
```

---

## TASK-010-F03: Fix Integration Test Fixture [COMPLETED]

**Priority:** HIGH
**Category:** Testing
**Estimated Effort:** 5 minutes
**Status:** COMPLETED in Option A scope
**Completed:** 2025-11-13

### Description

Integration test `test_pdf_export_full_lifecycle` fails because `sample_export_request` fixture is missing required `report_type` field.

### Current Fixture

```python
# tests/conftest.py lines 114-119
@pytest.fixture
def sample_export_request():
    return {
        "start_date": "2023-09-01",
        "end_date": "2024-01-31",
        "group_by": "month"
    }
```

### Required Fix

```python
@pytest.fixture
def sample_export_request():
    """Sample valid export request data for testing."""
    return {
        "report_type": "seasonal_activity",  # ADD THIS
        "start_date": "2023-09-01",
        "end_date": "2024-01-31",
        "group_by": "month",
        "include_charts": True,
        "include_tables": True,
        "include_insights": True,
        "title": "Test Seasonal Activity Report"
    }
```

### Files to Modify

- `tests/conftest.py` (lines 114-119)

### Success Criteria

- [x] Integration test passes (12/12 tests pass)
- [x] POST request returns 202 Accepted
- [x] Test validates full lifecycle

### Testing

```bash
docker-compose exec -T backend python3 -m pytest \
  tests/integration/test_export_lifecycle.py::TestExportLifecycle::test_pdf_export_full_lifecycle -v
```

---

## TASK-010-F04: Investigate Route Conflict

**Priority:** LOW
**Category:** Investigation
**Estimated Effort:** 1 hour

### Description

Possible route conflict between DELETE `/{job_id}` and GET `/pdf/{job_id}`. During testing, curl requests to GET endpoints returned 404 from custom handler, suggesting FastAPI might be matching the DELETE route first.

### Evidence

```
# OpenAPI shows route exists
/api/exports/pdf/{job_id}  # GET endpoint registered

# But curl returns custom 404
curl http://localhost:8001/api/exports/pdf/test-id
{"error":"Not Found","message":"The endpoint does not exist"}

# Function works when called directly (not through FastAPI router)
# Test client works (different routing mechanism)
```

### Investigation Steps

1. Review FastAPI route precedence rules
2. Test with actual curl in production-like environment
3. Check if DELETE `/{job_id}` is too generic
4. Consider route specificity improvements

### Possible Solutions

**Option 1: Make DELETE more specific**
```python
@router.delete("/jobs/{job_id}")  # Instead of /{job_id}
```

**Option 2: Reorder routes (more specific first)**
```python
# Ensure GET /pdf/{job_id} registered before DELETE /{job_id}
```

**Option 3: Use path parameter type hints**
```python
from uuid import UUID

@router.delete("/{job_id}")
def delete_export_job(job_id: UUID):  # Stricter matching
```

### Files to Review

- `src/backend/api/exports.py` (route definitions)
- `src/backend/app/main.py` (router registration order)

### Success Criteria

- [ ] Curl requests to GET `/api/exports/pdf/{job_id}` work
- [ ] Curl requests to DELETE `/api/exports/{job_id}` work
- [ ] No route conflicts in logs
- [ ] OpenAPI spec shows both routes correctly

---

## TASK-010-F05: Add Comprehensive Logging

**Priority:** LOW
**Category:** Observability
**Estimated Effort:** 1 hour

### Description

Add structured logging to track Redis operations and debug production issues.

### Required Logging

**Worker Tasks:**
```python
logger.info(f"[REDIS] Set status: export_job:{job_id} = processing, TTL=3600s")
logger.info(f"[REDIS] Updated status: export_job:{job_id} = completed")
logger.error(f"[REDIS] Failed to update status: {e}")
```

**API Endpoints:**
```python
logger.debug(f"[REDIS] GET export_job:{job_id}")
logger.warning(f"[REDIS] Key not found: export_job:{job_id}")
logger.info(f"[REDIS] TTL remaining: {ttl}s for job {job_id}")
```

### Files to Modify

- `src/worker/tasks/exports.py`
- `src/backend/api/exports.py`

### Success Criteria

- [ ] All Redis operations logged
- [ ] Log levels appropriate (DEBUG/INFO/WARNING/ERROR)
- [ ] Logs include job_id for tracing
- [ ] Production logs useful for debugging

---

## Dependencies

```
TASK-010-F03 (Fix test fixture)
    ↓ (blocks)
TASK-010-F01 (Complete Redis migration)
    ↓ (enables)
Integration test passing

TASK-010-F01 (Complete Redis migration)
    ↓ (prerequisite for)
TASK-010-F02 (Update DELETE endpoint)

TASK-010-F04 (Route conflict investigation)
    ↓ (independent of other tasks)
Production deployment readiness
```

## Execution Order

1. **TASK-010-F03** (5 min) - Quick fix, unblocks testing
2. **TASK-010-F01** (1-2 hrs) - Core migration, critical path
3. **TASK-010-F02** (30 min) - Cleanup, depends on F01
4. **TASK-010-F05** (1 hr) - Observability, can run in parallel
5. **TASK-010-F04** (1 hr) - Investigation, lowest priority

**Total Estimated Effort:** 4-5 hours

## Success Metrics

- [x] All 12 Option A tests passing (100%) - ACHIEVED
- [x] Zero usage of in-memory `export_jobs` dict - ACHIEVED
- [x] All Redis keys cleaned up properly - ACHIEVED
- [ ] Production curl requests work - PENDING (low priority investigation)
- [ ] Logs provide visibility into job lifecycle - PENDING (TASK-010-F05)
