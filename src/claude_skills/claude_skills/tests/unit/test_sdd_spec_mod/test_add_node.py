from __future__ import annotations

import pytest

from claude_skills.sdd_spec_mod.modification import (
    _propagate_task_count_increase,
    add_node,
)


pytestmark = pytest.mark.unit


def create_minimal_spec() -> dict:
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
                "children": ["phase-1"],
                "total_tasks": 0,
                "completed_tasks": 0,
                "metadata": {},
            },
            "phase-1": {
                "type": "phase",
                "title": "Phase 1",
                "status": "pending",
                "parent": "spec-root",
                "children": [],
                "total_tasks": 0,
                "completed_tasks": 0,
                "metadata": {},
            },
        },
    }


class TestAddNode:
    """Test suite for add_node() function."""

    def test_add_task_to_phase(self) -> None:
        """Test adding a basic task to a phase."""
        spec = create_minimal_spec()

        node_data = {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Implement feature X",
        }

        result = add_node(spec, "phase-1", node_data)

        assert result["success"] is True
        assert "task-1-1" in spec["hierarchy"]
        assert "task-1-1" in spec["hierarchy"]["phase-1"]["children"]

        # Check task was created with correct structure
        task = spec["hierarchy"]["task-1-1"]
        assert task["type"] == "task"
        assert task["title"] == "Implement feature X"
        assert task["status"] == "pending"
        assert task["parent"] == "phase-1"
        assert task["children"] == []
        assert task["total_tasks"] == 1  # Leaf tasks should have total_tasks=1
        assert task["completed_tasks"] == 0

    def test_add_task_updates_parent_counts(self) -> None:
        """Test that adding a task updates parent and ancestor task counts."""
        spec = create_minimal_spec()

        node_data = {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Implement feature X",
        }

        add_node(spec, "phase-1", node_data)

        # Check counts were propagated
        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 1
        assert spec["hierarchy"]["spec-root"]["total_tasks"] == 1

    def test_add_subtask_to_task(self) -> None:
        """Test adding a subtask to a task."""
        spec = create_minimal_spec()

        # First add a task
        task_data = {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Implement feature X",
        }
        add_node(spec, "phase-1", task_data)

        # Then add a subtask
        subtask_data = {
            "node_id": "task-1-1-1",
            "type": "subtask",
            "title": "Implement helper function",
        }
        result = add_node(spec, "task-1-1", subtask_data)

        assert result["success"] is True
        assert "task-1-1-1" in spec["hierarchy"]
        assert "task-1-1-1" in spec["hierarchy"]["task-1-1"]["children"]

        # Subtask should have total_tasks=1 (leaf node)
        assert spec["hierarchy"]["task-1-1-1"]["total_tasks"] == 1

        # Parent task should now have total_tasks=2 (itself + subtask)
        assert spec["hierarchy"]["task-1-1"]["total_tasks"] == 2

    def test_add_node_at_position(self) -> None:
        """Test adding a node at a specific position in children list."""
        spec = create_minimal_spec()

        # Add first task
        add_node(
            spec,
            "phase-1",
            {
                "node_id": "task-1-1",
                "type": "task",
                "title": "First task",
            },
        )

        # Add second task
        add_node(
            spec,
            "phase-1",
            {
                "node_id": "task-1-2",
                "type": "task",
                "title": "Second task",
            },
        )

        # Add third task at position 1 (between first and second)
        result = add_node(
            spec,
            "phase-1",
            {
                "node_id": "task-1-1-5",
                "type": "task",
                "title": "Middle task",
            },
            position=1,
        )

        assert result["success"] is True

        children = spec["hierarchy"]["phase-1"]["children"]
        assert children == ["task-1-1", "task-1-1-5", "task-1-2"]

    def test_add_node_with_metadata(self) -> None:
        """Test adding a node with custom metadata."""
        spec = create_minimal_spec()

        node_data = {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Implement feature X",
            "metadata": {
                "file_path": "src/feature_x.py",
                "estimated_hours": 4,
                "task_category": "implementation",
            },
        }

        result = add_node(spec, "phase-1", node_data)

        assert result["success"] is True

        task = spec["hierarchy"]["task-1-1"]
        assert task["metadata"]["file_path"] == "src/feature_x.py"
        assert task["metadata"]["estimated_hours"] == 4
        assert task["metadata"]["task_category"] == "implementation"

    def test_add_node_with_dependencies(self) -> None:
        """Test adding a node with dependencies."""
        spec = create_minimal_spec()

        # Add first task
        add_node(
            spec,
            "phase-1",
            {
                "node_id": "task-1-1",
                "type": "task",
                "title": "First task",
            },
        )

        # Add second task that depends on first
        node_data = {
            "node_id": "task-1-2",
            "type": "task",
            "title": "Second task",
            "dependencies": {
                "blocks": [],
                "blocked_by": ["task-1-1"],
                "depends": ["task-1-1"],
            },
        }

        result = add_node(spec, "phase-1", node_data)

        assert result["success"] is True

        task = spec["hierarchy"]["task-1-2"]
        assert "task-1-1" in task["dependencies"]["blocked_by"]
        assert "task-1-1" in task["dependencies"]["depends"]

    def test_add_node_duplicate_id_fails(self) -> None:
        """Test that adding a node with duplicate ID fails gracefully."""
        spec = create_minimal_spec()

        node_data = {
            "node_id": "task-1-1",
            "type": "task",
            "title": "First task",
        }

        # First addition should succeed
        result1 = add_node(spec, "phase-1", node_data)
        assert result1["success"] is True

        # Second addition with same ID should fail
        result2 = add_node(spec, "phase-1", node_data)
        assert result2["success"] is False
        assert "already exists" in result2["message"]

    def test_add_node_invalid_parent_raises_error(self) -> None:
        """Test that adding a node to non-existent parent raises KeyError."""
        spec = create_minimal_spec()

        node_data = {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Test task",
        }

        with pytest.raises(KeyError):
            add_node(spec, "non-existent-parent", node_data)

    def test_add_node_missing_required_fields_raises_error(self) -> None:
        """Test that missing required fields raises ValueError."""
        spec = create_minimal_spec()

        # Missing node_id
        with pytest.raises(ValueError, match="missing required fields"):
            add_node(spec, "phase-1", {"type": "task", "title": "Test"})

        # Missing type
        with pytest.raises(ValueError, match="missing required fields"):
            add_node(spec, "phase-1", {"node_id": "task-1-1", "title": "Test"})

        # Missing title
        with pytest.raises(ValueError, match="missing required fields"):
            add_node(spec, "phase-1", {"node_id": "task-1-1", "type": "task"})

    def test_add_node_invalid_type_fails(self) -> None:
        """Test that invalid node type fails gracefully."""
        spec = create_minimal_spec()

        node_data = {
            "node_id": "task-1-1",
            "type": "invalid_type",
            "title": "Test task",
        }

        result = add_node(spec, "phase-1", node_data)

        assert result["success"] is False
        assert "Invalid node type" in result["message"]

    def test_add_node_empty_title_fails(self) -> None:
        """Test that empty title fails gracefully."""
        spec = create_minimal_spec()

        node_data = {
            "node_id": "task-1-1",
            "type": "task",
            "title": "   ",  # Whitespace only
        }

        result = add_node(spec, "phase-1", node_data)

        assert result["success"] is False
        assert "title cannot be empty" in result["message"]

    def test_add_verify_node(self) -> None:
        """Test adding a verification node."""
        spec = create_minimal_spec()

        node_data = {
            "node_id": "verify-1-1",
            "type": "verify",
            "title": "Verify feature X works",
            "metadata": {
                "verification": {
                    "type": "test",
                    "command": "pytest tests/test_feature_x.py",
                    "expected": "All tests pass",
                }
            },
        }

        result = add_node(spec, "phase-1", node_data)

        assert result["success"] is True

        verify_node = spec["hierarchy"]["verify-1-1"]
        assert verify_node["type"] == "verify"
        assert verify_node["total_tasks"] == 1  # Verify nodes are leaf nodes
        assert "verification" in verify_node["metadata"]

    def test_add_group_node(self) -> None:
        """Test adding a group node (container that's not a phase)."""
        spec = create_minimal_spec()

        node_data = {
            "node_id": "group-1-1",
            "type": "group",
            "title": "Database operations",
            "description": "Group of tasks related to database",
        }

        result = add_node(spec, "phase-1", node_data)

        assert result["success"] is True

        group_node = spec["hierarchy"]["group-1-1"]
        assert group_node["type"] == "group"
        assert group_node["total_tasks"] == 0  # Groups are containers, start at 0
        assert group_node["children"] == []

    def test_propagate_task_count_increase(self) -> None:
        """Test the internal task count propagation function."""
        spec = create_minimal_spec()

        # Manually add a task (bypassing add_node to test propagation alone)
        spec["hierarchy"]["task-1-1"] = {
            "type": "task",
            "title": "Test task",
            "status": "pending",
            "parent": "phase-1",
            "children": [],
            "total_tasks": 1,
            "completed_tasks": 0,
            "metadata": {},
        }
        spec["hierarchy"]["phase-1"]["children"].append("task-1-1")

        # Propagate counts
        _propagate_task_count_increase(spec, "phase-1", total_increase=1)

        # Check counts were updated
        assert spec["hierarchy"]["phase-1"]["total_tasks"] == 1
        assert spec["hierarchy"]["spec-root"]["total_tasks"] == 1

        # Propagate completed task
        _propagate_task_count_increase(spec, "phase-1", completed_increase=1)

        assert spec["hierarchy"]["phase-1"]["completed_tasks"] == 1
        assert spec["hierarchy"]["spec-root"]["completed_tasks"] == 1
