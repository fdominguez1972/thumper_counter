# Antler Detection Annotation Schema

**Feature:** Phase 2B - Antler/Marking Detection for Enhanced Re-ID
**Created:** November 16, 2025
**Purpose:** Enable near-100% buck identification accuracy through physical feature detection

---

## ANNOTATION SCHEMA

### Primary Features

#### 1. Antler Points (Bucks Only)
**Detection Type:** Keypoint Detection (YOLOv8-pose)

**Left Antler Points:**
- `left_main_beam` - Base attachment point
- `left_brow_tine` - First point (G1)
- `left_g2` - Second point
- `left_g3` - Third point
- `left_g4` - Fourth point (if present)
- `left_g5+` - Additional points (if present)

**Right Antler Points:**
- `right_main_beam` - Base attachment point
- `right_brow_tine` - First point (G1)
- `right_g2` - Second point
- `right_g3` - Third point
- `right_g4` - Fourth point (if present)
- `right_g5+` - Additional points (if present)

**Metadata:**
- Total point count (e.g., "8-point", "10-point")
- Symmetry: symmetric/asymmetric
- Configuration: typical/non-typical
- Visibility: full/partial/obscured

---

#### 2. Body Markings (All Deer)
**Detection Type:** Object Detection + Segmentation

**Mark Types:**
- `scar` - Healed wounds, visible scars
- `injury` - Fresh wounds, injuries
- `white_patch` - Distinctive white fur patterns
- `dark_patch` - Distinctive dark fur patterns
- `ear_notch` - Ear tears/notches
- `ear_tag` - Artificial tags (if present)

**Attributes:**
- Location: head/neck/shoulder/body/leg
- Size: small/medium/large
- Permanence: temporary/permanent

---

#### 3. Unique Features (Optional)
**Detection Type:** Classification

- `antler_shape` - Drop tine, split G2, palmation, etc.
- `body_build` - Thin/average/muscular/heavy
- `coat_condition` - Poor/average/good/excellent
- `tail_pattern` - White tail pattern variations

---

## ANNOTATION FORMAT

### YOLOv8-Pose Format (for antler points)
```
class_id x_center y_center width height [keypoint1_x keypoint1_y visibility1] [keypoint2_x keypoint2_y visibility2] ...
```

**Example - 8-point buck:**
```
0 0.5 0.4 0.3 0.4 0.45 0.25 2 0.47 0.22 2 0.48 0.20 2 0.50 0.18 2 0.55 0.25 2 0.57 0.22 2 0.58 0.20 2 0.60 0.18 2
```

**Visibility Flags:**
- 0 = Not visible
- 1 = Occluded
- 2 = Visible

### Object Detection Format (for markings)
```
class_id x_center y_center width height
```

**Example - Scar on left shoulder:**
```
1 0.35 0.55 0.08 0.06
```

---

## ANNOTATION CLASSES

### Class IDs
```yaml
0: buck_with_antlers
1: scar
2: injury
3: white_patch
4: dark_patch
5: ear_notch
6: ear_tag
```

---

## ANNOTATION WORKFLOW

### Phase 1: Sample Dataset (100 images)
**Goal:** Test annotation schema, train initial model

**Image Selection Criteria:**
- 50 bucks with clearly visible antlers
- 25 does with distinctive markings
- 25 mixed (fawns, partial occlusion, challenging cases)

**Annotation Process:**
1. Load image in annotation tool (Label Studio / CVAT / Roboflow)
2. Identify buck/doe/fawn
3. If buck: Mark all visible antler points
4. For all deer: Mark any distinctive body markings
5. Add metadata (point count, symmetry, visibility)
6. Quality check: Verify keypoint accuracy

**Tools:**
- **Recommended:** Label Studio (supports keypoints + bbox)
- **Alternative:** CVAT, Roboflow

---

### Phase 2: Expanded Dataset (500-1000 images)
**Goal:** Production-quality model

**Image Selection:**
- Stratified sampling across locations
- Temporal diversity (different seasons, times)
- Various angles and lighting conditions
- Representation of all buck point counts (4-point through 12-point+)
- Does and fawns with unique markings

