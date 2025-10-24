"""Unit tests for sdd_validate.fix module."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from claude_skills.common.validation import EnhancedError, JsonSpecValidationResult
from claude_skills.sdd_validate.fix import (
    collect_fix_actions,
    apply_fix_actions,
    FixAction,
    FixReport,
    _build_counts_action,
    _build_metadata_action,
    _build_hierarchy_action,
    _build_date_action,
    _build_status_action,
    _normalize_timestamp,
    _normalize_status,
)


def test_collect_fix_actions_empty():
    """Test collecting actions from a clean validation result."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-001",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
        spec_data={},
    )

    actions = collect_fix_actions(result)

    assert len(actions) == 0


def test_collect_fix_actions_with_enhanced_errors():
    """Test collecting actions from enhanced errors."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-002",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
        spec_data={"hierarchy": {"task-1": {"id": "task-1", "type": "task"}}},
        enhanced_errors=[
            EnhancedError(
                message="Missing metadata",
                severity="warning",
                category="metadata",
                location="task-1",
                auto_fixable=True,
                suggested_fix="Add metadata defaults",
            ),
        ],
    )

    actions = collect_fix_actions(result)

    assert len(actions) >= 1
    assert any(action.category == "metadata" for action in actions)


def test_build_counts_action():
    """Test building counts fix action."""
    error = EnhancedError(
        message="Incorrect task counts",
        severity="error",
        category="counts",
        location="spec-root",
        auto_fixable=True,
        suggested_fix="Recalculate rollups",
    )

    spec_data = {
        "hierarchy": {
            "spec-root": {"id": "spec-root", "type": "root"},
        }
    }

    action = _build_counts_action(error, spec_data)

    assert action is not None
    assert action.id == "counts.recalculate"
    assert action.category == "counts"
    assert action.auto_apply is True
    assert callable(action.apply)


def test_build_metadata_action():
    """Test building metadata fix action."""
    error = EnhancedError(
        message="Missing metadata for task-1",
        severity="warning",
        category="metadata",
        location="task-1",
        auto_fixable=True,
        suggested_fix="Add metadata block",
    )

    spec_data = {
        "hierarchy": {
            "task-1": {"id": "task-1", "type": "task"},
        }
    }

    action = _build_metadata_action(error, spec_data)

    assert action is not None
    assert action.id == "metadata.ensure:task-1"
    assert action.category == "metadata"
    assert action.auto_apply is True

    # Test applying the action
    test_data = {"hierarchy": {"task-1": {"id": "task-1", "type": "task"}}}
    action.apply(test_data)

    assert "metadata" in test_data["hierarchy"]["task-1"]
    assert "file_path" in test_data["hierarchy"]["task-1"]["metadata"]


def test_build_metadata_action_verify():
    """Test building metadata fix action for verification nodes."""
    error = EnhancedError(
        message="Missing metadata for verify-1",
        severity="warning",
        category="metadata",
        location="verify-1",
        auto_fixable=True,
        suggested_fix="Add metadata block",
    )

    spec_data = {
        "hierarchy": {
            "verify-1": {"id": "verify-1", "type": "verify"},
        }
    }

    action = _build_metadata_action(error, spec_data)

    assert action is not None

    # Test applying the action
    test_data = {"hierarchy": {"verify-1": {"id": "verify-1", "type": "verify"}}}
    action.apply(test_data)

    metadata = test_data["hierarchy"]["verify-1"]["metadata"]
    assert "verification_type" in metadata
    assert "command" in metadata
    assert "expected" in metadata


def test_build_hierarchy_action():
    """Test building hierarchy fix action."""
    error = EnhancedError(
        message="'parent-1' lists 'child-1' as child, but 'child-1' has parent='wrong-parent'",
        severity="error",
        category="hierarchy",
        location="parent-1",
        auto_fixable=True,
        suggested_fix="Align parent reference",
    )

    spec_data = {
        "hierarchy": {
            "parent-1": {"id": "parent-1", "type": "phase", "children": ["child-1"]},
            "child-1": {"id": "child-1", "type": "task", "parent": "wrong-parent"},
        }
    }

    action = _build_hierarchy_action(error, spec_data)

    assert action is not None
    assert action.category == "hierarchy"
    assert "child-1" in action.id

    # Test applying the action
    test_data = {
        "hierarchy": {
            "parent-1": {"id": "parent-1", "type": "phase", "children": ["child-1"]},
            "child-1": {"id": "child-1", "type": "task", "parent": "wrong-parent"},
        }
    }
    action.apply(test_data)

    assert test_data["hierarchy"]["child-1"]["parent"] == "parent-1"


def test_build_date_action():
    """Test building date normalization action."""
    error = EnhancedError(
        message="Invalid generated timestamp",
        severity="warning",
        category="structure",
        location=None,
        auto_fixable=True,
        suggested_fix="Normalize ISO 8601 dates",
    )

    spec_data = {"generated": "2025-01-20 10:00:00"}

    action = _build_date_action(error, spec_data)

    assert action is not None
    assert action.category == "structure"
    assert "dates" in action.id

    # Test applying the action
    test_data = {"generated": "2025-01-20 10:00:00", "last_updated": "2025-01-20T11:00:00"}
    action.apply(test_data)

    assert "T" in test_data["generated"]
    assert test_data["generated"].endswith("Z")


def test_build_status_action():
    """Test building status normalization action."""
    error = EnhancedError(
        message="Invalid status for task-1",
        severity="warning",
        category="node",
        location="task-1",
        auto_fixable=True,
        suggested_fix="Normalize status field",
    )

    spec_data = {
        "hierarchy": {
            "task-1": {"id": "task-1", "type": "task", "status": "inprogress"},
        }
    }

    action = _build_status_action(error, spec_data)

    assert action is not None
    assert action.category == "node"
    assert "task-1" in action.id

    # Test applying the action
    test_data = {
        "hierarchy": {
            "task-1": {"id": "task-1", "type": "task", "status": "inprogress"},
        }
    }
    action.apply(test_data)

    assert test_data["hierarchy"]["task-1"]["status"] == "in_progress"


def test_normalize_timestamp():
    """Test timestamp normalization."""
    # Test various formats
    assert _normalize_timestamp("2025-01-20T10:00:00Z") == "2025-01-20T10:00:00Z"
    assert _normalize_timestamp("2025-01-20 10:00:00") == "2025-01-20T10:00:00Z"
    assert _normalize_timestamp("2025-01-20T10:00:00") == "2025-01-20T10:00:00Z"
    assert _normalize_timestamp(None) is None
    assert _normalize_timestamp("") is None
    assert _normalize_timestamp("invalid") is None


def test_normalize_status():
    """Test status normalization."""
    assert _normalize_status("pending") == "pending"
    assert _normalize_status("in_progress") == "in_progress"
    assert _normalize_status("completed") == "completed"
    assert _normalize_status("blocked") == "blocked"

    # Test normalization of variants
    assert _normalize_status("inprogress") == "in_progress"
    assert _normalize_status("in-progress") == "in_progress"
    assert _normalize_status("todo") == "pending"
    assert _normalize_status("done") == "completed"
    assert _normalize_status("complete") == "completed"

    # Test invalid values default to pending
    assert _normalize_status("invalid") == "pending"
    assert _normalize_status(None) == "pending"
    assert _normalize_status("") == "pending"


def test_apply_fix_actions_dry_run():
    """Test applying actions in dry-run mode."""
    actions = [
        FixAction(
            id="test-1",
            description="Test action",
            category="test",
            severity="warning",
            auto_apply=True,
            preview="Test preview",
            apply=lambda data: None,
        )
    ]

    with patch("builtins.open", mock_open(read_data='{"spec_id": "test"}')):
        report = apply_fix_actions(actions, "/tmp/test.json", dry_run=True, create_backup=False)

    assert report.spec_path == "/tmp/test.json"
    assert len(report.applied_actions) == 0
    assert len(report.skipped_actions) == 1
    assert report.backup_path is None


@patch("claude_skills.sdd_validate.fix.recalculate_progress")
@patch("claude_skills.sdd_validate.fix.validate_spec_hierarchy")
@patch("claude_skills.sdd_validate.fix.save_json_spec")
@patch("claude_skills.sdd_validate.fix.backup_json_spec")
def test_apply_fix_actions_real_apply(mock_backup, mock_save, mock_validate, mock_recalc):
    """Test actually applying fix actions."""
    mock_backup.return_value = Path("/tmp/test.json.backup")
    mock_validate.return_value = JsonSpecValidationResult(
        spec_id="test-spec",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
    )

    spec_data = {
        "spec_id": "test-spec",
        "hierarchy": {
            "task-1": {"id": "task-1", "type": "task", "status": "inprogress"},
        },
    }

    actions = [
        FixAction(
            id="test-1",
            description="Fix status",
            category="node",
            severity="warning",
            auto_apply=True,
            preview="Normalize status",
            apply=lambda data: data["hierarchy"]["task-1"].__setitem__("status", "in_progress"),
        )
    ]

    with patch("builtins.open", mock_open(read_data=json.dumps(spec_data))):
        report = apply_fix_actions(
            actions,
            "/tmp/test.json",
            dry_run=False,
            create_backup=True,
        )

    assert report.spec_path == "/tmp/test.json"
    assert len(report.applied_actions) == 1
    assert len(report.skipped_actions) == 0
    assert report.backup_path == "/tmp/test.json.backup"
    assert report.post_validation is not None

    # Verify that recalculate_progress was called
    mock_recalc.assert_called_once()

    # Verify that save_json_spec was called
    mock_save.assert_called_once()


def test_apply_fix_actions_handles_errors():
    """Test that apply_fix_actions handles errors gracefully."""
    actions = [
        FixAction(
            id="test-1",
            description="Failing action",
            category="test",
            severity="error",
            auto_apply=True,
            preview="This will fail",
            apply=lambda data: (_ for _ in ()).throw(ValueError("Test error")),
        )
    ]

    spec_data = {"spec_id": "test-spec"}

    with patch("builtins.open", mock_open(read_data=json.dumps(spec_data))):
        with patch("claude_skills.sdd_validate.fix.backup_json_spec", return_value=None):
            with patch("claude_skills.sdd_validate.fix.validate_spec_hierarchy") as mock_validate:
                with patch("claude_skills.sdd_validate.fix.save_json_spec"):
                    mock_validate.return_value = JsonSpecValidationResult(
                        spec_id="test-spec",
                        generated="2025-01-20T10:00:00Z",
                        last_updated="2025-01-20T10:00:00Z",
                    )

                    report = apply_fix_actions(actions, "/tmp/test.json", dry_run=False, create_backup=False)

    # Failed actions should be in skipped
    assert len(report.applied_actions) == 0
    assert len(report.skipped_actions) == 1


def test_collect_fix_actions_deduplicates():
    """Test that collect_fix_actions doesn't create duplicate actions."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-003",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
        spec_data={"hierarchy": {"task-1": {"id": "task-1", "type": "task"}}},
        enhanced_errors=[
            EnhancedError(
                message="Missing metadata for task-1",
                severity="warning",
                category="metadata",
                location="task-1",
                auto_fixable=True,
                suggested_fix="Add metadata",
            ),
            EnhancedError(
                message="Missing metadata for task-1 (duplicate)",
                severity="warning",
                category="metadata",
                location="task-1",
                auto_fixable=True,
                suggested_fix="Add metadata",
            ),
        ],
    )

    actions = collect_fix_actions(result)

    # Should only create one metadata action for task-1
    metadata_actions = [a for a in actions if a.category == "metadata" and "task-1" in a.id]
    assert len(metadata_actions) == 1
