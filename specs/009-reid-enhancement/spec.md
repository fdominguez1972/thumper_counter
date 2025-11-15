# Feature Specification: Re-ID Enhancement - Multi-Scale and Ensemble Learning

**Feature Branch**: `009-reid-enhancement`
**Created**: 2025-11-15
**Status**: Draft
**Input**: User description: "Enhance the deer re-identification system with multi-scale feature extraction and ensemble learning to improve assignment accuracy from 60% to 70-75%."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Improved Automatic Deer Matching (Priority: P1)

A wildlife researcher reviews their trail camera images and notices the system correctly identifies the same deer across multiple photos taken at different times and locations, reducing manual verification effort.

**Why this priority**: This is the core value proposition - improving Re-ID accuracy directly reduces manual work and increases research data quality.

**Independent Test**: Can be fully tested by processing a validation set of known deer with multiple sightings and measuring assignment accuracy. Delivers immediate value by reducing false negatives (missed matches).

**Acceptance Scenarios**:

1. **Given** a deer has been photographed 10 times across 3 locations, **When** the system processes all images, **Then** at least 8 of 10 detections are correctly assigned to the same deer profile
2. **Given** two visually similar deer (same sex, similar body size), **When** the system processes photos of both, **Then** detections are correctly assigned to separate deer profiles with no cross-contamination
3. **Given** a deer photographed at different angles (front, side, rear), **When** the system extracts features, **Then** all angles match to the same deer profile with similarity scores above threshold

---

### User Story 2 - Reduced False Positives (Priority: P2)

A researcher notices that different deer are no longer incorrectly merged into single profiles, maintaining data integrity for population studies and individual tracking.

**Why this priority**: False positives corrupt research data and require manual cleanup. Second priority because correct matches (P1) are more valuable than avoiding incorrect ones.

**Independent Test**: Can be tested independently by measuring precision on validation set with known distinct deer. Delivers value by improving data quality without requiring P1 completion.

**Acceptance Scenarios**:

1. **Given** two different bucks with similar antler configurations, **When** both are detected in the same photo burst, **Then** system creates separate deer profiles instead of merging
2. **Given** a mature doe and yearling doe in same location, **When** system compares features, **Then** similarity scores remain below threshold preventing false match
3. **Given** system has processed 1000 detections, **When** researcher reviews high-confidence matches (similarity > 0.50), **Then** false positive rate is below 5%

---

### User Story 3 - Faster Processing with Maintained Accuracy (Priority: P3)

A researcher processes a batch of 5,000 new images and notices the enhanced Re-ID system completes within reasonable time while maintaining higher accuracy than the previous system.

**Why this priority**: Performance is important but secondary to accuracy. Listed as P3 because users will tolerate slower processing for better results.

**Independent Test**: Can be tested independently by benchmarking processing time on standard image batches. Delivers value as performance optimization without requiring accuracy improvements first.

**Acceptance Scenarios**:

1. **Given** a batch of 100 images with deer detections, **When** Re-ID processing executes, **Then** total processing time remains under 5 minutes (3 seconds per detection average)
2. **Given** GPU memory limit of 16GB, **When** ensemble models load, **Then** total VRAM usage stays below 12GB leaving headroom for batch processing
3. **Given** system processes 1000 detections overnight, **When** morning arrives, **Then** all detections are assigned without worker crashes or memory errors

---

### Edge Cases

- What happens when deer crop is extremely small (under 50x50 pixels)?
- How does system handle partial occlusion (deer behind tree, only antlers visible)?
- What happens when only fawn detections exist but no adult references?
- How does system handle seasonal changes (bucks losing antlers post-rut)?
- What happens when similar-looking deer from same genetic line are photographed?
- How does system handle motion blur or low-light images?

## Requirements *(mandatory)*

### Functional Requirements

**Multi-Scale Feature Extraction**

