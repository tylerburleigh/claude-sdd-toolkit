"""Pytest fixtures for sdd_render tests."""

import json
import pytest
from pathlib import Path


@pytest.fixture
def sample_spec_data():
    """Sample spec data for testing."""
    return {
        "spec_id": "test-spec-2025-01-01-001",
        "title": "Test Specification",
        "generated": "2025-01-01T00:00:00Z",
        "metadata": {
            "status": "draft",
            "estimated_hours": 10,
            "complexity": "medium"
        },
        "hierarchy": {
            "spec-root": {
                "id": "spec-root",
                "type": "spec",
                "title": "Test Specification",
                "status": "in_progress",
                "parent": None,
                "children": ["phase-1", "phase-2"],
                "total_tasks": 8,
                "completed_tasks": 2
            },
            "phase-1": {
                "id": "phase-1",
                "type": "phase",
                "title": "Phase 1",
                "status": "completed",
                "parent": "spec-root",
                "children": ["task-1-1", "task-1-2"],
                "total_tasks": 2,
                "completed_tasks": 2,
                "dependencies": {"blocks": ["phase-2"]}
            },
            "task-1-1": {
                "id": "task-1-1",
                "type": "task",
                "title": "Task 1.1",
                "status": "completed",
                "parent": "phase-1",
                "children": [],
                "dependencies": {"blocks": ["task-1-2", "task-2-1"], "blocked_by": [], "depends": []},
                "total_tasks": 1,
                "completed_tasks": 1,
                "metadata": {
                    "task_category": "implementation",
                    "file_path": "src/module_a.py",
                    "estimated_hours": 2,
                    "risk_level": "low"
                }
            },
            "task-1-2": {
                "id": "task-1-2",
                "type": "task",
                "title": "Task 1.2",
                "status": "completed",
                "parent": "phase-1",
                "children": [],
                "dependencies": {"blocks": ["task-2-2"], "blocked_by": ["task-1-1"], "depends": []},
                "total_tasks": 1,
                "completed_tasks": 1,
                "metadata": {
                    "task_category": "verification",
                    "file_path": "tests/test_module_a.py",
                    "estimated_hours": 1,
                    "risk_level": "low"
                }
            },
            "phase-2": {
                "id": "phase-2",
                "type": "phase",
                "title": "Phase 2",
                "status": "in_progress",
                "parent": "spec-root",
                "children": ["task-2-1", "task-2-2", "task-2-3"],
                "total_tasks": 3,
                "completed_tasks": 0,
                "dependencies": {"blocks": [], "blocked_by": ["phase-1"], "depends": []}
            },
            "task-2-1": {
                "id": "task-2-1",
                "type": "task",
                "title": "Task 2.1",
                "status": "pending",
                "parent": "phase-2",
                "children": [],
                "dependencies": {"blocks": ["task-2-3"], "blocked_by": ["task-1-1"], "depends": []},
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "task_category": "implementation",
                    "file_path": "src/module_b.py",
                    "estimated_hours": 3,
                    "risk_level": "high"
                }
            },
            "task-2-2": {
                "id": "task-2-2",
                "type": "task",
                "title": "Task 2.2",
                "status": "pending",
                "parent": "phase-2",
                "children": [],
                "dependencies": {"blocks": ["task-2-3"], "blocked_by": ["task-1-2"], "depends": []},
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "task_category": "implementation",
                    "file_path": "src/module_b.py",
                    "estimated_hours": 2,
                    "risk_level": "medium"
                }
            },
            "task-2-3": {
                "id": "task-2-3",
                "type": "task",
                "title": "Task 2.3",
                "status": "pending",
                "parent": "phase-2",
                "children": [],
                "dependencies": {"blocks": [], "blocked_by": ["task-2-1", "task-2-2"], "depends": []},
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {
                    "task_category": "verification",
                    "file_path": "tests/test_module_b.py",
                    "estimated_hours": 1,
                    "risk_level": "low"
                }
            }
        }
    }
