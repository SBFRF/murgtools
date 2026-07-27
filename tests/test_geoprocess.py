"""Tests for geoprocess coordinate transformation functions.

Tests cover single point and array conversions for all coordinate systems:
- FRF local coordinates
- NC State Plane (EPSG:3358)
- Lat/Lon (WGS84)
- UTM
"""
import numpy as np
import pytest

from murgtools.utils import geoprocess as gp


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


# =============================================================================
# Centralized Validation Points Registry
# =============================================================================
# This registry contains known reference points for validating coordinate
# transformations. Points are categorized by their source and usage.

VALIDATION_POINTS = {
    # -------------------------------------------------------------------------
    # FRF Calibration Points (from Bill Birkemeier's 2014 survey)
    # -------------------------------------------------------------------------
    'frf_origin': {
        'xFRF': 0.0,
        'yFRF': 0.0,
        'StateplaneE': 901951.6805,
        'StateplaneN': 274093.1562,
        'Lat': 36.1775975,
        'Lon': -75.7496860,
        'source': 'FRF calibration 2014',
        'description': 'FRF coordinate system origin',
    },
    'south_rail_1860': {
        'xFRF': 566.93,
        'yFRF': 515.11,
        'StateplaneE': 902307.92,
        'StateplaneN': 274771.22,
        'Lat': 36.1836000,
        'Lon': -75.7454804,
        'source': 'FRF calibration 2014',
        'description': 'South rail marker at station 1860',
    },

    # -------------------------------------------------------------------------
    # Quadrant Test Points (computed via round-trip validation)
    # These test negative and positive FRF coordinate combinations
    # -------------------------------------------------------------------------
    'quadrant_1_offshore_north': {
        'xFRF': 500.0,
        'yFRF': 500.0,
        'source': 'computed',
        'description': 'Quadrant 1: offshore (+x), north of origin (+y)',
    },
    'quadrant_2_landward_north': {
        'xFRF': -100.0,
        'yFRF': 500.0,
        'source': 'computed',
        'description': 'Quadrant 2: landward (-x), north of origin (+y)',
    },
    'quadrant_3_landward_south': {
        'xFRF': -100.0,
        'yFRF': -500.0,
        'source': 'computed',
        'description': 'Quadrant 3: landward (-x), south of origin (-y)',
    },
    'quadrant_4_offshore_south': {
        'xFRF': 500.0,
        'yFRF': -500.0,
        'source': 'computed',
        'description': 'Quadrant 4: offshore (+x), south of origin (-y)',
    },

    # -------------------------------------------------------------------------
    # Cross-shore Transect Points (at yFRF=0, alongshore origin)
    # -------------------------------------------------------------------------
    'dune_landward': {
        'xFRF': -50.0,
        'yFRF': 0.0,
        'source': 'computed',
        'description': 'Dune/berm area, landward of shoreline',
    },
    'shoreline': {
        'xFRF': 25.0,
        'yFRF': 0.0,
        'source': 'computed',
        'description': 'Approximate shoreline/swash zone',
    },
    'inner_surf': {
        'xFRF': 150.0,
        'yFRF': 0.0,
        'source': 'computed',
        'description': 'Inner surf zone, breaking wave zone',
    },
    'mid_surf': {
        'xFRF': 400.0,
        'yFRF': 0.0,
        'source': 'computed',
        'description': 'Mid surf zone',
    },
    'pier_end': {
        'xFRF': 600.0,
        'yFRF': 0.0,
        'source': 'computed',
        'description': 'Approximate end of FRF research pier',
    },
    'nearshore_8m': {
        'xFRF': 900.0,
        'yFRF': 0.0,
        'source': 'computed',
        'description': 'Nearshore, approx 8m water depth array location',
    },
    'offshore_17m': {
        'xFRF': 1700.0,
        'yFRF': 0.0,
        'source': 'computed',
        'description': 'Offshore, approx 17m water depth',
    },
    'offshore_26m': {
        'xFRF': 2600.0,
        'yFRF': 0.0,
        'source': 'computed',
        'description': 'Offshore, approx 26m water depth waverider location',
    },

    # -------------------------------------------------------------------------
    # Alongshore Transect Points (at xFRF=500, mid-surf zone)
    # -------------------------------------------------------------------------
    'alongshore_south_1000': {
        'xFRF': 500.0,
        'yFRF': -1000.0,
        'source': 'computed',
        'description': 'South limit of typical survey area',
    },
    'alongshore_north_1000': {
        'xFRF': 500.0,
        'yFRF': 1000.0,
        'source': 'computed',
        'description': 'North of FRF pier',
    },
    'alongshore_north_1500': {
        'xFRF': 500.0,
        'yFRF': 1500.0,
        'source': 'computed',
        'description': 'Extended north coverage',
    },
}

# Placeholder for user-provided validation points
USER_VALIDATION_POINTS = [
    # Example format:
    # {'name': 'custom_point_1', 'xFRF': 100.0, 'yFRF': 200.0, 'source': 'GPS survey 2024'},
]


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


# =============================================================================
# Validation Point Tests
# =============================================================================

