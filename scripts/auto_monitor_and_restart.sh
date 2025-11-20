#!/bin/bash
# Automatic monitoring and worker restart script
# Monitors processing status and automatically restarts worker if it stalls
# Created: 2025-11-11
# Author: Claude Code

set -e

API_URL="${API_URL:-http://localhost:8001}"
CHECK_INTERVAL="${CHECK_INTERVAL:-60}"  # Check every 60 seconds
STALL_THRESHOLD="${STALL_THRESHOLD:-3}"  # Consider stalled after 3 checks with 0 workers

echo "======================================================================="
echo "AUTOMATIC PROCESSING MONITOR AND RECOVERY"
echo "======================================================================="
echo ""
echo "Configuration:"
echo "  API URL: $API_URL"
echo "  Check interval: ${CHECK_INTERVAL}s"
echo "  Stall threshold: ${STALL_THRESHOLD} consecutive checks"
echo ""
echo "Starting monitoring... (Press Ctrl+C to stop)"
echo "======================================================================="
echo ""

stall_count=0
last_completed=0
iteration=0

while true; do
    iteration=$((iteration + 1))
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # Fetch status
    status=$(curl -s "${API_URL}/api/processing/status" 2>/dev/null)

    if [ $? -ne 0 ]; then
        echo "[$timestamp] [WARN] Failed to fetch status from API"
        sleep $CHECK_INTERVAL
        continue
    fi

    # Parse status
    total=$(echo "$status" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))" 2>/dev/null || echo "0")
    completed=$(echo "$status" | python3 -c "import sys, json; print(json.load(sys.stdin).get('completed', 0))" 2>/dev/null || echo "0")
    pending=$(echo "$status" | python3 -c "import sys, json; print(json.load(sys.stdin).get('pending', 0))" 2>/dev/null || echo "0")
    processing=$(echo "$status" | python3 -c "import sys, json; print(json.load(sys.stdin).get('processing', 0))" 2>/dev/null || echo "0")
    rate=$(echo "$status" | python3 -c "import sys, json; print(json.load(sys.stdin).get('completion_rate', 0))" 2>/dev/null || echo "0")

    # Check Redis queue depth
    queue_depth=$(docker-compose exec -T redis redis-cli LLEN ml_processing 2>/dev/null | tr -d '\r' || echo "0")

    # Check if processing is stalled (worker crashed or routing issue)
    if [ "$processing" -eq 0 ] && [ "$pending" -gt 0 ]; then
        stall_count=$((stall_count + 1))
        echo "[$timestamp] [WARN] Processing stalled (0 workers, $pending pending) - stall count: $stall_count/$STALL_THRESHOLD"

        if [ $stall_count -ge $STALL_THRESHOLD ]; then
            echo "[$timestamp] [ACTION] Stall threshold reached - restarting worker and queueing tasks"

            # Restart worker
            docker-compose restart worker
            echo "[$timestamp] [OK] Worker restarted"

            # Wait for worker to start
            sleep 5

            # Queue batch of images
            queue_result=$(curl -s -X POST "${API_URL}/api/processing/batch?limit=10000" 2>/dev/null)
            queued=$(echo "$queue_result" | python3 -c "import sys, json; print(json.load(sys.stdin).get('queued_count', 0))" 2>/dev/null || echo "0")
            echo "[$timestamp] [OK] Queued $queued images"

            # Reset stall count
            stall_count=0
        fi
    # Check if queue is depleted (workers idle, queue empty, but images pending)
    elif [ "$queue_depth" -lt 100 ] && [ "$pending" -gt 0 ]; then
        echo "[$timestamp] [ACTION] Queue depth low ($queue_depth) - queueing more tasks"

        # Queue batch of images
        queue_result=$(curl -s -X POST "${API_URL}/api/processing/batch?limit=10000" 2>/dev/null)
        queued=$(echo "$queue_result" | python3 -c "import sys, json; print(json.load(sys.stdin).get('queued_count', 0))" 2>/dev/null || echo "0")
        echo "[$timestamp] [OK] Queued $queued images (queue depth was $queue_depth)"

        # Reset stall count
        stall_count=0
    else
        # Processing is active or queue is healthy
        if [ $stall_count -gt 0 ]; then
            echo "[$timestamp] [OK] Processing resumed - resetting stall counter"
        fi
        stall_count=0

        # Calculate progress
        progress_msg="[$timestamp] [INFO] Progress: $completed/$total ($rate%) | Processing: $processing workers | Pending: $pending | Queue: $queue_depth"

        # Only show every 5th iteration when things are working
        if [ $((iteration % 5)) -eq 0 ]; then
            echo "$progress_msg"
        fi
    fi

    # Store last completed count
    last_completed=$completed

    # Check if done
    if [ "$pending" -eq 0 ] && [ "$processing" -eq 0 ] && [ "$completed" -gt 0 ]; then
        echo "[$timestamp] [OK] Processing complete! ($completed/$total images)"
        break
    fi

    sleep $CHECK_INTERVAL
done

echo ""
echo "======================================================================="
echo "MONITORING COMPLETE"
echo "======================================================================="
