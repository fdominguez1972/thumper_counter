# Camera Location GPS Coordinates
# Hopkins Ranch Trail Cameras

## Coordinates in DMS (Degrees Minutes Seconds)
- Hayfield:          29°48'11"N  97°18'35"W
- 270_Jason:         29°47'50"N  97°18'18"W
- Sanctuary:         29°47'26"N  97°18'25"W
- TinMan:            29°46'58"N  97°18'36"W
- Camphouse:         29°48'03"N  97°18'19"W
- Phils_Secret_Spot: 29°47'00"N  97°18'48"W

## Coordinates in Decimal Degrees (for database)
# Conversion: degrees + (minutes/60) + (seconds/3600)
# North latitude is positive, West longitude is negative

Hayfield:          29.803056, -97.309722
270_Jason:         29.797222, -97.305000
Sanctuary:         29.790556, -97.306944
TinMan:            29.782778, -97.310000
Camphouse:         29.800833, -97.305278
Phils_Secret_Spot: 29.783333, -97.313333

## SQL to Insert/Update Locations
```sql
-- Update existing locations with coordinates
UPDATE locations SET coordinates = '{"lat": 29.803056, "lon": -97.309722}' WHERE name = 'Hayfield';
UPDATE locations SET coordinates = '{"lat": 29.797222, "lon": -97.305000}' WHERE name = '270_Jason';
UPDATE locations SET coordinates = '{"lat": 29.790556, "lon": -97.306944}' WHERE name = 'Sanctuary';
UPDATE locations SET coordinates = '{"lat": 29.782778, "lon": -97.310000}' WHERE name = 'TinMan';
UPDATE locations SET coordinates = '{"lat": 29.800833, "lon": -97.305278}' WHERE name = 'Camphouse';
UPDATE locations SET coordinates = '{"lat": 29.783333, "lon": -97.313333}' WHERE name = 'Phils_Secret_Spot';
```

## Python Script to Initialize Locations
```python
# Initialize locations in database
locations_data = [
    {"name": "Hayfield", "lat": 29.803056, "lon": -97.309722},
    {"name": "270_Jason", "lat": 29.797222, "lon": -97.305000},
    {"name": "Sanctuary", "lat": 29.790556, "lon": -97.306944},
    {"name": "TinMan", "lat": 29.782778, "lon": -97.310000},
    {"name": "Camphouse", "lat": 29.800833, "lon": -97.305278},
    {"name": "Phils_Secret_Spot", "lat": 29.783333, "lon": -97.313333},
]

for loc in locations_data:
    location = Location(
        name=loc["name"],
        active=True,
        description=f"Trail camera location at {loc['name']}"
    )
    location.set_coordinates(loc["lat"], loc["lon"])
    db.add(location)
db.commit()
```

## Notes
- Old_Rusty location from original project not in current list (camera removed?)
- All cameras are within about 1.5 miles of each other
- Coordinates obtained from Google Maps/Earth
- Multiple cameras may share same location (different angles/models)
- Folder names determine location assignment for images