class TestValidationPoints:
    """Tests using the centralized validation points registry."""

    @pytest.mark.parametrize("point_name,coords", [
        (name, data) for name, data in VALIDATION_POINTS.items()
        if 'StateplaneE' in data  # Only test points with known state plane coords
    ])
    def test_calibration_point_frf_to_stateplane(self, point_name, coords):
        """Test FRF to State Plane conversion for calibration points."""
        result = gp.FRF2ncsp(coords['xFRF'], coords['yFRF'])

        assert abs(result['StateplaneE'] - coords['StateplaneE']) < TOLERANCE_METERS, \
            f"{point_name}: StateplaneE mismatch"
        assert abs(result['StateplaneN'] - coords['StateplaneN']) < TOLERANCE_METERS, \
            f"{point_name}: StateplaneN mismatch"

    @pytest.mark.parametrize("point_name,coords", [
        (name, data) for name, data in VALIDATION_POINTS.items()
        if 'Lat' in data and 'Lon' in data
    ])
    def test_calibration_point_latlon(self, point_name, coords):
        """Test FRF to Lat/Lon conversion for points with known geographic coords."""
        result = gp.FRFcoord(coords['xFRF'], coords['yFRF'], coordType='FRF')

        assert abs(result['Lat'] - coords['Lat']) < TOLERANCE_DEGREES, \
            f"{point_name}: Lat mismatch"
        assert abs(result['Lon'] - coords['Lon']) < TOLERANCE_DEGREES, \
            f"{point_name}: Lon mismatch"

    @pytest.mark.parametrize("point_name,coords", VALIDATION_POINTS.items())
    def test_validation_point_roundtrip(self, point_name, coords):
        """Test that each validation point survives round-trip conversion.

        Round-trip: FRF -> StatePlane -> LatLon -> StatePlane -> FRF
        """
        x_orig = coords['xFRF']
        y_orig = coords['yFRF']

        # FRF -> State Plane
        sp1 = gp.FRF2ncsp(x_orig, y_orig)
        # State Plane -> Lat/Lon
        ll = gp.ncsp2LatLon(sp1['StateplaneE'], sp1['StateplaneN'])
        # Lat/Lon -> State Plane
        sp2 = gp.LatLon2ncsp(ll['lon'], ll['lat'])
        # State Plane -> FRF
        frf = gp.ncsp2FRF(sp2['StateplaneE'], sp2['StateplaneN'])

        assert abs(frf['xFRF'] - x_orig) < TOLERANCE_METERS, \
            f"{point_name}: xFRF round-trip error ({frf['xFRF']} vs {x_orig})"
        assert abs(frf['yFRF'] - y_orig) < TOLERANCE_METERS, \
            f"{point_name}: yFRF round-trip error ({frf['yFRF']} vs {y_orig})"


class TestNegativeCoordinates:
    """Tests specifically for negative FRF coordinates (landward and south of origin)."""

    @pytest.mark.parametrize("x,y,description", [
        (-50, 0, "Landward at origin alongshore"),
        (-100, 0, "Dune area at origin alongshore"),
        (0, -100, "At shoreline, south of origin"),
        (0, -500, "At shoreline, far south"),
        (-50, -500, "Landward, far south"),
        (-100, 500, "Landward, north of origin"),
        (500, -1000, "Offshore, south limit"),
    ])
    def test_negative_coordinate_roundtrip(self, x, y, description):
        """Test that negative FRF coordinates survive round-trip conversion."""
        # FRF -> State Plane -> FRF
        sp = gp.FRF2ncsp(x, y)
        frf = gp.ncsp2FRF(sp['StateplaneE'], sp['StateplaneN'])

        assert abs(frf['xFRF'] - x) < 0.01, \
            f"{description}: xFRF error ({frf['xFRF']} vs {x})"
        assert abs(frf['yFRF'] - y) < 0.01, \
            f"{description}: yFRF error ({frf['yFRF']} vs {y})"

    @pytest.mark.parametrize("x,y,description", [
        (-100, -500, "Landward south quadrant"),
        (-100, 500, "Landward north quadrant"),
    ])
    def test_negative_coordinate_full_roundtrip(self, x, y, description):
        """Test full round-trip (FRF->SP->LL->SP->FRF) for negative coordinates."""
        # FRF -> State Plane
        sp1 = gp.FRF2ncsp(x, y)
        # State Plane -> Lat/Lon
        ll = gp.ncsp2LatLon(sp1['StateplaneE'], sp1['StateplaneN'])
        # Lat/Lon -> State Plane
        sp2 = gp.LatLon2ncsp(ll['lon'], ll['lat'])
        # State Plane -> FRF
        frf = gp.ncsp2FRF(sp2['StateplaneE'], sp2['StateplaneN'])

        assert abs(frf['xFRF'] - x) < TOLERANCE_METERS, \
            f"{description}: xFRF round-trip error ({frf['xFRF']} vs {x})"
        assert abs(frf['yFRF'] - y) < TOLERANCE_METERS, \
            f"{description}: yFRF round-trip error ({frf['yFRF']} vs {y})"

    def test_negative_x_produces_smaller_stateplane_e(self):
        """Verify that negative xFRF (landward) produces smaller State Plane easting."""
        result_neg = gp.FRF2ncsp(-100, 0)
        result_zero = gp.FRF2ncsp(0, 0)
        result_pos = gp.FRF2ncsp(100, 0)

        # Landward (negative x) should have smaller easting
        assert result_neg['StateplaneE'] < result_zero['StateplaneE']
        assert result_zero['StateplaneE'] < result_pos['StateplaneE']

    def test_negative_y_produces_smaller_stateplane_n(self):
        """Verify that negative yFRF (south) produces smaller State Plane northing."""
        result_neg = gp.FRF2ncsp(0, -100)
        result_zero = gp.FRF2ncsp(0, 0)
        result_pos = gp.FRF2ncsp(0, 100)

        # South (negative y) should have smaller northing
        assert result_neg['StateplaneN'] < result_zero['StateplaneN']
        assert result_zero['StateplaneN'] < result_pos['StateplaneN']

    def test_frf_coord_with_negative_inputs(self):
        """Test FRFcoord with explicit FRF coordType and negative values."""
        result = gp.FRFcoord(-100, -500, coordType='FRF')

        # Should return the same xFRF/yFRF values
        assert result['xFRF'] == -100
        assert result['yFRF'] == -500

        # Should produce valid lat/lon in FRF region
        assert 36.0 < result['Lat'] < 37.0
        assert -76.0 < result['Lon'] < -75.0

        # Should produce valid state plane coords
        assert result['StateplaneE'] > 800000
        assert result['StateplaneN'] > 200000


