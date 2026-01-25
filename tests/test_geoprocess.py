"""Tests for geoprocess coordinate transformation functions.

Tests cover single point and array conversions for all coordinate systems:
- FRF local coordinates
- NC State Plane (EPSG:3358)
- Lat/Lon (WGS84)
- UTM
"""
import numpy as np
import pytest

from getdatatestbed.testbedutils import geoprocess as gp


# Reference test point from docstrings (south rail at 1860)
REF_FRF_X = 566.93
REF_FRF_Y = 515.11
REF_SP_E = 902307.92
REF_SP_N = 274771.22
REF_LAT = 36.1836000
REF_LON = -75.7454804

# Tolerance for coordinate comparisons (meters for FRF/SP, degrees for lat/lon)
TOLERANCE_METERS = 1.0  # 1 meter tolerance
TOLERANCE_DEGREES = 0.0001  # ~11 meters at this latitude


class TestFRF2ncsp:
    """Tests for FRF to NC State Plane conversion."""

    def test_single_point(self):
        """Test conversion of a single FRF point to state plane."""
        result = gp.FRF2ncsp(REF_FRF_X, REF_FRF_Y)

        assert 'StateplaneE' in result
        assert 'StateplaneN' in result
        assert 'xFRF' in result
        assert 'yFRF' in result
        assert abs(result['StateplaneE'] - REF_SP_E) < TOLERANCE_METERS
        assert abs(result['StateplaneN'] - REF_SP_N) < TOLERANCE_METERS

    def test_array_of_points(self):
        """Test conversion of arrays of FRF points to state plane."""
        x_arr = np.array([0.0, 100.0, 200.0, REF_FRF_X])
        y_arr = np.array([0.0, 100.0, 200.0, REF_FRF_Y])

        result = gp.FRF2ncsp(x_arr, y_arr)

        assert isinstance(result['StateplaneE'], np.ndarray)
        assert isinstance(result['StateplaneN'], np.ndarray)
        assert len(result['StateplaneE']) == 4
        assert len(result['StateplaneN']) == 4
        # Check last point matches reference
        assert abs(result['StateplaneE'][-1] - REF_SP_E) < TOLERANCE_METERS
        assert abs(result['StateplaneN'][-1] - REF_SP_N) < TOLERANCE_METERS

    def test_origin_point(self):
        """Test that FRF origin (0,0) converts to known state plane origin."""
        result = gp.FRF2ncsp(0.0, 0.0)

        # FRF origin in state plane coordinates
        expected_e = 901951.6805
        expected_n = 274093.1562
        assert abs(result['StateplaneE'] - expected_e) < 0.01
        assert abs(result['StateplaneN'] - expected_n) < 0.01


class TestNcsp2FRF:
    """Tests for NC State Plane to FRF conversion."""

    def test_single_point(self):
        """Test conversion of a single state plane point to FRF."""
        result = gp.ncsp2FRF(REF_SP_E, REF_SP_N)

        assert 'xFRF' in result
        assert 'yFRF' in result
        assert abs(result['xFRF'] - REF_FRF_X) < TOLERANCE_METERS
        assert abs(result['yFRF'] - REF_FRF_Y) < TOLERANCE_METERS

    def test_array_of_points(self):
        """Test conversion of arrays of state plane points to FRF."""
        e_arr = np.array([901951.6805, 902000.0, 902100.0, REF_SP_E])
        n_arr = np.array([274093.1562, 274100.0, 274200.0, REF_SP_N])

        result = gp.ncsp2FRF(e_arr, n_arr)

        assert isinstance(result['xFRF'], np.ndarray)
        assert isinstance(result['yFRF'], np.ndarray)
        assert len(result['xFRF']) == 4
        # Check last point matches reference
        assert abs(result['xFRF'][-1] - REF_FRF_X) < TOLERANCE_METERS
        assert abs(result['yFRF'][-1] - REF_FRF_Y) < TOLERANCE_METERS

    def test_origin_point(self):
        """Test that state plane origin converts to FRF origin (0,0)."""
        result = gp.ncsp2FRF(901951.6805, 274093.1562)

        assert abs(result['xFRF']) < 0.01
        assert abs(result['yFRF']) < 0.01


