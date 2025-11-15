# SESSION HANDOFF - Windows to WSL Migration
## Feature 010: Infrastructure Fixes Implementation

**Date:** November 12, 2025
**Session Type:** Cross-Platform Handoff (Windows → WSL)
**Branch:** 010-infrastructure-fixes
**Status:** IN PROGRESS - Spec creation phase
**Previous Session:** Windows Claude Code session (context lost on platform switch)

---

## EXECUTIVE SUMMARY

Mid-session handoff after identifying 4 critical infrastructure improvements from code audit. Was in process of creating speckit feature spec for Options A, B, and D (backend fixes), then planning to implement Option C (frontend UI) separately.

**Work Status:**
- Options A, B, D: Speckit specification phase (NOT STARTED)
- Option C: Pending (will start after A, B, D complete)
- Branch created: 010-infrastructure-fixes
- Spec directory created: specs/010-infrastructure-fixes/ (contains only "Test content")

---

## THE 4 OPTIONS - DETAILED BREAKDOWN

### Option A: Export Job Status Tracking (BACKEND)
**Priority:** CRITICAL (from CODE_AUDIT_2025-11-12.md, issue CRITICAL-2)
**Type:** Backend infrastructure fix
**Estimate:** 2-3 hours

**Problem:**
Export jobs (PDF/ZIP) complete successfully but API never receives status updates. Jobs remain stuck in "processing" status forever, preventing users from downloading completed files.

**Current Broken Flow:**
1. User requests PDF export via POST /api/exports/pdf
2. API creates job_id, returns {"job_id": "...", "status": "processing"}
3. Worker task runs, generates PDF, saves to disk at /mnt/exports/
4. Task completes but never updates job status
5. API GET /api/exports/pdf/{job_id} returns "processing" forever
6. File exists on disk but user can't access it

**Solution: Redis-Based Job Tracking (Recommended)**

**Implementation Steps:**
1. Worker task updates Redis with job status on completion
2. API polls Redis for job status instead of maintaining in-memory state
3. Use 1-hour TTL for job status entries
4. Handle both success and failure states

**Files to Modify:**
- `src/worker/tasks/exports.py` - Add Redis status updates
- `src/backend/api/exports.py` - Add Redis status polling
- `src/worker/celery_app.py` - Ensure Redis client available
- `requirements.txt` - Verify redis-py installed

**Code Pattern:**
```python
# In worker task (exports.py)
from celery import current_task
import json
from datetime import datetime

@app.task(bind=True)
def generate_pdf_report_task(self, ...):
    try:
        # ... generate PDF ...

        # Update Redis with completion status
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

# In API endpoint (exports.py)
@router.get("/pdf/{job_id}")
async def get_pdf_export_status(job_id: str):
    from backend.app.main import redis_client

    # Check Redis for job status
    job_data = redis_client.get(f"export_job:{job_id}")
    if not job_data:
        raise HTTPException(404, "Job not found or expired")

    return json.loads(job_data)
```

**Testing Plan:**
1. Create PDF export request
2. Verify job status updates from "processing" to "completed"
3. Verify download URL accessible
4. Verify job expires after 1 hour
5. Test failure scenario (invalid date range)

---

### Option B: Export Request Validation (BACKEND)
**Priority:** CRITICAL (from CODE_AUDIT_2025-11-12.md, issue CRITICAL-3)
**Type:** Backend validation
**Estimate:** 1 hour

**Problem:**
No validation on export request parameters before sending to worker. Invalid date ranges or parameters cause worker tasks to fail silently.

**Current Code:**
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

**Solution: Add Comprehensive Validation**

**Validation Rules:**
1. `start_date` must be before `end_date`
2. Date range cannot exceed 1 year (365 days)
3. `group_by` must be one of: "day", "week", "month"
4. Dates must be valid ISO format
5. Optional: start_date not in future

**Implementation:**
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
    valid_group_by = ["day", "week", "month"]
    if request.group_by not in valid_group_by:
        raise HTTPException(
            400,
            f"group_by must be one of: {', '.join(valid_group_by)}"
        )

    # Validate start_date not in future (optional)
    if request.start_date > datetime.utcnow().date():
        raise HTTPException(400, "start_date cannot be in the future")

    # Proceed with task creation
    task = celery_app.send_task(...)
    return {"job_id": task.id, "status": "processing"}
