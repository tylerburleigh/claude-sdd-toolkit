"""
Tests for status.py - Task status update operations.
"""
import pytest
import tempfile
import json
import time
from pathlib import Path
from datetime import datetime

from claude_skills.sdd_update.status import update_task_status
from claude_skills.common.spec import load_json_spec
from claude_skills.common.printer import PrettyPrinter


class TestUpdateTaskStatus:
    """Test update_task_status() function."""

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

    def test_started_at_resets_on_each_in_progress_transition(self):
        """Test moving task to in_progress multiple times updates started_at each time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)

            # Create spec with task in pending status
            hierarchy = {
                "spec-root": {
                    "type": "spec",
                    "title": "Test Spec",
                    "status": "pending",
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
                }
            }
            self._create_test_spec("test-status-001", hierarchy, specs_dir)

            printer = PrettyPrinter()

            # Step 1: Mark task as in_progress (first time)
            result = update_task_status(
                spec_id="test-status-001",
                task_id="task-1",
                new_status="in_progress",
                specs_dir=specs_dir,
                note="Starting work",
                dry_run=False,
                printer=printer
            )
            assert result is True

            # Get first started_at timestamp
            spec_data = load_json_spec("test-status-001", specs_dir)
            task = spec_data["hierarchy"]["task-1"]
            started_at_1 = task["metadata"].get("started_at")
            assert started_at_1 is not None

            # Verify timestamp format (ISO 8601)
            datetime.fromisoformat(started_at_1.replace('Z', '+00:00'))

            # Small delay to ensure timestamps differ
            time.sleep(0.01)

            # Step 2: Mark task as blocked
            result = update_task_status(
                spec_id="test-status-001",
                task_id="task-1",
                new_status="blocked",
                specs_dir=specs_dir,
                note="Waiting on dependency",
                dry_run=False,
                printer=printer
            )
            assert result is True

            # Verify started_at remains unchanged when blocked
            spec_data = load_json_spec("test-status-001", specs_dir)
            task = spec_data["hierarchy"]["task-1"]
            started_at_blocked = task["metadata"].get("started_at")
            assert started_at_blocked == started_at_1

            # Small delay to ensure timestamps differ
            time.sleep(0.01)

            # Step 3: Mark task as in_progress again (second time)
            result = update_task_status(
                spec_id="test-status-001",
                task_id="task-1",
                new_status="in_progress",
                specs_dir=specs_dir,
                note="Resuming work",
                dry_run=False,
                printer=printer
            )
            assert result is True

            # Get second started_at timestamp
            spec_data = load_json_spec("test-status-001", specs_dir)
            task = spec_data["hierarchy"]["task-1"]
            started_at_2 = task["metadata"].get("started_at")
            assert started_at_2 is not None

            # KEY ASSERTION: Verify timestamp was updated (t2 > t1)
            assert started_at_2 != started_at_1, \
                f"started_at should be updated on second in_progress transition. Was: {started_at_1}, Now: {started_at_2}"

            # Parse timestamps and verify t2 is after t1
            time_1 = datetime.fromisoformat(started_at_1.replace('Z', '+00:00'))
            time_2 = datetime.fromisoformat(started_at_2.replace('Z', '+00:00'))
            assert time_2 > time_1, \
                f"Second started_at ({time_2}) should be after first ({time_1})"

    def test_started_at_set_on_first_in_progress(self):
        """Test that started_at is set when task first moves to in_progress."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)

            # Create spec with task in pending status
            hierarchy = {
                "spec-root": {
                    "type": "spec",
                    "title": "Test Spec",
                    "status": "pending",
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
                }
            }
            self._create_test_spec("test-status-002", hierarchy, specs_dir)

            printer = PrettyPrinter()

            # Verify no started_at exists initially
            spec_data = load_json_spec("test-status-002", specs_dir)
            task = spec_data["hierarchy"]["task-1"]
            assert "started_at" not in task["metadata"]

            # Mark task as in_progress
            result = update_task_status(
                spec_id="test-status-002",
                task_id="task-1",
                new_status="in_progress",
                specs_dir=specs_dir,
                dry_run=False,
                printer=printer
            )
            assert result is True

            # Verify started_at is now set
            spec_data = load_json_spec("test-status-002", specs_dir)
            task = spec_data["hierarchy"]["task-1"]
            assert "started_at" in task["metadata"]
            assert task["metadata"]["started_at"] is not None

            # Verify timestamp format
            started_at = task["metadata"]["started_at"]
            datetime.fromisoformat(started_at.replace('Z', '+00:00'))

    def test_completed_at_set_on_completion(self):
        """Test that completed_at is set when task moves to completed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            specs_dir = Path(tmpdir)

            # Create spec with task in in_progress status
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
                        "started_at": "2025-10-30T10:00:00Z"
                    }
                }
            }
            self._create_test_spec("test-status-003", hierarchy, specs_dir)

            printer = PrettyPrinter()

            # Verify no completed_at exists initially
            spec_data = load_json_spec("test-status-003", specs_dir)
            task = spec_data["hierarchy"]["task-1"]
            assert "completed_at" not in task["metadata"]

            # Mark task as completed
            result = update_task_status(
                spec_id="test-status-003",
                task_id="task-1",
                new_status="completed",
                specs_dir=specs_dir,
                dry_run=False,
                printer=printer
            )
            assert result is True

            # Verify completed_at is now set
            spec_data = load_json_spec("test-status-003", specs_dir)
            task = spec_data["hierarchy"]["task-1"]
            assert "completed_at" in task["metadata"]
            assert task["metadata"]["completed_at"] is not None

            # Verify timestamp format
            completed_at = task["metadata"]["completed_at"]
            datetime.fromisoformat(completed_at.replace('Z', '+00:00'))

            # Verify needs_journaling flag is set
            assert task["metadata"].get("needs_journaling") is True
