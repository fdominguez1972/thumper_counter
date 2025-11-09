# Quick Stats - Thumper Counter
**Last Updated:** November 8, 2025

## Overall System Status

**Processing Progress:**
- Total Images: 35,251
- Completed: 24,440 (69.33%)
- Pending: 10,254 (29.08%)
- Failed: 557 (1.58%)
- Processing Speed: 840 images/min

**GPU Performance:**
- Model: RTX 4080 Super (16GB VRAM)
- Utilization: 31% (optimal)
- Speed: 0.04s per image (10x faster than CPU)
- Worker Concurrency: 32 (optimized)

## Detection Results

**Wildlife Detected:**
- Total Detections: ~60,000+ (estimated)
- Deer Profiles: 53 unique individuals
- Buck Profiles: 11 unique bucks
- Mature Bucks: 3 identified
- Species Diversity: 7 classes (4 deer, 3 non-deer)

**Data Quality:**
- Average Confidence: 68%
- Cattle Found: 8 detections (excellent accuracy!)
- Feral Hogs: 0
- Raccoons: 0
- Deer: 99.98% of detections

## Rut Season Analysis (Sept 2023 - Jan 2024)

**Dataset:**
- Rut Images: 3,656 (100% processed)
- Total Buck Detections: 285
- Mature Buck Detections: 16
- Unique Bucks: 11 total (3 mature)

**Peak Activity:**
- Peak Month: October 2023 (145 buck detections, 39.5% of activity)
- Peak Day: Oct 17, 2023 (19 bucks, 0 does)
- Buck:Doe Ratio (Peak): 1.67:1
- Buck:Doe Ratio (Normal): ~1:3

**Temporal Pattern:**
| Month    | Buck % | Pattern      |
|----------|--------|--------------|
| Sept-23  | 8.8%   | Pre-rut      |
| Oct-23   | 39.5%  | PEAK RUT     |
| Nov-23   | 28.8%  | Breeding     |
| Dec-23   | 2.3%   | Post-rut     |
| Jan-24   | 9.9%   | Recovery     |

## The Three Mature Bucks

**Buck #1 (Primary)** - ID: 815100e5-e7ea-409a-b897-bea303b6a23b
- Total Sightings: 26
- Mature Detections: 6
- Timeline: Oct 10-21, 2023 + Feb 5, 2024
- Status: UNNAMED (ready for Disney name!)
- Favorite Location: Hayfield

**Buck #2** - ID: b34ba7ed-30bd-4f23-9c07-7552d74f16c0
- Total Sightings: 20
- Mature Detections: 1 (Nov 6, conf: 0.80)
- Status: UNNAMED
- Favorite Location: Hayfield

**Buck #3** - ID: 3b2f9f77-d388-40d4-aa39-169441d2e606
- Total Sightings: 7
- Mature Detections: 1 (Oct 20, conf: 0.82 - HIGHEST)
- Status: UNNAMED
- Favorite Location: Hayfield

## Model Performance

**YOLOv8 Detection:**
- Speed: 0.04s per image (GPU)
- mAP50: 0.804
- Precision: 0.896
- Recall: 0.701

**Classification Accuracy:**
- Doe: 0.769 mAP50
- Fawn: 0.796 mAP50
- Mature Buck: 0.673 mAP50
- Mid Buck: 0.581 mAP50
- Young Buck: 0.676 mAP50

**Re-Identification:**
- Feature Extractor: ResNet50 (512-dim embeddings)
- Similarity Threshold: 0.85 (cosine)
- Assignment Rate: ~50% for mature bucks
- Unique Profiles: 53 total deer

## Infrastructure Optimizations

**Critical Fixes (Evening Session):**
- Volume Mount Format: Changed /mnt/i/ to I:\ (Windows Docker)
- Worker Concurrency: Optimized to 32 (from 1)
- Performance Gain: 13x speed improvement
- GPU Lock Contention: Eliminated (was 18s/task at concurrency=64)

**Architecture:**
- Backend: FastAPI (port 8001)
- Database: PostgreSQL + pgvector
- Queue: Redis + Celery
- Frontend: React + Material-UI (port 3000)
- Monitoring: Flower (port 5555)

## Locations

**Camera Sites:**
- Hayfield: Primary location (most activity)
- Sanctuary: (data pending)
- [Additional locations TBD]

**Image Storage:**
- Path: I:\Hopkins_Ranch_Trail_Cam_Pics
- Format: Windows path (critical for Docker Desktop)

## Upcoming Features

**Planned Enhancements:**
1. "Favorite Feeder" field on Deer Card (location with most sightings)
2. Disney names for all deer (user assignment)
3. Data verification and cleanup
4. Training data export for model fine-tuning

**Next Processing Batch:**
- Remaining Images: 10,254
- Estimated Time: ~12 minutes
- Completion Target: 100%

---

**Note:** These stats are live and updated as processing continues. For detailed analysis, see:
- docs/RUT_SEASON_ANALYSIS.md
- docs/SESSION_20251108_RUT_ANALYSIS.md
- docs/MATURE_BUCKS_REVIEW.md
