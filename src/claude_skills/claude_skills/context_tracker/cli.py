#!/usr/bin/env python3
"""
Context Tracker - Monitor Claude Code token and context usage.

Parses Claude Code transcript files to display real-time token usage metrics.
Uses a two-command session marker pattern to identify the current session's transcript.

Usage (Recommended):
  # Step 1: Generate and log a session marker
  sdd session-marker

  # Step 2: Check context using that marker (in a SEPARATE command)
  sdd context --session-marker <marker-from-step-1>

This two-command approach ensures the marker is written to the transcript before
attempting to locate it, enabling reliable session identification in concurrent
Claude Code sessions.
"""

import argparse
import json
import os
import re
import secrets
import sys
import time
from pathlib import Path

from claude_skills.cli.sdd.output_utils import (
    CONTEXT_ESSENTIAL,
    CONTEXT_STANDARD,
    prepare_output,
)
from claude_skills.common import PrettyPrinter
from claude_skills.common.json_output import output_json
from claude_skills.context_tracker.parser import parse_transcript


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


def find_transcript_by_specific_marker(
    cwd: Path, marker: str, max_retries: int = 10, verbosity_level=None
) -> str | None:
    """
    Search transcripts for a specific SESSION_MARKER to identify current session.

    This function searches all .jsonl transcript files in the project directory
    for a specific marker string. The transcript containing that exact marker
    is the current session's transcript.

    To handle race conditions where the marker may not be flushed to disk yet,
    this function will retry with exponential backoff if the marker is not found
    on the first attempt.

    Transcripts are searched in reverse chronological order (most recently modified
    first) to prioritize active sessions over historical ones.

    If the exact CWD-based transcript directory doesn't exist, this function will
    search parent directories as a fallback to handle cases where commands are run
    from subdirectories of the project root.

    Args:
        cwd: Current working directory (used to find project-specific transcripts)
        marker: Specific marker to search for (e.g., "SESSION_MARKER_abc12345")
        max_retries: Maximum number of retry attempts (default: 10)
        verbosity_level: Verbosity level to control output (optional)
    Returns:
        Path to transcript containing the marker, or None if not found
    """
    # Build list of candidate transcript directories to search
    # Start with the exact CWD, then try parent directories
    candidate_dirs = []

    # Claude Code stores transcripts in project-specific directories
    current_path = cwd.resolve()
    while True:
        project_dir_name = str(current_path).replace("/", "-").replace("_", "-")
        transcript_dir = Path.home() / ".claude" / "projects" / project_dir_name
        if transcript_dir.exists():
            candidate_dirs.append(transcript_dir)

        # Stop at root or after checking enough parents
        if current_path.parent == current_path or len(candidate_dirs) >= 5:
            break
        current_path = current_path.parent
    if not candidate_dirs:
        return None

    # Extended retry with exponential backoff, capped at 30 seconds total
    # Delays: 100ms, 200ms, 400ms, 800ms, 1.6s, 3.2s, 6.4s, 12.8s, ...
    delays = [min(0.1 * (2**i), 10.0) for i in range(max_retries)]
    for attempt in range(max_retries):
        current_time = time.time()

        # Search all candidate directories (prioritizing exact CWD match first)
        for transcript_dir in candidate_dirs:
            try:
                # Get all recent transcript files
                transcript_files = []
                for transcript_path in transcript_dir.glob("*.jsonl"):
                    try:
                        mtime = transcript_path.stat().st_mtime
                        # Only check recent transcripts (modified in last 24 hours)
                        if (current_time - mtime) > 86400:
                            continue
                        transcript_files.append((transcript_path, mtime))
                    except (OSError, IOError):
                        continue

                # Sort by modification time (most recent first)
                # This prioritizes the active session over historical transcripts
                transcript_files.sort(key=lambda x: x[1], reverse=True)

                # Search through transcripts in order of recency
                for transcript_path, _ in transcript_files:
                    try:
                        # Search for the specific marker in the transcript
                        with open(transcript_path, "r", encoding="utf-8") as f:
                            for line in f:
                                if marker in line:
                                    return str(transcript_path)
                    except (OSError, IOError, UnicodeDecodeError):
                        continue
            except (OSError, IOError):
                continue

        # If not found and we have retries left, wait before next attempt
        if attempt < max_retries - 1:
            # Show progress on stderr so it doesn't interfere with JSON output
            # Only show if not in quiet mode
            if (
                attempt > 0 and verbosity_level != VerbosityLevel.QUIET
            ):  # Don't show on first attempt or in quiet mode
                print(
                    f"Waiting for marker to be written to transcript... "
                    f"(attempt {attempt + 1}/{max_retries})",
                    file=sys.stderr,
                )
            time.sleep(delays[attempt])
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


