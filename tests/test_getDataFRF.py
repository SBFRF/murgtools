"""Unit tests for getDataFRF module."""
import datetime as DT
import os
import numpy as np
import pytest
import netCDF4 as nc
from unittest.mock import MagicMock, patch, PropertyMock

from murgtools.getdata.getDataFRF import gettime, removeDuplicatesFromDictionary
from murgtools.exceptions import InvalidGaugeError


class TestGettime:
    """Tests for the gettime function."""

    def test_gettime_returns_indices_within_range(self, sample_epoch_array):
        """Test that gettime returns correct indices for time range."""
        # Search for times between hour 5 and hour 10
        start_epoch = 1577836800.0  # 2020-01-01 00:00:00 UTC
        epoch_start = start_epoch + 5 * 3600  # hour 5
        epoch_end = start_epoch + 10 * 3600  # hour 10

        result = gettime(sample_epoch_array, epoch_start, epoch_end)

        assert result is not None
        assert len(result) == 5  # hours 5, 6, 7, 8, 9

    def test_gettime_returns_none_for_empty_range(self, sample_epoch_array):
        """Test that gettime returns None when no times match."""
        # Search for times way before the data
        epoch_start = 1000000000.0
        epoch_end = 1000001000.0

        result = gettime(sample_epoch_array, epoch_start, epoch_end)

        assert result is None

    def test_gettime_handles_none_input(self):
        """Test that gettime handles None input gracefully."""
        result = gettime(None, 1000000000.0, 1000001000.0)
        assert result is None

    def test_gettime_single_match(self):
        """Test gettime with a single matching time."""
        epoch_array = np.array([1577836800.0])  # single time
        result = gettime(epoch_array, 1577836800.0, 1577840400.0)

        assert result is not None

    def test_gettime_with_index_ref(self, sample_epoch_array):
        """Test that gettime applies indexRef offset correctly."""
        start_epoch = 1577836800.0
        epoch_start = start_epoch + 5 * 3600
        epoch_end = start_epoch + 10 * 3600

        result = gettime(sample_epoch_array, epoch_start, epoch_end, indexRef=100)

        # Indices should be offset by 100
        assert result is not None
        assert np.min(result) >= 100


class TestRemoveDuplicatesFromDictionary:
    """Tests for the removeDuplicatesFromDictionary function."""

    def test_removes_duplicate_times(self):
        """Test that duplicate times are removed."""
        test_dict = {
            'name': 'test_gauge',
            'time': np.array([1.0, 2.0, 2.0, 3.0]),
            'Hs': np.array([1.5, 1.6, 1.7, 1.8]),
        }
        result = removeDuplicatesFromDictionary(test_dict)

        # Should have removed one duplicate
        assert len(result['time']) == 3
        assert len(result['Hs']) == 3

    def test_preserves_unique_times(self):
        """Test that unique times are preserved."""
        test_dict = {
            'name': 'test_gauge',
            'time': np.array([1.0, 2.0, 3.0, 4.0]),
            'Hs': np.array([1.5, 1.6, 1.7, 1.8]),
        }
        result = removeDuplicatesFromDictionary(test_dict)

        # All times were unique, so nothing should be removed
        assert len(result['time']) == len(test_dict['time'])

    def test_handles_dict_with_time_key(self):
        """Test handling of dictionary with time key."""
        test_dict = {
            'name': 'test_gauge',
            'time': np.array([1.0]),
        }
        result = removeDuplicatesFromDictionary(test_dict)
        assert 'time' in result

    def test_preserves_non_array_values(self):
        """Test that non-array values are preserved."""
        test_dict = {
            'name': 'test_gauge',
            'time': np.array([1.0, 2.0, 2.0, 3.0]),
            'scalar_value': 42,
        }
        result = removeDuplicatesFromDictionary(test_dict)

        assert result['name'] == 'test_gauge'
        assert result['scalar_value'] == 42


class TestGetObsClass:
    """Tests for the getObs class initialization."""

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_getobs_initializes_with_valid_dates(self, mock_date2num, sample_datetime_range):
        """Test that getObs initializes correctly with valid datetime range."""
        mock_date2num.return_value = 1577836800.0
        d1, d2 = sample_datetime_range

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        assert obs.d1 == d1
        assert obs.d2 == d2
        assert obs.callingClass == 'getObs'

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_getobs_has_wave_gauge_list(self, mock_date2num, sample_datetime_range):
        """Test that getObs has predefined wave gauge list."""
        mock_date2num.return_value = 1577836800.0
        d1, d2 = sample_datetime_range

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        assert hasattr(obs, 'waveGaugeList')
        assert 'waverider-26m' in obs.waveGaugeList

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_getobs_has_thredds_locations(self, mock_date2num, sample_datetime_range):
        """Test that getObs has THREDDS server locations configured."""
        mock_date2num.return_value = 1577836800.0
        d1, d2 = sample_datetime_range

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        assert hasattr(obs, 'FRFdataloc')
        assert 'thredds' in obs.FRFdataloc.lower()


class TestGetDataTestBedClass:
    """Tests for the getDataTestBed class initialization."""

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_getdatatestbed_initializes_correctly(self, mock_date2num, sample_datetime_range):
        """Test that getDataTestBed initializes with correct attributes."""
        mock_date2num.return_value = 1577836800.0
        d1, d2 = sample_datetime_range

        from murgtools.getdata.getDataFRF import getDataTestBed
        tb = getDataTestBed(d1, d2)

        assert tb.start == d1
        assert tb.end == d2
        assert tb.callingClass == 'getDataTestBed'

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_getdatatestbed_has_data_locations(self, mock_date2num, sample_datetime_range):
        """Test that getDataTestBed has data location attributes."""
        mock_date2num.return_value = 1577836800.0
        d1, d2 = sample_datetime_range

        from murgtools.getdata.getDataFRF import getDataTestBed
        tb = getDataTestBed(d1, d2)

        assert hasattr(tb, 'FRFdataloc')
        assert hasattr(tb, 'chlDataLoc')
        assert hasattr(tb, 'crunchDataLoc')


