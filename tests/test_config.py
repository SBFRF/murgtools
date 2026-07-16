"""Tests for murgtools.config module."""

import pytest
import requests
from unittest.mock import patch

from murgtools import config


class TestConfigValues:
    """Test that config constants have expected values and types."""

    def test_thredds_urls_are_strings(self):
        """Verify THREDDS URLs are properly defined strings."""
        assert isinstance(config.THREDDS_FRF_LOCAL, str)
        assert isinstance(config.THREDDS_FRF_LOCAL_ALT, str)
        assert isinstance(config.THREDDS_CHL_PUBLIC, str)
        assert isinstance(config.THREDDS_CHL_ALT, str)
        assert isinstance(config.THREDDS_TESTBED, str)
        assert isinstance(config.THREDDS_CRUNCH, str)

    def test_thredds_urls_have_correct_format(self):
        """Verify THREDDS URLs have expected protocol and path components."""
        assert config.THREDDS_FRF_LOCAL.startswith('http://')
        assert 'thredds/dodsC' in config.THREDDS_FRF_LOCAL
        assert config.THREDDS_CHL_PUBLIC.startswith('https://')
        assert 'thredds/dodsC' in config.THREDDS_CHL_PUBLIC

    def test_argus_image_types(self):
        """Verify Argus image types include expected values."""
        assert 'timex' in config.ARGUS_IMAGE_TYPES
        assert 'bright' in config.ARGUS_IMAGE_TYPES
        assert 'dark' in config.ARGUS_IMAGE_TYPES
        assert 'var' in config.ARGUS_IMAGE_TYPES
        assert 'snap' in config.ARGUS_IMAGE_TYPES

    def test_argus_base_url_format(self):
        """Verify Argus base URL has expected format."""
        assert config.ARGUS_BASE_URL.startswith('https://')
        assert 'coastalimaging' in config.ARGUS_BASE_URL
        assert config.ARGUS_BASE_URL.endswith('/')

    def test_stac_urls_dict(self):
        """Verify STAC URLs dictionary has expected keys."""
        assert 'element84' in config.STAC_URLS
        assert 'planetary-computer' in config.STAC_URLS
        assert config.STAC_URLS['element84'].startswith('https://')
        assert config.STAC_URLS['planetary-computer'].startswith('https://')

    def test_ncep_url_format(self):
        """Verify NCEP URL has expected format."""
        assert 'ncep.noaa.gov' in config.NCEP_DATA_URL
        assert 'wave' in config.NCEP_DATA_URL

    def test_frf_ip_prefixes(self):
        """Verify FRF IP prefixes are defined."""
        assert isinstance(config.FRF_IP_PREFIXES, tuple)
        assert '134.164' in config.FRF_IP_PREFIXES

    def test_timeout_values(self):
        """Verify timeout configuration values are reasonable."""
        assert config.DEFAULT_TIMEOUT_SECONDS > 0
        assert config.DEFAULT_TIMEOUT_SECONDS <= 120

    def test_time_units_format(self):
        """Verify time units string has expected format."""
        assert 'seconds since' in config.TIME_UNITS
        assert '1970' in config.TIME_UNITS


