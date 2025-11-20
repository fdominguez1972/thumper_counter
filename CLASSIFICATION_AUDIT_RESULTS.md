# Classification Audit Results - Low Confidence Detections

**Audit Date:** November 16, 2025
**Auditor:** Claude AI Vision Analysis
**Sample Size:** 10 images (lowest confidence detections: 50.00% - 50.08%)
**Audit Method:** Manual visual inspection of each image

---

## Executive Summary

**Overall Accuracy:** 70% (7 correct out of 10)
**Misclassifications Found:** 3 images
**False Positives:** 1 image (no deer present)
**Species Confusion:** 1 image (cattle misidentified as deer)
**Buck/Doe Confusion:** 1 image

### Key Findings:
1. Very low confidence detections (50-50.1%) are often correct but uncertain due to:
   - Distance (deer too far from camera)
   - Poor lighting (night vision, IR images)
   - Image quality (grainy, low resolution)

2. Critical errors identified:
   - **Cattle misidentified as doe** (1 case)
   - **False positive detection** (1 case - no animal present)
   - **Buck misidentified as doe** (1 case - actually does)

3. Recommendation: All detections with confidence < 60% should be manually reviewed

---

## Detailed Review Results

### Image 1: SANCTUARY_10845.jpg ✓ CORRECT
- **Database Classification:** doe (50.00% confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Deer visible but very far from camera. Doe classification is correct but low confidence due to distance.
- **Detection ID:** `76a4f53b-4228-4ec0-92b0-ff68f967884c`
- **Image ID:** `01d8b58d-90c1-4643-8265-afca3f29f7df`
- **Action:** None required

---

### Image 2: Sanctuary2_20251102_172420_001.jpg ✓ CORRECT
- **Database Classification:** buck (50.01% confidence)
- **Audit Classification:** buck
- **Status:** CORRECT
- **Notes:** Multiple deer near feeder. Left deer has visible antlers. Classification is correct.
- **Detection ID:** `dadadd8b-d07e-4001-a523-b869d88e29a8`
- **Image ID:** `bc37b381-2219-4e2b-928b-811610bb49dc`
- **Action:** None required

---

### Image 3: HAYFIELD_03223.jpg ✓ CORRECT
- **Database Classification:** doe (50.01% confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night vision/IR image. Deer on right side. No visible antlers. Low confidence due to image quality.
- **Detection ID:** `b873d31e-9734-414f-ab61-472d45b72e7b`
- **Image ID:** `5f576b34-7b52-420e-bcbb-a653310a65b4`
- **Action:** None required

---

### Image 4: CAMPHOUSE_02025.jpg ✗ INCORRECT - CATTLE
- **Database Classification:** doe (50.02% confidence)
- **Audit Classification:** CATTLE (not deer)
- **Status:** INCORRECT - Species misidentification
- **Notes:** 2-3 cattle (cows) grazing in field. This is NOT a deer at all! Critical error.
- **Detection ID:** `cdd57436-24e3-4ed6-a61e-428db996d7ac`
- **Image ID:** `10f32ffa-5fb7-48c8-9e8e-7f521d5bc3ed`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/cdd57436-24e3-4ed6-a61e-428db996d7ac/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "cattle"}'
  ```

---

### Image 5: Sanctuary2_20251106_091323_001.jpg ✓ CORRECT
- **Database Classification:** buck (50.02% confidence)
- **Audit Classification:** buck
- **Status:** CORRECT
- **Notes:** Clear daylight image. Deer near feeder with visible antlers. Classification is correct.
- **Detection ID:** `9247bdc3-9036-4743-a10b-04abc38eff34`
- **Image ID:** `ec11d542-33f3-4de8-80e8-a0c17007f9a4`
- **Action:** None required

---

### Image 6: SANCTUARY_01826.jpg ✓ CORRECT
- **Database Classification:** doe (50.03% confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night vision. Two deer near feeder. Both appear to be does (no antlers visible).
- **Detection ID:** `b5d723fc-11d2-41f2-a4c8-66833fdaf1e1`
- **Image ID:** `e91cd425-a93e-4f84-a6d0-1803be1d8f33`
- **Action:** None required

---

### Image 7: Sanctuary2_20251103_090210_001.jpg ✓ CORRECT
- **Database Classification:** buck (50.05% confidence)
- **Audit Classification:** buck
- **Status:** CORRECT
- **Notes:** Clear daylight image. Deer with visible antlers. Buck classification is correct.
- **Detection ID:** `269713b5-0b9b-4b27-a4f2-c031504c2fca`
- **Image ID:** `fda1c0c9-60f2-423d-9c16-7a324ce53f75`
- **Action:** None required

---

### Image 8: SANCTUARY_01496.jpg ✗ INCORRECT - FALSE POSITIVE
- **Database Classification:** doe (50.06% confidence)
- **Audit Classification:** NO DEER PRESENT
- **Status:** INCORRECT - False positive detection
- **Notes:** Empty field with feeder. No deer visible in image. Detection should be marked as invalid.
- **Detection ID:** `53c3cf10-2d7b-4791-a80a-00cf8594642e`
- **Image ID:** `f04508a7-513c-4d86-8c5f-32dac607d9aa`
- **Action Required:**
  ```bash
  # Mark detection as invalid
  curl -X PATCH "http://localhost:8001/api/detections/53c3cf10-2d7b-4791-a80a-00cf8594642e/correct" \
    -H "Content-Type: application/json" \
    -d '{"is_valid": false}'
  ```

---

### Image 9: HAYFIELD_10187.jpg ✓ CORRECT
- **Database Classification:** buck (50.06% confidence)
- **Audit Classification:** buck
- **Status:** CORRECT
- **Notes:** Black and white image. Two deer near feeder. Foreground deer has visible antlers.
- **Detection ID:** `abe52d0b-8fac-46da-9a83-7852b7e83f57`
- **Image ID:** `ee9ddd32-9bdd-4caa-8bc8-73c955cfc937`
- **Action:** None required

---

### Image 10: CAMPHOUSE_01253.jpg ✗ INCORRECT - SHOULD BE DOE
- **Database Classification:** buck (50.08% confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT - Buck/doe misclassification
- **Notes:** Night vision. Three deer near feeder. None have visible antlers - all appear to be does.
- **Detection ID:** `b429d667-47b2-4903-bfa1-4673b34bd97d`
- **Image ID:** `6be9b8fc-a05a-40b2-9f31-cb9ad24eb1dc`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/b429d667-47b2-4903-bfa1-4673b34bd97d/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe"}'
  ```

---

## Batch Correction Commands

### Apply All Corrections at Once:
```bash
curl -X PATCH "http://localhost:8001/api/detections/batch/correct" \
  -H "Content-Type: application/json" \
  -d '{
    "corrections": [
      {
        "detection_id": "cdd57436-24e3-4ed6-a61e-428db996d7ac",
        "corrected_classification": "cattle"
      },
      {
        "detection_id": "b429d667-47b2-4903-bfa1-4673b34bd97d",
        "corrected_classification": "doe"
      }
    ]
  }'
```

### Mark False Positive as Invalid:
```bash
curl -X PATCH "http://localhost:8001/api/detections/53c3cf10-2d7b-4791-a80a-00cf8594642e/correct" \
  -H "Content-Type: application/json" \
  -d '{"is_valid": false}'
```

---

## Statistics

### Accuracy Breakdown:
- **Total Reviewed:** 10 images
- **Correct Classifications:** 7 (70%)
- **Incorrect Classifications:** 3 (30%)

### Error Types:
- **Species Confusion (Cattle vs Deer):** 1 (10%)
- **False Positive (No Animal):** 1 (10%)
- **Buck/Doe Confusion:** 1 (10%)

### Confidence Range Impact:
- Detections with 50.00-50.10% confidence have 30% error rate
- Recommend manual review for ALL detections < 60% confidence

---

## Recommendations

### Immediate Actions:
1. Apply the batch correction commands above to fix the 3 identified errors
2. Review remaining 40+ images with confidence < 65%
3. Consider retraining model with corrected images

### Long-term Improvements:
1. **Improve cattle/deer distinction** - Add more cattle training data
2. **Reduce false positives** - Adjust detection confidence threshold
3. **Better night vision classification** - Train specifically on IR images
4. **Manual review workflow** - Flag all detections < 60% for human review

### Model Retraining:
- Export corrected detections as new training data
- Include cattle examples to prevent species confusion
- Add negative examples (empty scenes) to reduce false positives
- Retrain YOLOv8 model with augmented dataset

---

## Next Steps

1. **Apply corrections** using batch command above
2. **Continue review** of remaining 40 low-confidence images
3. **Monitor correction rate** - track how many corrections are needed
4. **Plan model retraining** once sufficient corrections accumulated

---

**Audit Completed:** 2025-11-16
**Files Reviewed:** /tmp/low_confidence_detections.csv
**Images Downloaded:** I:/projects/thumper_counter/review_*.jpg