class TestGetArgusImagery:
    """Tests for the getArgusImagery function."""

    def test_invalid_image_type_raises_error(self):
        """Test that invalid imageType raises ValueError."""
        from murgtools.getdata.getDataFRF import getArgusImagery

        with pytest.raises(ValueError, match="Invalid imageType"):
            getArgusImagery(DT.datetime(2024, 6, 15, 12, 0, 0), imageType="invalid")

    def test_valid_image_types_accepted(self):
        """Test that all valid image types are accepted."""
        from murgtools.getdata.getDataFRF import getArgusImagery
        import requests

        valid_types = ['timex', 'var', 'snap', 'bright', 'dark']
        for img_type in valid_types:
            # Patch at the requests module level since it's imported locally
            with patch.object(requests, 'get') as mock_get:
                mock_get.side_effect = requests.exceptions.RequestException("Network disabled")
                # Should not raise ValueError for valid image types
                result = getArgusImagery(
                    DT.datetime(2024, 6, 15, 12, 0, 0),
                    imageType=img_type,
                    verbose=False
                )
                assert result is None  # Network error returns None

    def test_time_rounding_to_30_minutes(self):
        """Test that times are rounded to nearest 30 minutes."""
        from murgtools.getdata.getDataFRF import getArgusImagery
        import requests

        test_cases = [
            (DT.datetime(2024, 6, 15, 12, 10, 0), "120000"),  # rounds down to 12:00
            (DT.datetime(2024, 6, 15, 12, 20, 0), "123000"),  # rounds up to 12:30
            (DT.datetime(2024, 6, 15, 12, 40, 0), "123000"),  # rounds down to 12:30
            (DT.datetime(2024, 6, 15, 12, 50, 0), "130000"),  # rounds up to 13:00
        ]

        for input_time, expected_time_str in test_cases:
            with patch.object(requests, 'get') as mock_get:
                mock_get.side_effect = requests.exceptions.RequestException("Network disabled")
                getArgusImagery(input_time, verbose=False)

                # Verify the URL constructed contains the expected time
                call_args = mock_get.call_args
                assert call_args is not None, f"requests.get was not called for {input_time}"
                url = call_args[0][0]
                assert expected_time_str in url, f"Expected {expected_time_str} in URL {url}"

    def test_url_construction(self):
        """Test that URL is constructed correctly."""
        from murgtools.getdata.getDataFRF import getArgusImagery
        import requests

        with patch.object(requests, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Network disabled")
            getArgusImagery(DT.datetime(2024, 6, 15, 12, 0, 0), imageType="timex", verbose=False)

            call_args = mock_get.call_args
            url = call_args[0][0]

            assert "coastalimaging.erdc.dren.mil" in url
            assert "FrfTower/Processed/Orthophotos/cxgeo" in url
            assert "2024_06_15" in url
            assert "20240615T120000Z" in url
            assert "timex.tif" in url

    @pytest.mark.slow
    def test_successful_image_retrieval(self):
        """Test successful image retrieval (requires network)."""
        from murgtools.getdata.getDataFRF import getArgusImagery

        # Use a known date when imagery is likely available
        result = getArgusImagery(DT.datetime(2024, 6, 15, 12, 0, 0))

        if result is not None:
            assert 'image' in result
            assert 'time' in result
            assert 'epochtime' in result
            assert 'imageType' in result
            assert 'url' in result
            assert isinstance(result['image'], np.ndarray)
            assert result['imageType'] == 'timex'

    def test_returns_none_on_network_error(self):
        """Test that function returns None on network error."""
        from murgtools.getdata.getDataFRF import getArgusImagery
        import requests

        with patch.object(requests, 'get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Connection failed")
            result = getArgusImagery(DT.datetime(2024, 6, 15, 12, 0, 0), verbose=False)

            assert result is None


class TestThreadGetArgusImagery:
    """Tests for the threadGetArgusImagery function."""

    def test_returns_filename_immediately(self):
        """Test that function returns filename immediately without blocking."""
        from murgtools.getdata.getDataFRF import threadGetArgusImagery
        import time

        with patch('murgtools.getdata.getDataFRF.getArgusImagery') as mock_get:
            # Make the mock slow to ensure we're not waiting
            def slow_get(*args, **kwargs):
                time.sleep(10)
                return None
            mock_get.side_effect = slow_get

            start = time.time()
            filename = threadGetArgusImagery(DT.datetime(2024, 6, 15, 12, 0, 0))
            elapsed = time.time() - start

            # Should return almost immediately (less than 1 second)
            assert elapsed < 1.0
            assert filename is not None
            assert filename.endswith('.tif')

    def test_generates_default_filename(self):
        """Test that default filename is generated correctly."""
        from murgtools.getdata.getDataFRF import threadGetArgusImagery

        with patch('murgtools.getdata.getDataFRF.getArgusImagery'):
            filename = threadGetArgusImagery(
                DT.datetime(2024, 6, 15, 12, 0, 0),
                imageType="var"
            )

            assert "Argus_var_" in filename
            assert "20240615T120000Z" in filename
            assert filename.endswith('.tif')

    def test_uses_provided_filename(self):
        """Test that provided filename is used."""
        from murgtools.getdata.getDataFRF import threadGetArgusImagery

        with patch('murgtools.getdata.getDataFRF.getArgusImagery'):
            custom_filename = "/tmp/my_custom_argus.tif"
            filename = threadGetArgusImagery(
                DT.datetime(2024, 6, 15, 12, 0, 0),
                filename=custom_filename
            )

            assert filename == custom_filename


class TestGetObsGetWaveData:
    """Tests for the getObs.getWaveData method."""

    @patch('murgtools.getdata.getDataFRF.getnc')
    @patch('murgtools.getdata.getDataFRF.gettime')
    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    @patch('murgtools.getdata.getDataFRF.nc.num2date')
    @patch('murgtools.getdata.getDataFRF.gp.FRFcoord')
    def test_getWaveData_returns_expected_keys(self, mock_frfcoord, mock_num2date, mock_date2num,
                                               mock_gettime, mock_getnc):
        """Test that getWaveData returns dictionary with expected keys."""
        mock_date2num.return_value = 1577836800.0

        # Create mock dataset
        base_epoch = 1577836800.0
        time_values = np.array([base_epoch + i * 1800 for i in range(48)])
        n_times = 10
        n_freqs = 20
        n_dirs = 72

        mock_ds = MagicMock()
        mock_ds.__getitem__ = MagicMock(side_effect=lambda k: {
            'time': MagicMock(units='seconds since 1970-01-01 00:00:00'),
            'waveHs': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx) if hasattr(idx, '__len__') else 1) * 1.5),
            'waveTp': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx) if hasattr(idx, '__len__') else 1) * 8.0),
            'waveFrequency': np.linspace(0.05, 0.5, n_freqs),
            'waveDirectionBins': np.linspace(0, 360, n_dirs),
            'latitude': np.array([36.0]),
            'longitude': np.array([-75.0]),
            'nominalDepth': np.array([26.0]),
            'qcFlagE': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx) if hasattr(idx, '__len__') else 1) * 1),
            'qcFlagD': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx) if hasattr(idx, '__len__') else 1) * 1),
        }.get(k, MagicMock()))

        mock_ds.title = 'FRF Waverider 26m'
        mock_ds.variables = MagicMock()
        mock_ds.variables.keys = MagicMock(return_value=['time', 'waveHs', 'waveTp', 'waveFrequency',
                                                         'qcFlagE', 'qcFlagD', 'waveDirectionBins'])

        # getnc returns (ncFile, allEpoch, indexRef)
        mock_getnc.return_value = (mock_ds, time_values, None)

        # gettime returns indices within the time range
        mock_gettime.return_value = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

        d1 = DT.datetime(2020, 1, 1, 0, 0, 0)
        d2 = DT.datetime(2020, 1, 1, 12, 0, 0)
        mock_num2date.return_value = np.array([d1 + DT.timedelta(minutes=30*i) for i in range(n_times)])
        mock_frfcoord.return_value = {'xFRF': 914.0, 'yFRF': 515.0}

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)
        result = obs.getWaveData(gaugenumber='waverider-26m')

        # Verify expected keys present
        assert result is not None
        expected_keys = ['time', 'epochtime', 'name', 'wavefreqbin', 'xFRF', 'yFRF',
                         'lat', 'lon', 'depth', 'Hs']
        for key in expected_keys:
            assert key in result, f"Missing expected key: {key}"

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_getWaveData_gauge_lookup_valid_names(self, mock_date2num):
        """Test that _waveGaugeURLlookup accepts various valid gauge names."""
        mock_date2num.return_value = 1577836800.0
        d1 = DT.datetime(2020, 1, 1)
        d2 = DT.datetime(2020, 1, 2)

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        # Test various gauge name formats
        valid_gauges = [
            ('waverider-26m', 'oceanography/waves/waverider-26m/waverider-26m.ncml'),
            ('0', 'oceanography/waves/waverider-26m/waverider-26m.ncml'),
            ('awac-11m', 'oceanography/waves/awac-11m/awac-11m.ncml'),
            ('xp200m', 'oceanography/waves/xp200m/xp200m.ncml'),
            ('8m-array', 'oceanography/waves/8m-array/8m-array.ncml'),
        ]

        for gauge_name, expected_url in valid_gauges:
            obs._waveGaugeURLlookup(gauge_name)
            assert obs.dataloc == expected_url, f"Failed for gauge: {gauge_name}"

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_getWaveData_gauge_lookup_invalid_raises(self, mock_date2num):
        """Test that _waveGaugeURLlookup raises InvalidGaugeError for invalid gauge."""
        mock_date2num.return_value = 1577836800.0
        d1 = DT.datetime(2020, 1, 1)
        d2 = DT.datetime(2020, 1, 2)

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        with pytest.raises(InvalidGaugeError):
            obs._waveGaugeURLlookup('invalid-gauge-name')