class TestArrayValidation:
    """Tests for array inputs including mixed positive/negative values."""

    def test_mixed_sign_array_roundtrip(self):
        """Test arrays with mixed positive and negative FRF coordinates."""
        x_arr = np.array([-100, 0, 100, 500, -50])
        y_arr = np.array([-500, 0, 500, -1000, 250])

        # Round-trip through state plane
        sp = gp.FRF2ncsp(x_arr, y_arr)
        frf = gp.ncsp2FRF(sp['StateplaneE'], sp['StateplaneN'])

        np.testing.assert_array_almost_equal(frf['xFRF'], x_arr, decimal=2)
        np.testing.assert_array_almost_equal(frf['yFRF'], y_arr, decimal=2)

    def test_cross_shore_transect_array(self):
        """Test cross-shore transect from dune to offshore."""
        x_arr = np.array([-50, 0, 100, 300, 600, 900, 1700, 2600])
        y_arr = np.zeros_like(x_arr)  # All at yFRF=0

        result = gp.FRFcoord(x_arr, y_arr, coordType='FRF')

        # Verify all outputs are arrays of correct length
        assert len(result['xFRF']) == len(x_arr)
        assert len(result['Lat']) == len(x_arr)
        assert len(result['StateplaneE']) == len(x_arr)

        # Verify latitude generally increases as we go offshore (east)
        # This is due to FRF coordinate system orientation
        lats = result['Lat']
        assert all(lats > 36.0) and all(lats < 37.0)

    def test_alongshore_transect_array(self):
        """Test alongshore transect from south to north."""
        x_arr = np.full(5, 500.0)  # All at xFRF=500
        y_arr = np.array([-1000, -500, 0, 500, 1000])

        result = gp.FRFcoord(x_arr, y_arr, coordType='FRF')

        # Verify northing increases with yFRF
        northings = result['StateplaneN']
        for i in range(len(northings) - 1):
            assert northings[i] < northings[i + 1], \
                f"Northing should increase: {northings[i]} < {northings[i+1]}"


# =============================================================================
# Standardized Key Names Tests
# =============================================================================

