"""
Tests for time_tracking.py - Time calculation and tracking operations.
"""
import pytest
import tempfile
import json
from pathlib import Path
from claude_skills.sdd_update.time_tracking import (
    calculate_time_from_timestamps,
    validate_timestamp_pair,
    aggregate_task_times
)
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

    def test_calculate_time_one_hour(self):
        """Test calculation with exactly 1 hour duration."""
        result = calculate_time_from_timestamps(
            "2025-10-27T10:00:00Z",
            "2025-10-27T11:00:00Z"
        )
        assert result == 1.0

    def test_calculate_time_two_and_half_hours(self):
        """Test calculation with 2.5 hour duration."""
        result = calculate_time_from_timestamps(
            "2025-10-27T09:00:00Z",
            "2025-10-27T11:30:00Z"
        )
        assert result == 2.5

    def test_calculate_time_six_minutes(self):
        """Test calculation with 0.1 hour (6 minute) duration."""
        result = calculate_time_from_timestamps(
            "2025-10-27T10:00:00Z",
            "2025-10-27T10:06:00Z"
        )
        assert result == 0.1

    def test_calculate_time_over_24_hours(self):
        """Test calculation with duration over 24 hours."""
        result = calculate_time_from_timestamps(
            "2025-10-27T10:00:00Z",
            "2025-10-28T14:00:00Z"
        )
        assert result == 28.0

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

    def test_calculate_time_both_none(self):
        """Test with both timestamps as None."""
        result = calculate_time_from_timestamps(None, None)
        assert result is None

    def test_calculate_time_end_none(self):
        """Test with end timestamp as None."""
        result = calculate_time_from_timestamps(
            "2025-10-27T10:00:00Z",
            None
        )
        assert result is None

    def test_calculate_time_whitespace_strings(self):
        """Test with whitespace-only strings."""
        result = calculate_time_from_timestamps(
            "   ",
            "2025-10-27T10:00:00Z"
        )
        assert result is None

    def test_calculate_time_very_large_difference(self):
        """Test with timestamps years apart."""
        result = calculate_time_from_timestamps(
            "2020-01-01T00:00:00Z",
            "2025-10-27T10:00:00Z"
        )
        # Approximately 5 years, 9 months, 26 days, 10 hours
        # 5*365*24 + 9*30*24 + 26*24 + 10 ≈ 50,578 hours
        assert result > 50000  # Large positive number
        assert isinstance(result, float)

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


