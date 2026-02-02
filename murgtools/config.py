"""Centralized configuration for murgtools library.

This module contains all hardcoded URLs, server addresses, and configuration
values used throughout the murgtools package. Centralizing these values makes
it easier to update endpoints and ensures consistency across modules.
"""

import socket

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
SURVEY_TRANSECTS_URL = 'http://134.164.129.55/thredds/dodsC/FRF/geomorphology/elevationTransects/survey/surveyTransects.ncml'
WAVE_8M_ARRAY_URL = 'http://134.164.129.55/thredds/dodsC/FRF/oceanography/waves/8m-array/2017/FRF-ocean_waves_8m-array_201707.nc'

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


def get_thredds_server(server=None, ip_address=None):
    """Select appropriate THREDDS server based on network location.

    Args:
        server (str, optional): Force server selection. 'FRF' for local,
            'CHL' for public. If None, auto-detect based on IP.
        ip_address (str, optional): IP address to check. If None,
            uses current machine's IP.

    Returns:
        tuple: (server_url, server_prefix) where server_prefix is 'FRF' or 'frf'
            for use in constructing data paths.
    """
    if ip_address is None:
        try:
            ip_address = socket.gethostbyname(socket.gethostname())
        except socket.error:
            ip_address = ''

    is_frf_network = ip_address.startswith(FRF_IP_PREFIXES)

    if server == 'FRF' or (server is None and is_frf_network):
        return THREDDS_FRF_LOCAL, 'FRF'
    else:
        return THREDDS_CHL_PUBLIC, 'frf'


def is_frf_network(ip_address=None):
    """Check if the current machine is on the FRF internal network.

    Args:
        ip_address (str, optional): IP address to check. If None,
            uses current machine's IP.

    Returns:
        bool: True if on FRF network, False otherwise.
    """
    if ip_address is None:
        try:
            ip_address = socket.gethostbyname(socket.gethostname())
        except socket.error:
            return False

    return ip_address.startswith(FRF_IP_PREFIXES)