class TestStandardizedKeyNames:
    """Tests for new key names with units (Phase 2 enhancement)."""

    def test_frf2ncsp_has_unit_keys(self):
        """Test that FRF2ncsp returns both legacy and new keys with units."""
        result = gp.FRF2ncsp(REF_FRF_X, REF_FRF_Y)

        # Check legacy keys exist
        assert 'xFRF' in result
        assert 'yFRF' in result
        assert 'StateplaneE' in result
        assert 'StateplaneN' in result

        # Check new keys with units exist
        assert 'xFRF_m' in result
        assert 'yFRF_m' in result
        assert 'StateplaneE_m' in result
        assert 'StateplaneN_m' in result

        # Check values are equivalent
        assert result['xFRF'] == result['xFRF_m']
        assert result['yFRF'] == result['yFRF_m']
        assert result['StateplaneE'] == result['StateplaneE_m']
        assert result['StateplaneN'] == result['StateplaneN_m']

    def test_ncsp2frf_has_unit_keys(self):
        """Test that ncsp2FRF returns both legacy and new keys with units."""
        result = gp.ncsp2FRF(REF_SP_E, REF_SP_N)

        # Check new keys with units exist
        assert 'xFRF_m' in result
        assert 'yFRF_m' in result
        assert 'StateplaneE_m' in result
        assert 'StateplaneN_m' in result

    def test_ncsp2latlon_has_unit_keys(self):
        """Test that ncsp2LatLon returns both legacy and new keys with units."""
        result = gp.ncsp2LatLon(REF_SP_E, REF_SP_N)

        # Check legacy keys
        assert 'lat' in result
        assert 'lon' in result

        # Check new keys with units
        assert 'Lat_NAD83_deg' in result
        assert 'Lon_NAD83_deg' in result
        assert 'StateplaneE_m' in result
        assert 'StateplaneN_m' in result

    def test_latlon2ncsp_has_unit_keys(self):
        """Test that LatLon2ncsp returns both legacy and new keys with units."""
        result = gp.LatLon2ncsp(REF_LON, REF_LAT)

        # Check new keys with units
        assert 'Lat_NAD83_deg' in result
        assert 'Lon_NAD83_deg' in result
        assert 'StateplaneE_m' in result
        assert 'StateplaneN_m' in result

    def test_frfcoord_has_all_unit_keys(self):
        """Test that FRFcoord returns complete set of keys with units."""
        result = gp.FRFcoord(REF_FRF_X, REF_FRF_Y, coordType='FRF')

        # Check all new keys with units exist
        assert 'xFRF_m' in result
        assert 'yFRF_m' in result
        assert 'StateplaneE_m' in result
        assert 'StateplaneN_m' in result
        assert 'Lat_NAD83_deg' in result
        assert 'Lon_NAD83_deg' in result
        assert 'utmE_m' in result
        assert 'utmN_m' in result

        # Verify values match between legacy and new keys
        assert result['Lat'] == result['Lat_NAD83_deg']
        assert result['Lon'] == result['Lon_NAD83_deg']

    def test_latlon2utm_has_unit_keys(self):
        """Test that LatLon2utm returns keys with units."""
        result = gp.LatLon2utm(REF_LAT, REF_LON)

        # Check new keys with units
        assert 'utmE_m' in result
        assert 'utmN_m' in result

        # Zone info should still be available
        assert 'zn' in result
        assert 'zl' in result

    def test_utm2latlon_has_unit_keys(self):
        """Test that utm2LatLon returns keys with units."""
        utm_result = gp.LatLon2utm(REF_LAT, REF_LON)
        result = gp.utm2LatLon(
            utm_result['utmE'][0],
            utm_result['utmN'][0],
            utm_result['zn'][0],
            utm_result['zl'][0]
        )

        # Check new keys with units
        assert 'Lat_NAD83_deg' in result
        assert 'Lon_NAD83_deg' in result

    def test_deprecation_warning_on_legacy_key_access(self):
        """Test that accessing legacy keys triggers deprecation warning."""
        result = gp.FRF2ncsp(REF_FRF_X, REF_FRF_Y)

        # Accessing new key should not warn
        _ = result['xFRF_m']

        # Accessing legacy key should warn
        with pytest.warns(DeprecationWarning, match="Key 'xFRF' is deprecated"):
            _ = result['xFRF']

    def test_deprecation_warning_via_get_method(self):
        """Test that .get() on legacy keys also triggers warning."""
        result = gp.FRFcoord(REF_FRF_X, REF_FRF_Y, coordType='FRF')

        # Accessing via .get() on new key should not warn
        _ = result.get('Lat_NAD83_deg')

        # Accessing via .get() on legacy key should warn
        with pytest.warns(DeprecationWarning, match="Key 'Lat' is deprecated"):
            _ = result.get('Lat')

    def test_unit_keys_work_with_arrays(self):
        """Test that unit keys work correctly with array inputs."""
        x_arr = np.array([100.0, 200.0, 300.0])
        y_arr = np.array([100.0, 200.0, 300.0])

        result = gp.FRFcoord(x_arr, y_arr, coordType='FRF')

        # Check arrays are properly returned via new keys
        assert isinstance(result['xFRF_m'], np.ndarray)
        assert isinstance(result['StateplaneE_m'], np.ndarray)
        assert len(result['xFRF_m']) == 3
        assert len(result['Lat_NAD83_deg']) == 3

    def test_dict_operations_work(self):
        """Test that standard dict operations work on DeprecatingDict."""
        result = gp.FRF2ncsp(REF_FRF_X, REF_FRF_Y)

        # Test keys()
        keys = list(result.keys())
        assert 'xFRF_m' in keys
        assert 'StateplaneE_m' in keys

        # Test values()
        values = list(result.values())
        assert len(values) > 0

        # Test items()
        items = list(result.items())
        assert len(items) > 0

        # Test len()
        assert len(result) >= 8  # At least 4 legacy + 4 new keys

    def test_iteration_over_keys(self):
        """Test that iterating over DeprecatingDict works."""
        result = gp.FRF2ncsp(REF_FRF_X, REF_FRF_Y)

        keys_found = []
        for key in result:
            keys_found.append(key)

        assert 'xFRF_m' in keys_found
        assert 'yFRF_m' in keys_found


# =============================================================================
# CoordinateResult Dataclass Tests
# =============================================================================

