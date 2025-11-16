# Detection Model Retraining Plan

**Date:** November 16, 2025
**Current Model:** YOLOv8n (11 classes)
**Goal:** Fix classification issues identified during manual audit

---

## Critical Issues to Address

### 1. Buck Over-Classification Bias (HIGH PRIORITY)

**Problem:**
- At 50-52% confidence: 80-85% of "buck" classifications are WRONG
- Nearly all incorrect "bucks" are actually does
- Strong model bias toward classifying uncertain deer as bucks
- Suggests training data imbalance or threshold tuning needed

**Root Cause Theories:**
- Training dataset has more buck examples than doe examples
- Buck features (antlers) are over-weighted in model
- Does without clear head visibility default to "buck"
- Model may be picking up seasonal patterns (rut season = more bucks)

**Solutions:**
1. **Rebalance training data:**
   - Add more doe examples (especially head-on, grazing poses)
   - Include does from multiple seasons
   - Add does at different distances/angles

2. **Adjust classification thresholds:**
   - Require higher confidence for "buck" classification
   - Add "uncertain_deer" class for ambiguous cases
   - Implement ensemble voting (multiple model agreement)

3. **Feature engineering:**
   - Add explicit "no antlers visible" detection
   - Train on head/ear profile separately
   - Use temporal consistency (same deer across frames)

---

### 2. Cattle Recognition (MEDIUM PRIORITY)

**Problem:**
- Model has "cattle" class but performance unknown
- User has cattle on property (seen in Image 106: HAYFIELD_00559.jpg)
- Need to ensure cattle are NOT misclassified as deer

**Observations:**
- Batch 6, Image 106 had both deer and cattle at feeder
- Cattle are larger, different body shape
- Important for population counts

**Solutions:**
1. **Verify cattle detection accuracy:**
   - Sample images with known cattle
   - Check if cattle are being classified correctly
   - Measure false positive rate (cattle as deer)

2. **Training data:**
   - Ensure sufficient cattle examples in training set
   - Include cattle at feeders (common scenario)
   - Various breeds, colors, sizes

3. **Size/shape features:**
   - Cattle are larger than deer
   - Different body proportions
   - Distinct head shape

---

### 3. Feral Pig Recognition (MEDIUM PRIORITY)

**Problem:**
- Model has pig-related classes but need verification
- Pigs are invasive species - important to track
- Different behavior patterns than deer

**Current Classes:**
- "pig" in classification list
- May also have "sow", "boar" variants

**Solutions:**
1. **Verify pig detection:**
   - Sample images with known pigs
   - Check classification accuracy
   - Ensure pigs not confused with deer (especially fawns)

2. **Training data:**
   - Include feral pigs (not domestic pigs)
   - Various sizes/ages
   - Different lighting conditions

3. **Distinguishing features:**
   - Pigs have distinctive snouts
   - Different body shape (lower, rounder)
   - Different movement patterns

---

## Training Data Requirements

### Current Dataset
- 59,185 images processed
- ~40,000+ detections
- Multiple camera locations
- Various times of day (IR, daylight, dusk)

### Additional Data Needed

**Does (HIGH PRIORITY):**
- Target: 2,000-3,000 additional doe examples
- Focus on:
  - Head-on views
  - Grazing poses (head down)
  - Multiple does together
  - Various distances
  - All lighting conditions

**Bucks (MEDIUM PRIORITY):**
- May need to REDUCE buck weight in training
- Or require higher confidence threshold
- Ensure antler visibility in examples

**Cattle (MEDIUM PRIORITY):**
- Target: 500-1,000 cattle examples
- Texas ranch cattle (breeds present)
- At feeders
- Mixed with deer

**Feral Pigs (MEDIUM PRIORITY):**
- Target: 500-1,000 pig examples
- Feral pigs specifically
- Various sizes
- Day and night

---

## Model Architecture Considerations

### Current: YOLOv8n
- Fast, lightweight
- Good for real-time processing
- 11 classes

