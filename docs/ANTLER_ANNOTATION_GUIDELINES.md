# Antler Detection Annotation Guidelines

**Feature:** Phase 2B - Antler/Marking Detection for Enhanced Re-ID
**Tool:** Label Studio
**Format:** YOLOv8-pose (16 keypoints + bounding boxes)
**Last Updated:** November 16, 2025

---

## OVERVIEW

This guide provides step-by-step instructions for annotating deer images with antler keypoints and body markings. Consistent annotations are CRITICAL for training an accurate detection model.

**Annotation Goals:**
- Enable near-100% buck identification accuracy
- Track antler growth and configuration over time
- Identify unique body markings for Re-ID
- Prevent false matches (e.g., 8-point matched to 10-point)

---

## QUICK START

1. Access Label Studio: http://localhost:8080
2. Create account (first time only)
3. Create new project: "Antler Detection - Phase 2B"
4. Import configuration from: `docs/LABEL_STUDIO_ANTLER_CONFIG.xml`
5. Import images from: `src/models/training_data/antler_annotation_samples/`
6. Begin annotation following guidelines below

---

## ANNOTATION WORKFLOW

### Step 1: Identify Deer Classification

**For each deer in the image:**
1. Draw bounding box around entire deer body
2. Select classification:
   - **buck**: Male deer with visible or partial antlers
   - **doe**: Female deer (no antlers)
   - **fawn**: Young deer (small size, no antlers)

**Quality Check:**
- Bounding box includes entire body (head to tail, hooves to back)
- Box is tight (minimal empty space)
- Multiple deer? Create separate boxes for each

---

### Step 2: Annotate Antler Points (Bucks Only)

**IMPORTANT: Only annotate bucks with visible antlers**

#### Keypoint Order (16 total):
```
Left Antler (8 points):
1. left_main_beam - Base where antler attaches to skull
2. left_brow_tine - First point (G1)
3. left_g2 - Second point
4. left_g3 - Third point
5. left_g4 - Fourth point (if present)
6. left_g5 - Fifth point (if present)
7. left_g6 - Sixth point (if present)
8. left_g7 - Seventh point (if present)

Right Antler (8 points):
9. right_main_beam - Base where antler attaches to skull
10. right_brow_tine - First point (G1)
11. right_g2 - Second point
12. right_g3 - Third point
13. right_g4 - Fourth point (if present)
14. right_g5 - Fifth point (if present)
15. right_g6 - Sixth point (if present)
16. right_g7 - Seventh point (if present)
```

#### Annotation Rules:

**1. Start with Main Beam:**
- Click at the base where antler attaches to skull
- This is ALWAYS the first point on each side
- Even if partially obscured, estimate the attachment point

**2. Mark Each Tine:**
- Click at the TIP of each tine (point)
- Start from brow tine (closest to skull), work outward
- Skip points that don't exist (e.g., 6-point buck has no g4-g7)

**3. Handle Occlusion:**
- **Fully Visible**: Mark exact tip location
- **Partially Visible**: Estimate tip location based on visible portion
- **Not Visible**: Do NOT mark the point (skip it)

**4. Non-Typical Antlers:**
- **Drop Tine**: Mark as an extra point (g4, g5, etc.)
- **Split Points**: Mark the most prominent tip
- **Palmation**: Mark the highest visible points
- **Check "non_typical" in metadata**

**5. Asymmetric Antlers:**
- Buck has different point counts on left/right
- Annotate all visible points on both sides
- Check "asymmetric" in metadata
- Example: 4 points left, 5 points right = 9-point buck

---

### Step 3: Annotate Body Markings

**For ALL deer (bucks, does, fawns):**

Draw bounding boxes around any distinctive markings:

**1. Scars:**
- Healed wounds, visible scars
- Hairless patches from old injuries
- Distinctive pattern that persists over time

**2. Injuries:**
- Fresh wounds, visible blood
- Recent damage (antler breaks, cuts)
- Temporary features (may heal)

