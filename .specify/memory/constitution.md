<!--
Sync Impact Report - Constitution Update
Version: 0.1.0 -> 1.0.0 (MAJOR - Initial ratification from template)
Date: 2025-11-08

CHANGES:
- Initial constitution ratification
- Established 5 core principles:
  1. ASCII-Only Communication (new)
  2. GPU-First Architecture (new)
  3. Spec-Driven Development (new)
  4. Data Integrity & Accuracy (new)
  5. Performance-Aware Design (new)
- Added Wildlife ML Standards section (new)
- Added Development Workflow section (new)
- Defined Governance rules (new)

MODIFIED PRINCIPLES: N/A (initial version)
ADDED SECTIONS: All sections (initial ratification)
REMOVED SECTIONS: None

TEMPLATES REQUIRING UPDATES:
✅ .specify/templates/plan-template.md - Constitution Check section aligns
✅ .specify/templates/spec-template.md - User scenarios align with testing requirements
✅ .specify/templates/tasks-template.md - No updates needed (task structure compatible)

FOLLOW-UP TODOS:
- Add automated ASCII validation to testing suite (future sprint)
- Document GPU memory profiling procedures in developer guide

RATIONALE FOR VERSION 1.0.0:
- Initial ratification establishes baseline governance
- All principles derived from existing project practices (CLAUDE.md, documentation)
- MAJOR version appropriate for establishing constitutional framework
-->

# Thumper Counter Constitution

## Core Principles

### I. ASCII-Only Communication (NON-NEGOTIABLE)

ALL project output, documentation, logging, and user-facing text MUST use ASCII characters only. This principle applies to code comments, documentation files, log messages, API responses, error messages, and UI text.

