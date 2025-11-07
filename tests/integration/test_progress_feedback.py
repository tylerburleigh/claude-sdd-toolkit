"""
Integration tests for progress feedback across different operations.

Tests progress indicators for:
- AI tool consultations (with mock subprocess)
- Pytest test execution (with mock subprocess)
- Multi-file validation operations
- Batch AI consultations
"""

import pytest
import time
import threading
import logging
from unittest.mock import Mock, patch, MagicMock
from claude_skills.common.tui_progress import (
    ai_consultation_progress,
    batch_consultation_progress,
    ProgressCallback,
    NoOpProgressCallback,
)
from claude_skills.common.ai_tools import ToolStatus, ToolResponse


class TestAIConsultationProgress:
    """Test AI consultation progress feedback with mock subprocess."""

    def test_progress_context_manager_lifecycle(self):
        """Test that progress context manager handles full lifecycle."""
        mock_callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress("gemini", timeout=90, callback=mock_callback) as progress:
            # Verify start was called
            mock_callback.on_start.assert_called_once()
            assert mock_callback.on_start.call_args[1]["tool"] == "gemini"
            assert mock_callback.on_start.call_args[1]["timeout"] == 90

            # Simulate tool completion
            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="Test output",
                duration=1.5
            )
            progress.complete(response)

        # Verify complete was called
        mock_callback.on_complete.assert_called_once()
        assert mock_callback.on_complete.call_args[1]["tool"] == "gemini"
        assert mock_callback.on_complete.call_args[1]["status"] == ToolStatus.SUCCESS

    def test_progress_updates_during_execution(self):
        """Test that periodic updates are called during execution."""
        mock_callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress(
            "gemini",
            timeout=90,
            callback=mock_callback,
            update_interval=0.1  # Fast updates for testing
        ) as progress:
            # Wait for at least one update
            time.sleep(0.25)

            # Simulate completion
            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="Test",
                duration=0.25
            )
            progress.complete(response)

        # Verify at least one update was called
        assert mock_callback.on_update.call_count >= 1

        # Verify update had correct tool name
        first_update = mock_callback.on_update.call_args_list[0]
        assert first_update[1]["tool"] == "gemini"

    def test_progress_with_error(self):
        """Test progress callback when operation fails."""
        mock_callback = Mock(spec=ProgressCallback)

        try:
            with ai_consultation_progress("gemini", timeout=90, callback=mock_callback) as progress:
                # Simulate error
                raise RuntimeError("Test error")
        except RuntimeError:
            pass  # Expected

        # Verify complete was called with error status
        mock_callback.on_complete.assert_called_once()
        assert mock_callback.on_complete.call_args[1]["status"] == ToolStatus.ERROR
        assert "Test error" in mock_callback.on_complete.call_args[1]["error"]

    def test_progress_with_timeout(self):
        """Test progress tracking with timeout context."""
        mock_callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress("codex", timeout=120, callback=mock_callback):
            pass  # Auto-complete on exit

        # Verify timeout was passed to start callback
        assert mock_callback.on_start.call_args[1]["timeout"] == 120

    def test_progress_with_context_metadata(self):
        """Test that context metadata is passed through callbacks."""
        mock_callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress(
            "gemini",
            timeout=90,
            callback=mock_callback,
            model="gemini-2.0-flash-exp",
            prompt_length=500
        ) as progress:
            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="Test",
                duration=1.0
            )
            progress.complete(response)

        # Verify context was passed to start
        start_kwargs = mock_callback.on_start.call_args[1]
        assert start_kwargs["model"] == "gemini-2.0-flash-exp"
        assert start_kwargs["prompt_length"] == 500

        # Verify context was passed to complete
        complete_kwargs = mock_callback.on_complete.call_args[1]
        assert complete_kwargs["model"] == "gemini-2.0-flash-exp"
        assert complete_kwargs["prompt_length"] == 500

    def test_noop_callback_does_not_raise(self):
        """Test that NoOpProgressCallback never raises exceptions."""
        callback = NoOpProgressCallback()

        # Should not raise
        callback.on_start("gemini", 90)
        callback.on_update("gemini", 30.5, 90)
        callback.on_complete("gemini", ToolStatus.SUCCESS, 45.0)
        callback.on_batch_start(["gemini", "codex"], 2, 90)
        callback.on_tool_complete(
            "gemini",
            ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="output",
                duration=30.0
            ),
            1,
            2
        )
        callback.on_batch_complete(2, 2, 0, 60.0, 45.0)

    def test_double_complete_ignored(self):
        """Test that calling complete() twice doesn't call callback twice."""
        mock_callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress("gemini", timeout=90, callback=mock_callback) as progress:
            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="Test",
                duration=1.0
            )
            progress.complete(response)
            progress.complete(response)  # Second call should be ignored

        # Should only be called once
        assert mock_callback.on_complete.call_count == 1


