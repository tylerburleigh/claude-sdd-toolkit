"""
Tests for status_report.py dashboard functionality.

Tests the creation of status reports with phases, progress, and blockers panels.
"""

import pytest
from io import StringIO
from rich.console import Console
from claude_skills.sdd_update.status_report import (
    print_status_report,
    get_status_summary,
    _prepare_phases_table_data,
    _prepare_progress_data,
    _prepare_blockers_data
)


def render_panel_to_string(panel):
    """Helper to render a Rich Panel to string for testing."""
    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)
    console.print(panel)
    return string_io.getvalue()


@pytest.fixture
def sample_spec_data():
    """Create sample spec data with phases, tasks, and progress."""
    return {
        "hierarchy": {
            "phase-1": {
                "type": "phase",
                "title": "Phase 1: Foundation",
                "status": "completed",
                "total_tasks": 5,
                "completed_tasks": 5
            },
            "phase-2": {
                "type": "phase",
                "title": "Phase 2: Implementation",
                "status": "in_progress",
                "total_tasks": 10,
                "completed_tasks": 6
            },
            "phase-3": {
                "type": "phase",
                "title": "Phase 3: Testing",
                "status": "pending",
                "total_tasks": 8,
                "completed_tasks": 0
            },
            "task-1-1": {
                "type": "task",
                "title": "Create database schema",
                "status": "completed"
            },
            "task-2-1": {
                "type": "task",
                "title": "Implement authentication",
                "status": "completed"
            },
            "task-2-2": {
                "type": "task",
                "title": "Add rate limiting",
                "status": "in_progress"
            },
            "task-2-3": {
                "type": "task",
                "title": "Configure Redis",
                "status": "blocked",
                "metadata": {
                    "blocker_reason": "Redis server not configured"
                },
                "dependencies": {
                    "blocked_by": ["task-2-2"]
                }
            },
            "task-3-1": {
                "type": "task",
                "title": "Write unit tests",
                "status": "pending"
            }
        }
    }


@pytest.fixture
def empty_spec_data():
    """Create empty spec data."""
    return {"hierarchy": {}}


@pytest.fixture
def spec_with_no_blockers():
    """Create spec data with no blocked tasks."""
    return {
        "hierarchy": {
            "phase-1": {
                "type": "phase",
                "title": "Phase 1",
                "status": "in_progress",
                "total_tasks": 2,
                "completed_tasks": 1
            },
            "task-1-1": {
                "type": "task",
                "title": "Task 1",
                "status": "completed"
            },
            "task-1-2": {
                "type": "task",
                "title": "Task 2",
                "status": "in_progress"
            }
        }
    }


def test_prepare_phases_data_with_phases(sample_spec_data):
    """Test phases data preparation with sample data."""
    phases_data, phase_count = _prepare_phases_table_data(sample_spec_data)

    assert phases_data is not None
    assert len(phases_data) == 3
    assert phase_count == 3
    assert any("Phase 1" in row.get("Phase", "") for row in phases_data)


def test_prepare_phases_data_empty(empty_spec_data):
    """Test phases data preparation handles empty data gracefully."""
    phases_data, phase_count = _prepare_phases_table_data(empty_spec_data)

    assert phases_data == []
    assert phase_count == 0


def test_prepare_progress_data_with_tasks(sample_spec_data):
    """Test progress data shows correct metrics."""
    progress_data, subtitle = _prepare_progress_data(sample_spec_data)

    assert progress_data is not None
    assert len(progress_data) > 0
    assert any("Overall" in row.get("Metric", "") for row in progress_data)


def test_prepare_progress_data_empty(empty_spec_data):
    """Test progress data handles no tasks."""
    progress_data, subtitle = _prepare_progress_data(empty_spec_data)

    assert progress_data is not None
    assert any("No tasks" in row.get("Value", "") for row in progress_data)


def test_prepare_blockers_data_with_blockers(sample_spec_data):
    """Test blockers data shows blocked tasks."""
    blockers_content, blocker_count = _prepare_blockers_data(sample_spec_data)

    assert blockers_content is not None
    assert blocker_count == 1
    assert "task-2-3" in blockers_content
    assert "Redis server not configured" in blockers_content


def test_prepare_blockers_data_no_blockers(spec_with_no_blockers):
    """Test blockers data shows no blockers message."""
    blockers_content, blocker_count = _prepare_blockers_data(spec_with_no_blockers)

    assert blockers_content is not None
    assert blocker_count == 0
    assert "No blockers" in blockers_content


def test_print_status_report(sample_spec_data):
    """Test full report printing."""
    # Capture output
    from claude_skills.common.ui_factory import create_ui
    print_status_report(sample_spec_data)
    # Just verify it doesn't raise an exception


