from __future__ import annotations

import pytest

from claude_skills.sdd_spec_mod.modification import (
    _cleanup_dependencies,
    _collect_descendants,
    _propagate_task_count_decrease,
    add_node,
    remove_node,
)


pytestmark = pytest.mark.unit


def create_spec_with_tasks() -> dict:
    """Create a spec with multiple tasks for testing removal."""
    return {
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
                "metadata": {},
            },
            "phase-1": {
                "type": "phase",
                "title": "Phase 1",
                "status": "pending",
                "parent": "spec-root",
                "children": ["task-1-1", "task-1-2", "task-1-3"],
                "total_tasks": 3,
                "completed_tasks": 0,
                "metadata": {},
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
                "dependencies": {"blocks": [], "blocked_by": [], "depends": []},
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
                "dependencies": {
                    "blocks": [],
                    "blocked_by": ["task-1-1"],
                    "depends": ["task-1-1"],
                },
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
                "dependencies": {"blocks": [], "blocked_by": [], "depends": []},
            },
        },
    }


class TestRemoveNode:
    """Test suite for remove_node() function."""

    def test_remove_leaf_task(self) -> None:
        """Test removing a leaf task node."""
        spec = create_spec_with_tasks()

        result = remove_node(spec, "task-1-1")

        assert result["success"] is True
        assert "task-1-1" not in spec["hierarchy"]
        assert "task-1-1" not in spec["hierarchy"]["phase-1"]["children"]
        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 2
        assert spec["hierarchy"]["spec-root"]["total_tasks"] == 2

    def test_remove_node_updates_dependencies(self) -> None:
        """Test that removing a node cleans up dependency references."""
        spec = create_spec_with_tasks()

        # task-1-2 depends on task-1-1
        assert "task-1-1" in spec["hierarchy"]["task-1-2"]["dependencies"]["blocked_by"]

        result = remove_node(spec, "task-1-1")

        assert result["success"] is True
        assert "task-1-1" not in spec["hierarchy"]["task-1-2"]["dependencies"]["blocked_by"]
        assert "task-1-1" not in spec["hierarchy"]["task-1-2"]["dependencies"]["depends"]

    def test_remove_node_with_children_fails_without_cascade(self) -> None:
        """Test that removing a node with children fails without cascade=True."""
        spec = create_spec_with_tasks()

        result = remove_node(spec, "phase-1", cascade=False)

        assert result["success"] is False
        assert "children" in result["message"]
        assert "cascade" in result["message"]
        assert "phase-1" in spec["hierarchy"]

    def test_remove_node_with_cascade(self) -> None:
        """Test removing a node with cascade=True removes all descendants."""
        spec = create_spec_with_tasks()

        result = remove_node(spec, "phase-1", cascade=True)

        assert result["success"] is True
        removed = result["removed_nodes"]
        assert {"phase-1", "task-1-1", "task-1-2", "task-1-3"} <= set(removed)
        for node_id in removed:
            assert node_id not in spec["hierarchy"]
        assert "phase-1" not in spec["hierarchy"]["spec-root"]["children"]
        assert spec["hierarchy"]["spec-root"]["total_tasks"] == 0

    def test_remove_node_nonexistent_raises_error(self) -> None:
        """Test that removing non-existent node raises KeyError."""
        spec = create_spec_with_tasks()

        with pytest.raises(KeyError):
            remove_node(spec, "non-existent-task")

    def test_remove_spec_root_raises_error(self) -> None:
        """Test that removing spec-root raises ValueError."""
        spec = create_spec_with_tasks()

        with pytest.raises(ValueError, match="Cannot remove spec-root"):
            remove_node(spec, "spec-root")

    def test_remove_from_middle_of_children_list(self) -> None:
        """Test removing a node from the middle of parent's children list."""
        spec = create_spec_with_tasks()

        result = remove_node(spec, "task-1-2")

        assert result["success"] is True
        children = spec["hierarchy"]["phase-1"]["children"]
        assert children == ["task-1-1", "task-1-3"]

    def test_remove_completed_task_updates_completed_count(self) -> None:
        """Test that removing a completed task updates completed_tasks count."""
        spec = create_spec_with_tasks()

        spec["hierarchy"]["task-1-1"]["status"] = "completed"
        spec["hierarchy"]["task-1-1"]["completed_tasks"] = 1
        spec["hierarchy"]["phase-1"]["completed_tasks"] = 1
        spec["hierarchy"]["spec-root"]["completed_tasks"] = 1

        result = remove_node(spec, "task-1-1")

        assert result["success"] is True
        assert spec["hierarchy"]["phase-1"]["completed_tasks"] == 0
        assert spec["hierarchy"]["spec-root"]["completed_tasks"] == 0
        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 2
        assert spec["hierarchy"]["spec-root"]["total_tasks"] == 2

    def test_collect_descendants(self) -> None:
        """Test the _collect_descendants helper function."""
        spec = create_spec_with_tasks()

        result: list[str] = []
        _collect_descendants(spec, "phase-1", result)

        assert set(result) == {"phase-1", "task-1-1", "task-1-2", "task-1-3"}

    def test_collect_descendants_with_nested_hierarchy(self) -> None:
        """Test collecting descendants with nested subtasks."""
        spec = create_spec_with_tasks()

        add_node(
            spec,
            "task-1-1",
            {
                "node_id": "task-1-1-1",
                "type": "subtask",
                "title": "Subtask",
            },
        )

        result: list[str] = []
        _collect_descendants(spec, "phase-1", result)

        assert {"phase-1", "task-1-1", "task-1-1-1", "task-1-2", "task-1-3"} <= set(result)

    def test_cleanup_dependencies(self) -> None:
        """Test the _cleanup_dependencies helper function."""
        spec = create_spec_with_tasks()

        spec["hierarchy"]["task-1-3"]["dependencies"]["blocked_by"] = ["task-1-1", "task-1-2"]
        spec["hierarchy"]["task-1-3"]["dependencies"]["depends"] = ["task-1-1"]

        _cleanup_dependencies(spec, ["task-1-1"])

        assert "task-1-1" not in spec["hierarchy"]["task-1-2"]["dependencies"]["blocked_by"]
        assert "task-1-1" not in spec["hierarchy"]["task-1-3"]["dependencies"]["blocked_by"]
        assert "task-1-1" not in spec["hierarchy"]["task-1-3"]["dependencies"]["depends"]
        assert "task-1-2" in spec["hierarchy"]["task-1-3"]["dependencies"]["blocked_by"]

    def test_propagate_task_count_decrease(self) -> None:
        """Test the _propagate_task_count_decrease helper function."""
        spec = create_spec_with_tasks()

        _propagate_task_count_decrease(spec, "phase-1", total_decrease=1, completed_decrease=0)

        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 2
        assert spec["hierarchy"]["spec-root"]["total_tasks"] == 2

    def test_propagate_task_count_decrease_prevents_negative(self) -> None:
        """Test that task count decrease doesn't go negative."""
        spec = create_spec_with_tasks()

        _propagate_task_count_decrease(spec, "phase-1", total_decrease=10, completed_decrease=10)

        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 0
        assert spec["hierarchy"]["phase-1"]["completed_tasks"] == 0
        assert spec["hierarchy"]["spec-root"]["total_tasks"] == 0
        assert spec["hierarchy"]["spec-root"]["completed_tasks"] == 0

    def test_remove_group_node(self) -> None:
        """Test removing a group node (non-leaf, non-phase container)."""
        spec = create_spec_with_tasks()

        add_node(
            spec,
            "phase-1",
            {
                "node_id": "group-1-1",
                "type": "group",
                "title": "Database Operations",
            },
        )

        result = remove_node(spec, "group-1-1")

        assert result["success"] is True
        assert "group-1-1" not in spec["hierarchy"]
        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 3

    def test_remove_verify_node(self) -> None:
        """Test removing a verification node."""
        spec = create_spec_with_tasks()

        add_node(
            spec,
            "phase-1",
            {
                "node_id": "verify-1-1",
                "type": "verify",
                "title": "Verify feature works",
            },
        )

        result = remove_node(spec, "verify-1-1")

        assert result["success"] is True
        assert "verify-1-1" not in spec["hierarchy"]
        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 3

    def test_remove_node_with_complex_dependencies(self) -> None:
        """Test removing a node that blocks multiple other nodes."""
        spec = create_spec_with_tasks()

        spec["hierarchy"]["task-1-1"]["dependencies"]["blocks"] = ["task-1-2", "task-1-3"]
        spec["hierarchy"]["task-1-3"]["dependencies"]["blocked_by"] = ["task-1-1"]
        spec["hierarchy"]["task-1-3"]["dependencies"]["depends"] = ["task-1-1"]

        result = remove_node(spec, "task-1-1")

        assert result["success"] is True
        assert "task-1-1" not in spec["hierarchy"]["task-1-2"]["dependencies"]["blocked_by"]
        assert "task-1-1" not in spec["hierarchy"]["task-1-3"]["dependencies"]["blocked_by"]
        assert "task-1-1" not in spec["hierarchy"]["task-1-3"]["dependencies"]["depends"]
