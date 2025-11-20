# Tasks: Critical Infrastructure Fixes

**Input**: Design documents from `/specs/010-infrastructure-fixes/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Comprehensive automated tests included using pytest framework

**Organization**: Tasks are grouped by user story (Option A, Option B, Option D) to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which option/user story this task belongs to (USA, USB, USD)
- Include exact file paths in descriptions

## Path Conventions

- **Backend API**: `src/backend/api/`, `src/backend/schemas/`
- **Worker Tasks**: `src/worker/tasks/`, `src/worker/`
- **Analysis Scripts**: `scripts/`
- **Documentation**: `docs/`
- **Tests**: `tests/api/`, `tests/worker/`, `tests/scripts/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify environment and prerequisites for all three options

- [ ] T001 Verify Redis container running and accessible (docker-compose ps | grep redis)
- [ ] T002 [P] Verify redis-py installed in worker environment (docker-compose exec worker pip list | grep redis)
- [ ] T003 [P] Verify matplotlib, seaborn installed for analysis scripts (docker-compose exec worker pip list | grep -E "matplotlib|seaborn")
- [ ] T004 [P] Verify pytest installed for testing (docker-compose exec backend pip list | grep pytest)
- [ ] T005 Install missing Python dependencies if needed (add seaborn==0.13.0, scipy==1.11.4, pytest-mock==3.12.0 to requirements.txt)
- [ ] T006 Create analysis output directory (mkdir -p docs/reid_analysis/)
- [ ] T007 Create test directory structure (mkdir -p tests/api tests/worker tests/scripts)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 Create Redis client initialization in src/backend/app/main.py (import Redis, create redis_client)
- [ ] T009 Verify Redis client accessible in worker (src/worker/celery_app.py has Redis connection)
- [ ] T010 Create validation helper module in src/backend/api/validation.py (shared validation functions)
- [ ] T011 Update export schemas to import validation helpers in src/backend/schemas/export.py
- [ ] T012 [P] Create test fixtures for Redis in tests/conftest.py (redis_client fixture with fakeredis)
- [ ] T013 [P] Create test fixtures for database in tests/conftest.py (test_db session fixture)
- [ ] T014 [P] Create test fixtures for Celery in tests/conftest.py (mock celery_app fixture)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 (Option A) - Export Job Status Tracking (Priority: P1) 🎯 MVP

**Goal**: Worker tasks update Redis with job completion status, API polls Redis for status

**Independent Test**: Create PDF export, poll status endpoint, verify transitions from "processing" to "completed" with download URL

### Tests for Option A (Write FIRST, ensure they FAIL)

> **NOTE: Write these tests FIRST before implementation, ensure they FAIL, then implement to make them PASS**

- [ ] T015 [P] [USA] Create test_export_status_redis.py in tests/worker/ (test Redis status updates)
- [ ] T016 [P] [USA] Test worker writes "completed" status to Redis in tests/worker/test_export_status_redis.py
- [ ] T017 [P] [USA] Test worker writes "failed" status on exception in tests/worker/test_export_status_redis.py
- [ ] T018 [P] [USA] Test Redis TTL set to 3600 seconds in tests/worker/test_export_status_redis.py
- [ ] T019 [P] [USA] Test JSON structure includes all required fields in tests/worker/test_export_status_redis.py
- [ ] T020 [P] [USA] Create test_export_status_api.py in tests/api/ (test API status polling)
- [ ] T021 [P] [USA] Test GET /api/exports/pdf/{job_id} returns 200 with status in tests/api/test_export_status_api.py
- [ ] T022 [P] [USA] Test GET /api/exports/pdf/{job_id} returns 404 when job not found in tests/api/test_export_status_api.py
- [ ] T023 [P] [USA] Test GET /api/exports/pdf/{job_id} returns 404 when job expired in tests/api/test_export_status_api.py
- [ ] T024 [P] [USA] Test GET /api/exports/zip/{job_id} returns status correctly in tests/api/test_export_status_api.py
- [ ] T025 [P] [USA] Test API handles malformed JSON from Redis gracefully in tests/api/test_export_status_api.py
- [ ] T026 [P] [USA] Integration test: Full export lifecycle (create → poll → complete) in tests/integration/test_export_lifecycle.py

### Implementation for Option A

