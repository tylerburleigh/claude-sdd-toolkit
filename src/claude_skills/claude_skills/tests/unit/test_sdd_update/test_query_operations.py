"""
Unit tests for sdd-update query operations.

Tests query_tasks, get_task, list_phases, check_complete, phase_time, and list_blockers.
"""

import pytest
from pathlib import Path

# Import operations to test
from claude_skills.sdd_update.query import (
    query_tasks,
    get_task,
    list_phases,
    check_complete,
    phase_time,
    list_blockers
)
from claude_skills.common.query_operations import (
    get_journal_entries,
    get_task_journal
)


@pytest.mark.unit
class TestQueryTasks:
    """Tests for query_tasks function."""

    def test_query_all_tasks(self, sample_json_spec_simple, specs_structure):
        """Test querying all tasks without filters."""
        results = query_tasks(
            spec_id="simple-spec-2025-01-01-001",
            specs_dir=specs_structure,
            format_type="simple",
            printer=None
        )

        assert results is not None
        assert len(results) >= 4  # At least 4 tasks (task-1-1, task-1-2, task-2-1, task-2-2)

    def test_query_by_status_pending(self, sample_json_spec_simple, specs_structure):
        """Test filtering tasks by pending status."""
        results = query_tasks(
            spec_id="simple-spec-2025-01-01-001",
            specs_dir=specs_structure,
            status="pending",
            printer=None
        )

        assert results is not None
        # All tasks should be pending in the simple state
        assert all(task["status"] == "pending" for task in results if task["type"] == "task")

    def test_query_by_status_blocked(self, sample_json_spec_with_blockers, specs_structure):
        """Test filtering tasks by blocked status."""
        results = query_tasks(
            spec_id="blocked-spec-2025-01-01-005",
            specs_dir=specs_structure,
            status="blocked",
            printer=None
        )

        assert results is not None
        assert len(results) == 2  # task-1-2 and task-2-1 are blocked
        assert all(task["status"] == "blocked" for task in results)

    def test_query_by_status_completed(self, sample_json_spec_with_blockers, specs_structure):
        """Test filtering tasks by completed status."""
        results = query_tasks(
            spec_id="blocked-spec-2025-01-01-005",
            specs_dir=specs_structure,
            status="completed",
            printer=None
        )

        assert results is not None
        assert len(results) >= 1  # task-1-1 is completed

    def test_query_by_type_task(self, sample_json_spec_simple, specs_structure):
        """Test filtering by task type."""
        results = query_tasks(
            spec_id="simple-spec-2025-01-01-001",
            specs_dir=specs_structure,
            task_type="task",
            printer=None
        )

        assert results is not None
        assert all(task["type"] == "task" for task in results)

    def test_query_by_type_phase(self, sample_json_spec_simple, specs_structure):
        """Test filtering by phase type."""
        results = query_tasks(
            spec_id="simple-spec-2025-01-01-001",
            specs_dir=specs_structure,
            task_type="phase",
            printer=None
        )

        assert results is not None
        assert len(results) == 2  # phase-1 and phase-2
        assert all(task["type"] == "phase" for task in results)

    def test_query_by_parent(self, sample_json_spec_simple, specs_structure):
        """Test filtering by parent node."""
        results = query_tasks(
            spec_id="simple-spec-2025-01-01-001",
            specs_dir=specs_structure,
            parent="phase-1",
            printer=None
        )

        assert results is not None
        assert len(results) == 2  # task-1-1 and task-1-2
        assert all(task["parent"] == "phase-1" for task in results)

    def test_query_invalid_spec_id(self, specs_structure):
        """Test querying with invalid spec_id."""
        results = query_tasks(
            spec_id="nonexistent-spec",
            specs_dir=specs_structure,
            printer=None
        )

        assert results is None


