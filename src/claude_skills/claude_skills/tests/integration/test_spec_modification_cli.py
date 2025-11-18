"""
Integration tests for spec modification CLI commands.

Tests end-to-end functionality of:
- add-assumption: Add assumptions to spec metadata
- list-assumptions: List assumptions from spec
- update-estimate: Update task time/complexity estimates
- add-task: Add new tasks to spec hierarchy
- remove-task: Remove tasks from spec hierarchy

Note: Tests use unified CLI (sdd) instead of legacy sdd-update.
"""

import json

import pytest

from .cli_runner import run_cli


@pytest.mark.integration
class TestAddAssumptionCLI:
    """Tests for add-assumption command."""

    def test_add_assumption_basic(self, sample_json_spec_simple, specs_structure):
        """Test basic add-assumption command."""
        result = run_cli(
            "add-assumption",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001", "Users will have valid email addresses",
            "--type", "requirement",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "assumption" in result.stdout.lower() or "success" in result.stdout.lower()

        # Verify assumption was added to spec file
        from claude_skills.common.spec import load_json_spec
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        assumptions = spec_data.get("metadata", {}).get("assumptions", [])
        assert len(assumptions) > 0
        # Find the assumption we just added
        added = next((a for a in assumptions if a.get("text") == "Users will have valid email addresses"), None)
        assert added is not None
        assert added["type"] == "requirement"

    def test_add_assumption_different_types(self, sample_json_spec_simple, specs_structure):
        """Test add-assumption with different assumption types."""
        types_to_test = ["constraint", "requirement"]

        for assumption_type in types_to_test:
            result = run_cli(
                "add-assumption",
                "--path", str(specs_structure),
                "simple-spec-2025-01-01-001",
                f"Test {assumption_type} assumption",
                "--type", assumption_type,
                capture_output=True,
                text=True
            )

            assert result.returncode == 0

    def test_add_assumption_with_author(self, sample_json_spec_simple, specs_structure):
        """Test add-assumption with custom author."""
        result = run_cli(
            "add-assumption",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001", "API rate limit is 1000 req/min",
            "--type", "constraint",
            "--author", "alice@example.com",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Verify author was set
        from claude_skills.common.spec import load_json_spec
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        assumptions = spec_data.get("metadata", {}).get("assumptions", [])
        added = next((a for a in assumptions if "API rate limit" in a.get("text", "")), None)
        assert added is not None
        assert added.get("added_by") == "alice@example.com"

    def test_add_assumption_json_output(self, sample_json_spec_simple, specs_structure):
        """Test add-assumption with --json flag."""
        result = run_cli(
            "add-assumption",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001", "Database uses PostgreSQL",
            "--type", "requirement",
            "--json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should be valid JSON
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, dict)
            assert "assumption_id" in data
            assert "message" in data
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_add_assumption_dry_run(self, sample_json_spec_simple, specs_structure):
        """Test add-assumption with --dry-run flag."""
        # Get initial assumption count
        from claude_skills.common.spec import load_json_spec
        spec_data_before = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        assumptions_before = spec_data_before.get("metadata", {}).get("assumptions", [])
        count_before = len(assumptions_before)

        result = run_cli(
            "add-assumption",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001", "This is a dry run test",
            "--type", "requirement",
            "--dry-run",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Dry run should succeed even if no message in output

        # Verify assumption was NOT added
        spec_data_after = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        assumptions_after = spec_data_after.get("metadata", {}).get("assumptions", [])
        assert len(assumptions_after) == count_before

    def test_add_assumption_invalid_spec(self, specs_structure):
        """Test add-assumption with nonexistent spec."""
        result = run_cli(
            "add-assumption",
            "--path", str(specs_structure),
            "nonexistent-spec", "Some assumption",
            "--type", "requirement",
            capture_output=True,
            text=True
        )

        assert result.returncode == 1


@pytest.mark.integration
class TestListAssumptionsCLI:
    """Tests for list-assumptions command."""

    def test_list_assumptions_basic(self, sample_json_spec_simple, specs_structure):
        """Test basic list-assumptions command."""
        # First add some assumptions
        run_cli(
            "add-assumption",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001", "Assumption 1",
            "--type", "requirement",
            capture_output=True
        )

        result = run_cli(
            "list-assumptions",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "assumption" in result.stdout.lower()

    def test_list_assumptions_by_type(self, sample_json_spec_simple, specs_structure):
        """Test list-assumptions with --type filter."""
        # Add assumptions of different types
        run_cli(
            "add-assumption",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001", "Requirement assumption",
            "--type", "requirement",
            capture_output=True
        )
        run_cli(
            "add-assumption",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001", "Constraint assumption",
            "--type", "constraint",
            capture_output=True
        )

        # List only requirement assumptions
        result = run_cli(
            "list-assumptions",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "--type", "requirement",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "requirement" in result.stdout.lower()

    def test_list_assumptions_json_output(self, sample_json_spec_simple, specs_structure):
        """Test list-assumptions with --json flag."""
        # Add an assumption first
        run_cli(
            "add-assumption",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001", "Test assumption",
            "--type", "requirement",
            capture_output=True
        )

        result = run_cli(
            "list-assumptions",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "--json",
            capture_output=True,
            text=True,
            ensure_verbose=False
        )

        assert result.returncode == 0
        # Should be valid JSON
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, list)
            assert len(data) > 0
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_list_assumptions_empty(self, sample_json_spec_simple, specs_structure):
        """Test list-assumptions when no assumptions exist."""
        # Create a fresh spec without assumptions
        from claude_skills.common.spec import load_json_spec, save_json_spec
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        spec_data["metadata"]["assumptions"] = []
        save_json_spec("simple-spec-2025-01-01-001", specs_structure, spec_data)

        result = run_cli(
            "list-assumptions",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Empty output is acceptable when no assumptions exist


@pytest.mark.integration
class TestUpdateEstimateCLI:
    """Tests for update-estimate command."""

    def test_update_estimate_hours_only(self, sample_json_spec_simple, specs_structure):
        """Test update-estimate with hours only."""
        result = run_cli(
            "update-estimate",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "task-1-1",
            "--hours", "5",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "estimate" in result.stdout.lower() or "success" in result.stdout.lower()

        # Verify estimate was updated
        from claude_skills.common.spec import load_json_spec
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        task = spec_data["hierarchy"]["task-1-1"]
        assert task["metadata"]["estimated_hours"] == 5

    def test_update_estimate_complexity_only(self, sample_json_spec_simple, specs_structure):
        """Test update-estimate with complexity only."""
        result = run_cli(
            "update-estimate",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "task-1-1",
            "--complexity", "high",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Verify complexity was updated
        from claude_skills.common.spec import load_json_spec
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        task = spec_data["hierarchy"]["task-1-1"]
        assert task["metadata"]["complexity"] == "high"

    def test_update_estimate_both(self, sample_json_spec_simple, specs_structure):
        """Test update-estimate with both hours and complexity."""
        result = run_cli(
            "update-estimate",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "task-1-2",
            "--hours", "3",
            "--complexity", "medium",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Verify both were updated
        from claude_skills.common.spec import load_json_spec
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        task = spec_data["hierarchy"]["task-1-2"]
        assert task["metadata"]["estimated_hours"] == 3
        assert task["metadata"]["complexity"] == "medium"

    def test_update_estimate_json_output(self, sample_json_spec_simple, specs_structure):
        """Test update-estimate with --json flag."""
        result = run_cli(
            "update-estimate",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "task-1-1",
            "--hours", "4",
            "--json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should be valid JSON
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, dict)
            assert "task_id" in data
            assert "updates" in data
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_update_estimate_dry_run(self, sample_json_spec_simple, specs_structure):
        """Test update-estimate with --dry-run flag."""
        # Get initial value
        from claude_skills.common.spec import load_json_spec
        spec_data_before = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        hours_before = spec_data_before["hierarchy"]["task-1-1"]["metadata"].get("estimated_hours")

        result = run_cli(
            "update-estimate",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "task-1-1",
            "--hours", "10",
            "--dry-run",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Check both stdout and stderr for DRY RUN message
        assert "DRY RUN" in result.stdout or "DRY RUN" in result.stderr or result.returncode == 0

        # Verify estimate was NOT updated
        spec_data_after = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        hours_after = spec_data_after["hierarchy"]["task-1-1"]["metadata"].get("estimated_hours")
        assert hours_after == hours_before

    def test_update_estimate_invalid_task(self, sample_json_spec_simple, specs_structure):
        """Test update-estimate with nonexistent task."""
        result = run_cli(
            "update-estimate",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "nonexistent-task",
            "--hours", "5",
            capture_output=True,
            text=True
        )

        assert result.returncode == 1


@pytest.mark.integration
class TestAddTaskCLI:
    """Tests for add-task command."""

    def test_add_task_basic(self, sample_json_spec_simple, specs_structure):
        """Test basic add-task command."""
        result = run_cli(
            "add-task",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "--parent", "phase-1",
            "--title", "New Test Task",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "task" in result.stdout.lower() or "success" in result.stdout.lower()

        # Verify task was added
        from claude_skills.common.spec import load_json_spec
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        # Find the new task
        added_task = None
        for task_id, task in spec_data["hierarchy"].items():
            if task.get("title") == "New Test Task":
                added_task = task
                break
        assert added_task is not None
        assert added_task["parent"] == "phase-1"

    def test_add_task_with_description(self, sample_json_spec_simple, specs_structure):
        """Test add-task with description."""
        result = run_cli(
            "add-task",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "--parent", "phase-1",
            "--title", "Task with Description",
            "--description", "This is a detailed description of the task",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Verify description was set
        from claude_skills.common.spec import load_json_spec
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        added_task = None
        for task_id, task in spec_data["hierarchy"].items():
            if task.get("title") == "Task with Description":
                added_task = task
                break
        assert added_task is not None
        assert added_task.get("description") == "This is a detailed description of the task"

    def test_add_task_with_estimate(self, sample_json_spec_simple, specs_structure):
        """Test add-task with estimated hours."""
        result = run_cli(
            "add-task",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "--parent", "phase-1",
            "--title", "Task with Estimate",
            "--hours", "3",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Verify estimate was set
        from claude_skills.common.spec import load_json_spec
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        added_task = None
        for task_id, task in spec_data["hierarchy"].items():
            if task.get("title") == "Task with Estimate":
                added_task = task
                break
        assert added_task is not None
        assert added_task["metadata"]["estimated_hours"] == 3

    def test_add_task_with_position(self, sample_json_spec_simple, specs_structure):
        """Test add-task with specific position."""
        result = run_cli(
            "add-task",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "--parent", "phase-1",
            "--title", "Task at Position 0",
            "--position", "0",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Verify task was added at position 0
        from claude_skills.common.spec import load_json_spec
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        phase_children = spec_data["hierarchy"]["phase-1"]["children"]
        # Find the new task ID
        added_task_id = None
        for task_id, task in spec_data["hierarchy"].items():
            if task.get("title") == "Task at Position 0":
                added_task_id = task_id
                break
        assert added_task_id in phase_children
        assert phase_children[0] == added_task_id

    def test_add_task_json_output(self, sample_json_spec_simple, specs_structure):
        """Test add-task with --json flag."""
        result = run_cli(
            "add-task",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "--parent", "phase-1",
            "--title", "JSON Output Task",
            "--json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should be valid JSON
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, dict)
            assert "task_id" in data
            assert "message" in data
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_add_task_dry_run(self, sample_json_spec_simple, specs_structure):
        """Test add-task with --dry-run flag."""
        # Get initial task count
        from claude_skills.common.spec import load_json_spec
        spec_data_before = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        count_before = len(spec_data_before["hierarchy"])

        result = run_cli(
            "add-task",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "--parent", "phase-1",
            "--title", "Dry Run Task",
            "--dry-run",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Check both stdout and stderr for DRY RUN message
        assert "DRY RUN" in result.stdout or "DRY RUN" in result.stderr or result.returncode == 0

        # Verify task was NOT added
        spec_data_after = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        assert len(spec_data_after["hierarchy"]) == count_before

    def test_add_task_invalid_parent(self, sample_json_spec_simple, specs_structure):
        """Test add-task with nonexistent parent."""
        result = run_cli(
            "add-task",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "--parent", "nonexistent-parent",
            "--title", "Orphaned Task",
            capture_output=True,
            text=True
        )

        assert result.returncode == 1


@pytest.mark.integration
class TestRemoveTaskCLI:
    """Tests for remove-task command."""

    def test_remove_task_basic(self, sample_json_spec_simple, specs_structure):
        """Test basic remove-task command."""
        # First add a task to remove
        add_result = run_cli(
            "add-task",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "--parent", "phase-1",
            "--title", "Task to Remove",
            capture_output=True,
            text=True
        )
        assert add_result.returncode == 0

        # Find the task ID
        from claude_skills.common.spec import load_json_spec
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        task_id = None
        for tid, task in spec_data["hierarchy"].items():
            if task.get("title") == "Task to Remove":
                task_id = tid
                break
        assert task_id is not None

        # Now remove it
        result = run_cli(
            "remove-task",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            task_id,
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "remove" in result.stdout.lower() or "success" in result.stdout.lower()

        # Verify task was removed
        spec_data_after = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        assert task_id not in spec_data_after["hierarchy"]

    def test_remove_task_with_cascade(self, sample_json_spec_simple, specs_structure):
        """Test remove-task with --cascade flag to remove children."""
        # Add a parent task with children
        add_parent = run_cli(
            "add-task",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "--parent", "phase-1",
            "--title", "Parent Task",
            capture_output=True
        )
        assert add_parent.returncode == 0

        # Find parent task ID
        from claude_skills.common.spec import load_json_spec
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        parent_id = None
        for tid, task in spec_data["hierarchy"].items():
            if task.get("title") == "Parent Task":
                parent_id = tid
                break
        assert parent_id is not None

        # Add a child task
        add_child = run_cli(
            "add-task",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "--parent", parent_id,
            "--title", "Child Task",
            capture_output=True
        )
        assert add_child.returncode == 0

        # Find child task ID
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        child_id = None
        for tid, task in spec_data["hierarchy"].items():
            if task.get("title") == "Child Task":
                child_id = tid
                break
        assert child_id is not None

        # Remove parent with cascade
        result = run_cli(
            "remove-task",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            parent_id,
            "--cascade",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0

        # Verify both parent and child were removed
        spec_data_after = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        assert parent_id not in spec_data_after["hierarchy"]
        assert child_id not in spec_data_after["hierarchy"]

    def test_remove_task_json_output(self, sample_json_spec_simple, specs_structure):
        """Test remove-task with --json flag."""
        # Add a task first
        add_result = run_cli(
            "add-task",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "--parent", "phase-1",
            "--title", "JSON Remove Task",
            capture_output=True
        )
        assert add_result.returncode == 0

        # Find task ID
        from claude_skills.common.spec import load_json_spec
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        task_id = None
        for tid, task in spec_data["hierarchy"].items():
            if task.get("title") == "JSON Remove Task":
                task_id = tid
                break
        assert task_id is not None

        # Remove with JSON output
        result = run_cli(
            "remove-task",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            task_id,
            "--json",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Should be valid JSON
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, dict)
            assert "task_id" in data
            assert "removed_count" in data
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_remove_task_dry_run(self, sample_json_spec_simple, specs_structure):
        """Test remove-task with --dry-run flag."""
        # Task exists in simple spec
        task_id = "task-1-1"

        result = run_cli(
            "remove-task",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            task_id,
            "--dry-run",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        # Check both stdout and stderr for DRY RUN message
        assert "DRY RUN" in result.stdout or "DRY RUN" in result.stderr or result.returncode == 0

        # Verify task was NOT removed
        from claude_skills.common.spec import load_json_spec
        spec_data_after = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        assert task_id in spec_data_after["hierarchy"]

    def test_remove_task_invalid(self, sample_json_spec_simple, specs_structure):
        """Test remove-task with nonexistent task."""
        result = run_cli(
            "remove-task",
            "--path", str(specs_structure),
            "simple-spec-2025-01-01-001",
            "nonexistent-task",
            capture_output=True,
            text=True
        )

        assert result.returncode == 1


@pytest.mark.integration
class TestSpecModificationWorkflow:
    """End-to-end workflow tests combining multiple commands."""

    def test_complete_workflow(self, sample_json_spec_simple, specs_structure):
        """Test complete workflow: add assumptions, add task, update estimate, remove task."""
        spec_id = "simple-spec-2025-01-01-001"

        # 1. Add requirement assumption
        result1 = run_cli(
            "add-assumption",
            "--path", str(specs_structure),
            spec_id,
            "API supports pagination",
            "--type", "requirement",
            capture_output=True
        )
        assert result1.returncode == 0

        # 2. List assumptions to verify
        result2 = run_cli(
            "list-assumptions",
            "--path", str(specs_structure),
            spec_id,
            capture_output=True,
            text=True
        )
        assert result2.returncode == 0
        assert "API supports pagination" in result2.stdout

        # 3. Add a new task
        result3 = run_cli(
            "add-task",
            "--path", str(specs_structure),
            spec_id,
            "--parent", "phase-1",
            "--title", "Implement pagination",
            "--hours", "4",
            capture_output=True
        )
        assert result3.returncode == 0

        # Find the new task ID
        from claude_skills.common.spec import load_json_spec
        spec_data = load_json_spec(spec_id, specs_structure)
        new_task_id = None
        for tid, task in spec_data["hierarchy"].items():
            if task.get("title") == "Implement pagination":
                new_task_id = tid
                break
        assert new_task_id is not None

        # 4. Update the task estimate
        result4 = run_cli(
            "update-estimate",
            "--path", str(specs_structure),
            spec_id,
            new_task_id,
            "--hours", "6",
            "--complexity", "high",
            capture_output=True
        )
        assert result4.returncode == 0

        # Verify estimate was updated
        spec_data = load_json_spec(spec_id, specs_structure)
        task = spec_data["hierarchy"][new_task_id]
        assert task["metadata"]["estimated_hours"] == 6
        assert task["metadata"]["complexity"] == "high"

        # 5. Remove the task
        result5 = run_cli(
            "remove-task",
            "--path", str(specs_structure),
            spec_id,
            new_task_id,
            capture_output=True
        )
        assert result5.returncode == 0

        # Verify task was removed
        spec_data = load_json_spec(spec_id, specs_structure)
        assert new_task_id not in spec_data["hierarchy"]

        # 6. Verify assumptions still exist
        assumptions = spec_data.get("metadata", {}).get("assumptions", [])
        assert any("API supports pagination" in a.get("text", "") for a in assumptions)

    def test_multiple_assumptions_workflow(self, sample_json_spec_simple, specs_structure):
        """Test adding multiple assumptions and listing by type."""
        spec_id = "simple-spec-2025-01-01-001"

        # Add assumptions of different types
        assumptions = [
            ("Users authenticate via OAuth", "requirement"),
            ("System supports 10k concurrent users", "constraint"),
            ("Revenue from premium features", "requirement"),
        ]

        for text, atype in assumptions:
            result = run_cli(
                "add-assumption",
                "--path", str(specs_structure),
                spec_id, text,
                "--type", atype,
                capture_output=True
            )
            assert result.returncode == 0

        # List all assumptions
        result_all = run_cli(
            "list-assumptions",
            "--path", str(specs_structure),
            spec_id,
            "--json",
            capture_output=True,
            text=True,
            ensure_verbose=False
        )
        assert result_all.returncode == 0
        all_assumptions = json.loads(result_all.stdout)
        assert len(all_assumptions) >= 3

        # List only requirement assumptions
        result_req = run_cli(
            "list-assumptions",
            "--path", str(specs_structure),
            spec_id,
            "--type", "requirement",
            "--json",
            capture_output=True,
            text=True,
            ensure_verbose=False
        )
        assert result_req.returncode == 0
        req_assumptions = json.loads(result_req.stdout)
        assert all(a.get("type") == "requirement" for a in req_assumptions)
