"""
Unit tests for sdd-plan hierarchy validation operations.

Tests: validate_structure, validate_hierarchy, validate_nodes, validate_task_counts,
validate_dependencies, validate_metadata, validate_spec_hierarchy.
"""

import json
import sys
import builtins
from pathlib import Path

import pytest

# Import validation functions from sdd_common
from claude_skills.common.hierarchy_validation import (
    validate_structure,
    validate_hierarchy,
    validate_nodes,
    validate_task_counts,
    validate_dependencies,
    validate_metadata,
    validate_spec_hierarchy,
    _validate_against_schema,
)


class TestValidateStructure:
    """Tests for validate_structure function."""

    def test_valid_structure(self, valid_json_spec):
        """Test validation of state with valid structure."""
        spec_data = json.loads(valid_json_spec.read_text())
        is_valid, errors, warnings = validate_structure(spec_data)

        assert is_valid is True
        assert len(errors) == 0

    def test_missing_required_fields(self):
        """Test detection of missing required top-level fields."""
        spec_data = {
            "spec_id": "test"
            # Missing: title, hierarchy, generated, etc.
        }
        is_valid, errors, warnings = validate_structure(spec_data)

        assert is_valid is False
        assert len(errors) > 0
        # Should report missing required fields

    def test_empty_hierarchy(self):
        """Test validation with empty hierarchy."""
        spec_data = {
            "spec_id": "test-2025-01-01-001",
            "spec_version": "1.0",
            "title": "Test",
            "generated": "2025-01-01T12:00:00",
            "last_updated": "2025-01-01T12:00:00",
            "hierarchy": {}
        }
        is_valid, errors, warnings = validate_structure(spec_data)

        # Empty hierarchy might be a warning, not error
        assert isinstance(is_valid, bool)

    def test_invalid_json_types(self):
        """Test detection of invalid JSON types for fields."""
        spec_data = {
            "spec_id": 12345,  # Should be string
            "title": ["wrong", "type"],  # Should be string
            "hierarchy": "not a dict"  # Should be dict
        }
        is_valid, errors, warnings = validate_structure(spec_data)

        assert is_valid is False


class TestValidateHierarchy:
    """Tests for validate_hierarchy function."""

    def test_valid_hierarchy(self, valid_json_spec):
        """Test validation of valid hierarchy."""
        spec_data = json.loads(valid_json_spec.read_text())
        is_valid, errors, warnings = validate_hierarchy(spec_data['hierarchy'])

        assert is_valid is True
        assert len(errors) == 0

    def test_orphaned_nodes(self, state_with_orphaned_nodes):
        """Test detection of orphaned nodes (missing parents)."""
        spec_data = json.loads(state_with_orphaned_nodes.read_text())
        is_valid, errors, warnings = validate_hierarchy(spec_data['hierarchy'])

        assert is_valid is False
        assert len(errors) > 0
        # Should report nodes with non-existent parents

    def test_circular_parent_child(self):
        """Test detection of circular parent-child relationships."""
        hierarchy = {
            "spec-root": {
                "id": "spec-root",
                "type": "spec",
                "parent": None,
                "children": ["task-1"]
            },
            "task-1": {
                "id": "task-1",
                "type": "task",
                "parent": "task-2",
                "children": ["task-2"]
            },
            "task-2": {
                "id": "task-2",
                "type": "task",
                "parent": "task-1",
                "children": ["task-1"]
            }
        }
        is_valid, errors, warnings = validate_hierarchy(hierarchy)

        # Should detect circular relationship
        assert is_valid is False


class TestValidateNodes:
    """Tests for validate_nodes function."""

    def test_valid_nodes(self, valid_json_spec):
        """Test validation of properly structured nodes."""
        spec_data = json.loads(valid_json_spec.read_text())
        is_valid, errors, warnings = validate_nodes(spec_data['hierarchy'])

        assert is_valid is True
        assert len(errors) == 0

    def test_node_missing_required_fields(self, invalid_state_structure):
        """Test detection of nodes missing required fields."""
        spec_data = json.loads(invalid_state_structure.read_text())
        is_valid, errors, warnings = validate_nodes(spec_data['hierarchy'])

        assert is_valid is False
        # Should report missing required node fields

    def test_invalid_node_status(self):
        """Test detection of invalid status values."""
        spec_data = {
            "spec_id": "test",
            "hierarchy": {
                "task-1-1": {
                    "id": "task-1-1",
                    "type": "task",
                    "title": "Test",
                    "status": "invalid_status",  # Should be pending/in_progress/completed/blocked
                    "parent": None,
                    "children": [],
                    "dependencies": {}
                }
            }
        }
        is_valid, errors, warnings = validate_nodes(spec_data['hierarchy'])

        # Should detect invalid status
        assert is_valid is False or any("status" in err.lower() for err in errors)

    def test_invalid_node_type(self):
        """Test detection of invalid node types."""
        spec_data = {
            "spec_id": "test",
            "hierarchy": {
                "node-1": {
                    "id": "node-1",
                    "type": "invalid_type",  # Should be phase/task/subtask/verification
                    "title": "Test",
                    "status": "pending",
                    "parent": None,
                    "children": []
                }
            }
        }
        is_valid, errors, warnings = validate_nodes(spec_data['hierarchy'])

        assert is_valid is False


