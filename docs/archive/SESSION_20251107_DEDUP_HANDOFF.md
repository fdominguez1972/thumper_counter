# Session Handoff: Timestamp Correction & Deduplication Design
**Date:** 2025-11-07
**Duration:** ~4 hours
**Branch:** main
**Status:** Database updated, deduplication fields added, implementation in progress

## Executive Summary

Discovered and fixed critical timestamp issue where database contained fake "burst" timestamps from file copy operation instead of real camera timestamps. Extracted true timestamps from 29,939 original filenames and updated database. Analyzed real camera behavior and designed deduplication strategy. Added database fields for deduplication but implementation of dedup logic is incomplete.

## Work Completed

### 1. Timestamp Correction (COMPLETE)
- **Problem Found:** Database timestamps were from Jan 27, 2024 file copy operation, not camera
- **Solution:** Parsed original filenames (format: `YYYY_MM_DD_HH_MM_SS_LOCATION_CAMERA.JPG`)
- **Generated:** CSV mapping 29,939 files to correct timestamps
- **Updated:** All database Image.timestamp values with real camera times
- **Result:** Timestamps now range from 2022-2025 (real camera dates)

**Key Files:**
- `/mnt/i/projects/thumper_counter/data/timestamp_corrections.csv` (29,939 mappings)
- `/mnt/i/projects/thumper_counter/data/timestamp_updates.sql` (119,791 lines SQL)
- Original files: `/mnt/i/projects/thumper_counter/cifs/Hopkins_Ranch_Trail_Cam_Pics/`

### 2. Real Camera Behavior Analysis (COMPLETE)

**Discovered Patterns (After Correction):**
| Timing Pattern | Count | Percent | Description |
|----------------|-------|---------|-------------|
| 30-120 seconds | 5,639 | 50.2% | Normal camera trigger interval |
| Identical timestamp | 1,911 | 17.0% | Photos with same second (0s gap) |
| >10 minutes | 1,780 | 15.9% | New deer visit/event |
| 2-10 minutes | 1,572 | 14.0% | Longer gaps |
| 1-5 seconds | 312 | 2.8% | Rare close timing |

**Key Findings:**
- Cameras are NOT in burst mode
- No sub-second photo bursts (that was artifact of file copy)
- 50% of photos are 30-120s apart (normal trigger)
- 17% have identical timestamps (photos taken in same second)
- Original "bursts" we saw were fake from file modification times

### 3. Database Schema Updates (COMPLETE)

Added deduplication fields to Detection model:

```sql
ALTER TABLE detections
ADD COLUMN is_duplicate BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN burst_group_id UUID;

CREATE INDEX idx_detections_is_duplicate ON detections(is_duplicate);
CREATE INDEX idx_detections_burst_group ON detections(burst_group_id);
```

**Migration:** `migrations/006_add_deduplication_fields.sql` (executed successfully)

### 4. Deduplication Strategy Designed (COMPLETE)

**Problem 1: Within-Image Duplicates**
- Single images have 5-10 detections of same deer
- YOLOv8 detects same animal multiple times with slight bbox variations

**Solution:** IoU-based deduplication
```python
IOU_THRESHOLD = 0.5  # If bboxes overlap >50%, mark as duplicate
# Keep detection with highest confidence
# Mark others with is_duplicate = TRUE
```

**Problem 2: Same-Timestamp Photos**
- 1,911 photos (17%) have identical timestamps
- Photos taken within same second should be treated as single event

**Solution:** Burst grouping
```python
BURST_WINDOW = 5  # seconds
# Group photos with:
#   - Same location_id
#   - Timestamps within 5 seconds
#   - Assign same burst_group_id (UUID)
# Re-ID processes one detection per burst_group, links all to same deer_id
```

**Documentation:** `docs/BURST_DEDUPLICATION_DESIGN.md` (comprehensive design doc)

## Issues Resolved

### Issue 1: Fake Burst Timestamps
**Problem:** Database showed <1s gaps between 90% of photos
**Root Cause:** File modification times from copy operation (Jan 27, 2024)
**Solution:** Extracted true timestamps from original filenames
**Status:** [FIXED] All 29,939 images now have correct timestamps

