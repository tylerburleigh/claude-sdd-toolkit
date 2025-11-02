#!/usr/bin/env python3
"""
Context Tracker - Monitor Claude Code token and context usage.

Parses Claude Code transcript files to display real-time token usage metrics.
Adopts a stateless design inspired by ccstatusline - transcript path is provided
directly via CLI arg, environment variable, or stdin (hook mode).

Usage:
  # From CLI with explicit path
  sdd context --transcript-path /path/to/transcript.jsonl

  # From hook (reads stdin JSON)
  echo '{"transcript_path": "/path/to/transcript.jsonl"}' | sdd context

  # From environment variable
  export CLAUDE_TRANSCRIPT_PATH=/path/to/transcript.jsonl
  sdd context
"""

import argparse
import json
import os
import re
import secrets
import sys
import time
from pathlib import Path

from claude_skills.context_tracker.parser import parse_transcript
from claude_skills.common import PrettyPrinter


def generate_session_marker() -> str:
    """
    Generate a unique random session marker.

    Uses a short 8-character hex string for easier reproduction and lower
    chance of transcription errors.

    Returns:
        The generated marker string (e.g., "SESSION_MARKER_abc12345")
    """
    marker = f"SESSION_MARKER_{secrets.token_hex(4)}"
    return marker


def find_transcript_by_specific_marker(cwd: Path, marker: str) -> str | None:
    """
    Search transcripts for a specific SESSION_MARKER to identify current session.

    This function searches all .jsonl transcript files in the project directory
    for a specific marker string. The transcript containing that exact marker
    is the current session's transcript.

    Args:
        cwd: Current working directory (used to find project-specific transcripts)
        marker: Specific marker to search for (e.g., "SESSION_MARKER_abc12345")

    Returns:
        Path to transcript containing the marker, or None if not found
    """
    # Claude Code stores transcripts in project-specific directories
    project_dir_name = str(cwd.resolve()).replace("/", "-")
    transcript_dir = Path.home() / ".claude" / "projects" / project_dir_name

    if not transcript_dir.exists():
        return None

    current_time = time.time()

    try:
        for transcript_path in transcript_dir.glob("*.jsonl"):
            try:
                # Only check recent transcripts (modified in last 24 hours)
                mtime = transcript_path.stat().st_mtime
                if (current_time - mtime) > 86400:
                    continue

                # Search for the specific marker in the transcript
                with open(transcript_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if marker in line:
                            return str(transcript_path)
            except (OSError, IOError, UnicodeDecodeError):
                continue
    except (OSError, IOError):
        pass

    return None


def get_transcript_path_from_stdin() -> str | None:
    """
    Read transcript path from stdin JSON (hook mode).

    Expected JSON format:
    {
        "transcript_path": "/path/to/transcript.jsonl",
        "session_id": "...",
        "cwd": "...",
        ...
    }

    Returns:
        Transcript path from stdin, or None if stdin is a TTY or parsing fails
    """
    if sys.stdin.isatty():
        return None

    try:
        stdin_data = sys.stdin.read()
        if not stdin_data.strip():
            return None

        hook_data = json.loads(stdin_data)
        return hook_data.get("transcript_path")
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def get_transcript_path(args) -> str | None:
    """
    Get transcript path from multiple sources (priority order).

    Priority:
    1. Explicit CLI argument (--transcript-path)
    2. Environment variable (CLAUDE_TRANSCRIPT_PATH)
    3. stdin JSON (hook mode)
    4. Session marker discovery (if --session-marker provided)

    Args:
        args: Parsed CLI arguments

    Returns:
        Transcript path string, or None if not found
    """
    # Priority 1: Explicit CLI argument
    if hasattr(args, 'transcript_path') and args.transcript_path:
        return args.transcript_path

    # Priority 2: Environment variable
    env_path = os.environ.get("CLAUDE_TRANSCRIPT_PATH")
    if env_path:
        return env_path

    # Priority 3: stdin (hook mode)
    stdin_path = get_transcript_path_from_stdin()
    if stdin_path:
        return stdin_path

    # Priority 4: Session marker discovery
    # Search for transcripts containing the specific session marker
    if hasattr(args, 'session_marker') and args.session_marker:
        cwd = Path.cwd()
        marker_path = find_transcript_by_specific_marker(cwd, args.session_marker)
        if marker_path:
            return marker_path

    return None


def format_number(n: int) -> str:
    """Format a number with thousands separators."""
    return f"{n:,}"


def format_metrics_human(metrics, max_context: int = 160000, transcript_path: str = None):
    """
    Format token metrics for human-readable output.

    Args:
        metrics: TokenMetrics object
        max_context: Maximum context window size
        transcript_path: Optional path to transcript file (for display)
    """
    context_pct = (metrics.context_length / max_context * 100) if max_context > 0 else 0

    output = []
    output.append("=" * 60)
    output.append("Claude Code Context Usage")
    output.append("=" * 60)

    # Show transcript filename if available
    if transcript_path:
        transcript_name = Path(transcript_path).name
        output.append(f"\nTranscript: {transcript_name}")

    output.append("")
    output.append(f"Context Used:    {format_number(metrics.context_length)} / {format_number(max_context)} tokens ({context_pct:.1f}%)")
    output.append("")
    output.append("Session Totals:")
    output.append(f"  Input Tokens:    {format_number(metrics.input_tokens)}")
    output.append(f"  Output Tokens:   {format_number(metrics.output_tokens)}")
    output.append(f"  Cached Tokens:   {format_number(metrics.cached_tokens)}")
    output.append(f"  Total Tokens:    {format_number(metrics.total_tokens)}")
    output.append("=" * 60)

    return "\n".join(output)


def format_metrics_json(metrics, max_context: int = 160000, transcript_path: str = None):
    """
    Format token metrics as JSON.

    Args:
        metrics: TokenMetrics object
        max_context: Maximum context window size
        transcript_path: Optional path to transcript file (for metadata)
    """
    context_pct = (metrics.context_length / max_context * 100) if max_context > 0 else 0

    result = {
        "context_length": metrics.context_length,
        "context_percentage": round(context_pct, 2),
        "max_context": max_context,
        "input_tokens": metrics.input_tokens,
        "output_tokens": metrics.output_tokens,
        "cached_tokens": metrics.cached_tokens,
        "total_tokens": metrics.total_tokens,
    }

    if transcript_path:
        result["transcript_path"] = transcript_path

    return json.dumps(result, indent=2)


def cmd_session_marker(args, printer):
    """
    Handler for 'sdd session-marker' command.

    Generates and outputs a unique session marker that can be used
    to identify the current session's transcript.

    Args:
        args: Parsed arguments from ArgumentParser
        printer: PrettyPrinter instance for output
    """
    marker = generate_session_marker()
    # Output marker to stdout (not stderr) so it can be captured
    print(marker)


def cmd_context(args, printer):
    """
    Handler for 'sdd context' command.

    Args:
        args: Parsed arguments from ArgumentParser
        printer: PrettyPrinter instance for output
    """
    transcript_path = get_transcript_path(args)

    if not transcript_path:
        # Provide context-specific error message
        if hasattr(args, 'session_marker') and args.session_marker:
            printer.error(f"Could not find transcript containing marker: {args.session_marker}")
            printer.error("")
            printer.error("This usually means the marker hasn't been written to the transcript yet.")
            printer.error("If you're using the two-command approach, make sure to:")
            printer.error("  1. Call 'sdd session-marker' first (generates and logs marker)")
            printer.error("  2. Call 'sdd context --session-marker <marker>' in a SEPARATE command")
            printer.error("")
            printer.error("The marker must be logged to the transcript before it can be found.")
            printer.error("Try running 'sdd session-marker' again, then retry this command.")
        else:
            printer.error("No transcript path provided.")
            printer.error("")
            printer.error("Please provide transcript path via:")
            printer.error("  1. Session marker: sdd context --session-marker $(sdd session-marker)")
            printer.error("  2. CLI argument: sdd context --transcript-path /path/to/transcript.jsonl")
            printer.error("  3. Environment variable: export CLAUDE_TRANSCRIPT_PATH=/path/to/transcript.jsonl")
            printer.error("  4. stdin (hook mode): echo '{\"transcript_path\": \"...\"}' | sdd context")
        sys.exit(1)

    # Verify file exists
    if not Path(transcript_path).exists():
        printer.error(f"Transcript file not found: {transcript_path}")
        sys.exit(1)

    # Parse the transcript
    metrics = parse_transcript(transcript_path)

    if metrics is None:
        printer.error(f"Could not parse transcript file: {transcript_path}")
        sys.exit(1)

    # Output the metrics
    if args.json:
        print(format_metrics_json(metrics, args.max_context, transcript_path))
    else:
        print(format_metrics_human(metrics, args.max_context, transcript_path))


def register_session_marker(subparsers, parent_parser):
    """
    Register 'session-marker' subcommand for unified SDD CLI.

    Args:
        subparsers: ArgumentParser subparsers object
        parent_parser: Parent parser with global options
    """
    parser = subparsers.add_parser(
        'session-marker',
        parents=[parent_parser],
        help='Generate a unique session marker for transcript identification',
        description='Outputs a unique marker that gets logged to the transcript, allowing the context command to identify the current session'
    )

    parser.set_defaults(func=cmd_session_marker)


def register_context(subparsers, parent_parser):
    """
    Register 'context' subcommand for unified SDD CLI.

    Args:
        subparsers: ArgumentParser subparsers object
        parent_parser: Parent parser with global options
    """
    parser = subparsers.add_parser(
        'context',
        parents=[parent_parser],
        help='Monitor Claude Code token and context usage',
        description='Parse Claude Code transcript files to display real-time token usage metrics'
    )

    parser.add_argument(
        '--transcript-path',
        type=str,
        help='Path to the Claude Code transcript JSONL file'
    )

    parser.add_argument(
        '--session-marker',
        type=str,
        help='Session marker to search for (generated by session-marker command)'
    )

    parser.add_argument(
        '--max-context',
        type=int,
        default=160000,
        help='Maximum context window size (default: 160000)'
    )

    # Note: --json is inherited from parent_parser global options

    parser.set_defaults(func=cmd_context)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor Claude Code token and context usage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check context usage from transcript path
  sdd context --transcript-path /path/to/transcript.jsonl

  # Use environment variable
  export CLAUDE_TRANSCRIPT_PATH=/path/to/transcript.jsonl
  sdd context

  # Use as a Claude Code hook (reads from stdin)
  echo '{"transcript_path": "/path/to/transcript.jsonl"}' | sdd context

  # Get JSON output
  sdd context --transcript-path /path/to/transcript.jsonl --json
        """,
    )

    parser.add_argument(
        "--transcript-path",
        type=str,
        help="Path to the Claude Code transcript JSONL file",
    )

    parser.add_argument(
        "--max-context",
        type=int,
        default=160000,
        help="Maximum context window size (default: 160000)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output metrics in JSON format",
    )

    args = parser.parse_args()

    # Get transcript path from args, env var, or stdin
    transcript_path = get_transcript_path(args)

    if not transcript_path:
        parser.print_help()
        print("\nError: No transcript path provided", file=sys.stderr)
        print("", file=sys.stderr)
        print("Provide via:", file=sys.stderr)
        print("  --transcript-path argument", file=sys.stderr)
        print("  CLAUDE_TRANSCRIPT_PATH environment variable", file=sys.stderr)
        print("  stdin JSON (hook mode)", file=sys.stderr)
        sys.exit(1)

    # Verify file exists
    if not Path(transcript_path).exists():
        print(f"Error: Transcript file not found: {transcript_path}", file=sys.stderr)
        sys.exit(1)

    # Parse the transcript
    metrics = parse_transcript(transcript_path)

    if metrics is None:
        print(f"Error: Could not parse transcript file: {transcript_path}", file=sys.stderr)
        sys.exit(1)

    # Output the metrics
    if args.json:
        print(format_metrics_json(metrics, args.max_context, transcript_path))
    else:
        print(format_metrics_human(metrics, args.max_context, transcript_path))


if __name__ == "__main__":
    main()
