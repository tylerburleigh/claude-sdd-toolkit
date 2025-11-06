"""
Tests for transaction support and rollback in sdd_spec_mod module.
"""

import pytest
from claude_skills.sdd_spec_mod.modification import (
    add_node,
    remove_node,
    spec_transaction,
    transactional_modify,
    _validate_spec_integrity,
)


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
                "children": ["phase-1"],
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
            }
        }
    }


class TestSpecTransaction:
    """Test suite for spec_transaction context manager."""

    def test_transaction_commits_on_success(self):
        """Test that changes are kept when transaction completes successfully."""
        spec = create_minimal_spec()

        with spec_transaction(spec):
            add_node(spec, "phase-1", {
                "node_id": "task-1-1",
                "type": "task",
                "title": "Task 1"
            })

        # Change should persist after context exit
        assert "task-1-1" in spec["hierarchy"]

    def test_transaction_rolls_back_on_exception(self):
        """Test that changes are rolled back when exception occurs."""
        spec = create_minimal_spec()

        # Add initial task
        add_node(spec, "phase-1", {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Task 1"
        })

        initial_task_count = len(spec["hierarchy"])

        # Try to make changes that will fail
        try:
            with spec_transaction(spec):
                # Add a valid task
                add_node(spec, "phase-1", {
                    "node_id": "task-1-2",
                    "type": "task",
                    "title": "Task 2"
                })

                # Raise exception to trigger rollback
                raise ValueError("Intentional failure")
        except ValueError:
            pass  # Expected

        # Verify rollback: task-1-2 should not exist
        assert "task-1-2" not in spec["hierarchy"]
        # Original task should still exist
        assert "task-1-1" in spec["hierarchy"]
        # Task count should be same as before transaction
        assert len(spec["hierarchy"]) == initial_task_count

    def test_transaction_with_multiple_operations(self):
        """Test transaction with multiple operations."""
        spec = create_minimal_spec()

        with spec_transaction(spec):
            # Add multiple tasks
            add_node(spec, "phase-1", {
                "node_id": "task-1-1",
                "type": "task",
                "title": "Task 1"
            })
            add_node(spec, "phase-1", {
                "node_id": "task-1-2",
                "type": "task",
                "title": "Task 2"
            })
            add_node(spec, "phase-1", {
                "node_id": "task-1-3",
                "type": "task",
                "title": "Task 3"
            })

        # All tasks should be committed
        assert "task-1-1" in spec["hierarchy"]
        assert "task-1-2" in spec["hierarchy"]
        assert "task-1-3" in spec["hierarchy"]

    def test_transaction_rollback_multiple_operations(self):
        """Test that all operations are rolled back on failure."""
        spec = create_minimal_spec()

        try:
            with spec_transaction(spec):
                add_node(spec, "phase-1", {
                    "node_id": "task-1-1",
                    "type": "task",
                    "title": "Task 1"
                })
                add_node(spec, "phase-1", {
                    "node_id": "task-1-2",
                    "type": "task",
                    "title": "Task 2"
                })

                # This should trigger rollback
                raise RuntimeError("Test failure")
        except RuntimeError:
            pass

        # Neither task should exist
        assert "task-1-1" not in spec["hierarchy"]
        assert "task-1-2" not in spec["hierarchy"]


class TestTransactionalModify:
    """Test suite for transactional_modify function."""

    def test_transactional_modify_with_success(self):
        """Test successful modification with validation."""
        spec = create_minimal_spec()

        def my_operation(spec_data):
            return add_node(spec_data, "phase-1", {
                "node_id": "task-1-1",
                "type": "task",
                "title": "Task 1"
            })

        result = transactional_modify(spec, my_operation, validate=True)

        assert result["success"] is True
        assert "task-1-1" in spec["hierarchy"]

    def test_transactional_modify_with_operation_failure(self):
        """Test rollback when operation fails."""
        spec = create_minimal_spec()

        def failing_operation(spec_data):
            # Try to add with duplicate ID
            add_node(spec_data, "phase-1", {
                "node_id": "task-1-1",
                "type": "task",
                "title": "Task 1"
            })
            # Try to add same ID again (will fail)
            return add_node(spec_data, "phase-1", {
                "node_id": "task-1-1",
                "type": "task",
                "title": "Duplicate"
            })

        result = transactional_modify(spec, failing_operation, validate=True)

        assert result["success"] is False
        assert "rolled back" in result["message"].lower()

    def test_transactional_modify_without_validation(self):
        """Test modification without validation."""
        spec = create_minimal_spec()

        def my_operation(spec_data):
            return add_node(spec_data, "phase-1", {
                "node_id": "task-1-1",
                "type": "task",
                "title": "Task 1"
            })

        result = transactional_modify(spec, my_operation, validate=False)

        assert result["success"] is True
        assert "task-1-1" in spec["hierarchy"]

    def test_transactional_modify_with_validation_failure(self):
        """Test rollback when validation fails."""
        spec = create_minimal_spec()

        def corrupting_operation(spec_data):
            # Add task successfully
            result = add_node(spec_data, "phase-1", {
                "node_id": "task-1-1",
                "type": "task",
                "title": "Task 1"
            })

            # Manually corrupt the hierarchy to trigger validation failure
            # Remove task from parent's children but keep task node
            spec_data["hierarchy"]["phase-1"]["children"].remove("task-1-1")

            return result

        result = transactional_modify(spec, corrupting_operation, validate=True)

        assert result["success"] is False
        assert "validation failed" in result["message"].lower()
        # Task should be rolled back
        assert "task-1-1" not in spec["hierarchy"]


