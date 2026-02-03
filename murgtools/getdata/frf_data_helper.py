"""
FRF data helper utilities.

This module contains helper functions for working with FRF coastal data,
including coordinate system detection and data processing utilities.
"""


def detect_argus_coordinate_system(extent):
    """Detect coordinate system of Argus GeoTIFF extent values.
    
    Argus imagery GeoTIFFs may be in either NC State Plane NAD83 coordinates
    or geographic lon/lat coordinates. This function detects which system is
    being used based on the magnitude of the extent values.
    
    Args:
        extent (list): [left, right, bottom, top] extent values from GeoTIFF.
    
    Returns:
        str: Either 'state_plane' or 'lonlat' indicating the detected coordinate system.
    
    Notes:
        Detection is based on typical coordinate ranges for the FRF area:
        - State Plane: Easting ~900000-910000m, Northing ~270000-280000m
        - Lon/Lat: Longitude ~-76 to -75°, Latitude ~36.1-36.2°
        
        The thresholds (800000 for Easting, 200000 for Northing) provide a
        clear separation between the two systems since State Plane values are
        at least 3 orders of magnitude larger than lon/lat values.
    
    Example:
        >>> # State Plane extent
        >>> extent_sp = [901951, 902951, 274093, 275093]
        >>> detect_argus_coordinate_system(extent_sp)
        'state_plane'
        
        >>> # Lon/Lat extent
        >>> extent_ll = [-75.76, -75.72, 36.175, 36.195]
        >>> detect_argus_coordinate_system(extent_ll)
        'lonlat'
    
    """
    # State Plane coordinate detection thresholds
    # These values are chosen well below typical State Plane coordinates
    # but far above any valid lon/lat values for Earth
    STATEPLANE_EASTING_THRESHOLD = 800000  # meters
    STATEPLANE_NORTHING_THRESHOLD = 200000  # meters
    
    left, right, bottom, top = extent
    
    if left > STATEPLANE_EASTING_THRESHOLD and bottom > STATEPLANE_NORTHING_THRESHOLD:
        return 'state_plane'
    else:
        return 'lonlat'
