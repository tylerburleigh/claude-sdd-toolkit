"""
Tests for remove_node() function in sdd_spec_mod module.
"""

import pytest
from claude_skills.sdd_spec_mod.modification import (
    add_node,
    remove_node,
    _collect_descendants,
    _cleanup_dependencies,
    _propagate_task_count_decrease
)


def create_spec_with_tasks():
    """Create a spec with multiple tasks for testing removal."""
    spec = {
        "spec_id": "test-spec-001",
        "title": "Test Specification",
        "hierarchy": {
            "spec-root": {
                "type": "spec",
                "title": "Test Specification",
                "status": "in_progress",
                "parent": None,
                "children": ["phase-1"],
                "total_tasks": 3,
                "completed_tasks": 0,
                "metadata": {}
            },
            "phase-1": {
                "type": "phase",
                "title": "Phase 1",
                "status": "pending",
                "parent": "spec-root",
                "children": ["task-1-1", "task-1-2", "task-1-3"],
                "total_tasks": 3,
                "completed_tasks": 0,
                "metadata": {}
            },
            "task-1-1": {
                "type": "task",
                "title": "Task 1",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {},
                "dependencies": {"blocks": [], "blocked_by": [], "depends": []}
            },
            "task-1-2": {
                "type": "task",
                "title": "Task 2",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {},
                "dependencies": {"blocks": [], "blocked_by": ["task-1-1"], "depends": ["task-1-1"]}
            },
            "task-1-3": {
                "type": "task",
                "title": "Task 3",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {},
                "dependencies": {"blocks": [], "blocked_by": [], "depends": []}
            }
        }
    }
    return spec


