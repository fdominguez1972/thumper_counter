#!/bin/bash
# Queue all remaining images for processing
# Sprint 8-9: Batch processing

echo "[INFO] Queuing all remaining pending images..."
echo ""

total_queued=0

for i in {1..25}; do
    result=$(curl -s -X POST http://localhost:8001/api/processing/batch \
        -H "Content-Type: application/json" \
        -d '{"limit": 1000}' | python3 -c "import sys, json; d=json.load(sys.stdin); print(d['queued_count'])" 2>/dev/null)

    if [ "$result" = "0" ] || [ -z "$result" ]; then
        echo "[INFO] No more pending images. Stopping."
        break
    fi

    total_queued=$((total_queued + result))
    echo "[OK] Batch $i: Queued $result tasks (total: $total_queued)"
    sleep 1
done

echo ""
echo "[OK] Finished! Total queued: $total_queued tasks"
echo ""
echo "Monitor progress with:"
echo "  curl http://localhost:8001/api/processing/status"
