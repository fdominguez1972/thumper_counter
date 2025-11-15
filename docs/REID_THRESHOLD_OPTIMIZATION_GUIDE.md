# REID Threshold Optimization Guide

## Overview

The REID_THRESHOLD controls how similar two deer images must be to match as the same individual. This guide explains how to find the optimal threshold for your dataset.

## Problem Statement

**Current State (Nov 15, 2025):**
- 206 deer profiles (4x too many)
- Target: 30-50 profiles for practical naming
- REID_THRESHOLD: 0.60 (too conservative)
- Creating 17 new profiles per 1,000 images (should be ~0.1-1)

**Root Cause:**
- Higher threshold = more conservative = creates new profile more easily
- 0.60 threshold means deer need to be 60% similar to match
- Too many "new" deer are created instead of matching existing ones

## How the Threshold Works

### Similarity Score Range: 0.0 to 1.0

```
0.0 - Completely different deer
0.5 - Moderately similar
0.7 - Very similar (likely same deer)
0.9 - Nearly identical
1.0 - Exact match
```

### Threshold Behavior

**REID_THRESHOLD = 0.70 (very conservative)**
- Only matches if similarity >= 0.70
- Creates many new profiles
- Few false matches
- Good for: Initial data collection, unknown population

**REID_THRESHOLD = 0.60 (conservative - CURRENT)**
- Only matches if similarity >= 0.60
- Creates too many new profiles
- Very few false matches
- Status: TOO CONSERVATIVE for our dataset

**REID_THRESHOLD = 0.50 (moderate - RECOMMENDED)**
- Matches if similarity >= 0.50
- Balances new profiles vs matches
- Some false matches possible
- Good for: Mature datasets, known population

**REID_THRESHOLD = 0.40 (aggressive)**
- Matches if similarity >= 0.40
- Few new profiles created
- Higher false match rate
- Risk: Different deer matched as same

## Optimization Process

### Step 1: Analyze Current State

```bash
# Run analysis script
docker-compose exec backend python3 /app/scripts/analyze_reid_threshold.py
```

**What to Look For:**
- Total deer profiles
- Profiles with <5 sightings (likely false positives)
- Profile creation rate (profiles per 1,000 images)
- Assignment rate (detections assigned to deer)

**Example Output:**
```
Total Deer Profiles: 206
Profiles with <=1 sighting: 45 profiles
Profiles with <=5 sightings: 103 profiles
Profile Creation Rate: 17.0 profiles per 1,000 images
Expected Rate (mature): 0.1 profiles per 1,000 images
```

**Interpretation:**
- 103 profiles with <=5 sightings = likely duplicates
- 17x higher than expected = threshold too conservative
- Recommendation: Lower threshold to 0.50

### Step 2: Test New Threshold on Subset

**Why Test First?**
- Full reprocess takes ~15 hours (59,000 images)
- Testing 1,000 images takes ~10 minutes
- Allows iteration to find optimal threshold

**Run Test:**
```bash
# Interactive workflow
bash scripts/optimize_reid_threshold.sh
```

**What Happens:**
1. Script analyzes current state
2. Recommends new threshold (e.g., 0.50)
3. Updates .env: REID_THRESHOLD=0.50
4. Restarts worker container
5. Resets 1,000 random images to pending
6. Queues them for reprocessing
7. Monitors deer profile count during processing

**Expected Test Results:**

Good Threshold (0.50):
```
Deer profiles before: 206
Deer profiles after:  208
New profiles created: 2

[EXCELLENT] Low profile creation rate - threshold is working well!
RECOMMENDATION: Proceed with full reprocess using threshold 0.50
```

Still Too Conservative (0.55):
```
Deer profiles before: 206
Deer profiles after:  218
New profiles created: 12

[WARNING] Profile creation rate still high
RECOMMENDATION: Try lower threshold: 0.50
```

Too Aggressive (0.40):
```
Deer profiles before: 206
Deer profiles after:  206
New profiles created: 0

[WARNING] No new profiles created - may be over-matching
RECOMMENDATION: Try higher threshold: 0.45
```

### Step 3: Full Reprocess (if test successful)

**When test shows <3 new profiles per 1,000 images:**
```bash
# Full reprocess with new threshold
bash scripts/reprocess_all_images.sh
```

**What This Does:**
```sql
-- 1. Delete all deer profiles
DELETE FROM deer;

-- 2. Clear deer assignments
UPDATE detections SET deer_id = NULL;

-- 3. Reset all images to pending
UPDATE images
SET processing_status = 'pending'
WHERE processing_status = 'completed';

-- 4. Queue all images for reprocessing
POST /api/processing/batch?limit=59000
```

**Processing Time:**
- 59,185 images @ 840 images/min = ~70 minutes
- Worker concurrency: 32 threads
- GPU: RTX 4080 Super (31% utilization)

**Expected Result:**
- Deer profiles: 30-50 (down from 206)
- Assignment rate: 20-40% (detections with deer_id)
- Distribution: ~65% does, ~35% bucks (matches detection data)

## Threshold Recommendations by Situation

### New Dataset (Unknown Population)
- Start with: 0.70
- Allow high profile count initially
- Lower threshold after reviewing profiles

### Mature Dataset (Known Population)
- Use: 0.45-0.55
- Targets <50 profiles for naming
- Current situation: Use 0.50

### Very Large Population (>100 unique deer)
- Use: 0.60-0.65
- Accept higher profile count
- Focus on reducing false matches

### Small Population (<20 unique deer)
- Use: 0.40-0.50
- Aggressive matching acceptable
- Manually review and merge duplicates

## Common Issues and Solutions

