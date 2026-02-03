# Quick Reference: Argus Imagery Coordinate Fix

## The Problem
```
Argus imagery didn't align with satellite imagery in test_wave_and_imagery.py
Pier and shoreline features were misaligned between the two imagery sources
```

## Why It Happened
The Argus server changed GeoTIFF coordinate system from **State Plane** → **lon/lat**  
But the script assumed it was ALWAYS State Plane and tried to convert lon/lat values as if they were State Plane, producing incorrect coordinates.

## The Fix
```python
from murgtools.getdata import detect_argus_coordinate_system

# Automatically detect coordinate system
extent = get_geotiff_extent(argus_tif_path)
coord_system = detect_argus_coordinate_system(extent)

if coord_system == 'state_plane':
    # Convert State Plane to lon/lat (pseudocode: see examples/test_wave_and_imagery.py
    # for the actual conversion using gp.FRFcoord and building argus_extent)
    argus_extent = convert_to_lonlat(extent)
else:
    # Already lon/lat - use directly  
    argus_extent = extent
```

## How It Works
**Detection Logic:**
- State Plane: Easting ~900,000m, Northing ~270,000m (LARGE values)
- Lon/Lat: Longitude ~-75°, Latitude ~36° (SMALL values)

**Detection Rule:**
- IF `left > 800,000` AND `bottom > 200,000` → **State Plane** (convert it)
- ELSE → **lon/lat** (use directly)

## Usage

### In Your Code
```python
from murgtools.getdata import detect_argus_coordinate_system

extent = [left, right, bottom, top]  # From GeoTIFF
coord_sys = detect_argus_coordinate_system(extent)

# Returns: 'state_plane' or 'lonlat'
```

### Example Values
```python
# State Plane (will be converted)
extent_sp = [901951, 902951, 274093, 275093]
detect_argus_coordinate_system(extent_sp)  # → 'state_plane'

# Lon/Lat (used directly)
extent_ll = [-75.76, -75.72, 36.175, 36.195]
detect_argus_coordinate_system(extent_ll)  # → 'lonlat'
```

## Testing
- **5 unit tests** covering detection, conversion, and edge cases
- **124 total tests passing** (no regressions)
- **Validation script** demonstrates correct behavior
- **0 security vulnerabilities** (CodeQL verified)

## Files Changed
1. `murgtools/getdata/getDataFRF.py` - Added detection utility
2. `murgtools/getdata/__init__.py` - Export utility
3. `examples/test_wave_and_imagery.py` - Use detection utility
4. `tests/test_argus_coordinate_detection.py` - Unit tests
5. `examples/validate_coordinate_fix.py` - Validation script
6. `ARGUS_COORDINATE_FIX.md` - Full documentation

## Result
✅ Imagery now aligns correctly regardless of coordinate system  
✅ Backwards compatible with both old and new Argus formats  
✅ No code duplication - centralized detection logic  
✅ Comprehensive tests ensure it works correctly