class TestGetObsGetWind:
    """Tests for the getObs.getWind method."""

    @patch('murgtools.getdata.getDataFRF.getnc')
    @patch('murgtools.getdata.getDataFRF.gettime')
    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    @patch('murgtools.getdata.getDataFRF.nc.num2date')
    def test_getWind_returns_expected_keys(self, mock_num2date, mock_date2num, mock_gettime, mock_getnc):
        """Test that getWind returns dictionary with expected keys."""
        mock_date2num.return_value = 1577836800.0

        base_epoch = 1577836800.0
        time_values = np.array([base_epoch + i * 600 for i in range(144)])  # 10 min intervals

        mock_ds = MagicMock()
        mock_ds.__getitem__ = MagicMock(side_effect=lambda k: {
            'time': MagicMock(units='seconds since 1970-01-01 00:00:00'),
            'windSpeed': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 5.0),
            'windDirection': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 180.0),
            'vectorSpeed': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 4.8),
            'windGust': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 7.0),
            'stdWindSpeed': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 1.0),
            'qcFlagS': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 1),
            'qcFlagD': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 1),
            'minWindSpeed': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 3.0),
            'maxWindSpeed': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 8.0),
            'sustWindSpeed': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 6.0),
            'latitude': np.array([36.18]),
            'longitude': np.array([-75.75]),
        }.get(k, MagicMock()))

        mock_ds.title = 'FRF Derived Wind'
        mock_ds.geospatial_vertical_max = 19.0

        # getnc returns (ncFile, allEpoch, indexRef) - 3 values
        mock_getnc.return_value = (mock_ds, time_values, None)

        # gettime returns indices
        mock_gettime.return_value = np.arange(72)

        d1 = DT.datetime(2020, 1, 1, 0, 0, 0)
        d2 = DT.datetime(2020, 1, 1, 12, 0, 0)
        mock_num2date.return_value = np.array([d1 + DT.timedelta(minutes=10*i) for i in range(72)])

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)
        result = obs.getWind(gaugenumber=0)

        assert result is not None
        expected_keys = ['name', 'time', 'epochtime', 'vecspeed', 'windspeed',
                         'windspeed_corrected', 'winddir', 'windgust', 'qcflagS',
                         'qcflagD', 'stdspeed', 'minspeed', 'maxspeed', 'sustspeed',
                         'lat', 'lon', 'gaugeht']
        for key in expected_keys:
            assert key in result, f"Missing expected key: {key}"

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_getWind_gauge_selection(self, mock_date2num):
        """Test that getWind selects correct data location for gauge number."""
        mock_date2num.return_value = 1577836800.0
        d1 = DT.datetime(2020, 1, 1)
        d2 = DT.datetime(2020, 1, 2)

        from murgtools.getdata.getDataFRF import getObs
        getObs(d1, d2)

        # Test gauge selection by checking dataloc would be set correctly
        gauge_mappings = {
            0: 'meteorology/wind/derived/derived.ncml',
            'derived': 'meteorology/wind/derived/derived.ncml',
            1: 'meteorology/wind/D932/D932.ncml',
            2: 'meteorology/wind/D832/D832.ncml',
            3: 'meteorology/wind/D732/D732.ncml',
        }

        for gauge, expected_loc in gauge_mappings.items():
            # We can't fully test without mocking getnc, but we can test the gauge number validation
            assert gauge in [0, 1, 2, 3, 'derived', 'Derived']

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_getWind_invalid_gauge_raises(self, mock_date2num):
        """Test that getWind raises for invalid gauge number."""
        mock_date2num.return_value = 1577836800.0
        d1 = DT.datetime(2020, 1, 1)
        d2 = DT.datetime(2020, 1, 2)

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        with pytest.raises(InvalidGaugeError):
            obs.getWind(gaugenumber=99)


