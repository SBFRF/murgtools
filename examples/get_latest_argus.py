"""
Fetch the latest Argus image and save as GeoTIFF.

This script retrieves the most recent Argus orthophoto from the FRF coastal imaging server
and saves it as a GeoTIFF. Supports multiple image types: 'bright', 'timex', 'snap', 'dark'.

A specific UTC time can be prescribed with --datetime in YYYYmmddTHHMMSSZ format
(e.g. 20260902T143000Z); otherwise the current UTC time is used.
"""
import argparse
import datetime as DT
import os
from murgtools.getdata import find_argus_imagery

DATETIME_FORMAT = '%Y%m%dT%H%M%SZ'


def parse_datetime(value):
    """Parse a YYYYmmddTHHMMSSZ UTC timestamp string into a datetime."""
    try:
        return DT.datetime.strptime(value, DATETIME_FORMAT)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"invalid datetime {value!r}: expected YYYYmmddTHHMMSSZ (e.g. 20260902T143000Z)")


def main():
    parser = argparse.ArgumentParser(description='Fetch Argus imagery from FRF')
    parser.add_argument('image_type',
                        choices=['bright', 'timex', 'snap', 'dark', 'var'],
                        help='Type of Argus image to retrieve')
    parser.add_argument('--datetime', dest='date_of_interest', type=parse_datetime, default=None,
                        metavar='YYYYmmddTHHMMSSZ',
                        help='UTC time of interest in YYYYmmddTHHMMSSZ format '
                             '(e.g. 20260902T143000Z). Defaults to now (UTC).')
    parser.add_argument('--search-window-hours', type=int, default=48, metavar='HOURS',
                        help='Hours to search for available imagery (default: 48)')
    parser.add_argument('--method', type=int, choices=[0, 1], default=1,
                        help='Search strategy: 0 = nearest in time (bidirectional), '
                             '1 = most recent before target (default: 1)')
    args = parser.parse_args()

    image_type = args.image_type

    # Use the prescribed UTC time if given, otherwise the current time
    if args.date_of_interest is not None:
        utc_time = args.date_of_interest
        print(f"Searching for Argus {image_type} image near "
              f"{utc_time.strftime(DATETIME_FORMAT)}...")
        print(f"Requested UTC time: {utc_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        utc_time = DT.datetime.utcnow()
        print(f"Searching for latest Argus {image_type} image...")
        # Get local time for reference and UTC time for API call
        local_time = DT.datetime.now()
        print(f"Local time: {local_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"UTC time: {utc_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Intermediate filename is keyed to the requested time; it is renamed below to
    # reflect the time of the image actually found
    output_file = f'argus_{image_type}_{utc_time.strftime(DATETIME_FORMAT)}.tif'

    # method=1 (backward search) finds the most recent available image;
    # method=0 finds the nearest in time in either direction
    result = find_argus_imagery(
        dateOfInterest=utc_time,
        filename=output_file,
        imageType= image_type,
        search_window_hours=args.search_window_hours,
        method=args.method,
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