class TestNcsp2LatLon:
    """Tests for NC State Plane to Lat/Lon conversion."""

    def test_single_point(self):
        """Test conversion of a single state plane point to lat/lon."""
        result = gp.ncsp2LatLon(REF_SP_E, REF_SP_N)

        assert 'lat' in result
        assert 'lon' in result
        assert abs(result['lat'] - REF_LAT) < TOLERANCE_DEGREES
        assert abs(result['lon'] - REF_LON) < TOLERANCE_DEGREES

    def test_array_of_points(self):
        """Test conversion of arrays of state plane points to lat/lon."""
        e_arr = np.array([901926.2, 902307.92, 902500.0])
        n_arr = np.array([273871.0, 274771.22, 275000.0])

        result = gp.ncsp2LatLon(e_arr, n_arr)

        assert isinstance(result['lat'], np.ndarray)
        assert isinstance(result['lon'], np.ndarray)
        assert len(result['lat']) == 3
        assert len(result['lon']) == 3
        # All points should be in the FRF area
        assert all(result['lat'] > 36.0)
        assert all(result['lat'] < 37.0)
        assert all(result['lon'] < -75.0)
        assert all(result['lon'] > -76.0)

    def test_known_reference_point(self):
        """Test against known reference from SMS modeling system."""
        # From docstring: spE1 = 901926.2, spN1 = 273871.0 -> Lat1 = 36.17560399, Lon1 = -75.75004989
        result = gp.ncsp2LatLon(901926.2, 273871.0)

        assert abs(result['lat'] - 36.17560399) < TOLERANCE_DEGREES
        assert abs(result['lon'] - (-75.75004989)) < TOLERANCE_DEGREES


class TestLatLon2ncsp:
    """Tests for Lat/Lon to NC State Plane conversion."""

    def test_single_point(self):
        """Test conversion of a single lat/lon point to state plane."""
        result = gp.LatLon2ncsp(REF_LON, REF_LAT)

        assert 'StateplaneE' in result
        assert 'StateplaneN' in result
        assert abs(result['StateplaneE'] - REF_SP_E) < TOLERANCE_METERS
        assert abs(result['StateplaneN'] - REF_SP_N) < TOLERANCE_METERS

    def test_array_of_points(self):
        """Test conversion of arrays of lat/lon points to state plane."""
        lon_arr = np.array([-75.75004989, -75.7454804, -75.74])
        lat_arr = np.array([36.17560399, 36.1836000, 36.19])

        result = gp.LatLon2ncsp(lon_arr, lat_arr)

        assert isinstance(result['StateplaneE'], np.ndarray)
        assert isinstance(result['StateplaneN'], np.ndarray)
        assert len(result['StateplaneE']) == 3
        # All points should be in valid state plane range
        assert all(result['StateplaneE'] > 800000)
        assert all(result['StateplaneN'] > 200000)

    def test_known_reference_point(self):
        """Test against known reference from SMS modeling system."""
        # From docstring: Lon1 = -75.75004989, Lat1 = 36.17560399 -> spE1 = 901926.2, spN1 = 273871.0
        result = gp.LatLon2ncsp(-75.75004989, 36.17560399)

        assert abs(result['StateplaneE'] - 901926.2) < TOLERANCE_METERS
        assert abs(result['StateplaneN'] - 273871.0) < TOLERANCE_METERS