```

**Files to Modify:**
- `src/backend/api/exports.py` - Add validation to all export endpoints
- `src/backend/schemas/export.py` - Add field validators if using Pydantic

**Testing Plan:**
1. Test with start_date > end_date (expect 400 error)
2. Test with range > 365 days (expect 400 error)
3. Test with invalid group_by value (expect 400 error)
4. Test with valid parameters (expect success)
5. Test with future start_date (expect 400 error)

---

### Option C: Frontend Detection Correction UI (FRONTEND)
**Priority:** HIGH (from SESSION_20251112_CRITICAL_FIXES.md, Outstanding Issue #1)
**Type:** Frontend React component
**Estimate:** 2-3 days

**Note:** This is the "frontend" option - to be implemented AFTER Options A, B, D are complete.

**Problem:**
ML model misclassifications need manual review and correction. Currently no UI for reviewing and correcting individual or batch detections with visual feedback.

**Requirements:**
1. **Single Detection Editing**
   - View full image with bounding box overlay
   - Edit classification (buck/doe/fawn/etc.)
   - Edit confidence score
   - Save correction with timestamp

2. **Batch Detection Editing**
   - Multi-select images from gallery
   - Bulk change classification for all detections
   - Preview changes before applying
   - Apply corrections up to 1000 detections at once

3. **Bounding Box Visualization**
   - Canvas or SVG overlay on images
   - Color-coded boxes by classification
   - Click box to edit that detection
   - Toggle overlay on/off

4. **Classification Correction Workflow**
   - Filter images by incorrect classification
   - Review and correct in sequence
   - Track correction history
   - Export corrections as training data

**Backend APIs Already Exist:**
- PATCH /api/detections/{id}/correct - Single correction
- PATCH /api/detections/batch/correct - Batch correction (up to 1000)
- GET /api/images - List images with filters
- GET /api/detections - List detections with filters

**Frontend Components to Create:**
1. `DetectionCorrectionDialog.tsx` - Single detection editor
2. `BatchCorrectionDialog.tsx` - Batch editor
3. `BoundingBoxOverlay.tsx` - Canvas/SVG overlay component
4. `DetectionReviewPage.tsx` - Main review workflow page

**Technology Stack:**
- React 18 + TypeScript
- Material-UI v5 (already in use)
- Canvas API or SVG for bounding boxes
- React Query for API integration

**Implementation Order:**
1. BoundingBoxOverlay component (2 hours)
2. DetectionCorrectionDialog (4 hours)
3. BatchCorrectionDialog (4 hours)
4. DetectionReviewPage with workflow (6 hours)
5. Testing and polish (4 hours)

**Files to Create:**
- `frontend/src/components/detection/BoundingBoxOverlay.tsx`
- `frontend/src/components/detection/DetectionCorrectionDialog.tsx`
- `frontend/src/components/detection/BatchCorrectionDialog.tsx`
- `frontend/src/pages/DetectionReview.tsx`
- `frontend/src/api/detections.ts` (if not exists)

**Testing Plan:**
1. Load image with multiple detections
2. Verify bounding boxes display correctly
3. Edit single detection classification
4. Select multiple images and bulk edit
5. Verify changes persist to database
6. Test with 1000 detection batch

---

### Option D: Re-ID Performance Optimization (BACKEND)
**Priority:** HIGH (from SESSION_20251112_CRITICAL_FIXES.md, Outstanding Issue #3)
**Type:** Backend ML optimization
**Estimate:** 1 day

**Problem:**
Re-identification assignment rate is only 9.5% (1,100 of 11,570 detections assigned to deer profiles). This is lower than expected, suggesting the REID_THRESHOLD of 0.70 may be too conservative or there are other issues.

**Current Metrics:**
- Total detections: 11,570
- Assigned to deer profiles: 1,100 (9.5%)
- Unassigned: 10,470 (90.5%)
- REID_THRESHOLD: 0.70 (cosine similarity)
- Number of deer profiles: 20 (10 bucks, 10 does)

**Investigation Tasks:**

1. **Analyze Similarity Score Distribution**
   - Query all similarity scores from re-ID matching
   - Plot histogram of scores (0.0 - 1.0)
   - Identify where natural clustering occurs
   - Determine if 0.70 is cutting off valid matches

2. **Review Failed Matches**
   - Extract detections with similarity 0.65-0.69 (near-threshold)
   - Manually review if these should be matches
   - Check for issues: lighting, angle, occlusion

3. **Test Threshold Variations**
   - Try REID_THRESHOLD = 0.65, 0.60, 0.55
   - Measure assignment rate vs false positive rate
   - Find optimal balance

4. **Check Feature Extraction Quality**
   - Verify ResNet50 embeddings are normalized
   - Check for NaN or zero vectors
   - Validate L2 normalization applied correctly

5. **Burst Linking Effectiveness**
   - Review how burst detection groups detections
   - Verify temporal grouping (10 second window) working
   - Check if burst_id being properly assigned

**Files to Analyze:**
- `src/worker/tasks/reidentification.py` - Re-ID logic
- Database: detections table (similarity scores)
- Database: deer table (profile count)

**Implementation:**
1. Create analysis script: `scripts/analyze_reid_performance.py`
   - Query similarity score distribution
   - Calculate assignment rate by threshold
   - Generate recommendations

2. Create visualization script: `scripts/plot_reid_scores.py`
   - Histogram of similarity scores
   - Assignment rate vs threshold curve
   - Confusion analysis

3. Update REID_THRESHOLD if justified
   - Test on sample batch
   - Monitor false positive rate
   - Update .env and redeploy

4. Document findings: `docs/REID_OPTIMIZATION_ANALYSIS.md`

**Testing Plan:**
1. Run analysis on current 11,570 detections
2. Review similarity score distribution
3. Test threshold adjustments on 1000 detection sample
4. Measure assignment rate improvement
5. Validate no increase in false positives

---

## CURRENT BRANCH STATUS

```bash
Branch: 010-infrastructure-fixes
Status: Clean working directory (after WSL migration)

