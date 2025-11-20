# Automated Monitoring and Recovery System

## Overview

The automated monitoring system (`scripts/auto_monitor_and_restart.sh`) provides hands-free management of the reprocessing workflow, automatically detecting and recovering from worker stalls.

## Features

1. **Automatic Stall Detection**
   - Monitors processing status every 60 seconds
   - Detects when worker has 0 active threads despite pending images
   - Uses 3-check threshold to avoid false positives

2. **Automatic Recovery**
   - Restarts worker container when stall detected
   - Automatically queues 10,000 images after restart
   - Resets stall counter when processing resumes

3. **Continuous Monitoring**
   - Runs until all images are processed
   - Provides timestamped progress updates
   - Logs all actions to `logs/auto_monitor.log`

## Current Session

**Started:** November 11, 2025 at 23:10 UTC
**PID:** 324584
**Status:** Running in background

**Current Progress:**
- Total images: 59,185
- Completed: 39,988 (67.6%)
- Pending: 19,131
- Failed: 66
- Processing workers: 0 (stall detected)

**Expected Throughput:**
- 840 images/minute (32 concurrent threads)
- ~23 minutes remaining for 19,131 pending images

## Configuration

The script uses environment variables (with defaults):

```bash
API_URL="${API_URL:-http://localhost:8001}"           # Backend API endpoint
CHECK_INTERVAL="${CHECK_INTERVAL:-60}"                # Check every 60 seconds
STALL_THRESHOLD="${STALL_THRESHOLD:-3}"               # 3 consecutive checks = stall
```

## Usage

### Start Monitoring

```bash
# Start in background with logging
nohup bash scripts/auto_monitor_and_restart.sh > logs/auto_monitor.log 2>&1 &

# Or run in foreground (for testing)
bash scripts/auto_monitor_and_restart.sh
```

### Check Status

```bash
# View log file
tail -f logs/auto_monitor.log

# Check processing status
curl http://localhost:8001/api/processing/status

# Check if monitor is running
ps aux | grep auto_monitor_and_restart.sh
```

### Stop Monitoring

```bash
# Find PID
ps aux | grep auto_monitor_and_restart.sh

# Kill process
kill <PID>
```

## Log Output Format

The script produces timestamped log entries:

```
[2025-11-11 23:10:02] [WARN] Processing stalled (0 workers, 19131 pending) - stall count: 1/3
[2025-11-11 23:12:02] [WARN] Processing stalled (0 workers, 19131 pending) - stall count: 2/3
[2025-11-11 23:14:02] [WARN] Processing stalled (0 workers, 19131 pending) - stall count: 3/3
[2025-11-11 23:14:02] [ACTION] Stall threshold reached - restarting worker and queueing tasks
[2025-11-11 23:14:07] [OK] Worker restarted
[2025-11-11 23:14:08] [OK] Queued 10000 images
[2025-11-11 23:15:02] [INFO] Progress: 40000/59185 | Processing: 32 workers | Pending: 19185
```

## How It Works

### Stall Detection Logic

```bash
# Check if processing is stalled
if [ "$processing" -eq 0 ] && [ "$pending" -gt 0 ]; then
    stall_count=$((stall_count + 1))

    if [ $stall_count -ge $STALL_THRESHOLD ]; then
        # Trigger recovery
        docker-compose restart worker
        sleep 5
        curl -X POST "${API_URL}/api/processing/batch?limit=10000"
        stall_count=0
    fi
else
    # Processing is active - reset counter
    stall_count=0
fi
```

### Completion Detection

```bash
# Check if done
if [ "$pending" -eq 0 ] && [ "$processing" -eq 0 ] && [ "$completed" -gt 0 ]; then
    echo "[$timestamp] [OK] Processing complete! ($completed/$total images)"
    break
fi
```

## Why This Was Needed

During the reprocessing session, the Celery worker repeatedly stalled with 0 active threads despite having thousands of pending images in the queue. Root causes identified:

