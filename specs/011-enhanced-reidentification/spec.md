# Feature Specification: Enhanced Re-Identification Pipeline

**Feature Branch**: `009-enhanced-reidentification`
**Created**: 2025-11-08
**Status**: Draft
**Input**: Improve individual deer identification accuracy beyond current ResNet50-only approach by adding complementary biometric features and temporal analysis

## Current Baseline *(context)*

**Existing Re-ID System (Sprint 5):**
- Model: ResNet50 pretrained on ImageNet
- Output: 512-dim feature embeddings (L2 normalized)
- Similarity: Cosine distance with 0.85 threshold
- Search: pgvector HNSW index for O(log N) queries
- Sex filtering: Match only within same sex category
- Performance: 0.88s feature extraction, 5.57ms inference (GPU)

**Known Limitations:**
1. Pose variation reduces matching accuracy (frontal vs profile vs rear views)
2. No antler-specific features for buck identification
3. Temporal/behavioral patterns not leveraged
4. Single model - no ensemble voting
5. Coat patterns and unique markings not explicitly extracted

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Antler Pattern Recognition for Mature Bucks (Priority: P1)

As a wildlife researcher, I need the system to recognize individual bucks by their unique antler configurations so that I can reliably track mature males across the entire hunting/rut season before they shed antlers.

**Why this priority**: Antlers are the most distinctive feature for mature bucks and remain constant for 8+ months (Aug-Feb). This is the highest-value quick win for improving buck re-identification.

**Independent Test**: Process 100 images of 5 known mature bucks (20 images each) from different dates/angles during rut season. Verify system correctly clusters images by individual based on antler features, achieving >90% accuracy for bucks with 8+ point antlers visible in profile/frontal poses.

**Acceptance Scenarios**:

1. **Given** detection of mature buck with visible antlers in profile pose, **When** extracting antler features, **Then** system identifies antler region (upper 30% of bbox), counts visible points/tines, measures spread width, and creates antler fingerprint vector
2. **Given** two images of same buck from different dates, **When** comparing antler fingerprints, **Then** system returns similarity score >0.85 indicating same individual
3. **Given** antler fingerprint combined with body re-ID features, **When** matching against deer database, **Then** system improves match confidence by 15-25% compared to body features alone
4. **Given** buck detection with antlers not visible (rear view, low resolution), **When** antler extraction fails, **Then** system gracefully falls back to body-only re-ID without raising error
5. **Given** post-shed season (Feb-July), **When** processing buck images without antlers, **Then** system flags profile as "antler-seasonal-mismatch" and relies solely on body features

---

### User Story 2 - Pose-Normalized Feature Extraction (Priority: P1)

As a wildlife researcher, I need the system to identify the same deer regardless of camera angle (frontal, profile, rear) so that I can accurately count unique individuals across multiple camera locations with varied positioning.

**Why this priority**: Current re-ID struggles with pose variation, causing same deer to create duplicate profiles. This is critical for accurate population counts.

**Independent Test**: Process 50 images of 10 known deer (5 images each: frontal, left profile, right profile, rear, angled). Verify system correctly groups all 5 poses of each deer into single profile with >85% accuracy.

**Acceptance Scenarios**:

1. **Given** deer detection, **When** running pose estimation, **Then** system detects keypoints (nose, ears, shoulder, hip, tail) and classifies pose as frontal/profile-left/profile-right/rear/angled
2. **Given** pose classification result, **When** extracting re-ID features, **Then** system applies pose-specific normalization to align features to canonical pose
3. **Given** same deer in frontal vs profile pose, **When** comparing normalized features, **Then** similarity score improves by 10-20% compared to non-normalized features
4. **Given** pose estimation confidence <60%, **When** normalization would be unreliable, **Then** system falls back to standard ResNet50 features with warning flag
5. **Given** 100 detections across all poses, **When** benchmarking pose-normalized vs standard re-ID, **Then** false negative rate (missed matches) decreases by >25%

---

### User Story 3 - Temporal Context Scoring (Priority: P2)

As a wildlife researcher, I need the system to use deer behavior patterns (time-of-day preferences, location habits) to improve identification confidence so that I can distinguish between similar-looking individuals.