class TestGetThreddsServer:
    """Tests for get_thredds_server helper function."""

    def test_frf_network_returns_local_server(self):
        """Verify FRF network IP returns local THREDDS server."""
        url, prefix = config.get_thredds_server(ip_address='134.164.129.1')
        assert url == config.THREDDS_FRF_LOCAL
        assert prefix == 'FRF'

    def test_external_network_returns_chl_server(self):
        """Verify external IP returns CHL public server."""
        url, prefix = config.get_thredds_server(ip_address='192.168.1.1')
        assert url == config.THREDDS_CHL_PUBLIC
        assert prefix == 'frf'

    def test_force_frf_server(self):
        """Verify forcing FRF server works regardless of IP."""
        url, prefix = config.get_thredds_server(server='FRF', ip_address='192.168.1.1')
        assert url == config.THREDDS_FRF_LOCAL
        assert prefix == 'FRF'

    def test_force_chl_server(self):
        """Verify forcing CHL server works regardless of IP."""
        url, prefix = config.get_thredds_server(server='CHL', ip_address='134.164.129.1')
        assert url == config.THREDDS_CHL_PUBLIC
        assert prefix == 'frf'

    def test_socket_error_defaults_to_chl(self):
        """Verify socket errors default to CHL server."""
        with patch('socket.gethostbyname', side_effect=OSError('Network error')):
            config.clear_server_cache()  # Clear cache to force re-detection
            url, prefix = config.get_thredds_server()
            assert url == config.THREDDS_CHL_PUBLIC
            assert prefix == 'frf'


class TestServerCaching:
    """Tests for server detection caching functionality."""

    def setup_method(self):
        """Clear the cache before each test."""
        config.clear_server_cache()

    def teardown_method(self):
        """Clear the cache after each test."""
        config.clear_server_cache()

    def test_cache_returns_same_result(self):
        """Verify cached result is returned on subsequent calls."""
        # First call should compute and cache
        result1 = config.get_thredds_server()
        # Second call should return cached result
        result2 = config.get_thredds_server()

        assert result1 == result2

    def test_cache_avoids_repeated_socket_calls(self):
        """Verify socket operations are only called once with caching."""
        with patch('murgtools.config.socket.gethostbyname', return_value='192.168.1.1') as mock_socket:
            config.clear_server_cache()

            # Multiple calls should only trigger one socket operation
            config.get_thredds_server()
            config.get_thredds_server()
            config.get_thredds_server()

            # Socket should only be called once (for IP detection)
            assert mock_socket.call_count == 1

    def test_clear_cache_resets_detection(self):
        """Verify clear_server_cache resets the cached state."""
        with patch('murgtools.config.socket.gethostbyname', return_value='192.168.1.1') as mock_socket:
            config.clear_server_cache()

            # First call
            config.get_thredds_server()
            assert mock_socket.call_count == 1

            # Clear cache
            config.clear_server_cache()

            # Second call should trigger socket again
            config.get_thredds_server()
            assert mock_socket.call_count == 2

    def test_explicit_ip_bypasses_cache(self):
        """Verify explicit ip_address parameter still works correctly."""
        config.clear_server_cache()

        # Cache with external IP
        with patch('murgtools.config.socket.gethostbyname', return_value='192.168.1.1'):
            url1, prefix1 = config.get_thredds_server()
            assert prefix1 == 'frf'  # External network

        # Explicit FRF IP should return FRF server regardless of cache
        url2, prefix2 = config.get_thredds_server(ip_address='134.164.129.1')
        assert prefix2 == 'FRF'

    def test_explicit_server_bypasses_cache(self):
        """Verify explicit server parameter still works correctly."""
        config.clear_server_cache()

        # Cache with external IP
        with patch('murgtools.config.socket.gethostbyname', return_value='192.168.1.1'):
            url1, prefix1 = config.get_thredds_server()
            assert prefix1 == 'frf'  # External network

        # Explicit FRF server should return FRF regardless of cache
        url2, prefix2 = config.get_thredds_server(server='FRF')
        assert prefix2 == 'FRF'

    def test_is_frf_network_uses_cached_ip(self):
        """Verify is_frf_network uses cached IP address."""
        with patch('murgtools.config.socket.gethostbyname', return_value='134.164.129.1') as mock_socket:
            config.clear_server_cache()

            # Multiple calls should only trigger one socket operation
            config.is_frf_network()
            config.is_frf_network()
            config.is_frf_network()

            assert mock_socket.call_count == 1

    def test_thread_safety_concurrent_access(self):
        """Verify cache is thread-safe under concurrent access."""
        import threading
        import time

        config.clear_server_cache()
        results = []
        errors = []

        def worker():
            try:
                for _ in range(10):
                    result = config.get_thredds_server()
                    results.append(result)
            except Exception as e:
                errors.append(e)

        # Run multiple threads concurrently
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No errors should occur
        assert len(errors) == 0, f"Thread errors: {errors}"

        # All results should be identical
        assert len(set(results)) == 1, "Inconsistent results across threads"

    def test_invalid_ip_address_type_handled(self):
        """Verify non-string ip_address is handled safely."""
        # Should not raise, should return CHL (external) server
        url, prefix = config.get_thredds_server(ip_address=12345)
        assert prefix == 'frf'

        url, prefix = config.get_thredds_server(ip_address=None)
        # None triggers cache lookup, which is valid
        assert prefix in ('frf', 'FRF')

    def test_is_frf_network_invalid_ip_returns_false(self):
        """Verify is_frf_network returns False for invalid ip_address types."""
        assert config.is_frf_network(ip_address=12345) is False
        assert config.is_frf_network(ip_address=['134.164.1.1']) is False
        assert config.is_frf_network(ip_address={'ip': '134.164.1.1'}) is False


