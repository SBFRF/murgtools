import datetime as DT
import os
import netCDF4 as nc
import numpy as np
from matplotlib import pyplot as plt
from scipy.interpolate import griddata
from . import geoprocess as gp
from . import sblib as sb
from .anglesLib import geo2STWangle
import scipy.spatial
# Note: getObs and getDataTestBed imports are done locally in functions that need them
# to avoid circular imports

def frf2ij(xfrf, yfrf, x0, y0, dx, dy, ni, nj):
    """Convert FRF coordinates to ij grid locations.
    
    Matthew P. Geheran
    01 December 2017

    Args:
      xfrf(float): FRF x-coordinate to convert
      yfrf(float): FRF y-coordinate to convert
      x0(float): Grid origin x-coordinate (FRF)
      y0(float): Grid origin y-coordinate (FRF)
      dx(float): Grid resolution in x-direction.
        can be array of variable spaced cells, if so will handle it as cell centric values
      dy(float): Grid resolution in y-direction.
      ni(int): Number of grid cells in the i direction.
      nj(int): Number of grid cells in the j direction.

    Returns:
        i and j locations in cell

    """
    varibleSpaced = False  # default false
    dx_is_single_value = isinstance(dx, (float, int))
    dy_is_single_value = isinstance(dy, (float, int))

    # This routine assumes cell centric values (more cells than dx/dy values)
    if not dx_is_single_value or not dy_is_single_value:
        assert ni-1 == dx.shape[0], 'cell number must be greater than cell size '
        assert nj-1 == dy.shape[0], 'cell number must be greater than cell size '
        varibleSpaced = True

    if varibleSpaced == True:
        raise  NotImplementedError('See example in frontbackCMS')
        # shift origin to cell center instead of cell vertex
        x0N = x0 - dx[0]/2
        y0N = y0 - dy[0]/2
        # create new dx/dy array
        #dxN = dx[:-1] + np.diff(dx)/2
        # dyN = dy[:-1] + np.diff(dy)/2
        xFRFgrid, yFRFgrid = createGridNodesinFRF(x0N, y0N, dx, dy, ni, nj)
        xFRFgrid = x0 - np.arange(ni - 1) * dx
    else:
        xFRFgrid = x0 - np.arange(ni - 1) * dx - 0.5 * dx  # cell centric position of newly generated grid points in xFRF
        yFRFgrid = y0 - np.arange(nj - 1) * dy - 0.5 * dy  # cell centric position of newly generated grid points in yFRF
    i = np.abs(xfrf - xFRFgrid).argmin()  # find i and j values close to these locations
    j = np.abs(yfrf - yFRFgrid).argmin()

    # Convert from python base 0 indexing to STWAVE base 1.
    i += 1
    j += 1

    # Assign -99999 to i_sensor and j_sensor if the locations are
    # outside the grid.
    x_is_outside = xfrf < xFRFgrid.min() or xfrf > xFRFgrid.max()
    y_is_outside = yfrf < yFRFgrid.min() or yfrf > yFRFgrid.max()
    if x_is_outside or y_is_outside:
        i = -99999
        j = -99999

    return i, j

def makeCMSgridNodes(x0, y0, azi, dx, dy, z):
    """This interpolates from a node centric coordinate system defined by x0, y0
    to a cell centered values and returns

    Args:
      x0: Grid origin in NC stateplane
      y0: grid origin in NC stateplane
      azi: azimuth of the grid
      dx: array of x cell spacings (from ReadCMS_dep)
      dy: array of cell spacings (from ReadCMS_dep)
      z: elevation for dx, dx

    Returns:
      Dictionary with keys:
          'i': cell number for x direction

          'j': cell number for y direction

          'latitude': 2 d array  each cell location in latitude

          'longitude': 2 d array each cell location in longitude

          'easting': 2 d array each cell location in NC stateplane easting

          'northing': 2d array each cell location in NC stateplane northing

          'xFRF': FRF x coordinate values

          'yFRF': FRF y coordinate values

          'azimuth': grid azimuth

          'x0': grid origin x

          'y0': grid origin y

          'elevation': 2 d array of elevations

          'time': time of the grid in epoch time (0 is fill value) - currently set

    """
    # convert from node calculation to centric calculation
    # first move origin from vertex of grid to center of first grid cell

    # first convert to FRF coordinates
    FRF = gp.FRFcoord(x0, y0, coordType='ncsp')
    # shift origin to cell center instead of cell vertex
    x0N = FRF['xFRF'] - dx[0]/2
    y0N = FRF['yFRF'] - dy[0]/2
    # create new dx/dy array spaced with half of each of the 2 cells
    dxN = dx[:-1] + np.diff(dx)/2
    dyN = dy[:-1] + np.diff(dy)/2 # new nodes at the grid center - needed to fit into
    # create new nodes in FRF x and FRF Y using cell centric locations for accurate interpolation
    outXfrf, outYfrf = createGridNodesinFRF(x0N, y0N, dxN, dyN, dx.shape[0], dy.shape[0])
    xFRF, yFRF = np.meshgrid(outXfrf, sorted(outYfrf))
    # new work no need to loop as above
    convert2 = gp.FRFcoord(xFRF.flatten(), yFRF.flatten(), coordType='FRF')
    lat = convert2['Lat'].reshape(xFRF.shape)
    lon = convert2['Lon'].reshape(xFRF.shape)
    easting = convert2['StateplaneE'].reshape(xFRF.shape)
    northing = convert2['StateplaneN'].reshape(yFRF.shape)
    # making i's and j's for cell numbers
    ii = np.linspace(1, xFRF.shape[1], xFRF.shape[1])
    jj = np.linspace(1, yFRF.shape[0], yFRF.shape[0])

    BathyPacket = {'i': ii,
                   'j': jj,
                   'latitude': lat,
                   'longitude': lon,
                   'easting': easting,
                   'northing': northing,
                   'xFRF': sorted(xFRF[0, :]),
                   'yFRF': yFRF[:, 0],
                   'azimuth': azi,
                   'x0': x0,
                   'y0': y0,
                   'DX': dxN,
                   'DY': dyN,
                   'ni': len(ii),
                   'nj': len(jj),
                   'elevation': z,  # exported as [t, x,y] dimensions
                   'gridFname': 'CMS Grid',
                   'time': 0}

    return BathyPacket

def convertGridNodesFromStatePlane(icoords, jcoords):
    """this function converts nodes of a grid coordinate in state plane to FRF coordinates using FRFcoord function

    Args:
      icoords: an array of the i coordinates of a grid (easting, northing)
      jcoords: an array of the j coordinates of a grid (easting, northing)

    Returns:
      array of frf coordinates for I and J of the grid

    """

    out = gp.FRFcoord(icoords[0], icoords[1])
    outIfrf =  np.array((out['xFRF'], out['yFRF'])).T

    out = gp.FRFcoord(jcoords[0], jcoords[1])
    outJfrf = np.array((out['xFRF'], out['yFRF'])).T

    return outIfrf, outJfrf

