#!/usr/bin/env python
"""
Validation script to demonstrate the coordinate system detection fix.

This script shows how the fix handles both State Plane and lon/lat coordinate systems
correctly by detecting which system is being used and applying the appropriate conversion.
"""

from murgtools.utils import geoprocess as gp
from murgtools.getdata import detect_argus_coordinate_system


def validate_fix():
    """Validate that coordinate system detection works correctly."""
    
    print("="*80)
    print("Validating Argus Imagery Coordinate System Detection Fix")
    print("="*80)
    
    # Test Case 1: State Plane coordinates (old format)
    print("\n--- Test Case 1: State Plane Coordinates ---")
    sp_extent = [901951.6805, 902951.6805, 274093.1562, 275093.1562]
    print(f"Input extent: {sp_extent}")
    
    coord_system = detect_argus_coordinate_system(sp_extent)
    print(f"Detected coordinate system: {coord_system}")
    
    if coord_system == 'state_plane':
        print("✓ Correctly detected as State Plane - converting to lon/lat")
        left, right, bottom, top = sp_extent
        ll_corner = gp.FRFcoord(left, bottom, coordType='ncsp')
        ur_corner = gp.FRFcoord(right, top, coordType='ncsp')
        argus_extent = [ll_corner['Lon'], ur_corner['Lon'], ll_corner['Lat'], ur_corner['Lat']]
        print(f"Converted extent: {argus_extent}")
        print(f"  SW corner: lon={ll_corner['Lon']:.6f}, lat={ll_corner['Lat']:.6f}")
        print(f"  NE corner: lon={ur_corner['Lon']:.6f}, lat={ur_corner['Lat']:.6f}")
        
        # Verify results are reasonable for FRF area
        assert -76 < argus_extent[0] < -75, "Longitude should be in FRF range"
        assert 36 < argus_extent[2] < 37, "Latitude should be in FRF range"
        print("✓ Conversion successful - coordinates are in expected FRF range")
    else:
        print("✗ ERROR: Should have detected State Plane coordinates")
        return False
    
    # Test Case 2: Lon/Lat coordinates (new format that was causing the bug)
    print("\n--- Test Case 2: Lon/Lat Coordinates ---")
    latlon_extent = [-75.760, -75.720, 36.175, 36.195]
    print(f"Input extent: {latlon_extent}")
    
    coord_system = detect_argus_coordinate_system(latlon_extent)
    print(f"Detected coordinate system: {coord_system}")
    
    if coord_system == 'lonlat':
        print("✓ Correctly detected as lon/lat - using directly without conversion")
        argus_extent = latlon_extent
        print(f"Final extent: {argus_extent}")
        
        # Verify results are reasonable
        assert argus_extent[0] < argus_extent[1], "Longitude min < max"
        assert argus_extent[2] < argus_extent[3], "Latitude min < max"
        assert -76 < argus_extent[0] < -75, "Longitude in FRF range"
        assert 36 < argus_extent[2] < 37, "Latitude in FRF range"
        print("✓ No conversion needed - coordinates are already in expected range")
    else:
        print("✗ ERROR: Should have detected lon/lat coordinates")
        return False
    
    # Test Case 3: Edge case - very small values
    print("\n--- Test Case 3: Edge Case - Small Values ---")
    small_extent = [100, 200, 300, 400]
    print(f"Input extent: {small_extent}")
    
    coord_system = detect_argus_coordinate_system(small_extent)
    print(f"Detected coordinate system: {coord_system}")
    
    if coord_system == 'lonlat':
        print("✓ Correctly detected as lon/lat (not State Plane)")
        print("  (Would use values directly, though they're not valid FRF coords)")
    else:
        print("✗ ERROR: Should have detected as lon/lat (not State Plane)")
        return False
    
    print("\n" + "="*80)
    print("✓ ALL VALIDATION TESTS PASSED")
    print("="*80)
    print("\nSummary:")
    print("- State Plane coordinates (900000+ range) are correctly detected and converted")
    print("- Lon/lat coordinates (-75.x range) are correctly detected and used directly")
    print("- Edge cases with small values are handled safely")
    print("\nThe fix ensures that Argus imagery will align correctly with satellite imagery")
    print("regardless of which coordinate system the Argus GeoTIFF files use.")
    
    return True


if __name__ == '__main__':
    success = validate_fix()
    exit(0 if success else 1)
