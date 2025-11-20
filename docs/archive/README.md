# Documentation Archive

This directory contains historical documentation that has been superseded or is no longer actively referenced.

## Archive Date
November 11, 2025

## What's Archived

### Sprint Summaries (Historical)
- SPRINT_4_SUMMARY.md - Sprint 4: Multi-class model training
- SPRINT_5_SUMMARY.md - Sprint 5: Re-identification system
- SPRINT_6_SUMMARY.md - Sprint 6: Pipeline integration
- SPRINT_7_OCR_ANALYSIS.md - Sprint 7: OCR investigation
- SPRINT_8_DB_OPTIMIZATION.md - Sprint 8: Database performance
- SPRINT_9_PLAN.md - Sprint 9: Re-ID GPU optimization planning
- SPRINT_9_REID_GPU.md - Sprint 9: Re-ID performance analysis
- SPRINT_10_PLAN.md - Sprint 10: Frontend development planning
- SPRINT_10_SUMMARY.md - Sprint 10: Frontend implementation

### Session Handoffs (Superseded)
- SESSION_20251107_DEDUP_HANDOFF.md
- SESSION_20251107_HANDOFF.md
- SESSION_20251107_SPRINT8_HANDOFF.md
- SESSION_20251108_HANDOFF.md
- SESSION_HANDOFF_2025-11-07_Sprint9.md
- SESSION_HANDOFF_TEMPLATE.md

### Planning Documents (Completed)
- FRONTEND_REQUIREMENTS.md - Frontend specifications (implemented in Sprint 10)
- FRONTEND_REVIEW_REPORT.md - Frontend review results
- HANDOFF_SPRINT_10.md - Sprint 10 handoff notes
- BURST_DEDUPLICATION_DESIGN.md - Deduplication design document
- RETRAINING_WORKFLOW.md - Model retraining procedures

### Technical Guides (Obsolete)
- CLAUDE_CLI_GUIDE.md - Claude CLI setup (superseded by CLAUDE.md)
- DEVELOPMENT_OPTIONS.md - Development environment options
- SPEC_ALIGNMENT_REVIEW.md - Spec alignment review
- SPEC_UPDATES_SUMMARY.md - Spec update summary
- MODEL_INVENTORY.md - Historical model inventory
- TESTING_MODELS.md - Model testing procedures

## Active Documentation

Current documentation is in the parent docs/ directory:

- **CAMERA_LOCATIONS.md** - Camera site information
- **OPERATIONS_RUNBOOK.md** - Production operations guide
- **SESSION_20251108_PERFORMANCE_OPTIMIZATION.md** - Recent performance work
- **SESSION_20251111_MODEL_DEPLOYMENT.md** - Current model deployment

## Retrieval

If you need to reference archived documentation:

```bash
# List all archived docs
ls docs/archive/

# View specific archived doc
cat docs/archive/SPRINT_4_SUMMARY.md

# Search across archived docs
grep -r "keyword" docs/archive/
```

## Archival Policy

Documentation is archived when:
1. Sprint is complete and summarized in newer docs
2. Session handoff is superseded by more recent handoff
3. Planning document's work is completed and documented
4. Technical guide is obsolete or superseded

Archived documentation is retained for historical reference and audit trail purposes.
