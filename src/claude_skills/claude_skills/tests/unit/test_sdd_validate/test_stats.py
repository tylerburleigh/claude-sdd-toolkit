"""Unit tests for sdd_validate.stats module."""

import json
import pytest
from claude_skills.sdd_validate.stats import (
    calculate_statistics,
    render_statistics,
    SpecStatistics,
)


def test_calculate_statistics_basic():
    """Test basic statistics calculation."""
    spec_data = {
        "spec_id": "test-spec-001",
        "title": "Test Spec",
        "version": "1.0.0",
        "hierarchy": {
            "spec-root": {
                "id": "spec-root",
                "type": "root",
                "status": "in_progress",
                "children": ["phase-1"],
                "total_tasks": 2,
                "completed_tasks": 1,
            },
            "phase-1": {
                "id": "phase-1",
                "type": "phase",
                "status": "in_progress",
                "parent": "spec-root",
                "children": ["task-1-1", "task-1-2"],
            },
            "task-1-1": {
                "id": "task-1-1",
                "type": "task",
                "status": "completed",
                "parent": "phase-1",
                "children": [],
            },
            "task-1-2": {
                "id": "task-1-2",
                "type": "task",
                "status": "pending",
                "parent": "phase-1",
                "children": [],
            },
        },
    }

    stats = calculate_statistics(spec_data)

    assert stats.spec_id == "test-spec-001"
    assert stats.title == "Test Spec"
    assert stats.version == "1.0.0"
    assert stats.status == "in_progress"
    assert stats.totals["nodes"] == 4
    assert stats.totals["tasks"] == 2
    assert stats.totals["phases"] == 1
    assert stats.totals["verifications"] == 0
    assert stats.max_depth == 2
    assert stats.avg_tasks_per_phase == 2.0
    assert stats.progress == 0.5  # 1/2 = 50%


def test_calculate_statistics_with_verifications():
    """Test statistics with verification nodes."""
    spec_data = {
        "spec_id": "test-spec-002",
        "title": "Test Spec",
        "version": "1.0.0",
        "hierarchy": {
            "spec-root": {
                "id": "spec-root",
                "type": "root",
                "status": "in_progress",
                "children": ["task-1"],
                "total_tasks": 1,
                "completed_tasks": 0,
            },
            "task-1": {
                "id": "task-1",
                "type": "task",
                "status": "pending",
                "parent": "spec-root",
                "children": ["verify-1"],
            },
            "verify-1": {
                "id": "verify-1",
                "type": "verify",
                "parent": "task-1",
                "children": [],
            },
        },
    }

    stats = calculate_statistics(spec_data)

    assert stats.totals["tasks"] == 1
    assert stats.totals["verifications"] == 1
    assert stats.verification_coverage == 1.0  # 1 verification for 1 task


def test_calculate_statistics_empty_hierarchy():
    """Test statistics with empty hierarchy."""
    spec_data = {
        "spec_id": "empty-spec",
        "title": "Empty",
        "version": "1.0.0",
        "hierarchy": {},
    }

    stats = calculate_statistics(spec_data)

    assert stats.spec_id == "empty-spec"
    assert stats.totals["nodes"] == 0
    assert stats.totals["tasks"] == 0
    assert stats.max_depth == 0
    assert stats.progress == 0.0


def test_calculate_statistics_status_counts():
    """Test status counting."""
    spec_data = {
        "spec_id": "test-spec-003",
        "title": "Test",
        "version": "1.0.0",
        "hierarchy": {
            "spec-root": {
                "id": "spec-root",
                "type": "root",
                "status": "in_progress",
                "children": ["task-1", "task-2", "task-3"],
                "total_tasks": 3,
                "completed_tasks": 1,
            },
            "task-1": {
                "id": "task-1",
                "type": "task",
                "status": "completed",
                "parent": "spec-root",
                "children": [],
            },
            "task-2": {
                "id": "task-2",
                "type": "task",
                "status": "in_progress",
                "parent": "spec-root",
                "children": [],
            },
            "task-3": {
                "id": "task-3",
                "type": "task",
                "status": "pending",
                "parent": "spec-root",
                "children": [],
            },
        },
    }

    stats = calculate_statistics(spec_data)

    assert stats.status_counts["completed"] == 1
    assert stats.status_counts["in_progress"] == 1
    assert stats.status_counts["pending"] == 1
    assert stats.status_counts["blocked"] == 0


def test_render_statistics_text():
    """Test text rendering of statistics."""
    stats = SpecStatistics(
        spec_id="test-spec-001",
        title="Test Spec",
        version="1.0.0",
        status="in_progress",
        totals={"nodes": 4, "tasks": 2, "phases": 1, "verifications": 0},
        status_counts={"pending": 1, "in_progress": 0, "completed": 1, "blocked": 0},
        max_depth=2,
        avg_tasks_per_phase=2.0,
        verification_coverage=0.0,
        progress=0.5,
        file_size_kb=1.5,
    )

    output = render_statistics(stats, json_output=False)

    assert "Spec ID: test-spec-001" in output
    assert "Title: Test Spec" in output
    assert "Version: 1.0.0" in output
    assert "Nodes: 4" in output
    assert "Tasks: 2" in output
    assert "Phases: 1" in output
    assert "Max depth: 2" in output
    assert "50.00%" in output


def test_render_statistics_json():
    """Test JSON rendering of statistics."""
    stats = SpecStatistics(
        spec_id="test-spec-001",
        title="Test Spec",
        version="1.0.0",
        status="in_progress",
        totals={"nodes": 4, "tasks": 2, "phases": 1, "verifications": 0},
        status_counts={"pending": 1, "in_progress": 0, "completed": 1, "blocked": 0},
        max_depth=2,
        avg_tasks_per_phase=2.0,
        verification_coverage=0.0,
        progress=0.5,
        file_size_kb=1.5,
    )

    output = render_statistics(stats, json_output=True)
    data = json.loads(output)

    assert data["spec_id"] == "test-spec-001"
    assert data["title"] == "Test Spec"
    assert data["totals"]["tasks"] == 2
    assert data["max_depth"] == 2
    assert data["progress"] == 0.5
