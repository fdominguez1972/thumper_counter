#!/bin/bash
#
# Quick Backup Script for Thumper Counter
# Backs up code, configs, and database only (excludes large model files and images)
#

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/mnt/i/backups/thumper_counter_${TIMESTAMP}"

echo "==========================================
"
echo "THUMPER COUNTER - QUICK BACKUP"
echo "==========================================
"
echo ""

# Create backup directory
echo "[INFO] Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Git commit (if changes exist)
echo "[INFO] Checking for uncommitted changes..."
cd /mnt/i/projects/thumper_counter

if [[ -n $(git status -s) ]]; then
    echo "[WARN] Uncommitted changes found. Committing first..."
    git add -A
    git commit -m "backup: Session end - ${TIMESTAMP}"
fi

# Archive project (exclude large files)
echo "[BACKUP] Archiving project files (excluding models, images, node_modules)..."
tar -czf "$BACKUP_DIR/project_code.tar.gz" \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='src/models/*.pt' \
    --exclude='src/models/runs' \
    --exclude='frontend/dist' \
    --exclude='frontend/node_modules' \
    --exclude='.pytest_cache' \
    --exclude='.vscode' \
    .

echo "[OK] Project archived: $(du -h "$BACKUP_DIR/project_code.tar.gz" | cut -f1)"

# Backup database
echo "[BACKUP] Backing up database..."
docker-compose exec -T db pg_dump -U deertrack deer_tracking > "$BACKUP_DIR/database.sql" 2>/dev/null && \
    echo "[OK] Database backup complete: $(du -h "$BACKUP_DIR/database.sql" | cut -f1)" || \
    echo "[WARN] Database backup failed (is database running?)"

# Docker state
echo "[BACKUP] Saving Docker state..."
docker-compose ps > "$BACKUP_DIR/docker_status.txt" 2>/dev/null || echo "[WARN] Could not capture Docker status"
cp docker-compose.yml "$BACKUP_DIR/" 2>/dev/null || true
cp .env "$BACKUP_DIR/env_backup.txt" 2>/dev/null || true

# Copy key documentation
echo "[BACKUP] Copying documentation..."
mkdir -p "$BACKUP_DIR/docs"
cp docs/SESSION_* "$BACKUP_DIR/docs/" 2>/dev/null || true
cp CLAUDE.md "$BACKUP_DIR/" 2>/dev/null || true
cp README.md "$BACKUP_DIR/" 2>/dev/null || true

# Create inventory
echo "[BACKUP] Creating backup inventory..."
cat > "$BACKUP_DIR/BACKUP_INFO.txt" << EOF
THUMPER COUNTER BACKUP
=====================

Timestamp: $TIMESTAMP
Date: $(date)
Branch: $(git branch --show-current 2>/dev/null || echo "unknown")
Commit: $(git log -1 --oneline 2>/dev/null || echo "unknown")

Contents:
- project_code.tar.gz: Source code (excludes models, images, node_modules)
- database.sql: PostgreSQL dump
- docker_status.txt: Container status
- docker-compose.yml: Service configuration
- env_backup.txt: Environment variables
- docs/: Session handoff documents
- CLAUDE.md: Development guide

To Restore:
1. Extract: tar -xzf project_code.tar.gz -C /desired/location
2. Restore DB: docker-compose exec -T db psql -U deertrack deer_tracking < database.sql
3. Review docker-compose.yml and .env for any needed changes
4. Run: docker-compose up -d

Notes:
- Model files (.pt) not included - download separately if needed
- Training data not included
- Image files not included - stored separately at /mnt/i/Hopkins_Ranch_Trail_Cam_Pics
EOF

echo "[OK] Backup inventory created"

# Summary
echo ""
echo "=========================================="
echo "BACKUP COMPLETE"
echo "=========================================="
echo "Location: $BACKUP_DIR"
echo "Size: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo ""
echo "Contents:"
ls -lh "$BACKUP_DIR"
echo ""
echo "[OK] Backup successful!"
