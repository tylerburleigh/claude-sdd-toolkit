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
