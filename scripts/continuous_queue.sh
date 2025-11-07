#!/bin/bash
# Continuous queuing script - keeps queue fed until all images processed
# Usage: bash scripts/continuous_queue.sh

echo "[INFO] Starting continuous queuing..."
echo ""

total_queued=0

while true; do
    # Get pending count
    pending=$(curl -s http://localhost:8001/api/processing/status | python3 -c "import sys, json; print(json.load(sys.stdin)['pending'])" 2>/dev/null)

    if [ -z "$pending" ] || [ "$pending" = "0" ]; then
        echo ""
        echo "[OK] All images processed! Total queued: $total_queued"
        break
    fi

    # Queue 1000 tasks (limit as query parameter, not body)
    result=$(curl -s -X POST "http://localhost:8001/api/processing/batch?limit=1000" \
        | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['queued_count'])" 2>/dev/null)

    if [ "$result" = "0" ] || [ -z "$result" ]; then
        echo "[WARN] No tasks queued, waiting..."
        sleep 5
    else
        total_queued=$((total_queued + result))
        echo "[OK] Queued $result tasks (total: $total_queued, pending: $pending)"
        sleep 2
    fi
done

echo ""
echo "Monitor final results with:"
echo "  curl http://localhost:8001/api/processing/status"