**Quality Assurance:**
- Double annotation for 10% of images
- Inter-annotator agreement >90%
- Expert review of difficult cases

---

## TRAINING DATASET STRUCTURE

```
antler_detection_dataset/
├── data.yaml
├── images/
│   ├── train/
│   │   ├── BUCK_0001.jpg
│   │   ├── BUCK_0002.jpg
│   │   └── ...
│   └── val/
│       ├── BUCK_0101.jpg
│       └── ...
└── labels/
    ├── train/
    │   ├── BUCK_0001.txt
    │   ├── BUCK_0002.txt
    │   └── ...
    └── val/
        ├── BUCK_0101.txt
        └── ...
```

**data.yaml:**
```yaml
path: /app/src/models/training_data/antler_detection
train: images/train
val: images/val

# Keypoint detection
kpt_shape: [16, 3]  # 16 keypoints, each with (x, y, visibility)

# Classes
names:
  0: buck
  1: scar
  2: injury
  3: white_patch
  4: dark_patch
  5: ear_notch
  6: ear_tag

# Keypoint names
keypoint_names:
  - left_main_beam
  - left_brow_tine
  - left_g2
  - left_g3
  - left_g4
  - left_g5
  - left_g6
  - left_g7
  - right_main_beam
  - right_brow_tine
  - right_g2
  - right_g3
  - right_g4
  - right_g5
  - right_g6
  - right_g7
```

---

## INTEGRATION WITH RE-ID

### Hard Constraints
```python
def can_match(detection_antlers, deer_profile_antlers):
    """
    Check if antler configuration allows match.

    Returns: True if possible match, False if impossible
    """
    # Extract point counts
    det_left_points = count_points(detection_antlers['left'])
    det_right_points = count_points(detection_antlers['right'])
    prof_left_points = count_points(deer_profile_antlers['left'])
    prof_right_points = count_points(deer_profile_antlers['right'])

    # Hard constraint: Point counts must match (within 1 for growth/shedding)
    if abs(det_left_points - prof_left_points) > 1:
        return False
    if abs(det_right_points - prof_right_points) > 1:
        return False

    # Check antler shape features (if detected)
    if detection_antlers.get('drop_tine') != deer_profile_antlers.get('drop_tine'):
        return False

    return True
```

### Re-ID Workflow with Antler Features
```python
# 1. Run detection + antler detection
detections = yolo_detect(image)
antler_features = yolo_antler_detect(image, detections)

# 2. For each buck detection
for detection in bucks:
    antlers = antler_features[detection.id]

    # 3. Filter candidate deer by antler constraints
    candidates = get_deer_by_sex('buck')
    compatible = [d for d in candidates if can_match(antlers, d.antler_profile)]

    # 4. Run normal Re-ID only on compatible deer
    if len(compatible) > 0:
        match = find_best_reid_match(detection, compatible)
    else:
        match = None  # Create new deer profile
```

---

## EXPECTED BENEFITS

### Buck Identification
- **Before:** 58.25% assignment rate, ~40% buck accuracy
- **After:** 90-95% buck assignment rate with antlers visible
- **Impact:** Near-zero false positives for mismatched point counts

### Metadata Value
- Track antler growth over season
- Identify trophy bucks automatically
- Population analysis by age class (points correlate with age)
- Injury/health monitoring

### User Workflow
- Frontend displays detected antler points
- Manual corrections for missed/incorrect points
- Visual confirmation of Re-ID matches

---

## NEXT STEPS

1. **Select 100 sample images** - Diverse bucks with visible antlers
2. **Set up Label Studio** - Annotation tool with keypoint support
3. **Create annotation guidelines** - Training for consistent annotations
4. **Annotate sample dataset** - 100 images with antler points + markings
5. **Train initial YOLOv8-pose model** - Validate schema effectiveness
6. **Evaluate model performance** - Adjust schema if needed
7. **Expand to 500-1000 images** - Full production dataset
8. **Train production model** - Deploy to Re-ID pipeline

---

**Document Version:** 1.0
**Last Updated:** November 16, 2025
**Status:** Schema defined, ready for annotation
