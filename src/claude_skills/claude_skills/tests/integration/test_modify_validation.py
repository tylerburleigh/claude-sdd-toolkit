"""
Integration tests for spec modification validation and rollback.

Tests that invalid modifications are rejected and rolled back, leaving
the spec unchanged. Covers transactional modification operations with
automatic validation and rollback on failure.
"""

import json
import pytest
import tempfile
from pathlib import Path
from copy import deepcopy
from claude_skills.sdd_spec_mod.modification import (
    add_node,
    remove_node,
    update_node_field,
    move_node,
    spec_transaction,
    transactional_modify,
    apply_modifications
)


class TestValidationRollback:
    """Integration tests for validation and rollback mechanisms."""

    @pytest.fixture
    def sample_spec(self):
        """Create a valid sample spec for testing."""
        return {
            "spec_id": "test-rollback-001",
            "title": "Test Validation Rollback",
            "metadata": {
                "created_at": "2025-11-06T00:00:00Z",
                "estimated_hours": 10
            },
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "title": "Test Spec",
                    "parent": None,
                    "children": ["phase-1"],
                    "total_tasks": 2,
                    "completed_tasks": 0
                },
                "phase-1": {
                    "type": "phase",
                    "title": "Phase 1",
                    "parent": "spec-root",
                    "children": ["task-1-1", "task-1-2"],
                    "total_tasks": 2,
                    "completed_tasks": 0
                },
                "task-1-1": {
                    "type": "task",
                    "title": "Task 1.1",
                    "description": "First task",
                    "parent": "phase-1",
                    "children": [],
                    "status": "pending",
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "dependencies": {"blocks": [], "blocked_by": [], "depends": []},
                    "metadata": {"estimated_hours": 2}
                },
                "task-1-2": {
                    "type": "task",
                    "title": "Task 1.2",
                    "description": "Second task",
                    "parent": "phase-1",
                    "children": [],
                    "status": "pending",
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "dependencies": {"blocks": [], "blocked_by": [], "depends": []},
                    "metadata": {"estimated_hours": 3}
                }
            }
        }

    def test_transaction_rollback_on_exception(self, sample_spec):
        """Test that spec_transaction rolls back changes on exception."""
        original_spec = deepcopy(sample_spec)

        try:
            with spec_transaction(sample_spec):
                # Make a valid change
                result = add_node(
                    sample_spec,
                    "phase-1",
                    {
                        "node_id": "task-1-3",
                        "type": "task",
                        "title": "Task 1.3",
                        "description": "Third task"
                    }
                )
                assert result["success"], "add_node should succeed"
                assert "task-1-3" in sample_spec["hierarchy"], "Node should be added"

                # Raise an exception to trigger rollback
                raise ValueError("Simulated validation failure")

        except ValueError:
            pass  # Expected

        # Verify spec was rolled back to original state
        assert "task-1-3" not in sample_spec["hierarchy"], "Node should be rolled back"
        assert sample_spec["hierarchy"] == original_spec["hierarchy"], "Hierarchy should match original"

    def test_add_node_with_invalid_type(self, sample_spec):
        """Test that adding node with invalid type fails and rolls back."""
        original_spec = deepcopy(sample_spec)

        # Attempt to add node with invalid type
        result = add_node(
            sample_spec,
            "phase-1",
            {
                "node_id": "task-1-3",
                "type": "invalid_type",  # Invalid type
                "title": "Task 1.3",
                "description": "Third task"
            }
        )

        # Operation should fail
        assert not result["success"], "add_node should fail with invalid type"
        assert "Invalid node type" in result["message"], "Error message should mention invalid type"

        # Verify spec unchanged
        assert "task-1-3" not in sample_spec["hierarchy"], "Node should not be added"
        assert sample_spec == original_spec, "Spec should be unchanged"

    def test_add_node_with_empty_title(self, sample_spec):
        """Test that adding node with empty title fails and rolls back."""
        original_spec = deepcopy(sample_spec)

        # Attempt to add node with empty title
        result = add_node(
            sample_spec,
            "phase-1",
            {
                "node_id": "task-1-3",
                "type": "task",
                "title": "   ",  # Empty/whitespace title
                "description": "Third task"
            }
        )

        # Operation should fail
        assert not result["success"], "add_node should fail with empty title"
        assert "title cannot be empty" in result["message"].lower(), "Error message should mention empty title"

        # Verify spec unchanged
        assert "task-1-3" not in sample_spec["hierarchy"], "Node should not be added"
        assert sample_spec == original_spec, "Spec should be unchanged"

    def test_add_node_with_duplicate_id(self, sample_spec):
        """Test that adding node with existing ID fails and rolls back."""
        original_spec = deepcopy(sample_spec)

        # Attempt to add node with duplicate ID
        result = add_node(
            sample_spec,
            "phase-1",
            {
                "node_id": "task-1-1",  # Duplicate ID
                "type": "task",
                "title": "Duplicate Task",
                "description": "Should fail"
            }
        )

        # Operation should fail
        assert not result["success"], "add_node should fail with duplicate ID"
        assert "already exists" in result["message"].lower(), "Error message should mention duplicate ID"

        # Verify spec unchanged
        assert sample_spec == original_spec, "Spec should be unchanged"
        # Verify original task-1-1 is still intact
        assert sample_spec["hierarchy"]["task-1-1"]["title"] == "Task 1.1", "Original node should be unchanged"

    def test_add_node_with_nonexistent_parent(self, sample_spec):
        """Test that adding node to nonexistent parent fails with exception."""
        original_spec = deepcopy(sample_spec)

        # Attempt to add node to nonexistent parent
        with pytest.raises(KeyError) as exc_info:
            add_node(
                sample_spec,
                "phase-99",  # Nonexistent parent
                {
                    "node_id": "task-99-1",
                    "type": "task",
                    "title": "Orphan Task",
                    "description": "Should fail"
                }
            )

        assert "not found" in str(exc_info.value).lower(), "Exception should mention parent not found"

        # Verify spec unchanged
        assert "task-99-1" not in sample_spec["hierarchy"], "Node should not be added"
        assert sample_spec == original_spec, "Spec should be unchanged"

    def test_remove_node_with_children_no_cascade(self, sample_spec):
        """Test that removing node with children (no cascade) fails and rolls back."""
        original_spec = deepcopy(sample_spec)

        # Attempt to remove phase-1 which has children
        result = remove_node(sample_spec, "phase-1", cascade=False)

        # Operation should fail
        assert not result["success"], "remove_node should fail without cascade"
        assert "has" in result["message"] and "children" in result["message"], "Error message should mention children"

        # Verify spec unchanged
        assert "phase-1" in sample_spec["hierarchy"], "Phase should not be removed"
        assert sample_spec == original_spec, "Spec should be unchanged"

    def test_remove_node_nonexistent(self, sample_spec):
        """Test that removing nonexistent node fails with exception."""
        original_spec = deepcopy(sample_spec)

        # Attempt to remove nonexistent node
        with pytest.raises(KeyError) as exc_info:
            remove_node(sample_spec, "task-99-99", cascade=False)

        assert "not found" in str(exc_info.value).lower(), "Exception should mention node not found"

        # Verify spec unchanged
        assert sample_spec == original_spec, "Spec should be unchanged"

    def test_update_field_invalid_status(self, sample_spec):
        """Test that updating with invalid status value fails and rolls back."""
        original_spec = deepcopy(sample_spec)
        original_status = sample_spec["hierarchy"]["task-1-1"]["status"]

        # Attempt to update with invalid status
        result = update_node_field(sample_spec, "task-1-1", "status", "invalid_status")

        # Operation should fail
        assert not result["success"], "update_node_field should fail with invalid status"
        assert "Invalid status" in result["message"], "Error message should mention invalid status"

        # Verify spec unchanged
        assert sample_spec["hierarchy"]["task-1-1"]["status"] == original_status, "Status should be unchanged"
        assert sample_spec == original_spec, "Spec should be unchanged"

    def test_update_field_protected_field(self, sample_spec):
        """Test that updating protected field fails with exception."""
        original_spec = deepcopy(sample_spec)

        # Attempt to update protected field
        with pytest.raises(ValueError) as exc_info:
            update_node_field(sample_spec, "task-1-1", "parent", "phase-2")

        assert "protected" in str(exc_info.value).lower(), "Exception should mention protected field"

        # Verify spec unchanged
        assert sample_spec == original_spec, "Spec should be unchanged"

    def test_move_node_creates_circular_dependency(self, sample_spec):
        """Test that moving node to create circular dependency fails and rolls back."""
        # First add a child to task-1-1
        add_result = add_node(
            sample_spec,
            "task-1-1",
            {
                "node_id": "subtask-1-1-1",
                "type": "subtask",
                "title": "Subtask 1.1.1",
                "description": "Child of task-1-1"
            }
        )
        assert add_result["success"], "Should successfully add subtask"

        original_spec = deepcopy(sample_spec)

        # Attempt to move task-1-1 under its own child (circular dependency)
        result = move_node(sample_spec, "task-1-1", "subtask-1-1-1")

        # Operation should fail
        assert not result["success"], "move_node should fail with circular dependency"
        assert "circular" in result["message"].lower(), "Error message should mention circular dependency"

        # Verify spec unchanged
        assert sample_spec["hierarchy"]["task-1-1"]["parent"] == "phase-1", "Parent should be unchanged"
        assert sample_spec == original_spec, "Spec should be unchanged"

    def test_move_node_to_nonexistent_parent(self, sample_spec):
        """Test that moving node to nonexistent parent fails with exception."""
        original_spec = deepcopy(sample_spec)

        # Attempt to move to nonexistent parent
        with pytest.raises(KeyError) as exc_info:
            move_node(sample_spec, "task-1-1", "phase-99")

        assert "not found" in str(exc_info.value).lower(), "Exception should mention parent not found"

        # Verify spec unchanged
        assert sample_spec == original_spec, "Spec should be unchanged"

    def test_transactional_modify_with_validation(self, sample_spec):
        """Test transactional_modify with validation enabled."""
        original_spec = deepcopy(sample_spec)

        # Define an operation that succeeds
        def valid_operation(spec):
            return add_node(
                spec,
                "phase-1",
                {
                    "node_id": "task-1-3",
                    "type": "task",
                    "title": "Task 1.3",
                    "description": "Valid task"
                }
            )

        # Execute with validation
        result = transactional_modify(sample_spec, valid_operation, validate=True)

        # Operation should succeed
        assert result["success"], "Valid operation should succeed"
        assert "task-1-3" in sample_spec["hierarchy"], "Node should be added"

        # Now test with an operation that fails
        sample_spec2 = deepcopy(original_spec)

        def invalid_operation(spec):
            return add_node(
                spec,
                "phase-1",
                {
                    "node_id": "task-1-3",
                    "type": "invalid_type",  # Invalid type
                    "title": "Task 1.3"
                }
            )

        result2 = transactional_modify(sample_spec2, invalid_operation, validate=True)

        # Operation should fail and roll back
        assert not result2["success"], "Invalid operation should fail"
        assert "rolled back" in result2["message"].lower(), "Message should mention rollback"
        assert "task-1-3" not in sample_spec2["hierarchy"], "Node should not be added"
        assert sample_spec2 == original_spec, "Spec should be rolled back"

    def test_apply_modifications_with_validation(self, sample_spec, tmp_path):
        """Test apply_modifications with per-operation rollback (no full validation)."""
        original_spec = deepcopy(sample_spec)

        # Create modifications file with one valid and one invalid operation
        mod_file = tmp_path / "modifications.json"
        modifications = {
            "modifications": [
                {
                    "operation": "add_node",
                    "parent_id": "phase-1",
                    "node_data": {
                        "node_id": "task-1-3",
                        "type": "task",
                        "title": "Valid Task",
                        "description": "This should succeed"
                    }
                },
                {
                    "operation": "add_node",
                    "parent_id": "phase-1",
                    "node_data": {
                        "node_id": "task-1-4",
                        "type": "invalid_type",  # Invalid type
                        "title": "Invalid Task",
                        "description": "This should fail"
                    }
                }
            ]
        }

        with open(mod_file, 'w', encoding='utf-8') as f:
            json.dump(modifications, f)

        # Apply modifications WITHOUT full spec validation (validate_after_each=False)
        # This tests per-operation rollback without requiring complete spec structure
        result = apply_modifications(sample_spec, str(mod_file), validate_after_each=False)

        # Overall result should indicate partial success
        assert not result["success"], "Overall should fail due to invalid operation"
        assert result["successful"] == 1, "First operation should succeed"
        assert result["failed"] == 1, "Second operation should fail"

        # Verify first operation succeeded
        assert "task-1-3" in sample_spec["hierarchy"], "Valid task should be added"

        # Verify second operation failed and rolled back
        assert "task-1-4" not in sample_spec["hierarchy"], "Invalid task should not be added"

        # Check detailed results
        assert len(result["results"]) == 2, "Should have 2 operation results"
        assert result["results"][0]["success"], "First operation should succeed"
        assert not result["results"][1]["success"], "Second operation should fail"
        assert "Invalid node type" in result["results"][1]["message"], "Should mention invalid type"

    def test_apply_modifications_with_missing_fields(self, sample_spec, tmp_path):
        """Test apply_modifications with operations missing required fields."""
        original_spec = deepcopy(sample_spec)

        # Create modifications file with missing required fields
        mod_file = tmp_path / "modifications.json"
        modifications = {
            "modifications": [
                {
                    "operation": "add_node",
                    # Missing parent_id
                    "node_data": {
                        "node_id": "task-1-3",
                        "type": "task",
                        "title": "Task 1.3"
                    }
                },
                {
                    "operation": "update_node_field",
                    "node_id": "task-1-1",
                    # Missing field and value
                }
            ]
        }

        with open(mod_file, 'w', encoding='utf-8') as f:
            json.dump(modifications, f)

        # Apply modifications
        result = apply_modifications(sample_spec, str(mod_file), validate_after_each=True)

        # All operations should fail
        assert not result["success"], "Overall should fail"
        assert result["successful"] == 0, "No operations should succeed"
        assert result["failed"] == 2, "Both operations should fail"

        # Verify spec unchanged
        assert sample_spec == original_spec, "Spec should be unchanged"

        # Check error messages
        assert "Missing required field" in result["results"][0]["message"], "Should mention missing field"
        assert "Missing required field" in result["results"][1]["message"], "Should mention missing fields"

    def test_apply_modifications_with_invalid_json(self, sample_spec, tmp_path):
        """Test apply_modifications with invalid JSON file."""
        # Create invalid JSON file
        mod_file = tmp_path / "invalid.json"
        with open(mod_file, 'w', encoding='utf-8') as f:
            f.write("{ invalid json content }")

        # Attempt to apply modifications
        with pytest.raises(json.JSONDecodeError):
            apply_modifications(sample_spec, str(mod_file))

    def test_apply_modifications_with_nonexistent_file(self, sample_spec):
        """Test apply_modifications with nonexistent file."""
        # Attempt to apply modifications from nonexistent file
        with pytest.raises(FileNotFoundError):
            apply_modifications(sample_spec, "/nonexistent/path/modifications.json")

    def test_complex_rollback_scenario(self, sample_spec):
        """Test complex scenario with multiple operations and rollback."""
        original_spec = deepcopy(sample_spec)

        try:
            with spec_transaction(sample_spec):
                # Operation 1: Add a new task (succeeds)
                result1 = add_node(
                    sample_spec,
                    "phase-1",
                    {
                        "node_id": "task-1-3",
                        "type": "task",
                        "title": "Task 1.3",
                        "description": "Third task"
                    }
                )
                assert result1["success"], "First add should succeed"

                # Operation 2: Update existing task (succeeds)
                result2 = update_node_field(sample_spec, "task-1-1", "description", "Updated description")
                assert result2["success"], "Update should succeed"

                # Operation 3: Add another task (succeeds)
                result3 = add_node(
                    sample_spec,
                    "phase-1",
                    {
                        "node_id": "task-1-4",
                        "type": "task",
                        "title": "Task 1.4",
                        "description": "Fourth task"
                    }
                )
                assert result3["success"], "Second add should succeed"

                # Verify all changes were made
                assert "task-1-3" in sample_spec["hierarchy"], "task-1-3 should exist"
                assert "task-1-4" in sample_spec["hierarchy"], "task-1-4 should exist"
                assert sample_spec["hierarchy"]["task-1-1"]["description"] == "Updated description"

                # Simulate validation failure
                raise ValueError("Validation failed after multiple operations")

        except ValueError:
            pass  # Expected

        # Verify ALL changes were rolled back
        assert "task-1-3" not in sample_spec["hierarchy"], "task-1-3 should be rolled back"
        assert "task-1-4" not in sample_spec["hierarchy"], "task-1-4 should be rolled back"
        assert sample_spec["hierarchy"]["task-1-1"]["description"] == "First task", "Description should be rolled back"
        assert sample_spec == original_spec, "Spec should match original completely"


