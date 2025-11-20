#!/bin/bash
#
# Weekly Automated Reprocessing Script
# Runs every Sunday at 2:00 AM to ensure all images use latest models/fixes
#
# Setup: Add to crontab
#   0 2 * * 0 /mnt/i/projects/thumper_counter/scripts/weekly_reprocess.sh
#

set -e  # Exit on error

# Configuration
PROJECT_DIR="/mnt/i/projects/thumper_counter"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/weekly_reprocess_$(date +%Y%m%d_%H%M%S).log"
API_URL="http://localhost:8001"

# Create log directory
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "WEEKLY REPROCESSING STARTED"
log "=========================================="

# Change to project directory
cd "$PROJECT_DIR"

# Step 1: Check system health
log "[STEP 1] Checking system health..."
if ! docker-compose ps | grep -q "Up"; then
    log "[ERROR] Docker containers not running!"
    exit 1
fi
log "[OK] Docker containers healthy"

# Step 2: Get current stats
log "[STEP 2] Capturing pre-reprocess statistics..."
STATS_BEFORE=$(curl -s "${API_URL}/api/processing/status" | python3 -m json.tool)
log "$STATS_BEFORE"

DEER_BEFORE=$(docker-compose exec -T db psql -U deertrack deer_tracking -c \
    "SELECT COUNT(*) FROM deer;" -t | tr -d ' ')
log "[INFO] Deer profiles before: $DEER_BEFORE"

# Step 3: Clear old detections and reset image status
log "[STEP 3] Running full reprocessing script..."
docker-compose exec -T backend python3 /app/scripts/reprocess_with_new_model.py --turbo --clear-mode all >> "$LOG_FILE" 2>&1

if [ $? -ne 0 ]; then
    log "[ERROR] Reprocessing script failed!"
    exit 1
fi
log "[OK] Database cleared and images reset to pending"

# Step 4: Queue all pending images (6 batches of 10k in parallel)
log "[STEP 4] Queueing images for processing..."
for i in {1..6}; do
    curl -s -X POST "${API_URL}/api/processing/batch?limit=10000" > /dev/null &
done
wait
log "[OK] All images queued"

# Step 5: Monitor progress (check every 5 minutes)
log "[STEP 5] Monitoring reprocessing progress..."
MONITORING_INTERVAL=300  # 5 minutes
MAX_WAIT=14400  # 4 hours max
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    STATS=$(curl -s "${API_URL}/api/processing/status" | python3 -m json.tool)
    PENDING=$(echo "$STATS" | grep '"pending"' | awk '{print $2}' | tr -d ',')
    COMPLETED=$(echo "$STATS" | grep '"completed"' | awk '{print $2}' | tr -d ',')
    PROCESSING=$(echo "$STATS" | grep '"processing"' | awk '{print $2}' | tr -d ',')

    log "[PROGRESS] Pending: $PENDING, Processing: $PROCESSING, Completed: $COMPLETED"

    # Check if done
    if [ "$PENDING" -eq 0 ] && [ "$PROCESSING" -eq 0 ]; then
        log "[OK] Reprocessing complete!"
        break
    fi

    sleep $MONITORING_INTERVAL
    ELAPSED=$((ELAPSED + MONITORING_INTERVAL))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    log "[WARN] Reprocessing timeout after 4 hours"
fi

# Step 6: Collect final statistics
log "[STEP 6] Collecting post-reprocess statistics..."
STATS_AFTER=$(curl -s "${API_URL}/api/processing/status" | python3 -m json.tool)
log "$STATS_AFTER"

DEER_AFTER=$(docker-compose exec -T db psql -U deertrack deer_tracking -c \
    "SELECT COUNT(*) FROM deer;" -t | tr -d ' ')
log "[INFO] Deer profiles after: $DEER_AFTER"

DEER_CHANGE=$((DEER_AFTER - DEER_BEFORE))
log "[INFO] Deer profile change: $DEER_CHANGE"

# Step 7: Check for anomalies
log "[STEP 7] Checking for anomalies..."

# Check for excessive deer creation (might indicate Re-ID issue)
if [ $DEER_AFTER -gt 100 ]; then
    log "[WARN] Deer profile count unexpectedly high ($DEER_AFTER). Check REID_THRESHOLD."
fi

# Check assignment rate
ASSIGNMENT_RATE=$(docker-compose exec -T db psql -U deertrack deer_tracking -c \
    "SELECT ROUND(100.0 * COUNT(*) FILTER (WHERE deer_id IS NOT NULL) / COUNT(*), 1) FROM detections;" -t | tr -d ' ')
log "[INFO] Assignment rate: ${ASSIGNMENT_RATE}%"

if (( $(echo "$ASSIGNMENT_RATE < 60" | bc -l) )); then
    log "[WARN] Assignment rate low ($ASSIGNMENT_RATE%). Consider lowering REID_THRESHOLD."
fi

# Step 8: Summary
log "=========================================="
log "WEEKLY REPROCESSING COMPLETE"
log "=========================================="
log "Summary:"
log "  - Images processed: $COMPLETED"
log "  - Deer profiles: $DEER_BEFORE → $DEER_AFTER ($DEER_CHANGE change)"
log "  - Assignment rate: ${ASSIGNMENT_RATE}%"
log "  - Log file: $LOG_FILE"
log "=========================================="

# Optional: Send notification (email, Slack, etc.)
# echo "Weekly reprocessing complete. See $LOG_FILE for details." | mail -s "Thumper Counter Weekly Reprocess" you@example.com

exit 0