- [ ] T027 [P] [USA] Add Redis status update to generate_pdf_report_task in src/worker/tasks/exports.py (SETEX on success)
- [ ] T028 [P] [USA] Add Redis status update to create_zip_archive_task in src/worker/tasks/exports.py (SETEX on success)
- [ ] T029 [P] [USA] Add Redis error status update to generate_pdf_report_task exception handler in src/worker/tasks/exports.py
- [ ] T030 [P] [USA] Add Redis error status update to create_zip_archive_task exception handler in src/worker/tasks/exports.py
- [ ] T031 [USA] Modify get_pdf_export_status to poll Redis in src/backend/api/exports.py (replace in-memory state)
- [ ] T032 [USA] Modify get_zip_export_status to poll Redis in src/backend/api/exports.py (replace in-memory state)
- [ ] T033 [USA] Add 404 error handling for expired/missing jobs in src/backend/api/exports.py
- [ ] T034 [USA] Add JSON parsing error handling for malformed Redis data in src/backend/api/exports.py
- [ ] T035 [USA] Update OpenAPI documentation for status endpoints in src/backend/api/exports.py (docstrings)

### Verification for Option A

- [ ] T036 [USA] Run all Option A tests and verify they PASS (pytest tests/worker/test_export_status_redis.py tests/api/test_export_status_api.py -v)
- [ ] T037 [USA] Run integration test for full lifecycle (pytest tests/integration/test_export_lifecycle.py -v)
- [ ] T038 [USA] Manual validation: Create PDF export and verify status lifecycle (use quickstart.md Test 1)
- [ ] T039 [USA] Manual validation: Create ZIP export and verify status lifecycle (use quickstart.md Test 2)
- [ ] T040 [USA] Manual validation: Verify job expiry after 1 hour or manual deletion (use quickstart.md Test 3)
- [ ] T041 [USA] Manual validation: Verify failed export writes error status (use quickstart.md Test 4)
- [ ] T042 [USA] Document Option A implementation in docs/EXPORT_STATUS_TRACKING.md

**Checkpoint**: Option A complete - export jobs now track status via Redis with automatic 1-hour expiry

---

## Phase 4: User Story 2 (Option B) - Export Request Validation (Priority: P1)

**Goal**: API validates export requests before queueing worker tasks, preventing silent failures

**Independent Test**: Submit invalid export requests (wrong date order, range too large, invalid group_by, future dates) and verify immediate 400 rejection

### Tests for Option B (Write FIRST, ensure they FAIL)

> **NOTE: Write these tests FIRST before implementation, ensure they FAIL, then implement to make them PASS**

- [ ] T043 [P] [USB] Create test_export_validation.py in tests/api/ (test validation rules)
- [ ] T044 [P] [USB] Test VR-001: Reject start_date > end_date with 400 in tests/api/test_export_validation.py
- [ ] T045 [P] [USB] Test VR-002: Reject date range > 365 days with 400 in tests/api/test_export_validation.py
- [ ] T046 [P] [USB] Test VR-003: Reject invalid group_by value with 400 in tests/api/test_export_validation.py
- [ ] T047 [P] [USB] Test VR-004: Reject future start_date with 400 in tests/api/test_export_validation.py
- [ ] T048 [P] [USB] Test valid request returns 202 and queues task in tests/api/test_export_validation.py
- [ ] T049 [P] [USB] Test validation error messages are clear and specific in tests/api/test_export_validation.py
- [ ] T050 [P] [USB] Test Pydantic validators for group_by enum in tests/api/test_export_validation.py
- [ ] T051 [P] [USB] Test no worker task queued when validation fails in tests/api/test_export_validation.py
- [ ] T052 [P] [USB] Test validation latency <100ms using performance test in tests/api/test_export_validation.py
- [ ] T053 [P] [USB] Test backward compatibility: previously valid requests still work in tests/api/test_export_validation.py

### Implementation for Option B

- [ ] T054 [P] [USB] Add Pydantic validator for group_by field in src/backend/schemas/export.py (PDFExportRequest)
- [ ] T055 [P] [USB] Add Pydantic validator for group_by field in src/backend/schemas/export.py (ZIPExportRequest)
- [ ] T056 [USB] Add validation function validate_export_request in src/backend/api/validation.py (VR-001 to VR-004)
- [ ] T057 [USB] Add validation call to create_pdf_export endpoint in src/backend/api/exports.py (before queueing task)
- [ ] T058 [USB] Add validation call to create_zip_export endpoint in src/backend/api/exports.py (before queueing task)
- [ ] T059 [USB] Update OpenAPI documentation for validation errors in src/backend/api/exports.py (400 responses)

