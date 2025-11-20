# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## PROJECT: Thumper Counter - Deer Tracking ML Pipeline

**Production System:** Wildlife monitoring with automated deer identification
**Tech Stack:** FastAPI, React, PostgreSQL, Celery, PyTorch, Docker
**Hardware:** RTX 4080 Super (16GB VRAM), WSL2 + Docker Desktop
**Status:** ACTIVE - Processing 59,185 images

---

## SESSION HANDOFF - AUTOMATED CATCHUP

**IMPORTANT:** Start every new session by reading the latest session handoff document.

### Quick Start Commands
```bash
# 1. Find latest session document
ls -lt docs/SESSION_*.md | head -3

# 2. Read most recent handoff
cat docs/SESSION_20251115_REID_CUDA_FIX.md

# 3. Check system status
docker-compose ps
curl -s http://localhost:8001/api/processing/status | python3 -m json.tool

# 4. Check database state
docker-compose exec -T db psql -U deertrack deer_tracking -c \
  "SELECT processing_status, COUNT(*) FROM images GROUP BY processing_status;"
```

### Recent Session Documents
- `SESSION_20251115_REID_CUDA_FIX.md` - CUDA device mismatch fix + threshold optimization
- `SESSION_20251115_FEATURE_012_COMPLETE.md` - Bulk image upload with ZIP extraction
- `SESSION_20251115_REPROCESSING.md` - Re-ID threshold analysis
- `SESSION_20251112_CRITICAL_FIXES.md` - Sex mapping bug fix
- Full list: `ls docs/SESSION_*.md`

---

## USER PREFERENCES (CRITICAL)

### ASCII-ONLY OUTPUT (HIGHEST PRIORITY)
**ALL output must use ASCII characters only**

**FORBIDDEN:**
- Unicode characters (✓, ✗, →, etc.)
- Emojis (🦌, 🎉, ✅, etc.)
- Smart quotes (" " ' ')
- Special dashes (— –)
- Box-drawing characters (│ ─ ┌)

**ALLOWED:**
- Status indicators: [OK], [FAIL], [WARN], [INFO]
- ASCII borders: =, -, *, #
- ALL CAPS for emphasis

### User Profile
- **Skill Level:** Advanced (catches bugs, reviews code)
- **Platform:** Windows 10/11, Docker Desktop, WSL2
- **Editor:** vi
- **Workflow:** Turbo mode (parallel operations), one-step approval
- **Preference:** Comprehensive docs, understand WHY not just WHAT

---

## SYSTEM ARCHITECTURE

### Three-Tier ML Pipeline
```
1. API Layer (FastAPI) - port 8001
   - Image upload (individual + ZIP archives up to 2GB)
   - Processing queue management
   - Detection/Re-ID results API

2. Worker Layer (Celery) - 32 threads
   - YOLOv8n deer detection (11 classes)
   - Enhanced Re-ID (ResNet50 + multi-scale + EfficientNet ensemble)
   - GPU-accelerated (CUDA)

3. Data Layer
   - PostgreSQL 15 + pgvector (similarity search)
   - Redis (Celery queue)
   - Filesystem (images + crops)
```

### ML Models
- **Detection:** YOLOv8n (11 classes: buck, doe, fawn, cattle, pig, etc.)
- **Re-ID Primary:** ResNet50 (512-dim embeddings)
- **Re-ID Multi-scale:** ResNet50 with layer2/3/4/avgpool fusion
- **Re-ID Ensemble:** EfficientNet-B0 for architectural diversity
- **Similarity:** Cosine distance with pgvector HNSW index
- **Threshold:** REID_THRESHOLD=0.50 (optimized from 0.60)

---

## CRITICAL COMMANDS

### System Health
```bash
# Check all services
docker-compose ps

# API health
curl http://localhost:8001/health

# Processing status
curl -s http://localhost:8001/api/processing/status | python3 -m json.tool

# Worker logs
docker-compose logs -f worker --tail=50

# Queue depth
docker-compose exec redis redis-cli LLEN ml_processing
```

### Database Queries
```bash
# Processing breakdown
docker-compose exec -T db psql -U deertrack deer_tracking -c \
  "SELECT processing_status, COUNT(*) FROM images GROUP BY processing_status;"

# Deer profiles
docker-compose exec -T db psql -U deertrack deer_tracking -c \
  "SELECT sex, COUNT(*) FROM deer GROUP BY sex;"

# Re-ID assignment rate
docker-compose exec -T db psql -U deertrack deer_tracking -c \
  "SELECT COUNT(*) * 100.0 / (SELECT COUNT(*) FROM detections WHERE classification IN ('buck','doe','fawn')) as assignment_rate FROM detections WHERE deer_id IS NOT NULL;"
```