def makeTimeMeanBackgroundBathy(dir_loc, dSTR_s=None, dSTR_e=None, scalecDict=None, splineDict=None, plot=None):
    """This function will create a time-averaged background surface. It takes in a background netcdf
    file and adds in every survey between the start and end dates. Each survey is converted to a grid using
    scaleCinterpolation.  These grids are all stacked on top of each other and averaged. This final grid is
    smoothed using the scale-C interpolation at the end then written to a netcdf file.

    Notes:
        the original background grid is only counted once;
        in areas where it is the only data point the other values are nan)


    Args:
      dSTR_s: string that determines the start date of the times of the surveys you want to use to update the DEM
          format is  dSTR_s = '2013-01-04T00:00:00Z' no matter what you put here, it will always round it down to
          the beginning of the month (Default value = None)
      dSTR_e: string that determines the end date of the times of the surveys you want to use to update the DEM
          format is dSTR_e = '2014-12-22T23:59:59Z' no matter what you put here, it will always round it up to the
          end of the month (Default value = None)
      dir_loc: place where you want to save the .nc files that get written
          the function will make the year directories inside of this location on its own.
      scalecDict(dict): keys are:
          x_smooth - x direction smoothing length for scalecInterp (default = 100)

          y_smooth - y direction smoothing length for scalecInterp (default = 200)

          splinebctype - type of spline to use (default = 10)
            2 - second derivative goes to zero at boundary
            1 - first derivative goes to zero at boundary
            0 - value is zero at boundary
            10 - force value and derivative(first?!?) to zero at boundary

          lc: spline smoothing constraint value (integer <= 1) (default = 4)

          dxm:  coarsening of the grid for spline (e.g., 2 means calculate with a dx that is 2x input dx)
              can be tuple if you want to do dx and dy separately (dxm, dym), otherwise dxm is used for both (default = 2)

          dxi: fining of the grid for spline (e.g., 0.1 means return spline on a grid that is 10x input dx)
              as with dxm, can be a tuple if you want separate values for dxi and dyi (default = 1)

          targetvar: this is the target variance used in the spline function. (default = 0.45)

          wbysmooth: y-edge smoothing length scale (default = 300)

          wbxsmooth: x-edge smoothing length scale (default = 100
    
      plot (bool): turn plot on or off (Default value = None)

    Returns:
        netCDF file of the time mean bathymetry

    """
    # import MakeUpdatedBathyDEM as mbD
    # TODO add directions as to where to import these or how to get them, where they should be located ....
    # from bsplineFunctions import bspline_pertgrid
    from scaleCinterp_python.DEM_generator import DEM_generator

    #HARD CODED VARIABLES!!!
    filelist = ['http://134.164.129.55/thredds/dodsC/FRF/geomorphology/elevationTransects/survey/surveyTransects.ncml']
    # this is just the location of the ncml for the transects!!!!!

    nc_b_loc = '/home/david/BathyTroubleshooting/BackgroundFiles'
    nc_b_name = 'backgroundDEMt0_tel.nc'
    # these together are the location of the standard background bathymetry that we started from.

    # Yaml files for my .nc files!!!!!
    # global_yaml = '/home/david/PycharmProjects/makebathyinterp/yamls/BATHY/FRFt0_global.yml'
    # var_yaml = '/home/david/PycharmProjects/makebathyinterp/yamls/BATHY/FRFt0_TimeMean_var.yml'

    # CS-array url - I just use this to get the position, not for any other data
    cs_array_url = 'http://134.164.129.55/thredds/dodsC/FRF/oceanography/waves/8m-array/2017/FRF-ocean_waves_8m-array_201707.nc'
    # where do I want to save any QA/QC figures
    fig_loc = '/home/david/BathyTroubleshooting/BackgroundFiles/TestFigs'

    #check scalecDict
    if scalecDict is None:
        x_smooth = 100  # scale c interp x-direction smoothing
        y_smooth = 200  # scale c interp y-direction smoothing
    else:
        x_smooth = scalecDict['x_smooth']  # scale c interp x-direction smoothing
        y_smooth = scalecDict['y_smooth']  # scale c interp y-direction smoothing

    #check dSTR_s
    if dSTR_s is None:
        dSTR_s = '1970-01-01T00:00:00Z' # set it to before the first survey

    #check dSTR_e
    if dSTR_e is None:
        dSTR_e = DT.datetime.strftime(DT.datetime.now(), '%Y-%m-%dT%H:%M:%SZ')  # set it to right now

    # force the survey to start at the first of the month and end at the last of the month!!!!
    dSTR_s = dSTR_s[0:7] + '-01T00:00:00Z'
    if dSTR_e[5:7] == '12':
        dSTR_e = str(int(dSTR_e[0:4]) + 1) + '-01' + '-01T00:00:00Z'
    else:
        dSTR_e = dSTR_e[0:5] + str(int(dSTR_e[5:7]) + 1).zfill(2) + '-01T00:00:00Z'

    d_s = DT.datetime.strptime(dSTR_s, '%Y-%m-%dT%H:%M:%SZ')
    d_e = DT.datetime.strptime(dSTR_e, '%Y-%m-%dT%H:%M:%SZ')

    # ok, I just need to go through and find all surveys that fall in this date range
    bathy = nc.Dataset(filelist[0])
    # pull down all the times....
    times = nc.num2date(bathy.variables['time'][:], bathy.variables['time'].units, bathy.variables['time'].calendar)
    all_surveys = bathy.variables['surveyNumber'][:]

    # find some stuff here...
    mask = (times >= d_s) & (times < d_e)  # boolean true/false of time
    idx = np.where(mask)[0]

    # what surveys are in this range?
    surveys = np.unique(bathy.variables['surveyNumber'][idx])

    # get rid of any surveys with rounded middle time not in my range
    for tt in range(0, len(surveys)):
        ids = (all_surveys == surveys[tt])
        surv_times = times[ids]
        # pull out the mean time
        surv_timeM = surv_times[0] + (surv_times[-1] - surv_times[0]) / 2
        # round it to nearest 12 hours.
        surv_timeM = sb.roundtime(surv_timeM, roundTo=1 * 12 * 3600)

        # if the rounded time IS in the month, great
        if (surv_timeM >= d_s) and (surv_timeM < d_e):
            pass
        else:
            # if not set it to a fill value
            surveys[tt] == -1000
    # drop all the surveys that we decided are not going to use
    surveys = surveys[surveys >= 0]


    # pull the original background DEM
    old_bathy = nc.Dataset(os.path.join(nc_b_loc, nc_b_name))
    Zi = old_bathy.variables['elevation'][:]
    xFRFi_vec = old_bathy.variables['xFRF'][:]
    yFRFi_vec = old_bathy.variables['yFRF'][:]

    # if xFRF, yFRF are masked, remove?
    xFRFi_vec = np.array(xFRFi_vec)
    yFRFi_vec = np.array(yFRFi_vec)

    # read out the dx and dy of the background grid!!!
    # assume this is constant grid spacing!!!!!
    dx = abs(xFRFi_vec[1] - xFRFi_vec[0])
    dy = abs(yFRFi_vec[1] - yFRFi_vec[0])

    xFRFi, yFRFi = np.meshgrid(xFRFi_vec, yFRFi_vec)
    rows, cols = np.shape(xFRFi)

    # pre-allocate my netCDF dictionary variables here....
    elevation = np.nan*np.zeros((len(surveys)+1, rows, cols))
    weights = np.nan * np.zeros((len(surveys) + 1, rows, cols))
    xFRF = np.zeros(cols)
    yFRF = np.zeros(rows)

    # ok, now that I have the list of the surveys I am going to keep.....
    for tt in range(0, len(surveys)):

        # get the times of each survey
        ids = (all_surveys == surveys[tt])

        # pull out this NC stuf!!!!!!!!
        dataX, dataY, dataZ = [], [], []
        dataX = bathy['xFRF'][ids]
        dataY = bathy['yFRF'][ids]
        dataZ = bathy['elevation'][ids]
        profNum = bathy['profileNumber'][ids]
        survNum = bathy['surveyNumber'][ids]
        stimes = nc.num2date(bathy.variables['time'][ids], bathy.variables['time'].units,
                             bathy.variables['time'].calendar)
        # pull out the mean time
        stimeM = min(stimes) + (max(stimes) - min(stimes)) / 2
        # round it to nearest 12 hours.
        stimeM = sb.roundtime(stimeM, roundTo=1 * 12 * 3600)

        assert len(np.unique(survNum)) == 1, 'makeTimeMeanBackgroundBathy error: You have pulled down more than one survey number!'
        assert isinstance(dataZ, np.ndarray), 'makeTimeMeanBackgroundBathy error: Script only handles np.ndarrays for the transect data at this time!'

        # build my new bathymetry from the FRF transect files

        # what are my subgrid bounds?
        surveyDict = {}
        surveyDict['dataX'] = dataX
        surveyDict['dataY'] = dataY
        surveyDict['profNum'] = profNum

        gridDict = {}
        gridDict['dx'] = dx
        gridDict['dy'] = dy
        gridDict['xFRFi_vec'] = xFRFi_vec
        gridDict['yFRFi_vec'] = yFRFi_vec

        # TODO: mbD (MakeUpdatedBathyDEM) module not available - see line 232
        # temp = mbD.subgridBounds2(surveyDict, gridDict, maxSpace=249)
        # x0 = temp['x0']
        # x1 = temp['x1']
        # y0 = temp['y0']
        # y1 = temp['y1']
        # del temp
        raise NotImplementedError("mbD.subgridBounds2 requires MakeUpdatedBathyDEM module which is not available")
        x0 = x1 = y0 = y1 = None  # Placeholders - code unreachable after raise above

        # if you wound up throwing out this survey!!!
        if x0 is None:
            newZi = np.nan * np.zeros(np.shape(Zi))

        else:
            print(np.unique(survNum))
            dict = {'x0': x0,  # gp.FRFcoord(x0, y0)['Lon'],  # -75.47218285,
                    'y0': y0,  # gp.FRFcoord(x0, y0)['Lat'],  #  36.17560399,
                    'x1': x1,  # gp.FRFcoord(x1, y1)['Lon'],  # -75.75004989,
                    'y1': y1,  # gp.FRFcoord(x1, y1)['Lat'],  #  36.19666112,
                    'lambdaX': dx,
                    # grid spacing in x  -  Here is where CMS would hand array of variable grid spacing
                    'lambdaY': dy,  # grid spacing in y
                    'msmoothx': x_smooth,  # smoothing length scale in x
                    'msmoothy': y_smooth,  # smoothing length scale in y
                    'msmootht': 1,  # smoothing length scale in Time
                    'filterName': 'hanning',
                    'nmseitol': 0.75,
                    'grid_coord_check': 'FRF',
                    'grid_filename': '',  # should be none if creating background Grid!  becomes best guess grid
                    'data_coord_check': 'FRF',
                    'xFRF_s': dataX,
                    'yFRF_s': dataY,
                    'Z_s': dataZ,
                    }

            out = DEM_generator(dict)

            # read some stuff from this dict like a boss
            Zn = out['Zi']
            xFRFn_vec = out['x_out']
            yFRFn_vec = out['y_out']
            MSEn = out['MSEi']
            targetvar = 0.45
            wb = 1 - np.divide(MSEn, targetvar + MSEn) # these are my weights from scale C

            try:
                x1 = np.where(xFRFi_vec == min(xFRFn_vec))[0][0]
                x2 = np.where(xFRFi_vec == max(xFRFn_vec))[0][0]
                y1 = np.where(yFRFi_vec == min(yFRFn_vec))[0][0]
                y2 = np.where(yFRFi_vec == max(yFRFn_vec))[0][0]

                newZi = np.nan * np.zeros(np.shape(Zi))
                newZi[y1:y2 + 1, x1:x2 + 1] = Zn

                new_wb = np.nan * np.zeros(np.shape(Zi))
                new_wb[y1:y2 + 1, x1:x2 + 1] = wb

            except IndexError:
                newZi = np.nan * np.zeros(np.shape(Zi))
                new_wb = np.nan * np.zeros(np.shape(wb))

            elevation[tt, :, :] = newZi
            weights[tt, :, :] = new_wb

            """
            # plot each newZi to see if it looks ok
            fig_name = 'backgroundDEM_' + str(surveys[tt]) + '.png'
            plt.pcolor(xFRFi_vec, yFRFi_vec, elevation[tt, :, :], cmap=plt.cm.jet, vmin=-13, vmax=5)
            cbar = plt.colorbar()
            cbar.set_label('(m)')
            plt.scatter(dataX, dataY, marker='o', c='k', s=1, alpha=0.25, label='Transects')
            plt.xlabel('xFRF (m)')
            plt.ylabel('yFRF (m)')
            plt.legend()
            plt.savefig(os.path.join(fig_loc, fig_name))
            plt.close()
            """

            """
            # plot where it is nan....
            nan_loc = np.isnan(elevation[tt, :, :])
            fig_name = 'backgroundDEM_' + str(surveys[tt]) + 'NaN_loc' + '.png'
            plt.pcolor(xFRFi_vec, yFRFi_vec, nan_loc, cmap=plt.cm.jet, vmin=0, vmax=1)
            cbar = plt.colorbar()
            plt.xlabel('xFRF (m)')
            plt.ylabel('yFRF (m)')
            plt.legend()
            plt.savefig(os.path.join(fig_loc, fig_name))
            plt.close()
            """

    # drop in my original bathymetry as the last index!
    elevation[-1, :, :] = Zi
    weights[-1, :, :] = np.ones((rows, cols))
    xFRF = xFRFi[0, :]
    yFRF = yFRFi[:, 1]


    cleaned_elevation = np.ma.masked_array(elevation, np.isnan(elevation))
    cleaned_weights = np.ma.masked_array(weights, np.isnan(weights))

    # do a nanmean on the elevation!!!!
    Z = np.ma.average(cleaned_elevation, axis=0, weights=cleaned_weights)


    """
    # plot the mean to see if that is the problem?
    fig_name = 'backgroundDEM_' + 'TimeMean_NoScaleC' + '.png'
    plt.pcolor(xFRFi_vec, yFRFi_vec, Z[:, :], cmap=plt.cm.jet, vmin=-13, vmax=5)
    cbar = plt.colorbar()
    cbar.set_label('(m)')
    plt.xlabel('xFRF (m)')
    plt.ylabel('yFRF (m)')
    plt.legend()
    plt.savefig(os.path.join(fig_loc, fig_name))
    plt.close()
    """


    # run this through the DEM_generator function to smooth it....
    xFRF_mesh, yFRF_mesh = np.meshgrid(xFRF, yFRF)
    # reshape them and my Z...

    dataX = np.reshape(xFRF_mesh, (np.shape(xFRF_mesh)[0] * np.shape(xFRF_mesh)[1], 1)).flatten()
    dataY = np.reshape(yFRF_mesh, (np.shape(yFRF_mesh)[0] * np.shape(yFRF_mesh)[1], 1)).flatten()
    dataZ = np.reshape(Z, (np.shape(Z)[0] * np.shape(Z)[1], 1)).flatten()

    dict = {'x0': max(xFRF),
            'y0': max(yFRF),
            'x1': min(xFRF),
            'y1': min(yFRF),
            'lambdaX': dx,
            # grid spacing in x  -  Here is where CMS would hand array of variable grid spacing
            'lambdaY': dy,  # grid spacing in y
            'msmoothx': int(x_smooth),  # smoothing length scale in x
            'msmoothy': int(2*y_smooth),  # smoothing length scale in y
            'msmootht': 1,  # smoothing length scale in Time
            'filterName': 'hanning',
            'nmseitol': 0.75,
            'grid_coord_check': 'FRF',
            'grid_filename': '',  # should be none if creating background Grid!  becomes best guess grid
            'data_coord_check': 'FRF',
            'xFRF_s': dataX,
            'yFRF_s': dataY,
            'Z_s': dataZ,
            }

    out2 = DEM_generator(dict)

    # read some stuff from this dict like a boss
    del Z
    del xFRF
    del yFRF
    Z = out2['Zi']
    MSEn = out2['MSEi']
    xFRF = out2['x_out']
    yFRF = out2['y_out']

    # do we want to spline the ends?
    if splineDict is None:
        pass
    else:
        # we do spline the ends....
        splinebctype = splineDict['splinebctype']
        lc = splineDict['lc']
        dxm = splineDict['dxm']
        dxi = splineDict['dxi']
        targetvar = splineDict['targetvar']

        # get the difference!!!!
        Zdiff = Z - Zi

        # spline time?
        wb = 1 - np.divide(MSEn, targetvar + MSEn)
        # TODO: bspline_pertgrid function not available - see line 234
        # newZdiff = bspline_pertgrid(Zdiff, wb, splinebctype=splinebctype, lc=lc, dxm=dxm, dxi=dxi)
        raise NotImplementedError("bspline_pertgrid requires bsplineFunctions module which is not available")
        newZdiff = None  # Placeholder - code unreachable after raise above
        newZ = Zi + newZdiff

        del Z
        Z = newZ

    # save this to an nc file?
    # write the nc_file for this month, like a boss, with greatness
    nc_dict = {}
    nc_dict['elevation'] = Z
    nc_dict['xFRF'] = xFRF
    nc_dict['yFRF'] = yFRF

    if plot is None:
        pass
    else:
        # plot the bathymetry before and after....
        # where is the cross shore array?
        test = nc.Dataset(cs_array_url)
        Lat = test['latitude'][:]
        Lon = test['longitude'][:]
        # convert to FRF
        temp = gp.FRFcoord(Lon, Lat)
        CSarray_X = temp['xFRF']
        CSarray_Y = temp['yFRF']

        # original data
        fig_name = 'backgroundDEM_orig' + '.png'
        plt.figure()
        plt.pcolor(xFRF, yFRF, Zi, cmap=plt.cm.jet, vmin=-13, vmax=5)
        cbar = plt.colorbar()
        cbar.set_label('(m)')
        plt.plot(CSarray_X, CSarray_Y, 'rX', label='8m-array')
        plt.xlabel('xFRF (m)')
        plt.ylabel('yFRF (m)')
        plt.legend()
        plt.savefig(os.path.join(fig_loc, fig_name))
        plt.close()

        # new time-mean data
        fig_name = 'backgroundDEM_TimeMean' + '.png'
        plt.figure()
        plt.pcolor(xFRF, yFRF, Z, cmap=plt.cm.jet, vmin=-13, vmax=5)
        cbar = plt.colorbar()
        cbar.set_label('(m)')
        plt.plot(CSarray_X, CSarray_Y, 'rX', label='8m-array')
        plt.xlabel('xFRF (m)')
        plt.ylabel('yFRF (m)')
        plt.legend()
        plt.savefig(os.path.join(fig_loc, fig_name))
        plt.close()

    nc_name = 'backgroundDEMt0tel_TimeMean' + '.nc'
    # makenc.makenc_t0BATHY(os.path.join(dir_loc, nc_name), nc_dict, globalYaml=global_yaml, varYaml=var_yaml)
    return nc_dict

