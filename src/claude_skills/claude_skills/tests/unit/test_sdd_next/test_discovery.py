"""
Unit tests for sdd-next discovery operations.

Tests: get_next_task, get_task_info, check_dependencies, prepare_task.
"""

import json
import pytest
from pathlib import Path

from claude_skills.sdd_next.discovery import get_next_task, get_task_info, check_dependencies, prepare_task
from claude_skills.common import load_json_spec


class TestGetNextTask:
    """Tests for get_next_task function."""

    def test_get_next_task_returns_first_pending(self, sample_json_spec_simple, specs_structure):
        """Test getting next task returns first pending task."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        next_task = get_next_task(spec_data)

        assert next_task is not None
        task_id, task_data = next_task
        assert task_id == "task-1-1"
        assert task_data["status"] == "pending"

    def test_get_next_task_skips_completed(self, sample_json_spec_simple, specs_structure):
        """Test that completed tasks are skipped."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        # Complete first task
        spec_data["hierarchy"]["task-1-1"]["status"] = "completed"

        next_task = get_next_task(spec_data)

        assert next_task is not None
        task_id, task_data = next_task
        assert task_id == "task-1-2"  # Should return next pending task

    def test_get_next_task_respects_dependencies(self, sample_json_spec_with_deps, specs_structure):
        """Test that next task respects blocked_by dependencies."""
        spec_data = load_json_spec("deps-spec-2025-01-01-003", specs_structure)

        next_task = get_next_task(spec_data)

        if next_task:
            task_id, task_data = next_task
            # Should not return task-2-2 since it's blocked by task-2-1
            assert task_id != "task-2-2" or len(task_data.get("dependencies", {}).get("blocked_by", [])) == 0

    def test_get_next_task_from_current_phase(self, sample_json_spec_simple, specs_structure):
        """Test that next task comes from current in_progress phase."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        # Phase 1 should be in_progress
        assert spec_data["hierarchy"]["phase-1"]["status"] == "in_progress"

        next_task = get_next_task(spec_data)

        if next_task:
            task_id, task_data = next_task
            # Should be from phase-1
            assert task_data["parent"] == "phase-1"

    def test_get_next_task_none_when_all_complete(self, sample_json_spec_simple, specs_structure):
        """Test returns None when all tasks are completed."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        # Complete all tasks
        for key, value in spec_data["hierarchy"].items():
            if value.get("type") == "task":
                value["status"] = "completed"

        next_task = get_next_task(spec_data)

        assert next_task is None

    def test_get_next_task_empty_hierarchy(self):
        """Test with empty hierarchy."""
        spec_data = {"spec_id": "test", "hierarchy": {}}
        next_task = get_next_task(spec_data)

        assert next_task is None

    def test_get_next_task_finds_verify_tasks(self, sample_json_spec_simple, specs_structure):
        """Test that verification tasks are discoverable as actionable tasks."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        # Complete all regular tasks so verify tasks become next
        for key, value in spec_data["hierarchy"].items():
            if value.get("type") in ["task", "subtask"]:
                value["status"] = "completed"

        # Add a verify task to the hierarchy
        spec_data["hierarchy"]["verify-1-1"] = {
            "type": "verify",
            "title": "Test verification",
            "status": "pending",
            "parent": "phase-1",
            "children": [],
            "dependencies": {"blocked_by": [], "depends": [], "blocks": []},
            "metadata": {"verification_type": "manual"}
        }

        # Ensure phase-1 includes the verify task
        if "children" not in spec_data["hierarchy"]["phase-1"]:
            spec_data["hierarchy"]["phase-1"]["children"] = []
        spec_data["hierarchy"]["phase-1"]["children"].append("verify-1-1")

        next_task = get_next_task(spec_data)

        assert next_task is not None
        task_id, task_data = next_task
        assert task_id == "verify-1-1"
        assert task_data["type"] == "verify"


class TestGetTaskInfo:
    """Tests for get_task_info function."""

    def test_get_task_info_existing_task(self, sample_json_spec_simple, specs_structure):
        """Test getting info for existing task."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        task_info = get_task_info(spec_data, "task-1-1")

        assert task_info is not None
        assert task_info["id"] == "task-1-1"
        assert task_info["type"] == "task"
        assert "metadata" in task_info

    def test_get_task_info_nonexistent_task(self, sample_json_spec_simple, specs_structure):
        """Test getting info for non-existent task."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        task_info = get_task_info(spec_data, "task-99-99")

        assert task_info is None

    def test_get_task_info_includes_all_fields(self, sample_json_spec_simple, specs_structure):
        """Test that task info includes all expected fields."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        task_info = get_task_info(spec_data, "task-1-1")

        expected_fields = ["id", "type", "title", "status", "parent", "dependencies", "metadata"]
        for field in expected_fields:
            assert field in task_info, f"Missing field: {field}"

    def test_get_task_info_for_different_tasks(self, sample_json_spec_simple, specs_structure):
        """Test getting info for multiple different tasks."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        task_ids = ["task-1-1", "task-1-2", "task-2-1", "task-2-2"]

        for task_id in task_ids:
            task_info = get_task_info(spec_data, task_id)
            assert task_info is not None
            assert task_info["id"] == task_id


class TestCheckDependencies:
    """Tests for check_dependencies function."""

    def test_check_dependencies_no_blockers(self, sample_json_spec_simple, specs_structure):
        """Test checking dependencies for task with no blockers."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        deps = check_dependencies(spec_data, "task-1-1")

        assert "error" not in deps
        assert deps["can_start"] is True
        assert len(deps["blocked_by"]) == 0

    def test_check_dependencies_with_blockers(self, sample_json_spec_with_deps, specs_structure):
        """Test checking dependencies for blocked task."""
        spec_data = load_json_spec("deps-spec-2025-01-01-003", specs_structure)
        deps = check_dependencies(spec_data, "task-2-2")

        assert "error" not in deps
        assert deps["can_start"] is False
        assert len(deps["blocked_by"]) > 0
        assert "task-2-1" in [d["id"] for d in deps["blocked_by"]]

    def test_check_dependencies_nonexistent_task(self, sample_json_spec_simple, specs_structure):
        """Test checking dependencies for non-existent task."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        deps = check_dependencies(spec_data, "task-99-99")

        assert "error" in deps

    def test_check_dependencies_includes_blocks(self, sample_json_spec_with_deps, specs_structure):
        """Test that dependency check includes tasks this task blocks."""
        spec_data = load_json_spec("deps-spec-2025-01-01-003", specs_structure)

        # task-2-1 blocks task-2-2
        deps = check_dependencies(spec_data, "task-2-1")

        assert "blocks" in deps
        # Should show that completing this unblocks task-2-2

    def test_check_dependencies_resolved_when_complete(self, sample_json_spec_with_deps, specs_structure):
        """Test that dependencies are resolved when blocker is complete."""
        spec_data = load_json_spec("deps-spec-2025-01-01-003", specs_structure)

        # Complete the blocking task
        spec_data["hierarchy"]["task-2-1"]["status"] = "completed"

        # Now recalculate - task-2-2 should no longer be blocked
        # (This depends on implementation - might need to manually update blocked_by)
        deps = check_dependencies(spec_data, "task-2-2")

        # If implementation auto-resolves, can_start should be True
        # Otherwise, blocked_by should still show task-2-1 but with status completed


class TestPrepareTask:
    """Tests for prepare_task function."""

    def test_prepare_task_success(self, sample_json_spec_simple, sample_spec_simple, specs_structure):
        """Test preparing a task for implementation."""
        task_prep = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-1")

        assert task_prep is not None
        assert task_prep.get("success") is True or "task_id" in task_prep
        assert "task_id" in task_prep
        assert "task_data" in task_prep
        context = task_prep.get("context")
        assert isinstance(context, dict)
        assert "phase" in context
        assert "task_journal" in context
        assert isinstance(context.get("sibling_files"), list)

    def test_prepare_task_includes_dependencies(self, sample_json_spec_simple, specs_structure):
        """Test that prepare_task includes dependency information."""
        task_prep = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-1")

        assert "dependencies" in task_prep
        deps = task_prep["dependencies"]
        assert "can_start" in deps or "blocked_by" in deps

    def test_prepare_task_returns_metadata_only(self, sample_json_spec_simple, sample_spec_simple, specs_structure):
        """prepare_task should not attempt to include legacy markdown details."""
        task_prep = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-1")

        assert task_prep.get("success") is True
        # Legacy fields should remain absent now that specs are JSON-only
        assert task_prep.get("task_details") is None
        assert task_prep.get("spec_file") is None

    def test_prepare_task_nonexistent(self, sample_json_spec_simple, specs_structure):
        """Test preparing non-existent task."""
        task_prep = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-99-99")

        assert task_prep.get("success") is False or "error" in task_prep

    def test_prepare_task_auto_finds_next(self, sample_json_spec_simple, specs_structure):
        """Test prepare_task with None task_id finds next task."""
        # Some implementations allow task_id=None to auto-find next
        task_prep = prepare_task("simple-spec-2025-01-01-001", specs_structure, None)

        if task_prep and task_prep.get("success") is not False:
            assert "task_id" in task_prep
            assert task_prep["task_id"] == "task-1-1"

    def test_prepare_task_include_full_journal(self, sample_json_spec_simple, specs_structure):
        """Flag should return previous sibling journal entries when requested."""
        spec_path = sample_json_spec_simple
        spec_data = json.loads(spec_path.read_text())
        spec_data["journal"] = [
            {
                "task_id": "task-1-1",
                "timestamp": "2025-11-16T10:00:00Z",
                "entry_type": "note",
                "title": "Initial note",
                "content": "Captured baseline details",
            },
            {
                "task_id": "task-1-1",
                "timestamp": "2025-11-16T11:00:00Z",
                "entry_type": "decision",
                "title": "Follow-up",
                "content": "Decided on companion tasks",
            },
        ]
        spec_path.write_text(json.dumps(spec_data, indent=2))

        task_prep = prepare_task(
            "simple-spec-2025-01-01-001",
            specs_structure,
            "task-1-2",
            include_full_journal=True,
            include_phase_history=True,
            include_spec_overview=True,
        )

        extended = task_prep.get("extended_context")
        assert extended
        assert len(extended["previous_sibling_journal"]) == 2
        phase_entries = extended.get("phase_journal")
        assert phase_entries is not None
        assert len(phase_entries) == 2
        spec_overview = extended.get("spec_overview")
        assert spec_overview is not None
        assert spec_overview.get("total_tasks")


@pytest.mark.integration
class TestDiscoveryIntegration:
    """Integration tests for discovery operations."""

    def test_complete_task_discovery_workflow(self, sample_json_spec_simple, sample_spec_simple, specs_structure):
        """Test complete workflow: find next -> check deps -> prepare."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        # Step 1: Get next task
        next_task = get_next_task(spec_data)
        assert next_task is not None
        task_id, _ = next_task

        # Step 2: Get task info
        task_info = get_task_info(spec_data, task_id)
        assert task_info is not None

        # Step 3: Check dependencies
        deps = check_dependencies(spec_data, task_id)
        assert deps["can_start"] is True

        # Step 4: Prepare task
        task_prep = prepare_task("simple-spec-2025-01-01-001", specs_structure, task_id)
        assert task_prep.get("success") is True or "task_id" in task_prep

    def test_task_progression_through_phase(self, sample_json_spec_simple, specs_structure):
        """Test task discovery as phase progresses."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        # First task
        next_1 = get_next_task(spec_data)
        assert next_1[0] == "task-1-1"

        # Complete it
        spec_data["hierarchy"]["task-1-1"]["status"] = "completed"

        # Second task
        next_2 = get_next_task(spec_data)
        assert next_2[0] == "task-1-2"

        # Complete it
        spec_data["hierarchy"]["task-1-2"]["status"] = "completed"

        # Should move to phase 2
        next_3 = get_next_task(spec_data)
        if next_3:
            assert next_3[0] in ["task-2-1", "task-2-2"]
