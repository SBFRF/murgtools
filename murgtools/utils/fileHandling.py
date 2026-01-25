import os, logging
import datetime as DT

def makeCMTBfileStructure(path_prefix, date_str):
    """checks and makes sure there is a folder structure that can beused for file storage"""
    if not os.path.exists(os.path.join(path_prefix, date_str)):  # if it doesn't exist
        os.makedirs(os.path.join(path_prefix, date_str))  # make the directory
    if not os.path.exists(os.path.join(path_prefix, date_str, 'figures')):
        os.makedirs(os.path.join(path_prefix, date_str, "figures"))
    print("simulation input/output files and plots will be place in {0} folder".format(os.path.join(path_prefix, date_str)))

def makeTDSfileStructure(Thredds_Base, fldrArch, datestring, field):
    """ makes the thredds folder architecture and returns file name for particular file to be generated

    Args:
        Thredds_Base: the root directory where all TDS files lives
        fldrArch: local architecture from that location
        datestring: names specific simulation file (eg 20190905T000000Z)
        field: what type of file is this, a save point, spatial data, etc

    Returns:
        file name for writing netCDF file (eg '/thredds_data/cmsf/base/field/field20190905T000000Z.nc')
    """
    from prepdata import inputOutput
    TdsFldrBase = os.path.join(Thredds_Base, fldrArch, field)
    netCDFfileOutput = os.path.join(TdsFldrBase, field + '_%s.nc' % datestring)
    if not os.path.exists(TdsFldrBase):
        os.makedirs(TdsFldrBase)  # make the directory for the thredds data output
    if not os.path.exists(os.path.join(TdsFldrBase, field+'.ncml')):
        inputOutput.makencml(os.path.join(TdsFldrBase, field+'.ncml'))  # remake the ncml if its not there

    return netCDFfileOutput

def logFileLogic(outDataBase, version_prefix, startTime, endTime, log=True):
    """Checks and makes log file

    Args:
        outDataBase: string for working directory
        version_prefix: version prefix for model
        startTime: start time of project simulation
        endTime: end time of project simulation
        log(bool): turn logs on or not (default=True)

    Returns:

    """
    LOG_FILENAME =os.path.join(outDataBase, 'logs/cmtb_BatchRun_Log_{}_{}_{}.log'.format(version_prefix, startTime, endTime))
    if log is True:
        try:
            logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)
        except IOError:
            os.makedirs(outDataBase+'logs')
            logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)
        logging.debug('\n-------------------\nTraceback Error Log for:\n\nSimulation Started: %s\n-------------------\n'
                  % (DT.datetime.now()))
    # ____________________________________________________________
    return LOG_FILENAME

def displayStartInfo(projectStart, projectEnd, version_prefix, LOG_FILENAME, model):
    print('\n-\n-\nMASTER WorkFLOW for {} SIMULATIONS\n-\n-\n'.format(model))
    print('Batch Process Start: %s     Finish: %s '% (projectStart, projectEnd))
    print('The batch simulation is Run in %s Version' % version_prefix)
    print('Check for simulation errors here %s' % LOG_FILENAME)
    print('------------------------------------\n\n************************************\n\n------------------------------------\n\n')

def checkVersionPrefix(model, inputDict):
    """ a function to check if model prefix is already programmed into structure, this is to protect from ill
    described downstream errors.  This will also create a combined version prefix for coupled modeling systems of the format
    [waveprevix]_f[flowprefix]_m[morphprefix]
    
    Args:
        model: a model name string
        inputDict (dict):
        version_prefix: version prefix string
        
    Returns:
        version_prefix

    """
    # first check Flow Flags, and morph flags, otherwise set version prefix with just wave

    version_prefix = inputDict['modelSettings'].get('version_prefix', 'base').lower()
    if 'flowSettings' in inputDict.keys():
        flowFlag = inputDict['flowSettings'].get('flowFlag', False)
        morphFlag = inputDict['morphSettings'].get('morphFlag', False)
        if flowFlag:
            version_prefix = version_prefix + '_f' + inputDict['flowSettings'].get('flow_version_prefix', 'base').lower()
        if morphFlag and flowFlag:
            version_prefix = version_prefix + '_m' + inputDict.get('morph_version_prefix', 'base').lower()
    # now do model specific checks
    cmsStrings = ['base', 'base_fbase', 'base_fbase_mbase']
    ww3Strings = ['base']
    stwaveStrings= ['HP', 'FP', 'CB', 'CBKF']
    swashStrings = ['base', 'ts']
    ######### now do model specific Checks
    if model.lower() in ['cms']:
        modelList = cmsStrings
    elif model.lower() in ['ww3']:
        modelList = ww3Strings
    elif model.lower() in ['stwave']:
        modelList = stwaveStrings
    elif model.lower() in ['swash']:
        modelList = swashStrings
    else:
        raise NotImplementedError('Check model is programmed')
    checkString = 'Your model is not in version Prefix list {}'.format(modelList)
    # run assertion check
    assert version_prefix.lower() in modelList, checkString

    return version_prefix