@pytest.mark.unit
class TestGetTask:
    """Tests for get_task function."""

    def test_get_existing_task(self, sample_json_spec_simple, specs_structure):
        """Test getting an existing task."""
        task = get_task(
            spec_id="simple-spec-2025-01-01-001",
            task_id="task-1-1",
            specs_dir=specs_structure,
            printer=None
        )

        assert task is not None
        assert task["id"] == "task-1-1"
        assert task["type"] == "task"
        assert "title" in task
        assert "status" in task

    def test_get_task_with_metadata(self, sample_json_spec_with_time, specs_structure):
        """Test getting task with metadata."""
        task = get_task(
            spec_id="time-spec-2025-01-01-006",
            task_id="task-1-1",
            specs_dir=specs_structure,
            printer=None
        )

        assert task is not None
        assert "metadata" in task
        assert "actual_hours" in task["metadata"]
        assert task["metadata"]["actual_hours"] == 2.5

    def test_get_task_with_dependencies(self, sample_json_spec_with_deps, specs_structure):
        """Test getting task with dependencies."""
        task = get_task(
            spec_id="deps-spec-2025-01-01-003",
            task_id="task-2-2",
            specs_dir=specs_structure,
            printer=None
        )

        assert task is not None
        assert "dependencies" in task
        assert "blocked_by" in task["dependencies"]
        assert "task-2-1" in task["dependencies"]["blocked_by"]

    def test_get_nonexistent_task(self, sample_json_spec_simple, specs_structure):
        """Test getting a nonexistent task."""
        task = get_task(
            spec_id="simple-spec-2025-01-01-001",
            task_id="nonexistent-task",
            specs_dir=specs_structure,
            printer=None
        )

        assert task is None

    def test_get_task_invalid_spec(self, specs_structure):
        """Test getting task from invalid spec."""
        task = get_task(
            spec_id="nonexistent-spec",
            task_id="task-1-1",
            specs_dir=specs_structure,
            printer=None
        )

        assert task is None


@pytest.mark.unit
class TestListPhases:
    """Tests for list_phases function."""

    def test_list_all_phases(self, sample_json_spec_simple, specs_structure):
        """Test listing all phases."""
        phases = list_phases(
            spec_id="simple-spec-2025-01-01-001",
            specs_dir=specs_structure,
            printer=None
        )

        assert phases is not None
        assert len(phases) == 2  # phase-1 and phase-2
        assert phases[0]["id"] == "phase-1"
        assert phases[1]["id"] == "phase-2"

    def test_list_phases_with_progress(self, sample_json_spec_with_time, specs_structure):
        """Test listing phases with progress data."""
        phases = list_phases(
            spec_id="time-spec-2025-01-01-006",
            specs_dir=specs_structure,
            printer=None
        )

        assert phases is not None
        assert len(phases) >= 1
        # Phase-1 should be completed
        phase_1 = next((p for p in phases if p["id"] == "phase-1"), None)
        assert phase_1 is not None
        assert "percentage" in phase_1
        assert "status" in phase_1

    def test_list_phases_invalid_spec(self, specs_structure):
        """Test listing phases from invalid spec."""
        phases = list_phases(
            spec_id="nonexistent-spec",
            specs_dir=specs_structure,
            printer=None
        )

        assert phases is None

    def test_list_phases_empty(self, specs_structure, tmp_path):
        """Test listing phases when there are none."""
        # Create a state with no phases (just root)
        import json
        spec_data = {
            "spec_id": "no-phases-spec",
            "title": "No Phases Spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "status": "pending",
                    "children": []
                }
            }
        }
        # Create both spec file and JSON spec
        spec_file = specs_structure / "active" / "no-phases-spec.json"
        spec_file.write_text(json.dumps(spec_data))
        json_spec_file = specs_structure / "active" / "no-phases-spec.json"
        json_spec_file.write_text(json.dumps(spec_data))

        phases = list_phases(
            spec_id="no-phases-spec",
            specs_dir=specs_structure,
            printer=None
        )

        assert phases == []


