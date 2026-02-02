"""
Fetch the latest Argus bright image and save as GeoTIFF.

This script retrieves the most recent 'bright' (brightest pixels composite)
Argus orthophoto from the FRF coastal imaging server and saves it as a GeoTIFF.
"""
import datetime as DT
import os
from murgtools.getdata import findArgusImagery


def main():
    # Output filename
    output_file = 'latest_argus_bright.tif'
    image_type = 'bright'
    print("Searching for latest Argus bright image...")

    # Get local time for reference and UTC time for API call
    local_time = DT.datetime.now()
    utc_time = DT.datetime.utcnow()
    print(f"Local time: {local_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"UTC time: {utc_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Use method=1 (backward search) to find the most recent available image
    # search_window_hours=48 gives a 2-day window to find imagery
    result = findArgusImagery(
        dateOfInterest=utc_time,
        filename=output_file,
        imageType= image_type,
        search_window_hours=48,
        method=1,  # Search backward in history
        verbose=True
    )

    if result:
        new_name= f'argus_{image_type}_{result["time"].strftime("%Y%m%d_%H%MZ")}.png'
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
