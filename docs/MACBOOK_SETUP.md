# MacBook Pro Setup Guide
## Thumper Counter Development Environment

**Date:** November 14, 2025
**Target:** MacBook Pro (Apple Silicon or Intel)
**User:** pdominguez

---

## Prerequisites

### 1. Install Docker Desktop for Mac
```bash
# Download from: https://www.docker.com/products/docker-desktop

# Verify installation
docker --version
docker-compose --version
```

### 2. Configure Docker Resources
**Docker Desktop → Preferences → Resources:**
- CPUs: 4-6 cores (recommended)
- Memory: 8GB minimum (16GB recommended)
- Disk: 100GB minimum (for images + models)

**IMPORTANT:** MacBook does not support NVIDIA GPUs
- Worker will run on CPU only
- Expect 5-10x slower processing (1-2 images/sec vs 13 images/sec)

---

## Migration Steps

### Step 1: Receive Files from Windows Machine
The Windows machine should have already copied:
- Database backup: `~/thumper_db_backup.sql.gz`
- Trail camera images: `~/Hopkins_Ranch_Trail_Cam_Pics/` (59,185 images)
- ML models: Already in git repo at `src/models/`

**Verify files received:**
```bash
# Check database backup
ls -lh ~/thumper_db_backup.sql.gz

# Check images (should show ~59k files)
find ~/Hopkins_Ranch_Trail_Cam_Pics -type f | wc -l

# Check models
ls -lh ~/thumper_counter/src/models/
```

---

### Step 2: Update Configuration for MacBook

**Edit `.env` file:**
```bash
cd ~/thumper_counter
vi .env
```

**Update these lines:**
```bash
# Change from Windows path to Mac path
IMAGE_PATH=/Users/pdominguez/Hopkins_Ranch_Trail_Cam_Pics

# Reduce batch size for CPU processing
BATCH_SIZE=8  # Reduced from 32 (GPU optimized)

# Consider reducing worker concurrency
NUM_WORKERS=2  # Reduced from 4
```

**Edit `docker-compose.yml`:**
```bash
vi docker-compose.yml
```

**Update volume mounts (lines 78, 127):**
```yaml
# FROM (Windows):
- /mnt/i/Hopkins_Ranch_Trail_Cam_Pics:/mnt/images:ro

# TO (Mac):
- /Users/pdominguez/Hopkins_Ranch_Trail_Cam_Pics:/mnt/images:ro
```

**Remove NVIDIA GPU configuration (lines 140-148):**
```yaml
# Comment out or remove these lines in worker service:
# runtime: nvidia
# deploy:
#   resources:
#     reservations:
#       devices:
#         - driver: nvidia
#           count: 1
#           capabilities: [gpu]
```

---

### Step 3: Build and Start Services

```bash
cd ~/thumper_counter

# Build all services (first time - will take 5-10 minutes)
docker-compose build

# Start database and redis first
docker-compose up -d db redis

# Wait for database to be healthy (30 seconds)
sleep 30

# Import database backup
gunzip -c ~/thumper_db_backup.sql.gz | docker-compose exec -T db psql -U deertrack deer_tracking

# Start remaining services
docker-compose up -d

# Check all services are running
docker-compose ps
```

**Expected output:**
```
NAME                STATUS    PORTS
thumper_backend     Up        0.0.0.0:8001->8000/tcp
thumper_db          Up        0.0.0.0:5433->5432/tcp
thumper_flower      Up        0.0.0.0:5555->5555/tcp
thumper_frontend    Up        0.0.0.0:3000->3000/tcp
thumper_redis       Up        0.0.0.0:6380->6379/tcp
thumper_worker      Up
```

---

### Step 4: Verify Installation

**Test backend API:**
```bash
curl http://localhost:8001/health
# Expected: {"status":"ok","database":"connected","redis":"connected"}
```

**Test frontend:**
```bash
open http://localhost:3000
# Should show Dashboard with deer statistics
```

**Check database:**
```bash
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT COUNT(*) as images,
   COUNT(CASE WHEN processing_status='completed' THEN 1 END) as completed,
   COUNT(CASE WHEN processing_status='pending' THEN 1 END) as pending
   FROM images;"
```

**Test worker (CPU processing):**
```bash
# Queue a small batch to test CPU processing
curl -X POST "http://localhost:8001/api/processing/batch?limit=10"

# Watch worker logs
docker-compose logs -f worker

# Expected: Detection tasks completing (slower than GPU)
```

---

## Performance Expectations

### GPU (Windows RTX 4080 Super)
- Detection: 0.04s per image
- Re-ID: 0.005s per image
- Throughput: 13-15 images/second
- Batch size: 32

### CPU (MacBook Pro)
- Detection: 0.2-0.4s per image (5-10x slower)
- Re-ID: 0.05-0.1s per image (10-20x slower)
- Throughput: 1-2 images/second
- Batch size: 8 (reduced)

