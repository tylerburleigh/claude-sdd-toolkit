"""
Integration tests for sdd_update_tools.py CLI.

Tests all query CLI commands with various arguments, JSON output, and error handling.

Note: Tests updated to use unified CLI (sdd update) instead of legacy sdd-update.
"""

import json

import pytest

from .cli_runner import run_cli


@pytest.mark.integration
class TestCLIBasics:
    """Basic CLI functionality tests."""

    def test_cli_help(self):
        """Test CLI shows help."""
        result = run_cli("--help",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "usage" in result.stdout.lower() or "SDD Update" in result.stdout

    def test_cli_shows_new_commands(self):
        """Test that new query commands appear in help."""
        result = run_cli("--help",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "query-tasks" in result.stdout
        assert "get-task" in result.stdout
        assert "list-phases" in result.stdout
        assert "check-complete" in result.stdout
        assert "phase-time" in result.stdout
        assert "list-blockers" in result.stdout


@pytest.mark.integration
class TestQueryTasksCLI:
    """Tests for query-tasks command."""

    def test_query_tasks_basic(self, sample_json_spec_simple, specs_structure):
        """Test basic query-tasks command."""
        result = run_cli(
             "query-tasks",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "task" in result.stdout.lower()

    def test_query_tasks_status_filter(self, sample_json_spec_with_blockers, specs_structure):
        """Test query-tasks with --status filter."""
        result = run_cli(
             "query-tasks",
             "--path", str(specs_structure),
             "blocked-spec-2025-01-01-005",
             "--status", "blocked",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "task-1-2" in result.stdout or "task-2-1" in result.stdout

    def test_query_tasks_type_filter(self, sample_json_spec_simple, specs_structure):
        """Test query-tasks with --type filter."""
        result = run_cli( "query-tasks",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
             "--type", "phase",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "phase" in result.stdout.lower()

    def test_query_tasks_format_simple(self, sample_json_spec_simple, specs_structure):
        """Test query-tasks with --format simple."""
        result = run_cli( "query-tasks",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
             "--simple",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Simple format should just list IDs
        assert "task-1-1" in result.stdout or "task" in result.stdout

    def test_query_tasks_json_output(self, sample_json_spec_simple, specs_structure):
        """Test query-tasks with --json flag."""
        result = run_cli(
             "--json",
             "query-tasks",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should be valid JSON
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, list)
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_query_tasks_compact_and_pretty_output(self, sample_json_spec_simple, specs_structure):
        """Test query-tasks with compact vs pretty JSON flags."""
        compact_result = run_cli(
             "--json", "--compact",
             "query-tasks",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
            capture_output=True,
            text=True
        )
        assert compact_result.returncode == 0
        assert len(compact_result.stdout.strip().splitlines()) == 1
        compact_data = json.loads(compact_result.stdout)
        assert isinstance(compact_data, list)
        assert any(item["id"] == "task-1-1" for item in compact_data)

        pretty_result = run_cli(
             "--json", "--no-compact",
             "query-tasks",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
            capture_output=True,
            text=True
        )
        assert pretty_result.returncode == 0
        assert len(pretty_result.stdout.strip().splitlines()) > 1
        assert json.loads(pretty_result.stdout) == compact_data

    def test_query_tasks_invalid_spec(self, specs_structure):
        """Test query-tasks with invalid spec_id."""
        result = run_cli( "query-tasks",
             "--path", str(specs_structure),
             "nonexistent-spec",
            capture_output=True,
            text=True
        )

        assert result.returncode == 1  # Should fail


@pytest.mark.integration
class TestGetTaskCLI:
    """Tests for get-task command."""

    def test_get_task_basic(self, sample_json_spec_simple, specs_structure):
        """Test basic get-task command."""
        result = run_cli(
             "get-task",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
             "task-1-1",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "task-1-1" in result.stdout
        assert "Task" in result.stdout or "task" in result.stdout

    def test_get_task_json(self, sample_json_spec_simple, specs_structure):
        """Test get-task with --json output."""
        result = run_cli( "get-task",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
             "task-1-1",
             "--json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should be valid JSON
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, dict)
            assert data["id"] == "task-1-1"
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_get_task_nonexistent(self, sample_json_spec_simple, specs_structure):
        """Test get-task with nonexistent task."""
        result = run_cli(
             "get-task",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
             "nonexistent-task",
            capture_output=True,
            text=True
        )

        assert result.returncode == 1  # Should fail


@pytest.mark.integration
class TestListPhasesCLI:
    """Tests for list-phases command."""

    def test_list_phases_basic(self, sample_json_spec_simple, specs_structure):
        """Test basic list-phases command."""
        result = run_cli(
             "list-phases",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "phase" in result.stdout.lower()

    def test_list_phases_json(self, sample_json_spec_simple, specs_structure):
        """Test list-phases with --json output."""
        result = run_cli( "list-phases",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
             "--json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should be valid JSON
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, list)
            assert len(data) >= 1
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_list_phases_compact_and_pretty(self, sample_json_spec_simple, specs_structure):
        """Ensure list-phases obeys compact flags."""
        compact_result = run_cli(
             "list-phases",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
             "--json", "--compact",
            capture_output=True,
            text=True
        )
        assert compact_result.returncode == 0
        compact_lines = compact_result.stdout.strip().splitlines()
        assert len(compact_lines) == 1
        compact_data = json.loads(compact_result.stdout)
        assert isinstance(compact_data, list)

        pretty_result = run_cli(
             "list-phases",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
             "--json", "--no-compact",
            capture_output=True,
            text=True
        )
        assert pretty_result.returncode == 0
        assert len(pretty_result.stdout.strip().splitlines()) > 1
        assert json.loads(pretty_result.stdout) == compact_data

    def test_list_phases_help(self):
        """Test list-phases help output."""
        result = run_cli("list-phases", "--help",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "spec_id" in result.stdout.lower()


@pytest.mark.integration
class TestCheckCompleteCLI:
    """Tests for check-complete command."""

    def test_check_complete_spec(self, sample_json_spec_simple, specs_structure):
        """Test check-complete for entire spec."""
        result = run_cli(
             "check-complete",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
            capture_output=True,
            text=True
        )

        # Should run (exit code depends on completion status)
        assert result.returncode in [0, 1]

    def test_check_complete_phase(self, sample_json_spec_with_time, specs_structure):
        """Test check-complete with --phase flag."""
        result = run_cli(
             "check-complete",
             "--path", str(specs_structure),
             "time-spec-2025-01-01-006",
             "--phase", "phase-1",
            capture_output=True,
            text=True
        )

        # Phase-1 should be complete in time-spec
        assert result.returncode == 0

    def test_check_complete_json(self, sample_json_spec_completed, specs_structure):
        """Test check-complete with --json output."""
        result = run_cli( "check-complete",
             "--path", str(specs_structure),
             "completed-spec-2025-01-01-007",
             "--json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should be valid JSON
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, dict)
            assert "is_complete" in data
            assert data["is_complete"] is True
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_check_complete_exit_code(self, sample_json_spec_completed, sample_json_spec_simple, specs_structure):
        """Test check-complete exit codes."""
        # Completed spec should return 0
        result_complete = run_cli(
             "check-complete",
             "--path", str(specs_structure),
             "completed-spec-2025-01-01-007",
            capture_output=True,
            text=True
        )
        assert result_complete.returncode == 0

        # Incomplete spec should return 1
        result_incomplete = run_cli(
             "check-complete",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
            capture_output=True,
            text=True
        )
        assert result_incomplete.returncode == 1


@pytest.mark.integration
class TestPhaseTimeCLI:
    """Tests for phase-time command."""

    def test_phase_time_basic(self, sample_json_spec_with_time, specs_structure):
        """Test basic phase-time command."""
        result = run_cli(
             "phase-time",
             "--path", str(specs_structure),
             "time-spec-2025-01-01-006",
             "phase-1",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "hour" in result.stdout.lower() or "time" in result.stdout.lower()

    def test_phase_time_json(self, sample_json_spec_with_time, specs_structure):
        """Test phase-time with --json output."""
        result = run_cli( "phase-time",
             "--path", str(specs_structure),
             "time-spec-2025-01-01-006",
             "phase-1",
             "--json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should be valid JSON
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, dict)
            assert "total_estimated" in data
            assert "total_actual" in data
            assert "variance" in data
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_phase_time_nonexistent_phase(self, sample_json_spec_simple, specs_structure):
        """Test phase-time with nonexistent phase."""
        result = run_cli(
             "phase-time",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
             "nonexistent-phase",
            capture_output=True,
            text=True
        )

        assert result.returncode == 1  # Should fail


@pytest.mark.integration
class TestListBlockersCLI:
    """Tests for list-blockers command."""

    def test_list_blockers_basic(self, sample_json_spec_with_blockers, specs_structure):
        """Test basic list-blockers command."""
        result = run_cli(
               "--no-json",
               "list-blockers",
             "--path", str(specs_structure),
             "blocked-spec-2025-01-01-005",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "blocked" in result.stdout.lower() or "blocker" in result.stdout.lower()

    def test_list_blockers_json(self, sample_json_spec_with_blockers, specs_structure):
        """Test list-blockers with --json output."""
        result = run_cli(
             "list-blockers",
             "--path", str(specs_structure),
             "blocked-spec-2025-01-01-005",
             "--json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should be valid JSON
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, list)
            assert len(data) == 2  # Should have 2 blocked tasks
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_list_blockers_no_blockers(self, sample_json_spec_simple, specs_structure):
        """Test list-blockers when there are no blocked tasks."""
        result = run_cli(
               "--no-json",
               "list-blockers",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should indicate no blockers found
        assert "no" in result.stdout.lower() or "0" in result.stdout


@pytest.mark.integration
class TestUpdatedCLICommands:
    """Tests for updated CLI commands using new JSON-only signatures."""

    def test_add_journal_new_signature(self, sample_json_spec_simple, specs_structure):
        """Test add-journal command with new spec_id-based signature."""
        result = run_cli(
               "--no-json",
               "add-journal",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
             "--title", "Test Journal Entry",
             "--content", "This is a test journal entry",
             "--entry-type", "note",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "journal" in result.stdout.lower() or "success" in result.stdout.lower()

    def test_add_journal_with_task_id(self, sample_json_spec_simple, specs_structure):
        """Test add-journal command with task reference."""
        result = run_cli(
               "--no-json",
               "add-journal",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
             "--title", "Task Started",
             "--content", "Beginning work",
             "--task-id", "task-1-1",
             "--entry-type", "status_change",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    def test_add_journal_custom_author(self, sample_json_spec_simple, specs_structure):
        """Test add-journal with custom author."""
        result = run_cli(
             "add-journal",
             "--path", str(specs_structure),
             "simple-spec-2025-01-001",
             "--title", "Decision Made",
             "--content", "Using approach A",
             "--author", "alice@example.com",
            capture_output=True,
            text=True
        )

        # Should run even if spec doesn't exist (will error later)
        assert result.returncode in [0, 1]

    def test_sync_metadata_new_command(self, sample_json_spec_simple, specs_structure):
        """Test new sync-metadata command."""
        result = run_cli(
             "sync-metadata",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    def test_add_verification_new_signature(self, sample_json_spec_simple, specs_structure):
        """Test add-verification command with new spec_id-based signature."""
        # Add verify nodes to the spec for this test
        from claude_skills.common.spec import load_json_spec, save_json_spec
        spec_id = "simple-spec-2025-01-01-001"
        spec_data = load_json_spec(spec_id, specs_structure)

        # Add verify-1-1 node
        spec_data["hierarchy"]["verify-1-1"] = {
            "id": "verify-1-1",
            "type": "verify",
            "title": "Verify Phase 1",
            "status": "pending",
            "parent": "phase-1",
            "children": [],
            "metadata": {}
        }
        # Add verify-1-1 to phase-1 children
        if "verify-1-1" not in spec_data["hierarchy"]["phase-1"]["children"]:
            spec_data["hierarchy"]["phase-1"]["children"].append("verify-1-1")

        save_json_spec(spec_id, specs_structure, spec_data)

        result = run_cli(
             "add-verification",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
             "verify-1-1",
             "PASSED",
             "--command", "pytest tests/",
             "--output", "All tests passed",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    def test_add_verification_failed_status(self, sample_json_spec_simple, specs_structure):
        """Test add-verification with FAILED status."""
        # Add verify nodes to the spec for this test
        from claude_skills.common.spec import load_json_spec, save_json_spec
        spec_id = "simple-spec-2025-01-01-001"
        spec_data = load_json_spec(spec_id, specs_structure)

        # Add verify-1-2 node
        spec_data["hierarchy"]["verify-1-2"] = {
            "id": "verify-1-2",
            "type": "verify",
            "title": "Verify Phase 1 Task 2",
            "status": "pending",
            "parent": "phase-1",
            "children": [],
            "metadata": {}
        }
        # Add verify-1-2 to phase-1 children
        if "verify-1-2" not in spec_data["hierarchy"]["phase-1"]["children"]:
            spec_data["hierarchy"]["phase-1"]["children"].append("verify-1-2")

        save_json_spec(spec_id, specs_structure, spec_data)

        result = run_cli(
             "add-verification",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
             "verify-1-2",
             "FAILED",
             "--issues", "Configuration errors found",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    def test_bulk_journal_new_signature(self, sample_json_spec_simple, specs_structure):
        """Test bulk-journal command with new signature (no spec_file)."""
        # First mark some tasks as completed
        from claude_skills.common.spec import load_json_spec, save_json_spec
        spec_id = "simple-spec-2025-01-01-001"
        spec_data = load_json_spec(spec_id, specs_structure)
        spec_data["hierarchy"]["task-1-1"]["status"] = "completed"
        spec_data["hierarchy"]["task-1-1"]["metadata"]["completed_at"] = "2025-01-01T12:00:00Z"
        spec_data["hierarchy"]["task-1-1"]["metadata"]["needs_journaling"] = True
        save_json_spec(spec_id, specs_structure, spec_data)

        result = run_cli(
             "bulk-journal",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

    def test_bulk_journal_specific_tasks(self, sample_json_spec_simple, specs_structure):
        """Test bulk-journal with specific task IDs."""
        # Mark tasks as completed
        from claude_skills.common.spec import load_json_spec, save_json_spec
        spec_id = "simple-spec-2025-01-01-001"
        spec_data = load_json_spec(spec_id, specs_structure)
        for task_id in ["task-1-1", "task-1-2"]:
            spec_data["hierarchy"][task_id]["status"] = "completed"
            spec_data["hierarchy"][task_id]["metadata"]["completed_at"] = "2025-01-01T12:00:00Z"
        save_json_spec(spec_id, specs_structure, spec_data)

        result = run_cli(
             "bulk-journal",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
             "--tasks", "task-1-1,task-1-2",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0


@pytest.mark.integration
class TestCompletionDetection:
    """Tests for automatic spec completion detection after update-status."""

    def test_completion_detection_after_update(self, sample_json_spec_simple, specs_structure):
        """Test completion prompt appears when last task marked complete."""
        from claude_skills.common.spec import load_json_spec, save_json_spec
        from unittest.mock import patch

        spec_id = "simple-spec-2025-01-01-001"
        spec_data = load_json_spec(spec_id, specs_structure)

        # Mark all tasks as completed except task-1-2
        for task_id in ["task-1-1"]:
            spec_data["hierarchy"][task_id]["status"] = "completed"

        # Ensure task-1-2 is the only pending task
        spec_data["hierarchy"]["task-1-2"]["status"] = "pending"
        save_json_spec(spec_id, specs_structure, spec_data)

        # Mock user input to decline completion (to avoid file moves)
        with patch('builtins.input', return_value='n'):
            result = run_cli(
                "--no-json",
                "update-status",
                "--path", str(specs_structure),
                spec_id,
                "task-1-2",
                "completed",
                capture_output=True,
                text=True
            )

        assert result.returncode == 0
        # Check that completion prompt appeared in output
        assert "All tasks complete" in result.stdout or "complete" in result.stdout.lower()

    def test_completion_prompt_skipped_when_blocked(self, sample_json_spec_with_blockers, specs_structure):
        """Test completion prompt skipped when blocked tasks exist."""
        from claude_skills.common.spec import load_json_spec, save_json_spec

        spec_id = "blocked-spec-2025-01-01-005"
        spec_data = load_json_spec(spec_id, specs_structure)

        # Mark all non-blocked tasks as completed except one
        for node_id, node in spec_data["hierarchy"].items():
            if node.get("type") == "task" and node.get("status") != "blocked":
                if node_id != "task-1-1":  # Leave one task pending
                    node["status"] = "completed"

        save_json_spec(spec_id, specs_structure, spec_data)

        # Mark the last non-blocked task as completed
        result = run_cli(
            "--no-json",
            "update-status",
            "--path", str(specs_structure),
            spec_id,
            "task-1-1",
            "completed",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Completion prompt should NOT appear because blocked tasks exist
        # Instead, should see warning about blocked tasks
        assert "blocked" in result.stdout.lower() or "cannot complete" in result.stdout.lower()

    def test_user_confirmation_flow(self, sample_json_spec_completed, specs_structure):
        """Test user confirmation and spec completion flow."""
        from claude_skills.common.spec import load_json_spec, save_json_spec
        from pathlib import Path

        spec_id = "completed-spec-2025-01-01-007"
        spec_data = load_json_spec(spec_id, specs_structure)

        # Ensure one task is pending
        spec_data["hierarchy"]["task-1-1"]["status"] = "pending"
        save_json_spec(spec_id, specs_structure, spec_data)

        # Provide user input via stdin (y to confirm completion, empty for hours)
        result = run_cli(
            "--no-json",
            "update-status",
            "--path", str(specs_structure),
            spec_id,
            "task-1-1",
            "completed",
            capture_output=True,
            text=True,
            input="y\n\n"  # y for confirmation, Enter for hours
        )

        # The command might fail if complete_spec tries to move files
        # But we should still see the completion prompt
        assert "complete" in result.stdout.lower()
        assert "Mark spec as complete" in result.stdout or "mark this spec" in result.stdout.lower()

    def test_user_decline_flow(self, sample_json_spec_simple, specs_structure):
        """Test user decline flow - spec remains active."""
        from claude_skills.common.spec import load_json_spec, save_json_spec
        from pathlib import Path

        spec_id = "simple-spec-2025-01-01-001"
        spec_data = load_json_spec(spec_id, specs_structure)

        # Mark all tasks as completed except task-1-2
        hierarchy = spec_data.get("hierarchy", {})
        for node_id, node in hierarchy.items():
            if node.get("type") == "task" and node_id != "task-1-2":
                node["status"] = "completed"

        # Ensure task-1-2 is pending
        hierarchy["task-1-2"]["status"] = "pending"
        save_json_spec(spec_id, specs_structure, spec_data)

        # Provide user input via stdin to decline completion
        result = run_cli(
            "--no-json",
            "update-status",
            "--path", str(specs_structure),
            spec_id,
            "task-1-2",
            "completed",
            capture_output=True,
            text=True,
            input="n\n"  # n to decline completion
        )

        assert result.returncode == 0
        # Verify completion prompt appeared (shows that detection is working)
        assert "Mark spec as complete" in result.stdout or "mark this spec" in result.stdout.lower()
        # The prompt should include the progress
        assert "4/4 tasks" in result.stdout or "100%" in result.stdout

        # Verify spec still exists in active directory (wasn't moved to completed)
        # Note: The spec file should still be in the active directory since user declined
        spec_file = specs_structure / "active" / f"{spec_id}.json"
        assert spec_file.exists() or (specs_structure / f"{spec_id}.json").exists()


@pytest.mark.integration
class TestUpdateTaskMetadataCLI:
    """Tests for update-task-metadata command with --metadata flag."""

    def test_update_metadata_individual_flags(self, sample_json_spec_simple, specs_structure):
        """Test update-task-metadata with individual flags."""
        result = run_cli(
            "update-task-metadata",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "task-1-1",
            "--file-path", "src/test.py",
            "--description", "Updated description",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Verify metadata was updated
        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["task_id"] == "task-1-1"

    def test_update_metadata_json_flag(self, sample_json_spec_simple, specs_structure):
        """Test update-task-metadata with --metadata JSON flag."""
        result = run_cli(
            "update-task-metadata",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "task-1-1",
            "--metadata", '{"focus_areas": ["performance", "security"], "priority": "high"}',
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["success"] is True

        # Verify the metadata was actually saved
        from claude_skills.common.spec import load_json_spec
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        task_metadata = spec_data["hierarchy"]["task-1-1"]["metadata"]
        assert "focus_areas" in task_metadata
        assert task_metadata["focus_areas"] == ["performance", "security"]
        assert task_metadata["priority"] == "high"

    def test_update_metadata_merge_json_and_flags(self, sample_json_spec_simple, specs_structure):
        """Test that individual flags take precedence over JSON metadata."""
        result = run_cli(
            "update-task-metadata",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "task-1-1",
            "--metadata", '{"description": "from JSON", "custom_field": "test"}',
            "--description", "from flag",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Verify flag took precedence and JSON was merged
        from claude_skills.common.spec import load_json_spec
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        task_metadata = spec_data["hierarchy"]["task-1-1"]["metadata"]
        assert task_metadata["description"] == "from flag"  # Flag won
        assert task_metadata["custom_field"] == "test"  # JSON was merged

    def test_update_metadata_invalid_json(self, sample_json_spec_simple, specs_structure):
        """Test update-task-metadata with invalid JSON."""
        result = run_cli(
            "update-task-metadata",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "task-1-1",
            "--metadata", '{invalid json}',
            capture_output=True,
            text=True
        )

        assert result.returncode == 1
        assert "Invalid JSON" in result.stdout or "Invalid JSON" in result.stderr

    def test_update_metadata_non_dict_json(self, sample_json_spec_simple, specs_structure):
        """Test update-task-metadata with non-dictionary JSON."""
        result = run_cli(
            "update-task-metadata",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "task-1-1",
            "--metadata", '["array", "not", "dict"]',
            capture_output=True,
            text=True
        )

        assert result.returncode == 1
        assert "must be a JSON object" in result.stdout or "must be a JSON object" in result.stderr

    def test_update_metadata_no_fields_provided(self, sample_json_spec_simple, specs_structure):
        """Test update-task-metadata with no metadata fields."""
        result = run_cli(
            "update-task-metadata",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "task-1-1",
            capture_output=True,
            text=True
        )

        assert result.returncode == 1
        assert "No metadata fields provided" in result.stdout or "No metadata fields provided" in result.stderr

    def test_update_metadata_complex_nested_json(self, sample_json_spec_simple, specs_structure):
        """Test update-task-metadata with complex nested JSON structures."""
        complex_metadata = {
            "focus_areas": ["error handling", "edge cases"],
            "details": {
                "complexity": "high",
                "blockers": ["dependency X", "clarification needed"]
            },
            "estimated_subtasks": 5
        }

        result = run_cli(
            "update-task-metadata",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "task-1-1",
            "--metadata", json.dumps(complex_metadata),
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Verify the complex structure was saved correctly
        from claude_skills.common.spec import load_json_spec
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        task_metadata = spec_data["hierarchy"]["task-1-1"]["metadata"]
        assert task_metadata["focus_areas"] == ["error handling", "edge cases"]
        assert task_metadata["details"]["complexity"] == "high"
        assert task_metadata["estimated_subtasks"] == 5
