# Mature Bucks Review Guide
**Generated:** November 8, 2025
**Purpose:** Review and validate the 3 mature bucks identified during rut season

## Quick Access

**Frontend URL:** http://localhost:3000

**Navigation:**
1. Open frontend in browser
2. Click "Deer Gallery" in sidebar
3. Use filters: Sex = "Male"
4. Click on each buck profile to view details

## The Three Bucks

### Buck #1 (Primary Buck) - ID: 815100e5-e7ea-409a-b897-bea303b6a23b

**Profile Summary:**
- **Total Sightings:** 26
- **Mature Sightings:** 6 (most consistent mature buck)
- **Mid-Age Sightings:** 15
- **Young Sightings:** 2
- **Status:** UNNAMED (ready for you to name)

**Mature Detection Timeline:**
| Date       | Time     | Filename           | Confidence |
|------------|----------|--------------------|------------|
| 2023-10-10 | 12:20:51 | HAYFIELD_07225.jpg | 0.77       |
| 2023-10-10 | 12:39:18 | HAYFIELD_07231.jpg | 0.67       |
| 2023-10-13 | 12:24:13 | HAYFIELD_07352.jpg | 0.61       |
| 2023-10-17 | 00:13:17 | HAYFIELD_07495.jpg | 0.64       |
| 2023-10-21 | 00:11:18 | HAYFIELD_07643.jpg | 0.76       |
| 2024-02-05 | 01:12:12 | HAYFIELD_10256.jpg | 0.56       |

**Behavior Notes:**
- Consistent presence Oct 10-21 (peak rut)
- Mix of midday and midnight activity
- Returns in February 2024 (post-rut)
- Classification varies: 6 mature, 15 mid, 2 young
  - Suggests aging progression OR detection variability

**Review Actions:**
- [ ] View image gallery in frontend
- [ ] Verify it's the same buck in all 6 mature images
- [ ] Assign a name (e.g., "Big Boy", "Hayfield Dom", "October Buck")
- [ ] Add notes about antler characteristics
- [ ] Determine if mid-age sightings are same animal

---

### Buck #2 - ID: b34ba7ed-30bd-4f23-9c07-7552d74f16c0

**Profile Summary:**
- **Total Sightings:** 20
- **Mature Sightings:** 1
- **Mid-Age Sightings:** 17
- **Young Sightings:** 2
- **Status:** UNNAMED

**Mature Detection:**
| Date       | Time     | Filename           | Confidence |
|------------|----------|--------------------|------------|
| 2023-11-06 | 03:03:02 | HAYFIELD_08262.jpg | 0.80       |

**Behavior Notes:**
- Single mature detection (Nov 6, early morning)
- Primarily classified as mid-age (17 times)
- Suggests either:
  - Young buck maturing during season
  - Detection inconsistency (same mature buck)
  - Different individual (mostly mid-age with 1 false positive)

**Review Actions:**
- [ ] View the 1 mature detection image
- [ ] Compare to mid-age detection images
- [ ] Determine if this is truly a mature buck
- [ ] Consider reclassifying if needed
- [ ] Name if confirmed mature

---

### Buck #3 - ID: 3b2f9f77-d388-40d4-aa39-169441d2e606

**Profile Summary:**
- **Total Sightings:** 7
- **Mature Sightings:** 1
- **Mid-Age Sightings:** 6
- **Young Sightings:** 0
- **Status:** UNNAMED

**Mature Detection:**
| Date       | Time     | Filename           | Confidence |
|------------|----------|--------------------|------------|
| 2023-10-20 | 00:59:25 | HAYFIELD_07619.jpg | 0.82 (HIGHEST) |

**Behavior Notes:**
- Single mature detection (Oct 20, midnight)
- Highest confidence of all mature detections (0.82)
- Primarily mid-age classification (6 times)
- Limited sightings (7 total)

**Review Actions:**
- [ ] View the high-confidence mature image
- [ ] Compare to 6 mid-age images
- [ ] Assess if this is a distinct individual
- [ ] Determine true age class
- [ ] Name if confirmed as unique buck

---

## Additional Unassigned Mature Detections

**Found 8 mature buck detections WITHOUT Re-ID assignment:**

| Date       | Time     | Filename           | Confidence | Notes                    |
|------------|----------|--------------------|------------|--------------------------|
| 2023-10-11 | 12:34:17 | HAYFIELD_07300.jpg | 0.71       | Between Buck #1 sightings |
| 2023-10-19 | 00:48:25 | HAYFIELD_07588.jpg | 0.50       | Low confidence           |
| 2023-10-19 | 00:51:22 | HAYFIELD_07592.jpg | 0.65       | 3-min burst              |
| 2023-10-19 | 00:59:12 | HAYFIELD_07596.jpg | 0.51       | Low confidence           |
| 2023-10-20 | 00:37:04 | HAYFIELD_07611.jpg | 0.59       | Before Buck #3 sighting  |
| 2023-10-29 | 08:13:21 | HAYFIELD_07927.jpg | 0.50       | Late season              |
| 2023-11-05 | 00:17:12 | HAYFIELD_08243.jpg | 0.77       | Before Buck #2 sighting  |
| 2023-11-16 | 13:19:27 | HAYFIELD_08448.jpg | 0.67       | Mid-November             |
| 2023-11-21 | 13:03:50 | HAYFIELD_08571.jpg | 0.57       | Late November            |

**Possible Explanations:**
1. **Re-ID threshold too conservative** (0.85 similarity cutoff)
2. **Actually different bucks** (4+ mature bucks total)
3. **Poor feature quality** (angle, lighting, antlers blocking face)
4. **Photo bursts** (Oct 19: 3 detections in 11 minutes)

