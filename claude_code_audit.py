#!/usr/bin/env python3
"""
Classification Audit using Claude Code's Vision Capabilities
No external dependencies - uses Claude Code directly via file-based workflow
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Configuration
BATCH_SIZE = 20
API_URL = "http://localhost:8001"

def get_batch_data(offset: int, limit: int) -> List[Dict]:
    """Get batch data from database"""
    cmd = f"""docker-compose exec -T db psql -U deertrack deer_tracking -c "
SELECT d.id, i.filename, d.classification, ROUND(d.confidence::numeric, 4), i.id
FROM detections d
JOIN images i ON d.image_id = i.id
WHERE d.classification IN ('buck', 'doe', 'fawn')
  AND d.confidence >= 0.50 AND d.confidence < 0.60
ORDER BY d.confidence ASC
LIMIT {limit} OFFSET {offset};
" -t -A"""

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    lines = [l.strip() for l in result.stdout.split('\n') if l.strip() and '|' in l and 'id' not in l.lower()]

    detections = []
    for i, line in enumerate(lines, 1):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 5:
            detections.append({
                'num': offset + i,
                'detection_id': parts[0],
                'filename': parts[1],
                'db_class': parts[2],
                'confidence': float(parts[3]),
                'image_id': parts[4]
            })

    return detections

def download_images(detections: List[Dict], output_dir: Path) -> Dict[str, Path]:
    """Download all images for batch"""
    output_dir.mkdir(exist_ok=True)
    image_paths = {}

    print(f"\n[INFO] Downloading {len(detections)} images...")
    for det in detections:
        image_path = output_dir / f"{det['num']:03d}_{det['filename']}"
        cmd = f'curl -s {API_URL}/api/static/images/{det["image_id"]} -o "{image_path}"'
        result = subprocess.run(cmd, shell=True)

        if result.returncode == 0 and image_path.exists():
            image_paths[det['detection_id']] = image_path
            print(f"  [OK] Image {det['num']}: {det['filename']}")
        else:
            print(f"  [FAIL] Image {det['num']}: {det['filename']} - download failed")

    return image_paths

def create_audit_instructions(detections: List[Dict], image_paths: Dict[str, Path], batch_num: int) -> str:
    """Create instructions file for Claude Code to process"""

    instructions = f"""# AUDIT BATCH {batch_num} - CLASSIFICATION REVIEW

You are reviewing {len(detections)} deer trail camera images for classification accuracy.

## Your Task

For EACH image below:
1. I will show you the image
2. Review the database classification vs. what you see
3. Determine: CORRECT, INCORRECT, or UNCERTAIN
4. Provide reasoning

## Classification Guide

**BUCK:** Male deer with visible antlers (any size, even small nubs)
**DOE:** Female deer with NO antlers (smooth head)
**FAWN:** Young deer (small size, spots if summer)
**UNCERTAIN:** Cannot determine due to:
  - Too dark/night IR with poor visibility
  - Animal too distant/small
  - Partial view (only legs/body, head not visible)
  - No deer visible in frame
  - Motion blur

## Important Notes
- Even SMALL antler nubs = buck (not doe)
- Does sometimes have ear tufts (NOT antlers)
- IR/night images can be challenging
- Species confusion: pigs have snouts, cattle are larger

---

## Images to Review

"""

    for det in detections:
        image_path = image_paths.get(det['detection_id'])
        if not image_path:
            continue

        instructions += f"""
### Image {det['num']}: {det['filename']}
- **Database Classification:** {det['db_class']}
- **Confidence:** {det['confidence']:.4f} (LOW - needs verification)
- **Detection ID:** {det['detection_id']}
- **Image ID:** {det['image_id']}
- **Image Path:** {image_path}

**Please review this image and respond with:**
```
IMAGE_{det['num']}_RESULT: [CORRECT|INCORRECT|UNCERTAIN]
AUDIT_CLASS: [buck|doe|fawn|pig|cattle|none]
REASONING: [Your detailed explanation]
```

---
"""

    instructions += """

## After Reviewing All Images

Please create a summary JSON file with your results in this exact format:

```json
{
  "batch_num": BATCH_NUM,
  "audit_date": "YYYY-MM-DD",
  "auditor": "Claude Code Vision Analysis",
  "results": [
    {
      "num": IMAGE_NUM,
      "detection_id": "DETECTION_ID",
      "filename": "FILENAME",
      "db_class": "DATABASE_CLASS",
      "confidence": CONFIDENCE_VALUE,
      "image_id": "IMAGE_ID",
      "audit_class": "YOUR_CLASSIFICATION",
      "status": "CORRECT|INCORRECT|UNCERTAIN",
      "notes": "Your reasoning"
    },
    ...
  ]
}
```

Save this to: audit_batch_BATCH_NUM_results.json
"""

    return instructions

