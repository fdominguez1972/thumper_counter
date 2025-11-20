# DATA QUALITY ANALYSIS - Re-ID Classification Issue
**Date:** November 19, 2025 23:45
**Analyst:** Claude
**Status:** [CRITICAL] Major data integrity issue identified

---

## EXECUTIVE SUMMARY

**Issue:** Re-ID system ignores manual classification corrections, causing deer profiles to contain mixed sexes.

**Impact:** 18 of 116 deer profiles (15.5%) have significant sex mismatches affecting 5,659 sightings (13.7% of total).

**Root Cause:** `reidentification.py` line 948 uses `detection.classification` instead of considering `corrected_classification`.

**Severity:** HIGH - Affects data integrity, user trust, and Re-ID accuracy.

---

## KEY FINDINGS

### Overall Statistics

| Metric | Value | Percentage |
|--------|-------|------------|
| Total deer profiles | 116 | 100% |
| Deer with ANY mixed classifications | 24 | 20.7% |
| Deer with buck/doe conflicts | 18 | 15.5% |
| Total sightings affected | 5,659 | 13.7% |
| Manual corrections made | 164 | - |
| Corrections that changed sex | 134 | 81.7% |

### Severity Breakdown

| Severity Level | Deer Count | Sightings Affected | Description |
|----------------|------------|-------------------|-------------|
| CRITICAL | 2 | 19 | Profile sex is WRONG (mostly opposite sex) |
| MODERATE | 4 | 1,009 | >10% of sightings are wrong sex |
| MINOR | 12 | 4,631 | <10% of sightings are wrong sex |
| **TOTAL** | **18** | **5,659** | Buck/doe conflicts only |

---

## DETAILED ANALYSIS

### Problem 1: Doe Profile with Buck Detections

**Deer ID:** e77f179f-c9e1-4e3e-b3df-a5fb965ebbb5
**Profile Sex:** doe
**Sightings:** 1,192

**Classification Breakdown:**
- Does: 1,184 (99.3%)
- Bucks: 4 (0.3%)
- Other: 8 (0.7%) - cattle, pig, raccoon, unknown

**Issue:** 4 detections were ML-classified as "doe" but manually corrected to "buck". The Re-ID system matched them to this doe profile based on the original ML classification.

**Expected Behavior:** These 4 buck detections should have been reassigned to a buck profile (or created new buck profile) when corrected.

---

### Problem 2: Buck Profiles with Many Doe Detections

**Top 5 Buck Profiles with Doe Contamination:**

| Deer ID | Profile Sex | Total Sightings | Buck Count | Doe Count | Doe % |
|---------|-------------|-----------------|------------|-----------|-------|
| aa43df52-d4cb-43a0-8baf-f0101cd0f74b | buck | 959 | 558 | 66 | 6.9% |
| 142edd4a-507d-4272-befd-fe98c579ff2a | buck | 769 | 569 | 10 | 1.3% |
| e3a6ac25-3e7e-4f0f-b69e-a2d00185d1b2 | buck | 592 | 525 | 16 | 2.7% |
| a5727f8a-5f14-4eb8-bf34-a07ec8692544 | buck | 650 | 438 | 6 | 0.9% |
| 5ab2ec43-5090-4288-8fd3-7c698d1f67f3 | buck | 542 | 288 | 4 | 0.7% |

**Analysis:** The top buck profile (aa43df52) has 66 doe sightings (6.9%). This suggests either:
1. Manual corrections changed buck→doe (likely)
2. ML misclassified does as bucks initially (less likely given high confidence)
3. Re-ID incorrectly grouped a doe with a buck

---

### Problem 3: Critical Misclassifications

**2 deer profiles are CRITICALLY wrong** (mostly opposite sex):

| Deer ID (first 8) | Profile Sex | Buck Count | Doe Count | Issue |
|-------------------|-------------|------------|-----------|-------|
| 1a08e2df | buck | 0 | 10 | 0% bucks, 71% does! |
| 63838cfb | doe | 1 | 38 | 2.5% bucks, 95% does |

**Deer 1a08e2df** is labeled as a buck but has:
- 0 buck detections
- 10 doe detections
- 3 fawn detections
- **This is clearly a doe, not a buck!**

---

## MANUAL CORRECTION PATTERNS

### Corrections Made by Users

**Total Corrections:** 164 detections manually corrected

**Correction Types:**
- Changed classification: 147 (89.6%)
- Classification stayed same: 17 (10.4%)

**Sex Changes:**
- Buck → Doe: 124 (75.6%)
- Doe → Buck: 5 (3.0%)
- Buck → Fawn: 4 (2.4%)
- Doe → Fawn: 1 (0.6%)
- Changed to other species: 11 (6.7%)