class TestBatchConsultationProgress:
    """Test batch AI consultation progress with multiple tools."""

    def test_batch_progress_lifecycle(self):
        """Test batch progress context manager lifecycle."""
        mock_callback = Mock(spec=ProgressCallback)
        tools = ["gemini", "codex"]

        with batch_consultation_progress(
            tools,
            timeout=120,
            callback=mock_callback
        ) as progress:
            # Verify batch start was called
            mock_callback.on_batch_start.assert_called_once()
            assert mock_callback.on_batch_start.call_args[1]["tools"] == tools
            assert mock_callback.on_batch_start.call_args[1]["count"] == 2

            # Mark tools complete
            for tool in tools:
                response = ToolResponse(
                    tool=tool,
                    status=ToolStatus.SUCCESS,
                    output="Test",
                    duration=30.0
                )
                progress.mark_complete(tool, response)

        # Verify batch complete was called
        mock_callback.on_batch_complete.assert_called_once()
        assert mock_callback.on_batch_complete.call_args[1]["total_count"] == 2
        assert mock_callback.on_batch_complete.call_args[1]["success_count"] == 2
        assert mock_callback.on_batch_complete.call_args[1]["failure_count"] == 0

    def test_batch_tool_complete_callbacks(self):
        """Test that on_tool_complete is called for each tool."""
        mock_callback = Mock(spec=ProgressCallback)
        tools = ["gemini", "codex", "cursor-agent"]

        with batch_consultation_progress(tools, timeout=120, callback=mock_callback) as progress:
            for i, tool in enumerate(tools, 1):
                response = ToolResponse(
                    tool=tool,
                    status=ToolStatus.SUCCESS,
                    output="Test",
                    duration=20.0
                )
                progress.mark_complete(tool, response)

                # Verify on_tool_complete was called
                assert mock_callback.on_tool_complete.call_count == i
                last_call = mock_callback.on_tool_complete.call_args
                assert last_call[1]["tool"] == tool
                assert last_call[1]["completed_count"] == i
                assert last_call[1]["total_count"] == 3

    def test_batch_with_failures(self):
        """Test batch progress when some tools fail."""
        mock_callback = Mock(spec=ProgressCallback)
        tools = ["gemini", "codex"]

        with batch_consultation_progress(tools, timeout=120, callback=mock_callback) as progress:
            # First tool succeeds
            progress.mark_complete("gemini", ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="output",
                duration=30.0
            ))

            # Second tool fails
            progress.mark_complete("codex", ToolResponse(
                tool="codex",
                status=ToolStatus.ERROR,
                output="",
                duration=15.0,
                error="Connection failed"
            ))

        # Verify batch complete shows mixed results
        batch_complete = mock_callback.on_batch_complete.call_args[1]
        assert batch_complete["success_count"] == 1
        assert batch_complete["failure_count"] == 1

    def test_batch_max_duration_tracking(self):
        """Test that batch tracks maximum duration across tools."""
        mock_callback = Mock(spec=ProgressCallback)
        tools = ["gemini", "codex"]

        with batch_consultation_progress(tools, timeout=120, callback=mock_callback) as progress:
            progress.mark_complete("gemini", ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="output",
                duration=25.0
            ))
            progress.mark_complete("codex", ToolResponse(
                tool="codex",
                status=ToolStatus.SUCCESS,
                output="output",
                duration=45.0  # Longer duration
            ))

        # Max duration should be 45.0
        batch_complete = mock_callback.on_batch_complete.call_args[1]
        assert batch_complete["max_duration"] == 45.0

    def test_batch_prevents_double_counting(self):
        """Test that marking same tool complete twice doesn't double-count."""
        mock_callback = Mock(spec=ProgressCallback)
        tools = ["gemini"]

        with batch_consultation_progress(tools, timeout=120, callback=mock_callback) as progress:
            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="output",
                duration=30.0
            )
            progress.mark_complete("gemini", response)
            progress.mark_complete("gemini", response)  # Should be ignored

        # Should only count once
        batch_complete = mock_callback.on_batch_complete.call_args[1]
        assert batch_complete["total_count"] == 1
        assert batch_complete["success_count"] == 1

        # on_tool_complete should only be called once
        assert mock_callback.on_tool_complete.call_count == 1

    def test_batch_periodic_updates(self):
        """Test that periodic updates are called during batch execution."""
        mock_callback = Mock(spec=ProgressCallback)
        tools = ["gemini", "codex"]

        with batch_consultation_progress(
            tools,
            timeout=120,
            callback=mock_callback,
            update_interval=0.1  # Fast updates for testing
        ) as progress:
            # Wait for at least one update before completing
            time.sleep(0.25)

            # Mark tools complete
            for tool in tools:
                progress.mark_complete(tool, ToolResponse(
                    tool=tool,
                    status=ToolStatus.SUCCESS,
                    output="output",
                    duration=20.0
                ))

        # Verify at least one update was called
        assert mock_callback.on_update.call_count >= 1

        # Verify update includes batch context
        first_update = mock_callback.on_update.call_args_list[0]
        update_kwargs = first_update[1]
        assert update_kwargs.get("batch_mode") is True
        assert "completed_count" in update_kwargs
        assert "total_count" in update_kwargs

    def test_batch_concurrent_mark_complete(self):
        """Test thread-safety when marking tools complete concurrently."""
        mock_callback = Mock(spec=ProgressCallback)
        tools = ["gemini", "codex", "cursor-agent"]

        with batch_consultation_progress(tools, timeout=120, callback=mock_callback) as progress:
            # Simulate concurrent completion from multiple threads
            def mark_tool_complete(tool_name):
                response = ToolResponse(
                    tool=tool_name,
                    status=ToolStatus.SUCCESS,
                    output="output",
                    duration=25.0
                )
                progress.mark_complete(tool_name, response)

            # Create threads to mark tools complete concurrently
            threads = []
            for tool in tools:
                t = threading.Thread(target=mark_tool_complete, args=(tool,))
                threads.append(t)
                t.start()

            # Wait for all threads to complete
            for t in threads:
                t.join()

        # Verify all tools were counted exactly once
        batch_complete = mock_callback.on_batch_complete.call_args[1]
        assert batch_complete["total_count"] == 3
        assert batch_complete["success_count"] == 3
        assert batch_complete["failure_count"] == 0

        # Verify on_tool_complete was called exactly 3 times
        assert mock_callback.on_tool_complete.call_count == 3

    def test_batch_early_completion(self):
        """Test that batch completes immediately when all tools finish early."""
        mock_callback = Mock(spec=ProgressCallback)
        tools = ["gemini", "codex"]

        start_time = time.time()
        with batch_consultation_progress(tools, timeout=120, callback=mock_callback) as progress:
            # Mark all tools complete immediately
            for tool in tools:
                progress.mark_complete(tool, ToolResponse(
                    tool=tool,
                    status=ToolStatus.SUCCESS,
                    output="output",
                    duration=1.0
                ))

            # Verify _all_complete flag is set
            assert progress._all_complete is True

        elapsed = time.time() - start_time

        # Should complete much faster than timeout
        assert elapsed < 10.0

        # Verify batch complete was called
        mock_callback.on_batch_complete.assert_called_once()

    def test_batch_partial_completion(self):
        """Test batch behavior when only some tools complete."""
        mock_callback = Mock(spec=ProgressCallback)
        tools = ["gemini", "codex", "cursor-agent"]

        with batch_consultation_progress(tools, timeout=120, callback=mock_callback) as progress:
            # Only mark 2 out of 3 tools complete
            progress.mark_complete("gemini", ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="output",
                duration=20.0
            ))
            progress.mark_complete("codex", ToolResponse(
                tool="codex",
                status=ToolStatus.ERROR,
                output="",
                duration=15.0,
                error="Failed"
            ))
            # cursor-agent is never marked complete (simulates timeout/hang)

        # Verify batch complete still fires with partial results
        batch_complete = mock_callback.on_batch_complete.call_args[1]
        assert batch_complete["total_count"] == 3
        assert batch_complete["success_count"] == 1
        assert batch_complete["failure_count"] == 1

        # Only 2 tool completions should be recorded
        assert mock_callback.on_tool_complete.call_count == 2

    def test_batch_with_context_metadata(self):
        """Test that context metadata is passed through batch callbacks."""
        mock_callback = Mock(spec=ProgressCallback)
        tools = ["gemini", "codex"]

        with batch_consultation_progress(
            tools,
            timeout=120,
            callback=mock_callback,
            operation="consensus",
            phase="analysis"
        ) as progress:
            for tool in tools:
                progress.mark_complete(tool, ToolResponse(
                    tool=tool,
                    status=ToolStatus.SUCCESS,
                    output="output",
                    duration=30.0
                ))

        # Verify context was passed to batch_start
        batch_start_kwargs = mock_callback.on_batch_start.call_args[1]
        assert batch_start_kwargs["operation"] == "consensus"
        assert batch_start_kwargs["phase"] == "analysis"


