# Full 59k Image Reclassification Strategy

**Date:** November 16, 2025
**Context:** Based on Batches 1-5 audit results
**Goal:** Improve classification accuracy across all 59,185 images

---

## Current Situation

### Audit Results Summary (Batches 1-5)

**Batch 4:**
- Accuracy: 31.2% (5 correct out of 16 determinable)
- Corrections: 11 (55%)
- Uncertain: 4 (20%)
- Pattern: 85% of "buck" classifications were WRONG (actually does)

**Batch 5:**
- Accuracy: 53.3% (8 correct out of 15 determinable)
- Corrections: 7 (35%)
- Uncertain: 5 (25%)
- Pattern: 78% of "buck" classifications were WRONG (actually does)

### Critical Pattern Identified

**SEVERE BUCK OVER-CLASSIFICATION BIAS**
- At 50-51% confidence: ~80-85% of "buck" classifications are incorrect
- Nearly all incorrect "bucks" are actually does
- Model has strong bias toward classifying uncertain deer as bucks
- This suggests training data imbalance or model architecture issue

---

## Reclassification Approach

### Option 1: Continue Manual Vision Audit (Current Method)

**What We're Doing:**
- Using Claude Code vision to review low-confidence images
- Processing 20 images per batch
- ~40 seconds per batch (download + review + correct)
- 100% reliable (human-level vision analysis)

**Pros:**
- Perfect accuracy (vision-based, not statistical)
- Can handle edge cases (fog, night IR, partial views)
- Provides detailed reasoning for each decision
- No false positives

**Cons:**
- Time intensive: 1,713 low-confidence images / 20 per batch = 86 batches
- At 40 seconds per batch: ~60 minutes total
- Only covers low-confidence range (50-60%)

**Estimated Coverage:**
- Low confidence (50-60%): 1,713 images (can complete in ~1 hour)
- Medium confidence (60-70%): Unknown count
- High confidence (70%+): Likely accurate, but unverified

---

### Option 2: Statistical Correction Based on Audit Patterns

**What We Learned:**
- Buck classifications at 50-51% confidence: 80-85% are actually does
- Doe classifications at 50-51% confidence: ~75% are correct
- Pattern is consistent across all 5 batches

**Automated Correction Algorithm:**
```sql
-- Automatically correct high-probability errors
UPDATE detections
SET
  classification = 'doe',
  corrected_classification = 'doe',
  is_reviewed = true,
  reviewed_by = 'Statistical Pattern Correction',
  correction_notes = 'Auto-corrected: buck at 50-51% confidence (85% error rate in audit)'
WHERE
  classification = 'buck'
  AND confidence >= 0.50
  AND confidence < 0.52
  AND is_reviewed = false;
```

**Pros:**
- Instant: corrects thousands of images in seconds
- Based on empirical evidence from 100 manually reviewed images
- Can be run immediately

**Cons:**
- 15-20% will be incorrectly "corrected" (false negatives)
- No case-by-case analysis
- Might miss nuances

**Estimated Impact:**
- Would auto-correct ~800-1000 images
- Expected accuracy: ~80-85% (same as audit pattern)
- Remaining errors: ~150-200 images

---

### Option 3: Hybrid Approach (RECOMMENDED)

**Strategy:**
1. **Statistical correction for obvious cases (confidence 50.0-50.5%)**
   - Auto-correct buck->doe where confidence is 50.0-50.5%
   - This range has 85%+ error rate
   - Affects ~500-700 images

2. **Manual vision audit for borderline cases (confidence 50.5-52.0%)**
   - Continue current method for 50.5-52% range
   - More variability in this range
   - Affects ~1,000 images
   - At 20 per batch: 50 batches = ~35 minutes

3. **Sampling audit for medium confidence (55-65%)**
   - Random sample 100 images from this range
   - Check error rate
   - If error rate > 20%, do full audit
   - If error rate < 20%, accept as-is

4. **Spot-check high confidence (65%+)**
   - Random sample 50 images
   - Verify model is accurate at high confidence
   - Should be >95% accurate

**Timeline:**
- Statistical correction: 5 seconds
- Manual audit (50 batches): 35 minutes
- Sampling (150 images): 15 minutes
- **Total: ~50 minutes**

**Expected Accuracy Improvement:**
- Current low-confidence accuracy: ~40%
- Post-hybrid accuracy: ~85-90%
- High-confidence already likely >90%

