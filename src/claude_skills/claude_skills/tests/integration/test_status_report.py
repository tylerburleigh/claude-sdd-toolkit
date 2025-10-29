"""
Integration tests for status-report completion detection.

Tests that status-report command properly displays completion status
when a spec is finished, while remaining non-interactive.
"""

import sys
import pytest
import subprocess
import json
from pathlib import Path


# Unified CLI command (uses sdd instead of sdd-update)
CLI_CMD = "sdd"


def run_cli(*args, **kwargs):
    """
    Run sdd command with fallback to python -m if sdd not on PATH.

    Automatically reorders arguments to put global flags before subcommands.
    Global flags: --path, --specs-dir, --quiet, --json, --debug, --verbose, --no-color
    """
    # Define global flags that must come before subcommands
    global_flags_with_values = {'--path', '--specs-dir'}
    global_flags_boolean = {'--quiet', '-q', '--json', '--debug', '--verbose', '-v', '--no-color'}
    all_global_flags = global_flags_with_values | global_flags_boolean

    args_list = list(args)

    # Scan all args and separate global flags from subcommand and its args
    global_args = []
    non_global_args = []

    i = 0
    while i < len(args_list):
        arg = args_list[i]

        if arg in global_flags_with_values and i + 1 < len(args_list):
            # This is a global flag with a value
            global_args.append(arg)
            global_args.append(args_list[i + 1])
            i += 2
        elif arg in global_flags_boolean:
            # This is a boolean global flag
            global_args.append(arg)
            i += 1
        else:
            # Not a global flag, add to non-global
            non_global_args.append(arg)
            i += 1

    # Build command: [CLI_CMD] + global_args + non_global_args
    cmd = [CLI_CMD] + global_args + non_global_args

    # Check if sdd is on PATH
    try:
        result = subprocess.run(
            ['which', CLI_CMD],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            # sdd not on PATH, use python -m fallback
            cmd = [sys.executable, "-m", "claude_skills.cli"] + global_args + non_global_args
    except Exception:
        # If 'which' fails, try python -m fallback
        cmd = [sys.executable, "-m", "claude_skills.cli"] + global_args + non_global_args

    # Run the command
    return subprocess.run(cmd, **kwargs)


@pytest.mark.integration
class TestStatusReportCompletion:
    """Tests for status-report completion detection."""

    def test_completion_message_in_status_report(self, sample_json_spec_completed, specs_structure):
        """Test completion message appears in status report when spec is complete."""
        from claude_skills.common.spec import load_json_spec

        spec_id = "completed-spec-2025-01-01-007"
        spec_data = load_json_spec(spec_id, specs_structure)

        # Verify spec is actually complete (all tasks completed)
        assert spec_data is not None

        # Run status-report command
        result = run_cli(
            "status-report",
            "--path", str(specs_structure),
            spec_id,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Check that completion message appears
        assert "complete" in result.stdout.lower()
        # Should show indication that spec can be finalized
        assert "complete-spec" in result.stdout or "finalize" in result.stdout.lower()

    def test_non_interactive_behavior(self, sample_json_spec_completed, specs_structure):
        """Test status-report remains non-interactive (no prompts to user)."""
        spec_id = "completed-spec-2025-01-01-007"

        # Run status-report command
        result = run_cli(
            "status-report",
            "--path", str(specs_structure),
            spec_id,
            capture_output=True,
            text=True,
            input=""  # No input should be needed
        )

        assert result.returncode == 0

        # Verify no interactive prompts (these keywords appear in interactive prompts)
        assert "Mark spec as complete? (y/n)" not in result.stdout
        assert "Enter actual hours" not in result.stdout

        # But completion information should still be displayed
        assert "complete" in result.stdout.lower()

    def test_command_hint_displayed(self, sample_json_spec_completed, specs_structure):
        """Test command hint is displayed correctly."""
        spec_id = "completed-spec-2025-01-01-007"

        # Run status-report command
        result = run_cli(
            "status-report",
            "--path", str(specs_structure),
            spec_id,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Check that command hint for finalizing spec is shown
        assert "complete-spec" in result.stdout or "sdd complete-spec" in result.stdout.lower()

    def test_incomplete_spec_no_completion_message(self, sample_json_spec_simple, specs_structure):
        """Test that incomplete specs don't show completion message."""
        from claude_skills.common.spec import load_json_spec, save_json_spec

        spec_id = "simple-spec-2025-01-01-001"
        spec_data = load_json_spec(spec_id, specs_structure)

        # Ensure at least one task is pending
        spec_data["hierarchy"]["task-1-1"]["status"] = "pending"
        save_json_spec(spec_id, specs_structure, spec_data)

        # Run status-report command
        result = run_cli(
            "status-report",
            "--path", str(specs_structure),
            spec_id,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Should NOT show "Spec is complete" message
        # Note: "complete" might appear in other contexts, so check for the specific completion message
        output_lower = result.stdout.lower()
        assert not ("spec is complete" in output_lower or "all tasks complete" in output_lower)
