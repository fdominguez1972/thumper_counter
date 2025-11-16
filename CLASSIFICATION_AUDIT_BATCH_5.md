# Classification Audit Results - Batch 5

**Audit Date:** 2025-11-16
**Auditor:** Claude Code Vision Analysis
**Method:** Direct vision analysis via Claude Code (no Playwright, no 413 errors!)
**Sample Size:** 20 images
**Confidence Range:** 0.5046 - 0.5052

## Executive Summary

**Overall Accuracy:** 53.3% (8 correct out of 15 determinable)
**Corrections Needed:** 7 images (35.0%)
**Uncertain:** 5 images (25.0%)

### Statistics
- **Total Images:** 20
- **Correct:** 8 (40.0%)
- **Incorrect:** 7 (35.0%)
- **Uncertain:** 5 (25.0%)

### Key Findings
- **Buck misclassification pattern continues:** Most "buck" classifications at 50.3-50.4% confidence are actually does
- **Model bias:** Strong tendency to over-classify does as bucks at this confidence threshold
- **Night/IR images:** 5 images too dark/unclear for confident determination

---

## Detailed Results

### Image 81: Sanctuary2_20251105_162347_001.jpg [FAIL]
- **Database Classification:** buck (0.5046 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear image, multiple deer at feeder, all are does (no antlers)
- **Detection ID:** `1fdd8444-0f4f-4fc2-bc1d-062fa5d9bab2`
- **Image ID:** `a76f86c6-99c7-4dd1-8c93-fe1a06414685`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/1fdd8444-0f4f-4fc2-bc1d-062fa5d9bab2/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 5"}'
  ```

---

### Image 82: Sanctuary2_20251108_172750_001.jpg [OK]
- **Database Classification:** doe (0.5046 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear image, multiple deer at feeder, all are does
- **Detection ID:** `a76f86c6-99c7-4dd1-8c93-fe1a06414685`
- **Image ID:** `a76f86c6-99c7-4dd1-8c93-fe1a06414685`

---

### Image 83: Hayfield_20250915_085120_001.jpg [FAIL]
- **Database Classification:** buck (0.5046 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear morning image, deer grazing, no antlers visible = doe
- **Detection ID:** `9c8db883-c966-468a-a949-dd41ae326930`
- **Image ID:** `9c8db883-c966-468a-a949-dd41ae326930`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/9c8db883-c966-468a-a949-dd41ae326930/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 5"}'
  ```

---

### Image 84: Sanctuary2_20251031_185455_001.jpg [FAIL]
- **Database Classification:** buck (0.5047 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear dusk image, deer at feeder, no antlers = doe
- **Detection ID:** `a82ffed4-4c1c-45c3-9e93-6e9c54e0c14a`
- **Image ID:** `a82ffed4-4c1c-45c3-9e93-6e9c54e0c14a`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/a82ffed4-4c1c-45c3-9e93-6e9c54e0c14a/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 5"}'
  ```

---

### Image 85: Hayfield_20251101_093118_001.jpg [OK]
- **Database Classification:** doe (0.5048 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear daytime image, deer in field, no antlers = doe
- **Detection ID:** `cb823ecb-603b-4896-b95b-809f2cee3dfb`
- **Image ID:** `cb823ecb-603b-4896-b95b-809f2cee3dfb`

---

### Image 86: SANCTUARY_06124.jpg [WARN]
- **Database Classification:** doe (0.5049 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Night IR image, deer distant, too grainy to confidently determine
- **Detection ID:** `7f02f298-edaf-4aae-92d7-c308fc62408b`
- **Image ID:** `7f02f298-edaf-4aae-92d7-c308fc62408b`

---

### Image 87: Sanctuary2_20251101_174834_001.jpg [FAIL]
- **Database Classification:** buck (0.5049 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear dusk image, multiple deer at feeder, all are does (no antlers)
- **Detection ID:** `0a217184-8ecc-40ba-aef2-9fa4983cabde`
- **Image ID:** `0a217184-8ecc-40ba-aef2-9fa4983cabde`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/0a217184-8ecc-40ba-aef2-9fa4983cabde/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 5"}'
  ```

---

### Image 88: Sanctuary2_20251104_160627_001.jpg [FAIL]
- **Database Classification:** buck (0.5049 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear image, multiple deer at feeder, all are does (no antlers)
- **Detection ID:** `7b03c491-b681-4d94-aa71-1d40ad971e56`
- **Image ID:** `7b03c491-b681-4d94-aa71-1d40ad971e56`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/7b03c491-b681-4d94-aa71-1d40ad971e56/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 5"}'
  ```

---

### Image 89: HAYFIELD_11236.jpg [WARN]
- **Database Classification:** doe (0.5049 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Night IR image, no deer visible in frame or too dark to determine
- **Detection ID:** `fd73ce29-cc53-47fc-8906-c49d5d11e913`
- **Image ID:** `fd73ce29-cc53-47fc-8906-c49d5d11e913`

---

### Image 90: Sanctuary2_20251102_173314_001.jpg [FAIL]
- **Database Classification:** buck (0.5050 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear dusk image, multiple deer at feeder, all are does (no antlers)
- **Detection ID:** `f2330acd-fa16-4a33-acea-015b0f273f1a`
- **Image ID:** `f2330acd-fa16-4a33-acea-015b0f273f1a`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/f2330acd-fa16-4a33-acea-015b0f273f1a/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 5"}'
  ```

---

### Image 91: SANCTUARY_07772.jpg [OK]
- **Database Classification:** doe (0.5050 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night IR but clear enough, deer grazing, no antlers = doe
- **Detection ID:** `bab4fc49-ace9-43c4-87f6-046ce2b5b944`
- **Image ID:** `bab4fc49-ace9-43c4-87f6-046ce2b5b944`

---

### Image 92: SANCTUARY_05274.jpg [OK]
- **Database Classification:** doe (0.5050 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night IR image, two deer at feeder, both appear to be does (no antlers visible)
- **Detection ID:** `d860eab7-753c-4c97-8e89-2dde7f0d943b`
- **Image ID:** `d860eab7-753c-4c97-8e89-2dde7f0d943b`

---

### Image 93: Sanctuary2_20251105_153554_001.jpg [OK]
- **Database Classification:** doe (0.5050 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear daylight image, multiple deer at feeder, all are does (no antlers)
- **Detection ID:** `d8ac6737-c3d4-46ef-931b-1bd3575725ce`
- **Image ID:** `d8ac6737-c3d4-46ef-931b-1bd3575725ce`

---

### Image 94: Sanctuary2_20251104_174343_001.jpg [FAIL]
- **Database Classification:** buck (0.5051 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear dusk image, multiple deer visible, all are does (no antlers)
- **Detection ID:** `3397cece-aff1-4fa7-904d-6a05082a86bc`
- **Image ID:** `3397cece-aff1-4fa7-904d-6a05082a86bc`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/3397cece-aff1-4fa7-904d-6a05082a86bc/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 5"}'
  ```

---

### Image 95: HAYFIELD_09841.jpg [WARN]
- **Database Classification:** buck (0.5051 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Foggy/hazy early morning, deer distant and obscured, cannot confidently determine
- **Detection ID:** `3424b089-c979-4be7-b160-7f116047b8de`
- **Image ID:** `3424b089-c979-4be7-b160-7f116047b8de`

---

### Image 96: HAYFIELD_01888.jpg [OK]
- **Database Classification:** doe (0.5051 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear early morning image, deer at feeder, no antlers = doe
- **Detection ID:** `21b0bdd3-8377-4a1f-b520-5abf791dd86a`
- **Image ID:** `21b0bdd3-8377-4a1f-b520-5abf791dd86a`

---

### Image 97: Sanctuary2_20251106_131118_001.jpg [OK]
- **Database Classification:** doe (0.5051 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear daylight image, deer at feeder, no antlers = doe
- **Detection ID:** `7953991c-3ab2-44d7-af8c-39a8e84b5a39`
- **Image ID:** `7953991c-3ab2-44d7-af8c-39a8e84b5a39`

---

### Image 98: HAYFIELD_11905.jpg [WARN]
- **Database Classification:** doe (0.5051 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Dense fog/mist, dawn/dusk lighting, no deer clearly visible or too obscured to determine
- **Detection ID:** `418eafa2-1166-4598-bf43-56a54b0e6b64`
- **Image ID:** `418eafa2-1166-4598-bf43-56a54b0e6b64`

---

### Image 99: SANCTUARY_04842.jpg [OK]
- **Database Classification:** doe (0.5051 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night IR but clear, two deer at feeder, both are does (no antlers)
- **Detection ID:** `9febcf0d-3023-498a-b557-6d177e8e79c6`
- **Image ID:** `9febcf0d-3023-498a-b557-6d177e8e79c6`

---

### Image 100: 270_JASON_00664.jpg [WARN]
- **Database Classification:** doe (0.5052 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Night IR, no deer visible in frame, just empty field
- **Detection ID:** `0216efab-045f-421e-bd7c-5a3076f09562`
- **Image ID:** `0216efab-045f-421e-bd7c-5a3076f09562`

---

