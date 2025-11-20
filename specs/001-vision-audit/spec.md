# Feature Specification: Automated Vision Classification Audit

**Feature Branch**: `001-vision-audit`
**Created**: November 16, 2025
**Status**: Draft
**Input**: User description: "Automated vision-based classification audit system using Anthropic Python SDK in Docker worker, with frontend-initiated batch processing for low-confidence detections"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Initiate Vision Audit from Frontend (Priority: P1)

A wildlife researcher reviewing detection results notices several deer classified at 50-55% confidence and wants to verify their accuracy using AI vision analysis. They navigate to a low-confidence detections page, select a batch of 20-50 images, and click "Start Vision Audit". The system queues the images for vision analysis in the background worker and shows progress. When complete, they receive a notification and can review the audit results showing which classifications were correct, incorrect, or uncertain.

**Why this priority**: Core MVP functionality. Provides immediate value by allowing users to validate low-confidence detections without manual review of each image.

**Independent Test**: Can be fully tested by selecting detections with confidence <51%, starting an audit, and verifying that audit results are generated and stored in the database.

**Acceptance Scenarios**:

1. **Given** user is viewing detections with confidence 40-60%, **When** they select 25 images and click "Start Vision Audit", **Then** a background job is queued and they see a success message with job ID
2. **Given** an audit job is running, **When** user checks job status, **Then** they see current progress (e.g., "Processing image 12 of 25")
3. **Given** an audit job completes, **When** user views results, **Then** they see each image's vision classification compared to database classification with status (Correct/Incorrect/Uncertain)
4. **Given** audit finds incorrect classifications, **When** user reviews results, **Then** they can approve corrections to update the database
5. **Given** user lacks ANTHROPIC_API_KEY configuration, **When** they attempt to start audit, **Then** they see clear error message indicating API key is required

---

### User Story 2 - Automatic Low-Confidence Flagging (Priority: P2)

System automatically flags all new detections below 51% confidence threshold for vision audit review. These flagged detections appear in a dedicated "Needs Review" queue accessible from the main navigation. Users can process this queue in batches, and the system tracks which detections have been audited.

**Why this priority**: Prevents low-confidence errors from propagating through the system (bad Re-ID matches). Critical for data quality but not essential for MVP.

**Independent Test**: Can be tested by processing new images, verifying that <51% confidence detections appear in review queue, and confirming they're marked as audited after processing.

**Acceptance Scenarios**:

1. **Given** new images are processed, **When** detection confidence is below 51%, **Then** detection is automatically flagged for review with flag_reason="low_confidence"
2. **Given** flagged detections exist, **When** user navigates to "Needs Review" page, **Then** they see paginated list of unaudited detections sorted by confidence (lowest first)
3. **Given** user completes vision audit on flagged detection, **When** audit result is saved, **Then** detection is marked as reviewed and removed from queue

---

### User Story 3 - Batch Reporting and Analytics (Priority: P3)

After completing vision audits over time, users want to understand classification accuracy patterns. They access an "Audit Analytics" dashboard showing overall accuracy by confidence band (40-45%, 45-50%, 50-55%, etc.), common misclassification patterns (e.g., "85% of buck classifications at 50-51% are actually doe"), and species-specific error rates. This helps identify when model retraining is needed.

**Why this priority**: Valuable for long-term model improvement but not essential for core audit functionality.

**Independent Test**: Can be tested by running multiple audits, then verifying that analytics page displays accurate statistics aggregated from audit results.

**Acceptance Scenarios**:

1. **Given** multiple audit jobs have completed, **When** user views analytics dashboard, **Then** they see accuracy percentage by confidence band (e.g., "50-51%: 71% accuracy")
2. **Given** audit results contain misclassifications, **When** user views pattern analysis, **Then** they see top misclassification types (e.g., "buck→doe: 48 occurrences")
3. **Given** audit analytics show accuracy below 80% for a confidence range, **When** system generates recommendations, **Then** it suggests raising auto-accept threshold or model retraining

---

### Edge Cases

