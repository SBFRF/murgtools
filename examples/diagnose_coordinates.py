#!/usr/bin/env python
"""
Diagnostic script to understand the coordinate system issue between Argus and Satellite imagery.

This script will:
1. Fetch both Argus and Satellite imagery
2. Print the actual coordinate extents being used
3. Check if coordinates are in State Plane or lon/lat
4. Determine where the misalignment is happening
"""

import datetime as DT
import numpy as np
from murgtools.getdata import getSatelliteImagery, findArgusImagery, get_geotiff_extent
from murgtools.utils import geoprocess as gp
import tempfile

def diagnose_coordinates():
    """Run diagnostic to understand coordinate system issue."""
    
    print("="*80)
    print("COORDINATE SYSTEM DIAGNOSTIC")
    print("="*80)
    
    # Use a recent date
    now = DT.datetime.now()
    
    # 1. Test satellite imagery coordinates
    print("\n1. SATELLITE IMAGERY COORDINATES")
    print("-" * 80)
    
    # Define corners in lat/lon (FRF area)
    sat_corners = [
        (36.195, -75.760),  # NW
        (36.195, -75.720),  # NE  
        (36.175, -75.760),  # SW
        (36.175, -75.720),  # SE
    ]
    
    print(f"Input corners (lat, lon):")
    for i, corner in enumerate(sat_corners):
        print(f"  Corner {i}: lat={corner[0]:.6f}, lon={corner[1]:.6f}")
    
    try:
        sat_result = getSatelliteImagery(
            sat_corners,
            date=now,
            max_cloud_cover=50,
            collection='sentinel-2-l2a'
        )
        
        if sat_result:
            print(f"\n✓ Got satellite image from {sat_result['time'].strftime('%Y-%m-%d')}")
            print(f"  Image shape: {sat_result['image'].shape}")
            print(f"  Cloud cover: {sat_result['cloud_cover']:.1f}%")
            print(f"\nSatellite extent (for matplotlib imshow):")
            print(f"  extent = {sat_result['extent']}")
            print(f"  Format: [left_lon, right_lon, bottom_lat, top_lat]")
            print(f"  Left (min lon):   {sat_result['extent'][0]:.6f}")
            print(f"  Right (max lon):  {sat_result['extent'][1]:.6f}")
            print(f"  Bottom (min lat): {sat_result['extent'][2]:.6f}")
            print(f"  Top (max lat):    {sat_result['extent'][3]:.6f}")
        else:
            print("✗ No satellite imagery available")
            return
    except Exception as e:
        print(f"✗ Error fetching satellite imagery: {e}")
        return
    
    # 2. Test Argus imagery coordinates
    print("\n" + "="*80)
    print("2. ARGUS IMAGERY COORDINATES")
    print("-" * 80)
    
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        argus_result = findArgusImagery(
            now,
            filename=tmp_path,
            imageType='timex',
            search_window_hours=72,
            method=1  # Get most recent historical
        )
        
        if argus_result:
            print(f"✓ Got Argus image from {argus_result['time'].strftime('%Y-%m-%d %H:%M')}")
            print(f"  Offset from requested: {argus_result.get('time_offset_minutes', 0)} minutes")
            
            # Extract extent from GeoTIFF
            raw_extent = get_geotiff_extent(tmp_path)
            print(f"\nRaw GeoTIFF extent:")
            print(f"  extent = {raw_extent}")
            print(f"  Format: [left, right, bottom, top]")
            print(f"  Left:   {raw_extent[0]:.6f}")
            print(f"  Right:  {raw_extent[1]:.6f}")
            print(f"  Bottom: {raw_extent[2]:.6f}")
            print(f"  Top:    {raw_extent[3]:.6f}")
            
            # Determine coordinate system
            print(f"\nCoordinate System Detection:")
            left, right, bottom, top = raw_extent
            
            # Check if values look like State Plane
            is_state_plane = (left > 800000 and bottom > 200000)
            
            if is_state_plane:
                print(f"  ✓ DETECTED: North Carolina State Plane (NAD83)")
                print(f"    Easting values ~900,000m, Northing ~270,000m")
                print(f"\n  Converting to lon/lat...")
                
                # Convert SW and NE corners
                ll_corner = gp.FRFcoord(left, bottom, coordType='ncsp')
                ur_corner = gp.FRFcoord(right, top, coordType='ncsp')
                
                argus_extent_lonlat = [
                    ll_corner['Lon'],  # left (min lon)
                    ur_corner['Lon'],  # right (max lon)
                    ll_corner['Lat'],  # bottom (min lat)
                    ur_corner['Lat']   # top (max lat)
                ]
                
                print(f"  Converted extent (lon/lat):")
                print(f"    extent = {argus_extent_lonlat}")
                print(f"    Left (min lon):   {argus_extent_lonlat[0]:.6f}")
                print(f"    Right (max lon):  {argus_extent_lonlat[1]:.6f}")
                print(f"    Bottom (min lat): {argus_extent_lonlat[2]:.6f}")
                print(f"    Top (max lat):    {argus_extent_lonlat[3]:.6f}")
                
            else:
                print(f"  ✓ DETECTED: Geographic coordinates (lon/lat)")
                print(f"    Longitude ~-75°, Latitude ~36°")
                print(f"\n  Using extent directly (no conversion needed):")
                argus_extent_lonlat = raw_extent
                print(f"    extent = {argus_extent_lonlat}")
            
            # 3. Compare extents
            print("\n" + "="*80)
            print("3. COORDINATE COMPARISON")
            print("-" * 80)
            
            print(f"\nSatellite extent: {sat_result['extent']}")
            print(f"Argus extent:     {argus_extent_lonlat}")
            
            # Check overlap
            sat_lon_range = (sat_result['extent'][0], sat_result['extent'][1])
            sat_lat_range = (sat_result['extent'][2], sat_result['extent'][3])
            
            argus_lon_range = (argus_extent_lonlat[0], argus_extent_lonlat[1])
            argus_lat_range = (argus_extent_lonlat[2], argus_extent_lonlat[3])
            
            lon_overlap = (
                max(sat_lon_range[0], argus_lon_range[0]) < 
                min(sat_lon_range[1], argus_lon_range[1])
            )
            lat_overlap = (
                max(sat_lat_range[0], argus_lat_range[0]) < 
                min(sat_lat_range[1], argus_lat_range[1])
            )
            
            print(f"\nLongitude ranges:")
            print(f"  Satellite: {sat_lon_range[0]:.6f} to {sat_lon_range[1]:.6f}")
            print(f"  Argus:     {argus_lon_range[0]:.6f} to {argus_lon_range[1]:.6f}")
            print(f"  Overlap: {'✓ YES' if lon_overlap else '✗ NO'}")
            
            print(f"\nLatitude ranges:")
            print(f"  Satellite: {sat_lat_range[0]:.6f} to {sat_lat_range[1]:.6f}")
            print(f"  Argus:     {argus_lat_range[0]:.6f} to {argus_lat_range[1]:.6f}")
            print(f"  Overlap: {'✓ YES' if lat_overlap else '✗ NO'}")
            
            if lon_overlap and lat_overlap:
                print(f"\n✓✓ EXTENTS OVERLAP - Coordinates should align!")
            else:
                print(f"\n✗✗ EXTENTS DO NOT OVERLAP - This is the problem!")
                print(f"\nThe issue is that the coordinate systems don't match.")
                print(f"One or both need conversion to align properly.")
            
            # 4. Summary
            print("\n" + "="*80)
            print("4. DIAGNOSTIC SUMMARY")
            print("-" * 80)
            
            print(f"\nArgus GeoTIFF coordinate system: {'State Plane' if is_state_plane else 'Lon/Lat'}")
            print(f"Satellite imagery coordinate system: Lon/Lat (always)")
            
            if is_state_plane:
                print(f"\n→ Argus coordinates NEED conversion from State Plane to Lon/Lat")
                print(f"→ The original code was CORRECT in converting")
            else:
                print(f"\n→ Argus coordinates are ALREADY in Lon/Lat")
                print(f"→ NO conversion needed")
                print(f"→ The PR's 'fix' is actually WRONG if Argus is giving lon/lat!")
            
        else:
            print("✗ No Argus imagery available")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        import os
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    
    print("\n" + "="*80)


if __name__ == '__main__':
    diagnose_coordinates()
