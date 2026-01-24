# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

getdatatestbed is a Python library for retrieving data from the USACE Field Research Facility (FRF) Coastal Model Test Bed (CMTB). It interfaces with CHL public THREDDS servers and local FRF servers to access coastal oceanographic and meteorological data stored in NetCDF format.

## Build & Development Commands

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt  # test dependencies

# Install package in development mode
pip install -e .

# Run tests
pytest tests/ -v

# Run tests excluding slow/network tests
pytest tests/ -v -m "not slow"

# Run tests with coverage
pytest tests/ -v --cov=. --cov-report=term-missing

# Lint (CI configuration)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=120 --statistics

# Docstring style check
pydocstyle --convention=google
```

## Architecture

### Core Modules

**getDataFRF.py** - Main data retrieval module containing:
- `getObs` class: Retrieves observational data (waves, wind, water levels, bathymetry, lidar, CTD, altimeters)
- `getDataTestBed` class: Retrieves model output data (STWAVE, CMS, CSHORE)
- Helper functions: `getnc()`, `gettime()`, `removeDuplicatesFromDictionary()`

**getOutsideData.py** - External data sources:
- `forecastData` class: Retrieves forecast data from NCEP (WW3 spectral forecasts), ECMWF, and Argus cBathy

**getPlotData.py** - Plotting utilities that wrap getObs for time-matched model vs observation comparisons

### Data Access Pattern

All classes follow a similar pattern:
1. Initialize with datetime range (`d1`, `d2`)
2. Connect to appropriate THREDDS server (FRF local or CHL public based on IP)
3. Call specific getter methods (e.g., `getWaveData()`, `getWind()`, `getBathyTransectFromNC()`)
4. Returns dictionaries with data arrays and metadata

### THREDDS Servers

- FRF local: `http://134.164.129.55:8080/thredds/dodsC/`
- CHL public: `https://chldata.erdc.dren.mil/thredds/dodsC/`

Server selection is automatic based on network IP (FRF subnet uses local server).

### Key Dependencies

- `testbedutils` - Required utility library (geoprocess, sblib, anglesLib, gridTools)
- `netCDF4` - NetCDF data access
- `numpy`, `pandas` - Data manipulation

### Time Handling

- All time internally uses epoch seconds since 1970-01-01
- Input times should be Python `datetime` objects
- Data is typically rounded to nearest minute (configurable via `dtRound` parameter)
