"""
This is a home brew hack, to explore the thredds server for errors that might cause the ncml to break
"""

import netCDF4 as nc
import numpy as np

def main():
    """ """
    baseURL = 'http://134.164.129.55/thredds/dodsC/FRF/'
    baseURL = 'http://134.164.129.628080/thredds/dodsC/'

    scienceList = ['CMTB']#['oceanography/']
    disciplineList = ['CB_STWAVE_data/', 'CBHP_STWAVE_data/']
            #['waves/']'waterlevel/']

    for science in scienceList:
        for discipline in disciplineList:
            if discipline == 'waves/':
                #gaugeList = ['waverider-26m'] #, 'waverider-17m', 'awac-11m',
                gaugeList = [ 'Local_Field', 'Regional_Field']
                #'awac-8m', '8m-array', 'awac-6m', 'awac-5m', #'awac-4.5m',
                # 'adop-3.5m', 'xp200m', 'xp150m', 'xp125m',]
                # 'DWG-OC03', 'DWG-OC02', 'DWG-BB03', 'DWG-BB02',
                # 'adop-cs01', 'CS05-SBE26', 'CS04-SBE26', 'CS03-SBE26', 'CS02-SBE26', 'CS01-SBE26']
                #gaugeList = ['xp100m', 'xp200m', 'xp150m', 'xp125m']
                # gaugeList = ['8m-array']
                             #'adop-cs01', 'CS05-SBE26', 'CS04-SBE26', 'CS03-SBE26', 'CS02-SBE26', 'CS01-SBE26']
            elif discipline == 'waterlevel/':
                gaugeList = ['11', ]
            elif discipline in disciplineList:
                gaugeList = [ 'Local_Field', 'Regional_F ield']

            for gauge in gaugeList:
                # create the url
                print(gauge)
                callURL = baseURL + science + discipline + gauge + '/' + gauge + '.ncml'
                # open the ncml dataset
                ncfile = nc.Dataset(callURL)
                # now loop through check variables
                for var in list(ncfile.variables.keys()):
                    print('**' + var + '**')
                    print('shape %s' % str(np.shape(ncfile[var])))
                    if np.size(ncfile[var]) == 1:
                        tmp = ncfile[var][:]
                    elif np.size(ncfile[var], axis = 0) >= 100:
                        for ii in np.arange(0, np.shape(ncfile[var])[0], 100):
                            print('approximate time: %s\nfile: %s\nvariable %s' %( nc.num2date(ncfile['time'][ii] ,'seconds since 1970-01-01'), callURL, var))
                            if np.shape(ncfile[var])[0] > ii+100:
                                tmp = ncfile[var][ii:ii+100]
                            else:
                                print('less than 100 left')
                                tmp = ncfile[var][:]
                    elif var=='station_name':
                        print('station_Name %s' % var)


                    elif np.size(ncfile[var], axis=0) < 100:
                        print(ncfile[var][:])

if __name__ == '__main__':
    print(("This only executes when %s is executed rather than imported" % __file__))
