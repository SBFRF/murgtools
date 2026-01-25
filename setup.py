"""Setup tools for murgtools."""
from setuptools import setup, find_packages

setup(
    name='murgtools',
    version='0.9.0',
    description='Utilities for retrieving data from the USACE Field Research Facility Coastal Model Test Bed (CMTB)',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Spicer Bak',
    author_email='spicer.bak@usace.army.mil',
    url='https://github.com/SBFRF/murgtools',
    packages=find_packages(exclude=['tests', 'tests.*']),
    python_requires='>=3.9',
    install_requires=[
        'numpy>=1.20.1',
        'pandas>=1.2.4',
        'netCDF4>=1.5.7',
        'scikit-image>=0.18.1',
        'pyproj>=3.0.0',
        'matplotlib>=3.0.0',
        'scipy>=1.6.0',
        'python-dateutil>=2.8.0',
        'utm>=0.7.0',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'flake8>=5.0.0',
            'pydocstyle>=6.0.0',
        ],
        'test': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
        'Topic :: Scientific/Engineering :: GIS',
    ],
    keywords='oceanography coastal data-retrieval netcdf thredds frf usace',
)
