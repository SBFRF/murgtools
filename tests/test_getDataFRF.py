"""Unit tests for getDataFRF module."""
import datetime as DT
import numpy as np
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import sys

# Create proper mock for testbedutils before importing getDataFRF
class MockSblib:
    """Mock for testbedutils.sblib module."""
    @staticmethod
    def baseRound(x, base):
        return np.round(np.array(x) / base) * base

    @staticmethod
    def reduceDict(d, idx):
        result = {}
        for k, v in d.items():
            if hasattr(v, '__getitem__') and not isinstance(v, str):
                try:
                    result[k] = v[idx]
                except (IndexError, TypeError):
                    result[k] = v
            else:
                result[k] = v
        return result


class MockGeoprocess:
    """Mock for testbedutils.geoprocess module."""
    @staticmethod
    def FRFcoord(lon, lat):
        return {'xFRF': 500.0, 'yFRF': 100.0}


# Setup mocks before importing
mock_testbedutils = MagicMock()
mock_testbedutils.sblib = MockSblib()
mock_testbedutils.geoprocess = MockGeoprocess()

sys.modules['testbedutils'] = mock_testbedutils
sys.modules['testbedutils.sblib'] = MockSblib()
sys.modules['testbedutils.geoprocess'] = MockGeoprocess()

from getDataFRF import gettime, removeDuplicatesFromDictionary


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
        # Should return indices 5, 6, 7, 8, 9 (hour 10 is exclusive)
        expected = np.array([5, 6, 7, 8, 9])
        np.testing.assert_array_equal(result, expected)

    def test_gettime_returns_none_for_empty_range(self, sample_epoch_array):
        """Test that gettime returns None when no data in range."""
        # Search for times way in the future
        epoch_start = 1600000000.0
        epoch_end = 1600100000.0

        result = gettime(sample_epoch_array, epoch_start, epoch_end)

        assert result is None

    def test_gettime_handles_none_input(self):
        """Test that gettime handles None epoch array."""
        result = gettime(None, 1577836800.0, 1577840400.0)
        assert result is None

    def test_gettime_with_index_reference(self, sample_epoch_array):
        """Test gettime with non-zero indexRef."""
        start_epoch = 1577836800.0
        epoch_start = start_epoch + 2 * 3600
        epoch_end = start_epoch + 5 * 3600
        index_ref = 100

        result = gettime(sample_epoch_array, epoch_start, epoch_end, indexRef=index_ref)

        # Should return indices 102, 103, 104 (original 2,3,4 plus offset)
        expected = np.array([102, 103, 104])
        np.testing.assert_array_equal(result, expected)

    def test_gettime_single_match(self):
        """Test gettime when only one time matches."""
        epochs = np.array([100.0, 200.0, 300.0, 400.0])
        result = gettime(epochs, 150.0, 250.0)

        # Should return index 1 (value 200)
        assert result == 1


class TestRemoveDuplicatesFromDictionary:
    """Tests for the removeDuplicatesFromDictionary function."""

    def test_removes_duplicates_from_epochtime(self):
        """Test that duplicates are removed based on epochtime key."""
        input_dict = {
            'name': 'test_gauge',
            'epochtime': np.array([1577836800.0, 1577840400.0, 1577840400.0, 1577847600.0]),
            'Hs': np.array([1.5, 1.6, 1.7, 1.8]),
        }
        result = removeDuplicatesFromDictionary(input_dict)

        # Should have 3 unique times instead of 4
        assert len(result['epochtime']) == 3
        assert len(result['Hs']) == 3
        # First occurrence of duplicate should be kept (indices 0, 1, 3)
        np.testing.assert_array_equal(
            result['epochtime'],
            np.array([1577836800.0, 1577840400.0, 1577847600.0])
        )

    def test_no_change_when_no_duplicates(self):
        """Test that dict without duplicates is unchanged."""
        input_dict = {
            'name': 'test_gauge',
            'epochtime': np.array([1577836800.0, 1577840400.0, 1577844000.0, 1577847600.0]),
            'Hs': np.array([1.5, 1.6, 1.7, 1.8]),
        }
        original_length = len(input_dict['epochtime'])
        result = removeDuplicatesFromDictionary(input_dict)

        assert len(result['epochtime']) == original_length

    def test_handles_none_input(self):
        """Test that None input returns None."""
        result = removeDuplicatesFromDictionary(None)
        assert result is None

    def test_raises_on_missing_time_key(self):
        """Test that missing time key raises NotImplementedError."""
        bad_dict = {'name': 'test', 'data': [1, 2, 3]}

        with pytest.raises(NotImplementedError):
            removeDuplicatesFromDictionary(bad_dict)

    def test_uses_time_key_when_no_epochtime(self):
        """Test fallback to 'time' key when 'epochtime' not present."""
        dict_with_time = {
            'name': 'test',
            'time': np.array([1.0, 2.0, 2.0, 3.0]),
            'data': np.array([10, 20, 30, 40]),
        }

        with pytest.warns(UserWarning):
            result = removeDuplicatesFromDictionary(dict_with_time)

        assert len(result['time']) == 3


class TestGetObsClass:
    """Tests for the getObs class initialization and methods."""

    def test_getobs_init_with_valid_dates(self, sample_datetime_range):
        """Test getObs initialization with valid datetime range."""
        d1, d2 = sample_datetime_range

        with patch('getDataFRF.nc') as mock_nc:
            mock_nc.date2num = MagicMock(return_value=1577836800.0)
            from getDataFRF import getObs

            obs = getObs(d1, d2)

            assert obs.d1 == d1
            assert obs.d2 == d2
            assert obs.callingClass == 'getObs'

    def test_getobs_raises_on_reversed_dates(self):
        """Test that getObs raises assertion when d2 < d1."""
        d1 = DT.datetime(2020, 1, 2)
        d2 = DT.datetime(2020, 1, 1)

        with patch('getDataFRF.nc') as mock_nc:
            mock_nc.date2num = MagicMock(return_value=1577836800.0)
            from getDataFRF import getObs

            with pytest.raises(AssertionError):
                getObs(d1, d2)

    def test_getobs_wave_gauge_list(self, sample_datetime_range):
        """Test that getObs has expected wave gauge list."""
        d1, d2 = sample_datetime_range

        with patch('getDataFRF.nc') as mock_nc:
            mock_nc.date2num = MagicMock(return_value=1577836800.0)
            from getDataFRF import getObs

            obs = getObs(d1, d2)

            assert 'waverider-26m' in obs.waveGaugeList
            assert '8m-array' in obs.waveGaugeList
            assert len(obs.waveGaugeList) == 10


class TestGetDataTestBedClass:
    """Tests for the getDataTestBed class initialization."""

    def test_getdatatestbed_init_with_valid_dates(self, sample_datetime_range):
        """Test getDataTestBed initialization with valid datetime range."""
        d1, d2 = sample_datetime_range

        with patch('getDataFRF.nc') as mock_nc:
            mock_nc.date2num = MagicMock(return_value=1577836800.0)
            from getDataFRF import getDataTestBed

            tb = getDataTestBed(d1, d2)

            assert tb.start == d1
            assert tb.end == d2
            assert tb.callingClass == 'getDataTestBed'

    def test_getdatatestbed_raises_on_non_datetime(self):
        """Test that getDataTestBed raises on non-datetime input."""
        with patch('getDataFRF.nc') as mock_nc:
            mock_nc.date2num = MagicMock(return_value=1577836800.0)
            from getDataFRF import getDataTestBed

            with pytest.raises(AssertionError):
                getDataTestBed("2020-01-01", "2020-01-02")