### Docker Operations
```bash
# Start system
docker-compose up -d

# Restart worker (after model changes)
docker-compose restart worker

# Rebuild containers
docker-compose up -d --build

# Complete restart
docker-compose down && docker-compose up -d

# GPU check
docker-compose exec worker nvidia-smi
```

### Git Workflow
```bash
# Status
git status
git log --oneline -10

# Commit
git add -A
git commit -m "message"

# Push to both remotes
git push origin main && git push ubuntu main
```

---

## CURRENT SYSTEM STATE

### Database Statistics (as of Nov 15, 2025)
```
Total Images: 59,185
  - Completed: 35,279 (59.6%)
  - Pending: 23,288
  - Processing: 30
  - Failed: 588

Total Detections: ~40,000+
Deer Profiles: 116 (in progress - threshold optimization)
```

### Configuration
```yaml
# Key Environment Variables (.env)
REID_THRESHOLD: 0.50              # Optimized from 0.60
CONFIDENCE_THRESHOLD: 0.4         # YOLOv8 detection confidence
BATCH_SIZE: 16                    # Images per GPU batch
USE_ENHANCED_REID: true           # Multi-scale + ensemble
ENSEMBLE_WEIGHT_RESNET: 0.6       # Primary model weight
ENSEMBLE_WEIGHT_EFFICIENTNET: 0.4 # Ensemble diversity weight

# Worker Configuration (docker-compose.yml)
Concurrency: 32 threads           # Optimized for RTX 4080 Super
Queue: ml_processing
GPU: nvidia runtime, 8GB shared memory
```

### Performance Metrics
```
Detection Throughput: 840 images/min
Re-ID Processing: 10-15 detections/sec
GPU Utilization: 31% (optimal, no contention)
Bottleneck: Database writes (70% of time)
```

---

## DEVELOPMENT PATTERNS

### Adding API Endpoint
```python
# 1. Define schema (src/backend/schemas/)
class NewRequest(BaseModel):
    field: str

# 2. Create endpoint (src/backend/api/)
@router.post("/new")
async def create_new(request: NewRequest):
    # Business logic
    return {"status": "success"}

# 3. Register in main.py
app.include_router(router, prefix="/api", tags=["new"])
```

### Adding Celery Task
```python
# 1. Create task (src/worker/tasks/)
from worker.celery_app import celery_app

@celery_app.task(name="worker.tasks.new_task")
def new_task(param):
    # Task logic
    return result

# 2. Register in celery_app.py
imports = [
    'worker.tasks.new_task',
]

# 3. Queue task
from worker.tasks.new_task import new_task
new_task.apply_async(args=[value], queue='ml_processing')
```

### Database Schema Changes
```bash
# 1. Create migration SQL
vi migrations/NNN_description.sql

# 2. Run migration
docker-compose exec -T db psql -U deertrack deer_tracking < migrations/NNN_description.sql

# 3. Update models (src/backend/models/)
# Add/modify SQLAlchemy model classes
```

### Frontend Component
```tsx
// 1. Create component (frontend/src/components/)
export const NewComponent: React.FC<Props> = ({ data }) => {
  return <Box>...</Box>;
};

// 2. Import in page
import { NewComponent } from '../components/NewComponent';

// 3. Use with React Query
const { data } = useQuery(['key'], () => api.getData());
```

---

## TROUBLESHOOTING

### Worker Not Processing
```bash
# Check worker status
docker-compose logs worker --tail=100

# Restart worker
docker-compose restart worker

# Wait for models to load (30s)
sleep 30 && docker-compose logs worker | grep "loaded on cuda"
```

### Queue Stuck (Pending but Not Processing)
```bash
# Check queue depth
docker-compose exec redis redis-cli LLEN ml_processing

# If 0, manually queue images
curl -X POST "http://localhost:8001/api/processing/batch?limit=10000"

# Or start continuous queue monitor
nohup ./scripts/continuous_queue.sh > queue_monitor.log 2>&1 &
```

### CUDA Errors
```bash
# Verify GPU accessible
docker-compose exec worker nvidia-smi

# Check model loading
docker-compose logs worker | grep -E "loaded on cuda|ERROR"

# Common fix: Restart worker
docker-compose restart worker
```

### High Failure Rate
```bash
# Check error messages
docker-compose exec -T db psql -U deertrack deer_tracking -c \
  "SELECT error_message, COUNT(*) FROM images WHERE processing_status='failed' GROUP BY error_message LIMIT 10;"

# Reset failed to pending (if transient errors)
docker-compose exec -T db psql -U deertrack deer_tracking -c \
  "UPDATE images SET processing_status='pending', error_message=NULL WHERE processing_status='failed';"
```

