# Spec-Kit Transition Plan
**Date:** November 8, 2025
**Purpose:** Migrate Thumper Counter to spec-kit methodology
**Reference:** https://github.com/github/spec-kit

---

## Why Spec-Kit?

**Benefits:**
1. **Living Documentation** - Specs stay in sync with code
2. **AI-First Development** - Claude understands specs natively
3. **Design Before Code** - Think through architecture first
4. **Version Control** - Specs tracked in git like code
5. **Collaboration** - Clear contracts between components

**Perfect for this project because:**
- Already using sprints and structured development
- Extensive documentation exists (ready to convert)
- Complex ML pipeline (specs help manage complexity)
- AI-assisted development (spec-kit designed for this)

---

## Pre-Transition Checklist

### [OK] Document Current State
- [x] Quick stats documented (docs/QUICK_STATS.md)
- [x] All sprints documented (Sprint 1-10)
- [x] Session handoffs complete
- [x] Architecture decisions recorded (CLAUDE.md)
- [x] GPU optimizations documented
- [x] Filesystem fixes documented

### [READY] Clean Git State
```bash
# Current branch: main
# Status: Clean (only docs added)
```

### [READY] Commit All Work
```bash
# Prepare comprehensive commit before transition
git add docs/
git commit -m "docs: Complete rut season analysis and pre-spec-kit documentation

- Rut season analysis: 3,656 images, 16 mature buck detections
- 3 unique mature bucks identified (ready for naming)
- Complete documentation of Sprints 1-10
- GPU and filesystem optimizations documented
- Quick stats dashboard created
- System at 69.33% completion (24,440 / 35,251 images)

Ready for spec-kit transition."
```

---

## Spec-Kit Installation

### Install specify CLI

```bash
# Option 1: npm (recommended)
npm install -g @github/specify

# Option 2: Download binary
# See: https://github.com/github/spec-kit/releases

# Verify installation
specify --version
```

### Initialize in Project

```bash
cd /mnt/i/projects/thumper_counter

# Initialize spec-kit
specify init

# This creates:
# - .specify/ directory
# - .specify/config.yml
# - specs/ directory (if not exists)
```

---

## Directory Structure (After Spec-Kit)

```
thumper_counter/
├── .specify/
│   ├── config.yml          # spec-kit configuration
│   ├── memory/             # AI context and decisions
│   └── constitution.md     # Project principles
├── specs/
│   ├── system.spec         # Overall architecture
│   ├── ml-pipeline.spec    # Detection/Re-ID/Classification
│   ├── api.spec            # Backend endpoints
│   ├── frontend.spec       # React components
│   ├── database.spec       # Schema and migrations
│   └── infrastructure.spec # Docker, GPU, filesystem
├── src/                    # Existing code (unchanged)
├── docs/                   # Existing docs (keep as reference)
├── CLAUDE.md               # Keep as legacy reference
└── README.md               # Update to reference specs
```

---

## Migration Strategy

### Phase 1: Create Specifications (Week 1)

**Convert existing documentation to specs:**

#### 1.1 System Spec (Top-Level Architecture)
```yaml
# specs/system.spec
name: Thumper Counter - Deer Tracking System
version: 1.0.0
status: production

components:
  - ml-pipeline
  - api-backend
  - frontend-dashboard
  - database
  - infrastructure

architecture: |
  Three-tier processing pipeline:
  1. API Layer (FastAPI) - Upload and query
  2. Worker Layer (Celery + GPU) - ML processing
  3. Data Layer (PostgreSQL + Redis) - Storage

tech_stack:
  backend: FastAPI, Celery, Python 3.11
  frontend: React 18, TypeScript, Material-UI v5
  database: PostgreSQL 15, pgvector, Redis 7
  ml: YOLOv8n, ResNet50, PyTorch, CUDA
  infrastructure: Docker Desktop, WSL2, Windows 10/11
```

#### 1.2 ML Pipeline Spec
**File:** specs/ml-pipeline.spec

**Contents:**
- Detection model (YOLOv8n, 5 classes)
- Classification logic (doe/fawn/mature/mid/young)
- Re-identification (ResNet50, 512-dim embeddings)
- Performance benchmarks (0.04s detection, 5.57ms Re-ID)
- GPU optimizations (concurrency=32, cuDNN tuning)

#### 1.3 API Spec
**File:** specs/api.spec

