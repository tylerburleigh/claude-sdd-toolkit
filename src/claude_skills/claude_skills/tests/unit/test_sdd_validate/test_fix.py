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
    _build_task_category_action,
    _build_placeholder_file_path_action,
    _build_hierarchy_action,
    _build_date_action,
    _build_status_action,
    _build_bidirectional_deps_action,
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


def test_build_task_category_action():
    """Test building task_category fix action for implementation task."""
    error = EnhancedError(
        message="Missing task_category for task-1",
        severity="warning",
        category="metadata",
        location="task-1",
        auto_fixable=True,
        suggested_fix="Infer and set task_category",
    )

    spec_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "title": "src/services/auth.py",
                "metadata": {}
            },
        }
    }

    action = _build_task_category_action(error, spec_data)

    assert action is not None
    assert action.id == "task_category.infer:task-1"
    assert action.category == "metadata"
    assert action.auto_apply is True

    # Test applying the action
    test_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "title": "src/services/auth.py",
                "metadata": {}
            }
        }
    }
    action.apply(test_data)

    metadata = test_data["hierarchy"]["task-1"]["metadata"]
    assert "task_category" in metadata
    assert metadata["task_category"] == "implementation"


def test_build_task_category_action_investigation():
    """Test building task_category fix action for investigation task."""
    error = EnhancedError(
        message="Missing task_category for task-2",
        severity="warning",
        category="metadata",
        location="task-2",
        auto_fixable=True,
        suggested_fix="Infer and set task_category",
    )

    spec_data = {
        "hierarchy": {
            "task-2": {
                "id": "task-2",
                "type": "task",
                "title": "Analyze current authentication flow",
                "metadata": {}
            },
        }
    }

    action = _build_task_category_action(error, spec_data)

    assert action is not None

    # Test applying the action
    test_data = {
        "hierarchy": {
            "task-2": {
                "id": "task-2",
                "type": "task",
                "title": "Analyze current authentication flow",
                "metadata": {}
            }
        }
    }
    action.apply(test_data)

    metadata = test_data["hierarchy"]["task-2"]["metadata"]
    assert "task_category" in metadata
    assert metadata["task_category"] == "investigation"
    assert metadata["file_path"] == "investigation"


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

    # Should only create one of EACH TYPE of metadata action for task-1
    # (metadata.ensure and task_category.infer are different action types)
    metadata_ensure_actions = [a for a in actions if a.id == "metadata.ensure:task-1"]
    task_category_actions = [a for a in actions if a.id == "task_category.infer:task-1"]

    # Each specific action ID should only appear once (deduplication working)
    assert len(metadata_ensure_actions) == 1
    assert len(task_category_actions) == 1


def test_build_placeholder_file_path_action_category_name():
    """Test detecting file_path with category name as placeholder."""
    error = EnhancedError(
        message="Placeholder file_path detected",
        severity="info",
        category="migration",
        location="task-1",
        auto_fixable=True,
        suggested_fix="Remove placeholder and set task_category",
    )

    spec_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "title": "Analyze authentication flow",
                "metadata": {"file_path": "investigation"},
            },
        }
    }

    action = _build_placeholder_file_path_action(error, spec_data)

    assert action is not None
    assert action.id == "file_path.remove_placeholder:task-1"
    assert action.category == "migration"
    assert action.severity == "info"
    assert action.auto_apply is True

    # Test applying the action
    test_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "title": "Analyze authentication flow",
                "metadata": {"file_path": "investigation"},
            }
        }
    }
    action.apply(test_data)

    metadata = test_data["hierarchy"]["task-1"]["metadata"]
    assert "task_category" in metadata
    assert metadata["task_category"] == "investigation"
    assert "file_path" not in metadata


