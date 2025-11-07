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
import threading
import logging
import queue

from .ai_tools import ToolStatus, ToolResponse, MultiToolResponse

logger = logging.getLogger(__name__)


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


def _calculate_update_interval(timeout: int, custom_interval: Optional[float] = None) -> float:
    """
    Calculate appropriate update interval based on timeout.

    Args:
        timeout: Expected timeout in seconds
        custom_interval: Optional custom interval override

    Returns:
        Update interval in seconds
    """
    if custom_interval is not None:
        return custom_interval

    # Intelligent interval based on timeout duration
    if timeout < 30:
        return 2.0  # Short operations: update every 2s
    elif timeout <= 120:
        return 5.0  # Medium operations: update every 5s
    else:
        return 10.0  # Long operations: update every 10s


def format_progress_message(
    tool: str,
    elapsed: float,
    timeout: Optional[int] = None,
    include_timeout: bool = True
) -> str:
    """
    Format a progress status message for display.

    Args:
        tool: Tool name (e.g., "gemini", "codex")
        elapsed: Elapsed time in seconds
        timeout: Optional timeout in seconds
        include_timeout: Whether to include timeout in message

    Returns:
        Formatted message like "Waiting for gemini... 30.5s" or
        "Waiting for gemini... 30.5s / 90s"

    Examples:
        >>> format_progress_message("gemini", 30.5)
        'Waiting for gemini... 30.5s'

        >>> format_progress_message("gemini", 30.5, 90)
        'Waiting for gemini... 30.5s / 90s'

        >>> format_progress_message("codex", 125.7, 300, include_timeout=False)
        'Waiting for codex... 125.7s'
    """
    # Format elapsed time (1 decimal place)
    elapsed_str = f"{elapsed:.1f}s"

    # Base message
    message = f"Waiting for {tool}... {elapsed_str}"

    # Add timeout if requested
    if include_timeout and timeout is not None:
        message += f" / {timeout}s"

    return message


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


