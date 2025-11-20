# AI Model Retraining Workflow

This document describes the complete workflow for improving detection accuracy through manual review and model retraining.

## Overview

The system is designed to learn from your corrections. As you review and correct misclassifications (like cattle marked as doe/buck), you build a curated training dataset that improves the AI models.

## Workflow Steps

### 1. Review and Correct Images

**In the Web Interface (http://localhost:3000):**

#### Images Tab
- Browse all images with location and classification filters
- Select individual images or use batch selection
- Click "Edit" button (pencil icon) in lightbox view
- Or select multiple images and click "Edit Selected"

#### Deer Profiles
- View all sightings for each deer
- Edit individual images from the deer's photo gallery
- Batch edit multiple sightings at once

**Correction Actions:**
- Mark misclassifications as invalid (rear-end shots, wrong species, poor quality)
- Correct classifications: buck, doe, fawn, cattle, pig, raccoon, unknown
- Add notes explaining the correction

### 2. Export Corrected Data

Once you've reviewed a significant number of images (recommended: 500+ corrections), export the data for retraining.

**Run the export script:**
```bash
# Export all reviewed detections
docker-compose exec worker python3 scripts/export_training_data.py

# Export with custom options
docker-compose exec worker python3 scripts/export_training_data.py \
    --output-dir /mnt/training_data/corrected_$(date +%Y%m%d) \
    --reviewed-only \
    --min-confidence 0.5
```

**Output:**
- `/mnt/training_data/corrected/` directory with:
  - `images/train/` - 80% of images for training
  - `images/val/` - 20% of images for validation
  - `labels/train/` - YOLOv8 format labels
  - `labels/val/` - Validation labels
  - `data.yaml` - YOLOv8 configuration
  - `corrected_detections.csv` - Detailed report
  - `README.md` - Next steps guide

### 3. Analyze Corrections

**Review the export statistics:**
```bash
# Check class distribution
cat /mnt/training_data/corrected/README.md

# Analyze corrections in detail
head -50 /mnt/training_data/corrected/corrected_detections.csv
```

**Look for:**
- Are cattle now properly labeled as cattle?
- Are buck/doe classifications accurate?
- Enough examples of each class (aim for 100+ per class)

### 4. Retrain the Model

**Start training with your corrected dataset:**
```bash
docker-compose exec worker python3 scripts/train_deer_multiclass.py \
    --data /mnt/training_data/corrected/data.yaml \
    --epochs 100 \
    --batch 16 \
    --patience 20 \
    --name corrected_$(date +%Y%m%d)
```

**Training will:**
- Use your corrected images as ground truth
- Run for up to 100 epochs (stops early if no improvement)
- Save best model to `/app/src/models/runs/corrected_YYYYMMDD/weights/best.pt`
- Show real-time training metrics

**Expected training time:**
- 500 images: ~15-30 minutes
- 1000 images: ~30-60 minutes
- 2000+ images: 1-2 hours

### 5. Evaluate the New Model

**Test the retrained model:**
```bash
# Evaluate on test set
docker-compose exec worker python3 scripts/evaluate_multiclass_model.py \
    --model /app/src/models/runs/corrected_YYYYMMDD/weights/best.pt

# Test on random samples
docker-compose exec worker python3 scripts/test_detection.py \
    --model /app/src/models/runs/corrected_YYYYMMDD/weights/best.pt \
    --num-samples 20
```

**Compare metrics:**
- mAP50 (higher is better)
- Precision and Recall per class
- Check if cattle detection improved
- Verify buck/doe distinction is more accurate

### 6. Deploy the Improved Model

**If the new model performs better:**
```bash
# Backup current model
docker-compose exec worker cp /app/src/models/yolov8n_deer.pt \
    /app/src/models/yolov8n_deer_backup_$(date +%Y%m%d).pt

# Deploy new model
docker-compose exec worker cp \
    /app/src/models/runs/corrected_YYYYMMDD/weights/best.pt \
    /app/src/models/yolov8n_deer.pt

# Restart worker to load new model
docker-compose restart worker
```

**The system will now use your improved model for all new detections.**

### 7. Monitor Performance

**After deployment:**
- Continue reviewing new detections
- Track if misclassifications decrease
- Pay attention to edge cases (unusual lighting, angles, etc.)
- Repeat the cycle when you have more corrections

## Best Practices

### Review Strategy
1. **Start with obvious errors** - Cattle marked as deer, clearly wrong sex classifications
2. **Focus on high-confidence mistakes** - If ML is very confident but wrong, it needs correction
3. **Review diverse conditions** - Different times of day, weather, camera angles
4. **Batch similar errors** - If one cattle image is wrong, check similar ones

### Training Data Quality
- **Minimum recommended:** 500 reviewed images
- **Ideal:** 1000+ reviewed images with good class distribution
- **Balance classes:** Try to have similar numbers of buck, doe, fawn, cattle, etc.
- **Quality over quantity:** Accurate corrections more important than volume

### Retraining Frequency
- **After initial review:** First major cleanup (500+ corrections)
- **Monthly:** If actively reviewing images
- **When needed:** If you notice pattern of specific errors
- **After new camera locations:** Different environments may need adaptation

### Model Evaluation
- **Always compare** old vs new model on same test set
- **Don't deploy if worse** - Keep old model if new one doesn't improve
- **Document changes** - Keep notes on what corrections led to improvements
- **Incremental improvement** - Each cycle should make small gains

## Troubleshooting

### Export finds no detections
```bash
# Check if you have reviewed images
docker-compose exec backend python3 -c "
from backend.core.database import get_db
from backend.models.detection import Detection
db = next(get_db())
reviewed = db.query(Detection).filter(Detection.is_reviewed == True).count()
print(f'Reviewed detections: {reviewed}')
"
```

### Training fails with out-of-memory
- Reduce batch size: `--batch 8` or `--batch 4`
- Check GPU memory: `docker-compose exec worker nvidia-smi`
- Free up GPU: `docker-compose restart worker`

### Model not improving
- Need more training data (aim for 1000+ images)
- Check class distribution (balanced classes work better)
- Review validation metrics - may be overfitting
- Consider collecting more diverse examples

## Example Complete Cycle

```bash
# 1. Review images in web interface
#    - Correct 750 images over a few days
#    - Mark cattle properly as cattle
#    - Fix buck/doe confusions

# 2. Export corrected data
docker-compose exec worker python3 scripts/export_training_data.py

# 3. Check what we have
cat /mnt/training_data/corrected/README.md

# 4. Train new model
docker-compose exec worker python3 scripts/train_deer_multiclass.py \
    --data /mnt/training_data/corrected/data.yaml \
    --epochs 100 \
    --batch 16 \
    --name corrected_20251108

# 5. Evaluate
docker-compose exec worker python3 scripts/evaluate_multiclass_model.py \
    --model /app/src/models/runs/corrected_20251108/weights/best.pt

# 6. If better, deploy
docker-compose exec worker cp /app/src/models/yolov8n_deer.pt \
    /app/src/models/yolov8n_deer_backup_20251108.pt

docker-compose exec worker cp \
    /app/src/models/runs/corrected_20251108/weights/best.pt \
    /app/src/models/yolov8n_deer.pt

docker-compose restart worker

# 7. Test new model on incoming images
#    - Monitor for improvements
#    - Continue reviewing and correcting
```

## Success Metrics

Track these over time to measure improvement:
- **Cattle false positives:** Should decrease significantly
- **Buck/Doe accuracy:** Should improve with each cycle
- **Overall mAP50:** Target >0.85 (currently ~0.80)
- **Review time:** Fewer corrections needed per 100 images
- **Confidence distribution:** More high-confidence correct predictions

## Questions?

See `/mnt/i/projects/thumper_counter/scripts/export_training_data.py` for technical details on data export.

See `/mnt/i/projects/thumper_counter/scripts/train_deer_multiclass.py` for training configuration options.
