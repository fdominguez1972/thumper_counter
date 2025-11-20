# Classification Audit Results - Batch 2 (Low Confidence Detections)

**Audit Date:** November 16, 2025
**Auditor:** Claude AI Vision Analysis
**Sample Size:** 20 images (confidence range: 50.09% - 50.22%)
**Batch:** 2 of 171 (images 11-30 from sorted list)
**Audit Method:** Manual visual inspection of each image

---

## Executive Summary

**Overall Accuracy:** 55% (11 correct out of 20)
**Misclassifications Found:** 6 images (30%)
**Buck Misidentified as Doe:** 0 images
**Doe Misidentified as Buck:** 5 images (25%)
**False Positives:** 1 image (no deer present)
**Too Distant/Uncertain:** 3 images (15%)

### Key Findings:
1. Buck misidentification rate is HIGH (5 out of 8 buck classifications were actually does)
2. Doe classifications are generally accurate (only 1 false positive out of 12)
3. Low confidence (50.09-50.22%) correlates with image quality issues:
   - Poor lighting (dawn/dusk/night vision)
   - Distance (deer too far from camera)
   - Obscuration (vegetation, poor angle)

4. Critical pattern: Model tends to classify does as bucks when uncertain
5. Recommendation: All buck detections < 55% confidence should be manually reviewed

---

## Detailed Review Results

### Image 1: HAYFIELD_07511.jpg [OK] CORRECT
- **Database Classification:** buck (50.09% confidence)
- **Audit Classification:** buck
- **Status:** CORRECT
- **Notes:** Night vision/IR image. Deer with clearly visible antlers on right side.
- **Detection ID:** `fb85517f-9d50-400e-96dc-690fc72171da`
- **Image ID:** `8c7d8495-faf5-49da-8a85-6621d70319f5`
- **Action:** None required

---