### Verification for Option B

- [ ] T060 [USB] Run all Option B tests and verify they PASS (pytest tests/api/test_export_validation.py -v)
- [ ] T061 [USB] Manual validation: Submit request with start_date > end_date (use quickstart.md Test 1 - VR-001)
- [ ] T062 [USB] Manual validation: Submit request with range > 365 days (use quickstart.md Test 2 - VR-002)
- [ ] T063 [USB] Manual validation: Submit request with invalid group_by (use quickstart.md Test 3 - VR-003)
- [ ] T064 [USB] Manual validation: Submit request with future start_date (use quickstart.md Test 4 - VR-004)
- [ ] T065 [USB] Manual validation: Submit valid request to verify backward compatibility (use quickstart.md Test 5)
- [ ] T066 [USB] Manual validation: Measure validation performance <100ms (use quickstart.md Test 6)
- [ ] T067 [USB] Document Option B validation rules in docs/EXPORT_VALIDATION.md

**Checkpoint**: Option B complete - invalid export requests rejected immediately with clear error messages

---

## Phase 5: User Story 3 (Option D) - Re-ID Performance Optimization (Priority: P2)

**Goal**: Analyze similarity score distribution, test threshold variations, identify optimal matching threshold

**Independent Test**: Run analysis script, review histogram showing score distribution, verify threshold recommendations are data-driven

### Tests for Option D (Write FIRST, ensure they FAIL)

> **NOTE: Write these tests FIRST before implementation, ensure they FAIL, then implement to make them PASS**

- [ ] T068 [P] [USD] Create test_reid_analysis.py in tests/scripts/ (test analysis scripts)
- [ ] T069 [P] [USD] Test analyze_reid_performance.py loads detections correctly in tests/scripts/test_reid_analysis.py
- [ ] T070 [P] [USD] Test similarity computation returns valid scores (0.0-1.0) in tests/scripts/test_reid_analysis.py
- [ ] T071 [P] [USD] Test histogram generation creates PNG file in tests/scripts/test_reid_analysis.py
- [ ] T072 [P] [USD] Test test_reid_thresholds.py calculates assignment rates correctly in tests/scripts/test_reid_analysis.py
- [ ] T073 [P] [USD] Test threshold analysis returns DataFrame with expected columns in tests/scripts/test_reid_analysis.py
- [ ] T074 [P] [USD] Test plot_reid_scores.py creates comparison visualization in tests/scripts/test_reid_analysis.py
- [ ] T075 [P] [USD] Test analysis completes within 5 minutes on 11,570 detections in tests/scripts/test_reid_analysis.py
- [ ] T076 [P] [USD] Test analysis is read-only (no database modifications) in tests/scripts/test_reid_analysis.py
- [ ] T077 [P] [USD] Test command-line argument parsing for all three scripts in tests/scripts/test_reid_analysis.py
- [ ] T078 [P] [USD] Test optimal threshold recommendation is data-driven in tests/scripts/test_reid_analysis.py

### Implementation for Option D

- [ ] T079 [P] [USD] Create analyze_reid_performance.py script in scripts/ (query detections, compute similarities, generate histogram)
- [ ] T080 [P] [USD] Create test_reid_thresholds.py script in scripts/ (test 0.70, 0.65, 0.60, 0.55 thresholds)
- [ ] T081 [P] [USD] Create plot_reid_scores.py script in scripts/ (threshold comparison visualization)
- [ ] T082 [USD] Add database query helper function in scripts/analyze_reid_performance.py (load detections + deer profiles)
- [ ] T083 [USD] Add similarity computation function in scripts/analyze_reid_performance.py (cosine similarity matrix)
- [ ] T084 [USD] Add histogram generation with matplotlib/seaborn in scripts/analyze_reid_performance.py
- [ ] T085 [USD] Add threshold testing logic in scripts/test_reid_thresholds.py (calculate assignment rates)
- [ ] T086 [USD] Add recommendation engine in scripts/test_reid_thresholds.py (identify optimal threshold)
- [ ] T087 [USD] Add comparison plot generation in scripts/plot_reid_scores.py (bar + line charts)
- [ ] T088 [USD] Add command-line argument parsing to all three scripts (argparse)

