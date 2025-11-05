"""
AI Tool Consultation Interfaces

Standardized interfaces for interacting with external AI CLI tools (gemini, codex,
cursor-agent). Provides type-safe dataclasses, unified API, and comprehensive
error handling.

See docs/AI_TOOL_INTERFACES_DESIGN.md for complete design documentation.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum


class ToolStatus(Enum):
    """Status of AI tool execution."""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    INVALID_OUTPUT = "invalid_output"
    ERROR = "error"


@dataclass(frozen=True)
class ToolResponse:
    """
    Standardized response from AI tool consultation.

    This is the core response type used throughout the toolkit for
    all AI tool interactions.

    Attributes:
        tool: Name of the tool (gemini, codex, cursor-agent)
        status: Execution status (success, timeout, error, etc.)
        output: Raw output from the tool (stdout)
        error: Error message if any (stderr or exception message)
        duration: Execution time in seconds
        timestamp: When the consultation started (ISO format)
        model: Model used by the tool (if applicable)
        prompt: The prompt sent to the tool (optional, for debugging)
        exit_code: Process exit code (None if didn't run)
        metadata: Additional tool-specific metadata

    Example:
        >>> response = ToolResponse(
        ...     tool="gemini",
        ...     status=ToolStatus.SUCCESS,
        ...     output="Analysis complete",
        ...     duration=2.5
        ... )
        >>> response.success
        True
        >>> response.to_dict()
        {...}
    """
    tool: str
    status: ToolStatus
    output: str = ""
    error: Optional[str] = None
    duration: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    model: Optional[str] = None
    prompt: Optional[str] = None
    exit_code: Optional[int] = None
    metadata: dict = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if tool execution was successful."""
        return self.status == ToolStatus.SUCCESS

    @property
    def failed(self) -> bool:
        """Check if tool execution failed."""
        return not self.success

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "tool": self.tool,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "duration": self.duration,
            "timestamp": self.timestamp,
            "model": self.model,
            "prompt": self.prompt,
            "exit_code": self.exit_code,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ToolResponse":
        """
        Create from dictionary.

        Args:
            data: Dictionary with tool response data

        Returns:
            ToolResponse instance

        Raises:
            ValueError: If status value is invalid
        """
        # Convert status string to enum
        data = data.copy()  # Don't mutate input
        data["status"] = ToolStatus(data["status"])
        return cls(**data)


@dataclass(frozen=True)
class MultiToolResponse:
    """
    Response from multiple tool consultations run in parallel.

    Attributes:
        responses: Dictionary mapping tool names to their responses
        synthesis: Optional synthesis/consensus from all responses
        total_duration: Total wall-clock time (parallel execution)
        max_duration: Longest individual tool duration
        success_count: Number of successful tool calls
        failure_count: Number of failed tool calls
        timestamp: When the multi-tool consultation started
        failure_type: Optional failure type that triggered consultation

    Example:
        >>> responses = {
        ...     "gemini": ToolResponse(tool="gemini", status=ToolStatus.SUCCESS),
        ...     "codex": ToolResponse(tool="codex", status=ToolStatus.ERROR)
        ... }
        >>> multi = MultiToolResponse(
        ...     responses=responses,
        ...     success_count=1,
        ...     failure_count=1
        ... )
        >>> multi.success
        True
        >>> successful = multi.get_successful_responses()
        >>> len(successful)
        1
    """
    responses: dict[str, ToolResponse]
    synthesis: Optional[str] = None
    total_duration: float = 0.0
    max_duration: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    failure_type: Optional[str] = None

    @property
    def success(self) -> bool:
        """Check if at least one tool succeeded."""
        return self.success_count > 0

    @property
    def all_failed(self) -> bool:
        """Check if all tools failed."""
        return self.success_count == 0

    @property
    def all_succeeded(self) -> bool:
        """Check if all tools succeeded."""
        return self.failure_count == 0

    def get_successful_responses(self) -> dict[str, ToolResponse]:
        """
        Get only successful tool responses.

        Returns:
            Dictionary mapping tool names to successful responses
        """
        return {
            tool: response
            for tool, response in self.responses.items()
            if response.success
        }

    def get_failed_responses(self) -> dict[str, ToolResponse]:
        """
        Get only failed tool responses.

        Returns:
            Dictionary mapping tool names to failed responses
        """
        return {
            tool: response
            for tool, response in self.responses.items()
            if response.failed
        }

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "responses": {
                tool: response.to_dict()
                for tool, response in self.responses.items()
            },
            "synthesis": self.synthesis,
            "total_duration": self.total_duration,
            "max_duration": self.max_duration,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "timestamp": self.timestamp,
            "failure_type": self.failure_type
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MultiToolResponse":
        """
        Create from dictionary.

        Args:
            data: Dictionary with multi-tool response data

        Returns:
            MultiToolResponse instance
        """
        data = data.copy()  # Don't mutate input
        # Convert nested responses
        data["responses"] = {
            tool: ToolResponse.from_dict(resp_data)
            for tool, resp_data in data["responses"].items()
        }
        return cls(**data)


# Export public API
__all__ = [
    "ToolStatus",
    "ToolResponse",
    "MultiToolResponse",
]