class TestAggregateTaskTimes:
    """Test aggregate_task_times() function."""

    def _create_test_spec(self, spec_id: str, hierarchy: dict, specs_dir: Path) -> Path:
        """Helper to create a test spec file."""
        # Create active subdirectory (load_json_spec expects this structure)
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True, exist_ok=True)

        spec_file = active_dir / f"{spec_id}.json"
        spec_data = {
            "spec_id": spec_id,
            "generated": "2025-10-27T10:00:00Z",
            "hierarchy": hierarchy
        }
        with open(spec_file, 'w') as f:
            json.dump(spec_data, f, indent=2)
        return spec_file

    def test_aggregate_task_times_basic(self):
        """Test basic aggregation with multiple tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)
            hierarchy = {
                "task-1": {
                    "type": "task",
                    "title": "Task 1",
                    "status": "completed",
                    "metadata": {"actual_hours": 2.5}
                },
                "task-2": {
                    "type": "task",
                    "title": "Task 2",
                    "status": "completed",
                    "metadata": {"actual_hours": 3.0}
                },
                "task-3": {
                    "type": "task",
                    "title": "Task 3",
                    "status": "completed",
                    "metadata": {"actual_hours": 1.5}
                }
            }
            self._create_test_spec("test-spec-001", hierarchy, specs_dir)

            result = aggregate_task_times("test-spec-001", specs_dir)
            assert result == 7.0

    def test_aggregate_task_times_no_data(self):
        """Test with spec that has no actual_hours data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)
            hierarchy = {
                "task-1": {
                    "type": "task",
                    "title": "Task 1",
                    "status": "pending",
                    "metadata": {}
                },
                "task-2": {
                    "type": "task",
                    "title": "Task 2",
                    "status": "in_progress",
                    "metadata": {}
                }
            }
            self._create_test_spec("test-spec-002", hierarchy, specs_dir)

            result = aggregate_task_times("test-spec-002", specs_dir)
            assert result is None

    def test_aggregate_task_times_partial_data(self):
        """Test with spec that has partial actual_hours data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)
            hierarchy = {
                "task-1": {
                    "type": "task",
                    "title": "Task 1",
                    "status": "completed",
                    "metadata": {"actual_hours": 2.5}
                },
                "task-2": {
                    "type": "task",
                    "title": "Task 2",
                    "status": "in_progress",
                    "metadata": {}  # No actual_hours
                },
                "task-3": {
                    "type": "task",
                    "title": "Task 3",
                    "status": "completed",
                    "metadata": {"actual_hours": 3.0}
                }
            }
            self._create_test_spec("test-spec-003", hierarchy, specs_dir)

            result = aggregate_task_times("test-spec-003", specs_dir)
            assert result == 5.5

    def test_aggregate_task_times_nonexistent_spec(self):
        """Test with non-existent spec."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)

            result = aggregate_task_times("nonexistent-spec", specs_dir)
            assert result is None

    def test_aggregate_task_times_empty_hierarchy(self):
        """Test with spec that has empty hierarchy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)
            hierarchy = {}
            self._create_test_spec("test-spec-004", hierarchy, specs_dir)

            result = aggregate_task_times("test-spec-004", specs_dir)
            assert result is None

    def test_aggregate_task_times_mixed_node_types(self):
        """Test that only task-type nodes are counted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)
            hierarchy = {
                "spec-root": {
                    "type": "spec",
                    "title": "Root",
                    "metadata": {"actual_hours": 10.0}  # Should be ignored
                },
                "phase-1": {
                    "type": "phase",
                    "title": "Phase 1",
                    "metadata": {"actual_hours": 5.0}  # Should be ignored
                },
                "task-1": {
                    "type": "task",
                    "title": "Task 1",
                    "status": "completed",
                    "metadata": {"actual_hours": 2.5}  # Should be counted
                },
                "verify-1": {
                    "type": "verify",
                    "title": "Verify 1",
                    "metadata": {"actual_hours": 1.0}  # Should be ignored
                },
                "task-2": {
                    "type": "task",
                    "title": "Task 2",
                    "status": "completed",
                    "metadata": {"actual_hours": 3.0}  # Should be counted
                }
            }
            self._create_test_spec("test-spec-005", hierarchy, specs_dir)

            result = aggregate_task_times("test-spec-005", specs_dir)
            # Only task-1 and task-2 should be counted (2.5 + 3.0 = 5.5)
            assert result == 5.5

    def test_aggregate_task_times_invalid_values(self):
        """Test handling of invalid actual_hours values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)
            hierarchy = {
                "task-1": {
                    "type": "task",
                    "title": "Task 1",
                    "status": "completed",
                    "metadata": {"actual_hours": 2.5}  # Valid
                },
                "task-2": {
                    "type": "task",
                    "title": "Task 2",
                    "status": "completed",
                    "metadata": {"actual_hours": "invalid"}  # Invalid - should be skipped with warning
                },
                "task-3": {
                    "type": "task",
                    "title": "Task 3",
                    "status": "completed",
                    "metadata": {"actual_hours": 3.0}  # Valid
                }
            }
            self._create_test_spec("test-spec-006", hierarchy, specs_dir)

            result = aggregate_task_times("test-spec-006", specs_dir)
            # Only task-1 and task-3 should be counted (2.5 + 3.0 = 5.5)
            assert result == 5.5

    def test_aggregate_task_times_precision(self):
        """Test that result is rounded to 0.001 hour precision."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)
            hierarchy = {
                "task-1": {
                    "type": "task",
                    "title": "Task 1",
                    "status": "completed",
                    "metadata": {"actual_hours": 2.5555}
                },
                "task-2": {
                    "type": "task",
                    "title": "Task 2",
                    "status": "completed",
                    "metadata": {"actual_hours": 3.3333}
                }
            }
            self._create_test_spec("test-spec-007", hierarchy, specs_dir)

            result = aggregate_task_times("test-spec-007", specs_dir)
            # 2.5555 + 3.3333 = 5.8888, rounded to 5.889
            assert result == 5.889

    def test_aggregate_task_times_with_printer(self):
        """Test with custom printer for error messages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)
            hierarchy = {
                "task-1": {
                    "type": "task",
                    "title": "Task 1",
                    "status": "completed",
                    "metadata": {"actual_hours": 2.5}
                }
            }
            self._create_test_spec("test-spec-008", hierarchy, specs_dir)

            printer = PrettyPrinter()
            result = aggregate_task_times("test-spec-008", specs_dir, printer=printer)
            assert result == 2.5

    def test_aggregate_task_times_single_task(self):
        """Test aggregation with exactly one task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)
            hierarchy = {
                "task-1": {
                    "type": "task",
                    "title": "Task 1",
                    "status": "completed",
                    "metadata": {"actual_hours": 3.5}
                }
            }
            self._create_test_spec("test-spec-single", hierarchy, specs_dir)

            result = aggregate_task_times("test-spec-single", specs_dir)
            assert result == 3.5

    def test_aggregate_task_times_zero_hours(self):
        """Test aggregation with task having zero actual hours."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)
            hierarchy = {
                "task-1": {
                    "type": "task",
                    "title": "Task 1",
                    "status": "completed",
                    "metadata": {"actual_hours": 0.0}
                },
                "task-2": {
                    "type": "task",
                    "title": "Task 2",
                    "status": "completed",
                    "metadata": {"actual_hours": 2.5}
                }
            }
            self._create_test_spec("test-spec-zero", hierarchy, specs_dir)

            result = aggregate_task_times("test-spec-zero", specs_dir)
            assert result == 2.5

    def test_aggregate_task_times_negative_hours(self):
        """Test aggregation with negative actual hours (should include in sum)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)
            hierarchy = {
                "task-1": {
                    "type": "task",
                    "title": "Task 1",
                    "status": "completed",
                    "metadata": {"actual_hours": 5.0}
                },
                "task-2": {
                    "type": "task",
                    "title": "Task 2",
                    "status": "completed",
                    "metadata": {"actual_hours": -1.0}
                }
            }
            self._create_test_spec("test-spec-negative", hierarchy, specs_dir)

            result = aggregate_task_times("test-spec-negative", specs_dir)
            assert result == 4.0
