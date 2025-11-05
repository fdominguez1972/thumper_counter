#!/bin/bash
# backup_project.sh - Complete backup script for Thumper Counter project
# Run this script to create a full backup of the project

set -e  # Exit on any error

echo "=========================================="
echo "THUMPER COUNTER - BACKUP PROTOCOL"
echo "=========================================="
echo ""

# Set backup timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/mnt/i/backups/thumper_counter_${TIMESTAMP}"

echo "[INFO] Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Step 1: Git commit and tag
echo ""
echo "[STEP 1/6] Committing current work to Git..."
cd /mnt/i/projects/thumper_counter

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "[INFO] Uncommitted changes found, committing..."
    git add -A
    git commit -m "backup: Auto-backup on ${TIMESTAMP}

- Database models complete
- API endpoints partially implemented  
- ML pipeline configured
- 35,234 images ingested
- Documentation and specs updated"
    echo "[OK] Changes committed"
else
    echo "[INFO] No uncommitted changes"
fi

# Create backup tag
git tag -a "backup-${TIMESTAMP}" -m "Backup point: ${TIMESTAMP}"
echo "[OK] Git tag created: backup-${TIMESTAMP}"

# Step 2: Archive project files
echo ""
echo "[STEP 2/6] Archiving project files..."
tar -czf "$BACKUP_DIR/thumper_counter_code.tar.gz" \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.git/objects' \
    --exclude='*.pyc' \
    --exclude='src/models/*.pt' \
    -C /mnt/i/projects thumper_counter

echo "[OK] Code archive created: thumper_counter_code.tar.gz"

# Step 3: Backup models separately (large files)
echo ""
echo "[STEP 3/6] Backing up ML models..."
if [ -d "/mnt/i/projects/thumper_counter/src/models" ]; then
    cp -r /mnt/i/projects/thumper_counter/src/models "$BACKUP_DIR/models_backup"
    echo "[OK] Models backed up"
else
    echo "[SKIP] No models directory found"
fi

# Step 4: Database backup
echo ""
echo "[STEP 4/6] Backing up PostgreSQL database..."
if docker ps | grep -q thumper_db; then
    docker-compose exec -T db pg_dump -U deertrack deer_tracking > "$BACKUP_DIR/database_backup.sql" 2>/dev/null
    if [ -s "$BACKUP_DIR/database_backup.sql" ]; then
        echo "[OK] Database backed up: database_backup.sql"
        echo "     Size: $(du -h "$BACKUP_DIR/database_backup.sql" | cut -f1)"
    else
        echo "[WARN] Database backup may be empty"
    fi
else
    echo "[SKIP] Database container not running"
fi

# Step 5: Docker state
echo ""
echo "[STEP 5/6] Saving Docker configuration..."
docker-compose ps > "$BACKUP_DIR/docker_status.txt" 2>/dev/null
docker images | grep -E "(thumper|^REPOSITORY)" > "$BACKUP_DIR/docker_images.txt" 2>/dev/null
cp /mnt/i/projects/thumper_counter/docker-compose.yml "$BACKUP_DIR/docker-compose.yml.backup"
cp /mnt/i/projects/thumper_counter/.env "$BACKUP_DIR/.env.backup" 2>/dev/null || echo "[WARN] No .env file found"
echo "[OK] Docker configuration saved"

# Step 6: Create restoration script
echo ""
echo "[STEP 6/6] Creating restore script..."
cat > "$BACKUP_DIR/restore.sh" << 'RESTORE_SCRIPT'
#!/bin/bash
# Restore script for Thumper Counter backup

echo "=========================================="
echo "THUMPER COUNTER - RESTORE PROTOCOL"
echo "=========================================="

# Check if running from backup directory
if [ ! -f "thumper_counter_code.tar.gz" ]; then
    echo "[FAIL] Run this script from the backup directory"
    exit 1
fi

echo "[1/4] Restoring project files..."
tar -xzf thumper_counter_code.tar.gz -C /mnt/i/projects/
echo "[OK] Files restored"

echo "[2/4] Restoring models..."
if [ -d "models_backup" ]; then
    cp -r models_backup/* /mnt/i/projects/thumper_counter/src/models/
    echo "[OK] Models restored"
fi

echo "[3/4] Restoring Docker configuration..."
cp docker-compose.yml.backup /mnt/i/projects/thumper_counter/docker-compose.yml
if [ -f ".env.backup" ]; then
    cp .env.backup /mnt/i/projects/thumper_counter/.env
fi
echo "[OK] Configuration restored"

echo "[4/4] Restoring database..."
cd /mnt/i/projects/thumper_counter
docker-compose up -d db
sleep 5
docker-compose exec -T db psql -U deertrack deer_tracking < database_backup.sql
echo "[OK] Database restored"

echo ""
echo "=========================================="
echo "RESTORATION COMPLETE!"
echo "Run 'docker-compose up -d' to start all services"
echo "=========================================="
RESTORE_SCRIPT

chmod +x "$BACKUP_DIR/restore.sh"
echo "[OK] Restore script created"

# Create summary
echo ""
echo "[INFO] Creating backup summary..."
cat > "$BACKUP_DIR/BACKUP_INFO.txt" << EOF
THUMPER COUNTER BACKUP
=====================
Date: $(date)
Location: $BACKUP_DIR
Git Commit: $(git rev-parse HEAD)
Git Branch: $(git branch --show-current)

FILES INCLUDED:
- thumper_counter_code.tar.gz (project code)
- database_backup.sql (PostgreSQL data)
- models_backup/ (ML models)
- docker-compose.yml.backup
- docker_status.txt
- docker_images.txt
- restore.sh (restoration script)

PROJECT STATE:
- Images in database: 35,234
- Locations: 6 (Sanctuary, Hayfield, etc.)
- Models: 4 (Image, Deer, Detection, Location)
- API Endpoints: 8 implemented
- Docker Services: 3 running

KNOWN ISSUES AT BACKUP:
- Backend needs Pillow dependency
- Upload endpoint has filesystem permission issue
- Git on main branch (should be development)

TO RESTORE:
cd $BACKUP_DIR
./restore.sh
EOF

# Final summary
echo ""
echo "=========================================="
echo "BACKUP COMPLETE!"
echo "=========================================="
echo ""
echo "Backup Location: $BACKUP_DIR"
echo ""
echo "Contents:"
ls -lah "$BACKUP_DIR" | tail -n +2
echo ""
echo "Total Size: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo ""
echo "To restore from this backup:"
echo "  cd $BACKUP_DIR"
echo "  ./restore.sh"
echo ""
echo "[OK] Backup protocol complete!"
