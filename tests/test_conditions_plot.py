"""Unit tests for conditions_plot module."""
import datetime as dt
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from murgtools.plotting.conditions_plot import bin_data, conditions_plot


class TestBinData:
    """Tests for the bin_data function."""

    def test_bin_data_basic(self):
        """Test basic binning functionality."""
        data = np.array([0.5, 1.0, 1.5, 2.0, 2.5])
        bin_indices, bins = bin_data(data, bin_size=0.5)
        
        assert len(bins) > 0
        assert len(bin_indices) == len(data)
        # Indices should be 0-based (Python standard)
        assert np.all(bin_indices >= 0)
        assert np.all(bin_indices < len(bins) - 1)

    def test_bin_data_uniform_values(self):
        """Test binning with uniform values."""
        data = np.array([1.0, 1.0, 1.0, 1.0])
        bin_indices, bins = bin_data(data, bin_size=0.5)
        
        # All should be in same bin
        assert len(np.unique(bin_indices)) == 1

    def test_bin_data_with_nans(self):
        """Test binning with NaN values."""
        data = np.array([0.5, np.nan, 1.5, 2.0])
        bin_indices, bins = bin_data(data, bin_size=0.5)
        
        # Should handle NaN values
        assert len(bins) > 0
        assert len(bin_indices) == len(data)

    def test_bin_data_custom_bin_size(self):
        """Test binning with custom bin size."""
        data = np.array([0.0, 0.1, 0.2, 0.3, 0.4])
        bin_indices, bins = bin_data(data, bin_size=0.1)
        
        assert len(bins) > 0
        # Bin edges should be approximately bin_size apart
        if len(bins) > 1:
            assert np.allclose(np.diff(bins), 0.1)


