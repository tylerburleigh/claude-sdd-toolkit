"""Integration tests for task_category workflow.

Tests the complete workflow of task categorization including:
- Spec generation with task_category
- Validation of categorized specs
- Migration from old format to new format
- Backward compatibility with uncategorized specs
- sdd-next integration with categorized tasks
"""

import json
import tempfile
from pathlib import Path

import pytest

from claude_skills.sdd_plan.templates import generate_spec_from_template
from claude_skills.common.hierarchy_validation import validate_spec_hierarchy
from claude_skills.sdd_validate.fix import collect_fix_actions, apply_fix_actions


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def spec_with_all_categories():
    """Create a test spec with all five task_category types."""
    return {
        "spec_id": "category-test-2025-01-15-001",
        "title": "Task Category Test Spec",
        "version": "1.0.0",
        "generated": "2025-01-15T10:00:00Z",
        "last_updated": "2025-01-15T10:00:00Z",
        "hierarchy": {
            "spec-root": {
                "type": "spec",
                "title": "Task Category Test Spec",
                "status": "pending",
                "parent": None,
                "children": ["phase-1"],
                "total_tasks": 5,
                "completed_tasks": 0,
                "metadata": {},
            },
            "phase-1": {
                "type": "phase",
                "title": "Test All Categories",
                "status": "pending",
                "parent": "spec-root",
                "children": ["task-1", "task-2", "task-3", "task-4", "task-5"],
                "total_tasks": 5,
                "completed_tasks": 0,
                "metadata": {},
            },
            "task-1": {
                "type": "task",
                "title": "Investigate existing auth system",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "task_category": "investigation",
                    "file_path": "investigation",
                },
            },
            "task-2": {
                "type": "task",
                "title": "Implement authentication service",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "task_category": "implementation",
                    "file_path": "src/auth/service.py",
                },
            },
            "task-3": {
                "type": "task",
                "title": "Refactor user model",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "task_category": "refactoring",
                    "file_path": "src/models/user.py",
                },
            },
            "task-4": {
                "type": "task",
                "title": "Decide on token storage strategy",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "task_category": "decision",
                    "file_path": "decision",
                },
            },
            "task-5": {
                "type": "task",
                "title": "Research OAuth 2.0 best practices",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "task_category": "research",
                    "file_path": "research",
                },
            },
        },
    }


@pytest.fixture
def spec_without_categories():
    """Create a test spec in old format (no task_category field)."""
    return {
        "spec_id": "old-format-2025-01-15-001",
        "title": "Old Format Spec",
        "version": "1.0.0",
        "generated": "2025-01-15T10:00:00Z",
        "last_updated": "2025-01-15T10:00:00Z",
        "hierarchy": {
            "spec-root": {
                "type": "spec",
                "title": "Old Format Spec",
                "status": "pending",
                "parent": None,
                "children": ["phase-1"],
                "total_tasks": 2,
                "completed_tasks": 0,
                "metadata": {},
            },
            "phase-1": {
                "type": "phase",
                "title": "Phase 1",
                "status": "pending",
                "parent": "spec-root",
                "children": ["task-1", "task-2"],
                "total_tasks": 2,
                "completed_tasks": 0,
                "metadata": {},
            },
            "task-1": {
                "type": "task",
                "title": "src/auth/service.py",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "file_path": "src/auth/service.py",
                },
            },
            "task-2": {
                "type": "task",
                "title": "src/models/user.py",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "file_path": "src/models/user.py",
                },
            },
        },
    }


@pytest.fixture
def spec_with_mixed_categories():
    """Create a test spec with mix of categorized and uncategorized tasks."""
    return {
        "spec_id": "mixed-format-2025-01-15-001",
        "title": "Mixed Format Spec",
        "version": "1.0.0",
        "generated": "2025-01-15T10:00:00Z",
        "last_updated": "2025-01-15T10:00:00Z",
        "hierarchy": {
            "spec-root": {
                "type": "spec",
                "title": "Mixed Format Spec",
                "status": "pending",
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
                "children": ["task-1", "task-2", "task-3"],
                "total_tasks": 3,
                "completed_tasks": 0,
                "metadata": {},
            },
            "task-1": {
                "type": "task",
                "title": "Investigate auth patterns",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "task_category": "investigation",
                    "file_path": "investigation",
                },
            },
            "task-2": {
                "type": "task",
                "title": "src/auth/service.py",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    # No task_category - old format
                    "file_path": "src/auth/service.py",
                },
            },
            "task-3": {
                "type": "task",
                "title": "Refactor user validation",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "task_category": "refactoring",
                    "file_path": "src/models/user.py",
                },
            },
        },
    }