def get_transcript_path(args, verbosity_level=None) -> str | None:
    """
    Get transcript path from multiple sources (priority order).

    Priority:
    1. Session marker discovery (if --session-marker provided)
    2. Explicit CLI argument (--transcript-path)
    3. Environment variable (CLAUDE_TRANSCRIPT_PATH)
    4. stdin JSON (hook mode)

    Args:
        args: Parsed CLI arguments
        verbosity_level: Verbosity level to control output (optional)
    Returns:
        Transcript path string, or None if not found
    """
    # Priority 1: Session marker discovery (recommended approach)
    # Search for transcripts containing the specific session marker
    if hasattr(args, "session_marker") and args.session_marker:
        cwd = Path.cwd()
        marker_path = find_transcript_by_specific_marker(
            cwd, args.session_marker, verbosity_level=verbosity_level
        )
        if marker_path:
            return marker_path

    # Priority 2: Explicit CLI argument
    if hasattr(args, "transcript_path") and args.transcript_path:
        return args.transcript_path

    # Priority 3: Environment variable
    env_path = os.environ.get("CLAUDE_TRANSCRIPT_PATH")
    if env_path:
        return env_path

    # Priority 4: stdin (hook mode)
    stdin_path = get_transcript_path_from_stdin()
    if stdin_path:
        return stdin_path

    return None


def format_number(n: int) -> str:
    """Format a number with thousands separators."""
    return f"{n:,}"


def format_metrics_human(
    metrics, max_context: int = 155000, transcript_path: str = None
):
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
    output.append(
        f"Context Used:    {format_number(metrics.context_length)} / {format_number(max_context)} tokens ({context_pct:.1f}%)"
    )
    output.append("")
    output.append("Session Totals:")
    output.append(f"  Input Tokens:    {format_number(metrics.input_tokens)}")
    output.append(f"  Output Tokens:   {format_number(metrics.output_tokens)}")
    output.append(f"  Cached Tokens:   {format_number(metrics.cached_tokens)}")
    output.append(f"  Total Tokens:    {format_number(metrics.total_tokens)}")
    output.append("=" * 60)
    return "\n".join(output)


