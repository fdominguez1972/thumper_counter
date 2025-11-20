# Classification Audit Results - Batch 8

**Audit Date:** 2025-11-16
**Auditor:** Claude Code Vision - NVMe Turbo
**Method:** Direct vision analysis via Claude Code (no Playwright, no 413 errors!)
**Sample Size:** 20 images
**Confidence Range:** 0.5080 - 0.5086

## Executive Summary

**Overall Accuracy:** 57.9% (11 correct out of 19 determinable)
**Corrections Needed:** 8 images (40.0%)
**Uncertain:** 1 images (5.0%)

### Statistics
- **Total Images:** 20
- **Correct:** 11 (55.0%)
- **Incorrect:** 8 (40.0%)
- **Uncertain:** 1 (5.0%)

### Key Findings
- **Buck misclassification pattern continues:** Most "buck" classifications at 50.3-50.4% confidence are actually does
- **Model bias:** Strong tendency to over-classify does as bucks at this confidence threshold
- **Night/IR images:** 1 images too dark/unclear for confident determination

---

## Detailed Results

### Image 141: HAYFIELD_09155.jpg [OK]
- **Database Classification:** doe (0.5080 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night IR, deer at feeder, no antlers = doe
- **Detection ID:** `ec5ff21e-072d-4c33-a51c-0423733db0f9`
- **Image ID:** `ec5ff21e-072d-4c33-a51c-0423733db0f9`

---

### Image 142: Hayfield_20251008_065728_001.jpg [WARN]
- **Database Classification:** doe (0.5080 confidence)
- **Audit Classification:** uncertain
- **Status:** UNCERTAIN
- **Notes:** Dawn, too dark to determine
- **Detection ID:** `91d7a8b2-c8e1-47f2-8f6b-7a200d9e0739`
- **Image ID:** `91d7a8b2-c8e1-47f2-8f6b-7a200d9e0739`

---

### Image 143: Sanctuary2_20251105_171436_001.jpg [OK]
- **Database Classification:** doe (0.5081 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear dusk, deer at feeder, no antlers = doe
- **Detection ID:** `f4ada9b4-4957-40f5-8f1b-89f95b1a5171`
- **Image ID:** `f4ada9b4-4957-40f5-8f1b-89f95b1a5171`

---

### Image 144: Hayfield_20251102_000714_001.jpg [OK]
- **Database Classification:** doe (0.5081 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night IR, deer alert, no antlers = doe
- **Detection ID:** `ca640a08-fe2f-42fd-8ba2-916a681fcf6e`
- **Image ID:** `ca640a08-fe2f-42fd-8ba2-916a681fcf6e`

---

### Image 145: Sanctuary2_20251104_173210_001.jpg [OK]
- **Database Classification:** doe (0.5081 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear dusk, multiple does at feeder
- **Detection ID:** `0da34b1d-6f69-41a3-993f-c2eaba8f20ef`
- **Image ID:** `0da34b1d-6f69-41a3-993f-c2eaba8f20ef`

---

### Image 146: SANCTUARY_05302.jpg [OK]
- **Database Classification:** doe (0.5081 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night IR, deer grazing, no antlers = doe
- **Detection ID:** `81a07bc2-a1f2-4adc-9dbf-471afdc48fa4`
- **Image ID:** `81a07bc2-a1f2-4adc-9dbf-471afdc48fa4`

---

### Image 147: Jason1_20250926_034441_001.jpg [OK]
- **Database Classification:** doe (0.5082 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night IR but clear, deer alert at fence, no antlers = doe
- **Detection ID:** `b147b5a7-fa24-4fca-8f09-b12e4d24dd3c`
- **Image ID:** `b147b5a7-fa24-4fca-8f09-b12e4d24dd3c`

---

### Image 148: 270_JASON_00987.jpg [FAIL]
- **Database Classification:** doe (0.5082 confidence)
- **Audit Classification:** cattle
- **Status:** INCORRECT
- **Notes:** Night IR - CATTLE at fence, not deer! Larger body, different shape
- **Detection ID:** `5729c2e3-1638-491e-b237-20929689c40b`
- **Image ID:** `5729c2e3-1638-491e-b237-20929689c40b`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/5729c2e3-1638-491e-b237-20929689c40b/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "cattle", "reviewed_by": "Claude Code Batch 8"}'
  ```

---

### Image 149: Hayfield_20251011_182053_001.jpg [OK]
- **Database Classification:** doe (0.5082 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Dawn, deer and cattle at feeder, deer are does
- **Detection ID:** `1ee94ba4-b838-4fae-a049-27870cc9a942`
- **Image ID:** `1ee94ba4-b838-4fae-a049-27870cc9a942`

---

### Image 150: Sanctuary2_20251102_170527_001.jpg [FAIL]
- **Database Classification:** buck (0.5082 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear dusk, multiple does at feeder, no antlers
- **Detection ID:** `68915282-d5a5-4da7-9ec2-e7c345535172`
- **Image ID:** `68915282-d5a5-4da7-9ec2-e7c345535172`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/68915282-d5a5-4da7-9ec2-e7c345535172/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 8"}'
  ```

---

### Image 151: Sanctuary2_20251101_155809_001.jpg [FAIL]
- **Database Classification:** buck (0.5083 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear afternoon, deer in field, no antlers = doe
- **Detection ID:** `ba64c7ef-da4f-4a64-8fef-5fb5f601d4fc`
- **Image ID:** `ba64c7ef-da4f-4a64-8fef-5fb5f601d4fc`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/ba64c7ef-da4f-4a64-8fef-5fb5f601d4fc/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 8"}'
  ```

---

### Image 152: Sanctuary2_20251102_172737_001.jpg [FAIL]
- **Database Classification:** buck (0.5083 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear dusk, doe at feeder, no antlers
- **Detection ID:** `890e6d39-5b47-49f2-81c8-6e395b709968`
- **Image ID:** `890e6d39-5b47-49f2-81c8-6e395b709968`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/890e6d39-5b47-49f2-81c8-6e395b709968/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 8"}'
  ```

---

### Image 153: Hayfield_20251106_165958_001.jpg [OK]
- **Database Classification:** doe (0.5084 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Dusk, multiple deer and cattle visible
- **Detection ID:** `ee07556d-5bcf-41d2-9031-b8b3b8c4584b`
- **Image ID:** `ee07556d-5bcf-41d2-9031-b8b3b8c4584b`

---

### Image 154: Sanctuary2_20251104_175600_001.jpg [FAIL]
- **Database Classification:** buck (0.5084 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Dusk IR, doe at feeder, no antlers
- **Detection ID:** `6df5240f-f99a-4334-9bba-93dc866872e5`
- **Image ID:** `6df5240f-f99a-4334-9bba-93dc866872e5`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/6df5240f-f99a-4334-9bba-93dc866872e5/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 8"}'
  ```

---

### Image 155: HAYFIELD_11181.jpg [FAIL]
- **Database Classification:** buck (0.5085 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Dusk, deer and cattle at feeder, deer is doe
- **Detection ID:** `2db2b7fa-f221-470e-808b-a4e96f9ca353`
- **Image ID:** `2db2b7fa-f221-470e-808b-a4e96f9ca353`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/2db2b7fa-f221-470e-808b-a4e96f9ca353/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 8"}'
  ```

---

### Image 156: Hayfield_20251108_190806_001.jpg [OK]
- **Database Classification:** doe (0.5085 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night IR, two does visible
- **Detection ID:** `c609a9bf-c5f1-4e3a-8a14-e8931042c181`
- **Image ID:** `c609a9bf-c5f1-4e3a-8a14-e8931042c181`

---

### Image 157: Sanctuary2_20251106_093639_001.jpg [FAIL]
- **Database Classification:** buck (0.5085 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear morning, multiple does at feeder
- **Detection ID:** `34ffcea7-e475-4f23-ba09-1f0b24fdad23`
- **Image ID:** `34ffcea7-e475-4f23-ba09-1f0b24fdad23`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/34ffcea7-e475-4f23-ba09-1f0b24fdad23/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 8"}'
  ```

---

### Image 158: SANCTUARY_03113.jpg [OK]
- **Database Classification:** doe (0.5086 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Night IR, two does at feeder
- **Detection ID:** `fcebc4f5-b77d-4850-ba56-2118b300a21e`
- **Image ID:** `fcebc4f5-b77d-4850-ba56-2118b300a21e`

---

### Image 159: Sanctuary2_20251105_114622_001.jpg [OK]
- **Database Classification:** doe (0.5086 confidence)
- **Audit Classification:** doe
- **Status:** CORRECT
- **Notes:** Clear midday, doe in field, no antlers
- **Detection ID:** `02a47ef3-0682-4ccb-8d52-0d2beab4f29d`
- **Image ID:** `02a47ef3-0682-4ccb-8d52-0d2beab4f29d`

---

### Image 160: Sanctuary2_20251101_152609_001.jpg [FAIL]
- **Database Classification:** buck (0.5086 confidence)
- **Audit Classification:** doe
- **Status:** INCORRECT
- **Notes:** Clear afternoon, doe at feeder, no antlers
- **Detection ID:** `b39d8efd-68d0-44c2-b328-bb047211b322`
- **Image ID:** `b39d8efd-68d0-44c2-b328-bb047211b322`
- **Action Required:**
  ```bash
  curl -X PATCH "http://localhost:8001/api/detections/b39d8efd-68d0-44c2-b328-bb047211b322/correct" \
    -H "Content-Type: application/json" \
    -d '{"corrected_classification": "doe", "reviewed_by": "Claude Code Batch 8"}'
  ```

---

