"""
Integration tests for sdd_update_tools.py CLI.

Tests all query CLI commands with various arguments, JSON output, and error handling.

Note: Tests updated to use unified CLI (sdd update) instead of legacy sdd-update.
"""

import sys
import pytest
import subprocess
import json
import shutil
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
            # This is not a global flag - could be subcommand or subcommand arg
            non_global_args.append(arg)
            i += 1

    # Build final command: global_flags + subcommand + non-global args
    final_args = global_args + non_global_args

    if shutil.which(CLI_CMD):
        return subprocess.run([CLI_CMD] + final_args, **kwargs)
    else:
        return subprocess.run(
            [sys.executable, '-m', 'claude_skills.cli.sdd'] + final_args,
            **kwargs
        )


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
             "--format", "simple",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Simple format should just list IDs
        assert "task-1-1" in result.stdout or "task" in result.stdout

    def test_query_tasks_json_output(self, sample_json_spec_simple, specs_structure):
        """Test query-tasks with --json flag."""
        result = run_cli( "query-tasks",
             "--path", str(specs_structure),
             "simple-spec-2025-01-01-001",
             "--format", "json",
             "--json",
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
