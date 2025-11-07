# Burst Deduplication Design
**Created:** 2025-11-07
**Issue:** Trail camera photo bursts create duplicate deer profiles
**Status:** Design Phase

## Problem Statement

Trail cameras take rapid bursts of photos when motion is detected. This creates two deduplication problems:

### Problem 1: Within-Image Duplicates
**Observation:** Single images contain 5-10 detections of the same deer
**Example:** 270_JASON_01226.jpg has 10 detections
**Root Cause:** YOLOv8 multi-class model detects same deer with slight bbox variations

### Problem 2: Cross-Image Burst Duplicates
**Observation:** Sequential photos within seconds create separate deer profiles
**Example:** Images _01213, _01214, _01215 taken at 04:14:45 (same timestamp)
**Root Cause:** Re-ID treats each detection independently, ignoring temporal/spatial context

### Impact on Data Quality
- **Current:** 714 deer profiles from 31,092 detections (1 deer per 43.5 detections)
- **Expected:** Likely only 50-100 unique deer at Hopkins Ranch
- **Problem:** ~90% false unique deer profiles from burst photos

## Solution Design

### Two-Stage Deduplication Approach

#### Stage 1: Within-Image Deduplication
**Goal:** Keep only the best detection when multiple detections overlap in same image

**Algorithm:**
1. Group detections by image_id
2. For each image with multiple detections:
   - Calculate IoU (Intersection over Union) between all bbox pairs
   - If IoU > 0.5 (significant overlap):
     - Keep detection with highest confidence
     - Mark others as duplicate (don't process re-ID)

**Implementation Location:** Detection task (src/worker/tasks/detection.py)
**Database Change:** Add `is_duplicate` boolean field to Detection model

**Pseudocode:**
```python
def deduplicate_within_image(detections: List[Detection]) -> List[Detection]:
    # Sort by confidence descending
    sorted_dets = sorted(detections, key=lambda d: d.confidence, reverse=True)

    keepers = []
    for det in sorted_dets:
        # Check if overlaps with any keeper
        overlaps = False
        for keeper in keepers:
            iou = calculate_iou(det.bbox, keeper.bbox)
            if iou > 0.5:  # Significant overlap
                overlaps = True
                det.is_duplicate = True
                break

        if not overlaps:
            keepers.append(det)
            det.is_duplicate = False

    return sorted_dets  # Return all, but marked
```

#### Stage 2: Cross-Image Burst Grouping
**Goal:** Treat sequential photos from same camera as single sighting event

**Grouping Criteria:**
1. **Location Match:** Same location_id (same camera)
2. **Temporal Proximity:**
   - Option A: Within N seconds (e.g., 60 seconds)
   - Option B: Sequential filename numbers (e.g., _00123, _00124, _00125)
3. **Visual Similarity:** Feature vector cosine similarity > threshold

**Algorithm:**
```python
def group_burst_detections(detection_id: str) -> List[str]:
    """
    Find all detections that belong to same burst as this detection.

    Returns list of detection IDs in the same burst (including self).
    """
    # Get detection and its image
    detection = get_detection(detection_id)
    image = detection.image

    # Define burst window
    BURST_WINDOW_SECONDS = 60
    time_start = image.timestamp - timedelta(seconds=BURST_WINDOW_SECONDS)
    time_end = image.timestamp + timedelta(seconds=BURST_WINDOW_SECONDS)

    # Find candidate burst images from same location + time window
    burst_images = query(Image).filter(
        Image.location_id == image.location_id,
        Image.timestamp >= time_start,
        Image.timestamp <= time_end,
        Image.processing_status == 'completed'
    ).all()

    # Get all non-duplicate detections from burst images
    burst_detections = []
    for img in burst_images:
        for det in img.detections:
            if not det.is_duplicate and det.classification == detection.classification:
                burst_detections.append(det)

    return burst_detections
```

**Re-ID Modification:**
```python
def reidentify_burst_aware(detection_id: str) -> Dict:
    """
    Re-identify deer considering photo burst context.
    """
    # Get all detections in this burst
    burst_detections = group_burst_detections(detection_id)

    # If any detection in burst already has deer_id, use that
    for det in burst_detections:
        if det.deer_id is not None:
            logger.info(f"[BURST] Using existing deer_id from burst: {det.deer_id}")
            return {"deer_id": det.deer_id, "match_type": "burst_linked"}

    # Otherwise, extract features and search normally
    # But link ALL burst detections to the same deer_id
    feature_vector = extract_features(detection_id)
    deer, similarity = find_matching_deer(feature_vector)

    if deer:
        deer_id = deer.id
    else:
        deer_id = create_new_deer_profile(feature_vector)

    # Link all burst detections to same deer
    for det in burst_detections:
        det.deer_id = deer_id
    db.commit()

    return {"deer_id": deer_id, "match_type": "burst_grouped"}
```

## Implementation Plan

### Phase 1: Within-Image Deduplication (2-3 hours)
1. Add `is_duplicate` boolean field to Detection model
2. Create database migration
3. Implement IoU calculation function
4. Update detection task to mark duplicates
5. Test on sample images with multiple detections

### Phase 2: Burst Grouping (3-4 hours)
1. Implement `group_burst_detections()` function
2. Update `reidentify_deer_task()` to use burst grouping
3. Add burst metadata to response (burst_size, burst_start, burst_end)
4. Test on sequential photo sets

### Phase 3: Validation & Metrics (1-2 hours)
1. Run on test dataset (500 images)
2. Calculate metrics:
   - Detections marked as duplicates (%)
   - Average burst size
   - Deer profiles before/after deduplication
3. Manual verification of 50 random bursts
4. Adjust thresholds if needed

## Configuration Parameters

```python
# Detection deduplication
IOU_THRESHOLD = 0.5  # Overlap threshold for within-image duplicates

# Burst grouping
BURST_WINDOW_SECONDS = 60  # Max time gap for burst
MIN_BURST_SIZE = 2  # Minimum photos to consider a burst
MAX_BURST_SIZE = 50  # Maximum photos in single burst (safety limit)

# Re-ID with burst context
BURST_REID_ENABLED = True  # Enable burst-aware re-ID
```

## Database Schema Changes

### Detection Model
```python
class Detection(Base):
    __tablename__ = 'detections'

    # Existing fields...
    deer_id = Column(UUID(as_uuid=True), ForeignKey('deer.id'), nullable=True)

    # NEW FIELDS
    is_duplicate = Column(Boolean, default=False, nullable=False)
    burst_group_id = Column(UUID(as_uuid=True), nullable=True)  # Optional: track burst membership
```

### Migration SQL
```sql
ALTER TABLE detections
ADD COLUMN is_duplicate BOOLEAN DEFAULT FALSE NOT NULL,
ADD COLUMN burst_group_id UUID;

CREATE INDEX idx_detections_is_duplicate ON detections(is_duplicate);
CREATE INDEX idx_detections_burst_group ON detections(burst_group_id);
```

## Expected Results

### Before Deduplication
- Deer profiles: 714
- Detections: 31,092
- Avg detections/deer: 43.5
- Issue: Massive over-counting

### After Deduplication (Projected)
- Deer profiles: 80-120 (estimated unique deer)
- Unique detections: ~3,000-5,000 (non-duplicates)
- Duplicate detections: ~26,000-28,000 (marked)
- Avg detections/deer: 25-40
- Burst size: 5-10 photos average

## Alternative Approaches Considered

### Option 1: Filename Sequence Numbers
**Pros:** Deterministic, no threshold tuning
**Cons:** Assumes sequential numbering is reliable
**Decision:** Use as secondary signal, not primary

### Option 2: Visual Clustering (DBSCAN)
**Pros:** No fixed time window, handles variable bursts
**Cons:** Computationally expensive, complex to tune
**Decision:** Future enhancement if needed

### Option 3: Post-Processing Merge
**Pros:** Non-destructive, can revert
**Cons:** Leaves duplicate data in DB
**Decision:** Not chosen, prefer clean data

## Testing Strategy

### Unit Tests
- `test_calculate_iou()` - Bbox overlap calculation
- `test_deduplicate_within_image()` - Single image dedup
- `test_group_burst_detections()` - Burst grouping logic

### Integration Tests
- Process 100 images with known bursts
- Verify detection counts match expectations
- Verify deer profiles are correctly linked

### Manual Validation
- Select 50 random bursts
- Visual inspection of deer continuity
- Confirm same deer across burst photos

## Performance Impact

### Detection Task
- **Current:** 0.04s per image
- **With Dedup:** +0.01s per image (IoU calculations)
- **Impact:** <25% slowdown, acceptable

### Re-ID Task
- **Current:** 2s per detection
- **With Burst Grouping:** +0.1s per detection (burst query)
- **But:** Skip ~80% of detections (duplicates)
- **Net Impact:** 5x faster overall (process 1 per burst vs all)

## Rollout Plan

1. **Development:** Implement on feature branch (2-3 days)
2. **Testing:** Validate on 1,000 image subset (1 day)
3. **Dry Run:** Mark duplicates without skipping re-ID (verify accuracy)
4. **Production:** Enable full deduplication
5. **Backfill:** Re-process existing 11,222 images with new logic

## Success Metrics

- [ ] Detections marked duplicate: 70-85%
- [ ] Deer profiles reduced to <200
- [ ] Manual validation: >95% accuracy on burst grouping
- [ ] Processing throughput: 5x improvement
- [ ] Frontend gallery shows distinct deer, not duplicates

## Open Questions

1. **Burst window duration:** 60 seconds vs 120 seconds vs filename-based?
2. **Cross-species bursts:** If doe and buck in same burst, how to handle?
3. **Retroactive processing:** Re-run re-ID on all 11k images or just new ones?
4. **UI indication:** Should frontend show burst size or hide duplicates entirely?

## References
- IoU calculation: https://en.wikipedia.org/wiki/Jaccard_index
- DBSCAN clustering: https://scikit-learn.org/stable/modules/generated/sklearn.cluster.DBSCAN.html
- Trail camera behavior: Typically 3-10 photo bursts with 1-3 second intervals
