# Feature Enhancement: Support continuous time sampling for ASV operations

## Summary
Add support for continuous time range sampling in `conditions_plot()` to better represent extended autonomous surface vehicle (ASV) or boat operations, instead of sampling only discrete hourly intervals.

## Current Behavior
The `conditions_plot()` function currently samples data at discrete hourly intervals:
- `time_list`: List of dates when surveys occurred
- `sampling_hours`: Number of consecutive hours to sample (default: 1)  
- `start_hour`: Starting hour in UTC for sampling (default: 13)

**Example**: For date 2023-06-15 with `sampling_hours=2` and `start_hour=13`, only data at 13:00 and 14:00 UTC are plotted.

## Problem
For ASV operations or surveys that span multiple hours or entire days with varying start/end times, the current approach:
- Doesn't capture all data points during actual operation periods
- Assumes fixed start times across all survey dates
- Loses information about conditions experienced during extended operations

## Proposed Solutions

### Option 1: Time Range Support in date_groups (Recommended)

Add support for tuples of (start_time, end_time) in the `dates` field:

```python
from datetime import datetime
from murgtools import conditions_plot

date_groups = [
    {
        'dates': [
            (datetime(2023, 6, 15, 12, 0), datetime(2023, 6, 15, 18, 30)),  # 6.5 hours
            (datetime(2023, 6, 20, 10, 15), datetime(2023, 6, 20, 16, 45))  # 6.5 hours
        ],
        'label': 'ASV Survey',
        'color': '#ff7f0e',
        'marker': 'D'
    }
]

fig, axes = conditions_plot(
    time_list=None,  # Not needed when using date_groups with ranges
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    date_groups=date_groups
)
```

**Pros**:
- Integrates naturally with existing date_groups structure
- Maintains backward compatibility (single datetime still works)
- Each group can have different time ranges

**Cons**:
- Requires checking if date is datetime or tuple in processing logic

### Option 2: Separate time_ranges Parameter

Add a new `time_ranges` parameter alongside `time_list`:

```python
time_ranges = [
    (datetime(2023, 6, 15, 12, 0), datetime(2023, 6, 15, 18, 30)),
    (datetime(2023, 6, 20, 10, 0), datetime(2023, 6, 20, 16, 45))
]

fig, axes = conditions_plot(
    time_list=None,
    time_ranges=time_ranges,
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31)
)
```

**Pros**:
- Clear separation between discrete times and time ranges
- Easy to validate inputs

**Cons**:
- Adds another parameter to function signature
- Can't mix ranges and discrete times easily
- Doesn't work well with date_groups styling

### Option 3: Smart Auto-Detection

Automatically detect tuples in `time_list` and treat them as time ranges:

```python
time_list = [
    (datetime(2023, 6, 15, 12, 0), datetime(2023, 6, 15, 18, 30)),  # Time range
    datetime(2023, 7, 20),  # Single point (uses sampling_hours/start_hour)
    (datetime(2023, 8, 10, 9, 0), datetime(2023, 8, 10, 15, 30))   # Time range
]

fig, axes = conditions_plot(
    time_list=time_list,
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    sampling_hours=2,  # Used for single datetime entries
    start_hour=13
)
```

**Pros**:
- Most flexible - can mix single points and ranges
- No new parameters needed
- Intuitive API

**Cons**:
- Less explicit - behavior depends on input type
- May be confusing for users expecting consistent behavior

## Implementation Details

For any option, the implementation would:

1. Detect if a date entry is a time range (tuple) or single point (datetime)
2. For time ranges: Extract all data points between start and end times
3. For single points: Use existing `sampling_hours` and `start_hour` logic
4. Plot all collected points with the same styling

**Code location**: `murgtools/plotting/conditions_plot.py` lines 295-306 (current time sampling logic)

## Benefits

- **Better representation**: Shows actual conditions during entire operation
- **More accurate**: Captures temporal variability within operations
- **Flexible**: Supports both discrete sampling and continuous operations
- **Backward compatible**: Existing code continues to work (if implemented carefully)

## Priority

**Medium** - Valuable enhancement that improves usefulness for ASV/extended operations without breaking existing functionality.

## Related Files

- `murgtools/plotting/conditions_plot.py` - Main implementation
- `tests/test_conditions_plot.py` - Add tests for new functionality
- `examples/example_conditions_plot.py` - Add example demonstrating time ranges
- `murgtools/plotting/README.md` - Document new capability

## Acceptance Criteria

- [ ] Time ranges can be specified for survey dates
- [ ] All data points within time ranges are plotted
- [ ] Backward compatibility maintained for existing code
- [ ] Unit tests cover new functionality
- [ ] Documentation updated with examples
- [ ] Works correctly with date_groups styling
