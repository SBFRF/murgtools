"""
Fetch the latest Argus image and save as GeoTIFF.

This script retrieves the most recent Argus orthophoto from the FRF coastal imaging server
and saves it as a GeoTIFF. Supports multiple image types: 'bright', 'timex', 'snap', 'dark'.
"""
import argparse
import datetime as DT
import os
from murgtools.getdata import find_argus_imagery


def main():
    parser = argparse.ArgumentParser(description='Fetch the latest Argus imagery from FRF')
    parser.add_argument('image_type', 
                        choices=['bright', 'timex', 'snap', 'dark', 'var'],
                        help='Type of Argus image to retrieve')
    args = parser.parse_args()
    
    # Output filename
    image_type = args.image_type
    output_file = f'latest_argus_{image_type}.tif'
    print(f"Searching for latest Argus {image_type} image...")

    # Get local time for reference and UTC time for API call
    local_time = DT.datetime.now()
    utc_time = DT.datetime.utcnow()
    print(f"Local time: {local_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"UTC time: {utc_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Use method=1 (backward search) to find the most recent available image
    # search_window_hours=48 gives a 2-day window to find imagery
    result = find_argus_imagery(
        dateOfInterest=utc_time,
        filename=output_file,
        imageType= image_type,
        search_window_hours=48,
        method=1,  # Search backward in history
        verbose=True
    )

    if result:
        new_name= f'{result["time"].strftime("%Y%m%d_%H%MZ")}_argus_{image_type}.tif'
        os.rename(output_file, new_name)
        print(f"\nSuccess!")
        print(f"  Image time: {result['time'].strftime('%Y-%m-%d %H:%M')}")
        print(f"  Image shape: {result['image'].shape}")
        print(f"  Saved to: {new_name}")

        # Show time offset if image is from earlier than requested
        offset_mins = result.get('time_offset_minutes', 0)
        if offset_mins != 0:
            print(f"  Time offset: {abs(offset_mins)} minutes ago ({abs(offset_mins)/60:.1f} hours)")
    else:
        print("\nNo Argus imagery found within the search window.")


if __name__ == '__main__':
    main()
