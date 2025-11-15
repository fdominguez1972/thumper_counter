# Implementation Plan: Re-ID Enhancement - Multi-Scale and Ensemble Learning

**Branch**: `009-reid-enhancement` | **Date**: 2025-11-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-reid-enhancement/spec.md`

## Summary

Enhance the deer re-identification system from 60% to 70-75% assignment accuracy using multi-scale feature extraction (combining ResNet50 layers 2, 3, 4, and avgpool) and ensemble learning (adding EfficientNet-B0 for architectural diversity). The system extracts 512-dimensional embeddings from both models, computes weighted similarity scores (0.6 ResNet + 0.4 EfficientNet), and maintains backward compatibility with existing single-layer embeddings. Implementation includes database schema migration, re-embedding of 165 existing deer profiles, validation against known pairs, and gradual cutover with rollback capability.

## Technical Context

**Language/Version**: Python 3.11 (backend/worker containers)
**Primary Dependencies**: PyTorch 2.x (ResNet50, EfficientNet-B0), torchvision (pretrained models), pgvector (PostgreSQL vector extension), SQLAlchemy 2.x (ORM), FastAPI 0.100+ (backend API)
**Storage**: PostgreSQL 15+ with pgvector extension (vector embeddings), local filesystem (image crops), Redis (Celery queue)
**Testing**: pytest (validation scripts), manual A/B testing (assignment rate comparison), SQL queries (embedding quality checks)
**Target Platform**: Linux server (Docker containers), RTX 4080 Super GPU (16GB VRAM, CUDA 12.x), Celery worker pool (threads, concurrency=32)
**Project Type**: Web application (backend API + ML worker)
**Performance Goals**: <3 seconds per detection (multi-scale extraction 80ms + EfficientNet 40ms + DB query 10ms = 130ms), >70% assignment rate, <5% false positive rate
**Constraints**: VRAM <12GB (75% of 16GB), thread-safe model loading (32 concurrent workers), backward compatible (preserve old embeddings for rollback)
**Scale/Scope**: 165 deer profiles, 11,570 detections, 35,251 images, processing rate 8.3 images/second (overnight: 239,040 images)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Constitution Compliance Analysis

**Principle 1: Wildlife Conservation First**
- [PASS] No real-time location data exposure
- [PASS] All data remains local (no cloud dependencies)
- [PASS] Enhanced accuracy improves conservation research quality
- Impact: Positive (better individual tracking for population studies)

**Principle 2: Data Sovereignty**
- [PASS] Local GPU processing only (RTX 4080 Super on-premises)
- [PASS] Database remains on local PostgreSQL instance
- [PASS] No external API calls (pretrained models cached locally)
- Impact: None (maintains full data control)

**Principle 3: Operational Simplicity**
- [PASS] Transparent to end users (no UI changes required)
- [PASS] Automatic re-embedding script (one-time execution)
- [PASS] Rollback capability if issues arise
- Impact: None (backend enhancement, no user-facing changes)

**Principle 4: Scientific Rigor**
- [PASS] Validation script measures improvement quantitatively
- [PASS] Confidence scores tracked for all matches
- [PASS] False positive rate monitoring (<5% requirement)
- [PASS] A/B testing capability (compare old vs new embeddings)
- Impact: Positive (improves data quality with measurable validation)

**Principle 5: Modular Architecture**
- [PASS] New embedding models independently replaceable
- [PASS] Database schema backward compatible (additive changes)
- [PASS] Feature flag for gradual rollout (USE_ENHANCED_REID)
- [PASS] No changes to detection or classification modules
- Impact: Positive (maintains modularity, enhances Re-ID only)

**Principle 6: Performance Efficiency**
- [PASS] Processing time remains <3s per detection (130ms actual)
- [PASS] GPU utilization optimal (~2GB VRAM of 16GB available)
- [PASS] 24-hour processing capability maintained (239k images)
- [WARN] 40% slower throughput (13.5 → 8.3 images/sec)
- Justification: Acceptable trade-off for 10-15% accuracy gain
- Impact: Acceptable (still processes full dataset overnight)

**Principle 7: Open Development**
- [PASS] Uses open-source models (ResNet50, EfficientNet-B0)
- [PASS] Implementation documented for community sharing
- [PASS] pgvector extension is open-source
- Impact: Positive (leverages and contributes to OSS ecosystem)

### Technical Standards Compliance

**Mandatory Requirements**:
- [PASS] Python 3.11 (backend/worker containers)
- [PASS] PostgreSQL 15+ (with pgvector extension)
- [PASS] Docker deployment (containers: backend, worker, db)
- [PASS] Git branching (009-reid-enhancement branch)
- [PASS] ASCII-only output (all logging and CLI)

**Prohibited Practices**:
- [PASS] No credentials in code (uses environment variables)
- [PASS] No direct DB access from frontend (backend API only)
- [PASS] No synchronous ML processing in API (Celery tasks)
- [PASS] No hardcoded paths (uses environment variables)
- [PASS] No Unicode/emoji in output (ASCII logging only)

### Data Governance Compliance

**Data Retention**:
- [PASS] Backward compatible (old embeddings preserved)
- [PASS] New embeddings stored alongside existing data
- [PASS] Migration script maintains data integrity
- Impact: None (additive storage, no data loss)

**Privacy Protection**:
- [PASS] No PII in wildlife data
- [PASS] Camera locations not exposed via embeddings
- [PASS] User actions logged (audit trail maintained)
- Impact: None (enhances existing privacy-compliant system)

### Session Handoff Compliance

**Documentation Requirements**:
- [CREATED] research.md (Phase 0 findings)
- [CREATED] data-model.md (Phase 1 schema design)
- [CREATED] quickstart.md (Phase 1 operational guide)
- [PENDING] tasks.md (Phase 2 - generated by /speckit.tasks)
- [PENDING] Session handoff document (created at end of implementation)

**CONSTITUTION CHECK: PASSED**
All principles satisfied. Performance trade-off (40% slower) justified by accuracy improvement (10-15%). Ready for Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/009-reid-enhancement/
├── spec.md              # Feature specification (user scenarios, requirements)
├── plan.md              # This file (technical context, constitution check)
├── research.md          # Phase 0 research (multi-scale, ensemble, GPU optimization)
├── data-model.md        # Phase 1 design (database schema, migration strategy)
├── quickstart.md        # Phase 1 guide (deployment, validation, rollback)
├── checklists/          # Feature-specific checklists
│   └── *.md
└── tasks.md             # Phase 2 output (/speckit.tasks - NOT yet created)
```

