#!/bin/bash
# Migration script: Windows WSL2 → MacBook Pro
# Run this script on the Windows machine

set -e

MACBOOK_USER="pdominguez"
MACBOOK_HOST="10.0.6.107"
PROJECT_PATH="/mnt/i/projects/thumper_counter"
IMAGES_PATH="/mnt/i/Hopkins_Ranch_Trail_Cam_Pics"

echo "[INFO] Thumper Counter Migration to MacBook"
echo "=========================================="

# Step 1: Create database backup
echo ""
echo "[STEP 1] Creating database backup..."
docker-compose exec -T db pg_dump -U deertrack deer_tracking | gzip > /tmp/thumper_db_backup.sql.gz
echo "[OK] Database backup created: /tmp/thumper_db_backup.sql.gz"
echo "    Size: $(du -h /tmp/thumper_db_backup.sql.gz | cut -f1)"

# Step 2: Copy database backup to MacBook
echo ""
echo "[STEP 2] Copying database backup to MacBook..."
scp /tmp/thumper_db_backup.sql.gz ${MACBOOK_USER}@${MACBOOK_HOST}:~/ai_projects/thumper_counter/thumper_db_backup.sql.gz
echo "[OK] Database backup copied to MacBook:~/thumper_db_backup.sql.gz"

# Step 3: Copy ML models
echo ""
echo "[STEP 3] Copying ML models to MacBook..."
rsync -avz --progress \
  ${PROJECT_PATH}/src/models/ \
  ${MACBOOK_USER}@${MACBOOK_HOST}:~/ai_projects/thumper_counter/thumper_counter/src/models/
echo "[OK] ML models copied"

# Step 4: Copy images (LARGE - this will take time)
echo ""
echo "[STEP 4] Copying trail camera images to MacBook..."
echo "[WARN] This will transfer ~59,000 images - may take 30-60 minutes"
read -p "Continue? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rsync -avz --progress \
      ${IMAGES_PATH}/ \
      ${MACBOOK_USER}@${MACBOOK_HOST}:~/ai_projects/thumper_counter/Hopkins_Ranch_Trail_Cam_Pics/
    echo "[OK] Images copied"
else
    echo "[SKIP] Image copy skipped - you can run this later:"
    echo "  rsync -avz --progress ${IMAGES_PATH}/ ${MACBOOK_USER}@${MACBOOK_HOST}:~/ai_projects/thumper_counter/Hopkins_Ranch_Trail_Cam_Pics/"
fi

# Step 5: Summary
echo ""
echo "=========================================="
echo "[OK] Migration preparation complete!"
echo ""
echo "Next steps ON MACBOOK:"
echo "  1. cd ~/thumper_counter"
echo "  2. Update .env file with MacBook paths"
echo "  3. Import database: cat ~/thumper_db_backup.sql.gz | gunzip | docker-compose exec -T db psql -U deertrack deer_tracking"
echo "  4. Start services: docker-compose up -d"
echo ""
echo "IMPORTANT: MacBook needs Docker Desktop installed (no NVIDIA GPU support)"
echo "Worker will run on CPU only - expect slower processing"
