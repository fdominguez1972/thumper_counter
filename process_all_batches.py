#!/usr/bin/env python3
import subprocess
import json
import sys

def process_batch_range(start, end):
    total_corrections = 0
    total_reviewed = 0
    total_cattle = 0
    total_buck_to_doe = 0
    total_uncertain = 0
    
    for batch_num in range(start, end + 1):
        print(f"Processing batch {batch_num}...")
        
        # Prepare batch
        subprocess.run(["python3", "direct_filesystem_audit.py", str(batch_num)], 
                      capture_output=True, text=True)
        
        # Read metadata
        try:
            with open(f"batch_{batch_num}_metadata.txt", "r") as f:
                lines = f.readlines()
        except:
            print(f"  [SKIP] No metadata file for batch {batch_num}")
            continue
        
        # Parse detections
        detections = []
        for line in lines:
            if "|" in line and not line.startswith("BATCH"):
                parts = line.strip().split("|")
                if len(parts) >= 5:
                    detections.append({
                        "id": parts[1],
                        "filename": parts[2],
                        "classification": parts[3],
                        "confidence": parts[4],
                        "path": parts[5] if len(parts) > 5 else ""
                    })
        
        if not detections:
            continue
            
        total_reviewed += len(detections)
        print(f"  Found {len(detections)} detections")
        
    print(f"\n=== SUMMARY ===")
    print(f"Total batches: {end - start + 1}")
    print(f"Total reviewed: {total_reviewed}")
    
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: process_all_batches.py <start> <end>")
        sys.exit(1)
    
    start = int(sys.argv[1])
    end = int(sys.argv[2])
    process_batch_range(start, end)
