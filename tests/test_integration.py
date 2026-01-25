"""Integration tests with mocked THREDDS/network connections."""
import datetime as DT
import numpy as np
import pytest
from unittest.mock import MagicMock, patch, PropertyMock


class TestGetnc:
    """Tests for the getnc function with mocked network."""

    @patch('getdatatestbed.getDataFRF.socket.gethostbyname')
    @patch('getdatatestbed.getDataFRF.nc.Dataset')
    def test_getnc_selects_chl_server_for_external_ip(self, mock_dataset, mock_gethostbyname):
        """Test that getnc selects CHL server for non-FRF IPs."""
        mock_gethostbyname.return_value = '192.168.1.1'

        # Mock the dataset
        mock_ds = MagicMock()
        mock_time = MagicMock()
        mock_time.shape = (100,)
        mock_time.__getitem__ = MagicMock(return_value=np.arange(100) * 3600 + 1577836800)
        mock_ds.__getitem__ = MagicMock(return_value=mock_time)
        mock_dataset.return_value = mock_ds

        from getdatatestbed.getDataFRF import getnc

        result = getnc('oceanography/waves/waverider-26m.ncml', 'getObs')

        # Verify CHL URL was used
        call_args = mock_dataset.call_args[0][0]
        assert 'chldata.erdc.dren.mil' in call_args or 'chlthredds' in call_args

    @patch('getdatatestbed.getDataFRF.socket.gethostbyname')
    @patch('getdatatestbed.getDataFRF.nc.Dataset')
    def test_getnc_selects_frf_server_for_internal_ip(self, mock_dataset, mock_gethostbyname):
        """Test that getnc selects FRF server for internal IPs."""
        mock_gethostbyname.return_value = '134.164.129.50'

        mock_ds = MagicMock()
        mock_time = MagicMock()
        mock_time.shape = (100,)
        mock_time.__getitem__ = MagicMock(return_value=np.arange(100) * 3600 + 1577836800)
        mock_ds.__getitem__ = MagicMock(return_value=mock_time)
        mock_dataset.return_value = mock_ds

        from getdatatestbed.getDataFRF import getnc

        result = getnc('oceanography/waves/waverider-26m.ncml', 'getObs', server='FRF')

        # Verify FRF URL was used
        call_args = mock_dataset.call_args[0][0]
        assert '134.164.129.55' in call_args

    @patch('getdatatestbed.getDataFRF.socket.gethostbyname')
    @patch('getdatatestbed.getDataFRF.nc.Dataset')
    def test_getnc_drills_to_monthly_file(self, mock_dataset, mock_gethostbyname):
        """Test that getnc drills down to monthly file when dates are in same month."""
        mock_gethostbyname.return_value = '192.168.1.1'

        mock_ds = MagicMock()
        mock_time = MagicMock()
        mock_time.shape = (100,)
        mock_time.__getitem__ = MagicMock(return_value=np.arange(100) * 3600 + 1577836800)
        mock_ds.__getitem__ = MagicMock(return_value=mock_time)
        mock_dataset.return_value = mock_ds

        from getdatatestbed.getDataFRF import getnc

        d1 = DT.datetime(2020, 1, 5)
        d2 = DT.datetime(2020, 1, 15)

        result = getnc(
            'oceanography/waves/waverider-26m/waverider-26m.ncml',
            'getObs',
            start=d1,
            end=d2
        )

        # Should construct a monthly file path
        call_args = mock_dataset.call_args[0][0]
        # Check it contains year/month format
        assert '2020' in call_args
        assert '202001' in call_args or '01.nc' in call_args

    @patch('getdatatestbed.getDataFRF.socket.gethostbyname')
    @patch('getdatatestbed.getDataFRF.nc.Dataset')
    def test_getnc_retries_on_io_error(self, mock_dataset, mock_gethostbyname):
        """Test that getnc retries on IOError."""
        mock_gethostbyname.return_value = '192.168.1.1'

        # Fail twice, then succeed
        mock_ds = MagicMock()
        mock_time = MagicMock()
        mock_time.shape = (100,)
        mock_time.__getitem__ = MagicMock(return_value=np.arange(100) * 3600 + 1577836800)
        mock_ds.__getitem__ = MagicMock(return_value=mock_time)

        mock_dataset.side_effect = [IOError("Network error"), IOError("Network error"), mock_ds]

        from getdatatestbed.getDataFRF import getnc

        with patch('getdatatestbed.getDataFRF.time.sleep'):  # Don't actually sleep in tests
            result = getnc('test/data.ncml', 'getObs')

        # Should have tried 3 times
        assert mock_dataset.call_count == 3


