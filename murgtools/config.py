"""Centralized configuration for murgtools library.

This module contains all hardcoded URLs, server addresses, and configuration
values used throughout the murgtools package. Centralizing these values makes
it easier to update endpoints and ensures consistency across modules.
"""

import socket
import threading

# =============================================================================
# THREDDS Server URLs
# =============================================================================

# FRF Local THREDDS (internal network only)
THREDDS_FRF_LOCAL = 'http://134.164.129.55:8080/thredds/dodsC/'
THREDDS_FRF_LOCAL_ALT = 'http://134.164.129.55/thredds/dodsC/'
THREDDS_FRF_LOCAL_FRF = 'http://134.164.129.55/thredds/dodsC/FRF/'

# CHL Public THREDDS (externally accessible)
THREDDS_CHL_PUBLIC = 'https://chldata.erdc.dren.mil/thredds/dodsC/'
THREDDS_CHL_ALT = 'https://chlthredds.erdc.dren.mil/thredds/dodsC/frf/'

# CMTB (Coastal Model Test Bed) THREDDS
THREDDS_TESTBED = 'http://134.164.129.62:8080/thredds/dodsC/CMTB'
THREDDS_CRUNCH = 'http://134.164.129.55:8080/thredds/dodsC/cmtb/'

# Survey data URLs
SURVEY_TRANSECTS_URL = 'http://134.164.129.55/thredds/dodsC/FRF/geomorphology/elevationTransects/survey/surveyTransects.ncml'  # noqa: E501
WAVE_8M_ARRAY_URL = 'http://134.164.129.55/thredds/dodsC/FRF/oceanography/waves/8m-array/2017/FRF-ocean_waves_8m-array_201707.nc'  # noqa: E501

# =============================================================================
# Imagery URLs
# =============================================================================

# Argus coastal imaging system
ARGUS_BASE_URL = 'https://coastalimaging.erdc.dren.mil/FrfTower/Processed/Orthophotos/cxgeo/'

# STAC (SpatioTemporal Asset Catalog) endpoints for satellite imagery
STAC_URLS = {
    'element84': 'https://earth-search.aws.element84.com/v1/search',
    'planetary-computer': 'https://planetarycomputer.microsoft.com/api/stac/v1/search'
}

# Planetary Computer signing endpoint
PLANETARY_COMPUTER_SIGN_URL = 'https://planetarycomputer.microsoft.com/api/sas/v1/sign'

# =============================================================================
# External Data Sources
# =============================================================================

# NCEP WaveWatch III forecast data
NCEP_DATA_URL = 'http://nomads.ncep.noaa.gov/pub/data/nccf/com/wave/prod/'

# =============================================================================
# Network Configuration
# =============================================================================

# IP prefixes that indicate FRF internal network
FRF_IP_PREFIXES = ('134.164', '10.0.0')

# Default timeout for network requests (seconds)
DEFAULT_TIMEOUT_SECONDS = 60

# Maximum retry attempts for network operations
# Used in getdata/getDataFRF.py getnc() function when fetching NetCDF files from THREDDS servers
# If a network error occurs, the function will retry up to this many times before giving up
MAX_RETRY_ATTEMPTS = 3

# =============================================================================
# Time Configuration
# =============================================================================

# Argus imagery is available at 30-minute intervals
ARGUS_IMAGE_INTERVAL_MINUTES = 30

# Default time rounding (seconds)
# Used in getdata/getDataFRF.py getnc() function to round timestamps from NetCDF files
# This ensures consistent time intervals when retrieving oceanographic and meteorological data
DEFAULT_TIME_ROUND_SECONDS = 60

# NetCDF time units standard
TIME_UNITS = 'seconds since 1970-01-01 00:00:00'

# =============================================================================
# Argus Image Types
# =============================================================================

ARGUS_IMAGE_TYPES = ('timex', 'var', 'snap', 'bright', 'dark')

# =============================================================================
# Helper Functions
# =============================================================================

# =============================================================================
# Server Detection Cache (thread-safe)
# =============================================================================
# Cache is computed once at first use to avoid repeated socket operations.
# Both FRF and CHL servers are trusted government endpoints - server selection
# only affects performance (local vs remote), not security.

# Use RLock (reentrant lock) because get_thredds_server calls _get_cached_ip
# while holding the lock
_cache_lock = threading.RLock()
_cached_ip_address = None
_cached_server_result = None


def _get_cached_ip():
    """Get the cached IP address, computing it once if needed (thread-safe).

    Returns:
        str: The machine's IP address, or empty string if detection failed.
    """
    global _cached_ip_address

    # Fast path: check without lock first (safe because we only write once)
    if _cached_ip_address is not None:
        return _cached_ip_address

    with _cache_lock:
        # Double-check after acquiring lock
        if _cached_ip_address is not None:
            return _cached_ip_address

        try:
            _cached_ip_address = socket.gethostbyname(socket.gethostname())
        except OSError:
            # Covers socket.error, socket.gaierror, socket.herror in Python 3
            _cached_ip_address = ''

    return _cached_ip_address


def get_thredds_server(server=None, ip_address=None):
    """Select appropriate THREDDS server based on network location (thread-safe).

    Results are cached at module level for auto-detection (when server=None
    and ip_address=None) to avoid repeated socket operations.

    Args:
        server (str, optional): Force server selection. 'FRF' for local,
            'CHL' for public. If None, auto-detect based on IP.
        ip_address (str, optional): IP address to check. If None,
            uses cached machine IP.

    Returns:
        tuple: (server_url, server_prefix) where server_prefix is 'FRF' or 'frf'
            for use in constructing data paths.
    """
    global _cached_server_result

    # Fast path: return cached result for default auto-detection case
    if server is None and ip_address is None:
        # Check without lock first
        if _cached_server_result is not None:
            return _cached_server_result

        with _cache_lock:
            # Double-check after acquiring lock
            if _cached_server_result is not None:
                return _cached_server_result

            # Compute and cache the result
            detected_ip = _get_cached_ip()
            on_frf_network = detected_ip.startswith(FRF_IP_PREFIXES)

            if on_frf_network:
                _cached_server_result = (THREDDS_FRF_LOCAL, 'FRF')
            else:
                _cached_server_result = (THREDDS_CHL_PUBLIC, 'frf')

            return _cached_server_result

    # Non-cached path: explicit server or ip_address provided
    if ip_address is None:
        ip_address = _get_cached_ip()

    # Validate ip_address is a string to prevent type confusion
    if not isinstance(ip_address, str):
        ip_address = ''

    on_frf_network = ip_address.startswith(FRF_IP_PREFIXES)

    if server == 'FRF' or (server is None and on_frf_network):
        return THREDDS_FRF_LOCAL, 'FRF'
    else:
        return THREDDS_CHL_PUBLIC, 'frf'


def is_frf_network(ip_address=None):
    """Check if the current machine is on the FRF internal network.

    Args:
        ip_address (str, optional): IP address to check. If None,
            uses cached machine IP.

    Returns:
        bool: True if on FRF network, False otherwise.
    """
    if ip_address is None:
        ip_address = _get_cached_ip()

    # Validate ip_address is a string to prevent type confusion
    if not isinstance(ip_address, str):
        return False

    return ip_address.startswith(FRF_IP_PREFIXES)


def clear_server_cache():
    """Clear the cached server detection results (thread-safe).

    Useful for testing or if network configuration changes during runtime.
    """
    global _cached_ip_address, _cached_server_result

    with _cache_lock:
        _cached_ip_address = None
        _cached_server_result = None