### Verification for Option D

- [ ] T089 [USD] Run all Option D tests and verify they PASS (pytest tests/scripts/test_reid_analysis.py -v)
- [ ] T090 [USD] Manual validation: Run similarity score analysis (use quickstart.md Test 1)
- [ ] T091 [USD] Manual validation: Run threshold testing with multiple values (use quickstart.md Test 2)
- [ ] T092 [USD] Manual validation: Generate visualization plots (use quickstart.md Test 3)
- [ ] T093 [USD] Manual validation: Verify performance <5 minutes (use quickstart.md Test 4)
- [ ] T094 [USD] Manual validation: Document analysis results (use quickstart.md Test 5)
- [ ] T095 [USD] Document analysis results in docs/REID_OPTIMIZATION_ANALYSIS.md

**Checkpoint**: Option D complete - Re-ID performance analyzed with data-driven threshold recommendations

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple options and final validation

- [ ] T096 [P] Run full test suite for all options (pytest tests/ -v --cov=src --cov-report=html)
- [ ] T097 [P] Verify test coverage >=80% for modified files (check htmlcov/index.html)
- [ ] T098 [P] Run full quickstart.md validation for Option A (all 4 manual tests)
- [ ] T099 [P] Run full quickstart.md validation for Option B (all 6 manual tests)
- [ ] T100 [P] Run full quickstart.md validation for Option D (all 5 manual tests)
- [ ] T101 [P] Review worker logs for Redis connection warnings (docker-compose logs worker | grep -i redis)
- [ ] T102 [P] Review API logs for validation error rates (docker-compose logs backend | grep "400")
- [ ] T103 Verify Redis memory usage acceptable (docker stats thumper_redis)
- [ ] T104 Verify no performance regression in export endpoints (compare response times before/after)
- [ ] T105 [P] Update README.md with new features (export status tracking, validation, Re-ID analysis)
- [ ] T106 [P] Update API documentation (OpenAPI spec in src/backend/app/main.py)
- [ ] T107 Create session handoff document (docs/SESSION_20251113_IMPLEMENTATION.md)
- [ ] T108 Code cleanup: Remove commented code, add docstrings to new functions
- [ ] T109 Security review: Ensure job_id validation prevents injection attacks
- [ ] T110 Commit all changes with descriptive message following conventional commits

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-5)**: All depend on Foundational phase completion
  - Option A (Phase 3): Independent, can start after Foundational
  - Option B (Phase 4): Independent, can start after Foundational
  - Option D (Phase 5): Independent, can start after Foundational
- **Polish (Phase 6)**: Depends on completion of Options A, B, D

### User Story Dependencies

- **Option A (USA - P1)**: Can start after Foundational (Phase 2) - No dependencies on other options
- **Option B (USB - P1)**: Can start after Foundational (Phase 2) - No dependencies on other options
- **Option C (deferred)**: Frontend detection correction UI - separate feature (not in this scope)
- **Option D (USD - P2)**: Can start after Foundational (Phase 2) - No dependencies on other options

**NOTE**: All three options (A, B, D) are completely independent and can be implemented in parallel by different developers.

### Within Each Option (TDD Workflow)

**Option A (Export Status Tracking)**:
1. **Write Tests FIRST** (T015-T026) - all tests should FAIL
2. Worker Redis updates (T027-T030) - implement to make tests pass
3. API Redis polling (T031-T035) - implement to make tests pass
4. **Verify Tests PASS** (T036-T037)
5. Manual validation (T038-T041)
6. Documentation (T042)

**Option B (Export Validation)**:
1. **Write Tests FIRST** (T043-T053) - all tests should FAIL
2. Pydantic validators (T054-T055) - implement to make tests pass
3. Validation function (T056) - implement to make tests pass
4. API integration (T057-T059) - implement to make tests pass
5. **Verify Tests PASS** (T060)
6. Manual validation (T061-T066)
7. Documentation (T067)

**Option D (Re-ID Analysis)**:
1. **Write Tests FIRST** (T068-T078) - all tests should FAIL
2. Script creation (T079-T081) - implement to make tests pass
3. Implementation details (T082-T088) - implement to make tests pass
4. **Verify Tests PASS** (T089)
5. Manual validation (T090-T094)
6. Documentation (T095)