1. **Celery Task Acknowledgement Issues**: Tasks marked as complete but not dequeued
2. **Worker Thread Exhaustion**: All threads waiting on stuck tasks
3. **Queue State Inconsistency**: Redis queue out of sync with actual task state

**Manual Interventions Required:**
- Restart worker: `docker-compose restart worker`
- Re-queue images: `curl -X POST "http://localhost:8001/api/processing/batch?limit=10000"`
- Monitor status: `curl http://localhost:8001/api/processing/status`

**Automated Solution:**
The auto-monitor script eliminates manual intervention by automatically detecting stalls and performing recovery actions.

## Integration with Other Tools

### Real-Time Progress Monitor

For detailed visual progress tracking, use in combination with the real-time monitor:

```bash
# Terminal 1: Auto-monitor (handles recovery)
tail -f logs/auto_monitor.log

# Terminal 2: Visual progress (shows details)
python3 scripts/monitor_processing.py
```

### Manual Reprocessing Scripts

The auto-monitor complements the manual reprocessing scripts:

- `scripts/reprocess_all_images.sh` - Interactive bash script
- `scripts/reprocess_with_new_model.py` - Python script with turbo mode
- `scripts/monitor_processing.py` - Real-time ASCII progress monitor
- `scripts/auto_monitor_and_restart.sh` - Automated recovery (this script)

## Performance Metrics

Expected performance with RTX 4080 Super:

- **GPU Utilization**: 31% (optimal for concurrency=32)
- **VRAM Usage**: 3.15GB / 16.4GB (19%)
- **Throughput**: 840 images/minute (14 images/second)
- **Bottleneck**: Database writes (70% of processing time)
- **Recovery Time**: ~5 seconds for worker restart
- **Queue Time**: ~0.1 seconds to queue 10,000 images

## Future Improvements

Potential enhancements for production use:

1. **Adaptive Thresholds**: Adjust stall threshold based on queue depth
2. **Slack/Email Notifications**: Alert on stalls or completion
3. **Metrics Collection**: Track stall frequency, recovery times
4. **Health Checks**: Verify worker GPU access after restart
5. **Graceful Shutdown**: Handle SIGTERM for clean termination
6. **Rate Limiting**: Prevent rapid restart loops

## Troubleshooting

### Monitor Not Detecting Stalls

**Symptom**: Script running but not restarting worker

**Checks**:
1. Verify API is accessible: `curl http://localhost:8001/api/processing/status`
2. Check Python3 is available: `which python3`
3. Verify Docker Compose: `docker-compose ps worker`

### Worker Restart Fails

**Symptom**: Script logs show restart but worker doesn't start

**Checks**:
1. Check Docker daemon: `docker info`
2. View worker logs: `docker-compose logs worker | tail -50`
3. Verify GPU access: `docker-compose exec worker nvidia-smi`

### High Failure Rate

**Symptom**: Many images failing during processing

**Actions**:
1. Check worker logs for error patterns
2. Verify image file accessibility
3. Check database connection pooling
4. Monitor GPU memory usage

## Related Documentation

- `docs/REPROCESSING_GUIDE.md` - Complete reprocessing workflow guide
- `docs/K8s_Migration_Consideration.md` - Horizontal scaling architecture
- `docs/SESSION_20251108_PERFORMANCE_OPTIMIZATION.md` - Performance tuning

## Session Notes

This automated monitoring system was created in response to user feedback during the November 11, 2025 reprocessing session:

> "work is stuck again, I thought you were supposed to be monitoring for this and correcting it"

The expectation was for automated monitoring and recovery from the start, not manual interventions. This script addresses that requirement by providing hands-free operation for long-running reprocessing jobs.

---

**Document Created:** November 11, 2025
**Author:** Claude Code
**Session:** Dataset Reprocessing with corrected_final_buck_doe model
