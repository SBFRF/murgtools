#!/usr/bin/env python
"""Example script demonstrating the use of getArgusPixelIntensity.

This script shows how to extract pixel intensity values from Argus imagery
at specified locations using different coordinate systems.
"""
import datetime as DT
import numpy as np
from murgtools.getdata import getArgusPixelIntensity


def example_pixel_coordinates():
    """Example 1: Extract pixel intensity using pixel coordinates."""
    print("=" * 70)
    print("Example 1: Using pixel coordinates (i, j)")
    print("=" * 70)

    # Define times of interest (will be rounded to nearest 30 minutes)
    times = [
        DT.datetime(2024, 6, 15, 12, 0, 0),
        DT.datetime(2024, 6, 15, 13, 0, 0),
    ]

    # Pixel location in image (column, row)
    location = (500, 300)

    # Extract red channel intensity
    result = getArgusPixelIntensity(
        times=times,
        location=location,
        coordType='pixel',
        imageType='timex',
        channel='red',
        verbose=True
    )

    if result:
        print(f"\nSuccessfully retrieved {len(result['time'])} images")
        print(f"Times: {result['time']}")
        print(f"Red channel intensities: {result['intensity']}")
        print(f"Missing times: {result['missing_times']}")
    else:
        print("\nNo valid images found")


def example_frf_coordinates():
    """Example 2: Extract pixel intensity using FRF coordinates."""
    print("\n" + "=" * 70)
    print("Example 2: Using FRF coordinates (xFRF, yFRF)")
    print("=" * 70)

    # FRF coordinates (meters)
    location = (500, 100)  # xFRF, yFRF

    # Single time
    time = DT.datetime(2024, 6, 15, 12, 0, 0)

    # Extract RGB values (all channels)
    result = getArgusPixelIntensity(
        times=time,
        location=location,
        coordType='FRF',
        imageType='timex',
        channel=None,  # Return all RGB channels
        verbose=True,
        search_window_hours=48,  # Search within 48 hours if exact time not available
        method=0  # Nearest in time (bidirectional search)
    )

    if result:
        print(f"\nSuccessfully retrieved {len(result['time'])} images")
        print(f"Location: xFRF={result['location']['xFRF']}, yFRF={result['location']['yFRF']}")
        print(f"Pixel coordinates: i={result['location']['pixel_i']}, j={result['location']['pixel_j']}")
        print(f"RGB values: {result['intensity']}")
    else:
        print("\nNo valid images found")


def example_latlon_coordinates():
    """Example 3: Extract pixel intensity using lat/lon coordinates."""
    print("\n" + "=" * 70)
    print("Example 3: Using geographic coordinates (lon, lat)")
    print("=" * 70)

    # Geographic coordinates (degrees)
    location = (-75.7497, 36.1776)  # lon, lat (FRF location)

    # Multiple times
    times = [
        DT.datetime(2024, 6, 15, 10, 0, 0),
        DT.datetime(2024, 6, 15, 12, 0, 0),
        DT.datetime(2024, 6, 15, 14, 0, 0),
    ]

    # Extract grayscale (average of RGB)
    result = getArgusPixelIntensity(
        times=times,
        location=location,
        coordType='LL',
        imageType='timex',
        channel='gray',
        verbose=True
    )

    if result:
        print(f"\nSuccessfully retrieved {len(result['time'])} images")
        for i, (time, intensity) in enumerate(zip(result['time'], result['intensity'])):
            print(f"  {time}: grayscale = {intensity:.1f}")
    else:
        print("\nNo valid images found")


def example_multiple_image_types():
    """Example 4: Extract from different image types."""
    print("\n" + "=" * 70)
    print("Example 4: Different image types (timex, var, bright, dark)")
    print("=" * 70)

    location = (500, 300)  # pixel coordinates
    time = DT.datetime(2024, 6, 15, 12, 0, 0)

    for img_type in ['timex', 'var', 'bright', 'dark']:
        result = getArgusPixelIntensity(
            times=time,
            location=location,
            coordType='pixel',
            imageType=img_type,
            channel='red',
            verbose=False
        )

        if result:
            print(f"{img_type:6s}: red = {result['intensity'][0]}")
        else:
            print(f"{img_type:6s}: No data available")


def example_location_dict():
    """Example 5: Specify location as dictionary."""
    print("\n" + "=" * 70)
    print("Example 5: Using dictionary for location specification")
    print("=" * 70)

    # Location as dictionary
    location = {'xFRF': 500, 'yFRF': 100}

    result = getArgusPixelIntensity(
        times=DT.datetime(2024, 6, 15, 12, 0, 0),
        location=location,
        coordType='FRF',
        imageType='timex',
        channel='green',
        verbose=False
    )

    if result:
        print(f"Green channel intensity: {result['intensity'][0]}")
    else:
        print("No valid images found")


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Argus Pixel Intensity Extraction Examples")
    print("=" * 70)
    print("\nNote: These examples will attempt to download real Argus imagery")
    print("from the FRF server. Some may fail if imagery is not available")
    print("for the specified times.")

    # Run examples
    try:
        example_pixel_coordinates()
    except Exception as e:
        print(f"\nExample 1 failed: {e}")

    try:
        example_frf_coordinates()
    except Exception as e:
        print(f"\nExample 2 failed: {e}")

    try:
        example_latlon_coordinates()
    except Exception as e:
        print(f"\nExample 3 failed: {e}")

    try:
        example_multiple_image_types()
    except Exception as e:
        print(f"\nExample 4 failed: {e}")

    try:
        example_location_dict()
    except Exception as e:
        print(f"\nExample 5 failed: {e}")

    print("\n" + "=" * 70)
    print("Examples complete")
    print("=" * 70)