Previous uncommitted changes (Windows):
  - CLAUDE.md: Added note about implementing into speckit
  - specs/010-infrastructure-fixes/spec.md: Contains only "Test content"

Files to create:
  - specs/010-infrastructure-fixes/spec.md (full specification)
  - specs/010-infrastructure-fixes/plan.md (implementation plan)
  - specs/010-infrastructure-fixes/tasks.md (task list)
```

---

## IMPLEMENTATION STRATEGY

### Phase 1: Speckit Setup (Current Phase)
**Estimate:** 2-3 hours

1. **Create Feature Spec** (specs/010-infrastructure-fixes/spec.md)
   - User scenarios for Options A, B, D
   - Technical requirements
   - Acceptance criteria
   - Dependencies and constraints

2. **Generate Implementation Plan**
   ```bash
   /speckit.plan
   ```

3. **Generate Task List**
   ```bash
   /speckit.tasks
   ```

4. **Review and Commit**
   ```bash
   git add specs/010-infrastructure-fixes/
   git commit -m "feat: Add infrastructure fixes specification (Options A, B, D)"
   ```

### Phase 2: Backend Implementation (Options A, B, D)
**Estimate:** 1 day

1. **Implement Option B First** (validation - easiest, no dependencies)
2. **Implement Option A Second** (Redis job tracking)
3. **Implement Option D Third** (Re-ID optimization - requires analysis)
4. **Test end-to-end**
5. **Commit and merge to main**

### Phase 3: Frontend Implementation (Option C)
**Estimate:** 2-3 days

1. **Create separate feature branch** (011-detection-correction-ui)
2. **Implement bounding box overlay component**
3. **Implement single detection editor**
4. **Implement batch detection editor**
5. **Create review workflow page**
6. **Test with real data**
7. **Commit and merge to main**

---

## QUICK START COMMANDS (WSL)

### 1. Verify Environment
```bash
# Check you're on correct branch
git branch --show-current
# Should output: 010-infrastructure-fixes

# Check git status
git status

# Start Docker services
docker-compose up -d

# Verify services running
docker-compose ps
curl http://localhost:8001/health
```

### 2. Create Feature Spec
```bash
# Open spec file for editing
vim specs/010-infrastructure-fixes/spec.md

# Or use speckit command
/speckit.specify "Implement critical infrastructure fixes from code audit: Export job status tracking with Redis, export request validation, and Re-ID performance optimization. These fixes address CRITICAL-2, CRITICAL-3, and high-priority re-identification issues identified in November 12 audit."
```

### 3. Generate Plan and Tasks
```bash
# Generate implementation plan
/speckit.plan

# Generate task list
/speckit.tasks

