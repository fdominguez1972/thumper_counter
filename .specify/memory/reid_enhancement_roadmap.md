# Re-ID Enhancement Roadmap - 5-Week Implementation Plan

**Created:** November 15, 2025
**Feature Branch:** 009-reid-enhancement
**Specification:** specs/009-reid-enhancement/spec.md
**Status:** Specification Complete, Ready for Planning

---

## Overview

Following successful completion of Feature 010 (threshold optimization improving assignment rate from 39% to 60%), we now implement ML enhancements to push accuracy to 70-75% through advanced feature extraction and ensemble learning.

---

## Phased Implementation Schedule

### Week 1: Quick Wins - Multi-Scale + Ensemble (Feature 009)

**Focus:** Implement multi-scale feature fusion and EfficientNet-B0 ensemble

**Days 1-2: Multi-Scale Feature Fusion**
- Modify `src/worker/tasks/reidentification.py` feature extraction
- Extract features from ResNet50 layers 1, 2, 3, 4
- Apply adaptive pooling and concatenation (3840-dim → 512-dim)
- Add database migration for feature_vector_multiscale column
- Re-extract embeddings for 165 deer profiles
- Validate similarity score improvements on test set

**Deliverable:** Multi-scale feature extraction operational
**Expected Impact:** 10-15% improvement in similarity scores

**Days 3-5: Ensemble Model Integration**
- Install efficientnet_pytorch package
- Load pretrained EfficientNet-B0 model
- Add projection layer (1280-dim → 512-dim)
- Extract dual embeddings (ResNet50 + EfficientNet)
- Implement weighted similarity combination (0.6 + 0.4)
- Re-embed all 6,982 assigned detections
- Tune ensemble weights on validation data

**Deliverable:** Ensemble Re-ID system operational
**Expected Impact:** Additional 5-10% improvement (cumulative 15-25%)

**Success Metrics:**
- Assignment rate increases from 60% to 70%+
- Similarity scores for true matches increase 15-25%
- Processing time remains under 3 seconds per detection
- False positive rate stays below 5%

**Files Modified:**
- `src/worker/tasks/reidentification.py` (feature extraction)
- `src/backend/models/deer.py` (add feature_vector_efficientnet column)
- `requirements.txt` (add efficientnet_pytorch)
- `migrations/012_add_ensemble_embeddings.sql` (new migration)

**Scripts Created:**
- `scripts/re_embed_multiscale.py` (re-extract with multi-scale)
- `scripts/re_embed_ensemble.py` (extract EfficientNet embeddings)
- `scripts/validate_embeddings.py` (before/after comparison)
- `scripts/tune_ensemble_weights.py` (optimize weights)

---

### Weeks 2-3: High-Impact Fine-Tuning (Feature 012)

**Focus:** Train deer-specific Re-ID model using triplet loss

**Week 2: Dataset Preparation & Training Infrastructure**
- Create triplet dataset from 6,982 assigned detections
- Split into train (80%), validation (10%), test (10%)
- Implement triplet loss function (PyTorch)
- Set up training loop with hard negative mining
- Configure GPU training (RTX 4080 Super)

**Week 3: Model Training & Deployment**
- Train ResNet50 with triplet loss (50-100 epochs)
- Monitor validation loss and similarity metrics
- Select best checkpoint based on validation performance
- Extract new embeddings with fine-tuned model
- A/B test against ensemble model
- Deploy if performance improves

**Deliverable:** Deer-specific Re-ID model trained and deployed
**Expected Impact:** 20-30% improvement in similarity scores (cumulative 35-55%)

**Success Metrics:**
- Assignment rate reaches 75%+
- Similarity scores for same-deer pairs increase significantly
- Model separates similar-looking deer better
- Validation loss converges below baseline

**Files Created:**
- `scripts/create_triplet_dataset.py` (dataset generation)
- `src/worker/models/triplet_reid.py` (training code)
- `src/worker/models/triplet_loss.py` (loss function)
- `scripts/train_reid_triplet.py` (training script)
- `migrations/013_add_finetuned_embeddings.sql` (if needed)

---

### Weeks 4-5: Transformative Features (Feature 013)

**Focus:** Antler/marking detection for buck identification

**Week 4: Annotation & Model Training**
- Annotate 500-1000 buck images with antler points
- Label unique physical features (scars, markings, ear patterns)
- Configure YOLOv8 for keypoint detection
- Train antler point detection model
- Validate on test set

**Week 5: Integration & Validation**
- Integrate antler detection into Re-ID pipeline
- Extract structured features (8-point, 10-point, etc.)
- Use as hard constraints in matching logic
- Update UI to display detected features
- End-to-end testing

**Deliverable:** Antler-based feature detection operational
**Expected Impact:** Near 100% accuracy for bucks with visible antlers

**Success Metrics:**
- Antler point detection accuracy >90%
- Buck misidentification drops to <1%
- Feature metadata enriches deer profiles
- Users can manually verify antler features

**Files Created:**
- `datasets/antler_annotations/` (annotation data)
- `src/worker/models/antler_detector.py` (YOLOv8 model)
- `scripts/train_antler_detector.py` (training)
- `scripts/annotate_antlers.py` (annotation tool)
- `migrations/014_add_antler_features.sql` (feature storage)

---

### Ongoing: Active Learning Pipeline (Feature 014)

**Focus:** Continuous improvement through user corrections

**Components:**
- Detection correction UI (frontend)
- Label collection and storage
- Hard negative mining from corrections
- Retraining pipeline automation
- Performance tracking dashboard

**Deliverable:** Self-improving Re-ID system
**Expected Impact:** Continuous incremental improvements

