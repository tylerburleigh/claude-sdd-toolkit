"""
JSON output formatting utilities for SDD CLI commands.

This module provides utilities for formatting CLI command outputs as JSON,
with support for both pretty-printed (human-readable) and compact (minified)
formats. The compact format uses functional contracts to reduce token usage
while preserving all decision-enabling information.

Usage:
    from claude_skills.common.json_output import format_json_output, format_compact_output

    # Pretty-printed JSON (default)
    output = format_json_output(data)

    # Compact minified JSON
    output = format_json_output(data, compact=True)

    # Apply contract extraction and format as compact JSON
    output = format_compact_output(data, command_type='prepare-task')
"""

import json
from typing import Any, Dict, Optional, Literal
import logging

# Import contract extractors
from claude_skills.common.contracts import (
    extract_prepare_task_contract,
    extract_task_info_contract,
    extract_check_deps_contract,
    extract_progress_contract,
    extract_next_task_contract,
    extract_session_summary_contract
)

logger = logging.getLogger(__name__)

# Type alias for supported command types
CommandType = Literal['prepare-task', 'task-info', 'check-deps', 'progress', 'next-task', 'session-summary']


def format_json_output(
    data: Dict[str, Any],
    compact: bool = False,
    sort_keys: bool = False
) -> str:
    """
    Format data as JSON string with optional compact (minified) output.

    This is the central JSON formatting function used by all CLI commands.
    It provides consistent formatting behavior across the toolkit.

    Args:
        data: Dictionary data to format as JSON
        compact: If True, output minified JSON without whitespace.
                If False (default), output pretty-printed JSON with indentation.
        sort_keys: If True, sort dictionary keys in output. Default False.

    Returns:
        Formatted JSON string

    Examples:
        >>> data = {"task_id": "task-1-1", "title": "Example task"}

        >>> # Pretty-printed (default)
        >>> print(format_json_output(data))
        {
          "task_id": "task-1-1",
          "title": "Example task"
        }

        >>> # Compact minified
        >>> print(format_json_output(data, compact=True))
        {"task_id":"task-1-1","title":"Example task"}

    Notes:
        - Pretty format uses 2-space indentation for readability
        - Compact format uses minimal separators to reduce size
        - Both formats ensure valid JSON output
        - Non-ASCII characters are preserved (ensure_ascii=False)
    """
    if compact:
        # Minified output: no whitespace, minimal separators
        # separators=(',', ':') removes spaces after , and :
        return json.dumps(
            data,
            separators=(',', ':'),
            sort_keys=sort_keys,
            ensure_ascii=False
        )
    else:
        # Pretty-printed output: indented, human-readable
        return json.dumps(
            data,
            indent=2,
            sort_keys=sort_keys,
            ensure_ascii=False
        )


def format_compact_output(
    data: Dict[str, Any],
    command_type: CommandType
) -> str:
    """
    Apply contract extraction and format as compact JSON.

    This function combines contract extraction (to reduce data) with
    compact JSON formatting (to reduce whitespace), providing maximum
    token efficiency while preserving all decision-enabling information.

    The two-step process:
    1. Extract minimal contract based on command_type
    2. Format as minified JSON

    Args:
        data: Full command output data
        command_type: Type of command that generated the data.
                     Must be one of: 'prepare-task', 'task-info',
                     'check-deps', 'progress', 'next-task'

    Returns:
        Compact JSON string with minimal contract

    Raises:
        ValueError: If command_type is not recognized

    Examples:
        >>> full_output = {
        ...     "success": True,
        ...     "task_id": "task-1-1",
        ...     "task_data": {"title": "Example", "status": "pending"},
        ...     "dependencies": {"can_start": True, "blocked_by": []},
        ...     # ... many other fields
        ... }

        >>> # Apply contract extraction and compact formatting
        >>> output = format_compact_output(full_output, 'prepare-task')
        >>> print(output)
        {"task_id":"task-1-1","title":"Example","can_start":true,"blocked_by":[],...}

    Token Savings:
        Typical savings compared to pretty-printed full output:
        - prepare-task: 85-90%
        - task-info: 70-75%
        - check-deps: 80-85%
        - progress: 85-90%
        - next-task: 60-70%

    Notes:
        - Contract extraction is command-specific
        - See contracts.py for detailed field inclusion rules
        - All decision-enabling information is preserved
        - This is the recommended format for agent consumption
    """
    # Map command type to contract extractor function
    extractors = {
        'prepare-task': extract_prepare_task_contract,
        'task-info': extract_task_info_contract,
        'check-deps': extract_check_deps_contract,
        'progress': extract_progress_contract,
        'next-task': extract_next_task_contract,
        'session-summary': extract_session_summary_contract
    }

    # Validate command_type
    if command_type not in extractors:
        raise ValueError(
            f"Unknown command_type: {command_type}. "
            f"Must be one of: {', '.join(extractors.keys())}"
        )

    # Extract contract
    extractor = extractors[command_type]
    contract = extractor(data)

    # Format as compact JSON
    return format_json_output(contract, compact=True)


def output_json(data: Any, compact: bool = False) -> None:
    """
    Output JSON data with formatting based on compact flag.

    This is the standard output function used across SDD toolkit commands.
    Provides a simple, consistent interface for JSON output.

    Args:
        data: Data to serialize to JSON (must be JSON-serializable)
        compact: If True, output compact JSON; if False, pretty-print with indent (default: False)

    Returns:
        None (prints to stdout)

    Examples:
        >>> output_json({"status": "success", "count": 42})
        {
          "status": "success",
          "count": 42
        }

        >>> output_json({"status": "success"}, compact=True)
        {"status":"success"}

    Notes:
        - This function name matches the pattern used in sdd_update/cli.py
        - Internally delegates to format_json_output() for consistent formatting
        - Output goes to stdout for easy piping and redirection
    """
    output = format_json_output(data, compact=compact, sort_keys=False)
    print(output)


def print_json_output(
    data: Dict[str, Any],
    compact: bool = False,
    sort_keys: bool = False
) -> None:
    """
    Format and print JSON output to stdout.

    Convenience wrapper around format_json_output() that prints the result
    to stdout. Simplifies CLI command implementations by combining formatting
    and output in a single function call.

    Args:
        data: Dictionary data to format as JSON
        compact: If True, output minified JSON. If False (default), pretty-print.
        sort_keys: If True, sort dictionary keys in output. Default False.

    Returns:
        None (prints to stdout)

    Examples:
        >>> data = {"task_id": "task-1-1", "status": "pending"}

        >>> # Pretty-print to stdout
        >>> print_json_output(data)
        {
          "task_id": "task-1-1",
          "status": "pending"
        }

        >>> # Compact output to stdout
        >>> print_json_output(data, compact=True)
        {"task_id":"task-1-1","status":"pending"}

    Usage in CLI commands:
        Instead of:
            output = format_json_output(data, compact=args.compact)
            print(output)

        Use:
            print_json_output(data, compact=args.compact)

    Notes:
        - Output goes to stdout for easy piping and redirection
        - No trailing newline is added (print() adds it automatically)
        - For error messages, use stderr instead (logger.error, print to sys.stderr)
    """
    output = format_json_output(data, compact=compact, sort_keys=sort_keys)
    print(output)