- What happens when Anthropic API rate limit is exceeded during batch processing?
- How does system handle vision API timeout for a single image (retry logic)?
- What if vision API returns uncertain classification - does it require human review?
- How are already-audited detections handled if user re-audits the same batch?
- What happens if user lacks sufficient API credits mid-batch?
- How does system handle images that have been deleted from filesystem but exist in database?
- What if multiple users simultaneously audit the same detections?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST integrate Anthropic Python SDK (anthropic library) into Docker worker container with configurable API key via environment variable
- **FR-002**: System MUST provide frontend UI component for selecting detections and initiating vision audit batches
- **FR-003**: System MUST queue vision audit jobs via Celery with status tracking (pending/processing/complete/failed)
- **FR-004**: System MUST send each image to Claude Vision API with standardized classification prompt (buck/doe/fawn/cattle/pig/uncertain)
- **FR-005**: System MUST store audit results in database including: detection_id, vision_classification, confidence_match_status (correct/incorrect/uncertain), audit_timestamp, auditor="claude_vision"
- **FR-006**: System MUST automatically flag new detections with confidence <51% for review based on empirical audit findings
- **FR-007**: System MUST provide "Needs Review" queue UI showing flagged detections with ability to batch process
- **FR-008**: System MUST allow users to approve vision audit corrections, updating detection classification and setting is_reviewed=true
- **FR-009**: System MUST handle Anthropic API errors gracefully with retry logic (3 attempts) and failure notification
- **FR-010**: System MUST support batch sizes of 20-100 images with configurable limit to prevent API quota exhaustion
- **FR-011**: System MUST provide real-time progress updates during audit job execution using websockets or polling
- **FR-012**: System MUST generate audit summary reports showing total reviewed, accuracy percentage, corrections applied
- **FR-013**: System MUST validate that ANTHROPIC_API_KEY is configured before allowing audit initiation
- **FR-014**: Frontend MUST display vision audit results in comparison view: database classification vs vision classification side-by-side
- **FR-015**: System MUST log all vision API calls including image_id, request timestamp, response, tokens used for cost tracking

### Key Entities

- **VisionAuditJob**: Represents a batch audit request containing job_id, user_id, detection_ids (array), status (pending/processing/complete/failed), created_at, completed_at, total_images, processed_images, accuracy_percentage
- **VisionAuditResult**: Individual image audit outcome containing result_id, job_id, detection_id, db_classification, vision_classification, match_status (correct/incorrect/uncertain), vision_confidence_score, vision_reasoning (text), audited_at, auditor="claude_vision", tokens_used
- **DetectionReviewFlag**: Tracks detections requiring review containing flag_id, detection_id, flag_reason (low_confidence/user_reported/manual_review), flagged_at, reviewed (boolean), reviewed_at, reviewed_by

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can initiate vision audit on 20-100 selected detections and receive results within 5 minutes for batch of 50 images
- **SC-002**: System processes vision audit batches with 99%+ reliability (less than 1% job failure rate due to API issues)
- **SC-003**: Vision audit achieves 95%+ accuracy when validating against human expert review on sample set of 100 images
- **SC-004**: Users can review audit results and approve corrections in under 30 seconds per batch of 20 images
- **SC-005**: System correctly flags 100% of detections with confidence <51% for review queue
- **SC-006**: Audit analytics dashboard loads in under 2 seconds and displays accuracy metrics aggregated from all historical audits
- **SC-007**: Vision API integration costs remain under $0.02 per image analyzed (based on Claude Vision pricing)
- **SC-008**: System handles concurrent audit jobs from multiple users without job interference or data corruption
- **SC-009**: Users receive real-time progress updates during audit with less than 5-second latency
- **SC-010**: 90% of users successfully complete their first vision audit without requiring support documentation

## Assumptions

- Anthropic API key will be provided by user with sufficient quota/credits for batch processing
- Images are stored on accessible filesystem path from Docker worker container
- Existing detection confidence scores are available in database for threshold-based flagging
- Users have appropriate permissions to approve classification corrections
- Network connectivity between Docker worker and Anthropic API is stable
- Claude Vision API response time averages 2-3 seconds per image for 20MP trail camera images
- Standard vision classification prompt will work across all deer/cattle/pig species without fine-tuning

## Dependencies

- Anthropic Python SDK library (must be added to requirements.txt)
- Existing Celery worker infrastructure for background job processing
- Database schema updates to support VisionAuditJob, VisionAuditResult, DetectionReviewFlag entities
- Frontend component library (React/Material-UI) for audit UI components
- Existing API authentication/authorization system for securing audit endpoints
- Claude Vision API availability and pricing stability

## Out of Scope

- Training or fine-tuning custom vision models - uses Anthropic's pre-trained Claude Vision
- Real-time live camera feed analysis - only processes stored images
- Automated retraining of YOLOv8 detection model based on audit results
- Multi-language support for vision classification prompts
- Image preprocessing or enhancement before vision analysis
- Integration with vision APIs other than Anthropic (Google Vision, AWS Rekognition, etc.)
- Historical re-audit of all 59,185 existing images (only new low-confidence detections)

## Risks

- **API Cost**: High-volume audits could incur significant Anthropic API costs if not properly rate-limited or quota-managed
- **API Availability**: Dependency on Anthropic API uptime - outages would block audit functionality
- **Classification Drift**: Claude Vision model updates could change classification behavior over time
- **Privacy/Security**: Sending wildlife images to external API may have data governance implications
- **Performance**: Large batch processing could overwhelm worker if not properly throttled
- **Accuracy Variance**: Vision API may perform differently on night/IR images vs daylight images
