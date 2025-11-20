#!/bin/bash
# Assignment Rate Monitoring Script
# Feature 009: Monitor impact of threshold change (0.70 -> 0.60)
# Runs every 12 hours for 7 days to track assignment rate improvements

# Configuration
LOG_FILE="/mnt/i/projects/thumper_counter/logs/assignment_rate_monitoring.log"
CSV_FILE="/mnt/i/projects/thumper_counter/logs/assignment_rate_data.csv"
PROJECT_DIR="/mnt/i/projects/thumper_counter"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Initialize CSV with header if it doesn't exist
if [ ! -f "$CSV_FILE" ]; then
    echo "timestamp,total_detections,assigned,unassigned,assignment_rate_percent,threshold,notes" > "$CSV_FILE"
fi

# Get current timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
ISO_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Get current threshold from worker
CURRENT_THRESHOLD=$(docker-compose exec -T worker printenv REID_THRESHOLD 2>/dev/null || echo "unknown")

# Query database for assignment rate
QUERY_RESULT=$(docker-compose exec -T db psql -U deertrack deer_tracking -t -A -F',' -c "
SELECT
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE deer_id IS NOT NULL) as assigned,
  COUNT(*) FILTER (WHERE deer_id IS NULL) as unassigned,
  ROUND(100.0 * COUNT(*) FILTER (WHERE deer_id IS NOT NULL) / COUNT(*), 2) as rate
FROM detections;
" 2>&1)

# Check if query succeeded
if [ $? -ne 0 ]; then
    echo "[$TIMESTAMP] [ERROR] Failed to query database" | tee -a "$LOG_FILE"
    echo "$ISO_TIMESTAMP,0,0,0,0.00,$CURRENT_THRESHOLD,ERROR: Database query failed" >> "$CSV_FILE"
    exit 1
fi

# Parse results
TOTAL=$(echo "$QUERY_RESULT" | cut -d',' -f1 | tr -d ' ')
ASSIGNED=$(echo "$QUERY_RESULT" | cut -d',' -f2 | tr -d ' ')
UNASSIGNED=$(echo "$QUERY_RESULT" | cut -d',' -f3 | tr -d ' ')
RATE=$(echo "$QUERY_RESULT" | cut -d',' -f4 | tr -d ' ')

# Validate data
if [ -z "$TOTAL" ] || [ "$TOTAL" = "0" ]; then
    echo "[$TIMESTAMP] [ERROR] Invalid query result: $QUERY_RESULT" | tee -a "$LOG_FILE"
    exit 1
fi

# Calculate changes from baseline (60.35% from Feature 010)
BASELINE=60.35
CHANGE=$(awk "BEGIN {printf \"%.2f\", $RATE - $BASELINE}")

# Determine trend
if (( $(awk "BEGIN {print ($CHANGE > 0)}") )); then
    TREND="UP"
    TREND_SYMBOL="+"
elif (( $(awk "BEGIN {print ($CHANGE < 0)}") )); then
    TREND="DOWN"
    TREND_SYMBOL=""
else
    TREND="STABLE"
    TREND_SYMBOL="="
fi

# Log to file
echo "[$TIMESTAMP] Assignment Rate: $RATE% ($TREND_SYMBOL$CHANGE% vs baseline) | Total: $TOTAL | Assigned: $ASSIGNED | Unassigned: $UNASSIGNED | Threshold: $CURRENT_THRESHOLD" | tee -a "$LOG_FILE"

# Append to CSV
echo "$ISO_TIMESTAMP,$TOTAL,$ASSIGNED,$UNASSIGNED,$RATE,$CURRENT_THRESHOLD,Threshold change monitoring (7 days)" >> "$CSV_FILE"

# Generate report summary
echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "ASSIGNMENT RATE MONITORING REPORT" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "Timestamp: $TIMESTAMP" | tee -a "$LOG_FILE"
echo "Threshold: $CURRENT_THRESHOLD (changed from 0.70 to 0.60)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Current Metrics:" | tee -a "$LOG_FILE"
echo "  Total Detections: $TOTAL" | tee -a "$LOG_FILE"
echo "  Assigned:         $ASSIGNED" | tee -a "$LOG_FILE"
echo "  Unassigned:       $UNASSIGNED" | tee -a "$LOG_FILE"
echo "  Assignment Rate:  $RATE%" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Comparison to Baseline (Feature 010):" | tee -a "$LOG_FILE"
echo "  Baseline Rate:    $BASELINE%" | tee -a "$LOG_FILE"
echo "  Current Rate:     $RATE%" | tee -a "$LOG_FILE"
echo "  Change:           $TREND_SYMBOL$CHANGE%" | tee -a "$LOG_FILE"
echo "  Trend:            $TREND" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Show last 5 entries from CSV for trend
echo "Recent History (last 5 measurements):" | tee -a "$LOG_FILE"
echo "----------------------------------------" | tee -a "$LOG_FILE"
if [ -f "$CSV_FILE" ]; then
    tail -6 "$CSV_FILE" | head -5 | awk -F',' '{printf "  %s: %s%% (%s/%s assigned)\n", $1, $5, $3, $2}' | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# Alert if rate is significantly different
if (( $(awk "BEGIN {print ($CHANGE > 5)}") )); then
    echo "[ALERT] Assignment rate UP by ${CHANGE}% - Threshold change working!" | tee -a "$LOG_FILE"
elif (( $(awk "BEGIN {print ($CHANGE < -5)}") )); then
    echo "[WARNING] Assignment rate DOWN by ${CHANGE}% - Investigate!" | tee -a "$LOG_FILE"
else
    echo "[INFO] Assignment rate stable (${TREND_SYMBOL}${CHANGE}%)" | tee -a "$LOG_FILE"
fi

echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Exit successfully
exit 0
