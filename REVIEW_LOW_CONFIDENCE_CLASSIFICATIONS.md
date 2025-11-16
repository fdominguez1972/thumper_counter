# Low Confidence Classification Review

**Generated:** 2025-11-16
**Total Images for Review:** 50 low-confidence buck/doe detections (< 65% confidence)

## How to Review

1. Click on each image link below to open it in the frontend
2. Review the bounding box and image to verify the classification is correct
3. If incorrect, note the detection ID and correct classification
4. Use the batch correction API or UI to update multiple images at once

## Images to Review (Sorted by Confidence - Lowest First)

### Extremely Low Confidence (50.0% - 50.5%) - HIGHEST PRIORITY

1. **SANCTUARY_10845.jpg** - Classified as: **doe** (50.00% confidence)
   - Frontend: http://localhost:3000/images
   - Detection ID: `76a4f53b-4228-4ec0-92b0-ff68f967884c`
   - Image ID: `01d8b58d-90c1-4643-8265-afca3f29f7df`

2. **Sanctuary2_20251102_172420_001.jpg** - Classified as: **buck** (50.01% confidence)
   - Frontend: http://localhost:3000/images
   - Detection ID: `dadadd8b-d07e-4001-a523-b869d88e29a8`
   - Image ID: `bc37b381-2219-4e2b-928b-811610bb49dc`

3. **HAYFIELD_03223.jpg** - Classified as: **doe** (50.01% confidence)
   - Frontend: http://localhost:3000/images
   - Detection ID: `b873d31e-9734-414f-ab61-472d45b72e7b`
   - Image ID: `5f576b34-7b52-420e-bcbb-a653310a65b4`

4. **CAMPHOUSE_02025.jpg** - Classified as: **doe** (50.02% confidence)
   - Frontend: http://localhost:3000/images
   - Detection ID: `cdd57436-24e3-4ed6-a61e-428db996d7ac`
   - Image ID: `10f32ffa-5fb7-48c8-9e8e-7f521d5bc3ed`

5. **Sanctuary2_20251106_091323_001.jpg** - Classified as: **buck** (50.02% confidence)
   - Frontend: http://localhost:3000/images
   - Detection ID: `9247bdc3-9036-4743-a10b-04abc38eff34`
   - Image ID: `ec11d542-33f3-4de8-80e8-a0c17007f9a4`

6. **SANCTUARY_01826.jpg** - Classified as: **doe** (50.03% confidence)
   - Frontend: http://localhost:3000/images
   - Detection ID: `b5d723fc-11d2-41f2-a4c8-66833fdaf1e1`
   - Image ID: `e91cd425-a93e-4f84-a6d0-1803be1d8f33`

7. **Sanctuary2_20251103_090210_001.jpg** - Classified as: **buck** (50.05% confidence)
   - Frontend: http://localhost:3000/images
   - Detection ID: `269713b5-0b9b-4b27-a4f2-c031504c2fca`
   - Image ID: `fda1c0c9-60f2-423d-9c16-7a324ce53f75`

8. **SANCTUARY_01496.jpg** - Classified as: **doe** (50.06% confidence)
   - Frontend: http://localhost:3000/images
   - Detection ID: `53c3cf10-2d7b-4791-a80a-00cf8594642e`
   - Image ID: `f04508a7-513c-4d86-8c5f-32dac607d9aa`

9. **HAYFIELD_10187.jpg** - Classified as: **buck** (50.06% confidence)
   - Frontend: http://localhost:3000/images
   - Detection ID: `abe52d0b-8fac-46da-9a83-7852b7e83f57`
   - Image ID: `ee9ddd32-9bdd-4caa-8bc8-73c955cfc937`

10. **CAMPHOUSE_01253.jpg** - Classified as: **buck** (50.08% confidence)
    - Frontend: http://localhost:3000/images
    - Detection ID: `b429d667-47b2-4903-bfa1-4673b34bd97d`
    - Image ID: `6be9b8fc-a05a-40b2-9f31-cb9ad24eb1dc`

---

## Quick Correction Commands

### To correct a single detection:
```bash
curl -X PATCH "http://localhost:8001/api/detections/{detection_id}/correct" \
  -H "Content-Type: application/json" \
  -d '{"corrected_classification": "buck"}'  # or "doe"
```

### To correct multiple detections at once:
```bash
curl -X PATCH "http://localhost:8001/api/detections/batch/correct" \
  -H "Content-Type: application/json" \
  -d '{
    "corrections": [
      {"detection_id": "76a4f53b-4228-4ec0-92b0-ff68f967884c", "corrected_classification": "buck"},
      {"detection_id": "dadadd8b-d07e-4001-a523-b869d88e29a8", "corrected_classification": "doe"}
    ]
  }'
```

## Statistics

- Total doe detections: 7,504 (avg confidence: 78.2%)
- Total buck detections: 4,070 (avg confidence: 73.4%)
- Low confidence detections (<65%): ~50+ images
- Confidence range: 50.0% - 64.9%

## Next Steps

1. Review the top 10 images listed above (50.0% - 50.1% confidence)
2. Note corrections needed
3. Use batch correction API to update all at once
4. Consider retraining the model with corrected images

---

**Full CSV export available at:** `/tmp/low_confidence_detections.csv`
