'documented SB 12/2/17/'
import warnings
from dataclasses import dataclass
from typing import Optional, Union

import numpy as np
import pandas as pd
import pyproj


# =============================================================================
# Key Name Mapping: Legacy -> New (with units)
# =============================================================================
# Legacy keys are preserved for backward compatibility.
# New keys include units for clarity.
#
# Mapping:
#   xFRF -> xFRF_m (meters)
#   yFRF -> yFRF_m (meters)
#   StateplaneE -> StateplaneE_m (meters)
#   StateplaneN -> StateplaneN_m (meters)
#   Lat -> Lat_NAD83_deg (degrees)
#   Lon -> Lon_NAD83_deg (degrees)
#   lat -> Lat_NAD83_deg (degrees)
#   lon -> Lon_NAD83_deg (degrees)
#   utmE -> utmE_m (meters)
#   utmN -> utmN_m (meters)
# =============================================================================

_LEGACY_TO_NEW_KEYS = {
    'xFRF': 'xFRF_m',
    'yFRF': 'yFRF_m',
    'StateplaneE': 'StateplaneE_m',
    'StateplaneN': 'StateplaneN_m',
    'Lat': 'Lat_NAD83_deg',
    'Lon': 'Lon_NAD83_deg',
    'lat': 'Lat_NAD83_deg',
    'lon': 'Lon_NAD83_deg',
    'utmE': 'utmE_m',
    'utmN': 'utmN_m',
}

_NEW_TO_LEGACY_KEYS = {v: k for k, v in _LEGACY_TO_NEW_KEYS.items()}


class DeprecatingDict(dict):
    """A dictionary that warns when accessing legacy keys.

    This class wraps coordinate transformation results to provide both
    legacy keys (for backward compatibility) and new keys (with units).
    Accessing legacy keys will emit a DeprecationWarning.

    Args:
        data: Initial dictionary data.
        warn_on_legacy: If True, warn when legacy keys are accessed.
            Set to False to disable warnings (e.g., during internal use).

    Example:
        >>> result = FRFcoord(100, 200, coordType='FRF')
        >>> result['xFRF_m']  # New key with units (preferred)
        100.0
        >>> result['xFRF']    # Legacy key (works but emits warning)
        100.0
    """

    def __init__(self, data=None, warn_on_legacy=True):
        """Initialize DeprecatingDict with optional data."""
        super().__init__(data or {})
        self._warn_on_legacy = warn_on_legacy

    def __getitem__(self, key):
        """Get item, warning if legacy key is accessed."""
        if self._warn_on_legacy and key in _LEGACY_TO_NEW_KEYS:
            new_key = _LEGACY_TO_NEW_KEYS[key]
            if new_key in self:
                warnings.warn(
                    f"Key '{key}' is deprecated, use '{new_key}' instead. "
                    "Legacy keys will be removed in murgtools v2.0.",
                    DeprecationWarning,
                    stacklevel=2
                )
        return super().__getitem__(key)

    def get(self, key, default=None):
        """Get item with default, warning if legacy key is accessed."""
        if self._warn_on_legacy and key in _LEGACY_TO_NEW_KEYS:
            new_key = _LEGACY_TO_NEW_KEYS[key]
            if new_key in self:
                warnings.warn(
                    f"Key '{key}' is deprecated, use '{new_key}' instead. "
                    "Legacy keys will be removed in murgtools v2.0.",
                    DeprecationWarning,
                    stacklevel=2
                )
        return super().get(key, default)


def _add_unit_keys(result_dict):
    """Add new keys with units alongside legacy keys.

    Args:
        result_dict: Dictionary with legacy keys.

    Returns:
        DeprecatingDict with both legacy and new keys.
    """
    enhanced = dict(result_dict)
    for legacy_key, new_key in _LEGACY_TO_NEW_KEYS.items():
        if legacy_key in enhanced:
            enhanced[new_key] = enhanced[legacy_key]
    return DeprecatingDict(enhanced)


