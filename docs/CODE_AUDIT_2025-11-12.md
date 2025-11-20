# Code Audit Report - November 12, 2025

## Executive Summary

**Auditor:** Senior Software Engineer (Claude Code)
**Date:** November 12, 2025
**Scope:** Comprehensive codebase review following Celery routing bug fix
**Total Issues Found:** 37
- 4 CRITICAL severity
- 8 HIGH severity
- 12 MEDIUM severity
- 7 LOW severity
- 6 Informational notes

## Audit Context

This audit was triggered after discovering a critical Celery routing key mismatch that caused complete processing stalls. The audit aims to identify similar configuration mismatches, architectural issues, and potential bugs before they cause production failures.

---

## CRITICAL Issues (Immediate Action Required)

### CRITICAL-1: Duplicate Volume Mount in docker-compose.yml

**File:** `docker-compose.yml:82`
**Impact:** Configuration confusion, potential mount conflicts
**Severity:** CRITICAL

**Issue:**
```yaml
volumes:
  - I:/Hopkins_Ranch_Trail_Cam_Pics:/mnt/images
  - I:/Hopkins_Ranch_Trail_Cam_Pics:/mnt/images  # DUPLICATE
```

**Fix:**
```yaml
volumes:
  - I:/Hopkins_Ranch_Trail_Cam_Pics:/mnt/images
```

**Action:** Remove duplicate line immediately

---

### CRITICAL-2: Export Job Status Callback Broken

**Files:**
- `src/backend/api/exports.py`
- `src/worker/tasks/exports.py`

**Impact:** Export jobs complete successfully but API never receives status updates. Jobs stuck in "processing" forever, users cannot download completed files.

**Severity:** CRITICAL

**Issue:**
Worker tasks finish and save files, but have no mechanism to update job status in the API. The API polls for status but worker never writes it.

**Current Flow (BROKEN):**
1. User requests PDF export via POST /api/exports/pdf
2. API creates job_id, returns {"job_id": "...", "status": "processing"}
3. Worker task runs, generates PDF, saves to disk
4. Task completes but never updates job status
5. API GET /api/exports/pdf/{job_id} returns "processing" forever
6. File exists on disk but user can't access it

**Fix Options:**

**Option A: Redis-Based Job Tracking (RECOMMENDED)**
```python
# src/worker/tasks/exports.py
from celery import current_task

@app.task(bind=True)
def generate_pdf_report_task(self, ...):
    try:
        # ... generate PDF ...

        # Update Redis with job status
        redis_client.setex(
            f"export_job:{self.request.id}",
            3600,  # 1 hour expiry
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

```python
# src/backend/api/exports.py
@router.get("/pdf/{job_id}")
async def get_pdf_export_status(job_id: str):
    from backend.app.main import redis_client

    # Check Redis for job status
    job_data = redis_client.get(f"export_job:{job_id}")
    if not job_data:
        raise HTTPException(404, "Job not found or expired")

    return json.loads(job_data)
```

**Option B: Database Job Table**
Create `export_jobs` table with status tracking (more permanent but slower).

**Action:** Implement Option A (Redis tracking) this week

---

### CRITICAL-3: No Validation on Export Requests

**File:** `src/backend/api/exports.py:30-50`
**Impact:** Invalid date ranges cause worker tasks to fail
**Severity:** CRITICAL

**Issue:**
```python
@router.post("/pdf")
async def create_pdf_export(request: PDFExportRequest):
    # No validation!
    task = celery_app.send_task(
        'worker.tasks.exports.generate_pdf_report_task',
        args=[request.dict()],
        queue='exports'
    )
```

**Fix:**
```python
@router.post("/pdf")
async def create_pdf_export(request: PDFExportRequest):
    # Validate date range
    if request.start_date > request.end_date:
        raise HTTPException(400, "start_date must be before end_date")

    # Validate date range not too large (prevent DoS)
    delta = request.end_date - request.start_date
    if delta.days > 365:
        raise HTTPException(400, "Date range cannot exceed 1 year")

    # Validate group_by value
    if request.group_by not in ["day", "week", "month"]:
        raise HTTPException(400, "group_by must be day, week, or month")

    task = celery_app.send_task(...)
```

**Action:** Add validation before Sprint 8 merges to main

---

### CRITICAL-4: Port Configuration Mismatch

**Files:** `.env`, `docker-compose.yml`
**Impact:** Scripts running on host may connect to wrong database/Redis
**Severity:** CRITICAL

**Issue:**
```bash
# .env
POSTGRES_PORT=5432  # Internal port
REDIS_PORT=6379     # Internal port

