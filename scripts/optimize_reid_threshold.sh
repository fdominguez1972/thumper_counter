#!/bin/bash
# REID Threshold Optimization Workflow
# This script guides you through analyzing and optimizing the REID_THRESHOLD

set -e  # Exit on error

API_URL="${API_URL:-http://localhost:8001}"
BACKEND_CONTAINER="${BACKEND_CONTAINER:-thumper_backend}"

echo "========================================="
echo "REID THRESHOLD OPTIMIZATION WORKFLOW"
echo "========================================="
echo

# Step 1: Run analysis
echo "[Step 1/5] Running threshold analysis..."
echo
docker-compose exec backend python3 /app/scripts/analyze_reid_threshold.py

echo
echo "========================================="
echo "[Step 2/5] Review Analysis Results"
echo "========================================="
echo
echo "Based on the analysis above, answer these questions:"
echo
read -p "1. How many deer profiles do you currently have? " current_profiles
read -p "2. What is your target profile count? (recommended: 30-50) " target_profiles
read -p "3. Current REID_THRESHOLD from analysis? (e.g., 0.60) " current_threshold

echo
echo "Current: $current_profiles profiles with threshold $current_threshold"
echo "Target:  $target_profiles profiles"
echo

# Calculate recommended threshold
if (( $(echo "$current_profiles > $target_profiles * 2" | bc -l) )); then
    if (( $(echo "$current_threshold >= 0.65" | bc -l) )); then
        recommended="0.55"
    elif (( $(echo "$current_threshold >= 0.60" | bc -l) )); then
        recommended="0.50"
    elif (( $(echo "$current_threshold >= 0.55" | bc -l) )); then
        recommended="0.45"
    else
        recommended=$(echo "$current_threshold - 0.05" | bc)
    fi

    echo "[RECOMMENDATION] Lower threshold from $current_threshold to $recommended"
    echo "This should reduce profile count closer to target."
elif (( $(echo "$current_profiles < $target_profiles / 2" | bc -l) )); then
    recommended=$(echo "$current_threshold + 0.05" | bc)
    echo "[RECOMMENDATION] Raise threshold from $current_threshold to $recommended"
    echo "This will allow more profile diversity."
else
    recommended="$current_threshold"
    echo "[OK] Current threshold seems reasonable"
fi

echo
read -p "Enter new REID_THRESHOLD to test (or press Enter for $recommended): " new_threshold
new_threshold="${new_threshold:-$recommended}"

echo
echo "========================================="
echo "[Step 3/5] Test New Threshold on Subset"
echo "========================================="
echo
echo "Will test REID_THRESHOLD=$new_threshold on 1,000 random images"
echo "This allows validation before full reprocess."
echo
read -p "Continue with test? (y/n) " confirm

if [[ "$confirm" != "y" ]]; then
    echo "Aborted."
    exit 0
fi

# Update .env file
echo "Updating .env file..."
if grep -q "^REID_THRESHOLD=" .env; then
    # Backup original
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

    # Update threshold
    sed -i "s/^REID_THRESHOLD=.*/REID_THRESHOLD=$new_threshold/" .env
    echo "Updated REID_THRESHOLD to $new_threshold in .env"
else
    echo "REID_THRESHOLD=$new_threshold" >> .env
    echo "Added REID_THRESHOLD=$new_threshold to .env"
fi

# Restart worker to pick up new threshold
echo "Restarting worker container..."
docker-compose restart worker

# Wait for worker to be ready
echo "Waiting for worker to restart..."
sleep 5

echo "Worker restarted with REID_THRESHOLD=$new_threshold"
echo

# Reset 1,000 random images
echo "Resetting 1,000 random images for test..."
docker-compose exec -T db psql -U deertrack deer_tracking <<SQL
-- Reset 1,000 random completed images
UPDATE images
SET processing_status = 'pending'
WHERE id IN (
    SELECT id FROM images
    WHERE processing_status = 'completed'
    ORDER BY RANDOM()
    LIMIT 1000
);

-- Clear deer assignments for those images' detections
UPDATE detections d
SET deer_id = NULL
WHERE image_id IN (
    SELECT id FROM images
    WHERE processing_status = 'pending'
);
SQL

echo "Reset 1,000 images to pending"
echo

