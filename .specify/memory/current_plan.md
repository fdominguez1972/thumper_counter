# Current Plan - Re-ID Enhancement Roadmap
**Date:** November 15, 2025
**Status:** Feature 010 Complete, Feature 009 Specification Ready
**Branch:** 009-reid-enhancement (new feature branch)

---

## Executive Summary

Feature 010 (Infrastructure Fixes) completed successfully with 60.35% assignment rate achieved through threshold optimization. Now beginning Feature 009 (Re-ID Enhancement) to improve accuracy further through ML enhancements.

**Current Assignment Rate:** 60.35% (6,982 of 11,570 detections assigned to 165 deer profiles)
**Goal:** Increase assignment rate to 70-75% through multi-scale features and ensemble learning
**Approach:** 5-week phased implementation following recommended ML enhancement roadmap

---

## Three-Phase Plan

### Phase 1: Backfill Analysis (COMPLETE)
**Status:** COMPLETED (2025-11-15 21:06)
**Duration:** 7 minutes (not 6-8 hours!)
**Results:** 4,546 detections, 228,695 similarity scores
**Log File:** `/tmp/backfill.log`

**What's Running:**
```bash
Script: scripts/backfill_similarity_scores.py
Target: 4,546 detections with deer_id assignments
Expected Output: ~240,000 similarity scores
Purpose: Analyze Re-ID performance to optimize threshold
```

**How to Monitor:**
```bash
# Check progress
tail -f /tmp/backfill.log

# Check if still running
ps aux | grep backfill

# Check database progress
docker-compose exec -T db psql -U deertrack deer_tracking -c "
SELECT COUNT(*) FROM reid_similarity_scores;
"
```

**Expected Completion:** November 16, 2025 ~03:00-05:00

---

### Phase 2: Analysis & Threshold Tuning (COMPLETE)
**Status:** COMPLETED (2025-11-15 21:17)
**Duration:** 10 minutes
**Decision:** Lowered REID_THRESHOLD from 0.70 to 0.40
**Location:** `specs/010-infrastructure-fixes/OPTION_D_QUICKSTART.md`

**Tasks:**

1. **Query Similarity Distribution**
   ```sql
   SELECT
     ROUND(similarity_score, 1) as score_bucket,
     COUNT(*) as frequency,
     SUM(CASE WHEN matched THEN 1 ELSE 0 END) as matched_count
   FROM reid_similarity_scores
   GROUP BY score_bucket
   ORDER BY score_bucket DESC;
   ```

2. **Test Threshold Variations**
   ```sql
   -- Simulate different thresholds
   SELECT
     test_threshold,
     COUNT(DISTINCT detection_id) as total_detections,
     COUNT(DISTINCT CASE WHEN similarity_score >= test_threshold THEN detection_id END) as would_match,
     ROUND(100.0 * COUNT(DISTINCT CASE WHEN similarity_score >= test_threshold THEN detection_id END) / COUNT(DISTINCT detection_id), 2) as assignment_rate
   FROM reid_similarity_scores
   CROSS JOIN (SELECT unnest(ARRAY[0.40, 0.45, 0.50, 0.55, 0.60]) as test_threshold) t
   GROUP BY test_threshold
   ORDER BY test_threshold DESC;
   ```

3. **Identify Near-Miss Detections**
   ```sql
   -- Find detections just below threshold
   SELECT COUNT(*)
   FROM reid_similarity_scores
   WHERE matched = false
     AND similarity_score >= (threshold_used - 0.05);
   ```

4. **Make Decision**
   - Review histogram for natural clustering
   - Identify optimal threshold balancing assignment vs accuracy
   - Document recommendation with evidence

5. **Apply New Threshold (if justified)**
   ```bash
   # Update .env
   vim .env  # Change REID_THRESHOLD=0.55 to new value

   # Restart worker
   docker-compose restart worker

   # Queue unassigned detections for reprocessing
   curl -X POST "http://localhost:8001/api/processing/reid/reprocess"
   ```

**Success Criteria:**
- Data-driven threshold recommendation
- Clear evidence for decision (histogram, assignment rate projection)
- Optional: Assignment rate improvement demonstrated

---

### Phase 3: Reprocessing Unassigned Detections (IN PROGRESS)
**Status:** RUNNING (started 2025-11-15 21:17)
**Duration:** ~6 minutes total
**Progress:** 743 of 7,024 detections processed (10.6%)
**Results So Far:** Assignment rate 39.29% → 45.71% (+6.42%)

### Phase 4: Choose Next Feature (READY)
**Status:** READY (after reprocessing completes in ~5 minutes)
**Duration:** Depends on choice

**Options:**

#### Option A: Clean Up Branch 011-frontend-enhancements
**Branch:** 011-frontend-enhancements (exists on remotes)
**Work Done:** ML model improvements (Nov 11, 2025)
**Remaining:**
- Validate new model performance
- Clean up data quality issues
- Reprocess dataset with improved model (optional)
- Merge to main

**Estimate:** 4-6 hours
**Impact:** Better classification accuracy (85.1% mAP50)