class TestFRFcoord:
    """Tests for the universal FRFcoord converter."""

    def test_frf_input_single(self):
        """Test FRFcoord with FRF coordinate input."""
        result = gp.FRFcoord(REF_FRF_X, REF_FRF_Y)

        assert 'xFRF' in result
        assert 'yFRF' in result
        assert 'StateplaneE' in result
        assert 'StateplaneN' in result
        assert 'Lat' in result
        assert 'Lon' in result
        assert abs(result['StateplaneE'] - REF_SP_E) < TOLERANCE_METERS
        assert abs(result['Lat'] - REF_LAT) < TOLERANCE_DEGREES

    def test_frf_input_array(self):
        """Test FRFcoord with arrays of FRF coordinates."""
        x_arr = np.array([100.0, 200.0, REF_FRF_X])
        y_arr = np.array([100.0, 200.0, REF_FRF_Y])

        result = gp.FRFcoord(x_arr, y_arr)

        assert isinstance(result['StateplaneE'], np.ndarray)
        assert isinstance(result['Lat'], np.ndarray)
        assert len(result['StateplaneE']) == 3

    def test_stateplane_input_single(self):
        """Test FRFcoord with state plane coordinate input."""
        result = gp.FRFcoord(REF_SP_E, REF_SP_N)

        assert abs(result['xFRF'] - REF_FRF_X) < TOLERANCE_METERS
        assert abs(result['yFRF'] - REF_FRF_Y) < TOLERANCE_METERS

    def test_stateplane_input_array(self):
        """Test FRFcoord with arrays of state plane coordinates."""
        e_arr = np.array([901951.6805, 902100.0, REF_SP_E])
        n_arr = np.array([274093.1562, 274300.0, REF_SP_N])

        result = gp.FRFcoord(e_arr, n_arr)

        assert isinstance(result['xFRF'], np.ndarray)
        assert len(result['xFRF']) == 3

    def test_latlon_input_single(self):
        """Test FRFcoord with lat/lon coordinate input."""
        result = gp.FRFcoord(REF_LON, REF_LAT)

        assert abs(result['xFRF'] - REF_FRF_X) < TOLERANCE_METERS
        assert abs(result['StateplaneE'] - REF_SP_E) < TOLERANCE_METERS

    def test_latlon_input_array(self):
        """Test FRFcoord with arrays of lat/lon coordinates."""
        lon_arr = np.array([-75.75, -75.74, REF_LON])
        lat_arr = np.array([36.17, 36.18, REF_LAT])

        result = gp.FRFcoord(lon_arr, lat_arr)

        assert isinstance(result['xFRF'], np.ndarray)
        assert len(result['xFRF']) == 3

    def test_coordtype_override(self):
        """Test FRFcoord with explicit coordType parameter."""
        # Force FRF interpretation
        result = gp.FRFcoord(100.0, 200.0, coordType='FRF')
        assert result['xFRF'] == 100.0
        assert result['yFRF'] == 200.0

    def test_list_input_converted_to_array(self):
        """Test that list inputs are properly converted to arrays."""
        x_list = [100.0, 200.0, 300.0]
        y_list = [100.0, 200.0, 300.0]

        result = gp.FRFcoord(x_list, y_list)

        assert 'StateplaneE' in result
        assert len(result['StateplaneE']) == 3


class TestLatLon2utm:
    """Tests for Lat/Lon to UTM conversion."""

    def test_single_point(self):
        """Test conversion of a single lat/lon point to UTM."""
        result = gp.LatLon2utm(REF_LAT, REF_LON)

        assert 'utmE' in result
        assert 'utmN' in result
        assert 'zn' in result
        assert 'zl' in result
        # FRF is in UTM zone 18S
        assert result['zn'][0] == 18

    def test_array_of_points(self):
        """Test conversion of arrays of lat/lon points to UTM."""
        lat_arr = np.array([36.17, 36.18, REF_LAT])
        lon_arr = np.array([-75.75, -75.74, REF_LON])

        result = gp.LatLon2utm(lat_arr, lon_arr)

        assert isinstance(result['utmE'], np.ndarray)
        assert isinstance(result['utmN'], np.ndarray)
        assert len(result['utmE']) == 3
        # All points should be in zone 18
        assert all(result['zn'] == 18)


class TestUtm2LatLon:
    """Tests for UTM to Lat/Lon conversion."""

    def test_single_point(self):
        """Test conversion of a single UTM point to lat/lon."""
        # First get UTM coords from known lat/lon
        utm_result = gp.LatLon2utm(REF_LAT, REF_LON)

        result = gp.utm2LatLon(
            utm_result['utmE'][0],
            utm_result['utmN'][0],
            utm_result['zn'][0],
            utm_result['zl'][0]
        )

        assert abs(result['lat'][0] - REF_LAT) < TOLERANCE_DEGREES
        assert abs(result['lon'][0] - REF_LON) < TOLERANCE_DEGREES

    def test_array_of_points(self):
        """Test conversion of arrays of UTM points to lat/lon."""
        # First get UTM coords
        lat_arr = np.array([36.17, 36.18, REF_LAT])
        lon_arr = np.array([-75.75, -75.74, REF_LON])
        utm_result = gp.LatLon2utm(lat_arr, lon_arr)

        result = gp.utm2LatLon(
            utm_result['utmE'],
            utm_result['utmN'],
            18,  # zone number
            'S'  # zone letter
        )

        assert isinstance(result['lat'], np.ndarray)
        assert isinstance(result['lon'], np.ndarray)
        assert len(result['lat']) == 3