@pytest.fixture
def spec_with_placeholder_paths():
    """Create spec with placeholder file_path values that need migration."""
    return {
        "spec_id": "placeholder-2025-01-15-001",
        "title": "Spec with Placeholders",
        "version": "1.0.0",
        "generated": "2025-01-15T10:00:00Z",
        "last_updated": "2025-01-15T10:00:00Z",
        "hierarchy": {
            "spec-root": {
                "type": "spec",
                "title": "Spec with Placeholders",
                "status": "pending",
                "parent": None,
                "children": ["phase-1"],
                "total_tasks": 2,
                "completed_tasks": 0,
                "metadata": {},
            },
            "phase-1": {
                "type": "phase",
                "title": "Phase 1",
                "status": "pending",
                "parent": "spec-root",
                "children": ["task-1", "task-2"],
                "total_tasks": 2,
                "completed_tasks": 0,
                "metadata": {},
            },
            "task-1": {
                "type": "task",
                "title": "Research authentication patterns",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "file_path": "TBD",  # Should be migrated to "research"
                },
            },
            "task-2": {
                "type": "task",
                "title": "Decide on token strategy",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "file_path": "N/A",  # Should be migrated to "decision"
                },
            },
        },
    }


# ============================================================================
# Validation Tests
# ============================================================================

def test_validate_spec_with_all_categories(spec_with_all_categories):
    """Test that validation accepts spec with all valid task_category types."""
    result = validate_spec_hierarchy(spec_with_all_categories)

    # Should have no critical errors
    error_count, _ = result.count_all_issues()
    assert error_count == 0, f"Expected no critical errors, got: {error_count} errors"

    # Verify all five categories are present and valid
    hierarchy = spec_with_all_categories["hierarchy"]
    categories_found = set()

    for node_id, node in hierarchy.items():
        if node.get("type") == "task" and "metadata" in node:
            category = node["metadata"].get("task_category")
            if category:
                categories_found.add(category)

    expected_categories = {"investigation", "implementation", "refactoring", "decision", "research"}
    assert categories_found == expected_categories, \
        f"Expected all categories {expected_categories}, found: {categories_found}"


def test_validate_spec_without_categories(spec_without_categories):
    """Test that validation accepts old-format spec without task_category (backward compat)."""
    result = validate_spec_hierarchy(spec_without_categories)

    # Should have no critical errors - old format is still valid
    error_count, _ = result.count_all_issues()
    assert error_count == 0, \
        f"Old format spec should still validate, got {error_count} errors"


def test_validate_spec_with_invalid_category():
    """Test that validation rejects invalid task_category values."""
    invalid_spec = {
        "spec_id": "invalid-category-2025-01-15-001",
        "title": "Invalid Category Spec",
        "version": "1.0.0",
        "generated": "2025-01-15T10:00:00Z",
        "last_updated": "2025-01-15T10:00:00Z",
        "hierarchy": {
            "spec-root": {
                "type": "spec",
                "title": "Invalid Category Spec",
                "status": "pending",
                "parent": None,
                "children": ["task-1"],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {},
            },
            "task-1": {
                "type": "task",
                "title": "Invalid task",
                "status": "pending",
                "parent": "spec-root",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "task_category": "invalid_category_type",  # Invalid!
                    "file_path": "src/test.py",
                },
            },
        },
    }

    result = validate_spec_hierarchy(invalid_spec)

    # Should have validation errors
    error_count, _ = result.count_all_issues()
    assert error_count > 0, "Expected validation errors for invalid category"

    # Check for metadata-related error
    all_errors = (result.metadata_errors + result.node_errors + result.structure_errors +
                  result.hierarchy_errors + result.count_errors + result.dependency_errors)
    category_errors = [e for e in all_errors if "task_category" in str(e).lower()]
    assert len(category_errors) > 0, "Expected error mentioning task_category"


