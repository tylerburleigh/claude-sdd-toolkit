from __future__ import annotations

from typing import Dict, Any

import pytest
from rich.console import Console

from claude_skills.sdd_update.status_report import (
    _prepare_phases_table_data,
    _prepare_progress_data,
    _prepare_blockers_data,
    create_status_layout,
    print_status_report,
    get_status_summary,
)


pytestmark = pytest.mark.unit


@pytest.fixture
def status_spec() -> Dict[str, Any]:
    """Representative spec hierarchy covering phases, tasks, and blockers."""
    return {
        "hierarchy": {
            "phase-1": {
                "type": "phase",
                "title": "Phase 1: Foundation",
                "status": "completed",
                "total_tasks": 5,
                "completed_tasks": 5,
            },
            "phase-2": {
                "type": "phase",
                "title": "Phase 2: Implementation",
                "status": "in_progress",
                "total_tasks": 10,
                "completed_tasks": 6,
            },
            "phase-3": {
                "type": "phase",
                "title": "Phase 3: Testing",
                "status": "pending",
                "total_tasks": 8,
                "completed_tasks": 0,
            },
            "task-1-1": {
                "type": "task",
                "title": "Create database schema",
                "status": "completed",
            },
            "task-2-1": {
                "type": "task",
                "title": "Implement authentication",
                "status": "completed",
            },
            "task-2-2": {
                "type": "task",
                "title": "Add rate limiting",
                "status": "in_progress",
            },
            "task-2-3": {
                "type": "task",
                "title": "Configure Redis",
                "status": "blocked",
                "metadata": {"blocker_reason": "Redis server not configured"},
                "dependencies": {"blocked_by": ["task-2-2"]},
            },
            "task-3-1": {
                "type": "task",
                "title": "Write unit tests",
                "status": "pending",
            },
        }
    }


@pytest.fixture
def empty_spec() -> Dict[str, Any]:
    """Spec without hierarchy nodes."""
    return {"hierarchy": {}}


@pytest.fixture
def spec_without_blockers() -> Dict[str, Any]:
    """Spec containing only non-blocked tasks."""
    return {
        "hierarchy": {
            "phase-1": {
                "type": "phase",
                "title": "Phase 1",
                "status": "in_progress",
                "total_tasks": 2,
                "completed_tasks": 1,
            },
            "task-1-1": {
                "type": "task",
                "title": "Task 1",
                "status": "completed",
            },
            "task-1-2": {
                "type": "task",
                "title": "Task 2",
                "status": "in_progress",
            },
        }
    }


def _render(renderable: Any) -> str:
    """Render a Rich renderable to text for assertion-friendly inspection."""
    console = Console(record=True, width=100)
    console.print(renderable)
    return console.export_text()


class TestPhasePreparation:
    def test_prepare_phases_table_data_returns_sorted_rows(self, status_spec: Dict[str, Any]) -> None:
        rows, count = _prepare_phases_table_data(status_spec)

        assert count == 3
        assert [row["Phase"] for row in rows] == [
            "Phase 1: Foundation",
            "Phase 2: Implementation",
            "Phase 3: Testing",
        ]
        assert rows[0]["Status"].startswith("✓")
        assert "60%" in rows[1]["Progress"]

    def test_prepare_phases_table_handles_empty_spec(self, empty_spec: Dict[str, Any]) -> None:
        rows, count = _prepare_phases_table_data(empty_spec)

        assert rows == []
        assert count == 0


class TestProgressPreparation:
    def test_prepare_progress_data_populates_metrics(self, status_spec: Dict[str, Any]) -> None:
        rows, subtitle = _prepare_progress_data(status_spec)

        metrics = {row["Metric"]: row["Value"] for row in rows}
        assert subtitle == "40% complete"
        assert metrics["Overall"] == "40.0%"
        assert metrics["Completed"] == "2"
        assert metrics["In Progress"] == "1"
        assert metrics["Blocked"] == "1"
        assert metrics["Remaining"] == "3"

    def test_prepare_progress_data_with_no_tasks(self, empty_spec: Dict[str, Any]) -> None:
        rows, subtitle = _prepare_progress_data(empty_spec)

        assert rows == [{"Metric": "Overall", "Value": "No tasks"}]
        assert subtitle == "No tasks"


class TestBlockerPreparation:
    def test_prepare_blockers_data_includes_reason(self, status_spec: Dict[str, Any]) -> None:
        content, blocker_count = _prepare_blockers_data(status_spec)

        assert blocker_count == 1
        assert "task-2-3" in content
        assert "Redis server not configured" in content

    def test_prepare_blockers_data_without_blockers(self, spec_without_blockers: Dict[str, Any]) -> None:
        content, blocker_count = _prepare_blockers_data(spec_without_blockers)

        assert blocker_count == 0
        assert content.startswith("✓ No blockers")

    def test_prepare_blockers_data_limits_display(self) -> None:
        spec_data: Dict[str, Any] = {"hierarchy": {}}
        for i in range(15):
            spec_data["hierarchy"][f"task-{i}"] = {
                "type": "task",
                "title": f"Task {i}",
                "status": "blocked",
                "metadata": {"blocker_reason": f"Blocker {i}"},
            }

        content, blocker_count = _prepare_blockers_data(spec_data)

        assert blocker_count == 15
        assert "task-0" in content
        # Content is truncated to ten entries to keep panels readable.
        assert "task-10" not in content


class TestLayoutRendering:
    def test_create_status_layout_renders_panels(self, status_spec: Dict[str, Any]) -> None:
        layout = create_status_layout(status_spec)
        rendered = _render(layout)

        assert "Phases" in rendered
        assert "Progress" in rendered
        assert "Blockers" in rendered
        assert "Phase 1: Foundation" in rendered

    def test_print_status_report_uses_rich_ui(self, monkeypatch: pytest.MonkeyPatch, status_spec: Dict[str, Any]) -> None:
        console = Console(record=True, width=100)

        class StubUi:
            def __init__(self, console: Console) -> None:
                self.console = console

        stub_ui = StubUi(console)
        monkeypatch.setattr("claude_skills.sdd_update.status_report.create_ui", lambda: stub_ui)

        print_status_report(status_spec, title="Daily Status")
        output = console.export_text()

        assert "Daily Status" in output
        assert "Phases" in output
        assert "Progress" in output


class TestStatusSummary:
    def test_get_status_summary_counts_tasks(self, status_spec: Dict[str, Any]) -> None:
        summary = get_status_summary(status_spec)

        assert summary["total_tasks"] == 5
        assert summary["completed_tasks"] == 2
        assert summary["in_progress_tasks"] == 1
        assert summary["blocked_tasks"] == 1
        assert len(summary["phases"]) == 3
        assert len(summary["blockers"]) == 1

    def test_get_status_summary_handles_empty_spec(self, empty_spec: Dict[str, Any]) -> None:
        summary = get_status_summary(empty_spec)

        assert summary["total_tasks"] == 0
        assert summary["completed_tasks"] == 0
        assert summary["in_progress_tasks"] == 0
        assert summary["blocked_tasks"] == 0
        assert summary["phases"] == []
        assert summary["blockers"] == []