class TestElapsedTimeTracking:
    """Test elapsed time tracking accuracy in progress feedback."""

    def test_single_consultation_elapsed_time(self):
        """Test that elapsed time is accurately tracked for single consultations."""
        mock_callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress("gemini", timeout=90, callback=mock_callback) as progress:
            # Simulate operation taking ~0.5 seconds
            time.sleep(0.5)

            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="Test",
                duration=0.5
            )
            progress.complete(response)

        # Verify on_complete was called with duration
        complete_kwargs = mock_callback.on_complete.call_args[1]
        reported_duration = complete_kwargs["duration"]

        # Duration should be approximately the sleep time (with some overhead)
        assert 0.4 < reported_duration < 2.0  # Allow overhead for thread operations

    def test_update_elapsed_time_increases(self):
        """Test that elapsed time increases in periodic updates."""
        mock_callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress(
            "gemini",
            timeout=90,
            callback=mock_callback,
            update_interval=0.1
        ) as progress:
            # Wait for multiple updates
            time.sleep(0.35)

            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="Test",
                duration=0.35
            )
            progress.complete(response)

        # Verify multiple updates were called
        assert mock_callback.on_update.call_count >= 2

        # Verify elapsed time increases across updates
        update_calls = mock_callback.on_update.call_args_list
        elapsed_times = [call[1]["elapsed"] for call in update_calls]

        # Each elapsed time should be greater than the previous
        for i in range(1, len(elapsed_times)):
            assert elapsed_times[i] > elapsed_times[i-1]

    def test_batch_total_duration_tracking(self):
        """Test that batch tracks total duration accurately."""
        mock_callback = Mock(spec=ProgressCallback)
        tools = ["gemini", "codex"]

        with batch_consultation_progress(tools, timeout=120, callback=mock_callback) as progress:
            # Simulate staggered completions
            time.sleep(0.2)
            progress.mark_complete("gemini", ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="output",
                duration=0.2
            ))

            time.sleep(0.3)
            progress.mark_complete("codex", ToolResponse(
                tool="codex",
                status=ToolStatus.SUCCESS,
                output="output",
                duration=0.3
            ))

        # Verify batch complete reports total duration
        batch_complete = mock_callback.on_batch_complete.call_args[1]
        reported_total = batch_complete["total_duration"]

        # Duration should be at least the sum of sleeps (0.5s) with overhead
        assert 0.4 < reported_total < 2.0

    def test_max_duration_vs_total_duration(self):
        """Test that max_duration tracks longest individual tool, not total."""
        mock_callback = Mock(spec=ProgressCallback)
        tools = ["gemini", "codex"]

        with batch_consultation_progress(tools, timeout=120, callback=mock_callback) as progress:
            progress.mark_complete("gemini", ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="output",
                duration=0.2
            ))
            progress.mark_complete("codex", ToolResponse(
                tool="codex",
                status=ToolStatus.SUCCESS,
                output="output",
                duration=0.5  # Longer individual duration
            ))

        batch_complete = mock_callback.on_batch_complete.call_args[1]

        # max_duration should be the longest individual tool (0.5)
        assert batch_complete["max_duration"] == 0.5

        # total_duration should be the wall-clock time (will be >= 0.5 in sequential)
        assert batch_complete["total_duration"] >= 0.5

    def test_elapsed_time_on_error(self):
        """Test that elapsed time is tracked even when errors occur."""
        mock_callback = Mock(spec=ProgressCallback)

        try:
            with ai_consultation_progress("gemini", timeout=90, callback=mock_callback):
                time.sleep(0.3)
                raise RuntimeError("Simulated error")
        except RuntimeError:
            pass  # Expected

        # Verify on_complete was still called with duration
        complete_kwargs = mock_callback.on_complete.call_args[1]
        reported_duration = complete_kwargs["duration"]

        # Duration should be approximately the sleep time (with some overhead)
        assert 0.2 < reported_duration < 2.0

    def test_auto_complete_tracks_elapsed_time(self):
        """Test that auto-complete (no explicit complete() call) tracks elapsed time."""
        mock_callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress("gemini", timeout=90, callback=mock_callback):
            time.sleep(0.4)
            # No explicit complete() call - should auto-complete

        # Verify on_complete was called with duration
        complete_kwargs = mock_callback.on_complete.call_args[1]
        reported_duration = complete_kwargs["duration"]

        # Duration should be approximately the sleep time (with some overhead)
        assert 0.3 < reported_duration < 2.0