@dataclass
class CoordinateResult:
    """Coordinate transformation result with multiple reference frames.

    A dataclass providing attribute-based access to coordinate values across
    FRF local, NC State Plane, geographic (Lat/Lon), and UTM systems.

    This class supports both attribute access (result.xFRF_m) and dictionary-style
    access (result['xFRF_m']) for backward compatibility.

    Attributes:
        xFRF_m: FRF cross-shore coordinate in meters. Positive = seaward.
        yFRF_m: FRF alongshore coordinate in meters. Positive = north.
        StateplaneE_m: NC State Plane Easting in meters.
        StateplaneN_m: NC State Plane Northing in meters.
        Lat_NAD83_deg: Latitude in decimal degrees (NAD83).
        Lon_NAD83_deg: Longitude in decimal degrees (NAD83). Negative for west.
        utmE_m: UTM Easting in meters. None if not computed.
        utmN_m: UTM Northing in meters. None if not computed.
        utm_zone: UTM zone string (e.g., '18S'). None if not computed.

    Example:
        >>> result = FRFcoord(566.93, 515.11, coordType='FRF', return_dataclass=True)
        >>> result.xFRF_m
        566.93
        >>> result.Lat_NAD83_deg
        36.1836
        >>> result['StateplaneE_m']  # Dict-style access also works
        902307.92
    """

    xFRF_m: Union[float, np.ndarray]
    yFRF_m: Union[float, np.ndarray]
    StateplaneE_m: Union[float, np.ndarray]
    StateplaneN_m: Union[float, np.ndarray]
    Lat_NAD83_deg: Union[float, np.ndarray]
    Lon_NAD83_deg: Union[float, np.ndarray]
    utmE_m: Optional[Union[float, np.ndarray]] = None
    utmN_m: Optional[Union[float, np.ndarray]] = None
    utm_zone: Optional[str] = None

    def __getitem__(self, key):
        """Support dictionary-style access for backward compatibility.

        Args:
            key: Attribute name to access. Both legacy and new key names work.

        Returns:
            The value of the requested attribute.

        Raises:
            KeyError: If the key doesn't correspond to a valid attribute.
        """
        # Map legacy keys to new attribute names (reuse module-level mapping)
        attr_name = _LEGACY_TO_NEW_KEYS.get(key, key)
        if hasattr(self, attr_name):
            return getattr(self, attr_name)
        raise KeyError(f"'{key}' is not a valid coordinate key")

    def __contains__(self, key):
        """Check if key exists in coordinate result."""
        attr_name = _LEGACY_TO_NEW_KEYS.get(key, key)
        return hasattr(self, attr_name) and getattr(self, attr_name) is not None

    def to_dict(self, include_legacy=True):
        """Convert to dictionary.

        Args:
            include_legacy: If True, include both legacy and new key names.
                Defaults to True for backward compatibility.

        Returns:
            Dictionary with coordinate values.
        """
        result = {
            'xFRF_m': self.xFRF_m,
            'yFRF_m': self.yFRF_m,
            'StateplaneE_m': self.StateplaneE_m,
            'StateplaneN_m': self.StateplaneN_m,
            'Lat_NAD83_deg': self.Lat_NAD83_deg,
            'Lon_NAD83_deg': self.Lon_NAD83_deg,
        }
        if self.utmE_m is not None:
            result['utmE_m'] = self.utmE_m
        if self.utmN_m is not None:
            result['utmN_m'] = self.utmN_m
        if self.utm_zone is not None:
            result['utm_zone'] = self.utm_zone

        if include_legacy:
            result['xFRF'] = self.xFRF_m
            result['yFRF'] = self.yFRF_m
            result['StateplaneE'] = self.StateplaneE_m
            result['StateplaneN'] = self.StateplaneN_m
            result['Lat'] = self.Lat_NAD83_deg
            result['Lon'] = self.Lon_NAD83_deg
            if self.utmE_m is not None:
                result['utmE'] = self.utmE_m
            if self.utmN_m is not None:
                result['utmN'] = self.utmN_m

        return result

    @classmethod
    def from_dict(cls, data):
        """Create CoordinateResult from dictionary.

        Args:
            data: Dictionary with coordinate values. Supports both legacy
                and new key names.

        Returns:
            CoordinateResult instance.
        """
        # Try new keys first, fall back to legacy
        xFRF = data.get('xFRF_m', data.get('xFRF'))
        yFRF = data.get('yFRF_m', data.get('yFRF'))
        spE = data.get('StateplaneE_m', data.get('StateplaneE'))
        spN = data.get('StateplaneN_m', data.get('StateplaneN'))
        lat = data.get('Lat_NAD83_deg', data.get('Lat', data.get('lat')))
        lon = data.get('Lon_NAD83_deg', data.get('Lon', data.get('lon')))
        utmE = data.get('utmE_m', data.get('utmE'))
        utmN = data.get('utmN_m', data.get('utmN'))
        utm_zone = data.get('utm_zone')

        # Construct zone string if we have zone number and letter
        if utm_zone is None and 'zn' in data and 'zl' in data:
            zn = data['zn']
            zl = data['zl']
            if np.size(zn) == 1:
                zn_val = zn[0] if hasattr(zn, '__getitem__') else zn
                zl_val = zl[0] if hasattr(zl, '__getitem__') else zl
                utm_zone = f"{zn_val}{zl_val}"

        return cls(
            xFRF_m=xFRF,
            yFRF_m=yFRF,
            StateplaneE_m=spE,
            StateplaneN_m=spN,
            Lat_NAD83_deg=lat,
            Lon_NAD83_deg=lon,
            utmE_m=utmE,
            utmN_m=utmN,
            utm_zone=utm_zone,
        )

def FRF2ncsp(xFRF, yFRF):
    """Convert FRF local coordinates to NC State Plane coordinates.

    Based on Kent Hathaway's code and Bill Birkemeier's calculations.
    Written by Kent Hathaway, 15 Dec 2014.
    Translated from Matlab to Python 2015-11-30 - Spicer Bak.

    Uses new fit (angles and scales) Bill Birkemeier determined in Nov 2014.
    Uses NAD83-2011.

    Reference constants (NAD83-86, 2014):
        Origin Latitude:          36.1775975 deg
        Origin Longitude:         75.7496860 deg
        m/degLat:                 110963.357
        m/degLon:                 89953.364
        GridAngle:                18.1465 deg
        Angle FRF to Lat/Lon:     71.8535 deg
        Angle FRF to State Grid:  69.9747 deg
        FRF Origin Northing:      274093.1562 m
        FRF Origin Easting:       901951.6805 m

    Args:
        xFRF: FRF cross-shore coordinate (m). Positive = seaward.
        yFRF: FRF alongshore coordinate (m). Positive = north.

    Returns:
        DeprecatingDict with keys:
            xFRF, xFRF_m: Input cross-shore coordinate (m)
            yFRF, yFRF_m: Input alongshore coordinate (m)
            StateplaneE, StateplaneE_m: NC State Plane Easting (m)
            StateplaneN, StateplaneN_m: NC State Plane Northing (m)

    Example:
        >>> result = FRF2ncsp(566.93, 515.11)  # south rail at 1860
        >>> result['StateplaneE_m']
        902307.92
        >>> result['StateplaneN_m']
        274771.22
    """
    r2d = 180.0 / np.pi

    Eom = 901951.6805  # E Origin State Plane (m)
    Nom = 274093.1562  # N Origin State Plane (m)
    spAngle = (90 - 69.974707831) / r2d
    X = xFRF
    Y = yFRF

    R = np.sqrt(X ** 2 + Y ** 2)
    Ang1 = np.arctan2(X, Y)  # CW from Y
    # to state plane
    Ang2 = Ang1 - spAngle
    AspN = R * np.cos(Ang2)
    AspE = R * np.sin(Ang2)
    spN = AspN + Nom
    spE = AspE + Eom
    out = {'xFRF': xFRF, 'yFRF': yFRF, 'StateplaneE': spE, 'StateplaneN': spN}
    return _add_unit_keys(out)