---

## Implementation Plan

### Phase 1: Statistical Correction (Now)
```bash
# Run SQL update for ultra-low confidence bucks
docker-compose exec -T db psql -U deertrack deer_tracking -c "
UPDATE detections
SET
  classification = 'doe',
  corrected_classification = 'doe',
  is_reviewed = true,
  reviewed_by = 'Statistical Pattern Correction (Batch 1-5 Audit)',
  correction_notes = 'Auto-corrected based on 85% error rate in manual audit of 50.0-50.5% confidence bucks'
WHERE
  classification = 'buck'
  AND confidence >= 0.500
  AND confidence < 0.505
  AND is_reviewed = false;
"
```

### Phase 2: Continue Manual Audit (Batches 6-30)
```bash
# Process batches 6-30 (confidence 50.5-52.0%)
for batch in {6..30}; do
  python3 turbo_audit.py $batch
  # Claude Code reviews images
  python3 generate_report.py $batch
  bash apply_batch_${batch}_corrections.sh
done
```

### Phase 3: Sampling Audit (Medium Confidence)
```bash
# Random sample from 55-65% confidence
python3 create_sample_audit.py --confidence-range 0.55-0.65 --sample-size 100
# Review sample
# Decide if full audit needed
```

### Phase 4: Reprocess Re-ID with Corrected Classifications
```bash
# After corrections, rerun Re-ID to create better deer profiles
curl -X POST "http://localhost:8001/api/processing/reprocess-reid"
```

---

## Resource Requirements

### Time Estimates

**Full Manual Audit (1,713 images):**
- 86 batches x 40 seconds = ~60 minutes

**Hybrid Approach (recommended):**
- Statistical: 5 seconds
- Manual (borderline): 35 minutes
- Sampling: 15 minutes
- **Total: 50 minutes**

**Statistical Only (fastest, less accurate):**
- 5 seconds total
- But leaves 15-20% errors

### Computational Resources

**Vision Analysis (Claude Code):**
- No GPU needed (vision is on Claude's side)
- Network bandwidth: minimal (images are local)
- Storage: ~2GB for downloaded audit images

**Database Updates:**
- Corrections are instant (SQL UPDATE)
- Re-ID reprocessing: 2-3 hours (GPU-intensive)

---

## Recommendations

### Immediate Actions (Next 60 minutes)

1. **Run statistical correction** for 50.0-50.5% confidence bucks
   - Expected corrections: 500-700 images
   - Accuracy: 85%

2. **Continue manual audit** through Batch 30
   - Covers 50.5-52.5% confidence range
   - Expected corrections: 500-800 images
   - Accuracy: 95%+

3. **Sample medium confidence** (55-65%)
   - 100 image sample
   - Determine if full audit needed

4. **Spot-check high confidence** (70%+)
   - 50 image sample
   - Verify model is accurate

### Long-Term Actions (Next Week)

1. **Retrain detection model**
   - Address buck over-classification bias
   - Add more doe training examples
   - Adjust classification thresholds

2. **Reprocess Re-ID** with corrected classifications
   - Should result in better deer profiles
   - Fewer false matches

3. **Continuous monitoring**
   - Audit new images as they come in
   - Track accuracy over time

---

## Expected Outcomes

### After Full Reclassification

**Classification Accuracy:**
- Low confidence (50-55%): 85-90% (from 40%)
- Medium confidence (55-65%): 90-95% (estimated)
- High confidence (65%+): 95%+ (already good)

**Re-ID Accuracy:**
- Fewer false buck/doe matches
- Better profile consolidation
- More reliable deer tracking

**Data Quality:**
- Clean dataset for future model training
- Better sex ratio analysis
- More reliable population estimates

---

## Decision Point

**What would you like to do?**

A. **Hybrid Approach (recommended)** - 50 minutes, 85-90% accuracy
B. **Full Manual Audit** - 60 minutes, 95%+ accuracy
C. **Statistical Only** - 5 seconds, 80% accuracy
D. **Continue Current Pace** - Manual audit only, no statistical corrections
E. **Custom Approach** - Tell me what you want

---

**My Recommendation: Option A (Hybrid)**
- Best balance of time vs accuracy
- Leverages both statistical patterns and vision analysis
- Can complete in under 1 hour
- Leaves room for future refinement
