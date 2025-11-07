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
    QueuedProgressCallback,
    ProgressTracker,
    BatchProgressTracker,
    ProgressCallback,
    format_progress_message
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


class TestElapsedTimeTracking:
    """Test elapsed time tracking and periodic update callbacks."""

    def test_on_update_called_periodically(self):
        """Context manager calls on_update at regular intervals."""
        callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress(
            "gemini",
            timeout=10,
            callback=callback,
            update_interval=0.5  # Fast updates for testing
        ) as progress:
            # Wait for at least 2 updates
            time.sleep(1.5)

            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="test",
                error=None,
                duration=1.5,
                timestamp="2025-11-07T12:00:00Z"
            )
            progress.complete(response)

        # Should have called on_update at least twice (at 0.5s and 1.0s)
        assert callback.on_update.call_count >= 2

    def test_on_update_receives_elapsed_time(self):
        """on_update callback receives elapsed time parameter."""
        callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress(
            "gemini",
            timeout=10,
            callback=callback,
            update_interval=0.3
        ) as progress:
            time.sleep(0.8)  # Wait for at least 2 updates

            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="test",
                error=None,
                duration=0.8,
                timestamp="2025-11-07T12:00:00Z"
            )
            progress.complete(response)

        # Check that on_update was called with elapsed parameter
        assert callback.on_update.call_count >= 1
        args, kwargs = callback.on_update.call_args
        assert "elapsed" in kwargs
        assert kwargs["elapsed"] > 0.0
        assert kwargs["tool"] == "gemini"
        assert kwargs["timeout"] == 10

    def test_update_thread_stops_on_completion(self):
        """Background update thread stops when consultation completes."""
        callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress(
            "gemini",
            timeout=30,
            callback=callback,
            update_interval=0.2
        ) as progress:
            time.sleep(0.5)  # Wait for at least 2 updates
            initial_count = callback.on_update.call_count

            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="test",
                error=None,
                duration=0.5,
                timestamp="2025-11-07T12:00:00Z"
            )
            progress.complete(response)

            # Wait a bit to ensure thread has stopped
            time.sleep(0.5)
            final_count = callback.on_update.call_count

        # No new updates should have occurred after completion
        assert final_count == initial_count

    def test_update_thread_stops_on_context_exit(self):
        """Background update thread stops when exiting context."""
        callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress(
            "gemini",
            timeout=30,
            callback=callback,
            update_interval=0.2
        ) as progress:
            time.sleep(0.5)

        # After exiting context, thread should be stopped
        # Wait to ensure no more updates
        initial_count = callback.on_update.call_count
        time.sleep(0.5)
        final_count = callback.on_update.call_count

        # No new updates should occur after context exit
        assert final_count == initial_count

    def test_update_thread_stops_on_exception(self):
        """Background update thread stops when exception raised."""
        callback = Mock(spec=ProgressCallback)

        try:
            with ai_consultation_progress(
                "gemini",
                timeout=30,
                callback=callback,
                update_interval=0.2
            ) as progress:
                time.sleep(0.5)
                raise ValueError("Test exception")
        except ValueError:
            pass

        # After exception, thread should be stopped
        initial_count = callback.on_update.call_count
        time.sleep(0.5)
        final_count = callback.on_update.call_count

        # No new updates should occur after exception
        assert final_count == initial_count

    def test_no_race_condition_on_completion(self):
        """No race condition when complete() called during update."""
        callback = Mock(spec=ProgressCallback)

        with ai_consultation_progress(
            "gemini",
            timeout=30,
            callback=callback,
            update_interval=0.1  # Very fast updates to increase chance of race
        ) as progress:
            time.sleep(0.25)  # Let some updates happen

            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="test",
                error=None,
                duration=0.25,
                timestamp="2025-11-07T12:00:00Z"
            )
            progress.complete(response)

        # Should only call on_complete once, not multiple times
        assert callback.on_complete.call_count == 1

    def test_update_interval_calculation_short_timeout(self):
        """Update interval is 2s for short timeouts (<30s)."""
        from claude_skills.common.tui_progress import _calculate_update_interval

        interval = _calculate_update_interval(20)
        assert interval == 2.0

    def test_update_interval_calculation_medium_timeout(self):
        """Update interval is 5s for medium timeouts (30-120s)."""
        from claude_skills.common.tui_progress import _calculate_update_interval

        interval = _calculate_update_interval(60)
        assert interval == 5.0

    def test_update_interval_calculation_long_timeout(self):
        """Update interval is 10s for long timeouts (>120s)."""
        from claude_skills.common.tui_progress import _calculate_update_interval

        interval = _calculate_update_interval(300)
        assert interval == 10.0

    def test_custom_update_interval_override(self):
        """Custom update_interval parameter overrides calculation."""
        from claude_skills.common.tui_progress import _calculate_update_interval

        interval = _calculate_update_interval(60, custom_interval=1.0)
        assert interval == 1.0


