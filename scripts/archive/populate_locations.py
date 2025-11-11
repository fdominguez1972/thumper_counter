#!/usr/bin/env python3
"""
Populate database with camera locations using the Thumper Counter API.

This script adds all 6 camera locations with their GPS coordinates.
Safe to run multiple times - skips locations that already exist.

Usage:
    python3 scripts/populate_locations.py

Or from Docker:
    docker-compose exec backend python3 scripts/populate_locations.py
"""

import sys
import requests
from typing import Dict, Any, List


# API Configuration
API_BASE_URL = "http://localhost:8001"
LOCATIONS_ENDPOINT = f"{API_BASE_URL}/api/locations"


# Camera locations with GPS coordinates
LOCATIONS = [
    {
        "name": "Hayfield",
        "description": "Open field with good visibility",
        "coordinates": {
            "lat": 29.803056,
            "lon": -97.309722
        },
        "active": True
    },
    {
        "name": "270_Jason",
        "description": "Jason's camera location on property boundary",
        "coordinates": {
            "lat": 29.797222,
            "lon": -97.305000
        },
        "active": True
    },
    {
        "name": "Sanctuary",
        "description": "East pasture near water tank, heavy deer traffic",
        "coordinates": {
            "lat": 29.790556,
            "lon": -97.306944
        },
        "active": True
    },
    {
        "name": "TinMan",
        "description": "TinMan camera station",
        "coordinates": {
            "lat": 29.782778,
            "lon": -97.310000
        },
        "active": True
    },
    {
        "name": "Camphouse",
        "description": "Near the camp house",
        "coordinates": {
            "lat": 29.800833,
            "lon": -97.305278
        },
        "active": True
    },
    {
        "name": "Phils_Secret_Spot",
        "description": "Phil's secret camera location",
        "coordinates": {
            "lat": 29.783333,
            "lon": -97.313333
        },
        "active": True
    }
]


def create_location(location_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a location via the API.

    Args:
        location_data: Location details including name, coordinates, etc.

    Returns:
        dict: API response containing created location or error
    """
    try:
        response = requests.post(
            LOCATIONS_ENDPOINT,
            json=location_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        # Return response data regardless of status code
        return {
            "status_code": response.status_code,
            "data": response.json() if response.content else None,
            "success": response.status_code == 201
        }

    except requests.exceptions.ConnectionError:
        return {
            "status_code": 0,
            "data": {"error": "Connection failed - is the API running?"},
            "success": False
        }
    except requests.exceptions.Timeout:
        return {
            "status_code": 0,
            "data": {"error": "Request timeout"},
            "success": False
        }
    except Exception as e:
        return {
            "status_code": 0,
            "data": {"error": str(e)},
            "success": False
        }


def check_api_health() -> bool:
    """
    Check if the API is running and healthy.

    Returns:
        bool: True if API is healthy, False otherwise
    """
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "healthy"
        return False
    except Exception:
        return False


def main():
    """Main execution function."""
    print("=" * 70)
    print("THUMPER COUNTER - Location Population Script")
    print("=" * 70)
    print()

    # Check API health
    print("[INFO] Checking API health...")
    if not check_api_health():
        print("[FAIL] API is not healthy or not running")
        print("[INFO] Make sure the backend is running:")
        print("       docker-compose up -d backend")
        sys.exit(1)

    print("[OK] API is healthy")
    print()

    # Process each location
    print(f"[INFO] Processing {len(LOCATIONS)} locations...")
    print()

    created_count = 0
    skipped_count = 0
    failed_count = 0

    for location in LOCATIONS:
        name = location["name"]
        lat = location["coordinates"]["lat"]
        lon = location["coordinates"]["lon"]

        print(f"Processing: {name} ({lat}, {lon})")

        result = create_location(location)

        if result["success"]:
            # Successfully created
            location_id = result["data"]["id"]
            print(f"  [OK] Created - ID: {location_id}")
            created_count += 1

        elif result["status_code"] == 409:
            # Already exists
            print(f"  [SKIP] Already exists")
            skipped_count += 1

        else:
            # Error occurred
            error_msg = result["data"].get("detail", result["data"].get("error", "Unknown error"))
            print(f"  [FAIL] {error_msg}")
            failed_count += 1

        print()

    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total locations: {len(LOCATIONS)}")
    print(f"Created:         {created_count}")
    print(f"Skipped:         {skipped_count} (already exist)")
    print(f"Failed:          {failed_count}")
    print()

    if failed_count > 0:
        print("[WARN] Some locations failed to create")
        sys.exit(1)
    else:
        print("[OK] All locations processed successfully!")

    # Show all locations
    print()
    print("[INFO] Fetching all locations from database...")
    try:
        response = requests.get(LOCATIONS_ENDPOINT, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Total locations in database: {data['total']}")
            print()
            print("Locations:")
            for loc in data["locations"]:
                coords = loc.get("coordinates")
                if coords:
                    print(f"  - {loc['name']}: ({coords['lat']}, {coords['lon']})")
                else:
                    print(f"  - {loc['name']}: (no coordinates)")
        else:
            print("[WARN] Could not fetch locations list")
    except Exception as e:
        print(f"[WARN] Error fetching locations: {e}")

    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
