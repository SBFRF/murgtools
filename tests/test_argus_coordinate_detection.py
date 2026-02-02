"""Test Argus imagery coordinate system detection."""

import pytest
from murgtools.utils import geoprocess as gp
from murgtools.getdata import detect_argus_coordinate_system


def test_state_plane_detection():
    """Test that State Plane coordinates are correctly detected."""
    # State Plane coordinates for FRF area
    sp_extent = [901951.6805, 902951.6805, 274093.1562, 275093.1562]
    
    coord_system = detect_argus_coordinate_system(sp_extent)
    assert coord_system == 'state_plane', "Should detect State Plane coordinates"


def test_lonlat_detection():
    """Test that lon/lat coordinates are correctly detected."""
    # Lon/lat coordinates for FRF area
    ll_extent = [-75.760, -75.720, 36.175, 36.195]
    
    coord_system = detect_argus_coordinate_system(ll_extent)
    assert coord_system == 'lonlat', "Should detect lon/lat coordinates"


def test_state_plane_to_latlon_conversion():
    """Test that State Plane coordinates are correctly identified and converted."""
    # State Plane coordinates for FRF area
    sp_left = 901951.6805  # Origin Easting
    sp_bottom = 274093.1562  # Origin Northing
    sp_right = sp_left + 1000  # 1km east
    sp_top = sp_bottom + 1000  # 1km north
    
    extent = [sp_left, sp_right, sp_bottom, sp_top]
    
    # Should detect as State Plane
    coord_system = detect_argus_coordinate_system(extent)
    assert coord_system == 'state_plane', "Should detect State Plane coordinates"
    
    # Convert to lat/lon
    left, right, bottom, top = extent
    ll_corner = gp.FRFcoord(left, bottom, coordType='ncsp')
    ur_corner = gp.FRFcoord(right, top, coordType='ncsp')
    
    # Check that conversion produces reasonable lat/lon values
    assert -76 < ll_corner['Lon'] < -75, f"Longitude should be in FRF range, got {ll_corner['Lon']}"
    assert 36 < ll_corner['Lat'] < 37, f"Latitude should be in FRF range, got {ll_corner['Lat']}"
    assert -76 < ur_corner['Lon'] < -75, f"Longitude should be in FRF range, got {ur_corner['Lon']}"
    assert 36 < ur_corner['Lat'] < 37, f"Latitude should be in FRF range, got {ur_corner['Lat']}"
    
    # Check that the converted extent makes sense
    argus_extent = [ll_corner['Lon'], ur_corner['Lon'], ll_corner['Lat'], ur_corner['Lat']]
    assert argus_extent[0] < argus_extent[1], "Longitude min should be less than max"
    assert argus_extent[2] < argus_extent[3], "Latitude min should be less than max"


def test_latlon_coordinates_not_converted():
    """Test that lon/lat coordinates are correctly identified and used directly."""
    # Lon/lat coordinates for FRF area
    lon_left = -75.760
    lon_right = -75.720
    lat_bottom = 36.175
    lat_top = 36.195
    
    extent = [lon_left, lon_right, lat_bottom, lat_top]
    
    # Should detect as lon/lat
    coord_system = detect_argus_coordinate_system(extent)
    assert coord_system == 'lonlat', "Should detect lon/lat coordinates"
    
    # Should use extent directly without conversion
    argus_extent = extent
    
    # Verify extent is valid
    assert argus_extent[0] < argus_extent[1], "Longitude min should be less than max"
    assert argus_extent[2] < argus_extent[3], "Latitude min should be less than max"
    assert -76 < argus_extent[0] < -75, "Longitude should be in FRF range"
    assert 36 < argus_extent[2] < 37, "Latitude should be in FRF range"


def test_coordinate_detection_edge_cases():
    """Test edge cases for coordinate system detection."""
    # Edge case 1: Very small State Plane values (shouldn't happen but test robustness)
    extent1 = [100, 200, 300, 400]
    coord_system1 = detect_argus_coordinate_system(extent1)
    assert coord_system1 == 'lonlat', "Small values should be detected as lon/lat"
    
    # Edge case 2: Negative values (definitely lon/lat or some other system)
    extent2 = [-75.76, -75.72, 36.17, 36.19]
    coord_system2 = detect_argus_coordinate_system(extent2)
    assert coord_system2 == 'lonlat', "Negative values should be detected as lon/lat"
    
    # Edge case 3: Mixed values - Easting looks like State Plane but Northing doesn't
    extent3 = [900000, 901000, 36.17, 36.19]
    coord_system3 = detect_argus_coordinate_system(extent3)
    assert coord_system3 == 'lonlat', "Mixed coordinates (high E, low N) should be detected as lon/lat"
    
    # Edge case 4: Mixed values - Northing looks like State Plane but Easting doesn't
    extent4 = [100, 200, 300000, 301000]
    coord_system4 = detect_argus_coordinate_system(extent4)
    assert coord_system4 == 'lonlat', "Mixed coordinates (low E, high N) should be detected as lon/lat"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