def createGridNodesinFRF(x0, y0, dx, dy, ni, nj):
    """This function assumes azimuth of the grid is the same as that of the FRF coordinate system
    code developed for CMS wave and

    Args:
      x0: origin of x in FRF coords
      y0: origin of grid in FRF coords
      dx: Array of dx values
      dy: Array of dy values
      ni: number of cells in i
      nj: number of cells in j

    Returns:
      array of i coords, array of j coordinates

    """
    assert dx.shape[0] == ni-1, 'This function assumes that there are n-1 dx values'

    if np.mean(np.diff(dx)) != np.mean(dx):  # vairable spacing cell array
        icoord = np.zeros(ni)  # assume
        jcoord = np.zeros(nj)
        icoord[0] = x0
        jcoord[0] = y0
        for xx, dxx in enumerate(dx):
            icoord[xx+1] = icoord[xx] - dxx  # assumes offshore origin
        for yy, dyy in enumerate(dy):
            jcoord[yy+1] = jcoord[yy] - dyy
    else:
        raise NotImplementedError

    return icoord, jcoord

def makeBackgroundBathyAzimuth(origin, geo_ang, dx, dy, ni, nj, coord_system='FRF'):
    """This function makes the grid nodes using the origin and the azimuth

    Args:
      origin: this is the origin of your new grid in the form (xFRF, yFRF), (Lat, Lon), (easting, northing)
      geo_ang: angle of the x-axis of your grid clockwise relative to true north
      dx: x-direction spacing between your grid nodes in m
      dy: y-direction spacing between your grid nodes in m
      ni: number of nodes in the x-direction
      nj: number of nodes in the y-direction
      coord_system: FRF', 'utm', 'stateplane', 'LAT/LON' (Default value = 'FRF')

    Returns:
      dictionary with keys containing
      2D arrays of x & y grid nodes in the coordinate system you specify (easting/northing, lat/lon)
      2D array of bottom elevation at those node locations from the background dem

    """
    from getdatatestbed.getDataFRF import getObs

    assert len(origin) == 2, 'makeBackgroundBathy Error: invalid origin input.  origin input must be of form (xFRF, yFRF), (easting, northing), or (LAT, LON)'

    # first check the coord_system string to see if it matches!
    coord_list = ['FRF', 'stateplane', 'utm', 'Lat/Lon']
    import pandas as pd
    import string
    exclude = set(string.punctuation)
    columns = ['coord', 'user']
    df = pd.DataFrame(index=list(range(0, np.size(coord_list))), columns=columns)
    df['coord'] = coord_list
    df['user'] = coord_system
    df['coordToken'] = df.coord.apply(lambda x: ''.join(ch for ch in str(x) if ch not in exclude).strip().upper())
    df['coordToken'] = df.coordToken.apply(lambda x: ''.join(str(x).split()))
    df['userToken'] = df.user.apply(lambda x: ''.join(ch for ch in str(x) if ch not in exclude).strip().upper())
    df['userToken'] = df.userToken.apply(lambda x: ''.join(str(x).split()))
    userToken = np.unique(np.asarray(df['userToken']))[0]
    assert df['coordToken'].str.contains(userToken).any(), 'makeBackgroundBathy Error: invalid coord_system string.  Acceptable strings include %s' % coord_list

    # convert origin to stateplane if it isn't already....
    if userToken == 'FRF':
        temp = gp.FRF2ncsp(origin[0], origin[1])
        x0 = temp['StateplaneE']
        y0 = temp['StateplaneN']

    elif userToken == 'STATEPLANE':
        x0 = origin[0]
        y0 = origin[1]

    elif userToken == 'UTM':
        temp = gp.utm2ncsp(origin[0], origin[1], 18, 'S')
        x0 = temp['easting']
        y0 = temp['northing']

    elif userToken == 'LATLON':
        temp = gp.LatLon2ncsp(origin[1], origin[0])
        x0 = temp['StateplaneE']
        y0 = temp['StateplaneN']

    else:
        pass

    # convert my geographic coordinate angle to azimuth!!
    azi = geo2STWangle(geo_ang, zeroAngle=71.8)
    # azi = geo_ang

    # note: I just striaght up pulled this bit of code from CreateGridNodesInStatePlane

    # calculating change in alongshore coordinate for northing and easting
    # given the associated dx dy
    dE_j = dy * np.cos(np.deg2rad(azi + 90))
    dN_j = dy * np.sin(np.deg2rad(azi + 90))

    # calculating change in cross-shore coordinate for northing and easting
    dE_i = dx * np.cos(np.deg2rad(azi))
    dN_i = dx * np.sin(np.deg2rad(azi))

    easting = np.zeros((ni, nj))
    northing = np.zeros((ni, nj))

    for ii in range(0, ni):
        for jj in range(0, nj):
            easting[ii, jj] = x0 + ii * dE_i + jj * dE_j
            northing[ii, jj] = y0 + ii * dN_i + jj * dN_j


    #convert all my new points to utm!
    east_vec = easting.reshape((1, easting.shape[0] * easting.shape[1]))[0]
    north_vec = northing.reshape((1, northing.shape[0] * northing.shape[1]))[0]

    # convert them to UTM
    temp = gp.ncsp2utm(east_vec, north_vec)
    utmE = temp['utmE']
    utmN = temp['utmN']


    # pull out the piece of the DEM I need!
    # these are just some random times I made up because the getObs class requires it.  They have no effect on the
    # bathymetry that is pulled, so put whatever you want in here...
    d_s = DT.datetime.strptime('2015-06-20T12:00:00Z', '%Y-%m-%dT%H:%M:%SZ')
    d_e = DT.datetime.strptime('2015-06-20T12:00:00Z', '%Y-%m-%dT%H:%M:%SZ')
    frf_bathy = getObs(d_s, d_e)
    buffer = 20 # buffer around my grid in m to make sure I pull at least one point to the outside

    bathyDEM = frf_bathy.getBathyRegionalDEM(min(utmE) - buffer, max(utmE) + buffer, min(utmN) - buffer, max(utmN) + buffer)
    assert np.size(np.where(bathyDEM == -9999)) <= 1, 'makeBackgroundDEM Error:  Your domain contains areas with no background DEM data!'


    # interpolate the bottom elevation onto my new nodes!!!!
    utmEdem = bathyDEM['utmEasting'].reshape((1, bathyDEM['utmEasting'].shape[0] * bathyDEM['utmEasting'].shape[1]))[0]
    utmNdem = bathyDEM['utmNorthing'].reshape((1, bathyDEM['utmNorthing'].shape[0] * bathyDEM['utmNorthing'].shape[1]))[0]

    points = (utmEdem, utmNdem)
    values = bathyDEM['bottomElevation'].reshape((1, bathyDEM['bottomElevation'].shape[0] * bathyDEM['bottomElevation'].shape[1]))[0]


    # do the interpolation
    bottomElevation_vec = griddata(points, values, (utmE, utmN), method='linear')
    # reshape it back to 2D array!
    bottomElevation = bottomElevation_vec.reshape((easting.shape[0], easting.shape[1]))


    # now convert my stateplane grid back into the coordinates specified!!!!
    if userToken == 'FRF':
        temp = gp.ncsp2FRF(east_vec, north_vec)
        x_vec = temp['xFRF']
        y_vec = temp['yFRF']

    elif userToken == 'STATEPLANE':
        x_vec = east_vec
        y_vec = north_vec

    elif userToken == 'UTM':
        x_vec = utmE
        y_vec = utmN

    elif userToken == 'LATLON':
        temp = gp.ncsp2LatLon(east_vec, north_vec)
        x_vec = temp['lon']
        y_vec = temp['lat']

    else:
        pass


    # reshape them back
    x = x_vec.reshape((easting.shape[0], easting.shape[1]))
    y = y_vec.reshape((easting.shape[0], easting.shape[1]))

    # return the grid in the coordinate system of the origin
    out = {}
    out['bottomElevation'] = bottomElevation

    if userToken == 'FRF':
        out['xFRF'] = x
        out['yFRF'] = y

    elif userToken == 'STATEPLANE':
        out['easting'] = x
        out['northing'] = y

    elif userToken == 'UTM':
        out['utmEasting'] = x
        out['utmNorthing'] = y

    elif userToken == 'LATLON':
        out['longitude'] = x
        out['latitude'] = y

    else:
        pass

    return out

