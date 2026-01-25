# -*- coding: utf-8 -*-
"""
Author: spicer bak
Contact: spicer.bak@usace.army.mil
Association: USACE CHL Field Research Facility

A base level utility function library that don't fit into specific other places

documented 12/2/17
"""
import numpy as np
import datetime as DT
import netCDF4 as nc
import math, warnings, os
from dateutil.relativedelta import relativedelta

########################################
#  following functions deal with general things
########################################
def oMagnitude(x):
    """Calculates the order of magnitude of a number, works only on single value not array or lists

    Args:
        x (float):  float - single

    Returns:
        integer of order of magnitude

    Examples:
        oMagnitude(99.23)
            1
        oMagnitude(9432)
            3
        oMagnitude(.002)
            -3
    """
    if x is not 0:
        return int(math.floor(math.log10(x)))
    else:
        return 0

def reduceDict(dictIn, idxToKeep, exemptList=None):
    """This function will take a dictionary and  reduce it by given indicies, making a COPY of the array
    it assumes that all things of multidimensions have time in the first dimension
    
    WARNING: This could potentially be dangerous as it works by checking each key to see if its the length of the
        variable dictIn['time'].  If it is then it will reduce the variable to keep the idxToKeep.  If not it will
        skip the key
    
    This function is useful if trying to reduce a dictionary to specific indicies of interest eg with a time matched index
    Improvement to be safer is welcome, or use with caution.

    Args:
      dictIn: dictionary with no limit to how many keys assumes one key is 'time'
      idxToKeep: indices to reduce to, must be shorter than key 'time'
      exemptList: this is a list of variables to exclude
    default values are 'time', 'name', 'xFRF', 'yFRF'

    Returns:
      a dictionary with the same keys that were input
      all keys that came in with the same length as 'time' have been reduced to use the indices of idxToKeep

    """
    assert 'time' in dictIn, 'This function must have a variable "time"'
    if np.size(idxToKeep) == 0:
        return None
    if exemptList == None:
        exemptList = ['time', 'name', 'xFRF', 'yFRF', 'xm', 'ym']
    idxToKeep = np.array(idxToKeep, dtype=int) # force data to integer type
    dictOut = dictIn.copy()
    for key in dictIn:
        # if things are longer than the indices of interest and not 'time'
        # print 'key %s size %d' %(key, np.size(dictIn[key], axis=0))
        try:
            if key not in exemptList and dictIn[key].dtype.kind not in ['U', 'S'] and np.size(dictIn[key], axis=0) == np.size(dictIn['time']):
                # then reduce
                dictOut[key] = dictIn[key][idxToKeep]  # reduce variable
                #
        except (IndexError, AttributeError):
            pass  # this passes for single number (not arrays), and attribute error passes for single datetime objects
    if np.size(dictIn['time']) == 1 and np.size(idxToKeep) == 1:
        dictOut['time'] == dictIn['time']
    else:
        dictOut['time'] = dictIn['time'][idxToKeep]  # # once the rest are done finally reduce 'time'
    return dictOut

def removeMaskedDataFromDictionary(dictIn):
    """ removes masked data from dictionary
    in development

    """
    warnings.warn('check that this is ready for use')
    if isinstance(dictIn, np.ma.MaskedArray):   # then operate on it
        # first loop through find everything that has same dimension
        dictOut = {}
        for key, value in dictIn.items():
            if isinstance(value, np.ndarray):
                shapes = np.array([x.shape for x in dictIn.values()])
                maxDimension = shapes.max()


                # if wBinObsLocal[key].mask.any():  # if the masks are true
                #     print('    Found Masked data in observations... Removing')
                #     # last remove from where found
                #     for key2 in wBinObsLocal.keys():
                #         if key is not 'time' and key2 in set(wBinObsLocal.keys()).intersection(
                #                 wBinHP):  # ['name', 'wavefreqbin', 'xFRF', 'yFRF', 'lat', 'lon', 'depth', 'wavedirbin', 'qcFlagE', 'qcFlagD', 'a1', 'b1', 'a2', 'b2']:
                #             try:  # to do it for multidimensions eg dWED
                #                 wBinObsLocal[key2] = np.array(
                #                     wBinObsLocal[key2][~wBinObsLocal[key].mask.any(axis=(1, 2))])
                #             except(np.core._internal.AxisError):
                #                 wBinObsLocal[key2] = np.array(wBinObsLocal[key2][~wBinObsLocal[key].mask.any()])
                #     # then remove time from wBinObsLocal
                #     # wBinObsLocal['time'] = wBinObsLocal['time'][~wBinObsLocal[key].mask.any(axis=(1, 2))]
                # wBinObsLocal[key] = np.array(wBinObsLocal[key])
                #

        return dictOut
    else:
        return dictIn