**Review Actions:**
- [ ] View all 8 unassigned images in frontend
- [ ] Compare to the 3 identified bucks
- [ ] Manually assign to existing profiles if matches found
- [ ] Create new deer profiles if truly unique
- [ ] Use batch correction tool for efficient editing

---

## Review Workflow

### Step 1: View Buck #1 (Primary Buck)
1. Frontend → Deer Gallery
2. Click on buck with 26 sightings
3. Review image gallery (look for 6 mature detections)
4. Click "Edit" to add name and notes
5. Check timeline to see activity pattern

### Step 2: View Buck #2
1. Find buck with 20 sightings
2. Review the single mature image (HAYFIELD_08262.jpg)
3. Compare to mid-age images
4. Determine if reclassification needed

### Step 3: View Buck #3
1. Find buck with 7 sightings
2. Review high-confidence mature image (HAYFIELD_07619.jpg)
3. Assess if distinct from Buck #1

### Step 4: Review Unassigned Detections
1. Frontend → Image Browser
2. Filter: Has Detections = Yes
3. Search for filenames above
4. View each detection's bounding box
5. Use correction dialog to assign deer_id if matches found

### Step 5: Batch Corrections (if needed)
1. Use frontend batch correction tool
2. Select multiple images of same buck
3. Assign to correct deer profile
4. Update classifications if needed

---

## Data Quality Questions

### Question 1: Is Buck #1 truly aging?
- **Evidence FOR:** 6 mature, 15 mid, 2 young detections
- **Evidence AGAINST:** Timeline shows mature in Oct, then mid/young later
- **Expected:** Deer don't get younger over time
- **Likely:** Detection inconsistency, not true aging

**Action:** Review images to determine if all 26 sightings are same animal

### Question 2: Are Bucks #2 and #3 actually mature?
- **Evidence FOR:** Model classified them as mature at least once
- **Evidence AGAINST:** Mostly classified as mid-age
- **Possible:** Borderline mature bucks (2.5 years old)

**Action:** Visual inspection to confirm antler development

### Question 3: How many TOTAL unique mature bucks?
- **Re-ID says:** 3 unique bucks
- **Unassigned detections:** 8 additional
- **Possible range:** 3-11 unique mature bucks

**Action:** Manual review of all 16 mature images to count distinct individuals

### Question 4: Should Re-ID threshold be lowered?
- **Current:** 0.85 similarity (conservative)
- **Result:** Only 50% of mature detections assigned
- **Alternative:** 0.80 or 0.75 threshold

**Action:** Test lower threshold after visual confirmation

---

## Expected Outcomes

### Likely Scenario
- **1-2 truly mature bucks** (dominant animals)
- **Several mid-age bucks** (2.5 years, borderline classification)
- **Detection variability** explains multiple classifications per animal

### Best Case Scenario
- **3+ unique mature bucks** confirmed
- **All identifiable** via Re-ID with adjusted threshold
- **Clear territory patterns** emerge

### Worst Case Scenario
- **Detection errors** (false positives on mature classification)
- **Re-ID failures** (unable to match same animal)
- **Need manual tracking** instead of automated Re-ID

---

## Naming Suggestions

If confirmed as distinct mature bucks, consider names based on:

**Temporal:**
- "October Dom" (dominant buck during October rut)
- "Early Season" / "Late Season"

**Location:**
- "Hayfield Boss"
- "Hayfield Regular"

**Physical:**
- "Big 8" / "Wide 10" (if antlers visible)
- "Dark Face" / "Gray Face"

**Behavior:**
- "Midnight Runner" (mostly nighttime)
- "Noon Buck" (midday sightings)

**Simple:**
- "Buck #1", "Buck #2", "Buck #3"
- "Alpha", "Beta", "Gamma"

---

## Frontend Features to Use

### Deer Profile Page
- **Image Gallery:** All detection crops for this deer
- **Timeline Chart:** Activity by hour/day/week/month
- **Location Map:** Movement between camera sites (future)
- **Edit Fields:** Name, status, notes

### Image Browser
- **Filters:** Date range, location, classification
- **Lightbox:** Full image with detection overlays
- **Click Box:** Jump to deer profile

### Correction Tools
- **Single Edit:** Fix one detection at a time
- **Batch Edit:** Update multiple detections (up to 1000)

---

## SQL Queries for Reference

### Get all detections for a specific buck:
```sql
SELECT i.filename, i.timestamp, d.classification, d.confidence
FROM detections d
JOIN images i ON d.image_id = i.id
WHERE d.deer_id = '815100e5-e7ea-409a-b897-bea303b6a23b'
ORDER BY i.timestamp;
```

### Find all mature detections:
```sql
SELECT i.filename, i.timestamp, d.confidence, d.deer_id
FROM detections d
JOIN images i ON d.image_id = i.id
WHERE d.classification = 'mature'
ORDER BY i.timestamp;
```

### Count detections by classification for a buck:
```sql
SELECT classification, COUNT(*) as count
FROM detections
WHERE deer_id = '815100e5-e7ea-409a-b897-bea303b6a23b'
GROUP BY classification;
```

---

## Next Steps After Review

1. **Name the confirmed bucks** - Give them meaningful identifiers
2. **Assign unassigned detections** - Reduce orphan count
3. **Adjust Re-ID threshold** - If too conservative
4. **Export training data** - Use confirmed bucks to improve model
5. **Generate final report** - Updated with manual validation

**Status:** Ready for your review!
**Access:** http://localhost:3000
**Start with:** Buck #1 (most sightings, highest confidence)