#### Option B: Frontend Detection Correction UI (HIGH VALUE)
**Purpose:** Manual correction of ML misclassifications
**Features:**
- Visual bounding box editor
- Single and batch detection correction
- Export corrected data for retraining

**Estimate:** 2-3 days
**Impact:** Enables continuous model improvement through corrections

#### Option C: Complete Rut Season Analysis (Feature 008)
**Status:** Phase 8 pending (Feature 010 fixes should help!)
**Remaining:**
- Validate PDF export works (should work now with Feature 010!)
- Add charts/visualizations
- End-to-end testing
- Merge to main

**Estimate:** 4-6 hours
**Impact:** Seasonal analysis capability

#### Option D: Reprocess Unassigned Detections
**Current:** 7,024 unassigned detections (60.71%)
**Approach:** Queue for re-ID with new threshold
**Estimate:** 2-3 hours + overnight processing
**Impact:** Potentially create more deer profiles

**Recommendation:** Will be clearer after Phase 2 analysis

---

## Current System State

### Database Status
```
Total Images: 59,185
Processed: 59,077 (99.82%)
Failed: 104
Pending: 0

Total Detections: 11,570
Assigned: 4,546 (39.29%)
Unassigned: 7,024 (60.71%)

Deer Profiles: 53
- Does: 38 (71.7%)
- Bucks: 15 (28.3%)
```

### Feature Status
- **Feature 010:** ✓ COMPLETE (merged to main)
  - Option A: Export status tracking ✓
  - Option B: Export validation ✓
  - Option D: Similarity logging infrastructure ✓
- **Feature 011:** Branch exists, needs cleanup
- **Feature 008:** Mostly complete, pending polish

### Infrastructure
- Redis: reid_similarity_scores logging active
- Worker: 32 threads, GPU enabled
- REID_THRESHOLD: 0.55 (current)
- Database: Migration 011 applied

---

## Quick Resume Commands

### Check Phase 1 Status
```bash
# Is backfill still running?
ps aux | grep backfill | grep -v grep

# Check progress in log
tail -100 /tmp/backfill.log | grep PROGRESS

# Check database records
docker-compose exec -T db psql -U deertrack deer_tracking -c "
SELECT COUNT(*) as scores_logged,
       COUNT(DISTINCT detection_id) as detections_analyzed,
       MIN(calculated_at) as started_at,
       MAX(calculated_at) as latest_at
FROM reid_similarity_scores
WHERE calculated_at > NOW() - INTERVAL '24 hours';
"
```

### Start Phase 2 (After Phase 1 Completes)
```bash
# Follow guide
cat specs/010-infrastructure-fixes/OPTION_D_QUICKSTART.md

# Run analysis queries (section: Analysis Queries)
docker-compose exec -T db psql -U deertrack deer_tracking

# Generate visualizations (if needed)
docker-compose exec -T backend python3 /app/scripts/analyze_reid_performance.py
```

### Phase 3 Decision Point
```bash
# Review options
cat .specify/memory/current_plan.md

# Check branch status
git branch -a | grep 011

# Review pending features
ls specs/ | grep -E "008|011|012"
```

---

## Success Metrics

### Phase 1 Complete When:
- [x] Backfill script started successfully
- [ ] 4,546 detections processed (~240,000 scores logged)
- [ ] Log shows completion message
- [ ] Database contains full similarity distribution

### Phase 2 Complete When:
- [ ] Similarity histogram generated
- [ ] Threshold recommendation documented
- [ ] Decision made (keep 0.55 or change)
- [ ] If changed: worker restarted with new threshold

### Phase 3 Complete When:
- [ ] Feature option chosen based on priorities
- [ ] Spec created (if new feature)
- [ ] Implementation started

---

## Files to Reference

**Feature 010 Documentation:**
- `specs/010-infrastructure-fixes/FEATURE_COMPLETE.md` - Overview
- `specs/010-infrastructure-fixes/OPTION_D_QUICKSTART.md` - Analysis guide
- `docs/FEATURE_010_MERGE_SUMMARY.md` - Merge details

**Analysis Scripts:**
- `scripts/backfill_similarity_scores.py` - Currently running
- `scripts/analyze_reid_performance.py` - Visualization (ready to use)
- `scripts/analyze_reid_simple.py` - Simplified analysis

**Session Handoffs:**
- `docs/SESSION_20251112_WSL_HANDOFF.md` - Feature 010 context
- `docs/SESSION_20251112_CRITICAL_FIXES.md` - Critical fixes background

---

## Notes

**Backfill Fix Applied:**
- Fixed numpy boolean type error
- Changed `matched` and `sex_match` to `bool()` cast
- Script restarted successfully at 20:59

**Why This Plan:**
- Logical progression: Fix infrastructure → Optimize performance → Build features
- Data-driven decisions: Analysis before threshold changes
- Flexible: Phase 3 choice depends on Phase 2 results

**Timeline:**
- Tonight: Let backfill run (no action needed)
- Tomorrow AM: Analyze results, tune threshold
- Tomorrow PM - Next Week: Execute chosen feature

---

**Created:** November 15, 2025 21:05
**Updated:** November 15, 2025 21:05
**Next Update:** After Phase 1 completes (~morning of Nov 16)
