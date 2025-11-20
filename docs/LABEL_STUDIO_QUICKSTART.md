# Label Studio Quick Start Guide

**Feature:** Phase 2B - Antler Detection Annotation
**Tool:** Label Studio (Docker container)
**Status:** Ready for use

---

## LABEL STUDIO ACCESS

**URL:** http://localhost:8080
**Container:** thumper_labelstudio
**Port:** 8080

---

## FIRST-TIME SETUP

### Step 1: Create Account

1. Open browser: http://localhost:8080
2. You'll see signup page
3. Create account:
   - Email: (any email, not validated)
   - Password: (remember this)
4. Click "Sign Up"

### Step 2: Create Project

1. Click "Create Project"
2. Project Name: **Antler Detection - Phase 2B**
3. Description: **Annotate deer with antler keypoints and body markings for Re-ID enhancement**

### Step 3: Import Configuration

**Option A: Copy/Paste Configuration**

1. In project setup, go to "Labeling Interface" tab
2. Click "Code" button (top right)
3. Copy entire contents of `docs/LABEL_STUDIO_ANTLER_CONFIG.xml`
4. Paste into editor
5. Click "Save"

**Option B: Upload Configuration File**

1. In project setup, go to "Labeling Interface" tab
2. Click "Import Config" button
3. Select file: `docs/LABEL_STUDIO_ANTLER_CONFIG.xml`
4. Click "Save"

### Step 4: Import Images

**Important:** Images are already mounted in the container at `/label-studio/data/antler_samples`

**Method 1: Local Storage (Recommended)**

1. In project setup, go to "Cloud Storage" tab
2. Click "Add Source Storage"
3. Select "Local files"
4. Settings:
   - Storage Title: **Antler Samples**
   - Absolute local path: `/label-studio/data/antler_samples`
   - File Filter Regex: `.*\.(jpg|jpeg|png)$`
   - Treat every bucket object as a source file: **Checked**
5. Click "Add Storage"
6. Click "Sync Storage" button
7. Confirm 73 tasks imported

**Method 2: Manual Upload**

1. In project setup, go to "Import" tab
2. Click "Upload Files"
3. Navigate to:
   - `src/models/training_data/antler_annotation_samples/bucks/` (50 images)
   - `src/models/training_data/antler_annotation_samples/does/` (12 images)
   - `src/models/training_data/antler_annotation_samples/mixed/` (11 images)
4. Select all images and upload
5. Confirm 73 tasks imported

---

## STARTING ANNOTATION

1. Click on project: "Antler Detection - Phase 2B"
2. You'll see list of tasks (73 images)
3. Click on first task
4. Annotation interface will open
5. Follow guidelines in `docs/ANTLER_ANNOTATION_GUIDELINES.md`

---

## ANNOTATION INTERFACE OVERVIEW

**Left Panel: Tools**
- Rectangle (Bounding Box) - Draw boxes around deer
- KeyPoint - Click to place antler keypoints
- Pan/Zoom - Navigate image

**Right Panel: Labels**
- **bbox**: Buck, Doe, Fawn classifications
- **antler_points**: 16 keypoint labels (left/right antlers)
- **markings**: Scar, injury, white_patch, etc.
- **Metadata**: Point count, symmetry, visibility

**Bottom Panel: Controls**
- Submit - Save current annotation
- Update - Save changes to existing annotation
- Skip - Skip this task for now

---

## ANNOTATION WORKFLOW QUICK REFERENCE

**For each image:**

1. **Draw bounding box** around deer body
   - Select buck/doe/fawn label
   - Click and drag to create box

2. **If buck: Annotate antler keypoints**
   - Select "left_main_beam" label
   - Click at base of left antler
   - Continue with left_brow_tine, left_g2, etc.
   - Repeat for right antler
   - Skip points that don't exist

3. **Annotate body markings** (if any)
   - Draw boxes around scars, white patches, etc.
   - Select appropriate marking label

4. **Fill metadata**
   - Point count (total points on both antlers)
   - Symmetry (symmetric/asymmetric)
   - Visibility (full/partial/obscured)
   - Special features (drop_tine, split_g2, etc.)

5. **Click Submit**

---

## KEYBOARD SHORTCUTS

**Navigation:**
- Arrow keys: Next/previous task
- Space: Submit and next
- Ctrl+Enter: Submit

**Tools:**
- 1: Rectangle tool
- 2: KeyPoint tool
- 3: Pan tool
- Z: Zoom in
- X: Zoom out

**Editing:**
- Delete: Remove selected annotation
- Ctrl+Z: Undo
- Ctrl+Shift+Z: Redo

---

## PROGRESS TRACKING

**View Progress:**
1. Click project name (top left)
2. Dashboard shows:
   - Total tasks: 73
   - Completed: X
   - Remaining: Y

