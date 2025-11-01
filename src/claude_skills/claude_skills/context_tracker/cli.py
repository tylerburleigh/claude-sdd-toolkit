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
from claude_skills.context_tracker.process_utils import (
    find_session_by_pid,
    is_pid_alive,
    get_parent_pids
)
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

    Uses multi-layered detection to identify which transcript belongs to the
    current Claude Code session, enabling correct session detection even with
    multiple concurrent sessions in the same directory.

    Detection Strategy (in order of priority):
    1. PID-based: Match current process tree to cached session PPIDs
    2. TTY-based: Match current terminal to cached session TTY
    3. Environment variable: Check CLAUDE_SESSION_ID
    4. File writing detection: Check which transcript is open for writing (lsof)
    5. Fallback: Most recently modified transcript (last resort)

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

        # Fast path: If only one session exists, validate and return it directly
        # This skips expensive lsof and multi-strategy detection
        if len(sessions) == 1:
            session_id, session_data = next(iter(sessions.items()))
            ppid = session_data.get("ppid")
            path = session_data.get("transcript_path")

            if path and Path(path).exists():
                # Validate session is still alive
                if ppid and is_pid_alive(ppid):
                    return path
                # Allow recently modified files without PPID (old cache format)
                import time
                if time.time() - Path(path).stat().st_mtime < 60:
                    return path

        # Strategy 1: PID-based detection (most reliable)
        session_id = find_session_by_pid(dir_entry)
        if session_id and session_id in sessions:
            transcript_path = sessions[session_id].get("transcript_path")
            if transcript_path and Path(transcript_path).exists():
                return transcript_path

        # Strategy 2: TTY-based detection (for multiple sessions in same directory)
        # This helps disambiguate when running from different terminals
        try:
            current_tty = os.ttyname(0)  # Get current terminal's TTY
            for session_id, session_data in sessions.items():
                cached_tty = session_data.get("tty")
                if cached_tty and cached_tty == current_tty:
                    transcript_path = session_data.get("transcript_path")
                    if transcript_path and Path(transcript_path).exists():
                        return transcript_path
        except (OSError, AttributeError):
            # Not running in a TTY, skip this strategy
            pass

        # Strategy 3: Environment variable detection
        env_session_id = os.environ.get("CLAUDE_SESSION_ID")
        if env_session_id and env_session_id in sessions:
            transcript_path = sessions[env_session_id].get("transcript_path")
            if transcript_path and Path(transcript_path).exists():
                return transcript_path

        # Strategy 4: File writing detection (existing lsof method)
        transcript_paths = [
            s.get("transcript_path")
            for s in sessions.values()
            if s.get("transcript_path")
        ]
        for path in transcript_paths:
            if is_file_open_for_writing(path):
                return path

        # Strategy 5: Fallback to most recently modified transcript
        # Only consider sessions with alive PIDs or recent timestamps
        valid_paths = []
        import time
        current_time = time.time()

        for session_id, session_data in sessions.items():
            path = session_data.get("transcript_path")
            if not path or not Path(path).exists():
                continue

            # Check if session is likely still active
            ppid = session_data.get("ppid")
            started_at = session_data.get("started_at", 0)

            # Consider session valid if:
            # 1. PID is still alive, OR
            # 2. Session started less than 24 hours ago (generous window)
            is_valid = (
                (ppid and is_pid_alive(ppid)) or
                (current_time - started_at < 86400)
            )

            if is_valid:
                valid_paths.append(path)

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


def _clean_stale_sessions(dir_entry):
    """
    Remove sessions with dead PIDs from the cache entry.

    Modifies dir_entry in place.

    Args:
        dir_entry: Directory entry from cache with 'sessions' dict
    """
    import time

    sessions = dir_entry.get("sessions", {})
    if not sessions:
        return

    current_time = time.time()
    stale_session_ids = []

    for session_id, session_data in sessions.items():
        ppid = session_data.get("ppid")
        started_at = session_data.get("started_at", 0)

        # Mark as stale if:
        # 1. Has PPID but it's dead, AND
        # 2. Session is older than 1 hour
        if ppid and not is_pid_alive(ppid):
            age = current_time - started_at
            if age > 3600:  # 1 hour
                stale_session_ids.append(session_id)

    # Remove stale sessions
    for session_id in stale_session_ids:
        del sessions[session_id]

    # Update most_recent if it was removed
    most_recent = dir_entry.get("most_recent")
    if most_recent in stale_session_ids and sessions:
        # Set most_recent to the session with highest timestamp
        dir_entry["most_recent"] = max(
            sessions.keys(),
            key=lambda sid: sessions[sid].get("timestamp", 0)
        )


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
