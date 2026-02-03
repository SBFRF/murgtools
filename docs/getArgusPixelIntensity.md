# getArgusPixelIntensity

## Overview

The `getArgusPixelIntensity` function is a wrapper around `getArgusImagery` that extracts pixel intensity values from Argus imagery at specified locations. It provides flexible coordinate system support and handles gaps in imagery data.

## Key Features

- **Multiple coordinate systems**: pixel (i,j), FRF (xFRF, yFRF), geographic (lon, lat), NC State Plane
- **Multiple image types**: timex, var, snap, bright, dark
- **Channel selection**: individual RGB channels or grayscale
- **Batch processing**: process multiple times in one call
- **Gap handling**: returns timestamps with pixel values to identify missing data
- **Automatic rounding**: times rounded to nearest 30-minute interval

## Function Signature

```python
def getArgusPixelIntensity(times, location, coordType='FRF', imageType='timex',
                           channel=None, verbose=True, **kwargs)
```

## Parameters

- **times** (datetime or list): Single or multiple datetime objects for image retrieval
- **location** (tuple or dict): Location specification (format depends on coordType)
- **coordType** (str): Coordinate system type
  - `'pixel'`: Direct pixel indices (i, j)
  - `'FRF'`: FRF local coordinates (xFRF, yFRF) in meters
  - `'LL'`, `'geographic'`, `'LatLon'`: Geographic coordinates (lon, lat)
  - `'spnc'`, `'ncsp'`: NC State Plane coordinates
- **imageType** (str): Type of Argus image product
  - `'timex'`: Time exposure average (default)
  - `'var'`: Variance
  - `'snap'`: Snapshot
  - `'bright'`: Brightest pixels
  - `'dark'`: Darkest pixels
- **channel** (str, int, or None): Color channel to extract
  - `'red'`, `'r'`, `0`: Red channel
  - `'green'`, `'g'`, `1`: Green channel
  - `'blue'`, `'b'`, `2`: Blue channel
  - `'gray'`, `'grey'`, `'bw'`: Grayscale (weighted average)
  - `None`: Return all RGB channels (default)
- **verbose** (bool): Enable logging output (default: True)
- **kwargs**: Additional arguments passed to `findArgusImagery` (e.g., `search_window_hours`, `method`)

## Returns

Dictionary containing:
- **time**: list of datetime objects for successfully retrieved images
- **epochtime**: list of epoch times (seconds since 1970-01-01)
- **intensity**: numpy array of intensity values
  - Shape: [time] if channel specified
  - Shape: [time, 3] if channel is None (RGB)
- **location**: dict with coordinate information (includes xFRF, yFRF, pixel_i, pixel_j)
- **imageType**: str, image type used
- **missing_times**: list of datetime objects where no image was found

Returns `None` if no valid images could be retrieved.

## Examples

See `examples/argus_pixel_intensity_example.py` for complete working examples.

### Example 1: Extract red channel using pixel coordinates

```python
import datetime as DT
from murgtools.getdata import getArgusPixelIntensity

times = [DT.datetime(2024, 6, 15, 12, 0, 0)]
location = (500, 300)  # pixel (i, j)

result = getArgusPixelIntensity(
    times=times,
    location=location,
    coordType='pixel',
    imageType='timex',
    channel='red'
)
```

### Example 2: Extract RGB values using FRF coordinates

```python
location = (500, 100)  # xFRF, yFRF in meters

result = getArgusPixelIntensity(
    times=DT.datetime(2024, 6, 15, 12, 0, 0),
    location=location,
    coordType='FRF',
    imageType='timex',
    channel=None  # All RGB channels
)
```

## See Also

- `getArgusImagery`: Retrieve full Argus imagery
- `findArgusImagery`: Search for available Argus imagery
- Example script: `examples/argus_pixel_intensity_example.py`
