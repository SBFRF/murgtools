"""
getdatatestbed - Python library for accessing USACE FRF Coastal Model Test Bed data.

This package provides utilities for retrieving observational and model data from
the USACE Field Research Facility (FRF) Coastal Model Test Bed (CMTB).
"""

# New snake_case function names (preferred)
from .getDataFRF import (getObs, getDataTestBed, gettime, getnc,
                         remove_duplicates_from_dictionary,
                         get_geotiff_extent, get_argus_imagery, thread_get_argus_imagery,
                         find_argus_imagery, getArgusPixelIntensity)
# Deprecated camelCase aliases (for backward compatibility)
from .getDataFRF import (removeDuplicatesFromDictionary,
                         getArgusImagery, threadGetArgusImagery, findArgusImagery)
from .getOutsideData import forecastData, getSatelliteImagery
from .getPlotData import alt_PlotData

__version__ = "0.9.0"
__author__ = "Spicer Bak"
__email__ = "spicer.bak@usace.army.mil"

__all__ = [
    "getObs",
    "getDataTestBed",
    "gettime",
    "getnc",
    # New snake_case names (preferred)
    "remove_duplicates_from_dictionary",
    "get_argus_imagery",
    "thread_get_argus_imagery",
    "find_argus_imagery",
    # Deprecated camelCase aliases (backward compatibility)
    "removeDuplicatesFromDictionary",
    "getArgusImagery",
    "threadGetArgusImagery",
    "findArgusImagery",
    # Other exports
    "forecastData",
    "getSatelliteImagery",
    "get_geotiff_extent",
    "getArgusPixelIntensity",
    "alt_PlotData",
]