@pytest.mark.unit
class TestCheckComplete:
    """Tests for check_complete function."""

    def test_check_completed_spec(self, sample_json_spec_completed, specs_structure):
        """Test checking a fully completed spec."""
        result = check_complete(
            spec_id="completed-spec-2025-01-01-007",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is not None
        assert result["is_complete"] is True
        assert result["incomplete_count"] == 0
        assert len(result["incomplete_tasks"]) == 0

    def test_check_incomplete_spec(self, sample_json_spec_simple, specs_structure):
        """Test checking an incomplete spec."""
        result = check_complete(
            spec_id="simple-spec-2025-01-01-001",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is not None
        assert result["is_complete"] is False
        assert result["incomplete_count"] > 0
        assert len(result["incomplete_tasks"]) > 0

    def test_check_phase_complete(self, sample_json_spec_with_time, specs_structure):
        """Test checking a completed phase."""
        result = check_complete(
            spec_id="time-spec-2025-01-01-006",
            specs_dir=specs_structure,
            phase_id="phase-1",
            printer=None
        )

        assert result is not None
        assert result["is_complete"] is True
        assert result["incomplete_count"] == 0

    def test_check_phase_incomplete(self, sample_json_spec_simple, specs_structure):
        """Test checking an incomplete phase."""
        result = check_complete(
            spec_id="simple-spec-2025-01-01-001",
            specs_dir=specs_structure,
            phase_id="phase-1",
            printer=None
        )

        assert result is not None
        assert result["is_complete"] is False
        assert result["incomplete_count"] == 2  # task-1-1 and task-1-2 are pending

    def test_check_nonexistent_phase(self, sample_json_spec_simple, specs_structure):
        """Test checking a nonexistent phase."""
        result = check_complete(
            spec_id="simple-spec-2025-01-01-001",
            specs_dir=specs_structure,
            phase_id="nonexistent-phase",
            printer=None
        )

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_check_invalid_spec(self, specs_structure):
        """Test checking invalid spec."""
        result = check_complete(
            spec_id="nonexistent-spec",
            specs_dir=specs_structure,
            printer=None
        )

        assert "error" in result


@pytest.mark.unit
class TestPhaseTime:
    """Tests for phase_time function."""

    def test_phase_with_time_data(self, sample_json_spec_with_time, specs_structure):
        """Test calculating time for phase with tracking data."""
        result = phase_time(
            spec_id="time-spec-2025-01-01-006",
            phase_id="phase-1",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is not None
        assert result["phase_id"] == "phase-1"
        assert result["total_estimated"] == 5.0  # 2.0 + 3.0
        assert result["total_actual"] == 5.0  # 2.5 + 2.5
        assert result["variance"] == 0.0
        assert len(result["task_times"]) == 2

    def test_phase_without_time_data(self, sample_json_spec_simple, specs_structure):
        """Test calculating time for phase without tracking data."""
        result = phase_time(
            spec_id="simple-spec-2025-01-01-001",
            phase_id="phase-1",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is not None
        assert result["total_estimated"] >= 0
        assert result["total_actual"] == 0  # No actual hours tracked

    def test_phase_time_variance_positive(self, specs_structure, tmp_path):
        """Test phase time with positive variance (over estimate)."""
        import json
        # Create state with over-budget tasks
        spec_data = {
            "spec_id": "over-spec",
            "hierarchy": {
                "phase-1": {
                    "type": "phase",
                    "title": "Phase 1",
                    "children": ["task-1-1"],
                    "status": "completed"
                },
                "task-1-1": {
                    "type": "task",
                    "title": "Task 1",
                    "parent": "phase-1",
                    "children": [],
                    "status": "completed",
                    "metadata": {
                        "estimated_hours": 2.0,
                        "actual_hours": 3.5
                    }
                }
            }
        }
        # Create both spec file and JSON spec
        spec_file = specs_structure / "active" / "over-spec.json"
        spec_file.write_text(json.dumps(spec_data))
        json_spec_file = specs_structure / "active" / "over-spec.json"
        json_spec_file.write_text(json.dumps(spec_data))

        result = phase_time(
            spec_id="over-spec",
            phase_id="phase-1",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is not None
        assert result["variance"] == 1.5  # 3.5 - 2.0
        assert result["variance_percentage"] == 75.0  # (1.5 / 2.0) * 100

    def test_phase_time_variance_negative(self, specs_structure, tmp_path):
        """Test phase time with negative variance (under estimate)."""
        import json
        spec_data = {
            "spec_id": "under-spec",
            "hierarchy": {
                "phase-1": {
                    "type": "phase",
                    "title": "Phase 1",
                    "children": ["task-1-1"],
                    "status": "completed"
                },
                "task-1-1": {
                    "type": "task",
                    "title": "Task 1",
                    "parent": "phase-1",
                    "children": [],
                    "status": "completed",
                    "metadata": {
                        "estimated_hours": 4.0,
                        "actual_hours": 3.0
                    }
                }
            }
        }
        # Create both spec file and JSON spec
        spec_file = specs_structure / "active" / "under-spec.json"
        spec_file.write_text(json.dumps(spec_data))
        json_spec_file = specs_structure / "active" / "under-spec.json"
        json_spec_file.write_text(json.dumps(spec_data))

        result = phase_time(
            spec_id="under-spec",
            phase_id="phase-1",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is not None
        assert result["variance"] == -1.0  # 3.0 - 4.0

    def test_phase_time_nonexistent_phase(self, sample_json_spec_simple, specs_structure):
        """Test calculating time for nonexistent phase."""
        result = phase_time(
            spec_id="simple-spec-2025-01-01-001",
            phase_id="nonexistent-phase",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is None

    def test_phase_time_invalid_spec(self, specs_structure):
        """Test calculating time for invalid spec."""
        result = phase_time(
            spec_id="nonexistent-spec",
            phase_id="phase-1",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is None


@pytest.mark.unit
class TestListBlockers:
    """Tests for list_blockers function."""

    def test_list_blocked_tasks(self, sample_json_spec_with_blockers, specs_structure):
        """Test listing blocked tasks."""
        blockers = list_blockers(
            spec_id="blocked-spec-2025-01-01-005",
            specs_dir=specs_structure,
            printer=None
        )

        assert blockers is not None
        assert len(blockers) == 2  # task-1-2 and task-2-1 are blocked

        # Check blocker details
        task_1_2_blocker = next((b for b in blockers if b["id"] == "task-1-2"), None)
        assert task_1_2_blocker is not None
        assert task_1_2_blocker["blocker_type"] == "dependency"
        assert task_1_2_blocker["blocker_ticket"] == "OPS-123"
        assert "API" in task_1_2_blocker["blocker_description"]

    def test_list_no_blockers(self, sample_json_spec_simple, specs_structure):
        """Test listing when there are no blocked tasks."""
        blockers = list_blockers(
            spec_id="simple-spec-2025-01-01-001",
            specs_dir=specs_structure,
            printer=None
        )

        assert blockers is not None
        assert len(blockers) == 0

    def test_list_blockers_metadata(self, sample_json_spec_with_blockers, specs_structure):
        """Test blocker metadata is included."""
        blockers = list_blockers(
            spec_id="blocked-spec-2025-01-01-005",
            specs_dir=specs_structure,
            printer=None
        )

        assert blockers is not None
        for blocker in blockers:
            assert "id" in blocker
            assert "title" in blocker
            assert "blocked_at" in blocker
            assert "blocker_type" in blocker
            assert "blocker_description" in blocker

    def test_list_blockers_invalid_spec(self, specs_structure):
        """Test listing blockers for invalid spec."""
        blockers = list_blockers(
            spec_id="nonexistent-spec",
            specs_dir=specs_structure,
            printer=None
        )

        assert blockers is None


@pytest.mark.unit
class TestGetJournalEntries:
    """Tests for get_journal_entries function."""

    def test_get_all_journal_entries(self, specs_structure, tmp_path):
        """Test getting all journal entries from a spec."""
        import json
        # Create spec with journal entries
        spec_data = {
            "spec_id": "journal-spec",
            "title": "Journal Test Spec",
            "hierarchy": {
                "spec-root": {"type": "spec", "status": "pending", "children": []},
                "task-1-1": {"type": "task", "title": "Task 1", "status": "completed", "parent": "spec-root", "children": []}
            },
            "journal": [
                {
                    "timestamp": "2025-01-01T10:00:00+00:00",
                    "entry_type": "decision",
                    "title": "Entry 1",
                    "author": "claude-code",
                    "content": "First entry content",
                    "metadata": {},
                    "task_id": "task-1-1"
                },
                {
                    "timestamp": "2025-01-01T11:00:00+00:00",
                    "entry_type": "note",
                    "title": "Entry 2",
                    "author": "claude-code",
                    "content": "Second entry content",
                    "metadata": {}
                },
                {
                    "timestamp": "2025-01-01T12:00:00+00:00",
                    "entry_type": "status_change",
                    "title": "Entry 3",
                    "author": "claude-code",
                    "content": "Third entry content",
                    "metadata": {},
                    "task_id": "task-1-1"
                }
            ]
        }
        spec_file = specs_structure / "active" / "journal-spec.json"
        spec_file.write_text(json.dumps(spec_data))

        entries = get_journal_entries(
            spec_id="journal-spec",
            specs_dir=specs_structure,
            printer=None
        )

        assert entries is not None
        assert len(entries) == 3
        assert entries[0]["title"] == "Entry 1"
        assert entries[1]["title"] == "Entry 2"
        assert entries[2]["title"] == "Entry 3"

    def test_get_journal_entries_filtered_by_task(self, specs_structure, tmp_path):
        """Test getting journal entries filtered by task_id."""
        import json
        spec_data = {
            "spec_id": "journal-spec",
            "title": "Journal Test Spec",
            "hierarchy": {
                "spec-root": {"type": "spec", "status": "pending", "children": []},
                "task-1-1": {"type": "task", "title": "Task 1", "status": "completed", "parent": "spec-root", "children": []}
            },
            "journal": [
                {
                    "timestamp": "2025-01-01T10:00:00+00:00",
                    "entry_type": "decision",
                    "title": "Task 1 Entry",
                    "author": "claude-code",
                    "content": "Entry for task 1",
                    "metadata": {},
                    "task_id": "task-1-1"
                },
                {
                    "timestamp": "2025-01-01T11:00:00+00:00",
                    "entry_type": "note",
                    "title": "General Entry",
                    "author": "claude-code",
                    "content": "General entry",
                    "metadata": {}
                },
                {
                    "timestamp": "2025-01-01T12:00:00+00:00",
                    "entry_type": "status_change",
                    "title": "Task 1 Status",
                    "author": "claude-code",
                    "content": "Another entry for task 1",
                    "metadata": {},
                    "task_id": "task-1-1"
                }
            ]
        }
        spec_file = specs_structure / "active" / "journal-spec.json"
        spec_file.write_text(json.dumps(spec_data))

        entries = get_journal_entries(
            spec_id="journal-spec",
            specs_dir=specs_structure,
            task_id="task-1-1",
            printer=None
        )

        assert entries is not None
        assert len(entries) == 2  # Only entries with task_id="task-1-1"
        assert all(e.get("task_id") == "task-1-1" for e in entries)
        assert entries[0]["title"] == "Task 1 Entry"
        assert entries[1]["title"] == "Task 1 Status"

    def test_get_journal_entries_empty(self, specs_structure, tmp_path):
        """Test getting journal entries when there are none."""
        import json
        spec_data = {
            "spec_id": "no-journal-spec",
            "title": "No Journal Spec",
            "hierarchy": {
                "spec-root": {"type": "spec", "status": "pending", "children": []}
            },
            "journal": []
        }
        spec_file = specs_structure / "active" / "no-journal-spec.json"
        spec_file.write_text(json.dumps(spec_data))

        entries = get_journal_entries(
            spec_id="no-journal-spec",
            specs_dir=specs_structure,
            printer=None
        )

        assert entries is not None
        assert len(entries) == 0

    def test_get_journal_entries_no_matching_task(self, specs_structure, tmp_path):
        """Test filtering by task_id that doesn't exist in journal."""
        import json
        spec_data = {
            "spec_id": "journal-spec",
            "title": "Journal Test Spec",
            "hierarchy": {
                "spec-root": {"type": "spec", "status": "pending", "children": []}
            },
            "journal": [
                {
                    "timestamp": "2025-01-01T10:00:00+00:00",
                    "entry_type": "note",
                    "title": "General Entry",
                    "author": "claude-code",
                    "content": "General entry",
                    "metadata": {}
                }
            ]
        }
        spec_file = specs_structure / "active" / "journal-spec.json"
        spec_file.write_text(json.dumps(spec_data))

        entries = get_journal_entries(
            spec_id="journal-spec",
            specs_dir=specs_structure,
            task_id="nonexistent-task",
            printer=None
        )

        assert entries is not None
        assert len(entries) == 0

    def test_get_journal_entries_invalid_spec(self, specs_structure):
        """Test getting journal entries from invalid spec."""
        entries = get_journal_entries(
            spec_id="nonexistent-spec",
            specs_dir=specs_structure,
            printer=None
        )

        assert entries is None


@pytest.mark.unit
class TestGetTaskJournal:
    """Tests for get_task_journal function."""

    def test_get_task_journal(self, specs_structure, tmp_path):
        """Test getting journal entries for a specific task."""
        import json
        spec_data = {
            "spec_id": "journal-spec",
            "title": "Journal Test Spec",
            "hierarchy": {
                "spec-root": {"type": "spec", "status": "pending", "children": []},
                "task-1-1": {"type": "task", "title": "Task 1", "status": "completed", "parent": "spec-root", "children": []}
            },
            "journal": [
                {
                    "timestamp": "2025-01-01T10:00:00+00:00",
                    "entry_type": "decision",
                    "title": "Task Entry",
                    "author": "claude-code",
                    "content": "Task-specific entry",
                    "metadata": {},
                    "task_id": "task-1-1"
                }
            ]
        }
        spec_file = specs_structure / "active" / "journal-spec.json"
        spec_file.write_text(json.dumps(spec_data))

        entries = get_task_journal(
            spec_id="journal-spec",
            task_id="task-1-1",
            specs_dir=specs_structure,
            printer=None
        )

        assert entries is not None
        assert len(entries) == 1
        assert entries[0]["task_id"] == "task-1-1"


@pytest.mark.unit
class TestGetTaskWithJournal:
    """Tests for get_task with include_journal parameter."""

    def test_get_task_with_journal(self, specs_structure, tmp_path):
        """Test getting task with journal entries included."""
        import json
        spec_data = {
            "spec_id": "journal-task-spec",
            "title": "Journal Task Test",
            "hierarchy": {
                "spec-root": {"type": "spec", "status": "pending", "children": ["task-1-1"]},
                "task-1-1": {
                    "type": "task",
                    "title": "Task 1",
                    "status": "completed",
                    "parent": "spec-root",
                    "children": [],
                    "metadata": {}
                }
            },
            "journal": [
                {
                    "timestamp": "2025-01-01T10:00:00+00:00",
                    "entry_type": "decision",
                    "title": "Task Decision",
                    "author": "claude-code",
                    "content": "Decision content",
                    "metadata": {},
                    "task_id": "task-1-1"
                },
                {
                    "timestamp": "2025-01-01T11:00:00+00:00",
                    "entry_type": "status_change",
                    "title": "Task Completed",
                    "author": "claude-code",
                    "content": "Status change",
                    "metadata": {},
                    "task_id": "task-1-1"
                }
            ]
        }
        spec_file = specs_structure / "active" / "journal-task-spec.json"
        spec_file.write_text(json.dumps(spec_data))

        task = get_task(
            spec_id="journal-task-spec",
            task_id="task-1-1",
            specs_dir=specs_structure,
            printer=None,
            include_journal=True
        )

        assert task is not None
        assert "journal_entries" in task
        assert len(task["journal_entries"]) == 2
        assert task["journal_entries"][0]["title"] == "Task Decision"
        assert task["journal_entries"][1]["title"] == "Task Completed"

    def test_get_task_without_journal(self, specs_structure, tmp_path):
        """Test getting task without journal entries (default behavior)."""
        import json
        spec_data = {
            "spec_id": "journal-task-spec",
            "title": "Journal Task Test",
            "hierarchy": {
                "spec-root": {"type": "spec", "status": "pending", "children": ["task-1-1"]},
                "task-1-1": {
                    "type": "task",
                    "title": "Task 1",
                    "status": "completed",
                    "parent": "spec-root",
                    "children": [],
                    "metadata": {}
                }
            },
            "journal": [
                {
                    "timestamp": "2025-01-01T10:00:00+00:00",
                    "entry_type": "decision",
                    "title": "Task Decision",
                    "author": "claude-code",
                    "content": "Decision content",
                    "metadata": {},
                    "task_id": "task-1-1"
                }
            ]
        }
        spec_file = specs_structure / "active" / "journal-task-spec.json"
        spec_file.write_text(json.dumps(spec_data))

        task = get_task(
            spec_id="journal-task-spec",
            task_id="task-1-1",
            specs_dir=specs_structure,
            printer=None,
            include_journal=False
        )

        assert task is not None
        assert "journal_entries" not in task

    def test_get_task_with_journal_no_entries(self, specs_structure, tmp_path):
        """Test getting task with journal when there are no entries for that task."""
        import json
        spec_data = {
            "spec_id": "journal-task-spec",
            "title": "Journal Task Test",
            "hierarchy": {
                "spec-root": {"type": "spec", "status": "pending", "children": ["task-1-1"]},
                "task-1-1": {
                    "type": "task",
                    "title": "Task 1",
                    "status": "completed",
                    "parent": "spec-root",
                    "children": [],
                    "metadata": {}
                }
            },
            "journal": []
        }
        spec_file = specs_structure / "active" / "journal-task-spec.json"
        spec_file.write_text(json.dumps(spec_data))

        task = get_task(
            spec_id="journal-task-spec",
            task_id="task-1-1",
            specs_dir=specs_structure,
            printer=None,
            include_journal=True
        )

        assert task is not None
        assert "journal_entries" in task
        assert len(task["journal_entries"]) == 0