### Parallel Opportunities

**Within Foundational Phase (Phase 2)**:
- T012, T013, T014 can run in parallel (different fixture types in conftest.py)

**Within Option A Tests (Phase 3)**:
- T015-T019 can run in parallel (different test functions in same file)
- T020-T025 can run in parallel (different test functions in same file)
- T027, T028, T029, T030 can run in parallel (different worker task functions)
- T031, T032 can run in parallel (different API endpoints)

**Within Option B Tests (Phase 4)**:
- T043-T053 can run in parallel (different test functions in same file)
- T054, T055 can run in parallel (different schema classes)

**Within Option D Tests (Phase 5)**:
- T068-T078 can run in parallel (different test functions)
- T079, T080, T081 can run in parallel (three independent script files)

**Across Options (After Foundational)**:
- ALL of Phase 3 (Option A including tests)
- ALL of Phase 4 (Option B including tests)
- ALL of Phase 5 (Option D including tests)
- Can be worked on simultaneously by 3 different developers

**Within Polish Phase (Phase 6)**:
- T096, T097, T098, T099, T100, T101, T102, T105, T106 can run in parallel

---

## Parallel Example: All Three Options with TDD

```bash
# After Foundational phase completes, launch all three options in parallel:

# Developer 1 - Option A (TDD):
Task: "Create test_export_status_redis.py - write tests FIRST"
Task: "Create test_export_status_api.py - write tests FIRST"
Task: "Verify tests FAIL"
Task: "Add Redis status update to generate_pdf_report_task - make tests PASS"
Task: "Modify get_pdf_export_status to poll Redis - make tests PASS"
Task: "Verify all tests PASS"

# Developer 2 - Option B (TDD):
Task: "Create test_export_validation.py - write tests FIRST"
Task: "Verify tests FAIL"
Task: "Add Pydantic validator for group_by field - make tests PASS"
Task: "Add validation function validate_export_request - make tests PASS"
Task: "Verify all tests PASS"

# Developer 3 - Option D (TDD):
Task: "Create test_reid_analysis.py - write tests FIRST"
Task: "Verify tests FAIL"
Task: "Create analyze_reid_performance.py script - make tests PASS"
Task: "Create test_reid_thresholds.py script - make tests PASS"
Task: "Verify all tests PASS"
```

---

## Implementation Strategy

### TDD Workflow (Test-Driven Development)

**CRITICAL**: For each option, follow this strict order:

1. **RED**: Write tests FIRST, run them, watch them FAIL
2. **GREEN**: Write minimal code to make tests PASS
3. **REFACTOR**: Clean up code while keeping tests passing
4. **VERIFY**: Run manual validation from quickstart.md
5. **DOCUMENT**: Write implementation docs

### MVP First (Option A + Option B with TDD)

**Critical Fixes Priority**: Options A and B are both CRITICAL (P1), Option D is HIGH (P2)

1. Complete Phase 1: Setup (including pytest)
2. Complete Phase 2: Foundational (including test fixtures)
3. **Option A (TDD)**:
   - Write all tests (T015-T026) - verify they FAIL
   - Implement features (T027-T035) - make tests PASS
   - Verify and validate (T036-T041)
4. **Option B (TDD)**:
   - Write all tests (T043-T053) - verify they FAIL
   - Implement features (T054-T059) - make tests PASS
   - Verify and validate (T060-T066)
5. **STOP and VALIDATE**: Run full test suite, verify coverage >=80%
6. Deploy to production if critical fixes validated
7. (Optional) Complete Option D with TDD workflow

**Rationale**: TDD ensures correctness before deployment. Tests serve as living documentation and prevent regressions.

### Test Coverage Goals

**Target**: >=80% code coverage on modified files

**Coverage by Option**:
- Option A: Worker tasks (exports.py), API endpoints (exports.py status polling)
- Option B: Validation function (validation.py), API endpoints (exports.py request handling)
- Option D: Analysis scripts (analyze_reid_performance.py, test_reid_thresholds.py, plot_reid_scores.py)

**Measurement**:
```bash
# Run tests with coverage
pytest tests/ -v --cov=src/backend/api/exports --cov=src/backend/api/validation --cov=src/worker/tasks/exports --cov=scripts --cov-report=html

# Review coverage report
open htmlcov/index.html
```