def ncsp2FRF(p1, p2):
    """Convert NC State Plane coordinates to FRF local coordinates.

    Based on Kent Hathaway's code.
    15 Dec 2014 - Kent Hathaway.
    Translated from Matlab to Python 2015-11-30 - Spicer Bak.

    Uses new fit (angles and scales) Bill Birkemeier determined in Nov 2014.
    Uses NAD83-2011.

    Reference constants (NAD83-86, 2014):
        Origin Latitude:          36.1775975 deg
        Origin Longitude:         75.7496860 deg
        m/degLat:                 110963.357
        m/degLon:                 89953.364
        GridAngle:                18.1465 deg
        Angle FRF to Lat/Lon:     71.8535 deg
        Angle FRF to State Grid:  69.9747 deg
        FRF Origin Northing:      274093.1562 m
        FRF Origin Easting:       901951.6805 m

    Args:
        p1: NC State Plane Easting (m)
        p2: NC State Plane Northing (m)

    Returns:
        DeprecatingDict with keys:
            xFRF, xFRF_m: FRF cross-shore coordinate (m)
            yFRF, yFRF_m: FRF alongshore coordinate (m)
            StateplaneE, StateplaneE_m: Input NC State Plane Easting (m)
            StateplaneN, StateplaneN_m: Input NC State Plane Northing (m)

    Example:
        >>> result = ncsp2FRF(902307.92, 274771.22)  # south rail at 1860
        >>> result['xFRF_m']
        566.93
        >>> result['yFRF_m']
        515.11
    """
    r2d = 180.0 / np.pi
    Eom = 901951.6805  # E Origin State Plane (m)
    Nom = 274093.1562  # N Origin State Plane (m)
    spAngle = (90 - 69.974707831) / r2d

    spE = p1
    spN = p2  # designating stateplane vars

    # to FRF coords
    spLengE = p1 - Eom
    spLengN = p2 - Nom
    R = np.sqrt(spLengE ** 2 + spLengN ** 2)
    Ang1 = np.arctan2(spLengE, spLengN)
    Ang2 = Ang1 + spAngle
    # to FRF
    X = R * np.sin(Ang2)
    Y = R * np.cos(Ang2)
    ans = {'xFRF': X,
           'yFRF': Y,
           'StateplaneE': spE,
           'StateplaneN': spN}
    return _add_unit_keys(ans)

def ncsp2LatLon(spE, spN):
    """Convert NC State Plane coordinates to latitude/longitude.

    Uses pyproj to transform from NC State Plane (EPSG:3358) to WGS84.

    Test points from USACE SMS modeling system:
        spE1 = 901926.2 m, spN1 = 273871.0 m -> Lat = 36.17560399, Lon = -75.75004989
        spE2 = 902556.4 m, spN2 = 276229.5 m -> Lat = 36.19666112, Lon = -75.47218285

    Args:
        spE: NC State Plane Easting (m)
        spN: NC State Plane Northing (m)

    Returns:
        DeprecatingDict with keys:
            lat, Lat_NAD83_deg: Latitude (decimal degrees, NAD83)
            lon, Lon_NAD83_deg: Longitude (decimal degrees, NAD83)
            StateplaneE, StateplaneE_m: Input NC State Plane Easting (m)
            StateplaneN, StateplaneN_m: Input NC State Plane Northing (m)

    Example:
        >>> result = ncsp2LatLon(901926.2, 273871.0)
        >>> result['Lat_NAD83_deg']
        36.17560399
        >>> result['Lon_NAD83_deg']
        -75.75004989
    """
    EPSG = 3358  # NC State Plane NAD83 (m)
    # NC stateplane NAD83 to WGS84 (EPSG:4326)
    transformer = pyproj.Transformer.from_crs(
        f"epsg:{EPSG}",
        "epsg:4326",
        always_xy=True
    )
    lon, lat = transformer.transform(spE, spN)

    return _add_unit_keys({'lon': lon, 'lat': lat, 'StateplaneE': spE, 'StateplaneN': spN})

def LatLon2ncsp(lon, lat):
    """Convert latitude/longitude to NC State Plane coordinates.

    Uses pyproj to transform from WGS84 to NC State Plane (EPSG:3358).

    Test points from USACE SMS modeling system:
        Lat = 36.17560399, Lon = -75.75004989 -> spE = 901926.2 m, spN = 273871.0 m
        Lat = 36.19666112, Lon = -75.47218285 -> spE = 902556.4 m, spN = 276229.5 m

    Args:
        lon: Longitude (decimal degrees, NAD83). Negative for western hemisphere.
        lat: Latitude (decimal degrees, NAD83).

    Returns:
        DeprecatingDict with keys:
            lat, Lat_NAD83_deg: Input latitude (decimal degrees)
            lon, Lon_NAD83_deg: Input longitude (decimal degrees)
            StateplaneE, StateplaneE_m: NC State Plane Easting (m)
            StateplaneN, StateplaneN_m: NC State Plane Northing (m)

    Example:
        >>> result = LatLon2ncsp(-75.75004989, 36.17560399)
        >>> result['StateplaneE_m']
        901926.2
        >>> result['StateplaneN_m']
        273871.0
    """
    EPSG = 3358  # NC State Plane NAD83 (m)
    # WGS84 (EPSG:4326) to NC stateplane NAD83
    transformer = pyproj.Transformer.from_crs(
        "epsg:4326",
        f"epsg:{EPSG}",
        always_xy=True
    )
    spE, spN = transformer.transform(lon, lat)

    ans = {'lon': lon, 'lat': lat, 'StateplaneE': spE, 'StateplaneN': spN}
    return _add_unit_keys(ans)

