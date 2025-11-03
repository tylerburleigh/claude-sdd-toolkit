"""
Tests for workflow.py - Complete task workflow operations.
"""
import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from claude_skills.sdd_update.workflow import complete_task_workflow
from claude_skills.common.printer import PrettyPrinter
from claude_skills.common.spec import load_json_spec


class TestCompleteTaskWorkflow:
    """Test complete_task_workflow() function."""

    def _create_test_spec(self, spec_id: str, hierarchy: dict, specs_dir: Path) -> Path:
        """Helper to create a test spec file."""
        # Create active subdirectory (load_json_spec expects this structure)
        active_dir = specs_dir / "active"
        active_dir.mkdir(parents=True, exist_ok=True)

        spec_file = active_dir / f"{spec_id}.json"
        spec_data = {
            "spec_id": spec_id,
            "generated": "2025-10-27T10:00:00Z",
            "hierarchy": hierarchy
        }
        with open(spec_file, 'w') as f:
            json.dump(spec_data, f, indent=2)
        return spec_file

    def test_complete_task_workflow_auto_calculates_time(self):
        """Test that completing a task with timestamps automatically populates actual_hours."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)

            # Create timestamp 2 hours ago for started_at
            now = datetime.now(timezone.utc)
            two_hours_ago = now - timedelta(hours=2)
            started_at_timestamp = two_hours_ago.isoformat().replace("+00:00", "Z")

            # Create spec with task in in_progress status with started_at timestamp
            hierarchy = {
                "spec-root": {
                    "type": "spec",
                    "title": "Test Spec",
                    "status": "in_progress",
                    "parent": None,
                    "children": ["task-1"],
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "metadata": {}
                },
                "task-1": {
                    "type": "task",
                    "title": "Test Task",
                    "status": "in_progress",
                    "parent": "spec-root",
                    "children": [],
                    "dependencies": {
                        "blocks": [],
                        "blocked_by": [],
                        "depends": []
                    },
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "metadata": {
                        "started_at": started_at_timestamp
                        # Note: No actual_hours set initially
                    }
                }
            }
            self._create_test_spec("test-workflow-001", hierarchy, specs_dir)

            # Complete the task WITHOUT providing actual_hours
            printer = PrettyPrinter()
            result = complete_task_workflow(
                spec_id="test-workflow-001",
                task_id="task-1",
                specs_dir=specs_dir,
                actual_hours=None,  # Not provided - should auto-calculate
                note="Task completed",
                dry_run=False,
                printer=printer
            )

            # Verify workflow succeeded
            assert result is not None
            assert result["dry_run"] is False
            assert result["task_id"] == "task-1"

            # Reload spec to verify changes
            updated_spec = load_json_spec("test-workflow-001", specs_dir)
            assert updated_spec is not None

            task = updated_spec["hierarchy"]["task-1"]
            task_metadata = task.get("metadata", {})

            # Verify task was completed
            assert task["status"] == "completed"

            # Verify timestamps exist
            assert "started_at" in task_metadata
            assert "completed_at" in task_metadata

            # KEY ASSERTION: Verify actual_hours was automatically calculated
            assert "actual_hours" in task_metadata
            assert task_metadata["actual_hours"] is not None
            assert task_metadata["actual_hours"] > 0

            # Verify calculated time is approximately 2 hours (with reasonable tolerance)
            # Allow range of 1.9-2.1 hours to account for test execution time
            assert 1.9 <= task_metadata["actual_hours"] <= 2.1, \
                f"Expected ~2 hours, got {task_metadata['actual_hours']}"

    def test_complete_task_workflow_manual_hours_not_overridden(self):
        """Test that manually provided actual_hours is not overridden by auto-calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)

            # Create timestamp 2 hours ago for started_at
            now = datetime.now(timezone.utc)
            two_hours_ago = now - timedelta(hours=2)
            started_at_timestamp = two_hours_ago.isoformat().replace("+00:00", "Z")

            # Create spec with task in in_progress status with started_at timestamp
            hierarchy = {
                "spec-root": {
                    "type": "spec",
                    "title": "Test Spec",
                    "status": "in_progress",
                    "parent": None,
                    "children": ["task-1"],
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "metadata": {}
                },
                "task-1": {
                    "type": "task",
                    "title": "Test Task",
                    "status": "in_progress",
                    "parent": "spec-root",
                    "children": [],
                    "dependencies": {
                        "blocks": [],
                        "blocked_by": [],
                        "depends": []
                    },
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "metadata": {
                        "started_at": started_at_timestamp
                    }
                }
            }
            self._create_test_spec("test-workflow-002", hierarchy, specs_dir)

            # Complete the task WITH manual actual_hours
            printer = PrettyPrinter()
            manual_hours = 3.5
            result = complete_task_workflow(
                spec_id="test-workflow-002",
                task_id="task-1",
                specs_dir=specs_dir,
                actual_hours=manual_hours,  # Manually provided
                note="Task completed with manual hours",
                dry_run=False,
                printer=printer
            )

            # Verify workflow succeeded
            assert result is not None

            # Reload spec to verify changes
            updated_spec = load_json_spec("test-workflow-002", specs_dir)
            assert updated_spec is not None

            task = updated_spec["hierarchy"]["task-1"]
            task_metadata = task.get("metadata", {})

            # Verify task was completed
            assert task["status"] == "completed"

            # Verify manual hours was used (not auto-calculated ~2 hours)
            assert "actual_hours" in task_metadata
            assert task_metadata["actual_hours"] == manual_hours

    def test_complete_task_workflow_no_started_at_no_calculation(self):
        """Test that no auto-calculation occurs when started_at is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)

            # Create spec with task in pending status (no started_at timestamp)
            hierarchy = {
                "spec-root": {
                    "type": "spec",
                    "title": "Test Spec",
                    "status": "in_progress",
                    "parent": None,
                    "children": ["task-1"],
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "metadata": {}
                },
                "task-1": {
                    "type": "task",
                    "title": "Test Task",
                    "status": "pending",
                    "parent": "spec-root",
                    "children": [],
                    "dependencies": {
                        "blocks": [],
                        "blocked_by": [],
                        "depends": []
                    },
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "metadata": {}
                    # Note: No started_at timestamp
                }
            }
            self._create_test_spec("test-workflow-003", hierarchy, specs_dir)

            # Complete the task WITHOUT providing actual_hours
            printer = PrettyPrinter()
            result = complete_task_workflow(
                spec_id="test-workflow-003",
                task_id="task-1",
                specs_dir=specs_dir,
                actual_hours=None,  # Not provided
                note="Task completed without timing",
                dry_run=False,
                printer=printer
            )

            # Verify workflow succeeded
            assert result is not None

            # Reload spec to verify changes
            updated_spec = load_json_spec("test-workflow-003", specs_dir)
            assert updated_spec is not None

            task = updated_spec["hierarchy"]["task-1"]
            task_metadata = task.get("metadata", {})

            # Verify task was completed
            assert task["status"] == "completed"

            # Verify no actual_hours was set (no auto-calculation without started_at)
            assert "actual_hours" not in task_metadata or task_metadata.get("actual_hours") is None

    def test_complete_task_workflow_journals_parent_nodes(self):
        """Test that completing a task journals auto-completed parent nodes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)

            # Create spec with a phase containing 2 tasks
            hierarchy = {
                "spec-root": {
                    "type": "spec",
                    "title": "Test Spec",
                    "status": "in_progress",
                    "parent": None,
                    "children": ["phase-1"],
                    "total_tasks": 2,
                    "completed_tasks": 0,
                    "metadata": {}
                },
                "phase-1": {
                    "type": "phase",
                    "title": "Phase 1",
                    "status": "in_progress",
                    "parent": "spec-root",
                    "children": ["task-1-1", "task-1-2"],
                    "total_tasks": 2,
                    "completed_tasks": 0,
                    "metadata": {}
                },
                "task-1-1": {
                    "type": "task",
                    "title": "Task 1.1",
                    "status": "completed",
                    "parent": "phase-1",
                    "children": [],
                    "dependencies": {"blocks": [], "blocked_by": [], "depends": []},
                    "total_tasks": 1,
                    "completed_tasks": 1,
                    "metadata": {"completed_at": "2025-01-01T10:00:00Z"}
                },
                "task-1-2": {
                    "type": "task",
                    "title": "Task 1.2",
                    "status": "in_progress",
                    "parent": "phase-1",
                    "children": [],
                    "dependencies": {"blocks": [], "blocked_by": [], "depends": []},
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "metadata": {"started_at": "2025-01-01T10:00:00Z"}
                }
            }
            self._create_test_spec("test-workflow-004", hierarchy, specs_dir)

            # Complete the last task in phase-1 (should auto-complete phase-1)
            printer = PrettyPrinter()
            result = complete_task_workflow(
                spec_id="test-workflow-004",
                task_id="task-1-2",
                specs_dir=specs_dir,
                note="Completed final task in phase",
                dry_run=False,
                printer=printer
            )

            # Verify workflow succeeded
            assert result is not None

            # Reload spec to verify changes
            updated_spec = load_json_spec("test-workflow-004", specs_dir)
            assert updated_spec is not None

            # Verify phase-1 was auto-completed
            phase_1 = updated_spec["hierarchy"]["phase-1"]
            assert phase_1["status"] == "completed"

            # Verify journal entries were created
            journal = updated_spec.get("journal", [])
            assert len(journal) >= 2  # At least one for task + one for phase

            # Find journal entries
            task_entry = None
            phase_entry = None
            for entry in journal:
                if entry.get("task_id") == "task-1-2":
                    task_entry = entry
                elif entry.get("task_id") == "phase-1":
                    phase_entry = entry

            # Verify task journal entry exists
            assert task_entry is not None
            assert "Task" in task_entry.get("title", "")

            # Verify phase journal entry exists (auto-journaled)
            assert phase_entry is not None
            assert "Phase Completed" in phase_entry.get("title", "")
            assert "phase-1" in phase_entry.get("content", "")

            # Verify phase metadata is cleared of needs_journaling flag
            assert phase_1.get("metadata", {}).get("needs_journaling") is not True

    def test_complete_task_workflow_journals_multiple_parent_levels(self):
        """Test that completing a task journals parent nodes at multiple hierarchy levels."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)

            # Create spec with nested hierarchy: phase -> group -> task
            hierarchy = {
                "spec-root": {
                    "type": "spec",
                    "title": "Test Spec",
                    "status": "in_progress",
                    "parent": None,
                    "children": ["phase-1"],
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "metadata": {}
                },
                "phase-1": {
                    "type": "phase",
                    "title": "Phase 1",
                    "status": "in_progress",
                    "parent": "spec-root",
                    "children": ["group-1"],
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "metadata": {}
                },
                "group-1": {
                    "type": "group",
                    "title": "Group 1",
                    "status": "in_progress",
                    "parent": "phase-1",
                    "children": ["task-1"],
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "metadata": {}
                },
                "task-1": {
                    "type": "task",
                    "title": "Task 1",
                    "status": "in_progress",
                    "parent": "group-1",
                    "children": [],
                    "dependencies": {"blocks": [], "blocked_by": [], "depends": []},
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "metadata": {"started_at": "2025-01-01T10:00:00Z"}
                }
            }
            self._create_test_spec("test-workflow-005", hierarchy, specs_dir)

            # Complete the only task (should auto-complete group AND phase)
            printer = PrettyPrinter()
            result = complete_task_workflow(
                spec_id="test-workflow-005",
                task_id="task-1",
                specs_dir=specs_dir,
                note="Completed only task",
                dry_run=False,
                printer=printer
            )

            # Verify workflow succeeded
            assert result is not None

            # Reload spec to verify changes
            updated_spec = load_json_spec("test-workflow-005", specs_dir)
            assert updated_spec is not None

            # Verify both parent levels were auto-completed
            group_1 = updated_spec["hierarchy"]["group-1"]
            phase_1 = updated_spec["hierarchy"]["phase-1"]
            assert group_1["status"] == "completed"
            assert phase_1["status"] == "completed"

            # Verify journal entries were created for all levels
            journal = updated_spec.get("journal", [])
            assert len(journal) >= 3  # task + group + phase

            # Find journal entries by task_id
            task_entry = None
            group_entry = None
            phase_entry = None
            for entry in journal:
                tid = entry.get("task_id")
                if tid == "task-1":
                    task_entry = entry
                elif tid == "group-1":
                    group_entry = entry
                elif tid == "phase-1":
                    phase_entry = entry

            # Verify all entries exist
            assert task_entry is not None
            assert group_entry is not None
            assert phase_entry is not None

            # Verify parent entries have correct content
            assert "Group Completed" in group_entry.get("title", "")
            assert "Phase Completed" in phase_entry.get("title", "")

    def test_complete_task_workflow_does_not_journal_already_completed_parents(self):
        """Test that already-completed parent nodes don't get duplicate journal entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)

            # Create spec where phase is already completed (manually)
            hierarchy = {
                "spec-root": {
                    "type": "spec",
                    "title": "Test Spec",
                    "status": "completed",
                    "parent": None,
                    "children": ["phase-1"],
                    "total_tasks": 1,
                    "completed_tasks": 1,
                    "metadata": {}
                },
                "phase-1": {
                    "type": "phase",
                    "title": "Phase 1",
                    "status": "completed",  # Already completed
                    "parent": "spec-root",
                    "children": ["task-1"],
                    "total_tasks": 1,
                    "completed_tasks": 1,
                    "metadata": {
                        "completed_at": "2025-01-01T09:00:00Z",
                        # Note: NO needs_journaling flag (already journaled)
                    }
                },
                "task-1": {
                    "type": "task",
                    "title": "Task 1",
                    "status": "completed",
                    "parent": "phase-1",
                    "children": [],
                    "dependencies": {"blocks": [], "blocked_by": [], "depends": []},
                    "total_tasks": 1,
                    "completed_tasks": 1,
                    "metadata": {"completed_at": "2025-01-01T10:00:00Z"}
                }
            }

            # Pre-populate with existing journal entry for phase
            spec_data = {
                "spec_id": "test-workflow-006",
                "generated": "2025-10-27T10:00:00Z",
                "hierarchy": hierarchy,
                "journal": [
                    {
                        "id": "journal-001",
                        "timestamp": "2025-01-01T09:00:00Z",
                        "title": "Phase Completed: Phase 1",
                        "content": "Phase already completed",
                        "task_id": "phase-1",
                        "entry_type": "status_change",
                        "author": "test-user"
                    }
                ]
            }

            active_dir = specs_dir / "active"
            active_dir.mkdir(parents=True, exist_ok=True)
            spec_file = active_dir / "test-workflow-006.json"
            with open(spec_file, 'w') as f:
                json.dump(spec_data, f, indent=2)

            # Complete task again (shouldn't create duplicate phase journal)
            printer = PrettyPrinter()
            result = complete_task_workflow(
                spec_id="test-workflow-006",
                task_id="task-1",
                specs_dir=specs_dir,
                note="Re-completing task",
                dry_run=False,
                printer=printer
            )

            # Verify workflow succeeded
            assert result is not None

            # Reload spec to verify changes
            updated_spec = load_json_spec("test-workflow-006", specs_dir)
            assert updated_spec is not None

            # Verify journal entries
            journal = updated_spec.get("journal", [])

            # Count phase-1 entries (should only be 1 - the original)
            phase_entries = [e for e in journal if e.get("task_id") == "phase-1"]
            assert len(phase_entries) == 1
            assert phase_entries[0]["id"] == "journal-001"  # Original entry
