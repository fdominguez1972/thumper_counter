#!/usr/bin/env python3
"""
Test OCR extraction on trail camera footers.

This script tests EasyOCR on sample footer images to:
1. Verify OCR accuracy
2. Extract timestamp, camera name, temperature
3. Validate parsing logic
"""

import sys
import re
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageEnhance
import easyocr
import json
import cv2
import numpy as np

# Sample original images to test (full resolution)
TEST_IMAGES = [
    '/mnt/images/270_Jason/270_JASON_01603.jpg',
    '/mnt/images/Sanctuary/SANCTUARY_06209.jpg',
    '/mnt/images/Phils_Secret_Spot/PHILS_SECRET_SPOT_01353.jpg',
    '/mnt/images/Hayfield/HAYFIELD_05780.jpg',
    '/mnt/images/TinMan/TINMAN_00482.jpg',
    '/mnt/images/Camphouse/CAMPHOUSE_00312.jpg',
]


def extract_footer_region(image_path: str, footer_height: int = 35) -> Image.Image:
    """
    Extract just the footer region from an image.

    Args:
        image_path: Path to image file
        footer_height: Height of footer in pixels (default 35)

    Returns:
        PIL Image of footer region
    """
    img = Image.open(image_path)
    width, height = img.size

    # For full images, crop to just the footer bar
    # For already-extracted footers (100px tall), take bottom portion
    if height > 100:
        # Full image - take bottom 35px
        footer = img.crop((0, height - footer_height, width, height))
    else:
        # Already a footer extraction - take bottom 35px
        footer = img.crop((0, height - footer_height, width, height))

    return footer


def preprocess_footer_for_ocr(footer_img: Image.Image, scale_factor: int = 4) -> str:
    """
    Preprocess footer image to improve OCR accuracy.

    Simple approach:
    1. Upscale image significantly (4x) for better text recognition
    2. Enhance contrast moderately
    3. Sharpen slightly

    Args:
        footer_img: PIL Image of footer
        scale_factor: Upscaling factor (default 4x = 640x35 -> 2560x140)

    Returns:
        Path to preprocessed image file
    """
    # Upscale significantly for better OCR
    width, height = footer_img.size
    new_size = (width * scale_factor, height * scale_factor)
    footer_large = footer_img.resize(new_size, Image.Resampling.LANCZOS)

    # Moderate contrast enhancement
    enhancer = ImageEnhance.Contrast(footer_large)
    footer_enhanced = enhancer.enhance(1.8)

    # Moderate sharpening
    sharpener = ImageEnhance.Sharpness(footer_enhanced)
    footer_sharp = sharpener.enhance(1.3)

    # Save preprocessed image (keep color for better OCR)
    output_path = '/tmp/footer_preprocessed.jpg'
    footer_sharp.save(output_path, quality=95)

    return output_path


def extract_timestamp_from_ocr(text: str) -> dict:
    """
    Parse OCR text to extract structured data.

    Expected format examples:
    - "270 JASON 024F -04C 01/21/2025 04:16:06"
    - "SANCTUARY 071F 21C 03/26/2024 19:46:19"
    - "PHIL1 096F 35C 09/03/2021 05:53:47"

    Returns dict with:
        - camera_name: str
        - temperature_f: int
        - temperature_c: int
        - date: str (MM/DD/YYYY)
        - time: str (HH:MM:SS)
        - timestamp: datetime object
    """
    result = {
        'camera_name': None,
        'temperature_f': None,
        'temperature_c': None,
        'date': None,
        'time': None,
        'timestamp': None,
        'raw_text': text,
    }

    # Clean up text (remove extra whitespace, normalize)
    text = ' '.join(text.split())

    # Pattern 1: Date in MM/DD/YYYY format
    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', text)
    if date_match:
        result['date'] = date_match.group(1)

    # Pattern 2: Time in HH:MM:SS format
    time_match = re.search(r'(\d{1,2}:\d{2}:\d{2})', text)
    if time_match:
        result['time'] = time_match.group(1)

    # Pattern 3: Temperature (###F ##C or ###F-##C)
    temp_match = re.search(r'(\d{2,3})F\s*(-?\d{1,3})C', text)
    if temp_match:
        result['temperature_f'] = int(temp_match.group(1))
        result['temperature_c'] = int(temp_match.group(2))

    # Pattern 4: Camera name (everything before temperature)
    # Remove known non-camera text (RIGF, T, etc)
    camera_text = re.sub(r'RIGF|^T\s+', '', text)

    # Extract camera name (text before temperature or date)
    if temp_match:
        camera_text = camera_text[:camera_text.find(temp_match.group(0))].strip()
    elif date_match:
        camera_text = camera_text[:camera_text.find(date_match.group(0))].strip()

    # Clean camera name
    camera_text = re.sub(r'[^A-Za-z0-9\s_-]', '', camera_text).strip()
    if camera_text:
        result['camera_name'] = camera_text

    # Build timestamp if we have both date and time
    if result['date'] and result['time']:
        try:
            timestamp_str = f"{result['date']} {result['time']}"
            result['timestamp'] = datetime.strptime(timestamp_str, '%m/%d/%Y %H:%M:%S')
        except ValueError as e:
            print(f"    [WARN] Failed to parse timestamp: {e}")

    return result