**Contents:**
- All endpoint contracts (locations, images, deer, detections)
- Request/response schemas
- Authentication (if added)
- Rate limiting
- WebSocket (if added)

#### 1.4 Frontend Spec
**File:** specs/frontend.spec

**Contents:**
- Component hierarchy
- Pages (Dashboard, Deer Gallery, Deer Detail, Image Browser)
- New: "Favorite Feeder" field on Deer Card
- Material-UI theme (earth tones)
- API integration (React Query)

#### 1.5 Database Spec
**File:** specs/database.spec

**Contents:**
- Schema (locations, images, detections, deer)
- Relationships and constraints
- Indexes (performance critical)
- pgvector configuration
- Migration history (009_add_detection_corrections.sql)

#### 1.6 Infrastructure Spec
**File:** specs/infrastructure.spec

**Contents:**
- Docker Compose setup
- Volume mounts (I:\ format - CRITICAL)
- GPU configuration (NVIDIA Container Toolkit)
- Worker concurrency (32)
- Port mappings (8001, 3000, 5555, 5433, 6380)

### Phase 2: Update .specify Configuration

#### .specify/config.yml
```yaml
version: 1
project:
  name: thumper_counter
  description: ML-powered deer tracking and re-identification

specs:
  directory: specs
  extensions: [.spec, .md]

ai:
  model: claude-sonnet-4-5
  context_files:
    - docs/QUICK_STATS.md
    - docs/SPRINTS/SPRINT_*_SUMMARY.md
    - CLAUDE.md

git:
  auto_commit: false  # Manual control preferred
  branch_strategy: sprint-based
  remotes:
    - origin  # GitHub
    - ubuntu  # Local server
    # Skip synology (per user request)
```

#### .specify/memory/ (AI Context)
Convert existing session handoffs and decision logs:
- memory/gpu-optimizations.md
- memory/filesystem-fixes.md
- memory/re-id-architecture.md
- memory/frontend-mui-migration.md

#### .specify/constitution.md (Project Principles)
```markdown
# Thumper Counter Constitution

## Core Principles

1. **ASCII-Only Output** - No Unicode, emojis, or special characters
2. **Documentation-First** - Specs before code
3. **User Approval** - One step at a time
4. **Performance Matters** - GPU optimization is critical
5. **Data Quality** - Accuracy over speed

## Technical Standards

- Python: 3.11, type hints required
- Git: Sprint-based branching (00X-feature-name)
- Testing: pytest for all new features
- Docker: Windows paths (I:\) for volume mounts
- GPU: RTX 4080 Super, concurrency=32

## Decision Record

- Chose YOLOv8n over larger models (speed vs accuracy)
- Chose ResNet50 for Re-ID (proven architecture)
- Chose Material-UI v5 (component library)
- Chose pgvector over separate vector DB (simplicity)
- Chose concurrency=32 over 64 (GPU lock contention)
```

### Phase 3: Workflow Integration

#### Daily Development with Spec-Kit

```bash
# Start new feature
specify plan "Add favorite feeder to deer card"

# This generates:
# - Task breakdown
# - Affected specs
# - Implementation steps

# Make changes
# ... edit code ...

# Update specs to match reality
specify sync

# Commit with spec reference
git add .
git commit -m "feat: Add favorite feeder to deer card

As specified in frontend.spec section 4.2
Closes #12"
```

#### Sprint Planning with Spec-Kit

```bash
# Plan next sprint
specify plan "Sprint 11: OCR Pipeline for Trail Camera Metadata"

# Review proposed changes
specify diff

# Accept plan
specify apply

# Work through tasks
# ... implementation ...

# Mark sprint complete
specify milestone "Sprint 11 Complete"
```

---

## Pre-Commit Actions (This Session)

### 1. Final Commit of Current Work

