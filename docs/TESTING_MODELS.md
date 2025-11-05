# Testing ML Models

This document describes how to test the ML models for the Thumper Counter system.

## Test Script: scripts/test_detection.py

**Purpose:** Verify YOLOv8 detection model loads correctly and produces expected results.

**Features:**
- Load model from src/models/yolov8n_deer.pt
- Run detection on sample images
- Display detected classes, confidence scores, and bounding boxes
- Show overall statistics across multiple images
- Support for single image or batch testing

## Running Tests

### Option 1: Inside Docker Container (Recommended)

The ML packages (torch, ultralytics, opencv-python) should be installed in the Docker worker container.

```bash
# Start the worker container
docker-compose up -d worker

# Run test script inside container
docker-compose exec worker python3 scripts/test_detection.py --num-samples 5

# Test specific image
docker-compose exec worker python3 scripts/test_detection.py \
    --image /mnt/i/Hopkins_Ranch_Trail_Cam_Pics/Sanctuary/SANCTUARY_00001.jpg

# Change confidence threshold
docker-compose exec worker python3 scripts/test_detection.py --conf 0.3 --num-samples 10
```

### Option 2: Local Environment (If dependencies installed)

If you have installed the ML dependencies locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run test
python3 scripts/test_detection.py --num-samples 5
```

## Test Script Usage

```
usage: test_detection.py [-h] [--image IMAGE] [--sample-dir SAMPLE_DIR]
                         [--num-samples NUM_SAMPLES] [--conf CONF]
                         [--model MODEL]

Test YOLOv8 deer detection model

optional arguments:
  -h, --help            show this help message and exit
  --image IMAGE         Path to single image to test
  --sample-dir SAMPLE_DIR
                        Directory to sample images from (default: Sanctuary)
  --num-samples NUM_SAMPLES
                        Number of random samples to test (default: 3)
  --conf CONF           Confidence threshold (default: 0.5)
  --model MODEL         Path to model file (default: src/models/yolov8n_deer.pt)
```

## Expected Output

```
======================================================================
YOLOv8 Deer Detection Test
======================================================================

[INFO] Loading model from: src/models/yolov8n_deer.pt
[OK] Model loaded successfully
[INFO] Model classes (11): ['UTV', 'cow', 'coyote', 'doe', 'fawn', 'mature', 'mid', 'person', 'raccoon', 'turkey', 'young']

[INFO] Found 11658 images in /mnt/i/Hopkins_Ranch_Trail_Cam_Pics/Sanctuary
[INFO] Selected 5 random samples

----------------------------------------------------------------------
Image: SANCTUARY_00123.jpg
----------------------------------------------------------------------
[OK] Found 2 detections

  Detection #1:
    Class:      doe
    Confidence: 0.856
    BBox:       [245.3, 187.2, 512.7, 445.8]
    Size:       267.4 x 258.6 pixels

  Detection #2:
    Class:      fawn
    Confidence: 0.723
    BBox:       [567.1, 234.5, 689.3, 421.2]
    Size:       122.2 x 186.7 pixels

  Summary:
    doe: 1
    fawn: 1

----------------------------------------------------------------------
Image: SANCTUARY_00456.jpg
----------------------------------------------------------------------
[OK] Found 1 detections

  Detection #1:
    Class:      mature
    Confidence: 0.912
    BBox:       [123.4, 156.7, 456.8, 489.2]
    Size:       333.4 x 332.5 pixels

  Summary:
    mature: 1

======================================================================
Overall Summary
======================================================================

Images processed:        5
Images with detections:  3
Total detections:        8

Detections by class:
  doe             3
  fawn            2
  mature          2
  mid             1

Detection rate: 60.0%
Avg detections per image (when detected): 2.7

======================================================================
Class Mapping Information
======================================================================

YOLOv8 model has 11 classes that can be mapped to simplified categories:

  Deer (5 classes):
    doe       -> doe
    fawn      -> fawn
    mature    -> buck (mature)
    mid       -> buck (mid-age)
    young     -> buck (young)

  Other (6 classes):
    coyote, cow, raccoon, turkey, person, UTV

[OK] Detection test completed
```

## Troubleshooting

### Model Not Found

```
[FAIL] Model file not found: src/models/yolov8n_deer.pt
[INFO] Run: ./scripts/copy_models.sh
```

**Solution:** Run the model copy script:
```bash
./scripts/copy_models.sh
```

### ultralytics Not Installed

```
[FAIL] ultralytics package not installed
[INFO] Install with: pip install ultralytics
```

**Solution:** Install dependencies or run inside Docker container:
```bash
# Option A: Install locally
pip install ultralytics torch torchvision opencv-python

# Option B: Use Docker (recommended)
docker-compose exec worker python3 scripts/test_detection.py
```

### No Images Found

```
[FAIL] No images found in: /mnt/i/Hopkins_Ranch_Trail_Cam_Pics/Sanctuary/
```

**Solution:** Check that the image directory is mounted correctly:
```bash
ls /mnt/i/Hopkins_Ranch_Trail_Cam_Pics/Sanctuary/

# Update --sample-dir argument to correct path
python3 scripts/test_detection.py --sample-dir /path/to/images/
```

### Low Detection Rate

If you're getting very few detections, try:

1. **Lower confidence threshold:**
   ```bash
   python3 scripts/test_detection.py --conf 0.3
   ```

2. **Check image quality:**
   - Are images well-lit?
   - Are deer clearly visible?
   - Is camera angle appropriate?

3. **Verify model accuracy:**
   - Original model trained on specific dataset
   - May need fine-tuning for your camera setup

## Testing Other Locations

The Hopkins Ranch has 7 camera locations:

```bash
# Test Sanctuary
python3 scripts/test_detection.py \
    --sample-dir /mnt/i/Hopkins_Ranch_Trail_Cam_Pics/Sanctuary/ \
    --num-samples 10

# Test other locations (update path as needed)
# - Corn Feeder
# - Protein Feeder
# - Salt Lick
# - Water Hole
# - Trail Camera 1
# - Trail Camera 2
```

## Performance Testing

To test processing speed:

```bash
# Time detection on batch
time docker-compose exec worker python3 scripts/test_detection.py --num-samples 50

# Expected performance on RTX 4080 Super:
# - ~50-100 images per minute
# - ~2-3 seconds per image including I/O
```

## Next Steps

After verifying detection works:

1. **Test classification accuracy:** Manually verify class predictions
2. **Evaluate confidence thresholds:** Find optimal threshold for your data
3. **Test re-identification:** Build feature extraction pipeline
4. **Integration testing:** Test full pipeline with Celery tasks

## Related Documentation

- `src/models/README.md` - Model details and training requirements
- `docs/MODEL_INVENTORY.md` - Model status and architecture
- `specs/ml.spec` - ML pipeline specifications
- `src/worker/tasks/process_images.py` - Production ML pipeline code
