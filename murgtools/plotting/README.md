# Plotting Module

This module provides plotting utilities for visualizing coastal environmental conditions.

## Conditions Plot

The `conditions_plot` function creates a comprehensive visualization of environmental conditions during surveys or operations. It's inspired by operational analysis needs for autonomous surface vehicles and field campaigns.

### Features

- **Flexible variable selection**: Plot any combination of variables (default: wave height vs. peak period)
- **Multiple survey groups**: Support for multiple groups with different colors and markers
- **Climatological context**: Background distributions show typical conditions
- **Color coding**: Optional color coding by scalar values
- **Date flexibility**: Accept both datetime objects and date strings
- **Customizable styling**: Control axis limits, bin sizes, markers, and more

### Basic Usage

```python
import datetime as dt
from murgtools.plotting import conditions_plot

# Define survey dates
dates = [
    dt.datetime(2023, 6, 15),
    dt.datetime(2023, 7, 20)
]

# Define time range for background climatology
start = dt.datetime(2023, 1, 1)
end = dt.datetime(2023, 12, 31)

# Create the plot
fig, axes = conditions_plot(dates, start, end, ofname='survey_conditions.png')
```

### Advanced Usage

#### Multiple Survey Groups

```python
date_groups = [
    {
        'dates': [dt.datetime(2023, 6, 15), dt.datetime(2023, 6, 20)],
        'label': 'Survey A',
        'color': '#ff7f0e',
        'marker': 'D'
    },
    {
        'dates': [dt.datetime(2023, 7, 10)],
        'label': 'Survey B',
        'color': '#1f77b4',
        'marker': 'o'
    }
]

all_dates = [dt.datetime(2023, 6, 15), dt.datetime(2023, 6, 20), 
             dt.datetime(2023, 7, 10)]

fig, axes = conditions_plot(
    all_dates, start, end,
    date_groups=date_groups,
    sampling_hours=2,
    start_hour=13,
    ofname='multi_group_conditions.png'
)
```

#### Custom Variables

```python
# Plot peak period vs wave height
fig, axes = conditions_plot(
    dates, start, end,
    x_var='Tp',
    y_var='Hs',
    x_limits=[5, 20],
    y_limits=[0, 3],
    ofname='custom_vars.png'
)
```

#### Color by Scalar Value

```python
# Color points by wave direction
fig, axes = conditions_plot(
    dates, start, end,
    color_var='waveDirectionPeak',
    ofname='colored_by_direction.png'
)
```

### Function Reference

#### `conditions_plot(time_list, start_date, end_date, **kwargs)`

Create a two-panel conditions plot.

**Parameters:**
- `time_list` (list): List of datetime objects or date strings (YYYYMMDD format)
- `start_date` (datetime): Start date for background climatology
- `end_date` (datetime): End date for background climatology
- `gauge` (str): Gauge name (default: 'waverider-17m')
- `x_var` (str): X-axis variable (default: 'Hs')
- `y_var` (str): Y-axis variable (default: 'Tp')
- `color_var` (str, optional): Variable for color coding
- `date_groups` (list of dict, optional): Groups of dates with labels and styling
- `sampling_hours` (int): Hours to sample per date (default: 1)
- `start_hour` (int): Starting hour UTC (default: 13)
- `bin_size` (float): Bin size for climatology (default: 0.25)
- `x_limits` (list, optional): [min, max] for x-axis
- `y_limits` (list, optional): [min, max] for y-axis
- `ofname` (str, optional): Output filename
- `title` (str): Plot title (default: 'Survey Conditions')
- `server` (str, optional): THREDDS server ('FRF' or 'CHL')

**Returns:**
- `tuple`: (fig, axes) - matplotlib Figure and list of Axes objects

#### `bin_data(data_to_be_binned, bin_size=0.1)`

Bin data into specified bin sizes.

**Parameters:**
- `data_to_be_binned` (array-like): Data to bin
- `bin_size` (float): Size of bins (default: 0.1)

**Returns:**
- `tuple`: (bin_indices, bins) - bin assignments and bin edges

## Examples

See `examples/example_conditions_plot.py` for complete usage examples.

## Reference

This implementation is based on operational plotting needs for autonomous vehicle surveys at the USACE Field Research Facility, as documented in [kkoetje/asv_conditions_plot](https://github.com/kkoetje/asv_conditions_plot).
