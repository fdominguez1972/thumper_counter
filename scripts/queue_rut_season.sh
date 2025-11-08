#!/bin/bash
# Queue September-November images (rut season with hard antlers)

echo "========================================"
echo "Queueing Rut Season Images for Processing"
echo "September, October, November"
echo "========================================"
echo ""

# Get image IDs for Sept-Nov pending images
echo "[INFO] Finding September-November pending images..."

IMAGE_IDS=$(docker-compose exec -T db psql -U deertrack deer_tracking -t -c "
SELECT id 
FROM images 
WHERE EXTRACT(MONTH FROM timestamp) IN (9, 10, 11)
  AND processing_status = 'pending'
ORDER BY timestamp
LIMIT 5000;
" | tr -d ' ' | grep -v '^$')

# Count images
COUNT=$(echo "$IMAGE_IDS" | wc -l)
echo "[OK] Found $COUNT rut season images to process"
echo ""

# Queue in batches of 100
BATCH_SIZE=100
BATCH_NUM=1

echo "$IMAGE_IDS" | while read -r batch; do
  # Collect batch
  BATCH_IDS=""
  for i in $(seq 1 $BATCH_SIZE); do
    read -r id || break
    if [ -n "$id" ]; then
      BATCH_IDS="$BATCH_IDS\"$id\","
    fi
  done <<< "$IMAGE_IDS"
  
  # Remove trailing comma
  BATCH_IDS=$(echo "$BATCH_IDS" | sed 's/,$//')
  
  if [ -n "$BATCH_IDS" ]; then
    echo "[INFO] Queueing batch $BATCH_NUM..."
    
    # Queue batch via API
    curl -s -X POST http://localhost:8001/api/processing/batch \
      -H "Content-Type: application/json" \
      -d "{\"image_ids\": [$BATCH_IDS]}" \
      | python3 -c "import sys, json; d=json.load(sys.stdin); print(f\"  [OK] Queued {d.get('queued_count', 0)} images\")" 2>/dev/null || echo "  [FAIL] Error queueing batch"
    
    BATCH_NUM=$((BATCH_NUM + 1))
    sleep 0.5
  fi
done

echo ""
echo "[INFO] Rut season images queued for processing"
echo "[INFO] Monitor progress: curl http://localhost:8001/api/processing/status"
echo ""
