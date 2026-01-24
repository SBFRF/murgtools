"""Setup tools for getDataTestBed."""
from setuptools import setup

setup(name='getdatatestbed',
      version='0.9.dev',
      description=('Utilities for retrieving data relevant to the USACE' +
                   'Field Research Facility Coastal Model Test Bed' +
                   '(CMTB)'),
      author='Spicer Bak',
      author_email='spicer.bak@usace.army.mil',
      packages='getdatatestbed',
      modules=['getDataFRF', 'getOutsideData'],

    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
     )