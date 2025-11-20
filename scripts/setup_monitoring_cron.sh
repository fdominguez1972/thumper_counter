#!/bin/bash
# Setup Cron Job for Assignment Rate Monitoring
# Feature 009: Monitor threshold change impact for 7 days
# Runs every 12 hours starting now

SCRIPT_PATH="/mnt/i/projects/thumper_counter/scripts/monitor_assignment_rate.sh"
CRON_LOG="/mnt/i/projects/thumper_counter/logs/cron.log"

# Ensure logs directory exists
mkdir -p /mnt/i/projects/thumper_counter/logs

echo "[INFO] Setting up assignment rate monitoring cron job"
echo "[INFO] Frequency: Every 12 hours for 7 days"
echo "[INFO] Script: $SCRIPT_PATH"

# Calculate end date (7 days from now)
END_DATE=$(date -d '+7 days' '+%Y-%m-%d')
START_DATE=$(date '+%Y-%m-%d')

echo "[INFO] Monitoring period: $START_DATE to $END_DATE"

# Create temporary cron job
TEMP_CRON=$(mktemp)

# Get existing crontab (if any)
crontab -l > "$TEMP_CRON" 2>/dev/null || true

# Remove any existing assignment rate monitoring jobs
sed -i '/monitor_assignment_rate.sh/d' "$TEMP_CRON"

# Add new cron job - runs every 12 hours (at 00:00 and 12:00)
echo "# Feature 009: Assignment Rate Monitoring (expires $END_DATE)" >> "$TEMP_CRON"
echo "0 */12 * * * $SCRIPT_PATH >> $CRON_LOG 2>&1" >> "$TEMP_CRON"

# Install new crontab
crontab "$TEMP_CRON"

# Clean up
rm "$TEMP_CRON"

echo "[OK] Cron job installed successfully"
echo ""
echo "Cron schedule:"
crontab -l | grep -A1 "Feature 009"

echo ""
echo "[INFO] The job will run:"
echo "  - Every 12 hours (00:00 and 12:00 UTC)"
echo "  - For 7 days (until $END_DATE)"
echo "  - Logs: $CRON_LOG"
echo "  - CSV data: /mnt/i/projects/thumper_counter/logs/assignment_rate_data.csv"
echo ""
echo "[INFO] To manually run now:"
echo "  bash $SCRIPT_PATH"
echo ""
echo "[INFO] To view monitoring logs:"
echo "  tail -f /mnt/i/projects/thumper_counter/logs/assignment_rate_monitoring.log"
echo ""
echo "[INFO] To remove cron job before 7 days:"
echo "  crontab -e  # Then delete the line with 'monitor_assignment_rate.sh'"
echo ""

# Run immediately to establish baseline
echo "[INFO] Running initial measurement..."
bash "$SCRIPT_PATH"

echo ""
echo "[OK] Monitoring setup complete!"
