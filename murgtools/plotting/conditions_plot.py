# -*- coding: utf-8 -*-
"""Conditions plot functionality for visualizing survey or operational conditions.

This module provides flexible plotting tools for visualizing coastal conditions
during surveys or operations, including wave height, period, and other environmental
variables with optional color coding by scalar values.

@author: SBFRF
@organization: USACE CHL FRF
"""
import datetime as dt
import numpy as np
from matplotlib import pyplot as plt
from murgtools.getdata import getObs

# Color constants for consistent styling
BACKGROUND_COLOR = '#4d4d4d'  # Gray for time series background
DEFAULT_GROUP_COLOR = '#1f77b4'  # Blue for default data group


def _validate_date_groups(date_groups):
    """Validate that date_groups contains required keys.
    
    Args:
        date_groups (list): List of dictionaries defining groups of dates.
        
    Raises:
        ValueError: If any required keys are missing from a group.
    """
    required_keys = ['dates', 'label', 'color']
    for i, group in enumerate(date_groups):
        missing_keys = [key for key in required_keys if key not in group]
        if missing_keys:
            raise ValueError(
                f"date_groups[{i}] is missing required keys: {missing_keys}. "
                f"Each group must have 'dates' (list), 'label' (str), and 'color' (str)."
            )
        if not isinstance(group['dates'], list):
            raise ValueError(
                f"date_groups[{i}]['dates'] must be a list, got {type(group['dates']).__name__}"
            )


def bin_data(data_to_be_binned, bin_size=0.1):
    """Bin data into specified bin sizes.

    Args:
        data_to_be_binned (array-like): Data to be binned (e.g., wave heights).
        bin_size (float): Size of bins. Default is 0.1.

    Returns:
        tuple: (bin_indices, bins) where:
            - bin_indices: Array of 0-based bin indices for each data point
            - bins: Array of bin edges

    Examples:
        >>> data = np.array([0.5, 1.0, 1.5, 2.0])
        >>> indices, bins = bin_data(data, bin_size=0.5)
    """
    # Convert input to numpy array for consistent handling
    data_array = np.asarray(data_to_be_binned)

    # Validate that there is at least one non-NaN value to bin
    if data_array.size == 0 or not np.any(~np.isnan(data_array)):
        raise ValueError(
            "bin_data: data_to_be_binned must contain at least one non-NaN value."
        )

    # Ensure the upper bound includes all data by adding bin_size
    bins = np.arange(np.nanmin(data_array),
                     np.ceil(np.nanmax(data_array)) + bin_size,
                     bin_size)
    # np.digitize returns 1-based indices, convert to 0-based for Python consistency
    bin_indices = np.digitize(data_array, bins=bins, right=False) - 1
    # Guard against values equal to the minimum falling below the first bin (index -1)
    bin_indices[bin_indices < 0] = 0
    return bin_indices, bins


