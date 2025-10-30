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
