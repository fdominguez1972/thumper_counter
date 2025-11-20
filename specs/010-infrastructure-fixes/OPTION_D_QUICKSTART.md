# Option D: Re-ID Performance Analysis - Quick Start Guide

**Feature:** 010-infrastructure-fixes, Option D
**Status:** Infrastructure complete, analysis ready
**Estimated Time:** 6-8 hours for full dataset

---

## Overview

Option D uses a **hybrid approach**:
1. **Option 3 (Ongoing Logging):** Real-time similarity score logging during normal Re-ID processing
2. **Option 2 (Backfill Analysis):** One-time re-calculation for existing detections

This guide covers running the backfill analysis and interpreting results.

---

## Quick Start (5 Minutes)

### Step 1: Verify Infrastructure
```bash
# Check similarity scores table exists
docker-compose exec -T db psql -U deertrack deer_tracking -c "\d reid_similarity_scores"

# Should show table with columns:
# - id, detection_id, deer_id, similarity_score, sex_match, matched, threshold_used, etc.
```

### Step 2: Test with Small Batch
```bash
# Dry-run mode (shows what would happen)
docker-compose exec -T backend python3 /app/scripts/backfill_similarity_scores.py --limit 10 --dry-run

# Expected output:
# [INFO] Total detections with deer_id: 4546
# [INFO] Will process: 10 detections
# [DRY-RUN] Would log 53 similarity scores for detection ...
```

### Step 3: Run Small Real Batch
```bash
# Process 100 detections (takes ~2 minutes)
docker-compose exec -T backend python3 /app/scripts/backfill_similarity_scores.py --limit 100

# Monitor progress:
# [PROGRESS] 10/100 (10.0%) | Rate: 0.7 det/s | ETA: 0.0h | Scores: 530
# [PROGRESS] 20/100 (20.0%) | Rate: 0.7 det/s | ETA: 0.0h | Scores: 1060
```

### Step 4: Query Results
```bash
# View similarity score distribution
docker-compose exec -T db psql -U deertrack deer_tracking -c "
SELECT
  ROUND(similarity_score, 1) as score_bucket,
  COUNT(*) as frequency,
  SUM(CASE WHEN matched THEN 1 ELSE 0 END) as matched_count
FROM reid_similarity_scores
GROUP BY score_bucket
ORDER BY score_bucket DESC
LIMIT 20;
"

# Expected output shows distribution like:
#  score_bucket | frequency | matched_count
# --------------+-----------+--------------
#       0.8     |       45  |          45
#       0.7     |      123  |         123
#       0.6     |      234  |           0
#       0.5     |      456  |           0
```

---

## Full Dataset Analysis (6-8 Hours)

### Option 1: Interactive Session
```bash
# Run in foreground with progress monitoring
docker-compose exec backend python3 /app/scripts/backfill_similarity_scores.py

# Watch progress in real-time:
# [PROGRESS] 500/4546 (11.0%) | Rate: 0.7 det/s | ETA: 1.6h | Scores: 26500
```

### Option 2: Background Mode (Recommended)
```bash
# Run in background, redirect output to log file
nohup docker-compose exec -T backend python3 /app/scripts/backfill_similarity_scores.py > backfill.log 2>&1 &

# Monitor progress
tail -f backfill.log

# Or check database directly
docker-compose exec -T db psql -U deertrack deer_tracking -c "
SELECT COUNT(*) as total_scores FROM reid_similarity_scores;
"
```

### Option 3: Batched Approach (Safer)
```bash
# Process in 1000-detection batches with breaks
for i in {0..4000..1000}; do
  echo "Processing batch starting at offset $i"
  docker-compose exec -T backend python3 /app/scripts/backfill_similarity_scores.py \
    --start-offset $i --limit 1000
  echo "Batch complete. Waiting 60 seconds..."
  sleep 60
done
```

---

## Analysis Queries

### Query 1: Similarity Score Distribution
```sql
-- Histogram with 0.1 bucket size
SELECT
  ROUND(similarity_score, 1) as score_bucket,
  COUNT(*) as frequency,
  SUM(CASE WHEN matched THEN 1 ELSE 0 END) as matched_count,
  ROUND(100.0 * SUM(CASE WHEN matched THEN 1 ELSE 0 END) / COUNT(*), 2) as match_rate
FROM reid_similarity_scores
GROUP BY score_bucket
ORDER BY score_bucket DESC;
```

**What to Look For:**
- Natural clustering (gaps in distribution)
- Current threshold effectiveness
- Potential false positives/negatives

