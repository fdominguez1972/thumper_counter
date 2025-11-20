# Feature 009: Enhanced Re-ID Rollback Guide

**Date:** November 14, 2025
**Feature:** 009-reid-enhancement
**Purpose:** Emergency rollback procedures if enhanced Re-ID causes issues

---

## WHEN TO ROLLBACK

Consider rolling back if you observe:

1. **High false positive rate:** Many duplicate deer profiles created
2. **Low assignment rate:** Fewer detections assigned than before (< 60%)
3. **Performance issues:** Worker processing slower than expected
4. **Database errors:** Issues with vector columns or indexes
5. **Model loading failures:** GPU memory or CUDA errors

---

## QUICK ROLLBACK (5 minutes)

### Step 1: Disable Enhanced Re-ID

```bash
# Edit .env file
cd /mnt/i/projects/thumper_counter
vi .env

# Change this line:
USE_ENHANCED_REID=false

# Save and exit (:wq)
```

### Step 2: Restart Worker

```bash
docker-compose restart worker
```

### Step 3: Verify Rollback

```bash
# Check worker logs
docker-compose logs worker | tail -20

# Should see:
# [FEATURE009] Enhanced Re-ID disabled (USE_ENHANCED_REID=false)
# [INFO] Using original ResNet50 Re-ID
```

### Step 4: Test Detection Pipeline

```bash
# Queue a small batch
curl -X POST "http://localhost:8001/api/processing/batch?limit=10"

# Monitor worker
docker-compose logs -f worker | grep "Re-ID complete"

# Should see detections processed with original Re-ID
```

**Result:** System reverts to original ResNet50-only matching with threshold 0.40

---

## FULL ROLLBACK (30 minutes)

If disabling enhanced Re-ID is not sufficient, perform full rollback:

### Step 1: Revert Threshold

```bash
# Edit .env
vi .env

# Change:
REID_THRESHOLD=0.40  # Revert from 0.60
USE_ENHANCED_REID=false
```

### Step 2: Identify Affected Deer Profiles

```bash
# Find deer created with enhanced Re-ID
docker-compose exec db psql -U deertrack deer_tracking

# Query:
SELECT id, name, sex, sighting_count, embedding_version, created_at
FROM deer
WHERE embedding_version = 'v3_ensemble'
  AND created_at > '2025-11-14'  -- Adjust date to rollback period
ORDER BY created_at DESC;
```

### Step 3: Review Potential Duplicates

**CAUTION:** Only delete deer profiles if you're CERTAIN they are duplicates.

```sql
-- Find potential duplicate deer (created during rollback period with low sighting count)
SELECT
  d1.id as deer1_id,
  d1.name as deer1_name,
  d1.sighting_count as deer1_sightings,
  d1.created_at as deer1_created,
  d2.id as deer2_id,
  d2.name as deer2_name,
  d2.sighting_count as deer2_sightings,
  d2.created_at as deer2_created,
  (1 - d1.feature_vector <=> d2.feature_vector) as similarity
FROM deer d1
JOIN deer d2 ON d1.id < d2.id
WHERE d1.sex = d2.sex
  AND d1.created_at > '2025-11-14'  -- Adjust rollback period
  AND (1 - d1.feature_vector <=> d2.feature_vector) > 0.40
ORDER BY similarity DESC;
```

### Step 4: Merge Duplicates (if found)

**Manual Process:**

1. Review each pair with similarity > 0.40
2. Choose primary deer profile (usually earliest created or most sightings)
3. Reassign detections from duplicate to primary
4. Delete duplicate

```sql
-- Example: Merge deer2 into deer1
BEGIN;

-- Reassign all detections
UPDATE detections
SET deer_id = 'DEER1_UUID'
WHERE deer_id = 'DEER2_UUID';

-- Update primary deer sighting count
UPDATE deer
SET sighting_count = sighting_count + (
  SELECT sighting_count FROM deer WHERE id = 'DEER2_UUID'
)
WHERE id = 'DEER1_UUID';

-- Delete duplicate
DELETE FROM deer WHERE id = 'DEER2_UUID';

COMMIT;
```

### Step 5: Restart Worker

```bash
docker-compose restart worker
```

### Step 6: Validate System

```bash
# Check deer count
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT embedding_version, COUNT(*) FROM deer GROUP BY embedding_version;"

# Check assignment rate
curl -s http://localhost:8001/api/processing/status | python3 -m json.tool

# Process test batch
curl -X POST "http://localhost:8001/api/processing/batch?limit=100"
```