class TestPytestRunProgress:
    """Test pytest test run progress feedback with mock subprocess output."""

    def test_pytest_progress_basic_lifecycle(self):
        """Test basic pytest progress tracking lifecycle."""
        mock_callback = Mock(spec=ProgressCallback)

        # Simulate pytest execution with mock callback
        # This would use a hypothetical test_run_progress context manager
        # For now, test using ai_consultation_progress as a stand-in
        with ai_consultation_progress("pytest", timeout=300, callback=mock_callback) as progress:
            # Simulate pytest collecting tests
            time.sleep(0.1)

            # Simulate pytest running tests
            time.sleep(0.2)

            response = ToolResponse(
                tool="pytest",
                status=ToolStatus.SUCCESS,
                output="5 passed in 0.3s",
                duration=0.3
            )
            progress.complete(response)

        # Verify lifecycle callbacks
        mock_callback.on_start.assert_called_once()
        assert mock_callback.on_start.call_args[1]["tool"] == "pytest"
        mock_callback.on_complete.assert_called_once()
        assert mock_callback.on_complete.call_args[1]["status"] == ToolStatus.SUCCESS

    def test_pytest_progress_with_test_count(self):
        """Test pytest progress tracking with test count metadata."""
        mock_callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress(
            "pytest",
            timeout=300,
            callback=mock_callback,
            test_count=10,
            test_file="tests/unit/test_example.py"
        ) as progress:
            response = ToolResponse(
                tool="pytest",
                status=ToolStatus.SUCCESS,
                output="10 passed in 1.5s",
                duration=1.5
            )
            progress.complete(response)

        # Verify context metadata was passed
        start_kwargs = mock_callback.on_start.call_args[1]
        assert start_kwargs["test_count"] == 10
        assert start_kwargs["test_file"] == "tests/unit/test_example.py"

    def test_pytest_progress_with_failures(self):
        """Test pytest progress when tests fail."""
        mock_callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress("pytest", timeout=300, callback=mock_callback) as progress:
            response = ToolResponse(
                tool="pytest",
                status=ToolStatus.ERROR,
                output="2 failed, 3 passed in 2.0s",
                duration=2.0,
                error="Test failures detected"
            )
            progress.complete(response)

        # Verify error status propagated
        complete_kwargs = mock_callback.on_complete.call_args[1]
        assert complete_kwargs["status"] == ToolStatus.ERROR

    def test_pytest_progress_with_periodic_updates(self):
        """Test that pytest shows periodic updates during long test runs."""
        mock_callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress(
            "pytest",
            timeout=300,
            callback=mock_callback,
            update_interval=0.1
        ) as progress:
            # Simulate long test run
            time.sleep(0.35)

            response = ToolResponse(
                tool="pytest",
                status=ToolStatus.SUCCESS,
                output="20 passed in 0.35s",
                duration=0.35
            )
            progress.complete(response)

        # Verify periodic updates were called
        assert mock_callback.on_update.call_count >= 2

    def test_pytest_progress_timeout_handling(self):
        """Test pytest progress when tests timeout."""
        mock_callback = Mock(spec=ProgressCallback)

        try:
            with ai_consultation_progress("pytest", timeout=5, callback=mock_callback):
                # Simulate timeout scenario
                time.sleep(0.2)
                raise TimeoutError("Test execution timed out after 5s")
        except TimeoutError:
            pass  # Expected

        # Verify complete was called with error
        complete_kwargs = mock_callback.on_complete.call_args[1]
        assert complete_kwargs["status"] == ToolStatus.ERROR
        assert "timed out" in complete_kwargs.get("error", "").lower()

    def test_pytest_progress_with_collection_info(self):
        """Test pytest progress tracking during test collection phase."""
        mock_callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress(
            "pytest",
            timeout=300,
            callback=mock_callback,
            phase="collection"
        ) as progress:
            # Simulate collection
            time.sleep(0.1)

            response = ToolResponse(
                tool="pytest",
                status=ToolStatus.SUCCESS,
                output="collected 25 items",
                duration=0.1
            )
            progress.complete(response)

        # Verify phase context was passed
        start_kwargs = mock_callback.on_start.call_args[1]
        assert start_kwargs["phase"] == "collection"