# Queue for reprocessing
echo "Queuing test images for reprocessing..."
curl -s -X POST "$API_URL/api/processing/batch?limit=1000" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Queued: {data.get('queued_count', 0)} images\")
"

echo
echo "========================================="
echo "[Step 4/5] Monitor Test Progress"
echo "========================================="
echo
echo "Monitoring processing progress. Press Ctrl+C to stop monitoring."
echo

# Get baseline deer count
deer_before=$(docker-compose exec -T db psql -U deertrack deer_tracking -t -c "SELECT COUNT(*) FROM deer;")
deer_before=$(echo $deer_before | xargs)  # Trim whitespace

echo "Deer profiles before test: $deer_before"
echo

# Monitor processing
while true; do
    status=$(curl -s "$API_URL/api/processing/status")

    pending=$(echo "$status" | python3 -c "import sys,json; print(json.load(sys.stdin).get('pending', 0))")
    processing=$(echo "$status" | python3 -c "import sys,json; print(json.load(sys.stdin).get('processing', 0))")
    completed=$(echo "$status" | python3 -c "import sys,json; print(json.load(sys.stdin).get('completed', 0))")

    deer_now=$(docker-compose exec -T db psql -U deertrack deer_tracking -t -c "SELECT COUNT(*) FROM deer;")
    deer_now=$(echo $deer_now | xargs)

    deer_change=$((deer_now - deer_before))

    echo "[$(date +%H:%M:%S)] Pending: $pending | Processing: $processing | Completed: $completed | Deer: $deer_now (+$deer_change)"

    # Check if test complete
    if [ "$pending" -eq 0 ] && [ "$processing" -eq 0 ]; then
        echo
        echo "Test processing complete!"
        break
    fi

    sleep 10
done

echo
echo "========================================="
echo "[Step 5/5] Evaluate Test Results"
echo "========================================="
echo

# Get final deer count
deer_after=$(docker-compose exec -T db psql -U deertrack deer_tracking -t -c "SELECT COUNT(*) FROM deer;")
deer_after=$(echo $deer_after | xargs)

new_profiles=$((deer_after - deer_before))

echo "Results:"
echo "  Deer profiles before:  $deer_before"
echo "  Deer profiles after:   $deer_after"
echo "  New profiles created:  $new_profiles"
echo "  New profile rate:      $new_profiles per 1,000 images"
echo

# Evaluate results
expected_new=1  # 1 new profile per 1,000 images is good
if [ "$new_profiles" -lt 3 ]; then
    echo "[EXCELLENT] Low profile creation rate - threshold is working well!"
    recommendation="proceed"
elif [ "$new_profiles" -lt 10 ]; then
    echo "[GOOD] Acceptable profile creation rate"
    recommendation="proceed"
elif [ "$new_profiles" -lt 20 ]; then
    echo "[WARNING] Profile creation rate still high"
    recommendation="lower"
    suggested_threshold=$(echo "$new_threshold - 0.05" | bc)
else
    echo "[POOR] Profile creation rate too high"
    recommendation="lower"
    suggested_threshold=$(echo "$new_threshold - 0.10" | bc)
fi

echo

if [ "$recommendation" == "proceed" ]; then
    echo "RECOMMENDATION: Proceed with full reprocess using threshold $new_threshold"
    echo
    read -p "Reprocess all images with this threshold? (y/n) " proceed

    if [[ "$proceed" == "y" ]]; then
        echo
        echo "Starting full reprocess..."
        echo "This will:"
        echo "  1. Delete all existing deer profiles"
        echo "  2. Reset all images to pending"
        echo "  3. Reprocess all images with new threshold"
        echo
        read -p "Are you SURE? This cannot be undone. (yes/no) " confirm_full

        if [[ "$confirm_full" == "yes" ]]; then
            bash scripts/reprocess_all_images.sh
        else
            echo "Cancelled full reprocess"
        fi
    else
        echo "Skipped full reprocess"
    fi
else
    echo "RECOMMENDATION: Try lower threshold: $suggested_threshold"
    echo "Run this script again with the new threshold."
fi

echo
echo "========================================="
echo "THRESHOLD OPTIMIZATION COMPLETE"
echo "========================================="
echo
echo "Current configuration:"
echo "  REID_THRESHOLD: $new_threshold"
echo "  Deer Profiles: $deer_after"
echo
echo "To try a different threshold, run:"
echo "  bash scripts/optimize_reid_threshold.sh"
echo