def FRFcoord(p1, p2, coordType=None, return_dataclass=False):
    """Universal coordinate converter for FRF, State Plane, Lat/Lon, and UTM.

    Automatically detects input coordinate type based on value ranges,
    or use coordType to force interpretation. Converts to all other systems.

    Uses Kent Hathaway's original code and pyproj for transformations.
    Based on Bill Birkemeier's 2014 calibration. Uses NAD83-2011.

    Reference constants (NAD83-86, 2014):
        Origin Latitude:          36.1775975 deg
        Origin Longitude:         75.7496860 deg
        FRF Origin Northing:      274093.1562 m
        FRF Origin Easting:       901951.6805 m

    Args:
        p1: Input coordinate - one of:
            - FRF xFRF (m): cross-shore, positive = seaward
            - Longitude (deg): negative for western hemisphere
            - State Plane Easting (m)
            - UTM Easting (m)
        p2: Input coordinate - one of:
            - FRF yFRF (m): alongshore, positive = north
            - Latitude (deg)
            - State Plane Northing (m)
            - UTM Northing (m)
        coordType: Force input interpretation. Options:
            - 'FRF': FRF local coordinates
            - 'LL', 'geographic', 'LatLon': Lat/Lon (lon, lat order)
            - 'spnc', 'ncsp': NC State Plane
            - None: Auto-detect (default)
        return_dataclass: If True, return a CoordinateResult dataclass
            instead of a dictionary. Defaults to False for backward
            compatibility.

    Returns:
        If return_dataclass=False (default):
            DeprecatingDict with keys (legacy and new with units):
                xFRF, xFRF_m: FRF cross-shore coordinate (m)
                yFRF, yFRF_m: FRF alongshore coordinate (m)
                StateplaneE, StateplaneE_m: NC State Plane Easting (m)
                StateplaneN, StateplaneN_m: NC State Plane Northing (m)
                Lat, Lat_NAD83_deg: Latitude (decimal degrees, NAD83)
                Lon, Lon_NAD83_deg: Longitude (decimal degrees, NAD83)
                utmE, utmE_m: UTM Easting (m)
                utmN, utmN_m: UTM Northing (m)

        If return_dataclass=True:
            CoordinateResult dataclass with attribute access.

    Example:
        >>> # From FRF coordinates (dict return)
        >>> result = FRFcoord(566.93, 515.11, coordType='FRF')
        >>> result['Lat_NAD83_deg']
        36.1836
        >>> result['StateplaneE_m']
        902307.92

        >>> # From FRF coordinates (dataclass return)
        >>> result = FRFcoord(566.93, 515.11, coordType='FRF', return_dataclass=True)
        >>> result.Lat_NAD83_deg
        36.1836
        >>> result.StateplaneE_m
        902307.92

        >>> # From Lat/Lon
        >>> result = FRFcoord(-75.7454804, 36.1836, coordType='LL')
        >>> result['xFRF_m']
        566.93
    """
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
        UTM1 = (p1 > 300000).all()
        UTM2 = (p2 > 1000000).all()
        FRF1 = (p1 > -10000).all() and (p1 < 10000).all()
        FRF2 = (p2 > -10000).all() and (p2 < 10000).all()
    else:
        LL1 = np.floor(np.absolute(p1)) == 75
        LL2 = np.floor(p2) == 36
        SP1 = p1 > 800000
        SP2 = p2 > 200000
        UTM1 = p1 > 300000
        UTM2 = p2 > 1000000
        FRF1 = (p1 > -10000) and (p1 < 10000)
        FRF2 = (p2 > -10000) and (p2 < 10000)

    # Determine Data type
    if LL1 and LL2 or coordType in ['LL', 'geographic', 'LatLon']:  # lat/lon input
        sp = LatLon2ncsp(p1, p2)  # convert from lon/lat to state plane
        frf = ncsp2FRF(sp['StateplaneE'], sp['StateplaneN'])  # convert from nc state plane to FRF coords
        utm = LatLon2utm(p2, p1)  # convert to utm from lon/lat
        coordsOut = {'xFRF': frf['xFRF'], 'yFRF': frf['yFRF'], 'StateplaneE': sp['StateplaneE'],
                     'StateplaneN': sp['StateplaneN'], 'Lat': p2, 'Lon': p1, 'utmE': utm['utmE'], 'utmN': utm['utmN']}

    elif SP1 and SP2 or coordType in ['spnc', 'ncsp']:  # state plane input
        frf = ncsp2FRF(p1, p2)     # convert state plane to FRF
        ll = ncsp2LatLon(p1, p2)  # convert state plane to Lat Lon
        utm = LatLon2utm(ll['lat'], ll['lon'])
        coordsOut = {'xFRF': frf['xFRF'], 'yFRF': frf['yFRF'], 'StateplaneE': p1,
                     'StateplaneN': p2, 'Lat': ll['lat'], 'Lon': ll['lon'], 'utmE': utm['utmE'], 'utmN': utm['utmN']}

    elif UTM1 and UTM2:  # UTM input
        ll = utm2LatLon(p1, p2, 18, 'S')
        sp = LatLon2ncsp(ll['lon'], ll['lat'])
        frf = ncsp2FRF(sp['StateplaneE'], sp['StateplaneN'])
        coordsOut = {'xFRF': frf['xFRF'], 'yFRF': frf['yFRF'], 'StateplaneE': sp['StateplaneE'],
                     'StateplaneN': sp['StateplaneN'], 'Lat': ll['lat'], 'Lon': ll['lon'], 'utmE': p1, 'utmN': p2}

    elif (FRF1 and FRF2) or coordType in ['FRF']:  # FRF input
        # this is FRF in
        sp = FRF2ncsp(p1, p2)
        ll = ncsp2LatLon(sp['StateplaneE'], sp['StateplaneN'])
        utm = LatLon2utm(ll['lat'], ll['lon'])
        coordsOut = {'xFRF': p1, 'yFRF': p2, 'StateplaneE': sp['StateplaneE'],
                     'StateplaneN': sp['StateplaneN'], 'Lat': ll['lat'], 'Lon': ll['lon'], 'utmE': utm['utmE'], 'utmN': utm['utmN']}

    else:
        warnings.warn(
            'FRFcoord could not determine input coordinate type, returning NaNs. '
            'Use coordType parameter to specify input type.',
            UserWarning
        )
        coordsOut = {'xFRF': float('NaN'), 'yFRF': float('NaN'), 'StateplaneE': float('NaN'),
             'StateplaneN': float('NaN'), 'Lat': float('NaN'), 'Lon': float('NaN')}

    result = _add_unit_keys(coordsOut)

    if return_dataclass:
        return CoordinateResult.from_dict(result)
    return result

