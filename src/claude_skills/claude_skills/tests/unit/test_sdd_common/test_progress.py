"""
Unit tests for sdd_common.progress module.

Tests progress calculation: recalculate_progress, update_parent_status,
get_progress_summary, list_phases.
"""

import pytest
from claude_skills.common import (
    recalculate_progress,
    update_parent_status,
    get_progress_summary,
    list_phases,
    load_json_spec
)


class TestGetProgressSummary:
    """Tests for get_progress_summary function."""

    def test_get_progress_summary_simple_spec(self, sample_json_spec_simple, specs_structure):
        """Test getting progress summary from simple spec."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        progress = get_progress_summary(spec_data)

        assert progress is not None
        assert "spec_id" in progress
        assert "title" in progress
        assert "total_tasks" in progress
        assert "completed_tasks" in progress
        assert "percentage" in progress

    def test_progress_summary_calculates_percentage(self, sample_json_spec_simple, specs_structure):
        """Test that progress summary correctly calculates percentage."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        # Complete one task
        spec_data["hierarchy"]["task-1-1"]["status"] = "completed"
        spec_data = recalculate_progress(spec_data)  # Recalculate from root

        progress = get_progress_summary(spec_data)

        assert progress["completed_tasks"] == 1
        assert progress["total_tasks"] == 4  # 2 phases * 2 tasks
        assert progress["percentage"] == 25  # 1/4 = 25%

    def test_progress_summary_with_all_completed(self, sample_json_spec_simple, specs_structure):
        """Test progress summary when all tasks completed."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        # Complete all tasks
        for key, value in spec_data["hierarchy"].items():
            if value.get("type") == "task":
                value["status"] = "completed"

        progress = get_progress_summary(spec_data)

        assert progress["completed_tasks"] == progress["total_tasks"]
        assert progress["percentage"] == 100

    def test_progress_summary_includes_current_phase(self, sample_json_spec_simple, specs_structure):
        """Test that progress summary includes current phase info."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        progress = get_progress_summary(spec_data)

        # Should have current_phase information
        assert "current_phase" in progress
        if progress["current_phase"]:
            assert "title" in progress["current_phase"]
            assert "completed" in progress["current_phase"]
            assert "total" in progress["current_phase"]


class TestListPhases:
    """Tests for list_phases function."""

    def test_list_phases_returns_all_phases(self, sample_json_spec_simple, specs_structure):
        """Test that list_phases returns all phases."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        phases = list_phases(spec_data)

        assert phases is not None
        assert len(phases) == 2  # Our simple spec has 2 phases

    def test_list_phases_structure(self, sample_json_spec_simple, specs_structure):
        """Test that each phase has expected structure."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        phases = list_phases(spec_data)

        for phase in phases:
            assert "id" in phase
            assert "title" in phase
            assert "status" in phase
            assert "total_tasks" in phase or "total" in phase
            assert "completed_tasks" in phase or "completed" in phase

    def test_list_phases_calculates_task_counts(self, sample_json_spec_simple, specs_structure):
        """Test that phases correctly count tasks."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)
        phases = list_phases(spec_data)

        # Each phase should have 2 tasks
        for phase in phases:
            total = phase.get("total_tasks") or phase.get("total")
            assert total == 2

    def test_list_phases_with_complex_spec(self, sample_spec_complex, sample_json_spec_complex, specs_structure, tmp_path):
        """Test listing phases from complex spec (3 phases)."""
        spec_data = load_json_spec("complex-spec-2025-01-01-002", specs_structure)
        phases = list_phases(spec_data)

        assert len(phases) == 3
        assert all("phase" in p.get("id", "") for p in phases)


class TestRecalculateProgress:
    """Tests for recalculate_progress function."""

    def test_recalculate_progress_updates_counts(self, sample_json_spec_simple, specs_structure):
        """Test that recalculate_progress updates task counts."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        # Complete some tasks
        spec_data["hierarchy"]["task-1-1"]["status"] = "completed"
        spec_data["hierarchy"]["task-1-2"]["status"] = "completed"

        # Recalculate
        updated_state = recalculate_progress(spec_data)

        # Phases should reflect completed tasks
        phase_1 = updated_state["hierarchy"]["phase-1"]
        # Check if phase status updated or has progress metadata
        assert phase_1["status"] == "completed" or "progress" in phase_1

    def test_recalculate_progress_propagates_to_parents(self, sample_json_spec_simple, specs_structure):
        """Test that progress updates propagate to parent phases."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        # Complete all tasks in phase 1
        spec_data["hierarchy"]["task-1-1"]["status"] = "completed"
        spec_data["hierarchy"]["task-1-2"]["status"] = "completed"

        updated_state = recalculate_progress(spec_data)

        # Phase 1 should now be completed
        assert updated_state["hierarchy"]["phase-1"]["status"] in ["completed", "in_progress"]


class TestUpdateParentStatus:
    """Tests for update_parent_status function."""

    def test_update_parent_when_all_children_complete(self, sample_json_spec_simple, specs_structure):
        """Test updating parent status when all children are complete."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        # Complete all tasks in phase 1
        spec_data["hierarchy"]["task-1-1"]["status"] = "completed"
        spec_data["hierarchy"]["task-1-2"]["status"] = "completed"

        # Update parent (call with child ID to update the actual parent)
        updated_state = update_parent_status(spec_data, "task-1-1")

        # Phase 1 should be completed
        assert updated_state["hierarchy"]["phase-1"]["status"] == "completed"

    def test_update_parent_when_some_children_in_progress(self, sample_json_spec_simple, specs_structure):
        """Test updating parent when some children are in progress."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        # Start one task
        spec_data["hierarchy"]["task-1-1"]["status"] = "in_progress"

        updated_state = update_parent_status(spec_data, "task-1-1")

        # Phase 1 should be in_progress
        assert updated_state["hierarchy"]["phase-1"]["status"] == "in_progress"


@pytest.mark.integration
class TestProgressIntegration:
    """Integration tests for progress calculation."""

    def test_complete_workflow_progress_tracking(self, sample_json_spec_simple, specs_structure):
        """Test progress tracking through a complete workflow."""
        spec_data = load_json_spec("simple-spec-2025-01-01-001", specs_structure)

        # Initial progress
        progress_initial = get_progress_summary(spec_data)
        assert progress_initial["completed_tasks"] == 0
        assert progress_initial["percentage"] == 0

        # Complete first task
        spec_data["hierarchy"]["task-1-1"]["status"] = "completed"
        spec_data = recalculate_progress(spec_data)
        progress_1 = get_progress_summary(spec_data)
        assert progress_1["completed_tasks"] == 1
        assert progress_1["percentage"] == 25

        # Complete second task (phase 1 complete)
        spec_data["hierarchy"]["task-1-2"]["status"] = "completed"
        spec_data = recalculate_progress(spec_data)
        progress_2 = get_progress_summary(spec_data)
        assert progress_2["completed_tasks"] == 2
        assert progress_2["percentage"] == 50

        # Complete all tasks
        spec_data["hierarchy"]["task-2-1"]["status"] = "completed"
        spec_data["hierarchy"]["task-2-2"]["status"] = "completed"
        spec_data = recalculate_progress(spec_data)
        progress_final = get_progress_summary(spec_data)
        assert progress_final["completed_tasks"] == 4
        assert progress_final["percentage"] == 100