class TestUtm2ncsp:
    """Tests for UTM to NC State Plane conversion."""

    def test_single_point(self):
        """Test conversion of a single UTM point to state plane."""
        # First get UTM coords from known lat/lon
        utm_result = gp.LatLon2utm(REF_LAT, REF_LON)

        result = gp.utm2ncsp(
            utm_result['utmE'][0],
            utm_result['utmN'][0],
            utm_result['zn'][0],
            utm_result['zl'][0]
        )

        assert 'easting' in result
        assert 'northing' in result
        assert abs(result['easting'][0] - REF_SP_E) < TOLERANCE_METERS
        assert abs(result['northing'][0] - REF_SP_N) < TOLERANCE_METERS

    def test_array_of_points(self):
        """Test conversion of arrays of UTM points to state plane."""
        lat_arr = np.array([36.17, 36.18, REF_LAT])
        lon_arr = np.array([-75.75, -75.74, REF_LON])
        utm_result = gp.LatLon2utm(lat_arr, lon_arr)

        result = gp.utm2ncsp(
            utm_result['utmE'],
            utm_result['utmN'],
            18,
            'S'
        )

        assert isinstance(result['easting'], np.ndarray)
        assert len(result['easting']) == 3


class TestNcsp2utm:
    """Tests for NC State Plane to UTM conversion."""

    def test_single_point(self):
        """Test conversion of a single state plane point to UTM."""
        result = gp.ncsp2utm(REF_SP_E, REF_SP_N)

        assert 'utmE' in result
        assert 'utmN' in result
        assert 'zn' in result
        assert 'zl' in result

    def test_array_of_points(self):
        """Test conversion of arrays of state plane points to UTM."""
        e_arr = np.array([901926.2, 902307.92, 902500.0])
        n_arr = np.array([273871.0, 274771.22, 275000.0])

        result = gp.ncsp2utm(e_arr, n_arr)

        assert isinstance(result['utmE'], np.ndarray)
        assert isinstance(result['utmN'], np.ndarray)
        assert len(result['utmE']) == 3


class TestRoundTrip:
    """Test round-trip conversions to verify accuracy."""

    def test_frf_stateplane_roundtrip(self):
        """Test FRF -> State Plane -> FRF round trip."""
        x_orig = np.array([100.0, 200.0, 500.0])
        y_orig = np.array([100.0, 300.0, 600.0])

        sp = gp.FRF2ncsp(x_orig, y_orig)
        frf = gp.ncsp2FRF(sp['StateplaneE'], sp['StateplaneN'])

        np.testing.assert_array_almost_equal(frf['xFRF'], x_orig, decimal=2)
        np.testing.assert_array_almost_equal(frf['yFRF'], y_orig, decimal=2)

    def test_stateplane_latlon_roundtrip(self):
        """Test State Plane -> Lat/Lon -> State Plane round trip."""
        e_orig = np.array([901926.2, 902307.92, 902500.0])
        n_orig = np.array([273871.0, 274771.22, 275000.0])

        ll = gp.ncsp2LatLon(e_orig, n_orig)
        sp = gp.LatLon2ncsp(ll['lon'], ll['lat'])

        np.testing.assert_array_almost_equal(sp['StateplaneE'], e_orig, decimal=1)
        np.testing.assert_array_almost_equal(sp['StateplaneN'], n_orig, decimal=1)

    def test_latlon_utm_roundtrip(self):
        """Test Lat/Lon -> UTM -> Lat/Lon round trip."""
        lat_orig = np.array([36.17, 36.18, 36.19])
        lon_orig = np.array([-75.75, -75.74, -75.73])

        utm = gp.LatLon2utm(lat_orig, lon_orig)
        ll = gp.utm2LatLon(utm['utmE'], utm['utmN'], 18, 'S')

        np.testing.assert_array_almost_equal(ll['lat'], lat_orig, decimal=5)
        np.testing.assert_array_almost_equal(ll['lon'], lon_orig, decimal=5)

    def test_full_roundtrip_frf(self):
        """Test complete round trip: FRF -> SP -> LL -> SP -> FRF."""
        x_orig = 566.93
        y_orig = 515.11

        # FRF -> State Plane
        sp1 = gp.FRF2ncsp(x_orig, y_orig)
        # State Plane -> Lat/Lon
        ll = gp.ncsp2LatLon(sp1['StateplaneE'], sp1['StateplaneN'])
        # Lat/Lon -> State Plane
        sp2 = gp.LatLon2ncsp(ll['lon'], ll['lat'])
        # State Plane -> FRF
        frf = gp.ncsp2FRF(sp2['StateplaneE'], sp2['StateplaneN'])

        assert abs(frf['xFRF'] - x_orig) < TOLERANCE_METERS
        assert abs(frf['yFRF'] - y_orig) < TOLERANCE_METERS