def utm2LatLon(utmE, utmN, zn, zl):
    """Convert UTM coordinates to latitude/longitude.

    Uses the utm library to convert UTM points to geographic coordinates.

    Args:
        utmE: UTM Easting (m)
        utmN: UTM Northing (m)
        zn: UTM zone number (1-60)
        zl: UTM zone letter (e.g., 'S' for FRF area)

    Returns:
        DeprecatingDict with keys:
            lat, Lat_NAD83_deg: Latitude (decimal degrees)
            lon, Lon_NAD83_deg: Longitude (decimal degrees)

    Example:
        >>> result = utm2LatLon(430000, 4006000, 18, 'S')
        >>> result['Lat_NAD83_deg']
        36.18...
    """
    import utm

    # check to see if points are...
    assert np.size(utmE) == np.size(utmN), 'utm2LatLon error: UTM point vectors must be equal lengths'

    # check to see if zn, zl are either both length 1 or the same length as p1, p2
    if np.size(zn) == 1:
        assert np.size(zn) == np.size(zl), 'utm2LatLon error: UTM zone number and letter must both be of length 1 or length of UTM point vectors'
    else:
        assert np.size(zn) == np.size(zl) == np.size(utmE), 'utm2LatLon error: UTM zone number and letter must both be of length 1 or length of UTM point vectors'

    columns = ['utmE', 'utmN', 'zn', 'zl']

    df = pd.DataFrame(index=list(range(0, np.size(utmE))), columns=columns)

    # Handle 2D arrays by flattening
    if np.ndim(utmE) > 1:
        utmE = np.asarray(utmE).flatten()
        utmN = np.asarray(utmN).flatten()

    df['utmE'] = utmE
    df['utmN'] = utmN
    df['zn'] = zn
    df['zl'] = zl

    df['ll'] = df.apply(lambda x: utm.to_latlon(x.utmE, x.utmN, int(x.zn), x.zl), axis=1)

    L1, L2 = list(zip(*np.asarray(df['ll'])))

    return_dict = {}
    return_dict['lat'] = np.asarray(L1)
    return_dict['lon'] = np.asarray(L2)

    return _add_unit_keys(return_dict)

def LatLon2utm(lat, lon):
    """Convert latitude/longitude to UTM coordinates.

    Uses the utm library to convert geographic coordinates to UTM.

    Args:
        lat: Latitude (decimal degrees, NAD83/WGS84)
        lon: Longitude (decimal degrees, NAD83/WGS84). Negative for western hemisphere.

    Returns:
        DeprecatingDict with keys:
            utmE, utmE_m: UTM Easting (m)
            utmN, utmN_m: UTM Northing (m)
            zn: UTM zone number (1-60)
            zl: UTM zone letter

    Example:
        >>> result = LatLon2utm(36.1836, -75.7454804)
        >>> result['utmE_m']
        430000...
        >>> result['zn']
        18
    """
    import utm

    # check to see if points are...
    assert np.size(lat) == np.size(lon), 'LatLon2utm error: lat lon coordinate vectors must be equal lengths'

    columns = ['lat', 'lon']

    df = pd.DataFrame(index=list(range(0, np.size(lat))), columns=columns)

    df['lat'] = lat
    df['lon'] = lon
    try:
        df['utm'] = df.apply(lambda x: utm.from_latlon(x.lat, x.lon), axis=1)
    except:
        df['utm'] = utm.from_latlon(df.lat.values, df.lon.values)

    utmE, utmN, zn, zl = list(zip(*np.asarray(df['utm'])))

    return_dict = {}
    return_dict['utmE'] = np.asarray(utmE)
    return_dict['utmN'] = np.asarray(utmN)
    return_dict['zn'] = np.asarray(zn)
    return_dict['zl'] = np.asarray(zl)

    return _add_unit_keys(return_dict)

def utm2ncsp(utmE, utmN, zn, zl):
    """Convert UTM coordinates to NC State Plane.

    Uses the utm library to convert through Lat/Lon to NC State Plane.

    Args:
        utmE: UTM Easting (m)
        utmN: UTM Northing (m)
        zn: UTM zone number (1-60)
        zl: UTM zone letter (e.g., 'S' for FRF area)

    Returns:
        DeprecatingDict with keys:
            easting: NC State Plane Easting (m)
            northing: NC State Plane Northing (m)

    Example:
        >>> result = utm2ncsp(430000, 4006000, 18, 'S')
        >>> result['easting']
        901926...
    """
    import utm

    # so, all this does it go through Lat/Lon to get to ncsp..

    # check to see if points are...
    assert np.size(utmE) == np.size(utmN), 'utm2ncsp error: UTM point vectors must be equal lengths'

    # check to see if zn, zl are either both length 1 or the same length as p1, p2
    if np.size(zn) == 1:
        assert np.size(zn) == np.size(zl), 'utm2ncsp error: UTM zone number and letter must both be of length 1 or length of UTM point vectors'
    else:
        assert np.size(zn) == np.size(zl) == np.size(utmE), 'utm2ncsp error: UTM zone number and letter must both be of length 1 or length of UTM point vectors'

    columns = ['utmE', 'utmN', 'zn', 'zl']

    df = pd.DataFrame(index=list(range(0, np.size(utmE))), columns=columns)

    df['utmE'] = utmE
    df['utmN'] = utmN
    df['zn'] = zn
    df['zl'] = zl

    df['ll'] = df.apply(lambda x: utm.to_latlon(x.utmE, x.utmN, x.zn, x.zl), axis=1)

    L1, L2 = list(zip(*np.asarray(df['ll'])))

    ncsp_dict = LatLon2ncsp(np.asarray(L2), np.asarray(L1))

    return_dict = {}
    return_dict['easting'] = np.asarray(ncsp_dict['StateplaneE'])
    return_dict['northing'] = np.asarray(ncsp_dict['StateplaneN'])

    return DeprecatingDict(return_dict)

def ncsp2utm(easting, northing):
    """Convert NC State Plane coordinates to UTM.

    Converts through Lat/Lon to get to UTM.

    Args:
        easting: NC State Plane Easting (m)
        northing: NC State Plane Northing (m)

    Returns:
        DeprecatingDict with keys:
            utmE, utmE_m: UTM Easting (m)
            utmN, utmN_m: UTM Northing (m)
            zn: UTM zone number
            zl: UTM zone letter

    Example:
        >>> result = ncsp2utm(902307.92, 274771.22)
        >>> result['utmE_m']
        430000...
    """
    # all this does it go through lat/lon to get to utm...

    assert np.shape(easting) == np.shape(northing), 'ncsp2utm Error: northing and easting vectors must be same length'

    ll_dict = ncsp2LatLon(easting, northing)
    utm_dict = LatLon2utm(ll_dict['lat'], ll_dict['lon'])

    return utm_dict