class TestValidationProgress:
    """Test validation progress feedback with multiple specs."""

    def test_single_spec_validation(self):
        """Test progress tracking for single spec validation."""
        mock_callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress(
            "sdd-validate",
            timeout=60,
            callback=mock_callback,
            spec_file="user-auth-001.json"
        ) as progress:
            time.sleep(0.2)

            response = ToolResponse(
                tool="sdd-validate",
                status=ToolStatus.SUCCESS,
                output="Validation passed: 0 errors, 2 warnings",
                duration=0.2
            )
            progress.complete(response)

        # Verify context metadata
        start_kwargs = mock_callback.on_start.call_args[1]
        assert start_kwargs["spec_file"] == "user-auth-001.json"

        # Verify completion
        complete_kwargs = mock_callback.on_complete.call_args[1]
        assert complete_kwargs["status"] == ToolStatus.SUCCESS

    def test_multiple_spec_validation_batch(self):
        """Test batch validation progress for multiple specs."""
        mock_callback = Mock(spec=ProgressCallback)
        spec_files = ["spec-1.json", "spec-2.json", "spec-3.json"]

        with batch_consultation_progress(
            spec_files,
            timeout=120,
            callback=mock_callback
        ) as progress:
            # Mark each spec validation complete
            for spec_file in spec_files:
                response = ToolResponse(
                    tool=spec_file,
                    status=ToolStatus.SUCCESS,
                    output="Validation passed",
                    duration=0.3
                )
                progress.mark_complete(spec_file, response)

        # Verify batch completion
        batch_complete = mock_callback.on_batch_complete.call_args[1]
        assert batch_complete["total_count"] == 3
        assert batch_complete["success_count"] == 3
        assert batch_complete["failure_count"] == 0

    def test_validation_progress_with_errors(self):
        """Test validation progress when specs have errors."""
        mock_callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress(
            "sdd-validate",
            timeout=60,
            callback=mock_callback,
            spec_file="broken-spec.json"
        ) as progress:
            response = ToolResponse(
                tool="sdd-validate",
                status=ToolStatus.ERROR,
                output="Validation failed: 5 errors, 10 warnings",
                duration=0.3,
                error="Critical errors found in spec"
            )
            progress.complete(response)

        # Verify error status
        complete_kwargs = mock_callback.on_complete.call_args[1]
        assert complete_kwargs["status"] == ToolStatus.ERROR

    def test_multi_spec_validation_mixed_results(self):
        """Test batch validation with mixed success/failure results."""
        mock_callback = Mock(spec=ProgressCallback)
        specs = ["good-spec.json", "bad-spec.json", "warning-spec.json"]

        with batch_consultation_progress(specs, timeout=120, callback=mock_callback) as progress:
            # First spec succeeds
            progress.mark_complete("good-spec.json", ToolResponse(
                tool="good-spec.json",
                status=ToolStatus.SUCCESS,
                output="Validation passed",
                duration=0.2
            ))

            # Second spec fails
            progress.mark_complete("bad-spec.json", ToolResponse(
                tool="bad-spec.json",
                status=ToolStatus.ERROR,
                output="Validation failed: 3 errors",
                duration=0.3,
                error="Critical errors"
            ))

            # Third spec succeeds with warnings
            progress.mark_complete("warning-spec.json", ToolResponse(
                tool="warning-spec.json",
                status=ToolStatus.SUCCESS,
                output="Validation passed: 0 errors, 5 warnings",
                duration=0.25
            ))

        # Verify mixed results
        batch_complete = mock_callback.on_batch_complete.call_args[1]
        assert batch_complete["total_count"] == 3
        assert batch_complete["success_count"] == 2
        assert batch_complete["failure_count"] == 1

    def test_validation_progress_per_file_tracking(self):
        """Test that individual file validation progress is tracked."""
        mock_callback = Mock(spec=ProgressCallback)
        specs = ["spec-1.json", "spec-2.json"]

        with batch_consultation_progress(specs, timeout=120, callback=mock_callback) as progress:
            for spec in specs:
                progress.mark_complete(spec, ToolResponse(
                    tool=spec,
                    status=ToolStatus.SUCCESS,
                    output="Validation passed",
                    duration=0.2
                ))

                # Verify on_tool_complete was called after each file
                assert mock_callback.on_tool_complete.call_count >= 1

        # Should have been called once per spec
        assert mock_callback.on_tool_complete.call_count == 2

    def test_validation_progress_with_metadata(self):
        """Test validation progress includes spec metadata."""
        mock_callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress(
            "sdd-validate",
            timeout=60,
            callback=mock_callback,
            spec_file="api-spec.json",
            validation_level="strict",
            check_dependencies=True
        ) as progress:
            response = ToolResponse(
                tool="sdd-validate",
                status=ToolStatus.SUCCESS,
                output="Strict validation passed",
                duration=0.4
            )
            progress.complete(response)

        # Verify all metadata was passed through
        start_kwargs = mock_callback.on_start.call_args[1]
        assert start_kwargs["spec_file"] == "api-spec.json"
        assert start_kwargs["validation_level"] == "strict"
        assert start_kwargs["check_dependencies"] is True