def generate_report(batch_num: int, results_file: Path):
    """Generate markdown report from JSON results"""

    if not results_file.exists():
        print(f"[ERROR] Results file not found: {results_file}")
        return

    with open(results_file, 'r') as f:
        data = json.load(f)

    results = data['results']

    # Calculate statistics
    stats = {
        'total': len(results),
        'correct': sum(1 for r in results if r['status'] == 'CORRECT'),
        'incorrect': sum(1 for r in results if r['status'] == 'INCORRECT'),
        'uncertain': sum(1 for r in results if r['status'] == 'UNCERTAIN'),
    }

    accuracy = stats['correct'] / (stats['correct'] + stats['incorrect']) * 100 if (stats['correct'] + stats['incorrect']) > 0 else 0

    # Generate report
    report = f"""# Classification Audit Results - Batch {batch_num}

**Audit Date:** {data.get('audit_date', datetime.now().strftime('%Y-%m-%d'))}
**Auditor:** {data.get('auditor', 'Claude Code Vision Analysis')}
**Method:** Direct vision analysis via Claude Code
**Sample Size:** {len(results)} images

## Executive Summary

**Overall Accuracy:** {accuracy:.1f}% ({stats['correct']} correct out of {stats['correct']+stats['incorrect']} determinable)
**Corrections Needed:** {stats['incorrect']} images
**Uncertain:** {stats['uncertain']} images

### Statistics
- **Total Images:** {stats['total']}
- **Correct:** {stats['correct']} ({stats['correct']/stats['total']*100:.1f}%)
- **Incorrect:** {stats['incorrect']} ({stats['incorrect']/stats['total']*100:.1f}%)
- **Uncertain:** {stats['uncertain']} ({stats['uncertain']/stats['total']*100:.1f}%)

---

## Detailed Results

"""

    corrections = []

    for r in results:
        status_label = "OK" if r['status'] == 'CORRECT' else "FAIL" if r['status'] == 'INCORRECT' else "WARN"

        report += f"""### Image {r['num']}: {r['filename']} [{status_label}]
- **Database Classification:** {r['db_class']} ({r['confidence']:.4f} confidence)
- **Audit Classification:** {r['audit_class']}
- **Status:** {r['status']}
- **Notes:** {r['notes']}
- **Detection ID:** `{r['detection_id']}`
- **Image ID:** `{r['image_id']}`
"""

        if r['status'] == 'INCORRECT':
            corrections.append(r)
            report += f"""- **Action Required:**
  ```bash
  curl -X PATCH "{API_URL}/api/detections/{r['detection_id']}/correct" \\
    -H "Content-Type: application/json" \\
    -d '{{"corrected_classification": "{r['audit_class']}", "reviewed_by": "Claude Code Batch {batch_num}"}}'
  ```
"""

        report += "\n---\n\n"

    # Save report
    report_file = Path(f"CLASSIFICATION_AUDIT_BATCH_{batch_num}.md")
    report_file.write_text(report)
    print(f"\n[INFO] Report saved: {report_file}")

    # Generate correction script
    if corrections:
        script = f"""#!/bin/bash
# Batch {batch_num} Corrections - Generated by Claude Code Audit
API_URL="{API_URL}"

"""
        for i, corr in enumerate(corrections, 1):
            script += f"""echo "[{i}/{len(corrections)}] Correcting {corr['filename']} ({corr['db_class']}->{corr['audit_class']})"
curl -X PATCH "${{API_URL}}/api/detections/{corr['detection_id']}/correct" \\
  -H "Content-Type: application/json" \\
  -d '{{"corrected_classification": "{corr['audit_class']}", "reviewed_by": "Claude Code Batch {batch_num}"}}' \\
  && echo " [OK]" || echo " [FAILED]"

"""

        script_file = Path(f"apply_batch_{batch_num}_corrections.sh")
        script_file.write_text(script)
        subprocess.run(['chmod', '+x', str(script_file)], shell=True)
        print(f"[INFO] Correction script saved: {script_file}")
        print(f"\n[INFO] To apply corrections, run: bash {script_file}")

    print(f"\n[INFO] Batch {batch_num} audit complete!")
    print(f"  Accuracy: {accuracy:.1f}%")
    print(f"  Corrections needed: {len(corrections)}")

