"""
Test script for murgtools wave data and imagery functionality.

Creates a two-panel figure:
- Top: Wave height time series from all available gauges (last 30 days)
- Bottom: Gauge locations over satellite imagery with Argus imagery overlay (50% opacity)
"""
import datetime as DT
import tempfile
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

from murgtools.getdata import getObs, getSatelliteImagery, findArgusImagery, get_geotiff_extent
from murgtools.utils import geoprocess as gp


def main():
    # Define time range: last 30 days with clean datetime boundaries
    now = DT.datetime.now()
    # End at start of today (midnight), start 30 days before that
    d2 = DT.datetime(now.year, now.month, now.day, 0, 0, 0)
    d1 = d2 - DT.timedelta(days=30)

    print(f"Fetching wave data from {d1.strftime('%Y-%m-%d %H:%M')} to {d2.strftime('%Y-%m-%d %H:%M')}...")

    # Initialize the observation data retriever
    obs = getObs(d1, d2)

    # Wave gauges with recent data (others may have historical data only)
    gauge_list = [
        'waverider-26m',
        'waverider-17m',
        'awac-11m',
        '8m-array',
        'awac-6m',
        'awac-4.5m',
        'adop-3.5m',
        'xp200m',
        'xp150m',
        'xp125m',
        'sig940-300',
        'sig940-400',
        'sig940-600',
        'sig769-300',
        'lidarwavegauge140',
        'lidarwavegauge110',
        'lidarwavegauge100',
    ]

    # Retrieve wave data from all gauges
    wave_data = {}
    gauge_locations = []

    for gauge in gauge_list:
        print(f"  Fetching {gauge}...")
        try:
            data = obs.getWaveData(gaugenumber=gauge, roundto=30)
            if data is not None and 'Hs' in data:
                wave_data[gauge] = data
                # Get lat/lon from xFRF/yFRF using geoprocess
                xFRF = data.get('xFRF')
                yFRF = data.get('yFRF')
                if xFRF is not None and yFRF is not None:
                    coords = gp.FRFcoord(xFRF, yFRF, coordType='FRF')
                    lat = coords['Lat']
                    lon = coords['Lon']
                else:
                    lat = data.get('lat')
                    lon = data.get('lon')

                gauge_locations.append({
                    'name': gauge,
                    'lat': lat,
                    'lon': lon,
                    'xFRF': xFRF,
                    'yFRF': yFRF,
                    'depth': data.get('depth'),
                })
                print(f"    Got {len(data['Hs'])} records")
            else:
                print(f"    No data available")
        except Exception as e:
            print(f"    Error: {e}")

    # Define corners for satellite imagery (wider FRF area to include all gauges)
    # Satellite extent: ~2km offshore, 2km alongshore
    corners = [
        (36.195, -75.760),  # NW - further offshore and north
        (36.195, -75.720),  # NE
        (36.175, -75.760),  # SW
        (36.175, -75.720),  # SE
    ]

    # Get satellite imagery (finds closest available to current time)
    print("\nFetching satellite imagery...")
    sat_result = getSatelliteImagery(
        corners,
        date=now,
        max_cloud_cover=30,
        collection='sentinel-2-l2a'
    )
    if sat_result:
        print(f"  Got satellite image from {sat_result['time'].strftime('%Y-%m-%d')}")
        print(f"  Shape: {sat_result['image'].shape}, Cloud cover: {sat_result['cloud_cover']:.1f}%")
    else:
        print("  No satellite imagery available")

    # Get Argus imagery (searches for nearest available within 24-hour window)
    print("\nFetching Argus imagery...")
    argus_result = None
    argus_extent = None

    # Save to temp file so we can extract extent
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Use findArgusImagery with method=1 (nearest in history) to get most recent image
        # Using 'bright' (brightest pixels composite) for best visualization
        argus_result = findArgusImagery(now, filename=tmp_path, imageType='bright',
                                        search_window_hours=48, method=1)
        if argus_result:
            print(f"  Got Argus image from {argus_result['time'].strftime('%Y-%m-%d %H:%M')}")
            print(f"  Shape: {argus_result['image'].shape}")
            # Show time offset if search was needed
            offset_mins = argus_result.get('time_offset_minutes', 0)
            if offset_mins != 0:
                print(f"  Time offset from requested: {offset_mins} minutes ({offset_mins/60:.1f} hours)")
            native_extent = get_geotiff_extent(tmp_path)
            print(f"  Native GeoTIFF extent: {native_extent}")

            # Convert the Argus GeoTIFF bounds to lat/lon using the embedded CRS metadata.
            argus_extent = get_geotiff_extent(tmp_path, to_latlon=True)
            print(f"  Lat/Lon extent: {argus_extent}")
    except Exception as e:
        print(f"  Error fetching Argus imagery: {e}")

    # Clean up temp file
    import os
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)

    # Create the figure with height ratio - top plot shorter, bottom plot taller
    fig, axes = plt.subplots(2, 1, figsize=(14, 12), gridspec_kw={'height_ratios': [1, 2.5]})

    # =========================================
    # TOP PLOT: Wave height time series
    # =========================================
    ax1 = axes[0]

    colors = plt.cm.tab10(np.linspace(0, 1, len(wave_data)))

    for (gauge_name, data), color in zip(wave_data.items(), colors):
        if 'time' in data and 'Hs' in data:
            ax1.plot(data['time'], data['Hs'], label=gauge_name, color=color, linewidth=1.5)

    ax1.set_ylabel('Significant Wave Height (m)')
    if d1.year == d2.year:
        date_range_str = f'{d1.strftime("%d-%b")} to {d2.strftime("%d-%b-%Y")}'
    else:
        date_range_str = f'{d1.strftime("%d-%b-%Y")} to {d2.strftime("%d-%b-%Y")}'
    ax1.set_title(f'Wave Height at FRF Gauges\n{date_range_str}')
    ax1.legend(loc='upper right', fontsize=8, ncol=2)
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    ax1.tick_params(axis='x', rotation=45)

    # =========================================
    # BOTTOM PLOT: Gauge locations over imagery
    # =========================================
    ax2 = axes[1]

    # Plot satellite imagery as base layer (larger area)
    if sat_result is not None:
        ax2.imshow(sat_result['image'], extent=sat_result['extent'], aspect='auto', zorder=1)

    # Overlay Argus imagery at 50% opacity (smaller nearshore inset)
    if argus_result is not None and argus_extent is not None:
        ax2.imshow(argus_result['image'], extent=argus_extent, aspect='auto', alpha=0.5, zorder=2)

    # Plot gauge locations
    for i, gauge in enumerate(gauge_locations):
        if gauge['lat'] is not None and gauge['lon'] is not None:
            color_idx = gauge_list.index(gauge['name']) % len(colors)
            ax2.scatter(gauge['lon'], gauge['lat'], s=100, c=[colors[color_idx]],
                       edgecolors='white', linewidth=2, zorder=10)
            ax2.annotate(gauge['name'], (gauge['lon'], gauge['lat']),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=7, color='white', fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.7),
                        zorder=11)

    ax2.set_xlabel('Longitude')
    ax2.set_ylabel('Latitude')

    # Build title based on what imagery is available
    title_parts = ['FRF Wave Gauge Locations']
    if sat_result:
        title_parts.append(f'Satellite: {sat_result["time"].strftime("%Y-%m-%d")}')
    if argus_result:
        argus_title = f'Argus overlay (50% opacity): {argus_result["time"].strftime("%Y-%m-%d %H:%M")}'
        offset_mins = argus_result.get('time_offset_minutes', 0)
        if offset_mins != 0:
            argus_title += f' (offset: {offset_mins/60:.1f}h)'
        title_parts.append(argus_title)
    ax2.set_title('\n'.join(title_parts))

    # Set extent to satellite extent or compute from gauge locations
    if sat_result is not None:
        ax2.set_xlim(sat_result['extent'][0], sat_result['extent'][1])
        ax2.set_ylim(sat_result['extent'][2], sat_result['extent'][3])
    else:
        # Fallback: set extent based on gauge locations
        lons = [g['lon'] for g in gauge_locations if g['lon'] is not None]
        lats = [g['lat'] for g in gauge_locations if g['lat'] is not None]
        if lons and lats:
            pad = 0.01
            ax2.set_xlim(min(lons) - pad, max(lons) + pad)
            ax2.set_ylim(min(lats) - pad, max(lats) + pad)

    plt.tight_layout()

    # Save the figure
    output_file = 'frf_wave_and_imagery.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nFigure saved to: {output_file}")

    plt.show()

    # Print summary of gauge locations
    print("\n" + "="*80)
    print("Gauge Location Summary:")
    print("="*80)
    for gauge in gauge_locations:
        depth_str = f"{gauge['depth']:.1f}m" if gauge['depth'] is not None else "N/A"
        xfrf_str = f"{gauge['xFRF']:7.1f}m" if gauge['xFRF'] is not None else "N/A"
        yfrf_str = f"{gauge['yFRF']:7.1f}m" if gauge['yFRF'] is not None else "N/A"
        lat_str = f"{gauge['lat']:.6f}" if gauge['lat'] is not None else "N/A"
        lon_str = f"{gauge['lon']:.6f}" if gauge['lon'] is not None else "N/A"
        print(f"  {gauge['name']:15s} | lat: {lat_str}, lon: {lon_str} | "
              f"xFRF: {xfrf_str}, yFRF: {yfrf_str} | depth: {depth_str}")


if __name__ == '__main__':
    main()