# docker-compose.yml
ports:
  - "5433:5432"  # External:Internal
  - "6380:6379"  # External:Internal
```

Scripts running on Windows host should use 5433/6380, but .env suggests 5432/6379.

**Fix:** Add clear comments
```bash
# .env
# Internal ports (used by containers)
POSTGRES_PORT=5432
REDIS_PORT=6379

# External ports (used by host machine):
# PostgreSQL: 5433
# Redis: 6380
# These are defined in docker-compose.yml
```

**Action:** Update .env with comments immediately

---

## HIGH Severity Issues

### HIGH-1: Missing Database Indexes

**File:** Database schema
**Impact:** Slow queries on large datasets (35k+ images)
**Severity:** HIGH

**Missing Indexes:**
```sql
-- images table
CREATE INDEX idx_images_processing_status ON images(processing_status);
CREATE INDEX idx_images_location_status ON images(location_id, processing_status);
CREATE INDEX idx_images_timestamp ON images(timestamp);

-- detections table
CREATE INDEX idx_detections_image_id ON detections(image_id);
CREATE INDEX idx_detections_deer_id ON detections(deer_id);
CREATE INDEX idx_detections_classification ON detections(classification);

-- deer table
CREATE INDEX idx_deer_sex ON deer(sex);
CREATE INDEX idx_deer_status ON deer(status);
```

**Action:** Create migration with these indexes

---

### HIGH-2: No Database Connection Retry Logic

**File:** `src/backend/core/database.py`
**Impact:** Transient network issues cause immediate failures
**Severity:** HIGH

**Current:**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Fix:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def get_db():
    db = SessionLocal()
    try:
        # Test connection
        db.execute(text("SELECT 1"))
        yield db
    finally:
        db.close()
```

**Action:** Add tenacity to requirements.txt and implement retry logic

---

### HIGH-3: Bare Except Clauses

**Files:** Multiple
**Impact:** Silently swallows important errors, makes debugging impossible
**Severity:** HIGH

**Found in:**
1. `scripts/monitor_processing.py:82` - `except:` with no type
2. `scripts/reprocess_with_new_model.py:156` - `except Exception` too broad

**Fix Pattern:**
```python
# BEFORE (BAD)
try:
    operation()
except:
    print("Error occurred")

# AFTER (GOOD)
try:
    operation()
except requests.RequestException as e:
    print(f"[ERROR] API request failed: {e}")
except json.JSONDecodeError as e:
    print(f"[ERROR] Invalid JSON response: {e}")
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    raise  # Re-raise if truly unexpected
```

**Action:** Replace all bare except clauses with specific exception types

---

### HIGH-4: Celery App Created Multiple Times

**Files:**
- `src/worker/celery_app.py` (canonical)
- `src/backend/app/main.py` (creates separate instance)
- `src/backend/api/images.py` (imports from main)
- `src/backend/api/exports.py` (imports from main)

**Impact:** Configuration drift, potential routing inconsistencies
**Severity:** HIGH

**Issue:**
Each import creates a new Celery app instance with potentially different configurations.

**Fix:** Centralize in `src/backend/core/celery.py`
```python
# src/backend/core/celery.py
from celery import Celery

# Import worker's canonical Celery app configuration
from worker.celery_app import app as worker_app

# Use same instance everywhere
celery_app = worker_app
```

```python
# All other files
from backend.core.celery import celery_app
```

**Action:** Create centralized celery module, update all imports

---

### HIGH-5: No Transaction Rollback on Error

**File:** `src/backend/api/images.py:80-100`
**Impact:** Partial database writes on failures
**Severity:** HIGH

**Issue:**
```python
for file in files:
    db.add(image)
    db.commit()  # Commits even if later files fail
```

**Fix:**
```python
try:
    for file in files:
        db.add(image)
    db.commit()  # Single commit at end
except Exception as e:
    db.rollback()  # Rollback all on any failure
    raise
```

**Action:** Wrap bulk operations in single transaction

---

### HIGH-6: Redis Connection Not Pooled

**File:** `src/worker/celery_app.py`
**Impact:** Connection exhaustion under load
**Severity:** HIGH

**Issue:**
```python
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'
```

No connection pooling configured.

**Fix:**
```python
from redis import ConnectionPool, Redis

redis_pool = ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    max_connections=50,
    socket_connect_timeout=5,
    socket_timeout=5
)

redis_client = Redis(connection_pool=redis_pool)
```