class TestBatchElapsedTimeTracking:
    """Test elapsed time tracking for batch operations."""

    def test_batch_on_update_called_periodically(self):
        """Batch context manager calls on_update at regular intervals."""
        callback = Mock(spec=ProgressCallback)

        with batch_consultation_progress(
            ["gemini", "codex"],
            timeout=10,
            callback=callback,
            update_interval=0.5
        ) as progress:
            # Wait for at least 2 updates
            time.sleep(1.5)

            # Complete the batch
            progress.mark_complete("gemini", ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="test",
                error=None,
                duration=1.0,
                timestamp="2025-11-07T12:00:00Z"
            ))
            progress.mark_complete("codex", ToolResponse(
                tool="codex",
                status=ToolStatus.SUCCESS,
                output="test",
                error=None,
                duration=1.2,
                timestamp="2025-11-07T12:00:01Z"
            ))

        # Should have called on_update at least twice
        assert callback.on_update.call_count >= 2

    def test_batch_on_update_includes_batch_context(self):
        """Batch on_update includes batch-specific context."""
        callback = Mock(spec=ProgressCallback)

        with batch_consultation_progress(
            ["gemini", "codex"],
            timeout=10,
            callback=callback,
            update_interval=0.3
        ) as progress:
            time.sleep(0.5)

            progress.mark_complete("gemini", ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="test",
                error=None,
                duration=0.4,
                timestamp="2025-11-07T12:00:00Z"
            ))

        # Check that on_update was called with batch context
        assert callback.on_update.call_count >= 1
        args, kwargs = callback.on_update.call_args
        assert "batch_mode" in kwargs
        assert kwargs["batch_mode"] is True
        assert "completed_count" in kwargs
        assert "total_count" in kwargs

    def test_batch_update_thread_stops_on_all_complete(self):
        """Batch update thread stops when all tools complete."""
        callback = Mock(spec=ProgressCallback)

        with batch_consultation_progress(
            ["gemini", "codex"],
            timeout=30,
            callback=callback,
            update_interval=0.2
        ) as progress:
            time.sleep(0.5)

            # Complete all tools
            progress.mark_complete("gemini", ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="test",
                error=None,
                duration=0.3,
                timestamp="2025-11-07T12:00:00Z"
            ))
            progress.mark_complete("codex", ToolResponse(
                tool="codex",
                status=ToolStatus.SUCCESS,
                output="test",
                error=None,
                duration=0.4,
                timestamp="2025-11-07T12:00:01Z"
            ))

            initial_count = callback.on_update.call_count

            # Wait to ensure no more updates
            time.sleep(0.5)
            final_count = callback.on_update.call_count

        # No new updates should occur after all tools complete
        assert final_count == initial_count

    def test_batch_update_thread_stops_on_context_exit(self):
        """Batch update thread stops when exiting context."""
        callback = Mock(spec=ProgressCallback)

        with batch_consultation_progress(
            ["gemini", "codex"],
            timeout=30,
            callback=callback,
            update_interval=0.2
        ) as progress:
            time.sleep(0.5)

        # After exiting, thread should be stopped
        initial_count = callback.on_update.call_count
        time.sleep(0.5)
        final_count = callback.on_update.call_count

        # No new updates should occur
        assert final_count == initial_count


class TestThreadSafety:
    """Test thread safety of progress tracking."""

    def test_concurrent_completion_is_safe(self):
        """Multiple threads can safely interact with tracker."""
        import threading
        callback = Mock(spec=ProgressCallback)

        def complete_task(progress):
            response = ToolResponse(
                tool="gemini",
                status=ToolStatus.SUCCESS,
                output="test",
                error=None,
                duration=0.1,
                timestamp="2025-11-07T12:00:00Z"
            )
            progress.complete(response)

        with ai_consultation_progress(
            "gemini",
            timeout=30,
            callback=callback,
            update_interval=0.1
        ) as progress:
            # Spawn multiple threads trying to complete simultaneously
            threads = [
                threading.Thread(target=complete_task, args=(progress,))
                for _ in range(5)
            ]

            for t in threads:
                t.start()

            for t in threads:
                t.join()

        # Despite multiple threads, on_complete should only be called once
        assert callback.on_complete.call_count == 1

    def test_batch_concurrent_marking_is_safe(self):
        """Multiple threads can safely mark tools complete in batch."""
        callback = Mock(spec=ProgressCallback)

        with batch_consultation_progress(
            ["tool1", "tool2", "tool3", "tool4"],
            timeout=30,
            callback=callback,
            update_interval=0.1
        ) as progress:
            # Mark tools complete from different threads
            import threading

            def mark_tool(tool_name):
                progress.mark_complete(tool_name, ToolResponse(
                    tool=tool_name,
                    status=ToolStatus.SUCCESS,
                    output="test",
                    error=None,
                    duration=0.1,
                    timestamp="2025-11-07T12:00:00Z"
                ))

            threads = [
                threading.Thread(target=mark_tool, args=(f"tool{i}",))
                for i in range(1, 5)
            ]

            for t in threads:
                t.start()

            for t in threads:
                t.join()

        # All 4 tools should be marked complete exactly once
        assert callback.on_tool_complete.call_count == 4


