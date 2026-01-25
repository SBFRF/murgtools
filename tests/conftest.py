"""Pytest configuration and fixtures for getdatatestbed tests."""
import datetime as DT
import numpy as np
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def sample_datetime_range():
    """Provide a sample datetime range for testing."""
    d1 = DT.datetime(2020, 1, 1, 0, 0, 0)
    d2 = DT.datetime(2020, 1, 2, 0, 0, 0)
    return d1, d2


@pytest.fixture
def sample_epoch_array():
    """Provide sample epoch time array for testing."""
    # Epoch times for Jan 1, 2020 00:00 to Jan 2, 2020 00:00 (hourly)
    start_epoch = 1577836800.0  # 2020-01-01 00:00:00 UTC
    return np.array([start_epoch + i * 3600 for i in range(25)])


@pytest.fixture
def sample_wave_dict():
    """Provide sample wave data dictionary for testing."""
    return {
        'name': 'test_gauge',
        'epochtime': np.array([1577836800.0, 1577840400.0, 1577844000.0, 1577847600.0]),
        'time': np.array([
            DT.datetime(2020, 1, 1, 0, 0, 0),
            DT.datetime(2020, 1, 1, 1, 0, 0),
            DT.datetime(2020, 1, 1, 2, 0, 0),
            DT.datetime(2020, 1, 1, 3, 0, 0),
        ]),
        'Hs': np.array([1.5, 1.6, 1.7, 1.8]),
        'xFRF': 500.0,
        'yFRF': 100.0,
    }


@pytest.fixture
def sample_dict_with_duplicates():
    """Provide sample dictionary with duplicate times for testing."""
    return {
        'name': 'test_gauge',
        'epochtime': np.array([1577836800.0, 1577840400.0, 1577840400.0, 1577847600.0]),
        'Hs': np.array([1.5, 1.6, 1.7, 1.8]),
    }


@pytest.fixture
def mock_netcdf_dataset():
    """Mock netCDF4.Dataset for testing without network access."""
    mock_ds = MagicMock()
    mock_ds.__getitem__ = MagicMock(return_value=MagicMock())
    mock_ds.variables = {'time': MagicMock(), 'waveHs': MagicMock()}
    return mock_ds
