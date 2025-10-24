"""Unit tests for sdd_validate.reporting module."""

import json
import pytest

from claude_skills.common.validation import JsonSpecValidationResult
from claude_skills.sdd_validate.reporting import generate_report


def test_generate_report_markdown_clean():
    """Test generating markdown report for clean validation."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-001",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
    )

    report = generate_report(result, format="markdown")

    assert "# Validation Report" in report
    assert "test-spec-001" in report
    assert "Errors: 0" in report
    assert "Warnings: 0" in report
    assert "No validation issues detected" in report


def test_generate_report_markdown_with_errors():
    """Test generating markdown report with errors."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-002",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
        structure_errors=["Missing required field"],
        hierarchy_errors=["Invalid parent reference"],
    )

    report = generate_report(result, format="markdown")

    assert "# Validation Report" in report
    assert "test-spec-002" in report
    assert "Errors: 2" in report
    assert "## Issues" in report
    assert "Missing required field" in report
    assert "Invalid parent reference" in report


def test_generate_report_markdown_with_warnings():
    """Test generating markdown report with warnings."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-003",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
        metadata_warnings=["Non-standard format"],
    )

    report = generate_report(result, format="markdown")

    assert "# Validation Report" in report
    assert "Warnings: 1" in report
    assert "Non-standard format" in report


def test_generate_report_json_clean():
    """Test generating JSON report for clean validation."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-004",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
    )

    report = generate_report(result, format="json")
    data = json.loads(report)

    assert data["summary"]["spec_id"] == "test-spec-004"
    assert data["summary"]["status"] == "valid"
    assert data["summary"]["errors"] == 0
    assert data["summary"]["warnings"] == 0
    assert len(data["errors"]) == 0
    assert len(data["warnings"]) == 0


def test_generate_report_json_with_errors():
    """Test generating JSON report with errors."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-005",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
        structure_errors=["Missing field"],
    )

    report = generate_report(result, format="json")
    data = json.loads(report)

    assert data["summary"]["status"] == "errors"
    assert data["summary"]["errors"] == 1
    assert len(data["errors"]) == 1
    assert data["errors"][0]["severity"] == "error"


def test_generate_report_with_stats():
    """Test generating report with statistics."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-006",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
    )

    stats = {
        "spec_id": "test-spec-006",
        "totals": {"nodes": 10, "tasks": 5, "phases": 2},
        "max_depth": 3,
        "progress": 0.5,
    }

    report = generate_report(result, format="markdown", stats=stats)

    assert "## Statistics Snapshot" in report
    assert "spec_id" in report
    assert "totals" in report
    assert "max_depth" in report


def test_generate_report_with_stats_json():
    """Test generating JSON report with statistics."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-007",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
    )

    stats = {
        "spec_id": "test-spec-007",
        "totals": {"nodes": 10, "tasks": 5},
    }

    report = generate_report(result, format="json", stats=stats)
    data = json.loads(report)

    assert "stats" in data
    assert data["stats"]["spec_id"] == "test-spec-007"
    assert data["stats"]["totals"]["nodes"] == 10


def test_generate_report_with_dependencies_cycles():
    """Test generating report with dependency cycles (CLI format)."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-008",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
    )

    dependency_analysis = {
        "cycles": [["task-1", "task-2", "task-1"]],
        "orphaned": [],
        "deadlocks": [],
        "bottlenecks": [],
        "status": "issues",
    }

    report = generate_report(result, format="markdown", dependency_analysis=dependency_analysis)

    assert "## Dependency Findings" in report
    assert "Cycles:" in report
    assert "task-1 -> task-2 -> task-1" in report


def test_generate_report_with_dependencies_orphaned():
    """Test generating report with orphaned dependencies (CLI format)."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-009",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
    )

    dependency_analysis = {
        "cycles": [],
        "orphaned": [{"task": "task-3", "missing_dependency": "task-999"}],
        "deadlocks": [],
        "bottlenecks": [],
        "status": "issues",
    }

    report = generate_report(result, format="markdown", dependency_analysis=dependency_analysis)

    assert "## Dependency Findings" in report
    assert "Orphaned dependencies:" in report
    assert "task-3 references missing task-999" in report


def test_generate_report_with_dependencies_deadlocks():
    """Test generating report with deadlocks (CLI format)."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-010",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
    )

    dependency_analysis = {
        "cycles": [],
        "orphaned": [],
        "deadlocks": [{"task": "task-4", "blocked_by": ["task-5", "task-6"]}],
        "bottlenecks": [],
        "status": "issues",
    }

    report = generate_report(result, format="markdown", dependency_analysis=dependency_analysis)

    assert "## Dependency Findings" in report
    assert "Potential deadlocks:" in report
    assert "task-4 blocked by task-5, task-6" in report


