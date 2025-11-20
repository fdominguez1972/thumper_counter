#!/bin/bash
# Process all batches 11-85 - generate reports and apply corrections
# Generated: 2025-11-16

echo "PROCESSING ALL BATCHES 11-85"
echo "======================================"
echo ""

total_batches=0
total_corrections=0

for batch in {11..85}; do
    echo "[INFO] Processing Batch $batch..."

    # Generate report
    python3 generate_report.py $batch > /dev/null 2>&1

    if [ $? -eq 0 ]; then
        ((total_batches++))

        # Check if correction script exists
        if [ -f "apply_batch_${batch}_corrections.sh" ]; then
            # Count corrections in the script
            corrections=$(grep -c "Correcting" "apply_batch_${batch}_corrections.sh" || echo "0")

            if [ "$corrections" -gt 0 ]; then
                echo "  [FOUND] $corrections corrections needed"
                ((total_corrections += corrections))

                # Optionally apply corrections (commented out for safety)
                # bash "apply_batch_${batch}_corrections.sh"
            else
                echo "  [OK] No corrections needed"
            fi
        else
            echo "  [OK] No corrections needed"
        fi
    else
        echo "  [FAIL] Could not process batch $batch"
    fi

    echo ""
done

echo "======================================"
echo "SUMMARY:"
echo "  Batches processed: $total_batches"
echo "  Total corrections: $total_corrections"
echo ""
echo "To apply all corrections, uncomment the bash line"
echo "in this script and run again."