**Why this priority**: Low-cost enhancement using existing data. Helps disambiguate deer with similar appearance by leveraging biological behavior patterns.

**Independent Test**: Identify 3 pairs of visually similar deer (does with similar body size/coat). Track their activity over 30 days. Verify temporal scoring correctly differentiates pairs based on time-of-day and location preferences with >80% accuracy when visual similarity is high (>0.75).

**Acceptance Scenarios**:

1. **Given** new detection with potential matches from database, **When** calculating temporal score, **Then** system analyzes historical patterns: location frequency (% visits per camera), time-of-day distribution (hourly histogram), seasonal presence (first/last seen dates)
2. **Given** candidate match with similar appearance (visual similarity 0.75-0.85), **When** temporal patterns align (same preferred location, same time-of-day window), **Then** system boosts match confidence by 0.05-0.10
3. **Given** candidate match with strong visual similarity (>0.85) but conflicting temporal patterns (detected simultaneously at different locations >1km apart), **When** evaluating match, **Then** system flags as "temporal-conflict" and reduces confidence or rejects match
4. **Given** deer with <5 historical sightings, **When** temporal data insufficient, **Then** system skips temporal scoring and relies solely on visual features
5. **Given** seasonal transitions (e.g., rut season increasing buck range), **When** applying temporal scoring, **Then** system applies season-specific weighting (lower temporal weight during rut Nov-Dec)

---

### User Story 4 - Coat Pattern & Marking Analysis (Priority: P2)

As a wildlife researcher, I need the system to identify unique coat markings (white chest patches, facial blazes, scars) so that I can reliably identify does and fawns that lack distinctive antlers.

**Why this priority**: Critical for doe/fawn identification where antlers unavailable. Persistent features across seasons (unlike antlers).

**Independent Test**: Manually tag 20 deer with distinctive markings (white chest patches, facial blazes, visible scars). Process 100 images of these deer. Verify system extracts and matches based on coat patterns with >75% accuracy.

**Acceptance Scenarios**:

1. **Given** deer detection, **When** analyzing coat patterns, **Then** system segments body into regions (chest, flanks, face, legs) and extracts color histograms per region
2. **Given** deer with white chest patch, **When** processing chest region, **Then** system detects high-contrast white area, measures size/shape, and adds to identification fingerprint
3. **Given** deer with facial blaze or unique facial markings, **When** in frontal/near-frontal pose, **Then** system extracts facial region features and weights them higher for matching
4. **Given** lighting variation between images (bright daylight vs dawn/dusk), **When** comparing coat patterns, **Then** system normalizes for illumination before matching to reduce false negatives
5. **Given** summer vs winter coat differences, **When** matching across seasons, **Then** system applies seasonal tolerance allowing 15-20% color histogram variation

---

### User Story 5 - Multi-Model Ensemble Voting (Priority: P3)

As a wildlife researcher, I need the system to combine predictions from multiple re-ID models so that I can achieve higher accuracy and reduce false positive deer profile creation.

**Why this priority**: Nice-to-have for maximum accuracy. Computationally expensive but provides best results for challenging cases. Lower priority due to cost vs incremental gain.

**Independent Test**: Process 200 challenging images (varied poses, lighting, partial occlusion). Compare single ResNet50 vs 3-model ensemble (ResNet50 + EfficientNet + ViT). Verify ensemble achieves >10% accuracy improvement and >30% reduction in false positive matches.

**Acceptance Scenarios**:

1. **Given** deer detection, **When** running ensemble re-ID, **Then** system extracts features using ResNet50, EfficientNet-B3, and Vision Transformer (ViT-B/16) in parallel
2. **Given** three feature vectors, **When** matching against database, **Then** each model produces similarity scores independently, then combined via weighted average (ResNet50: 0.4, EfficientNet: 0.3, ViT: 0.3)
3. **Given** ensemble similarity >0.90, **When** all models agree (individual scores >0.85), **Then** system marks as "high-confidence match" suitable for automatic profile assignment
4. **Given** ensemble similarity 0.75-0.85 with model disagreement, **When** scores vary >0.15 between models, **Then** system flags for manual review or creates new profile
5. **Given** processing time constraints, **When** user enables "fast mode", **Then** system uses ResNet50-only (current baseline) instead of ensemble

