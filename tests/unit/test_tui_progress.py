"""
Unit tests for TUI progress feedback context managers.

Tests the progress callback protocol, context managers, and tracker classes
for AI tool consultation progress feedback.
"""

import pytest
import time
from unittest.mock import Mock, call

from claude_skills.common.tui_progress import (
    ai_consultation_progress,
    batch_consultation_progress,
    NoOpProgressCallback,
    ProgressTracker,
    BatchProgressTracker,
    ProgressCallback
)
from claude_skills.common.ai_tools import ToolStatus, ToolResponse


class TestNoOpProgressCallback:
    """Test that NoOp callback never crashes."""

    def test_on_start_no_crash(self):
        """on_start accepts arguments without error."""
        callback = NoOpProgressCallback()
        callback.on_start("gemini", 90, model="gemini-2.5-pro")
        # No assertion needed - just verify no exception

    def test_on_update_no_crash(self):
        """on_update accepts arguments without error."""
        callback = NoOpProgressCallback()
        callback.on_update("gemini", elapsed=30.0, timeout=90)

    def test_on_complete_no_crash(self):
        """on_complete accepts arguments without error."""
        callback = NoOpProgressCallback()
        callback.on_complete(
            "gemini",
            ToolStatus.SUCCESS,
            45.2,
            output_length=1024,
            error=None
        )

    def test_on_batch_start_no_crash(self):
        """on_batch_start accepts arguments without error."""
        callback = NoOpProgressCallback()
        callback.on_batch_start(["gemini", "codex"], 2, 120)

    def test_on_tool_complete_no_crash(self):
        """on_tool_complete accepts arguments without error."""
        callback = NoOpProgressCallback()
        response = ToolResponse(
            tool="gemini",
            status=ToolStatus.SUCCESS,
            output="test",
            error=None,
            duration=45.2,
            timestamp="2025-11-07T12:00:00Z"
        )
        callback.on_tool_complete("gemini", response, 1, 2)

    def test_on_batch_complete_no_crash(self):
        """on_batch_complete accepts arguments without error."""
        callback = NoOpProgressCallback()
        callback.on_batch_complete(
            total_count=2,
            success_count=2,
            failure_count=0,
            total_duration=60.0,
            max_duration=45.2
        )


class TestSingleConsultationContextManager:
    """Test context manager for single tool consultations."""

    def test_calls_on_start_when_entering(self):
        """Context manager calls on_start when entering."""
        callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress("gemini", timeout=90, callback=callback) as progress:
            pass

        callback.on_start.assert_called_once()
        args, kwargs = callback.on_start.call_args
        assert kwargs["tool"] == "gemini"
        assert kwargs["timeout"] == 90

    def test_calls_on_complete_when_complete_called(self):
        """Context manager calls on_complete when complete() called."""
        callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress("gemini", timeout=90, callback=callback) as progress:
            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="test output",
                error=None,
                duration=45.2,
                timestamp="2025-11-07T12:00:00Z"
            )
            progress.complete(response)

        callback.on_complete.assert_called_once()
        args, kwargs = callback.on_complete.call_args
        assert kwargs["tool"] == "gemini"
        assert kwargs["status"] == ToolStatus.SUCCESS
        assert "duration" in kwargs
        assert "output_length" in kwargs

    def test_auto_completes_if_user_forgets(self):
        """Context manager auto-completes if complete() not called."""
        callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress("gemini", timeout=90, callback=callback) as progress:
            # User forgets to call progress.complete()
            pass

        # Should still call on_complete in finally block
        callback.on_complete.assert_called_once()

    def test_handles_exception_during_execution(self):
        """Context manager calls on_complete even if exception raised."""
        callback = Mock(spec=ProgressCallback)

        with pytest.raises(ValueError):
            with ai_consultation_progress("gemini", timeout=90, callback=callback) as progress:
                raise ValueError("Test error")

        callback.on_complete.assert_called_once()
        args, kwargs = callback.on_complete.call_args
        assert kwargs["status"] == ToolStatus.ERROR
        assert "Test error" in kwargs["error"]

    def test_prevents_double_completion(self):
        """ProgressTracker ignores duplicate complete() calls."""
        callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress("gemini", timeout=90, callback=callback) as progress:
            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="test",
                error=None,
                duration=45.2,
                timestamp="2025-11-07T12:00:00Z"
            )
            progress.complete(response)
            progress.complete(response)  # Second call should be ignored

        # on_complete should only be called once (not twice)
        assert callback.on_complete.call_count == 1

    def test_passes_context_to_callbacks(self):
        """Context manager passes extra context to callbacks."""
        callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress(
            "gemini",
            timeout=90,
            callback=callback,
            model="gemini-2.5-pro",
            prompt_length=1024
        ) as progress:
            pass

        args, kwargs = callback.on_start.call_args
        assert kwargs["model"] == "gemini-2.5-pro"
        assert kwargs["prompt_length"] == 1024

    def test_uses_no_op_callback_by_default(self):
        """Context manager uses NoOp callback if none provided."""
        # Should not raise any exceptions
        with ai_consultation_progress("gemini", timeout=90) as progress:
            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="test",
                error=None,
                duration=45.2,
                timestamp="2025-11-07T12:00:00Z"
            )
            progress.complete(response)