```bash
cd /mnt/i/projects/thumper_counter

# Stage all documentation
git add docs/

# Commit with comprehensive message
git commit -m "docs: Complete rut season analysis and pre-spec-kit state

Sprint 8 Evening Session Complete:
- Rut season: 100% processed (3,656 images)
- 16 mature buck detections found
- 3 unique bucks identified via Re-ID
- Peak rut: October 2023 (145 buck detections, 39.5%)
- System: 69.33% complete (24,440 / 35,251 images)

Documentation Added:
- docs/QUICK_STATS.md - Live system metrics
- docs/RUT_SEASON_ANALYSIS.md - Complete rut analysis
- docs/MATURE_BUCKS_REVIEW.md - Frontend review guide
- docs/SESSION_20251108_RUT_ANALYSIS.md - Session summary
- docs/SPEC_KIT_TRANSITION_PLAN.md - Migration plan

Infrastructure Optimizations:
- Volume mounts: I:\ format (Windows Docker Desktop)
- Worker concurrency: 32 (optimal for RTX 4080 Super)
- GPU utilization: 31% (no contention)
- Throughput: 840 images/min

Ready for spec-kit migration and Disney naming ceremony.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 2. Push to Remotes

```bash
# Push to GitHub (origin)
git push origin main

# Push to Ubuntu server
git push ubuntu main

# Verify both pushes succeeded
git remote -v
```

### 3. Create Pre-Spec-Kit Tag

```bash
# Tag this state for reference
git tag -a v1.0-pre-spec-kit -m "State before spec-kit migration

System Status:
- 10 sprints completed
- 69.33% dataset processed
- 3 mature bucks identified
- Rut season fully analyzed
- All optimizations documented"

# Push tag to remotes
git push origin v1.0-pre-spec-kit
git push ubuntu v1.0-pre-spec-kit
```

---

## Recommendations for New Session

### Session 1 Goals: Spec-Kit Setup
1. Install specify CLI
2. Run `specify init`
3. Create initial specs (system.spec, ml-pipeline.spec)
4. Test workflow with small feature ("Favorite Feeder")

### Session 2 Goals: Spec Migration
1. Convert all existing docs to specs
2. Populate .specify/memory/ with decision logs
3. Write constitution.md
4. Validate specs with `specify validate`

### Session 3 Goals: First Feature with Spec-Kit
1. Spec: "Favorite Feeder" field on Deer Card
2. Implement: Backend + Frontend
3. Test: spec-driven development workflow
4. Document: Lessons learned

---

## Tips for Spec-Kit Success

### DO's
- **Start simple** - Begin with system.spec, expand later
- **Keep specs current** - Update as you code
- **Use specify plan** - Let AI help with task breakdown
- **Version specs with code** - Same git commit
- **Reference specs in commits** - "As specified in X.spec"

### DON'Ts
- **Don't over-spec upfront** - Start minimal, evolve
- **Don't duplicate docs** - Specs ARE the documentation
- **Don't skip specify sync** - Keep reality and specs aligned
- **Don't ignore constitution** - It guides AI behavior
- **Don't commit specs separately** - Atomic changes

### Best Practices
1. **Spec before code** - Design in specs, implement in code
2. **Use memory/** - Record all architectural decisions
3. **AI context files** - Point to QUICK_STATS.md, sprint summaries
4. **Sprint-based workflow** - Matches your existing pattern
5. **Manual git control** - Turn off auto-commit, you approve

---

## Backward Compatibility

### Keep for Reference
- **CLAUDE.md** - Historical context, session notes
- **docs/** - Existing documentation (don't delete)
- **Sprint summaries** - Already well-documented

### Migrate to Spec-Kit
- **Architecture** → specs/system.spec
- **API contracts** → specs/api.spec
- **Component design** → specs/frontend.spec
- **DB schema** → specs/database.spec
- **Decisions** → .specify/memory/

### Update
- **README.md** - Point to specs/ instead of docs/
- **CLAUDE.md** - Add note: "Migrated to spec-kit, see specs/"

---

## Favorite Feeder Implementation (Example)

### Spec First (specs/frontend.spec)
```markdown
## Deer Card Component

Fields:
- Name (editable)
- Sex (badge)
- Sighting Count
- First Seen / Last Seen
- **Favorite Feeder** (location with most sightings) [NEW]
- Status (alive/deceased/unknown)

Implementation:
- Query: SELECT location_id, COUNT(*) FROM detections WHERE deer_id=X GROUP BY location_id ORDER BY COUNT(*) DESC LIMIT 1
- Display: Location name with count badge
- Example: "Hayfield (26 visits)"
```

### Code Second (src/backend/api/deer.py)
```python
# Add to deer response schema
favorite_location: Optional[str] = None
favorite_location_count: Optional[int] = None