---

### Edge Cases

- What if antlers partially obscured by branches/vegetation? [Reduce antler feature weight, rely more on body features]
- How to handle velvet vs hardened antlers (seasonal variation)? [Antler shape consistent, ignore surface texture differences]
- What if deer never shows consistent pose across sightings? [Pose normalization may degrade quality; require >3 sightings before high confidence]
- How to handle fawns growing rapidly (changing body proportions)? [Age-based matching tolerance, increase threshold for fawns <1 year]
- What about lighting extremes (night IR vs bright daylight)? [Train models on augmented data with lighting variations, normalize features]
- How to reset antler features after shedding season? [Archive antler fingerprints by season (2024-rut, 2025-rut), match within season only]

---

## Requirements *(mandatory)*

### Functional Requirements

#### Antler Pattern Recognition

- **FR-001**: System MUST detect antler region as upper 30% of deer bounding box for classifications 'mature', 'mid', 'young'
- **FR-002**: System MUST extract antler features: point/tine count estimate, spread width (px), symmetry score (0-1), unique formation flags
- **FR-003**: System MUST create antler fingerprint as 64-dim feature vector combining geometric and visual features
- **FR-004**: System MUST store antler fingerprint separately in database with seasonal tagging (year-season: 2024-rut, 2025-rut)
- **FR-005**: System MUST combine antler fingerprint with body re-ID features using weighted fusion (antler: 0.4, body: 0.6 for profile poses)
- **FR-006**: System MUST gracefully fallback to body-only re-ID when antler extraction fails (rear pose, low resolution, occlusion)
- **FR-007**: System MUST flag potential profile duplicates when same buck detected with/without antlers across Feb shedding boundary

#### Pose-Normalized Features

- **FR-008**: System MUST perform pose estimation to detect keypoints: nose, left ear, right ear, shoulder, hip, tail base
- **FR-009**: System MUST classify pose into categories: frontal (0-30deg), profile-left (60-120deg), profile-right (240-300deg), rear (150-210deg), angled (other)
- **FR-010**: System MUST apply pose-specific feature normalization to align features to canonical profile pose before similarity comparison
- **FR-011**: System MUST store pose classification with each detection for analysis and debugging
- **FR-012**: System MUST fallback to standard ResNet50 when pose confidence <60% and log warning

#### Temporal Context Scoring

- **FR-013**: System MUST calculate temporal features for each deer profile: location frequency distribution (7 locations), time-of-day histogram (24 hourly bins), date range (first/last seen)
- **FR-014**: System MUST compute temporal similarity score (0-1) between new detection and candidate profiles based on pattern alignment
- **FR-015**: System MUST boost visual match confidence by 0.05-0.10 when temporal patterns align (location overlap >50%, time-of-day overlap >40%)
- **FR-016**: System MUST flag "temporal-conflict" and reduce confidence when simultaneous detections at distant locations (>1km apart, <5min time difference)
- **FR-017**: System MUST skip temporal scoring when deer profile has <5 historical sightings (insufficient data)
- **FR-018**: System MUST apply season-specific temporal weights: rut season (Nov-Dec) 0.3x weight, non-rut 1.0x weight

#### Coat Pattern Analysis

- **FR-019**: System MUST segment deer body into 4 regions: chest (lower 25%), flanks (middle 50%), face (upper front 15%), legs (lower 15%)
- **FR-020**: System MUST extract color histogram (16 bins per RGB channel = 48-dim) per body region
- **FR-021**: System MUST detect high-contrast markings: white patches (>2x brightness vs surrounding), dark spots, facial blazes
- **FR-022**: System MUST normalize color histograms for illumination before comparison (histogram equalization)
- **FR-023**: System MUST apply seasonal tolerance allowing 15-20% histogram variation to account for summer/winter coat changes
- **FR-024**: System MUST weight facial markings 2x higher when detected in frontal poses (<45deg angle)

#### Multi-Model Ensemble