### Issue 2: Misunderstood Camera Behavior
**Problem:** Thought cameras used burst mode (rapid-fire photos)
**Reality:** Cameras take single shots 30-120s apart
**Impact:** Changed entire deduplication strategy
**Status:** [RESOLVED] Strategy redesigned based on real data

## Work Remaining (HIGH PRIORITY)

### 1. Implement Within-Image Deduplication (2-3 hours)

**File to modify:** `src/worker/tasks/detection.py`

**After YOLOv8 detection, before saving to DB:**
```python
def deduplicate_detections(detections: List[Detection]) -> List[Detection]:
    """Mark overlapping detections as duplicates."""
    # Sort by confidence descending
    sorted_dets = sorted(detections, key=lambda d: d.confidence, reverse=True)

    for i, det in enumerate(sorted_dets):
        if det.is_duplicate:
            continue

        # Check all lower-confidence detections
        for other in sorted_dets[i+1:]:
            if det.iou(other) > 0.5:  # Significant overlap
                other.is_duplicate = True

    return sorted_dets
```

**Integration point:** After line where detections are created, before db.commit()

### 2. Implement Burst Grouping in Re-ID (3-4 hours)

**File to modify:** `src/worker/tasks/reidentification.py`

**Add before re-ID processing:**
```python
def get_burst_detections(detection_id: str, db) -> List[Detection]:
    """Find all detections in same photo burst."""
    detection = db.query(Detection).get(detection_id)
    image = detection.image

    # Find images within 5 seconds at same location
    time_start = image.timestamp - timedelta(seconds=5)
    time_end = image.timestamp + timedelta(seconds=5)

    burst_images = db.query(Image).filter(
        Image.location_id == image.location_id,
        Image.timestamp >= time_start,
        Image.timestamp <= time_end
    ).all()

    # Get all non-duplicate detections from burst
    burst_detections = []
    for img in burst_images:
        for det in img.detections:
            if not det.is_duplicate:
                burst_detections.append(det)

    return burst_detections

def reidentify_with_burst_grouping(detection_id: str) -> Dict:
    """Re-ID considering photo burst context."""
    burst_dets = get_burst_detections(detection_id, db)

    # If any detection in burst already has deer_id, reuse it
    for det in burst_dets:
        if det.deer_id:
            # Link all burst detections to same deer
            burst_group_id = uuid.uuid4()
            for d in burst_dets:
                d.deer_id = det.deer_id
                d.burst_group_id = burst_group_id
            db.commit()
            return {"deer_id": det.deer_id, "method": "burst_linked"}

    # Otherwise, run re-ID once and link all
    deer_id = run_reid_normally(detection_id)
    burst_group_id = uuid.uuid4()
    for det in burst_detections:
        det.deer_id = deer_id
        det.burst_group_id = burst_group_id
    db.commit()

    return {"deer_id": deer_id, "method": "burst_created"}
```

### 3. Reprocess Existing Detections (Optional)

31,295 existing detections need deduplication flags set:

```bash
# Mark duplicates in existing data
python3 scripts/mark_existing_duplicates.py

# Re-run re-ID with burst grouping
python3 scripts/reprocess_with_burst_grouping.py
```

**Impact:** Will reduce 714 deer profiles to ~80-120 unique deer

## Database Status

```sql
-- After timestamp correction
SELECT COUNT(*) FROM images;
-- Result: 35,251 total

SELECT COUNT(*) FROM images WHERE processing_status = 'completed';
-- Result: 11,222 processed (31.8%)

SELECT COUNT(*) FROM detections;
-- Result: 31,295 total detections

SELECT COUNT(*) FROM detections WHERE is_duplicate = TRUE;
-- Result: 0 (not yet marked - needs implementation)

SELECT COUNT(*) FROM deer;
-- Result: 714 profiles (will reduce after dedup)
```

## Git Status

**Modified Files:**
- `.gitignore` (added cifs/)
- `src/backend/models/detection.py` (added is_duplicate, burst_group_id)
- `migrations/006_add_deduplication_fields.sql` (new)
- `docs/BURST_DEDUPLICATION_DESIGN.md` (new)
- `scripts/fix_timestamps_from_originals.py` (new)
- `data/timestamp_corrections.csv` (generated)
- `data/timestamp_updates.sql` (generated)

