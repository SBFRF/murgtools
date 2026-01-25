'documented SB 12/2/17/'
import numpy as np
import pyproj
import pandas as pd

def FRF2ncsp(xFRF, yFRF):
    """this function makes NC stateplane out of X and Y FRF coordinates,
    based on kent Hathaway's code, bill birkmeir's calculations .
    written by Kent Hathaway.      15 Dec 2014
    Translated from Matlab to python 2015-11-30 - Spicer Bak

    Uses new fit (angles and scales) Bill Birkemeier determined in Nov 2014
    This version will determine the input based on values, outputs FRF, lat/lon,
    and state plane coordinates.  Uses NAD83-2011.



    yFRF = FRF Y (m), or Latitude (deg), or state plane Northing (m)

    NAD83-86	2014
    Origin Latitude          36.1775975
    Origin Longitude         75.7496860
    m/degLat             110963.357
    m/degLon              89953.364
    GridAngle (deg)          18.1465
    Angle FRF to Lat/Lon     71.8535
    Angle FRF to State Grid  69.9747
    FRF Origin Northing  274093.1562
    Easting              901951.6805

    Test:

        xFRF=566.93;
        yFRF=515.11;  % south rail at 1860
        p1 = 902307.92;
        p2 = 274771.22;

    Args:
      xFRF: frf coordinate system cross-shore locatioin
      yFRF: frf coordinat system alongshore location

    Returns:
       xFRF: cross shore location in FRF coordinate system

       yFRF: alongshore location in FRF coodrinate system

       spE: North Carolina state plane coordinate system Easting

       spN: North Carolina State Plane coordinate system Northing

    """
    r2d = 180.0 / np.pi;

    Eom = 901951.6805;  # % E Origin State Plane
    Nom = 274093.1562;  # % N Origin State Plane
    spAngle = (90 - 69.974707831) / r2d
    X = xFRF
    Y = yFRF

    R = np.sqrt(X ** 2 + Y ** 2)
    Ang1 = np.arctan2(X, Y)  # % CW from Y
    #  to state plane
    Ang2 = Ang1 - spAngle
    AspN = R * np.cos(Ang2)
    AspE = R * np.sin(Ang2)
    spN = AspN + Nom
    spE = AspE + Eom
    out = {'xFRF': xFRF,  'yFRF': yFRF, 'StateplaneE': spE, 'StateplaneN': spN}
    return out

def ncsp2FRF(p1, p2):
    """this function converts nc StatePlane (3200 fips) to FRF coordinates
    based on kent Hathaways Code
    #
    #  15 Dec 2014
    #  Kent Hathaway.
    #  Translated from Matlab to python 2015-11-30 - Spicer Bak
    #
    #  Uses new fit (angles and scales) Bill Birkemeier determined in Nov 2014
    #
    #  This version will determine the input based on values, outputs FRF, lat/lon,
    #  and state plane coordinates.  Uses NAD83-2011.
    #
    #  IO:
    #  p1 = FRF X (m), or Longitude (deg + or -), or state plane Easting (m)
    #  p2 = FRF Y (m), or Latitude (deg), or state plane Northing (m)
    #
    #  X = FRF cross-shore (m)
    #  Y = FRF longshore (m)
    #  ALat = latitude (decimal degrees)
    #  ALon = longitude (decimal degrees, positive, or W)
    #  spN = state plane northing (m)
    #  spE = state plane easting (m)
    
    NAD83-86	2014
    Origin Latitude       36.1775975
    Origin Longitude      75.7496860
    m/degLat              110963.357
    m/degLon               89953.364
    GridAngle (deg)          18.1465
    Angle FRF to Lat/Lon     71.8535
    Angle FRF to State Grid  69.9747
    FRF Origin Northing  274093.1562
    Easting              901951.6805
    
    #  Debugging values
    p1=566.93;  p2=515.11;  % south rail at 1860
    ALat = 36.1836000
    ALon = 75.7454804
    p2= 36.18359977;
    p1=-75.74548109;
    SP:  p1 = 902307.92;
    p2 = 274771.22;

    Args:
      spE: North carolina state plane coordinate system - Easting
      spN: North carolina state plane coordinate system - Northing
      p1: first point
      p2: second point

    Returns:
      dictionary
       'xFRF': cross shore location in FRF coordinates

       'yFRF': alongshore location in FRF coodrindate system

       'StateplaneE': north carolina state plane coordinate system - easting

       'StateplaneN': north carolina state plane coordinate system - northing

    """
    r2d = 180.0 / np.pi;
    Eom = 901951.6805;  # % E Origin State Plane
    Nom = 274093.1562;  # % N Origin State Plane
    spAngle = (90 - 69.974707831) / r2d

    spE = p1
    spN = p2  # designating stateplane vars


    # to FRF coords
    spLengE = p1 - Eom
    spLengN = p2 - Nom
    R = np.sqrt(spLengE ** 2 + spLengN ** 2)
    Ang1 = np.arctan2(spLengE, spLengN)
    Ang2 = Ang1 + spAngle
    # to FRF
    X = R * np.sin(Ang2)
    Y = R * np.cos(Ang2)
    # to Lat Lon
    ans = {'xFRF': X,
           'yFRF': Y,
           'StateplaneE': spE,
           'StateplaneN': spN}
    return ans