def format_metrics_json(
    metrics,
    max_context: int = 155000,
    transcript_path: str = None,
    compact: bool = False,
):
    """
    Format and output token metrics as JSON.

    Args:
        metrics: TokenMetrics object
        max_context: Maximum context window size
        transcript_path: Optional path to transcript file (for metadata)
        compact: Whether to use compact JSON formatting (default: False)
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

    output_json(result, compact=compact)


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


from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.common.sdd_config import load_sdd_config


def cmd_context(args, printer):
    """
    Handler for 'sdd context' command.

    Args:
        args: Parsed arguments from ArgumentParser
        printer: PrettyPrinter instance for output
    """
    sdd_config = load_sdd_config()

    # Determine verbosity level early so we can use it in get_transcript_path
    args.verbosity_level = VerbosityLevel.from_args(args, sdd_config)

    # Apply config default for JSON output if not explicitly set
    # This ensures config settings are observed even if main CLI didn't apply them
    if not hasattr(args, 'json') or args.json is None:
        args.json = sdd_config.get('output', {}).get('default_mode') == 'json'

    transcript_path = get_transcript_path(args, args.verbosity_level)
    if not transcript_path:
        # Provide context-specific error message
        if hasattr(args, "session_marker") and args.session_marker:
            cwd = Path.cwd()

            # Build list of searched directories (same logic as find_transcript_by_specific_marker)
            searched_dirs = []
            current_path = cwd.resolve()
            while True:
                project_dir_name = str(current_path).replace("/", "-").replace("_", "-")
                transcript_dir = Path.home() / ".claude" / "projects" / project_dir_name
                if transcript_dir.exists():
                    searched_dirs.append(transcript_dir)
                if current_path.parent == current_path or len(searched_dirs) >= 5:
                    break
                current_path = current_path.parent
            printer.error(
                f"Could not find transcript containing marker: {args.session_marker}"
            )
            printer.error("")
            printer.error(
                "This usually means the marker hasn't been written to the transcript yet."
            )
            printer.error("")
            printer.error("Make sure you're using the two-command pattern:")
            printer.error(
                "  1. Call 'sdd session-marker' first (generates and logs marker)"
            )
            printer.error(
                "  2. Call 'sdd context --session-marker <marker>' in a SEPARATE command"
            )
            printer.error("")
            printer.error(
                "Important: 'SEPARATE command' means a separate conversation turn,"
            )
            printer.error(
                "not just separate bash commands. The marker must be logged to the"
            )
            printer.error("transcript file before it can be found.")
            printer.error("")

            if searched_dirs:
                printer.error(
                    f"Searched in {len(searched_dirs)} transcript director{'y' if len(searched_dirs) == 1 else 'ies'}:"
                )
                for dir_path in searched_dirs:
                    transcript_count = len(list(dir_path.glob("*.jsonl")))
                    printer.error(
                        f"  • {dir_path} ({transcript_count} transcript file(s))"
                    )
            else:
                printer.error("Warning: No transcript directories found")
            printer.error("")
            printer.error("Troubleshooting:")
            printer.error("  • Wait a few seconds after generating the marker")
            printer.error(
                "  • Ensure both commands run from the same working directory"
            )
            printer.error("  • If multiple sessions are active, use a fresh marker")
            printer.error("  • Try running 'sdd session-marker' again in a new message")
        else:
            printer.error("Error: No session marker provided.")
            printer.error("")
            printer.error("Usage: Use the two-command pattern to check context:")
            printer.error("")
            printer.error("  Step 1: Generate and log a session marker")
            printer.error("    sdd session-marker")
            printer.error("")
            printer.error(
                "  Step 2: Check context using that marker (in a SEPARATE command)"
            )
            printer.error("    sdd context --session-marker <marker-from-step-1>")
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
        # Build the full payload
        context_pct = (
            (metrics.context_length / args.max_context * 100)
            if args.max_context > 0
            else 0
        )
        payload = {
            "context_length": metrics.context_length,
            "context_percentage": round(context_pct, 2),
            "context_percentage_used": round(context_pct),
            "max_context": args.max_context,
            "input_tokens": metrics.input_tokens,
            "output_tokens": metrics.output_tokens,
            "cached_tokens": metrics.cached_tokens,
            "total_tokens": metrics.total_tokens,
        }

        if transcript_path:
            payload["transcript_path"] = transcript_path

        # Apply verbosity filtering
        filtered_output = prepare_output(
            payload, args, CONTEXT_ESSENTIAL, CONTEXT_STANDARD
        )

        # Determine compact setting
        use_compact = sdd_config.get("output", {}).get("json_compact", True)
        if hasattr(args, "compact") and args.compact is not None:
            use_compact = args.compact

        output_json(filtered_output, compact=use_compact)
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
        "session-marker",
        parents=[parent_parser],
        help="Generate a unique session marker for transcript identification",
        description="Outputs a unique marker that gets logged to the transcript, allowing the context command to identify the current session",
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
        "context",
        parents=[parent_parser],
        help="Monitor Claude Code token and context usage",
        description="Parse Claude Code transcript files to display real-time token usage metrics",
    )

    parser.add_argument(
        "--transcript-path",
        type=str,
        help="Path to the Claude Code transcript JSONL file",
    )

    parser.add_argument(
        "--session-marker",
        type=str,
        help="Session marker to search for (generated by session-marker command)",
    )

    parser.add_argument(
        "--max-context",
        type=int,
        default=155000,
        help="Maximum context window size (default: 155000)",
    )

    # Note: --json and --verbose are inherited from parent_parser global options
    # --verbose flag is used to control output verbosity:
    #   - Without --verbose: Simplified JSON output (just context_percentage_used)
    #   - With --verbose: Full JSON output (all metrics)

    parser.set_defaults(func=cmd_context)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Monitor Claude Code token and context usage",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage (Recommended):
  Use the two-command session marker pattern:

  Step 1: Generate and log a session marker
    sdd session-marker

  Step 2: Check context using that marker (in a SEPARATE command)
    sdd context --session-marker <marker-from-step-1>

  Get JSON output:
    sdd context --session-marker <marker> --json

This two-command approach ensures reliable session identification
when running multiple concurrent Claude Code sessions.
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
        default=155000,
        help="Maximum context window size (default: 155000)",
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
        print("\nError: No session marker provided.", file=sys.stderr)
        print("", file=sys.stderr)
        print("Usage: Use the two-command pattern to check context:", file=sys.stderr)
        print("", file=sys.stderr)
        print("  Step 1: Generate and log a session marker", file=sys.stderr)
        print("    sdd session-marker", file=sys.stderr)
        print("", file=sys.stderr)
        print(
            "  Step 2: Check context using that marker (in a SEPARATE command)",
            file=sys.stderr,
        )
        print("    sdd context --session-marker <marker-from-step-1>", file=sys.stderr)
        sys.exit(1)

    # Verify file exists
    if not Path(transcript_path).exists():
        print(f"Error: Transcript file not found: {transcript_path}", file=sys.stderr)
        sys.exit(1)

    # Parse the transcript
    metrics = parse_transcript(transcript_path)
    if metrics is None:
        print(
            f"Error: Could not parse transcript file: {transcript_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Output the metrics
    if args.json:
        # main() doesn't have --verbose flag, so always output essential fields only
        context_pct = (
            (metrics.context_length / args.max_context * 100)
            if args.max_context > 0
            else 0
        )
        payload = {"context_percentage_used": round(context_pct)}
        output_json(payload, compact=getattr(args, "compact", True))
    else:
        print(format_metrics_human(metrics, args.max_context, transcript_path))


if __name__ == "__main__":
    main()