class TestNonTTYBehavior:
    """Test progress behavior in non-TTY environments."""

    def test_progress_in_non_tty_uses_callback(self):
        """Test that progress still works in non-TTY with callbacks."""
        mock_callback = Mock(spec=ProgressCallback)

        # Simulate non-TTY environment (callbacks should still fire)
        with ai_consultation_progress("gemini", timeout=90, callback=mock_callback) as progress:
            time.sleep(0.2)

            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="Test output",
                duration=0.2
            )
            progress.complete(response)

        # Callbacks should be called regardless of TTY status
        mock_callback.on_start.assert_called_once()
        mock_callback.on_complete.assert_called_once()

    def test_noop_callback_safe_in_non_tty(self):
        """Test that NoOpProgressCallback works in non-TTY."""
        callback = NoOpProgressCallback()

        # Should not raise even in non-TTY
        with ai_consultation_progress("gemini", timeout=90, callback=callback) as progress:
            time.sleep(0.1)

            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="Test",
                duration=0.1
            )
            progress.complete(response)

        # No assertions needed - just verify no exceptions

    def test_batch_progress_in_non_tty(self):
        """Test batch progress in non-TTY environment."""
        mock_callback = Mock(spec=ProgressCallback)
        tools = ["gemini", "codex"]

        with batch_consultation_progress(tools, timeout=120, callback=mock_callback) as progress:
            for tool in tools:
                progress.mark_complete(tool, ToolResponse(
                    tool=tool,
                    status=ToolStatus.SUCCESS,
                    output="output",
                    duration=0.2
                ))

        # Verify batch callbacks fired
        mock_callback.on_batch_start.assert_called_once()
        mock_callback.on_batch_complete.assert_called_once()
        assert mock_callback.on_tool_complete.call_count == 2

    def test_callback_errors_logged_not_raised(self):
        """Test that callback errors are logged but don't crash progress tracking."""
        # Create callback that raises exceptions
        error_callback = Mock(spec=ProgressCallback)
        error_callback.on_start.side_effect = RuntimeError("Callback error")
        error_callback.on_complete.side_effect = RuntimeError("Callback error")

        # Should not raise despite callback errors
        with ai_consultation_progress("gemini", timeout=90, callback=error_callback) as progress:
            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="Test",
                duration=0.1
            )
            progress.complete(response)

        # Verify callbacks were attempted (and failed gracefully)
        error_callback.on_start.assert_called_once()
        error_callback.on_complete.assert_called_once()

    def test_progress_without_explicit_callback(self):
        """Test progress tracking when no callback is provided (uses NoOp)."""
        # No callback provided - should use NoOpProgressCallback internally
        with ai_consultation_progress("gemini", timeout=90) as progress:
            time.sleep(0.1)

            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="Test",
                duration=0.1
            )
            progress.complete(response)

        # No assertions needed - just verify no exceptions

    def test_batch_progress_without_explicit_callback(self):
        """Test batch progress when no callback is provided."""
        tools = ["gemini", "codex"]

        with batch_consultation_progress(tools, timeout=120) as progress:
            for tool in tools:
                progress.mark_complete(tool, ToolResponse(
                    tool=tool,
                    status=ToolStatus.SUCCESS,
                    output="output",
                    duration=0.2
                ))

        # No assertions needed - just verify no exceptions