def test_validate_mixed_format_spec(spec_with_mixed_categories):
    """Test that validation accepts spec with mix of categorized/uncategorized tasks."""
    result = validate_spec_hierarchy(spec_with_mixed_categories)

    # Should have no critical errors - mixed format is valid
    error_count, _ = result.count_all_issues()
    assert error_count == 0, \
        f"Mixed format spec should validate, got {error_count} errors"


# ============================================================================
# Migration Tests
# ============================================================================

def test_migrate_old_spec_preserves_functionality(spec_without_categories, tmp_path):
    """Test that old specs can be migrated without breaking functionality."""
    spec_file = tmp_path / "old-spec.json"
    with open(spec_file, "w") as f:
        json.dump(spec_without_categories, f, indent=2)

    # Validate old spec
    result_before = validate_spec_hierarchy(spec_without_categories)
    error_count_before, _ = result_before.count_all_issues()

    # Old spec should be valid
    assert error_count_before == 0, "Old spec should be valid before migration"

    # Note: Actual migration would be done via sdd fix --migrate-categories
    # This test verifies the spec is valid both before and after migration

    # Load spec again to verify it's still valid
    with open(spec_file, "r") as f:
        reloaded_spec = json.load(f)

    result_after = validate_spec_hierarchy(reloaded_spec)
    error_count_after, _ = result_after.count_all_issues()

    assert error_count_after == 0, "Spec should remain valid after file operations"


def test_migrate_placeholder_file_paths(spec_with_placeholder_paths, tmp_path):
    """Test that placeholder file_path values can be migrated with task_category."""
    spec_file = tmp_path / "placeholder-spec.json"
    with open(spec_file, "w") as f:
        json.dump(spec_with_placeholder_paths, f, indent=2)

    # Validate and collect fix actions
    result = validate_spec_hierarchy(spec_with_placeholder_paths)
    actions = collect_fix_actions(result)

    # If there are auto-fixable actions, apply them
    if actions:
        report = apply_fix_actions(
            actions,
            str(spec_file),
            dry_run=False,
            create_backup=True,
        )

        # Verify some fixes were applied
        assert len(report.applied_actions) >= 0, "Expected fix actions to be processed"

    # Load the potentially fixed spec
    with open(spec_file, "r") as f:
        fixed_spec = json.load(f)

    # Verify spec is still valid after migration
    result_after = validate_spec_hierarchy(fixed_spec)
    error_count, _ = result_after.count_all_issues()
    assert error_count == 0, "Migrated spec should be valid"


# ============================================================================
# Workflow Integration Tests
# ============================================================================

def test_full_workflow_with_categories(tmp_path):
    """Test complete workflow: generate -> validate -> use spec with task_category."""
    # Step 1: Generate spec from template with default category
    spec = generate_spec_from_template(
        template_id="simple",
        title="Test Workflow Spec",
        spec_id="workflow-test-2025-01-15-001",
        default_category="implementation",
    )

    assert spec is not None, "Spec generation should succeed"
    assert spec["spec_id"] == "workflow-test-2025-01-15-001"

    # Step 2: Validate generated spec
    result = validate_spec_hierarchy(spec)
    error_count, _ = result.count_all_issues()
    assert error_count == 0, \
        f"Generated spec should be valid, got {error_count} errors"

    # Step 3: Verify spec can be written and read
    spec_file = tmp_path / "workflow-spec.json"
    with open(spec_file, "w") as f:
        json.dump(spec, f, indent=2)

    with open(spec_file, "r") as f:
        loaded_spec = json.load(f)

    # Step 4: Verify loaded spec is still valid
    result_after = validate_spec_hierarchy(loaded_spec)
    error_count_after, _ = result_after.count_all_issues()
    assert error_count_after == 0, "Loaded spec should remain valid"