def makeBackgroundBathyCorners(LLHC, URHC, dx, dy, coord_system='FRF'):
    """This function makes grid nodes using the corners of the grid using different coordinate systems

    Args:
        LLHC: tuple: lower left hand corner of the desired domain (xFRF, yFRF) (easting, northing) or (Lat, Lon)
        URHC: tuple: upper right hand corner of the desired domain (xFRF, yFRF) (easting, northing) or (Lat, Lon)
        dx: x-direction grid spacing in m - lat/lon corners get converted to utm!!!
        dy: y-direction grid spacing in m - lat/lon corners get converted to utm!!!
        coord_system(str): string containing the coordinate system for your corners ('FRF' 'utm', 'stateplane', or 'LAT/LON') (Default value = 'FRF')

    Returns:
        dictionary containing 2D arrays of:
           xFRF (or easting or longitude)

           yFRF (or northing or Latitude)

           bottomElevation at those points interpolated from background DEM onto desired grid

    """
    from getdatatestbed.getDataFRF import getObs

    # first check the coord_system string to see if it matches!
    coord_list = ['FRF', 'LAT/LON', 'utm', 'stateplane']
    import pandas as pd
    import string
    exclude = set(string.punctuation)
    columns = ['coord', 'user']
    df = pd.DataFrame(index=list(range(0, np.size(coord_list))), columns=columns)
    df['coord'] = coord_list
    df['user'] = coord_system
    df['coordToken'] = df.coord.apply(lambda x: ''.join(ch for ch in str(x) if ch not in exclude).strip().upper())
    df['coordToken'] = df.coordToken.apply(lambda x: ''.join(str(x).split()))
    df['userToken'] = df.user.apply(lambda x: ''.join(ch for ch in str(x) if ch not in exclude).strip().upper())
    df['userToken'] = df.userToken.apply(lambda x: ''.join(str(x).split()))
    userToken = np.unique(np.asarray(df['userToken']))[0]
    assert df['coordToken'].str.contains(userToken).any(), 'makeBackgroundBathy Error: invalid coord_system string.  Acceptable strings include %s' % coord_list

    # second, check the format of the corner inputs
    LLHC = np.asarray(LLHC)
    URHC = np.asarray(URHC)
    assert len(LLHC) == len(URHC) == 2, 'makeBackgroundBathy Error: invalid corner input.  corner inputs must be of form (xFRF, yFRF) (easting, northing) or (LAT, LON)'


    # make my new grid first!!!
    x_pts = [LLHC[0], URHC[0]]
    y_pts = [LLHC[1], URHC[1]]

    if userToken == 'LATLON':
        # if corners are in LAT/LON then we convert directly to UTM and work from that
        temp = gp.LatLon2utm(x_pts, y_pts)
        x_vec = np.arange(min(temp['utmE']), max(temp['utmE']), dx)
        y_vec = np.arange(min(temp['utmN']), max(temp['utmN']), dy)

    else:
        x_vec = np.arange(x_pts[0], x_pts[1], dx)
        y_vec = np.arange(y_pts[0], y_pts[1], dy)


    xv, yv = np.meshgrid(x_vec, y_vec)
    # reshape my points
    xv_vec = xv.reshape((1, xv.shape[0] * xv.shape[1]))[0]
    yv_vec = yv.reshape((1, yv.shape[0] * yv.shape[1]))[0]


    # convert all my points to UTM
    utmE = np.zeros(len(xv_vec))
    utmN = np.zeros(len(yv_vec))
    if userToken == 'FRF':
        for ii in range(0, len(xv_vec)):
            # note: I didn't use FRFcoord fxn because I don't want the code to "guess" what coordinate system I am in.
            temp = gp.FRF2ncsp(xv_vec[ii], yv_vec[ii])
            spE = temp['StateplaneE']
            spN = temp['StateplaneN']
            temp2 = gp.ncsp2utm(spE, spN)
            utmE[ii] = temp2['utmE']
            utmN[ii] = temp2['utmN']

    elif userToken == 'LATLON':
        utmE = xv_vec
        utmN = yv_vec

    elif userToken == 'UTM':
        utmE = xv_vec
        utmN = yv_vec

    elif userToken == 'STATEPLANE':
        temp = gp.ncsp2utm(xv_vec, yv_vec)
        utmE = temp['utmE']
        utmN = temp['utmN']



    # these are just some random times I made up because the getObs class requires it.  They have no effect on the
    # bathymetry that is pulled, so put whatever you want in here...
    d_s = DT.datetime.strptime('2015-06-20T12:00:00Z', '%Y-%m-%dT%H:%M:%SZ')
    d_e = DT.datetime.strptime('2015-06-20T12:00:00Z', '%Y-%m-%dT%H:%M:%SZ')
    frf_bathy = getObs(d_s, d_e)
    buffer = 20  # buffer in m(grid spacing is 10m, so this will make sure you always
    # have at least one node to each side

    bathyDEM = frf_bathy.getBathyRegionalDEM(min(utmE) - buffer, max(utmE) + buffer, min(utmN) - buffer, max(utmN) + buffer)

    # the getBathyDEM function will check to see if you are too close to the bounds.
    # All you have to do now is check to see if any piece of this sub-DEM has fill values instead of data!

    assert np.size(np.where(bathyDEM == -9999)) <= 1, 'makeBackgroundDEM Error:  Your domain contains areas with no background DEM data!'

    """
    # check to see if this actually worked...
    import matplotlib.pyplot as plt
    fig_name = 'DEMsubgrid.png'
    fig_loc = 'C:\\Users\RDCHLDLY\Desktop\David Stuff\Projects\CSHORE\Bathy Interpolation\Test Figures'
    plt.contourf(bathyDEM['utmEasting'], bathyDEM['utmNorthing'], bathyDEM['bottomElevation'])
    plt.axis('equal')
    plt.savefig(os.path.join(fig_loc, fig_name))
    plt.close()
    """

    # reshape my DEM into a list of points
    utmEdem = bathyDEM['utmEasting'].reshape((1, bathyDEM['utmEasting'].shape[0] * bathyDEM['utmEasting'].shape[1]))[0]
    utmNdem = bathyDEM['utmNorthing'].reshape((1, bathyDEM['utmNorthing'].shape[0] * bathyDEM['utmNorthing'].shape[1]))[0]

    points = (utmEdem, utmNdem)
    values = bathyDEM['bottomElevation'].reshape((1, bathyDEM['bottomElevation'].shape[0] * bathyDEM['bottomElevation'].shape[1]))[0]
    # do the interpolation
    bottomElevation_vec = griddata(points, values, (utmE, utmN), method='linear')
    # reshape it back to 2D array!
    bottomElevation = bottomElevation_vec.reshape((xv.shape[0], xv.shape[1]))

    # so now I have xv, yv, bottomElevation on a rectangular grid in my new coordinate system. I think
    """
    # check to see if this actually worked...
    import matplotlib.pyplot as plt
    fig_name = 'newGrid.png'
    fig_loc = 'C:\\Users\RDCHLDLY\Desktop\David Stuff\Projects\CSHORE\Bathy Interpolation\Test Figures'
    plt.contourf(xv, yv, bottomElevation)
    plt.axis('equal')
    plt.xlabel('xFRF')
    plt.ylabel('yFRF')
    plt.savefig(os.path.join(fig_loc, fig_name))
    plt.close()
    """

    # now return my stuff to the user....
    out = {}
    if userToken == 'FRF':
        out['xFRF'] = xv
        out['yFRF'] = yv
        out['bottomElevation'] = bottomElevation

    elif userToken == 'STATEPLANE':
        out['easting'] = xv
        out['northing'] = yv
        out['bottomElevation'] = bottomElevation

    elif userToken == 'UTM':
        out['utmEasting'] = xv
        out['utmNorthing'] = yv
        out['bottomElevation'] = bottomElevation

    elif userToken == 'LATLON':
        # if it is lat lon I have to convert all my points back from UTM!!!!
        temp = gp.utm2LatLon(xv_vec, yv_vec, 18, 'S')

        lat_vec = temp['lat']
        lon_vec = temp['lon']

        out['latitude'] = lat_vec.reshape((xv.shape[0], xv.shape[1]))
        out['longitude'] = lon_vec.reshape((xv.shape[0], xv.shape[1]))
        out['bottomElevation'] = bottomElevation

    else:
        pass

    return out

