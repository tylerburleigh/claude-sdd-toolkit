"""
Tests for move_node() function in sdd_spec_mod module.
"""

import pytest
from claude_skills.sdd_spec_mod.modification import move_node, add_node


def create_minimal_spec():
    """Create a minimal valid spec structure for testing."""
    return {
        "spec_id": "test-spec-001",
        "title": "Test Specification",
        "hierarchy": {
            "spec-root": {
                "type": "spec",
                "title": "Test Specification",
                "status": "in_progress",
                "parent": None,
                "children": ["phase-1", "phase-2"],
                "total_tasks": 0,
                "completed_tasks": 0,
                "metadata": {}
            },
            "phase-1": {
                "type": "phase",
                "title": "Phase 1",
                "status": "pending",
                "parent": "spec-root",
                "children": [],
                "total_tasks": 0,
                "completed_tasks": 0,
                "metadata": {}
            },
            "phase-2": {
                "type": "phase",
                "title": "Phase 2",
                "status": "pending",
                "parent": "spec-root",
                "children": [],
                "total_tasks": 0,
                "completed_tasks": 0,
                "metadata": {}
            }
        }
    }


class TestMoveNode:
    """Test suite for move_node() function."""

    def test_move_task_between_phases(self):
        """Test moving a task from one phase to another."""
        spec = create_minimal_spec()

        # Add task to phase-1
        task_data = {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Implement feature X"
        }
        add_node(spec, "phase-1", task_data)

        # Verify initial state
        assert "task-1-1" in spec["hierarchy"]["phase-1"]["children"]
        assert spec["hierarchy"]["task-1-1"]["parent"] == "phase-1"
        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 1
        assert spec["hierarchy"]["phase-2"]["total_tasks"] == 0

        # Move task to phase-2
        result = move_node(spec, "task-1-1", "phase-2")

        assert result["success"] is True
        assert result["old_parent_id"] == "phase-1"
        assert result["new_parent_id"] == "phase-2"

        # Verify task was moved
        assert "task-1-1" not in spec["hierarchy"]["phase-1"]["children"]
        assert "task-1-1" in spec["hierarchy"]["phase-2"]["children"]
        assert spec["hierarchy"]["task-1-1"]["parent"] == "phase-2"

        # Verify task counts updated
        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 0
        assert spec["hierarchy"]["phase-2"]["total_tasks"] == 1

    def test_move_task_with_position(self):
        """Test moving a task with a specific position."""
        spec = create_minimal_spec()

        # Add three tasks to phase-1
        for i in range(1, 4):
            add_node(spec, "phase-1", {
                "node_id": f"task-1-{i}",
                "type": "task",
                "title": f"Task {i}"
            })

        # Add one task to phase-2
        add_node(spec, "phase-2", {
            "node_id": "task-2-1",
            "type": "task",
            "title": "Task 2-1"
        })

        # Move task-1-2 to phase-2 at position 0 (before task-2-1)
        result = move_node(spec, "task-1-2", "phase-2", position=0)

        assert result["success"] is True
        phase2_children = spec["hierarchy"]["phase-2"]["children"]
        assert phase2_children[0] == "task-1-2"
        assert phase2_children[1] == "task-2-1"

    def test_move_task_with_subtasks(self):
        """Test moving a task that has subtasks (moves entire subtree)."""
        spec = create_minimal_spec()

        # Add task with subtasks to phase-1
        add_node(spec, "phase-1", {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Task with subtasks"
        })
        add_node(spec, "task-1-1", {
            "node_id": "task-1-1-1",
            "type": "subtask",
            "title": "Subtask 1"
        })
        add_node(spec, "task-1-1", {
            "node_id": "task-1-1-2",
            "type": "subtask",
            "title": "Subtask 2"
        })

        # Verify initial counts (1 task + 2 subtasks = 3 total)
        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 3
        assert spec["hierarchy"]["phase-2"]["total_tasks"] == 0

        # Move task-1-1 (and its subtasks) to phase-2
        result = move_node(spec, "task-1-1", "phase-2")

        assert result["success"] is True

        # Verify entire subtree moved
        assert "task-1-1" in spec["hierarchy"]["phase-2"]["children"]
        assert spec["hierarchy"]["task-1-1"]["parent"] == "phase-2"
        assert spec["hierarchy"]["task-1-1-1"]["parent"] == "task-1-1"  # Subtasks unchanged
        assert spec["hierarchy"]["task-1-1-2"]["parent"] == "task-1-1"

        # Verify task counts updated correctly
        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 0
        assert spec["hierarchy"]["phase-2"]["total_tasks"] == 3

    def test_move_prevents_circular_dependency(self):
        """Test that moving a node under its own descendant is prevented."""
        spec = create_minimal_spec()

        # Create hierarchy: phase-1 -> task-1-1 -> task-1-1-1
        add_node(spec, "phase-1", {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Parent task"
        })
        add_node(spec, "task-1-1", {
            "node_id": "task-1-1-1",
            "type": "subtask",
            "title": "Child subtask"
        })

        # Try to move task-1-1 under its own child task-1-1-1 (should fail)
        result = move_node(spec, "task-1-1", "task-1-1-1")

        assert result["success"] is False
        assert "circular dependency" in result["message"].lower()

        # Verify nothing changed
        assert spec["hierarchy"]["task-1-1"]["parent"] == "phase-1"
        assert spec["hierarchy"]["task-1-1-1"]["parent"] == "task-1-1"

    def test_move_to_same_parent_without_position(self):
        """Test that moving to same parent without position fails."""
        spec = create_minimal_spec()

        add_node(spec, "phase-1", {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Task 1"
        })

        # Try to move to same parent without specifying position
        result = move_node(spec, "task-1-1", "phase-1")

        assert result["success"] is False
        assert "already a child" in result["message"].lower()

    def test_reposition_within_same_parent(self):
        """Test repositioning a task within the same parent."""
        spec = create_minimal_spec()

        # Add three tasks to phase-1
        for i in range(1, 4):
            add_node(spec, "phase-1", {
                "node_id": f"task-1-{i}",
                "type": "task",
                "title": f"Task {i}"
            })

        # Verify initial order
        initial_children = spec["hierarchy"]["phase-1"]["children"].copy()
        assert initial_children == ["task-1-1", "task-1-2", "task-1-3"]

        # Move task-1-3 to position 0
        result = move_node(spec, "task-1-3", "phase-1", position=0)

        assert result["success"] is True
        new_children = spec["hierarchy"]["phase-1"]["children"]
        assert new_children == ["task-1-3", "task-1-1", "task-1-2"]

        # Verify parent unchanged
        assert spec["hierarchy"]["task-1-3"]["parent"] == "phase-1"

        # Verify task counts unchanged
        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 3

    def test_move_nonexistent_node(self):
        """Test that moving a nonexistent node raises KeyError."""
        spec = create_minimal_spec()

        with pytest.raises(KeyError, match="not found"):
            move_node(spec, "nonexistent-task", "phase-1")

    def test_move_to_nonexistent_parent(self):
        """Test that moving to a nonexistent parent raises KeyError."""
        spec = create_minimal_spec()

        add_node(spec, "phase-1", {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Task 1"
        })

        with pytest.raises(KeyError, match="not found"):
            move_node(spec, "task-1-1", "nonexistent-parent")

    def test_move_spec_root(self):
        """Test that moving spec-root is prevented."""
        spec = create_minimal_spec()

        with pytest.raises(ValueError, match="Cannot move spec-root"):
            move_node(spec, "spec-root", "phase-1")

    def test_move_with_invalid_position(self):
        """Test that invalid position is handled gracefully."""
        spec = create_minimal_spec()

        add_node(spec, "phase-1", {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Task 1"
        })

        # Try to move with invalid position type (should be caught)
        result = move_node(spec, "task-1-1", "phase-2", position="invalid")

        assert result["success"] is False
        assert "Invalid position" in result["message"]

        # Verify node wasn't moved (rollback worked)
        assert spec["hierarchy"]["task-1-1"]["parent"] == "phase-1"
        assert "task-1-1" in spec["hierarchy"]["phase-1"]["children"]

    def test_move_with_negative_position(self):
        """Test moving with negative position (counts from end)."""
        spec = create_minimal_spec()

        # Add two tasks to phase-2
        add_node(spec, "phase-2", {
            "node_id": "task-2-1",
            "type": "task",
            "title": "Task 2-1"
        })
        add_node(spec, "phase-2", {
            "node_id": "task-2-2",
            "type": "task",
            "title": "Task 2-2"
        })

        # Add task to phase-1
        add_node(spec, "phase-1", {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Task 1-1"
        })

        # Move task-1-1 to phase-2 at position -1 (before last element)
        result = move_node(spec, "task-1-1", "phase-2", position=-1)

        assert result["success"] is True
        phase2_children = spec["hierarchy"]["phase-2"]["children"]
        # Should be inserted before the last element
        assert phase2_children == ["task-2-1", "task-1-1", "task-2-2"]

    def test_move_preserves_completed_tasks(self):
        """Test that moving completed tasks updates completed_tasks counts correctly."""
        spec = create_minimal_spec()

        # Add completed task to phase-1
        add_node(spec, "phase-1", {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Completed task",
            "status": "completed"
        })

        # Manually set completed_tasks to simulate completion
        spec["hierarchy"]["task-1-1"]["completed_tasks"] = 1
        spec["hierarchy"]["phase-1"]["completed_tasks"] = 1
        spec["hierarchy"]["spec-root"]["completed_tasks"] = 1

        # Move to phase-2
        result = move_node(spec, "task-1-1", "phase-2")

        assert result["success"] is True

        # Verify completed_tasks counts updated correctly
        assert spec["hierarchy"]["phase-1"]["completed_tasks"] == 0
        assert spec["hierarchy"]["phase-2"]["completed_tasks"] == 1
        assert spec["hierarchy"]["spec-root"]["completed_tasks"] == 1

    def test_move_updates_spec_root_counts(self):
        """Test that moving tasks updates spec-root counts correctly."""
        spec = create_minimal_spec()

        # Add task to phase-1
        add_node(spec, "phase-1", {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Task 1"
        })

        # Verify spec-root has correct count
        assert spec["hierarchy"]["spec-root"]["total_tasks"] == 1

        # Move to phase-2
        move_node(spec, "task-1-1", "phase-2")

        # Verify spec-root count unchanged (task still under spec-root hierarchy)
        assert spec["hierarchy"]["spec-root"]["total_tasks"] == 1

    def test_move_invalid_spec_data(self):
        """Test that invalid spec_data raises ValueError."""
        with pytest.raises(ValueError, match="must be a dictionary"):
            move_node("invalid", "task-1", "phase-1")

        with pytest.raises(ValueError, match="must contain 'hierarchy'"):
            move_node({"no_hierarchy": {}}, "task-1", "phase-1")

        with pytest.raises(ValueError, match="must be a dictionary"):
            move_node({"hierarchy": "invalid"}, "task-1", "phase-1")