def test_build_placeholder_file_path_action_tbd():
    """Test detecting file_path with TBD placeholder.

    TBD (To Be Determined) maps to 'decision' category because it indicates
    a decision needs to be made about what to implement.
    """
    error = EnhancedError(
        message="Placeholder file_path detected",
        severity="info",
        category="migration",
        location="task-2",
        auto_fixable=True,
        suggested_fix="Remove placeholder and set task_category",
    )

    spec_data = {
        "hierarchy": {
            "task-2": {
                "id": "task-2",
                "type": "task",
                "title": "src/services/auth.py",
                "metadata": {"file_path": "TBD"},
            },
        }
    }

    action = _build_placeholder_file_path_action(error, spec_data)

    assert action is not None

    # Test applying the action
    test_data = {
        "hierarchy": {
            "task-2": {
                "id": "task-2",
                "type": "task",
                "title": "src/services/auth.py",
                "metadata": {"file_path": "TBD"},
            }
        }
    }
    action.apply(test_data)

    metadata = test_data["hierarchy"]["task-2"]["metadata"]
    assert "task_category" in metadata
    assert metadata["task_category"] == "decision"  # TBD maps to decision category
    assert "file_path" not in metadata


def test_build_placeholder_file_path_action_case_insensitive():
    """Test that placeholder detection is case-insensitive."""
    placeholders = ["INVESTIGATION", "Implementation", "n/a", "Null", "TbD"]

    for placeholder in placeholders:
        error = EnhancedError(
            message="Placeholder file_path detected",
            severity="info",
            category="migration",
            location="task-1",
            auto_fixable=True,
            suggested_fix="Remove placeholder and set task_category",
        )

        spec_data = {
            "hierarchy": {
                "task-1": {
                    "id": "task-1",
                    "type": "task",
                    "title": "Test task",
                    "metadata": {"file_path": placeholder},
                },
            }
        }

        action = _build_placeholder_file_path_action(error, spec_data)

        assert action is not None, f"Failed to detect placeholder: {placeholder}"

        # Apply and verify
        test_data = {
            "hierarchy": {
                "task-1": {
                    "id": "task-1",
                    "type": "task",
                    "title": "Test task",
                    "metadata": {"file_path": placeholder},
                }
            }
        }
        action.apply(test_data)

        metadata = test_data["hierarchy"]["task-1"]["metadata"]
        assert "task_category" in metadata
        assert "file_path" not in metadata


def test_build_placeholder_file_path_action_all_placeholders():
    """Test detection of all placeholder patterns."""
    placeholders = [
        "investigation",
        "implementation",
        "refactoring",
        "decision",
        "research",
        "tbd",
        "n/a",
        "none",
        "null",
    ]

    for placeholder in placeholders:
        error = EnhancedError(
            message="Placeholder file_path detected",
            severity="info",
            category="migration",
            location="task-1",
            auto_fixable=True,
            suggested_fix="Remove placeholder and set task_category",
        )

        spec_data = {
            "hierarchy": {
                "task-1": {
                    "id": "task-1",
                    "type": "task",
                    "title": "Test task",
                    "metadata": {"file_path": placeholder},
                },
            }
        }

        action = _build_placeholder_file_path_action(error, spec_data)

        assert action is not None, f"Failed to detect placeholder: {placeholder}"


def test_build_placeholder_file_path_action_non_placeholder():
    """Test that real file paths are not detected as placeholders."""
    real_paths = [
        "src/services/auth.py",
        "investigation_results.txt",
        "implementation_details.md",
        "test_investigation.py",
        "n/a.txt",
    ]

    for file_path in real_paths:
        error = EnhancedError(
            message="Test error",
            severity="info",
            category="migration",
            location="task-1",
            auto_fixable=True,
            suggested_fix="Test",
        )

        spec_data = {
            "hierarchy": {
                "task-1": {
                    "id": "task-1",
                    "type": "task",
                    "title": "Test task",
                    "metadata": {"file_path": file_path},
                },
            }
        }

        action = _build_placeholder_file_path_action(error, spec_data)

        assert action is None, f"Incorrectly detected real path as placeholder: {file_path}"


def test_build_placeholder_file_path_action_no_file_path():
    """Test that nodes without file_path are skipped."""
    error = EnhancedError(
        message="Test error",
        severity="info",
        category="migration",
        location="task-1",
        auto_fixable=True,
        suggested_fix="Test",
    )

    spec_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "title": "Test task",
                "metadata": {},
            },
        }
    }

    action = _build_placeholder_file_path_action(error, spec_data)

    assert action is None