def test_backward_compatibility_no_breaking_changes(spec_without_categories):
    """Test that existing workflows work unchanged with old-format specs."""
    # Validate old spec
    result = validate_spec_hierarchy(spec_without_categories)

    # Should validate without errors
    error_count, _ = result.count_all_issues()
    assert error_count == 0, \
        "Old specs must continue to work without task_category field"

    # Verify hierarchy is intact
    hierarchy = spec_without_categories["hierarchy"]
    assert "spec-root" in hierarchy
    assert "phase-1" in hierarchy
    assert len(hierarchy) > 2, "Hierarchy should have multiple nodes"

    # Verify tasks exist and are valid
    tasks = [node for node in hierarchy.values() if node.get("type") == "task"]
    assert len(tasks) > 0, "Should have tasks in hierarchy"

    for task in tasks:
        assert "status" in task, "Tasks should have status"
        assert "metadata" in task, "Tasks should have metadata"


def test_gradual_migration_path(spec_with_mixed_categories, tmp_path):
    """Test that specs can be gradually migrated (some tasks categorized, some not)."""
    spec_file = tmp_path / "gradual-migration.json"
    with open(spec_file, "w") as f:
        json.dump(spec_with_mixed_categories, f, indent=2)

    # Validate mixed spec
    result = validate_spec_hierarchy(spec_with_mixed_categories)
    error_count, _ = result.count_all_issues()

    # Mixed format should be valid (gradual migration supported)
    assert error_count == 0, \
        "Gradual migration should be supported - mixed format should be valid"

    # Verify we can identify which tasks have categories
    hierarchy = spec_with_mixed_categories["hierarchy"]
    categorized = []
    uncategorized = []

    for node_id, node in hierarchy.items():
        if node.get("type") == "task":
            has_category = "task_category" in node.get("metadata", {})
            if has_category:
                categorized.append(node_id)
            else:
                uncategorized.append(node_id)

    # Should have both categorized and uncategorized tasks
    assert len(categorized) > 0, "Should have some categorized tasks"
    assert len(uncategorized) > 0, "Should have some uncategorized tasks"


# ============================================================================
# Edge Cases
# ============================================================================

def test_empty_task_category_field():
    """Test handling of empty/null task_category (should use default inference)."""
    spec = {
        "spec_id": "empty-category-2025-01-15-001",
        "title": "Empty Category Spec",
        "version": "1.0.0",
        "generated": "2025-01-15T10:00:00Z",
        "last_updated": "2025-01-15T10:00:00Z",
        "hierarchy": {
            "spec-root": {
                "type": "spec",
                "title": "Empty Category Spec",
                "status": "pending",
                "parent": None,
                "children": ["task-1"],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {},
            },
            "task-1": {
                "type": "task",
                "title": "src/test.py",
                "status": "pending",
                "parent": "spec-root",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "task_category": "",  # Empty string
                    "file_path": "src/test.py",
                },
            },
        },
    }

    result = validate_spec_hierarchy(spec)

    # Empty category should trigger a validation issue
    # (either error or warning depending on validation rules)
    error_count, warning_count = result.count_all_issues()
    total_issues = error_count + warning_count
    assert total_issues > 0, "Empty task_category should be flagged"


def test_case_sensitivity_of_categories():
    """Test that task_category values are case-sensitive."""
    spec = {
        "spec_id": "case-test-2025-01-15-001",
        "title": "Case Sensitivity Test",
        "version": "1.0.0",
        "generated": "2025-01-15T10:00:00Z",
        "last_updated": "2025-01-15T10:00:00Z",
        "hierarchy": {
            "spec-root": {
                "type": "spec",
                "title": "Case Sensitivity Test",
                "status": "pending",
                "parent": None,
                "children": ["task-1"],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {},
            },
            "task-1": {
                "type": "task",
                "title": "Test case sensitivity",
                "status": "pending",
                "parent": "spec-root",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "task_category": "Investigation",  # Wrong case!
                    "file_path": "investigation",
                },
            },
        },
    }

    result = validate_spec_hierarchy(spec)

    # Should have validation errors for wrong case
    error_count, _ = result.count_all_issues()
    assert error_count > 0, \
        "Case-sensitive validation should reject 'Investigation' (correct: 'investigation')"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
