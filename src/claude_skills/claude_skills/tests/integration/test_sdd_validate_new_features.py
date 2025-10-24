"""Integration tests for new sdd-validate features."""

import json
import tempfile
from pathlib import Path

import pytest

from claude_skills.sdd_validate import (
    collect_fix_actions,
    apply_fix_actions,
    compute_diff,
    format_diff_markdown,
)
from claude_skills.common import validate_spec_hierarchy


@pytest.fixture
def spec_with_issues():
    """Create a test spec with various fixable issues."""
    return {
        "spec_id": "test-spec-2025-01-15-001",
        "title": "Test Spec",
        "version": "1.0.0",
        "generated": "2025-01-15T10:00:00Z",
        "last_updated": "2025-01-15T10:00:00",  # Missing Z (fixable)
        "hierarchy": {
            "spec-root": {
                "type": "spec",
                "title": "Test Spec Root",
                "status": "pending",
                "parent": None,
                "children": ["phase-001", "task-orphan"],
                "total_tasks": 5,  # Wrong count (fixable)
                "completed_tasks": 0,
                "metadata": {},
            },
            "phase-001": {
                "type": "phase",
                "title": "Phase 1",
                "status": "inprogress",  # Invalid status (fixable)
                "parent": "spec-root",
                "children": ["task-001"],
                "total_tasks": 2,  # Wrong count (fixable)
                "completed_tasks": 0,
                "metadata": {},
            },
            "task-001": {
                "type": "task",
                "title": "",  # Empty title (fixable)
                "status": "pending",
                "parent": "phase-001",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {},  # Missing file_path (fixable)
            },
            "task-orphan": {
                "type": "task",
                "title": "Orphaned Task",
                "status": "pending",
                "parent": None,  # Orphan (fixable)
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {"file_path": "orphan.md"},
            },
        }
    }


def test_collect_fix_actions_finds_multiple_issues(spec_with_issues):
    """Test that collect_fix_actions finds all auto-fixable issues."""
    result = validate_spec_hierarchy(spec_with_issues)
    actions = collect_fix_actions(result)

    # Should find multiple issues
    assert len(actions) > 0, "Expected to find auto-fixable issues"

    # Check we found various types of fixes
    action_ids = [a.id for a in actions]
    categories = set(a.category for a in actions)

    # Should have fixes from multiple categories
    assert len(categories) > 1, f"Expected fixes from multiple categories, got: {categories}"


def test_apply_fix_actions_with_diff(spec_with_issues, tmp_path):
    """Test apply_fix_actions with diff capture."""
    # Write spec to temp file
    spec_file = tmp_path / "test-spec.json"
    with open(spec_file, "w") as f:
        json.dump(spec_with_issues, f, indent=2)

    # Validate and collect fixes
    result = validate_spec_hierarchy(spec_with_issues)
    actions = collect_fix_actions(result)

    assert actions, "Expected to find fixable actions"

    # Apply fixes with diff capture
    report = apply_fix_actions(
        actions,
        str(spec_file),
        dry_run=False,
        create_backup=True,
        capture_diff=True,
    )

    # Verify report contains diff data
    assert report.before_state is not None, "Expected before_state to be captured"
    assert report.after_state is not None, "Expected after_state to be captured"
    assert len(report.applied_actions) > 0, "Expected some fixes to be applied"

    # Compute diff
    diff = compute_diff(report.before_state, report.after_state)
    assert diff.total_changes > 0, "Expected changes to be detected"

    # Format diff as markdown
    diff_md = format_diff_markdown(diff, "test-spec-2025-01-15-001")
    assert "# Fix Diff Report" in diff_md
    assert "test-spec-2025-01-15-001" in diff_md


def test_selective_fix_application(spec_with_issues, tmp_path):
    """Test that we can selectively apply only certain fixes."""
    spec_file = tmp_path / "test-spec.json"
    with open(spec_file, "w") as f:
        json.dump(spec_with_issues, f, indent=2)

    result = validate_spec_hierarchy(spec_with_issues)
    all_actions = collect_fix_actions(result)

    # Select only metadata fixes
    metadata_actions = [a for a in all_actions if a.category == "metadata"]

    if metadata_actions:
        report = apply_fix_actions(
            metadata_actions,
            str(spec_file),
            dry_run=False,
            create_backup=True,
        )

        # Verify only metadata fixes were applied
        applied_categories = set(a.category for a in report.applied_actions)
        assert applied_categories == {"metadata"} or len(applied_categories) == 0


def test_new_fix_builders_work(spec_with_issues):
    """Test that the new fix builders are functional."""
    result = validate_spec_hierarchy(spec_with_issues)
    actions = collect_fix_actions(result)

    # Group by category
    by_category = {}
    for action in actions:
        by_category.setdefault(action.category, []).append(action)

    # Should have various fix types
    expected_categories = {"node", "counts", "structure"}
    found_categories = set(by_category.keys())

    # At least some overlap with expected categories
    overlap = expected_categories & found_categories
    assert len(overlap) > 0, f"Expected to find fixes in categories {expected_categories}, found: {found_categories}"


def test_diff_computation():
    """Test diff computation with before/after states."""
    before = {
        "spec_id": "test-001",
        "hierarchy": {
            "task-001": {
                "status": "pending",
                "total_tasks": 5,
                "metadata": {"file_path": "old.md"},
            }
        }
    }

    after = {
        "spec_id": "test-001",
        "hierarchy": {
            "task-001": {
                "status": "in_progress",  # Changed
                "total_tasks": 7,  # Changed
                "metadata": {"file_path": "new.md"},  # Changed
            }
        }
    }

    diff = compute_diff(before, after)

    # Should detect 3 changes
    assert diff.total_changes >= 3, f"Expected at least 3 changes, got: {diff.total_changes}"

    # Verify specific changes were detected
    changes_by_field = {c.field_path: c for c in diff.changes if c.location == "task-001"}
    assert "status" in changes_by_field
    assert changes_by_field["status"].old_value == "pending"
    assert changes_by_field["status"].new_value == "in_progress"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
