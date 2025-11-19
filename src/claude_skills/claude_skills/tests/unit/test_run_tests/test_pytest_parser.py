from __future__ import annotations

"""Unit tests covering the pytest output parser and progress display."""

from unittest.mock import Mock

import pytest

from claude_skills.run_tests.pytest_parser import (
    ProgressInfo,
    PytestOutputParser,
    PytestProgressDisplay,
    TestStatus,
    format_progress_summary,
)

pytestmark = pytest.mark.unit

# Prevent pytest from treating imported helper classes as tests.
TestStatus.__test__ = False  # type: ignore[attr-defined]


class TestPytestOutputParser:
    """Test suite for PytestOutputParser."""

    def test_parse_passed_test(self) -> None:
        """Test parsing a PASSED test result."""
        parser = PytestOutputParser()
        line = "tests/test_auth.py::test_login PASSED  [ 50%]"

        result = parser.parse_line(line)

        assert result is not None
        assert result.file_path == "tests/test_auth.py"
        assert result.test_name == "test_login"
        assert result.status == TestStatus.PASSED
        assert result.percentage == 50

    def test_parse_failed_test(self) -> None:
        """Test parsing a FAILED test result."""
        parser = PytestOutputParser()
        line = "tests/test_auth.py::test_validation FAILED  [ 75%]"

        result = parser.parse_line(line)

        assert result is not None
        assert result.file_path == "tests/test_auth.py"
        assert result.test_name == "test_validation"
        assert result.status == TestStatus.FAILED
        assert result.percentage == 75

    def test_parse_skipped_test(self) -> None:
        """Test parsing a SKIPPED test result."""
        parser = PytestOutputParser()
        line = "tests/test_integration.py::test_slow SKIPPED  [ 25%]"

        result = parser.parse_line(line)

        assert result is not None
        assert result.status == TestStatus.SKIPPED
        assert result.percentage == 25

    def test_parse_error_test(self) -> None:
        """Test parsing an ERROR test result."""
        parser = PytestOutputParser()
        line = "tests/test_setup.py::test_fixture ERROR  [100%]"

        result = parser.parse_line(line)

        assert result is not None
        assert result.status == TestStatus.ERROR
        assert result.percentage == 100

    def test_parse_xfail_test(self) -> None:
        """Test parsing an XFAIL test result."""
        parser = PytestOutputParser()
        line = "tests/test_known_issues.py::test_bug_123 XFAIL  [ 33%]"

        result = parser.parse_line(line)

        assert result is not None
        assert result.status == TestStatus.XFAIL
        assert result.percentage == 33

    def test_parse_xpass_test(self) -> None:
        """Test parsing an XPASS test result."""
        parser = PytestOutputParser()
        line = "tests/test_known_issues.py::test_bug_456 XPASS  [ 66%]"

        result = parser.parse_line(line)

        assert result is not None
        assert result.status == TestStatus.XPASS
        assert result.percentage == 66

    def test_parse_test_without_percentage(self) -> None:
        """Test parsing test result without percentage."""
        parser = PytestOutputParser()
        line = "tests/test_auth.py::test_login PASSED"

        result = parser.parse_line(line)

        assert result is not None
        assert result.status == TestStatus.PASSED
        assert result.percentage is None

    def test_parse_parametrized_test(self) -> None:
        """Test parsing parametrized test names."""
        parser = PytestOutputParser()
        line = "tests/test_auth.py::test_validation[case1] PASSED  [ 10%]"

        result = parser.parse_line(line)

        assert result is not None
        assert result.test_name == "test_validation[case1]"
        assert result.status == TestStatus.PASSED

    def test_parse_class_method(self) -> None:
        """Test parsing test class method."""
        parser = PytestOutputParser()
        line = "tests/test_auth.py::TestAuth::test_login PASSED  [ 20%]"

        result = parser.parse_line(line)

        assert result is not None
        assert result.test_name == "TestAuth::test_login"
        assert result.status == TestStatus.PASSED

    def test_parse_nested_path(self) -> None:
        """Test parsing test with nested directory structure."""
        parser = PytestOutputParser()
        line = "tests/integration/auth/test_oauth.py::test_flow PASSED  [ 30%]"

        result = parser.parse_line(line)

        assert result is not None
        assert result.file_path == "tests/integration/auth/test_oauth.py"
        assert result.test_name == "test_flow"

    def test_parse_non_test_line(self) -> None:
        """Test that non-test lines return None."""
        parser = PytestOutputParser()

        # Try various non-test lines
        assert parser.parse_line("") is None
        assert parser.parse_line("collecting ... 100 items") is None
        assert parser.parse_line("=== test session starts ===") is None
        assert parser.parse_line("platform linux -- Python 3.9.0") is None

    def test_parse_with_ansi_codes(self) -> None:
        """Test parsing line with ANSI color codes."""
        parser = PytestOutputParser()
        # ANSI codes: \x1b[32m for green, \x1b[0m for reset
        line = "\x1b[32mtests/test_auth.py::test_login PASSED\x1b[0m  [ 50%]"

        result = parser.parse_line(line)

        assert result is not None
        assert result.status == TestStatus.PASSED
        assert result.percentage == 50

    def test_count_tracking_multiple_tests(self) -> None:
        """Test that counts are tracked correctly across multiple tests."""
        parser = PytestOutputParser()

        parser.parse_line("tests/test_1.py::test_a PASSED  [ 25%]")
        parser.parse_line("tests/test_1.py::test_b PASSED  [ 50%]")
        parser.parse_line("tests/test_2.py::test_c FAILED  [ 75%]")
        parser.parse_line("tests/test_2.py::test_d SKIPPED  [100%]")

        progress = parser.get_progress()

        assert progress.passed == 2
        assert progress.failed == 1
        assert progress.skipped == 1
        assert progress.errors == 0
        assert progress.total_run == 4
        assert progress.percentage == 100

    def test_count_tracking_with_errors(self) -> None:
        """Test count tracking including errors."""
        parser = PytestOutputParser()

        parser.parse_line("tests/test_1.py::test_a PASSED  [ 20%]")
        parser.parse_line("tests/test_2.py::test_b ERROR  [ 40%]")
        parser.parse_line("tests/test_3.py::test_c FAILED  [ 60%]")
        parser.parse_line("tests/test_4.py::test_d ERROR  [ 80%]")
        parser.parse_line("tests/test_5.py::test_e PASSED  [100%]")

        progress = parser.get_progress()

        assert progress.passed == 2
        assert progress.failed == 1
        assert progress.errors == 2
        assert progress.total_run == 5

    def test_count_tracking_with_xfail_xpass(self) -> None:
        """Test count tracking with xfail and xpass."""
        parser = PytestOutputParser()

        parser.parse_line("tests/test_1.py::test_a PASSED  [ 20%]")
        parser.parse_line("tests/test_2.py::test_b XFAIL  [ 40%]")
        parser.parse_line("tests/test_3.py::test_c XPASS  [ 60%]")
        parser.parse_line("tests/test_4.py::test_d PASSED  [ 80%]")
        parser.parse_line("tests/test_5.py::test_e FAILED  [100%]")

        progress = parser.get_progress()

        assert progress.passed == 2
        assert progress.failed == 1
        assert progress.xfailed == 1
        assert progress.xpassed == 1
        assert progress.total_run == 5

    def test_get_progress_empty(self) -> None:
        """Test get_progress with no tests parsed."""
        parser = PytestOutputParser()

        progress = parser.get_progress()

        assert progress.passed == 0
        assert progress.failed == 0
        assert progress.skipped == 0
        assert progress.errors == 0
        assert progress.total_run == 0
        assert progress.percentage is None

    def test_reset(self) -> None:
        """Test that reset clears all counts."""
        parser = PytestOutputParser()

        parser.parse_line("tests/test_1.py::test_a PASSED  [ 50%]")
        parser.parse_line("tests/test_2.py::test_b FAILED  [100%]")

        progress_before = parser.get_progress()
        assert progress_before.total_run == 2

        parser.reset()

        progress_after = parser.get_progress()
        assert progress_after.passed == 0
        assert progress_after.failed == 0
        assert progress_after.total_run == 0
        assert progress_after.percentage is None

    def test_percentage_retained_across_lines(self) -> None:
        """Test that last percentage is retained for tests without percentage."""
        parser = PytestOutputParser()

        parser.parse_line("tests/test_1.py::test_a PASSED  [ 50%]")
        progress1 = parser.get_progress()
        assert progress1.percentage == 50

        # Parse line without percentage
        parser.parse_line("tests/test_2.py::test_b PASSED")
        progress2 = parser.get_progress()
        assert progress2.percentage == 50  # Should retain last percentage

        parser.parse_line("tests/test_3.py::test_c FAILED  [100%]")
        progress3 = parser.get_progress()
        assert progress3.percentage == 100


