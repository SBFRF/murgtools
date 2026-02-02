# Argus Imagery Coordinate System Fix

## Problem

The `examples/test_wave_and_imagery.py` script was experiencing misalignment between satellite imagery and Argus imagery. The pier and shoreline (dune vegetation line) were not aligning correctly between the two imagery sources.

### Root Cause

The Argus coastal imaging server apparently changed the coordinate system used in their GeoTIFF files from **NC State Plane NAD83** coordinates to **geographic lon/lat** coordinates. The example script was hardcoded to always assume Argus GeoTIFFs use State Plane coordinates and would unconditionally convert them to lon/lat.

When the server started providing GeoTIFFs that were already in lon/lat:
- The script would read the extent values (e.g., `-75.76, -75.72, 36.175, 36.195`)
- It would treat these as State Plane coordinates (expecting values like `901951, 902951, 274093, 275093`)
- The coordinate conversion function would interpret the small lon/lat values as if they were State Plane coordinates
- This produced completely incorrect final coordinates, causing severe misalignment

## Solution

Added automatic coordinate system detection using the `detect_argus_coordinate_system()` utility function in `examples/test_wave_and_imagery.py`:

```python
from murgtools.getdata import detect_argus_coordinate_system

# Extract extent from the GeoTIFF
extent = get_geotiff_extent(tmp_path)

# Detect coordinate system and convert if needed
coord_system = detect_argus_coordinate_system(extent)

if coord_system == 'state_plane':
    # Convert State Plane corners to lat/lon
    left, right, bottom, top = extent
    ll_corner = gp.FRFcoord(left, bottom, coordType='ncsp')
    ur_corner = gp.FRFcoord(right, top, coordType='ncsp')
    argus_extent = [ll_corner['Lon'], ur_corner['Lon'], ll_corner['Lat'], ur_corner['Lat']]
else:
    # Already in lon/lat - use directly
    argus_extent = extent
```

### Detection Logic

The fix uses the `detect_argus_coordinate_system()` utility function which implements a simple heuristic based on the magnitude of coordinate values:

- **State Plane coordinates** for the FRF area:
  - Easting: ~900,000 - 910,000 meters
  - Northing: ~270,000 - 280,000 meters
  
- **Lon/Lat coordinates** for the FRF area:
  - Longitude: -76 to -75 degrees
  - Latitude: 36.1 to 36.2 degrees

The detection requires BOTH conditions to be true for State Plane classification:
- `left > 800000` (Easting threshold)
- `bottom > 200000` (Northing threshold)

If both conditions are met, the coordinates are classified as State Plane and converted. Otherwise, they're used directly as lon/lat.

## Files Changed

1. **`examples/test_wave_and_imagery.py`**: Added coordinate system detection logic
2. **`tests/test_argus_coordinate_detection.py`**: Added comprehensive unit tests for the detection logic
3. **`examples/validate_coordinate_fix.py`**: Added validation script demonstrating the fix

## Testing

The fix includes three levels of testing:

1. **Unit tests** (`tests/test_argus_coordinate_detection.py`):
   - Tests State Plane coordinate detection and conversion
   - Tests lon/lat coordinate detection (no conversion)
   - Tests edge cases with unusual values

2. **Validation script** (`examples/validate_coordinate_fix.py`):
   - Demonstrates the fix working correctly for both coordinate systems
   - Shows the detection logic in action with real FRF coordinate values

3. **Backwards compatibility**:
   - All existing tests pass
   - Works correctly with old State Plane GeoTIFFs
   - Works correctly with new lon/lat GeoTIFFs

## Impact

The fix ensures that:
- The example script works regardless of which coordinate system Argus uses
- No hardcoded assumptions about coordinate systems
- Satellite and Argus imagery will align correctly for visualization
- Wave gauge locations (already in lon/lat) continue to align properly with both imagery types