class Bunch(object):
    """allows user to access dictionary data from 'object'
    instead of object['key']
    do x = sblib.Bunch(object)
    x.key
    
    do x = Bunch(object)
    x.key

    Args:
      object: input dictionary
    :return class: with objects being the same as the keys from dictionary

    Returns:
        class

    """

    def __init__(self, aDict):
        self.__dict__.update(aDict)

def makeNCdir(netCDFdir, version_prefix, date_str, model):
    """All this function is going to do is take in some info from CSHORE analysis,
    return the appropriate filepath where the netcdf file is to be saved, and make sure that folder exists

    Args:
      netCDFdir: parent directory for the netCDF files to be saved
      version_prefix: what version of the model are you running
      date_str: this is the date string that tells this thing what month/year it is.
            it doesn't matter if you hand it the file savename (WITHOUT the COLONS) or the input datestring
            (WITH THE COLONS) because it only looks at the first 7 characters, which are the same either way
      model: this is the name of the model you are running -> this is in here because some
            of the models have the same version prefixes

    Returns:
      path (str)

    """
    import os
    # parse my date string
    year = date_str[0:4]

    mList = ['01-Jan', '02-Feb', '03-March', '04-Apr', '05-May', '06-Jun', '07-Jul', '08-Aug', '09-Sep', '10-Oct',
             '11-Nov', '12-Dec']
    month = mList[int(date_str[5:7]) - 1]

    NCpath = os.path.join(netCDFdir, model, version_prefix, year, month)

    if not os.path.exists(NCpath):  # if it doesn't exist
        os.makedirs(NCpath)  # make the directory

    return NCpath