class TestBatchConsultationContextManager:
    """Test context manager for batch tool consultations."""

    def test_calls_on_batch_start_when_entering(self):
        """Context manager calls on_batch_start when entering."""
        callback = Mock(spec=ProgressCallback)

        with batch_consultation_progress(
            ["gemini", "codex"],
            timeout=120,
            callback=callback
        ) as progress:
            pass

        callback.on_batch_start.assert_called_once()
        args, kwargs = callback.on_batch_start.call_args
        assert kwargs["tools"] == ["gemini", "codex"]
        assert kwargs["count"] == 2
        assert kwargs["timeout"] == 120

    def test_calls_on_tool_complete_for_each_tool(self):
        """Context manager calls on_tool_complete for each marked tool."""
        callback = Mock(spec=ProgressCallback)

        with batch_consultation_progress(
            ["gemini", "codex"],
            timeout=120,
            callback=callback
        ) as progress:
            response1 = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="output1",
                error=None,
                duration=45.2,
                timestamp="2025-11-07T12:00:00Z"
            )
            response2 = ToolResponse(
                tool="codex",
                status=ToolStatus.SUCCESS,
                output="output2",
                error=None,
                duration=50.1,
                timestamp="2025-11-07T12:00:05Z"
            )
            progress.mark_complete("gemini", response1)
            progress.mark_complete("codex", response2)

        assert callback.on_tool_complete.call_count == 2

    def test_tracks_success_and_failure_counts(self):
        """BatchProgressTracker correctly counts successes and failures."""
        callback = Mock(spec=ProgressCallback)

        with batch_consultation_progress(
            ["gemini", "codex", "cursor-agent"],
            timeout=120,
            callback=callback
        ) as progress:
            progress.mark_complete("gemini", ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="ok",
                error=None,
                duration=45.2,
                timestamp="2025-11-07T12:00:00Z"
            ))
            progress.mark_complete("codex", ToolResponse(
                tool="codex",
                status=ToolStatus.TIMEOUT,
                output="",
                error="Timeout",
                duration=120.0,
                timestamp="2025-11-07T12:02:00Z"
            ))
            progress.mark_complete("cursor-agent", ToolResponse(
                tool="cursor-agent",
                status=ToolStatus.SUCCESS,
                output="ok",
                error=None,
                duration=60.0,
                timestamp="2025-11-07T12:01:00Z"
            ))

        # Check on_batch_complete call
        callback.on_batch_complete.assert_called_once()
        args, kwargs = callback.on_batch_complete.call_args
        assert kwargs["total_count"] == 3
        assert kwargs["success_count"] == 2
        assert kwargs["failure_count"] == 1

    def test_tracks_max_duration(self):
        """BatchProgressTracker tracks maximum individual tool duration."""
        callback = Mock(spec=ProgressCallback)

        with batch_consultation_progress(
            ["gemini", "codex"],
            timeout=120,
            callback=callback
        ) as progress:
            progress.mark_complete("gemini", ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="ok",
                error=None,
                duration=45.2,
                timestamp="2025-11-07T12:00:00Z"
            ))
            progress.mark_complete("codex", ToolResponse(
                tool="codex",
                status=ToolStatus.SUCCESS,
                output="ok",
                error=None,
                duration=85.7,  # Longer
                timestamp="2025-11-07T12:01:00Z"
            ))

        args, kwargs = callback.on_batch_complete.call_args
        assert kwargs["max_duration"] == 85.7

    def test_prevents_double_marking_same_tool(self):
        """BatchProgressTracker ignores duplicate mark_complete for same tool."""
        callback = Mock(spec=ProgressCallback)

        with batch_consultation_progress(
            ["gemini", "codex"],
            timeout=120,
            callback=callback
        ) as progress:
            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="ok",
                error=None,
                duration=45.2,
                timestamp="2025-11-07T12:00:00Z"
            )
            progress.mark_complete("gemini", response)
            progress.mark_complete("gemini", response)  # Duplicate

        # on_tool_complete should only be called once for gemini
        assert callback.on_tool_complete.call_count == 1

    def test_calls_on_batch_complete_when_exiting(self):
        """Context manager calls on_batch_complete when exiting."""
        callback = Mock(spec=ProgressCallback)

        with batch_consultation_progress(
            ["gemini", "codex"],
            timeout=120,
            callback=callback
        ) as progress:
            pass

        callback.on_batch_complete.assert_called_once()

    def test_uses_no_op_callback_by_default(self):
        """Context manager uses NoOp callback if none provided."""
        # Should not raise any exceptions
        with batch_consultation_progress(["gemini", "codex"], timeout=120) as progress:
            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="test",
                error=None,
                duration=45.2,
                timestamp="2025-11-07T12:00:00Z"
            )
            progress.mark_complete("gemini", response)