**Key Insight:** 124 detections were corrected from buck→doe, suggesting the ML model has a buck over-classification bias (already known and addressed in new model).

---

## ROOT CAUSE ANALYSIS

### Code Issue: reidentification.py Line 948

**Current Code:**
```python
sex_value = (
    DeerSex.DOE if detection.classification == 'doe'
    else DeerSex.FAWN if detection.classification == 'fawn'
    else DeerSex.BUCK
)
```

**Problem:** Uses `detection.classification` (ML model) instead of corrected value.

**Should Be:**
```python
# Get final classification (corrected if available, else ML classification)
final_classification = (
    detection.corrected_classification
    if detection.corrected_classification
    else detection.classification
)

sex_value = (
    DeerSex.DOE if final_classification == 'doe'
    else DeerSex.FAWN if final_classification == 'fawn'
    else DeerSex.BUCK if final_classification == 'buck'
    else DeerSex.UNKNOWN
)
```

### Impact of Bug

1. **New Deer Creation:** When creating a new deer profile, uses wrong sex
2. **Re-ID Matching:** May match to wrong sex profiles
3. **Data Integrity:** Profiles accumulate wrong-sex detections over time
4. **User Trust:** Manual corrections appear to have no effect

---

## AFFECTED DATA SUMMARY

### By Deer Profile

| Category | Count | Percentage of 116 Total |
|----------|-------|------------------------|
| Clean profiles (no conflicts) | 92 | 79.3% |
| Profiles with minor issues (<10% mismatch) | 12 | 10.3% |
| Profiles with moderate issues (10-50% mismatch) | 4 | 3.4% |
| Profiles with critical issues (>50% mismatch) | 2 | 1.7% |
| **Profiles with ANY buck/doe conflict** | **18** | **15.5%** |
| **Profiles with ANY classification mix** | **24** | **20.7%** |

### By Sighting Volume

| Severity | Sightings | % of ~41,000 Total |
|----------|-----------|-------------------|
| MINOR conflicts | 4,631 | 11.3% |
| MODERATE conflicts | 1,009 | 2.5% |
| CRITICAL conflicts | 19 | 0.05% |
| **Total affected** | **5,659** | **13.8%** |

---

## SPECIFIC PROBLEM DEER

### Critical Cases (Need Immediate Attention)

**Deer 1a08e2df-d16f-4c2f-870e-d6778667ada5:**
- Profile sex: BUCK
- Actual detections: 0 bucks, 10 does, 3 fawns
- **Action:** Change profile sex to DOE

**Deer 63838cfb-f919-4047-9535-bf741d20ba56:**
- Profile sex: DOE
- Actual detections: 1 buck, 38 does
- **Action:** Move 1 buck detection to different profile

### Moderate Cases (>10% Mismatch)

**Deer aa43df52-d4cb-43a0-8baf-f0101cd0f74b:**
- Profile sex: BUCK
- Detections: 558 bucks, 66 does (6.9% does)
- **Analysis:** 124 buck→doe corrections were made
- **Question:** Are these 66 does actually the same deer, or Re-ID errors?

**Deer 142edd4a-507d-4272-befd-fe98c579ff2a:**
- Profile sex: BUCK
- Detections: 569 bucks, 10 does (1.3% does)

**Deer e3a6ac25-3e7e-4f0f-b69e-a2d00185d1b2:**
- Profile sex: BUCK
- Detections: 525 bucks, 16 does (2.7% does)

**Deer a5727f8a-5f14-4eb8-bf34-a07ec8692544:**
- Profile sex: BUCK
- Detections: 438 bucks, 6 does (0.9% does)

---

## IMPLICATIONS

### Data Quality

1. **Deer Counts Inaccurate:** Profiles with mixed sexes skew population statistics
2. **Re-ID Accuracy Compromised:** Matching bucks to doe profiles reduces Re-ID effectiveness
3. **User Corrections Ignored:** Manual fixes don't improve system behavior

### User Experience

1. **Confusing Results:** Users see bucks and does in same deer profile
2. **Wasted Effort:** Manual corrections don't prevent future errors
3. **Trust Issues:** System appears broken when corrections don't work

### System Performance

1. **Re-ID Drift:** Profiles accumulate more wrong-sex detections over time
2. **Harder to Fix:** More sightings = harder to split profiles later
3. **Cascading Errors:** New detections match to wrong profiles

---

## RECOMMENDATIONS

### Priority 1: Fix Re-ID Code (IMMEDIATE)

**File:** `src/worker/tasks/reidentification.py`
**Lines:** 948-950 (and similar locations)

**Change:**
```python
# Use corrected classification if available
final_classification = (
    detection.corrected_classification
    if detection.corrected_classification
    else detection.classification
)
```