### Incremental Delivery with Testing

1. Complete Setup + Foundational → Foundation ready + test fixtures
2. Add Option A with tests → Run tests → Manual validation → Deploy (CRITICAL-2 fixed!)
3. Add Option B with tests → Run tests → Manual validation → Deploy (CRITICAL-3 fixed!)
4. Add Option D with tests → Run tests → Manual validation → Deploy (Performance optimized!)
5. Each option validated by both automated tests and manual procedures

### Parallel Team Strategy with TDD

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: Option A (write tests → implement → verify) - 3-4 hours
   - Developer B: Option B (write tests → implement → verify) - 1.5-2 hours
   - Developer C: Option D (write tests → implement → verify) - 1.5 days
3. All developers follow TDD workflow independently
4. Options complete with full test coverage

**Estimated Timeline with TDD**:
- Setup + Foundational: 1.5 hours (includes test fixtures)
- Option A (TDD): 3-4 hours (tests + implementation + verification)
- Option B (TDD): 1.5-2 hours (tests + implementation + verification)
- Option D (TDD): 1.5 days (tests + implementation + verification)
- Polish: 1.5 hours (full test suite, coverage review)
- **Total (sequential)**: ~2 days
- **Total (parallel, 3 developers)**: ~1.5 days

---

## Success Metrics

### Test Coverage Metrics
- [ ] Test coverage >=80% on src/backend/api/exports.py
- [ ] Test coverage >=80% on src/backend/api/validation.py
- [ ] Test coverage >=80% on src/worker/tasks/exports.py
- [ ] Test coverage >=60% on analysis scripts (scripts/*.py)
- [ ] All tests PASS before deployment
- [ ] Zero failing tests in CI/CD pipeline

### Option A (Export Status Tracking)
- [ ] 100% of completed exports update status to "completed" (SC-001, SC-005)
- [ ] Export status queries return within 1 second (SC-001)
- [ ] Completed exports provide download URL (SC-002)
- [ ] Failed exports provide error messages (SC-003)
- [ ] Jobs expire after 1 hour returning 404 (SC-004)
- [ ] All automated tests PASS (12 tests)

### Option B (Export Validation)
- [ ] Invalid requests rejected within 100ms (SC-006)
- [ ] Zero worker tasks queued for invalid requests (SC-007)
- [ ] Users receive immediate validation feedback (SC-008)
- [ ] Error messages specify which rule failed (SC-009)
- [ ] 100% of validation failures return 400 status (SC-010)
- [ ] All automated tests PASS (11 tests)

### Option D (Re-ID Analysis)
- [ ] Analysis completes within 5 minutes on 11,570 detections (SC-011)
- [ ] Histogram clearly shows score distribution (SC-012)
- [ ] Threshold recommendations are data-driven (SC-013)
- [ ] Optimal threshold increases assignment rate >=20% (SC-014)
- [ ] False positive rate remains <5% (SC-015)
- [ ] Analysis results documented with visualizations (SC-016)
- [ ] All automated tests PASS (11 tests)

---

## Test Files Summary

**Total Test Files**: 6 new test files + 1 modified conftest.py

**Test Files Created**:
1. `tests/conftest.py` - Test fixtures (redis_client, test_db, mock_celery)
2. `tests/worker/test_export_status_redis.py` - Worker Redis status updates (5 tests)
3. `tests/api/test_export_status_api.py` - API status polling (6 tests)
4. `tests/integration/test_export_lifecycle.py` - Full export lifecycle (1 integration test)
5. `tests/api/test_export_validation.py` - Validation rules (11 tests)
6. `tests/scripts/test_reid_analysis.py` - Analysis scripts (11 tests)

**Total Automated Tests**: 34 tests across all options

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific option: USA (Option A), USB (Option B), USD (Option D)
- Each option is independently completable and testable
- **TDD Workflow**: RED (write tests, watch fail) → GREEN (implement, watch pass) → REFACTOR (clean up)
- Commit after each task or logical group
- Stop at any checkpoint to validate option independently
- All three options can be implemented in parallel after Foundational phase
- Tests written BEFORE implementation ensure correctness
- Automated tests + manual validation = comprehensive quality assurance
- Coverage goal: >=80% on modified files
- Option C (Frontend UI) is out of scope for this feature - separate implementation