def test_build_placeholder_file_path_action_subtask():
    """Test that placeholder detection works for subtasks."""
    error = EnhancedError(
        message="Placeholder file_path detected",
        severity="info",
        category="migration",
        location="subtask-1",
        auto_fixable=True,
        suggested_fix="Remove placeholder and set task_category",
    )

    spec_data = {
        "hierarchy": {
            "subtask-1": {
                "id": "subtask-1",
                "type": "subtask",
                "title": "Research API documentation",
                "metadata": {"file_path": "research"},
            },
        }
    }

    action = _build_placeholder_file_path_action(error, spec_data)

    assert action is not None

    # Test applying the action
    test_data = {
        "hierarchy": {
            "subtask-1": {
                "id": "subtask-1",
                "type": "subtask",
                "title": "Research API documentation",
                "metadata": {"file_path": "research"},
            }
        }
    }
    action.apply(test_data)

    metadata = test_data["hierarchy"]["subtask-1"]["metadata"]
    assert "task_category" in metadata
    assert metadata["task_category"] == "research"
    assert "file_path" not in metadata


def test_build_placeholder_file_path_action_non_task_node():
    """Test that placeholder detection only applies to task/subtask nodes."""
    node_types = ["phase", "verify", "root"]

    for node_type in node_types:
        error = EnhancedError(
            message="Test error",
            severity="info",
            category="migration",
            location="node-1",
            auto_fixable=True,
            suggested_fix="Test",
        )

        spec_data = {
            "hierarchy": {
                "node-1": {
                    "id": "node-1",
                    "type": node_type,
                    "title": "Test node",
                    "metadata": {"file_path": "investigation"},
                },
            }
        }

        action = _build_placeholder_file_path_action(error, spec_data)

        assert action is None, f"Should not detect placeholder for {node_type} nodes"


def test_build_placeholder_file_path_action_preserves_existing_category():
    """Test that existing task_category is not overwritten."""
    error = EnhancedError(
        message="Placeholder file_path detected",
        severity="info",
        category="migration",
        location="task-1",
        auto_fixable=True,
        suggested_fix="Remove placeholder and set task_category",
    )

    spec_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "title": "Test task",
                "metadata": {
                    "file_path": "investigation",
                    "task_category": "implementation",  # Already set
                },
            },
        }
    }

    action = _build_placeholder_file_path_action(error, spec_data)

    assert action is not None

    # Test applying the action
    test_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "title": "Test task",
                "metadata": {
                    "file_path": "investigation",
                    "task_category": "implementation",
                },
            }
        }
    }
    action.apply(test_data)

    metadata = test_data["hierarchy"]["task-1"]["metadata"]
    # Should preserve existing category
    assert metadata["task_category"] == "implementation"
    # Should remove placeholder file_path
    assert "file_path" not in metadata


def test_build_placeholder_file_path_action_whitespace():
    """Test that placeholders with whitespace are detected."""
    error = EnhancedError(
        message="Placeholder file_path detected",
        severity="info",
        category="migration",
        location="task-1",
        auto_fixable=True,
        suggested_fix="Remove placeholder and set task_category",
    )

    spec_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "title": "Test task",
                "metadata": {"file_path": "  investigation  "},
            },
        }
    }

    action = _build_placeholder_file_path_action(error, spec_data)

    assert action is not None

    # Test applying the action
    test_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "title": "Test task",
                "metadata": {"file_path": "  investigation  "},
            }
        }
    }
    action.apply(test_data)

    metadata = test_data["hierarchy"]["task-1"]["metadata"]
    assert "task_category" in metadata
    assert "file_path" not in metadata


def test_build_placeholder_file_path_action_tbd_maps_to_decision():
    """Test that 'tbd' placeholder maps to 'decision' category."""
    error = EnhancedError(
        message="Placeholder file_path detected",
        severity="info",
        category="migration",
        location="task-1",
        auto_fixable=True,
        suggested_fix="Remove placeholder and set task_category",
    )

    spec_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "title": "Some task with TBD file path",
                "metadata": {"file_path": "tbd"},
            },
        }
    }

    action = _build_placeholder_file_path_action(error, spec_data)

    assert action is not None

    # Test applying the action
    test_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "title": "Some task with TBD file path",
                "metadata": {"file_path": "tbd"},
            }
        }
    }
    action.apply(test_data)

    metadata = test_data["hierarchy"]["task-1"]["metadata"]
    assert "task_category" in metadata
    assert metadata["task_category"] == "decision"
    assert "file_path" not in metadata