**Filter Tasks:**
- All tasks
- Completed only
- Incomplete only

**Search:**
- Filter by filename
- Filter by annotation status

---

## EXPORT ANNOTATIONS

**When ready to export (after completing annotations):**

1. Go to project dashboard
2. Click "Export" button (top right)
3. Select format: **JSON**
4. Click "Export"
5. Save file: `antler_annotations_phase2b.json`

**Next:** Convert to YOLO format using `scripts/convert_labelstudio_to_yolo.py`

---

## QUALITY ASSURANCE

**Before exporting, review 10% random sample:**

1. Click "Tasks" tab
2. Sort by random
3. Review every 7th annotation
4. Check for:
   - Correct keypoint placement
   - Complete annotations
   - Accurate metadata
   - No missing markings

**Common Issues:**
- Keypoints not at tine tips
- Wrong point count
- Missing distinctive markings
- Bounding box cuts off deer

---

## TROUBLESHOOTING

**Issue: Can't access http://localhost:8080**
```bash
# Check container status
docker-compose ps labelstudio

# Check logs
docker-compose logs labelstudio

# Restart if needed
docker-compose restart labelstudio
```

**Issue: Images not showing**
```bash
# Verify image mount
docker-compose exec labelstudio ls -la /label-studio/data/antler_samples/bucks/

# Should show 50 images
```

**Issue: Lost annotations**
```bash
# Annotations are persisted in Docker volume
docker volume ls | grep labelstudio

# Volume: thumper_labelstudio_data
```

**Issue: Can't import configuration**
- Copy/paste XML content directly
- Make sure all tags are closed
- Check for special characters

---

## CONTAINER MANAGEMENT

**Start Label Studio:**
```bash
docker-compose up -d labelstudio
```

**Stop Label Studio:**
```bash
docker-compose stop labelstudio
```

**Restart Label Studio:**
```bash
docker-compose restart labelstudio
```

**View Logs:**
```bash
docker-compose logs -f labelstudio
```

**Check Status:**
```bash
docker-compose ps labelstudio
curl http://localhost:8080/health
```

---

## DATA PERSISTENCE

**Annotations Storage:**
- Location: Docker volume `thumper_labelstudio_data`
- Persists across container restarts
- Backup recommended before major changes

**Backup Annotations:**
```bash
# Export from Label Studio UI
# Or backup Docker volume
docker run --rm -v thumper_labelstudio_data:/data -v $(pwd):/backup alpine tar czf /backup/labelstudio_backup_$(date +%Y%m%d).tar.gz /data
```

**Restore Annotations:**
```bash
# Import in Label Studio UI
# Or restore Docker volume
docker run --rm -v thumper_labelstudio_data:/data -v $(pwd):/backup alpine tar xzf /backup/labelstudio_backup_YYYYMMDD.tar.gz -C /
```

---

## SAMPLE STATISTICS

**Dataset Breakdown:**
- Bucks: 50 images (68.5%)
  - High confidence avg: 0.963
  - Large bbox avg: 244,893 px
- Does: 12 images (16.4%)
  - High confidence avg: 0.969
- Mixed/Challenging: 11 images (15.1%)
  - Fawns: 0 (none at high confidence)
  - Medium confidence: 11

**Expected Annotation Time:**
- Simple buck: 2-3 minutes
- Complex buck: 5-7 minutes
- Does/markings: 1-2 minutes
- Average: 3-4 minutes/image
- Total: 3-5 hours for 73 images

---

## NEXT STEPS

**After completing annotations:**

1. Export annotations (JSON format)
2. Convert to YOLO format: `scripts/convert_labelstudio_to_yolo.py`
3. Quality review (10% sample)
4. Train YOLOv8-pose model
5. Evaluate on validation set
6. If successful: Expand to 500-1000 images
7. Integrate into Re-ID pipeline

---

## HELPFUL LINKS

**Documentation:**
- Annotation Guidelines: `docs/ANTLER_ANNOTATION_GUIDELINES.md`
- Annotation Schema: `docs/ANTLER_DETECTION_ANNOTATION_SCHEMA.md`
- Configuration File: `docs/LABEL_STUDIO_ANTLER_CONFIG.xml`

**Sample Images:**
- Bucks: `src/models/training_data/antler_annotation_samples/bucks/`
- Does: `src/models/training_data/antler_annotation_samples/does/`
- Mixed: `src/models/training_data/antler_annotation_samples/mixed/`
- Metadata: `src/models/training_data/antler_annotation_samples/metadata/sample_selection.json`

**Label Studio:**
- Official Docs: https://labelstud.io/guide/
- Keypoint Annotation: https://labelstud.io/templates/keypoint_detection
- Local Files: https://labelstud.io/guide/storage.html#Local-storage

---

**Document Version:** 1.0
**Last Updated:** November 16, 2025
**Status:** Ready for use
