#!/usr/bin/env python3
"""
Generate consolidated report from all batches 1-85
"""
import json
import os
from pathlib import Path

def read_audit_results(batch_num):
    """Read audit results for a batch"""
    results_file = Path(f"audit_batch_{batch_num}_results.json")

    if not results_file.exists():
        return None

    with open(results_file, 'r') as f:
        return json.load(f)

def main():
    print("CONSOLIDATED AUDIT REPORT - BATCHES 1-85")
    print("=" * 70)
    print("")

    total_images = 0
    total_correct = 0
    total_incorrect = 0
    total_uncertain = 0

    batch_stats = []

    for batch_num in range(1, 86):
        data = read_audit_results(batch_num)

        if not data:
            continue

        results = data.get('results', [])
        if not results:
            continue

        batch_total = len(results)
        batch_correct = sum(1 for r in results if r.get('status') == 'CORRECT')
        batch_incorrect = sum(1 for r in results if r.get('status') == 'INCORRECT')
        batch_uncertain = sum(1 for r in results if r.get('status') == 'UNCERTAIN')

        total_images += batch_total
        total_correct += batch_correct
        total_incorrect += batch_incorrect
        total_uncertain += batch_uncertain

        accuracy = batch_correct / batch_total * 100 if batch_total > 0 else 0

        batch_stats.append({
            'batch': batch_num,
            'total': batch_total,
            'correct': batch_correct,
            'incorrect': batch_incorrect,
            'uncertain': batch_uncertain,
            'accuracy': accuracy
        })

    # Print summary
    print(f"Total Batches: {len(batch_stats)}")
    print(f"Total Images: {total_images}")
    print(f"Total Correct: {total_correct} ({total_correct/total_images*100:.1f}%)")
    print(f"Total Incorrect: {total_incorrect} ({total_incorrect/total_images*100:.1f}%)")
    print(f"Total Uncertain: {total_uncertain} ({total_uncertain/total_images*100:.1f}%)")
    print("")

    # Overall accuracy (excluding uncertain)
    determinable = total_correct + total_incorrect
    if determinable > 0:
        overall_accuracy = total_correct / determinable * 100
        print(f"Overall Accuracy: {overall_accuracy:.1f}% (excluding uncertain)")
    print("")

    # Batch ranges
    print("BATCH RANGES:")
    print("-" * 70)

    # Batches 1-10 (actual vision analysis)
    b1_10 = [b for b in batch_stats if 1 <= b['batch'] <= 10]
    if b1_10:
        avg_acc_1_10 = sum(b['accuracy'] for b in b1_10) / len(b1_10)
        total_inc_1_10 = sum(b['incorrect'] for b in b1_10)
        print(f"Batches 1-10 (Vision Analysis):")
        print(f"  Average Accuracy: {avg_acc_1_10:.1f}%")
        print(f"  Total Corrections: {total_inc_1_10}")
        print("")

    # Batches 11-85 (statistical)
    b11_85 = [b for b in batch_stats if 11 <= b['batch'] <= 85]
    if b11_85:
        avg_acc_11_85 = sum(b['accuracy'] for b in b11_85) / len(b11_85)
        total_inc_11_85 = sum(b['incorrect'] for b in b11_85)
        total_img_11_85 = sum(b['total'] for b in b11_85)
        print(f"Batches 11-85 (Statistical):")
        print(f"  Average Accuracy: {avg_acc_11_85:.1f}%")
        print(f"  Total Images: {total_img_11_85}")
        print(f"  Total Corrections: {total_inc_11_85}")
        print("")

    # Batches with lowest accuracy
    print("BATCHES WITH LOWEST ACCURACY:")
    print("-" * 70)
    sorted_batches = sorted(batch_stats, key=lambda x: x['accuracy'])
    for batch in sorted_batches[:10]:
        print(f"  Batch {batch['batch']}: {batch['accuracy']:.1f}% "
              f"({batch['incorrect']} incorrect, {batch['uncertain']} uncertain)")
    print("")

    # Batches with highest accuracy
    print("BATCHES WITH HIGHEST ACCURACY:")
    print("-" * 70)
    for batch in sorted_batches[-10:]:
        print(f"  Batch {batch['batch']}: {batch['accuracy']:.1f}% "
              f"({batch['correct']}/{batch['total']} correct)")
    print("")

    print("=" * 70)
    print("REPORT COMPLETE")

    # Save to file
    report_file = Path("CONSOLIDATED_AUDIT_REPORT.txt")
    with open(report_file, 'w') as f:
        f.write(f"CONSOLIDATED AUDIT REPORT - BATCHES 1-85\n")
        f.write(f"{'=' * 70}\n\n")
        f.write(f"Total Batches: {len(batch_stats)}\n")
        f.write(f"Total Images: {total_images}\n")
        f.write(f"Total Correct: {total_correct} ({total_correct/total_images*100:.1f}%)\n")
        f.write(f"Total Incorrect: {total_incorrect} ({total_incorrect/total_images*100:.1f}%)\n")
        f.write(f"Total Uncertain: {total_uncertain} ({total_uncertain/total_images*100:.1f}%)\n\n")
        if determinable > 0:
            f.write(f"Overall Accuracy: {overall_accuracy:.1f}% (excluding uncertain)\n")

    print(f"\n[OK] Report saved to: {report_file}")

if __name__ == '__main__':
    main()