**Action:** Add connection pooling for Redis

---

### HIGH-7: File Handle Leak in Export Tasks

**File:** `src/worker/tasks/exports.py:80-120`
**Impact:** File descriptor exhaustion in long-running workers
**Severity:** HIGH

**Issue:**
```python
# File opened but not guaranteed to close on error
output_file = open(output_path, 'wb')
pdf.output(output_file)
```

**Fix:**
```python
with open(output_path, 'wb') as output_file:
    pdf.output(output_file)
```

**Action:** Use context managers for all file operations

---

### HIGH-8: Missing CSRF Protection

**File:** `src/backend/app/main.py`
**Impact:** Vulnerability to cross-site request forgery
**Severity:** HIGH

**Issue:**
FastAPI app has no CSRF middleware.

**Fix:**
```python
from fastapi.middleware.csrf import CSRFMiddleware

app.add_middleware(
    CSRFMiddleware,
    secret_key=os.getenv("SECRET_KEY", "change-this-in-production")
)
```

**Action:** Add CSRF middleware and generate secure secret key

---

## MEDIUM Severity Issues

### MEDIUM-1: Hardcoded Timeout Values

**Files:** Multiple
**Impact:** Inflexible configuration, potential production issues
**Severity:** MEDIUM

**Examples:**
- `scripts/auto_monitor_and_restart.sh:10` - CHECK_INTERVAL=60 hardcoded
- `src/backend/api/processing.py` - No timeout on queue operations

**Fix:** Move to environment variables
```bash
CHECK_INTERVAL="${CHECK_INTERVAL:-60}"
STALL_THRESHOLD="${STALL_THRESHOLD:-3}"
```

---

### MEDIUM-2: No Rate Limiting on API Endpoints

**File:** `src/backend/app/main.py`
**Impact:** Potential DoS via excessive requests
**Severity:** MEDIUM

**Fix:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@router.post("/batch")
@limiter.limit("10/minute")  # Max 10 batch requests per minute
async def queue_batch_processing(...):
    ...
```

---

### MEDIUM-3: Environment Variables Not Validated

**File:** `src/worker/celery_app.py:105-108`
**Impact:** Runtime errors if env vars invalid
**Severity:** MEDIUM

**Current:**
```python
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
```

No validation if REDIS_PORT is actually a number.

**Fix:**
```python
try:
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    if not (1 <= REDIS_PORT <= 65535):
        raise ValueError(f"REDIS_PORT must be 1-65535, got {REDIS_PORT}")
except ValueError as e:
    print(f"[FAIL] Invalid REDIS_PORT: {e}")
    sys.exit(1)
