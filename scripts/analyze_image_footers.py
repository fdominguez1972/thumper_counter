#!/usr/bin/env python3
"""
Analyze trail camera image footers to extract timestamp and metadata.

This script examines sample images from each location to determine:
1. Footer format and layout
2. Camera name format
3. Date/time format (12hr vs 24hr)
4. Moon phase indicator format
5. Best extraction method (OCR vs template matching)
"""

import sys
from pathlib import Path
from PIL import Image
import json

# Sample image paths from each location
SAMPLE_IMAGES = {
    '270_Jason': [
        '/mnt/images/270_Jason/270_JASON_01603.jpg',
        '/mnt/images/270_Jason/270_JASON_01546.jpg',
        '/mnt/images/270_Jason/270_JASON_02242.jpg',
        '/mnt/images/270_Jason/270_JASON_01739.jpg',
        '/mnt/images/270_Jason/270_JASON_03266.jpg',
    ],
    'Camphouse': [
        '/mnt/images/Camphouse/CAMPHOUSE_03356.jpg',
        '/mnt/images/Camphouse/CAMPHOUSE_00312.jpg',
        '/mnt/images/Camphouse/CAMPHOUSE_00023.jpg',
        '/mnt/images/Camphouse/CAMPHOUSE_02881.jpg',
        '/mnt/images/Camphouse/CAMPHOUSE_02231.jpg',
    ],
    'Hayfield': [
        '/mnt/images/Hayfield/HAYFIELD_05780.jpg',
        '/mnt/images/Hayfield/HAYFIELD_07459.jpg',
        '/mnt/images/Hayfield/HAYFIELD_08049.jpg',
        '/mnt/images/Hayfield/HAYFIELD_08697.jpg',
        '/mnt/images/Hayfield/HAYFIELD_07902.jpg',
    ],
    'Phils_Secret_Spot': [
        '/mnt/images/Phils_Secret_Spot/PHILS_SECRET_SPOT_01353.jpg',
        '/mnt/images/Phils_Secret_Spot/PHILS_SECRET_SPOT_00254.jpg',
        '/mnt/images/Phils_Secret_Spot/PHILS_SECRET_SPOT_00110.jpg',
        '/mnt/images/Phils_Secret_Spot/PHILS_SECRET_SPOT_00036.jpg',
        '/mnt/images/Phils_Secret_Spot/PHILS_SECRET_SPOT_00936.jpg',
    ],
    'Sanctuary': [
        '/mnt/images/Sanctuary/SANCTUARY_07116.jpg',
        '/mnt/images/Sanctuary/SANCTUARY_06209.jpg',
        '/mnt/images/Sanctuary/SANCTUARY_01109.jpg',
        '/mnt/images/Sanctuary/SANCTUARY_11385.jpg',
        '/mnt/images/Sanctuary/SANCTUARY_10612.jpg',
    ],
    'TinMan': [
        '/mnt/images/TinMan/TINMAN_00482.jpg',
        '/mnt/images/TinMan/TINMAN_00588.jpg',
        '/mnt/images/TinMan/TINMAN_01077.jpg',
        '/mnt/images/TinMan/TINMAN_01237.jpg',
        '/mnt/images/TinMan/TINMAN_00023.jpg',
    ],
}


def analyze_image_footer(image_path: str) -> dict:
    """
    Analyze an image to extract footer dimensions and characteristics.

    Returns dict with:
    - dimensions: (width, height)
    - footer_height: estimated footer bar height
    - footer_region: PIL Image of just the footer
    - has_footer: whether a footer bar was detected
    """
    try:
        img = Image.open(image_path)
        width, height = img.size

        # Trail camera footers are typically 30-80 pixels tall at bottom
        # Let's sample the bottom 100 pixels to be safe
        footer_height = 100
        footer_region = img.crop((0, height - footer_height, width, height))

        # Check if there's a distinct footer by analyzing pixel patterns
        # Trail camera footers usually have dark background with light text
        pixels = list(footer_region.getdata())

        # Sample some pixels to detect footer characteristics
        avg_brightness = sum(sum(p) if isinstance(p, tuple) else p for p in pixels) / len(pixels)

        result = {
            'path': image_path,
            'dimensions': (width, height),
            'footer_height': footer_height,
            'footer_region_size': footer_region.size,
            'avg_footer_brightness': avg_brightness,
            'has_footer': avg_brightness < 100,  # Dark footer detection
            'success': True,
        }

        # Save footer region for visual inspection
        footer_filename = Path(image_path).stem + '_footer.jpg'
        footer_path = f'/tmp/{footer_filename}'
        footer_region.save(footer_path)
        result['footer_saved_to'] = footer_path

        return result

    except Exception as e:
        return {
            'path': image_path,
            'success': False,
            'error': str(e)
        }


def main():
    """Analyze sample images from all locations."""
    print("=" * 80)
    print("TRAIL CAMERA IMAGE FOOTER ANALYSIS")
    print("=" * 80)
    print()

    all_results = {}

    for location, image_paths in SAMPLE_IMAGES.items():
        print(f"\n[INFO] Analyzing location: {location}")
        print("-" * 80)

        location_results = []

        for img_path in image_paths:
            if not Path(img_path).exists():
                print(f"  [WARN] Image not found: {img_path}")
                continue

            print(f"  [INFO] Processing: {Path(img_path).name}")
            result = analyze_image_footer(img_path)
            location_results.append(result)

            if result['success']:
                print(f"    Dimensions: {result['dimensions']}")
                print(f"    Footer brightness: {result['avg_footer_brightness']:.1f}")
                print(f"    Has footer: {result['has_footer']}")
                print(f"    Footer saved: {result['footer_saved_to']}")
            else:
                print(f"    [FAIL] Error: {result['error']}")

        all_results[location] = location_results

    # Summary
    print("\n" + "=" * 80)
    print("ANALYSIS SUMMARY")
    print("=" * 80)

    total_analyzed = sum(len(results) for results in all_results.values())
    total_with_footer = sum(
        sum(1 for r in results if r.get('has_footer', False))
        for results in all_results.values()
    )

    print(f"\nTotal images analyzed: {total_analyzed}")
    print(f"Images with detected footer: {total_with_footer}")
    print(f"Footer detection rate: {100.0 * total_with_footer / total_analyzed:.1f}%")

    print("\n[INFO] Footer images saved to /tmp/ for visual inspection")
    print("[INFO] Next step: Visually inspect footer images to determine extraction strategy")

    # Save results to JSON
    output_file = '/tmp/footer_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[OK] Full analysis saved to: {output_file}")


if __name__ == '__main__':
    main()