class QueuedProgressCallback:
    """
    Thread-safe progress callback wrapper using queue.Queue.

    Wraps a ProgressCallback and routes all calls through a queue,
    making it safe to call from multiple worker threads in parallel
    consultations. A consumer thread processes the queue and forwards
    calls to the underlying callback.

    Usage:
        # Create queued wrapper
        queued = QueuedProgressCallback(callback)
        queued.start()  # Start consumer thread

        # Use from multiple threads
        queued.on_start("tool", 90)
        queued.on_complete("tool", ToolStatus.SUCCESS, 45.0)

        # Cleanup
        queued.stop()  # Stop consumer thread
    """

    def __init__(self, wrapped: ProgressCallback):
        """
        Initialize queued callback wrapper.

        Args:
            wrapped: The underlying ProgressCallback to forward calls to
        """
        self.wrapped = wrapped
        self._queue: queue.Queue = queue.Queue()
        self._consumer_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        """Start the consumer thread that processes queued callback calls."""
        if self._consumer_thread and self._consumer_thread.is_alive():
            return  # Already running

        self._stop_event.clear()
        self._consumer_thread = threading.Thread(
            target=self._consume_queue,
            daemon=True,
            name="progress-queue-consumer"
        )
        self._consumer_thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        """
        Stop the consumer thread.

        Args:
            timeout: Maximum time to wait for thread to finish (seconds)
        """
        if not self._consumer_thread:
            return

        # Signal stop and put sentinel
        self._stop_event.set()
        self._queue.put(None)  # Sentinel to wake up consumer

        # Wait for thread to finish
        if self._consumer_thread.is_alive():
            self._consumer_thread.join(timeout=timeout)

    def _consume_queue(self) -> None:
        """Consumer thread worker that processes queued callbacks."""
        while not self._stop_event.is_set():
            try:
                # Get next item with timeout so we can check stop_event
                item = self._queue.get(timeout=0.1)

                # Check for sentinel (None means stop)
                if item is None:
                    break

                # Unpack and execute callback
                method_name, args, kwargs = item
                method = getattr(self.wrapped, method_name)
                method(*args, **kwargs)

            except queue.Empty:
                # Timeout expired, check stop_event
                continue
            except Exception as e:
                logger.warning(f"Error processing queued callback: {e}")

    def _enqueue(self, method_name: str, *args, **kwargs) -> None:
        """
        Enqueue a callback method call.

        Args:
            method_name: Name of the callback method to call
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        self._queue.put((method_name, args, kwargs))

    def on_start(self, tool: str, timeout: int, **context) -> None:
        """Queue on_start callback."""
        self._enqueue("on_start", tool=tool, timeout=timeout, **context)

    def on_update(self, tool: str, elapsed: float, timeout: int, **context) -> None:
        """Queue on_update callback."""
        self._enqueue("on_update", tool=tool, elapsed=elapsed, timeout=timeout, **context)

    def on_complete(self, tool: str, status: ToolStatus, duration: float, **context) -> None:
        """Queue on_complete callback."""
        self._enqueue("on_complete", tool=tool, status=status, duration=duration, **context)

    def on_batch_start(self, tools: list[str], count: int, timeout: int, **context) -> None:
        """Queue on_batch_start callback."""
        self._enqueue("on_batch_start", tools=tools, count=count, timeout=timeout, **context)

    def on_tool_complete(
        self,
        tool: str,
        response: ToolResponse,
        completed_count: int,
        total_count: int
    ) -> None:
        """Queue on_tool_complete callback."""
        self._enqueue(
            "on_tool_complete",
            tool=tool,
            response=response,
            completed_count=completed_count,
            total_count=total_count
        )

    def on_batch_complete(
        self,
        total_count: int,
        success_count: int,
        failure_count: int,
        total_duration: float,
        max_duration: float
    ) -> None:
        """Queue on_batch_complete callback."""
        self._enqueue(
            "on_batch_complete",
            total_count=total_count,
            success_count=success_count,
            failure_count=failure_count,
            total_duration=total_duration,
            max_duration=max_duration
        )


@dataclass
class ProgressTracker:
    """Tracks progress state within context manager."""
    tool: str
    timeout: int
    callback: ProgressCallback
    context: dict[str, Any]
    start_time: float = 0.0
    completed: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _update_thread: Optional[threading.Thread] = field(default=None, init=False, repr=False)

    def complete(self, response: ToolResponse) -> None:
        """
        Mark consultation as complete with response.

        Args:
            response: ToolResponse from AI tool execution
        """
        with self._lock:
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
            logger.warning(f"Progress callback error in on_complete: {e}")


def _update_worker(tracker: ProgressTracker, interval: float) -> None:
    """
    Background worker thread for periodic progress updates.

    Args:
        tracker: ProgressTracker to monitor
        interval: Update interval in seconds
    """
    while True:
        time.sleep(interval)

        # Check if completed (thread-safe)
        with tracker._lock:
            if tracker.completed:
                break

        # Calculate elapsed time
        elapsed = time.time() - tracker.start_time

        # Call update callback
        try:
            tracker.callback.on_update(
                tool=tracker.tool,
                elapsed=elapsed,
                timeout=tracker.timeout,
                **tracker.context
            )
        except Exception as e:
            logger.warning(f"Progress callback error in on_update: {e}")


@contextmanager
def ai_consultation_progress(
    tool: str,
    timeout: int = 90,
    callback: Optional[ProgressCallback] = None,
    update_interval: Optional[float] = None,
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
        update_interval: Optional custom update interval in seconds (auto-calculated if None)
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
        logger.warning(f"Progress callback error in on_start: {e}")

    tracker.start_time = time.time()

    # Start background update thread
    interval = _calculate_update_interval(timeout, update_interval)
    update_thread = threading.Thread(
        target=_update_worker,
        args=(tracker, interval),
        daemon=True,
        name=f"progress-update-{tool}"
    )
    tracker._update_thread = update_thread
    update_thread.start()

    try:
        yield tracker
    except Exception as e:
        # Handle errors gracefully
        with tracker._lock:
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
            logger.warning(f"Progress callback error in on_complete (exception): {callback_error}")
        raise
    finally:
        # Ensure cleanup happens
        with tracker._lock:
            was_completed = tracker.completed
            if not tracker.completed:
                tracker.completed = True

        # Wait for update thread to finish (it will exit when it sees completed=True)
        if tracker._update_thread and tracker._update_thread.is_alive():
            tracker._update_thread.join(timeout=1.0)

        if not was_completed:
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
                logger.warning(f"Progress callback error in on_complete (finally): {callback_error}")


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
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _update_thread: Optional[threading.Thread] = field(default=None, init=False, repr=False)
    _all_complete: bool = field(default=False, init=False, repr=False)

    def mark_complete(self, tool: str, response: ToolResponse) -> None:
        """
        Mark individual tool as complete.

        Args:
            tool: Tool name
            response: ToolResponse from tool execution
        """
        with self._lock:
            if tool in self.completed_tools:
                return  # Prevent double-counting

            self.completed_tools.append(tool)

            if response.success:
                self.success_count += 1
            else:
                self.failure_count += 1

            self.max_duration = max(self.max_duration, response.duration)

            # Check if all tools are complete
            if len(self.completed_tools) >= len(self.tools):
                self._all_complete = True

        try:
            self.callback.on_tool_complete(
                tool=tool,
                response=response,
                completed_count=len(self.completed_tools),
                total_count=len(self.tools)
            )
        except Exception as e:
            logger.warning(f"Progress callback error in on_tool_complete: {e}")


def _batch_update_worker(tracker: BatchProgressTracker, interval: float) -> None:
    """
    Background worker thread for periodic batch progress updates.

    Args:
        tracker: BatchProgressTracker to monitor
        interval: Update interval in seconds
    """
    # Note: For batch operations, we track elapsed time for the entire batch,
    # not individual tools. Individual tool completion is reported via on_tool_complete.
    while True:
        time.sleep(interval)

        # Check if all tools are complete (thread-safe)
        with tracker._lock:
            if tracker._all_complete:
                break

        # Calculate elapsed time for the batch
        elapsed = time.time() - tracker.start_time

        # Call update callback with batch context
        # Use first tool name as representative (or "batch" as tool name)
        tool_name = tracker.tools[0] if tracker.tools else "batch"
        try:
            tracker.callback.on_update(
                tool=tool_name,
                elapsed=elapsed,
                timeout=tracker.timeout,
                batch_mode=True,
                completed_count=len(tracker.completed_tools),
                total_count=len(tracker.tools),
                **tracker.context
            )
        except Exception as e:
            logger.warning(f"Progress callback error in batch on_update: {e}")


@contextmanager
def batch_consultation_progress(
    tools: list[str],
    timeout: int = 90,
    callback: Optional[ProgressCallback] = None,
    update_interval: Optional[float] = None,
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
        update_interval: Optional custom update interval in seconds (auto-calculated if None)
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
        logger.warning(f"Progress callback error in on_batch_start: {e}")

    tracker.start_time = time.time()

    # Start background update thread for batch
    interval = _calculate_update_interval(timeout, update_interval)
    update_thread = threading.Thread(
        target=_batch_update_worker,
        args=(tracker, interval),
        daemon=True,
        name=f"batch-progress-update"
    )
    tracker._update_thread = update_thread
    update_thread.start()

    try:
        yield tracker
    finally:
        # Mark batch as complete
        with tracker._lock:
            tracker._all_complete = True

        # Wait for update thread to finish
        if tracker._update_thread and tracker._update_thread.is_alive():
            tracker._update_thread.join(timeout=1.0)

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
            logger.warning(f"Progress callback error in on_batch_complete: {e}")


__all__ = [
    "ProgressCallback",
    "NoOpProgressCallback",
    "QueuedProgressCallback",
    "ai_consultation_progress",
    "batch_consultation_progress",
    "ProgressTracker",
    "BatchProgressTracker",
    "format_progress_message",
]