- **FR-025**: System MUST support ensemble mode extracting features from 3 models: ResNet50, EfficientNet-B3, Vision Transformer (ViT-B/16)
- **FR-026**: System MUST combine model predictions via weighted average: ResNet50 (0.4), EfficientNet (0.3), ViT (0.3)
- **FR-027**: System MUST mark matches as "high-confidence" when ensemble score >0.90 AND all individual models agree (>0.85)
- **FR-028**: System MUST flag for manual review when ensemble score 0.75-0.85 with model disagreement (score variance >0.15)
- **FR-029**: System MUST provide "fast mode" option to use ResNet50-only (current baseline) instead of ensemble
- **FR-030**: System MUST parallelize model inference using GPU batch processing to minimize latency overhead

#### Integration & Configuration

- **FR-031**: System MUST provide configuration to enable/disable each enhancement independently: antler_recognition, pose_normalization, temporal_context, coat_patterns, ensemble_mode
- **FR-032**: System MUST expose enhanced re-ID as new Celery task: enhanced_reidentify_detection(detection_id, config)
- **FR-033**: System MUST maintain backward compatibility with existing reidentify_detection task (ResNet50-only)
- **FR-034**: System MUST log feature extraction breakdown showing contribution of each component: body (0.X), antler (0.Y), temporal (0.Z), coat (0.W)
- **FR-035**: System MUST store enhancement metadata in database: pose_detected, antler_visible, temporal_score, coat_features_extracted

### Non-Functional Requirements

#### Performance

- **NFR-001**: Antler feature extraction MUST complete within 0.2s per detection (GPU) without blocking re-ID pipeline
- **NFR-002**: Pose estimation MUST complete within 0.15s per detection using lightweight model (<50MB)
- **NFR-003**: Temporal scoring MUST complete within 0.05s per candidate match using indexed database queries
- **NFR-004**: Coat pattern extraction MUST complete within 0.1s per detection using efficient segmentation
- **NFR-005**: Ensemble mode (3 models) MUST complete within 0.5s per detection using GPU batch inference (vs 0.05s single model)
- **NFR-006**: Enhanced re-ID pipeline (all features enabled except ensemble) MUST maintain >10 detections/second throughput
- **NFR-007**: Database storage overhead MUST remain <500 bytes per detection for enhancement metadata

#### Accuracy Targets

- **NFR-008**: Antler-based buck re-ID MUST achieve >90% accuracy for mature bucks with 8+ point antlers in profile/frontal poses
- **NFR-009**: Pose-normalized re-ID MUST reduce false negative rate by >25% compared to baseline across all pose combinations
- **NFR-010**: Temporal context MUST improve disambiguation accuracy by >15% for visually similar deer pairs (similarity 0.75-0.85)
- **NFR-011**: Coat pattern analysis MUST achieve >75% accuracy for deer with distinctive markings (white patches, blazes)
- **NFR-012**: Ensemble mode MUST achieve >10% overall accuracy improvement and >30% false positive reduction vs single model baseline

#### Model Requirements

- **NFR-013**: Pose estimation model MUST be lightweight (<50MB) and compatible with CUDA for GPU acceleration
- **NFR-014**: EfficientNet and ViT models MUST be pretrained on ImageNet or wildlife-specific datasets (iNaturalist)
- **NFR-015**: All models MUST support batch inference with batch_size=16 for processing efficiency
- **NFR-016**: Antler feature extractor MUST handle image resolutions from 224x224 to 1024x1024 without degradation

### Key Entities

- **AntlerFingerprint**: Feature vector (64-dim) containing: point_count_estimate (int), spread_width_px (float), symmetry_score (0-1), tine_angles (array), unique_formations (flags), seasonal_tag (str: "2024-rut")
- **PoseEstimation**: Keypoint coordinates (x, y, confidence) for: nose, left_ear, right_ear, shoulder, hip, tail_base; pose_classification (enum), pose_angle (degrees), confidence_score (0-1)
- **TemporalProfile**: Activity patterns per deer: location_frequency (dict: location_id -> count), time_of_day_histogram (24-element array), first_seen (datetime), last_seen (datetime), sighting_count (int), seasonal_presence (array of season tags)
- **CoatPattern**: Body region features: chest_histogram (48-dim), flank_histogram (48-dim), face_histogram (48-dim), detected_markings (array of {type, region, size, contrast}), seasonal_tag (str)
- **EnhancedReIDResult**: Combined re-ID output: visual_similarity (0-1), temporal_similarity (0-1), antler_similarity (0-1), coat_similarity (0-1), ensemble_scores (dict: model -> score), final_confidence (0-1), match_deer_id (UUID or null), flags (array: "high-confidence", "temporal-conflict", "manual-review")
- **ReIDConfig**: Feature flags: enable_antler (bool), enable_pose_norm (bool), enable_temporal (bool), enable_coat (bool), enable_ensemble (bool), fast_mode (bool), similarity_threshold (float)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

