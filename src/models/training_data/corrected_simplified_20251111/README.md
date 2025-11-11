# Corrected Training Data Export

Exported: 2025-11-11T19:43:07.878534

## Summary
- Total detections: 2039
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

## Class Mapping (Simplified)
- doe (3): Female deer
- fawn (4): Young deer (unknown sex)
- buck (5): Male deer (all ages - young/mid/mature combined)
- cattle (0): Cattle
- pig (1): Pig/feral hog
- raccoon (2): Raccoon

## Notes
- All buck age classes (young, mid, mature) are now combined into single 'buck' class
- Review the corrected_detections.csv file for detailed analysis of your corrections.
