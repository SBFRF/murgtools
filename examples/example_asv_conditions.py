#!/usr/bin/env python
"""Example script demonstrating conditions_plot with ASV survey data.

This example replicates the analysis from https://github.com/kkoetje/asv_conditions_plot
using murgtools' conditions_plot functionality. It visualizes wave conditions during
Jaiabot and Yellowfin autonomous surface vehicle (ASV) surveys at the FRF.

Survey dates sourced from:
- all_jaiabot_dates.txt
- all_yellowfin_dates.txt
"""
import datetime as dt
from murgtools.plotting import conditions_plot


# Jaiabot survey dates (from kkoetje/asv_conditions_plot)
JAIABOT_DATES = [
    '20230315', '20230404', '20230406', '20230418', '20230427', '20230501',
    '20230503', '20230510', '20230517', '20230712', '20230713', '20230810',
    '20230823', '20230824', '20230830', '20230831', '20230905', '20230906',
    '20230912', '20231004', '20231005', '20231010', '20231011', '20231018',
    '20231019', '20231109', '20240130', '20240131', '20240205', '20240206',
    '20240208', '20240212', '20240222', '20240305', '20240306', '20240307',
    '20240521', '20240522', '20240528', '20240529', '20240530', '20240627',
    '20240701', '20240702', '20240703', '20240710', '20240711', '20240716',
    '20240717', '20240718', '20240724', '20240730', '20240731', '20240806',
    '20240807', '20240814', '20250430', '20250512', '20250602', '20250617'
]

# Yellowfin survey dates (from kkoetje/asv_conditions_plot)
YELLOWFIN_DATES = [
    '20230216', '20230327', '20230417', '20230504', '20230507', '20230512',
    '20230518', '20230623', '20230705', '20230816', '20230913', '20231017',
    '20231109', '20231130', '20240103', '20240124', '20240227', '20240229',
    '20240312', '20240418', '20240528', '20240626', '20240716', '20240724',
    '20240813', '20240815', '20240816', '20240828', '20240930', '20241030',
    '20241120', '20241209', '20241217', '20250414', '20250415', '20250617'
]


def example_jaiabot_only():
    """Plot wave conditions for Jaiabot surveys only."""
    print("Creating Jaiabot survey conditions plot...")

    # Use a subset of dates for faster processing (2023 data)
    dates_2023 = [d for d in JAIABOT_DATES if d.startswith('2023')]

    fig, axes = conditions_plot(
        dates_2023,
        start_date=dt.datetime(2023, 3, 1),
        end_date=dt.datetime(2023, 12, 31),
        gauge='waverider-17m',
        x_var='Hs',
        y_var='Tp',
        bin_size=0.25,
        sampling_hours=1,
        start_hour=13,
        title='Jaiabot Survey Conditions (2023)',
        ofname='jaiabot_wave_conditions_2023.png'
    )
    print("Saved: jaiabot_wave_conditions_2023.png")
    return fig, axes


def example_yellowfin_only():
    """Plot wave conditions for Yellowfin surveys only."""
    print("Creating Yellowfin survey conditions plot...")

    # Use a subset of dates for faster processing (2023 data)
    dates_2023 = [d for d in YELLOWFIN_DATES if d.startswith('2023')]

    fig, axes = conditions_plot(
        dates_2023,
        start_date=dt.datetime(2023, 2, 1),
        end_date=dt.datetime(2023, 12, 31),
        gauge='waverider-17m',
        x_var='Hs',
        y_var='Tp',
        bin_size=0.25,
        sampling_hours=1,
        start_hour=13,
        title='Yellowfin Survey Conditions (2023)',
        ofname='yellowfin_wave_conditions_2023.png'
    )
    print("Saved: yellowfin_wave_conditions_2023.png")
    return fig, axes