def CreateGridNodesInStatePlane(x0, y0, azi, dx, dy, ni, nj):
    """this function takes in a sim file and creates tuples of grid locations
    in state plane, can further be converted to lat/lon
    stateplane sp3200

    Args:
      x0: integer/float describing origin in x (easting)
      y0: integer/float describing origin in y (northing)
      azi: grid azimuth defining rotation of grid
      dx: can be integer/float or numpy array/list describing cell width in x direction (i)
      dy: can be integer/float or numpy array/list describing cell with in y direction (j)
      ni: integer/float describing number of cells in i
      nj: integer/float describing  number of cells in j

    Returns:
      tuples of i/j coords, jStatePlane in stateplane sp3200

    """
    # calculating change in alongshore coordinate for northing and easting
    # given the associated dx dy
    dE_j = dy * np.cos(np.deg2rad(azi + 90))
    dN_j = dy * np.sin(np.deg2rad(azi + 90))
    # calculating change in cross-shore coordinate for northing and easting
    dE_i = dx * np.cos(np.deg2rad(azi))
    dN_i = dx * np.sin(np.deg2rad(azi))
    # create Easting & Northing coordinates for
    # cross shore location (in grid space)
    try:  # this works for when dE_i is not an array .... ie regularly spaced grid nodes
        easting_i = np.linspace(x0, x0 + ni * dE_i, num=ni, endpoint=True)
        northing_i = np.linspace(y0, y0 + ni * dN_i, num=ni, endpoint=True)
        # create Northing and Easting coords for Along-shore location
        easting_j = np.linspace(x0, x0 + nj * dE_j, num=nj, endpoint=True)
        northing_j = np.linspace(y0, y0 + nj * dN_j, num=nj, endpoint=True)
    except ValueError:  # for instances when grid nodes are irregularly spaced
        easting_i, northing_i = [x0], [y0]  # seeding the origin for the first value in the coordinates
        easting_j, northing_j = [x0], [y0]
        for ii in range(0, ni-1):  # first doing the i coordinate (start at origin add the change in e/n for each grid cell
            easting_i.append(easting_i[ii] + dE_i[ii])
            northing_i.append(northing_i[ii] + dN_i[ii])
        for jj in range(0, nj-1):
            easting_j.append(easting_j[jj] + dE_j[jj])
            northing_j.append(northing_j[jj] + dN_j[jj])
        # convert lists to arrays
        easting_i = np.array(easting_i)
        easting_j = np.array(easting_j)
        northing_i = np.array(northing_i)
        northing_j = np.array(northing_j)
        assert easting_j.shape[0] == nj, 'len of cstateplane sp3200oordinates are not the same as the number of cells'
        assert northing_i.shape[0] == ni, 'len of coordinates are not the same as the number of cells'

    icoords = np.array([easting_i, northing_i])
    jcoords = np.array([easting_j, northing_j])

    return icoords, jcoords

