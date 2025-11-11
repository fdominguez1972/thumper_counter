#!/bin/bash
# Monitor processing progress with periodic updates

API_URL="http://localhost:8001"
CHECK_INTERVAL=120  # Check every 2 minutes

echo "============================================================"
echo "Processing Monitor - Checking every ${CHECK_INTERVAL}s"
echo "============================================================"
echo ""

# Get initial state
initial=$(curl -s "${API_URL}/api/processing/status")
initial_completed=$(echo $initial | python3 -c "import sys, json; print(json.load(sys.stdin)['completed'])")
start_time=$(date +%s)

echo "[$(date '+%H:%M:%S')] Starting monitor..."
echo "Initial: $initial_completed images completed"
echo ""

iteration=1

while true; do
    sleep $CHECK_INTERVAL

    current=$(curl -s "${API_URL}/api/processing/status")
    completed=$(echo $current | python3 -c "import sys, json; print(json.load(sys.stdin)['completed'])")
    pending=$(echo $current | python3 -c "import sys, json; print(json.load(sys.stdin)['pending'])")
    total=$(echo $current | python3 -c "import sys, json; print(json.load(sys.stdin)['total'])")
    completion_rate=$(echo $current | python3 -c "import sys, json; print(json.load(sys.stdin)['completion_rate'])")

    # Calculate progress since start
    processed=$((completed - initial_completed))
    elapsed=$(($(date +%s) - start_time))
    elapsed_min=$((elapsed / 60))

    # Calculate rate
    if [ $elapsed -gt 0 ]; then
        rate_per_min=$((processed * 60 / elapsed))
        rate_per_sec=$(echo "scale=1; $processed / $elapsed" | bc)
    else
        rate_per_min=0
        rate_per_sec=0
    fi

    # Calculate ETA
    if [ $rate_per_min -gt 0 ]; then
        eta_min=$((pending / rate_per_min))
        eta_hours=$(echo "scale=1; $eta_min / 60" | bc)
    else
        eta_min=999
        eta_hours=99
    fi

    echo "[$(date '+%H:%M:%S')] Update #$iteration (${elapsed_min}m elapsed):"
    echo "  Completed: $completed/$total ($completion_rate%)"
    echo "  Pending: $pending"
    echo "  Processed since start: $processed images"
    echo "  Current rate: ${rate_per_sec}/sec (~${rate_per_min}/min)"

    if [ $rate_per_min -gt 0 ]; then
        echo "  ETA: ${eta_hours}h (${eta_min} minutes)"
    fi
    echo ""

    # Stop if no pending images
    if [ "$pending" -eq "0" ]; then
        echo "[OK] All images processed!"
        break
    fi

    iteration=$((iteration + 1))
done

echo ""
echo "Monitor stopped at $(date '+%H:%M:%S')"
echo "Total processed: $processed images in ${elapsed_min} minutes"
