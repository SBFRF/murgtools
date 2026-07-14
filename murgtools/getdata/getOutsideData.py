# -*- coding: utf-8 -*-
"""Module for retrieving data that are not hosted by the FRF."""
import datetime as DT
import os
import re
import sys

import netCDF4 as nc
import numpy as np
from pyproj import Transformer

from murgtools import config

class forecastData:
    """A data retrival class situated around gathering forecast data."""
    def __init__(self, d1):
        """Initialization description here.
        
        Data are returned in self.datainex are inclusive at start,end

        Args:
          d1: datetime object start time of forecast data

        Returns:
          instance of forecastData
        """
        self.rawdataloc_wave = []
        self.outputdir = []  # location for outputfiles
        self.d1 = d1  # start date for data grab
        self.timeunits = config.TIME_UNITS
        self.epochd1 = nc.date2num(self.d1, self.timeunits)
        self.dataLocFRF = config.THREDDS_FRF_LOCAL_FRF
        self.dataLocTB = config.THREDDS_TESTBED
        self.dataLocCHL = config.THREDDS_CHL_ALT
        self.dataLocNCEP = config.NCEP_DATA_URL
        self.dataLocECWMF = 'ftp://data-portal.ecmwf.int/20170808120000/'  # ECMWF forecasts
        assert type(self.d1) == DT.datetime, 'end need to be in python "Datetime" data types'

    def getWW3(self, forecastHour, buoyNumber=44100):
        """This function will get spectral forecasts from the NCEP nomads server.
        
        The function will parse it out to geographic coordinate system. Currently, the data is
        transformed from oceanographic to meteorological coordinates and from
        units of m^2 s rad^-1 to m^2 s deg^-1 to maintain FRF gauge data
        conventions. Spectra are also sorted in ascending order by frequency and
        direction. The functionality associated with transforming the data may be
        more appropriately located in cmtb/PrepData.

        Args:
          forecastHour: param buoyNumber:
          buoyNumber:  (Default value = 44100)

        Returns:
          A dictionary with wave directions, frequencies, directional wave
          :key 'wavedirbin':
          :key 'wavefreqbin':
          :key 'dWED': 2dimensional wave spectra [t, freq, dir]
          :key 'lat': latitude
          :key 'lon': longitude
          :key 'time': date time
          spectra, and the timestamps for each spectrum.

        """
        import urllib.request, urllib.parse, urllib.error
        assert type(forecastHour) is str, 'Forecast hour variable must be a string'
        forecastHour = forecastHour.zfill(2)
        urlBack = '/bulls.t%sz/' %forecastHour +'multi_1.%d.spec' %buoyNumber
        ftpURL = self.dataLocNCEP + 'multi_1.' + self.d1.strftime('%Y%m%d') + urlBack
        ftpstream = urllib.request.urlopen(ftpURL)  # open url
        lines = ftpstream.readlines()  # read the lines of the url into an array of lines
        ftpstream.close()  # close connection with the server
        # # # # # # # # # # # # now the forecast spectra are in lines # # # # # # # # # # # #
        frequencies, directions, forcastDates, forcastDateLines = [], [], [], []

        for ii, line in enumerate(lines):  # read through each line
            split = line.split()   # split the current line up
            if split[0].strip("'")  == 'WAVEWATCH':  # is it the header of the file?
                nFreq = int(split[3])  # number of Frequencies
                nDir = int(split[4])
            elif len(split) == 8 or nFreq - len(frequencies) == len(split) and len(frequencies) != nFreq: # this is frequencies
                frequencies.extend(split)
            elif (len(split) == 7 or nDir - len(directions) == len(split)) and len(directions) != nDir:  # this is directions
                directions.extend(split)
            elif len(split[0]) == 8  and len(split) == 2: ## this is the date line for the beggining of a spectra
                # MPG: Include time component (second entry in date line).
                timestampstr = split[0] + split[1]
                timestamp = DT.datetime.strptime(timestampstr, '%Y%m%d%H%M%S')
                forcastDates.append(timestamp)
                forcastDateLines.append(ii)
        
        # MPG: convert directions and frequencies from list(string) to
        # np.array(float).
        directions = np.array(directions).astype('float')
        frequencies = np.array(frequencies).astype('float')

        # MPG: convert directions from radians to degrees.
        directions = np.rad2deg(directions)

        # MPG: convert directions from oceanographic to meteorological
        # convention to be consistent w/ FRF wave gauge data.
        small_angle = directions < 180.0
        directions[small_angle] = 180.0 + directions[small_angle]
        directions[~small_angle] = directions[~small_angle] - 180.0

        # MPG: sort directions and frequencies.
        didx = directions.argsort()
        fidx = frequencies.argsort()
        directions = directions[didx]
        frequencies = frequencies[fidx]
        
        ## now go back through 'lines' and parse spectra
        spectra = np.ones((len(forcastDateLines), nFreq, nDir), dtype=float) * 1e-8
        buoyNum, lon, lat, Depth, Hm0, Dp, b, c = [], [], [], [], [], [], [], []
        for ll in forcastDateLines:
            numLinesPerSpec = np.ceil(nFreq*float(nDir)/len(lines[ll+2].split())).astype(int)
            buoyStats = lines[ll+1].split()
            if ll == forcastDateLines[0]:  # if its not going to change only grab it once
                buoyNum = int(buoyStats[0].strip("'"))
                lon = float(buoyStats[2])
                lat = float(buoyStats[3])
                Depth = float(buoyStats[4])
            # Hm0.append(float(buoyStats[5])) # these need to be converted to meters ... is this actually wind?
            # Dp.append(float(buoyStats[6])) # these are not exported   ... are these wind?
            # b.append(float(buoyStats[7]))  # not sure what this field is .... wind speed?
            # c.append(float(buoyStats[8]))  # not sure what this field is  ... wind dir?

            tt = np.floor(float(ll) / (numLinesPerSpec - 1)).astype(int)  # time index
            linear = []
            for ss in range(numLinesPerSpec):
                # data =
                linear.extend(lines[ss + ll + 2].split())
            spectra[tt] = np.array(linear, dtype=float).reshape(nDir, nFreq).T
            spectra[tt] = spectra[tt][fidx][:,didx]

        # MPG: convert dWED from rad^-1 to deg^-1 to be consistent w/
        # FRF wave gauge data.
        spectra = spectra*2*np.pi / 180.0
        
        out = {'wavedirbin': directions,
               'wavefreqbin': frequencies,
               'buoyNum': buoyNum,
               'dWED': spectra,
               'lat': lat,
               'lon': lon,
               'Depth': Depth,
               'time': np.array(forcastDates)}

        return out

    def get_CbathyFromFTP(self, dlist, path, timex=True):
        """This function downloads argus cbathy bathy data from the argus ftp server.
        
        Times must be on the hour or half hour, it will return dates from a list
        provided as dlist.  dlist can be a single point (not in list) in time or
        a list of datetimes
        # written by Ty Hesser
        # modified by Spicer Bak
        

        Args:
            dlist(list, np.array): a list of  datetime dataList for cbathy data to be collected
            path (str): directory to put the cbathy file(s)
            timex:  (Default value = True)

        Returns:
            oflist (list): list of strings of files to be downloaded

        """
        curdir = os.getcwd()  # remembering where i am now
        if not os.path.exists(path):
            os.mkdir(path)
        os.chdir(path)  # changing locations to where data should be downloaded to
        # defining month string to month numbers
        mon = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul',
               8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
        # defining days of the week to day number
        dow = {0: 'Mon', 1: 'Tue', 2: 'Wed', 3: 'Thu', 4: 'Fri', 5: 'Sat', 6: 'Sun'}
        # quick data check
        if type(dlist) == DT.datetime:
            dlist = [dlist]  # making it into a list if its a single value
        assert type(dlist[0]) == DT.datetime, 'This function requires datetime dataList'
        # begin looping through data, acquiring cbathy data
        oflist = []
        for ii in range(0, len(dlist)):
            # assert dlist[ii].minute == 0 or dlist[ii].minute == 30, 'the minutes on your datetime object are not 0 or 30'
            if timex == True:
                din_m = DT.timedelta(0, seconds=1) + dlist[
                    ii]  # changing to data processed on the mintue and 31 of the hour
            else:
                din_m = dlist[ii] - DT.timedelta(0, 60)

            # creating month/day hours of timestamp that is being looked for
            yearc = din_m.strftime('%Y')  # string year
            # monthc = din_m.strftime('%m') # string month
            monthc = mon[din_m.month]  # making a month string
            tt = din_m.timetuple()  # making time tuple to make more strings
            dayc = din_m.strftime('%d')  # making a day string
            hourc = din_m.strftime('%H')
            mmc = str(tt.tm_min)  # making a minute string
            if len(mmc) == 1:
                mmc = '0' + mmc
            ssc = str(tt.tm_sec)
            if len(ssc) == 1:
                ssc = '0' + ssc
            # creating epoch time
            eptm = str(int(nc.date2num(din_m, 'seconds since 1970-01-01')))

            # creating the url to download the cbathy data from
            # frfserver = "'\\134.164.129.42\cil\argus02b\'"                       # at the frf
            OSUserver = "ftp://cil-ftp.coas.oregonstate.edu/pub/argus02b/"  # the oregon state server
            svr = OSUserver + yearc + "/cx/"  # server base
            daynum = str(tt.tm_yday)  # day number in a year
            fldr = daynum + "_" + monthc + "." + dayc  # defining the folder (date) structure to be used
            fname = "/" + eptm + '.' + dow[tt.tm_wday] + '.' + monthc + '.' + dayc + \
                    "_" + hourc + '_' + mmc + \
                    '_' + ssc + '.GMT.' + yearc + ".argus02b.cx.cBathy.mat"
            # fname = '/1445709540.Sat.Oct.24_17_59_00.GMT.2015.argus02b.cx.cBathy.mat'  # copied and pasted
            if timex == True:
                fname = '/*timex.merge.mat'
            addr = svr + fldr + fname
            print("checking " + fldr + fname)
            if os.path.isfile(fname[1:]):
                print("already downloaded: %s" % fname)
            elif not os.path.isfile(fname[1:]):
                # try:
                # dlfname = wget.download(addr)
                os.system('wget %s' % addr)
                # oflist.append(dlfname)
                # print 'Retrieved %s' %dlfname
                # except IOError:
                #    print "There is no file on the server, It's probably dark outside"

        os.chdir(curdir)
        #    import urllib
        #    urllib.urlretrieve(fn4)
        return oflist