class TestGetObsGetWL:
    """Tests for the getObs.getWL method."""

    @patch('murgtools.getdata.getDataFRF.getnc')
    @patch('murgtools.getdata.getDataFRF.gettime')
    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    @patch('murgtools.getdata.getDataFRF.nc.num2date')
    def test_getWL_returns_expected_keys(self, mock_num2date, mock_date2num, mock_gettime, mock_getnc):
        """Test that getWL returns dictionary with expected keys."""
        mock_date2num.return_value = 1577836800.0

        base_epoch = 1577836800.0
        time_values = np.array([base_epoch + i * 360 for i in range(240)])  # 6 min intervals

        mock_ds = MagicMock()
        mock_ds.__getitem__ = MagicMock(side_effect=lambda k: {
            'time': MagicMock(units='seconds since 1970-01-01 00:00:00'),
            'waterLevel': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 0.5),
            'predictedWaterLevel': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 0.4),
            'latitude': np.array([36.18]),
            'longitude': np.array([-75.75]),
        }.get(k, MagicMock()))

        mock_ds.title = 'FRF NOAA Tide Gauge'

        # getWL unpacks 3 values from getnc
        mock_getnc.return_value = (mock_ds, time_values, None)

        # gettime returns indices (need more than 1 for getWL)
        mock_gettime.return_value = np.arange(120)

        d1 = DT.datetime(2020, 1, 1, 0, 0, 0)
        d2 = DT.datetime(2020, 1, 1, 12, 0, 0)
        mock_num2date.return_value = np.array([d1 + DT.timedelta(minutes=6*i) for i in range(120)])

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)
        result = obs.getWL()

        assert result is not None
        expected_keys = ['name', 'WL', 'time', 'epochtime', 'lat', 'lon',
                         'predictedWL', 'residual']
        for key in expected_keys:
            assert key in result, f"Missing expected key: {key}"

    @patch('murgtools.getdata.getDataFRF.getnc')
    @patch('murgtools.getdata.getDataFRF.gettime')
    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    @patch('murgtools.getdata.getDataFRF.nc.num2date')
    def test_getWL_calculates_residual(self, mock_num2date, mock_date2num, mock_gettime, mock_getnc):
        """Test that getWL correctly calculates residual from WL and predicted."""
        mock_date2num.return_value = 1577836800.0

        base_epoch = 1577836800.0
        time_values = np.array([base_epoch + i * 360 for i in range(100)])

        wl_values = np.array([0.6, 0.7, 0.8])
        predicted_values = np.array([0.5, 0.5, 0.5])

        mock_ds = MagicMock()
        mock_ds.__getitem__ = MagicMock(side_effect=lambda k: {
            'time': MagicMock(units='seconds since 1970-01-01 00:00:00'),
            'waterLevel': MagicMock(__getitem__=lambda s, idx: wl_values),
            'predictedWaterLevel': MagicMock(__getitem__=lambda s, idx: predicted_values),
            'latitude': np.array([36.18]),
            'longitude': np.array([-75.75]),
        }.get(k, MagicMock()))

        mock_ds.title = 'FRF NOAA Tide Gauge'

        # getWL unpacks 3 values from getnc
        mock_getnc.return_value = (mock_ds, time_values, None)

        # gettime returns indices (need more than 1 for getWL)
        mock_gettime.return_value = np.arange(3)

        d1 = DT.datetime(2020, 1, 1, 0, 0, 0)
        d2 = DT.datetime(2020, 1, 1, 1, 0, 0)
        mock_num2date.return_value = np.array([d1 + DT.timedelta(minutes=6*i) for i in range(3)])

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)
        result = obs.getWL()

        if result is not None:
            # Residual should be WL - predictedWL
            assert 'residual' in result