def conditions_plot(time_list, start_date, end_date, gauge='waverider-17m',
                    x_var='Hs', y_var='Tp', color_var=None,
                    date_groups=None, sampling_hours=1, start_hour=13,
                    bin_size=0.25, x_limits=None, y_limits=None,
                    ofname=None, title='Survey Conditions', server=None):
    """Create a conditions plot showing environmental conditions during specified times.

    This function creates a two-panel plot:
    1. Top panel: Time series of the primary variable (default: wave height)
    2. Bottom panel: Scatter plot of two variables (default: Hs vs Tp) during specified times,
       with background showing climatological distributions

    Args:
        time_list (list): List of datetime objects or date strings (YYYYMMDD format) when
            data should be extracted for plotting.
        start_date (datetime): Start date for retrieving background climatology data.
        end_date (datetime): End date for retrieving background climatology data.
        gauge (str): Name of the gauge/station to retrieve data from.
            Default is 'waverider-17m'.
        x_var (str): Variable name for x-axis. Default is 'Hs' (wave height).
            Common options: 'Hs', 'Tp', 'waveDirectionPeak', etc.
        y_var (str): Variable name for y-axis. Default is 'Tp' (peak period).
            If 'Tp' is requested but not available, will compute from 'peakf'.
        color_var (str, optional): Variable name to use for color coding scatter points.
            If None, points will be colored by group. Default is None.
        date_groups (list of dict, optional): List of dictionaries defining groups of dates.
            Each dict should have:
                - 'dates': list of datetime objects or date strings
                - 'label': str, label for the legend
                - 'color': str, matplotlib color for this group
                - 'marker': str, matplotlib marker style (default: 'o')
            If None, all dates in time_list will be plotted as a single group.
        sampling_hours (int): Number of hours to sample for each date in time_list.
            Default is 1.
        start_hour (int): Starting hour (UTC) for sampling on each date. Default is 13.
        bin_size (float): Size of bins for climatological distribution. Default is 0.25.
        x_limits (list, optional): [min, max] limits for x-axis. If None, auto-determined.
        y_limits (list, optional): [min, max] limits for y-axis. If None, auto-determined.
        ofname (str, optional): Output filename for saving the figure. If None, figure
            is displayed but not saved.
        title (str): Title for the overall figure. Default is 'Survey Conditions'.
        server (str, optional): THREDDS server to use ('FRF' or 'CHL'). If None, auto-detected.

    Returns:
        tuple: (fig, axes) where fig is the matplotlib Figure object and axes is a list
            of the two Axes objects [ax1, ax2].

    Examples:
        Basic usage with default wave height and period:
        >>> import datetime as dt
        >>> dates = [dt.datetime(2023, 6, 15), dt.datetime(2023, 7, 20)]
        >>> start = dt.datetime(2023, 1, 1)
        >>> end = dt.datetime(2023, 12, 31)
        >>> fig, axes = conditions_plot(dates, start, end)

        With multiple groups and custom styling:
        >>> date_groups = [
        ...     {'dates': [dt.datetime(2023, 6, 15)], 'label': 'Survey A',
        ...      'color': 'blue', 'marker': 'o'},
        ...     {'dates': [dt.datetime(2023, 7, 20)], 'label': 'Survey B',
        ...      'color': 'red', 'marker': 's'}
        ... ]
        >>> fig, axes = conditions_plot(dates, start, end, date_groups=date_groups,
        ...                             ofname='conditions.png')

        With custom variables:
        >>> fig, axes = conditions_plot(dates, start, end, x_var='Tp', y_var='Hs',
        ...                             gauge='waverider-26m')
    """
    # Convert start_date and end_date to datetime if needed
    if not isinstance(start_date, dt.datetime):
        start_date = dt.datetime.strptime(str(start_date), '%Y%m%d')
    if not isinstance(end_date, dt.datetime):
        end_date = dt.datetime.strptime(str(end_date), '%Y%m%d')

    # Get wave data for the entire period
    gd = getObs(start_date, end_date, server=server)
    all_data = gd.get_wave_data(gauge, spec=False)

    # Validate that we have data
    if len(all_data['time']) == 0:
        raise ValueError(f"No wave data available for gauge '{gauge}' in the specified time range")

    # Convert times to datetime.datetime for easier manipulation
    # Handle both datetime objects and netCDF4 datetime objects
    if hasattr(all_data['time'][0], 'timetuple'):
        # Already datetime-compatible, just ensure they're regular datetime objects
        all_data_dates = np.array([
            dt.datetime(d.year, d.month, d.day, d.hour, d.minute) 
            for d in all_data['time']
        ])
    else:
        # If they're some other type, try to convert directly
        all_data_dates = np.array(all_data['time'])

    # Helper function to ensure Tp exists when needed
    def _ensure_tp_available():
        """Compute Tp from peakf if not already available."""
        if 'Tp' not in all_data:
            if 'peakf' in all_data:
                # Safely compute Tp, avoiding divide-by-zero and infinite values
                with np.errstate(divide='ignore', invalid='ignore'):
                    tp = np.divide(1.0, all_data['peakf'])
                    # Replace non-finite results (inf, -inf, nan) with nan
                    tp[~np.isfinite(tp)] = np.nan
                all_data['Tp'] = tp
            else:
                raise ValueError("Cannot compute Tp: 'peakf' not found in wave data")

    # Handle Tp if requested for either axis
    if x_var == 'Tp' or y_var == 'Tp':
        _ensure_tp_available()

    # Validate that requested variables exist
    if x_var not in all_data:
        raise ValueError(f"Variable '{x_var}' not found in wave data")
    if y_var not in all_data:
        raise ValueError(f"Variable '{y_var}' not found in wave data")
    if color_var is not None and color_var not in all_data:
        raise ValueError(f"Variable '{color_var}' not found in wave data")

    # Compute climatological statistics for background
    # Bin the x variable and compute mean/std of y variable in each bin
    idx_bins, bins = bin_data(all_data[x_var], bin_size=bin_size)
    y_std, y_mean = [], []
    # Loop through bins (indices are 0-based, so range is 0 to len(bins)-1)
    for ii in range(len(bins) - 1):
        mask = idx_bins == ii
        if np.sum(mask) > 0:
            y_std.append(np.nanstd(all_data[y_var][mask]))
            y_mean.append(np.nanmean(all_data[y_var][mask]))
        else:
            y_std.append(np.nan)
            y_mean.append(np.nan)
    y_mean = np.array(y_mean)
    y_std = np.array(y_std)

    # Setup date groups if not provided
    if date_groups is None:
        # Process time_list to ensure all are datetime objects
        processed_dates = []
        for d in time_list:
            if isinstance(d, str):
                processed_dates.append(dt.datetime.strptime(d, '%Y%m%d'))
            elif isinstance(d, dt.datetime):
                processed_dates.append(d)
            else:
                raise ValueError(f"Unsupported date format: {type(d)}")
        
        date_groups = [{
            'dates': processed_dates,
            'label': 'Data',
            'color': DEFAULT_GROUP_COLOR,
            'marker': 'o'
        }]
    else:
        # Validate date_groups structure
        _validate_date_groups(date_groups)
        
        # Process dates in each group
        for group in date_groups:
            processed_dates = []
            for d in group['dates']:
                if isinstance(d, str):
                    processed_dates.append(dt.datetime.strptime(d, '%Y%m%d'))
                elif isinstance(d, dt.datetime):
                    processed_dates.append(d)
                else:
                    raise ValueError(f"Unsupported date format: {type(d)}")
            group['dates'] = processed_dates
            # Set default marker if not provided
            if 'marker' not in group:
                group['marker'] = 'o'

    # Create figure
    fig = plt.figure(figsize=(10, 6))
    fig.suptitle(title, fontweight='bold')

    # Panel 1: Time series of primary variable
    ax1 = plt.subplot2grid((3, 2), (0, 0), colspan=2)
    ax1.set_title(f'{gauge} {x_var}')
    ax1.plot(all_data['time'], all_data[x_var], color=BACKGROUND_COLOR, linewidth=0.5)
    ax1.set_ylabel(f'{x_var}')
    ax1.set_xlabel('Date')

    # Add vertical lines for survey dates
    for group in date_groups:
        for i, d in enumerate(group['dates']):
            label = group['label'] if i == 0 else None  # Only label first occurrence
            ax1.axvline(d, color=group['color'], linestyle='--', linewidth=1, label=label)

    if len(date_groups) > 1:
        ax1.legend(loc='upper right')

    # Panel 2: Scatter plot of conditions during surveys
    ax2 = plt.subplot2grid((3, 2), (1, 0), colspan=2, rowspan=2)
    ax2.set_title(f'{y_var} vs {x_var} During Specified Times')

    # Plot climatological distribution (mean +/- std)
    # Use the left edge of each bin for x-coordinates (bins[:-1] since we have len(bins)-1 stats)
    valid_mask = ~np.isnan(y_mean) & ~np.isnan(y_std)
    valid_bins = bins[:-1][valid_mask]  # Use left edges of bins
    valid_mean = y_mean[valid_mask]
    valid_std = y_std[valid_mask]
    
    if len(valid_bins) > 0:
        ax2.fill_between(valid_bins, valid_mean + valid_std, valid_mean - valid_std,
                        alpha=0.25, color='black', label='67% (1σ)')
        ax2.fill_between(valid_bins, valid_mean + 2 * valid_std, valid_mean - 2 * valid_std,
                        alpha=0.15, color='black', label='95% (2σ)')

    # Plot data for each group
    scatter_collection = None  # Keep track of scatter for colorbar
    for group in date_groups:
        group_x, group_y, group_colors = [], [], []
        
        for d in group['dates']:
            # Create times for this date
            min_time = d + dt.timedelta(hours=start_hour)
            sample_times = [min_time + dt.timedelta(hours=i) for i in range(sampling_hours)]
            
            # Find matching times in data
            mask = np.isin(all_data_dates, sample_times)
            group_x.extend(all_data[x_var][mask])
            group_y.extend(all_data[y_var][mask])
            
            if color_var is not None:
                group_colors.extend(all_data[color_var][mask])

        # Plot the group
        if len(group_x) > 0:
            if color_var is not None:
                scatter = ax2.scatter(group_x, group_y, marker=group['marker'],
                                    c=group_colors, s=50, edgecolor='k',
                                    label=group['label'], cmap='viridis')
                # Keep first scatter for colorbar
                if scatter_collection is None:
                    scatter_collection = scatter
            else:
                ax2.scatter(group_x, group_y, marker=group['marker'],
                          c=group['color'], s=50, edgecolor='k',
                          label=group['label'])
    
    # Add colorbar if color_var was used
    if color_var is not None and scatter_collection is not None:
        cbar = plt.colorbar(scatter_collection, ax=ax2)
        cbar.set_label(color_var)

    ax2.set_xlabel(f'{x_var}')
    ax2.set_ylabel(f'{y_var}')
    
    # Set axis limits if provided
    if x_limits is not None:
        ax2.set_xlim(x_limits)
    if y_limits is not None:
        ax2.set_ylim(y_limits)
    
    ax2.legend(loc='upper right')
    plt.tight_layout(rect=[0.02, 0.02, 0.99, 0.98])

    # Save figure if filename provided
    if ofname is not None:
        plt.savefig(ofname, dpi=150, bbox_inches='tight')
        print(f"Figure saved to {ofname}")
        plt.close(fig)

    return fig, [ax1, ax2]