class TestFormatProgressSummary:
    """Test suite for format_progress_summary."""

    def test_format_all_passed(self) -> None:
        """Test formatting when all tests passed."""
        progress = ProgressInfo(
            passed=10,
            failed=0,
            skipped=0,
            errors=0,
            xfailed=0,
            xpassed=0,
            total_run=10,
            percentage=100,
        )

        summary = format_progress_summary(progress)

        assert summary == "10 passed (100%)"

    def test_format_mixed_results(self) -> None:
        """Test formatting with mixed results."""
        progress = ProgressInfo(
            passed=10,
            failed=2,
            skipped=1,
            errors=0,
            xfailed=0,
            xpassed=0,
            total_run=13,
            percentage=65,
        )

        summary = format_progress_summary(progress)

        assert "10 passed" in summary
        assert "2 failed" in summary
        assert "1 skipped" in summary
        assert "(65%)" in summary

    def test_format_with_errors(self) -> None:
        """Test formatting with errors."""
        progress = ProgressInfo(
            passed=5,
            failed=1,
            skipped=0,
            errors=2,
            xfailed=0,
            xpassed=0,
            total_run=8,
            percentage=80,
        )

        summary = format_progress_summary(progress)

        assert "5 passed" in summary
        assert "1 failed" in summary
        assert "2 errors" in summary

    def test_format_with_xfail_xpass(self) -> None:
        """Test formatting with xfail and xpass."""
        progress = ProgressInfo(
            passed=10,
            failed=0,
            skipped=0,
            errors=0,
            xfailed=2,
            xpassed=1,
            total_run=13,
            percentage=100,
        )

        summary = format_progress_summary(progress)

        assert "10 passed" in summary
        assert "2 xfailed" in summary
        assert "1 xpassed" in summary

    def test_format_without_percentage(self) -> None:
        """Test formatting without percentage."""
        progress = ProgressInfo(
            passed=5,
            failed=1,
            skipped=0,
            errors=0,
            xfailed=0,
            xpassed=0,
            total_run=6,
            percentage=None,
        )

        summary = format_progress_summary(progress)

        assert "5 passed" in summary
        assert "1 failed" in summary
        assert "%" not in summary

    def test_format_no_tests(self) -> None:
        """Test formatting when no tests run."""
        progress = ProgressInfo(
            passed=0,
            failed=0,
            skipped=0,
            errors=0,
            xfailed=0,
            xpassed=0,
            total_run=0,
            percentage=None,
        )

        summary = format_progress_summary(progress)

        assert summary == "No tests run"