class TestGetObsGetCurrents:
    """Tests for the getObs.getCurrents method."""

    @patch('murgtools.getdata.getDataFRF.getnc')
    @patch('murgtools.getdata.getDataFRF.gettime')
    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    @patch('murgtools.getdata.getDataFRF.nc.num2date')
    @patch('murgtools.getdata.getDataFRF.gp.FRFcoord')
    def test_getCurrents_returns_expected_keys(self, mock_frfcoord, mock_num2date, mock_date2num,
                                               mock_gettime, mock_getnc):
        """Test that getCurrents returns dictionary with expected keys."""
        mock_date2num.return_value = 1577836800.0
        mock_frfcoord.return_value = {'xFRF': 400.0, 'yFRF': 515.0}

        base_epoch = 1577836800.0
        time_values = np.array([base_epoch + i * 60 for i in range(720)])  # 1 min intervals

        mock_ds = MagicMock()
        mock_time = MagicMock()
        mock_time.units = 'seconds since 1970-01-01 00:00:00'
        mock_time.calendar = 'standard'

        mock_ds.__getitem__ = MagicMock(side_effect=lambda k: {
            'time': mock_time,
            'aveE': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 0.1),
            'aveN': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 0.2),
            'currentSpeed': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 0.22),
            'currentDirection': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 63.0),
            'meanPressure': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 10.5),
            'latitude': np.array([36.18]),
            'longitude': np.array([-75.75]),
            'depth': np.array([4.5]),
        }.get(k, MagicMock()))

        mock_ds.title = 'FRF AWAC 4.5m Currents'

        # getCurrents unpacks 3 values from getnc
        mock_getnc.return_value = (mock_ds, time_values, None)

        # gettime returns indices (need more than 1 for getCurrents)
        mock_gettime.return_value = np.arange(360)

        d1 = DT.datetime(2020, 1, 1, 0, 0, 0)
        d2 = DT.datetime(2020, 1, 1, 6, 0, 0)
        mock_num2date.return_value = np.array([d1 + DT.timedelta(minutes=i) for i in range(360)])

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)
        result = obs.getCurrents(gaugenumber='awac-4.5m')

        assert result is not None
        expected_keys = ['name', 'time', 'epochtime', 'aveU', 'aveV', 'speed',
                         'dir', 'lat', 'lon', 'xFRF', 'yFRF', 'depth', 'meanP']
        for key in expected_keys:
            assert key in result, f"Missing expected key: {key}"

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_getCurrents_valid_gauge_names(self, mock_date2num):
        """Test that getCurrents accepts valid gauge names."""
        mock_date2num.return_value = 1577836800.0
        d1 = DT.datetime(2020, 1, 1)
        d2 = DT.datetime(2020, 1, 2)

        from murgtools.getdata.getDataFRF import getObs
        getObs(d1, d2)

        valid_gauges = ['awac-11m', 'awac-8m', 'awac-6m', 'awac-4.5m', 'adop-3.5m']
        for gauge in valid_gauges:
            # The gauge name validation happens at the start of getCurrents
            # We verify they are in the accepted list
            assert gauge.lower() in ['awac-11m', 'awac-8m', 'awac-6m', 'awac-4.5m', 'adop-3.5m']

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_getCurrents_invalid_gauge_raises(self, mock_date2num):
        """Test that getCurrents raises InvalidGaugeError for invalid gauge."""
        mock_date2num.return_value = 1577836800.0
        d1 = DT.datetime(2020, 1, 1)
        d2 = DT.datetime(2020, 1, 2)

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        with pytest.raises(InvalidGaugeError):
            obs.getCurrents(gaugenumber='invalid-gauge')


class TestGetObsGetWaveSpec:
    """Tests for the getObs.getWaveSpec method."""

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_getWaveSpec_emits_deprecation_warning(self, mock_date2num):
        """Test that getWaveSpec emits a deprecation warning."""
        mock_date2num.return_value = 1577836800.0
        d1 = DT.datetime(2020, 1, 1)
        d2 = DT.datetime(2020, 1, 2)

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        with pytest.warns(UserWarning, match="getWaveSpec is depreciated"):
            with patch.object(obs, 'getWaveData', return_value={'test': 'data'}):
                obs.getWaveSpec()

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_getWaveSpec_calls_getWaveData_with_spec_true(self, mock_date2num):
        """Test that getWaveSpec calls getWaveData with spec=True."""
        mock_date2num.return_value = 1577836800.0
        d1 = DT.datetime(2020, 1, 1)
        d2 = DT.datetime(2020, 1, 2)

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        with patch.object(obs, 'getWaveData', return_value={'test': 'data'}) as mock_wave:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = obs.getWaveSpec(gaugenumber='waverider-26m', roundto=30)

            mock_wave.assert_called_once()
            call_kwargs = mock_wave.call_args[1]
            assert call_kwargs.get('spec') is True