def test_build_placeholder_file_path_action_category_mapping():
    """Test that category-name placeholders map directly to their category."""
    category_placeholders = {
        "investigation": "investigation",
        "decision": "decision",
        "research": "research",
        "refactoring": "refactoring",
        "implementation": "implementation",
    }

    for placeholder, expected_category in category_placeholders.items():
        error = EnhancedError(
            message="Placeholder file_path detected",
            severity="info",
            category="migration",
            location="task-1",
            auto_fixable=True,
            suggested_fix="Remove placeholder and set task_category",
        )

        spec_data = {
            "hierarchy": {
                "task-1": {
                    "id": "task-1",
                    "type": "task",
                    "title": "Generic task title",
                    "metadata": {"file_path": placeholder},
                },
            }
        }

        action = _build_placeholder_file_path_action(error, spec_data)

        assert action is not None, f"Failed to create action for placeholder: {placeholder}"

        # Test applying the action
        test_data = {
            "hierarchy": {
                "task-1": {
                    "id": "task-1",
                    "type": "task",
                    "title": "Generic task title",
                    "metadata": {"file_path": placeholder},
                }
            }
        }
        action.apply(test_data)

        metadata = test_data["hierarchy"]["task-1"]["metadata"]
        assert "task_category" in metadata, f"task_category not set for placeholder: {placeholder}"
        assert metadata["task_category"] == expected_category, \
            f"Expected {expected_category}, got {metadata['task_category']} for placeholder: {placeholder}"
        assert "file_path" not in metadata, f"file_path not removed for placeholder: {placeholder}"


def test_build_placeholder_file_path_action_generic_placeholder_uses_title():
    """Test that generic placeholders (n/a, none, null) use title-based inference."""
    error = EnhancedError(
        message="Placeholder file_path detected",
        severity="info",
        category="migration",
        location="task-1",
        auto_fixable=True,
        suggested_fix="Remove placeholder and set task_category",
    )

    spec_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "title": "Analyze authentication flow",  # Should infer "investigation"
                "metadata": {"file_path": "n/a"},
            },
        }
    }

    action = _build_placeholder_file_path_action(error, spec_data)

    assert action is not None

    # Test applying the action
    test_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "title": "Analyze authentication flow",
                "metadata": {"file_path": "n/a"},
            }
        }
    }
    action.apply(test_data)

    metadata = test_data["hierarchy"]["task-1"]["metadata"]
    assert "task_category" in metadata
    # Should infer "investigation" from "Analyze" keyword in title
    assert metadata["task_category"] == "investigation"
    assert "file_path" not in metadata


def test_build_placeholder_file_path_action_preview_shows_category():
    """Test that the preview message shows the inferred category."""
    error = EnhancedError(
        message="Placeholder file_path detected",
        severity="info",
        category="migration",
        location="task-1",
        auto_fixable=True,
        suggested_fix="Remove placeholder and set task_category",
    )

    spec_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "title": "Test task",
                "metadata": {"file_path": "investigation"},
            },
        }
    }

    action = _build_placeholder_file_path_action(error, spec_data)

    assert action is not None
    # Preview should show the category being set
    assert "investigation" in action.preview.lower()
    assert "task_category" in action.preview.lower()
    # Should use arrow notation
    assert "→" in action.preview or "->" in action.preview


