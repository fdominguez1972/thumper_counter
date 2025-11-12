#!/bin/bash
#
# Continuous Queue Monitor
# Automatically queues pending images when the worker queue is idle
#
# Usage: ./scripts/continuous_queue.sh
# To run in background: nohup ./scripts/continuous_queue.sh > queue_monitor.log 2>&1 &
#

set -e

API_URL="http://localhost:8001"
CHECK_INTERVAL=60  # Check every 60 seconds
BATCH_SIZE=10000   # Queue 10k images at a time

echo "[INFO] Starting continuous queue monitor..."
echo "[INFO] Check interval: ${CHECK_INTERVAL}s"
echo "[INFO] Batch size: ${BATCH_SIZE}"
echo ""

while true; do
    # Get current processing status
    STATUS=$(curl -s "${API_URL}/api/processing/status")

    PENDING=$(echo "$STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin)['pending'])" 2>/dev/null || echo "0")
    PROCESSING=$(echo "$STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin)['processing'])" 2>/dev/null || echo "0")
    COMPLETED=$(echo "$STATUS" | python3 -c "import sys, json; print(json.load(sys.stdin)['completed'])" 2>/dev/null || echo "0")

    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$TIMESTAMP] Status: Pending=$PENDING, Processing=$PROCESSING, Completed=$COMPLETED"

    # If there are pending images AND no images currently processing
    # (which means the queue is empty), queue a batch
    if [ "$PENDING" -gt "0" ] && [ "$PROCESSING" -eq "0" ]; then
        echo "[$TIMESTAMP] [ACTION] Queue is empty with $PENDING pending images - queueing batch of $BATCH_SIZE"

        RESULT=$(curl -s -X POST "${API_URL}/api/processing/batch?limit=${BATCH_SIZE}")
        QUEUED=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin)['queued_count'])" 2>/dev/null || echo "0")

        echo "[$TIMESTAMP] [OK] Queued $QUEUED images for processing"
    elif [ "$PENDING" -eq "0" ]; then
        echo "[$TIMESTAMP] [INFO] All images processed! No pending images."
    else
        echo "[$TIMESTAMP] [INFO] Worker actively processing ($PROCESSING images in queue)"
    fi

    echo ""
    sleep $CHECK_INTERVAL
done
