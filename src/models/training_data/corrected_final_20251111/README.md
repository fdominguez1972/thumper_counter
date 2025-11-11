# Corrected Training Data Export

Exported: 2025-11-11T20:03:12.949516

## Summary
- Total detections: 2145
- Reviewed only: True
- Include invalid: False
- Min confidence: 0.5

## Next Steps

### Retrain YOLOv8 Model
```bash
# From worker container
python3 scripts/train_deer_multiclass.py \
    --data /mnt/training_data/corrected/data.yaml \
    --epochs 100 \
    --batch 16 \
    --name corrected_model
```

### Evaluate Model
```bash
python3 scripts/evaluate_multiclass_model.py \
    --model /app/src/models/runs/corrected_model/weights/best.pt
```

### Deploy Improved Model
```bash
# Replace current model
cp /app/src/models/runs/corrected_model/weights/best.pt \
   /app/src/models/yolov8n_deer.pt

# Restart worker to load new model
docker-compose restart worker
```

## Class Mapping (Simplified for Male/Female Counting)
- doe (3): Female deer
- buck (5): Male deer (all ages - young/mid/mature combined)
- unknown (4): Unknown sex (includes fawn which contains both male/female)
- cattle (0): Cattle
- pig (1): Pig/feral hog
- raccoon (2): Raccoon

## Notes
- All buck age classes (young, mid, mature) combined into single 'buck' class
- Fawn class merged into 'unknown' since young deer can be either male or female
- This allows accurate male vs female population counting
- Mature buck classifier can be built later from collected images
- Review the corrected_detections.csv file for detailed analysis of your corrections.