---

## NUCLEAR ROLLBACK (1-2 hours)

If enhanced Re-ID created many incorrect deer profiles and manual cleanup is impractical:

### Option 1: Reprocess All Detections

**Warning:** This will delete ALL deer profiles and recreate from detections.

```bash
# Step 1: Backup database
docker-compose exec db pg_dump -U deertrack deer_tracking > backup_before_reprocess.sql

# Step 2: Delete all deer profiles
docker-compose exec db psql -U deertrack deer_tracking -c \
  "DELETE FROM deer;"

# Step 3: Reset all detections
docker-compose exec db psql -U deertrack deer_tracking -c \
  "UPDATE detections SET deer_id = NULL;"

# Step 4: Reprocess with original Re-ID
# Make sure USE_ENHANCED_REID=false and REID_THRESHOLD=0.40
docker-compose restart worker

# Step 5: Queue reprocessing
curl -X POST "http://localhost:8001/api/processing/reidentify/all"

# Step 6: Monitor progress
docker-compose logs -f worker | grep "Re-ID complete"
```

### Option 2: Restore from Database Backup

**Prerequisite:** You must have a backup from before enhanced Re-ID deployment.

```bash
# Step 1: Stop all services
docker-compose down

# Step 2: Start only database
docker-compose up -d db

# Step 3: Drop and recreate database
docker-compose exec db psql -U deertrack postgres -c \
  "DROP DATABASE deer_tracking;"
docker-compose exec db psql -U deertrack postgres -c \
  "CREATE DATABASE deer_tracking;"

# Step 4: Restore from backup
cat backup_before_feature009.sql | \
  docker-compose exec -T db psql -U deertrack deer_tracking

# Step 5: Restart all services
docker-compose up -d

# Step 6: Verify restoration
curl http://localhost:8001/health
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT COUNT(*) FROM deer;"
```

---

## POST-ROLLBACK VALIDATION

After any rollback, validate the system:

### 1. Check Deer Count

```bash
docker-compose exec db psql -U deertrack deer_tracking -c "
SELECT
  embedding_version,
  COUNT(*) as count,
  ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM deer), 1) as percent
FROM deer
GROUP BY embedding_version
ORDER BY count DESC;
"
```

Expected after rollback:
- v1_resnet50: 100% (or majority)
- v3_ensemble: 0% or minimal

### 2. Check Assignment Rate

```bash
curl -s http://localhost:8001/api/processing/status | python3 -m json.tool
```

Expected:
- Assignment rate: 55-65% (baseline from Feature 010)
- Similar to pre-Feature 009 performance

### 3. Test Re-ID Pipeline

```bash
# Process 100 test images
curl -X POST "http://localhost:8001/api/processing/batch?limit=100"

# Monitor for errors
docker-compose logs -f worker | grep -E "(ERROR|FAIL|Re-ID complete)"
```

### 4. Check Similarity Scores

```bash
# Run validation script with original Re-ID
docker-compose exec backend python3 /app/scripts/validate_enhanced_reid.py

# Verify mean similarity is back to ~0.42
```

### 5. Monitor for 24 Hours

After rollback, monitor these metrics:

1. **Worker errors:** Should be zero
2. **Assignment rate:** Stable at 55-65%
3. **New deer creation rate:** Similar to before Feature 009
4. **Processing throughput:** Back to 45-50 detections/sec

---

## PREVENTIVE MEASURES

To avoid needing rollback in future:

### 1. Always Test in Staging First

```bash
# Create test environment variable
USE_ENHANCED_REID_TEST=true

# Process only test batches
curl -X POST "http://localhost:8001/api/processing/batch?limit=100&test_mode=true"

# Validate results before full deployment
```

### 2. Enable Gradual Rollout

```bash
# Process only X% of detections with enhanced Re-ID
ENHANCED_REID_SAMPLE_RATE=0.1  # 10% of detections

# Gradually increase: 0.1 -> 0.5 -> 1.0
```

### 3. Set Up Monitoring Alerts

Monitor and alert on:
- Assignment rate drops below 50%
- New deer creation rate > 10/hour
- Mean similarity < 0.40 (indicates model issues)
- Worker errors > 5/minute