**Full dataset processing:**
- GPU: ~8 hours (Windows)
- CPU: ~40-80 hours (MacBook) - DO NOT process full dataset on Mac!

**Recommendation:** Use MacBook for development only, not batch processing

---

## Development Workflow on MacBook

### Daily Commands
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f frontend

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build backend worker frontend
```

### Frontend Development
```bash
# Hot reload is enabled - edit files in frontend/src/
# Changes auto-refresh at http://localhost:3000
cd frontend/src/pages
vi Dashboard.tsx  # Edit, save, see changes immediately
```

### Backend Development
```bash
# Edit backend files
cd src/backend/api
vi deer.py

# Rebuild backend
docker-compose up -d --build backend

# Or restart without rebuild
docker-compose restart backend
```

### Database Access
```bash
# PostgreSQL command line
docker-compose exec db psql -U deertrack deer_tracking

# Common queries
SELECT sex, COUNT(*) FROM deer GROUP BY sex;
SELECT processing_status, COUNT(*) FROM images GROUP BY processing_status;
```

---

## Troubleshooting

### Frontend doesn't build
**Issue:** Only backend and worker containers built

**Solution:**
```bash
# Ensure frontend Dockerfile exists
ls -l docker/dockerfiles/Dockerfile.frontend.dev

# Explicitly build frontend
docker-compose build frontend

# Check for errors
docker-compose logs frontend
```

### Images not found errors
**Issue:** Volume mount path incorrect

**Solution:**
```bash
# Verify images exist
ls ~/Hopkins_Ranch_Trail_Cam_Pics | head

# Check volume mount in docker-compose.yml
grep "Hopkins_Ranch" docker-compose.yml

# Should show Mac path, not Windows path:
# - /Users/pdominguez/Hopkins_Ranch_Trail_Cam_Pics:/mnt/images:ro
```

### Worker crashes or slow performance
**Issue:** CPU processing limitations

**Solutions:**
1. Reduce batch size in .env: `BATCH_SIZE=4`
2. Reduce workers: `NUM_WORKERS=1`
3. Process smaller batches: `curl -X POST "http://localhost:8001/api/processing/batch?limit=100"`
4. Use Windows machine for large batch processing

### Database connection errors
**Issue:** Port conflicts or service not ready

**Solutions:**
```bash
# Check if port 5433 is available
lsof -i :5433

# Restart database
docker-compose restart db

# Wait for healthy status
docker-compose exec db pg_isready -U deertrack -d deer_tracking
```

---

## What's Different on MacBook vs Windows

| Feature | Windows (WSL2 + RTX 4080) | MacBook Pro |
|---------|---------------------------|-------------|
| GPU Support | Yes (NVIDIA CUDA) | No |
| Processing Speed | 13 images/sec | 1-2 images/sec |
| Batch Size | 32 | 8 |
| Full Dataset Time | 8 hours | 40-80 hours |
| Docker Runtime | nvidia | default |
| Path Format | /mnt/i/... | /Users/... |
| Use Case | Production processing | Development only |

---

## Recommended Setup

**Best Practice:**
1. **MacBook:** Frontend + backend development
2. **Windows:** ML model training, batch processing
3. **Sync:** Git push/pull for code changes
4. **Database:** Periodic exports from Windows → import to Mac

**Development Cycle:**
```
MacBook: Edit frontend/backend code → Test locally
         ↓
       Git commit + push
         ↓
Windows: Git pull → Run batch processing → Export database
         ↓
MacBook: Import database → Continue development
```

---

## File Locations Reference

### MacBook Paths
- Project: `~/thumper_counter/`
- Images: `~/Hopkins_Ranch_Trail_Cam_Pics/`
- Database backup: `~/thumper_db_backup.sql.gz`
- Uploads: `~/thumper_counter/data/uploads/`
- Models: `~/thumper_counter/src/models/`

### Container Paths
- Images: `/mnt/images` (read-only)
- Uploads: `/mnt/uploads` (read-write)
- Models: `/app/models`
- Exports: `/mnt/exports`

### URLs
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs
- Flower (Celery): http://localhost:5555

---

## Next Steps

1. Complete migration using `migrate_to_macbook.sh` on Windows
2. Follow this setup guide on MacBook
3. Verify all services running
4. Test frontend development workflow
5. Use MacBook for UI/API development
6. Use Windows for batch processing
7. Sync code via git regularly

---

## Support

**Documentation:**
- Main README: `README.md`
- Session handoffs: `docs/SESSION_*.md`
- Code audit: `docs/CODE_AUDIT_2025-11-12.md`

**Common Issues:**
- Check docker-compose logs: `docker-compose logs <service>`
- Verify health: `curl http://localhost:8001/health`
- Database status: See "Database Access" section above