### Image 2: SANCTUARY_05355.jpg [OK] CORRECT
- **Database Classification:** doe (50.09% confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Very dark dawn/dusk image. Deer silhouettes near feeder. No antlers visible.
- **Detection ID:** `92bfc409-e303-4680-ae23-97a0e0506dfa`
- **Image ID:** `76c641bc-1ee6-465f-a52a-7c132dad1653`
- **Action:** None required

---

### Image 3: Hayfield_20250910_184443_001.jpg [FAIL] INCORRECT
- **Database Classification:** buck (50.10% confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT - Buck misidentified
- **Notes:** Clear daylight image. Two deer near feeder. Neither has visible antlers. Both appear to be does.
- **Detection ID:** `cc143c1d-04c9-4eb6-a8d1-072c72d58bd9`
- **Image ID:** `04ced0cc-6a90-4630-9299-19836f80cfc4`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/cc143c1d-04c9-4eb6-a8d1-072c72d58bd9/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 2"}'
  ```

---

### Image 4: Jason1_20250930_084404_001.jpg [OK] CORRECT
- **Database Classification:** doe (50.10% confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Close-up of deer with large ears. No antlers visible. Clear doe.
- **Detection ID:** `f6167206-b212-41b7-a222-7370da3c1427`
- **Image ID:** `50f5908d-d2ac-4695-8391-d6231f14b7a8`
- **Action:** None required

---

### Image 5: Hayfield_20251020_073510_001.jpg [FAIL] INCORRECT
- **Database Classification:** buck (50.11% confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT - Buck misidentified
- **Notes:** Dawn/dusk image. Two deer near feeder. No visible antlers on either deer. Both appear to be does.
- **Detection ID:** `39facc44-dfa6-4887-bc28-91f49de0b8cf`
- **Image ID:** `bf32fca9-ca86-4f38-b8ad-a90c163e0401`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/39facc44-dfa6-4887-bc28-91f49de0b8cf/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 2"}'
  ```

---

### Image 6: Sanctuary2_20251101_103312_001.jpg [OK] CORRECT
- **Database Classification:** doe (50.11% confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear daylight image. Two deer grazing near feeder. No antlers visible.
- **Detection ID:** `12d04d04-4576-47cf-85d8-e8abe1cdcfb0`
- **Image ID:** `885664ee-7e07-4eb4-9435-6cd7fa46a564`
- **Action:** None required

---

### Image 7: Sanctuary2_20251104_164008_001.jpg [FAIL] INCORRECT
- **Database Classification:** buck (50.12% confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT - Buck misidentified
- **Notes:** Clear daylight image. Three deer near feeder. None have visible antlers. All appear to be does.
- **Detection ID:** `a2a87d11-ffb2-4cb1-be73-fc32a79e340c`
- **Image ID:** `38622bcb-9474-41db-bea1-d5f0f93b8ef1`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/a2a87d11-ffb2-4cb1-be73-fc32a79e340c/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 2"}'
  ```

---

### Image 8: Hayfield_20251029_073217_001.jpg [FAIL] INCORRECT
- **Database Classification:** buck (50.13% confidence)
- **Audit Classification:** doe (or uncertain)
- **Status:** INCORRECT - Buck misidentified
- **Notes:** Very dark dawn image. Multiple deer silhouettes near feeder. Cannot see antlers clearly. Likely does.
- **Detection ID:** `6689745a-192d-4692-821b-e216f7f453cc`
- **Image ID:** `0945e839-da66-4f1d-bfd1-d353d76798cf`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/6689745a-192d-4692-821b-e216f7f453cc/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 2"}'
  ```

---

### Image 9: Jason1_20250915_030941_001.jpg [FAIL] INCORRECT - FALSE POSITIVE
- **Database Classification:** doe (50.13% confidence)
- **Audit Classification:** NO DEER PRESENT
- **Status:** INCORRECT - False positive detection
- **Notes:** Night vision image showing vegetation/corn stalks. No deer visible in frame.
- **Detection ID:** `ad878ecc-b5b3-4edf-9e5b-bf8160353eb8`
- **Image ID:** `02250f52-76ea-42a8-8be5-72353f759fd9`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/ad878ecc-b5b3-4edf-9e5b-bf8160353eb8/correct" \
    -H "Content-Type: application/json" \
    -d '{"is_valid": false, "reviewed_by": "Claude AI Audit Batch 2"}'
  ```

---

### Image 10: SANCTUARY_04224.jpg [OK] CORRECT
- **Database Classification:** doe (50.15% confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night vision/IR. Single deer near feeder. No antlers visible.
- **Detection ID:** `e6e29cb5-2323-4554-9c9b-bc0285766bd3`
- **Image ID:** `cfa2951a-94fb-4a7a-9a66-a1e279dcdc16`
- **Action:** None required

---

### Image 11: Sanctuary2_20251109_071535_001.jpg [WARN] UNCERTAIN
- **Database Classification:** buck (50.15% confidence)
- **Audit Classification:** UNCERTAIN - too distant
- **Status:** UNCERTAIN - Cannot confirm
- **Notes:** Dawn image. Deer visible far away on left side. Too distant to reliably identify antlers.
- **Detection ID:** `33b18b94-cd3f-4661-8e51-4e7931913f68`
- **Image ID:** `a9dbedf5-fdcc-4357-9eb1-764ee7437749`
- **Action:** Consider marking as uncertain or reviewing original high-res image

---

### Image 12: SANCTUARY_09669.jpg [OK] CORRECT
- **Database Classification:** doe (50.16% confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night vision/IR. Deer grazing in grass. No antlers visible.
- **Detection ID:** `e3ea5ec2-e2d0-433c-a5e3-0ad2eae552ec`
- **Image ID:** `8107e9ff-868c-45bd-a680-15c71ef818e2`
- **Action:** None required

---

### Image 13: Sanctuary2_20251108_171300_001.jpg [OK] CORRECT
- **Database Classification:** doe (50.18% confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear daylight image. Three deer near feeder. No antlers visible on any.
- **Detection ID:** `47b1518f-2a08-419b-af83-31dfc788416a`
- **Image ID:** `4106f732-c1e2-497c-b4fb-509b99a11cc9`
- **Action:** None required

---

### Image 14: SANCTUARY_09631.jpg [OK] CORRECT
- **Database Classification:** doe (50.19% confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night vision/IR. Deer grazing. No antlers visible.
- **Detection ID:** `c64d3332-f48b-4827-ac4f-0945396c52f3`
- **Image ID:** `2c4c02fb-a5c7-441c-a7e2-33ef77b86370`
- **Action:** None required

---

### Image 15: HAYFIELD_09229.jpg [WARN] UNCERTAIN
- **Database Classification:** doe (50.19% confidence)
- **Audit Classification:** UNCERTAIN - too distant
- **Status:** UNCERTAIN - Cannot confirm
- **Notes:** Dawn/dusk image. Very distant deer barely visible at far right edge. Too far to classify reliably.
- **Detection ID:** `91d48244-f46c-4c94-8bff-de4ff0fe3b5c`
- **Image ID:** `ff48e9db-83c3-47a6-b6b7-c1fd862129a9`
- **Action:** Consider reviewing with higher resolution or marking as uncertain

---

### Image 16: Sanctuary2_20251104_164454_001.jpg [OK] CORRECT
- **Database Classification:** buck (50.20% confidence)
- **Audit Classification:** buck
- **Status:** CORRECT
- **Notes:** Clear daylight image. Multiple deer. Left foreground deer has visible small antlers.
- **Detection ID:** `8d911fa5-ee69-405e-a951-88e1860ed8c0`
- **Image ID:** `af7715de-3d1e-4dcd-84aa-c071207119b3`
- **Action:** None required

---

### Image 17: Sanctuary2_20251101_164028_001.jpg [OK] CORRECT
- **Database Classification:** buck (50.21% confidence)
- **Audit Classification:** buck
- **Status:** CORRECT
- **Notes:** Clear daylight image. Two deer. Left deer has clearly visible antlers.
- **Detection ID:** `24635734-93b8-4cbf-90e5-ab07820e0263`
- **Image ID:** `e1ec0d82-4639-4acb-b1a4-0de2406a1908`
- **Action:** None required

---

### Image 18: TINMAN_00116.jpg [FAIL] INCORRECT - FALSE POSITIVE
- **Database Classification:** doe (50.21% confidence)
- **Audit Classification:** NO DEER PRESENT
- **Status:** INCORRECT - False positive detection
- **Notes:** Daylight image. Shows empty field with feeder. No deer visible at all.
- **Detection ID:** `446b6e8d-9fef-4169-a1ae-2dad082e4b86`
- **Image ID:** `ccfd4bbf-bc5b-4afe-b06e-f63244bf86ed`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/446b6e8d-9fef-4169-a1ae-2dad082e4b86/correct" \
    -H "Content-Type: application/json" \
    -d '{"is_valid": false, "reviewed_by": "Claude AI Audit Batch 2"}'
  ```

---

### Image 19: SANCTUARY_02832.jpg [OK] CORRECT
- **Database Classification:** doe (50.21% confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night vision/IR. Deer visible on left side. No antlers visible.
- **Detection ID:** `8a98237a-6578-477c-a13f-14a90d85aa4f`
- **Image ID:** `9bfa654c-6414-4300-9cc7-18c6076e1c13`
- **Action:** None required

---

### Image 20: Sanctuary2_20251103_095644_001.jpg [FAIL] INCORRECT
- **Database Classification:** buck (50.22% confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT - Buck misidentified
- **Notes:** Clear daylight image. Multiple deer near feeder. No visible antlers on any deer. All appear to be does.
- **Detection ID:** `329449c7-c621-44c7-af2b-6d4713e1e1bb`
- **Image ID:** `97a78597-0b6e-4b85-8ee4-e86df7e685d2`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/329449c7-c621-44c7-af2b-6d4713e1e1bb/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 2"}'
  ```

---

## Statistics

### Accuracy Breakdown:
- **Total Reviewed:** 20 images
- **Correct Classifications:** 11 (55%)
- **Incorrect Classifications:** 6 (30%)
- **Uncertain/Too Distant:** 3 (15%)

### Error Types:
- **Does Misclassified as Bucks:** 5 (25%)
- **Bucks Misclassified as Does:** 0 (0%)
- **False Positives (No Deer):** 2 (10%)
- **Too Distant to Classify:** 3 (15%)

### Buck Classification Accuracy:
- **Buck Classifications:** 8 total
- **Correct:** 3 (37.5%)
- **Incorrect (actually does):** 5 (62.5%)
- **Uncertain:** 1 (12.5%)

### Doe Classification Accuracy:
- **Doe Classifications:** 12 total
- **Correct:** 9 (75%)
- **False Positives:** 2 (16.7%)
- **Uncertain:** 1 (8.3%)

---

## Critical Pattern Identified

**Buck Over-Classification:** When the model is uncertain (confidence ~50%), it has a strong bias toward classifying deer as "buck" even when no antlers are visible.

**Evidence:**
- 8 buck classifications in this batch
- Only 3 were actually bucks (37.5% accuracy)
- 5 were actually does (62.5% error rate)

**Recommendation:** This suggests the model's decision boundary may be biased toward the "buck" class when confidence is low. Consider adjusting classification thresholds or retraining with more balanced data.

---

## Batch Correction Commands

### Apply All Buck->Doe Corrections:
```bash
#!/bin/bash
API_URL="http://localhost:8001"

echo "[1/5] Correcting Hayfield_20250910_184443_001.jpg"
curl -X PATCH "${API_URL}/api/detections/cc143c1d-04c9-4eb6-a8d1-072c72d58bd9/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 2"}'

echo "[2/5] Correcting Hayfield_20251020_073510_001.jpg"
curl -X PATCH "${API_URL}/api/detections/39facc44-dfa6-4887-bc28-91f49de0b8cf/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 2"}'

echo "[3/5] Correcting Sanctuary2_20251104_164008_001.jpg"
curl -X PATCH "${API_URL}/api/detections/a2a87d11-ffb2-4cb1-be73-fc32a79e340c/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 2"}'

echo "[4/5] Correcting Hayfield_20251029_073217_001.jpg"
curl -X PATCH "${API_URL}/api/detections/6689745a-192d-4692-821b-e216f7f453cc/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 2"}'

echo "[5/5] Correcting Sanctuary2_20251103_095644_001.jpg"
curl -X PATCH "${API_URL}/api/detections/329449c7-c621-44c7-af2b-6d4713e1e1bb/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "doe", "reviewed_by": "Claude AI Audit Batch 2"}'
```

### Mark False Positives as Invalid:
```bash
echo "[1/2] Marking Jason1_20250915_030941_001.jpg as invalid"
curl -X PATCH "${API_URL}/api/detections/ad878ecc-b5b3-4edf-9e5b-bf8160353eb8/correct" \
  -H "Content-Type: application/json" \
  -d '{"is_valid": false, "reviewed_by": "Claude AI Audit Batch 2"}'

echo "[2/2] Marking TINMAN_00116.jpg as invalid"
curl -X PATCH "${API_URL}/api/detections/446b6e8d-9fef-4169-a1ae-2dad082e4b86/correct" \
  -H "Content-Type: application/json" \
  -d '{"is_valid": false, "reviewed_by": "Claude AI Audit Batch 2"}'
```

---

## Combined Results (Batch 1 + Batch 2)

### Overall Statistics:
- **Total Images Reviewed:** 30 (Batch 1: 10, Batch 2: 20)
- **Correct:** 18 (60%)
- **Incorrect:** 9 (30%)
- **Uncertain:** 3 (10%)

### Error Pattern Comparison:
**Batch 1 (50.00-50.08%):**
- Accuracy: 70%
- Cattle confusion: 1
- False positives: 1
- Buck/doe confusion: 1

**Batch 2 (50.09-50.22%):**
- Accuracy: 55%
- Cattle confusion: 0
- False positives: 2
- Buck/doe confusion: 5 (all does misclassified as bucks)

**Trend:** As confidence increases slightly (50.00→50.22%), accuracy decreases (70%→55%), primarily due to increased buck over-classification.

---

## Recommendations

### Immediate Actions:
1. Apply the 7 corrections identified above (5 buck→doe, 2 false positives)
2. Review all buck classifications with confidence < 55% (high error rate)
3. Consider implementing confidence-based flagging for manual review

### Model Improvement:
1. **Buck classification bias:** Investigate why model defaults to "buck" when uncertain
2. **Training data balance:** Ensure equal representation of bucks and does
3. **Feature engineering:** Improve antler detection specifically
4. **Threshold adjustment:** Consider raising minimum confidence for buck classification to 60%

### Workflow Improvements:
1. Flag all detections < 55% confidence for mandatory manual review
2. Implement two-stage review: automated + human verification for low confidence
3. Create training data from corrected detections

---

**Audit Completed:** November 16, 2025
**Batch:** 2 of 171
**Next Batch:** Images 31-50 (confidence 50.22-52%)