# =============================================================================
# Vertical Coordinate Transformations
# =============================================================================
# These functions convert between ellipsoidal and orthometric heights.
#
# IMPORTANT: WGS84 vs NAD83 differences
# --------------------------------------
# WGS84 and NAD83 use different ellipsoids and reference frames:
#   - NAD83 uses GRS80 ellipsoid (a=6378137.0m, f=1/298.257222101)
#   - WGS84 uses WGS84 ellipsoid (a=6378137.0m, f=1/298.257223563)
#
# While the ellipsoids are nearly identical (~0.1mm difference in flattening),
# the reference frame realizations differ:
#   - NAD83(2011) is fixed to the North American plate
#   - WGS84 (G2139) is a global frame aligned with ITRF
#
# At the FRF, the horizontal difference is typically <1m, but for vertical
# transformations, the choice of geoid model matters:
#   - NAVD88 uses GEOID18 referenced to NAD83/GRS80 (~-35.5m at FRF)
#   - EGM96/EGM2008 are referenced to WGS84 (~-35.0m at FRF)
#
# Common use cases:
#   - GPS/GNSS measurements: typically WGS84 ellipsoidal height
#   - RTK surveys in US: typically NAD83 ellipsoidal height
#   - FRF surveys/DEMs: NAVD88 orthometric height (requires NAD83)
#   - Ocean models: often MSL or EGM-based vertical datums
# =============================================================================

# Approximate geoid separations at FRF (Duck, NC)
# These are used as fallbacks when PROJ grid files are unavailable
_FRF_GEOID_SEPARATIONS = {
    # NAD83/GRS80 ellipsoid to various vertical datums
    ('NAD83', 'NAVD88'): -35.5,    # GEOID18 at FRF: N = -35.5m
    ('NAD83', 'EGM96'): -35.2,     # Approximate, requires datum shift
    ('NAD83', 'EGM2008'): -35.3,   # Approximate, requires datum shift
    # WGS84 ellipsoid to various vertical datums
    ('WGS84', 'NAVD88'): -35.5,    # Requires NAD83<->WGS84 shift (~0.0m horiz)
    ('WGS84', 'EGM96'): -35.0,     # EGM96 referenced to WGS84
    ('WGS84', 'EGM2008'): -35.1,   # EGM2008 referenced to WGS84
}


def ellipsoid_to_orthometric(lat, lon, ellipsoid_height_m, from_crs='NAD83', to_vertical='NAVD88'):
    """Convert ellipsoidal height to orthometric height.

    Transforms height above the ellipsoid (from GPS/GNSS) to height above
    the geoid (orthometric height used in surveys and DEMs).

    The conversion uses the appropriate geoid model:
    - NAVD88: Uses GEOID18/GEOID12B for NAD83 (US national vertical datum)
    - EGM96/EGM2008: Global geoid models referenced to WGS84

    IMPORTANT - WGS84 vs NAD83:
        NAVD88 is officially defined relative to NAD83, not WGS84. If you have
        WGS84 ellipsoidal heights and need NAVD88, the transformation includes
        an implicit datum shift. For highest accuracy with NAVD88, use NAD83
        ellipsoidal heights from RTK surveys or apply a rigorous WGS84->NAD83
        transformation first.

        At the FRF, the horizontal difference between NAD83(2011) and
        WGS84(G2139) is typically <1m. The vertical datum shift is ~0m
        but the geoid models differ slightly.

    Args:
        lat: Latitude (decimal degrees, positive north)
        lon: Longitude (decimal degrees, negative west for FRF)
        ellipsoid_height_m: Height above ellipsoid (m). This is what
            GPS receivers typically output.
        from_crs: Source ellipsoid/reference frame.
            'NAD83' (default) - NAD83(2011), GRS80 ellipsoid. Use for US
                RTK surveys and when targeting NAVD88.
            'WGS84' - WGS84, WGS84 ellipsoid. Use for raw GPS/GNSS data
                or when using EGM96/EGM2008.
        to_vertical: Target vertical datum.
            'NAVD88' (default) - North American Vertical Datum 1988.
                Best used with from_crs='NAD83'.
            'EGM96' - Earth Gravitational Model 1996 (global).
            'EGM2008' - Earth Gravitational Model 2008 (global).
            'MSL' - Approximate Mean Sea Level (uses EGM96).

    Returns:
        DeprecatingDict with keys:
            orthometric_height_m: Height above geoid/vertical datum (m)
            geoid_separation_m: Geoid undulation N (m), where
                orthometric = ellipsoidal - N
            from_crs: Input ellipsoid used
            to_vertical: Target vertical datum
            lat: Input latitude
            lon: Input longitude
            ellipsoid_height_m: Input ellipsoidal height

    Raises:
        ValueError: If from_crs or to_vertical is not supported.

    Example:
        >>> # NAD83 RTK survey height at FRF -> NAVD88
        >>> result = ellipsoid_to_orthometric(36.1836, -75.7454, 10.5,
        ...                                   from_crs='NAD83', to_vertical='NAVD88')
        >>> result['orthometric_height_m']  # Height above NAVD88
        46.0  # (10.5 - (-35.5) = 46.0m)

        >>> # Raw WGS84 GPS height -> EGM2008
        >>> result = ellipsoid_to_orthometric(36.1836, -75.7454, 10.5,
        ...                                   from_crs='WGS84', to_vertical='EGM2008')

    Note:
        At the FRF, geoid separations are approximately:
        - NAD83 to NAVD88 (GEOID18): N ≈ -35.5m
        - WGS84 to EGM96: N ≈ -35.0m
        - WGS84 to EGM2008: N ≈ -35.1m

        The negative value means the geoid is below the ellipsoid at FRF,
        so orthometric heights are HIGHER than ellipsoidal heights by ~35m.
    """
    lat = np.asarray(lat)
    lon = np.asarray(lon)
    ellipsoid_height_m = np.asarray(ellipsoid_height_m)

    # Validate inputs
    valid_crs = ['NAD83', 'WGS84']
    valid_vertical = ['NAVD88', 'MSL', 'EGM96', 'EGM2008']

    if from_crs not in valid_crs:
        raise ValueError(f"from_crs must be one of {valid_crs}, got '{from_crs}'")
    if to_vertical not in valid_vertical:
        raise ValueError(f"to_vertical must be one of {valid_vertical}, got '{to_vertical}'")

    # Warn if using WGS84 with NAVD88 (not the standard combination)
    if from_crs == 'WGS84' and to_vertical == 'NAVD88':
        warnings.warn(
            "Using WGS84 ellipsoidal heights with NAVD88 requires an implicit "
            "WGS84->NAD83 datum transformation. For highest accuracy with NAVD88, "
            "use NAD83 ellipsoidal heights (from_crs='NAD83'). At FRF, the "
            "difference is typically <0.1m vertically.",
            UserWarning
        )

    # Define EPSG codes for transformations
    # NAD83(2011) 3D: EPSG:6319 (GRS80 ellipsoid)
    # WGS84 3D: EPSG:4979 (WGS84 ellipsoid)
    # NAD83(2011) + NAVD88: EPSG:6349

    if from_crs == 'NAD83':
        source_crs = "EPSG:6319"  # NAD83(2011) 3D
    else:  # WGS84
        source_crs = "EPSG:4979"  # WGS84 3D

    # Target CRS depends on vertical datum
    # For NAVD88, we need NAD83-based compound CRS
    # For EGM models, we use WGS84-based compound CRS
    if to_vertical == 'NAVD88':
        target_crs = "EPSG:6349"  # NAD83(2011) + NAVD88 height
    elif to_vertical in ['MSL', 'EGM96']:
        target_crs = "EPSG:4326+5773"  # WGS84 + EGM96 height
    elif to_vertical == 'EGM2008':
        target_crs = "EPSG:4326+3855"  # WGS84 + EGM2008 height

    try:
        transformer = pyproj.Transformer.from_crs(
            source_crs,
            target_crs,
            always_xy=True
        )
        # Transform: (lon, lat, ellipsoid_height) -> (lon, lat, orthometric_height)
        _, _, orthometric_height = transformer.transform(lon, lat, ellipsoid_height_m)

        # Calculate geoid separation (N = ellipsoidal - orthometric)
        geoid_separation = ellipsoid_height_m - orthometric_height

        # Check if transformation actually applied (grids may be missing)
        # If geoid separation is exactly 0, the grid files are likely missing
        if np.all(np.abs(geoid_separation) < 1e-10):
            raise RuntimeError("Vertical transformation returned identity (grid files likely missing)")

    except Exception as e:
        # Fallback: Use approximate geoid separation for FRF area
        # Get the appropriate fallback value for this CRS/vertical combination
        fallback_key = (from_crs, to_vertical if to_vertical != 'MSL' else 'EGM96')
        fallback_sep = _FRF_GEOID_SEPARATIONS.get(fallback_key, -35.5)

        warnings.warn(
            f"Vertical transformation unavailable ({e}). Using approximate geoid "
            f"separation of {fallback_sep}m for FRF area ({from_crs} to {to_vertical}). "
            "For accurate results, install PROJ grid files via: "
            "projsync --source-id us_noaa --file us_noaa_g2018u0.tif",
            UserWarning
        )
        geoid_separation = np.full_like(ellipsoid_height_m, fallback_sep, dtype=float)
        orthometric_height = ellipsoid_height_m - geoid_separation

    result = {
        'orthometric_height_m': orthometric_height,
        'geoid_separation_m': geoid_separation,
        'from_crs': from_crs,
        'to_vertical': to_vertical,
        'lat': lat,
        'lon': lon,
        'ellipsoid_height_m': ellipsoid_height_m,
    }
    return DeprecatingDict(result)