def interpIntegratedBathy4UnstructGrid(ugridDict, THREDDS='FRF', forcedSurveyDate=None, bathy=None):
    """This function takes scattered x & y points and returns elevations at those points interpolated used for grid.
    
    
    DLY Note - 3/27/2018: this function has only been verified to work for NCSP meters!!!!
                          other coordinate systems and english units have not been checked!!!
    Arg:
        ugridDict: dictionary containing unstructured gridded data
            'x': xFRF, NCSP Easting, UTM Easting, or Lat
            
            'y': yFRF, NCSP Northing, UTM Easting, or Lon
            
            'coord_system': string containing the coordinate system for your corners ('FRF' 'utm', 'stateplane',
                or 'LAT/LON') (Default value = 'FRF')
            
            'units': ('meters', 'm') or ('feet', 'ft')

        # note: if coord_system is 'UTM' this code assumes you are in zone number 18 and zone letter S!  This is the
        # zone number/letter in the vicinity of the FRF property!!!!

        THREDDS: 'FRF' or 'CHL'(default='FRF')
        forcedSurveyDate: datestring in the format of '2017-10-10T00:00:00Z' or datetime. will use most recent survey if
            not specified.
        bathy: this is blank unless you want to directly hand it a bathy dictionary.  the dictionary needs to be in the
            same format as the output of cmtb_data.getBathyIntegratedTransect()
    
    Returns:
         out: output dictionary
            'z': elevation at each of those points interpolated from the integrated bathymetry product - units will be
                same as input.  will return nans where extrapolated.
                
            'surveyDate': datestring or datetime of the survey that these values came from.
            
    """
    # first check the coord_system string to see if it matches!
    coord_list = ['FRF', 'LAT/LON', 'utm', 'stateplane', 'ncsp']
    import pandas as pd
    import string
    exclude = set(string.punctuation)
    columns = ['coord', 'user']
    df = pd.DataFrame(index=list(range(0, np.size(coord_list))), columns=columns)
    df['coord'] = coord_list
    df['user'] = ugridDict['coord_system']
    df['coordToken'] = df.coord.apply(lambda x: ''.join(ch for ch in str(x) if ch not in exclude).strip().upper())
    df['coordToken'] = df.coordToken.apply(lambda x: ''.join(str(x).split()))
    df['userToken'] = df.user.apply(lambda x: ''.join(ch for ch in str(x) if ch not in exclude).strip().upper())
    df['userToken'] = df.userToken.apply(lambda x: ''.join(str(x).split()))
    coordToken = np.unique(np.asarray(df['userToken']))[0]
    assert df['coordToken'].str.contains(coordToken).any(), 'Error: invalid coord_system string.  Acceptable strings include %s' % coord_list

    # first deal with lat/lon stuff
    if coordToken == 'LATLON':
        # if corners are in LAT/LON then we convert directly to FRF and work from that
        temp = gp.LatLon2ncsp(ugridDict['y'], ugridDict['x'])
        temp2 = gp.ncsp2FRF(temp['StateplaneE'], temp['StateplaneN'])
        x = temp2['xFRF']  # these should be in m
        y = temp2['yFRF']  # these should be in m
    else:
        # check to see if we are in m or feet
        del df
        units_list = ['meters', 'm', 'feet', 'ft']
        columns = ['coord', 'user']
        df = pd.DataFrame(index=list(range(0, np.size(units_list))), columns=columns)
        df['units'] = units_list
        df['user'] = ugridDict['units']
        df['unitToken'] = df.units.apply(lambda x: ''.join(ch for ch in str(x) if ch not in exclude).strip().upper())
        df['unitToken'] = df.unitToken.apply(lambda x: ''.join(str(x).split()))
        df['userToken'] = df.user.apply(lambda x: ''.join(ch for ch in str(x) if ch not in exclude).strip().upper())
        df['userToken'] = df.userToken.apply(lambda x: ''.join(str(x).split()))
        unitToken = np.unique(np.asarray(df['userToken']))[0]
        assert df['unitToken'].str.contains(unitToken).any(), 'Error: invalid units string.  Acceptable strings include %s' % units_list
        feetFlag = False
        if unitToken in ['FT', 'FEET']:
            # convert to meters and flag
            feetFlag = True
            ugridDict['x'] = 0.3048*ugridDict['x']
            ugridDict['y'] = 0.3048*ugridDict['y']

        # convert to FRF coords.
        if coordToken in ['STATEPLANE', 'NCSP']:
            temp = gp.ncsp2FRF(ugridDict['x'], ugridDict['y'])
            x = temp['xFRF']  # these should be in m
            y = temp['yFRF']  # these should be in m
        elif coordToken == 'UTM':
            temp = gp.utm2ncsp(ugridDict['x'], ugridDict['y'], 18, 'S')
            temp2 = gp.ncsp2FRF(temp['easting'], temp['northing'])
            x = temp2['xFRF']
            y = temp2['yFRF']
        elif coordToken == 'FRF':
            x = ugridDict['x']
            y = ugridDict['y']

    # okay, so I should have everything converted to FRF coordinates and meters.
    # if bathy is None:
    #     # i don't already have an integrated bathy, so now I pull the integrated bathymetry
    #     if forcedSurveyDate is None:
    #         forcedSurveyDate = DT.datetime.strftime(DT.datetime.now(), '%Y-%m-%dT%H:%M:%SZ')
    #     elif isinstance(forcedSurveyDate, DT.datetime):
    #         forcedSurveyDate = DT.datetime.strftime(forcedSurveyDate, '%Y-%m-%dT%H:%M:%SZ')
    #
    #     start_time = DT.datetime.strptime(forcedSurveyDate, '%Y-%m-%dT%H:%M:%SZ')
    #
    #     # pull that bathymetry down.
    #     cmtb_data = getDataTestBed(start_time, start_time + DT.timedelta(days=0, hours=0, minutes=1), THREDDS)
    #     bathy_data = cmtb_data.getBathyIntegratedTransect()
    # else:
    #     # i already have pulled it so there is no reason to get it again
    bathy_data = bathy

    # now interpolate
    gridX = bathy_data['xFRF']
    gridY = bathy_data['yFRF']
    elevation = bathy_data['elevation']
    stime = bathy_data['time']
    xGrid, yGrid = np.meshgrid(gridX, gridY)

    # reshape my DEM into a list of points
    xPts = xGrid.reshape((1, xGrid.shape[0] * xGrid.shape[1]))[0]
    yPts = yGrid.reshape((1, yGrid.shape[0] * yGrid.shape[1]))[0]
    points = (xPts, yPts)
    values = elevation.reshape((1, elevation.shape[0] * elevation.shape[1]))[0]
    # do the interpolation
    newElevation = griddata(points, values, (x, y), method='linear')

    # this elevation is in meters do I need to convert back?
    if feetFlag:
        # convert back to ft
        newElevation = 3.28084 * newElevation

    # put this stuff in my return dict
    out = {'z': newElevation, 'surveyDate': stime}

    return out

