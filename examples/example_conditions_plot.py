#!/usr/bin/env python
"""Example script demonstrating the conditions_plot functionality.

This example shows how to create a conditions plot for visualizing
environmental conditions during surveys or operations.
"""
import datetime as dt
from murgtools.plotting import conditions_plot

# Example 1: Basic usage with default wave height and period
print("Example 1: Basic conditions plot")
dates = [
    dt.datetime(2023, 6, 15),
    dt.datetime(2023, 7, 20),
    dt.datetime(2023, 8, 10)
]
start = dt.datetime(2023, 6, 1)
end = dt.datetime(2023, 8, 31)

# Note: This requires actual data access. In this example, we'll just show the API
# fig, axes = conditions_plot(dates, start, end, ofname='example_basic.png')

# Example 2: Multiple survey groups with different colors
print("\nExample 2: Multiple survey groups")
date_groups = [
    {
        'dates': [dt.datetime(2023, 6, 15), dt.datetime(2023, 6, 20)],
        'label': 'Yellowfin Survey',
        'color': '#ff7f0e',
        'marker': 'D'
    },
    {
        'dates': [dt.datetime(2023, 7, 10), dt.datetime(2023, 7, 15)],
        'label': 'Autonomous Vessel',
        'color': '#1f77b4',
        'marker': 'o'
    }
]
all_dates = [dt.datetime(2023, 6, 15), dt.datetime(2023, 6, 20),
             dt.datetime(2023, 7, 10), dt.datetime(2023, 7, 15)]

# fig, axes = conditions_plot(
#     all_dates, start, end,
#     date_groups=date_groups,
#     sampling_hours=2,  # Sample 2 hours per survey
#     start_hour=13,     # Start at 1 PM UTC
#     ofname='example_groups.png',
#     title='Survey Conditions - Multiple Platforms'
# )

# Example 3: Custom variables (different from default Hs and Tp)
print("\nExample 3: Custom variables")
# Plot peak period vs wave height (reversed from default)
# fig, axes = conditions_plot(
#     dates, start, end,
#     x_var='Tp',  # X-axis: peak period
#     y_var='Hs',  # Y-axis: wave height
#     x_limits=[5, 20],
#     y_limits=[0, 3],
#     ofname='example_custom_vars.png'
# )

# Example 4: Date strings instead of datetime objects
print("\nExample 4: Using date strings")
date_strings = ['20230615', '20230720', '20230810']
# fig, axes = conditions_plot(
#     date_strings,
#     '20230601',
#     '20230831',
#     ofname='example_date_strings.png'
# )

# Example 5: Using different gauge
print("\nExample 5: Different gauge")
# fig, axes = conditions_plot(
#     dates, start, end,
#     gauge='waverider-26m',  # Use 26m waverider instead of default 17m
#     ofname='example_different_gauge.png'
# )

# Example 6: Color by scalar value (if available in data)
print("\nExample 6: Color by scalar value")
# fig, axes = conditions_plot(
#     dates, start, end,
#     color_var='waveDirectionPeak',  # Color points by wave direction
#     ofname='example_color_scalar.png',
#     title='Survey Conditions - Colored by Wave Direction'
# )

print("\nExamples complete!")
print("\nTo actually generate plots, uncomment the conditions_plot calls above.")
print("Note: Requires access to FRF THREDDS servers and valid date ranges with data.")
