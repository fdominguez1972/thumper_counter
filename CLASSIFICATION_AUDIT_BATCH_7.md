# Classification Audit Results - Batch 7

**Audit Date:** 2025-11-16
**Auditor:** Claude Code Vision - NVMe Turbo
**Method:** Direct vision analysis via Claude Code (no Playwright, no 413 errors!)
**Sample Size:** 20 images
**Confidence Range:** 0.5068 - 0.5079

## Executive Summary

**Overall Accuracy:** 42.9% (6 correct out of 14 determinable)
**Corrections Needed:** 8 images (40.0%)
**Uncertain:** 6 images (30.0%)

### Statistics
- **Total Images:** 20
- **Correct:** 6 (30.0%)
- **Incorrect:** 8 (40.0%)
- **Uncertain:** 6 (30.0%)

### Key Findings
- **Buck misclassification pattern continues:** Most "buck" classifications at 50.3-50.4% confidence are actually does
- **Model bias:** Strong tendency to over-classify does as bucks at this confidence threshold
- **Night/IR images:** 6 images too dark/unclear for confident determination

---

## Detailed Results

### Image 121: HAYFIELD_09804.jpg [OK]
- **Database Classification:** doe (0.5068 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Rainy day, deer distant at feeder, no antlers = doe
- **Detection ID:** `447438c5-5af7-4a17-94b3-e613d8847fbc`
- **Image ID:** `447438c5-5af7-4a17-94b3-e613d8847fbc`

---

### Image 122: CAMPHOUSE_03283.jpg [OK]
- **Database Classification:** doe (0.5068 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear daylight, deer grazing, no antlers = doe
- **Detection ID:** `55d858ca-d40c-44d7-9307-8c2c772a0a46`
- **Image ID:** `55d858ca-d40c-44d7-9307-8c2c772a0a46`

---

### Image 123: Sanctuary2_20251102_172509_001.jpg [FAIL]
- **Database Classification:** buck (0.5068 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear dusk, deer at feeder, no antlers = doe
- **Detection ID:** `50c19df5-42d2-48e3-966a-4c8444a70dec`
- **Image ID:** `50c19df5-42d2-48e3-966a-4c8444a70dec`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/50c19df5-42d2-48e3-966a-4c8444a70dec/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 7"}'
  ```

---

### Image 124: Hayfield_20250915_181119_001.jpg [OK]
- **Database Classification:** doe (0.5069 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Dusk, deer at feeder, no antlers = doe
- **Detection ID:** `28bcc8a0-f8ef-46bd-9446-2827c3354c03`
- **Image ID:** `28bcc8a0-f8ef-46bd-9446-2827c3354c03`

---

### Image 125: HAYFIELD_10873.jpg [WARN]
- **Database Classification:** buck (0.5070 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Grainy overcast day, multiple deer, too unclear to determine
- **Detection ID:** `aba7cc95-fc67-4827-9438-261cc1bddd62`
- **Image ID:** `aba7cc95-fc67-4827-9438-261cc1bddd62`

---

### Image 126: HAYFIELD_09436.jpg [FAIL]
- **Database Classification:** buck (0.5071 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Overcast, multiple deer at feeder, all are does (no antlers)
- **Detection ID:** `5848b938-1b1a-4c71-b070-c0268f7d1684`
- **Image ID:** `5848b938-1b1a-4c71-b070-c0268f7d1684`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/5848b938-1b1a-4c71-b070-c0268f7d1684/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 7"}'
  ```

---

### Image 127: Hayfield_20251108_032521_001.jpg [FAIL]
- **Database Classification:** buck (0.5071 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Night IR but clear, deer alert, no antlers = doe
- **Detection ID:** `b05be066-38de-40d1-8500-367db2f5e1b4`
- **Image ID:** `b05be066-38de-40d1-8500-367db2f5e1b4`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/b05be066-38de-40d1-8500-367db2f5e1b4/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 7"}'
  ```

---

### Image 128: SANCTUARY_09373.jpg [WARN]
- **Database Classification:** doe (0.5072 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Night IR, deer grainy and distant, too unclear
- **Detection ID:** `a9031ea9-34d5-4148-b325-95b6a9f6b720`
- **Image ID:** `a9031ea9-34d5-4148-b325-95b6a9f6b720`

---

### Image 129: Sanctuary2_20251106_124944_001.jpg [FAIL]
- **Database Classification:** buck (0.5072 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear daylight, multiple does at feeder, all no antlers
- **Detection ID:** `49edd3a8-0d3d-4f2e-a584-517f4b15126c`
- **Image ID:** `49edd3a8-0d3d-4f2e-a584-517f4b15126c`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/49edd3a8-0d3d-4f2e-a584-517f4b15126c/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 7"}'
  ```

---

### Image 130: Sanctuary2_20251102_130804_001.jpg [OK]
- **Database Classification:** doe (0.5072 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear daylight, deer at feeder, no antlers = doe
- **Detection ID:** `caf643cc-85ca-4264-bf35-75b1eb8d9c83`
- **Image ID:** `caf643cc-85ca-4264-bf35-75b1eb8d9c83`

---

### Image 131: CAMPHOUSE_00666.jpg [FAIL]
- **Database Classification:** buck (0.5073 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear daylight, deer grazing at feeder, no antlers = doe
- **Detection ID:** `9014ded2-bb12-481c-9c6a-50d9f885363f`
- **Image ID:** `9014ded2-bb12-481c-9c6a-50d9f885363f`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/9014ded2-bb12-481c-9c6a-50d9f885363f/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 7"}'
  ```

---

### Image 132: Hayfield_20251105_173323_001.jpg [OK]
- **Database Classification:** doe (0.5073 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Dawn, two deer in field, both appear to be does
- **Detection ID:** `6d8c66c3-ee7b-42bd-b977-2c691a691b17`
- **Image ID:** `6d8c66c3-ee7b-42bd-b977-2c691a691b17`

---

### Image 133: SANCTUARY_02283.jpg [WARN]
- **Database Classification:** buck (0.5073 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Night IR, too grainy, no deer clearly visible
- **Detection ID:** `88085518-e6d3-4bb3-95c3-d6a95b743251`
- **Image ID:** `88085518-e6d3-4bb3-95c3-d6a95b743251`

---

### Image 134: SANCTUARY_01163.jpg [WARN]
- **Database Classification:** doe (0.5073 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Dusk, no deer visible or too dark to determine
- **Detection ID:** `6d738fe2-ada3-4f0f-9186-cfa38e10cff9`
- **Image ID:** `6d738fe2-ada3-4f0f-9186-cfa38e10cff9`

---

### Image 135: Sanctuary2_20251105_164037_001.jpg [FAIL]
- **Database Classification:** buck (0.5074 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear afternoon, two deer at feeder, both does (no antlers)
- **Detection ID:** `eeccfbe6-e02d-4c8b-97fa-8092d81efec6`
- **Image ID:** `eeccfbe6-e02d-4c8b-97fa-8092d81efec6`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/eeccfbe6-e02d-4c8b-97fa-8092d81efec6/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 7"}'
  ```

---

### Image 136: Hayfield_20251030_171930_001.jpg [WARN]
- **Database Classification:** buck (0.5075 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Dusk silhouette, deer at feeder but too dark to determine
- **Detection ID:** `e3515f31-27ff-4bd8-97c2-332e6ade797b`
- **Image ID:** `e3515f31-27ff-4bd8-97c2-332e6ade797b`

---

### Image 137: Hayfield_20251108_191732_001.jpg [OK]
- **Database Classification:** doe (0.5076 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night IR but clear, deer alert, no antlers = doe
- **Detection ID:** `b5872dda-f38a-4a7a-ba0a-d5d7e905befe`
- **Image ID:** `b5872dda-f38a-4a7a-ba0a-d5d7e905befe`

---

### Image 138: Hayfield_20251008_070906_001.jpg [WARN]
- **Database Classification:** buck (0.5077 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Dusk/dawn, deer silhouette, too dark to confidently determine
- **Detection ID:** `972eb065-7064-4d31-945a-fb8d487ebaba`
- **Image ID:** `972eb065-7064-4d31-945a-fb8d487ebaba`

---

### Image 139: Sanctuary2_20251109_072747_001.jpg [FAIL]
- **Database Classification:** buck (0.5079 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear morning, deer at feeder, no antlers = doe
- **Detection ID:** `a921fb16-e9ae-4d8e-87a2-7f177823c33d`
- **Image ID:** `a921fb16-e9ae-4d8e-87a2-7f177823c33d`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/a921fb16-e9ae-4d8e-87a2-7f177823c33d/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 7"}'
  ```

---

### Image 140: Sanctuary2_20251102_162757_001.jpg [FAIL]
- **Database Classification:** buck (0.5079 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear afternoon, multiple deer at feeder, all does (no antlers)
- **Detection ID:** `f0d70dc7-14e7-4917-800b-f67dacc4b92e`
- **Image ID:** `f0d70dc7-14e7-4917-800b-f67dacc4b92e`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/f0d70dc7-14e7-4917-800b-f67dacc4b92e/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 7"}'
  ```

---