def convertGridNodes2ncsp(x0, y0, azi, xPos, yPos):
    """This function is used to convert the cms grid nodes from the CMS convention in the .tel file to NCSP.
    
    you can interpolate our gridded bathymetry onto it.

    Args:
        x0: integer/float describing origin in x (easting)
        y0: integer/float describing origin in y (northing)
        azi: grid azimuth defining rotation of grid
        xPos: 1D np.array that contains the x-distance from the origin from the .tel file
        yPos: 1D np.array that contains the y-distance from the origin from the .tel file

    Returns
            easting: 1D np.array of the NC stateplane easting of the grid nodes
            northing: 1D np.array of the NC stateplane northing of the grid nodes

    """
    # calculating change in alongshore coordinate for northing and easting
    # given the associated dx dy
    E_j = yPos * np.cos(np.deg2rad(azi + 90))
    N_j = yPos * np.sin(np.deg2rad(azi + 90))
    # calculating change in cross-shore coordinate for northing and easting
    E_i = xPos * np.cos(np.deg2rad(azi))
    N_i = xPos * np.sin(np.deg2rad(azi))
    # add em all up.
    easting = x0 + E_j + E_i
    northing = y0 + N_j + N_i

    return easting, northing

def findNearestUnstructNode(xFRF, yFRF, ugridDict):
    """This script will take in the xFRF and yFRF coordinates of an instrument (or any other location of interest)
    and then find the index of the closest node in an unstructured grid.  it also returns the distance between that the
    position handed to the function and the closest grid node.

    Args:
        xFRF: xFRF location (of an instrument or other location of interest)
        yFRF: yFRF location (of an instrument or other location of interest)
        ugridDict: input dictionary
            'xFRF': - xFRF of all the points in the unstructured grid
            'yFRF': - yFRF of all the points in the unstructured grid

    Returns:
        ind:  index in the list of grid points that is closest to the input xFRF and yFRF position
        dist: distance from the unstruct grid point to the xFRF and yFRF position.

    """
    assert 'xFRF' in list(ugridDict.keys()), 'Error: xFRF is a required key in ugridDict'
    assert 'yFRF' in list(ugridDict.keys()), 'Error: yFRF is a required key in ugridDict'

    points = np.column_stack((ugridDict['xFRF'], ugridDict['yFRF']))
    qPt = np.column_stack((xFRF, yFRF))

    # compute nearest neighbor
    kdt = scipy.spatial.cKDTree(points)
    dist, ind = kdt.query(qPt, 1)

    return ind, dist