**Rules:**
- NO Unicode characters (checkmarks, crosses, arrows, etc.)
- NO Emojis of any kind
- NO Smart quotes (use straight quotes: ' and ")
- NO Special dashes (use hyphen: -)
- NO Box-drawing characters

**Allowed for emphasis:**
- Status indicators: [OK], [FAIL], [WARN], [INFO]
- ASCII art borders: dashes (-), equals (=), asterisks (*)
- ALL CAPS for headers

**Rationale:** Ensures consistent rendering across all terminals, log aggregators, and display environments. Critical for Windows/WSL2/Docker development where character encoding issues are common. Prevents visual noise and maintains professional, accessible output.

### II. GPU-First Architecture

All ML processing MUST be designed for GPU execution. CPU fallback is acceptable for development/testing only. Performance characteristics must be documented with explicit bottleneck analysis.

**Rules:**
- YOLOv8 detection MUST run on CUDA-enabled GPU
- ResNet50 re-identification MUST use GPU acceleration
- Batch processing MUST maximize GPU utilization
- CPU mode allowed only for: development, testing, non-production environments
- Performance metrics MUST include: inference time, throughput, GPU memory usage, bottleneck identification

**Rationale:** Processing 35,000+ images requires GPU acceleration (0.04s vs 0.4s per image = 10x improvement). Dataset size makes CPU-only processing impractical. GPU architecture decisions impact Docker configuration, memory management, and scaling strategy.

### III. Spec-Driven Development

Features MUST be specified before implementation using spec-kit methodology. Specifications are living documentation maintained in sync with code.

**Rules:**
- All features require specification document in `/specs/` directory
- Specifications MUST include: user scenarios, acceptance criteria, technical constraints
- Implementation plan MUST derive from specification
- Specifications updated when requirements change (not retroactively)
- Branch naming MUST match spec directory: `###-feature-name`

**Rationale:** Separates design decisions from implementation details. Provides clear contracts between components. Enables iterative refinement before coding begins. Creates GitHub-ready documentation for publication.

### IV. Data Integrity & Accuracy

Detection and classification results MUST be auditable and correctable. System MUST support manual correction of ML predictions while preserving original results.

**Rules:**
- Original ML predictions MUST be preserved in database (never overwritten)
- Corrections MUST be tracked with: corrected fields, correction timestamps, correction reasons
- Multi-species classification MUST be explicit (deer: buck/doe/fawn/unknown, non-deer: cattle/pig/raccoon)
- Batch correction MUST support up to 1000 detections per operation
- Re-identification similarity threshold: 0.85 (conservative to prevent false matches)

**Rationale:** ML models are imperfect (76% average confidence). Wildlife monitoring requires data quality for population analysis. Manual correction enables: training data improvement, model validation, scientific accuracy. Preserving original predictions enables model performance analysis over time.

### V. Performance-Aware Design

System design MUST identify and document bottlenecks. Optimization decisions MUST be data-driven with before/after metrics.

**Rules:**
- All performance changes MUST include benchmark results
- Bottleneck analysis MUST quantify time distribution (e.g., "DB writes: 70% of total time")
- Throughput MUST be measured end-to-end (not just GPU inference)
- Performance documentation MUST include: hardware specs, processing speed, dataset size, estimated completion time
- Optimization MUST target documented bottlenecks (not premature optimization)

**Rationale:** Large dataset (35,251 images) makes performance critical. Enables informed scaling decisions. Documents system behavior for future maintenance. Prevents wasted effort on non-bottleneck optimizations.

## Wildlife ML Standards

This section defines constraints specific to the wildlife tracking ML pipeline.

**Model Selection:**
- Detection: YOLOv8n (21.5MB, balanced speed/accuracy)
- Classification: Custom 5-class model (doe/fawn/mature/mid/young bucks)
- Re-ID: ResNet50 (512-dim embeddings, L2 normalized)

**Quality Thresholds:**
- Detection confidence: Store all detections (no minimum threshold)
- Re-ID matching: 0.85 cosine similarity (conservative)
- Bounding box minimum: 50x50 pixels for re-ID processing
- Classification confidence: Display in UI, no filtering

**Database Requirements:**
- PostgreSQL with pgvector extension for similarity search
- Feature vectors: MUST be nullable (manual deer profiles allowed)
- Enums: MUST use lowercase values (e.g., 'buck', 'doe', 'fawn')
- Processing status: pending → processing → completed/failed

**Pipeline Behavior:**
- Auto-chain re-ID for all deer detections
- Sex-based filtering for re-ID matching (males vs females)
- Automatic deer profile creation when no match found
- Burst optimization: reuse deer_id for photo sequences (98% hit rate)

## Development Workflow

**Branch Strategy:**
- One branch per sprint: `00X-feature-name`
- Branch from: previous sprint or main
- Merge at sprint completion

**Technology Stack:**
- Backend: FastAPI 0.104+, Python 3.11
- Worker: Celery 5.3+ with Redis
- Database: PostgreSQL 15 with pgvector 0.5.1
- Frontend: React 18 with TypeScript, Material-UI v5
- Containerization: Docker Compose (use `docker-compose`, not `docker compose`)

**Testing Requirements (Future):**
- All API endpoints MUST have pytest tests
- ML pipeline MUST have integration tests
- Frontend MUST have component tests
- Manual testing REQUIRED for sprint completion

**Documentation Standards:**
- Session handoffs: `docs/SESSION_YYYYMMDD_*.md`
- Sprint summaries: `docs/SPRINT_N_SUMMARY.md`
- API documentation: Auto-generated from FastAPI (Swagger UI)
- Constitution amendments: Documented in Sync Impact Report

## Governance

**Constitution Authority:**
This constitution supersedes all other development practices. When conflicts arise between this document and other guidance, constitution principles take precedence.

**Amendment Procedure:**
1. Proposed changes MUST include rationale and impact analysis
2. Version MUST increment following semantic versioning:
   - MAJOR: Backward incompatible principle changes or removals
   - MINOR: New principle additions or material expansions
   - PATCH: Clarifications, wording fixes, non-semantic refinements
3. Sync Impact Report MUST be prepended to constitution file
4. Dependent templates MUST be updated or flagged for update
5. Amendments become effective immediately upon commit to main branch

**Compliance Verification:**
- All pull requests MUST verify compliance with applicable principles
- Sprint completions MUST document any principle violations with justification
- Performance claims MUST include supporting metrics
- ASCII-only output MUST be verified in all user-facing components

**Runtime Guidance:**
- Development environment: See `/CLAUDE.md` for AI assistant instructions
- Project structure: See `/README.md` for quick start and architecture
- Current sprint: See `/.specify/plan.md` for active tasks and metrics
- Implementation details: See individual spec documents in `/specs/` directory

**Version**: 1.0.0 | **Ratified**: 2025-11-08 | **Last Amended**: 2025-11-08
