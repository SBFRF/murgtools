"""
getdatatestbed - Python library for accessing USACE FRF Coastal Model Test Bed data.

This package provides utilities for retrieving observational and model data from
the USACE Field Research Facility (FRF) Coastal Model Test Bed (CMTB).
"""

from .getDataFRF import (getObs, getDataTestBed, gettime, getnc, removeDuplicatesFromDictionary,
                         get_geotiff_extent, getArgusImagery, threadGetArgusImagery, findArgusImagery)
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
    "removeDuplicatesFromDictionary",
    "forecastData",
    "getSatelliteImagery",
    "get_geotiff_extent",
    "getArgusImagery",
    "threadGetArgusImagery",
    "findArgusImagery",
    "alt_PlotData",
]