def getSatelliteImagery(corners, filename=None, collection='sentinel-2-l2a',
                        date=None, max_cloud_cover=20, pad=0.01,
                        endpoint='element84'):
    """Retrieve satellite imagery from STAC catalog for any location on Earth.

    Fetches the nearest-in-time, cloud-filtered satellite imagery for a given
    area of interest. Supports rotated/skewed quadrilateral AOIs and returns
    georeferenced data suitable for overlay plotting.

    Args:
        corners: Four corner coordinates as [(lat, lon), (lat, lon), (lat, lon), (lat, lon)].
            Defines a quadrilateral AOI (can be rotated/skewed).
            Order: [top-left, top-right, bottom-left, bottom-right] or any consistent order.
        filename: Optional path to save image as GeoTIFF (default None).
        collection: STAC collection name. Options vary by endpoint:
            Element84 (default):
                - 'sentinel-2-l2a' (10m resolution, default)
                - 'landsat-c2-l2' (30m resolution)
            Planetary Computer:
                - 'naip' (1m resolution, US only)
                - 'sentinel-2-l2a' (10m resolution)
                - 'landsat-c2-l2' (30m resolution)
        date: datetime object for target date (default: most recent available).
        max_cloud_cover: Maximum cloud cover percentage to accept (default: 20).
            Note: NAIP doesn't have cloud cover metadata, so this is ignored for NAIP.
        pad: Bbox padding in degrees for conservative coverage (default: 0.01).
        endpoint: STAC endpoint to use. Options:
            - 'element84' (default): Element84 Earth Search
            - 'planetary-computer': Microsoft Planetary Computer (has NAIP 1m imagery)

    Returns:
        dict: Dictionary containing:
            - 'image': numpy.ndarray (H, W, 3) uint8 RGB, rotated to match AOI orientation
            - 'time': datetime object of scene acquisition
            - 'epochtime': float, seconds since 1970-01-01
            - 'bbox': [min_lon, min_lat, max_lon, max_lat], original query bbox
            - 'extent': [left, right, bottom, top], for matplotlib imshow extent param
            - 'corners_geo': [(lat, lon), ...], 4 corners of output image in geo coords
            - 'pixel_to_geo': function(px, py) -> (lat, lon), coordinate transform
            - 'geo_to_pixel': function(lat, lon) -> (px, py), inverse transform
            - 'resolution_m': float, approximate meters per pixel
            - 'rotation_angle': float, degrees of rotation applied
            - 'cloud_cover': float, cloud cover percentage of scene
            - 'collection': str, STAC collection used
            - 'scene_id': str, unique scene identifier
        Returns None if no imagery found matching criteria.

    Example:
        >>> import datetime as DT
        >>> corners = [
        ...     (36.1860983, -75.7529892),  # top-left
        ...     (36.1878844, -75.7464819),  # top-right
        ...     (36.1779848, -75.7496048),  # bottom-left
        ...     (36.1792073, -75.7421465)   # bottom-right
        ... ]
        >>> result = getSatelliteImagery(corners, date=DT.datetime(2024, 6, 15))
        >>> if result:
        ...     plt.imshow(result['image'], extent=result['extent'])
        ...     # Overlay a point
        ...     px, py = result['geo_to_pixel'](36.183, -75.749)
        ...     plt.plot(-75.749, 36.183, 'ro')

    """
    import requests
    import tifffile
    import tempfile
    from scipy.ndimage import rotate as scipy_rotate

    # 1. Parse corners - accept (lat, lon) format
    lons = [c[1] for c in corners]
    lats = [c[0] for c in corners]
    bbox = [min(lons) - pad, min(lats) - pad,
            max(lons) + pad, max(lats) + pad]

    # 2. Compute rotation angle from AOI orientation
    # corners[0] to corners[1] defines the "top edge" direction
    dx = corners[1][1] - corners[0][1]  # lon difference
    dy = corners[1][0] - corners[0][0]  # lat difference
    rotation_angle = np.degrees(np.arctan2(dy, dx))

    # 3. Build STAC search query based on endpoint
    if endpoint not in config.STAC_URLS:
        raise ValueError(f"Unknown endpoint '{endpoint}'. Options: {list(config.STAC_URLS.keys())}")

    stac_url = config.STAC_URLS[endpoint]

    if date is None:
        date = DT.datetime.now()

    # Search window: target date - 30 days to target date
    # NAIP is released yearly, so use larger window
    if collection == 'naip':
        date_start = (date - DT.timedelta(days=365)).strftime('%Y-%m-%dT00:00:00Z')
    else:
        date_start = (date - DT.timedelta(days=30)).strftime('%Y-%m-%dT00:00:00Z')
    date_end = date.strftime('%Y-%m-%dT23:59:59Z')

    query = {
        "collections": [collection],
        "bbox": bbox,
        "datetime": f"{date_start}/{date_end}",
        "limit": 20
    }

    # 4. Execute STAC search
    response = requests.post(stac_url, json=query)
    response.raise_for_status()
    results = response.json()

    if not results.get('features'):
        return None

    # Filter by cloud cover (skip for NAIP which doesn't have cloud metadata)
    if collection == 'naip':
        features = results['features']
    else:
        features = [f for f in results['features']
                    if f['properties'].get('eo:cloud_cover', 100) < max_cloud_cover]

    if not features:
        return None

    # Sort by datetime descending (most recent first)
    features.sort(key=lambda x: x['properties']['datetime'], reverse=True)
    item = features[0]

    # 5. Get visual/RGB composite asset URL (varies by collection)
    if collection == 'naip':
        # NAIP has 'image' asset with RGBIR bands
        if 'image' in item['assets']:
            rgb_url = item['assets']['image']['href']
        else:
            raise ValueError(f"No image asset found for NAIP {item['id']}")
    elif 'visual' in item['assets']:
        rgb_url = item['assets']['visual']['href']
    elif 'tci' in item['assets']:
        rgb_url = item['assets']['tci']['href']
    else:
        raise ValueError(f"No visual/RGB asset found for {item['id']}")

    # Sign URL if using Planetary Computer (required for asset access)
    if endpoint == 'planetary-computer':
        sign_url = f"{config.PLANETARY_COMPUTER_SIGN_URL}?href={rgb_url}"
        sign_resp = requests.get(sign_url)
        sign_resp.raise_for_status()
        rgb_url = sign_resp.json()['href']

    # 6. Download COG and read with tifffile
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        tmp_path = tmp.name
        resp = requests.get(rgb_url, stream=True)
        resp.raise_for_status()
        for chunk in resp.iter_content(chunk_size=8192):
            tmp.write(chunk)

    # Track whether we have GeoTIFF metadata for accurate UTM-based cropping
    has_geotiff_metadata = False
    tiepoint = None
    scale = None
    epsg = None

    try:
        image = tifffile.imread(tmp_path)

        # Extract actual image extent from GeoTIFF tags and convert to lat/lon
        # STAC bbox is not reliable for pixel coordinate calculation
        try:
            with tifffile.TiffFile(tmp_path) as tif:
                tags = tif.pages[0].tags
                tiepoint = tags[33922].value  # (i, j, k, x, y, z) - UTM coordinates
                scale = tags[33550].value     # (scaleX, scaleY, scaleZ)
                img_h, img_w = tif.pages[0].shape[:2]

                # UTM bounds - normalize with min/max to handle negative scale
                x_edge1 = tiepoint[3]
                x_edge2 = tiepoint[3] + img_w * scale[0]
                y_edge1 = tiepoint[4]
                y_edge2 = tiepoint[4] - img_h * scale[1]
                utm_left = min(x_edge1, x_edge2)
                utm_right = max(x_edge1, x_edge2)
                utm_bottom = min(y_edge1, y_edge2)
                utm_top = max(y_edge1, y_edge2)

                # Determine EPSG from GeoKeys first, then fall back to parsing projection string
                page = tif.pages[0]
                geotiff_tags = page.geotiff_tags or {}
                epsg = (geotiff_tags.get('ProjectedCSTypeGeoKey') or
                        geotiff_tags.get(3072) or
                        geotiff_tags.get('GeographicTypeGeoKey') or
                        geotiff_tags.get(2048))
                if hasattr(epsg, 'value'):
                    epsg = epsg.value
                if isinstance(epsg, str):
                    match = re.search(r'(\d+)', epsg)
                    epsg = int(match.group(1)) if match else None

                # Fall back to parsing projection string if GeoKeys not found
                if epsg is None:
                    proj_str = tags.get(34737, None)
                    if proj_str:
                        proj_str = proj_str.value
                        # Parse UTM zone from string like "WGS 84 / UTM zone 18N"
                        match = re.search(r'UTM zone (\d+)([NS])', str(proj_str))
                        if match:
                            zone = int(match.group(1))
                            hemisphere = match.group(2)
                            epsg = 32600 + zone if hemisphere == 'N' else 32700 + zone

                # Default to UTM zone 18N only as last resort
                if epsg is None:
                    epsg = 32618

                # Convert UTM corners to lat/lon
                transformer = Transformer.from_crs(f'EPSG:{epsg}', 'EPSG:4326', always_xy=True)

                tl_lon, tl_lat = transformer.transform(utm_left, utm_top)
                br_lon, br_lat = transformer.transform(utm_right, utm_bottom)

                # scene_bbox in lat/lon: [west, south, east, north]
                scene_bbox = [tl_lon, br_lat, br_lon, tl_lat]
                has_geotiff_metadata = True
        except KeyError:
            # Missing GeoTIFF georeferencing tags; fall back to STAC bbox if available.
            if isinstance(item, dict) and 'bbox' in item:
                scene_bbox = item['bbox']
    finally:
        os.unlink(tmp_path)

    # Handle NAIP's RGBIR format (4 bands) - extract RGB only
    if collection == 'naip' and image.ndim == 3 and image.shape[-1] == 4:
        image = image[:, :, :3]  # Keep only RGB, drop NIR

    # 7. Crop to bbox - use UTM coordinates if GeoTIFF metadata available
    h, w = image.shape[:2]
    import math

    if has_geotiff_metadata:
        # Use UTM coordinates for accurate pixel calculation
        to_utm = Transformer.from_crs('EPSG:4326', f'EPSG:{epsg}', always_xy=True)

        # Convert all 4 bbox corners to UTM and take min/max for proper bounds
        corners_ll = [
            (bbox[0], bbox[1]),  # SW
            (bbox[0], bbox[3]),  # NW
            (bbox[2], bbox[1]),  # SE
            (bbox[2], bbox[3]),  # NE
        ]
        corners_utm = [to_utm.transform(lon, lat) for lon, lat in corners_ll]
        bbox_utm_west = min(c[0] for c in corners_utm)
        bbox_utm_east = max(c[0] for c in corners_utm)
        bbox_utm_south = min(c[1] for c in corners_utm)
        bbox_utm_north = max(c[1] for c in corners_utm)

        # Use GeoTIFF origin and scale for pixel calculation
        utm_origin_x = tiepoint[3]
        utm_origin_y = tiepoint[4]
        scale_x = scale[0]
        scale_y = scale[1]

        # Compute pixel indices using floor/ceil to include full bbox
        # Handle negative scale by computing both edges and normalizing
        px_west = (bbox_utm_west - utm_origin_x) / scale_x
        px_east = (bbox_utm_east - utm_origin_x) / scale_x
        px_north = (utm_origin_y - bbox_utm_north) / scale_y
        px_south = (utm_origin_y - bbox_utm_south) / scale_y

        # Normalize pixel indices (handle negative scale)
        x1 = math.floor(min(px_west, px_east))
        x2 = math.ceil(max(px_west, px_east))
        y1 = math.floor(min(px_north, px_south))
        y2 = math.ceil(max(px_north, px_south))

        x1, x2 = max(0, x1), min(w, x2)
        y1, y2 = max(0, y1), min(h, y2)

        # Check for empty crop region (bbox outside scene)
        if x2 <= x1 or y2 <= y1:
            return None

        # Compute actual UTM bounds of cropped region
        # Use the normalized image coordinates (utm_left/right/bottom/top from earlier)
        # to ensure consistency regardless of scale sign
        actual_utm_x1 = utm_origin_x + x1 * scale_x
        actual_utm_x2 = utm_origin_x + x2 * scale_x
        actual_utm_y1 = utm_origin_y - y1 * scale_y
        actual_utm_y2 = utm_origin_y - y2 * scale_y
        actual_utm_west = min(actual_utm_x1, actual_utm_x2)
        actual_utm_east = max(actual_utm_x1, actual_utm_x2)
        actual_utm_south = min(actual_utm_y1, actual_utm_y2)
        actual_utm_north = max(actual_utm_y1, actual_utm_y2)

        # Convert actual UTM bounds back to lat/lon
        from_utm = Transformer.from_crs(f'EPSG:{epsg}', 'EPSG:4326', always_xy=True)
        actual_west, actual_south = from_utm.transform(actual_utm_west, actual_utm_south)
        actual_east, actual_north = from_utm.transform(actual_utm_east, actual_utm_north)

        resolution_m = abs(scale_x)  # GeoTIFF scale magnitude in meters for UTM
    else:
        # Fallback: use linear lat/lon mapping (less accurate but works without GeoTIFF metadata)
        px_per_deg_x = w / (scene_bbox[2] - scene_bbox[0])
        px_per_deg_y = h / (scene_bbox[3] - scene_bbox[1])

        x1 = math.floor((bbox[0] - scene_bbox[0]) * px_per_deg_x)
        x2 = math.ceil((bbox[2] - scene_bbox[0]) * px_per_deg_x)
        y1 = math.floor((scene_bbox[3] - bbox[3]) * px_per_deg_y)
        y2 = math.ceil((scene_bbox[3] - bbox[1]) * px_per_deg_y)

        x1, x2 = max(0, x1), min(w, x2)
        y1, y2 = max(0, y1), min(h, y2)

        # Check for empty crop region (bbox outside scene)
        if x2 <= x1 or y2 <= y1:
            return None

        # Compute actual bounds from pixel indices
        actual_west = scene_bbox[0] + x1 / px_per_deg_x
        actual_east = scene_bbox[0] + x2 / px_per_deg_x
        actual_north = scene_bbox[3] - y1 / px_per_deg_y
        actual_south = scene_bbox[3] - y2 / px_per_deg_y

        meters_per_deg = 111320 * np.cos(np.radians(np.mean(lats)))
        resolution_m = (actual_east - actual_west) / (x2 - x1) * meters_per_deg

    image = image[y1:y2, x1:x2]

    # 8. Ensure uint8 RGB format
    if image.dtype != np.uint8:
        image = np.clip(image / image.max() * 255, 0, 255).astype(np.uint8)

    # 9. Compute georeferencing before rotation
    deg_per_px_x = (actual_east - actual_west) / image.shape[1]
    deg_per_px_y = (actual_north - actual_south) / image.shape[0]

    # 10. Rotate image to match AOI orientation
    if abs(rotation_angle) > 0.1:
        image = scipy_rotate(image, -rotation_angle, reshape=True, order=1,
                            mode='constant', cval=0)
    post_rot_shape = image.shape[:2]

    # 11. Compute georeferencing for rotated image
    center_lon = (actual_west + actual_east) / 2
    center_lat = (actual_south + actual_north) / 2

    rot_rad = np.radians(rotation_angle)
    cos_r, sin_r = np.cos(rot_rad), np.sin(rot_rad)

    half_w_deg = (post_rot_shape[1] / 2) * deg_per_px_x
    half_h_deg = (post_rot_shape[0] / 2) * deg_per_px_y

    extent = [center_lon - half_w_deg, center_lon + half_w_deg,
              center_lat - half_h_deg, center_lat + half_h_deg]

    h_out, w_out = post_rot_shape
    corners_geo = [
        (center_lat + half_h_deg, center_lon - half_w_deg),
        (center_lat + half_h_deg, center_lon + half_w_deg),
        (center_lat - half_h_deg, center_lon - half_w_deg),
        (center_lat - half_h_deg, center_lon + half_w_deg),
    ]

    # Coordinate transform functions
    def geo_to_pixel(lat, lon):
        """Convert geographic coords to pixel coords in rotated image."""
        dx = lon - center_lon
        dy = lat - center_lat
        dx_rot = dx * cos_r + dy * sin_r
        dy_rot = -dx * sin_r + dy * cos_r
        px = int(w_out / 2 + dx_rot / deg_per_px_x)
        py = int(h_out / 2 - dy_rot / deg_per_px_y)
        return (px, py)

    def pixel_to_geo(px, py):
        """Convert pixel coords in rotated image to geographic coords."""
        dx_px = px - w_out / 2
        dy_px = h_out / 2 - py
        dx_deg = dx_px * deg_per_px_x
        dy_deg = dy_px * deg_per_px_y
        dx = dx_deg * cos_r - dy_deg * sin_r
        dy = dx_deg * sin_r + dy_deg * cos_r
        return (center_lat + dy, center_lon + dx)

    # 12. Save as GeoTIFF if filename provided
    if filename is not None:
        tiepoint = (0, 0, 0, extent[0], extent[3], 0)
        pixel_scale = (deg_per_px_x, deg_per_px_y, 0)
        geotiff_geokeys = (1, 1, 0, 3,
                          1024, 0, 1, 2,
                          1025, 0, 1, 1,
                          2048, 0, 1, 4326)

        tifffile.imwrite(filename, image, photometric='rgb',
                        extratags=[(33550, 'd', 3, pixel_scale),
                                   (33922, 'd', 6, tiepoint),
                                   (34735, 'H', 16, geotiff_geokeys)])

    # 13. Build return dict
    scene_time = DT.datetime.fromisoformat(
        item['properties']['datetime'].replace('Z', '+00:00')
    ).replace(tzinfo=None)

    return {
        'image': image,
        'time': scene_time,
        'epochtime': nc.date2num(scene_time, 'seconds since 1970-01-01 00:00:00'),
        'bbox': bbox,
        'extent': extent,
        'corners_geo': corners_geo,
        'pixel_to_geo': pixel_to_geo,
        'geo_to_pixel': geo_to_pixel,
        'resolution_m': resolution_m,
        'rotation_angle': rotation_angle,
        'cloud_cover': item['properties'].get('eo:cloud_cover'),
        'collection': collection,
        'scene_id': item['id']
    }
