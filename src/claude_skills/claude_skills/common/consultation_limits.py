"""
Consultation limits tracking for AI tool usage.

This module provides thread-safe tracking of the number of unique AI tools/providers
consulted during a single skill invocation, allowing enforcement of per-run limits.
"""

import threading
from typing import Set, Optional


class ConsultationTracker:
    """
    Thread-safe tracker for unique AI tools consulted during a skill run.

    Tracks the set of unique tools used (e.g., gemini, cursor-agent, codex, claude)
    to enforce max_tools_per_run limits defined in ai_config.yaml.
    """

    def __init__(self):
        """Initialize the consultation tracker with an empty tool set."""
        self._tools_used: Set[str] = set()
        self._lock = threading.Lock()

    def record_consultation(self, tool: str) -> None:
        """
        Record that a tool was consulted.

        Args:
            tool: The tool/provider name (e.g., 'gemini', 'cursor-agent')
        """
        with self._lock:
            self._tools_used.add(tool)

    def get_tools_used(self) -> Set[str]:
        """
        Get the set of unique tools that have been consulted.

        Returns:
            A copy of the set of tool names that have been consulted
        """
        with self._lock:
            return self._tools_used.copy()

    def get_count(self) -> int:
        """
        Get the number of unique tools that have been consulted.

        Returns:
            The count of unique tools used
        """
        with self._lock:
            return len(self._tools_used)

    def check_limit(self, tool: str, max_tools: Optional[int]) -> bool:
        """
        Check if consulting a tool would exceed the limit.

        Args:
            tool: The tool/provider name to check
            max_tools: Maximum number of unique tools allowed (None = unlimited)

        Returns:
            True if consulting this tool is allowed, False if it would exceed the limit
        """
        if max_tools is None:
            return True

        with self._lock:
            # If we've already used this tool, it doesn't count against the limit
            if tool in self._tools_used:
                return True

            # Check if adding a new tool would exceed the limit
            return len(self._tools_used) < max_tools

    def reset(self) -> None:
        """Reset the tracker, clearing all recorded consultations."""
        with self._lock:
            self._tools_used.clear()

    def __repr__(self) -> str:
        """String representation of the tracker state."""
        with self._lock:
            return f"ConsultationTracker(tools_used={self._tools_used})"


# Global tracker instance for the current skill run
# This should be reset at the start of each skill invocation
_global_tracker = ConsultationTracker()


def get_global_tracker() -> ConsultationTracker:
    """
    Get the global consultation tracker instance.

    Returns:
        The global ConsultationTracker instance
    """
    return _global_tracker


def reset_global_tracker() -> None:
    """Reset the global consultation tracker."""
    _global_tracker.reset()
