#!/bin/bash
#
# Continuous Queue Monitor
# Automatically queues batches when Redis queue is low
#
# Usage: nohup ./scripts/continuous_queue.sh > /tmp/continuous_queue.log 2>&1 &

set -e

API_URL="http://localhost:8001"
CHECK_INTERVAL=60  # Check every 60 seconds
QUEUE_THRESHOLD=100  # Queue more if below this
BATCH_SIZE=10000

echo "[$(date)] Continuous queue monitor started"

while true; do
    # Get processing status
    STATUS=$(curl -s "${API_URL}/api/processing/status")
    PENDING=$(echo "$STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin)['pending'])")
    PROCESSING=$(echo "$STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin)['processing'])")

    # Check Redis queue depth
    QUEUE_DEPTH=$(docker-compose exec -T redis redis-cli LLEN ml_processing 2>/dev/null || echo "0")

    timestamp=$(date +'%Y-%m-%d %H:%M:%S')

    # Queue more if queue is low and we have pending images
    if [ "$QUEUE_DEPTH" -lt "$QUEUE_THRESHOLD" ] && [ "$PENDING" -gt 0 ]; then
        echo "[$timestamp] [ACTION] Queue depth: $QUEUE_DEPTH, Pending: $PENDING - Queuing batch"
        curl -s -X POST "${API_URL}/api/processing/batch?limit=${BATCH_SIZE}" > /dev/null
    else
        echo "[$timestamp] [OK] Queue: $QUEUE_DEPTH, Pending: $PENDING, Processing: $PROCESSING"
    fi

    sleep $CHECK_INTERVAL
done