---

## Technical Architecture

### Current System (Post-Feature 010)
```
Detection Crop (image)
    ↓
ResNet50 (final layer only)
    ↓
512-dim embedding
    ↓
Cosine similarity vs deer profiles
    ↓
Match if similarity >= 0.40
```

### After Week 1 (Multi-Scale + Ensemble)
```
Detection Crop (image)
    ↓
ResNet50 Multi-Scale               EfficientNet-B0
 ├─ Layer 1 (256-dim)              └─ Final layer (1280-dim)
 ├─ Layer 2 (512-dim)                  ↓
 ├─ Layer 3 (1024-dim)             Project to 512-dim
 └─ Layer 4 (2048-dim)
    ↓
Concat + Pool (3840-dim)
    ↓
Project to 512-dim
    ↓                                  ↓
Similarity A                      Similarity B
    ↓                                  ↓
    Combined: 0.6*A + 0.4*B
    ↓
Match if combined >= threshold
```

### After Week 3 (Fine-Tuned)
```
Detection Crop (image)
    ↓
ResNet50 (fine-tuned on deer triplets)
    ↓
512-dim deer-specific embedding
    ↓
Higher quality similarities
    ↓
Better matching decisions
```

### After Week 5 (Antler Detection)
```
Detection Crop (buck)
    ↓
YOLOv8 Antler Detector
    ↓
Antler Points: [8-point, split G2]
    ↓
IF antler_points_match(detection, deer):
    Use ResNet50 similarity
ELSE:
    Reject (impossible match)
```

---

## Database Schema Changes

### Migration 012: Ensemble Embeddings
```sql
ALTER TABLE deer
ADD COLUMN feature_vector_multiscale VECTOR(512),
ADD COLUMN feature_vector_efficientnet VECTOR(512),
ADD COLUMN embedding_version VARCHAR(20) DEFAULT 'baseline';

CREATE INDEX idx_deer_multiscale ON deer
USING ivfflat (feature_vector_multiscale vector_cosine_ops);

CREATE INDEX idx_deer_efficientnet ON deer
USING ivfflat (feature_vector_efficientnet vector_cosine_ops);
```

### Migration 013: Fine-Tuned Embeddings (Optional)
```sql
ALTER TABLE deer
ADD COLUMN feature_vector_finetuned VECTOR(512);

CREATE INDEX idx_deer_finetuned ON deer
USING ivfflat (feature_vector_finetuned vector_cosine_ops);
```

### Migration 014: Antler Features
```sql
ALTER TABLE deer
ADD COLUMN antler_points INTEGER,
ADD COLUMN antler_description TEXT,
ADD COLUMN physical_features JSONB;

CREATE INDEX idx_deer_antler_points ON deer (antler_points)
WHERE antler_points IS NOT NULL;
```

---

## Success Tracking

### Baseline (Post-Feature 010)
- Assignment Rate: 60.35% (6,982 / 11,570)
- Deer Profiles: 165 (119 bucks, 46 does)
- REID_THRESHOLD: 0.40
- Max Similarity Observed: 0.4764
- Processing Time: ~2 seconds per detection

### Target (Post-Feature 009 Week 1)
- Assignment Rate: 70%+ (8,100+ / 11,570)
- Similarity Scores: +15-25% for true matches
- False Positive Rate: <5%
- Processing Time: <3 seconds per detection

### Target (Post-Feature 012 Week 3)
- Assignment Rate: 75%+ (8,678+ / 11,570)
- Similarity Scores: +35-55% for true matches
- Better separation of similar-looking deer
- Processing Time: <3 seconds per detection

### Target (Post-Feature 013 Week 5)
- Buck Identification: >95% accuracy
- Antler Point Detection: >90% accuracy
- Buck Misidentification: <1%
- Structured metadata for all bucks

---

## Risk Mitigation

### Risk 1: Re-Embedding Changes Matches
**Mitigation:** Preserve old embeddings, run parallel validation, only replace if improved

### Risk 2: GPU Memory Overflow
**Mitigation:** Batch size tuning, model quantization if needed, monitor VRAM usage

### Risk 3: Performance Regression
**Mitigation:** Benchmark at each phase, optimize bottlenecks, consider caching

### Risk 4: Annotation Bottleneck (Week 4)
**Mitigation:** Start annotations early, use data augmentation, consider semi-supervised learning

### Risk 5: False Positive Increase
**Mitigation:** Tune thresholds carefully, validate on test set, implement rollback mechanism

---

## Dependencies & Prerequisites

**Software:**
- PyTorch 2.x (installed)
- torchvision (installed)
- efficientnet_pytorch (needs installation)
- pgvector PostgreSQL extension (installed)

**Hardware:**
- RTX 4080 Super (16GB VRAM) - available
- 32-thread CPU worker (configured)

**Data:**
- 6,982 assigned detections (available)
- 165 deer profiles with embeddings (available)
- 4,588 unassigned detections for testing (available)

**Models:**
- ResNet50 pretrained (available)
- EfficientNet-B0 pretrained (will download)
- YOLOv8 base model (for antler detection, will download)

---

## Next Steps

1. **Immediate:** Run `/speckit.plan` to generate implementation tasks for Feature 009
2. **Day 1:** Begin multi-scale feature fusion implementation
3. **Day 3:** Deploy multi-scale, start ensemble integration
4. **Week 2:** Plan Feature 012 (triplet training) specification
5. **Week 4:** Plan Feature 013 (antler detection) specification

---

**Document Owner:** Claude Code
**Last Updated:** November 15, 2025
**Status:** Approved, Ready for Implementation