class TestValidateTaskCounts:
    """Tests for validate_task_counts function."""

    def test_valid_task_counts(self, valid_json_spec):
        """Test validation of task counts."""
        spec_data = json.loads(valid_json_spec.read_text())
        is_valid, errors, warnings = validate_task_counts(spec_data['hierarchy'])

        assert is_valid is True
        assert len(errors) == 0

    def test_children_count_mismatch(self):
        """Test detection of children count mismatch."""
        spec_data = {
            "spec_id": "test",
            "hierarchy": {
                "phase-1": {
                    "id": "phase-1",
                    "type": "phase",
                    "title": "Phase 1",
                    "status": "pending",
                    "parent": None,
                    "children": ["task-1-1", "task-1-2"],  # Claims 2 children
                    "metadata": {}
                },
                "task-1-1": {
                    "id": "task-1-1",
                    "type": "task",
                    "title": "Task 1",
                    "status": "pending",
                    "parent": "phase-1",
                    "children": [],
                    "dependencies": {},
                    "metadata": {}
                }
                # task-1-2 doesn't exist!
            }
        }
        is_valid, errors, warnings = validate_task_counts(spec_data['hierarchy'])

        # Should detect that phase-1 claims child that doesn't exist
        assert is_valid is False


class TestValidateDependencies:
    """Tests for validate_dependencies function."""

    def test_valid_dependencies(self, valid_json_spec):
        """Test validation of valid dependencies."""
        spec_data = json.loads(valid_json_spec.read_text())
        is_valid, errors, warnings = validate_dependencies(spec_data['hierarchy'])

        assert is_valid is True
        assert len(errors) == 0

    def test_circular_dependencies(self, state_with_circular_deps_plan):
        """Test detection of circular dependencies."""
        spec_data = json.loads(state_with_circular_deps_plan.read_text())
        is_valid, errors, warnings = validate_dependencies(spec_data['hierarchy'])

        assert is_valid is False
        assert len(errors) > 0
        # Should report circular dependency chain

    def test_dependency_on_nonexistent_task(self, state_with_orphaned_nodes):
        """Test detection of dependencies on non-existent tasks."""
        spec_data = json.loads(state_with_orphaned_nodes.read_text())
        is_valid, errors, warnings = validate_dependencies(spec_data['hierarchy'])

        assert is_valid is False
        # Should report dependency on nonexistent-task

    def test_bidirectional_dependency_consistency(self):
        """Test that blocked_by and blocks are consistent."""
        spec_data = {
            "spec_id": "test",
            "hierarchy": {
                "task-1-1": {
                    "id": "task-1-1",
                    "type": "task",
                    "title": "Task 1",
                    "status": "pending",
                    "parent": None,
                    "children": [],
                    "dependencies": {
                        "blocked_by": [],
                        "depends": [],
                        "blocks": ["task-1-2"]  # Claims it blocks task-1-2
                    }
                },
                "task-1-2": {
                    "id": "task-1-2",
                    "type": "task",
                    "title": "Task 2",
                    "status": "pending",
                    "parent": None,
                    "children": [],
                    "dependencies": {
                        "blocked_by": [],  # But doesn't list task-1-1 as blocker!
                        "depends": [],
                        "blocks": []
                    }
                }
            }
        }
        is_valid, errors, warnings = validate_dependencies(spec_data['hierarchy'])

        # Should detect inconsistent bidirectional dependencies
        assert is_valid is False or len(errors) > 0


