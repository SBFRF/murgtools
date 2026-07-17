"""murgtools - Tools for USACE FRF Coastal Model Test Bed data access."""

from .getdata import getObs, getDataTestBed, gettime, getnc
# New snake_case function names (preferred)
from .getdata import remove_duplicates_from_dictionary
from .getdata import get_argus_imagery, thread_get_argus_imagery
# Deprecated camelCase aliases (backward compatibility)
from .getdata import removeDuplicatesFromDictionary
from .getdata import getArgusImagery, threadGetArgusImagery
from .getdata import forecastData, getSatelliteImagery, alt_PlotData
from .plotting import conditions_plot, bin_data
from .cache import DataCache, get_cache, enable_cache, disable_cache, clear_cache

__all__ = [
    "getObs",
    "getDataTestBed",
    "gettime",
    "getnc",
    # New snake_case names (preferred)
    "remove_duplicates_from_dictionary",
    "get_argus_imagery",
    "thread_get_argus_imagery",
    # Deprecated camelCase aliases (backward compatibility)
    "removeDuplicatesFromDictionary",
    "getArgusImagery",
    "threadGetArgusImagery",
    # Other exports
    "forecastData",
    "getSatelliteImagery",
    "alt_PlotData",
    "conditions_plot",
    "bin_data",
    # Cache functions
    "DataCache",
    "get_cache",
    "enable_cache",
    "disable_cache",
    "clear_cache",
]
