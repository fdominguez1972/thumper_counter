# Operations Runbook - Thumper Counter ML Pipeline

**Last Updated**: 2025-11-11  
**System**: Deer Tracking ML Pipeline  
**Environment**: Production (WSL2 + Docker Desktop)

---

## Table of Contents

1. [System Health Checks](#system-health-checks)
2. [Bulk Image Import Workflow](#bulk-image-import-workflow)
3. [Queue Management](#queue-management)
4. [Troubleshooting](#troubleshooting)
5. [Performance Tuning](#performance-tuning)
6. [Monitoring](#monitoring)

---

## System Health Checks

### Quick Status Check

```bash
# Check all containers
docker-compose ps

# Check API health
curl http://localhost:8001/health

# Check processing status
curl -s http://localhost:8001/api/processing/status | python3 -m json.tool

# Check worker logs
docker-compose logs --tail=50 worker

# Check queue length
docker-compose exec redis redis-cli LLEN ml_processing
```

### Expected Healthy State

```
Containers: All "Up" status
API: Returns {"status": "healthy"}
Processing: pending + processing + completed = total
Worker: Recent log entries showing "Detection complete"
Queue: 0-50,000 (depends on pending images)
```

---

## Bulk Image Import Workflow

### Step 1: Copy Images to Storage

```bash
# Run rsync copy script
bash scripts/copy_and_queue_images.sh

# Monitor progress
# Output shows: [OK] Copied images for {location}
```

**Expected Results**:
- 270_Jason: ~8,788 images
- Hayfield: ~5,533 images
- Sanctuary: ~9,613 images

### Step 2: Register Images in Database

```bash
# Run registration script in backend container
docker-compose exec -T backend python3 /app/scripts/register_copied_images.py

# Expected output:
# [INFO] Found X total images in directory
# [INFO] Already have Y images in database
# [OK] Total new imports: Z
```

**Key Metrics**:
- EXIF timestamp success: Should be >95%
- Duplicates: Expected based on previous imports
- Errors: Should be 0

### Step 3: Start Automatic Queue Monitor

```bash
# Start background monitor
nohup ./scripts/continuous_queue.sh > queue_monitor.log 2>&1 &

# Get process ID
echo $!

# Monitor progress
tail -f queue_monitor.log
```

**What it does**:
- Checks status every 60 seconds
- Auto-queues 10,000 images when queue is empty
- Continues until all images processed

### Step 4: Verify Processing

```bash
# Check status every 5 minutes
watch -n 300 'curl -s http://localhost:8001/api/processing/status | python3 -m json.tool'

# Check completion rate
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT processing_status, COUNT(*) FROM images GROUP BY processing_status;"
```

---

## Queue Management

### Manual Queue Operations

```bash
# Queue 10,000 pending images
curl -X POST "http://localhost:8001/api/processing/batch?limit=10000"

# Queue specific images by ID
curl -X POST "http://localhost:8001/api/processing/batch" \
  -H "Content-Type: application/json" \
  -d '{"image_ids": ["uuid1", "uuid2", "uuid3"]}'

# Check queue length
docker-compose exec redis redis-cli LLEN ml_processing
```

### Queue States

| State | Processing Value | Meaning |
|-------|-----------------|---------|
| **Idle** | 0 | Queue empty, worker waiting |
| **Active** | >0 | Images being processed |
| **Stuck** | 0 with pending>0 for >5min | Requires manual queue |

### Automatic Queue Recovery

If automatic queue monitor is not running:

```bash
# Find and stop old processes
ps aux | grep continuous_queue.sh
kill <PID>

# Start fresh
nohup ./scripts/continuous_queue.sh > queue_monitor.log 2>&1 &
```

---

## Troubleshooting

### Issue: Images Stuck in Pending Status

**Symptoms**:
- `/api/processing/status` shows `pending > 0` and `processing = 0`
- Queue length is 0: `redis-cli LLEN ml_processing` returns 0

**Root Cause**: Images imported but not queued

**Solution**:
```bash
# Option 1: Start automatic monitor
nohup ./scripts/continuous_queue.sh > queue_monitor.log 2>&1 &

# Option 2: Manual queue
curl -X POST "http://localhost:8001/api/processing/batch?limit=10000"
```

### Issue: Worker Not Processing Images

**Symptoms**:
- Queue length >0 but worker logs show no activity
- Images stuck in "processing" status

**Solution**:
```bash
# Restart worker
docker-compose restart worker

# Wait 30 seconds for model loading
sleep 30

# Check worker startup
docker-compose logs --tail=50 worker | grep "celery@"
```

### Issue: High Failure Rate

**Symptoms**:
- `/api/processing/status` shows `failed > 100`
- Worker logs show repeated errors

**Diagnosis**:
```bash
# Check failed images
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT error_message, COUNT(*) FROM images WHERE processing_status='failed' GROUP BY error_message LIMIT 10;"

# Check worker errors
docker-compose logs worker | grep ERROR | tail -20
```

**Common Causes**:
- Missing image files: Check file paths
- GPU out of memory: Reduce batch size (see Performance Tuning)
- Model loading failure: Check model file exists

### Issue: Slow Processing

**Symptoms**:
- Throughput <500 images/minute
- GPU utilization <20%

**Solution**: See Performance Tuning section

---

## Performance Tuning

### Optimal Configuration (Current)

```yaml
# docker-compose.yml worker configuration
concurrency: 32  # Threads
BATCH_SIZE: 16   # Images per batch
GPU: RTX 4080 Super (16GB VRAM)
```

**Results**:
- Throughput: 840 images/minute
- GPU Utilization: 31%
- Bottleneck: Database writes (70% of time)

### Concurrency Testing Results

| Concurrency | Throughput | GPU Util | Notes |
|-------------|------------|----------|-------|
| 1 | 150 img/min | 10% | Baseline |
| 16 | 600 img/min | 25% | Good |
| 32 | 840 img/min | 31% | Optimal |
| 64 | 540 img/min | 18% | GPU lock contention |

### Adjust Worker Concurrency

```bash
# Edit docker-compose.yml
# Change: celery -A worker.celery_app worker --concurrency=32
# To: celery -A worker.celery_app worker --concurrency=16

# Restart worker
docker-compose up -d --build worker
```

### GPU Memory Issues

If you see CUDA OOM errors:

```bash
# Reduce batch size (in .env)
BATCH_SIZE=8  # Down from 16

# Restart backend and worker
docker-compose restart backend worker
```

---

## Monitoring

### Real-Time Processing Dashboard

```bash
# Terminal 1: Queue monitor
tail -f queue_monitor.log

# Terminal 2: Worker logs
docker-compose logs -f worker | grep "Detection complete"

# Terminal 3: Status polling
watch -n 10 'curl -s http://localhost:8001/api/processing/status | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"Pending: {d[\"pending\"]}, Processing: {d[\"processing\"]}, Completed: {d[\"completed\"]}, Rate: {d[\"completion_rate\"]:.1f}%\")"'
```

### Database Queries

```sql
-- Image processing breakdown
SELECT processing_status, COUNT(*) as count
FROM images
GROUP BY processing_status;

-- Detections per location
SELECT l.name, COUNT(d.id) as detection_count
FROM locations l
JOIN images i ON i.location_id = l.id
JOIN detections d ON d.image_id = i.id
GROUP BY l.name
ORDER BY detection_count DESC;

-- Recent processing failures
SELECT filename, error_message, updated_at
FROM images
WHERE processing_status = 'failed'
ORDER BY updated_at DESC
LIMIT 20;
```

### Celery Flower (Web UI)

```bash
# Access Flower monitoring
open http://localhost:5555

# View active tasks, worker status, task history
```

---

## Alerts and Notifications

### Conditions Requiring Attention

1. **Queue Idle with Pending Images**
   - Check: `processing=0 AND pending>100 for >5 minutes`
   - Action: Start continuous queue monitor

2. **High Failure Rate**
   - Check: `failed>1000 OR failure_rate>5%`
   - Action: Investigate worker logs and failed image error messages

3. **Low Throughput**
   - Check: `throughput<300 images/minute sustained for >10 minutes`
   - Action: Check GPU utilization and worker logs

4. **Worker Crash**
   - Check: Worker container exits or restarts
   - Action: Review worker logs, check model file, restart worker

---

## Emergency Procedures

### Complete System Restart

```bash
# Stop all services
docker-compose down

# Start fresh
docker-compose up -d

# Wait for health checks
sleep 30

# Verify all healthy
docker-compose ps
curl http://localhost:8001/health
```

### Clear Stuck Queue

```bash
# WARNING: This clears the entire queue
docker-compose exec redis redis-cli FLUSHDB

# Re-queue pending images
curl -X POST "http://localhost:8001/api/processing/batch?limit=10000"
```

### Reset Failed Images to Pending

```sql
-- Connect to database
docker-compose exec db psql -U deertrack deer_tracking

-- Reset specific failed images
UPDATE images
SET processing_status = 'pending',
    error_message = NULL
WHERE processing_status = 'failed'
  AND error_message LIKE '%specific error pattern%';

-- Or reset ALL failed images
UPDATE images
SET processing_status = 'pending',
    error_message = NULL
WHERE processing_status = 'failed';
```

---

## Contact and Escalation

- **System Owner**: Ranch Manager
- **Technical Support**: Spec-Kit Development Team
- **Documentation**: `/docs/` directory
- **Issue Tracking**: GitHub Issues

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2025-11-11 | Initial runbook created with queue management procedures | Claude |
| 2025-11-11 | Added performance tuning section with concurrency testing results | Claude |
| 2025-11-11 | Documented bulk import workflow for 23,934 image import | Claude |