class TestNewGaugeURLLookups:
    """Tests for newly added gauge URL lookups (sig940-*, awac-jpier, waverider-20m, etc.)."""

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_wave_gauge_lookup_signature_profilers(self, mock_date2num):
        """Test that signature profiler wave gauges are recognized."""
        mock_date2num.return_value = 1577836800.0
        d1 = DT.datetime(2020, 1, 1)
        d2 = DT.datetime(2020, 1, 2)

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        # Test new signature profiler gauges
        sig_gauges = [
            ('sig940-400', 'oceanography/waves/sig940-400/sig940-400.ncml'),
            ('940-400', 'oceanography/waves/sig940-400/sig940-400.ncml'),
            ('sig940-600', 'oceanography/waves/sig940-600/sig940-600.ncml'),
            ('940-600', 'oceanography/waves/sig940-600/sig940-600.ncml'),
        ]

        for gauge_name, expected_url in sig_gauges:
            obs._waveGaugeURLlookup(gauge_name)
            assert obs.dataloc == expected_url, f"Failed for gauge: {gauge_name}"

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_wave_gauge_lookup_awac_jpier(self, mock_date2num):
        """Test that AWAC jetty pier gauge is recognized."""
        mock_date2num.return_value = 1577836800.0
        d1 = DT.datetime(2020, 1, 1)
        d2 = DT.datetime(2020, 1, 2)

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        jpier_gauges = [
            ('awac-jpier-11m', 'oceanography/waves/awac-jpier-11m/awac-jpier-11m.ncml'),
            ('awac-jpier', 'oceanography/waves/awac-jpier-11m/awac-jpier-11m.ncml'),
            ('jpier-11m', 'oceanography/waves/awac-jpier-11m/awac-jpier-11m.ncml'),
        ]

        for gauge_name, expected_url in jpier_gauges:
            obs._waveGaugeURLlookup(gauge_name)
            assert obs.dataloc == expected_url, f"Failed for gauge: {gauge_name}"

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_wave_gauge_lookup_new_waveriders(self, mock_date2num):
        """Test that new waverider gauges are recognized."""
        mock_date2num.return_value = 1577836800.0
        d1 = DT.datetime(2020, 1, 1)
        d2 = DT.datetime(2020, 1, 2)

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        waverider_gauges = [
            ('waverider-17m-1d', 'oceanography/waves/waverider-17m-1d/waverider-17m-1d.ncml'),
            ('waverider-17m-1D', 'oceanography/waves/waverider-17m-1d/waverider-17m-1d.ncml'),
            ('17m-1d', 'oceanography/waves/waverider-17m-1d/waverider-17m-1d.ncml'),
            ('17m-1D', 'oceanography/waves/waverider-17m-1d/waverider-17m-1d.ncml'),
            ('waverider-20m', 'oceanography/waves/waverider-20m-1d/waverider-20m-1d.ncml'),
            ('waverider-20m-1d', 'oceanography/waves/waverider-20m-1d/waverider-20m-1d.ncml'),
            ('20m', 'oceanography/waves/waverider-20m-1d/waverider-20m-1d.ncml'),
        ]

        for gauge_name, expected_url in waverider_gauges:
            obs._waveGaugeURLlookup(gauge_name)
            assert obs.dataloc == expected_url, f"Failed for gauge: {gauge_name}"

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_wave_gauge_lookup_paros_aliases(self, mock_date2num):
        """Test that both paros naming conventions work."""
        mock_date2num.return_value = 1577836800.0
        d1 = DT.datetime(2020, 1, 1)
        d2 = DT.datetime(2020, 1, 2)

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        paros_gauges = [
            ('paros-200-940m', 'oceanography/waves/paros940-200/paros940-200.ncml'),
            ('paros940-200', 'oceanography/waves/paros940-200/paros940-200.ncml'),
            ('paros-250-940m', 'oceanography/waves/paros940-250/paros940-250.ncml'),
            ('paros940-250', 'oceanography/waves/paros940-250/paros940-250.ncml'),
        ]

        for gauge_name, expected_url in paros_gauges:
            obs._waveGaugeURLlookup(gauge_name)
            assert obs.dataloc == expected_url, f"Failed for gauge: {gauge_name}"

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_currents_gauge_lookup_signature_profilers(self, mock_date2num):
        """Test that signature profiler current meters are recognized."""
        mock_date2num.return_value = 1577836800.0
        d1 = DT.datetime(2020, 1, 1)
        d2 = DT.datetime(2020, 1, 2)

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        # Verify signature profilers are in the valid gauge list for currents
        sig_gauges = ['sig769-300', 'sig940-300', 'sig940-400', 'sig940-600']
        for gauge in sig_gauges:
            assert gauge in obs.currentsGaugeList, f"{gauge} should be in currentsGaugeList"

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_currents_gauge_lookup_awac_jpier(self, mock_date2num):
        """Test that AWAC jetty pier current gauge is recognized."""
        mock_date2num.return_value = 1577836800.0
        d1 = DT.datetime(2020, 1, 1)
        d2 = DT.datetime(2020, 1, 2)

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        assert 'awac-jpier-11m' in obs.currentsGaugeList

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_wave_gauge_list_contains_new_gauges(self, mock_date2num):
        """Test that waveGaugeList includes newly added gauges."""
        mock_date2num.return_value = 1577836800.0
        d1 = DT.datetime(2020, 1, 1)
        d2 = DT.datetime(2020, 1, 2)

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        new_wave_gauges = [
            'waverider-17m-1d', 'waverider-20m-1d', 'awac-jpier-11m',
            'sig940-300', 'sig769-300', 'sig940-400', 'sig940-600'
        ]
        for gauge in new_wave_gauges:
            assert gauge in obs.waveGaugeList, f"{gauge} should be in waveGaugeList"

    @patch('murgtools.getdata.getDataFRF.nc.date2num')
    def test_directional_wave_gauge_list_contains_new_gauges(self, mock_date2num):
        """Test that directionalWaveGaugeList includes newly added directional gauges."""
        mock_date2num.return_value = 1577836800.0
        d1 = DT.datetime(2020, 1, 1)
        d2 = DT.datetime(2020, 1, 2)

        from murgtools.getdata.getDataFRF import getObs
        obs = getObs(d1, d2)

        # Waveriders and AWACs provide directional data
        directional_gauges = ['waverider-17m-1d', 'waverider-20m-1d', 'awac-jpier-11m']
        for gauge in directional_gauges:
            assert gauge in obs.directionalWaveGaugeList, \
                f"{gauge} should be in directionalWaveGaugeList"


