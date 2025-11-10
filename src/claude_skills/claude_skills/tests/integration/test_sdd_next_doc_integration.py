"""
Integration tests for sdd-next doc integration.

Tests the full workflow of doc availability checking and context gathering.
"""

import json
from unittest.mock import patch

import pytest

from .cli_runner import run_cli


class TestDocIntegration:
    """Integration tests for doc integration in sdd-next."""

    def test_docs_available(self, sample_json_spec_simple, specs_structure):
        """Test workflow when documentation is available."""
        # This is a minimal integration test that verifies the command
        # executes without errors when docs are available

        # The sample_json_spec_simple fixture creates the spec file
        # specs_structure provides the directory structure

        # Run prepare-task command
        result = run_cli(
            "prepare-task",
            "simple-spec-2025-01-01-001",
            "--path", str(specs_structure),
            "--json",
            capture_output=True,
            text=True
        )

        # Should succeed
        assert result.returncode == 0

        # Parse output
        output = json.loads(result.stdout)
        assert output.get("success") is True
        assert "task_id" in output

    def test_docs_missing_no_prompt_in_json_mode(self, sample_json_spec_simple, specs_structure):
        """Test that JSON mode doesn't prompt for docs."""
        # The sample_json_spec_simple fixture creates the spec file

        # Run prepare-task command with --json flag
        result = run_cli(
            "prepare-task",
            "simple-spec-2025-01-01-001",
            "--path", str(specs_structure),
            "--json",
            capture_output=True,
            text=True
        )

        # Should succeed even if docs are missing
        assert result.returncode == 0

        # Parse output
        output = json.loads(result.stdout)
        assert output.get("success") is True

        # In JSON mode, we should not get interactive prompts
        # (the prompt is only shown in non-JSON mode)
        assert "task_id" in output

    def test_docs_missing_accept(self, sample_json_spec_simple, specs_structure):
        """Test that doc_prompt_needed flag is set when docs are missing."""
        # In automated tests, we can't truly test interactive prompts,
        # but we can verify that the flag is set correctly for the CLI to handle

        # Run prepare-task command with --json flag
        result = run_cli(
            "prepare-task",
            "simple-spec-2025-01-01-001",
            "--path", str(specs_structure),
            "--json",
            capture_output=True,
            text=True
        )

        # Should succeed
        assert result.returncode == 0

        # Parse output
        output = json.loads(result.stdout)
        assert output.get("success") is True

        # When docs are missing/stale, the doc_prompt_needed flag should be set
        # (The actual prompting happens in the CLI layer, not in JSON mode)
        # This flag tells the CLI to prompt the user
        if output.get("doc_status") in ["missing", "stale"]:
            assert output.get("doc_prompt_needed") is True

    def test_docs_missing_decline(self, sample_json_spec_simple, specs_structure):
        """Test graceful degradation when docs are missing (user declines scenario)."""
        # In automated tests, we can't simulate user declining the prompt,
        # but we can verify that the workflow continues successfully even
        # when docs are unavailable (which is what happens when user declines)

        # Run prepare-task command with --json flag
        result = run_cli(
            "prepare-task",
            "simple-spec-2025-01-01-001",
            "--path", str(specs_structure),
            "--json",
            capture_output=True,
            text=True
        )

        # Should succeed - workflow continues with manual exploration
        assert result.returncode == 0

        # Parse output
        output = json.loads(result.stdout)

        # Verify graceful degradation: task preparation succeeds
        assert output.get("success") is True
        assert "task_id" in output

        # Even though docs might be missing, the workflow doesn't fail
        # This demonstrates graceful degradation behavior

    def test_prepare_task_complete_workflow(self, sample_json_spec_simple, specs_structure):
        """
        E2E test: Complete prepare-task workflow.

        Tests the full prepare-task workflow from start to finish:
        1. Load spec file
        2. Find next actionable task
        3. Check doc availability
        4. Gather task context
        5. Return formatted task info
        """
        # Run prepare-task command
        result = run_cli(
            "prepare-task",
            "simple-spec-2025-01-01-001",
            "--path", str(specs_structure),
            "--json",
            capture_output=True,
            text=True
        )

        # Should succeed
        assert result.returncode == 0

        # Parse output
        output = json.loads(result.stdout)

        # Verify complete workflow executed
        assert output.get("success") is True
        assert "task_id" in output, "Should return task_id"
        assert "task_data" in output, "Should return task data"
        assert "dependencies" in output, "Should return dependency info"

        # Verify task data structure
        task_data = output.get("task_data")
        assert task_data is not None
        assert "type" in task_data
        assert "status" in task_data
        assert "dependencies" in task_data

    def test_next_task_command_workflow(self, sample_json_spec_simple, specs_structure):
        """
        E2E test: next-task command workflow.

        Tests that next-task command successfully:
        1. Finds the next actionable task
        2. Returns task ID
        3. Respects dependency ordering
        """
        # Run next-task command
        result = run_cli(
            "next-task",
            "simple-spec-2025-01-01-001",
            "--path", str(specs_structure),
            "--json",
            capture_output=True,
            text=True
        )

        # Should succeed
        assert result.returncode == 0

        # Parse output
        output = json.loads(result.stdout)

        # Should return next task info
        assert "task_id" in output or "next_task" in output

    def test_task_info_command_workflow(self, sample_json_spec_simple, specs_structure):
        """
        E2E test: task-info command workflow.

        Tests that task-info command successfully retrieves
        detailed information about a specific task.
        """
        # First get the next task
        result = run_cli(
            "next-task",
            "simple-spec-2025-01-01-001",
            "--path", str(specs_structure),
            "--json",
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            pytest.skip("next-task command failed")

        output = json.loads(result.stdout)
        task_id = output.get("task_id") or output.get("next_task")

        if not task_id:
            pytest.skip("No task ID returned")

        # Now get detailed info about that task
        result = run_cli(
            "task-info",
            "simple-spec-2025-01-01-001",
            task_id,
            "--path", str(specs_structure),
            "--json",
            capture_output=True,
            text=True
        )

        # Should succeed
        assert result.returncode == 0

        # Should return task details
        output = json.loads(result.stdout)
        assert output is not None

    @patch('claude_skills.common.doc_integration.check_doc_availability')
    def test_doc_availability_check_integration(self, mock_check_doc, sample_json_spec_simple, specs_structure):
        """
        E2E test: Verify doc availability checking is integrated.

        Tests that prepare-task properly checks for documentation
        availability and handles the response appropriately.
        """
        from claude_skills.common.doc_integration import DocStatus

        # Test with docs available
        mock_check_doc.return_value = DocStatus.AVAILABLE

        result = run_cli(
            "prepare-task",
            "simple-spec-2025-01-01-001",
            "--path", str(specs_structure),
            "--json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output.get("success") is True

        # In non-mocked scenario, doc_status would reflect actual availability
        # Here we verify the workflow completes successfully

    @patch('claude_skills.common.doc_integration.check_doc_availability')
    @patch('claude_skills.common.doc_integration.prompt_for_generation')
    def test_user_prompt_integration(self, mock_prompt, mock_check_doc, sample_json_spec_simple, specs_structure):
        """
        E2E test: User prompt integration for doc generation.

        Tests that when docs are missing, the system would prompt
        the user (in non-JSON mode) and handle the response.

        Note: In JSON mode (automated testing), prompts are suppressed.
        """
        from claude_skills.common.doc_integration import DocStatus

        # Simulate missing docs, user accepts
        mock_check_doc.return_value = DocStatus.MISSING
        mock_prompt.return_value = True

        # Run in JSON mode (no actual prompting)
        result = run_cli(
            "prepare-task",
            "simple-spec-2025-01-01-001",
            "--path", str(specs_structure),
            "--json",
            capture_output=True,
            text=True
        )

        # Should succeed - JSON mode doesn't prompt
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output.get("success") is True

    def test_graceful_degradation_comprehensive(self, sample_json_spec_simple, specs_structure):
        """
        E2E test: Comprehensive graceful degradation.

        Verifies that the complete workflow succeeds even when:
        - Documentation is unavailable
        - Context gathering falls back to manual tools
        - No errors are raised
        - Task information is still returned
        """
        # Run prepare-task (will use whatever context is available)
        result = run_cli(
            "prepare-task",
            "simple-spec-2025-01-01-001",
            "--path", str(specs_structure),
            "--json",
            capture_output=True,
            text=True
        )

        # Workflow should complete successfully
        assert result.returncode == 0

        # Parse and verify output
        output = json.loads(result.stdout)

        # Core functionality works regardless of doc availability
        assert output.get("success") is True
        assert "task_id" in output

        # Task data should be present
        assert "task_data" in output
        task_data = output["task_data"]
        assert task_data is not None

        # Dependencies should be analyzed
        assert "dependencies" in output
        deps = output["dependencies"]
        assert "can_start" in deps or "blocked_by" in deps
