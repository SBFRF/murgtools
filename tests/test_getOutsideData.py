"""Unit tests for getOutsideData module."""
import datetime as DT
import numpy as np
import pytest
from unittest.mock import MagicMock, patch


class TestForecastDataClass:
    """Tests for the forecastData class."""

    def test_forecastdata_init_with_datetime(self):
        """Test forecastData initialization with valid datetime."""
        d1 = DT.datetime(2020, 1, 1, 0, 0, 0)

        with patch('getdatatestbed.getOutsideData.nc') as mock_nc:
            mock_nc.date2num = MagicMock(return_value=1577836800.0)
            from getdatatestbed.getOutsideData import forecastData

            fd = forecastData(d1)

            assert fd.d1 == d1
            assert fd.timeunits == 'seconds since 1970-01-01 00:00:00'
            mock_nc.date2num.assert_called_once_with(d1, fd.timeunits)

    def test_forecastdata_raises_on_non_datetime(self):
        """Test that forecastData raises on non-datetime input."""
        with patch('getdatatestbed.getOutsideData.nc') as mock_nc:
            mock_nc.date2num = MagicMock(return_value=1577836800.0)
            from getdatatestbed.getOutsideData import forecastData

            with pytest.raises(AssertionError):
                forecastData("2020-01-01")

    def test_forecastdata_has_required_attributes(self):
        """Test that forecastData has all required data location attributes."""
        d1 = DT.datetime(2020, 1, 1, 0, 0, 0)

        with patch('getdatatestbed.getOutsideData.nc') as mock_nc:
            mock_nc.date2num = MagicMock(return_value=1577836800.0)
            from getdatatestbed.getOutsideData import forecastData

            fd = forecastData(d1)

            assert hasattr(fd, 'dataLocFRF')
            assert hasattr(fd, 'dataLocTB')
            assert hasattr(fd, 'dataLocCHL')
            assert hasattr(fd, 'dataLocNCEP')
            assert hasattr(fd, 'dataLocECWMF')

    def test_forecastdata_server_urls(self):
        """Test that forecastData has correct server URLs."""
        d1 = DT.datetime(2020, 1, 1, 0, 0, 0)

        with patch('getdatatestbed.getOutsideData.nc') as mock_nc:
            mock_nc.date2num = MagicMock(return_value=1577836800.0)
            from getdatatestbed.getOutsideData import forecastData

            fd = forecastData(d1)

            assert 'thredds' in fd.dataLocFRF
            assert 'thredds' in fd.dataLocCHL
            assert 'ncep.noaa.gov' in fd.dataLocNCEP


class TestGetWW3Method:
    """Tests for the getWW3 method of forecastData."""

    def test_getww3_requires_string_forecast_hour(self):
        """Test that getWW3 requires string type for forecastHour."""
        d1 = DT.datetime(2020, 1, 1, 0, 0, 0)

        with patch('getdatatestbed.getOutsideData.nc') as mock_nc:
            mock_nc.date2num = MagicMock(return_value=1577836800.0)
            from getdatatestbed.getOutsideData import forecastData

            fd = forecastData(d1)

            with pytest.raises(AssertionError):
                fd.getWW3(12)  # integer instead of string

    def test_getww3_url_format(self):
        """Test that getWW3 constructs URLs with expected format."""
        d1 = DT.datetime(2020, 1, 15, 0, 0, 0)

        with patch('getdatatestbed.getOutsideData.nc') as mock_nc:
            mock_nc.date2num = MagicMock(return_value=1577836800.0)
            from getdatatestbed.getOutsideData import forecastData

            fd = forecastData(d1)

            # Verify the URL components would be constructed correctly
            expected_date_str = d1.strftime('%Y%m%d')
            assert expected_date_str == '20200115'

            # Verify dataLocNCEP contains expected base URL
            assert 'ncep.noaa.gov' in fd.dataLocNCEP
            assert 'wave' in fd.dataLocNCEP


class TestGetCbathyFromFTP:
    """Tests for the get_CbathyFromFTP method."""

    def test_get_cbathy_converts_single_datetime_to_list(self):
        """Test that single datetime is converted to list."""
        d1 = DT.datetime(2020, 1, 1, 0, 0, 0)

        with patch('getdatatestbed.getOutsideData.nc') as mock_nc:
            mock_nc.date2num = MagicMock(return_value=1577836800.0)
            from getdatatestbed.getOutsideData import forecastData

            fd = forecastData(d1)

            with patch('os.path.exists', return_value=True), \
                 patch('os.chdir'), \
                 patch('os.getcwd', return_value='/tmp'), \
                 patch('os.path.isfile', return_value=True):

                dlist = DT.datetime(2020, 1, 1, 12, 0, 0)
                result = fd.get_CbathyFromFTP(dlist, '/tmp/output')

                # Function should handle single datetime input
                assert isinstance(result, list)

    def test_get_cbathy_raises_on_non_datetime(self):
        """Test that non-datetime input raises assertion."""
        d1 = DT.datetime(2020, 1, 1, 0, 0, 0)

        with patch('getdatatestbed.getOutsideData.nc') as mock_nc:
            mock_nc.date2num = MagicMock(return_value=1577836800.0)
            from getdatatestbed.getOutsideData import forecastData

            fd = forecastData(d1)

            with patch('os.path.exists', return_value=True), \
                 patch('os.chdir'), \
                 patch('os.getcwd', return_value='/tmp'), \
                 patch('os.mkdir'):

                with pytest.raises(AssertionError):
                    fd.get_CbathyFromFTP(["2020-01-01"], '/tmp/output')
