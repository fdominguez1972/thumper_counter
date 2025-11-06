# Next Steps for Thumper Counter
**Last Updated:** 2025-11-05 (after MVP detection pipeline completion)
**Branch:** 001-detection-pipeline
**Status:** Phase 1 MVP Complete - Ready for Phase 2

## Quick Start (Next Session)

### 1. Start the Environment
```bash
cd /mnt/i/projects/thumper_counter

# Start all services
docker-compose up -d

# Verify everything is running
docker-compose ps
curl http://localhost:8001/health

# Check worker is ready
docker-compose logs worker | grep "celery@.*ready"
```

### 2. Check Current State
```bash
# Verify we're on the feature branch
git status
git log --oneline -5

# Check database status
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT processing_status, COUNT(*) FROM images GROUP BY processing_status;"

# Check detection count
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT COUNT(*) FROM detections;"
```

## What Was Just Completed

### Phase 1 MVP - Detection Pipeline ✅
- [x] Image upload via POST /api/images
- [x] EXIF metadata extraction
- [x] Celery task queueing to ml_processing queue
- [x] YOLOv8 detection with CPU inference
- [x] Detection records stored in database
- [x] Processing status tracking (pending -> processing -> completed)
- [x] End-to-end test: 1 deer detected at 87% confidence in 0.4s

**Files Modified:**
- src/backend/api/images.py (Celery send_task integration)
- src/backend/models/image.py (Enum values fix)
- src/worker/tasks/detection.py (Detection implementation)
- src/worker/celery_app.py (Task registration)
- docker/dockerfiles/Dockerfile.worker (PYTHONPATH fix)
- docker-compose.yml (CUDA disabled for CPU mode)

**Test Results:**
- Upload: Working
- Queue: Working (Redis ml_processing queue)
- Detection: Working (YOLOv8 CPU mode)
- Database: Working (status updates, detection records)

## What to Do Next

### Immediate Priority: Enable GPU Support

**Issue:** CUDA disabled due to fork() multiprocessing incompatibility
**Error:** "Cannot re-initialize CUDA in forked subprocess"

**Solution Options:**

#### Option 1: Switch to Celery Solo Pool (Easiest)
```bash
# Edit docker-compose.yml worker environment
CELERY_POOL: solo

# Or edit Dockerfile.worker CMD
CMD ["celery", "-A", "worker.celery_app", "worker", "--loglevel=info", "--pool=solo"]
```
Pros: Simple, no code changes
Cons: No parallelism (1 task at a time)

#### Option 2: Use Threads Pool
```bash
CMD ["celery", "-A", "worker.celery_app", "worker", "--loglevel=info", "--pool=threads", "--concurrency=2"]
```
Pros: Parallel tasks, CUDA compatible
Cons: GIL limitations for CPU-bound work

#### Option 3: Preload Model at Startup (Recommended)
Move model loading to worker startup (before fork), cache in shared memory.

```python
# In celery_app.py after validate_model_files()
from worker.tasks.detection import get_detection_model

# Load model BEFORE worker forks
print("[INFO] Pre-loading YOLOv8 model...")
_global_model = get_detection_model()
print("[OK] Model loaded in main process")
```

Then update docker-compose.yml to enable CUDA:
```yaml
# Remove CUDA_VISIBLE_DEVICES: "" line
# Add GPU runtime if available
runtime: nvidia
```

### Phase 2: Batch Processing

**Goal:** Process existing 35,234 images in database

**Tasks:**
1. Create batch processing endpoint
   ```python
   # POST /api/processing/batch
   # Query parameters:
   # - location_id (optional)
   # - status=pending (filter)
   # - limit=1000 (batch size)
   ```

2. Create batch Celery task
   ```python
   # src/worker/tasks/batch.py
   @app.task(name='worker.tasks.batch.process_batch')
   def process_batch(image_ids: List[str]) -> Dict:
       """Process multiple images in sequence"""
   ```

3. Add progress monitoring
   ```python
   # GET /api/processing/status
   # Returns: total, pending, processing, completed, failed
   ```

**Estimated Time:** 3-4 hours

### Phase 3: Deer Management API

**Tasks:**
1. Deer CRUD endpoints (POST/GET/PUT/DELETE /api/deer)
2. Detection query endpoints (GET /api/detections)
3. Link detections to deer profiles (manual assignment for now)

**Estimated Time:** 4-5 hours

### Phase 4: Basic Re-ID

**Tasks:**
1. Extract simple features (bounding box size, color histogram)
2. Implement similarity matching
3. Auto-assign deer IDs based on similarity

**Estimated Time:** 6-8 hours

## Known Issues & Fixes Needed

### Critical
- [ ] **GPU Support Disabled** (see solutions above)
  - Current: CPU only (0.4s per image)
  - Target: GPU enabled (~0.05s per image = 8x faster)

### Important
- [ ] **Detection UUID Not Stored in Response**
  - Line: src/worker/tasks/detection.py:236
  - Issue: `detections_created.append(str(detection.id))` but detection.id is None
  - Fix: Commit detection first, then append ID

### Minor
- [ ] **Model Path Hardcoded**
  - Line: src/worker/tasks/detection.py:54
  - Current: `YOLO_MODEL_PATH = MODEL_DIR / 'yolov8n_deer.pt'`
  - Better: Load from environment variable

- [ ] **No Error Rate Tracking**
  - Add Prometheus metrics for monitoring
  - Track: success rate, avg processing time, GPU memory

