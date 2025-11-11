#!/bin/bash
# backup_with_handoff.sh - Complete backup with session handoff documentation
# Creates database dump, code archive, and documentation for next session

set -e  # Exit on any error

echo "=========================================="
echo "THUMPER COUNTER - BACKUP + HANDOFF"
echo "=========================================="
echo ""

# Set timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE_READABLE=$(date +"%B %d, %Y at %H:%M")
BACKUP_DIR="/mnt/i/backups/thumper_counter_${TIMESTAMP}"

echo "[INFO] Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Navigate to project
cd /mnt/i/projects/thumper_counter

# ============================================
# PART 1: GIT INFORMATION
# ============================================

echo ""
echo "[1/5] Collecting git information..."

git log --oneline -10 > "$BACKUP_DIR/recent_commits.txt"
git status > "$BACKUP_DIR/git_status.txt"
git branch -v > "$BACKUP_DIR/branches.txt"

echo "[OK] Git info saved"

# ============================================
# PART 2: DATABASE BACKUP
# ============================================

echo ""
echo "[2/5] Backing up database..."

# Dump database
docker-compose exec -T db pg_dump -U deertrack deer_tracking > "$BACKUP_DIR/database_dump.sql"

# Get database stats
docker-compose exec -T db psql -U deertrack deer_tracking -c "
SELECT
    'images' as table_name, COUNT(*) as row_count
FROM images
UNION ALL
SELECT 'detections', COUNT(*) FROM detections
UNION ALL
SELECT 'deer', COUNT(*) FROM deer
UNION ALL
SELECT 'locations', COUNT(*) FROM locations;
" > "$BACKUP_DIR/database_stats.txt"

echo "[OK] Database backup complete"

# ============================================
# PART 3: CODE ARCHIVE
# ============================================

echo ""
echo "[3/5] Creating code archive..."

# Archive source code (exclude node_modules, __pycache__, etc.)
tar -czf "$BACKUP_DIR/source_code.tar.gz" \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='build' \
    --exclude='dist' \
    src/ frontend/ migrations/ docker/ docker-compose.yml requirements.txt

# Archive documentation
tar -czf "$BACKUP_DIR/documentation.tar.gz" \
    docs/ specs/ CLAUDE.md README.md

# Archive scripts
tar -czf "$BACKUP_DIR/scripts.tar.gz" scripts/

echo "[OK] Code archives created"

# ============================================
# PART 4: SYSTEM STATE
# ============================================

echo ""
echo "[4/5] Capturing system state..."

# Docker container status
docker-compose ps > "$BACKUP_DIR/docker_status.txt"

# Running services
docker-compose logs --tail=50 backend > "$BACKUP_DIR/backend_logs.txt" 2>&1
docker-compose logs --tail=50 worker > "$BACKUP_DIR/worker_logs.txt" 2>&1
docker-compose logs --tail=50 frontend > "$BACKUP_DIR/frontend_logs.txt" 2>&1

# API health check
curl -s http://localhost:8001/health > "$BACKUP_DIR/api_health.json" 2>&1 || echo "API not responding" > "$BACKUP_DIR/api_health.json"

# Processing stats
curl -s http://localhost:8001/api/processing/status > "$BACKUP_DIR/processing_stats.json" 2>&1 || echo "Stats not available" > "$BACKUP_DIR/processing_stats.json"

# Species stats
curl -s http://localhost:8001/api/deer/stats/species > "$BACKUP_DIR/species_stats.json" 2>&1 || echo "Species stats not available" > "$BACKUP_DIR/species_stats.json"

echo "[OK] System state captured"

# ============================================
# PART 5: COPY SESSION HANDOFF
# ============================================

echo ""
echo "[5/5] Copying session handoff document..."

# Copy the session handoff document
if [ -f "docs/SESSION_$(date +%Y%m%d)_HANDOFF.md" ]; then
    cp "docs/SESSION_$(date +%Y%m%d)_HANDOFF.md" "$BACKUP_DIR/SESSION_HANDOFF.md"
    echo "[OK] Session handoff copied"
else
    echo "[WARN] No session handoff found for today"
fi

# Create backup manifest
cat > "$BACKUP_DIR/MANIFEST.txt" << EOF
THUMPER COUNTER BACKUP
======================
Created: $DATE_READABLE
Backup ID: $TIMESTAMP

Contents:
---------
1. Database Dump: database_dump.sql
2. Database Stats: database_stats.txt
3. Source Code: source_code.tar.gz
4. Documentation: documentation.tar.gz
5. Scripts: scripts.tar.gz
6. Docker Status: docker_status.txt
7. Service Logs: backend_logs.txt, worker_logs.txt, frontend_logs.txt
8. API Health: api_health.json
9. Processing Stats: processing_stats.json
10. Species Stats: species_stats.json
11. Session Handoff: SESSION_HANDOFF.md
12. Git Info: recent_commits.txt, git_status.txt, branches.txt

Restore Instructions:
--------------------
1. Extract source code: tar -xzf source_code.tar.gz
2. Restore database: psql -U deertrack deer_tracking < database_dump.sql
3. Review SESSION_HANDOFF.md for session context
4. Start services: docker-compose up -d

Git Status:
-----------
$(cat $BACKUP_DIR/git_status.txt)

Last Commits:
-------------
$(cat $BACKUP_DIR/recent_commits.txt)
EOF

# Create summary
cat > "$BACKUP_DIR/README.txt" << EOF
BACKUP SUMMARY
==============

This backup contains a complete snapshot of the Thumper Counter project
as of $DATE_READABLE.

Key Files:
- SESSION_HANDOFF.md - Start here! Contains session summary and next steps
- MANIFEST.txt - Complete list of backup contents
- database_dump.sql - Full PostgreSQL database dump
- source_code.tar.gz - All application code
- documentation.tar.gz - All documentation and specs

Quick Restore:
1. Read SESSION_HANDOFF.md
2. Extract: tar -xzf source_code.tar.gz
3. Restore DB: docker-compose up -d db && sleep 5
4. Import: docker-compose exec -T db psql -U deertrack deer_tracking < database_dump.sql
5. Start: docker-compose up -d

For detailed instructions, see MANIFEST.txt
EOF

# ============================================
# SUMMARY
# ============================================

echo ""
echo "=========================================="
echo "BACKUP COMPLETE!"
echo "=========================================="
echo ""
echo "Backup Location: $BACKUP_DIR"
echo ""
echo "Backup Contents:"
echo "  - Database dump ($(du -h "$BACKUP_DIR/database_dump.sql" | cut -f1))"
echo "  - Source code archive"
echo "  - Documentation archive"
echo "  - Scripts archive"
echo "  - System state snapshots"
echo "  - Session handoff document"
echo ""
echo "To restore this backup:"
echo "  1. cd /mnt/i/projects/thumper_counter"
echo "  2. Read $BACKUP_DIR/SESSION_HANDOFF.md"
echo "  3. Follow restore instructions in $BACKUP_DIR/MANIFEST.txt"
echo ""
echo "[OK] Ready for session handoff!"
echo ""