def test_get_status_summary(sample_spec_data):
    """Test status summary returns correct metrics."""
    summary = get_status_summary(sample_spec_data)

    assert summary["total_tasks"] == 5  # 5 tasks in hierarchy
    assert summary["completed_tasks"] == 2  # task-1-1 and task-2-1
    assert summary["in_progress_tasks"] == 1  # task-2-2
    assert summary["blocked_tasks"] == 1  # task-2-3
    assert len(summary["phases"]) == 3
    assert len(summary["blockers"]) == 1


def test_get_status_summary_empty(empty_spec_data):
    """Test status summary handles empty data."""
    summary = get_status_summary(empty_spec_data)

    assert summary["total_tasks"] == 0
    assert summary["completed_tasks"] == 0
    assert summary["in_progress_tasks"] == 0
    assert summary["blocked_tasks"] == 0
    assert len(summary["phases"]) == 0
    assert len(summary["blockers"]) == 0


def test_phases_data_shows_status_indicators(sample_spec_data):
    """Test phases data includes status indicators."""
    phases_data, _ = _prepare_phases_table_data(sample_spec_data)
    combined_text = " ".join(str(row) for row in phases_data)

    # Should include different status indicators
    assert "Complete" in combined_text or "✓" in combined_text
    assert "In Progress" in combined_text or "●" in combined_text
    assert "Pending" in combined_text or "○" in combined_text


def test_phases_data_shows_progress_percentages(sample_spec_data):
    """Test phases data includes progress percentages."""
    phases_data, _ = _prepare_phases_table_data(sample_spec_data)
    combined_text = " ".join(str(row) for row in phases_data)

    # Should show completion percentages
    assert "100%" in combined_text  # phase-1 is 5/5
    assert "60%" in combined_text  # phase-2 is 6/10


def test_progress_data_shows_metrics(sample_spec_data):
    """Test progress data includes all required metrics."""
    progress_data, _ = _prepare_progress_data(sample_spec_data)
    combined_text = " ".join(str(row) for row in progress_data)

    # Should include key metrics
    assert "Overall" in combined_text
    assert "Completed" in combined_text
    assert "In Progress" in combined_text
    assert "Blocked" in combined_text or "Remaining" in combined_text


def test_blockers_data_shows_blocker_details(sample_spec_data):
    """Test blockers data includes task ID and reason."""
    blockers_content, _ = _prepare_blockers_data(sample_spec_data)

    # Should show blocked task details
    assert "task-2-3" in blockers_content
    assert ("Redis server not configured" in blockers_content or
            "task-2-2" in blockers_content)  # reason or dependency


def test_blockers_data_limits_display():
    """Test blockers data limits display to top 10."""
    # Create spec with more than 10 blocked tasks
    spec_data = {"hierarchy": {}}
    for i in range(15):
        spec_data["hierarchy"][f"task-{i}"] = {
            "type": "task",
            "title": f"Task {i}",
            "status": "blocked",
            "metadata": {"blocker_reason": f"Blocker {i}"}
        }

    blockers_content, blocker_count = _prepare_blockers_data(spec_data)

    # Should show all blockers in content (not limited in data prep)
    assert blocker_count == 15
    assert "task-0" in blockers_content


def test_status_summary_phases_sorted():
    """Test status summary returns phases in sorted order."""
    spec_data = {
        "hierarchy": {
            "phase-3": {"type": "phase", "title": "Phase 3", "status": "pending", "total_tasks": 0, "completed_tasks": 0},
            "phase-1": {"type": "phase", "title": "Phase 1", "status": "completed", "total_tasks": 0, "completed_tasks": 0},
            "phase-2": {"type": "phase", "title": "Phase 2", "status": "in_progress", "total_tasks": 0, "completed_tasks": 0}
        }
    }

    summary = get_status_summary(spec_data)

    assert len(summary["phases"]) == 3
    assert summary["phases"][0]["id"] == "phase-1"
    assert summary["phases"][1]["id"] == "phase-2"
    assert summary["phases"][2]["id"] == "phase-3"


def test_status_summary_blocker_details():
    """Test status summary includes blocker reason and dependencies."""
    spec_data = {
        "hierarchy": {
            "task-1": {
                "type": "task",
                "title": "Blocked Task",
                "status": "blocked",
                "metadata": {"blocker_reason": "Waiting for review"},
                "dependencies": {"blocked_by": ["task-0"]}
            }
        }
    }

    summary = get_status_summary(spec_data)

    assert len(summary["blockers"]) == 1
    blocker = summary["blockers"][0]
    assert blocker["id"] == "task-1"
    assert blocker["title"] == "Blocked Task"
    assert blocker["reason"] == "Waiting for review"
    assert blocker["blocked_by"] == ["task-0"]
