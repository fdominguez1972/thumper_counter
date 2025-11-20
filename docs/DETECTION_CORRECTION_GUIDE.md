# Detection Correction Quick Start Guide

**Last Updated:** November 15, 2025
**System:** Thumper Counter - Deer Tracking ML Pipeline
**Status:** Feature Complete and Tested

---

## Overview

The Detection Correction system allows you to manually review and correct ML classification errors, then export the corrected data to retrain the YOLOv8 model for improved accuracy over time.

**Complete Workflow:**
1. Review images in the frontend UI
2. Correct misclassifications (single or batch)
3. Export corrected data to YOLO training format
4. Retrain model with improved dataset
5. Deploy updated model

---

## Part 1: Manual Correction in Frontend

### Access the Images Page

**URL:** http://localhost:3000/images

The Images page displays all processed images with their detections, organized in a grid view.

### Features Available

**Filter Options:**
- Location (dropdown)
- Classification (buck, doe, unknown, cattle, pig, raccoon, etc.)
- Date Range (start/end date pickers)
- Processing Status (completed, failed, pending)
- Has Detections (toggle)

**Sort Options:**
- Newest First (default)
- Oldest First
- Most Detections
- Filename A-Z

**Selection:**
- Click checkboxes to select multiple images
- Selected count displayed at top
- "Clear Selection" button available

### Single Detection Correction

**Step-by-Step:**

1. Click on any image thumbnail to open lightbox
2. View full-resolution image with detection info
3. Click the "Edit Detection" button
4. Detection Correction Dialog appears with:
   - Current classification
   - Confidence score
   - Image filename
   - Deer name (if assigned)

5. Make corrections:
   - **Valid/Invalid Toggle:** Mark if detection is correct
   - **Classification:** Select from dropdown or enter custom
     - Predefined: buck, doe, fawn, unknown, cattle, pig, raccoon, human, vehicle, no animals
     - Custom: Type your own tag
   - **Correction Notes:** Add explanation (optional)
   - **Reviewer Name:** Your name/ID

6. Click "Save Correction"
7. Dialog closes, changes saved to database

### Batch Correction

**When to Use:**
- Multiple images from same photo burst (all same animal)
- Systematic classification error (e.g., all does misclassified as bucks)
- Bulk quality control

**Step-by-Step:**

1. Select multiple images using checkboxes (up to 1000)
2. Click "Batch Edit" button at top
3. Batch Correction Dialog appears showing:
   - Number of images selected
   - Total detections that will be affected
   - Warning about bulk operation

4. Make corrections:
   - Same fields as single correction
   - Applied to ALL selected detections
   - **Caution:** This affects multiple detections at once

5. Click "Apply to All"
6. Progress indicator shows operation
7. Success message displays count corrected

**Performance:**
- Optimized for 100x faster bulk queries
- Can handle 1000 detections in < 1 second
- All changes committed in single transaction

---

## Part 2: Export Corrected Data for Retraining

### Prerequisites

- At least some detections marked as reviewed (is_reviewed = true)
- Corrections saved in database
- Access to Docker containers

### Export Command

**Basic Usage:**
```bash
docker-compose exec backend python3 scripts/export_training_data.py \
  --output-dir /mnt/training_data/corrected \
  --reviewed-only \
  --format both
```

**Options:**

- `--output-dir DIR`: Output directory (default: /mnt/training_data/corrected)
- `--min-confidence 0.5`: Minimum ML confidence to include (default: 0.5)
- `--reviewed-only`: Only export human-reviewed detections (RECOMMENDED)
- `--include-invalid`: Include detections marked as invalid (default: exclude)
- `--format {yolo,csv,both}`: Export format (default: both)

### Output Structure

**YOLO Format (for training):**
```
/mnt/training_data/corrected/
  images/
    train/           # 80% of images
      image1.jpg
      image2.jpg
    val/             # 20% of images
      image3.jpg
  labels/
    train/
      image1.txt     # YOLO format: class x y width height
      image2.txt
    val/
      image3.txt
  data.yaml          # YOLOv8 config file
```

**CSV Format (for analysis):**
```
corrections.csv columns:
- image_id
- filename
- detection_id
- original_classification
- corrected_classification
- confidence
- is_valid
- correction_notes
- reviewed_by
- reviewed_at
```

### Verify Export

**Check file counts:**
```bash
# Count exported images
ls /mnt/training_data/corrected/images/train/*.jpg | wc -l
ls /mnt/training_data/corrected/images/val/*.jpg | wc -l

# Check CSV
head /mnt/training_data/corrected/corrections.csv
```

**Expected Output:**
```
[INFO] Exporting corrected detections...
[INFO] Found 150 reviewed detections
[INFO] Train split: 120 images (80%)
[INFO] Val split: 30 images (20%)
[OK] Export complete
```

---

## Part 3: Retrain YOLOv8 Model

