"""
TUI progress feedback for AI tool consultations.

Provides context managers and callbacks for displaying progress
indicators during long-running AI tool executions.
"""

from contextlib import contextmanager
from typing import Optional, Protocol, Any
from dataclasses import dataclass, field
from enum import Enum
import time

from .ai_tools import ToolStatus, ToolResponse, MultiToolResponse


class ProgressCallback(Protocol):
    """Protocol for progress feedback callbacks."""

    def on_start(self, tool: str, timeout: int, **context) -> None:
        """Called when tool execution starts."""
        ...

    def on_update(self, tool: str, elapsed: float, timeout: int, **context) -> None:
        """Called periodically during execution (Phase 5 feature)."""
        ...

    def on_complete(
        self,
        tool: str,
        status: ToolStatus,
        duration: float,
        **context
    ) -> None:
        """Called when tool execution completes."""
        ...

    def on_batch_start(
        self,
        tools: list[str],
        count: int,
        timeout: int,
        **context
    ) -> None:
        """Called when parallel execution starts."""
        ...

    def on_tool_complete(
        self,
        tool: str,
        response: ToolResponse,
        completed_count: int,
        total_count: int
    ) -> None:
        """Called when individual tool in batch completes."""
        ...

    def on_batch_complete(
        self,
        total_count: int,
        success_count: int,
        failure_count: int,
        total_duration: float,
        max_duration: float
    ) -> None:
        """Called when all tools in batch complete."""
        ...


class NoOpProgressCallback:
    """No-op implementation for environments without TUI support."""

    def on_start(self, tool: str, timeout: int, **context) -> None:
        """No-op start handler."""
        pass

    def on_update(self, tool: str, elapsed: float, timeout: int, **context) -> None:
        """No-op update handler."""
        pass

    def on_complete(self, tool: str, status: ToolStatus, duration: float, **context) -> None:
        """No-op completion handler."""
        pass

    def on_batch_start(self, tools: list[str], count: int, timeout: int, **context) -> None:
        """No-op batch start handler."""
        pass

    def on_tool_complete(
        self,
        tool: str,
        response: ToolResponse,
        completed_count: int,
        total_count: int
    ) -> None:
        """No-op tool completion handler."""
        pass

    def on_batch_complete(
        self,
        total_count: int,
        success_count: int,
        failure_count: int,
        total_duration: float,
        max_duration: float
    ) -> None:
        """No-op batch completion handler."""
        pass


@dataclass
class ProgressTracker:
    """Tracks progress state within context manager."""
    tool: str
    timeout: int
    callback: ProgressCallback
    context: dict[str, Any]
    start_time: float = 0.0
    completed: bool = False

    def complete(self, response: ToolResponse) -> None:
        """
        Mark consultation as complete with response.

        Args:
            response: ToolResponse from AI tool execution
        """
        if self.completed:
            return  # Prevent double-completion

        self.completed = True
        duration = time.time() - self.start_time

        try:
            self.callback.on_complete(
                tool=self.tool,
                status=response.status,
                duration=duration,
                output_length=len(response.output) if response.output else 0,
                error=response.error,
                **self.context
            )
        except Exception as e:
            # Don't let callback errors break execution
            import logging
            logging.warning(f"Progress callback error in on_complete: {e}")