def test_generate_report_with_dependencies_bottlenecks():
    """Test generating report with bottlenecks (CLI format)."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-011",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
    )

    dependency_analysis = {
        "cycles": [],
        "orphaned": [],
        "deadlocks": [],
        "bottlenecks": [{"task": "task-7", "blocks": 5, "threshold": 3}],
        "status": "issues",
    }

    report = generate_report(result, format="markdown", dependency_analysis=dependency_analysis)

    assert "## Dependency Findings" in report
    assert "Bottleneck tasks:" in report
    assert "task-7 blocks 5 tasks (threshold: 3)" in report


def test_generate_report_with_dependencies_all_types():
    """Test generating report with all dependency types."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-012",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
    )

    dependency_analysis = {
        "cycles": [["task-1", "task-2", "task-1"]],
        "orphaned": [{"task": "task-3", "missing_dependency": "task-999"}],
        "deadlocks": [{"task": "task-4", "blocked_by": ["task-5"]}],
        "bottlenecks": [{"task": "task-6", "blocks": 4, "threshold": 3}],
        "status": "issues",
    }

    report = generate_report(result, format="markdown", dependency_analysis=dependency_analysis)

    assert "Cycles:" in report
    assert "Orphaned dependencies:" in report
    assert "Potential deadlocks:" in report
    assert "Bottleneck tasks:" in report


def test_generate_report_with_dependencies_json():
    """Test generating JSON report with dependencies."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-013",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
    )

    dependency_analysis = {
        "cycles": [["task-1", "task-2", "task-1"]],
        "orphaned": [{"task": "task-3", "missing_dependency": "task-999"}],
        "deadlocks": [],
        "bottlenecks": [{"task": "task-4", "blocks": 5, "threshold": 3}],
        "status": "issues",
    }

    report = generate_report(result, format="json", dependency_analysis=dependency_analysis)
    data = json.loads(report)

    assert "dependencies" in data
    assert len(data["dependencies"]["cycles"]) == 1
    assert len(data["dependencies"]["orphaned"]) == 1
    assert len(data["dependencies"]["bottlenecks"]) == 1
    assert data["dependencies"]["status"] == "issues"


def test_generate_report_legacy_dependency_keys():
    """Test report generation with legacy dependency key names."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-014",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
    )

    # Use legacy key names
    dependency_analysis = {
        "circular_chains": [["task-1", "task-2", "task-1"]],
        "orphaned_tasks": [{"task": "task-3", "missing_dependency": "task-999"}],
        "impossible_chains": [{"task": "task-4", "blocked_by": ["task-5"]}],
        "status": "issues",
    }

    report = generate_report(result, format="markdown", dependency_analysis=dependency_analysis)

    # Should still work with legacy keys
    assert "Cycles:" in report
    assert "task-1 -> task-2 -> task-1" in report
    assert "Orphaned dependencies:" in report
    assert "task-3 references missing task-999" in report
    assert "Potential deadlocks:" in report
    assert "task-4 blocked by task-5" in report


def test_generate_report_mixed_dependency_keys():
    """Test report generation with mixed new and legacy keys."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-015",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
    )

    # Mix of new and legacy keys (new keys should take precedence)
    dependency_analysis = {
        "cycles": [["new-task-1", "new-task-2", "new-task-1"]],
        "circular_chains": [["old-task-1", "old-task-2", "old-task-1"]],
        "orphaned": [],
        "status": "issues",
    }

    report = generate_report(result, format="markdown", dependency_analysis=dependency_analysis)

    # Should prefer new key names
    assert "new-task-1" in report
    assert "old-task-1" not in report


def test_generate_report_invalid_format():
    """Test that invalid format raises ValueError."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-016",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
    )

    with pytest.raises(ValueError, match="Unsupported report format"):
        generate_report(result, format="xml")


def test_generate_report_empty_dependency_analysis():
    """Test report with empty dependency analysis."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-017",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
    )

    dependency_analysis = {
        "cycles": [],
        "orphaned": [],
        "deadlocks": [],
        "bottlenecks": [],
        "status": "ok",
    }

    report = generate_report(result, format="markdown", dependency_analysis=dependency_analysis)

    # Should still have dependency section header but no findings listed
    assert "## Dependency Findings" in report
    # Should not list empty categories
    assert "Cycles:" not in report
    assert "Orphaned dependencies:" not in report
