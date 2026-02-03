# FRFcoord Multiple Point Input Support - Verification

## Issue Summary

**Original Issue**: "Currently `FRFcoord` is limited to single point inputs thereby requiring looping outside of this function."

**Agent Instructions**: "I think this was solved with most recent update to Transformer class in pyproj. confirm or fix"

## Verification Results

### ✅ CONFIRMED: `FRFcoord` Already Supports Multiple Input Points

The `FRFcoord` function and all related coordinate transformation functions in `murgtools.utils.geoprocess` **already support multiple input points** without requiring any code changes.

This functionality is enabled by pyproj version 3.0+, which provides native array handling in the `Transformer` class.

## Key Findings

### Supported Input Types

1. **Single Point** (original functionality)
   - Input: `FRFcoord(566.93, 515.11)`
   - Output: Scalar/float values

2. **NumPy Arrays** (enhanced functionality)
   - Input: `FRFcoord(np.array([100, 200, 300]), np.array([100, 200, 300]))`
   - Output: NumPy arrays of same shape

3. **Python Lists** (automatic conversion)
   - Input: `FRFcoord([100, 200, 300], [100, 200, 300])`
   - Output: NumPy arrays (lists automatically converted)

### Supported Coordinate Systems

All coordinate systems support array inputs:
- **FRF Local Coordinates** (xFRF, yFRF)
- **NC State Plane** (EPSG:3358)
- **Lat/Lon** (WGS84, EPSG:4326)
- **UTM** (Zone 18S)

### Functions Supporting Arrays

All transformation functions support array inputs:
- `FRFcoord(p1, p2, coordType)` - Universal converter
- `FRF2ncsp(xFRF, yFRF)` - FRF to State Plane
- `ncsp2FRF(spE, spN)` - State Plane to FRF
- `ncsp2LatLon(spE, spN)` - State Plane to Lat/Lon
- `LatLon2ncsp(lon, lat)` - Lat/Lon to State Plane
- `LatLon2utm(lat, lon)` - Lat/Lon to UTM
- `utm2LatLon(utmE, utmN, zn, zl)` - UTM to Lat/Lon
- `utm2ncsp(utmE, utmN, zn, zl)` - UTM to State Plane
- `ncsp2utm(easting, northing)` - State Plane to UTM

## Usage Examples

### Example 1: Converting Multiple FRF Points

```python
import numpy as np
from murgtools.utils import geoprocess as gp

# Define multiple points in FRF coordinates
x_frf = np.array([100.0, 200.0, 300.0, 566.93])
y_frf = np.array([100.0, 200.0, 300.0, 515.11])

# Convert all points at once (no loop needed!)
result = gp.FRFcoord(x_frf, y_frf)

# Access converted coordinates
print(f"State Plane Easting: {result['StateplaneE']}")
print(f"State Plane Northing: {result['StateplaneN']}")
print(f"Latitude: {result['Lat']}")
print(f"Longitude: {result['Lon']}")
print(f"UTM Easting: {result['utmE']}")
print(f"UTM Northing: {result['utmN']}")
```

### Example 2: Converting Multiple Lat/Lon Points

```python
import numpy as np
from murgtools.utils import geoprocess as gp

# Define multiple points in Lat/Lon
lon = np.array([-75.75, -75.74, -75.73])
lat = np.array([36.17, 36.18, 36.19])

# Convert all at once
result = gp.FRFcoord(lon, lat)

# Get FRF coordinates for all points
xFRF = result['xFRF']
yFRF = result['yFRF']
```

### Example 3: Using Lists Instead of Arrays

```python
from murgtools.utils import geoprocess as gp

# Python lists work too!
x_list = [100.0, 200.0, 300.0]
y_list = [100.0, 200.0, 300.0]

result = gp.FRFcoord(x_list, y_list)
# Output is automatically converted to numpy arrays
```

## Test Results

All 32 existing tests pass, including:
- Single point conversions
- Array conversions
- List conversions
- Round-trip conversions (FRF → SP → LL → SP → FRF)
- All coordinate system combinations

```bash
pytest tests/test_geoprocess.py -v
# Result: 32 passed, 1 warning in 1.57s
```

## Technical Details

### How It Works

1. **pyproj Transformer**: Version 3.0+ of pyproj includes native support for array transformations
2. **FRFcoord Logic**: The function automatically detects array inputs using `np.size(p1) > 1`
3. **Consistent Behavior**: Uses `.all()` for array comparisons when detecting coordinate types
4. **Pass-through**: Arrays are passed through all transformation functions without modification

### Implementation in Code

The key code in `FRFcoord` (lines 321-344 of geoprocess.py):

```python
# convert list to array if needed
if isinstance(p1, list):
    p1 = np.asarray(p1)
if isinstance(p2, list):
    p2 = np.asarray(p2)

# now run checks to see what version of input we have!
if np.size(p1) > 1:
    LL1 = (np.floor(np.absolute(p1)) == 75).all()
    LL2 = (np.floor(p2) == 36).all()
    SP1 = (p1 > 800000).all()
    SP2 = (p2 > 200000).all()
    # ... etc
```

The pyproj Transformer handles arrays natively (lines 195-200):

```python
transformer = pyproj.Transformer.from_crs(
    f"epsg:{EPSG}",
    "epsg:4326",
    always_xy=True
)
lon, lat = transformer.transform(spE, spN)  # Works with arrays!
```

## Conclusion

✅ **No code changes required** - the functionality already exists and is fully tested.

The issue has been resolved by the update to pyproj 3.0+, which provides native array handling in the `Transformer` class. The `FRFcoord` function and all related coordinate transformation functions properly leverage this capability.

Users can now convert multiple points without external loops, significantly improving performance and code simplicity.

## Dependencies

- **pyproj >= 3.0.0** (current: 3.7.2)
- **numpy >= 1.20.1**

These are already specified in `requirements.txt`.
