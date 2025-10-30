"""
Tests for time_tracking.py - Time calculation and tracking operations.
"""
import pytest
from claude_skills.sdd_update.time_tracking import calculate_time_from_timestamps, validate_timestamp_pair
from claude_skills.common.printer import PrettyPrinter


class TestCalculateTimeFromTimestamps:
    """Test calculate_time_from_timestamps() function."""

    def test_calculate_time_basic(self):
        """Test basic time calculation with fractional hours."""
        result = calculate_time_from_timestamps(
            "2025-10-27T10:00:00Z",
            "2025-10-27T13:30:00Z"
        )
        assert result == 3.5

    def test_calculate_time_whole_hours(self):
        """Test calculation with whole hours."""
        result = calculate_time_from_timestamps(
            "2025-10-27T09:00:00Z",
            "2025-10-27T12:00:00Z"
        )
        assert result == 3.0

    def test_calculate_time_fractional(self):
        """Test calculation with small fractional duration."""
        result = calculate_time_from_timestamps(
            "2025-10-27T10:00:00Z",
            "2025-10-27T10:15:00Z"
        )
        # 15 minutes = 0.25 hours, rounds to 0.25 with 0.001 hour precision
        assert result == 0.25

    def test_calculate_time_across_days(self):
        """Test calculation across day boundary."""
        result = calculate_time_from_timestamps(
            "2025-10-27T22:00:00Z",
            "2025-10-28T02:00:00Z"
        )
        assert result == 4.0

    def test_calculate_time_with_timezone_offset(self):
        """Test with +00:00 timezone offset format."""
        result = calculate_time_from_timestamps(
            "2025-10-27T10:00:00+00:00",
            "2025-10-27T13:00:00+00:00"
        )
        assert result == 3.0

    def test_calculate_time_invalid_format(self):
        """Test with invalid timestamp format."""
        result = calculate_time_from_timestamps(
            "invalid",
            "2025-10-27T13:00:00Z"
        )
        assert result is None

    def test_calculate_time_negative_duration(self):
        """Test with end timestamp before start (negative duration)."""
        result = calculate_time_from_timestamps(
            "2025-10-27T13:00:00Z",
            "2025-10-27T10:00:00Z"
        )
        assert result == -3.0

    def test_calculate_time_same_timestamp(self):
        """Test with identical timestamps (zero duration)."""
        result = calculate_time_from_timestamps(
            "2025-10-27T10:00:00Z",
            "2025-10-27T10:00:00Z"
        )
        assert result == 0.0

    def test_calculate_time_with_seconds(self):
        """Test calculation with seconds precision."""
        result = calculate_time_from_timestamps(
            "2025-10-27T10:00:00Z",
            "2025-10-27T10:01:30Z"
        )
        # 1 minute 30 seconds = 1.5 minutes = 0.025 hours
        assert result == 0.025  # Rounded to 0.001 hour precision (3.6 second increments)

    def test_calculate_time_missing_z_suffix(self):
        """Test with ISO format without Z suffix."""
        result = calculate_time_from_timestamps(
            "2025-10-27T10:00:00",
            "2025-10-27T13:00:00"
        )
        assert result == 3.0

    def test_calculate_time_none_input(self):
        """Test with None input."""
        result = calculate_time_from_timestamps(
            None,
            "2025-10-27T13:00:00Z"
        )
        assert result is None

    def test_calculate_time_empty_string(self):
        """Test with empty string input."""
        result = calculate_time_from_timestamps(
            "",
            "2025-10-27T13:00:00Z"
        )
        assert result is None

    def test_calculate_time_with_printer_none_input(self):
        """Test error message for None input with printer."""
        printer = PrettyPrinter()
        result = calculate_time_from_timestamps(
            None,
            "2025-10-27T10:00:00Z",
            printer=printer
        )
        assert result is None

    def test_calculate_time_with_printer_invalid_format(self):
        """Test error message for invalid format with printer."""
        printer = PrettyPrinter()
        result = calculate_time_from_timestamps(
            "invalid",
            "2025-10-27T10:00:00Z",
            printer=printer
        )
        assert result is None

    def test_calculate_time_with_printer_negative_duration(self):
        """Test warning for negative duration with printer."""
        printer = PrettyPrinter()
        result = calculate_time_from_timestamps(
            "2025-10-27T13:00:00Z",
            "2025-10-27T10:00:00Z",
            printer=printer
        )
        # Should still return the negative value
        assert result == -3.0


class TestValidateTimestampPair:
    """Test validate_timestamp_pair() function."""

    def test_validate_timestamp_pair_valid(self):
        """Test validation for valid timestamp pair."""
        is_valid, error = validate_timestamp_pair(
            "2025-10-27T10:00:00Z",
            "2025-10-27T13:00:00Z"
        )
        assert is_valid is True
        assert error is None

    def test_validate_timestamp_pair_none_start(self):
        """Test validation catches None start timestamp."""
        is_valid, error = validate_timestamp_pair(
            None,
            "2025-10-27T13:00:00Z"
        )
        assert is_valid is False
        assert "Start timestamp is required" in error

    def test_validate_timestamp_pair_none_end(self):
        """Test validation catches None end timestamp."""
        is_valid, error = validate_timestamp_pair(
            "2025-10-27T10:00:00Z",
            None
        )
        assert is_valid is False
        assert "End timestamp is required" in error

    def test_validate_timestamp_pair_empty_start(self):
        """Test validation catches empty start timestamp."""
        is_valid, error = validate_timestamp_pair(
            "",
            "2025-10-27T13:00:00Z"
        )
        assert is_valid is False
        assert "Start timestamp is required" in error

    def test_validate_timestamp_pair_invalid_format(self):
        """Test validation catches invalid timestamp format."""
        is_valid, error = validate_timestamp_pair(
            "invalid",
            "2025-10-27T13:00:00Z"
        )
        assert is_valid is False
        assert "Invalid timestamp format" in error

    def test_validate_timestamp_pair_negative_disallowed(self):
        """Test validation catches negative duration when disallowed."""
        is_valid, error = validate_timestamp_pair(
            "2025-10-27T13:00:00Z",
            "2025-10-27T10:00:00Z",
            allow_negative=False
        )
        assert is_valid is False
        assert "before start" in error

    def test_validate_timestamp_pair_negative_allowed(self):
        """Test validation allows negative duration when allowed."""
        is_valid, error = validate_timestamp_pair(
            "2025-10-27T13:00:00Z",
            "2025-10-27T10:00:00Z",
            allow_negative=True
        )
        assert is_valid is True
        assert error is None

    def test_validate_timestamp_pair_with_printer(self):
        """Test validation with custom printer."""
        printer = PrettyPrinter()
        is_valid, error = validate_timestamp_pair(
            "2025-10-27T10:00:00Z",
            "2025-10-27T13:00:00Z",
            printer=printer
        )
        assert is_valid is True
        assert error is None