```

---

### MEDIUM-4: Inconsistent Logging Levels

**Files:** Multiple
**Impact:** Difficult debugging, noisy logs
**Severity:** MEDIUM

**Issue:**
Mix of print(), logger.info(), and echo statements.

**Fix:** Standardize on Python logging
```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Use everywhere
logger.info("Processing started")
logger.warning("Worker stalled")
logger.error("Failed to process image", exc_info=True)
```

---

### MEDIUM-5: No Health Check Endpoints

**File:** Missing from `src/backend/app/main.py`
**Impact:** Can't verify service health in production
**Severity:** MEDIUM

**Fix:**
```python
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Check database
        db.execute(text("SELECT 1"))

        # Check Redis
        redis_client.ping()

        return {
            "status": "healthy",
            "database": "ok",
            "redis": "ok",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(503, f"Unhealthy: {e}")
```

---

### MEDIUM-6: Worker Max Tasks Per Child Too High

**File:** `src/worker/celery_app.py:181`
**Current:** `worker_max_tasks_per_child=100`
**Impact:** Potential GPU memory leaks accumulate
**Severity:** MEDIUM

**Fix:**
```python
worker_max_tasks_per_child=50  # Restart worker more frequently
```

---

### MEDIUM-7-12: Additional Issues

- Inconsistent error messages (some ASCII, some with emojis)
- No database migration version tracking
- Missing API versioning (/v1/api/...)
- No request ID tracking for debugging
- File upload size limit not enforced at app level
- No metrics/Prometheus endpoint

---

## LOW Severity (Code Quality)

### LOW-1: Legacy Code Not Removed

**File:** `src/worker/tasks/process_images.py`
**Impact:** Code confusion, potential bugs if used
**Severity:** LOW

**Issue:**
File uses old task names (`src.worker.tasks.*` instead of `worker.tasks.*`) and appears to be pre-Sprint 4 legacy code.

**Action:** Mark as deprecated or remove if unused

---

### LOW-2: Inconsistent Type Hints

**Files:** Multiple
**Severity:** LOW

Some functions have full type hints, others have none. Standardize.

---

### LOW-3: Magic Numbers

**Examples:**
- `scripts/monitor_processing.py:46` - `width=50` (progress bar width)
- `src/worker/celery_app.py:181` - `100` (max tasks)

**Fix:** Use named constants

---

### LOW-4-7: Additional Code Quality Issues

- Docstrings missing on some functions
- Inconsistent string formatting (f-strings vs .format() vs %)
- Long functions (>100 lines) need refactoring
- Duplicate code in monitoring scripts

---

## Informational Notes

### INFO-1: Excellent Session Management

Worker tasks properly manage database sessions:
```python
try:
    # ... task work ...
finally:
    session.close()  # GOOD!
```

### INFO-2: Recent Routing Fix Verified

The Celery routing key fix is correctly implemented. All queue configurations now use direct routing.

### INFO-3: Good Error Handling in Detection Task

`src/worker/tasks/detection.py` has comprehensive exception handling with specific error types.

### INFO-4: Type Safety Generally Good

Most critical functions have proper type hints. Few improvements needed.

### INFO-5: Docker Configuration Clean

docker-compose.yml is well-structured (except for duplicate mount).

### INFO-6: Good Separation of Concerns

Clean separation between API layer, worker layer, and data layer.

---

## Recommended Action Plan

### This Week (CRITICAL Fixes)

1. [x] Fix Celery routing key mismatch (COMPLETED)
2. [ ] Remove duplicate volume mount in docker-compose.yml
3. [ ] Implement Redis job status tracking for exports
4. [ ] Add validation to export request endpoints
5. [ ] Add port configuration comments to .env

**Estimated Time:** 4 hours

### Next Week (HIGH Priority)

6. [ ] Create database indexes migration
7. [ ] Add database connection retry logic
8. [ ] Replace bare except clauses
9. [ ] Centralize Celery app creation
10. [ ] Fix transaction handling in bulk operations
11. [ ] Add Redis connection pooling
12. [ ] Fix file handle leaks (use context managers)
13. [ ] Add CSRF protection

**Estimated Time:** 8 hours

### Following Week (MEDIUM Priority)

14. [ ] Move hardcoded values to environment variables
15. [ ] Add API rate limiting
16. [ ] Validate environment variables at startup
17. [ ] Standardize logging (remove print statements)
18. [ ] Add health check endpoints
19. [ ] Reduce worker max_tasks_per_child to 50

**Estimated Time:** 6 hours

### Future Improvements (LOW Priority)

20. [ ] Remove legacy code (process_images.py)
21. [ ] Add consistent type hints
22. [ ] Replace magic numbers with constants
23. [ ] Add comprehensive docstrings
24. [ ] Refactor long functions
25. [ ] Add API versioning

**Estimated Time:** 12 hours

---

## Testing Recommendations

After implementing fixes, test:

1. **Export Job Lifecycle**
   - Create PDF export
   - Verify job status updates correctly
   - Download completed export
   - Verify job expires after 1 hour

2. **Database Resilience**
   - Stop PostgreSQL mid-operation
   - Verify retry logic works
   - Verify transactions rollback on error

3. **Queue Performance**
   - Queue 10,000 images
   - Verify Redis connections stable
   - Monitor for file descriptor leaks
   - Check GPU memory doesn't accumulate

4. **API Security**
   - Test CSRF protection
   - Test rate limiting
   - Verify input validation

5. **Worker Stability**
   - Run 1000 tasks
   - Verify worker restarts at 50 tasks
   - Check for memory leaks
   - Monitor GPU memory release

---

## Conclusion

The codebase is generally well-structured with good separation of concerns and proper resource management in critical areas. The recent Celery routing fix demonstrates the value of thorough code audits.

**Key Strengths:**
- Good database session management
- Proper error handling in detection tasks
- Clean separation of concerns
- Recent routing fix correctly implemented

**Key Weaknesses:**
- Export job status tracking broken
- Missing database indexes
- No retry logic for transient failures
- Configuration scattered across multiple files

**Overall Assessment:** Production-ready with critical fixes applied. Recommended to address CRITICAL and HIGH severity issues before scaling to larger datasets or deploying to production environment.

---

**Report Generated:** November 12, 2025
**Auditor:** Claude Code (Senior Software Engineer Mode)
**Next Audit:** Recommended after Sprint 9 completion
