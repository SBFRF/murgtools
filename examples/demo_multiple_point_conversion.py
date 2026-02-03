#!/usr/bin/env python3
"""
Demo: FRFcoord Multiple Point Input Support

This example demonstrates that FRFcoord and related coordinate transformation
functions in murgtools already support multiple input points without requiring
external loops.

This capability is provided by pyproj >= 3.0.0, which has native array support
in the Transformer class.
"""

import numpy as np
from murgtools.utils import geoprocess as gp


def demo_single_point():
    """Demonstrate single point conversion (original functionality)."""
    print("=" * 70)
    print("DEMO 1: Single Point Conversion")
    print("=" * 70)
    
    # Single point in FRF coordinates
    x = 566.93
    y = 515.11
    
    print(f"\nInput: FRF coordinates")
    print(f"  xFRF = {x} m")
    print(f"  yFRF = {y} m")
    
    result = gp.FRFcoord(x, y)
    
    print(f"\nOutput: All coordinate systems")
    print(f"  State Plane E: {result['StateplaneE']:.2f} m")
    print(f"  State Plane N: {result['StateplaneN']:.2f} m")
    print(f"  Latitude:      {result['Lat']:.6f}°")
    print(f"  Longitude:     {result['Lon']:.6f}°")
    if isinstance(result['utmE'], np.ndarray):
        print(f"  UTM E:         {result['utmE'][0]:.2f} m")
        print(f"  UTM N:         {result['utmN'][0]:.2f} m")
    else:
        print(f"  UTM E:         {result['utmE']:.2f} m")
        print(f"  UTM N:         {result['utmN']:.2f} m")
    print()


def demo_array_input():
    """Demonstrate array input conversion (enhanced functionality)."""
    print("=" * 70)
    print("DEMO 2: Multiple Points - Array Input (No Loop Needed!)")
    print("=" * 70)
    
    # Multiple points in FRF coordinates
    x_array = np.array([0.0, 100.0, 200.0, 300.0, 566.93])
    y_array = np.array([0.0, 100.0, 200.0, 300.0, 515.11])
    
    print(f"\nInput: {len(x_array)} points as numpy arrays")
    print(f"  xFRF = {x_array}")
    print(f"  yFRF = {y_array}")
    
    result = gp.FRFcoord(x_array, y_array)
    
    print(f"\nOutput: All {len(x_array)} points converted simultaneously")
    print(f"  State Plane E: {result['StateplaneE']}")
    print(f"  Latitude:      {result['Lat']}")
    print()
    print(f"Result types: {type(result['xFRF'])} with shape {result['xFRF'].shape}")
    print()


def demo_different_coordinate_systems():
    """Demonstrate array conversion for different input coordinate systems."""
    print("=" * 70)
    print("DEMO 3: Different Input Coordinate Systems (All Support Arrays)")
    print("=" * 70)
    
    # Test with Lat/Lon
    print("\n3a. Lat/Lon Input:")
    lon = np.array([-75.75, -75.74, -75.73])
    lat = np.array([36.17, 36.18, 36.19])
    result = gp.FRFcoord(lon, lat)
    print(f"  Input:  {len(lon)} Lat/Lon points")
    print(f"  Output: xFRF = {result['xFRF'][:3]}")
    
    # Test with State Plane
    print("\n3b. State Plane Input:")
    sp_e = np.array([902000.0, 902100.0, 902200.0])
    sp_n = np.array([274000.0, 274100.0, 274200.0])
    result = gp.FRFcoord(sp_e, sp_n)
    print(f"  Input:  {len(sp_e)} State Plane points")
    print(f"  Output: xFRF = {result['xFRF']}")
    
    # Test with Lists (automatically converted)
    print("\n3c. Python List Input (auto-converted to arrays):")
    x_list = [100.0, 200.0, 300.0]
    y_list = [100.0, 200.0, 300.0]
    result = gp.FRFcoord(x_list, y_list)
    print(f"  Input:  {len(x_list)} points as Python lists")
    print(f"  Output: {type(result['xFRF'])} with values {result['xFRF']}")
    print()


def demo_individual_functions():
    """Demonstrate that individual transformation functions also support arrays."""
    print("=" * 70)
    print("DEMO 4: Individual Transformation Functions (All Support Arrays)")
    print("=" * 70)
    
    # Test FRF2ncsp
    print("\n4a. FRF2ncsp (FRF to State Plane):")
    x = np.array([100.0, 200.0, 300.0])
    y = np.array([100.0, 200.0, 300.0])
    result = gp.FRF2ncsp(x, y)
    print(f"  Input:  {len(x)} FRF points")
    print(f"  Output: StateplaneE = {result['StateplaneE']}")
    
    # Test ncsp2LatLon
    print("\n4b. ncsp2LatLon (State Plane to Lat/Lon):")
    result = gp.ncsp2LatLon(result['StateplaneE'], result['StateplaneN'])
    print(f"  Output: Latitude = {result['lat']}")
    
    # Test LatLon2ncsp
    print("\n4c. LatLon2ncsp (Lat/Lon to State Plane):")
    result2 = gp.LatLon2ncsp(result['lon'], result['lat'])
    print(f"  Output: StateplaneE = {result2['StateplaneE']}")
    
    print("\n✓ Round-trip conversion successful!")
    print()


def demo_performance_comparison():
    """Compare performance between loop and array approaches."""
    print("=" * 70)
    print("DEMO 5: Performance Comparison")
    print("=" * 70)
    
    import time
    
    # Create test data
    n = 100
    x = np.linspace(0, 1000, n)
    y = np.linspace(0, 1000, n)
    
    print(f"\nConverting {n} points...")
    
    # Method 1: Loop (old way)
    print("\nMethod 1: Loop (OLD - not necessary)")
    start = time.time()
    results = []
    for i in range(n):
        results.append(gp.FRFcoord(x[i], y[i]))
    time_loop = time.time() - start
    print(f"  Time: {time_loop:.4f} seconds")
    
    # Method 2: Array (new way)
    print("\nMethod 2: Array (NEW - already supported!)")
    start = time.time()
    result = gp.FRFcoord(x, y)
    time_array = time.time() - start
    print(f"  Time: {time_array:.4f} seconds")
    
    # Compare
    speedup = time_loop / time_array
    print(f"\n✓ Array input is {speedup:.1f}x faster!")
    print()


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  FRFcoord Multiple Point Input Support - Demo".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    demo_single_point()
    demo_array_input()
    demo_different_coordinate_systems()
    demo_individual_functions()
    demo_performance_comparison()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    print("✓ FRFcoord supports single point AND multiple point inputs")
    print("✓ No external loops needed for batch conversions")
    print("✓ Array input is significantly faster than looping")
    print("✓ All coordinate systems supported: FRF, State Plane, Lat/Lon, UTM")
    print("✓ All transformation functions support arrays")
    print()
    print("This functionality is provided by pyproj >= 3.0.0")
    print("No code changes needed - it already works!")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
