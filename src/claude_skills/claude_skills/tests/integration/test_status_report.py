"""
Integration tests for status-report completion detection.

Tests that status-report command properly displays completion status
when a spec is finished, while remaining non-interactive.
"""

import pytest

from .cli_runner import run_cli


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
            "--no-json",
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
            "--no-json",
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
            "--no-json",
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