def statsBryant(observations, models):
    """This function does Non-Directional Statsistics
    These statistics are from the Bryant Wave stats CHETN - I - 91

    Args:
      observations: array of observational data
      models: array of model data

    Returns:
      dictiornay with statistics calculated
            'bias' average of residuals

            'RMSEdemeaned': RMSEdemeaned,

            'RMSE': R oot mean square error

            'RMSEnorm': normalized root Mean square error also Percent RMSE

            'scatterIndex': ScatterIndex

            'symSlope': symetrical slope

            'corr': r

            'r2': coefficient of determination (corr squared)

            'PscoreWilmont': performance score developed by Wilmont

            'PscoreIMEDS':  see Hanson 2007 for description

            'residuals': model - observations

    """

    # convert masked values to nans! # this way you can use
    # the logic for nans and you won't hit the issues with masked arrays..
    observations = np.ma.filled(observations, np.nan)
    models = np.ma.filled(models, np.nan)

    obsNaNs = np.argwhere(np.isnan(observations)).squeeze()
    modNaNs = np.argwhere(np.isnan(models)).squeeze()
    if isinstance(observations, np.ma.masked_array) or isinstance(models, np.ma.masked_array):
        raise NotImplementedError('this handles masked arrays poorly, fix or remove before use')
    if np.size(obsNaNs) > 0:
        warnings.warn('warning found nans in bryant stats, removing compared data')
        observations = np.delete(observations, obsNaNs)
        models = np.delete(models, obsNaNs)  # removing corresponding model data, that cannot be compared
        modNaNs = np.argwhere(np.isnan(models))
        if np.size(modNaNs) > 0:
            observations = np.delete(observations, modNaNs)
            models = np.delete(models, modNaNs)  # removing c
    elif np.size(modNaNs) > 0:
        warnings.warn('warning found nans in bryant stats, removing compared data')
        models = np.delete(models, modNaNs)
        observations = np.delete(observations, modNaNs, 0)
        obsNaNs = np.argwhere(np.isnan(observations))
        if np.size(obsNaNs) > 0:
            observations = np.delete(observations, obsNaNs)
            models = np.delete(models, obsNaNs)  # removing cor
    assert np.size(observations) == np.size(models), 'these data must be the same length'

    residuals = models - observations
    bias = np.nansum(residuals) / len(residuals)

    ## RMSE's
    # demeaned RMSE
    RMSEdemeaned = np.sqrt(np.sum((residuals - bias) ** 2) / (len(observations) - 1))
    # regular RMSE
    RMSE = np.sqrt(np.sum(residuals ** 2) / len(observations))
    # normalized RMSE or percentage
    RMSEnorm = np.sqrt(np.sum(residuals ** 2) / np.sum(observations ** 2))
    # scatter index - a normalize measure of error often times presented as %
    ScatterIndex = RMSE / np.mean(observations)
    # symetric Slope
    symr = np.sqrt((models ** 2).sum() / (observations ** 2).sum())
    # coefficient of determination
    r = np.sum((observations - observations.mean()) * (models - models.mean())) \
        / (np.sqrt(((observations - observations.mean()) ** 2).sum()) *
           np.sqrt(((models - models.mean()) ** 2).sum()))
    r2 = r ** 2  # square to get r2
    # SSres = (residuals ** 2).sum()  ## from wiki
    # SStot = ((observations - observations.mean()) ** 2).sum()
    # r2 = 1 - SSres/SStot
    # wilmont 1985
    topW = np.abs(models - observations).sum()
    botW = np.sum(np.abs(models - observations.mean()) + np.abs(observations - observations.mean()))
    Wilmont = 1 - topW / botW

    xRMS = np.sqrt((observations ** 2).sum() / len(observations))
    pRMS = 1 - (RMSE / xRMS)
    pBias = 1 - np.abs(bias) / xRMS
    IMEDS = (pRMS + pBias) / 2
    stats = {'bias': bias,
             'RMSEdemeaned': RMSEdemeaned,
             'RMSE': RMSE,
             'RMSEnorm': RMSEnorm,
             'scatterIndex': ScatterIndex,
             'symSlope': symr,
             'corr': r,
             'r2': r2,
             'PscoreWilmont': Wilmont,
             'PscoreIMEDS': IMEDS,
             'residuals': residuals,
             'meta': 'please see Bryant, et al.(2016). Evaluation Statistics computed for the WIS ERDC/CHL CHETN-I-91'}

    return stats

def makeMovie(ofname, images, fps=5):
    """make movies from list of images
    
    Args:
        ofname:  output file name
        images: list of images

    Returns:
        None, will make a movie in types

    needs openCV, can install with pip install opencv-python

    Refrences:
        https://stackoverflow.com/questions/30509573/writing-an-mp4-video-using-python-opencv

    """
    import cv2
    video_name = ofname
    if ofname.split('.')[-1].lower() in ['mp4']:
        forcc = cv2.VideoWriter_fourcc(*'mp4v')
    else:
        forcc = 0
    frame = cv2.imread(images[0])
    height, width, layers = frame.shape
    video = cv2.VideoWriter(video_name, forcc, fps, (width, height))
    for image in images:
        video.write(cv2.imread(image))
    cv2.destroyAllWindows()
    video.release()

def makegif(flist, ofname, size=None, dt=0.5):
    """This function uses imageio to create gifs from a list of images
        requires imageio library

    References:
        http://imageio.readthedocs.org/en/latest/format_gif.html#gif

    Args:
      flist: a sorted list of files to be made into gifs (including path)
      ofname: output gif filename (including path)
      size: size of pictures (default not resized)
      loop: number of loops to do, 0 is default and infinite
      dt: Default value = 0.5)

    Returns:
      will write a gif to ofname location

    """
    # images = [Image.open(fn) for fn in flist]
    #
    # for im in images:
    #     im.thumbnail(size, Image.ANTIALIAS)
    # images2gif.writeGif(ofname, images, duration=dt, nq=15)
    import imageio
    images = []
    if size != None:
        for im in images:
            im.thumbnail(size, Image.ANTIALIAS)
    for filename in flist:
        images.append(imageio.imread(filename))
    imageio.mimwrite(ofname, images, duration=dt)