def orthometric_to_ellipsoid(lat, lon, orthometric_height_m, from_vertical='NAVD88', to_crs='NAD83'):
    """Convert orthometric height to ellipsoidal height.

    Transforms height above the geoid (orthometric, from surveys/DEMs) to
    height above the ellipsoid (used by GPS/GNSS).

    IMPORTANT - WGS84 vs NAD83:
        NAVD88 is officially defined relative to NAD83. Converting NAVD88 to
        WGS84 ellipsoidal heights requires an implicit NAD83->WGS84 datum shift.
        For highest accuracy, convert NAVD88 to NAD83 ellipsoidal heights first,
        then apply a rigorous NAD83->WGS84 transformation if needed.

    Args:
        lat: Latitude (decimal degrees, positive north)
        lon: Longitude (decimal degrees, negative west for FRF)
        orthometric_height_m: Height above geoid/vertical datum (m).
            This is what surveys and DEMs typically provide.
        from_vertical: Source vertical datum.
            'NAVD88' (default) - North American Vertical Datum 1988.
                Best converted to NAD83 ellipsoidal heights.
            'EGM96' - Earth Gravitational Model 1996 (WGS84-based).
            'EGM2008' - Earth Gravitational Model 2008 (WGS84-based).
            'MSL' - Approximate Mean Sea Level (uses EGM96).
        to_crs: Target ellipsoid/reference frame.
            'NAD83' (default) - NAD83(2011), GRS80 ellipsoid.
                Recommended when converting from NAVD88.
            'WGS84' - WGS84, WGS84 ellipsoid.
                Natural choice when converting from EGM96/EGM2008.

    Returns:
        DeprecatingDict with keys:
            ellipsoid_height_m: Height above ellipsoid (m)
            geoid_separation_m: Geoid undulation N (m), where
                ellipsoidal = orthometric + N
            from_vertical: Input vertical datum
            to_crs: Target ellipsoid used
            lat: Input latitude
            lon: Input longitude
            orthometric_height_m: Input orthometric height

    Raises:
        ValueError: If from_vertical or to_crs is not supported.

    Example:
        >>> # NAVD88 survey elevation at FRF -> NAD83 ellipsoidal
        >>> result = orthometric_to_ellipsoid(36.1836, -75.7454, 6.1,
        ...                                   from_vertical='NAVD88', to_crs='NAD83')
        >>> result['ellipsoid_height_m']  # Height above NAD83/GRS80 ellipsoid
        -29.4  # (6.1 + (-35.5) = -29.4m)

        >>> # EGM2008 height -> WGS84 ellipsoidal
        >>> result = orthometric_to_ellipsoid(36.1836, -75.7454, 6.1,
        ...                                   from_vertical='EGM2008', to_crs='WGS84')

    Note:
        At the FRF, geoid separations are approximately:
        - NAD83 to NAVD88 (GEOID18): N ≈ -35.5m
        - WGS84 to EGM96: N ≈ -35.0m
        - WGS84 to EGM2008: N ≈ -35.1m

        Since N is negative at FRF (geoid below ellipsoid):
        ellipsoidal_height = orthometric_height + N
        e.g., 6.1m NAVD88 + (-35.5m) = -29.4m NAD83 ellipsoidal
    """
    lat = np.asarray(lat)
    lon = np.asarray(lon)
    orthometric_height_m = np.asarray(orthometric_height_m)

    # Validate inputs
    valid_crs = ['NAD83', 'WGS84']
    valid_vertical = ['NAVD88', 'MSL', 'EGM96', 'EGM2008']

    if to_crs not in valid_crs:
        raise ValueError(f"to_crs must be one of {valid_crs}, got '{to_crs}'")
    if from_vertical not in valid_vertical:
        raise ValueError(f"from_vertical must be one of {valid_vertical}, got '{from_vertical}'")

    # Warn if using NAVD88 with WGS84 (not the standard combination)
    if from_vertical == 'NAVD88' and to_crs == 'WGS84':
        warnings.warn(
            "Converting NAVD88 orthometric heights to WGS84 ellipsoidal heights "
            "requires an implicit NAD83->WGS84 datum transformation. For highest "
            "accuracy, use to_crs='NAD83' when converting from NAVD88. At FRF, "
            "the difference is typically <0.1m vertically.",
            UserWarning
        )

    # Define EPSG codes (inverse of ellipsoid_to_orthometric)
    # NAVD88 is defined relative to NAD83, so its source CRS is NAD83-based
    # EGM models are defined relative to WGS84
    if from_vertical == 'NAVD88':
        source_crs = "EPSG:6349"  # NAD83(2011) + NAVD88 height
    elif from_vertical in ['MSL', 'EGM96']:
        source_crs = "EPSG:4326+5773"  # WGS84 + EGM96 height
    elif from_vertical == 'EGM2008':
        source_crs = "EPSG:4326+3855"  # WGS84 + EGM2008 height

    if to_crs == 'NAD83':
        target_crs = "EPSG:6319"  # NAD83(2011) 3D
    else:  # WGS84
        target_crs = "EPSG:4979"  # WGS84 3D

    try:
        transformer = pyproj.Transformer.from_crs(
            source_crs,
            target_crs,
            always_xy=True
        )
        # Transform: (lon, lat, orthometric_height) -> (lon, lat, ellipsoid_height)
        _, _, ellipsoid_height = transformer.transform(lon, lat, orthometric_height_m)

        # Calculate geoid separation (N = ellipsoidal - orthometric)
        geoid_separation = ellipsoid_height - orthometric_height_m

        # Check if transformation actually applied (grids may be missing)
        if np.all(np.abs(geoid_separation) < 1e-10):
            raise RuntimeError("Vertical transformation returned identity (grid files likely missing)")

    except Exception as e:
        # Fallback: Use approximate geoid separation for FRF area
        # Get the appropriate fallback value for this CRS/vertical combination
        fallback_key = (to_crs, from_vertical if from_vertical != 'MSL' else 'EGM96')
        fallback_sep = _FRF_GEOID_SEPARATIONS.get(fallback_key, -35.5)

        warnings.warn(
            f"Vertical transformation unavailable ({e}). Using approximate geoid "
            f"separation of {fallback_sep}m for FRF area ({from_vertical} to {to_crs}). "
            "For accurate results, install PROJ grid files via: "
            "projsync --source-id us_noaa --file us_noaa_g2018u0.tif",
            UserWarning
        )
        geoid_separation = np.full_like(orthometric_height_m, fallback_sep, dtype=float)
        ellipsoid_height = orthometric_height_m + geoid_separation

    result = {
        'ellipsoid_height_m': ellipsoid_height,
        'geoid_separation_m': geoid_separation,
        'from_vertical': from_vertical,
        'to_crs': to_crs,
        'lat': lat,
        'lon': lon,
        'orthometric_height_m': orthometric_height_m,
    }
    return DeprecatingDict(result)


