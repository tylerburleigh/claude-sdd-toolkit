#!/usr/bin/env python3
"""
Context Tracker - Monitor Claude Code token and context usage.

Parses Claude Code transcript files to display real-time token usage metrics.
Can be used as a standalone command or configured as a Claude Code hook.
"""

import argparse
import json
import sys
from pathlib import Path

from claude_skills.context_tracker.parser import parse_transcript
from claude_skills.common import PrettyPrinter


def is_file_open_for_writing(filepath):
    """
    Check if a file is currently open for writing by any process.

    Uses platform-specific tools:
    - Linux/macOS: lsof
    - Windows: fallback to modification time check

    Returns:
        True if file is open for writing, False otherwise
    """
    import subprocess
    import platform

    if not Path(filepath).exists():
        return False

    system = platform.system()

    try:
        if system in ("Linux", "Darwin"):  # Darwin = macOS
            # Use lsof to check if file is open
            # lsof returns 0 if file is open, 1 if not
            result = subprocess.run(
                ["lsof", str(filepath)],
                capture_output=True,
                timeout=2
            )
            # If lsof finds the file open (exit code 0), check if it's for writing
            if result.returncode == 0:
                output = result.stdout.decode()
                # lsof shows file descriptor + mode like "3w", "4u", "5W"
                # Look for write mode indicators in the FD column
                # Modes: w=write, u=read+write, W=write with lock
                for line in output.split('\n'):
                    # Skip header line
                    if 'COMMAND' in line or not line.strip():
                        continue
                    # FD column is typically the 4th column
                    parts = line.split()
                    if len(parts) >= 4:
                        fd_mode = parts[3]  # File descriptor + mode
                        # Check if it ends with write indicators
                        if fd_mode.endswith(('w', 'u', 'W')):
                            return True
                return False
        elif system == "Windows":
            # Windows: try using handle.exe or fall back to modification time
            # For now, fall back to modification time check
            import time
            mtime = Path(filepath).stat().st_mtime
            # If modified in last 5 seconds, consider it active
            return (time.time() - mtime) < 5
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
        pass

    return False


def get_cached_transcript_path():
    """
    Load transcript path from cache for current working directory.

    Uses open file detection to identify which transcript is actively being
    written to, enabling correct session detection even with multiple concurrent
    Claude Code sessions in the same directory.

    Strategy:
    1. Load all cached transcript paths for this directory
    2. Check which one is currently open for writing (using lsof)
    3. Return the actively-written transcript
    4. Fallback to most recently modified if detection fails

    Returns:
        Cached transcript path or None if not found
    """
    import os

    cache_dir = Path.home() / ".config" / "claude-sdd-toolkit"
    cache_file = cache_dir / "transcript-cache.json"

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, "r") as f:
            cache = json.load(f)

        cwd = os.getcwd()
        dir_entry = cache.get(cwd)

        if not dir_entry:
            return None

        # Check if this is old format (direct transcript_path)
        if "transcript_path" in dir_entry:
            return dir_entry["transcript_path"]

        # New multi-session format
        sessions = dir_entry.get("sessions", {})
        if not sessions:
            return None

        # Collect all transcript paths
        transcript_paths = [
            s.get("transcript_path")
            for s in sessions.values()
            if s.get("transcript_path")
        ]

        # Find which transcript is actively being written to
        for path in transcript_paths:
            if is_file_open_for_writing(path):
                return path

        # Fallback: use most recently modified transcript file
        valid_paths = [p for p in transcript_paths if Path(p).exists()]
        if valid_paths:
            most_recent_file = max(
                valid_paths,
                key=lambda p: Path(p).stat().st_mtime,
                default=None
            )
            if most_recent_file:
                return most_recent_file

    except (json.JSONDecodeError, IOError, ValueError, OSError):
        pass

    return None


def format_number(n: int) -> str:
    """Format a number with thousands separators."""
    return f"{n:,}"


def format_metrics_human(metrics, max_context: int = 160000):
    """Format token metrics for human-readable output."""
    context_pct = (metrics.context_length / max_context * 100) if max_context > 0 else 0

    output = []
    output.append("=" * 60)
    output.append("Claude Code Context Usage")
    output.append("=" * 60)
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


def format_metrics_json(metrics, max_context: int = 160000):
    """Format token metrics as JSON."""
    context_pct = (metrics.context_length / max_context * 100) if max_context > 0 else 0

    return json.dumps(
        {
            "context_length": metrics.context_length,
            "context_percentage": round(context_pct, 2),
            "context_percentage_interpretation": "Percentage of available context used",
            "max_context": max_context,
            "input_tokens": metrics.input_tokens,
            "output_tokens": metrics.output_tokens,
            "cached_tokens": metrics.cached_tokens,
            "total_tokens": metrics.total_tokens,
        },
        indent=2,
    )


def cmd_context(args, printer):
    """
    Handler for 'sdd context' command.

    Args:
        args: Parsed arguments from ArgumentParser
        printer: PrettyPrinter instance for output
    """
    transcript_path = args.transcript_path

    # If explicit path provided, use it
    if not transcript_path:
        # Otherwise, auto-discover from cache
        transcript_path = get_cached_transcript_path()

    if not transcript_path:
        printer.error("No transcript found for this session.")
        printer.error("")
        printer.error("The SessionStart hook caches transcript paths automatically.")
        printer.error("If this is a new session, the hook may not have run yet.")
        printer.error("")
        printer.error("To specify a transcript manually, use:")
        printer.error("  sdd context --transcript-path /path/to/transcript.jsonl")
        sys.exit(1)

    # Parse the transcript
    metrics = parse_transcript(transcript_path)

    if metrics is None:
        printer.error(f"Could not parse transcript file: {transcript_path}")
        sys.exit(1)

    # Output the metrics
    if args.json:
        print(format_metrics_json(metrics, args.max_context))
    else:
        print(format_metrics_human(metrics, args.max_context))


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
  sdd:context --transcript-path /path/to/transcript.jsonl

  # Use as a Claude Code hook (reads from stdin)
  echo '{"transcript_path": "/path/to/transcript.jsonl"}' | sdd:context

  # Get JSON output
  sdd:context --transcript-path /path/to/transcript.jsonl --json
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

    transcript_path = args.transcript_path

    # If no transcript path provided, try reading from stdin (hook mode)
    if not transcript_path:
        if not sys.stdin.isatty():
            try:
                stdin_data = sys.stdin.read()
                hook_data = json.loads(stdin_data)
                transcript_path = hook_data.get("transcript_path")
            except (json.JSONDecodeError, KeyError):
                print("Error: Could not parse hook data from stdin", file=sys.stderr)
                sys.exit(1)

    if not transcript_path:
        parser.print_help()
        print("\nError: No transcript path provided", file=sys.stderr)
        sys.exit(1)

    # Parse the transcript
    metrics = parse_transcript(transcript_path)

    if metrics is None:
        print(f"Error: Could not parse transcript file: {transcript_path}", file=sys.stderr)
        sys.exit(1)

    # Output the metrics
    if args.json:
        print(format_metrics_json(metrics, args.max_context))
    else:
        print(format_metrics_human(metrics, args.max_context))


if __name__ == "__main__":
    main()