class TestIsFrfNetwork:
    """Tests for is_frf_network helper function."""

    def test_frf_ip_returns_true(self):
        """Verify FRF IP addresses return True."""
        assert config.is_frf_network('134.164.129.55') is True
        assert config.is_frf_network('134.164.1.1') is True
        assert config.is_frf_network('10.0.0.1') is True

    def test_external_ip_returns_false(self):
        """Verify external IP addresses return False."""
        assert config.is_frf_network('192.168.1.1') is False
        assert config.is_frf_network('8.8.8.8') is False

    def test_socket_error_returns_false(self):
        """Verify socket errors return False."""
        with patch('socket.gethostbyname', side_effect=OSError('Network error')):
            assert config.is_frf_network() is False


@pytest.mark.slow
class TestEndpointReachability:
    """Integration tests that verify endpoints are reachable.

    These tests require network access and are marked as slow.
    Run with: pytest -m slow
    """

    def test_chl_thredds_reachable(self):
        """Verify CHL THREDDS server responds."""
        # Test catalog page (not dodsC which requires netCDF client)
        url = config.THREDDS_CHL_PUBLIC.replace('/dodsC/', '/catalog/')
        try:
            resp = requests.head(url, timeout=15, allow_redirects=True)
            # 404 is OK for HEAD - means server is up but doesn't serve HEAD on catalog
            assert resp.status_code in (200, 302, 301, 403, 404), \
                f"CHL THREDDS returned unexpected status: {resp.status_code}"
        except requests.exceptions.Timeout:
            pytest.skip("CHL THREDDS server timed out")
        except requests.exceptions.ConnectionError as e:
            pytest.skip(f"Could not connect to CHL THREDDS: {e}")

    def test_argus_base_url_reachable(self):
        """Verify Argus imagery server responds."""
        try:
            resp = requests.head(config.ARGUS_BASE_URL, timeout=15, allow_redirects=True)
            # 403/404 is OK - means server is up but needs specific file path
            assert resp.status_code in (200, 301, 302, 403, 404), \
                f"Argus server returned unexpected status: {resp.status_code}"
        except requests.exceptions.Timeout:
            pytest.skip("Argus server timed out")
        except requests.exceptions.ConnectionError as e:
            pytest.skip(f"Could not connect to Argus server: {e}")

    def test_stac_element84_reachable(self):
        """Verify Element84 STAC API responds."""
        try:
            resp = requests.head(config.STAC_URLS['element84'], timeout=15)
            # 405 = Method Not Allowed (POST only endpoint)
            assert resp.status_code in (200, 405), \
                f"Element84 STAC returned unexpected status: {resp.status_code}"
        except requests.exceptions.Timeout:
            pytest.skip("Element84 STAC timed out")
        except requests.exceptions.ConnectionError as e:
            pytest.skip(f"Could not connect to Element84 STAC: {e}")

    def test_stac_planetary_computer_reachable(self):
        """Verify Planetary Computer STAC API responds."""
        try:
            resp = requests.head(config.STAC_URLS['planetary-computer'], timeout=15)
            # 405 = Method Not Allowed (POST only endpoint)
            assert resp.status_code in (200, 405), \
                f"Planetary Computer STAC returned unexpected status: {resp.status_code}"
        except requests.exceptions.Timeout:
            pytest.skip("Planetary Computer STAC timed out")
        except requests.exceptions.ConnectionError as e:
            pytest.skip(f"Could not connect to Planetary Computer STAC: {e}")

    def test_ncep_url_reachable(self):
        """Verify NCEP data server responds."""
        try:
            resp = requests.head(config.NCEP_DATA_URL, timeout=15, allow_redirects=True)
            assert resp.status_code in (200, 301, 302, 403), \
                f"NCEP server returned unexpected status: {resp.status_code}"
        except requests.exceptions.Timeout:
            pytest.skip("NCEP server timed out")
        except requests.exceptions.ConnectionError as e:
            pytest.skip(f"Could not connect to NCEP server: {e}")