- **FR-001**: System MUST extract features from 4 layers of neural network (early texture, mid-level shapes, high-level parts, semantic features)
- **FR-002**: System MUST combine multi-layer features into single 512-dimensional embedding vector
- **FR-003**: System MUST apply adaptive pooling to normalize different layer dimensions before concatenation
- **FR-004**: System MUST preserve existing single-layer embeddings during migration for backward compatibility testing

**Ensemble Model Integration**

- **FR-005**: System MUST extract features using two independent neural networks (existing ResNet50 + new EfficientNet-B0)
- **FR-006**: System MUST compute similarity scores from both models independently
- **FR-007**: System MUST combine dual similarity scores using weighted average (configurable weights)
- **FR-008**: System MUST store embeddings from both models for all deer profiles

**Re-Embedding Pipeline**

- **FR-009**: System MUST provide script to re-extract embeddings for existing deer profiles using new feature extraction
- **FR-010**: System MUST preserve original embeddings until validation confirms new embeddings perform better
- **FR-011**: System MUST re-process all assigned detections (currently 6,982) with new feature extraction
- **FR-012**: System MUST provide comparison report showing similarity score changes before/after enhancement

**Performance Requirements**

- **FR-013**: System MUST complete feature extraction for single detection in under 3 seconds
- **FR-014**: System MUST fit both models (ResNet50 + EfficientNet-B0) in available GPU memory (16GB VRAM)
- **FR-015**: System MUST maintain thread-safe model loading for concurrent worker processes

**Validation & Testing**

- **FR-016**: System MUST provide validation script to compare old vs new embeddings on known deer pairs
- **FR-017**: System MUST log similarity scores to database for before/after analysis
- **FR-018**: System MUST allow rollback to original embeddings if new system underperforms

### Key Entities

- **Multi-Scale Embedding**: 512-dimensional vector combining features from 4 neural network layers (texture at 256-dim, shapes at 512-dim, parts at 1024-dim, semantics at 2048-dim pooled and concatenated)
- **Ensemble Embedding Pair**: Two 512-dimensional vectors (one from ResNet50, one from EfficientNet-B0) stored per deer profile for dual-model matching
- **Feature Extraction Model**: Neural network that transforms deer crop image into embedding vector (two models: ResNet50 multi-scale, EfficientNet-B0)
- **Similarity Score**: Numerical value (0.0 to 1.0) representing match confidence between detection and deer profile, computed via cosine similarity
- **Ensemble Weight Configuration**: Two decimal values (summing to 1.0) defining how much each model contributes to final similarity (default: 0.6 ResNet + 0.4 EfficientNet)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Assignment rate increases from 60% to at least 70% on current dataset (11,570 detections)
- **SC-002**: For deer with 5+ sightings, at least 80% of detections correctly assigned to same profile
- **SC-003**: False positive rate (different deer matched together) remains below 5% for matches with similarity > 0.50
- **SC-004**: Processing time per detection stays under 3 seconds (allowing 50% increase from current ~2 seconds)
- **SC-005**: System successfully processes overnight batch of 5,000 images without memory errors or crashes
- **SC-006**: Similarity scores for true matches (same deer) increase by average of 10-15% compared to baseline
- **SC-007**: Re-embedding pipeline completes for all 165 deer profiles and 6,982 detections within 2 hours

### Assumptions

1. **GPU Availability**: RTX 4080 Super with 16GB VRAM remains available for processing (documented in system specs)
2. **Image Quality**: Deer crops maintain minimum 50x50 pixel size for meaningful feature extraction (existing system requirement)
3. **Model Performance**: EfficientNet-B0 provides complementary features to ResNet50 (based on literature showing ensemble benefits)
4. **Threshold Stability**: Current REID_THRESHOLD of 0.40 remains appropriate for new embeddings (will validate and adjust if needed)
5. **Data Sufficiency**: 6,982 existing assigned detections provide adequate validation set for before/after comparison
6. **Sex Classification**: Existing sex classification (buck/doe) remains reliable for sex-based filtering in Re-ID
7. **Backward Compatibility**: Storing dual embeddings (old + new) acceptable given database capacity

## Open Questions

*None identified - feature scope is well-defined based on established ML techniques and existing system architecture.*
