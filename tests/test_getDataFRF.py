"""Unit tests for getDataFRF module."""
import datetime as DT
import numpy as np
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from murgtools.getdata.getDataFRF import gettime, removeDuplicatesFromDictionary


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

        valid_types = ['timex', 'var', 'snap', 'brightest', 'darkest']
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