# Add to query (already have location aggregation in timeline endpoint)
# Reuse logic from GET /api/deer/{id}/locations
```

### Commit
```bash
git add specs/frontend.spec src/backend/api/deer.py src/frontend/...
git commit -m "feat: Add favorite feeder to deer card

As specified in specs/frontend.spec section 2.1.

Shows location with most sightings for each deer.
Example: 'Hayfield (26 visits)'

Backend: Added favorite_location fields to deer schema
Frontend: Updated DeerCard component with new field

Tested with Buck #1: Hayfield (26 visits)"
```

---

## Git Workflow Post-Spec-Kit

### Branch Strategy (Unchanged)
- Sprint branches: `00X-feature-name`
- Merge to main at sprint end
- Tag major milestones

### Commit Message Format
```
<type>: <subject>

[spec reference]
[body]

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:**
- feat: New feature
- fix: Bug fix
- docs: Documentation (including specs)
- spec: Spec-only changes
- refactor: Code restructure
- perf: Performance improvement
- test: Testing

**Example:**
```
feat: Implement OCR pipeline for trail camera metadata

As specified in specs/ml-pipeline.spec section 3.4

Extracts timestamp, temperature, moon phase from camera footer.
Uses EasyOCR with GPU acceleration.
Stores in new metadata JSONB column.

Performance: 0.12s per image (GPU)
Accuracy: 94% on test set (50 images)

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Push Strategy (Your Preference)
```bash
# After each commit or batch of commits
git push origin main
git push ubuntu main

# Skip synology (per your request)
```

---

## Questions for Next Session

When starting the new chat with spec-kit:

1. **Do you want to install specify globally or locally?**
   - Global: `npm install -g @github/specify`
   - Local: `npm install --save-dev @github/specify`

2. **Which specs to create first?**
   - Recommend: system.spec, ml-pipeline.spec, frontend.spec
   - Or: All 6 specs at once

3. **Memory migration strategy?**
   - Convert all session handoffs to .specify/memory/?
   - Or: Start fresh, reference old docs?

4. **Constitution content?**
   - Use example above?
   - Or: Customize further?

5. **First feature to spec-drive?**
   - "Favorite Feeder" (simple, good test)?
   - Or: "Disney Names" (data update)?
   - Or: Something else?

---

## Success Criteria

### Spec-Kit Transition Complete When:
- [x] All sprints documented (already done)
- [x] All optimizations documented (already done)
- [ ] specify CLI installed
- [ ] .specify/ directory created
- [ ] 6 core specs written (system, ml, api, frontend, db, infra)
- [ ] constitution.md written
- [ ] memory/ populated with decisions
- [ ] First feature implemented using spec-kit workflow
- [ ] README.md updated to reference specs

### You'll Know It's Working When:
- Claude references specs in responses
- `specify plan` generates useful task breakdowns
- Specs stay in sync with code
- Git history shows spec + code commits together
- New contributors can read specs and understand system

---

## Resources

**Spec-Kit:**
- GitHub: https://github.com/github/spec-kit
- CLI Reference: https://github.com/github/spec-kit/blob/main/README.md#-specify-cli-reference
- Examples: https://github.com/github/spec-kit/tree/main/examples

**Your Existing Docs (Reference):**
- docs/QUICK_STATS.md - Current system state
- docs/CLAUDE.md - Full project history
- docs/SPRINTS/ - All sprint summaries
- docs/SESSION_* - Session handoffs

**Key Decisions to Preserve:**
- GPU: Concurrency 32, cuDNN enabled
- Filesystem: I:\ paths for Windows Docker
- Re-ID: Threshold 0.85, ResNet50 512-dim
- Frontend: Material-UI v5, earth tones
- Testing: One step at a time, user approval

---

## Final Checklist Before Logging Out

- [x] Quick stats documented
- [x] Rut analysis complete
- [x] Mature bucks review guide created
- [x] Session summary written
- [x] Spec-kit transition plan created
- [ ] Commit all docs
- [ ] Push to origin and ubuntu
- [ ] Tag v1.0-pre-spec-kit
- [ ] Start new chat for spec-kit setup

---

**You're ready! Good luck with the spec-kit migration!**

The system is in great shape:
- 69.33% processed
- 3 mature bucks waiting for Disney names
- All optimizations documented
- Ready for "Favorite Feeder" feature

See you in the next chat for spec-kit setup!