## File Locations (Key Files)

### Backend API
- `src/backend/api/images.py` - Image upload endpoint
- `src/backend/api/locations.py` - Location management
- `src/backend/app/main.py` - FastAPI app entry point

### Database Models
- `src/backend/models/image.py` - Image model with ProcessingStatus enum
- `src/backend/models/detection.py` - Detection model
- `src/backend/models/location.py` - Location model
- `src/backend/models/deer.py` - Deer model (not used yet)

### Worker Tasks
- `src/worker/celery_app.py` - Celery configuration
- `src/worker/tasks/detection.py` - YOLOv8 detection task
- `src/worker/tasks/process_images.py` - Old placeholder tasks

### Configuration
- `docker-compose.yml` - Service orchestration
- `docker/dockerfiles/Dockerfile.backend` - Backend container
- `docker/dockerfiles/Dockerfile.worker` - Worker container
- `.env` - Environment variables (DB credentials, paths)

### Documentation
- `CLAUDE.md` - Claude Code preferences and instructions
- `.specify/plan.md` - Sprint plan (needs update)
- `docs/SESSION_20251105_HANDOFF.md` - Session handoff notes

## Testing Commands

### Test Image Upload
```bash
curl -X POST http://localhost:8001/api/images \
  -F "files=@/mnt/i/Hopkins_Ranch_Trail_Cam_Pics/Sanctuary/SANCTUARY_00001.jpg" \
  -F "location_name=Sanctuary" \
  -F "process_immediately=true"
```

### Check Processing Status
```bash
# Get specific image
IMAGE_ID="<uuid-from-upload>"
curl http://localhost:8001/api/images/$IMAGE_ID | python3 -m json.tool

# List all completed images
curl "http://localhost:8001/api/images?status=completed&page_size=10" | python3 -m json.tool
```

### Monitor Worker
```bash
# Watch worker logs
docker-compose logs -f worker | grep -E "(Starting detection|Detection complete)"

# Check queue depth
docker-compose exec redis redis-cli LLEN celery

# Check Celery worker status
docker-compose exec worker celery -A worker.celery_app inspect active
```

### Database Queries
```bash
# Processing status summary
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT processing_status, COUNT(*) FROM images GROUP BY processing_status;"

# Detection statistics
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT COUNT(*) as total_detections,
          AVG(confidence)::numeric(5,2) as avg_confidence,
          MIN(confidence)::numeric(5,2) as min_confidence,
          MAX(confidence)::numeric(5,2) as max_confidence
   FROM detections;"

# Recent detections
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT i.filename, d.confidence, d.bbox, i.processing_status
   FROM detections d
   JOIN images i ON d.image_id = i.id
   ORDER BY d.created_at DESC LIMIT 10;"
```

## Performance Targets

### Current Performance (CPU Mode)
- Detection speed: ~0.4s per image
- Throughput: ~150 images/minute (single worker)
- Model: YOLOv8n (21.5MB)

### Target Performance (GPU Mode)
- Detection speed: ~0.05s per image (8x improvement)
- Throughput: ~1200 images/minute (single worker)
- Batch size: 16-32 images

### Processing All Images
- Total images: 35,234
- CPU mode: ~235 minutes (~4 hours)
- GPU mode: ~29 minutes (~30 min)
- With 4 workers + GPU: ~7-8 minutes

## Git Workflow

### Current Branch
- Feature branch: `001-detection-pipeline`
- Base branch: `main`
- Remotes: origin (GitHub), ubuntu, synology

### Next Commit
When you complete the next phase:
```bash
# Stage changes
git add -A

# Commit with descriptive message
git commit -m "feat: add batch processing endpoint and GPU support

- Implement POST /api/processing/batch endpoint
- Enable CUDA with solo/threads pool
- Add progress monitoring
- Process 1000 images in test batch

Fixes GPU multiprocessing issue
Closes #[issue-number]"

# Push to remotes
git push origin 001-detection-pipeline
git push ubuntu 001-detection-pipeline
```

### When MVP is Complete
```bash
# Merge feature branch to main
git checkout main
git merge 001-detection-pipeline
git tag -a v0.1.0 -m "MVP: Detection pipeline complete"
git push origin main --tags
git push ubuntu main --tags
```

## Questions to Consider

### Architecture
- [ ] Should we add a queue for each location? (7 queues total)
- [ ] Implement priority queue for recent images?
- [ ] Add Redis caching for API responses?

### Scaling
- [ ] How many concurrent workers can GPU handle?
- [ ] Should we shard database by location?
- [ ] Implement horizontal scaling with multiple worker containers?

### Monitoring
- [ ] Set up Flower UI for Celery monitoring?
- [ ] Add Prometheus + Grafana for metrics?
- [ ] Implement alerting for failed tasks?

## Resources

### Documentation
- [Celery GPU Support](https://docs.celeryq.dev/en/stable/userguide/concurrency/index.html)
- [YOLOv8 Docs](https://docs.ultralytics.com/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)

### Original Project
- Location: `I:\deer_tracker`
- Reference for model configs and processing pipeline

### GPU Info
- GPU: RTX 4080 Super
- VRAM: 16GB
- CUDA Version: Check with `nvidia-smi`

---

**Next Review:** After GPU enablement and batch processing
**Estimated Time to Next Milestone:** 4-6 hours
**Priority:** Enable GPU → Batch Processing → Deer API