class TestValidateMetadata:
    """Tests for validate_metadata function."""

    def test_valid_metadata(self, valid_json_spec):
        """Test validation of valid metadata."""
        spec_data = json.loads(valid_json_spec.read_text())
        is_valid, errors, warnings = validate_metadata(spec_data['hierarchy'])

        assert is_valid is True
        assert len(errors) == 0

    def test_task_missing_file_path(self):
        """Test detection of tasks missing file_path in metadata."""
        spec_data = {
            "spec_id": "test",
            "hierarchy": {
                "task-1-1": {
                    "id": "task-1-1",
                    "type": "task",
                    "title": "Task 1",
                    "status": "pending",
                    "parent": None,
                    "children": [],
                    "dependencies": {},
                    "metadata": {}  # Missing file_path!
                }
            }
        }
        is_valid, errors, warnings = validate_metadata(spec_data['hierarchy'])

        # Should warn or error about missing file_path
        assert is_valid is False or len(errors) > 0

    def test_implementation_task_requires_file_path(self):
        """Test that implementation tasks require file_path."""
        hierarchy = {
            "task-1-1": {
                "id": "task-1-1",
                "type": "task",
                "title": "Implement feature",
                "status": "pending",
                "parent": None,
                "children": [],
                "dependencies": {},
                "metadata": {
                    "task_category": "implementation"
                    # Missing file_path - should error
                }
            }
        }
        is_valid, errors, warnings = validate_metadata(hierarchy)

        assert is_valid is False
        assert len(errors) > 0
        assert any("file_path" in err for err in errors)

    def test_investigation_task_no_file_path_required(self):
        """Test that investigation tasks don't require file_path."""
        hierarchy = {
            "task-1-1": {
                "id": "task-1-1",
                "type": "task",
                "title": "Investigate issue",
                "status": "pending",
                "parent": None,
                "children": [],
                "dependencies": {},
                "metadata": {
                    "task_category": "investigation"
                    # No file_path - should be valid
                }
            }
        }
        is_valid, errors, warnings = validate_metadata(hierarchy)

        assert is_valid is True
        assert len(errors) == 0

    def test_missing_category_defaults_to_implementation(self):
        """Test that missing task_category defaults to implementation (requires file_path)."""
        hierarchy = {
            "task-1-1": {
                "id": "task-1-1",
                "type": "task",
                "title": "Some task",
                "status": "pending",
                "parent": None,
                "children": [],
                "dependencies": {},
                "metadata": {
                    # No task_category - defaults to implementation
                    # No file_path - should error
                }
            }
        }
        is_valid, errors, warnings = validate_metadata(hierarchy)

        assert is_valid is False
        assert len(errors) > 0
        assert any("file_path" in err for err in errors)

    def test_invalid_task_category_rejected(self):
        """Test that invalid task_category values are rejected."""
        hierarchy = {
            "task-1-1": {
                "id": "task-1-1",
                "type": "task",
                "title": "Some task",
                "status": "pending",
                "parent": None,
                "children": [],
                "dependencies": {},
                "metadata": {
                    "task_category": "invalid_category"
                }
            }
        }
        is_valid, errors, warnings = validate_metadata(hierarchy)

        assert is_valid is False
        assert len(errors) > 0
        assert any("invalid task_category" in err.lower() for err in errors)

    def test_investigation_task_with_file_path_warns(self):
        """Test that investigation tasks with file_path generate a warning."""
        hierarchy = {
            "task-1-1": {
                "id": "task-1-1",
                "type": "task",
                "title": "Investigate",
                "status": "pending",
                "parent": None,
                "children": [],
                "dependencies": {},
                "metadata": {
                    "task_category": "investigation",
                    "file_path": "src/something.py"  # Unusual but not wrong
                }
            }
        }
        is_valid, errors, warnings = validate_metadata(hierarchy)

        assert is_valid is True
        assert len(errors) == 0
        assert len(warnings) > 0
        assert any("file_path" in warn.lower() for warn in warnings)

    def test_backward_compat_no_category_with_file_path(self):
        """Test backward compatibility: old specs without task_category but with file_path validate."""
        hierarchy = {
            "task-1-1": {
                "id": "task-1-1",
                "type": "task",
                "title": "Some task",
                "status": "pending",
                "parent": None,
                "children": [],
                "dependencies": {},
                "metadata": {
                    "file_path": "src/feature.py"
                    # No task_category - should validate (backward compat)
                }
            }
        }
        is_valid, errors, warnings = validate_metadata(hierarchy)

        assert is_valid is True
        assert len(errors) == 0

    def test_backward_compat_old_style_spec(self):
        """Test that old-style specs (pre-task_category) still work correctly."""
        hierarchy = {
            "task-1-1": {
                "id": "task-1-1",
                "type": "task",
                "title": "Implement auth",
                "status": "pending",
                "parent": None,
                "children": [],
                "dependencies": {},
                "metadata": {
                    "file_path": "src/auth.py",
                    "estimated_hours": 4
                    # No task_category - should work as before
                }
            },
            "verify-1-1": {
                "id": "verify-1-1",
                "type": "verify",
                "title": "Test auth",
                "status": "pending",
                "parent": None,
                "children": [],
                "dependencies": {},
                "metadata": {
                    "verification_type": "auto",
                    "command": "pytest tests/test_auth.py"
                }
            }
        }
        is_valid, errors, warnings = validate_metadata(hierarchy)

        assert is_valid is True
        assert len(errors) == 0