#### Phase 1: Antler Recognition + Temporal Context (MVP)

- **SC-001**: Process 100 images of 5 known mature bucks (20 each) during rut season. Achieve >90% correct clustering based on antler+body features
- **SC-002**: Antler feature extraction completes in <0.2s per detection on RTX 4080 Super GPU
- **SC-003**: Temporal scoring improves match accuracy by >15% for 10 pairs of visually similar deer (similarity 0.75-0.85) tracked over 30 days
- **SC-004**: Combined antler+temporal+body re-ID reduces false positive profile creation by >20% compared to body-only baseline on rut season dataset (6,115 images)

#### Phase 2: Pose Normalization (High Impact)

- **SC-005**: Process 50 images of 10 known deer (5 poses each). Achieve >85% correct grouping across frontal/profile/rear poses
- **SC-006**: Pose-normalized re-ID reduces false negative rate by >25% on multi-pose test set (500 images, varied angles)
- **SC-007**: Pose estimation completes in <0.15s per detection using lightweight model (<50MB)

#### Phase 3: Coat Patterns (Doe Enhancement)

- **SC-008**: Process 100 images of 20 deer with distinctive markings. Achieve >75% matching accuracy based on coat features
- **SC-009**: Coat pattern extraction improves doe re-ID accuracy by >20% compared to body-only baseline (does lack antler features)

#### Phase 4: Ensemble Mode (Maximum Accuracy)

- **SC-010**: Three-model ensemble achieves >10% overall accuracy improvement vs single ResNet50 on challenging test set (200 images: varied poses, lighting, occlusion)
- **SC-011**: Ensemble mode reduces false positive matches by >30% when used with high-confidence threshold (0.90)
- **SC-012**: Ensemble inference completes in <0.5s per detection using GPU batch processing

#### System Integration

- **SC-013**: Enhanced re-ID pipeline (antler+pose+temporal+coat, no ensemble) maintains >10 detections/second throughput on RTX 4080 Super
- **SC-014**: Database storage overhead for enhancement metadata remains <500 bytes per detection
- **SC-015**: All enhancements can be toggled independently via configuration without code changes or service restart

---

## Assumptions

- **ASSUMPTION-001**: RTX 4080 Super GPU (16GB VRAM) has sufficient capacity to load 3 models simultaneously for ensemble mode (estimated 6GB total)
- **ASSUMPTION-002**: Antler features only applicable Aug-Feb (rut/hunting season); system will gracefully handle off-season (Mar-Jul) when bucks lack antlers
- **ASSUMPTION-003**: Pose estimation model (lightweight keypoint detector) available pretrained on wildlife/animal datasets or can be fine-tuned from COCO human pose model
- **ASSUMPTION-004**: Trail camera image quality sufficient for antler point counting at distances up to 15-20 meters (typical camera range)
- **ASSUMPTION-005**: Temporal patterns stable across weeks but may shift seasonally (e.g., rut increases buck range); season-specific weighting required
- **ASSUMPTION-006**: Coat patterns sufficiently stable across 6-12 months to enable cross-season matching (excluding summer/winter coat transition periods)
- **ASSUMPTION-007**: EfficientNet and Vision Transformer models can be downloaded from Hugging Face or torchvision and do not require custom training initially
- **ASSUMPTION-008**: False positive deer profile creation is more problematic than false negatives (prefer conservative matching to avoid duplicate profiles)

---

## Implementation Phases *(recommended)*

### Phase 1: Temporal Context + Antler Recognition (2-3 weeks)
**Priority**: P1 (High value, low complexity)
**Goal**: Improve buck re-ID and leverage existing data