**3. White Patches:**
- Distinctive white fur patterns
- NOT normal white on chest/belly
- Unusual white markings on face, legs, body

**4. Dark Patches:**
- Distinctive dark fur patterns
- Unusually dark areas
- Birth marks, pigmentation differences

**5. Ear Notches:**
- Torn ears, missing pieces
- Distinctive notch patterns
- Natural or injury-caused

**6. Ear Tags:**
- Artificial tags (rare in wild deer)
- Collar, tracking devices
- Human-applied markers

**Quality Check:**
- Only mark DISTINCTIVE features (not normal patterns)
- Box tightly around the marking
- Consider: "Would this help identify this specific deer?"

---

### Step 4: Fill Metadata Fields

**Point Count:** (Bucks only)
- Count TOTAL points on both antlers
- 4-point: 2 per side (main beam + brow tine)
- 8-point: 4 per side (typical)
- 10-point: 5 per side (typical mature buck)
- Select "not_applicable_doe" for does/fawns

**Symmetry:**
- **symmetric**: Same point count and similar shape on both sides
- **asymmetric**: Different point counts or very different shapes
- **not_applicable**: Does, fawns, or antlers not visible

**Visibility:**
- **full_visibility**: Both antlers fully visible
- **partial_left**: Left antler partially obscured
- **partial_right**: Right antler partially obscured
- **both_partial**: Both antlers partially obscured
- **obscured**: Antlers barely visible or not visible

**Antler Configuration:**
(Select all that apply)
- **typical**: Normal antler configuration
- **drop_tine**: Has a drop tine (points down from main beam)
- **split_g2**: G2 splits into multiple points
- **palmation**: Flattened, moose-like antler sections
- **non_typical**: Unusual configuration

**Notes:**
(Optional but helpful)
- Unusual features
- Annotation challenges
- Uncertainty about keypoints
- Image quality issues

---

## QUALITY STANDARDS

### High-Quality Annotations:

**Bounding Boxes:**
- [OK] Tight around deer body, no excessive empty space
- [OK] Includes entire animal (head to tail)
- [OK] Separate boxes for each deer in multi-deer images

**Keypoints:**
- [OK] Placed at exact tip of each tine
- [OK] All visible points marked in correct order
- [OK] Missing points skipped (not randomly placed)
- [OK] Main beams marked at skull attachment

**Markings:**
- [OK] Only distinctive, identifying features marked
- [OK] Tight boxes around each marking
- [OK] All significant markings included

**Metadata:**
- [OK] Point count matches annotated keypoints
- [OK] Symmetry accurately reflects antler configuration
- [OK] Visibility reflects actual occlusion level

### Common Mistakes to Avoid:

- [FAIL] Marking non-existent points (e.g., g7 on 6-point buck)
- [FAIL] Wrong keypoint order (g3 before g2)
- [FAIL] Bounding box cuts off part of deer
- [FAIL] Marking normal chest white as "white_patch"
- [FAIL] Guessing keypoint location when completely obscured
- [FAIL] Missing distinctive markings (scars, notches)
- [FAIL] Point count doesn't match keypoints

---

## ANNOTATION TIPS

### Buck Point Counting:
```
4-point: Main beam + brow tine (2x2)
6-point: Main beam + brow + G2 (3x3)
8-point: Main beam + brow + G2 + G3 (4x4) [TYPICAL]
10-point: Main beam + brow + G2 + G3 + G4 (5x5) [MATURE]
12-point: Main beam + brow + G2 + G3 + G4 + G5 (6x6)
```

**Remember:** Total count = left + right
- 8-point = 4 points per side
- Asymmetric: 4 left + 5 right = 9-point

### Handling Difficult Cases:

**Low Resolution:**
- Estimate keypoint locations based on visible antler structure
- Mark "partial_visibility" or "obscured" in metadata
- Add note about image quality

**Multiple Deer:**
- Annotate each deer separately
- Start with clearest/largest deer first
- Check that bounding boxes don't overlap significantly

