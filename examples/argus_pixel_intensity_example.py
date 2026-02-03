#!/usr/bin/env python
"""Example script demonstrating the use of getArgusPixelIntensity.

This script shows how to extract pixel intensity values from Argus imagery
at specified locations using different coordinate systems.
"""
import datetime as DT
from murgtools.getdata import getArgusPixelIntensity


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


if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("Argus Pixel Intensity Extraction Examples")
    print("=" * 70)
    print("\nNote: This example will attempt to download real Argus imagery")
    print("from the FRF server. It may fail if imagery is not available")
    print("for the specified times.")

    # Run only the FRF coordinates example
    try:
        example_frf_coordinates()
    except Exception as e:
        print(f"\nExample failed: {e}")

    print("\n" + "=" * 70)
    print("Example complete")
    print("=" * 70)