class TestQueuedProgressCallback:
    """Test queue-based progress callback wrapper for parallel consultations."""

    def test_forwards_on_start_to_wrapped_callback(self):
        """QueuedProgressCallback forwards on_start calls to wrapped callback."""
        wrapped = Mock(spec=ProgressCallback)
        queued = QueuedProgressCallback(wrapped)

        queued.start()
        queued.on_start("gemini", 90, model="gemini-2.5-pro")

        # Give consumer thread time to process
        time.sleep(0.2)
        queued.stop()

        wrapped.on_start.assert_called_once()
        args, kwargs = wrapped.on_start.call_args
        assert kwargs["tool"] == "gemini"
        assert kwargs["timeout"] == 90
        assert kwargs["model"] == "gemini-2.5-pro"

    def test_handles_large_queue_bursts(self):
        """QueuedProgressCallback handles large bursts of progress updates."""
        wrapped = Mock(spec=ProgressCallback)
        queued = QueuedProgressCallback(wrapped)

        queued.start()

        # Queue a large burst of updates
        for i in range(100):
            queued.on_update(f"tool{i % 5}", elapsed=float(i), timeout=90)

        # Give time to process all items
        time.sleep(1.0)
        queued.stop()

        # All updates should have been processed
        assert wrapped.on_update.call_count == 100

    def test_stop_waits_for_pending_queue_items(self):
        """QueuedProgressCallback waits for pending items when stopping."""
        wrapped = Mock(spec=ProgressCallback)
        queued = QueuedProgressCallback(wrapped)

        queued.start()

        # Queue several items
        queued.on_start("gemini", 90)
        queued.on_update("gemini", 10.0, 90)
        queued.on_update("gemini", 20.0, 90)
        queued.on_complete("gemini", ToolStatus.SUCCESS, 30.0)

        # Give a short time for processing to start
        time.sleep(0.1)

        # Stop with sufficient timeout for processing
        queued.stop(timeout=5.0)

        # All items should have been processed before stop completed
        assert wrapped.on_start.call_count == 1
        assert wrapped.on_update.call_count == 2
        assert wrapped.on_complete.call_count == 1

    def test_restart_after_stop(self):
        """QueuedProgressCallback can be restarted after stopping."""
        wrapped = Mock(spec=ProgressCallback)
        queued = QueuedProgressCallback(wrapped)

        # First cycle
        queued.start()
        queued.on_start("gemini", 90)
        time.sleep(0.2)
        queued.stop()

        first_call_count = wrapped.on_start.call_count

        # Second cycle
        queued.start()
        queued.on_start("codex", 120)
        time.sleep(0.2)
        queued.stop()

        # Should have two on_start calls total
        assert wrapped.on_start.call_count == first_call_count + 1

    def test_queue_preserves_update_sequence(self):
        """QueuedProgressCallback preserves exact sequence of rapid updates."""
        wrapped = Mock(spec=ProgressCallback)
        queued = QueuedProgressCallback(wrapped)

        queued.start()

        # Rapid sequence of updates with increasing elapsed times
        expected_sequence = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0]
        for elapsed in expected_sequence:
            queued.on_update("gemini", elapsed, 90)

        # Give time to process
        time.sleep(0.5)
        queued.stop()

        # Verify exact sequence was preserved
        assert wrapped.on_update.call_count == len(expected_sequence)
        actual_sequence = [
            call[1]["elapsed"]
            for call in wrapped.on_update.call_args_list
        ]
        assert actual_sequence == expected_sequence

    def test_queue_with_mixed_callback_types(self):
        """QueuedProgressCallback handles mixed callback types in sequence."""
        wrapped = Mock(spec=ProgressCallback)
        queued = QueuedProgressCallback(wrapped)

        queued.start()

        # Mix different callback types
        queued.on_start("gemini", 90)
        queued.on_update("gemini", 10.0, 90)
        queued.on_batch_start(["codex", "cursor-agent"], 2, 120)
        queued.on_update("gemini", 20.0, 90)
        response = ToolResponse(
            tool="codex",
            status=ToolStatus.SUCCESS,
            output="test",
            error=None,
            duration=45.0,
            timestamp="2025-11-07T12:00:00Z"
        )
        queued.on_tool_complete("codex", response, 1, 2)
        queued.on_complete("gemini", ToolStatus.SUCCESS, 30.0)
        queued.on_batch_complete(2, 2, 0, 100.0, 45.0)

        # Give time to process
        time.sleep(0.5)
        queued.stop()

        # Verify all callbacks were called
        assert wrapped.on_start.call_count == 1
        assert wrapped.on_update.call_count == 2
        assert wrapped.on_batch_start.call_count == 1
        assert wrapped.on_tool_complete.call_count == 1
        assert wrapped.on_complete.call_count == 1
        assert wrapped.on_batch_complete.call_count == 1

    def test_forwards_on_update_to_wrapped_callback(self):
        """QueuedProgressCallback forwards on_update calls to wrapped callback."""
        wrapped = Mock(spec=ProgressCallback)
        queued = QueuedProgressCallback(wrapped)

        queued.start()
        queued.on_update("gemini", elapsed=30.0, timeout=90)

        time.sleep(0.2)
        queued.stop()

        wrapped.on_update.assert_called_once()
        args, kwargs = wrapped.on_update.call_args
        assert kwargs["tool"] == "gemini"
        assert kwargs["elapsed"] == 30.0
        assert kwargs["timeout"] == 90

    def test_forwards_on_complete_to_wrapped_callback(self):
        """QueuedProgressCallback forwards on_complete calls to wrapped callback."""
        wrapped = Mock(spec=ProgressCallback)
        queued = QueuedProgressCallback(wrapped)

        queued.start()
        queued.on_complete("gemini", ToolStatus.SUCCESS, 45.0, output_length=1024)

        time.sleep(0.2)
        queued.stop()

        wrapped.on_complete.assert_called_once()
        args, kwargs = wrapped.on_complete.call_args
        assert kwargs["tool"] == "gemini"
        assert kwargs["status"] == ToolStatus.SUCCESS
        assert kwargs["duration"] == 45.0
        assert kwargs["output_length"] == 1024

    def test_handles_multiple_parallel_calls(self):
        """QueuedProgressCallback safely handles calls from multiple threads."""
        wrapped = Mock(spec=ProgressCallback)
        queued = QueuedProgressCallback(wrapped)

        queued.start()

        # Spawn multiple threads making calls
        def make_calls(thread_id):
            for i in range(10):
                queued.on_update(f"tool{thread_id}", elapsed=float(i), timeout=90)

        import threading
        threads = [
            threading.Thread(target=make_calls, args=(tid,))
            for tid in range(5)
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Give consumer time to process all
        time.sleep(0.5)
        queued.stop()

        # Should have called on_update 50 times (5 threads * 10 calls each)
        assert wrapped.on_update.call_count == 50

    def test_stops_cleanly(self):
        """QueuedProgressCallback stops consumer thread cleanly."""
        wrapped = Mock(spec=ProgressCallback)
        queued = QueuedProgressCallback(wrapped)

        queued.start()
        assert queued._consumer_thread is not None
        assert queued._consumer_thread.is_alive()

        queued.stop()

        # Thread should have stopped
        assert not queued._consumer_thread.is_alive()

    def test_ignores_duplicate_start(self):
        """QueuedProgressCallback ignores duplicate start() calls."""
        wrapped = Mock(spec=ProgressCallback)
        queued = QueuedProgressCallback(wrapped)

        queued.start()
        first_thread = queued._consumer_thread

        queued.start()  # Try to start again
        second_thread = queued._consumer_thread

        # Should be the same thread instance
        assert first_thread is second_thread

        queued.stop()

    def test_processes_queued_calls_in_order(self):
        """QueuedProgressCallback processes calls in FIFO order."""
        wrapped = Mock(spec=ProgressCallback)
        queued = QueuedProgressCallback(wrapped)

        queued.start()

        # Queue multiple different calls
        queued.on_start("gemini", 90)
        queued.on_update("gemini", 10.0, 90)
        queued.on_update("gemini", 20.0, 90)
        queued.on_complete("gemini", ToolStatus.SUCCESS, 30.0)

        # Give consumer time to process
        time.sleep(0.3)
        queued.stop()

        # Verify order using call_args_list
        assert wrapped.on_start.call_count == 1
        assert wrapped.on_update.call_count == 2
        assert wrapped.on_complete.call_count == 1

        # Check elapsed times are in order
        first_update = wrapped.on_update.call_args_list[0][1]["elapsed"]
        second_update = wrapped.on_update.call_args_list[1][1]["elapsed"]
        assert first_update == 10.0
        assert second_update == 20.0

    def test_handles_wrapped_callback_exceptions(self):
        """QueuedProgressCallback handles exceptions from wrapped callback gracefully."""
        wrapped = Mock(spec=ProgressCallback)
        wrapped.on_start.side_effect = Exception("Callback error")

        queued = QueuedProgressCallback(wrapped)
        queued.start()

        # This should not crash the consumer thread
        queued.on_start("gemini", 90)

        time.sleep(0.2)

        # Queue should still be working
        queued.on_update("gemini", 10.0, 90)

        time.sleep(0.2)
        queued.stop()

        # Both calls should have been attempted
        assert wrapped.on_start.call_count == 1
        assert wrapped.on_update.call_count == 1

    def test_forwards_batch_callbacks(self):
        """QueuedProgressCallback forwards batch-specific callbacks."""
        wrapped = Mock(spec=ProgressCallback)
        queued = QueuedProgressCallback(wrapped)

        queued.start()

        # Test batch_start
        queued.on_batch_start(["gemini", "codex"], 2, 120)

        # Test tool_complete
        response = ToolResponse(
            tool="gemini",
            status=ToolStatus.SUCCESS,
            output="test",
            error=None,
            duration=45.0,
            timestamp="2025-11-07T12:00:00Z"
        )
        queued.on_tool_complete("gemini", response, 1, 2)

        # Test batch_complete
        queued.on_batch_complete(
            total_count=2,
            success_count=2,
            failure_count=0,
            total_duration=100.0,
            max_duration=55.0
        )

        time.sleep(0.3)
        queued.stop()

        wrapped.on_batch_start.assert_called_once()
        wrapped.on_tool_complete.assert_called_once()
        wrapped.on_batch_complete.assert_called_once()

    def test_can_be_used_with_no_op_callback(self):
        """QueuedProgressCallback works with NoOpProgressCallback."""
        noop = NoOpProgressCallback()
        queued = QueuedProgressCallback(noop)

        queued.start()

        # Should not raise any exceptions
        queued.on_start("gemini", 90)
        queued.on_update("gemini", 30.0, 90)
        queued.on_complete("gemini", ToolStatus.SUCCESS, 45.0)

        time.sleep(0.2)
        queued.stop()


class TestProgressMessageFormatting:
    """Test progress message formatting helper."""

    def test_basic_message_format(self):
        """format_progress_message creates basic status message."""
        message = format_progress_message("gemini", 30.5)
        assert message == "Waiting for gemini... 30.5s"

    def test_message_with_timeout(self):
        """format_progress_message includes timeout when provided."""
        message = format_progress_message("gemini", 30.5, 90)
        assert message == "Waiting for gemini... 30.5s / 90s"

    def test_message_without_timeout_display(self):
        """format_progress_message excludes timeout when include_timeout=False."""
        message = format_progress_message("codex", 125.7, 300, include_timeout=False)
        assert message == "Waiting for codex... 125.7s"

    def test_formats_decimal_places(self):
        """format_progress_message formats elapsed time to 1 decimal place."""
        message = format_progress_message("gemini", 45.678)
        assert message == "Waiting for gemini... 45.7s"

    def test_formats_integer_elapsed(self):
        """format_progress_message handles integer elapsed time."""
        message = format_progress_message("gemini", 45)
        assert message == "Waiting for gemini... 45.0s"

    def test_formats_different_tool_names(self):
        """format_progress_message works with different tool names."""
        message1 = format_progress_message("gemini", 10.0)
        message2 = format_progress_message("codex", 20.0)
        message3 = format_progress_message("cursor-agent", 30.0)

        assert "gemini" in message1
        assert "codex" in message2
        assert "cursor-agent" in message3

    def test_formats_long_elapsed_times(self):
        """format_progress_message handles long elapsed times."""
        message = format_progress_message("gemini", 725.3, 900)
        assert message == "Waiting for gemini... 725.3s / 900s"

    def test_formats_zero_elapsed(self):
        """format_progress_message handles zero elapsed time."""
        message = format_progress_message("gemini", 0.0)
        assert message == "Waiting for gemini... 0.0s"