def myTarMaker(tarOutFile, fileList, **kwargs):
    """ makes a tarball file with a file name and list of files

    Args:
        tarOutFile (str): file output name/location
        fileList (list): list of files to put into tarbball

    Keyword Args:
          'compressionString': denotes type of compression to write with (default='w:gz', write with gzip)
          'removeFiles' (bool): Denotes whether to remove files or not after taring

    Returns:
        a tarball written to tarOutFile location

    """
    import tarfile
    compressionString = kwargs.get('compressionString',  "w:gz")
    removeFiles = kwargs.get('removeFiles', True)
    with tarfile.open(tarOutFile, compressionString) as tar:
        for fileName in fileList:
            tar.add(fileName, arcname=os.path.split(fileName)[-1])

    if removeFiles:
        [os.remove(ff) for ff in fileList]

########################################
#  following functions deal with averaging
########################################

def baseRound(x, base=5, **kwargs):
    """This function will round any value to a multiple of the base,

    Args:
      x: values to be rounded:
      base: this is the value by which x is rounded to a multiple of
    ie base = 10  x = [4, 8, 2, 12]  returns [0,10,0,10] (Default value = 5)

    Keyword Args:
        'floor': will force a round down
        'ceil': will force a  round up

    Returns:
      np.array of floating point numbers rounded to a multiple of base

    """
    x = np.array(x, dtype=float)
    floor=kwargs.get('floor', False)
    ceil = kwargs.get('ceil', False)
    if floor is True:
        return base * np.floor(x/base)
    elif ceil is True:
        return base * np.ceil(x/base)
    else:
        return base * np.round(x/base)

def weightedAvg(toBeAveraged, weights, avgAxis=0, inverseWeight=False):
    """This function does a weighted average on a multidimensional array

    Args:
      toBeAveraged: values to be averaged (array)
      weights: values to be used as weights (does not have to be normalized)
      avgAxis: axis over which to average (Default value = 0)
      inverseWeight: if true will invert the weights, high values weighted higher with marked FALSE
    to weight high values lower, inverseWeight must be True (Default value = False)

    Returns:
      an array of weighted average

    """
    if inverseWeight == True:
        weights = 1/weights
    assert toBeAveraged.shape == weights.shape, 'data and weights need to be the same shapes to be averaged'
    averagedData = np.sum(weights * toBeAveraged, axis=avgAxis) / (weights).sum(axis=avgAxis)
    return averagedData

def running_mean(data, window):
    """found running mean function on the internet, untested

    Args:
      data: data to run mean
      window: window over which to take mean

    Returns:
      meaned data

    """
    cumsum = np.cumsum(np.insert(data, 0, 0))
    return (cumsum[window:] - cumsum[:-window]) / window

########################################
#  following functions deal with time
########################################
def mtime2epoch(timeIn):
    """Function will convert matlab time to epoch time

    Args:
      timeIn: array of time in

    Returns:
      epoch times out

    """
    Start = 719529  # 1970-01-01 in days since 0000-01-01
    return (timeIn - Start) * 24 * 60 * 60

def roundtime(timeIn=None, roundTo=60):
    """"
    Round a datetime object to any time lapse in seconds
    Author: Thierry Husson 2012 - Use it as you want but don't blame me.

    modified by SB to include lists of datetime dataList, returned as a list if it came in as
        a list, if it came in as a datetime object it is returned as such


    Args:
      timeIn: datetime.datetime object, default now.
      roundTo: Closest number of seconds to round to, (Default 1 minute).
    
    Returns:
        rounded datetime objects rounded to 'round to value'

    """
    # making dt a list
    warnings.warn('This Function is SLOW!')
    if np.size(timeIn) > 1:
        dtlist = timeIn
    elif np.size(timeIn) == 1:
        if type(timeIn) == np.ndarray and timeIn.shape == (1,):
            dtlist = timeIn.tolist()
        else:
            dtlist = [timeIn]
    elif np.size(timeIn) == None:
        dtlist = [DT.datetime.now()]
        # checking to make datetime
        # if type(dt[0] != DT.datetime):
        # trying to convert epoch time to datetime object  if need be but doen'st solve problem currently working on

    # looping through list
    for ii, dt in enumerate(dtlist):
        seconds = (dt - dt.min).seconds
        # // is a floor division, not a comment on following line:
        rounding = (seconds + roundTo / 2) // roundTo * roundTo
        dtlist[ii] = dt + DT.timedelta(0, rounding - seconds, -dt.microsecond)
    # return data as it came in
    if len(dtlist) == 1:
        if type(timeIn) == np.ndarray:
            dtlist = np.array(dtlist)  # if it came in as an array, return it as an array
        else:
            dtlist = dtlist[0]  # if it came in as a single element, return it as such
    return dtlist