class TestProgressTracker:
    """Test ProgressTracker dataclass directly."""

    def test_tracks_completion_state(self):
        """ProgressTracker tracks whether complete() has been called."""
        callback = Mock(spec=ProgressCallback)
        tracker = ProgressTracker(
            tool="gemini",
            timeout=90,
            callback=callback,
            context={},
            start_time=time.time()
        )

        assert tracker.completed is False

        response = ToolResponse(
            tool="gemini",
            status=ToolStatus.SUCCESS,
            output="test",
            error=None,
            duration=45.2,
            timestamp="2025-11-07T12:00:00Z"
        )
        tracker.complete(response)

        assert tracker.completed is True


class TestBatchProgressTracker:
    """Test BatchProgressTracker dataclass directly."""

    def test_initializes_with_empty_completed_list(self):
        """BatchProgressTracker initializes completed_tools as empty list."""
        callback = Mock(spec=ProgressCallback)
        tracker = BatchProgressTracker(
            tools=["gemini", "codex"],
            timeout=120,
            callback=callback,
            context={}
        )

        assert tracker.completed_tools == []
        assert tracker.success_count == 0
        assert tracker.failure_count == 0

    def test_updates_counts_correctly(self):
        """BatchProgressTracker updates success/failure counts correctly."""
        callback = Mock(spec=ProgressCallback)
        tracker = BatchProgressTracker(
            tools=["gemini", "codex"],
            timeout=120,
            callback=callback,
            context={},
            start_time=time.time()
        )

        tracker.mark_complete("gemini", ToolResponse(
            tool="gemini",
            status=ToolStatus.SUCCESS,
            output="ok",
            error=None,
            duration=45.2,
            timestamp="2025-11-07T12:00:00Z"
        ))

        assert tracker.success_count == 1
        assert tracker.failure_count == 0

        tracker.mark_complete("codex", ToolResponse(
            tool="codex",
            status=ToolStatus.ERROR,
            output="",
            error="Failed",
            duration=10.0,
            timestamp="2025-11-07T12:00:10Z"
        ))

        assert tracker.success_count == 1
        assert tracker.failure_count == 1