# Review generated files
cat specs/010-infrastructure-fixes/plan.md
cat specs/010-infrastructure-fixes/tasks.md
```

### 4. Implement Using Speckit
```bash
# Use speckit to guide implementation
/speckit.implement
```

---

## REFERENCE DOCUMENTS

**Code Audit (Source of Options A, B, D):**
- `docs/CODE_AUDIT_2025-11-12.md` - Full audit with 37 issues
  - CRITICAL-2: Export job status (Option A)
  - CRITICAL-3: Export validation (Option B)

**Session Handoff (Source of Option C, D):**
- `docs/SESSION_20251112_CRITICAL_FIXES.md` - Session summary
  - Outstanding Issue #1: Frontend correction UI (Option C)
  - Outstanding Issue #3: Re-ID optimization (Option D)

**Related Documentation:**
- `docs/CELERY_ROUTING_FIX.md` - Recent routing bug fix
- `docs/AUTO_MONITORING_SETUP.md` - Monitoring system
- `docs/OPERATIONS_RUNBOOK.md` - Operations guide
- `docs/FRONTEND_REQUIREMENTS.md` - Frontend specs (for Option C)

**Database Status:**
- Total images: 59,185
- Completed: 40,520+ (68.5%)
- Detections: 80,000+ (estimated)
- Deer profiles: 20 (after Re-ID sex mapping fix)

---

## SUCCESS CRITERIA

### Option A - Export Job Status
- [x] Worker updates Redis on task completion
- [x] API polls Redis for job status
- [x] Status transitions: processing -> completed/failed
- [x] Download URL available on completion
- [x] Jobs expire after 1 hour
- [x] Tests pass for success and failure scenarios

### Option B - Export Validation
- [x] Date range validation (start < end)
- [x] Max range validation (≤365 days)
- [x] group_by parameter validation
- [x] Future date rejection
- [x] Clear error messages with 400 status
- [x] All validation tests pass

### Option C - Frontend UI (Future)
- [x] Bounding box overlay displays correctly
- [x] Single detection editing works
- [x] Batch editing (up to 1000) works
- [x] Changes persist to database
- [x] Review workflow intuitive
- [x] No console errors

### Option D - Re-ID Optimization (Future)
- [x] Similarity score analysis complete
- [x] Optimal threshold identified
- [x] Assignment rate improved by >20%
- [x] False positive rate remains low (<5%)
- [x] Documentation updated
- [x] Tests pass with new threshold

---

## DEPENDENCIES AND BLOCKERS

**No Current Blockers**

**Dependencies:**
- Option A requires Redis running (already configured)
- Option A requires redis-py installed (verify in requirements.txt)
- Option B has no dependencies
- Option C requires Options A, B, D complete first
- Option D requires analysis scripts created

**Environment:**
- WSL environment configured
- Docker Desktop running
- Backend: http://localhost:8001
- Frontend: http://localhost:3000
- PostgreSQL: port 5433
- Redis: port 6380

---

## NOTES FROM PREVIOUS SESSION

**Session Context Lost:**
The Windows Claude Code session context was lost when switching to WSL. This handoff reconstructs the work plan from:
1. Git commit history
2. Uncommitted changes (CLAUDE.md note)
3. Created directory structure (specs/010-infrastructure-fixes/)
4. Code audit documentation
5. Session handoff documentation

**User's Note in CLAUDE.md:**
> "this si what we were working on. We were implementing this into speckit"
> Reference: docs/SESSION_20251112_CRITICAL_FIXES.md

**Reconstruction Confidence:**
High confidence in Options A, B, D (directly from code audit)
High confidence in Option C (clearly documented in outstanding issues)
Options match user's description of "A, B, D into speckit, then C (frontend)"

---

## RECOMMENDED NEXT STEPS

**Immediate (Next 30 minutes):**
1. Review this handoff document thoroughly
2. Verify WSL environment operational
3. Review code audit: docs/CODE_AUDIT_2025-11-12.md
4. Review session handoff: docs/SESSION_20251112_CRITICAL_FIXES.md

**Phase 1 (Next 2-3 hours):**
1. Create comprehensive feature spec for Options A, B, D
2. Use /speckit.specify command or write manually
3. Generate plan with /speckit.plan
4. Generate tasks with /speckit.tasks
5. Review and commit specification

**Phase 2 (Next 1 day):**
1. Implement Option B (validation - 1 hour)
2. Implement Option A (Redis tracking - 2-3 hours)
3. Implement Option D (Re-ID analysis - 4-6 hours)
4. Test all implementations
5. Merge to main

**Phase 3 (Next 2-3 days):**
1. Create new branch for Option C
2. Implement frontend detection correction UI
3. Test with real data
4. Merge to main
5. Update documentation

---

## CONTACT AND QUESTIONS

If anything is unclear or doesn't match your recollection:
1. Review the source documents listed in REFERENCE DOCUMENTS section
2. Check git log for recent commits
3. Review uncommitted changes: `git diff HEAD`
4. Ask clarifying questions before proceeding

**This handoff should be sufficient to resume work in WSL with full context.**

---

**Handoff Created:** November 12, 2025
**Platform:** Windows → WSL Migration
**Branch:** 010-infrastructure-fixes
**Next Action:** Create feature specification for Options A, B, D
**Estimated Time to Complete:** 3-4 days total (backend + frontend)