class TestConditionsPlot:
    """Tests for the conditions_plot function."""

    @pytest.fixture
    def mock_wave_data(self):
        """Create mock wave data for testing."""
        times = [dt.datetime(2023, 6, 15, h, 0) for h in range(24)]
        return {
            'time': np.array(times),
            'Hs': np.array([1.0 + 0.1 * i for i in range(24)]),
            'peakf': np.array([0.1 + 0.01 * i for i in range(24)]),
            'waveDirectionPeak': np.array([180.0 + i for i in range(24)]),
        }

    @patch('murgtools.plotting.conditions_plot.getObs')
    @patch('murgtools.plotting.conditions_plot.plt.savefig')
    def test_conditions_plot_basic(self, mock_savefig, mock_getObs, mock_wave_data):
        """Test basic conditions plot creation."""
        # Setup mock
        mock_obs = MagicMock()
        mock_obs.getWaveData.return_value = mock_wave_data
        mock_getObs.return_value = mock_obs

        # Create plot
        time_list = [dt.datetime(2023, 6, 15)]
        start_date = dt.datetime(2023, 6, 1)
        end_date = dt.datetime(2023, 6, 30)
        
        fig, axes = conditions_plot(time_list, start_date, end_date)
        
        # Verify
        assert fig is not None
        assert len(axes) == 2
        mock_obs.getWaveData.assert_called_once()

    @patch('murgtools.plotting.conditions_plot.getObs')
    @patch('murgtools.plotting.conditions_plot.plt.savefig')
    def test_conditions_plot_with_date_string(self, mock_savefig, mock_getObs, mock_wave_data):
        """Test conditions plot with date strings."""
        # Setup mock
        mock_obs = MagicMock()
        mock_obs.getWaveData.return_value = mock_wave_data
        mock_getObs.return_value = mock_obs

        # Create plot with date strings
        time_list = ['20230615']
        start_date = '20230601'
        end_date = '20230630'
        
        fig, axes = conditions_plot(time_list, start_date, end_date)
        
        assert fig is not None
        assert len(axes) == 2

    @patch('murgtools.plotting.conditions_plot.getObs')
    @patch('murgtools.plotting.conditions_plot.plt.savefig')
    def test_conditions_plot_with_groups(self, mock_savefig, mock_getObs, mock_wave_data):
        """Test conditions plot with multiple date groups."""
        # Setup mock
        mock_obs = MagicMock()
        mock_obs.getWaveData.return_value = mock_wave_data
        mock_getObs.return_value = mock_obs

        # Create plot with groups
        date_groups = [
            {
                'dates': [dt.datetime(2023, 6, 15)],
                'label': 'Survey A',
                'color': 'blue',
                'marker': 'o'
            },
            {
                'dates': [dt.datetime(2023, 6, 20)],
                'label': 'Survey B',
                'color': 'red',
                'marker': 's'
            }
        ]
        time_list = [dt.datetime(2023, 6, 15), dt.datetime(2023, 6, 20)]
        start_date = dt.datetime(2023, 6, 1)
        end_date = dt.datetime(2023, 6, 30)
        
        fig, axes = conditions_plot(time_list, start_date, end_date, date_groups=date_groups)
        
        assert fig is not None
        assert len(axes) == 2

    @patch('murgtools.plotting.conditions_plot.getObs')
    def test_conditions_plot_tp_computation(self, mock_getObs, mock_wave_data):
        """Test that Tp is computed from peakf when not present."""
        # Setup mock
        mock_obs = MagicMock()
        mock_obs.getWaveData.return_value = mock_wave_data
        mock_getObs.return_value = mock_obs

        # Create plot requesting Tp
        time_list = [dt.datetime(2023, 6, 15)]
        start_date = dt.datetime(2023, 6, 1)
        end_date = dt.datetime(2023, 6, 30)
        
        fig, axes = conditions_plot(time_list, start_date, end_date, y_var='Tp')
        
        assert fig is not None
        # Tp should have been computed
        call_args = mock_obs.getWaveData.call_args
        assert call_args is not None

    @patch('murgtools.plotting.conditions_plot.getObs')
    def test_conditions_plot_missing_variable(self, mock_getObs, mock_wave_data):
        """Test error handling for missing variables."""
        # Setup mock
        mock_obs = MagicMock()
        mock_obs.getWaveData.return_value = mock_wave_data
        mock_getObs.return_value = mock_obs

        # Try to plot with non-existent variable
        time_list = [dt.datetime(2023, 6, 15)]
        start_date = dt.datetime(2023, 6, 1)
        end_date = dt.datetime(2023, 6, 30)
        
        with pytest.raises(ValueError, match="not found in wave data"):
            conditions_plot(time_list, start_date, end_date, x_var='NonExistentVar')

    @patch('murgtools.plotting.conditions_plot.getObs')
    @patch('murgtools.plotting.conditions_plot.plt.savefig')
    def test_conditions_plot_custom_limits(self, mock_savefig, mock_getObs, mock_wave_data):
        """Test conditions plot with custom axis limits."""
        # Setup mock
        mock_obs = MagicMock()
        mock_obs.getWaveData.return_value = mock_wave_data
        mock_getObs.return_value = mock_obs

        # Create plot with custom limits
        time_list = [dt.datetime(2023, 6, 15)]
        start_date = dt.datetime(2023, 6, 1)
        end_date = dt.datetime(2023, 6, 30)
        
        fig, axes = conditions_plot(
            time_list, start_date, end_date,
            x_limits=[0, 3],
            y_limits=[5, 15]
        )
        
        assert fig is not None
        assert axes[1].get_xlim() == (0, 3)
        assert axes[1].get_ylim() == (5, 15)

    @patch('murgtools.plotting.conditions_plot.getObs')
    @patch('murgtools.plotting.conditions_plot.plt.savefig')
    def test_conditions_plot_save_file(self, mock_savefig, mock_getObs, mock_wave_data):
        """Test that plot is saved when ofname is provided."""
        # Setup mock
        mock_obs = MagicMock()
        mock_obs.getWaveData.return_value = mock_wave_data
        mock_getObs.return_value = mock_obs

        # Create plot with output filename
        time_list = [dt.datetime(2023, 6, 15)]
        start_date = dt.datetime(2023, 6, 1)
        end_date = dt.datetime(2023, 6, 30)
        
        _, _ = conditions_plot(time_list, start_date, end_date, ofname='test_output.png')
        
        # Verify savefig was called
        mock_savefig.assert_called_once()
        call_args = mock_savefig.call_args
        assert 'test_output.png' in str(call_args)


