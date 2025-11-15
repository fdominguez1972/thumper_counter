# Assignment Rate Monitoring Setup

**Date:** November 15, 2025
**Feature:** 009 Re-ID Enhancement - Threshold Optimization
**Purpose:** Monitor impact of threshold change from 0.70 to 0.60

---

## Overview

Automated monitoring system to track assignment rate improvements after adjusting REID_THRESHOLD from 0.70 to 0.60 (recommended value for enhanced Re-ID).

**Monitoring Period:** 7 days (November 15-22, 2025)
**Frequency:** Every 12 hours (00:00 and 12:00 UTC)
**Baseline:** 60.35% assignment rate (Feature 010)

---

## Files Created

### 1. Monitor Script (`scripts/monitor_assignment_rate.sh`)

Queries database every 12 hours and records:
- Total detections
- Assigned detections (with deer_id)
- Unassigned detections (deer_id IS NULL)
- Assignment rate percentage
- Current threshold setting
- Comparison to baseline (60.35%)

**Output Files:**
- **Log:** `logs/assignment_rate_monitoring.log` (human-readable reports)
- **CSV:** `logs/assignment_rate_data.csv` (structured data for analysis)

### 2. Setup Script (`scripts/setup_monitoring_cron.sh`)

Installs cron job with:
- Schedule: `0 */12 * * *` (every 12 hours)
- Duration: 7 days
- Initial baseline measurement

---

## Cron Job Details

**Schedule:**
```cron
0 */12 * * * /mnt/i/projects/thumper_counter/scripts/monitor_assignment_rate.sh
```

**Runs at:**
- 00:00 UTC (7:00 PM CST previous day)
- 12:00 UTC (7:00 AM CST)

**Total Measurements:** 14 data points over 7 days

---

## Usage

### View Current Status

```bash
# View latest report
tail -50 /mnt/i/projects/thumper_counter/logs/assignment_rate_monitoring.log

# View CSV data
cat /mnt/i/projects/thumper_counter/logs/assignment_rate_data.csv
```

### Manual Run

```bash
# Run monitoring script manually
bash /mnt/i/projects/thumper_counter/scripts/monitor_assignment_rate.sh
```

### View Cron Status

```bash
# Check installed cron jobs
crontab -l

# View cron execution log
tail -f /mnt/i/projects/thumper_counter/logs/cron.log
```

### Remove Monitoring (before 7 days)

```bash
# Edit crontab
crontab -e

# Delete the line containing 'monitor_assignment_rate.sh'
# Save and exit
```

---

## Initial Baseline Measurement

**Date:** November 15, 2025 07:59:59 UTC

```
Total Detections:   11,570
Assigned:           6,982 (60.35%)
Unassigned:         4,588 (39.65%)
Threshold:          0.60
Change vs Baseline: 0.00% (STABLE)
```

**Note:** This is the same as Feature 010 baseline because the threshold change just happened. We expect improvement as new detections are processed with the 0.60 threshold.

---

## Expected Results

### Short-term (24-48 hours)
- Assignment rate should remain stable or slightly increase
- New detections processed with 0.60 threshold
- Fewer new deer profiles created for existing deer

### Mid-term (3-5 days)
- Assignment rate expected to increase to 65-70%
- Improved matching for enhanced embeddings (135/165 deer)
- Reduction in unassigned detections

### End of Monitoring (7 days)
- Clear trend visible in CSV data
- Decision point: Keep 0.60, adjust to 0.55, or revert to 0.40

---

## CSV Data Format

```csv
timestamp,total_detections,assigned,unassigned,assignment_rate_percent,threshold,notes
2025-11-15T13:59:59Z,11570,6982,4588,60.35,0.60,Threshold change monitoring (7 days)
```

**Fields:**
- `timestamp`: ISO 8601 format (UTC)
- `total_detections`: Total detection count
- `assigned`: Detections with deer_id assigned
- `unassigned`: Detections without deer_id
- `assignment_rate_percent`: (assigned/total) * 100
- `threshold`: Current REID_THRESHOLD value
- `notes`: Context for this measurement

---

## Analysis After 7 Days

After the monitoring period completes, analyze the data:

### 1. Calculate Average Improvement

```bash
# Get all assignment rates
awk -F',' 'NR>1 {sum+=$5; count++} END {print "Average:", sum/count"%"}' \
  logs/assignment_rate_data.csv
```

### 2. Visualize Trend

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load CSV
df = pd.read_csv('logs/assignment_rate_data.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Plot assignment rate over time
plt.figure(figsize=(12, 6))
plt.plot(df['timestamp'], df['assignment_rate_percent'], marker='o')
plt.axhline(y=60.35, color='r', linestyle='--', label='Baseline (Feature 010)')
plt.xlabel('Date')
plt.ylabel('Assignment Rate (%)')
plt.title('Assignment Rate Monitoring - Feature 009 Threshold Change')
plt.legend()
plt.grid(True)
plt.savefig('assignment_rate_trend.png')
```

### 3. Decision Matrix

Based on results:

| Avg Rate | Decision | Action |
|----------|----------|--------|
| 65-70% | SUCCESS | Keep threshold 0.60 |
| 62-64% | MODERATE | Monitor another week |
| 60-61% | MINIMAL | Consider lowering to 0.55 |
| <60% | REGRESSION | Revert to 0.40 baseline |

---

## Troubleshooting

### Cron Job Not Running

```bash
# Check cron service is running
sudo service cron status

# Check system logs
grep CRON /var/log/syslog | tail -20

# Verify crontab is installed
crontab -l | grep monitor_assignment_rate
```

### Script Errors

```bash
# Check error log
cat /mnt/i/projects/thumper_counter/logs/cron.log

# Run script manually to see errors
bash -x /mnt/i/projects/thumper_counter/scripts/monitor_assignment_rate.sh
```

### Docker Containers Not Running

```bash
# Check container status
docker-compose ps

# Restart if needed
cd /mnt/i/projects/thumper_counter
./docker-up.sh
```

---

## Monitoring Alerts

The script automatically alerts on significant changes:

**Alert Types:**
- `[ALERT]` - Rate increased >5% (threshold change working!)
- `[WARNING]` - Rate decreased >5% (investigate issue)
- `[INFO]` - Rate stable within ±5%

---

## Integration with Feature 012

This monitoring data will inform the next phase:

**Feature 012: Triplet Loss Fine-tuning**
- Use optimal threshold (0.60 or adjusted) as baseline
- Target: Additional 5-10% improvement
- Expected final rate: 70-75%

---

## Summary

**Status:** ACTIVE
- Cron job installed: ✓
- Initial baseline recorded: ✓ (60.35%)
- 7-day monitoring started: ✓
- Next measurement: November 15, 2025 at 20:00 UTC

**Manual Checks:**
```bash
# View latest measurement
tail -30 logs/assignment_rate_monitoring.log

# Check cron is running
crontab -l | grep monitor_assignment_rate
```

**Files to Review:**
- `logs/assignment_rate_monitoring.log` - Detailed reports
- `logs/assignment_rate_data.csv` - Structured data
- `logs/cron.log` - Cron execution log

---

**Document Version:** 1.0
**Last Updated:** November 15, 2025
**Monitoring Ends:** November 22, 2025
