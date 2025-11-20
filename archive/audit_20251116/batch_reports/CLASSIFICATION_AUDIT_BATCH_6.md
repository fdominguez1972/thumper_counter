# Classification Audit Results - Batch 6

**Audit Date:** 2025-11-16
**Auditor:** Claude Code Vision Analysis - Direct Filesystem
**Method:** Direct vision analysis via Claude Code (no Playwright, no 413 errors!)
**Sample Size:** 20 images
**Confidence Range:** 0.5058 - 0.5067

## Executive Summary

**Overall Accuracy:** 70.6% (12 correct out of 17 determinable)
**Corrections Needed:** 5 images (25.0%)
**Uncertain:** 3 images (15.0%)

### Statistics
- **Total Images:** 20
- **Correct:** 12 (60.0%)
- **Incorrect:** 5 (25.0%)
- **Uncertain:** 3 (15.0%)

### Key Findings
- **Buck misclassification pattern continues:** Most "buck" classifications at 50.3-50.4% confidence are actually does
- **Model bias:** Strong tendency to over-classify does as bucks at this confidence threshold
- **Night/IR images:** 3 images too dark/unclear for confident determination

---

## Detailed Results

### Image 101: HAYFIELD_01546.jpg [OK]
- **Database Classification:** doe (0.5058 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Dusk image, multiple deer distant in field, appear to be does
- **Detection ID:** `a86fa88b-2d84-43bc-bab0-3cf4554f94f6`
- **Image ID:** `a86fa88b-2d84-43bc-bab0-3cf4554f94f6`

---

### Image 102: Sanctuary2_20251101_104338_001.jpg [FAIL]
- **Database Classification:** buck (0.5058 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear daylight, two deer at feeder, both are does (no antlers)
- **Detection ID:** `0307f96c-2a91-4286-8010-96c90f39e946`
- **Image ID:** `0307f96c-2a91-4286-8010-96c90f39e946`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/0307f96c-2a91-4286-8010-96c90f39e946/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 6"}'
  ```

---

### Image 103: Sanctuary2_20251104_163854_001.jpg [OK]
- **Database Classification:** doe (0.5059 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear image, multiple deer at feeder, all does (no antlers)
- **Detection ID:** `71fb2e1b-6feb-4e17-afe3-5fec634f473e`
- **Image ID:** `71fb2e1b-6feb-4e17-afe3-5fec634f473e`

---

### Image 104: HAYFIELD_07695.jpg [WARN]
- **Database Classification:** doe (0.5059 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Night IR, deer distant and grainy, cannot confidently determine
- **Detection ID:** `95e6f87c-877f-4bd4-802e-e52aaa835410`
- **Image ID:** `95e6f87c-877f-4bd4-802e-e52aaa835410`

---

### Image 105: HAYFIELD_07111.jpg [WARN]
- **Database Classification:** doe (0.5059 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Dawn/sunrise, deer distant in field, backlit and too dark to determine
- **Detection ID:** `7c66428d-a45c-4438-9892-e9a6adc682cb`
- **Image ID:** `7c66428d-a45c-4438-9892-e9a6adc682cb`

---

### Image 106: HAYFIELD_00559.jpg [OK]
- **Database Classification:** doe (0.5060 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear daytime image, multiple deer and cattle at feeder, deer are does
- **Detection ID:** `8180f928-1d94-45ac-bde5-81f5c249d810`
- **Image ID:** `8180f928-1d94-45ac-bde5-81f5c249d810`

---

### Image 107: Jason1_20250921_002041_001.jpg [OK]
- **Database Classification:** doe (0.5060 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night IR but clear, deer at fence, no antlers visible = doe
- **Detection ID:** `0da4de5a-5932-47e5-be25-56a10ffc46d6`
- **Image ID:** `0da4de5a-5932-47e5-be25-56a10ffc46d6`

---

### Image 108: Sanctuary2_20251101_174253_001.jpg [FAIL]
- **Database Classification:** buck (0.5060 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear dusk image, deer at feeder, no antlers = doe
- **Detection ID:** `f183d605-7f8b-4d21-8cd5-c8004edf8e68`
- **Image ID:** `f183d605-7f8b-4d21-8cd5-c8004edf8e68`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/f183d605-7f8b-4d21-8cd5-c8004edf8e68/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 6"}'
  ```

---

### Image 109: Hayfield_20251020_064531_001.jpg [FAIL]
- **Database Classification:** buck (0.5061 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Night IR but reasonably clear, deer in field, no antlers = doe
- **Detection ID:** `e00690e1-2410-4b3a-8d9f-7a2150949598`
- **Image ID:** `e00690e1-2410-4b3a-8d9f-7a2150949598`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/e00690e1-2410-4b3a-8d9f-7a2150949598/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 6"}'
  ```

---

### Image 110: HAYFIELD_03599.jpg [OK]
- **Database Classification:** doe (0.5061 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear daytime image, deer at feeder, no antlers = doe
- **Detection ID:** `521f995e-b23d-44f2-a514-9204179a3160`
- **Image ID:** `521f995e-b23d-44f2-a514-9204179a3160`

---

### Image 111: 270_JASON_00491.jpg [OK]
- **Database Classification:** doe (0.5062 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear sunrise image, two deer at fence, both appear to be does (no antlers visible)
- **Detection ID:** `ad96bcc5-e82f-41d9-9f0b-cbcff9fb3818`
- **Image ID:** `ad96bcc5-e82f-41d9-9f0b-cbcff9fb3818`

---

### Image 112: Hayfield_20251016_064901_001.jpg [OK]
- **Database Classification:** doe (0.5062 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night IR but clear, deer in field, no antlers = doe
- **Detection ID:** `530bb686-679a-4257-85a5-a15d2348aa20`
- **Image ID:** `530bb686-679a-4257-85a5-a15d2348aa20`

---

### Image 113: Hayfield_20251108_191613_001.jpg [OK]
- **Database Classification:** doe (0.5063 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night IR, two deer visible, both appear to be does
- **Detection ID:** `4d8b3689-bfbb-4623-bc2b-f7539ec9a0ea`
- **Image ID:** `4d8b3689-bfbb-4623-bc2b-f7539ec9a0ea`

---

### Image 114: CAMPHOUSE_03199.jpg [OK]
- **Database Classification:** doe (0.5063 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear early morning image, deer at feeder, no antlers = doe
- **Detection ID:** `f71b0802-4f3a-49ec-bf6e-8797c75d1d3a`
- **Image ID:** `f71b0802-4f3a-49ec-bf6e-8797c75d1d3a`

---

### Image 115: SANCTUARY_03146.jpg [OK]
- **Database Classification:** doe (0.5065 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night IR but clear, two deer at feeder, both appear to be does (no antlers)
- **Detection ID:** `6edd831d-9b0a-4038-ae7c-d124b66ad42d`
- **Image ID:** `6edd831d-9b0a-4038-ae7c-d124b66ad42d`

---

### Image 116: Sanctuary2_20251109_064211_001.jpg [FAIL]
- **Database Classification:** buck (0.5066 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear early morning image, two deer at feeder, both are does (no antlers)
- **Detection ID:** `0e8a9c6b-0c3d-40fa-ac42-ce6c07afcf66`
- **Image ID:** `0e8a9c6b-0c3d-40fa-ac42-ce6c07afcf66`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/0e8a9c6b-0c3d-40fa-ac42-ce6c07afcf66/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 6"}'
  ```

---

### Image 117: Sanctuary2_20251102_171248_001.jpg [FAIL]
- **Database Classification:** buck (0.5066 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear dusk image, deer in field, no antlers visible = doe
- **Detection ID:** `925c431f-cf0f-4d1a-8a19-245d066ab6f1`
- **Image ID:** `925c431f-cf0f-4d1a-8a19-245d066ab6f1`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/925c431f-cf0f-4d1a-8a19-245d066ab6f1/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 6"}'
  ```

---

### Image 118: Sanctuary2_20251108_172614_001.jpg [OK]
- **Database Classification:** doe (0.5066 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear dusk image, two deer at feeder, both are does (no antlers)
- **Detection ID:** `7d30ca51-1d77-4714-841f-7458ac041e73`
- **Image ID:** `7d30ca51-1d77-4714-841f-7458ac041e73`

---

### Image 119: SANCTUARY_09704.jpg [WARN]
- **Database Classification:** doe (0.5067 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Night IR, deer distant in grass, too grainy to confidently determine
- **Detection ID:** `0f5cc145-2659-4bba-a3c2-22a471ba4b25`
- **Image ID:** `0f5cc145-2659-4bba-a3c2-22a471ba4b25`

---

### Image 120: Sanctuary2_20251103_203208_001.jpg [OK]
- **Database Classification:** doe (0.5067 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night IR but clear, multiple deer at feeder, all appear to be does
- **Detection ID:** `a3b5ec95-cffd-4f68-9b39-ccd2be88e0c1`
- **Image ID:** `a3b5ec95-cffd-4f68-9b39-ccd2be88e0c1`

---

