# Reprocessing Schedule & Strategy
## Automated Maintenance for Thumper Counter

**Created:** November 15, 2025
**GPU:** RTX 4080 Super (16GB VRAM, dedicated)
**Current Throughput:** 840 images/min @ concurrency=32, upgrading to 64

---

## PERIODIC REPROCESSING SCHEDULE

### Recommended Schedule

**WEEKLY REPROCESSING** - Every Sunday at 2:00 AM
- **Why Weekly:** Model improvements, bug fixes, threshold adjustments accumulate
- **Why 2 AM:** Low system usage, won't interfere with daily ops
- **Duration:** ~70 minutes for full 59k image dataset @ 840 img/min
- **Impact:** Ensures all images benefit from latest improvements

**Implementation:**
```bash
# Add to crontab
0 2 * * 0 /mnt/i/projects/thumper_counter/scripts/weekly_reprocess.sh
```

### When to Trigger IMMEDIATE Reprocessing

Reprocess immediately when:

1. **New Model Deployed** - YOLOv8 detection or classification model updated
2. **REID_THRESHOLD Changed** - Significant threshold adjustment (>0.05 delta)
3. **Bug Fixed** - Critical detection/classification bug discovered and fixed
4. **Major Dataset Import** - >10k new images added at once
5. **Sex Mapping Fixed** - Like the buck/doe fix from Nov 15

### When to SKIP Reprocessing

Don't reprocess for:

- Minor configuration changes (logging, monitoring)
- Frontend updates (UI changes only)
- Database schema changes (migrations handle these)
- Small threshold tweaks (<0.05 delta)
- Adding <1000 new images (process incrementally instead)

---

## DEER NAMING STRATEGY

### Current State (Pre-Reprocessing)
- 165 deer profiles (before nov 15 full reprocess)
- Expectation: Will consolidate to 20-50 unique deer after enhanced Re-ID

### When to Start Naming

**STABLE COUNT CRITERIA:**
1. **Count <50 deer** - Manageable for manual naming
2. **7-day stability** - Profile count changes <5% week-over-week
3. **Assignment rate >70%** - Most detections assigned to existing profiles
4. **No major model changes planned** - System is "production stable"

### Naming Readiness Checklist

Run this query weekly to check:
```sql
-- Weekly deer profile stats
SELECT
  COUNT(*) as total_deer,
  COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as new_this_week,
  ROUND(100.0 * COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') / COUNT(*), 1) as new_percent
FROM deer;

-- If new_percent < 5% for 2 consecutive weeks AND total_deer < 50 → READY TO NAME
```

### Naming Conventions

When ready to name (count is stable):

**Disney-Inspired Naming Rules:**
1. **Bucks:** Classic Disney characters (Bambi, Thumper, Mickey, etc.)
2. **Does:** Disney princesses/heroines (Belle, Elsa, Ariel, etc.)
3. **Fawns:** Disney sidekicks (Flounder, Pascal, Meeko, etc.)
4. **Unknown:** Nature-themed (Willow, River, Storm, etc.)

**Implementation:**
- Use frontend UI to assign names
- Add notes about distinguishing features
- Upload best photo as primary

---

## PERFORMANCE OPTIMIZATION

### Current Setup
- Concurrency: 32 threads (Nov 12-14)
- GPU Utilization: 71%
- VRAM Usage: 4.4GB / 16.4GB
- Throughput: 840 images/min

### Optimization (Nov 15)
- Concurrency: 64 threads (DOUBLED)
- Expected GPU: 90-95%
- Expected VRAM: 8-10GB / 16.4GB
- Expected Throughput: 1,400-1,600 images/min
- Estimated Full Dataset: 37-42 minutes (was 70 minutes)

### Future Optimization Potential
- Batch size increase (currently 16, could test 32)
- Multiple worker containers (horizontal scaling)
- Queue prioritization (high-quality images first)

---

## MONITORING & ALERTS

### Daily Health Check (Automated)
```bash
# Check deer profile stability
docker-compose exec db psql -U deertrack deer_tracking -c "
SELECT
  DATE(created_at) as date,
  COUNT(*) as new_deer_count
FROM deer
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;"

# If new_deer_count > 10 per day consistently → Re-ID threshold too high
```

### Weekly Report (Manual Review)
1. Check deer profile count trend
2. Review assignment rate (target >70%)
3. Check for duplicate deer (manual review of photos)
4. Verify GPU utilization logs
5. Review failed image count

---

## QUICK COMMANDS

### Trigger Manual Reprocessing
```bash
# Full dataset reprocess with new models/fixes
docker-compose exec backend python3 /app/scripts/reprocess_with_new_model.py --turbo --clear-mode all

# Then queue images (automatic with continuous_queue.sh running)
curl -X POST "http://localhost:8001/api/processing/batch?limit=10000"
```

### Check Naming Readiness
```bash
# Deer profile count
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT COUNT(*) as total_deer FROM deer;"

# Weekly growth rate
docker-compose exec db psql -U deertrack deer_tracking -c \
  "SELECT COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') as new_this_week FROM deer;"
```

### Monitor Reprocessing Progress
```bash
curl -s http://localhost:8001/api/processing/status | python3 -m json.tool
```

---

## DECISION TREE

```
New Model Deployed?
├─ YES → Immediate full reprocess
└─ NO → Continue...

REID Threshold Changed >0.05?
├─ YES → Immediate full reprocess
└─ NO → Continue...

Bug Fixed in Detection?
├─ YES → Immediate full reprocess
└─ NO → Continue...

Weekly Schedule (Sunday 2AM)?
├─ YES → Automated full reprocess
└─ NO → Continue...

Otherwise → Process new images incrementally only
```

---

## SUCCESS METRICS

### Week 1 Post-Enhancement
- Deer profiles: <50 (down from 165)
- Assignment rate: >70%
- GPU utilization: >90%
- Processing speed: >1,200 images/min

### Month 1 (Stable Production)
- Deer profiles: <60 (slow growth as new deer appear)
- Assignment rate: >75%
- Named deer: 100% (all profiles have Disney names)
- Weekly reprocessing: Automated and successful

---

**Next Review:** After tonight's full reprocessing completes
**Owner:** Development Team / Claude Code
**Status:** ACTIVE