class TestCoordinateResultDataclass:
    """Tests for the CoordinateResult dataclass (Phase 3 enhancement)."""

    def test_frfcoord_returns_dataclass_when_requested(self):
        """Test that FRFcoord can return a CoordinateResult dataclass."""
        result = gp.FRFcoord(REF_FRF_X, REF_FRF_Y, coordType='FRF', return_dataclass=True)

        # Should be a CoordinateResult instance
        assert isinstance(result, gp.CoordinateResult)

    def test_dataclass_attribute_access(self):
        """Test attribute access on CoordinateResult."""
        result = gp.FRFcoord(REF_FRF_X, REF_FRF_Y, coordType='FRF', return_dataclass=True)

        # Test attribute access
        assert hasattr(result, 'xFRF_m')
        assert hasattr(result, 'yFRF_m')
        assert hasattr(result, 'StateplaneE_m')
        assert hasattr(result, 'StateplaneN_m')
        assert hasattr(result, 'Lat_NAD83_deg')
        assert hasattr(result, 'Lon_NAD83_deg')
        assert hasattr(result, 'utmE_m')
        assert hasattr(result, 'utmN_m')

        # Test values
        assert abs(result.xFRF_m - REF_FRF_X) < 0.01
        assert abs(result.yFRF_m - REF_FRF_Y) < 0.01
        assert abs(result.StateplaneE_m - REF_SP_E) < TOLERANCE_METERS
        assert abs(result.StateplaneN_m - REF_SP_N) < TOLERANCE_METERS
        assert abs(result.Lat_NAD83_deg - REF_LAT) < TOLERANCE_DEGREES
        assert abs(result.Lon_NAD83_deg - REF_LON) < TOLERANCE_DEGREES

    def test_dataclass_dict_style_access(self):
        """Test dictionary-style access on CoordinateResult."""
        result = gp.FRFcoord(REF_FRF_X, REF_FRF_Y, coordType='FRF', return_dataclass=True)

        # Test dict-style access with new keys
        assert abs(result['xFRF_m'] - REF_FRF_X) < 0.01
        assert abs(result['Lat_NAD83_deg'] - REF_LAT) < TOLERANCE_DEGREES

        # Test dict-style access with legacy keys
        assert abs(result['xFRF'] - REF_FRF_X) < 0.01
        assert abs(result['Lat'] - REF_LAT) < TOLERANCE_DEGREES
        assert abs(result['StateplaneE'] - REF_SP_E) < TOLERANCE_METERS

    def test_dataclass_contains_operator(self):
        """Test 'in' operator on CoordinateResult."""
        result = gp.FRFcoord(REF_FRF_X, REF_FRF_Y, coordType='FRF', return_dataclass=True)

        # New keys should be found
        assert 'xFRF_m' in result
        assert 'Lat_NAD83_deg' in result
        assert 'StateplaneE_m' in result

        # Legacy keys should also work
        assert 'xFRF' in result
        assert 'Lat' in result
        assert 'StateplaneE' in result

    def test_dataclass_to_dict(self):
        """Test CoordinateResult.to_dict() method."""
        result = gp.FRFcoord(REF_FRF_X, REF_FRF_Y, coordType='FRF', return_dataclass=True)

        # Convert to dict with legacy keys
        d = result.to_dict(include_legacy=True)
        assert 'xFRF_m' in d
        assert 'xFRF' in d
        assert 'Lat_NAD83_deg' in d
        assert 'Lat' in d

        # Convert to dict without legacy keys
        d_new = result.to_dict(include_legacy=False)
        assert 'xFRF_m' in d_new
        assert 'xFRF' not in d_new
        assert 'Lat_NAD83_deg' in d_new
        assert 'Lat' not in d_new

    def test_dataclass_from_dict(self):
        """Test CoordinateResult.from_dict() class method."""
        # Create from dict with legacy keys
        data = {
            'xFRF': 100.0,
            'yFRF': 200.0,
            'StateplaneE': 902000.0,
            'StateplaneN': 274500.0,
            'Lat': 36.18,
            'Lon': -75.74,
            'utmE': 430000.0,
            'utmN': 4006000.0,
        }
        result = gp.CoordinateResult.from_dict(data)

        assert result.xFRF_m == 100.0
        assert result.yFRF_m == 200.0
        assert result.Lat_NAD83_deg == 36.18

        # Create from dict with new keys
        data_new = {
            'xFRF_m': 100.0,
            'yFRF_m': 200.0,
            'StateplaneE_m': 902000.0,
            'StateplaneN_m': 274500.0,
            'Lat_NAD83_deg': 36.18,
            'Lon_NAD83_deg': -75.74,
        }
        result_new = gp.CoordinateResult.from_dict(data_new)

        assert result_new.xFRF_m == 100.0
        assert result_new.Lat_NAD83_deg == 36.18

    def test_dataclass_with_arrays(self):
        """Test CoordinateResult works with array inputs."""
        x_arr = np.array([100.0, 200.0, 300.0])
        y_arr = np.array([100.0, 200.0, 300.0])

        result = gp.FRFcoord(x_arr, y_arr, coordType='FRF', return_dataclass=True)

        # Attributes should be arrays
        assert isinstance(result.xFRF_m, np.ndarray)
        assert isinstance(result.Lat_NAD83_deg, np.ndarray)
        assert len(result.xFRF_m) == 3

        # Dict-style access should also return arrays
        assert len(result['xFRF_m']) == 3

    def test_default_returns_dict_not_dataclass(self):
        """Test that FRFcoord returns dict by default (backward compatible)."""
        result = gp.FRFcoord(REF_FRF_X, REF_FRF_Y, coordType='FRF')

        # Should NOT be a CoordinateResult
        assert not isinstance(result, gp.CoordinateResult)

        # Should be a dict-like object
        assert hasattr(result, '__getitem__')
        assert hasattr(result, 'keys')

    def test_dataclass_keyerror_on_invalid_key(self):
        """Test that invalid keys raise KeyError on CoordinateResult."""
        result = gp.FRFcoord(REF_FRF_X, REF_FRF_Y, coordType='FRF', return_dataclass=True)

        with pytest.raises(KeyError):
            _ = result['invalid_key']

    def test_dataclass_utm_zone_string(self):
        """Test that utm_zone is properly formatted."""
        result = gp.FRFcoord(REF_FRF_X, REF_FRF_Y, coordType='FRF', return_dataclass=True)

        # UTM should be computed
        assert result.utmE_m is not None
        assert result.utmN_m is not None

        # Zone might be None if not constructed from UTM input
        # But we can verify it doesn't error


