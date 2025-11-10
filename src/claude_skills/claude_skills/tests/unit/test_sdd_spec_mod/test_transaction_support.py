from __future__ import annotations

import pytest

from claude_skills.sdd_spec_mod.modification import (
    _validate_spec_integrity,
    add_node,
    remove_node,
    spec_transaction,
    transactional_modify,
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


class TestSpecTransaction:
    """Test suite for spec_transaction context manager."""

    def test_transaction_commits_on_success(self) -> None:
        spec = create_minimal_spec()

        with spec_transaction(spec):
            add_node(
                spec,
                "phase-1",
                {
                    "node_id": "task-1-1",
                    "type": "task",
                    "title": "Task 1",
                },
            )

        assert "task-1-1" in spec["hierarchy"]

    def test_transaction_rolls_back_on_exception(self) -> None:
        spec = create_minimal_spec()
        add_node(
            spec,
            "phase-1",
            {
                "node_id": "task-1-1",
                "type": "task",
                "title": "Task 1",
            },
        )

        initial_task_count = len(spec["hierarchy"])

        with pytest.raises(ValueError):
            with spec_transaction(spec):
                add_node(
                    spec,
                    "phase-1",
                    {
                        "node_id": "task-1-2",
                        "type": "task",
                        "title": "Task 2",
                    },
                )
                raise ValueError("Intentional failure")

        assert "task-1-2" not in spec["hierarchy"]
        assert "task-1-1" in spec["hierarchy"]
        assert len(spec["hierarchy"]) == initial_task_count

    def test_transaction_with_multiple_operations(self) -> None:
        spec = create_minimal_spec()

        with spec_transaction(spec):
            for i in range(1, 4):
                add_node(
                    spec,
                    "phase-1",
                    {
                        "node_id": f"task-1-{i}",
                        "type": "task",
                        "title": f"Task {i}",
                    },
                )

        for i in range(1, 4):
            assert f"task-1-{i}" in spec["hierarchy"]

    def test_transaction_rollback_multiple_operations(self) -> None:
        spec = create_minimal_spec()

        with pytest.raises(RuntimeError):
            with spec_transaction(spec):
                add_node(
                    spec,
                    "phase-1",
                    {
                        "node_id": "task-1-1",
                        "type": "task",
                        "title": "Task 1",
                    },
                )
                add_node(
                    spec,
                    "phase-1",
                    {
                        "node_id": "task-1-2",
                        "type": "task",
                        "title": "Task 2",
                    },
                )
                raise RuntimeError("Test failure")

        assert "task-1-1" not in spec["hierarchy"]
        assert "task-1-2" not in spec["hierarchy"]


class TestTransactionalModify:
    """Test suite for transactional_modify function."""

    def test_transactional_modify_with_success(self) -> None:
        spec = create_minimal_spec()

        def my_operation(spec_data: dict) -> dict:
            return add_node(
                spec_data,
                "phase-1",
                {
                    "node_id": "task-1-1",
                    "type": "task",
                    "title": "Task 1",
                },
            )

        result = transactional_modify(spec, my_operation, validate=True)

        assert result["success"] is True
        assert "task-1-1" in spec["hierarchy"]

    def test_transactional_modify_with_operation_failure(self) -> None:
        spec = create_minimal_spec()

        def failing_operation(spec_data: dict) -> dict:
            add_node(
                spec_data,
                "phase-1",
                {
                    "node_id": "task-1-1",
                    "type": "task",
                    "title": "Task 1",
                },
            )
            return add_node(
                spec_data,
                "phase-1",
                {
                    "node_id": "task-1-1",
                    "type": "task",
                    "title": "Duplicate",
                },
            )

        result = transactional_modify(spec, failing_operation, validate=True)

        assert result["success"] is False
        assert "rolled back" in result["message"].lower()

    def test_transactional_modify_without_validation(self) -> None:
        spec = create_minimal_spec()

        def my_operation(spec_data: dict) -> dict:
            return add_node(
                spec_data,
                "phase-1",
                {
                    "node_id": "task-1-1",
                    "type": "task",
                    "title": "Task 1",
                },
            )

        result = transactional_modify(spec, my_operation, validate=False)

        assert result["success"] is True
        assert "task-1-1" in spec["hierarchy"]

    def test_transactional_modify_with_validation_failure(self) -> None:
        spec = create_minimal_spec()

        def corrupting_operation(spec_data: dict) -> dict:
            result = add_node(
                spec_data,
                "phase-1",
                {
                    "node_id": "task-1-1",
                    "type": "task",
                    "title": "Task 1",
                },
            )
            spec_data["hierarchy"]["phase-1"]["children"].remove("task-1-1")
            return result

        result = transactional_modify(spec, corrupting_operation, validate=True)

        assert result["success"] is False
        assert "validation failed" in result["message"].lower()
        assert "task-1-1" not in spec["hierarchy"]


class TestValidateSpecIntegrity:
    """Test suite for _validate_spec_integrity function."""

    def test_validate_valid_spec(self) -> None:
        spec = create_minimal_spec()
        result = _validate_spec_integrity(spec)
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_missing_parent(self) -> None:
        spec = create_minimal_spec()
        spec["hierarchy"]["task-1-1"] = {
            "type": "task",
            "title": "Orphaned task",
            "parent": "nonexistent-phase",
            "children": [],
            "total_tasks": 1,
            "completed_tasks": 0,
        }
        result = _validate_spec_integrity(spec)
        assert result["valid"] is False
        assert any("nonexistent parent" in err.lower() for err in result["errors"])

    def test_validate_missing_child(self) -> None:
        spec = create_minimal_spec()
        spec["hierarchy"]["phase-1"]["children"].append("nonexistent-task")
        result = _validate_spec_integrity(spec)
        assert result["valid"] is False
        assert any("nonexistent child" in err.lower() for err in result["errors"])

    def test_validate_bidirectional_parent_child(self) -> None:
        spec = create_minimal_spec()
        spec["hierarchy"]["task-1-1"] = {
            "type": "task",
            "title": "Task 1",
            "parent": "phase-1",
            "children": [],
            "total_tasks": 1,
            "completed_tasks": 0,
        }
        result = _validate_spec_integrity(spec)
        assert result["valid"] is False
        assert any("not in parent" in err.lower() for err in result["errors"])

    def test_validate_spec_root_with_parent(self) -> None:
        spec = create_minimal_spec()
        spec["hierarchy"]["spec-root"]["parent"] = "invalid-parent"
        result = _validate_spec_integrity(spec)
        assert result["valid"] is False
        assert any("spec-root" in err.lower() and "parent" in err.lower() for err in result["errors"])

    def test_validate_orphaned_node(self) -> None:
        spec = create_minimal_spec()
        spec["hierarchy"]["orphan-task"] = {
            "type": "task",
            "title": "Orphaned task",
            "parent": None,
            "children": [],
            "total_tasks": 1,
            "completed_tasks": 0,
        }
        result = _validate_spec_integrity(spec)
        assert result["valid"] is False
        assert any("no parent" in err.lower() for err in result["errors"])

    def test_validate_child_wrong_parent(self) -> None:
        spec = create_minimal_spec()
        spec["hierarchy"]["phase-2"] = {
            "type": "phase",
            "title": "Phase 2",
            "parent": "spec-root",
            "children": [],
            "total_tasks": 0,
            "completed_tasks": 0,
        }
        spec["hierarchy"]["task-1-1"] = {
            "type": "task",
            "title": "Task 1",
            "parent": "phase-1",
            "children": [],
            "total_tasks": 1,
            "completed_tasks": 0,
        }
        spec["hierarchy"]["phase-2"]["children"].append("task-1-1")
        result = _validate_spec_integrity(spec)
        assert result["valid"] is False
        assert result["errors"]


class TestTransactionIntegration:
    """Integration tests for transaction support with modification functions."""

    def test_transaction_with_remove_node(self) -> None:
        spec = create_minimal_spec()
        add_node(
            spec,
            "phase-1",
            {
                "node_id": "task-1-1",
                "type": "task",
                "title": "Task 1",
            },
        )

        with pytest.raises(ValueError):
            with spec_transaction(spec):
                remove_node(spec, "task-1-1")
                assert "task-1-1" not in spec["hierarchy"]
                raise ValueError("Test rollback")

        assert "task-1-1" in spec["hierarchy"]

    def test_transactional_modify_with_complex_operation(self) -> None:
        spec = create_minimal_spec()

        def complex_operation(spec_data: dict) -> dict:
            add_node(
                spec_data,
                "phase-1",
                {
                    "node_id": "task-1-1",
                    "type": "task",
                    "title": "Task 1",
                },
            )
            add_node(
                spec_data,
                "task-1-1",
                {
                    "node_id": "task-1-1-1",
                    "type": "subtask",
                    "title": "Subtask 1",
                },
            )
            add_node(
                spec_data,
                "task-1-1",
                {
                    "node_id": "task-1-1-2",
                    "type": "subtask",
                    "title": "Subtask 2",
                },
            )
            return {"success": True, "message": "Complex operation completed"}

        result = transactional_modify(spec, complex_operation, validate=True)

        assert result["success"] is True
        assert "task-1-1" in spec["hierarchy"]
        assert "task-1-1-1" in spec["hierarchy"]
        assert "task-1-1-2" in spec["hierarchy"]