def get_geoid_separation(lat, lon, from_crs='NAD83', to_vertical='NAVD88'):
    """Get the geoid separation (undulation) at a location.

    The geoid separation N is the height of the geoid above the ellipsoid.
    At the FRF, N is approximately -35 to -36 meters (geoid below ellipsoid).

    Relationship: ellipsoidal_height = orthometric_height + N

    IMPORTANT - Different geoid models give different values:
        - NAD83 to NAVD88 (GEOID18): N ≈ -35.5m at FRF
        - WGS84 to EGM96: N ≈ -35.0m at FRF
        - WGS84 to EGM2008: N ≈ -35.1m at FRF

    The difference is due to both the ellipsoid (GRS80 vs WGS84) and
    the geoid model (GEOID18 vs EGM96/EGM2008).

    Args:
        lat: Latitude (decimal degrees, positive north)
        lon: Longitude (decimal degrees, negative west for FRF)
        from_crs: Ellipsoid reference.
            'NAD83' (default) - Use with NAVD88 for US surveys.
            'WGS84' - Use with EGM96/EGM2008 for global applications.
        to_vertical: Geoid/vertical datum.
            'NAVD88' (default) - US national datum (NAD83-based).
            'EGM96' - Global geoid model (WGS84-based).
            'EGM2008' - Global geoid model (WGS84-based).

    Returns:
        DeprecatingDict with keys:
            geoid_separation_m: Geoid undulation N (m)
            from_crs: Ellipsoid used
            to_vertical: Vertical datum used
            lat: Input latitude
            lon: Input longitude

    Example:
        >>> # Get NAD83/NAVD88 geoid separation at FRF origin
        >>> result = get_geoid_separation(36.1775975, -75.7496860,
        ...                               from_crs='NAD83', to_vertical='NAVD88')
        >>> result['geoid_separation_m']
        -35.5

        >>> # Get WGS84/EGM2008 geoid separation (slightly different)
        >>> result = get_geoid_separation(36.1775975, -75.7496860,
        ...                               from_crs='WGS84', to_vertical='EGM2008')
        >>> result['geoid_separation_m']
        -35.1
    """
    # Use a reference height of 0 and compute the transformation
    result = ellipsoid_to_orthometric(lat, lon, 0.0, from_crs=from_crs, to_vertical=to_vertical)

    return DeprecatingDict({
        'geoid_separation_m': result['geoid_separation_m'],
        'from_crs': from_crs,
        'to_vertical': to_vertical,
        'lat': lat,
        'lon': lon,
    })