def ncsp2LatLon(spE, spN):
    """This function uses pyproj to convert state plane to lat/lon
    
    test points taken from conversions made in USACE SMS modeling system
    
    nc stateplane  meters NAD83
    spE1 = 901926.2 m
    spN1 = 273871.0 m
    Lon1 = -75.75004989
    Lat1 =  36.17560399
    
    spE2 = 9025563.9 m
    spN2 = 276229.5 m
    lon2 = -75.47218285
    lat2 =  36.19666112

    Args:
      spE: easting - assumed north carolina state plane Meters
      spN: northing - assumed north carolina state plane meters

    Returns:
      dictionary with original coords and output of latitude and longitude.
        'lat': latitude
        'lon': longitude
        'StateplaneE': NC stateplane
        'StateplaneN': NC stateplane

    """
    #      from pyproj import CRS
    # >>> c1 = CRS(proj='latlong',datum='WGS84')
    # >>> x1 = -111.5; y1 = 45.25919444444
    # >>> c2 = CRS(proj="utm",zone=10,datum='NAD27')
    # >>> x2, y2 = transform(c1, c2, x1, y1)
    # >>> "%s  %s" % (str(x2)[:9],str(y2)[:9])
    # '1402291.0  5076289.5'

    EPSG = 3358  # taken from spatialreference.org/ref/epsg/3358
    # NC stateplane NAD83
    spNC = pyproj.Proj("epsg:{}".format(EPSG))
    LL = pyproj.CRS(proj='latlon', datum='WGS84')#pyproj.Proj('epsg:{}'.format(epsgLL))  # epsg for NAD83 projection
    lon, lat = pyproj.transform(spNC, LL, spE, spN)

    return  {'lon': lon, 'lat': lat, 'StateplaneE': spE, 'StateplaneN': spN}

def LatLon2ncsp(lon, lat):
    """This function uses pyproj to convert longitude and latitude to stateplane
    
      test points taken from conversions made in USACE SMS modeling system
    
        nc stateplane  meters NAD83
        spE1 = 901926.2 m
        spN1 = 273871.0 m
        Lon1 = -75.75004989
        Lat1 =  36.17560399
    
        spE2 = 9025563.9 m
        spN2 = 276229.5 m
        lon2 = -75.47218285
        lat2 =  36.19666112

    Args:
      lon: geographic longitude (NAD83)  decimal degrees
      lat: geographic longitude (NAD83)  decimal degrees

    Returns:
      output dictionary with original coords and output of NC stateplane FIPS 3200
        'lat': latitude

        'lon': longitude

        'StateplaneE': NC stateplane

        'StateplaneN': NC stateplane

    """
    EPSG = 3358  # taken from spatialreference.org/ref/epsg/3358
    # NC stateplane NAD83
    spNC = pyproj.Proj(init="epsg:{}".format(EPSG))
    spE, spN = spNC(lon,lat)

    # epsgLL =  4269 # 4326
    # LL = pyproj.Proj('epsg:{}'.format(epsgLL))  # epsg for NAD83 projection
    # replaced below transform with direct conversion above
    # spE, spN = pyproj.transform(LL, spNC, lon, lat)
    ans = {'lon': lon, 'lat': lat, 'StateplaneE': spE, 'StateplaneN': spN}
    return ans