### Issue 1: Too Many Deer Profiles
**Symptoms:**
- Profile count >> expected
- Many profiles with <5 sightings
- Profile creation rate >5 per 1,000 images

**Solution:**
- Lower REID_THRESHOLD by 0.05-0.10
- Test on subset
- Full reprocess if test successful

### Issue 2: Suspected False Matches
**Symptoms:**
- Profile count << expected
- Profiles with mixed buck/doe in images
- Very high sighting counts (>1000)

**Solution:**
- Raise REID_THRESHOLD by 0.05
- Review burst detection logic
- Check for classification cross-contamination

### Issue 3: Inconsistent Results
**Symptoms:**
- Profile count varies wildly between runs
- Similarity scores cluster near threshold
- High variance in sighting counts

**Solution:**
- Check model ensemble consistency
- Verify image quality (focus, lighting)
- Consider adding burst detection window

## Monitoring and Validation

### Key Metrics to Track

**During Processing:**
```bash
# Check processing status
curl -s http://localhost:8001/api/processing/status | python3 -m json.tool

# Monitor deer count
watch -n 10 'docker-compose exec -T db psql -U deertrack deer_tracking -c "SELECT COUNT(*) FROM deer;"'
```

**After Reprocess:**
```bash
# Deer profile summary
docker-compose exec db psql -U deertrack deer_tracking -c "
  SELECT sex, COUNT(*) as profiles, SUM(sighting_count) as sightings
  FROM deer
  GROUP BY sex;
"

# Low sighting profiles
docker-compose exec db psql -U deertrack deer_tracking -c "
  SELECT COUNT(*) FROM deer WHERE sighting_count <= 5;
"

# Assignment rate
docker-compose exec db psql -U deertrack deer_tracking -c "
  SELECT
    COUNT(*) as total_detections,
    COUNT(deer_id) as assigned,
    CAST(COUNT(deer_id) * 100.0 / COUNT(*) AS DECIMAL(5,1)) as assignment_rate
  FROM detections;
"
```

### Success Criteria

**Excellent Results:**
- [OK] Deer profiles: 30-50
- [OK] Profiles with <=5 sightings: <20%
- [OK] Assignment rate: >20%
- [OK] Sex distribution matches detection data (65/35)

**Good Results:**
- [OK] Deer profiles: 50-100
- [OK] Profiles with <=5 sightings: <30%
- [OK] Assignment rate: >15%
- [OK] No obvious duplicates in manual review

**Needs Adjustment:**
- [WARN] Deer profiles: >100 or <20
- [WARN] Profiles with <=5 sightings: >40%
- [WARN] Assignment rate: <10%
- [WARN] Obvious duplicates or false matches

## Advanced: Manual Profile Consolidation

If threshold optimization doesn't achieve target, manual consolidation:

```sql
-- Find likely duplicates (same sex, overlapping time, similar sighting patterns)
SELECT
    d1.id as deer1_id,
    d1.sex as sex1,
    d1.sighting_count as sightings1,
    d2.id as deer2_id,
    d2.sex as sex2,
    d2.sighting_count as sightings2,
    ABS(EXTRACT(EPOCH FROM (d1.first_seen - d2.first_seen))) as time_diff_seconds
FROM deer d1
JOIN deer d2 ON d1.sex = d2.sex AND d1.id < d2.id
WHERE d1.sighting_count <= 10 OR d2.sighting_count <= 10
    AND ABS(EXTRACT(EPOCH FROM (d1.first_seen - d2.first_seen))) < 86400  -- within 24 hours
ORDER BY time_diff_seconds ASC
LIMIT 50;

-- Merge deer profiles (reassign detections from deer2 to deer1)
UPDATE detections
SET deer_id = :deer1_id
WHERE deer_id = :deer2_id;

-- Delete merged deer
DELETE FROM deer WHERE id = :deer2_id;

-- Update sighting count
UPDATE deer
SET sighting_count = (SELECT COUNT(*) FROM detections WHERE deer_id = :deer1_id)
WHERE id = :deer1_id;
```

## Files Reference

**Analysis:**
- `scripts/analyze_reid_threshold.py` - Comprehensive analysis script
- `scripts/optimize_reid_threshold.sh` - Interactive workflow

**Reprocessing:**
- `scripts/reprocess_all_images.sh` - Full dataset reprocess
- `scripts/reset_reid_with_new_threshold.py` - Database reset

**Configuration:**
- `.env` - REID_THRESHOLD setting
- `src/worker/tasks/reidentification.py` - Re-ID logic

**Documentation:**
- `docs/REID_THRESHOLD_OPTIMIZATION_GUIDE.md` - This guide
- `docs/SESSION_20251115_FINAL_STATUS.md` - Current state analysis

## Quick Reference

```bash
# 1. Analyze current state
docker-compose exec backend python3 /app/scripts/analyze_reid_threshold.py

# 2. Run interactive optimization
bash scripts/optimize_reid_threshold.sh

# 3. Full reprocess (after successful test)
bash scripts/reprocess_all_images.sh

# 4. Monitor progress
curl -s http://localhost:8001/api/processing/status | python3 -m json.tool

# 5. Check results
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT sex, COUNT(*) FROM deer GROUP BY sex;"
```

## Timeline

**Expected Duration:**
- Analysis: 1 minute
- Test (1,000 images): 10 minutes
- Full reprocess decision: 5 minutes
- Full reprocess (59,000 images): 70 minutes
- **Total: ~90 minutes to optimal threshold**

## Next Steps

1. Wait for containers to finish building
2. Run: `bash scripts/optimize_reid_threshold.sh`
3. Follow interactive prompts
4. Review test results
5. Proceed with full reprocess if test successful
6. Assign Disney names to <50 deer profiles

**Ready to begin optimization once containers are online!**