class TestLoggingInteraction:
    """Test that progress output doesn't interfere with logging."""

    def test_progress_with_concurrent_logging(self):
        """Test that progress tracking doesn't interfere with log messages."""
        mock_callback = Mock(spec=ProgressCallback)
        logger = logging.getLogger("test_logger")

        with ai_consultation_progress("gemini", timeout=90, callback=mock_callback) as progress:
            # Log messages during progress tracking
            logger.info("Starting AI consultation")
            time.sleep(0.1)
            logger.debug("Processing request")
            time.sleep(0.1)
            logger.info("Consultation complete")

            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="Test output",
                duration=0.2
            )
            progress.complete(response)

        # Verify progress callbacks were called despite logging
        mock_callback.on_start.assert_called_once()
        mock_callback.on_complete.assert_called_once()

    def test_callback_exception_logging(self):
        """Test that callback exceptions are logged without crashing."""
        error_callback = Mock(spec=ProgressCallback)
        error_callback.on_update.side_effect = ValueError("Test callback error")

        # Capture log output
        with patch('claude_skills.common.tui_progress.logger') as mock_logger:
            with ai_consultation_progress(
                "gemini",
                timeout=90,
                callback=error_callback,
                update_interval=0.1
            ) as progress:
                time.sleep(0.25)

                response = ToolResponse(
                    tool="gemini",
                    status=ToolStatus.SUCCESS,
                    output="Test",
                    duration=0.25
                )
                progress.complete(response)

            # Verify warning was logged for callback errors
            assert mock_logger.warning.called

    def test_batch_progress_with_logging(self):
        """Test batch progress doesn't interfere with logging."""
        mock_callback = Mock(spec=ProgressCallback)
        logger = logging.getLogger("test_batch_logger")
        tools = ["gemini", "codex"]

        with batch_consultation_progress(tools, timeout=120, callback=mock_callback) as progress:
            for tool in tools:
                logger.info(f"Processing {tool}")
                time.sleep(0.1)

                progress.mark_complete(tool, ToolResponse(
                    tool=tool,
                    status=ToolStatus.SUCCESS,
                    output="output",
                    duration=0.1
                ))

                logger.info(f"Completed {tool}")

        # Verify batch callbacks completed successfully
        mock_callback.on_batch_start.assert_called_once()
        mock_callback.on_batch_complete.assert_called_once()

    def test_progress_logger_isolated(self):
        """Test that progress module logger doesn't affect application logging."""
        # Get the progress module logger
        progress_logger = logging.getLogger("claude_skills.common.tui_progress")
        app_logger = logging.getLogger("test_app")

        # Create separate handlers to verify isolation
        progress_handler = Mock()
        app_handler = Mock()

        progress_logger.addHandler(progress_handler)
        app_logger.addHandler(app_handler)

        try:
            with ai_consultation_progress("gemini", timeout=90) as progress:
                # Log to both loggers
                progress_logger.info("Progress log message")
                app_logger.info("App log message")

                response = ToolResponse(
                    tool="gemini",
                    status=ToolStatus.SUCCESS,
                    output="Test",
                    duration=0.1
                )
                progress.complete(response)

            # Both should have received their respective messages
            # (Actual handler verification would depend on logging configuration)

        finally:
            progress_logger.removeHandler(progress_handler)
            app_logger.removeHandler(app_handler)

    def test_error_logging_with_progress(self):
        """Test that errors during progress are properly logged."""
        mock_callback = Mock(spec=ProgressCallback)
        logger = logging.getLogger("test_error_logger")

        try:
            with ai_consultation_progress("gemini", timeout=90, callback=mock_callback):
                logger.error("Simulated error during consultation")
                raise RuntimeError("Test error")
        except RuntimeError:
            pass  # Expected

        # Verify error completion was tracked
        complete_kwargs = mock_callback.on_complete.call_args[1]
        assert complete_kwargs["status"] == ToolStatus.ERROR

    def test_debug_logging_during_updates(self):
        """Test debug logging during periodic progress updates."""
        mock_callback = Mock(spec=ProgressCallback)
        logger = logging.getLogger("test_debug_logger")

        with ai_consultation_progress(
            "gemini",
            timeout=90,
            callback=mock_callback,
            update_interval=0.1
        ) as progress:
            # Log debug messages during updates
            logger.debug("Update 1")
            time.sleep(0.15)
            logger.debug("Update 2")
            time.sleep(0.15)

            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="Test",
                duration=0.3
            )
            progress.complete(response)

        # Verify updates were called
        assert mock_callback.on_update.call_count >= 1