def FRFcoord(p1, p2, coordType=None):
    """updated FRF coord in python, using kent's original code as guide but converting pyproj for all
    conversions between state plane and Lat Lon,  Then all conversions between stateplane and
    FRF coordinates are done using kents original geometry.  Can force input to specfic coordinate type using coordType
    argument. Default will guess

    Args:
      p1: input any of the following to convert [lon, easting, xFRF]

      p2: input any of the following to convert [lat, northing, yFRF]

      coordType: valid values are ['LL', 'geographic', 'LatLon', 'spnc', 'ncsp', 'FRF'] (Default value = None)

    Returns:
        dictionary with appropriate data in it
            'xFRF': cross-shore FRF local coordinate system,

            'yFRF': along shore FRF local coordinte system,

            'StateplaneE': north carolina State Plane Easting ,

            'StateplaneN': north carolina State plane Northing,

            'Lat': Latitude ,

            'Lon': Longitude,

            'utmE': UTM easting

            'utmN': UTM northing

    Notes:
        From original code:
            #  15 Dec 2014
            #  Kent Hathaway.
            #  Translated from Matlab to python 2015-11-30 - Spicer Bak
            #
            #  Uses new fit (angles and scales) Bill Birkemeier determined in Nov 2014
            #
            #  This version will determine the input based on values, outputs FRF, lat/lon,
            #  and state plane coordinates.  Uses NAD83-2011.
            #
            #  IO:
            #  p1 = FRF X (m), or Longitude (deg + or -), or state plane Easting (m)
            #  p2 = FRF Y (m), or Latitude (deg), or state plane Northing (m)
            #
            #  X = FRF cross-shore (m)
            #  Y = FRF longshore (m)
            #  ALat = latitude (decimal degrees)
            #  ALon = longitude (decimal degrees, positive, or W)
            #  spN = state plane northing (m)
            #  spE = state plane easting (m)

            NAD83-86	2014
            Origin Latitude          36.1775975
            Origin Longitude         75.7496860
            m/degLat             110963.357
            m/degLon              89953.364
            GridAngle (deg)          18.1465
            Angle FRF to Lat/Lon     71.8535
            Angle FRF to State Grid  69.9747
            FRF Origin Northing  274093.1562
            Easting              901951.6805

            #  Debugging values
            p1=566.93;  p2=515.11;  % south rail at 1860
            ALat = 36.1836000
            ALon = 75.7454804
            p2= 36.18359977;  p1=-75.74548109;
            SP:  p1 = 902307.92; 	p2 = 274771.22;

    """

    # convert list to array if needed
    if isinstance(p1, list):
        p1 = np.asarray(p1)
    if isinstance(p2, list):
        p2 = np.asarray(p2)
    # now run checks to see what version of input we have!
    if np.size(p1) > 1:
        LL1 = (np.floor(np.absolute(p1)) == 75).all()
        LL2 = (np.floor(p2) == 36).all()
        SP1 = (p1 > 800000).all()
        SP2 = (p2 > 200000).all()
        UTM1 = (p1 > 300000).all()
        UTM2 = (p2 > 1000000).all()
        FRF1 = (p1 > -10000).all() and (p1 < 10000).all()
        FRF2 = (p2 > -10000).all() and (p2 < 10000).all()
    else:
        LL1 = np.floor(np.absolute(p1)) == 75
        LL2 = np.floor(p2) == 36
        SP1 = p1 > 800000
        SP2 = p2 > 200000
        UTM1 = p1 > 300000
        UTM2 = p2 > 1000000
        FRF1 = (p1 > -10000) and (p1 < 10000)
        FRF2 = (p2 > -10000) and (p2 < 10000)

    # Determine Data type
    if LL1 and LL2 or coordType in ['LL', 'geographic', 'LatLon']:  # lat/lon input
        sp = LatLon2ncsp(p1, p2)  # convert from lon/lat to state plane
        frf = ncsp2FRF(sp['StateplaneE'], sp['StateplaneN'])  # convert from nc state plane to FRF coords
        utm = LatLon2utm(p2, p1)  # convert to utm from lon/lat
        coordsOut = {'xFRF': frf['xFRF'], 'yFRF': frf['yFRF'], 'StateplaneE': sp['StateplaneE'],
                     'StateplaneN': sp['StateplaneN'], 'Lat': p2, 'Lon': p1, 'utmE': utm['utmE'], 'utmN': utm['utmN']}

    elif SP1 and SP2 or coordType in ['spnc', 'ncsp']:  # state plane input
        frf = ncsp2FRF(p1, p2)     # convert state plane to FRF
        ll = ncsp2LatLon(p1, p2)  # convert state plane to Lat Lon
        utm = LatLon2utm(ll['lat'], ll['lon'])
        coordsOut = {'xFRF': frf['xFRF'], 'yFRF': frf['yFRF'], 'StateplaneE': p1,
                     'StateplaneN': p2, 'Lat': ll['lat'], 'Lon': ll['lon'], 'utmE': utm['utmE'], 'utmN': utm['utmN']}

    elif UTM1 and UTM2:  # UTM input
        ll = utm2LatLon(p1, p2, 18, 'S')
        sp = LatLon2ncsp(ll['lon'], ll['lat'])
        frf = ncsp2FRF(sp['StateplaneE'], sp['StateplaneN'])
        coordsOut = {'xFRF': frf['xFRF'], 'yFRF': frf['yFRF'], 'StateplaneE': sp['StateplaneE'],
                     'StateplaneN': sp['StateplaneN'], 'Lat': ll['lat'], 'Lon': ll['lon'], 'utmE': p1, 'utmN': p2}

    elif (FRF1 and FRF2) or coordType in ['FRF']:  # FRF input
        # this is FRF in
        sp = FRF2ncsp(p1, p2)
        ll = ncsp2LatLon(sp['StateplaneE'], sp['StateplaneN'])
        utm = LatLon2utm(ll['lat'], ll['lon'])
        coordsOut = {'xFRF': p1, 'yFRF': p2, 'StateplaneE': sp['StateplaneE'],
                     'StateplaneN': sp['StateplaneN'], 'Lat': ll['lat'], 'Lon': ll['lon'], 'utmE': utm['utmE'], 'utmN': utm['utmN']}

    else:
        print('<<ERROR>> testbedUtils Geoprocess FRF coord Cound not determine input type, returning NaNs')
        coordsOut = {'xFRF': float('NaN'), 'yFRF': float('NaN'), 'StateplaneE': float('NaN'),
             'StateplaneN': float('NaN'), 'Lat': float('NaN'), 'Lon':float('NaN')}

    return coordsOut