### Query 2: Assignment Rate by Threshold
```sql
-- Simulate different threshold values
WITH threshold_tests AS (
  SELECT unnest(ARRAY[0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70]) as test_threshold
)
SELECT
  t.test_threshold,
  COUNT(DISTINCT s.detection_id) as total_detections,
  COUNT(DISTINCT CASE WHEN s.similarity_score >= t.test_threshold THEN s.detection_id END) as would_match,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN s.similarity_score >= t.test_threshold THEN s.detection_id END) / COUNT(DISTINCT s.detection_id), 2) as assignment_rate
FROM reid_similarity_scores s
CROSS JOIN threshold_tests t
GROUP BY t.test_threshold
ORDER BY t.test_threshold DESC;
```

**What to Look For:**
- Threshold with highest assignment rate
- Diminishing returns (small rate increase for large threshold drop)
- Sweet spot balancing assignment vs accuracy

### Query 3: Near-Miss Detections
```sql
-- Find detections that almost matched (within 0.05 of threshold)
SELECT
  detection_id,
  deer_id,
  similarity_score,
  threshold_used,
  (threshold_used - similarity_score) as score_gap,
  detection_classification,
  deer_sex
FROM reid_similarity_scores
WHERE matched = false
  AND similarity_score >= (threshold_used - 0.05)
ORDER BY similarity_score DESC
LIMIT 100;
```

**What to Look For:**
- How many "almost matches" exist
- Would lowering threshold capture these?
- Are they same-sex comparisons (sex_match=true)?

### Query 4: Performance by Sex
```sql
-- Compare matching performance across sexes
SELECT
  detection_classification,
  deer_sex,
  COUNT(*) as attempts,
  AVG(similarity_score) as avg_score,
  MAX(similarity_score) as max_score,
  SUM(CASE WHEN matched THEN 1 ELSE 0 END) as matches,
  ROUND(100.0 * SUM(CASE WHEN matched THEN 1 ELSE 0 END) / COUNT(*), 2) as match_rate
FROM reid_similarity_scores
WHERE sex_match = true
GROUP BY detection_classification, deer_sex
ORDER BY match_rate DESC;
```

**What to Look For:**
- Does Re-ID perform better for bucks or does?
- Are certain age classes easier to match?
- Sex-specific threshold adjustments needed?

---

## Interpreting Results

### Good Signs
- **Natural Clustering:** Histogram shows clear gaps (e.g., matched at 0.7+, unmatched at <0.5)
- **High Peak Near Threshold:** Many scores just below current threshold (easy wins)
- **Low False Positives:** Very few matches with scores 0.55-0.60 (if threshold is 0.55)

### Warning Signs
- **Flat Distribution:** Scores evenly spread (no clear separation)
- **Bimodal Distribution:** Two peaks (might indicate two different deer populations)
- **High Near-Miss Count:** Thousands of scores 0.50-0.54 (current threshold 0.55 too high)

### Threshold Recommendations

| Current Rate | Histogram Shape | Recommendation |
|--------------|-----------------|----------------|
| < 10% | High near-miss count | Lower threshold by 0.05-0.10 |
| 10-20% | Clustering visible | Lower threshold to cluster boundary |
| 20-40% | Clear separation | Current threshold good, monitor |
| > 40% | Very flat curve | Threshold may be too low, check false positives |

---

## Adjusting Threshold

### Step 1: Decide New Threshold
Based on analysis above, choose new value (e.g., 0.50 instead of 0.55)

### Step 2: Update Environment
```bash
# Edit .env file
# Change: REID_THRESHOLD=0.55
# To:     REID_THRESHOLD=0.50
```

### Step 3: Restart Worker
```bash
docker-compose restart worker

# Verify new threshold loaded
docker-compose logs worker | grep REID_THRESHOLD
```

### Step 4: Monitor Impact
```bash
# Query assignment rate over time
docker-compose exec -T db psql -U deertrack deer_tracking -c "
SELECT
  DATE(calculated_at) as date,
  threshold_used,
  COUNT(*) as comparisons,
  SUM(CASE WHEN matched THEN 1 ELSE 0 END) as matches,
  ROUND(100.0 * SUM(CASE WHEN matched THEN 1 ELSE 0 END) / COUNT(*), 2) as match_rate
FROM reid_similarity_scores
GROUP BY DATE(calculated_at), threshold_used
ORDER BY date DESC
LIMIT 30;
"
```

---

## Troubleshooting

### Issue: Script runs slow (< 0.5 det/sec)
**Solution:** Use GPU instead of CPU
```bash
# Ensure worker has GPU access
docker-compose exec worker nvidia-smi

# If GPU available, backfill will automatically use it
# Expected rate: 3-5 det/sec on GPU
```

