#!/usr/bin/env python3
"""
Real-time ASCII progress monitor for image processing.

Displays live progress with:
- Overall progress bar
- Status breakdown (completed, pending, processing, failed)
- Throughput rate (images/minute)
- ETA to completion
- Detection statistics

Usage:
  python3 monitor_processing.py
  python3 monitor_processing.py --refresh 2  # Update every 2 seconds

Created: 2025-11-11
Author: Claude Code
"""
import os
import sys
import time
import argparse
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional

API_BASE = os.getenv('API_BASE_URL', 'http://localhost:8001')


def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name == 'posix' else 'cls')


def draw_bar(percent: float, width: int = 50) -> str:
    """
    Draw ASCII progress bar.

    Args:
        percent: Percentage complete (0-100)
        width: Bar width in characters

    Returns:
        ASCII bar string
    """
    filled = int(width * percent / 100)
    empty = width - filled
    return f"[{'=' * filled}{'.' * empty}] {percent:5.1f}%"


def draw_horizontal_bar(label: str, count: int, total: int, width: int = 40) -> str:
    """
    Draw horizontal bar for status breakdown.

    Args:
        label: Status label
        count: Count for this status
        total: Total count
        width: Bar width

    Returns:
        Formatted bar string
    """
    if total == 0:
        percent = 0
    else:
        percent = (count / total) * 100

    filled = int(width * count / total) if total > 0 else 0
    bar = '#' * filled + '.' * (width - filled)

    return f"{label:12s} {bar} {count:6,d} ({percent:5.1f}%)"


def get_status() -> Optional[Dict]:
    """Fetch processing status from API."""
    try:
        response = requests.get(f"{API_BASE}/api/processing/status", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return None


def format_duration(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def main():
    """Main monitoring loop."""
    parser = argparse.ArgumentParser(description='Real-time processing progress monitor')
    parser.add_argument('--refresh', type=int, default=3, help='Refresh interval in seconds (default: 3)')
    parser.add_argument('--no-clear', action='store_true', help='Do not clear screen (append mode)')
    args = parser.parse_args()

    print("Starting monitor...")
    time.sleep(1)

    # Track start time and previous completed count for throughput
    start_time = datetime.now()
    prev_completed = 0
    prev_time = start_time

    iteration = 0

    try:
        while True:
            iteration += 1

            # Fetch status
            status = get_status()

            if not status:
                print("[ERROR] Failed to fetch status from API")
                time.sleep(args.refresh)
                continue

            # Clear screen (unless --no-clear)
            if not args.no_clear:
                clear_screen()

            # Header
            print("=" * 70)
            print("DEER TRACKING - REAL-TIME PROCESSING MONITOR")
            print("=" * 70)
            print()
            print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Model: corrected_final_buck_doe (mAP50=0.851, 85.1% accuracy)")
            print()

            # Extract stats (API returns 'total', 'completed', etc. not 'total_images')
            total = status.get('total', status.get('total_images', 0))
            completed = status.get('completed', status.get('completed_images', 0))
            pending = status.get('pending', status.get('pending_images', 0))
            processing = status.get('processing', status.get('processing_images', 0))
            failed = status.get('failed', status.get('failed_images', 0))
            completion_rate = status.get('completion_rate', 0.0)

            # Main progress bar
            print("[OVERALL PROGRESS]")
            print()
            print(draw_bar(completion_rate, width=60))
            print()
            print(f"  Completed: {completed:6,d} / {total:6,d} images")
            print()

            # Status breakdown with horizontal bars
            print("[STATUS BREAKDOWN]")
            print()
            print(draw_horizontal_bar("Completed", completed, total, width=40))
            print(draw_horizontal_bar("Pending", pending, total, width=40))
            print(draw_horizontal_bar("Processing", processing, total, width=40))
            print(draw_horizontal_bar("Failed", failed, total, width=40))
            print()

            # Calculate throughput
            now = datetime.now()
            elapsed_total = (now - start_time).total_seconds()
            elapsed_since_last = (now - prev_time).total_seconds()

            if elapsed_total > 0 and completed > 0:
                throughput_overall = completed / (elapsed_total / 60)  # images/minute
            else:
                throughput_overall = 0

            if elapsed_since_last > 0:
                throughput_recent = (completed - prev_completed) / (elapsed_since_last / 60)
            else:
                throughput_recent = 0

            # Update tracking
            prev_completed = completed
            prev_time = now

            # Performance metrics
            print("[PERFORMANCE]")
            print()
            print(f"  Throughput (Overall):  {throughput_overall:6.0f} images/min ({throughput_overall/60:5.1f} images/sec)")
            print(f"  Throughput (Recent):   {throughput_recent:6.0f} images/min ({throughput_recent/60:5.1f} images/sec)")
            print(f"  Worker Concurrency:    32 threads")
            print(f"  Active Workers:        {processing:,d}")
            print()

            # ETA calculation
            if throughput_overall > 0 and pending > 0:
                eta_minutes = pending / throughput_overall
                eta_seconds = eta_minutes * 60
                eta_time = now + timedelta(seconds=eta_seconds)

                print("[ESTIMATED TIME]")
                print()
                print(f"  Remaining Images:  {pending:,d}")
                print(f"  Time Remaining:    {format_duration(eta_seconds)} (HH:MM:SS)")
                print(f"  Estimated Completion:  {eta_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print()

            # Footer
            print("=" * 70)
            print(f"Refresh: Every {args.refresh}s | Press Ctrl+C to stop")
            print("=" * 70)

            # Wait before next update
            time.sleep(args.refresh)

    except KeyboardInterrupt:
        print()
        print()
        print("=" * 70)
        print("MONITOR STOPPED")
        print("=" * 70)
        print()

        # Final status
        status = get_status()
        if status:
            print(f"Final Status:")
            print(f"  Completed: {status.get('completed_images', 0):,d} / {status.get('total_images', 0):,d}")
            print(f"  Progress:  {status.get('completion_rate', 0):.1f}%")
            print()


if __name__ == '__main__':
    main()