**Tasks**:
1. Implement temporal profile calculation (location frequency, time-of-day histogram)
2. Add temporal similarity scoring to re-ID pipeline
3. Create antler region detection using bbox geometry
4. Extract basic antler features (point count, spread, symmetry)
5. Combine antler + body features with weighted fusion
6. Database schema: add antler_fingerprint, temporal_profile columns
7. Test on rut season dataset (6,115 images)

**Deliverables**:
- Temporal scoring functional with >15% accuracy improvement on similar deer
- Antler recognition achieving >90% accuracy on mature bucks in profile/frontal poses

---

### Phase 2: Pose Normalization (2-3 weeks)
**Priority**: P1 (High impact, moderate complexity)
**Goal**: Reduce pose-related matching failures

**Tasks**:
1. Integrate lightweight pose estimation model (e.g., MMPose, Detectron2)
2. Fine-tune on deer images if needed (transfer from COCO)
3. Implement pose classification (frontal/profile/rear/angled)
4. Create pose-specific feature normalization functions
5. Benchmark pose-normalized vs standard re-ID
6. Database schema: add pose_keypoints, pose_classification columns
7. Test on multi-pose dataset (50 images x 10 deer x 5 poses)

**Deliverables**:
- Pose estimation running at <0.15s per detection
- False negative rate reduced by >25% across pose variations

---

### Phase 3: Coat Pattern Analysis (2 weeks)
**Priority**: P2 (Important for does, moderate complexity)
**Goal**: Improve doe/fawn re-ID where antlers unavailable

**Tasks**:
1. Implement body region segmentation (chest/flanks/face/legs)
2. Extract color histograms per region (48-dim per region)
3. Detect high-contrast markings (white patches, blazes)
4. Implement illumination normalization
5. Add seasonal tolerance for coat color variation
6. Database schema: add coat_pattern column (JSON or vector)
7. Test on 20 deer with distinctive markings (100 images)

**Deliverables**:
- Coat pattern matching achieving >75% accuracy on marked deer
- Doe re-ID accuracy improved by >20% vs body-only baseline

---

### Phase 4: Multi-Model Ensemble (3-4 weeks)
**Priority**: P3 (Maximum accuracy but expensive, high complexity)
**Goal**: Achieve best possible re-ID performance

**Tasks**:
1. Integrate EfficientNet-B3 model (download pretrained)
2. Integrate Vision Transformer ViT-B/16 (download pretrained)
3. Implement parallel GPU batch inference for 3 models
4. Create weighted voting system (ResNet50: 0.4, others: 0.3 each)
5. Implement high-confidence and manual-review flagging
6. Add "fast mode" toggle for ResNet50-only
7. Benchmark 1-model vs 3-model ensemble on challenging dataset (200 images)

**Deliverables**:
- Ensemble achieving >10% accuracy improvement vs single model
- False positives reduced by >30% at 0.90 threshold
- Inference time <0.5s per detection with batch processing

---

### Phase 5: Integration & Optimization (1-2 weeks)
**Priority**: P1 (Required for production)
**Goal**: Production-ready deployment

**Tasks**:
1. Create ReIDConfig system for feature toggles
2. Implement enhanced_reidentify_detection Celery task
3. Add logging for feature contribution breakdown
4. Performance optimization (GPU memory, batch sizes)
5. Database migration for new columns
6. Documentation and testing
7. Benchmark full pipeline throughput (target: >10 detections/sec)

**Deliverables**:
- All features configurable via settings
- Backward compatibility maintained
- Production deployment ready

---

## Related Specifications

- **Sprint 5**: Re-identification baseline (ResNet50, pgvector)
- **Sprint 4**: Multi-class classification (mature/mid/young buck detection)
- **008-rut-season-analysis**: Seasonal analysis requiring accurate buck tracking

---

## Open Questions

1. **Pose estimation model selection**: Use MMPose, Detectron2, or custom lightweight model?
2. **Antler shedding transition**: How to handle Feb-Mar when some bucks shed early, others retain?
3. **Model hosting**: Store 3 ensemble models (total ~500MB) in Git LFS or download on-demand?
4. **Manual review UI**: Need frontend interface for "manual-review" flagged detections?
5. **Training data**: Should we collect labeled deer pose dataset for fine-tuning, or rely on transfer learning?
6. **Ensemble weights**: Use fixed weights (0.4/0.3/0.3) or learn optimal weights from validation data?
