#!/bin/bash
#
# Continuous Queue Monitor
# Automatically queues batches when Redis queue is low
# Monitors BOTH image detection AND Re-ID processing
#
# Usage: nohup ./scripts/continuous_queue.sh > /tmp/continuous_queue.log 2>&1 &

set -e

API_URL="http://localhost:8001"
CHECK_INTERVAL=60  # Check every 60 seconds
QUEUE_THRESHOLD=100  # Queue more if below this
BATCH_SIZE=10000

echo "[$(date)] Continuous queue monitor started (v2 - with Re-ID monitoring)"

while true; do
    # Get processing status
    STATUS=$(curl -s "${API_URL}/api/processing/status")
    PENDING=$(echo "$STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin)['pending'])")
    PROCESSING=$(echo "$STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin)['processing'])")

    # Check Redis queue depth
    QUEUE_DEPTH=$(docker-compose exec -T redis redis-cli LLEN ml_processing 2>/dev/null || echo "0")

    # Check unassigned detections (need Re-ID)
    UNASSIGNED=$(docker-compose exec -T db psql -U deertrack deer_tracking -t -c \
        "SELECT COUNT(*) FROM detections WHERE deer_id IS NULL AND classification IN ('buck', 'doe', 'fawn');" \
        2>/dev/null | tr -d ' ' || echo "0")

    timestamp=$(date +'%Y-%m-%d %H:%M:%S')

    # Queue detection tasks if queue is low and we have pending images
    if [ "$QUEUE_DEPTH" -lt "$QUEUE_THRESHOLD" ] && [ "$PENDING" -gt 0 ]; then
        echo "[$timestamp] [ACTION-DETECTION] Queue: $QUEUE_DEPTH, Pending: $PENDING - Queuing detection batch"
        curl -s -X POST "${API_URL}/api/processing/batch?limit=${BATCH_SIZE}" > /dev/null
    # Queue Re-ID tasks if queue is low and we have unassigned detections
    elif [ "$QUEUE_DEPTH" -lt "$QUEUE_THRESHOLD" ] && [ "$UNASSIGNED" -gt 0 ]; then
        echo "[$timestamp] [ACTION-REID] Queue: $QUEUE_DEPTH, Unassigned: $UNASSIGNED - Queuing Re-ID batch"
        docker-compose exec -T backend python3 /app/scripts/queue_all_reid.py > /dev/null 2>&1
    else
        echo "[$timestamp] [OK] Queue: $QUEUE_DEPTH, Pending: $PENDING, Processing: $PROCESSING, Unassigned: $UNASSIGNED"
    fi

    sleep $CHECK_INTERVAL
done