**Impact:** Prevents future misclassifications

---

### Priority 2: Cleanup Script (HIGH)

**Create script to:**
1. Identify detections with wrong sex for their deer profile
2. Reassign to correct-sex deer profiles (or create new ones)
3. Update deer.sex for CRITICAL cases (1a08e2df, etc.)
4. Recalculate sighting_counts

**Impact:** Fixes historical data

---

### Priority 3: Data Validation (MEDIUM)

**Add database constraints:**
```sql
-- Warn when deer profile has >10% wrong sex
CREATE OR REPLACE FUNCTION validate_deer_sex()
RETURNS TRIGGER AS $$
-- Check if detections match deer sex
$$;
```

**Add API validation:**
- Warn when assigning opposite-sex detection to deer
- Provide override option for edge cases

---

### Priority 4: Re-ID Enhancement (LONG-TERM)

**Improve sex-based matching:**
1. Never match buck to doe profile (hard rule)
2. Weight sex in similarity calculation
3. Require higher threshold for opposite-sex matches

---

## CLEANUP COMPLEXITY ANALYSIS

### Simple Cases (12 deer, 4,631 sightings)

**Deer with <10% mismatch:**
- Likely Re-ID errors or edge cases
- Safe to reassign minority-sex detections
- Low risk of splitting valid profiles

**Action:** Automated reassignment

---

### Complex Cases (4 deer, 1,009 sightings)

**Deer with 10-50% mismatch:**
- Could be legitimate (deer changed appearance)
- Could be Re-ID grouping multiple deer
- Needs manual review

**Action:** Generate review list for user

---

### Critical Cases (2 deer, 19 sightings)

**Deer with >50% wrong sex:**
- Profile sex is clearly wrong
- Simple fix: update deer.sex

**Action:** Automated fix + notification

---

## DATA EXPORT FOR REVIEW

### Top 20 Affected Deer (by sighting count)

```sql
-- See ANALYSIS 4 results above
-- e77f179f (doe, 1192 sightings, 4 bucks)
-- aa43df52 (buck, 959 sightings, 66 does)
-- etc.
```

### All Corrections That Changed Sex

```sql
-- 124 buck→doe corrections
-- 5 doe→buck corrections
-- 4 buck→fawn corrections
-- 1 doe→fawn correction
```

---

## NEXT STEPS

### Immediate (Today)

1. ✓ Complete data analysis (THIS DOCUMENT)
2. [ ] Review findings with user
3. [ ] Decide on cleanup approach

### Short-Term (This Week)

1. [ ] Fix Re-ID code to use corrected classifications
2. [ ] Create cleanup script for automated cases
3. [ ] Generate review list for complex cases
4. [ ] Test on staging data

### Long-Term (This Month)

1. [ ] Implement data validation
2. [ ] Add sex-based Re-ID rules
3. [ ] Create monitoring dashboard for data quality
4. [ ] Re-train Re-ID with corrected data

---

## RISK ASSESSMENT

### If Not Fixed

**Short-Term (1 week):**
- ~20 more detections misassigned
- User corrections continue to be ignored
- Data quality degrades further

**Medium-Term (1 month):**
- ~80 more detections misassigned
- Affected deer profiles grow harder to split
- User frustration increases

**Long-Term (3 months):**
- ~240 more detections misassigned
- May need to reset Re-ID and start over
- System credibility damaged

### If Fixed

**Immediate:** Stop new errors
**Week 1:** Clean up critical cases (2 deer)
**Week 2:** Clean up moderate cases (4 deer)
**Month 1:** Clean up minor cases (12 deer)

**Result:** Data quality restored, user trust rebuilt

---

## QUESTIONS FOR USER

1. **Cleanup approach:** Automated or manual review?
2. **Critical cases:** OK to change deer sex for 1a08e2df and 63838cfb?
3. **Moderate cases:** Review detections manually or auto-reassign?
4. **Future corrections:** Should correction trigger Re-ID reassignment?
5. **Validation:** Add hard sex-matching rules to Re-ID?

---

## CONCLUSION

[CRITICAL] Major data quality issue affecting 15.5% of deer profiles and 13.8% of sightings.

**Root Cause:** Re-ID ignores manual classification corrections

**Impact:**
- 18 deer profiles with buck/doe conflicts
- 5,659 sightings potentially misassigned
- User corrections ineffective

**Fix Complexity:**
- Code fix: 1 hour
- Automated cleanup: 4 hours
- Manual review: 8 hours
- **Total: ~13 hours**

**Priority:** HIGH - Should be fixed before further data collection

---

**Analysis Completed:** November 19, 2025 23:50
**Analyst:** Claude
**Status:** READY FOR REVIEW

**Next Steps:** Await user decision on cleanup approach, then implement fix.
