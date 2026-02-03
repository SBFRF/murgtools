#!/usr/bin/env python
"""Example script demonstrating the conditions_plot functionality.

This example shows how to create a conditions plot for visualizing
environmental conditions during surveys or operations.

NOTE: These examples require access to FRF THREDDS servers and valid date 
ranges with data. To run, update the dates to match available data periods.
"""
import datetime as dt


def example_basic():
    """Example 1: Basic usage with default wave height and period."""
    from murgtools.plotting import conditions_plot
    
    print("Example 1: Basic conditions plot")
    dates = [
        dt.datetime(2023, 6, 15),
        dt.datetime(2023, 7, 20),
        dt.datetime(2023, 8, 10)
    ]
    start = dt.datetime(2023, 6, 1)
    end = dt.datetime(2023, 8, 31)
    
    fig, axes = conditions_plot(dates, start, end, ofname='example_basic.png')
    print("Plot saved to example_basic.png")
    return fig, axes


def example_multiple_groups():
    """Example 2: Multiple survey groups with different colors."""
    from murgtools.plotting import conditions_plot
    
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
    start = dt.datetime(2023, 6, 1)
    end = dt.datetime(2023, 8, 31)
    
    fig, axes = conditions_plot(
        all_dates, start, end,
        date_groups=date_groups,
        sampling_hours=2,  # Sample 2 hours per survey
        start_hour=13,     # Start at 1 PM UTC
        ofname='example_groups.png',
        title='Survey Conditions - Multiple Platforms'
    )
    print("Plot saved to example_groups.png")
    return fig, axes


def example_custom_variables():
    """Example 3: Custom variables (different from default Hs and Tp)."""
    from murgtools.plotting import conditions_plot
    
    print("\nExample 3: Custom variables")
    dates = [dt.datetime(2023, 6, 15), dt.datetime(2023, 7, 20)]
    start = dt.datetime(2023, 6, 1)
    end = dt.datetime(2023, 8, 31)
    
    # Plot peak period vs wave height (reversed from default)
    fig, axes = conditions_plot(
        dates, start, end,
        x_var='Tp',  # X-axis: peak period
        y_var='Hs',  # Y-axis: wave height
        x_limits=[5, 20],
        y_limits=[0, 3],
        ofname='example_custom_vars.png'
    )
    print("Plot saved to example_custom_vars.png")
    return fig, axes


def example_date_strings():
    """Example 4: Date strings instead of datetime objects."""
    from murgtools.plotting import conditions_plot
    
    print("\nExample 4: Using date strings")
    date_strings = ['20230615', '20230720', '20230810']
    
    fig, axes = conditions_plot(
        date_strings,
        '20230601',
        '20230831',
        ofname='example_date_strings.png'
    )
    print("Plot saved to example_date_strings.png")
    return fig, axes


def example_different_gauge():
    """Example 5: Using different gauge."""
    from murgtools.plotting import conditions_plot
    
    print("\nExample 5: Different gauge")
    dates = [dt.datetime(2023, 6, 15), dt.datetime(2023, 7, 20)]
    start = dt.datetime(2023, 6, 1)
    end = dt.datetime(2023, 8, 31)
    
    fig, axes = conditions_plot(
        dates, start, end,
        gauge='waverider-26m',  # Use 26m waverider instead of default 17m
        ofname='example_different_gauge.png'
    )
    print("Plot saved to example_different_gauge.png")
    return fig, axes


def example_color_by_scalar():
    """Example 6: Color by scalar value (if available in data)."""
    from murgtools.plotting import conditions_plot
    
    print("\nExample 6: Color by scalar value")
    dates = [dt.datetime(2023, 6, 15), dt.datetime(2023, 7, 20)]
    start = dt.datetime(2023, 6, 1)
    end = dt.datetime(2023, 8, 31)
    
    fig, axes = conditions_plot(
        dates, start, end,
        color_var='waveDirectionPeak',  # Color points by wave direction
        ofname='example_color_scalar.png',
        title='Survey Conditions - Colored by Wave Direction'
    )
    print("Plot saved to example_color_scalar.png")
    return fig, axes


if __name__ == '__main__':
    print("=" * 60)
    print("CONDITIONS PLOT EXAMPLES")
    print("=" * 60)
    print("\nNOTE: These examples require access to FRF THREDDS servers")
    print("and valid date ranges with available data.")
    print("\nTo run a specific example, call the function directly, e.g.:")
    print("  python -c 'from example_conditions_plot import example_basic; example_basic()'")
    print("\nAvailable examples:")
    print("  - example_basic()")
    print("  - example_multiple_groups()")
    print("  - example_custom_variables()")
    print("  - example_date_strings()")
    print("  - example_different_gauge()")
    print("  - example_color_by_scalar()")
    print("=" * 60)