### Training Command

**Full Retraining:**
```bash
docker-compose exec worker python3 scripts/train_deer_multiclass.py \
  --data /mnt/training_data/corrected/data.yaml \
  --epochs 100 \
  --batch 32 \
  --patience 20
```

**Quick Validation Run:**
```bash
# Test with just 10 epochs to verify setup
docker-compose exec worker python3 scripts/train_deer_multiclass.py \
  --data /mnt/training_data/corrected/data.yaml \
  --epochs 10 \
  --batch 16
```

### Training Parameters

- `--data`: Path to data.yaml config (REQUIRED)
- `--epochs 100`: Number of training epochs (default: 200)
- `--batch 32`: Batch size (adjust based on GPU memory)
- `--patience 20`: Early stopping patience (default: 20)
- `--imgsz 640`: Image size for training (default: 640)

**GPU Memory Guidance:**
- RTX 4080 Super (16GB): batch=32 comfortable
- RTX 3080 (10GB): batch=16-24
- RTX 3060 (12GB): batch=16-24

### Monitor Training

**Check progress:**
```bash
# View training logs
docker-compose logs -f worker | grep "Epoch\|mAP"

# Or tail the log file
tail -f src/models/runs/corrected_model/train/train.log
```

**Expected Output:**
```
Epoch 1/100: 100%|██████████| 15/15 [00:12<00:00,  1.21it/s]
      Class     Images  Instances      P      R   mAP50  mAP50-95
        all         30         45  0.856  0.724  0.804     0.620
        doe         30         25  0.892  0.760  0.812     0.635
       buck         30         20  0.820  0.688  0.796     0.605
```

### Training Completion

**Results saved to:**
```
src/models/runs/corrected_model/
  weights/
    best.pt        # Best model checkpoint
    last.pt        # Last epoch checkpoint
  train/
    confusion_matrix.png
    results.csv
    results.png
```

---

## Part 4: Deploy Updated Model

### Backup Current Model

**ALWAYS backup before replacing:**
```bash
# Create backup with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp src/models/yolov8n_deer.pt \
   src/models/yolov8n_deer_BACKUP_$TIMESTAMP.pt

echo "Backup created: yolov8n_deer_BACKUP_$TIMESTAMP.pt"
```

### Deploy New Model

**Copy trained model to production:**
```bash
cp src/models/runs/corrected_model/weights/best.pt \
   src/models/yolov8n_deer.pt
```

### Restart Worker

**Load new model:**
```bash
docker-compose restart worker
```

**Verify deployment:**
```bash
# Check worker loaded new model
docker-compose logs worker | grep "Model file validated"

# Expected output:
# [OK] Model file validated: yolov8n_deer.pt (6.00MB)
```

### Test New Model

**Process a test image:**
```bash
curl -X POST "http://localhost:8001/api/processing/batch?limit=10"
```

**Check detection results:**
```bash
docker-compose exec -T db psql -U deertrack deer_tracking -c \
  "SELECT classification, COUNT(*), ROUND(AVG(confidence)::numeric, 3)
   FROM detections
   WHERE created_at > NOW() - INTERVAL '5 minutes'
   GROUP BY classification;"
```

---

## Part 5: Continuous Improvement Loop

### Recommended Workflow

**Monthly Cycle:**

1. **Week 1-2:** Run system, collect images
2. **Week 3:** Manual review session
   - Review 100-200 detections
   - Correct misclassifications
   - Focus on low-confidence detections (< 0.6)
3. **Week 4:** Retrain and deploy
   - Export corrected data
   - Train new model
   - Test and deploy
   - Repeat

### Focus Areas for Review

**Priority 1 - Low Confidence:**
```sql
-- Find detections needing review
SELECT id, classification, confidence, filename
FROM detections d
JOIN images i ON d.image_id = i.id
WHERE confidence < 0.6
  AND is_reviewed = false
ORDER BY confidence ASC
LIMIT 100;
```

**Priority 2 - Misclassified Sex:**
- Bucks classified as does (antlers present)
- Does classified as bucks (no antlers visible)

**Priority 3 - Non-Deer:**
- Cattle, pigs, raccoons
- Verify classification accuracy

### Track Improvement

**Query correction statistics:**
```sql
-- Count corrections by type
SELECT
  classification as original,
  corrected_classification as corrected,
  COUNT(*) as corrections
FROM detections
WHERE is_reviewed = true
  AND corrected_classification IS NOT NULL
GROUP BY classification, corrected_classification
ORDER BY corrections DESC;
```

**Expected Results:**
- Classification accuracy improves 5-10% per cycle
- False positive rate decreases
- Model confidence increases on correct classifications

---

## Troubleshooting

### Issue: Correction Dialog Won't Open

**Check:**
1. Image has detections (`detection_count > 0`)
2. Browser console for JavaScript errors
3. Backend API is accessible: `curl http://localhost:8001/health`