def utm2LatLon(utmE, utmN, zn, zl):
    """uses utm library to convert utm points to lat/lon

    Args:
      utmE: utm easting
      utmN: utm northing
      zn: utm zone number
      zl: utm zone letter

    Returns:
      dict
        lat:  coordinates of the UTM input points
        lon:  coordinates of the utm input points

    """

    # check to see if points are...
    assert np.size(utmE) == np.size(utmN), 'utm2LatLon error: UTM point vectors must be equal lengths'

    #check to see if zn, zl are either both length 1 or the same length as p1, p2
    if np.size(zn) == 1:
        assert np.size(zn) == np.size(zl), 'utm2LatLon error: UTM zone number and letter must both be of length 1 or length of UTM point vectors'
    else:
        assert np.size(zn) == np.size(zl) == np.size(utmE), 'utm2LatLon error: UTM zone number and letter must both be of length 1 or length of UTM point vectors'

    columns = ['utmE', 'utmN', 'zn', 'zl']

    df = pd.DataFrame(index=list(range(0, np.size(utmE))), columns=columns)

    if np.size(utmE) > len(utmE):
        utmE = utmE[0]
        utmN = utmN[0]

    df['utmE'] = utmE
    df['utmN'] = utmN
    df['zn'] = zn
    df['zl'] = zl

    df['ll'] = df.apply(lambda x: utm.to_latlon(x.utmE, x.utmN, x.zn, x.zl), axis=1)

    L1, L2 = list(zip(*np.asarray(df['ll'])))

    return_dict = {}
    return_dict['lat'] = np.asarray(L1)
    return_dict['lon'] = np.asarray(L2)

    return return_dict