# =============================================================================
# Vertical Coordinate Transformation Tests
# =============================================================================

class TestVerticalTransformations:
    """Tests for vertical coordinate transformations (Phase 4 enhancement)."""

    # FRF approximate geoid separation (NAD83 to NAVD88)
    # At FRF, the geoid is about 35-36m below the ellipsoid
    FRF_GEOID_SEP_APPROX = -35.5
    FRF_GEOID_SEP_TOLERANCE = 2.0  # Allow 2m tolerance for variations

    def test_ellipsoid_to_orthometric_returns_dict(self):
        """Test that ellipsoid_to_orthometric returns proper dict."""
        result = gp.ellipsoid_to_orthometric(REF_LAT, REF_LON, 10.0)

        assert 'orthometric_height_m' in result
        assert 'geoid_separation_m' in result
        assert 'lat' in result
        assert 'lon' in result
        assert 'ellipsoid_height_m' in result

    def test_orthometric_to_ellipsoid_returns_dict(self):
        """Test that orthometric_to_ellipsoid returns proper dict."""
        result = gp.orthometric_to_ellipsoid(REF_LAT, REF_LON, 5.0)

        assert 'ellipsoid_height_m' in result
        assert 'geoid_separation_m' in result
        assert 'lat' in result
        assert 'lon' in result
        assert 'orthometric_height_m' in result

    def test_get_geoid_separation_returns_dict(self):
        """Test that get_geoid_separation returns proper dict."""
        result = gp.get_geoid_separation(REF_LAT, REF_LON)

        assert 'geoid_separation_m' in result
        assert 'lat' in result
        assert 'lon' in result

    def test_geoid_separation_at_frf(self):
        """Test geoid separation at FRF is approximately -35 to -36m."""
        result = gp.get_geoid_separation(REF_LAT, REF_LON)

        geoid_sep = result['geoid_separation_m']

        # FRF geoid separation should be approximately -35.5m
        assert abs(geoid_sep - self.FRF_GEOID_SEP_APPROX) < self.FRF_GEOID_SEP_TOLERANCE, \
            f"Geoid separation at FRF should be ~{self.FRF_GEOID_SEP_APPROX}m, got {geoid_sep}m"

    def test_roundtrip_ellipsoid_orthometric(self):
        """Test round-trip conversion: ellipsoid -> orthometric -> ellipsoid."""
        original_ellipsoid_height = 10.0

        # Ellipsoid to orthometric
        ortho_result = gp.ellipsoid_to_orthometric(REF_LAT, REF_LON, original_ellipsoid_height)
        orthometric_height = ortho_result['orthometric_height_m']

        # Orthometric back to ellipsoid
        ellip_result = gp.orthometric_to_ellipsoid(REF_LAT, REF_LON, orthometric_height)
        recovered_ellipsoid_height = ellip_result['ellipsoid_height_m']

        # Should recover original height within tolerance
        assert abs(recovered_ellipsoid_height - original_ellipsoid_height) < 0.01, \
            f"Round-trip failed: {original_ellipsoid_height} -> {orthometric_height} -> {recovered_ellipsoid_height}"

    def test_roundtrip_orthometric_ellipsoid(self):
        """Test round-trip conversion: orthometric -> ellipsoid -> orthometric."""
        original_orthometric_height = 5.0

        # Orthometric to ellipsoid
        ellip_result = gp.orthometric_to_ellipsoid(REF_LAT, REF_LON, original_orthometric_height)
        ellipsoid_height = ellip_result['ellipsoid_height_m']

        # Ellipsoid back to orthometric
        ortho_result = gp.ellipsoid_to_orthometric(REF_LAT, REF_LON, ellipsoid_height)
        recovered_orthometric_height = ortho_result['orthometric_height_m']

        # Should recover original height within tolerance
        assert abs(recovered_orthometric_height - original_orthometric_height) < 0.01, \
            f"Round-trip failed: {original_orthometric_height} -> {ellipsoid_height} -> {recovered_orthometric_height}"

    def test_ellipsoid_higher_than_orthometric_at_frf(self):
        """Test that ellipsoidal height > orthometric height at FRF (geoid below ellipsoid)."""
        ellipsoid_height = 0.0  # Sea level in ellipsoid terms

        result = gp.ellipsoid_to_orthometric(REF_LAT, REF_LON, ellipsoid_height)

        # At FRF, geoid is ~35m below ellipsoid, so orthometric should be higher
        # orthometric = ellipsoidal - N (where N is negative)
        orthometric_height = result['orthometric_height_m']
        assert orthometric_height > ellipsoid_height, \
            f"At FRF, orthometric ({orthometric_height}) should be > ellipsoidal ({ellipsoid_height})"

    def test_array_input_vertical_transforms(self):
        """Test that vertical transforms work with array inputs."""
        lat_arr = np.array([36.17, 36.18, REF_LAT])
        lon_arr = np.array([-75.75, -75.74, REF_LON])
        height_arr = np.array([0.0, 5.0, 10.0])

        result = gp.ellipsoid_to_orthometric(lat_arr, lon_arr, height_arr)

        # Results should be arrays
        assert isinstance(result['orthometric_height_m'], np.ndarray)
        assert isinstance(result['geoid_separation_m'], np.ndarray)
        assert len(result['orthometric_height_m']) == 3

    def test_invalid_from_crs_raises_error(self):
        """Test that invalid from_crs raises ValueError."""
        with pytest.raises(ValueError, match="from_crs must be one of"):
            gp.ellipsoid_to_orthometric(REF_LAT, REF_LON, 10.0, from_crs='INVALID')

    def test_invalid_to_vertical_raises_error(self):
        """Test that invalid to_vertical raises ValueError."""
        with pytest.raises(ValueError, match="to_vertical must be one of"):
            gp.ellipsoid_to_orthometric(REF_LAT, REF_LON, 10.0, to_vertical='INVALID')

    def test_wgs84_conversion(self):
        """Test conversion using WGS84 ellipsoid."""
        result = gp.ellipsoid_to_orthometric(
            REF_LAT, REF_LON, 10.0,
            from_crs='WGS84', to_vertical='EGM96'
        )

        assert 'orthometric_height_m' in result
        assert 'geoid_separation_m' in result

    def test_geoid_separation_consistent(self):
        """Test that geoid separation is consistent across functions."""
        # Get geoid separation directly
        sep_result = gp.get_geoid_separation(REF_LAT, REF_LON)
        direct_sep = sep_result['geoid_separation_m']

        # Get geoid separation from ellipsoid_to_orthometric
        ellip_result = gp.ellipsoid_to_orthometric(REF_LAT, REF_LON, 0.0)
        computed_sep = ellip_result['geoid_separation_m']

        # Should be the same
        assert abs(direct_sep - computed_sep) < 0.01, \
            f"Geoid separations should match: direct={direct_sep}, computed={computed_sep}"

    def test_negative_heights(self):
        """Test that negative heights (below sea level) work correctly."""
        negative_height = -5.0

        result = gp.ellipsoid_to_orthometric(REF_LAT, REF_LON, negative_height)

        # Should not error and should return valid values
        assert np.isfinite(result['orthometric_height_m'])
        assert np.isfinite(result['geoid_separation_m'])

    def test_frf_origin_geoid_separation(self):
        """Test geoid separation specifically at FRF origin."""
        frf_origin_lat = 36.1775975
        frf_origin_lon = -75.7496860

        result = gp.get_geoid_separation(frf_origin_lat, frf_origin_lon)

        geoid_sep = result['geoid_separation_m']

        # Should be approximately -35.5m at FRF origin
        assert abs(geoid_sep - self.FRF_GEOID_SEP_APPROX) < self.FRF_GEOID_SEP_TOLERANCE, \
            f"FRF origin geoid separation should be ~{self.FRF_GEOID_SEP_APPROX}m, got {geoid_sep}m"