@contextmanager
def ai_consultation_progress(
    tool: str,
    timeout: int = 90,
    callback: Optional[ProgressCallback] = None,
    **context
):
    """
    Context manager for AI consultation with progress feedback.

    Automatically handles progress lifecycle: start, update (Phase 5), and completion.
    Ensures cleanup even if exceptions occur.

    Usage:
        with ai_consultation_progress("gemini", timeout=90) as progress:
            response = execute_tool("gemini", prompt)
            progress.complete(response)

    Args:
        tool: Tool name ("gemini", "codex", "cursor-agent")
        timeout: Expected timeout in seconds (default 90)
        callback: Optional progress callback (defaults to no-op)
        **context: Additional context for progress display (model, prompt_length, etc.)

    Yields:
        ProgressTracker: Progress tracker object with complete() method
    """
    if callback is None:
        callback = NoOpProgressCallback()

    # Track state
    tracker = ProgressTracker(
        tool=tool,
        timeout=timeout,
        callback=callback,
        context=context
    )

    # Start progress
    try:
        callback.on_start(tool=tool, timeout=timeout, **context)
    except Exception as e:
        import logging
        logging.warning(f"Progress callback error in on_start: {e}")

    tracker.start_time = time.time()

    try:
        yield tracker
    except Exception as e:
        # Handle errors gracefully
        if not tracker.completed:
            tracker.completed = True  # Mark as completed to prevent double-call in finally
            duration = time.time() - tracker.start_time
            try:
                callback.on_complete(
                    tool=tool,
                    status=ToolStatus.ERROR,
                    duration=duration,
                    error=str(e),
                    **context
                )
            except Exception as callback_error:
                import logging
                logging.warning(f"Progress callback error in on_complete (exception): {callback_error}")
        raise
    finally:
        # Ensure cleanup happens
        if not tracker.completed:
            # Auto-complete if user forgot to call complete()
            duration = time.time() - tracker.start_time
            try:
                callback.on_complete(
                    tool=tool,
                    status=ToolStatus.SUCCESS,
                    duration=duration,
                    **context
                )
            except Exception as callback_error:
                import logging
                logging.warning(f"Progress callback error in on_complete (finally): {callback_error}")


@dataclass
class BatchProgressTracker:
    """Tracks progress for batch consultations."""
    tools: list[str]
    timeout: int
    callback: ProgressCallback
    context: dict[str, Any]
    start_time: float = 0.0
    completed_tools: list[str] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    max_duration: float = 0.0

    def mark_complete(self, tool: str, response: ToolResponse) -> None:
        """
        Mark individual tool as complete.

        Args:
            tool: Tool name
            response: ToolResponse from tool execution
        """
        if tool in self.completed_tools:
            return  # Prevent double-counting

        self.completed_tools.append(tool)

        if response.success:
            self.success_count += 1
        else:
            self.failure_count += 1

        self.max_duration = max(self.max_duration, response.duration)

        try:
            self.callback.on_tool_complete(
                tool=tool,
                response=response,
                completed_count=len(self.completed_tools),
                total_count=len(self.tools)
            )
        except Exception as e:
            import logging
            logging.warning(f"Progress callback error in on_tool_complete: {e}")


@contextmanager
def batch_consultation_progress(
    tools: list[str],
    timeout: int = 90,
    callback: Optional[ProgressCallback] = None,
    **context
):
    """
    Context manager for batch AI consultation with progress feedback.

    Handles parallel tool execution with per-tool and aggregate progress tracking.

    Usage:
        with batch_consultation_progress(["gemini", "codex"], timeout=120) as progress:
            multi_response = execute_tools_parallel(...)
            for tool, response in multi_response.responses.items():
                progress.mark_complete(tool, response)

    Args:
        tools: List of tool names to execute
        timeout: Per-tool timeout in seconds (default 90)
        callback: Optional progress callback (defaults to no-op)
        **context: Additional context for progress display

    Yields:
        BatchProgressTracker: Batch progress tracker with mark_complete() method
    """
    if callback is None:
        callback = NoOpProgressCallback()

    tracker = BatchProgressTracker(
        tools=tools,
        timeout=timeout,
        callback=callback,
        context=context
    )

    # Start batch
    try:
        callback.on_batch_start(
            tools=tools,
            count=len(tools),
            timeout=timeout,
            **context
        )
    except Exception as e:
        import logging
        logging.warning(f"Progress callback error in on_batch_start: {e}")

    tracker.start_time = time.time()

    try:
        yield tracker
    finally:
        # Batch complete
        total_duration = time.time() - tracker.start_time
        try:
            callback.on_batch_complete(
                total_count=len(tools),
                success_count=tracker.success_count,
                failure_count=tracker.failure_count,
                total_duration=total_duration,
                max_duration=tracker.max_duration
            )
        except Exception as e:
            import logging
            logging.warning(f"Progress callback error in on_batch_complete: {e}")


__all__ = [
    "ProgressCallback",
    "NoOpProgressCallback",
    "ai_consultation_progress",
    "batch_consultation_progress",
    "ProgressTracker",
    "BatchProgressTracker",
]
