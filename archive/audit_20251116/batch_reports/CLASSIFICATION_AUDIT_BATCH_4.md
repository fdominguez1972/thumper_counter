# Classification Audit Results - Batch 4

**Audit Date:** 2025-11-16
**Auditor:** Claude Code Vision Analysis
**Method:** Direct vision analysis via Claude Code (no Playwright, no 413 errors!)
**Sample Size:** 20 images
**Confidence Range:** 0.5033 - 0.5044

## Executive Summary

**Overall Accuracy:** 31.2% (5 correct out of 16 determinable)
**Corrections Needed:** 11 images (55.0%)
**Uncertain:** 4 images (20.0%)

### Statistics
- **Total Images:** 20
- **Correct:** 5 (25.0%)
- **Incorrect:** 11 (55.0%)
- **Uncertain:** 4 (20.0%)

### Key Findings
- **Buck misclassification pattern continues:** Most "buck" classifications at 50.3-50.4% confidence are actually does
- **Model bias:** Strong tendency to over-classify does as bucks at this confidence threshold
- **Night/IR images:** 4 images too dark/unclear for confident determination

---

## Detailed Results

### Image 61: CAMPHOUSE_02956.jpg [OK]
- **Database Classification:** doe (0.5033 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear daylight image, deer has no antlers, definitely a doe
- **Detection ID:** `adb9a81b-3e39-4c27-ac8b-c37289a054ba`
- **Image ID:** `7818f96e-48b2-4129-896d-3af088f4d058`

---

### Image 62: CAMPHOUSE_03187.jpg [OK]
- **Database Classification:** doe (0.5035 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Same location, doe grazing, no antlers visible
- **Detection ID:** `2ac3cbe4-ca34-43da-a2e5-66fda8a20ce1`
- **Image ID:** `7c799a77-a871-4c37-9eaf-cb0c0eb79193`

---

### Image 63: Sanctuary2_20251108_173213_001.jpg [FAIL]
- **Database Classification:** buck (0.5035 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear image, deer feeding at feeder, no antlers visible, smooth head = doe
- **Detection ID:** `6d909440-4502-4b3b-8c44-aa7cd408ceb1`
- **Image ID:** `c4e90266-1233-49c8-9658-b0d684a8bc5a`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/6d909440-4502-4b3b-8c44-aa7cd408ceb1/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 4"}'
  ```

---

### Image 64: HAYFIELD_09582.jpg [WARN]
- **Database Classification:** buck (0.5036 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Dusk/twilight image, deer is distant and head position makes it hard to see antlers clearly
- **Detection ID:** `f40fb252-10be-467f-a681-d0f77c93ffd6`
- **Image ID:** `6bc2aecd-c04a-4bbd-966d-e43ea484d89e`

---

### Image 65: HAYFIELD_07934.jpg [WARN]
- **Database Classification:** doe (0.5036 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Night IR image, very grainy, deer barely visible, cannot determine with confidence
- **Detection ID:** `a28c3bc4-07de-4eca-be92-c26b74352ee3`
- **Image ID:** `4dc3b35f-88a6-48ec-a5df-dc5cb4d62b7a`

---

### Image 66: Sanctuary2_20251101_110905_001.jpg [FAIL]
- **Database Classification:** buck (0.5037 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear daylight image, deer at feeder, no antlers visible, smooth head = doe
- **Detection ID:** `26e25389-65c7-4193-b1d1-32e719db8b1c`
- **Image ID:** `e18fae3d-aee5-4828-80cc-31f64a4ce6a3`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/26e25389-65c7-4193-b1d1-32e719db8b1c/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 4"}'
  ```

---

### Image 67: Hayfield_20250918_075928_001.jpg [FAIL]
- **Database Classification:** buck (0.5037 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear daylight, multiple deer visible, closest deer (right side) has no antlers = doe
- **Detection ID:** `33d86a56-b928-4aa6-a28d-be4d13ed7282`
- **Image ID:** `378b8a68-ddb1-4a53-8de3-28e4bd9f9fe9`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/33d86a56-b928-4aa6-a28d-be4d13ed7282/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 4"}'
  ```

---

### Image 68: Sanctuary2_20251101_165327_001.jpg [FAIL]
- **Database Classification:** buck (0.5037 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear image, two deer visible, both are does (no antlers)
- **Detection ID:** `49430f45-c915-4f12-ab41-3c3e9f2b67fa`
- **Image ID:** `2e2c44d3-dabd-4a2a-9a00-6c155b71a252`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/49430f45-c915-4f12-ab41-3c3e9f2b67fa/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 4"}'
  ```

---

### Image 69: Sanctuary2_20251106_090419_001.jpg [FAIL]
- **Database Classification:** buck (0.5037 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear daylight image, deer at feeder, no antlers, smooth head = doe
- **Detection ID:** `851d4bfc-af53-42cf-9424-8c1355c1a424`
- **Image ID:** `f70aff64-134e-4f05-abb3-1b58ca424db6`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/851d4bfc-af53-42cf-9424-8c1355c1a424/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 4"}'
  ```

---

### Image 70: Sanctuary2_20251103_210552_001.jpg [WARN]
- **Database Classification:** buck (0.5037 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Night IR image, two deer in distance, cannot clearly see head details to confirm antlers
- **Detection ID:** `73ddc214-96bd-4c6d-a431-19a03a291de7`
- **Image ID:** `c8844810-4606-4d14-b747-1663517b9e15`

---

### Image 71: Hayfield_20251030_172333_001.jpg [OK]
- **Database Classification:** doe (0.5038 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear daylight image, deer at feeder, no antlers visible = doe
- **Detection ID:** `29c2c135-4b07-4719-a049-db459b8d7970`
- **Image ID:** `054ce42d-4fa5-48fb-9d63-745385554220`

---

### Image 72: Sanctuary2_20251102_170510_001.jpg [FAIL]
- **Database Classification:** buck (0.5038 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear daylight image, multiple deer visible, all are does (no antlers)
- **Detection ID:** `7f54eb1c-b555-4fdf-9a70-b34dcf5ea24b`
- **Image ID:** `042d68a9-16b1-494a-8d27-08421d36b5a3`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/7f54eb1c-b555-4fdf-9a70-b34dcf5ea24b/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 4"}'
  ```

---

### Image 73: Jason1_20251010_014512_001.jpg [WARN]
- **Database Classification:** doe (0.5040 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Night IR image, deer at fence, head position and IR blur make it impossible to confirm presence/absence of antlers
- **Detection ID:** `5a73a1db-93cb-4f5c-a710-a00b2a207e96`
- **Image ID:** `3b42917f-6306-4fcc-a1a2-a136aa6b80a3`

---

### Image 74: Jason1_20251009_202123_001.jpg [FAIL]
- **Database Classification:** buck (0.5041 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Night IR but clear image, deer head visible, no antlers, smooth head profile = doe
- **Detection ID:** `4ff4d91b-a79d-4081-acc0-cee02c994f73`
- **Image ID:** `bf01e8a2-4235-46e0-853f-eef06b1fb1e8`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/4ff4d91b-a79d-4081-acc0-cee02c994f73/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 4"}'
  ```

---

### Image 75: Sanctuary2_20251031_194058_001.jpg [OK]
- **Database Classification:** doe (0.5042 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night IR image but clear enough, deer at feeder, no antlers visible, appears to be doe
- **Detection ID:** `6dcf2949-c1b1-4acd-9a72-45cdd97a582d`
- **Image ID:** `b4f3c5bd-ce44-48c7-b0c8-685dcce3c1f6`

---

### Image 76: Sanctuary2_20251101_102202_001.jpg [FAIL]
- **Database Classification:** buck (0.5042 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear daylight image, deer alert at feeder, no antlers visible, smooth head = doe
- **Detection ID:** `45f790a8-024e-45df-8e48-c70359186549`
- **Image ID:** `a6199e68-0e4a-4e5c-ad02-7f3c6e337b70`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/45f790a8-024e-45df-8e48-c70359186549/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 4"}'
  ```

---

### Image 77: Sanctuary2_20251102_173105_001.jpg [FAIL]
- **Database Classification:** buck (0.5043 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear daylight image, two deer at feeder, both are does (no antlers visible)
- **Detection ID:** `e231603b-1d12-4504-8b76-fc0edd372b54`
- **Image ID:** `1776eea3-f4ea-4433-b160-4dd5b3fbf609`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/e231603b-1d12-4504-8b76-fc0edd372b54/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 4"}'
  ```

---

### Image 78: Hayfield_20251014_172146_001.jpg [FAIL]
- **Database Classification:** buck (0.5043 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear daylight image, two deer at feeder, both are does (no antlers)
- **Detection ID:** `c607e4db-3068-4608-a74d-9181c4228865`
- **Image ID:** `30313339-0551-421b-bff5-02811b3fac5b`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/c607e4db-3068-4608-a74d-9181c4228865/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 4"}'
  ```

---

### Image 79: Hayfield_20250914_080518_001.jpg [FAIL]
- **Database Classification:** buck (0.5044 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear early morning image, deer standing alert, no antlers visible = doe
- **Detection ID:** `4c9cb3a9-1f50-458e-aa15-cfa038d574da`
- **Image ID:** `42f4b61f-0026-4210-9a4d-8d8940b0b651`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/4c9cb3a9-1f50-458e-aa15-cfa038d574da/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 4"}'
  ```

---

### Image 80: Sanctuary2_20251104_170520_001.jpg [OK]
- **Database Classification:** doe (0.5044 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear daylight image, two deer at feeder, both does (no antlers)
- **Detection ID:** `21f73e7f-f5fe-4d2b-998e-a1e52c0ab3f7`
- **Image ID:** `affb7f78-42bf-414a-8ea0-0d680c55cd6b`

---

