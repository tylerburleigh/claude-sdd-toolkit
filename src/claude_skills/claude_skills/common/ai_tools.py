"""
AI Tool Consultation Interfaces

Standardized interfaces for interacting with external AI CLI tools (gemini, codex,
cursor-agent). Provides type-safe dataclasses, unified API, and comprehensive
error handling.

See docs/AI_TOOL_INTERFACES_DESIGN.md for complete design documentation.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from enum import Enum
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from claude_skills.common.providers import get_provider_detector


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


# =============================================================================
# TOOL AVAILABILITY FUNCTIONS
# =============================================================================

_TOOL_PATH_ENV = "CLAUDE_SKILLS_TOOL_PATH"


def _get_configured_tool_path() -> Optional[str]:
    """
    Return an explicit search path for tool discovery if configured.

    When ``CLAUDE_SKILLS_TOOL_PATH`` is set, detection uses that value (a PATH-style
    string) instead of the ambient ``PATH``. This allows tests to inject mock
    binaries without leaking to the developer's real tools.
    """
    value = os.environ.get(_TOOL_PATH_ENV)
    if value:
        return value
    return None


def _resolve_tool_executable(tool: str) -> Optional[str]:
    """
    Resolve the executable path for a tool, honoring the configured search path.
    """
    configured_path = _get_configured_tool_path()
    if configured_path is not None:
        return shutil.which(tool, path=configured_path)
    return shutil.which(tool)


def check_tool_available(
    tool: str,
    *,
    check_version: bool = False,
    timeout: int = 5
) -> bool:
    """
    Check if a tool is available and optionally working.

    Uses shutil.which() for fast PATH lookup. Optionally verifies tool
    responds to --version flag.

    Args:
        tool: Tool name to check (e.g., "gemini", "codex", "cursor-agent")
        check_version: If True, verify tool responds to --version
        timeout: Timeout in seconds for version check (default 5)

    Returns:
        True if tool is available (and working if check_version=True)

    Example:
        >>> check_tool_available("gemini")
        True
        >>> check_tool_available("nonexistent")
        False
        >>> check_tool_available("gemini", check_version=True)
        True
    """
    detector = get_provider_detector(tool)
    if detector is not None:
        return detector.is_available(use_probe=check_version)

    executable = _resolve_tool_executable(tool)

    # Quick PATH check
    if not executable:
        return False

    # Optional version check
    if check_version:
        try:
            result = subprocess.run(
                [executable, "--version"],
                capture_output=True,
                timeout=timeout,
                check=False
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False

    return True


def detect_available_tools(
    tools: Optional[list[str]] = None,
    *,
    check_version: bool = False
) -> list[str]:
    """
    Detect which AI tools are available in PATH.

    Args:
        tools: Optional list of tool names to check. If None, checks
            default tools: ["gemini", "codex", "cursor-agent"]
        check_version: If True, verify each tool responds to --version

    Returns:
        List of available tool names (empty if none found)

    Example:
        >>> detect_available_tools()
        ['gemini', 'codex']
        >>> detect_available_tools(["gemini", "nonexistent"])
        ['gemini']
        >>> detect_available_tools(check_version=True)
        ['gemini']
    """
    if tools is None:
        tools = ["gemini", "codex", "cursor-agent"]

    available = []
    for tool in tools:
        if check_tool_available(tool, check_version=check_version):
            available.append(tool)

    return available


def build_tool_command(
    tool: str,
    prompt: str,
    *,
    model: Optional[str] = None
) -> list[str]:
    """
    Build command list for tool execution.

    Handles tool-specific command patterns:
    - gemini: uses -m for model, -p for prompt
    - codex: uses -m for model, positional arg for prompt
    - cursor-agent: uses --print flag, positional arg for prompt

    Args:
        tool: Tool name ("gemini", "codex", "cursor-agent")
        prompt: The prompt to include in command
        model: Optional model override

    Returns:
        Command as list of strings (shell-safe)

    Raises:
        ValueError: If tool is unknown

    Example:
        >>> build_tool_command("gemini", "Analyze code", model="gemini-exp-1114")
        ['gemini', '-m', 'gemini-exp-1114', '--output-format', 'json', '-p', 'Analyze code']
        >>> build_tool_command("codex", "Fix bug", model="o1")
        ['codex', 'exec', '--sandbox', 'read-only', '--json', '-m', 'o1', 'Fix bug']
        >>> build_tool_command("cursor-agent", "Review code", model="composer-1")
        ['cursor-agent', '--print', '--json', '--model', 'composer-1', 'Review code']
    """
    if tool == "gemini":
        cmd = ["gemini"]
        if model:
            cmd.extend(["-m", model])
        # SECURITY: We intentionally do NOT add --yolo flag here
        # In non-interactive mode without --yolo, Gemini defaults to read-only tools only
        # IMPROVEMENT: Request JSON output for structured parsing
        cmd.extend(["--output-format", "json"])
        cmd.extend(["-p", prompt])
        return cmd

    elif tool == "codex":
        cmd = ["codex", "exec"]
        # SECURITY: Enforce read-only sandbox mode (critical for fidelity review)
        # NOTE: --sandbox read-only in exec mode runs non-interactively without approval prompts
        cmd.extend(["--sandbox", "read-only"])
        # IMPROVEMENT: Request JSON output for structured parsing
        cmd.append("--json")
        if model:
            cmd.extend(["-m", model])
        cmd.append(prompt)
        return cmd

    elif tool == "cursor-agent":
        # SECURITY: We intentionally do NOT add --force flag here
        # Without --force, Cursor Agent operates in propose-only mode (read-only)
        # IMPROVEMENT: Request JSON output for structured parsing
        cmd = ["cursor-agent", "--print"]
        cmd.append("--json")
        if model:
            cmd.extend(["--model", model])
        cmd.append(prompt)
        return cmd

    else:
        raise ValueError(f"Unknown tool: {tool}. Supported: gemini, codex, cursor-agent")


def _cursor_agent_json_flag_error(result: subprocess.CompletedProcess) -> bool:
    """
    Detect if cursor-agent failed because it does not support the --json flag.

    Args:
        result: CompletedProcess from subprocess.run

    Returns:
        True if diagnostics indicate --json is an unknown/unsupported option
    """
    if result.returncode == 0:
        return False

    diagnostics_parts = [result.stderr or "", result.stdout or ""]
    diagnostics = " ".join(part for part in diagnostics_parts if part).lower()

    if "--json" not in diagnostics:
        return False

    unsupported_indicators = [
        "unrecognized option",
        "unknown option",
        "unrecognized argument",
        "unknown argument",
        "no such option",
        "does not support",
        "not support",
        "flag provided but not defined",
        "invalid option",
    ]

    return any(indicator in diagnostics for indicator in unsupported_indicators)


def _remove_first_occurrence(items: list[str], token: str) -> tuple[list[str], bool]:
    """
    Remove the first occurrence of token from a list without mutating the original.

    Returns a tuple of (new_list, removed_flag).
    """
    removed = False
    new_items: list[str] = []
    for item in items:
        if item == token and not removed:
            removed = True
            continue
        new_items.append(item)
    return new_items, removed


# =============================================================================
# TOOL EXECUTION FUNCTIONS
# =============================================================================


def execute_tool(
    tool: str,
    prompt: str,
    *,
    model: Optional[str] = None,
    timeout: int = 90
) -> ToolResponse:
    """
    Execute AI tool with a prompt and return structured response.

    Handles all subprocess error modes: timeout, not found, invalid output,
    and general errors. Always returns a ToolResponse with appropriate status.

    Args:
        tool: Tool name ("gemini", "codex", "cursor-agent")
        prompt: The prompt to send to the tool
        model: Optional model override
        timeout: Timeout in seconds (default 90)

    Returns:
        ToolResponse with execution results and metadata

    Example:
        >>> response = execute_tool("gemini", "Analyze code", timeout=60)
        >>> if response.success:
        ...     print(response.output)
        >>> else:
        ...     print(f"Failed: {response.error}")
    """
    start_time = time.time()
    timestamp = datetime.now().isoformat()

    try:
        # Build command
        command = build_tool_command(tool, prompt, model=model)

        # Execute with timeout
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False  # Don't raise on non-zero exit
        )

        # Check exit code
        if result.returncode == 0:
            duration = time.time() - start_time
            return ToolResponse(
                tool=tool,
                status=ToolStatus.SUCCESS,
                output=result.stdout.strip(),
                error=None,
                duration=duration,
                timestamp=timestamp,
                model=model,
                prompt=prompt,
                exit_code=0
            )

        # Retry cursor-agent once without --json if it appears unsupported
        if (
            tool == "cursor-agent"
            and "--json" in command
            and _cursor_agent_json_flag_error(result)
        ):
            fallback_command, removed = _remove_first_occurrence(command, "--json")

            if removed:
                fallback_result = subprocess.run(
                    fallback_command,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False
                )

                if fallback_result.returncode == 0:
                    duration = time.time() - start_time
                    return ToolResponse(
                        tool=tool,
                        status=ToolStatus.SUCCESS,
                        output=fallback_result.stdout.strip(),
                        error=None,
                        duration=duration,
                        timestamp=timestamp,
                        model=model,
                        prompt=prompt,
                        exit_code=0,
                        metadata={"cursor_agent_retry_without_json": True}
                    )

                duration = time.time() - start_time
                first_error = result.stderr.strip() or result.stdout.strip() or f"Tool exited with code {result.returncode}"
                second_error = fallback_result.stderr.strip() or fallback_result.stdout.strip() or f"Tool exited with code {fallback_result.returncode}"
                combined_error = (
                    "cursor-agent rejected '--json' flag "
                    f"(exit code {result.returncode}): {first_error}. "
                    "Retry without '--json' also failed "
                    f"(exit code {fallback_result.returncode}): {second_error}"
                )

                return ToolResponse(
                    tool=tool,
                    status=ToolStatus.ERROR,
                    output=fallback_result.stdout.strip() or result.stdout.strip(),
                    error=combined_error,
                    duration=duration,
                    timestamp=timestamp,
                    model=model,
                    prompt=prompt,
                    exit_code=fallback_result.returncode,
                    metadata={"cursor_agent_retry_without_json": True}
                )

        duration = time.time() - start_time

        # Non-zero exit code without retry
        return ToolResponse(
            tool=tool,
            status=ToolStatus.ERROR,
            output=result.stdout.strip(),
            error=result.stderr.strip() or f"Tool exited with code {result.returncode}",
            duration=duration,
            timestamp=timestamp,
            model=model,
            prompt=prompt,
            exit_code=result.returncode
        )

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return ToolResponse(
            tool=tool,
            status=ToolStatus.TIMEOUT,
            output="",
            error=f"Tool timed out after {timeout}s",
            duration=duration,
            timestamp=timestamp,
            model=model,
            prompt=prompt,
            exit_code=None
        )

    except FileNotFoundError:
        duration = time.time() - start_time
        return ToolResponse(
            tool=tool,
            status=ToolStatus.NOT_FOUND,
            output="",
            error=f"Tool '{tool}' not found in PATH",
            duration=duration,
            timestamp=timestamp,
            model=model,
            prompt=prompt,
            exit_code=None
        )

    except ValueError as e:
        # Unknown tool from build_tool_command
        duration = time.time() - start_time
        return ToolResponse(
            tool=tool,
            status=ToolStatus.ERROR,
            output="",
            error=str(e),
            duration=duration,
            timestamp=timestamp,
            model=model,
            prompt=prompt,
            exit_code=None
        )

    except Exception as e:
        # Unexpected error
        duration = time.time() - start_time
        return ToolResponse(
            tool=tool,
            status=ToolStatus.ERROR,
            output="",
            error=f"Unexpected error: {type(e).__name__}: {str(e)}",
            duration=duration,
            timestamp=timestamp,
            model=model,
            prompt=prompt,
            exit_code=None
        )


def execute_tools_parallel(
    tools: list[str],
    prompt: str,
    *,
    models: Optional[dict[str, str]] = None,
    timeout: int = 90
) -> MultiToolResponse:
    """
    Execute multiple AI tools in parallel with same prompt.

    Uses ThreadPoolExecutor to run tools concurrently. Returns as soon
    as each tool completes (doesn't wait for slowest).

    Args:
        tools: List of tool names to execute
        prompt: The prompt to send to all tools
        models: Optional dict mapping tool names to models
        timeout: Timeout per tool in seconds (default 90)

    Returns:
        MultiToolResponse with all results and aggregated statistics

    Example:
        >>> response = execute_tools_parallel(
        ...     tools=["gemini", "codex"],
        ...     prompt="Analyze code",
        ...     models={"gemini": "gemini-exp-1114"}
        ... )
        >>> print(f"Success: {response.success_count}/{len(response.responses)}")
        >>> for tool, resp in response.get_successful_responses().items():
        ...     print(f"{tool}: {resp.output[:50]}...")
    """
    if not tools:
        # No tools provided
        return MultiToolResponse(
            responses={},
            success_count=0,
            failure_count=0,
            total_duration=0.0,
            max_duration=0.0
        )

    start_time = time.time()
    timestamp = datetime.now().isoformat()
    models = models or {}

    responses = {}

    # Execute tools in parallel
    with ThreadPoolExecutor(max_workers=len(tools)) as executor:
        # Submit all tasks
        future_to_tool = {
            executor.submit(
                execute_tool,
                tool,
                prompt,
                model=models.get(tool),
                timeout=timeout
            ): tool
            for tool in tools
        }

        # Collect results as they complete
        for future in as_completed(future_to_tool):
            tool = future_to_tool[future]
            try:
                response = future.result(timeout=timeout + 5)  # Small buffer
                responses[tool] = response
            except Exception as e:
                # Shouldn't happen (execute_tool handles all errors)
                # but handle it just in case
                responses[tool] = ToolResponse(
                    tool=tool,
                    status=ToolStatus.ERROR,
                    output="",
                    error=f"Parallel execution error: {str(e)}",
                    duration=0.0,
                    timestamp=timestamp,
                    model=models.get(tool),
                    prompt=prompt
                )

    total_duration = time.time() - start_time

    # Calculate statistics
    success_count = sum(1 for r in responses.values() if r.success)
    failure_count = len(responses) - success_count
    max_duration = max((r.duration for r in responses.values()), default=0.0)

    return MultiToolResponse(
        responses=responses,
        synthesis=None,  # Synthesis is added by separate function
        total_duration=total_duration,
        max_duration=max_duration,
        success_count=success_count,
        failure_count=failure_count,
        timestamp=timestamp,
        failure_type=None
    )


# Export public API
__all__ = [
    "ToolStatus",
    "ToolResponse",
    "MultiToolResponse",
    "check_tool_available",
    "detect_available_tools",
    "build_tool_command",
    "execute_tool",
    "execute_tools_parallel",
]