**To Commit:**
```bash
git add -A
git commit -m "feat: Add timestamp correction and deduplication infrastructure

- Extract true timestamps from original filenames (29,939 files)
- Update database with correct camera timestamps (not file copy times)
- Add is_duplicate and burst_group_id fields to detections table
- Design deduplication strategy based on real camera behavior
- Create migration 006 for deduplication fields

Analysis shows:
- 50% of photos are 30-120s apart (normal camera trigger)
- 17% have identical timestamps (same-second photos)
- No true burst mode (fake bursts were file copy artifacts)

Next: Implement dedup logic in detection/re-ID tasks"
```

## Performance Impact (Projected)

### Current State
- Total detections: 31,295
- Deer profiles: 714
- Detections per deer: 43.8

### After Deduplication (Estimated)
- Unique detections: ~6,000-8,000 (75-80% reduction)
- Deer profiles: 80-120 (85% reduction)
- Detections per deer: 50-100 (more realistic)

### Processing Speedup
- Skip re-ID for 75-80% of detections (marked is_duplicate=TRUE)
- Process 1 detection per burst instead of all
- Expected: 4-5x faster re-ID throughput

## Next Session Priorities

1. **HIGH:** Implement within-image deduplication in detection task
2. **HIGH:** Implement burst grouping in re-ID task
3. **MEDIUM:** Test on sample data (100-200 images)
4. **MEDIUM:** Reprocess existing 31k detections with dedup logic
5. **LOW:** Validate deer profile reduction (714 → 80-120)

## Resources Created

**Documentation:**
- `docs/BURST_DEDUPLICATION_DESIGN.md` - Complete design specification
- `docs/SESSION_20251107_DEDUP_HANDOFF.md` - This document

**Data Files:**
- `data/timestamp_corrections.csv` - Mapping of renamed → original timestamps
- `data/timestamp_updates.sql` - SQL to update timestamps (119k lines)

**Scripts:**
- `scripts/fix_timestamps_from_originals.py` - Timestamp extraction (unused, superseded)
- Python inline scripts for CSV generation and SQL execution

**Database Migrations:**
- `migrations/006_add_deduplication_fields.sql` - Deduplication schema changes

## Technical Decisions Made

### Decision 1: Parse Original Filenames vs EXIF
**Context:** Need true camera timestamps
**Options:** EXIF data, filename parsing, file modification time
**Decision:** Filename parsing (EXIF not available in trail camera JPGs)
**Rationale:** Original filenames have embedded timestamps in consistent format

### Decision 2: Burst Window = 5 Seconds
**Context:** How to group photos into single event
**Options:** 5s, 30s, 60s, 120s windows
**Decision:** 5 seconds
**Rationale:** Catches 2.8% of close-timing photos, plus 17% with identical timestamps. 30-120s gaps are different deer visits based on data.

### Decision 3: IoU Threshold = 0.5
**Context:** When to mark detection as duplicate
**Options:** 0.3 (lenient), 0.5 (moderate), 0.7 (strict)
**Decision:** 0.5 (50% overlap)
**Rationale:** Standard computer vision threshold, catches significant overlaps without false positives

## Notes for AI Assistant (Claude)

- User discovered original files with timestamps in filenames
- Fake "bursts" in database were from file copy operation, not camera
- Real camera behavior: single shots 30-120s apart, no burst mode
- Deduplication strategy completely changed based on real data
- Database schema updated but implementation incomplete
- Need to mark duplicates in detection task before re-ID
- Need to group bursts in re-ID task and link to same deer

## How to Resume

```bash
cd /mnt/i/projects/thumper_counter
docker-compose ps  # Verify services running

# Check database migration applied
docker-compose exec db psql -U deertrack deer_tracking -c "\d detections"

# Review design document
cat docs/BURST_DEDUPLICATION_DESIGN.md

# Continue implementation in:
# 1. src/worker/tasks/detection.py (add deduplicate_detections function)
# 2. src/worker/tasks/reidentification.py (add burst grouping logic)
```

---

**Session End:** 2025-11-07
**Next Focus:** Implement deduplication logic in ML tasks
**Completion:** Database updated, fields added, strategy designed
**Estimated Time to Complete:** 5-7 hours