def createDateList(start, end, delta):
    """creates a generator of dates

    Args:
      start: date to start (date time object ... I think)
      end: date to end (datetime object .. I think)
      delta: 

    Returns:
        generator
    """
    curr = start
    while curr <= end:
        yield curr
        curr += delta

def whatIsYesterday(now=DT.date.today(), stringOut=False, days=1):
    """this function finds what yesterday's date string is in the format
    of yyyy-mm-dd

    Args:
        now: the date to start counting backwards from (default = right now)
        stringOut (bool): a format to convert the string as output (default=False returns datetime)
        days (int): how many days to count backwards from (Default = 1)

    Returns:
        the date of yesterday ( "days" previous to input 'now')
        Default value = DT.date.today()

    """

    yesterday = now - DT.timedelta(days)
    if stringOut is not False:
        yesterday = DT.date.strftime(yesterday, stringOut)
    return yesterday

def timeMatch(obs_time, obs_data, model_time, model_data):
    """This is the time match function from the IMEDs lite version created by ASA
    This has been removed from the IMEDS package to simplify use.
    This method returns the matching model data to the closest obs point.
    

    similar to time match imeds
    
    Time Matching is done by creating a threshold by taking the median of the difference of each time
       then taking the minimum of the difference between the two input times divided by 2.
       a small, arbitrary (as far as I know) factor is then subtracted from that minimum to remove the possiblity
       of matching a time that is exactly half of the sampling interval.

    TODO: This could be improved in speed, long lists take a while. see references below for ideas

    Args:
      obs_time: observation times, in
      obs_data: matching observation data, any shape, can be None: will create indicies corresponding to obs_time
      model_time: modeling time
      model_data: modeling data (any shape) can be None: will create indicies corresponding to obs_time

    Returns:
      time, (as float)
      obs_data_s: data as input
      model_data_s: data as input

    Refrences:
        https://stackoverflow.com/questions/1388818/how-can-i-compare-two-lists-in-python-and-return-matches
        https://stackoverflow.com/questions/10367020/compare-two-lists-in-python-and-return-indices-of-matched-values
        https://stackoverflow.com/questions/16685384/finding-the-indices-of-matching-elements-in-list-in-python
    """

    if obs_data is None:
        obs_data = np.arange(len(obs_time), dtype=int)
    if model_data is None:
        model_data = np.arange(len(model_time), dtype=int)


    dt_check = False
    try:  # try to convert from datetime units (if fails, assume it's already numeric)
        timeunits = 'seconds since 1970-01-01 00:00:00'
        obs_time_n = nc.date2num(obs_time, timeunits)
        del obs_time
        obs_time = obs_time_n
        del obs_time_n
        dt_check = True
    except:
        pass
    try:  # try to convert from datetime units (if fails, assume it's already numeric)
        timeunits = 'seconds since 1970-01-01 00:00:00'
        model_time_n = nc.date2num(model_time, timeunits)
        del model_time
        model_time = model_time_n
        del model_time_n
        dt_check = True
    except:
        pass

    assert type(obs_time[0]) != DT.datetime, 'time in must be numeric, try epoch!'
    assert type(model_time[0]) != DT.datetime, 'time in must be numeric, try epoch!'

    time, obs_data_s, model_data_s = [], [], []  # working as lists (faster than numpy append)
    # 43 seconds here makes it 43 seconds less than 1/2 of smallest increment
    threshold = min(np.median(np.diff(obs_time)) / 2.0 - 43,
                    np.median(np.diff(model_time)) / 2.0 - 43)

    # Loop through model records
    for data, record in zip(model_data, model_time):
        in1 = np.where(obs_time <= record)[0]
        in2 = np.where(obs_time >= record)[0]

        if in1.size == 0 or in2.size == 0:
            continue

        if in1[-1] == in2[0]:  # Times match up
            indx = in2[0]
        else:
            d1 = record - obs_time[in1[-1]]
            d2 = obs_time[in2[0]] - record
            if min(d1, d2) > threshold:
                continue
            elif (d1 <= d2):
                indx = in1[-1]
            elif (d2 < d1):
                indx = in2[0]

        if (np.isnan(obs_data[indx]).all() or np.isnan(data).all()):
            continue

        time.append(record)  # (faster than numpy append)
        obs_data_s.append(obs_data[indx])
        model_data_s.append(data)

    # if I was handed a datetime, convert back to datetime
    if dt_check and len(time) > 0:
        timeunits = 'seconds since 1970-01-01 00:00:00'
        calendar = 'gregorian'
        time_n = nc.num2date(time, timeunits, calendar)
        del time
        time = time_n
        del time_n

    return np.array(time), np.array(obs_data_s), np.array(model_data_s)

