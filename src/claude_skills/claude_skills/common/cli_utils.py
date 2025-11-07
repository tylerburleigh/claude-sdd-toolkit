"""
CLI Utilities - Shared utilities for command-line interface operations.

Provides helper functions for JSON output formatting, ANSI code stripping,
and other common CLI operations.
"""

import argparse
import json
import re
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Sequence, Union


def strip_ansi_codes(text: str) -> str:
    """
    Remove ANSI escape codes from text.

    ANSI codes are used for terminal coloring and formatting (e.g., from Rich library).
    This function strips them to produce clean text suitable for JSON output.

    Args:
        text: Text potentially containing ANSI escape sequences

    Returns:
        Text with all ANSI codes removed

    Example:
        >>> strip_ansi_codes("\\x1b[31mRed text\\x1b[0m")
        'Red text'
        >>> strip_ansi_codes("[bold]Text[/bold]")  # Rich markup
        '[bold]Text[/bold]'  # Rich markup is not ANSI codes
    """
    # ANSI escape sequences pattern
    # Matches ESC [ followed by any number of parameter bytes and a final byte
    ansi_pattern = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
    return ansi_pattern.sub('', text)


def format_json_output(
    data: Union[Dict[str, Any], List[Any]],
    compact: bool = False,
    strip_ansi: bool = True
) -> str:
    """
    Format data as JSON output with optional ANSI code stripping.

    This helper ensures consistent JSON output across CLI commands by:
    1. Stripping ANSI escape codes from string values (if enabled)
    2. Providing compact or pretty-printed formatting
    3. Handling nested dictionaries and lists recursively

    Args:
        data: Dictionary or list to convert to JSON
        compact: If True, use compact formatting (no indentation)
                If False, use pretty-printed formatting (2-space indentation)
        strip_ansi: If True, strip ANSI codes from all string values

    Returns:
        JSON-formatted string

    Example:
        >>> data = {"status": "\\x1b[32mcompleted\\x1b[0m", "count": 5}
        >>> format_json_output(data, compact=False, strip_ansi=True)
        '{\\n  "status": "completed",\\n  "count": 5\\n}'
    """
    if strip_ansi:
        data = _strip_ansi_recursive(data)

    if compact:
        return json.dumps(data, separators=(',', ':'))
    else:
        return json.dumps(data, indent=2)


def _strip_ansi_recursive(obj: Any) -> Any:
    """
    Recursively strip ANSI codes from all string values in an object.

    Handles dictionaries, lists, and nested structures. Non-string values
    are returned unchanged.

    Args:
        obj: Object to process (dict, list, str, or primitive)

    Returns:
        Object with ANSI codes stripped from all strings
    """
    if isinstance(obj, dict):
        return {key: _strip_ansi_recursive(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_strip_ansi_recursive(item) for item in obj]
    elif isinstance(obj, str):
        return strip_ansi_codes(obj)
    else:
        # Return primitives (int, float, bool, None) unchanged
        return obj


def add_format_flag(
    parser: argparse.ArgumentParser,
    choices: Optional[Sequence[str]] = None,
    default: str = 'text',
    help_text: Optional[str] = None
) -> argparse.ArgumentParser:
    """
    Add a consistent --format flag to an argparse parser.

    This utility function provides a standardized way to add output format options
    to CLI commands, reducing code duplication across different command implementations.

    Args:
        parser: The argparse ArgumentParser or subparser to modify
        choices: Valid format options (default: ['text', 'json'])
        default: Default format value (default: 'text')
        help_text: Custom help text (default: auto-generated from choices)

    Returns:
        The modified parser (for chaining)

    Example:
        >>> parser = argparse.ArgumentParser()
        >>> add_format_flag(parser, choices=['json', 'table'], default='table')
        <ArgumentParser ...>

        >>> # With subparsers
        >>> subparsers = parser.add_subparsers()
        >>> cmd_parser = subparsers.add_parser('stats')
        >>> add_format_flag(cmd_parser, choices=['text', 'json', 'markdown'])
        <ArgumentParser ...>

    Raises:
        ValueError: If default is not in choices
    """
    if choices is None:
        choices = ['text', 'json']

    # Validate default is in choices
    if default not in choices:
        raise ValueError(
            f"Default format '{default}' must be one of {list(choices)}"
        )

    # Generate help text if not provided
    if help_text is None:
        choices_str = ', '.join(choices)
        help_text = f'Output format: {choices_str} (default: {default})'

    # Add the --format argument
    parser.add_argument(
        '--format',
        choices=list(choices),
        default=default,
        help=help_text
    )

    return parser