def LatLon2utm(lat, lon):
    """uses utm library to convert lat lon to UTM

    Args:
      lat: input value
      lon: input value

    Returns:
      dictionary
         utmE - UTM easting,
         utmN - northing,
         zn - zone number,
         zl - zone letter of each point

    """
    import utm

    # check to see if points are...
    assert np.size(lat) == np.size(lon), 'LatLon2utm error: lat lon coordinate vectors must be equal lengths'

    columns = ['lat', 'lon']

    df = pd.DataFrame(index=list(range(0, np.size(lat))), columns=columns)

    df['lat'] = lat
    df['lon'] = lon
    try:
        df['utm'] = df.apply(lambda x: utm.from_latlon(x.lat, x.lon), axis=1)
    except:
        df['utm'] = utm.from_latlon(df.lat.values, df.lon.values)

    utmE, utmN, zn, zl = list(zip(*np.asarray(df['utm'])))

    return_dict = {}
    return_dict['utmE'] = np.asarray(utmE)
    return_dict['utmN'] = np.asarray(utmN)
    return_dict['zn'] = np.asarray(zn)
    return_dict['zl'] = np.asarray(zl)

    return return_dict

def utm2ncsp(utmE, utmN, zn, zl):
    """uses utm library converts from utm to north carolina state plane

    Args:
      utmE: utm easting
      utmN: utm northing
      zn: utm zone number
      zl: utm zone letter

    Returns:
      dictionary
          easting  - ncsp easting

          northing - ncsp northing

    """
    import utm

    # so, all this does it go through Lat/Lon to get to ncsp..

    # check to see if points are...
    assert np.size(utmE) == np.size(utmE), 'utm2ncsp error: UTM point vectors must be equal lengths'

    #check to see if zn, zl are either both length 1 or the same length as p1, p2
    if np.size(zn) == 1:
        assert np.size(zn) == np.size(zl), 'utm2ncsp error: UTM zone number and letter must both be of length 1 or length of UTM point vectors'
    else:
        assert np.size(zn) == np.size(zl) == np.size(utmE), 'utm2ncsp error: UTM zone number and letter must both be of length 1 or length of UTM point vectors'

    columns = ['utmE', 'utmN', 'zn', 'zl']

    df = pd.DataFrame(index=list(range(0, np.size(utmE))), columns=columns)

    df['utmE'] = utmE
    df['utmN'] = utmN
    df['zn'] = zn
    df['zl'] = zl

    df['ll'] = df.apply(lambda x: utm.to_latlon(x.utmE, x.utmN, x.zn, x.zl), axis=1)

    L1, L2 = list(zip(*np.asarray(df['ll'])))

    ncsp_dict = LatLon2ncsp(np.asarray(L2), np.asarray(L1))

    return_dict = {}
    return_dict['easting'] = np.asarray(ncsp_dict['StateplaneE'])
    return_dict['northing'] = np.asarray(ncsp_dict['StateplaneN'])

    return return_dict

def ncsp2utm(easting, northing):
    """conversion from NC stateplnae to UTM

    Args:
      easting: ncstateplane easting
      northing: nc stateplane northing

    Returns:
      dictionary
          utmE - utm Easting

          utmN - utm Northing

          zn - zone number

          zl - zone letter

    """
    # all this does it go through lat/lon to get to utm...

    assert np.shape(easting) == np.shape(northing), 'ncsp2utm Error: northing and easting vectors must be same length'

    ll_dict = ncsp2LatLon(easting, northing)
    utm_dict = LatLon2utm(ll_dict['lat'], ll_dict['lon'])

    return utm_dict