class TestValidateSpecIntegrity:
    """Test suite for _validate_spec_integrity function."""

    def test_validate_valid_spec(self):
        """Test validation of a valid spec."""
        spec = create_minimal_spec()

        result = _validate_spec_integrity(spec)

        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_validate_missing_parent(self):
        """Test detection of missing parent references."""
        spec = create_minimal_spec()

        # Add task with nonexistent parent
        spec["hierarchy"]["task-1-1"] = {
            "type": "task",
            "title": "Orphaned task",
            "parent": "nonexistent-phase",
            "children": [],
            "total_tasks": 1,
            "completed_tasks": 0
        }

        result = _validate_spec_integrity(spec)

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("nonexistent parent" in error.lower() for error in result["errors"])

    def test_validate_missing_child(self):
        """Test detection of missing child references."""
        spec = create_minimal_spec()

        # Add nonexistent child to phase-1
        spec["hierarchy"]["phase-1"]["children"].append("nonexistent-task")

        result = _validate_spec_integrity(spec)

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("nonexistent child" in error.lower() for error in result["errors"])

    def test_validate_bidirectional_parent_child(self):
        """Test detection of broken parent-child bidirectionality."""
        spec = create_minimal_spec()

        # Add task to hierarchy
        spec["hierarchy"]["task-1-1"] = {
            "type": "task",
            "title": "Task 1",
            "parent": "phase-1",
            "children": [],
            "total_tasks": 1,
            "completed_tasks": 0
        }

        # But don't add to parent's children list (breaks bidirectionality)
        # phase-1 should list task-1-1 as child but doesn't

        result = _validate_spec_integrity(spec)

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("not in parent" in error.lower() for error in result["errors"])

    def test_validate_spec_root_with_parent(self):
        """Test detection of spec-root having a parent."""
        spec = create_minimal_spec()

        # Give spec-root a parent (invalid)
        spec["hierarchy"]["spec-root"]["parent"] = "invalid-parent"

        result = _validate_spec_integrity(spec)

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("spec-root" in error.lower() and "parent" in error.lower() for error in result["errors"])

    def test_validate_orphaned_node(self):
        """Test detection of orphaned nodes (no parent)."""
        spec = create_minimal_spec()

        # Add task without parent
        spec["hierarchy"]["orphan-task"] = {
            "type": "task",
            "title": "Orphaned task",
            "parent": None,
            "children": [],
            "total_tasks": 1,
            "completed_tasks": 0
        }

        result = _validate_spec_integrity(spec)

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert any("no parent" in error.lower() for error in result["errors"])

    def test_validate_child_wrong_parent(self):
        """Test detection of child referencing wrong parent."""
        spec = create_minimal_spec()

        # Add phase-2
        spec["hierarchy"]["phase-2"] = {
            "type": "phase",
            "title": "Phase 2",
            "parent": "spec-root",
            "children": [],
            "total_tasks": 0,
            "completed_tasks": 0
        }

        # Add task claiming phase-1 as parent
        spec["hierarchy"]["task-1-1"] = {
            "type": "task",
            "title": "Task 1",
            "parent": "phase-1",
            "children": [],
            "total_tasks": 1,
            "completed_tasks": 0
        }

        # But phase-2 lists it as child (inconsistent)
        spec["hierarchy"]["phase-2"]["children"].append("task-1-1")

        result = _validate_spec_integrity(spec)

        assert result["valid"] is False
        assert len(result["errors"]) > 0
        # Should detect that task-1-1 is not in phase-1's children
        # or that phase-2 claims a child that doesn't reference it as parent


class TestTransactionIntegration:
    """Integration tests for transaction support with modification functions."""

    def test_transaction_with_remove_node(self):
        """Test transaction rollback with remove_node."""
        spec = create_minimal_spec()

        # Add task
        add_node(spec, "phase-1", {
            "node_id": "task-1-1",
            "type": "task",
            "title": "Task 1"
        })

        try:
            with spec_transaction(spec):
                # Remove task
                remove_node(spec, "task-1-1")

                # Verify removed within transaction
                assert "task-1-1" not in spec["hierarchy"]

                # Trigger rollback
                raise ValueError("Test rollback")
        except ValueError:
            pass

        # Task should be restored
        assert "task-1-1" in spec["hierarchy"]

    def test_transactional_modify_with_complex_operation(self):
        """Test transactional_modify with complex multi-step operation."""
        spec = create_minimal_spec()

        def complex_operation(spec_data):
            # Add multiple nodes
            add_node(spec_data, "phase-1", {
                "node_id": "task-1-1",
                "type": "task",
                "title": "Task 1"
            })
            add_node(spec_data, "task-1-1", {
                "node_id": "task-1-1-1",
                "type": "subtask",
                "title": "Subtask 1"
            })
            add_node(spec_data, "task-1-1", {
                "node_id": "task-1-1-2",
                "type": "subtask",
                "title": "Subtask 2"
            })

            return {
                "success": True,
                "message": "Complex operation completed"
            }

        result = transactional_modify(spec, complex_operation, validate=True)

        assert result["success"] is True
        assert "task-1-1" in spec["hierarchy"]
        assert "task-1-1-1" in spec["hierarchy"]
        assert "task-1-1-2" in spec["hierarchy"]