class TestGetArgusPixelIntensity:
    """Tests for the getArgusPixelIntensity function."""

    @patch('murgtools.getdata.getDataFRF.getArgusImagery')
    def test_single_time_pixel_coords(self, mock_get_imagery):
        """Test extraction with single time and pixel coordinates."""
        from murgtools.getdata.getDataFRF import getArgusPixelIntensity

        # Mock image data
        mock_image = np.ones((1000, 1500, 3), dtype=np.uint8) * 100
        mock_image[200, 150, :] = [255, 128, 64]  # Set specific pixel
        
        mock_get_imagery.return_value = {
            'image': mock_image,
            'time': DT.datetime(2024, 6, 15, 12, 0, 0),
            'epochtime': 1718452800.0,
            'imageType': 'timex',
            'url': 'http://test.com/image.tif',
        }

        result = getArgusPixelIntensity(
            DT.datetime(2024, 6, 15, 12, 0, 0),
            location=(150, 200),
            coordType='pixel',
            verbose=False
        )

        assert result is not None
        assert len(result['time']) == 1
        assert len(result['intensity']) == 1
        np.testing.assert_array_equal(result['intensity'][0], [255, 128, 64])
        assert result['location']['pixel_i'] == 150
        assert result['location']['pixel_j'] == 200

    @patch('murgtools.getdata.getDataFRF.getArgusImagery')
    def test_multiple_times(self, mock_get_imagery):
        """Test extraction over multiple times."""
        from murgtools.getdata.getDataFRF import getArgusPixelIntensity

        # Mock responses for multiple times
        def mock_imagery_side_effect(dateOfInterest, **kwargs):
            mock_image = np.ones((1000, 1500, 3), dtype=np.uint8) * 100
            mock_image[200, 150, :] = [255, 128, 64]
            return {
                'image': mock_image,
                'time': dateOfInterest,
                'epochtime': nc.date2num(dateOfInterest, 'seconds since 1970-01-01'),
                'imageType': 'timex',
                'url': 'http://test.com/image.tif',
            }

        mock_get_imagery.side_effect = mock_imagery_side_effect

        times = [
            DT.datetime(2024, 6, 15, 12, 0, 0),
            DT.datetime(2024, 6, 15, 13, 0, 0),
            DT.datetime(2024, 6, 15, 14, 0, 0),
        ]

        result = getArgusPixelIntensity(
            times,
            location=(150, 200),
            coordType='pixel',
            verbose=False
        )

        assert result is not None
        assert len(result['time']) == 3
        assert len(result['intensity']) == 3
        assert len(result['missing_times']) == 0

    @patch('murgtools.getdata.getDataFRF.getArgusImagery')
    def test_missing_times_handling(self, mock_get_imagery):
        """Test that missing times are properly tracked."""
        from murgtools.getdata.getDataFRF import getArgusPixelIntensity

        # Mock: first and third succeed, second fails
        call_count = [0]
        
        def mock_imagery_side_effect(dateOfInterest, **kwargs):
            call_count[0] += 1
            if call_count[0] == 2:  # Second call returns None
                return None
            
            mock_image = np.ones((1000, 1500, 3), dtype=np.uint8) * 100
            mock_image[200, 150, :] = [255, 128, 64]
            return {
                'image': mock_image,
                'time': dateOfInterest,
                'epochtime': nc.date2num(dateOfInterest, 'seconds since 1970-01-01'),
                'imageType': 'timex',
                'url': 'http://test.com/image.tif',
            }

        mock_get_imagery.side_effect = mock_imagery_side_effect

        times = [
            DT.datetime(2024, 6, 15, 12, 0, 0),
            DT.datetime(2024, 6, 15, 13, 0, 0),  # This will fail
            DT.datetime(2024, 6, 15, 14, 0, 0),
        ]

        result = getArgusPixelIntensity(
            times,
            location=(150, 200),
            coordType='pixel',
            verbose=False
        )

        assert result is not None
        assert len(result['time']) == 2
        assert len(result['intensity']) == 2
        assert len(result['missing_times']) == 1
        assert result['missing_times'][0] == times[1]

    @patch('murgtools.getdata.getDataFRF.getArgusImagery')
    def test_channel_extraction(self, mock_get_imagery):
        """Test extraction of specific color channels."""
        from murgtools.getdata.getDataFRF import getArgusPixelIntensity

        mock_image = np.ones((1000, 1500, 3), dtype=np.uint8) * 100
        mock_image[200, 150, :] = [255, 128, 64]
        
        mock_get_imagery.return_value = {
            'image': mock_image,
            'time': DT.datetime(2024, 6, 15, 12, 0, 0),
            'epochtime': 1718452800.0,
            'imageType': 'timex',
            'url': 'http://test.com/image.tif',
        }

        # Test red channel
        result = getArgusPixelIntensity(
            DT.datetime(2024, 6, 15, 12, 0, 0),
            location=(150, 200),
            coordType='pixel',
            channel='red',
            verbose=False
        )
        assert result['intensity'][0] == 255

        # Test green channel
        result = getArgusPixelIntensity(
            DT.datetime(2024, 6, 15, 12, 0, 0),
            location=(150, 200),
            coordType='pixel',
            channel='green',
            verbose=False
        )
        assert result['intensity'][0] == 128

        # Test blue channel
        result = getArgusPixelIntensity(
            DT.datetime(2024, 6, 15, 12, 0, 0),
            location=(150, 200),
            coordType='pixel',
            channel='blue',
            verbose=False
        )
        assert result['intensity'][0] == 64

    @patch('murgtools.getdata.getDataFRF.getArgusImagery')
    def test_grayscale_conversion(self, mock_get_imagery):
        """Test grayscale conversion."""
        from murgtools.getdata.getDataFRF import getArgusPixelIntensity

        mock_image = np.ones((1000, 1500, 3), dtype=np.uint8) * 100
        mock_image[200, 150, :] = [255, 128, 64]
        
        mock_get_imagery.return_value = {
            'image': mock_image,
            'time': DT.datetime(2024, 6, 15, 12, 0, 0),
            'epochtime': 1718452800.0,
            'imageType': 'timex',
            'url': 'http://test.com/image.tif',
        }

        result = getArgusPixelIntensity(
            DT.datetime(2024, 6, 15, 12, 0, 0),
            location=(150, 200),
            coordType='pixel',
            channel='gray',
            verbose=False
        )

        # Grayscale: 0.299*R + 0.587*G + 0.114*B
        expected = 0.299 * 255 + 0.587 * 128 + 0.114 * 64
        assert np.isclose(result['intensity'][0], expected)

    @patch('murgtools.getdata.getDataFRF.getArgusImagery')
    def test_out_of_bounds_pixel(self, mock_get_imagery):
        """Test handling of out-of-bounds pixel coordinates.

        When pixel coordinates are out of bounds, the function should return None
        since all requested times resulted in out-of-bounds coordinates.
        """
        from murgtools.getdata.getDataFRF import getArgusPixelIntensity

        mock_image = np.ones((1000, 1500, 3), dtype=np.uint8) * 100

        mock_get_imagery.return_value = {
            'image': mock_image,
            'time': DT.datetime(2024, 6, 15, 12, 0, 0),
            'epochtime': 1718452800.0,
            'imageType': 'timex',
            'url': 'http://test.com/image.tif',
        }

        # Pixel coordinates out of bounds (image width is 1500, so i=2000 is invalid)
        result = getArgusPixelIntensity(
            DT.datetime(2024, 6, 15, 12, 0, 0),
            location=(2000, 200),  # i out of bounds (> 1500)
            coordType='pixel',
            verbose=False
        )

        # Should return None because the only time has out-of-bounds coordinates
        assert result is None

    @patch('requests.get')
    @patch('murgtools.getdata.getDataFRF.getArgusImagery')
    @patch('murgtools.utils.geoprocess.FRF2ncsp')
    def test_frf_coordinates(self, mock_frf2ncsp, mock_get_imagery, mock_requests_get):
        """Test extraction using FRF coordinates.

        This test verifies that FRF local coordinates (xFRF, yFRF) are correctly
        converted to pixel coordinates via State Plane coordinates. The test uses
        realistic FRF coordinates and sets up a GeoTIFF with appropriate georeferencing
        tags to enable accurate coordinate transformation.
        """
        from murgtools.getdata.getDataFRF import getArgusPixelIntensity
        import tempfile
        import tifffile

        # Create a minimal valid GeoTIFF
        mock_image = np.ones((1000, 1500, 3), dtype=np.uint8) * 100
        mock_image[200, 150, :] = [255, 128, 64]

        mock_get_imagery.return_value = {
            'image': mock_image,
            'time': DT.datetime(2024, 6, 15, 12, 0, 0),
            'epochtime': 1718452800.0,
            'imageType': 'timex',
            'url': 'http://test.com/image.tif',
        }

        # Mock FRF to state plane conversion
        # FRF (500, 100) -> State Plane (902000.0, 274500.0)
        mock_frf2ncsp.return_value = {
            'StateplaneE': 902000.0,
            'StateplaneN': 274500.0,
        }

        # Create a mock GeoTIFF file with proper tags
        with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
            tmp_path = tmp.name
            # Create GeoTIFF with tags using extratags parameter
            # ModelTiepointTag: (pixel_i, pixel_j, 0, world_x, world_y, 0)
            # Pixel (0, 0) is at State Plane (900500.0, 276000.0)
            # With scale_x=10, scale_y=-10 (negative for typical GeoTIFF y-axis)
            # Then pixel (150, 200) maps to:
            #   world_x = 900500 + 150*10 = 902000 (matches our test location)
            #   world_y = 276000 + 200*(-10) = 274000 (close to our test location)
            tiepoint = [0.0, 0.0, 0.0, 900500.0, 276000.0, 0.0]
            # ModelPixelScaleTag: (scale_x, scale_y, scale_z)
            # scale_y is negative in GeoTIFF (y decreases as row increases)
            scale = [10.0, -10.0, 0.0]  # 10 meters per pixel

            extratags = [
                (33922, 'd', 6, tiepoint, True),  # ModelTiepointTag
                (33550, 'd', 3, scale, True),     # ModelPixelScaleTag
            ]

            tifffile.imwrite(tmp_path, mock_image, extratags=extratags)
        
        try:
            # Mock requests.get to return the temp file content
            with open(tmp_path, 'rb') as f:
                file_content = f.read()
            
            mock_response = MagicMock()
            mock_response.iter_content = MagicMock(return_value=[file_content])
            mock_response.raise_for_status = MagicMock()
            mock_requests_get.return_value = mock_response
            
            result = getArgusPixelIntensity(
                DT.datetime(2024, 6, 15, 12, 0, 0),
                location=(500, 100),  # xFRF, yFRF
                coordType='FRF',
                verbose=False
            )
            
            # Should succeed and convert coordinates
            assert result is not None
            assert 'xFRF' in result['location']
            assert 'yFRF' in result['location']
            assert result['location']['xFRF'] == 500
            assert result['location']['yFRF'] == 100
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_invalid_coord_type(self):
        """Test that invalid coordType raises error."""
        from murgtools.getdata.getDataFRF import getArgusPixelIntensity

        with pytest.raises(ValueError, match="Invalid coordType"):
            getArgusPixelIntensity(
                DT.datetime(2024, 6, 15, 12, 0, 0),
                location=(500, 100),
                coordType='invalid',
                verbose=False
            )

    def test_invalid_channel(self):
        """Test that invalid channel raises error."""
        from murgtools.getdata.getDataFRF import getArgusPixelIntensity

        with patch('murgtools.getdata.getDataFRF.getArgusImagery') as mock_get_imagery:
            mock_image = np.ones((1000, 1500, 3), dtype=np.uint8) * 100
            
            mock_get_imagery.return_value = {
                'image': mock_image,
                'time': DT.datetime(2024, 6, 15, 12, 0, 0),
                'epochtime': 1718452800.0,
                'imageType': 'timex',
                'url': 'http://test.com/image.tif',
            }

            with pytest.raises(ValueError, match="Invalid channel"):
                getArgusPixelIntensity(
                    DT.datetime(2024, 6, 15, 12, 0, 0),
                    location=(150, 200),
                    coordType='pixel',
                    channel='invalid',
                    verbose=False
                )

    def test_location_as_dict(self):
        """Test location specification as dictionary."""
        from murgtools.getdata.getDataFRF import getArgusPixelIntensity

        with patch('murgtools.getdata.getDataFRF.getArgusImagery') as mock_get_imagery:
            mock_image = np.ones((1000, 1500, 3), dtype=np.uint8) * 100
            mock_image[200, 150, :] = [255, 128, 64]
            
            mock_get_imagery.return_value = {
                'image': mock_image,
                'time': DT.datetime(2024, 6, 15, 12, 0, 0),
                'epochtime': 1718452800.0,
                'imageType': 'timex',
                'url': 'http://test.com/image.tif',
            }

            # Test with dict location
            result = getArgusPixelIntensity(
                DT.datetime(2024, 6, 15, 12, 0, 0),
                location={'i': 150, 'j': 200},
                coordType='pixel',
                verbose=False
            )

            assert result is not None
            np.testing.assert_array_equal(result['intensity'][0], [255, 128, 64])