### Issue: Out of memory
**Solution:** Reduce batch size
```bash
# Use smaller batches
docker-compose exec -T backend python3 /app/scripts/backfill_similarity_scores.py \
  --batch-size 50  # default is 100
```

### Issue: Database connection errors
**Solution:** Check database is running and accessible
```bash
docker-compose ps db
docker-compose logs db | tail -50
```

### Issue: Feature extraction fails
**Solution:** Check image files exist
```bash
# Verify image mount
docker-compose exec backend ls /mnt/images/ | head

# Check detection image paths
docker-compose exec -T db psql -U deertrack deer_tracking -c "
SELECT path FROM images LIMIT 5;
"
```

---

## Performance Expectations

### Small Test (100 detections)
- Time: ~2 minutes
- Scores logged: ~5,300 (53 per detection)
- Rate: 0.7 det/sec
- Use for: Quick verification

### Medium Test (1,000 detections)
- Time: ~20 minutes
- Scores logged: ~53,000
- Rate: 0.7 det/sec
- Use for: Preliminary analysis

### Full Dataset (4,546 detections with deer_id)
- Time: 6-8 hours
- Scores logged: ~240,000
- Rate: 0.7 det/sec (CPU), 3-5 det/sec (GPU)
- Use for: Complete analysis

### Storage Impact
- Database size increase: ~50-100MB for full dataset
- Disk space needed: Minimal (PostgreSQL handles efficiently)
- Index overhead: ~7 indexes, ~20MB total

---

## Next Steps After Analysis

1. **Document Findings**
   - Create analysis report with histogram
   - Document threshold decision rationale
   - Save analysis queries for future reference

2. **Adjust Threshold (if needed)**
   - Update REID_THRESHOLD in .env
   - Restart worker
   - Monitor new assignment rate

3. **Reprocess Unassigned Detections (optional)**
   - With new threshold, reprocess detections where deer_id IS NULL
   - Use existing re-ID pipeline
   - Compare before/after assignment rates

4. **Setup Ongoing Monitoring**
   - Weekly review of reid_similarity_scores
   - Alert if assignment rate drops below X%
   - Track model performance over time

---

## Example Session

```bash
# 1. Verify setup
docker-compose exec -T db psql -U deertrack deer_tracking -c "\d reid_similarity_scores"
# [OK] Table exists with correct schema

# 2. Test with small batch
docker-compose exec -T backend python3 /app/scripts/backfill_similarity_scores.py --limit 10
# [OK] Processed: 10 detections, Logged: 530 scores

# 3. Run medium batch for analysis
docker-compose exec -T backend python3 /app/scripts/backfill_similarity_scores.py --limit 1000
# [OK] Processed: 1000 detections in 23.5 minutes

# 4. Analyze results
docker-compose exec -T db psql -U deertrack deer_tracking -c "
SELECT ROUND(similarity_score, 1) as score, COUNT(*) as freq
FROM reid_similarity_scores
GROUP BY score ORDER BY score DESC;
"
# [INSIGHT] Peak at 0.7-0.8 (matches), valley at 0.4-0.5, current threshold 0.55

# 5. Test threshold impact
docker-compose exec -T db psql -U deertrack deer_tracking -c "
SELECT test_threshold, ROUND(100.0 * COUNT(DISTINCT CASE WHEN similarity_score >= test_threshold THEN detection_id END) / COUNT(DISTINCT detection_id), 2) as rate
FROM reid_similarity_scores
CROSS JOIN (SELECT unnest(ARRAY[0.45, 0.50, 0.55, 0.60]) as test_threshold) t
GROUP BY test_threshold ORDER BY test_threshold DESC;
"
# [DECISION] 0.50 threshold increases assignment rate by 15% with minimal false positives

# 6. Update threshold
vim .env
# Change: REID_THRESHOLD=0.50
docker-compose restart worker
# [OK] Worker restarted with new threshold

# 7. Monitor impact over next week
# Query reid_similarity_scores daily to track assignment rate trend
```

---

## Conclusion

Option D hybrid approach provides:
- **Immediate analysis capability** (backfill script)
- **Ongoing monitoring** (real-time similarity logging)
- **Data-driven decisions** (threshold tuning based on actual performance)

**Ready to run:** All infrastructure deployed and tested
**Next action:** Run backfill analysis when convenient (recommend overnight)

---

**Created:** November 15, 2025
**Author:** Claude Code
**Feature:** 010-infrastructure-fixes, Option D
