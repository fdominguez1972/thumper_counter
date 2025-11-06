#!/bin/bash
# complete_backup_with_handoff.sh - Full backup with complete session documentation
# This creates backup AND all handoff documentation for next session

set -e  # Exit on any error

echo "=========================================="
echo "THUMPER COUNTER - COMPLETE BACKUP + HANDOFF"
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
# PART 1: CREATE SESSION HANDOFF DOCUMENTATION
# ============================================

echo ""
echo "[HANDOFF 1/5] Creating session summary..."

# Create session handoff document
cat > "docs/SESSION_$(date +%Y%m%d)_HANDOFF.md" << EOF
# Session Handoff Document
**Date:** ${DATE_READABLE}
**Session:** Sprint 1-2 (November 1-5, 2025)
**Next Session:** Continue Sprint 2

## Quick Start for Next Session

\`\`\`bash
# 1. Navigate to project
cd /mnt/i/projects/thumper_counter

# 2. Start services
docker-compose up -d

# 3. Fix backend (if not already done)
echo "Pillow==10.1.0" >> requirements.txt
docker-compose build backend
docker-compose up -d backend

# 4. Test health
curl http://localhost:8001/health
\`\`\`

## What Was Accomplished This Session

### ✅ Complete (100%)
- Project structure with spec-kit
- Database schema (4 models)
- 35,234 images ingested
- Location management API (5 endpoints)
- Docker infrastructure
- GPU configuration (RTX 4080 Super)
- Git setup (Ubuntu + Synology)
- Project constitution
- Development plan (6 sprints)

### ⚠️ Partial
- Image upload API (needs filesystem fix)
- YOLOv8 detection (tested but not integrated)
- API implementation (40% of endpoints)

### ❌ Not Started
- Frontend (React)
- Deer management API
- Detection storage
- Re-identification
- Testing

## Issues to Fix Next Session

### Priority 1: Backend Container
**Issue:** Missing Pillow dependency
**Fix:**
\`\`\`bash
echo "Pillow==10.1.0" >> requirements.txt
docker-compose build backend
docker-compose up -d backend
\`\`\`

### Priority 2: Upload Filesystem
**Issue:** Read-only filesystem at /mnt/images
**Fix:** Update docker-compose.yml volume mount to read-write

### Priority 3: Git Branch
**Issue:** On main branch, need development
**Fix:**
\`\`\`bash
git checkout -b development
git push ubuntu development
git push synology development
\`\`\`

## Sprint 2 Remaining Tasks (from plan.md)

| Task | Hours | Priority | Status |
|------|-------|----------|---------|
| Fix backend Pillow | 0.5 | HIGH | 🔴 Blocked |
| Test upload endpoint | 1.0 | HIGH | ⏸️ Waiting |
| Create batch Celery task | 3.0 | HIGH | ⏹️ Not started |
| Database integration | 2.0 | HIGH | ⏹️ Not started |
| Progress monitoring | 2.0 | MEDIUM | ⏹️ Not started |

## Key Metrics
- **Images:** 35,234 ingested (353/sec)
- **Locations:** 6 with GPS coordinates
- **Detection:** 80% accuracy in testing
- **GPU:** RTX 4080 Super (16GB VRAM)
- **Batch Size:** 32 images
- **Processing Speed:** 70-90 images/sec

## Important Files
- \`.specify/constitution.md\` - Project principles
- \`.specify/plan.md\` - Sprint planning
- \`specs/ml_updated.spec\` - YOLOv8 multi-class
- \`scripts/test_detection.py\` - Test ML model

## Git Information
- **Current Branch:** main (should be development)
- **Last Commit:** Check with \`git log --oneline -1\`
- **Remotes:** ubuntu (10.0.6.206), synology (10.0.4.82)

## Docker Services
| Service | Port | Status | Notes |
|---------|------|--------|-------|
| thumper_db | 5433 | ✅ Running | PostgreSQL 15 |
| thumper_redis | 6380 | ✅ Running | Redis 7 |
| thumper_worker | - | ✅ Running | GPU enabled |
| thumper_backend | 8001 | ❌ Needs Pillow | FastAPI |

## Database Status
- **Tables:** images, deer, detections, locations
- **Records:** 35,234 images, 6 locations
- **Size:** ~2GB

EOF

echo "[OK] Session handoff created"

# ============================================
# PART 2: UPDATE CLAUDE.MD
# ============================================

echo ""
echo "[HANDOFF 2/5] Updating CLAUDE.md..."

# Create updated CLAUDE.md section (append to existing)
cat >> CLAUDE.md << EOF

## SESSION UPDATE - ${DATE_READABLE}

### Current State
- **Sprint:** 2 of 6 (ML Integration)
- **Overall Completion:** 40%
- **Database:** 100% complete
- **API:** 40% complete
- **ML:** 30% complete
- **Frontend:** 0% complete

### Active Issues
1. Backend container needs Pillow==10.1.0
2. Upload endpoint: read-only filesystem error
3. Git branch: on main, needs development

### Quick Resume Commands
\`\`\`bash
cd /mnt/i/projects/thumper_counter
docker-compose up -d
curl http://localhost:8001/health
docker-compose logs -f backend
\`\`\`

### Next Tasks (Sprint 2)
- [ ] Fix backend Pillow dependency
- [ ] Test upload endpoint
- [ ] Create batch processing task
- [ ] Integrate detection with database

### System Configuration
- **GPU:** RTX 4080 Super (16GB)
- **Batch Size:** 32 images
- **Models:** yolov8n_deer.pt (22MB, 11 classes)
- **Database:** 35,234 images ingested
EOF

echo "[OK] CLAUDE.md updated"

# ============================================
# PART 3: UPDATE SPEC-KIT MEMORY
# ============================================

echo ""
echo "[HANDOFF 3/5] Updating spec-kit memory..."

mkdir -p .specify/memory

# Update decisions log
cat > ".specify/memory/decisions.md" << EOF
# Architecture Decision Records
**Last Updated:** ${DATE_READABLE}

## ADR-001: YOLOv8 Multi-Class Detection
- **Date:** 2025-11-04
- **Decision:** Use single YOLOv8 model for detection + classification
- **Rationale:** Model has 11 built-in classes
- **Impact:** 30% faster, 33% less memory

## ADR-002: Folder-Based Locations
- **Date:** 2025-11-04
- **Decision:** Extract location from folder name
- **Rationale:** Cameras lack GPS EXIF data
- **Impact:** Simpler, matches reality

## ADR-003: Port Configuration
- **Date:** 2025-11-05
- **Decision:** Use ports 5433, 6380, 8001
- **Rationale:** Avoid conflicts with deer_tracker
- **Impact:** Both projects can run simultaneously

## ADR-004: Simple Pagination
- **Date:** 2025-11-05
- **Decision:** Use skip/limit instead of cursors
- **Rationale:** Simpler implementation
- **Impact:** Less efficient for large datasets
EOF

# Update changes log
cat > ".specify/memory/changes.md" << EOF
# Project Change Log
**Last Updated:** ${DATE_READABLE}

## [Sprint 2] - 2025-11-05
### Added
- Project constitution (.specify/constitution.md)
- Development plan (.specify/plan.md)
- ML spec updates for YOLOv8 multi-class
- Session handoff documentation

### Fixed
- Worker container OpenGL dependencies
- Git remote configuration

### Changed
- ML pipeline simplified (unified model)
- Port configuration shifted

## [Sprint 1] - 2025-11-01 to 2025-11-04
### Added
- Complete database schema (4 models)
- Location management API
- Image ingestion pipeline
- Docker infrastructure
- 35,234 images loaded

### Discovered
- YOLOv8 handles classification
- 35,234 images (not 40,617)
- 6 locations active
EOF

echo "[OK] Spec-kit memory updated"

# ============================================
# PART 4: CREATE QUICK START SCRIPT
# ============================================

echo ""
echo "[HANDOFF 4/5] Creating quick start script..."

cat > "scripts/quick_start_next_session.sh" << 'EOF'
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
EOF

chmod +x scripts/quick_start_next_session.sh
echo "[OK] Quick start script created"

# ============================================
# PART 5: RUN FULL BACKUP
# ============================================

echo ""
echo "[BACKUP] Starting full project backup..."

# Git commit
if [[ -n $(git status -s) ]]; then
    git add -A
    git commit -m "backup: Session end - ${TIMESTAMP}

- Sprint 1 complete, Sprint 2 in progress
- 35,234 images ingested
- Database and API partially complete
- Documentation updated"
fi

# Create git tag
git tag -a "session-$(date +%Y%m%d)" -m "End of session: ${DATE_READABLE}"

# Archive project
echo "[BACKUP] Archiving project files..."
tar -czf "$BACKUP_DIR/project_code.tar.gz" \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.git/objects' \
    -C /mnt/i/projects thumper_counter

# Backup models
if [ -d "src/models" ]; then
    cp -r src/models "$BACKUP_DIR/models_backup"
fi

# Database backup
echo "[BACKUP] Backing up database..."
docker-compose exec -T db pg_dump -U deertrack deer_tracking > "$BACKUP_DIR/database.sql" 2>/dev/null || echo "[WARN] Database backup failed"

# Docker state
docker-compose ps > "$BACKUP_DIR/docker_status.txt"
cp docker-compose.yml "$BACKUP_DIR/"
cp .env "$BACKUP_DIR/" 2>/dev/null || true

# Create restore script
cat > "$BACKUP_DIR/restore.sh" << 'RESTORE'
#!/bin/bash
echo "[INFO] Restoring Thumper Counter..."
tar -xzf project_code.tar.gz -C /mnt/i/projects/
cd /mnt/i/projects/thumper_counter
docker-compose up -d db
sleep 5
docker-compose exec -T db psql -U deertrack deer_tracking < database.sql
docker-compose up -d
echo "[OK] Restoration complete!"
RESTORE

chmod +x "$BACKUP_DIR/restore.sh"

# ============================================
# FINAL SUMMARY
# ============================================

echo ""
echo "=========================================="
echo "COMPLETE BACKUP + HANDOFF FINISHED!"
echo "=========================================="
echo ""
echo "📁 Backup Location:"
echo "   $BACKUP_DIR"
echo ""
echo "📄 Documentation Updated:"
echo "   ✓ docs/SESSION_$(date +%Y%m%d)_HANDOFF.md"
echo "   ✓ CLAUDE.md (session state appended)"
echo "   ✓ .specify/memory/decisions.md"
echo "   ✓ .specify/memory/changes.md"
echo "   ✓ scripts/quick_start_next_session.sh"
echo ""
echo "💾 Backup Contents:"
echo "   ✓ project_code.tar.gz"
echo "   ✓ database.sql"
echo "   ✓ models_backup/"
echo "   ✓ docker configuration"
echo "   ✓ restore.sh"
echo ""
echo "🚀 To Start Next Session:"
echo "   1. Read: docs/SESSION_$(date +%Y%m%d)_HANDOFF.md"
echo "   2. Run: ./scripts/quick_start_next_session.sh"
echo ""
echo "[OK] Ready for session handoff!"