class TestRemoveNode:
    """Test suite for remove_node() function."""

    def test_remove_leaf_task(self):
        """Test removing a leaf task node."""
        spec = create_spec_with_tasks()

        result = remove_node(spec, "task-1-1")

        assert result["success"] is True
        assert "task-1-1" not in spec["hierarchy"]
        assert "task-1-1" not in spec["hierarchy"]["phase-1"]["children"]

        # Check counts were updated
        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 2
        assert spec["hierarchy"]["spec-root"]["total_tasks"] == 2

    def test_remove_node_updates_dependencies(self):
        """Test that removing a node cleans up dependency references."""
        spec = create_spec_with_tasks()

        # task-1-2 depends on task-1-1
        assert "task-1-1" in spec["hierarchy"]["task-1-2"]["dependencies"]["blocked_by"]

        # Remove task-1-1
        result = remove_node(spec, "task-1-1")

        assert result["success"] is True

        # Check that dependency was cleaned up
        assert "task-1-1" not in spec["hierarchy"]["task-1-2"]["dependencies"]["blocked_by"]
        assert "task-1-1" not in spec["hierarchy"]["task-1-2"]["dependencies"]["depends"]

    def test_remove_node_with_children_fails_without_cascade(self):
        """Test that removing a node with children fails without cascade=True."""
        spec = create_spec_with_tasks()

        # phase-1 has children
        result = remove_node(spec, "phase-1", cascade=False)

        assert result["success"] is False
        assert "children" in result["message"]
        assert "cascade" in result["message"]

        # Node should still exist
        assert "phase-1" in spec["hierarchy"]

    def test_remove_node_with_cascade(self):
        """Test removing a node with cascade=True removes all descendants."""
        spec = create_spec_with_tasks()

        result = remove_node(spec, "phase-1", cascade=True)

        assert result["success"] is True

        # Check all nodes were removed
        removed = result["removed_nodes"]
        assert "phase-1" in removed
        assert "task-1-1" in removed
        assert "task-1-2" in removed
        assert "task-1-3" in removed

        # Check none of these nodes exist anymore
        for node_id in removed:
            assert node_id not in spec["hierarchy"]

        # Check parent's children list was updated
        assert "phase-1" not in spec["hierarchy"]["spec-root"]["children"]

        # Check counts were reset
        assert spec["hierarchy"]["spec-root"]["total_tasks"] == 0

    def test_remove_node_nonexistent_raises_error(self):
        """Test that removing non-existent node raises KeyError."""
        spec = create_spec_with_tasks()

        with pytest.raises(KeyError):
            remove_node(spec, "non-existent-task")

    def test_remove_spec_root_raises_error(self):
        """Test that removing spec-root raises ValueError."""
        spec = create_spec_with_tasks()

        with pytest.raises(ValueError, match="Cannot remove spec-root"):
            remove_node(spec, "spec-root")

    def test_remove_from_middle_of_children_list(self):
        """Test removing a node from the middle of parent's children list."""
        spec = create_spec_with_tasks()

        # Remove task-1-2 (middle child)
        result = remove_node(spec, "task-1-2")

        assert result["success"] is True

        children = spec["hierarchy"]["phase-1"]["children"]
        assert children == ["task-1-1", "task-1-3"]
        assert "task-1-2" not in children

    def test_remove_completed_task_updates_completed_count(self):
        """Test that removing a completed task updates completed_tasks count."""
        spec = create_spec_with_tasks()

        # Mark task-1-1 as completed
        spec["hierarchy"]["task-1-1"]["status"] = "completed"
        spec["hierarchy"]["task-1-1"]["completed_tasks"] = 1
        spec["hierarchy"]["phase-1"]["completed_tasks"] = 1
        spec["hierarchy"]["spec-root"]["completed_tasks"] = 1

        # Remove the completed task
        result = remove_node(spec, "task-1-1")

        assert result["success"] is True

        # Check completed_tasks was decremented
        assert spec["hierarchy"]["phase-1"]["completed_tasks"] == 0
        assert spec["hierarchy"]["spec-root"]["completed_tasks"] == 0

        # total_tasks should also be decremented
        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 2
        assert spec["hierarchy"]["spec-root"]["total_tasks"] == 2

    def test_collect_descendants(self):
        """Test the _collect_descendants helper function."""
        spec = create_spec_with_tasks()

        result = []
        _collect_descendants(spec, "phase-1", result)

        # Should collect phase-1 and all its children
        assert "phase-1" in result
        assert "task-1-1" in result
        assert "task-1-2" in result
        assert "task-1-3" in result
        assert len(result) == 4

    def test_collect_descendants_with_nested_hierarchy(self):
        """Test collecting descendants with nested subtasks."""
        spec = create_spec_with_tasks()

        # Add a subtask under task-1-1
        add_node(spec, "task-1-1", {
            "node_id": "task-1-1-1",
            "type": "subtask",
            "title": "Subtask"
        })

        result = []
        _collect_descendants(spec, "phase-1", result)

        # Should collect phase, task, and subtask
        assert "phase-1" in result
        assert "task-1-1" in result
        assert "task-1-1-1" in result
        assert "task-1-2" in result
        assert "task-1-3" in result
        assert len(result) == 5

    def test_cleanup_dependencies(self):
        """Test the _cleanup_dependencies helper function."""
        spec = create_spec_with_tasks()

        # Manually setup more complex dependencies
        spec["hierarchy"]["task-1-3"]["dependencies"]["blocked_by"] = ["task-1-1", "task-1-2"]
        spec["hierarchy"]["task-1-3"]["dependencies"]["depends"] = ["task-1-1"]

        # Clean up task-1-1
        _cleanup_dependencies(spec, ["task-1-1"])

        # Check task-1-1 was removed from dependencies
        assert "task-1-1" not in spec["hierarchy"]["task-1-2"]["dependencies"]["blocked_by"]
        assert "task-1-1" not in spec["hierarchy"]["task-1-3"]["dependencies"]["blocked_by"]
        assert "task-1-1" not in spec["hierarchy"]["task-1-3"]["dependencies"]["depends"]

        # Check task-1-2 is still there
        assert "task-1-2" in spec["hierarchy"]["task-1-3"]["dependencies"]["blocked_by"]

    def test_propagate_task_count_decrease(self):
        """Test the _propagate_task_count_decrease helper function."""
        spec = create_spec_with_tasks()

        # Manually decrease counts
        _propagate_task_count_decrease(spec, "phase-1", total_decrease=1, completed_decrease=0)

        # Check counts were propagated
        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 2
        assert spec["hierarchy"]["spec-root"]["total_tasks"] == 2

    def test_propagate_task_count_decrease_prevents_negative(self):
        """Test that task count decrease doesn't go negative."""
        spec = create_spec_with_tasks()

        # Try to decrease by more than exists
        _propagate_task_count_decrease(spec, "phase-1", total_decrease=10, completed_decrease=10)

        # Counts should be 0, not negative
        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 0
        assert spec["hierarchy"]["phase-1"]["completed_tasks"] == 0
        assert spec["hierarchy"]["spec-root"]["total_tasks"] == 0
        assert spec["hierarchy"]["spec-root"]["completed_tasks"] == 0

    def test_remove_group_node(self):
        """Test removing a group node (non-leaf, non-phase container)."""
        spec = create_spec_with_tasks()

        # Add a group under phase-1
        add_node(spec, "phase-1", {
            "node_id": "group-1-1",
            "type": "group",
            "title": "Database Operations"
        })

        # Group has no children, so removal should succeed without cascade
        result = remove_node(spec, "group-1-1")

        assert result["success"] is True
        assert "group-1-1" not in spec["hierarchy"]

    def test_remove_verify_node(self):
        """Test removing a verification node."""
        spec = create_spec_with_tasks()

        # Add a verify node
        add_node(spec, "phase-1", {
            "node_id": "verify-1-1",
            "type": "verify",
            "title": "Verify feature works"
        })

        # Remove it
        result = remove_node(spec, "verify-1-1")

        assert result["success"] is True
        assert "verify-1-1" not in spec["hierarchy"]

        # total_tasks should be back to 3 (the original 3 tasks)
        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 3

    def test_remove_node_with_complex_dependencies(self):
        """Test removing a node that blocks multiple other nodes."""
        spec = create_spec_with_tasks()

        # Setup complex dependency chain
        # task-1-1 blocks both task-1-2 and task-1-3
        spec["hierarchy"]["task-1-1"]["dependencies"]["blocks"] = ["task-1-2", "task-1-3"]
        spec["hierarchy"]["task-1-3"]["dependencies"]["blocked_by"] = ["task-1-1"]
        spec["hierarchy"]["task-1-3"]["dependencies"]["depends"] = ["task-1-1"]

        # Remove task-1-1
        result = remove_node(spec, "task-1-1")

        assert result["success"] is True

        # Check all references were cleaned up
        assert "task-1-1" not in spec["hierarchy"]["task-1-2"]["dependencies"]["blocked_by"]
        assert "task-1-1" not in spec["hierarchy"]["task-1-3"]["dependencies"]["blocked_by"]
        assert "task-1-1" not in spec["hierarchy"]["task-1-3"]["dependencies"]["depends"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
