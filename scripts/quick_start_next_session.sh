#!/bin/bash
# Quick start script for next session

echo "[INFO] Starting Thumper Counter services..."
cd /mnt/i/projects/thumper_counter

# Start Docker services
docker-compose up -d

# Wait for services
sleep 5

# Check health
echo ""
echo "[INFO] Checking service health..."
curl -s http://localhost:8001/health | python3 -m json.tool

# Show status
echo ""
echo "[INFO] Service status:"
docker-compose ps

# Show remaining tasks
echo ""
echo "[INFO] Sprint 2 remaining tasks:"
echo "1. Fix backend: Add Pillow to requirements.txt"
echo "2. Test upload: curl -F files=@test.jpg http://localhost:8001/api/images"
echo "3. Create Celery task for batch processing"
echo "4. Integrate detection results with database"

echo ""
echo "[OK] Ready to continue development!"
