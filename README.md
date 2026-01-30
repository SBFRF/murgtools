# murgtools

A Python library for retrieving data from the USACE Field Research Facility (FRF) and supporting general tools, plotting routines, and generically useful stuff for the MURG.  Its comprised and was built from prior (no longer supported libraries) as `getdatatestbed` and `testbedutils`. Efforts have been made to streamline and make those prior libraries more generic and easier to use.

## Overview

`murgtools` provides utilities for accessing observational data from the CHL public THREDDS server and local FRF server. It interfaces with NetCDF data files containing coastal oceanographic and meteorological measurements.  It also has generically useful utilities to help with data transforms, file handling, easy evaluation and plotting routines.

## Installation

### From PyPI (when available)

```bash
pip install murgtools
```

### From GitHub

```bash
pip install git+https://github.com/SBFRF/murgtools.git
```

### Development Installation

```bash
git clone https://github.com/SBFRF/murgtools.git
cd murgtools
pip install -e ".[dev]"
```

## Quick Start

```python
from datetime import datetime
from murgtools.getdata import getObs

# Define time range
start = datetime(2020, 1, 1)
end = datetime(2020, 1, 7)

# Create observation data object
obs = getObs(start, end)

# Retrieve wave data
wave_data = obs.getWaveSpec('waverider-26m')

# Retrieve wind data
wind_data = obs.getWind()

# Retrieve water level data
wl_data = obs.getWL()
```

## Package Structure

```
murgtools/
├── getdata/             # Data retrieval subpackage
│   ├── getDataFRF.py    # FRF observational and model data
│   ├── getOutsideData.py # External data sources
│   └── getPlotData.py   # Plotting utilities
└── utils/               # Utility subpackage
    ├── geoprocess.py    # Coordinate transformations
    ├── sblib.py         # Base utility functions
    └── ...
```

## Main Classes

### `getObs`
Retrieves observational data including:
- Wave spectra and bulk parameters
- Wind measurements
- Water levels
- Bathymetry surveys
- Lidar data
- CTD profiles
- Altimeter measurements

### `getDataTestBed`
Retrieves model output data from:
- STWAVE
- CMS
- CSHORE

### `forecastData`
Retrieves forecast data from external sources:
- NCEP WW3 spectral forecasts
- ECMWF forecasts
- Argus cBathy

## Data Sources

The library automatically selects the appropriate THREDDS server based on network location:
- **FRF Local**: `http://134.164.129.55:8080/thredds/dodsC/`
- **CHL Public**: `https://chldata.erdc.dren.mil/thredds/dodsC/`

## Requirements

- Python >= 3.9
- numpy >= 1.20.1
- pandas >= 1.2.4
- netCDF4 >= 1.5.7
- scikit-image >= 0.18.1

## Running Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run all tests (excluding slow/network tests)
pytest tests/ -v -m "not slow"

# Run with coverage
pytest tests/ -v --cov=murgtools --cov-report=term-missing
```

## License

BSD-3-Clause License. See [LICENSE](LICENSE) for details.

## Author

Spicer Bak, PhD

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