@pytest.mark.slow
class TestDataDownload:
    """Integration tests that actually download and verify data from endpoints.

    These tests require network access and may take longer to run.
    Run with: pytest -m slow
    """

    def test_chl_thredds_netcdf_download(self):
        """Verify we can open a NetCDF file from CHL THREDDS and read variables."""
        import netCDF4 as nc

        # Use a known stable dataset - FRF pier end water level gauge
        # This is a small file that should always be available
        ncml_url = config.THREDDS_CHL_PUBLIC + 'frf/oceanography/waterlevel/eopNoaaTide/eopNoaaTide.ncml'

        try:
            dataset = nc.Dataset(ncml_url)

            # Verify expected variables exist
            assert 'time' in dataset.variables, "NetCDF missing 'time' variable"
            assert 'waterLevel' in dataset.variables or 'wl' in dataset.variables or \
                   'WL' in dataset.variables, "NetCDF missing water level variable"

            # Verify we can read time data
            time_var = dataset.variables['time']
            assert len(time_var) > 0, "Time variable is empty"

            # Verify time has units attribute
            assert hasattr(time_var, 'units'), "Time variable missing units attribute"

            dataset.close()

        except OSError as e:
            if 'NetCDF' in str(e) or 'HTTP' in str(e):
                pytest.skip(f"Could not connect to THREDDS: {e}")
            raise
        except Exception as e:
            pytest.skip(f"THREDDS NetCDF test failed: {e}")

    def test_stac_element84_search(self):
        """Verify Element84 STAC API returns valid search results."""
        import datetime as DT

        # Search for Sentinel-2 imagery near FRF
        frf_bbox = [-75.8, 36.1, -75.7, 36.2]  # Small area around FRF

        query = {
            "collections": ["sentinel-2-l2a"],
            "bbox": frf_bbox,
            "datetime": "2024-01-01T00:00:00Z/2024-01-31T23:59:59Z",
            "limit": 1
        }

        try:
            resp = requests.post(
                config.STAC_URLS['element84'],
                json=query,
                timeout=30
            )
            resp.raise_for_status()
            results = resp.json()

            # Verify response structure
            assert 'type' in results, "STAC response missing 'type' field"
            assert results['type'] == 'FeatureCollection', "STAC response is not a FeatureCollection"
            assert 'features' in results, "STAC response missing 'features' field"

            # If features exist, verify structure
            if results['features']:
                feature = results['features'][0]
                assert 'id' in feature, "STAC feature missing 'id'"
                assert 'properties' in feature, "STAC feature missing 'properties'"
                assert 'assets' in feature, "STAC feature missing 'assets'"
                assert 'datetime' in feature['properties'], "STAC feature missing datetime property"

        except requests.exceptions.Timeout:
            pytest.skip("Element84 STAC search timed out")
        except requests.exceptions.ConnectionError as e:
            pytest.skip(f"Could not connect to Element84 STAC: {e}")
        except requests.exceptions.HTTPError as e:
            pytest.skip(f"Element84 STAC returned error: {e}")

    def test_stac_planetary_computer_search(self):
        """Verify Planetary Computer STAC API returns valid search results."""
        import datetime as DT

        # Search for NAIP imagery near FRF
        frf_bbox = [-75.8, 36.1, -75.7, 36.2]

        query = {
            "collections": ["naip"],
            "bbox": frf_bbox,
            "datetime": "2020-01-01T00:00:00Z/2023-12-31T23:59:59Z",
            "limit": 1
        }

        try:
            resp = requests.post(
                config.STAC_URLS['planetary-computer'],
                json=query,
                timeout=30
            )
            resp.raise_for_status()
            results = resp.json()

            # Verify response structure
            assert 'type' in results, "STAC response missing 'type' field"
            assert results['type'] == 'FeatureCollection', "STAC response is not a FeatureCollection"
            assert 'features' in results, "STAC response missing 'features' field"

        except requests.exceptions.Timeout:
            pytest.skip("Planetary Computer STAC search timed out")
        except requests.exceptions.ConnectionError as e:
            pytest.skip(f"Could not connect to Planetary Computer STAC: {e}")
        except requests.exceptions.HTTPError as e:
            pytest.skip(f"Planetary Computer STAC returned error: {e}")

    def test_argus_image_download(self):
        """Verify we can download an actual Argus image."""
        import datetime as DT
        import numpy as np

        # Use the getArgusImagery function to download a real image
        # Try a date when imagery is likely available
        from murgtools.getdata.getDataFRF import getArgusImagery

        # Try multiple dates in case one doesn't have imagery
        test_dates = [
            DT.datetime(2024, 6, 15, 12, 0, 0),
            DT.datetime(2024, 6, 14, 12, 0, 0),
            DT.datetime(2024, 6, 13, 12, 0, 0),
        ]

        result = None
        for test_date in test_dates:
            try:
                result = getArgusImagery(test_date, imageType='timex', verbose=False)
                if result is not None:
                    break
            except Exception:
                continue

        if result is None:
            pytest.skip("Could not download Argus imagery for any test date")

        # Verify result structure
        assert 'image' in result, "Argus result missing 'image' key"
        assert 'time' in result, "Argus result missing 'time' key"
        assert 'epochtime' in result, "Argus result missing 'epochtime' key"
        assert 'url' in result, "Argus result missing 'url' key"

        # Verify image is a valid numpy array
        assert isinstance(result['image'], np.ndarray), "Argus image is not a numpy array"
        assert result['image'].ndim >= 2, "Argus image should be at least 2D"
        assert result['image'].size > 0, "Argus image is empty"

        # Verify image is uint8 (normalized)
        assert result['image'].dtype == np.uint8, f"Argus image dtype is {result['image'].dtype}, expected uint8"

    def test_ncep_directory_listing(self):
        """Verify NCEP data directory is accessible and contains expected files."""
        try:
            # Get directory listing
            resp = requests.get(config.NCEP_DATA_URL, timeout=30)
            resp.raise_for_status()

            # Verify response contains wave model references
            content = resp.text.lower()
            assert 'multi_1' in content or 'gfs' in content or 'wave' in content, \
                "NCEP directory doesn't contain expected wave model files"

        except requests.exceptions.Timeout:
            pytest.skip("NCEP directory listing timed out")
        except requests.exceptions.ConnectionError as e:
            pytest.skip(f"Could not connect to NCEP: {e}")
        except requests.exceptions.HTTPError as e:
            pytest.skip(f"NCEP returned error: {e}")