def main():
    """Main workflow"""
    import sys

    print("=" * 70)
    print("CLASSIFICATION AUDIT - CLAUDE CODE VISION ANALYSIS")
    print("=" * 70)

    # Get batch number
    if len(sys.argv) > 1:
        try:
            batch_num = int(sys.argv[1])
        except:
            print("[ERROR] Invalid batch number. Usage: python3 claude_code_audit.py <batch_num>")
            sys.exit(1)
    else:
        batch_num = 4  # Default

    offset = (batch_num - 1) * BATCH_SIZE

    print(f"\n[INFO] Starting Batch {batch_num}")
    print(f"[INFO] Offset: {offset}, Limit: {BATCH_SIZE}")

    # Step 1: Get detections from database
    print(f"\n[STEP 1/4] Fetching detections from database...")
    detections = get_batch_data(offset, BATCH_SIZE)

    if not detections:
        print(f"[ERROR] No detections found at offset {offset}")
        sys.exit(1)

    print(f"[OK] Found {len(detections)} detections")

    # Step 2: Download images
    print(f"\n[STEP 2/4] Downloading images...")
    output_dir = Path(f"audit_batch_{batch_num}_images")
    image_paths = download_images(detections, output_dir)
    print(f"[OK] Downloaded {len(image_paths)}/{len(detections)} images")

    # Step 3: Create audit instructions
    print(f"\n[STEP 3/4] Creating audit instructions...")
    instructions = create_audit_instructions(detections, image_paths, batch_num)

    instructions_file = Path(f"AUDIT_BATCH_{batch_num}_INSTRUCTIONS.md")
    instructions_file.write_text(instructions)
    print(f"[OK] Instructions saved: {instructions_file}")

    # Step 4: Wait for Claude Code to process
    print(f"\n[STEP 4/4] Ready for Claude Code review!")
    print(f"\n{'=' * 70}")
    print(f"NEXT STEPS:")
    print(f"{'=' * 70}")
    print(f"1. Review the instructions file: {instructions_file}")
    print(f"2. Images are in: {output_dir}/")
    print(f"3. Ask Claude Code to review each image and create results JSON")
    print(f"4. Run: python3 claude_code_audit.py --generate-report {batch_num}")
    print(f"{'=' * 70}")

    # Save metadata for report generation
    metadata = {
        'batch_num': batch_num,
        'offset': offset,
        'limit': BATCH_SIZE,
        'detections': detections,
        'output_dir': str(output_dir),
        'instructions_file': str(instructions_file)
    }

    metadata_file = Path(f"batch_{batch_num}_metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n[INFO] Metadata saved: {metadata_file}")

def generate_report_mode():
    """Generate report from existing results"""
    import sys

    if len(sys.argv) < 3:
        print("[ERROR] Usage: python3 claude_code_audit.py --generate-report <batch_num>")
        sys.exit(1)

    batch_num = int(sys.argv[2])
    results_file = Path(f"audit_batch_{batch_num}_results.json")

    print(f"\n[INFO] Generating report for Batch {batch_num}...")
    generate_report(batch_num, results_file)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--generate-report':
        generate_report_mode()
    else:
        main()
