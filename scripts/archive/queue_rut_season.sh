#!/bin/bash
# Queue rut season images for processing

echo "============================================================"
echo "Queueing Rut Season Images (Sept-Jan)"
echo "============================================================"
echo ""

API_URL="http://localhost:8001"

# Get current status
echo "[INFO] Current status:"
curl -s "${API_URL}/api/processing/status" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"  Pending: {d['pending']}, Completed: {d['completed']}, Total: {d['total']}\")"
echo ""

# Queue 7 batches of 1000 images each
BATCHES=7
BATCH_SIZE=1000
total_queued=0

echo "[INFO] Queueing ${BATCHES} batches of ${BATCH_SIZE} images each..."
echo ""

for i in $(seq 1 $BATCHES); do
    echo -n "Batch ${i}/${BATCHES}... "

    result=$(curl -s -X POST "${API_URL}/api/processing/batch?limit=${BATCH_SIZE}&status=pending" \
        | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('queued_count', 0))" 2>/dev/null)

    if [ "$result" = "0" ] || [ -z "$result" ]; then
        echo "[INFO] No more pending images"
        break
    else
        total_queued=$((total_queued + result))
        echo "[OK] Queued ${result} images (total: ${total_queued})"
        sleep 1
    fi
done

echo ""
echo "[SUCCESS] Queued ${total_queued} images total!"
echo ""
echo "Monitor progress:"
echo "  Frontend: http://localhost:3000"
echo "  API: curl http://localhost:8001/api/processing/status"
echo ""
