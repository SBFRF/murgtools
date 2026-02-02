"""Tests for murgtools.utils.sblib utility functions."""

import pytest
import datetime as DT

from murgtools.utils.sblib import roundDatetimeToInterval
from murgtools.exceptions import InvalidParameterError


class TestRoundDatetimeToInterval:
    """Test roundDatetimeToInterval function."""

    def test_round_to_nearest_30min(self):
        """Test rounding to nearest 30-minute interval."""
        dt = DT.datetime(2024, 6, 15, 14, 23, 45)
        result = roundDatetimeToInterval(dt, 30, method='nearest')
        expected = DT.datetime(2024, 6, 15, 14, 30, 0)
        assert result == expected

    def test_round_to_floor_30min(self):
        """Test rounding down (floor) to 30-minute interval."""
        dt = DT.datetime(2024, 6, 15, 14, 23, 45)
        result = roundDatetimeToInterval(dt, 30, method='floor')
        expected = DT.datetime(2024, 6, 15, 14, 0, 0)
        assert result == expected

    def test_round_to_ceil_30min(self):
        """Test rounding up (ceil) to 30-minute interval."""
        dt = DT.datetime(2024, 6, 15, 14, 23, 45)
        result = roundDatetimeToInterval(dt, 30, method='ceil')
        expected = DT.datetime(2024, 6, 15, 14, 30, 0)
        assert result == expected

    def test_default_method_is_nearest(self):
        """Test that default method is 'nearest'."""
        dt = DT.datetime(2024, 6, 15, 14, 23, 45)
        result = roundDatetimeToInterval(dt, 30)
        expected = DT.datetime(2024, 6, 15, 14, 30, 0)
        assert result == expected

    def test_invalid_method_raises_error(self):
        """Test that invalid method raises InvalidParameterError."""
        dt = DT.datetime(2024, 6, 15, 14, 23, 45)
        with pytest.raises(InvalidParameterError) as exc_info:
            roundDatetimeToInterval(dt, 30, method='round')
        
        # Check error message details
        assert "Invalid rounding method: 'round'" in str(exc_info.value)
        assert exc_info.value.parameter_name == 'method'
        assert exc_info.value.value == 'round'
        assert "['nearest', 'floor', 'ceil']" in str(exc_info.value.expected)

    def test_invalid_method_average_raises_error(self):
        """Test that 'average' method raises InvalidParameterError."""
        dt = DT.datetime(2024, 6, 15, 14, 23, 45)
        with pytest.raises(InvalidParameterError) as exc_info:
            roundDatetimeToInterval(dt, 30, method='average')
        
        assert "Invalid rounding method: 'average'" in str(exc_info.value)

    def test_invalid_method_empty_string_raises_error(self):
        """Test that empty string method raises InvalidParameterError."""
        dt = DT.datetime(2024, 6, 15, 14, 23, 45)
        with pytest.raises(InvalidParameterError) as exc_info:
            roundDatetimeToInterval(dt, 30, method='')
        
        assert "Invalid rounding method: ''" in str(exc_info.value)

    def test_seconds_and_microseconds_zeroed(self):
        """Test that seconds and microseconds are always zeroed."""
        dt = DT.datetime(2024, 6, 15, 14, 30, 45, 123456)
        result = roundDatetimeToInterval(dt, 30, method='nearest')
        assert result.second == 0
        assert result.microsecond == 0

    def test_midnight_overflow(self):
        """Test handling of overflow past midnight."""
        dt = DT.datetime(2024, 6, 15, 23, 50, 0)
        result = roundDatetimeToInterval(dt, 30, method='ceil')
        expected = DT.datetime(2024, 6, 16, 0, 0, 0)
        assert result == expected