---

## IMPORTANT FILES

### Configuration
- `.env` - Environment variables (DB, API, ML config)
- `docker-compose.yml` - Service orchestration
- `requirements.txt` - Python dependencies

### Backend
- `src/backend/app/main.py` - FastAPI app entry
- `src/backend/api/*.py` - API endpoints
- `src/backend/models/*.py` - SQLAlchemy models
- `src/backend/schemas/*.py` - Pydantic schemas

### Worker
- `src/worker/celery_app.py` - Celery configuration
- `src/worker/tasks/detection.py` - YOLOv8 detection
- `src/worker/tasks/reidentification.py` - Enhanced Re-ID
- `src/worker/models/*.py` - ML model loaders

### Frontend
- `frontend/src/App.tsx` - React router
- `frontend/src/pages/*.tsx` - Page components
- `frontend/src/components/*.tsx` - Reusable components
- `frontend/src/api/*.ts` - API client functions

### Database
- `migrations/*.sql` - Schema migrations
- `src/backend/models/` - SQLAlchemy ORM models

### Scripts
- `scripts/queue_all_reid.py` - Batch Re-ID processing
- `scripts/analyze_reid_threshold.py` - Threshold optimization analysis
- `scripts/continuous_queue.sh` - Auto-queue monitor

### Documentation
- `docs/SESSION_*.md` - Session handoff documents
- `docs/OPERATIONS_RUNBOOK.md` - Operational procedures
- `docs/REID_THRESHOLD_OPTIMIZATION_GUIDE.md` - Threshold tuning
- `.specify/memory/changes.md` - Project changelog
- `.specify/memory/decisions.md` - Architecture decisions

---

## ACTIVE TECHNOLOGIES

**Backend:**
- Python 3.11
- FastAPI 0.100+
- SQLAlchemy 2.x
- PostgreSQL 15 + pgvector
- Celery 5.x
- Redis 7

**ML Stack:**
- PyTorch 2.x
- torchvision (models: ResNet50, EfficientNet-B0)
- Ultralytics YOLOv8
- CUDA 11.8+ (RTX 4080 Super)

**Frontend:**
- React 18
- TypeScript 5.x
- Material-UI v5
- React Query v5
- React Router v6
- Recharts (visualization)
- Vite (build tool)

**Infrastructure:**
- Docker + Docker Compose
- WSL2 (Windows Subsystem for Linux)
- NVIDIA Container Toolkit
- Flower (Celery monitoring)

---

## RECENT CRITICAL FIXES

### CUDA Device Mismatch (Nov 15, 2025)
**Problem:** 100% Re-ID task failure - tensors split between CPU/CUDA
**Fix:** Move base_model.to(DEVICE) before layer extraction
**Files:** multiscale_resnet.py, efficientnet_extractor.py
**Result:** Re-ID now operational, 0.68-0.87 similarity scores
**Commit:** b7d56e3

### Re-ID Threshold Optimization (Nov 15, 2025)
**Problem:** 64.5x profile explosion (379 vs expected 30-50)
**Fix:** REID_THRESHOLD 0.60 -> 0.50, full reprocessing
**Result:** 116 profiles (69% reduction), proper sex distribution
**Status:** Reprocessing in progress (3-4 hours)

### Sex Mapping Bug (Nov 12, 2025)
**Problem:** 99.3% bucks (missing 'buck' in sex_mapping dict)
**Fix:** Added 'buck': DeerSex.BUCK to mapping
**Result:** 50/50 sex distribution corrected
**Commit:** d334b0f

---

## OPERATIONS REFERENCE

**Full operational procedures:** `docs/OPERATIONS_RUNBOOK.md`

**Key procedures:**
- Bulk image import workflow
- Queue management and troubleshooting
- Performance tuning (worker concurrency)
- Monitoring dashboards
- Emergency procedures

**Monitoring:**
- Flower UI: http://localhost:5555
- API Docs: http://localhost:8001/docs
- Frontend: http://localhost:3000

---

## NOTES

- Always use `python3` (not `python`)
- Always use `docker-compose` (not `docker compose`)
- Use MSYS_NO_PATHCONV=1 for Git Bash path issues
- Verify file creation with `ls` immediately
- GPU operations require nvidia runtime
- Model loading takes 30-60s on worker restart
- Database writes are the bottleneck (not GPU)

---

**Last Updated:** November 15, 2025
**System Version:** v1.5.0 (Feature 011 Complete)
**Branch:** main
**Status:** PRODUCTION - Active Re-ID Optimization