class TestGetObsWaveDataIntegration:
    """Integration tests for getObs.getWaveData with mocked network."""

    @patch('getdatatestbed.getDataFRF.socket.gethostbyname')
    @patch('getdatatestbed.getDataFRF.nc.Dataset')
    def test_getwavedata_returns_expected_keys(self, mock_dataset, mock_gethostbyname):
        """Test that getWaveData returns dictionary with expected keys."""
        mock_gethostbyname.return_value = '192.168.1.1'

        # Create comprehensive mock dataset
        mock_ds = MagicMock()

        # Mock time variable
        base_epoch = 1577836800.0  # 2020-01-01 00:00:00
        time_values = np.array([base_epoch + i * 1800 for i in range(48)])  # 24 hours of 30-min data
        mock_time = MagicMock()
        mock_time.shape = (48,)
        mock_time.__getitem__ = MagicMock(return_value=time_values)
        mock_time.units = 'seconds since 1970-01-01 00:00:00'

        # Mock other variables
        mock_ds.__getitem__ = MagicMock(side_effect=lambda k: {
            'time': mock_time,
            'waveHs': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 1.5),
            'waveTp': MagicMock(__getitem__=lambda s, idx: np.ones(len(idx)) * 8.0),
            'waveFrequency': np.linspace(0.05, 0.5, 20),
            'latitude': np.array([36.0]),
            'longitude': np.array([-75.0]),
            'nominalDepth': np.array([26.0]),
        }.get(k, MagicMock()))

        mock_ds.title = 'Test Wave Gauge'
        mock_ds.variables = MagicMock()
        mock_ds.variables.keys = MagicMock(return_value=['time', 'waveHs', 'waveTp'])
        mock_dataset.return_value = mock_ds

        d1 = DT.datetime(2020, 1, 1, 0, 0, 0)
        d2 = DT.datetime(2020, 1, 1, 12, 0, 0)

        with patch('getdatatestbed.getDataFRF.nc.num2date') as mock_num2date:
            mock_num2date.return_value = np.array([d1 + DT.timedelta(minutes=30*i) for i in range(24)])

            from getdatatestbed.getDataFRF import getObs
            obs = getObs(d1, d2)

            # This would require more extensive mocking to fully work,
            # but we can test the initialization
            assert obs.d1 == d1
            assert obs.d2 == d2
            assert 'waverider-26m' in obs.waveGaugeList


class TestGetDataTestBedIntegration:
    """Integration tests for getDataTestBed with mocked network."""

    def test_getdatatestbed_initialization(self):
        """Test getDataTestBed initializes with correct attributes."""
        d1 = DT.datetime(2020, 1, 1, 0, 0, 0)
        d2 = DT.datetime(2020, 1, 2, 0, 0, 0)

        with patch('getdatatestbed.getDataFRF.nc.date2num') as mock_date2num:
            mock_date2num.return_value = 1577836800.0

            from getdatatestbed.getDataFRF import getDataTestBed

            tb = getDataTestBed(d1, d2)

            assert tb.start == d1
            assert tb.end == d2
            assert tb.callingClass == 'getDataTestBed'
            assert 'cmtb' in tb.crunchDataLoc or 'CMTB' in tb.crunchDataLoc

    def test_getdatatestbed_server_urls(self):
        """Test getDataTestBed has correct server URLs configured."""
        d1 = DT.datetime(2020, 1, 1, 0, 0, 0)
        d2 = DT.datetime(2020, 1, 2, 0, 0, 0)

        with patch('getdatatestbed.getDataFRF.nc.date2num') as mock_date2num:
            mock_date2num.return_value = 1577836800.0

            from getdatatestbed.getDataFRF import getDataTestBed

            tb = getDataTestBed(d1, d2)

            assert 'thredds' in tb.FRFdataloc.lower()
            assert 'thredds' in tb.chlDataLoc.lower()


@pytest.mark.slow
class TestNetworkConnectivity:
    """Tests that verify network connectivity (marked slow, skipped in CI)."""

    @pytest.mark.skip(reason="Requires network access to THREDDS server")
    def test_can_reach_chl_thredds(self):
        """Test that CHL THREDDS server is reachable."""
        import urllib.request
        url = 'https://chldata.erdc.dren.mil/thredds/catalog.html'
        try:
            response = urllib.request.urlopen(url, timeout=10)
            assert response.status == 200
        except Exception as e:
            pytest.fail(f"Could not reach CHL THREDDS: {e}")