**Solution:**
```bash
# Restart frontend
docker-compose restart frontend
```

### Issue: Batch Correction Times Out

**Symptoms:**
- Request takes > 30 seconds
- Browser shows timeout error

**Cause:** Too many detections selected (> 1000)

**Solution:**
- Select fewer images (recommended: < 500)
- Or increase batch size limit in code

### Issue: Export Script Fails

**Error:** "No reviewed detections found"

**Check:**
```sql
-- Count reviewed detections
SELECT COUNT(*) FROM detections WHERE is_reviewed = true;
```

**Solution:** Review at least 10-20 detections before exporting

### Issue: Training Fails - Out of Memory

**Error:** "CUDA out of memory"

**Solution:**
```bash
# Reduce batch size
docker-compose exec worker python3 scripts/train_deer_multiclass.py \
  --data /mnt/training_data/corrected/data.yaml \
  --batch 8 \
  --epochs 100
```

---

## API Reference

### Single Detection Correction

**Endpoint:** `PATCH /api/detections/{detection_id}/correct`

**Request Body:**
```json
{
  "is_valid": true,
  "corrected_classification": "doe",
  "correction_notes": "Visible udders, definitely female",
  "reviewed_by": "john_doe"
}
```

**Response:**
```json
{
  "success": true,
  "detection_id": "uuid",
  "message": "Detection reviewed and classification corrected to doe, notes added",
  "detection": { ... }
}
```

### Batch Correction

**Endpoint:** `PATCH /api/detections/batch/correct`

**Request Body:**
```json
{
  "detection_ids": ["uuid1", "uuid2", "uuid3"],
  "is_valid": true,
  "corrected_classification": "buck",
  "correction_notes": "Photo burst of same buck",
  "reviewed_by": "john_doe"
}
```

**Response:**
```json
{
  "success": true,
  "total_requested": 3,
  "total_corrected": 3,
  "failed_ids": [],
  "message": "Reviewed 3 detections and marked as valid, classification corrected to buck, notes added"
}
```

---

## Best Practices

### Review Guidelines

1. **Start with High-Confidence Errors**
   - These have biggest impact on model
   - Easy to verify (obvious mistakes)

2. **Use Batch Correction for Photo Bursts**
   - Trail cameras capture 3-5 photos in quick succession
   - Same animal in all images
   - Correct entire burst at once

3. **Add Detailed Notes**
   - Explain WHY you corrected
   - Reference visible features (antlers, size, behavior)
   - Helps validate training data later

4. **Be Consistent**
   - Fawns: "unknown" (sex not determinable)
   - Young bucks: "buck" (if antlers visible)
   - Does with fawns: "doe" (not "fawn")

### Training Data Quality

**Good Training Data:**
- Clear, well-lit images
- Animal clearly visible
- Minimal obstruction
- Confidence > 0.5

**Exclude from Training:**
- Blurry images
- Heavy obstruction (>50% animal hidden)
- Poor lighting (night shots with low visibility)
- Edge cases (animal partially in frame)

### Model Deployment Safety

**Always:**
1. Backup current model before replacing
2. Test new model on small batch first
3. Monitor classification distribution after deployment
4. Keep rollback plan ready

**Never:**
- Deploy untested model to production
- Delete backup files
- Skip validation step

---

## Performance Metrics

### Current System Performance

**Model:** yolov8n_deer.pt (6-class simplified)
**Accuracy:** mAP50 = 85.1%, mAP50-95 = 66.7%
**Speed:** 0.04s per image (GPU), 1.2 images/sec (with DB writes)

**Classification Distribution (as of Nov 15, 2025):**
- Does: 7,504 detections (64.8%)
- Bucks: 4,070 detections (35.2%)
- Unknown: 4 detections (0.03%)
- Average Confidence: 0.73-0.78

**Database Status:**
- Total Images: 59,185
- Processed: 58,751 (99.27%)
- Total Detections: 11,578
- Deer Profiles: 379
- Re-ID Assignment Rate: 60%

---

## Support and Documentation

**Additional Resources:**
- System Documentation: `/docs/README.md`
- Model Training Guide: `/docs/MODEL_TRAINING.md`
- API Documentation: `http://localhost:8001/docs`
- Session Handoffs: `/docs/SESSION_*.md`

**Common Files:**
- Export Script: `scripts/export_training_data.py`
- Training Script: `scripts/train_deer_multiclass.py`
- Correction Dialogs: `frontend/src/components/*CorrectionDialog.tsx`
- Backend Endpoints: `src/backend/api/detections.py`

**Getting Help:**
- Check troubleshooting section above
- Review recent session handoffs
- Examine API logs: `docker-compose logs backend`
- Check worker logs: `docker-compose logs worker`

---

**Document Version:** 1.0
**Feature Status:** Complete and Tested
**Last Verification:** November 15, 2025