def test_ocr_on_footer(reader, image_path: str) -> dict:
    """
    Run OCR on a footer image and extract structured data.

    Args:
        reader: EasyOCR reader instance
        image_path: Path to original image

    Returns:
        Dictionary with OCR results and parsed data
    """
    print(f"\n[INFO] Testing: {Path(image_path).name}")

    # Check if file exists
    if not Path(image_path).exists():
        print(f"  [WARN] File not found, skipping")
        return {'success': False, 'error': 'File not found'}

    try:
        # Extract footer region
        footer_img = extract_footer_region(image_path, footer_height=35)
        print(f"  Original size: {Image.open(image_path).size}")
        print(f"  Footer size: {footer_img.size}")

        # Save original footer for inspection
        footer_path = f"/tmp/{Path(image_path).stem}_footer_35px.jpg"
        footer_img.save(footer_path)

        # Preprocess for better OCR
        preprocessed_path = preprocess_footer_for_ocr(footer_img, scale_factor=4)
        print(f"  Preprocessed: {preprocessed_path}")

        # Run OCR on preprocessed footer
        results = reader.readtext(preprocessed_path)

        # Combine all detected text
        detected_text = ' '.join([text for (bbox, text, conf) in results])
        print(f"  Raw OCR text: {detected_text}")

        # Parse structured data
        parsed = extract_timestamp_from_ocr(detected_text)

        print(f"  Camera: {parsed['camera_name']}")
        print(f"  Temperature: {parsed['temperature_f']}F / {parsed['temperature_c']}C")
        print(f"  Date: {parsed['date']}")
        print(f"  Time: {parsed['time']}")
        print(f"  Timestamp: {parsed['timestamp']}")

        # Check completeness
        is_complete = all([
            parsed['camera_name'],
            parsed['date'],
            parsed['time'],
            parsed['timestamp']
        ])

        if is_complete:
            print("  [OK] Complete extraction")
        else:
            print("  [WARN] Incomplete extraction")

        return {
            'success': True,
            'path': image_path,
            'ocr_results': results,
            'detected_text': detected_text,
            'parsed': parsed,
            'is_complete': is_complete,
        }

    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return {
            'success': False,
            'path': image_path,
            'error': str(e)
        }


def main():
    """Test OCR extraction on sample footers."""
    print("=" * 80)
    print("TRAIL CAMERA FOOTER OCR TEST")
    print("=" * 80)

    # Initialize EasyOCR reader
    print("\n[INFO] Initializing EasyOCR reader (this may take a moment)...")
    try:
        reader = easyocr.Reader(['en'], gpu=True)
        print("[OK] EasyOCR reader initialized (GPU enabled)")
    except Exception as e:
        print(f"[WARN] GPU initialization failed, falling back to CPU: {e}")
        reader = easyocr.Reader(['en'], gpu=False)
        print("[OK] EasyOCR reader initialized (CPU mode)")

    # Test each sample image
    results = []
    for image_path in TEST_IMAGES:
        result = test_ocr_on_footer(reader, image_path)
        results.append(result)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    total = len(results)
    successful = sum(1 for r in results if r.get('success', False))
    complete = sum(1 for r in results if r.get('is_complete', False))

    print(f"\nTotal images tested: {total}")
    print(f"Successful OCR: {successful} ({100.0 * successful / total:.1f}%)")
    print(f"Complete extractions: {complete} ({100.0 * complete / total:.1f}%)")

    # Save detailed results
    output_file = '/tmp/ocr_test_results.json'
    with open(output_file, 'w') as f:
        # Convert datetime objects to strings for JSON serialization
        for r in results:
            if r.get('parsed', {}).get('timestamp'):
                r['parsed']['timestamp'] = r['parsed']['timestamp'].isoformat()
        json.dump(results, f, indent=2)

    print(f"\n[OK] Detailed results saved to: {output_file}")

    # Return exit code
    if complete == total:
        print("\n[OK] All tests passed!")
        return 0
    else:
        print("\n[WARN] Some extractions incomplete")
        return 1


if __name__ == '__main__':
    sys.exit(main())
