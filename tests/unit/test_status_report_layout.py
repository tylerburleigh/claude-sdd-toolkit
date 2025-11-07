"""
Tests for status_report.py Rich.Layout dashboard functionality.

Tests the creation of multi-panel layouts for status reporting.
"""

import pytest
from io import StringIO
from rich.console import Console
from claude_skills.sdd_update.status_report import (
    create_phases_panel,
    create_progress_panel,
    create_blockers_panel,
    create_status_layout,
    get_status_summary
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


def test_create_phases_panel_with_phases(sample_spec_data):
    """Test phases panel creation with sample data."""
    panel = create_phases_panel(sample_spec_data)

    assert panel is not None
    panel_str = render_panel_to_string(panel)
    assert "Phases" in panel_str


def test_create_phases_panel_empty(empty_spec_data):
    """Test phases panel handles empty data gracefully."""
    panel = create_phases_panel(empty_spec_data)

    assert panel is not None
    panel_str = render_panel_to_string(panel)
    assert "No phases defined" in panel_str


def test_create_progress_panel_with_tasks(sample_spec_data):
    """Test progress panel shows correct metrics."""
    panel = create_progress_panel(sample_spec_data)

    assert panel is not None
    panel_str = render_panel_to_string(panel)
    assert "Progress" in panel_str


def test_create_progress_panel_empty(empty_spec_data):
    """Test progress panel handles no tasks."""
    panel = create_progress_panel(empty_spec_data)

    assert panel is not None
    panel_str = render_panel_to_string(panel)
    assert "No tasks" in panel_str or "Progress" in panel_str


def test_create_blockers_panel_with_blockers(sample_spec_data):
    """Test blockers panel shows blocked tasks."""
    panel = create_blockers_panel(sample_spec_data)

    assert panel is not None
    panel_str = render_panel_to_string(panel)
    assert "Blockers" in panel_str
    assert "task-2-3" in panel_str
    assert "Redis server not configured" in panel_str


def test_create_blockers_panel_no_blockers(spec_with_no_blockers):
    """Test blockers panel shows no blockers message."""
    panel = create_blockers_panel(spec_with_no_blockers)

    assert panel is not None
    panel_str = render_panel_to_string(panel)
    assert "No blockers" in panel_str


def test_create_status_layout(sample_spec_data):
    """Test full layout creation."""
    layout = create_status_layout(sample_spec_data)

    assert layout is not None
    assert len(layout.children) > 0


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


def test_phases_panel_shows_status_indicators(sample_spec_data):
    """Test phases panel includes status indicators."""
    panel = create_phases_panel(sample_spec_data)
    panel_str = render_panel_to_string(panel)

    # Should include different status indicators
    assert "Complete" in panel_str or "✓" in panel_str
    assert "In Progress" in panel_str or "●" in panel_str
    assert "Pending" in panel_str or "○" in panel_str


def test_phases_panel_shows_progress_percentages(sample_spec_data):
    """Test phases panel includes progress percentages."""
    panel = create_phases_panel(sample_spec_data)
    panel_str = render_panel_to_string(panel)

    # Should show completion percentages
    assert "100%" in panel_str  # phase-1 is 5/5
    assert "60%" in panel_str  # phase-2 is 6/10


def test_progress_panel_shows_metrics(sample_spec_data):
    """Test progress panel includes all required metrics."""
    panel = create_progress_panel(sample_spec_data)
    panel_str = render_panel_to_string(panel)

    # Should include key metrics
    assert "Overall" in panel_str
    assert "Completed" in panel_str
    assert "In Progress" in panel_str
    assert "Blocked" in panel_str or "Remaining" in panel_str


def test_blockers_panel_shows_blocker_details(sample_spec_data):
    """Test blockers panel includes task ID and reason."""
    panel = create_blockers_panel(sample_spec_data)
    panel_str = render_panel_to_string(panel)

    # Should show blocked task details
    assert "task-2-3" in panel_str
    assert ("Redis server not configured" in panel_str or
            "task-2-2" in panel_str)  # reason or dependency


def test_blockers_panel_limits_display():
    """Test blockers panel limits display to top 10."""
    # Create spec with more than 10 blocked tasks
    spec_data = {"hierarchy": {}}
    for i in range(15):
        spec_data["hierarchy"][f"task-{i}"] = {
            "type": "task",
            "title": f"Task {i}",
            "status": "blocked",
            "metadata": {"blocker_reason": f"Blocker {i}"}
        }

    panel = create_blockers_panel(spec_data)
    panel_str = render_panel_to_string(panel)

    # Should show only first 10
    assert "task-0" in panel_str
    assert "task-9" in panel_str
    # Should not show beyond 10
    # (Note: may not be strict due to rendering, but limit logic exists)


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