### 4. Maintain Regular Backups

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec db pg_dump -U deertrack deer_tracking > \
  backups/deer_tracking_${DATE}.sql
gzip backups/deer_tracking_${DATE}.sql

# Keep last 7 days
find backups/ -name "*.sql.gz" -mtime +7 -delete
```

---

## TROUBLESHOOTING

### Issue: Worker won't start after rollback

```bash
# Check logs
docker-compose logs worker

# Common causes:
# 1. .env changes not loaded - restart worker
# 2. Model files corrupted - rebuild worker container
# 3. GPU memory issue - reduce BATCH_SIZE

# Fix:
docker-compose down
docker-compose up -d --build worker
```

### Issue: Database queries slow after rollback

```bash
# Reanalyze tables
docker-compose exec db psql -U deertrack deer_tracking -c "
ANALYZE deer;
ANALYZE detections;
"

# Rebuild indexes
docker-compose exec db psql -U deertrack deer_tracking -c "
REINDEX TABLE deer;
"
```

### Issue: High false positive rate persists

```bash
# Check threshold is reset
echo $REID_THRESHOLD  # Should be 0.40

# Verify original Re-ID is active
docker-compose logs worker | grep "FEATURE009"
# Should see: "Enhanced Re-ID disabled"

# Manual review of recent deer
curl http://localhost:8001/api/deer?sort=created_at&order=desc&limit=20
```

---

## CONTACT AND ESCALATION

If rollback fails or issues persist:

### Level 1: Check Logs

```bash
# Worker logs
docker-compose logs worker --tail=100

# Backend logs
docker-compose logs backend --tail=100

# Database logs
docker-compose logs db --tail=100
```

### Level 2: Validate Configuration

```bash
# Check .env
cat .env | grep -E "(REID|ENHANCED)"

# Check worker environment
docker-compose exec worker env | grep -E "(REID|ENHANCED)"
```

### Level 3: Database Integrity

```bash
# Check for NULL vectors
docker-compose exec db psql -U deertrack deer_tracking -c "
SELECT COUNT(*) as null_vectors
FROM deer
WHERE feature_vector IS NULL;
"

# Should be 0 or very few
```

### Level 4: Rebuild from Clean State

If all else fails, rebuild worker container:

```bash
docker-compose down
docker-compose build --no-cache worker
docker-compose up -d
```

---

## ROLLBACK CHECKLIST

Use this checklist to ensure complete rollback:

- [ ] Step 1: Disable USE_ENHANCED_REID in .env
- [ ] Step 2: Revert REID_THRESHOLD to 0.40
- [ ] Step 3: Restart worker container
- [ ] Step 4: Verify worker logs show "Enhanced Re-ID disabled"
- [ ] Step 5: Test with 10-image batch
- [ ] Step 6: Check assignment rate (should be 55-65%)
- [ ] Step 7: Identify any duplicate deer profiles created
- [ ] Step 8: Merge duplicates if found (manual process)
- [ ] Step 9: Validate deer count matches expectations
- [ ] Step 10: Monitor for 24 hours
- [ ] Step 11: Document what went wrong
- [ ] Step 12: Plan fixes before re-enabling

---

## LESSONS LEARNED LOG

Document rollback incidents here for future reference:

### Incident Template

```
Date: YYYY-MM-DD
Issue: Brief description
Root Cause: What caused the problem
Rollback Method: Quick / Full / Nuclear
Time to Rollback: X hours
Data Lost: Yes/No (describe)
Prevention: How to avoid in future
```

### Example Entry

```
Date: 2025-11-15
Issue: High false positive rate (30% duplicates)
Root Cause: REID_THRESHOLD too low (0.40) for enhanced similarity scores
Rollback Method: Quick rollback (disabled enhanced Re-ID)
Time to Rollback: 15 minutes
Data Lost: No (all deer profiles preserved)
Prevention: Always adjust threshold when changing Re-ID method
```

---

## SUMMARY

Rollback procedures are provided at three levels:

1. **Quick (5 min):** Disable enhanced Re-ID, keep threshold
2. **Full (30 min):** Revert threshold, merge duplicates
3. **Nuclear (1-2 hours):** Reprocess all or restore backup

Always validate after rollback and monitor for 24 hours.

**Prevention is best:** Test in staging, enable gradually, maintain backups, set up monitoring alerts.

---

**Document Version:** 1.0
**Last Updated:** November 14, 2025
**Maintained By:** ML Operations Team
