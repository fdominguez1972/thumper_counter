# Tasks: Re-ID Enhancement - Multi-Scale and Ensemble Learning

**Input**: Design documents from `/specs/009-reid-enhancement/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: Tests are OPTIONAL for this feature - only included where explicitly needed for validation

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (Setup, Foundation, US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency management

- [X] T001 Install efficientnet-pytorch dependency in requirements.txt
- [X] T002 Update docker-compose.yml to mount src/worker/models/ directory
- [X] T003 [P] Create directory structure: src/worker/models/ for new model architectures
- [X] T004 [P] Create directory structure: scripts/ for re-embedding and validation scripts

**Estimated Time**: 15 minutes

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

### Database Schema Migration

- [X] T005 Create migration script migrations/012_add_reid_enhancement.sql
- [X] T006 Add feature_vector_multiscale VECTOR(512) column to deer table
- [X] T007 Add feature_vector_efficientnet VECTOR(512) column to deer table
- [X] T008 Add embedding_version VARCHAR(20) column to deer table with default 'v1_resnet50'
- [X] T009 Create HNSW index ix_deer_feature_vector_multiscale_hnsw with parameters (m=16, ef_construction=64)
- [X] T010 Create HNSW index ix_deer_feature_vector_efficientnet_hnsw with parameters (m=16, ef_construction=64)
- [X] T011 Create B-tree index ix_deer_embedding_version on embedding_version column
- [X] T012 Add column comments documenting multi-scale and ensemble embeddings
- [X] T013 Add migration validation checks (verify 3 columns and 3 indexes created)
- [X] T014 Execute migration on database: docker-compose exec db psql -U deertrack deer_tracking -f /app/migrations/012_add_reid_enhancement.sql

### Database Model Updates

- [X] T015 Update src/backend/models/deer.py to add feature_vector_multiscale column (SQLAlchemy VECTOR type)
- [X] T016 Update src/backend/models/deer.py to add feature_vector_efficientnet column (SQLAlchemy VECTOR type)
- [X] T017 Update src/backend/models/deer.py to add embedding_version column (String type, default='v1_resnet50')

### Multi-Scale ResNet50 Architecture

- [X] T018 Create src/worker/models/multiscale_resnet.py module
- [X] T019 [US1] Implement build_multiscale_resnet50() function to load pretrained ResNet50
- [X] T020 [US1] Add hook registration for layer2, layer3, layer4, avgpool feature extraction
- [X] T021 [US1] Implement AdaptiveAvgPool2d layers: layer2(4,4), layer3(2,2), layer4(1,1)
- [X] T022 [US1] Implement Linear reduction layers: layer2(8192->128), layer3(4096->128), layer4(2048->128), avgpool(2048->128)
- [X] T023 [US1] Implement feature concatenation logic (4 x 128-dim = 512-dim output)
- [X] T024 [US1] Implement L2 normalization for final 512-dim embedding
- [X] T025 [US1] Add thread-safe model loading with double-checked locking pattern
- [X] T026 [US1] Add GPU device placement (.to(DEVICE)) and eval mode (.eval())

### EfficientNet-B0 Architecture

- [X] T027 [P] Create src/worker/models/efficientnet_extractor.py module
- [X] T028 [P] [US1] Implement build_efficientnet_b0() function using torchvision.models.efficientnet_b0
- [X] T029 [P] [US1] Load pretrained weights: EfficientNet_B0_Weights.IMAGENET1K_V1
- [X] T030 [P] [US1] Remove classifier head, keep feature extractor only
- [X] T031 [P] [US1] Add adaptive pooling to produce 512-dim output (from 1280-dim base)
- [X] T032 [P] [US1] Implement L2 normalization for 512-dim embedding
- [X] T033 [P] [US1] Add thread-safe model loading with double-checked locking pattern
- [X] T034 [P] [US1] Add GPU device placement (.to(DEVICE)) and eval mode (.eval())

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

**Estimated Time**: 3 hours

---

## Phase 3: User Story 1 - Improved Automatic Deer Matching (Priority: P1)

**Goal**: Enhance re-identification accuracy from 60% to 70-75% through multi-scale and ensemble embeddings

**Independent Test**: Process validation set of known deer with multiple sightings and measure assignment accuracy

### Multi-Scale Feature Extraction Implementation

- [ ] T035 [US1] Update src/worker/tasks/reidentification.py to import multiscale_resnet module
- [ ] T036 [US1] Update src/worker/tasks/reidentification.py to import efficientnet_extractor module
- [ ] T037 [US1] Add get_multiscale_model() singleton function with thread-safe loading
- [ ] T038 [US1] Add get_efficientnet_model() singleton function with thread-safe loading
- [ ] T039 [US1] Implement extract_multiscale_features(crop_image) function returning 512-dim embedding
- [ ] T040 [US1] Implement extract_efficientnet_features(crop_image) function returning 512-dim embedding
- [ ] T041 [US1] Update extract_deer_features() to call both multi-scale and EfficientNet extractors
- [ ] T042 [US1] Return tuple (multiscale_embedding, efficientnet_embedding) from extract_deer_features()

### Ensemble Similarity Computation

- [ ] T043 [US1] Implement compute_ensemble_similarity(det_ms, det_en, deer_ms, deer_en, weights=(0.6, 0.4))
- [ ] T044 [US1] Compute cosine similarity for multi-scale embeddings (det_ms vs deer_ms)
- [ ] T045 [US1] Compute cosine similarity for EfficientNet embeddings (det_en vs deer_en)
- [ ] T046 [US1] Compute weighted average: 0.6 * sim_ms + 0.4 * sim_en
- [ ] T047 [US1] Return final ensemble similarity score (0.0 to 1.0)

### Re-ID Pipeline Integration

- [ ] T048 [US1] Add USE_ENHANCED_REID environment variable flag (default=false for backward compatibility)
- [ ] T049 [US1] Update find_matching_deer() to use ensemble similarity when USE_ENHANCED_REID=true
- [ ] T050 [US1] Query deer.feature_vector_multiscale and deer.feature_vector_efficientnet from database
- [ ] T051 [US1] Fallback to deer.feature_vector for deer without enhanced embeddings
- [ ] T052 [US1] Update create_new_deer_profile() to store both multiscale_embedding and efficientnet_embedding
- [ ] T053 [US1] Set embedding_version='v3_ensemble' when creating new deer with enhanced embeddings
- [ ] T054 [US1] Add logging for embedding extraction time (multi-scale + EfficientNet)
- [ ] T055 [US1] Add logging for similarity score comparison (old vs new)

### Re-Embedding Existing Deer Profiles

- [ ] T056 [US1] Create scripts/re_embed_multiscale.py script
- [ ] T057 [US1] Query all deer with assigned detections (165 deer, 6,982 detections)
- [ ] T058 [US1] For each deer, find best quality detection (highest confidence, largest bbox)
- [ ] T059 [US1] Extract deer crop from original image file
- [ ] T060 [US1] Generate multi-scale embedding using build_multiscale_resnet50()
- [ ] T061 [US1] Generate EfficientNet embedding using build_efficientnet_b0()
- [ ] T062 [US1] Update database: SET feature_vector_multiscale, feature_vector_efficientnet, embedding_version='v3_ensemble'
- [ ] T063 [US1] Add progress logging every 10 deer (e.g., "Progress: 10/165 (6.1%)")
- [ ] T064 [US1] Add --resume flag to skip deer with existing enhanced embeddings
- [ ] T065 [US1] Validate embeddings: check L2 norm = 1.0 for all generated vectors
- [ ] T066 [US1] Log total re-embedding time and average time per deer

### Validation Script

- [ ] T067 [US1] Create scripts/validate_embeddings.py script
- [ ] T068 [US1] Select 20 deer with 5+ sightings for validation
- [ ] T069 [US1] Compare similarity scores: old embedding vs old embedding (baseline)
- [ ] T070 [US1] Compare similarity scores: new multi-scale vs new multi-scale
- [ ] T071 [US1] Compare similarity scores: new ensemble (weighted) vs new ensemble
- [ ] T072 [US1] Calculate average improvement percentage for true matches (target: 10-15%)
- [ ] T073 [US1] Select 20 pairs of different deer (same sex) for false positive check
- [ ] T074 [US1] Verify new embeddings maintain low similarity (<0.40) for non-matches
- [ ] T075 [US1] Generate similarity score distribution histogram (old vs new)
- [ ] T076 [US1] Output validation report: PASS if improvement >= 10% and FP rate < 5%
- [ ] T077 [US1] Save validation results to logs/validation_YYYYMMDD_HHMMSS.txt

**Checkpoint**: At this point, User Story 1 should be fully functional with enhanced Re-ID accuracy

**Estimated Time**: 8 hours

---

## Phase 4: User Story 2 - Reduced False Positives (Priority: P2)

**Goal**: Reduce false positive rate (different deer incorrectly merged) to below 5% for matches with similarity > 0.50

**Independent Test**: Measure precision on validation set with known distinct deer pairs

### Ensemble Weight Tuning

- [ ] T078 [US2] Create scripts/tune_ensemble_weights.py script
- [ ] T079 [US2] Test ensemble weight combinations: (0.5, 0.5), (0.6, 0.4), (0.7, 0.3), (0.8, 0.2)
- [ ] T080 [US2] For each weight combination, compute similarity scores on validation set
- [ ] T081 [US2] Calculate true positive rate (TPR) and false positive rate (FPR) for each combination
- [ ] T082 [US2] Generate ROC curve plotting TPR vs FPR for different thresholds
- [ ] T083 [US2] Identify optimal ensemble weights that maximize TPR while keeping FPR < 5%
- [ ] T084 [US2] Update ENSEMBLE_WEIGHTS constant in src/worker/tasks/reidentification.py
- [ ] T085 [US2] Document final weight selection rationale in validation report

### Threshold Adjustment

- [ ] T086 [US2] Create scripts/analyze_similarity_distribution.py script
- [ ] T087 [US2] Query all similarity scores from recent detections (last 7 days)
- [ ] T088 [US2] Separate scores into: true matches (same deer) vs false matches (different deer)
- [ ] T089 [US2] Plot histogram showing distribution of true matches vs false matches
- [ ] T090 [US2] Calculate optimal threshold using F1-score maximization
- [ ] T091 [US2] Verify false positive rate < 5% at chosen threshold
- [ ] T092 [US2] Update REID_THRESHOLD in .env if needed (current: 0.40)
- [ ] T093 [US2] Add confidence intervals to validation report (95% CI for FPR)

### False Positive Monitoring

- [ ] T094 [US2] Add similarity_score column to detections table (store match confidence)
- [ ] T095 [US2] Update reidentification.py to log similarity_score when assigning deer_id
- [ ] T096 [US2] Create database index on detections(similarity_score) for analytics
- [ ] T097 [US2] Create scripts/monitor_false_positives.py script
- [ ] T098 [US2] Query high-confidence matches (similarity > 0.50) from last 24 hours
- [ ] T099 [US2] For each match, verify: same sex, similar body size, compatible timestamps
- [ ] T100 [US2] Flag suspicious matches for manual review (different locations within short time)
- [ ] T101 [US2] Output daily false positive rate report to logs/fp_monitoring_YYYYMMDD.txt

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently with improved accuracy and reduced false positives

**Estimated Time**: 5 hours

---

## Phase 5: User Story 3 - Faster Processing with Maintained Accuracy (Priority: P3)

**Goal**: Maintain processing time under 3 seconds per detection while delivering enhanced accuracy

**Independent Test**: Benchmark processing time on standard image batches (100 detections)

### Performance Benchmarking

- [ ] T102 [US3] Create scripts/benchmark_reid.py script
- [ ] T103 [US3] Select 100 representative deer detections (various sizes, angles, lighting)
- [ ] T104 [US3] Measure baseline: original single-layer ResNet50 processing time
- [ ] T105 [US3] Measure multi-scale ResNet50: feature extraction time per detection
- [ ] T106 [US3] Measure EfficientNet-B0: feature extraction time per detection
- [ ] T107 [US3] Measure database query time: HNSW similarity search on 2 vectors
- [ ] T108 [US3] Measure total end-to-end time: extraction + search + assignment
- [ ] T109 [US3] Calculate throughput: detections per second (target: maintain > 0.3 det/s)
- [ ] T110 [US3] Generate performance report comparing baseline vs enhanced system

### GPU Memory Optimization

- [ ] T111 [US3] Create scripts/test_gpu_memory.py script
- [ ] T112 [US3] Load both models (multi-scale ResNet50 + EfficientNet-B0) simultaneously
- [ ] T113 [US3] Monitor GPU memory usage using nvidia-smi during inference
- [ ] T114 [US3] Test with different batch sizes: 1, 8, 16, 32 images
- [ ] T115 [US3] Identify maximum safe batch size keeping VRAM < 12GB (75% of 16GB)
- [ ] T116 [US3] Verify no CUDA out-of-memory errors during batch processing
- [ ] T117 [US3] Document optimal batch size in quickstart.md

### Model Loading Optimization

- [ ] T118 [US3] Add model caching warmup on worker startup (load models once)
- [ ] T119 [US3] Verify double-checked locking prevents redundant model loads
- [ ] T120 [US3] Test concurrent worker threads (concurrency=32) for race conditions
- [ ] T121 [US3] Measure model loading time: cold start vs warm cache
- [ ] T122 [US3] Optimize image preprocessing: resize + normalize pipeline
- [ ] T123 [US3] Consider torch.no_grad() context for all inference (disable gradients)
- [ ] T124 [US3] Consider model.half() for FP16 inference if VRAM becomes constrained

### Batch Processing Validation

- [ ] T125 [US3] Test overnight batch: 5,000 images with enhanced Re-ID
- [ ] T126 [US3] Monitor worker logs for crashes or memory errors
- [ ] T127 [US3] Verify all detections processed successfully (no timeouts)
- [ ] T128 [US3] Calculate actual throughput: total images / total time
- [ ] T129 [US3] Compare to target: 239,040 images processable in 8 hours (8.3 img/s)
- [ ] T130 [US3] Document performance metrics in validation report

**Checkpoint**: All user stories should now be independently functional with validated performance

**Estimated Time**: 4 hours

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, testing, and deployment preparation

### Documentation

- [ ] T131 [P] Update docs/SESSION_HANDOFF.md with re-ID enhancement deployment
- [ ] T132 [P] Update README.md with enhanced Re-ID features section
- [ ] T133 [P] Document ensemble weights tuning process in specs/009-reid-enhancement/
- [ ] T134 [P] Document rollback procedure in quickstart.md
- [ ] T135 [P] Create migration checklist in quickstart.md (pre/post validation)

### Testing & Validation

- [ ] T136 Create test_multiscale_extraction.py script for manual testing
- [ ] T137 Create test_ensemble_matching.py script for manual testing (same deer + different deer)
- [ ] T138 Run full validation suite: scripts/validate_embeddings.py
- [ ] T139 Verify all 165 deer have v3_ensemble embeddings (NULL check query)
- [ ] T140 Verify L2 normalization: all embeddings have magnitude = 1.0
- [ ] T141 Test rollback procedure: disable USE_ENHANCED_REID and verify fallback

### Deployment Preparation

- [ ] T142 Create database backup before cutover: pg_dump pre_enhanced_reid.sql
- [ ] T143 Set USE_ENHANCED_REID=true in .env
- [ ] T144 Restart worker container: docker-compose restart worker
- [ ] T145 Monitor worker logs for "Enhanced Re-ID enabled" message
- [ ] T146 Process test batch (100 images) and verify correct assignment
- [ ] T147 Monitor assignment rate dashboard for 24 hours
- [ ] T148 Run quickstart.md validation steps end-to-end
- [ ] T149 Document post-deployment metrics in deployment report

### Performance Validation

- [ ] T150 Verify processing time < 3s per detection (check worker logs)
- [ ] T151 Verify GPU memory usage < 12GB (check nvidia-smi)
- [ ] T152 Verify HNSW index search time < 10ms (check query logs)
- [ ] T153 Verify assignment rate increase: 60% -> 70-75%
- [ ] T154 Verify false positive rate < 5% for similarity > 0.50
- [ ] T155 Create final performance report comparing before/after metrics

**Estimated Time**: 3 hours

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
  - User Story 1 (US1): Can start after Foundational - HIGHEST PRIORITY
  - User Story 2 (US2): Depends on US1 completion (needs enhanced embeddings to tune)
  - User Story 3 (US3): Can run in parallel with US2 (independent benchmarking)
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories (CRITICAL PATH)
- **User Story 2 (P2)**: Depends on US1 completion (needs enhanced embeddings to analyze false positives)
- **User Story 3 (P3)**: Can start after Foundational - Independent performance benchmarking

### Within Each User Story

**User Story 1 (US1)**:
1. Multi-Scale ResNet50 architecture (T019-T026)
2. EfficientNet-B0 architecture (T027-T034) - Can run in parallel with multi-scale
3. Feature extraction implementation (T035-T042)
4. Ensemble similarity (T043-T047)
5. Re-ID pipeline integration (T048-T055)
6. Re-embedding script (T056-T066) - Runs after integration complete
7. Validation script (T067-T077) - Runs after re-embedding complete

**User Story 2 (US2)**:
1. Ensemble weight tuning (T078-T085) - Requires US1 embeddings
2. Threshold adjustment (T086-T093) - Can run in parallel with weight tuning
3. False positive monitoring (T094-T101) - Runs after tuning complete

**User Story 3 (US3)**:
1. All tasks can run in parallel (independent benchmarking)
2. Final batch validation (T125-T130) runs last

### Parallel Opportunities

**Phase 1 (Setup)**: All 4 tasks can run in parallel

**Phase 2 (Foundational)**:
- Database migration (T005-T014): Sequential
- Database model updates (T015-T017): Can run in parallel with migration
- Multi-scale architecture (T018-T026): Can run in parallel with EfficientNet
- EfficientNet architecture (T027-T034): Can run in parallel with multi-scale

**Phase 3 (US1)**:
- Multi-scale implementation (T019-T026) || EfficientNet implementation (T027-T034)
- After both complete: Feature extraction (T035-T042) -> Pipeline integration (T048-T055) -> Re-embedding (T056-T066) -> Validation (T067-T077)

**Phase 4 (US2)**:
- Weight tuning (T078-T085) || Threshold adjustment (T086-T093)
- After both complete: False positive monitoring (T094-T101)

**Phase 5 (US3)**:
- All benchmarking tasks (T102-T124) can run in parallel
- Batch validation (T125-T130) runs last

**Phase 6 (Polish)**:
- Documentation (T131-T135): All parallel
- Testing (T136-T141): Sequential execution
- Deployment (T142-T149): Sequential execution
- Performance validation (T150-T155): Can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (15 minutes)
2. Complete Phase 2: Foundational (3 hours)
3. Complete Phase 3: User Story 1 (8 hours)
4. **STOP and VALIDATE**: Run validation script (scripts/validate_embeddings.py)
5. If validation passes (10-15% improvement), proceed to deployment
6. If validation fails, debug and retry US1

**Total MVP Time**: ~11-12 hours

### Incremental Delivery

1. **Foundation Ready** (Phase 1 + 2): Database schema, models loaded, ready for enhancement
2. **MVP Deployed** (+ Phase 3): Enhanced Re-ID active, 70-75% assignment rate
3. **Quality Improved** (+ Phase 4): False positive rate < 5%, tuned thresholds
4. **Performance Validated** (+ Phase 5): Confirmed < 3s per detection, GPU optimized
5. **Production Ready** (+ Phase 6): Documented, tested, monitored

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (3.25 hours)
2. Once Foundational is done:
   - **Developer A**: User Story 1 (CRITICAL PATH - 8 hours)
   - **Developer B**: Prepare User Story 3 benchmarking scripts (can start early)
3. After US1 complete:
   - **Developer A**: User Story 2 (5 hours)
   - **Developer B**: User Story 3 validation (4 hours)
4. **Developer A + B**: Phase 6 Polish together (3 hours)

**Total Team Time**: ~12 hours (vs ~23 hours sequential)

---

## Success Metrics

### User Story 1 Success Criteria

- [ ] Assignment rate increases from 60% to at least 70% (target: 75%)
- [ ] For deer with 5+ sightings, at least 80% of detections correctly assigned
- [ ] Similarity scores for true matches increase by 10-15% on average
- [ ] All 165 deer profiles have v3_ensemble embeddings
- [ ] Re-embedding completes in under 2 hours
- [ ] Validation script outputs [PASS] for all checks

### User Story 2 Success Criteria

- [ ] False positive rate < 5% for matches with similarity > 0.50
- [ ] No different deer incorrectly merged into same profile
- [ ] Optimal ensemble weights identified and documented
- [ ] Similarity score distribution shows clear separation between matches/non-matches

### User Story 3 Success Criteria

- [ ] Processing time per detection < 3 seconds (target: ~136ms actual)
- [ ] GPU VRAM usage < 12GB (target: ~2GB actual)
- [ ] Overnight batch of 5,000 images processes without crashes
- [ ] System maintains throughput of at least 8.3 images/second
- [ ] Performance benchmarks documented in validation report

### Overall Feature Success

- [ ] All 3 user stories pass independent validation
- [ ] Enhanced Re-ID enabled in production (USE_ENHANCED_REID=true)
- [ ] 24-hour monitoring shows stable performance
- [ ] Rollback procedure tested and documented
- [ ] Database backup created before cutover
- [ ] Session handoff document created with deployment details

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability (US1, US2, US3)
- Each user story should be independently testable
- Commit after each logical group of tasks (e.g., after T026, T034, T055, etc.)
- Stop at checkpoints to validate story independently
- US1 is CRITICAL PATH - prioritize completion before US2/US3
- US2 depends on US1 (needs enhanced embeddings)
- US3 can run parallel to US2 (independent benchmarking)
- Validation scripts are critical - do not skip
- Monitor GPU memory during all testing phases
- Keep database backups before major schema changes
- Document all ensemble weight decisions with rationale

---

## Total Task Count

- **Phase 1 (Setup)**: 4 tasks
- **Phase 2 (Foundational)**: 30 tasks
- **Phase 3 (User Story 1)**: 43 tasks
- **Phase 4 (User Story 2)**: 24 tasks
- **Phase 5 (User Story 3)**: 29 tasks
- **Phase 6 (Polish)**: 25 tasks

**Total**: 155 tasks

**Estimated Time**: 23 hours (sequential) or ~12 hours (parallel team)

**MVP Scope** (Recommended First Deployment): Phase 1 + Phase 2 + Phase 3 (User Story 1 only) = ~11-12 hours