def test_build_bidirectional_deps_action_missing_dependencies():
    """Test bidirectional deps action with missing dependencies structure."""
    error = EnhancedError(
        message="Node 'task-1' blocks 'task-2', but 'task-2' doesn't list 'task-1' in blocked_by",
        severity="error",
        category="dependency",
        auto_fixable=True,
    )

    spec_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                # No dependencies key at all
            },
            "task-2": {
                "id": "task-2",
                "type": "task",
                # No dependencies key at all
            },
        }
    }

    action = _build_bidirectional_deps_action(error, spec_data)

    assert action is not None
    assert action.category == "dependency"
    assert action.auto_apply is True
    assert callable(action.apply)

    # Apply the action and verify it creates complete dependencies structure
    action.apply(spec_data)

    # Verify task-1 has complete dependencies with task-2 in blocks
    assert "dependencies" in spec_data["hierarchy"]["task-1"]
    task1_deps = spec_data["hierarchy"]["task-1"]["dependencies"]
    assert isinstance(task1_deps, dict)
    assert "blocks" in task1_deps
    assert "blocked_by" in task1_deps
    assert "depends" in task1_deps
    assert "task-2" in task1_deps["blocks"]

    # Verify task-2 has complete dependencies with task-1 in blocked_by
    assert "dependencies" in spec_data["hierarchy"]["task-2"]
    task2_deps = spec_data["hierarchy"]["task-2"]["dependencies"]
    assert isinstance(task2_deps, dict)
    assert "blocks" in task2_deps
    assert "blocked_by" in task2_deps
    assert "depends" in task2_deps
    assert "task-1" in task2_deps["blocked_by"]


def test_build_bidirectional_deps_action_partial_dependencies():
    """Test bidirectional deps action with partial dependencies structure."""
    error = EnhancedError(
        message="Node 'task-1' blocks 'task-2', but 'task-2' doesn't list 'task-1' in blocked_by",
        severity="error",
        category="dependency",
        auto_fixable=True,
    )

    spec_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "dependencies": {
                    "blocks": [],  # Partial: only blocks, missing blocked_by and depends
                },
            },
            "task-2": {
                "id": "task-2",
                "type": "task",
                "dependencies": {
                    "blocked_by": [],  # Partial: only blocked_by, missing blocks and depends
                },
            },
        }
    }

    action = _build_bidirectional_deps_action(error, spec_data)

    assert action is not None
    assert action.category == "dependency"
    assert action.auto_apply is True

    # Apply the action
    action.apply(spec_data)

    # Verify setdefault added missing fields to task-1's dependencies
    task1_deps = spec_data["hierarchy"]["task-1"]["dependencies"]
    assert "blocks" in task1_deps
    assert "blocked_by" in task1_deps  # Added by setdefault
    assert "depends" in task1_deps  # Added by setdefault
    assert "task-2" in task1_deps["blocks"]

    # Verify setdefault added missing fields to task-2's dependencies
    task2_deps = spec_data["hierarchy"]["task-2"]["dependencies"]
    assert "blocks" in task2_deps  # Added by setdefault
    assert "blocked_by" in task2_deps
    assert "depends" in task2_deps  # Added by setdefault
    assert "task-1" in task2_deps["blocked_by"]


def test_build_bidirectional_deps_action_malformed_dependencies():
    """Test bidirectional deps action with malformed dependencies (null or non-dict)."""
    error = EnhancedError(
        message="Node 'task-1' blocks 'task-2', but 'task-2' doesn't list 'task-1' in blocked_by",
        severity="error",
        category="dependency",
        auto_fixable=True,
    )

    spec_data = {
        "hierarchy": {
            "task-1": {
                "id": "task-1",
                "type": "task",
                "dependencies": None,  # Malformed: null value
            },
            "task-2": {
                "id": "task-2",
                "type": "task",
                "dependencies": ["some", "list"],  # Malformed: list instead of dict
            },
        }
    }

    action = _build_bidirectional_deps_action(error, spec_data)

    assert action is not None
    assert action.category == "dependency"
    assert action.auto_apply is True

    # Apply the action
    action.apply(spec_data)

    # Verify task-1's malformed (null) dependencies was replaced with complete structure
    assert "dependencies" in spec_data["hierarchy"]["task-1"]
    task1_deps = spec_data["hierarchy"]["task-1"]["dependencies"]
    assert isinstance(task1_deps, dict)
    assert "blocks" in task1_deps
    assert "blocked_by" in task1_deps
    assert "depends" in task1_deps
    assert "task-2" in task1_deps["blocks"]

    # Verify task-2's malformed (list) dependencies was replaced with complete structure
    assert "dependencies" in spec_data["hierarchy"]["task-2"]
    task2_deps = spec_data["hierarchy"]["task-2"]["dependencies"]
    assert isinstance(task2_deps, dict)
    assert "blocks" in task2_deps
    assert "blocked_by" in task2_deps
    assert "depends" in task2_deps
    assert "task-1" in task2_deps["blocked_by"]
