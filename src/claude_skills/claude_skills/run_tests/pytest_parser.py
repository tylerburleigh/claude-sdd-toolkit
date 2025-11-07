"""
Pytest output parser for extracting test progress in real-time.

Parses pytest's verbose output line-by-line to extract test results,
track running counts, and calculate progress percentages.
"""

import re
from typing import Optional, NamedTuple
from enum import Enum


class TestStatus(Enum):
    """Test execution status."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"
    XFAIL = "XFAIL"  # Expected failure
    XPASS = "XPASS"  # Unexpected pass


class TestResult(NamedTuple):
    """Parsed test result from pytest output."""
    file_path: str
    test_name: str
    status: TestStatus
    percentage: Optional[int]  # Progress percentage (0-100)


class ProgressInfo(NamedTuple):
    """Current test execution progress."""
    passed: int
    failed: int
    skipped: int
    errors: int
    xfailed: int
    xpassed: int
    total_run: int
    percentage: Optional[int]


# Regex patterns for pytest output
# Matches: tests/test_file.py::test_name PASSED   [ 50%]
# Matches: tests/test_file.py::TestClass::test_method FAILED  [100%]
TEST_RESULT_PATTERN = re.compile(
    r'^(.+?)::([\w\[\]\-:,\.]+)\s+'  # file::test_name (with parametrize support)
    r'(PASSED|FAILED|SKIPPED|ERROR|XFAIL|XPASS)'  # status
    r'(?:\s+\[\s*(\d+)%\])?'  # optional percentage
)

# Alternative compact format: tests/test_file.py .F.s
# Not yet supported - future enhancement if needed


class PytestOutputParser:
    """
    Parser for pytest verbose output.

    Extracts test results line-by-line and maintains running counts.

    Usage:
        parser = PytestOutputParser()
        for line in pytest_output:
            result = parser.parse_line(line)
            if result:
                progress = parser.get_progress()
                print(f"{progress.passed} passed, {progress.failed} failed")
    """

    def __init__(self):
        """Initialize parser with zero counts."""
        self._passed = 0
        self._failed = 0
        self._skipped = 0
        self._errors = 0
        self._xfailed = 0
        self._xpassed = 0
        self._last_percentage: Optional[int] = None

    def parse_line(self, line: str) -> Optional[TestResult]:
        """
        Parse a single line of pytest output.

        Args:
            line: Output line from pytest

        Returns:
            TestResult if line contains a test result, None otherwise

        Examples:
            >>> parser = PytestOutputParser()
            >>> result = parser.parse_line("tests/test_auth.py::test_login PASSED  [ 50%]")
            >>> result.status
            <TestStatus.PASSED: 'PASSED'>
            >>> result.percentage
            50
        """
        # Strip ANSI color codes if present
        line = self._strip_ansi(line)

        # Try to match test result pattern
        match = TEST_RESULT_PATTERN.match(line.strip())
        if not match:
            return None

        file_path, test_name, status_str, percentage_str = match.groups()

        # Parse status
        try:
            status = TestStatus(status_str)
        except ValueError:
            return None  # Unknown status

        # Parse percentage
        percentage = int(percentage_str) if percentage_str else None
        if percentage is not None:
            self._last_percentage = percentage

        # Create result
        result = TestResult(
            file_path=file_path,
            test_name=test_name,
            status=status,
            percentage=percentage
        )

        # Update counts
        self._update_counts(result)

        return result

    def _update_counts(self, result: TestResult) -> None:
        """
        Update running counts based on test result.

        Args:
            result: Test result to count
        """
        if result.status == TestStatus.PASSED:
            self._passed += 1
        elif result.status == TestStatus.FAILED:
            self._failed += 1
        elif result.status == TestStatus.SKIPPED:
            self._skipped += 1
        elif result.status == TestStatus.ERROR:
            self._errors += 1
        elif result.status == TestStatus.XFAIL:
            self._xfailed += 1
        elif result.status == TestStatus.XPASS:
            self._xpassed += 1

    def get_progress(self) -> ProgressInfo:
        """
        Get current progress information.

        Returns:
            ProgressInfo with current counts and percentage
        """
        total_run = (
            self._passed + self._failed + self._skipped +
            self._errors + self._xfailed + self._xpassed
        )

        return ProgressInfo(
            passed=self._passed,
            failed=self._failed,
            skipped=self._skipped,
            errors=self._errors,
            xfailed=self._xfailed,
            xpassed=self._xpassed,
            total_run=total_run,
            percentage=self._last_percentage
        )

    def reset(self) -> None:
        """Reset all counts to zero."""
        self._passed = 0
        self._failed = 0
        self._skipped = 0
        self._errors = 0
        self._xfailed = 0
        self._xpassed = 0
        self._last_percentage = None

    @staticmethod
    def _strip_ansi(text: str) -> str:
        """
        Remove ANSI color codes from text.

        Args:
            text: Text potentially containing ANSI codes

        Returns:
            Text with ANSI codes removed
        """
        # ANSI escape sequence pattern
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
        return ansi_pattern.sub('', text)


def format_progress_summary(progress: ProgressInfo) -> str:
    """
    Format progress info as a human-readable summary.

    Args:
        progress: Progress information to format

    Returns:
        Formatted summary string

    Examples:
        >>> progress = ProgressInfo(passed=10, failed=2, skipped=1, errors=0,
        ...                         xfailed=0, xpassed=0, total_run=13, percentage=65)
        >>> format_progress_summary(progress)
        '10 passed, 2 failed, 1 skipped (65%)'
    """
    parts = []

    if progress.passed > 0:
        parts.append(f"{progress.passed} passed")
    if progress.failed > 0:
        parts.append(f"{progress.failed} failed")
    if progress.skipped > 0:
        parts.append(f"{progress.skipped} skipped")
    if progress.errors > 0:
        parts.append(f"{progress.errors} errors")
    if progress.xfailed > 0:
        parts.append(f"{progress.xfailed} xfailed")
    if progress.xpassed > 0:
        parts.append(f"{progress.xpassed} xpassed")

    summary = ", ".join(parts) if parts else "No tests run"

    if progress.percentage is not None:
        summary += f" ({progress.percentage}%)"

    return summary


class PytestProgressDisplay:
    """
    Rich.Progress display for pytest test execution.

    Shows a live progress bar with pass/fail/skip counters as tests run,
    plus the currently running test file.

    Usage:
        from rich.progress import Progress

        with Progress() as progress:
            display = PytestProgressDisplay(progress, total_tests=100)
            parser = PytestOutputParser()

            for line in pytest_output:
                result = parser.parse_line(line)
                if result:
                    display.update(parser.get_progress(), current_file=result.file_path)
    """

    def __init__(self, progress, total_tests: Optional[int] = None):
        """
        Initialize progress display.

        Args:
            progress: Rich Progress instance
            total_tests: Optional total number of tests (if known)
        """
        self.progress = progress
        self.total_tests = total_tests
        self._last_file: Optional[str] = None

        # Create progress task
        description = "Running tests"
        if total_tests:
            self.task_id = self.progress.add_task(
                description,
                total=total_tests
            )
        else:
            # Indeterminate progress (no total known)
            self.task_id = self.progress.add_task(
                description,
                total=None
            )

    def update(self, progress_info: ProgressInfo, current_file: Optional[str] = None) -> None:
        """
        Update progress display with new test results.

        Args:
            progress_info: Current progress information from parser
            current_file: Optional currently running test file path
        """
        # Track last file if provided
        if current_file is not None:
            self._last_file = current_file

        # Build description with counters
        parts = []
        if progress_info.passed > 0:
            parts.append(f"[green]{progress_info.passed} passed[/green]")
        if progress_info.failed > 0:
            parts.append(f"[red]{progress_info.failed} failed[/red]")
        if progress_info.skipped > 0:
            parts.append(f"[yellow]{progress_info.skipped} skipped[/yellow]")
        if progress_info.errors > 0:
            parts.append(f"[red]{progress_info.errors} errors[/red]")

        description = "Running tests: " + ", ".join(parts) if parts else "Running tests"

        # Add current file if available
        if self._last_file:
            # Show just the filename, not full path
            filename = self._last_file.split('/')[-1]
            description += f" [dim]({filename})[/dim]"

        # Update progress
        if self.total_tests is not None:
            # Known total - update completed count
            self.progress.update(
                self.task_id,
                completed=progress_info.total_run,
                description=description
            )
        else:
            # Unknown total - show as indeterminate with count
            self.progress.update(
                self.task_id,
                description=f"{description} ({progress_info.total_run} run)"
            )

    def finish(self, progress_info: ProgressInfo) -> None:
        """
        Mark progress as complete.

        Args:
            progress_info: Final progress information
        """
        # Build final description
        parts = []
        if progress_info.passed > 0:
            parts.append(f"[green]{progress_info.passed} passed[/green]")
        if progress_info.failed > 0:
            parts.append(f"[red]{progress_info.failed} failed[/red]")
        if progress_info.skipped > 0:
            parts.append(f"[yellow]{progress_info.skipped} skipped[/yellow]")
        if progress_info.errors > 0:
            parts.append(f"[red]{progress_info.errors} errors[/red]")

        description = "Tests complete: " + ", ".join(parts) if parts else "Tests complete"

        # Mark as complete
        if self.total_tests is not None:
            self.progress.update(
                self.task_id,
                completed=self.total_tests,
                description=description
            )
        else:
            self.progress.update(
                self.task_id,
                description=description
            )


__all__ = [
    "TestStatus",
    "TestResult",
    "ProgressInfo",
    "PytestOutputParser",
    "PytestProgressDisplay",
    "format_progress_summary",
]