def timeMatch_altimeter(altTime, altData, modTime, modData, window=30 * 60):
    """this function will loop though variable modTim and find the closest value
    then look to see if it's within a window (default, 30 minutes)
    
    Notes:
        this might be slower than imeds time match or time match, which is based on the imeds time match

    Args:
        altTime: altimeter time - tested as epoch (might work in datetime)
        altData: altimeter data, some/any floating (int?) value
        modTime: base time to match
        modData: data to be paired (could be indices)
        window: time in seconds (or time delta, if input as datetimes) (Default value = 30 * 60)

    Returns:
      timeout: matched time in same format put in
      dataout: time matched altimeter data from variable altData
      modout: time matched model data

    """

    # try to convert it from datetime to epochtime
    # this will fail if it already is in epochtime, so it wont do anything.
    dt_check = False
    try:
        timeunits = 'seconds since 1970-01-01 00:00:00'
        altTime_n = nc.date2num(altTime, timeunits)
        del altTime
        altTime = altTime_n
        del altTime_n
    except:
        pass
    try:
        timeunits = 'seconds since 1970-01-01 00:00:00'
        modTime_n = nc.date2num(modTime, timeunits)
        del modTime
        modTime = modTime_n
        del modTime_n
        dt_check = True
    except:
        pass

    assert type(altTime[0]) != DT.datetime, 'time in must be numeric, try epoch!'
    assert type(modTime[0]) != DT.datetime, 'time in must be numeric, try epoch!'

    dataout, timeout, modout = [], [], []
    if type(altData) == np.ma.MaskedArray:
        altTime = altTime[~altData.mask]
        altData = altData[~altData.mask]
    assert len(altData) == len(altTime), 'Altimeter time and data length must be the same'
    assert len(modTime) == len(modData), 'Model time and data length must be the same'
    for tt, time in enumerate(modTime):
        idx = np.argmin(np.abs(altTime - time))
        if altTime[idx] - time < window:
            # now append data
            dataout.append(altData[idx])
            timeout.append(modTime[tt])
            modout.append(modData[tt])

    # if I was handed a datetime, convert back to datetime
    if dt_check:
        timeunits = 'seconds since 1970-01-01 00:00:00'
        calendar = 'gregorian'
        timeout_n = nc.num2date(timeout, timeunits, calendar)
        del timeout
        timeout = timeout_n
        del timeout_n

    return np.array(timeout), np.array(dataout), np.array(modout)

def date_range(start, end, intv=None):
    """
    This is a date range function similar to "createDateList".  It will do date ranges that are monthly and yearly
    taking into account the variable number of days in the month and leap years etc...
    We may want this to eventually replace createDateList?
    :param start: string of the start date in format 20170101
    :param end:  string of the end date in format 20180206
    :param intv: what do you want the interval to be?
    :return: a list of datetimes on the interval you specify
    """

    if intv is None:
        intv = 'day'
    atBins = ['day', 'week', 'month', 'year']
    assert intv in atBins, 'Error: allowable intervals are day, week, month, or year.'

    start = DT.datetime.strptime(start, "%Y%m%d")
    end = DT.datetime.strptime(end, "%Y%m%d")

    date_list = [start]
    cnt = 1
    while date_list[-1] < end:
        if intv is 'day':
            date_list.append(start + DT.datetime.timedelta(days=1 * cnt))
        elif intv is 'week':
            date_list.append(start + DT.datetime.timedelta(days=7 * cnt))
        elif intv is 'month':
            date_list.append(start + relativedelta(months=+1 * cnt))
        elif intv is 'year':
            date_list.append(start + relativedelta(years=+1 * cnt))

        cnt = cnt + 1

    return date_list

