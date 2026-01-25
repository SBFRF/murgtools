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