def example_combined_platforms():
    """Compare Jaiabot and Yellowfin survey conditions side by side.

    This replicates the combined plot from kkoetje/asv_conditions_plot
    showing both platforms with different colors and markers.
    """
    print("Creating combined ASV survey conditions plot...")

    # Use 2023 data for both platforms
    jb_2023 = [d for d in JAIABOT_DATES if d.startswith('2023')]
    yf_2023 = [d for d in YELLOWFIN_DATES if d.startswith('2023')]

    # Define date groups for each platform
    date_groups = [
        {
            'dates': jb_2023,
            'label': 'Jaiabot',
            'color': '#1f77b4',  # Blue
            'marker': 'o'
        },
        {
            'dates': yf_2023,
            'label': 'Yellowfin',
            'color': '#ff7f0e',  # Orange
            'marker': 's'
        }
    ]

    # Combine all dates for time_list parameter
    all_dates = jb_2023 + yf_2023

    fig, axes = conditions_plot(
        all_dates,
        start_date=dt.datetime(2023, 2, 1),
        end_date=dt.datetime(2023, 12, 31),
        gauge='waverider-17m',
        x_var='Hs',
        y_var='Tp',
        date_groups=date_groups,
        bin_size=0.25,
        sampling_hours=1,
        start_hour=13,
        x_limits=[0, 3],
        y_limits=[4, 16],
        title='ASV Survey Conditions - Jaiabot & Yellowfin (2023)',
        ofname='combined_asv_wave_conditions_2023.png'
    )
    print("Saved: combined_asv_wave_conditions_2023.png")
    return fig, axes


def example_color_by_direction():
    """Color survey points by wave direction."""
    print("Creating conditions plot colored by wave direction...")

    jb_2023 = [d for d in JAIABOT_DATES if d.startswith('2023')]

    fig, axes = conditions_plot(
        jb_2023,
        start_date=dt.datetime(2023, 3, 1),
        end_date=dt.datetime(2023, 12, 31),
        gauge='waverider-17m',
        x_var='Hs',
        y_var='Tp',
        color_var='waveDirectionPeak',  # Color by wave direction
        bin_size=0.25,
        sampling_hours=1,
        start_hour=13,
        title='Jaiabot Survey Conditions - Colored by Wave Direction',
        ofname='jaiabot_wave_conditions_by_direction.png'
    )
    print("Saved: jaiabot_wave_conditions_by_direction.png")
    return fig, axes


def example_full_record():
    """Plot full survey record (2023-2024) for both platforms.

    Note: This requires more data and may take longer to run.
    """
    print("Creating full record ASV survey conditions plot...")

    # Use all available dates through 2024
    jb_dates = [d for d in JAIABOT_DATES if d.startswith(('2023', '2024'))]
    yf_dates = [d for d in YELLOWFIN_DATES if d.startswith(('2023', '2024'))]

    date_groups = [
        {
            'dates': jb_dates,
            'label': 'Jaiabot',
            'color': '#1f77b4',
            'marker': 'o'
        },
        {
            'dates': yf_dates,
            'label': 'Yellowfin',
            'color': '#ff7f0e',
            'marker': 's'
        }
    ]

    all_dates = jb_dates + yf_dates

    fig, axes = conditions_plot(
        all_dates,
        start_date=dt.datetime(2023, 1, 1),
        end_date=dt.datetime(2024, 12, 31),
        gauge='waverider-17m',
        x_var='Hs',
        y_var='Tp',
        date_groups=date_groups,
        bin_size=0.25,
        sampling_hours=1,
        start_hour=13,
        x_limits=[0, 4],
        y_limits=[4, 18],
        title='ASV Survey Conditions - Full Record (2023-2024)',
        ofname='all_asv_wave_conditions.png'
    )
    print("Saved: all_asv_wave_conditions.png")
    return fig, axes


if __name__ == '__main__':
    print("=" * 65)
    print("ASV SURVEY CONDITIONS PLOT EXAMPLES")
    print("Based on data from: https://github.com/kkoetje/asv_conditions_plot")
    print("=" * 65)
    print("\nNOTE: These examples require access to FRF THREDDS servers.")
    print("\nAvailable examples:")
    print("  - example_jaiabot_only()      : Jaiabot surveys (2023)")
    print("  - example_yellowfin_only()    : Yellowfin surveys (2023)")
    print("  - example_combined_platforms(): Both platforms compared")
    print("  - example_color_by_direction(): Points colored by wave direction")
    print("  - example_full_record()       : Full 2023-2024 record")
    print("\nTo run an example:")
    print("  >>> from example_asv_conditions import example_combined_platforms")
    print("  >>> fig, axes = example_combined_platforms()")
    print("=" * 65)