### Alternatives to Consider

**YOLOv8m/l:**
- Larger model
- Better accuracy
- Slower inference
- May not fit in RTX 4080 Super for batch processing

**Ensemble Approach:**
- Separate models for:
  - Species classification (deer vs cattle vs pig)
  - Sex classification (buck vs doe vs fawn)
  - Confidence calibration
- Combine predictions

**Two-Stage Detection:**
1. Stage 1: Detect "animal"
2. Stage 2: Classify species + sex
- More accurate but slower

---

## Validation Strategy

### Test Set Requirements
- Hold out 20% of data for testing
- Stratified by:
  - Species (deer, cattle, pig)
  - Sex (buck, doe, fawn)
  - Confidence level (high, medium, low)
  - Time of day (day, dusk, night IR)
  - Camera location

### Metrics to Track
1. **Overall Accuracy:** % correct classifications
2. **Per-Class Accuracy:**
   - Buck accuracy
   - Doe accuracy
   - Fawn accuracy
   - Cattle accuracy
   - Pig accuracy

3. **Confidence Calibration:**
   - At 50-60% confidence: should be 50-60% accurate
   - At 70-80% confidence: should be 70-80% accurate
   - At 90%+ confidence: should be 90%+ accurate

4. **Confusion Matrix:**
   - Most common misclassifications
   - Buck/doe confusion rate
   - Deer/cattle confusion rate
   - Deer/pig confusion rate

---

## Implementation Timeline

### Phase 1: Data Collection (1-2 weeks)
- [ ] Extract manually audited images as ground truth
- [ ] Identify additional doe examples from dataset
- [ ] Collect cattle images from camera traps
- [ ] Collect feral pig images

### Phase 2: Data Preparation (3-5 days)
- [ ] Create new training/validation split
- [ ] Augment doe examples (flip, rotate, brightness)
- [ ] Balance class distributions
- [ ] Annotate any unlabeled data

### Phase 3: Training (1-2 days)
- [ ] Train YOLOv8n with balanced dataset
- [ ] Train YOLOv8m for comparison
- [ ] Experiment with confidence thresholds
- [ ] Cross-validate performance

### Phase 4: Validation (2-3 days)
- [ ] Test on held-out test set
- [ ] Measure calibration curves
- [ ] Compare to current model
- [ ] A/B test with manual audit samples

### Phase 5: Deployment (1 day)
- [ ] Replace model weights
- [ ] Update confidence thresholds
- [ ] Restart worker
- [ ] Monitor first 1,000 images

---

## Success Criteria

### Minimum Requirements
- [ ] Buck classification at 50-60% confidence: >70% accurate (vs current 15-20%)
- [ ] Doe classification at 50-60% confidence: >80% accurate (vs current ~75%)
- [ ] Overall accuracy at low confidence: >75% (vs current ~40%)
- [ ] Cattle false positive rate: <5%
- [ ] Pig false positive rate: <5%

### Stretch Goals
- [ ] Buck/doe accuracy at 70%+ confidence: >95%
- [ ] Cattle detection: >90% accuracy
- [ ] Pig detection: >90% accuracy
- [ ] Calibrated confidence scores (50% = 50% accurate, 90% = 90% accurate)

---

## Notes from Manual Audit

### Patterns Observed

**Buck Misclassifications:**
- Most common: does at feeders misclassified as bucks
- Often multiple deer in scene (all does)
- Head-down grazing poses
- Dusk/dawn lighting
- No antlers visible but classified as buck

**Doe Correct Classifications:**
- Clear head visibility
- Multiple does together
- Daylight conditions
- Sanctuary2 camera location (good lighting)

**Uncertain Cases:**
- Night IR images (too grainy)
- Distant deer (small in frame)
- Fog/mist conditions
- Deer partially obscured

---

**Last Updated:** November 16, 2025
**Status:** Planning - awaiting manual audit completion