### Source Code (repository root)

**Structure Decision**: Web application (backend API + ML worker)

```text
src/
├── backend/
│   ├── api/
│   │   ├── deer.py                    # Deer profile endpoints (existing)
│   │   ├── detections.py              # Detection endpoints (existing)
│   │   └── processing.py              # Batch processing endpoints (existing)
│   ├── models/
│   │   ├── deer.py                    # [MODIFY] Add feature_vector_multiscale, feature_vector_efficientnet
│   │   ├── detection.py               # Detection model (existing, no changes)
│   │   └── image.py                   # Image model (existing, no changes)
│   ├── core/
│   │   └── database.py                # Database connection (existing, no changes)
│   └── app/
│       └── main.py                    # FastAPI app (existing, no changes)
│
└── worker/
    ├── tasks/
    │   ├── reidentification.py        # [MODIFY] Add multi-scale + ensemble extraction
    │   └── detection.py               # Detection task (existing, no changes)
    ├── models/
    │   ├── multiscale_resnet.py       # [NEW] Multi-scale ResNet50 architecture
    │   └── efficientnet_extractor.py  # [NEW] EfficientNet-B0 feature extraction
    └── celery_app.py                  # Celery config (existing, no changes)

migrations/
├── 010_*.sql                          # Previous migrations (existing)
└── 011_add_reid_enhancement.sql       # [NEW] Add vector columns and indexes

scripts/
├── reembed_deer_enhanced.py           # [NEW] Re-embed existing deer profiles
├── validate_enhanced_embeddings.py    # [NEW] Validation script (before/after)
├── test_multiscale_extraction.py      # [NEW] Test multi-scale feature extraction
├── test_ensemble_matching.py          # [NEW] Test ensemble similarity computation
└── analyze_similarity_distribution.py # [NEW] Analyze similarity score distribution

tests/
├── worker/
│   ├── test_multiscale_resnet.py      # [NEW] Unit tests for multi-scale model
│   ├── test_efficientnet.py           # [NEW] Unit tests for EfficientNet model
│   └── test_ensemble_reid.py          # [NEW] Integration tests for ensemble Re-ID
└── backend/
    └── test_deer_api.py               # Existing tests (no changes needed)
```

**Key Files Modified**:
1. `src/backend/models/deer.py`: Add 3 columns (feature_vector_multiscale, feature_vector_efficientnet, embedding_version)
2. `src/worker/tasks/reidentification.py`: Add multi-scale extraction, ensemble matching, backward compatibility flag

**Key Files Created**:
1. `src/worker/models/multiscale_resnet.py`: Multi-scale ResNet50 architecture
2. `src/worker/models/efficientnet_extractor.py`: EfficientNet-B0 feature extractor
3. `migrations/011_add_reid_enhancement.sql`: Database schema migration
4. `scripts/reembed_deer_enhanced.py`: Re-embedding script for existing deer
5. `scripts/validate_enhanced_embeddings.py`: Validation script (accuracy analysis)

**No Changes Required**:
- Frontend (no UI modifications)
- Detection pipeline (independent module)
- Classification pipeline (independent module)
- API endpoints (Re-ID is internal worker logic)

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations identified.** Constitution check passed with one acceptable trade-off:

| Design Decision | Justification | Alternative Rejected |
|-----------------|---------------|----------------------|
| 40% slower throughput (13.5 → 8.3 img/s) | 10-15% accuracy improvement critical for conservation research | Single-model optimization (insufficient accuracy gain) |
| Dual embeddings stored (ResNet + EfficientNet) | Required for ensemble matching and rollback capability | Single embedding only (no architectural diversity, no rollback) |
| HNSW index for 2 vector columns | Fast similarity search at scale (O(log N) vs O(N)) | Sequential scan (too slow for real-time Re-ID) |

**Complexity Justified**: Enhanced Re-ID accuracy directly improves wildlife conservation outcomes (better individual tracking for population studies). Performance trade-off acceptable as system still processes full dataset overnight (239k images in 8 hours).