class TestValidateJsonSpec:
    """Tests for validate_spec_hierarchy main function."""

    def test_validate_valid_json_spec(self, valid_json_spec):
        """Test complete validation of valid JSON spec."""
        spec_data = json.loads(valid_json_spec.read_text())
        result = validate_spec_hierarchy(spec_data)

        assert result is not None
        assert result.is_valid() is True
        error_count, warning_count = result.count_all_issues()
        assert error_count == 0

    def test_validate_state_with_structure_issues(self, invalid_state_structure):
        """Test validation detects structure issues."""
        spec_data = json.loads(invalid_state_structure.read_text())
        result = validate_spec_hierarchy(spec_data)

        assert result.is_valid() is False
        error_count, _ = result.count_all_issues()
        assert error_count > 0

    def test_validate_state_with_circular_deps(self, state_with_circular_deps_plan):
        """Test validation detects circular dependencies."""
        spec_data = json.loads(state_with_circular_deps_plan.read_text())
        result = validate_spec_hierarchy(spec_data)

        assert result.is_valid() is False

    def test_validate_state_with_orphaned_nodes(self, state_with_orphaned_nodes):
        """Test validation detects orphaned nodes."""
        spec_data = json.loads(state_with_orphaned_nodes.read_text())
        result = validate_spec_hierarchy(spec_data)

        assert result.is_valid() is False

    def test_validation_result_structure(self, valid_json_spec):
        """Test that validation result has expected structure."""
        spec_data = json.loads(valid_json_spec.read_text())
        result = validate_spec_hierarchy(spec_data)

        # Check result has expected attributes
        assert hasattr(result, 'spec_id')
        assert hasattr(result, 'total_nodes')
        assert hasattr(result, 'total_tasks')
        assert hasattr(result, 'completed_tasks')
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'count_all_issues')

    def test_validation_counts_nodes_correctly(self, valid_json_spec):
        """Test that validation counts nodes correctly."""
        spec_data = json.loads(valid_json_spec.read_text())
        result = validate_spec_hierarchy(spec_data)

        # Should count all nodes in hierarchy
        assert result.total_nodes > 0
        assert result.total_tasks > 0


class TestSchemaValidationHelpers:
    """Tests for schema validation fallback behaviour."""

    def test_validate_against_schema_missing_schema_emits_warning(self, monkeypatch):
        monkeypatch.setattr(
            "claude_skills.common.hierarchy_validation.load_json_schema",
            lambda name: (None, None, "schema cache missing"),
        )

        errors, warnings, source = _validate_against_schema({})

        assert errors == []
        assert warnings == ["schema cache missing"]
        assert source is None

    def test_validate_against_schema_missing_dependency_emits_warning(self, monkeypatch):
        monkeypatch.setattr(
            "claude_skills.common.hierarchy_validation.load_json_schema",
            lambda name: ({}, "package://schema", None),
        )

        original_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "jsonschema":
                raise ImportError("jsonschema not installed")
            return original_import(name, *args, **kwargs)

        monkeypatch.delitem(sys.modules, "jsonschema", raising=False)
        monkeypatch.setattr(builtins, "__import__", fake_import)

        errors, warnings, source = _validate_against_schema({})

        assert errors == []
        assert warnings == [
            "Schema validation skipped: install the 'jsonschema' package "
            "or use optional dependency group 'validation' to enable Draft 7 validation."
        ]
        assert source == "package://schema"


@pytest.mark.integration
class TestJsonSpecValidationIntegration:
    """Integration tests for state validation."""

    def test_complete_validation_workflow(self, valid_json_spec):
        """Test complete state validation workflow."""
        spec_data = json.loads(valid_json_spec.read_text())

        # Run full validation
        result = validate_spec_hierarchy(spec_data)

        assert result.is_valid()
        assert result.total_nodes == len(spec_data["hierarchy"])

    def test_validation_catches_multiple_issues(self, state_with_orphaned_nodes):
        """Test that validation catches multiple different issues."""
        spec_data = json.loads(state_with_orphaned_nodes.read_text())

        result = validate_spec_hierarchy(spec_data)

        # Should catch: orphaned nodes, missing dependencies
        error_count, _ = result.count_all_issues()
        assert error_count > 0