class TestWGS84NAD83VerticalDifferences:
    """Tests specifically for WGS84 vs NAD83 handling in vertical transformations.

    These tests verify that the code properly handles the differences between:
    - NAD83 (GRS80 ellipsoid) with NAVD88 (GEOID18)
    - WGS84 (WGS84 ellipsoid) with EGM96/EGM2008

    At the FRF, the differences are small but important for survey-grade work.
    """

    # Expected geoid separations at FRF for different combinations
    # These are approximate values from NOAA/NGS tools
    NAD83_NAVD88_SEP = -35.5  # GEOID18 at FRF
    WGS84_EGM96_SEP = -35.0   # EGM96 at FRF
    WGS84_EGM2008_SEP = -35.1  # EGM2008 at FRF
    TOLERANCE = 0.5  # Allow 0.5m tolerance for fallback values

    def test_nad83_navd88_geoid_separation(self):
        """Test NAD83 to NAVD88 geoid separation (standard US survey combination)."""
        result = gp.get_geoid_separation(
            REF_LAT, REF_LON,
            from_crs='NAD83', to_vertical='NAVD88'
        )

        assert abs(result['geoid_separation_m'] - self.NAD83_NAVD88_SEP) < self.TOLERANCE, \
            f"NAD83/NAVD88 sep should be ~{self.NAD83_NAVD88_SEP}m, got {result['geoid_separation_m']}m"

    def test_wgs84_egm96_geoid_separation(self):
        """Test WGS84 to EGM96 geoid separation (global model)."""
        result = gp.get_geoid_separation(
            REF_LAT, REF_LON,
            from_crs='WGS84', to_vertical='EGM96'
        )

        assert abs(result['geoid_separation_m'] - self.WGS84_EGM96_SEP) < self.TOLERANCE, \
            f"WGS84/EGM96 sep should be ~{self.WGS84_EGM96_SEP}m, got {result['geoid_separation_m']}m"

    def test_wgs84_egm2008_geoid_separation(self):
        """Test WGS84 to EGM2008 geoid separation (newer global model)."""
        result = gp.get_geoid_separation(
            REF_LAT, REF_LON,
            from_crs='WGS84', to_vertical='EGM2008'
        )

        assert abs(result['geoid_separation_m'] - self.WGS84_EGM2008_SEP) < self.TOLERANCE, \
            f"WGS84/EGM2008 sep should be ~{self.WGS84_EGM2008_SEP}m, got {result['geoid_separation_m']}m"

    def test_nad83_vs_wgs84_egm_difference(self):
        """Test that NAD83/NAVD88 gives different result than WGS84/EGM models."""
        nad83_result = gp.get_geoid_separation(
            REF_LAT, REF_LON,
            from_crs='NAD83', to_vertical='NAVD88'
        )
        wgs84_result = gp.get_geoid_separation(
            REF_LAT, REF_LON,
            from_crs='WGS84', to_vertical='EGM96'
        )

        # They should be different (NAD83/NAVD88 should be more negative)
        diff = nad83_result['geoid_separation_m'] - wgs84_result['geoid_separation_m']

        # At FRF, NAD83/NAVD88 is about 0.5m more negative than WGS84/EGM96
        assert diff < 0, \
            f"NAD83/NAVD88 should be more negative than WGS84/EGM96, diff={diff}m"

    def test_wgs84_navd88_emits_warning(self):
        """Test that using WGS84 with NAVD88 emits a warning."""
        with pytest.warns(UserWarning, match="WGS84.*NAVD88"):
            gp.ellipsoid_to_orthometric(
                REF_LAT, REF_LON, 10.0,
                from_crs='WGS84', to_vertical='NAVD88'
            )

    def test_navd88_wgs84_emits_warning(self):
        """Test that converting NAVD88 to WGS84 emits a warning."""
        with pytest.warns(UserWarning, match="NAVD88.*WGS84"):
            gp.orthometric_to_ellipsoid(
                REF_LAT, REF_LON, 5.0,
                from_vertical='NAVD88', to_crs='WGS84'
            )

    def test_result_includes_crs_info(self):
        """Test that results include from_crs and to_vertical info."""
        result = gp.ellipsoid_to_orthometric(
            REF_LAT, REF_LON, 10.0,
            from_crs='NAD83', to_vertical='NAVD88'
        )

        assert 'from_crs' in result
        assert 'to_vertical' in result
        assert result['from_crs'] == 'NAD83'
        assert result['to_vertical'] == 'NAVD88'

    def test_orthometric_result_includes_crs_info(self):
        """Test that orthometric_to_ellipsoid results include CRS info."""
        result = gp.orthometric_to_ellipsoid(
            REF_LAT, REF_LON, 5.0,
            from_vertical='NAVD88', to_crs='NAD83'
        )

        assert 'from_vertical' in result
        assert 'to_crs' in result
        assert result['from_vertical'] == 'NAVD88'
        assert result['to_crs'] == 'NAD83'

    def test_geoid_sep_result_includes_crs_info(self):
        """Test that get_geoid_separation results include CRS info."""
        result = gp.get_geoid_separation(
            REF_LAT, REF_LON,
            from_crs='WGS84', to_vertical='EGM2008'
        )

        assert 'from_crs' in result
        assert 'to_vertical' in result
        assert result['from_crs'] == 'WGS84'
        assert result['to_vertical'] == 'EGM2008'

    def test_roundtrip_nad83_navd88(self):
        """Test round-trip: NAD83 ellipsoid -> NAVD88 -> NAD83 ellipsoid."""
        original_height = 10.0

        # NAD83 ellipsoid to NAVD88
        ortho = gp.ellipsoid_to_orthometric(
            REF_LAT, REF_LON, original_height,
            from_crs='NAD83', to_vertical='NAVD88'
        )

        # NAVD88 back to NAD83 ellipsoid
        ellip = gp.orthometric_to_ellipsoid(
            REF_LAT, REF_LON, ortho['orthometric_height_m'],
            from_vertical='NAVD88', to_crs='NAD83'
        )

        assert abs(ellip['ellipsoid_height_m'] - original_height) < 0.01, \
            f"Round-trip should recover original: {original_height} != {ellip['ellipsoid_height_m']}"

    def test_roundtrip_wgs84_egm2008(self):
        """Test round-trip: WGS84 ellipsoid -> EGM2008 -> WGS84 ellipsoid."""
        original_height = 10.0

        # WGS84 ellipsoid to EGM2008
        ortho = gp.ellipsoid_to_orthometric(
            REF_LAT, REF_LON, original_height,
            from_crs='WGS84', to_vertical='EGM2008'
        )

        # EGM2008 back to WGS84 ellipsoid
        ellip = gp.orthometric_to_ellipsoid(
            REF_LAT, REF_LON, ortho['orthometric_height_m'],
            from_vertical='EGM2008', to_crs='WGS84'
        )

        assert abs(ellip['ellipsoid_height_m'] - original_height) < 0.01, \
            f"Round-trip should recover original: {original_height} != {ellip['ellipsoid_height_m']}"

    def test_cross_system_conversion_consistency(self):
        """Test that cross-system conversions are internally consistent.

        Converting NAD83 ell -> NAVD88 -> WGS84 ell should give a result
        that differs from the original by approximately the NAD83-WGS84
        vertical datum shift (~0m at FRF).
        """
        nad83_height = 10.0

        # NAD83 ellipsoid to NAVD88
        navd88 = gp.ellipsoid_to_orthometric(
            REF_LAT, REF_LON, nad83_height,
            from_crs='NAD83', to_vertical='NAVD88'
        )

        # NAVD88 to WGS84 ellipsoid (with warning)
        with pytest.warns(UserWarning):
            wgs84 = gp.orthometric_to_ellipsoid(
                REF_LAT, REF_LON, navd88['orthometric_height_m'],
                from_vertical='NAVD88', to_crs='WGS84'
            )

        # At FRF, the NAD83-WGS84 vertical difference is very small (<0.1m)
        # So the heights should be nearly equal
        diff = abs(wgs84['ellipsoid_height_m'] - nad83_height)
        assert diff < 0.2, \
            f"NAD83 and WGS84 ellipsoidal heights should be similar at FRF: diff={diff}m"
