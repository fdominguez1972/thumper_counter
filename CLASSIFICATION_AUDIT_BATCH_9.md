# Classification Audit Results - Batch 9

**Audit Date:** 2025-11-16
**Auditor:** Claude Compressed
**Method:** Direct vision analysis via Claude Code (no Playwright, no 413 errors!)
**Sample Size:** 20 images
**Confidence Range:** 0.5086 - 0.5102

## Executive Summary

**Overall Accuracy:** 57.1% (8 correct out of 14 determinable)
**Corrections Needed:** 6 images (30.0%)
**Uncertain:** 6 images (30.0%)

### Statistics
- **Total Images:** 20
- **Correct:** 8 (40.0%)
- **Incorrect:** 6 (30.0%)
- **Uncertain:** 6 (30.0%)

### Key Findings
- **Buck misclassification pattern continues:** Most "buck" classifications at 50.3-50.4% confidence are actually does
- **Model bias:** Strong tendency to over-classify does as bucks at this confidence threshold
- **Night/IR images:** 6 images too dark/unclear for confident determination

---

## Detailed Results

### Image 161: SANCTUARY_03484.jpg [WARN]
- **Database Classification:** buck (0.5086 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Night IR grainy
- **Detection ID:** `740716c3-f894-4d49-a850-34c47dc5fff1`
- **Image ID:** `740716c3-f894-4d49-a850-34c47dc5fff1`

---

### Image 162: Sanctuary2_20251109_072016_001.jpg [FAIL]
- **Database Classification:** buck (0.5088 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Multiple does,no antlers
- **Detection ID:** `9ddc4cc1-be51-4906-88a0-f8a947d074f7`
- **Image ID:** `9ddc4cc1-be51-4906-88a0-f8a947d074f7`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/9ddc4cc1-be51-4906-88a0-f8a947d074f7/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 9"}'
  ```

---

### Image 163: SANCTUARY_10015.jpg [WARN]
- **Database Classification:** doe (0.5090 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Deer distant
- **Detection ID:** `5a281b23-5fa9-466f-a3e7-f02e1af9c64e`
- **Image ID:** `5a281b23-5fa9-466f-a3e7-f02e1af9c64e`

---

### Image 164: HAYFIELD_01449.jpg [OK]
- **Database Classification:** doe (0.5090 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** OK
- **Detection ID:** `e1605c14-be54-4397-9acd-50675758c6df`
- **Image ID:** `e1605c14-be54-4397-9acd-50675758c6df`

---

### Image 165: Sanctuary2_20251102_162713_001.jpg [OK]
- **Database Classification:** doe (0.5090 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** OK
- **Detection ID:** `9e9b1367-3015-4c6e-80ca-2a23a0208470`
- **Image ID:** `9e9b1367-3015-4c6e-80ca-2a23a0208470`

---

### Image 166: Sanctuary2_20251106_095137_001.jpg [OK]
- **Database Classification:** doe (0.5091 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** OK
- **Detection ID:** `f52e5bbd-0bd4-4023-a400-1e30d41c569b`
- **Image ID:** `f52e5bbd-0bd4-4023-a400-1e30d41c569b`

---

### Image 167: Sanctuary2_20251101_175303_001.jpg [FAIL]
- **Database Classification:** buck (0.5093 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Does at feeder
- **Detection ID:** `b56cf15e-4d75-4ff7-8617-54f29ad24a8f`
- **Image ID:** `b56cf15e-4d75-4ff7-8617-54f29ad24a8f`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/b56cf15e-4d75-4ff7-8617-54f29ad24a8f/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 9"}'
  ```

---

### Image 168: HAYFIELD_09087.jpg [WARN]
- **Database Classification:** doe (0.5094 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** No deer visible
- **Detection ID:** `2033c0f4-1376-44ab-9bb2-c410c661d76f`
- **Image ID:** `2033c0f4-1376-44ab-9bb2-c410c661d76f`

---

### Image 169: Sanctuary2_20251102_172617_001.jpg [FAIL]
- **Database Classification:** buck (0.5094 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Multiple does
- **Detection ID:** `d1a4d239-20a5-4176-b1f4-48e4ab70ea69`
- **Image ID:** `d1a4d239-20a5-4176-b1f4-48e4ab70ea69`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/d1a4d239-20a5-4176-b1f4-48e4ab70ea69/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 9"}'
  ```

---

### Image 170: Sanctuary2_20251108_171640_001.jpg [OK]
- **Database Classification:** doe (0.5095 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** OK
- **Detection ID:** `5e20a301-f3c3-498d-acd0-61d9228648c0`
- **Image ID:** `5e20a301-f3c3-498d-acd0-61d9228648c0`

---

### Image 171: SANCTUARY_04836.jpg [OK]
- **Database Classification:** doe (0.5095 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** OK
- **Detection ID:** `cfb62a39-6c8e-4b85-b9cd-bc04fd5a02b9`
- **Image ID:** `cfb62a39-6c8e-4b85-b9cd-bc04fd5a02b9`

---

### Image 172: Sanctuary2_20251102_162103_001.jpg [OK]
- **Database Classification:** doe (0.5098 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** OK
- **Detection ID:** `a2b50165-291c-4ff4-bdcd-7c53e348bd4c`
- **Image ID:** `a2b50165-291c-4ff4-bdcd-7c53e348bd4c`

---

### Image 173: Sanctuary2_20251102_133350_001.jpg [OK]
- **Database Classification:** doe (0.5098 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** OK
- **Detection ID:** `b558e497-e1bf-4c71-8b09-7d47d7cc12d7`
- **Image ID:** `b558e497-e1bf-4c71-8b09-7d47d7cc12d7`

---

### Image 174: Sanctuary2_20251101_154731_001.jpg [FAIL]
- **Database Classification:** buck (0.5101 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Doe in field
- **Detection ID:** `f29d099d-5f17-4d9c-9823-4f6ab0f49f1a`
- **Image ID:** `f29d099d-5f17-4d9c-9823-4f6ab0f49f1a`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/f29d099d-5f17-4d9c-9823-4f6ab0f49f1a/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 9"}'
  ```

---

### Image 175: SANCTUARY_04196.jpg [WARN]
- **Database Classification:** buck (0.5101 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Night IR grainy
- **Detection ID:** `ab0a94be-8a92-4382-a4b0-1a5cb90b44fb`
- **Image ID:** `ab0a94be-8a92-4382-a4b0-1a5cb90b44fb`

---

### Image 176: Sanctuary2_20251102_163847_001.jpg [FAIL]
- **Database Classification:** buck (0.5101 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Multiple does
- **Detection ID:** `0ccae99d-3aa0-4682-be23-a760e674850a`
- **Image ID:** `0ccae99d-3aa0-4682-be23-a760e674850a`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/0ccae99d-3aa0-4682-be23-a760e674850a/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 9"}'
  ```

---

### Image 177: Sanctuary2_20251103_203907_001.jpg [OK]
- **Database Classification:** doe (0.5101 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** OK
- **Detection ID:** `f66d31e5-b536-470d-973a-191ffe30f65d`
- **Image ID:** `f66d31e5-b536-470d-973a-191ffe30f65d`

---

### Image 178: HAYFIELD_01512.jpg [WARN]
- **Database Classification:** doe (0.5101 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** No deer visible
- **Detection ID:** `40cff4e7-2d75-477e-bc03-25d01aba1fc4`
- **Image ID:** `40cff4e7-2d75-477e-bc03-25d01aba1fc4`

---

### Image 179: HAYFIELD_09130.jpg [WARN]
- **Database Classification:** buck (0.5101 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** No deer visible
- **Detection ID:** `e707da17-fb8f-4e98-8663-7eaafdfb187e`
- **Image ID:** `e707da17-fb8f-4e98-8663-7eaafdfb187e`

---

### Image 180: Sanctuary2_20251102_172917_001.jpg [FAIL]
- **Database Classification:** buck (0.5102 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Does at feeder
- **Detection ID:** `2fec528b-20eb-4d4b-acac-7353a2d56141`
- **Image ID:** `2fec528b-20eb-4d4b-acac-7353a2d56141`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/2fec528b-20eb-4d4b-acac-7353a2d56141/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 9"}'
  ```

---

