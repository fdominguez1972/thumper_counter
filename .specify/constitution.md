# Thumper Counter Project Constitution
**Version:** 1.0.0  
**Ratified:** 2025-11-05  
**Last Amended:** 2025-11-05  

## Preamble

This constitution establishes the fundamental principles, governance, and non-negotiable standards for the Thumper Counter wildlife tracking system. These principles guide all development, deployment, and operational decisions.

## Article I: Core Principles

### Principle 1: Wildlife Conservation First
**Statement:** The system MUST prioritize wildlife welfare and conservation goals above technical elegance or feature completeness.

**Rationale:** This project exists to understand and protect deer populations at Hopkins Ranch. Any feature that could harm wildlife or enable poaching is forbidden.

**Implementation:**
- No real-time location broadcasting
- Delay public data by 48+ hours
- Aggregate data for external sharing
- Secure storage of sensitive locations

### Principle 2: Data Sovereignty
**Statement:** Ranch data MUST remain under ranch control with local-first storage and processing.

**Rationale:** Trail camera data contains sensitive information about private property. Cloud dependence creates privacy and availability risks.

**Implementation:**
- Primary storage on local servers (Ubuntu/Synology)
- GPU processing on-premises
- No required internet connectivity
- Export capabilities for backup only

### Principle 3: Operational Simplicity
**Statement:** The system MUST be operable by non-technical ranch personnel with minimal training.

**Rationale:** The primary users are ranch workers who need reliable tools, not complex interfaces.

**Implementation:**
- Single-button upload process
- Location dropdown (no coordinates needed)
- Clear success/failure indicators
- Automatic error recovery

### Principle 4: Scientific Rigor
**Statement:** All wildlife identification and tracking MUST maintain documented confidence levels and support manual verification.

**Rationale:** Conservation decisions require accurate data. False positives/negatives must be trackable and correctable.

**Implementation:**
- Confidence thresholds (>0.5 for detection)
- Manual verification interface
- Audit trail for corrections
- Separate "verified" flag in database

### Principle 5: Modular Architecture
**Statement:** Components MUST be independently deployable, testable, and replaceable.

**Rationale:** ML models evolve rapidly. The system must accommodate updates without full rebuilds.

**Implementation:**
- Microservices architecture
- Versioned ML models
- Standard REST APIs between services
- Database migrations for schema changes

### Principle 6: Performance Efficiency
**Statement:** The system MUST process the full image backlog (35,000+ images) within 24 hours using available hardware.

**Rationale:** Timely processing enables responsive wildlife management decisions.

**Implementation:**
- GPU acceleration mandatory
- Batch processing (32 images)
- Multithreaded operations
- Progress monitoring

### Principle 7: Open Development
**Statement:** The system SHOULD use open-source components and contribute improvements back to the community.

**Rationale:** Wildlife conservation benefits from shared knowledge and tools.

**Implementation:**
- MIT license for custom code
- Public GitHub repository (sanitized)
- Use of open models (YOLOv8, ResNet)
- Documentation of methods

## Article II: Technical Standards

### Mandatory Requirements
1. **Python 3.11+** for all backend code
2. **PostgreSQL 15+** for data persistence
3. **Docker** for deployment
4. **Git** with branching strategy
5. **ASCII-only** output in logs and CLI

### Prohibited Practices
1. Storage of credentials in code
2. Direct database access from frontend
3. Synchronous ML processing in API calls
4. Hardcoded file paths
5. Unicode/emoji in system output

## Article III: Data Governance

### Data Retention
- **Images:** Indefinite retention (ranch property)
- **Detections:** Minimum 5 years
- **Audit logs:** Minimum 1 year
- **Backups:** 3-2-1 rule (3 copies, 2 media, 1 offsite)

### Privacy Protection
- No personally identifiable information in wildlife data
- Camera locations obscured in public exports
- User actions logged but not tracked
- GDPR-compliant data handling

## Article IV: Development Governance

### Change Management
1. **Specification First:** Changes must update specs before implementation
2. **Review Required:** Database schema changes require documentation
3. **Testing Mandatory:** No deployment without passing tests
4. **Rollback Plan:** Every deployment must be reversible

### Version Control
- **Branching:** main (stable) ← development ← feature/*
- **Commits:** Conventional format (feat/fix/docs)
- **Releases:** Semantic versioning (MAJOR.MINOR.PATCH)
- **Tags:** v1.0.0 format

### Documentation Standards
1. **Code:** Docstrings for all public functions
2. **API:** OpenAPI specification maintained
3. **User:** README for each component
4. **Specs:** Living documents updated with changes

## Article V: Operational Requirements

### Monitoring
- System health checks every 60 seconds
- GPU utilization tracking
- Queue depth monitoring
- Error rate alerting (<5% threshold)

### Maintenance Windows
- Scheduled: Sunday 2-4 AM CST
- Emergency: With 1-hour notice
- Duration: Maximum 2 hours
- Rollback: Within 30 minutes

## Article VI: Amendment Process

### Proposal Requirements
1. Written specification of change
2. Impact analysis on all principles
3. Migration plan if breaking
4. Review period (minimum 48 hours)

### Approval Threshold
- **Minor amendments:** Development team consensus
- **Major amendments:** Ranch owner approval required
- **Emergency fixes:** Retroactive approval within 24 hours

### Version Increments
- **MAJOR:** Principle removal or redefinition
- **MINOR:** Principle addition or expansion
- **PATCH:** Clarifications and corrections

## Article VII: Compliance Validation

### Regular Audits
- **Weekly:** Automated test suite
- **Monthly:** Manual verification sampling
- **Quarterly:** Full specification review
- **Annually:** Architecture assessment

### Non-Compliance Resolution
1. **Detection:** Automated alerts for violations
2. **Triage:** Severity assessment (critical/high/medium/low)
3. **Resolution:** Fix within severity SLA
4. **Prevention:** Root cause analysis

## Appendix A: Decision Record

### Key Architecture Decisions
1. **YOLOv8 Multi-class** (2025-11-04): Single model for detection and classification
2. **Folder-based Locations** (2025-11-04): Location from directory, not EXIF
3. **RTX 4080 Super** (2025-11-05): Hardware upgrade for larger batches
4. **Port Shifting** (2025-11-05): Avoid conflicts with existing deer_tracker

## Appendix B: Stakeholders

### Primary Stakeholders
- **Ranch Owner:** Final authority on features and data use
- **Ranch Workers:** Primary system users
- **Wildlife Biologists:** Data consumers for research

### Development Team
- **Lead Developer:** Architecture and implementation
- **ML Engineer:** Model training and optimization
- **DevOps:** Deployment and monitoring

## Appendix C: Glossary

- **Re-ID:** Re-identification of individual animals across images
- **EXIF:** Exchangeable Image File Format metadata
- **Confidence Threshold:** Minimum certainty for accepting ML predictions
- **Feature Vector:** Mathematical representation for individual identification

---

**Ratification:** This constitution is adopted as the governing document for the Thumper Counter project.

**Signatures:** [Digital signatures via Git commit]