class TestPytestProgressDisplay:
    """Test suite for PytestProgressDisplay."""

    def test_init_with_total(self) -> None:
        """Test initialization with known total tests."""
        mock_progress = Mock()
        mock_progress.add_task.return_value = 123

        display = PytestProgressDisplay(mock_progress, total_tests=100)

        assert display.total_tests == 100
        assert display.task_id == 123
        mock_progress.add_task.assert_called_once_with("Running tests", total=100)

    def test_init_without_total(self) -> None:
        """Test initialization without known total."""
        mock_progress = Mock()
        mock_progress.add_task.return_value = 456

        display = PytestProgressDisplay(mock_progress, total_tests=None)

        assert display.total_tests is None
        assert display.task_id == 456
        mock_progress.add_task.assert_called_once_with("Running tests", total=None)

    def test_update_with_passed_tests(self) -> None:
        """Test updating display with passed tests."""
        mock_progress = Mock()
        mock_progress.add_task.return_value = 1

        display = PytestProgressDisplay(mock_progress, total_tests=100)

        progress_info = ProgressInfo(
            passed=5,
            failed=0,
            skipped=0,
            errors=0,
            xfailed=0,
            xpassed=0,
            total_run=5,
            percentage=5,
        )

        display.update(progress_info)

        mock_progress.update.assert_called_once()
        call_args = mock_progress.update.call_args
        assert call_args[0][0] == 1  # task_id as first positional arg
        assert call_args[1]["completed"] == 5
        assert "5 passed" in call_args[1]["description"]

    def test_update_with_mixed_results(self) -> None:
        """Test updating display with mixed test results."""
        mock_progress = Mock()
        mock_progress.add_task.return_value = 1

        display = PytestProgressDisplay(mock_progress, total_tests=100)

        progress_info = ProgressInfo(
            passed=10,
            failed=2,
            skipped=1,
            errors=0,
            xfailed=0,
            xpassed=0,
            total_run=13,
            percentage=13,
        )

        display.update(progress_info)

        call_args = mock_progress.update.call_args
        description = call_args[1]["description"]
        assert "10 passed" in description
        assert "2 failed" in description
        assert "1 skipped" in description
        assert call_args[1]["completed"] == 13

    def test_update_without_total(self) -> None:
        """Test updating display when total is unknown."""
        mock_progress = Mock()
        mock_progress.add_task.return_value = 1

        display = PytestProgressDisplay(mock_progress, total_tests=None)

        progress_info = ProgressInfo(
            passed=5,
            failed=1,
            skipped=0,
            errors=0,
            xfailed=0,
            xpassed=0,
            total_run=6,
            percentage=None,
        )

        display.update(progress_info)

        call_args = mock_progress.update.call_args
        description = call_args[1]["description"]
        assert "5 passed" in description
        assert "1 failed" in description
        assert "(6 run)" in description

    def test_update_with_errors(self) -> None:
        """Test updating display with errors."""
        mock_progress = Mock()
        mock_progress.add_task.return_value = 1

        display = PytestProgressDisplay(mock_progress, total_tests=50)

        progress_info = ProgressInfo(
            passed=10,
            failed=2,
            skipped=0,
            errors=3,
            xfailed=0,
            xpassed=0,
            total_run=15,
            percentage=30,
        )

        display.update(progress_info)

        call_args = mock_progress.update.call_args
        description = call_args[1]["description"]
        assert "10 passed" in description
        assert "2 failed" in description
        assert "3 errors" in description

    def test_finish_with_total(self) -> None:
        """Test finishing progress with known total."""
        mock_progress = Mock()
        mock_progress.add_task.return_value = 1

        display = PytestProgressDisplay(mock_progress, total_tests=100)

        progress_info = ProgressInfo(
            passed=95,
            failed=3,
            skipped=2,
            errors=0,
            xfailed=0,
            xpassed=0,
            total_run=100,
            percentage=100,
        )

        display.finish(progress_info)

        call_args = mock_progress.update.call_args
        assert call_args[0][0] == 1  # task_id as first positional arg
        assert call_args[1]["completed"] == 100
        description = call_args[1]["description"]
        assert "Tests complete" in description
        assert "95 passed" in description
        assert "3 failed" in description
        assert "2 skipped" in description

    def test_finish_without_total(self) -> None:
        """Test finishing progress without known total."""
        mock_progress = Mock()
        mock_progress.add_task.return_value = 1

        display = PytestProgressDisplay(mock_progress, total_tests=None)

        progress_info = ProgressInfo(
            passed=50,
            failed=5,
            skipped=0,
            errors=0,
            xfailed=0,
            xpassed=0,
            total_run=55,
            percentage=None,
        )

        display.finish(progress_info)

        call_args = mock_progress.update.call_args
        description = call_args[1]["description"]
        assert "Tests complete" in description
        assert "50 passed" in description
        assert "5 failed" in description

    def test_color_formatting_in_description(self) -> None:
        """Test that descriptions include Rich color formatting."""
        mock_progress = Mock()
        mock_progress.add_task.return_value = 1

        display = PytestProgressDisplay(mock_progress, total_tests=10)

        progress_info = ProgressInfo(
            passed=5,
            failed=2,
            skipped=1,
            errors=0,
            xfailed=0,
            xpassed=0,
            total_run=8,
            percentage=80,
        )

        display.update(progress_info)

        call_args = mock_progress.update.call_args
        description = call_args[1]["description"]

        # Check for Rich color tags
        assert "[green]" in description  # passed should be green
        assert "[red]" in description  # failed should be red
        assert "[yellow]" in description  # skipped should be yellow

    def test_update_with_current_file(self) -> None:
        """Test that current file is displayed in description."""
        mock_progress = Mock()
        mock_progress.add_task.return_value = 1

        display = PytestProgressDisplay(mock_progress, total_tests=10)

        progress_info = ProgressInfo(
            passed=3,
            failed=0,
            skipped=0,
            errors=0,
            xfailed=0,
            xpassed=0,
            total_run=3,
            percentage=30,
        )

        display.update(progress_info, current_file="tests/integration/test_auth.py")

        call_args = mock_progress.update.call_args
        description = call_args[1]["description"]

        # Should show filename (not full path)
        assert "test_auth.py" in description
        # Should be dimmed
        assert "[dim]" in description

    def test_update_retains_last_file(self) -> None:
        """Test that last file is retained across updates without file."""
        mock_progress = Mock()
        mock_progress.add_task.return_value = 1

        display = PytestProgressDisplay(mock_progress, total_tests=10)

        # First update with file
        progress1 = ProgressInfo(1, 0, 0, 0, 0, 0, 1, 10)
        display.update(progress1, current_file="tests/test_a.py")

        # Second update without file (should retain last file)
        progress2 = ProgressInfo(2, 0, 0, 0, 0, 0, 2, 20)
        display.update(progress2)

        call_args = mock_progress.update.call_args
        description = call_args[1]["description"]

        # Should still show last file
        assert "test_a.py" in description

    def test_update_changes_file(self) -> None:
        """Test that current file updates when new file provided."""
        mock_progress = Mock()
        mock_progress.add_task.return_value = 1

        display = PytestProgressDisplay(mock_progress, total_tests=10)

        # First update with file A
        progress1 = ProgressInfo(1, 0, 0, 0, 0, 0, 1, 10)
        display.update(progress1, current_file="tests/test_a.py")

        # Second update with file B
        progress2 = ProgressInfo(2, 0, 0, 0, 0, 0, 2, 20)
        display.update(progress2, current_file="tests/test_b.py")

        call_args = mock_progress.update.call_args
        description = call_args[1]["description"]

        # Should show new file
        assert "test_b.py" in description
        # Should NOT show old file
        assert "test_a.py" not in description

    def test_update_filename_only_not_path(self) -> None:
        """Test that only filename is shown, not full path."""
        mock_progress = Mock()
        mock_progress.add_task.return_value = 1

        display = PytestProgressDisplay(mock_progress, total_tests=10)

        progress_info = ProgressInfo(1, 0, 0, 0, 0, 0, 1, 10)
        display.update(
            progress_info, current_file="tests/integration/auth/test_oauth_flow.py"
        )

        call_args = mock_progress.update.call_args
        description = call_args[1]["description"]

        # Should show only filename
        assert "test_oauth_flow.py" in description
        # Should NOT show directory structure
        assert "tests/integration/auth/" not in description