########################################
#  following functions deal with finding things
########################################
def dist(x1, y1, x2, y2, x0, y0):
    """This function computes the perpendicular distance between a line connecting points p1 (x1, y1) and p2 (x2, y2)
    and a third point (x0, y0)

    Args:
      x1: x-coord of first line end point
      y1: y-coord of first line end point
      x2: x-coord of second line end point
      y2: y-coord of second line end point
      x0: x-coord of comparison point
      y0: y-coord of comparison point

    Returns:
        distance of point

    """

    dist = np.abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1) / float(
        math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2))

    return dist

def findbtw(data, lwth, upth, type=0):
    """This function finds both values and indicies of a list values between two values
    :TODO: probably could be improved by using boolean compares

    Args:
      upth: upper level threshold
      lwth: lower level threshold
      data: list (or numpy array?)
      type: 0 = non inclusive  ie. lwth < list <  upth

            1 = low incluisve  ie. lwth <=list <  upth

            2 = high inclusive ie. lwth < list <= upth

            3 = all inclusive  ie  lwth <=list <= upth

    Returns:
        indicies returns idices that meet established criteria
        values   returns associated values from da (Default value = 0)
    """
    indices = []
    vals = []
    shp = np.shape(data)
    if len(shp) == 2:
        for i, in enumerate(data):
            for j, elem in enumerate(range):
                if type == 0:
                    if elem < upth and elem > lwth:
                        indices.append((i, j))
                        vals.append(elem)
                elif type == 1:
                    if elem < upth and elem >= lwth:
                        indices.append((i, j))
                        vals.append(elem)
                elif type == 2:
                    if elem <= upth and elem > lwth:
                        indices.append((i, j))
                        vals.append(elem)
                elif type == 3:
                    if elem <= upth and elem >= lwth:
                        indices.append((i, j))
                        vals.append(elem)
    if len(shp) == 1:
        for j, elem in enumerate(data):
            if type == 0:
                if elem < upth and elem > lwth:
                    indices.append((j))
                    vals.append(elem)
            elif type == 1:
                if elem < upth and elem >= lwth:
                    indices.append((j))
                    vals.append(elem)
            elif type == 2:
                if elem <= upth and elem > lwth:
                    indices.append((j))
                    vals.append(elem)
            elif type == 3:
                if elem <= upth and elem >= lwth:
                    indices.append((j))
                    vals.append(elem)

    return indices, vals

def find_nearest(array, value):
    """Function looks for value in array and returns the closest array value
    (to 'value') and index of that value

    Args:
      array: array to to find things in
      value: value to search against

    Returns:
        a number from the array value, that is closest to value input

    """
    idx = (np.abs(array - value)).argmin()
    return array[idx], idx

def findUniqueFromTuple(a, axis=1):
    """This function finds the unique values of a multi dimensional tuple (quickly)

    Args:
      a: an array of multidimensional size
      axis: this is the axis that it looks for unique values using (default is horizontal)

    Returns:
      array of unique tuples
      warning, values are not sorted

    """

    if axis == 0:
        a = a.T

    b = np.ascontiguousarray(a).view(np.dtype((np.void, a.dtype.itemsize * a.shape[1])))
    _, idx = np.unique(b, return_index=True)

    unique_a = a[idx]
    return unique_a

########################################
#  following functions deal with depricated functions 4/20/18
########################################

def FRFcoord(p1, p2):
    """place older

    Args:
      p1: 
      p2: 

    Returns:

    """
    raise ImportError('please use the function in sblib.geoprocess')

def waveStat(spec, dirbins, frqbins, lowFreq=0.05, highFreq=0.5):
    """this function will calculate the mean direction from a full spectrum
        Function is depricated

    Args:
      spec: param dirbins:
      frqbins: param lowFreq:  (Default value = 0.05)
      highFreq: Default value = 0.5)
      dirbins: 
      lowFreq:  (Default value = 0.05)

    Returns:
      Code Translated by Spicer Bak from: fd2BulkStats.m written by Kent Hathaway

    """
    raise NotImplementedError('This function is depricated, The development should be moved to sb.waveLib version!!!!')