class TestValidationEdgeCases:
    """Edge case tests for validation and rollback."""

    @pytest.fixture
    def minimal_spec(self):
        """Create minimal valid spec."""
        return {
            "spec_id": "minimal-001",
            "title": "Minimal Spec",
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "title": "Root",
                    "parent": None,
                    "children": [],
                    "total_tasks": 0,
                    "completed_tasks": 0
                }
            }
        }

    def test_add_node_with_invalid_dependencies_structure(self, minimal_spec):
        """Test adding node with invalid dependencies structure."""
        original_spec = deepcopy(minimal_spec)

        # Attempt to add node with invalid dependencies (not a dict)
        result = add_node(
            minimal_spec,
            "spec-root",
            {
                "node_id": "phase-1",
                "type": "phase",
                "title": "Phase 1",
                "dependencies": "invalid"  # Should be a dict
            }
        )

        # Operation should fail
        assert not result["success"], "add_node should fail with invalid dependencies"
        assert "dependencies must be a dictionary" in result["message"], "Error message should mention dependencies type"

        # Verify spec unchanged
        assert minimal_spec == original_spec, "Spec should be unchanged"

    def test_update_metadata_with_invalid_type(self, minimal_spec):
        """Test updating metadata with invalid type."""
        # First add a node
        add_node(
            minimal_spec,
            "spec-root",
            {
                "node_id": "phase-1",
                "type": "phase",
                "title": "Phase 1"
            }
        )

        original_spec = deepcopy(minimal_spec)

        # Attempt to update metadata with non-dict value
        result = update_node_field(minimal_spec, "phase-1", "metadata", "invalid")

        # Operation should fail
        assert not result["success"], "update should fail with invalid metadata type"
        assert "metadata value must be a dictionary" in result["message"], "Error message should mention metadata type"

        # Verify spec unchanged
        assert minimal_spec == original_spec, "Spec should be unchanged"

    def test_remove_spec_root(self, minimal_spec):
        """Test that removing spec-root raises exception."""
        original_spec = deepcopy(minimal_spec)

        # Attempt to remove spec-root
        with pytest.raises(ValueError) as exc_info:
            remove_node(minimal_spec, "spec-root")

        assert "cannot remove spec-root" in str(exc_info.value).lower(), "Exception should mention spec-root"

        # Verify spec unchanged
        assert minimal_spec == original_spec, "Spec should be unchanged"

    def test_move_spec_root(self, minimal_spec):
        """Test that moving spec-root raises exception."""
        # Add a phase first
        add_node(
            minimal_spec,
            "spec-root",
            {
                "node_id": "phase-1",
                "type": "phase",
                "title": "Phase 1"
            }
        )

        original_spec = deepcopy(minimal_spec)

        # Attempt to move spec-root
        with pytest.raises(ValueError) as exc_info:
            move_node(minimal_spec, "spec-root", "phase-1")

        assert "cannot move spec-root" in str(exc_info.value).lower(), "Exception should mention spec-root"

        # Verify spec unchanged
        assert minimal_spec == original_spec, "Spec should be unchanged"