**Side Views:**
- Only one antler visible? Annotate visible side fully
- Mark invisible side's keypoints as "not visible" (skip)
- Note "partial_left" or "partial_right" visibility

**Head-On Views:**
- Both antlers visible but may overlap
- Carefully distinguish left vs right points
- May need to zoom in for accuracy

**Blurry/Motion:**
- Do your best with visible information
- Don't guess completely obscured features
- Add note about motion blur or focus issues

---

## EXPORT FORMAT

After annotation, Label Studio will export in JSON format. We'll convert to YOLOv8-pose format:

```
class_id x_center y_center width height [kp1_x kp1_y vis1] [kp2_x kp2_y vis2] ...

Example (8-point buck):
0 0.5 0.4 0.3 0.4 0.45 0.25 2 0.47 0.22 2 0.48 0.20 2 0.50 0.18 2 0.55 0.25 2 0.57 0.22 2 0.58 0.20 2 0.60 0.18 2

Where:
- class_id: 0=buck, 1=doe, 2=fawn
- x_center, y_center, width, height: Normalized bbox coords [0-1]
- kp_x, kp_y: Normalized keypoint coords [0-1]
- vis: 0=not visible, 1=occluded, 2=visible
```

Conversion script will be provided: `scripts/convert_labelstudio_to_yolo.py`

---

## PROGRESS TRACKING

**Target:** 73 images for Phase 2B initial model

**Categories:**
- Bucks: 50 images (focus on antler keypoints)
- Does: 12 images (focus on body markings)
- Mixed: 11 images (challenging cases)

**Time Estimate:**
- Simple buck (clear antlers): 2-3 minutes
- Complex buck (partial occlusion): 5-7 minutes
- Does/markings only: 1-2 minutes
- Average: 3-4 minutes per image
- Total: 3-5 hours for 73 images

**Milestones:**
- [ ] 25 images annotated
- [ ] 50 images annotated
- [ ] 73 images complete
- [ ] Quality review (10% random sample)
- [ ] Export and convert to YOLO format

---

## QUESTIONS & TROUBLESHOOTING

**Q: What if I can't tell if a point is a tine or part of the main beam?**
A: If it clearly protrudes 1+ inches, mark it as a tine. When uncertain, add a note.

**Q: Should I mark broken antlers?**
A: Yes, mark all visible points including broken stubs. Note "injury" if fresh break.

**Q: What about velvet antlers (fuzzy, growing)?**
A: Annotate normally. Velvet doesn't affect point structure.

**Q: Buck has small "bump" that might be a point?**
A: If it's less than 1 inch, don't count it. Mark next clear tine as next G-number.

**Q: Image has both buck and doe, but bbox overlaps?**
A: Separate boxes if possible. If inseparable, annotate the clearer/larger deer.

**Q: Keypoint placement - exact tip or base of tine?**
A: ALWAYS the TIP (end point) of each tine, not the base.

---

## GETTING HELP

**Technical Issues:**
- Label Studio not loading: Check `docker-compose logs labelstudio`
- Can't import images: Verify path `/label-studio/data/antler_samples`
- Lost annotations: Label Studio auto-saves, check project tasks

**Annotation Questions:**
- Refer to this guide first
- Check examples in `docs/ANTLER_DETECTION_ANNOTATION_SCHEMA.md`
- Add detailed notes for review

**Configuration:**
- Label Studio: http://localhost:8080
- Config file: `docs/LABEL_STUDIO_ANTLER_CONFIG.xml`
- Sample images: `src/models/training_data/antler_annotation_samples/`

---

## NEXT STEPS AFTER ANNOTATION

1. **Export annotations** from Label Studio (JSON format)
2. **Convert to YOLO format** using conversion script
3. **Quality check** annotations (10% random sample)
4. **Train initial model** (YOLOv8-pose)
5. **Evaluate accuracy** on validation set
6. **Expand dataset** to 500-1000 images if successful
7. **Integrate** into Re-ID pipeline

---

**Document Version:** 1.0
**Last Updated:** November 16, 2025
**Status:** Ready for annotation
