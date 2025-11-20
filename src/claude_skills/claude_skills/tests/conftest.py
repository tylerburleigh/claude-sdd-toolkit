"""
Pytest configuration and shared fixtures for SDD Python Tools tests.

Provides fixtures for:
- Sample spec files and JSON specs
- Temporary directories
- Mock filesystem operations
- Common test data
"""

import json
import copy
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# No path manipulation needed - package is installed!


# =============================================================================
# Fixture Helpers
# =============================================================================

def create_sample_spec_content(
    spec_id: str = "test-spec-2025-01-01-001",
    title: str = "Test Specification",
    estimated_hours: float = 10.0,
    num_phases: int = 2,
    tasks_per_phase: int = 2,
    include_verify: bool = False,
    include_subtasks: bool = False
) -> Dict:
    """Create a sample spec JSON structure.

    Args:
        spec_id: Specification identifier
        title: Specification title
        estimated_hours: Estimated hours for the spec
        num_phases: Number of phases to create
        tasks_per_phase: Number of tasks per phase
        include_verify: Whether to include verify nodes (default: False)
        include_subtasks: Whether to include subtask nodes (default: False)

    Returns:
        Complete spec data dictionary
    """
    # Calculate actual task count based on what we're including
    tasks_count = num_phases * tasks_per_phase
    if include_subtasks:
        tasks_count += num_phases * tasks_per_phase  # Add subtasks
    if include_verify:
        tasks_count += num_phases * tasks_per_phase  # Add verify tasks

    hierarchy: Dict[str, Any] = {
        "spec-root": {
            "id": "spec-root",
            "type": "spec",
            "title": title,
            "status": "in_progress",
            "parent": None,
            "children": [],
            "total_tasks": tasks_count,
            "completed_tasks": 0,
            "metadata": {}
        }
    }

    for phase_num in range(1, num_phases + 1):
        phase_id = f"phase-{phase_num}"
        phase_children = []

        # Calculate phase task count
        phase_task_count = tasks_per_phase
        if include_subtasks:
            phase_task_count += tasks_per_phase
        if include_verify:
            phase_task_count += tasks_per_phase

        hierarchy[phase_id] = {
            "id": phase_id,
            "type": "phase",
            "title": f"Phase {phase_num} Title",
            "status": "pending" if phase_num > 1 else "in_progress",
            "parent": "spec-root",
            "children": phase_children,
            "total_tasks": phase_task_count,
            "completed_tasks": 0,
            "metadata": {
                "estimated_hours": estimated_hours / num_phases
            }
        }

        hierarchy["spec-root"]["children"].append(phase_id)

        for task_num in range(1, tasks_per_phase + 1):
            task_id = f"task-{phase_num}-{task_num}"
            subtask_id = f"task-{phase_num}-{task_num}-1"
            verify_id = f"verify-{phase_num}-{task_num}"

            # Create task with or without subtask children
            task_children = [subtask_id] if include_subtasks else []

            hierarchy[task_id] = {
                "id": task_id,
                "type": "task",
                "title": f"Task {task_id}",
                "status": "pending",
                "parent": phase_id,
                "children": task_children,
                "total_tasks": 1,
                "completed_tasks": 0,
                "dependencies": {
                    "blocked_by": [],
                    "depends": [],
                    "blocks": []
                },
                "metadata": {
                    "file_path": f"src/test_{phase_num}_{task_num}.py",
                    "estimated_hours": estimated_hours / (num_phases * tasks_per_phase)
                }
            }

            phase_children.append(task_id)

            # Optionally create subtask
            if include_subtasks:
                hierarchy[subtask_id] = {
                    "id": subtask_id,
                    "type": "subtask",
                    "title": f"Subtask for {task_id}",
                    "status": "pending",
                    "parent": task_id,
                    "children": [],
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "metadata": {}
                }

            # Optionally create verify node
            if include_verify:
                hierarchy[verify_id] = {
                    "id": verify_id,
                    "type": "verify",
                    "title": f"Verify {task_id}",
                    "status": "pending",
                    "parent": phase_id,
                    "children": [],
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "metadata": {
                        "verification_type": "auto",
                        "command": f"pytest tests/test_{phase_num}_{task_num}.py"
                    }
                }
                phase_children.append(verify_id)

    return {
        "spec_id": spec_id,
        "title": title,
        "generated": "2025-01-01T00:00:00Z",
        "last_updated": "2025-01-01T00:00:00Z",
        "metadata": {
            "estimated_hours": estimated_hours,
            "owner": "Test Author",
            "status": "active"
        },
        "hierarchy": hierarchy
    }


def create_sample_spec_data(
    spec_id: str = "test-spec-2025-01-01-001",
    num_phases: int = 2,
    tasks_per_phase: int = 2,
    with_dependencies: bool = False
) -> Dict[str, Any]:
    """Create sample JSON spec data."""
    state = {
        "spec_id": spec_id,
        "title": "Test Specification",
        "generated": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "hierarchy": {}
    }

    # Add spec-root node
    phase_ids = [f"phase-{i}" for i in range(1, num_phases + 1)]
    total_task_count = num_phases * tasks_per_phase
    state["hierarchy"]["spec-root"] = {
        "id": "spec-root",
        "type": "spec",
        "title": "Test Specification",
        "status": "in_progress",
        "parent": None,
        "children": phase_ids,
        "total_tasks": total_task_count,
        "completed_tasks": 0,
        "metadata": {}
    }

    for phase_num in range(1, num_phases + 1):
        phase_id = f"phase-{phase_num}"
        state["hierarchy"][phase_id] = {
            "id": phase_id,
            "type": "phase",
            "title": f"Phase {phase_num} Title",
            "status": "pending" if phase_num > 1 else "in_progress",
            "parent": "spec-root",
            "children": [],
            "total_tasks": tasks_per_phase,
            "completed_tasks": 0,
            "metadata": {
                "estimated_hours": 5.0
            }
        }

        for task_num in range(1, tasks_per_phase + 1):
            task_id = f"task-{phase_num}-{task_num}"

            task_data = {
                "id": task_id,
                "type": "task",
                "title": f"Task {task_id}",
                "status": "pending",
                "parent": phase_id,
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "dependencies": {
                    "blocked_by": [],
                    "depends": [],
                    "blocks": []
                },
                "metadata": {
                    "file_path": f"src/test_{phase_num}_{task_num}.py",
                    "estimated_hours": 2.5
                }
            }

            # Add dependencies if requested
            if with_dependencies and phase_num == 2 and task_num == 2:
                # Make task-2-2 depend on task-2-1
                task_data["dependencies"]["blocked_by"] = ["task-2-1"]

            state["hierarchy"][task_id] = task_data
            state["hierarchy"][phase_id]["children"].append(task_id)

    return state


def ensure_json_spec(
    specs_structure: Path,
    *,
    spec_id: str,
    title: Optional[str] = None,
    num_phases: int = 2,
    tasks_per_phase: int = 2,
    estimated_hours: float = 10.0,
) -> Path:
    """Ensure a JSON spec file exists for the given spec_id."""
    spec_path = specs_structure / "active" / f"{spec_id}.json"

    if not spec_path.exists():
        spec_content = create_sample_spec_content(
            spec_id=spec_id,
            title=title or spec_id.replace("-", " ").title(),
            estimated_hours=estimated_hours,
            num_phases=num_phases,
            tasks_per_phase=tasks_per_phase,
        )
        spec_path.write_text(json.dumps(spec_content, indent=2))

    return spec_path


def ensure_json_spec_file(specs_structure: Path, spec_data: Dict[str, Any]) -> Path:
    """Ensure matching JSON spec file is created for given spec data."""
    json_spec_path = specs_structure / "active" / f"{spec_data['spec_id']}.json"
    if not json_spec_path.exists():
        spec_data = create_sample_spec_data(
            spec_id=spec_data["spec_id"],
            num_phases=sum(1 for node in spec_data.get("hierarchy", {}).values() if node.get("type") == "phase"),
            tasks_per_phase=2,
        )
        json_spec_path.write_text(json.dumps(spec_data, indent=2))
    return json_spec_path


def write_spec_data(specs_structure: Path, data: Dict[str, Any]) -> Path:
    """Write updated spec data to the active specs directory."""
    spec_file = specs_structure / "active" / f"{data.get('spec_id', 'spec')}.json"
    spec_file.write_text(json.dumps(data, indent=2))
    return spec_file


# =============================================================================
# Directory and File Fixtures
# =============================================================================

@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory that's cleaned up after test."""
    yield tmp_path
    # Cleanup happens automatically with tmp_path


@pytest.fixture
def specs_structure(tmp_path):
    """
    Create a complete specs directory structure.

    Structure:
        tmp_path/
        └── specs/
            ├── active/      (JSON spec files)
            ├── completed/   (completed specs)
            └── archived/    (archived specs)

    Returns:
        Path to the specs directory (containing active/completed/archived subdirectories)
    """
    specs_dir = tmp_path / "specs"
    (specs_dir / "active").mkdir(parents=True)
    (specs_dir / "completed").mkdir(parents=True)
    (specs_dir / "archived").mkdir(parents=True)
    (specs_dir / "active").mkdir(parents=True, exist_ok=True)

    assert (specs_dir / "active").exists(), "Expected specs/active directory to exist"

    # Return the specs directory, not specs/active
    return specs_dir


# =============================================================================
# Spec File Fixtures
# =============================================================================

@pytest.fixture
def sample_spec_simple(specs_structure):
    """Create a simple spec file with 2 phases, 2 tasks each."""
    return ensure_json_spec(
        specs_structure,
        spec_id="simple-spec-2025-01-01-001",
        title="Simple Test Spec",
        num_phases=2,
        tasks_per_phase=2,
        estimated_hours=10.0,
    )


@pytest.fixture
def sample_spec_complex(specs_structure):
    """Create a complex spec file with 3 phases, 3 tasks each."""
    base_path = ensure_json_spec(
        specs_structure,
        spec_id="complex-spec-2025-01-01-002",
        title="Complex Test Spec",
        estimated_hours=30.0,
        num_phases=3,
        tasks_per_phase=3,
    )

    spec_data = json.loads(base_path.read_text())
    phase_children = []

    for phase_num in range(1, 4):
        phase_id = f"phase-{phase_num}"
        spec_data.setdefault("hierarchy", {})[phase_id] = {
            "id": phase_id,
            "type": "phase",
            "title": f"Phase {phase_num} Title",
            "status": "pending" if phase_num > 1 else "in_progress",
            "parent": "spec-root",
            "children": [],
            "total_tasks": 3,
            "completed_tasks": 0,
            "metadata": {"estimated_hours": 10},
        }
        phase_children.append(phase_id)

        for task_num in range(1, 4):
            task_id = f"task-{phase_num}-{task_num}"
            spec_data["hierarchy"][task_id] = {
                "id": task_id,
                "type": "task",
                "title": f"Task {task_id}",
                "status": "pending",
                "parent": phase_id,
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {"file_path": f"src/phase{phase_num}/task{task_num}.py"},
            }
            spec_data["hierarchy"][phase_id]["children"].append(task_id)

    spec_data["hierarchy"]["spec-root"] = {
        "id": "spec-root",
        "type": "spec",
        "title": spec_data.get("title", "Complex Test Spec"),
        "status": "in_progress",
        "parent": None,
        "children": phase_children,
        "total_tasks": len(phase_children) * 3,
        "completed_tasks": 0,
        "metadata": {},
    }

    return write_spec_data(specs_structure, spec_data)


@pytest.fixture
def sample_spec_invalid(specs_structure):
    """Create an invalid spec file (missing frontmatter)."""
    spec_path = ensure_json_spec(
        specs_structure,
        spec_id="invalid-spec-2025-01-01-003",
        title="Invalid Spec",
    )

    spec_data = json.loads(spec_path.read_text())
    spec_data.pop("hierarchy", None)
    spec_path.write_text(json.dumps(spec_data, indent=2))

    return spec_path


# =============================================================================
# JSON Spec Fixtures
# =============================================================================

@pytest.fixture
def sample_json_spec_simple(specs_structure, sample_spec_simple):
    """Create a simple JSON spec for testing basic operations."""
    # Use create_sample_spec_content without verify nodes for progress tests
    spec_data = create_sample_spec_content(
        spec_id="simple-spec-2025-01-01-001",
        title="Simple Test Spec",
        num_phases=2,
        tasks_per_phase=2,
        estimated_hours=10.0,
        include_verify=False  # Exclude verify nodes to keep counts simple
    )

    # Write to disk
    json_spec_file = specs_structure / "active" / "simple-spec-2025-01-01-001.json"
    json_spec_file.write_text(json.dumps(spec_data, indent=2))

    return json_spec_file


@pytest.fixture
def sample_json_spec_complex(specs_structure, sample_spec_complex):
    """Create a complex JSON spec for the complex spec."""
    spec_data = create_sample_spec_data(
        spec_id="complex-spec-2025-01-01-002",
        num_phases=3,
        tasks_per_phase=3,
        with_dependencies=False
    )

    json_spec_file = specs_structure / "active" / "complex-spec-2025-01-01-002.json"
    json_spec_file.write_text(json.dumps(spec_data, indent=2))

    return json_spec_file


@pytest.fixture
def sample_json_spec_with_deps(specs_structure, sample_spec_simple):
    """Create a JSON spec with task dependencies."""
    # Create spec data with dependencies using create_sample_spec_data
    spec_data = create_sample_spec_data(
        spec_id="deps-spec-2025-01-01-003",
        num_phases=2,
        tasks_per_phase=2,
        with_dependencies=True  # This creates task-2-2 blocked_by task-2-1
    )

    # Update top-level metadata
    spec_data["title"] = "Dependency Spec"
    spec_data["generated"] = "2025-01-01T00:00:00Z"
    spec_data["last_updated"] = "2025-01-01T00:00:00Z"
    spec_data["metadata"] = {
        "estimated_hours": 10.0,
        "owner": "Test Author",
        "status": "active"
    }

    # Write the spec with dependencies to disk
    json_spec_file = specs_structure / "active" / "deps-spec-2025-01-01-003.json"
    json_spec_file.write_text(json.dumps(spec_data, indent=2))

    return json_spec_file


@pytest.fixture
def sample_json_spec_circular_deps(specs_structure, sample_spec_simple):
    """Create a JSON spec with circular dependencies."""
    ensure_json_spec(
        specs_structure,
        spec_id="circular-spec-2025-01-01-004",
        title="Circular Dependency Spec",
        num_phases=1,
        tasks_per_phase=3,
    )

    spec_data = create_sample_spec_data(
        spec_id="circular-spec-2025-01-01-004",
        num_phases=1,
        tasks_per_phase=3,
        with_dependencies=False
    )

    # Create circular dependency: task-1-1 -> task-1-2 -> task-1-3 -> task-1-1
    spec_data["hierarchy"]["task-1-1"]["dependencies"]["blocked_by"] = ["task-1-3"]
    spec_data["hierarchy"]["task-1-2"]["dependencies"]["blocked_by"] = ["task-1-1"]
    spec_data["hierarchy"]["task-1-3"]["dependencies"]["blocked_by"] = ["task-1-2"]

    # Ensure the blocking relationships are mutual to trigger detection
    spec_data["hierarchy"]["task-1-1"]["dependencies"]["blocks"] = ["task-1-2"]
    spec_data["hierarchy"]["task-1-2"]["dependencies"]["blocks"] = ["task-1-3"]
    spec_data["hierarchy"]["task-1-3"]["dependencies"]["blocks"] = ["task-1-1"]

    # Save the spec file
    spec_path = specs_structure / "active" / "circular-spec-2025-01-01-004.json"
    spec_path.write_text(json.dumps(spec_data, indent=2))

    return spec_path


@pytest.fixture
def sample_json_spec_with_blockers(specs_structure, sample_spec_simple):
    """Create a JSON spec with some blocked tasks."""
    spec_data = create_sample_spec_data(
        spec_id="blocked-spec-2025-01-01-005",
        num_phases=2,
        tasks_per_phase=2
    )

    # Update top-level metadata
    spec_data["title"] = "Blocked Spec"
    spec_data["generated"] = "2025-01-01T00:00:00Z"
    spec_data["last_updated"] = "2025-01-01T00:00:00Z"
    spec_data["metadata"] = {
        "estimated_hours": 10.0,
        "owner": "Test Author",
        "status": "active"
    }

    # Mark task-1-2 as blocked
    spec_data["hierarchy"]["task-1-2"]["status"] = "blocked"
    spec_data["hierarchy"]["task-1-2"]["metadata"]["blocked_at"] = "2025-01-01T14:00:00Z"
    spec_data["hierarchy"]["task-1-2"]["metadata"]["blocker_type"] = "dependency"
    spec_data["hierarchy"]["task-1-2"]["metadata"]["blocker_description"] = "Waiting on external API setup"
    spec_data["hierarchy"]["task-1-2"]["metadata"]["blocker_ticket"] = "OPS-123"

    # Mark task-2-1 as blocked
    spec_data["hierarchy"]["task-2-1"]["status"] = "blocked"
    spec_data["hierarchy"]["task-2-1"]["metadata"]["blocked_at"] = "2025-01-01T15:30:00Z"
    spec_data["hierarchy"]["task-2-1"]["metadata"]["blocker_type"] = "technical"
    spec_data["hierarchy"]["task-2-1"]["metadata"]["blocker_description"] = "Bug in upstream library"
    spec_data["hierarchy"]["task-2-1"]["metadata"]["blocked_by_external"] = True

    # Mark task-1-1 as completed
    spec_data["hierarchy"]["task-1-1"]["status"] = "completed"
    spec_data["hierarchy"]["task-1-1"]["metadata"]["completed_at"] = "2025-01-01T12:00:00Z"

    # Write to disk
    json_spec_file = specs_structure / "active" / "blocked-spec-2025-01-01-005.json"
    json_spec_file.write_text(json.dumps(spec_data, indent=2))

    return json_spec_file


@pytest.fixture
def sample_json_spec_with_time(specs_structure):
    """Create a JSON spec with time tracking data."""
    spec_data = create_sample_spec_content(
        spec_id="time-spec-2025-01-01-006",
        title="Time Tracking Spec",
        num_phases=2,
        tasks_per_phase=2,
    )

    # Add time tracking to phase-1 tasks
    spec_data["hierarchy"]["task-1-1"]["status"] = "completed"
    spec_data["hierarchy"]["task-1-1"]["metadata"]["estimated_hours"] = 2.0
    spec_data["hierarchy"]["task-1-1"]["metadata"]["actual_hours"] = 2.5
    spec_data["hierarchy"]["task-1-1"]["metadata"]["started_at"] = "2025-01-01T09:00:00Z"
    spec_data["hierarchy"]["task-1-1"]["metadata"]["completed_at"] = "2025-01-01T11:30:00Z"

    spec_data["hierarchy"]["task-1-2"]["status"] = "completed"
    spec_data["hierarchy"]["task-1-2"]["metadata"]["estimated_hours"] = 3.0
    spec_data["hierarchy"]["task-1-2"]["metadata"]["actual_hours"] = 2.5
    spec_data["hierarchy"]["task-1-2"]["metadata"]["started_at"] = "2025-01-01T11:30:00Z"
    spec_data["hierarchy"]["task-1-2"]["metadata"]["completed_at"] = "2025-01-01T14:00:00Z"

    # Update phase-1 as completed
    spec_data["hierarchy"]["phase-1"]["status"] = "completed"

    # Add time tracking to phase-2 tasks
    spec_data["hierarchy"]["task-2-1"]["status"] = "in_progress"
    spec_data["hierarchy"]["task-2-1"]["metadata"]["estimated_hours"] = 4.0
    spec_data["hierarchy"]["task-2-1"]["metadata"]["started_at"] = "2025-01-01T14:00:00Z"

    spec_data["hierarchy"]["task-2-2"]["metadata"]["estimated_hours"] = 3.0

    # Save the spec file
    spec_path = specs_structure / "active" / "time-spec-2025-01-01-006.json"
    spec_path.write_text(json.dumps(spec_data, indent=2))

    return spec_path


@pytest.fixture
def sample_json_spec_completed(specs_structure):
    """Create a fully completed JSON spec."""
    spec_data = create_sample_spec_content(
        spec_id="completed-spec-2025-01-01-007",
        title="Completed Spec",
        num_phases=2,
        tasks_per_phase=2,
    )

    # Mark all tasks as completed
    for node_id, node_data in spec_data["hierarchy"].items():
        if node_data["type"] in ["task", "verify"]:
            node_data["status"] = "completed"
            node_data["metadata"]["completed_at"] = "2025-01-01T18:00:00Z"

    # Mark all phases as completed
    for node_id, node_data in spec_data["hierarchy"].items():
        if node_data["type"] == "phase":
            node_data["status"] = "completed"

    # Recalculate progress to update counters
    from claude_skills.common.progress import recalculate_progress
    spec_data = recalculate_progress(spec_data)

    # Save to active folder
    json_spec_file = specs_structure / "active" / "completed-spec-2025-01-01-007.json"
    json_spec_file.write_text(json.dumps(spec_data, indent=2))

    return json_spec_file


@pytest.fixture
def valid_json_spec(specs_structure):
    """Create a valid JSON spec with verification nodes for testing verification operations."""
    # Create a JSON spec with verification nodes using create_sample_spec_content
    # which includes verify nodes
    spec_data = create_sample_spec_content(
        spec_id="test-anchors-2025-01-01-001",
        title="Test Anchors Spec",
        num_phases=1,
        tasks_per_phase=1,
        estimated_hours=5.0,
        include_verify=True
    )

    # Create the actual spec file in the specs/active directory
    spec_file = specs_structure / "active" / "test-anchors-2025-01-01-001.json"
    spec_file.write_text(json.dumps(spec_data, indent=2))

    # Also write to a separate file that the test can read
    json_spec_file = specs_structure.parent / "valid_json_spec.json"
    json_spec_file.write_text(json.dumps(spec_data, indent=2))

    return json_spec_file


@pytest.fixture
def state_with_orphaned_nodes(specs_structure):
    """Create a JSON spec with orphaned nodes (missing parents/invalid dependencies)."""
    spec_data = {
        "spec_id": "orphaned-nodes-2025-01-20-003",
        "title": "Orphaned Nodes Test Spec",
        "version": "1.0.0",
        "generated": "2025-01-20T10:00:00Z",
        "last_updated": "2025-01-20T10:00:00Z",
        "hierarchy": {
            "spec-root": {
                "id": "spec-root",
                "type": "spec",
                "status": "in_progress",
                "title": "Orphaned Nodes Test Spec",
                "children": ["phase-1"],
                "parent": None,
                "total_tasks": 2,
                "completed_tasks": 0,
                "metadata": {}
            },
            "phase-1": {
                "id": "phase-1",
                "type": "phase",
                "status": "in_progress",
                "title": "Phase 1",
                "parent": "spec-root",
                "children": ["task-1-1", "task-1-2"],
                "total_tasks": 2,
                "completed_tasks": 0,
                "metadata": {}
            },
            "task-1-1": {
                "id": "task-1-1",
                "type": "task",
                "status": "pending",
                "title": "Task 1.1",
                "parent": "nonexistent-phase",  # Orphaned - parent doesn't exist
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "dependencies": {
                    "blocked_by": ["nonexistent-task"],  # Depends on non-existent task
                    "depends": [],
                    "blocks": []
                },
                "metadata": {"file_path": "task-1-1.md"}
            },
            "task-1-2": {
                "id": "task-1-2",
                "type": "task",
                "status": "pending",
                "title": "Task 1.2",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "dependencies": {
                    "blocked_by": [],
                    "depends": ["nonexistent-task"],  # Depends on non-existent task
                    "blocks": []
                },
                "metadata": {"file_path": "task-1-2.md"}
            }
        }
    }

    spec_file = specs_structure.parent / "orphaned_nodes_spec.json"
    spec_file.write_text(json.dumps(spec_data, indent=2))
    return spec_file


@pytest.fixture
def invalid_state_structure(specs_structure):
    """Create a JSON spec with nodes missing required fields."""
    spec_data = {
        "spec_id": "invalid-structure-2025-01-20-004",
        "title": "Invalid Structure Test Spec",
        "version": "1.0.0",
        "generated": "2025-01-20T10:00:00Z",
        "last_updated": "2025-01-20T10:00:00Z",
        "hierarchy": {
            "spec-root": {
                "id": "spec-root",
                "type": "spec",
                "status": "in_progress",
                "title": "Invalid Structure Test Spec",
                "children": ["phase-1"],
                "parent": None,
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {}
            },
            "phase-1": {
                "id": "phase-1",
                "type": "phase",
                "status": "in_progress",
                "title": "Phase 1",
                "parent": "spec-root",
                "children": ["task-1-1"],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {}
            },
            "task-1-1": {
                "id": "task-1-1",
                # Missing "type" field - REQUIRED
                "status": "pending",
                "title": "Task 1.1",
                "parent": "phase-1",
                # Missing "children" field - REQUIRED
                # Missing "dependencies" field - REQUIRED
                "metadata": {}  # Missing file_path
            }
        }
    }

    spec_file = specs_structure.parent / "invalid_structure_spec.json"
    spec_file.write_text(json.dumps(spec_data, indent=2))
    return spec_file


@pytest.fixture
def state_with_circular_deps_plan(specs_structure):
    """Create a JSON spec with circular dependencies."""
    spec_data = {
        "spec_id": "circular-deps-2025-01-20-005",
        "title": "Circular Dependencies Test Spec",
        "version": "1.0.0",
        "generated": "2025-01-20T10:00:00Z",
        "last_updated": "2025-01-20T10:00:00Z",
        "hierarchy": {
            "spec-root": {
                "id": "spec-root",
                "type": "spec",
                "status": "in_progress",
                "title": "Circular Dependencies Test Spec",
                "children": ["phase-1"],
                "parent": None,
                "total_tasks": 3,
                "completed_tasks": 0,
                "metadata": {}
            },
            "phase-1": {
                "id": "phase-1",
                "type": "phase",
                "status": "in_progress",
                "title": "Phase 1",
                "parent": "spec-root",
                "children": ["task-1-1", "task-1-2", "task-1-3"],
                "total_tasks": 3,
                "completed_tasks": 0,
                "metadata": {}
            },
            "task-1-1": {
                "id": "task-1-1",
                "type": "task",
                "status": "blocked",
                "title": "Task 1.1",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "dependencies": {
                    "blocked_by": ["task-1-3"],  # Circular: 1 → 2 → 3 → 1
                    "depends": [],
                    "blocks": ["task-1-2"]
                },
                "metadata": {"file_path": "task-1-1.md"}
            },
            "task-1-2": {
                "id": "task-1-2",
                "type": "task",
                "status": "blocked",
                "title": "Task 1.2",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "dependencies": {
                    "blocked_by": ["task-1-1"],  # Circular: 1 → 2 → 3 → 1
                    "depends": [],
                    "blocks": ["task-1-3"]
                },
                "metadata": {"file_path": "task-1-2.md"}
            },
            "task-1-3": {
                "id": "task-1-3",
                "type": "task",
                "status": "blocked",
                "title": "Task 1.3",
                "parent": "phase-1",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "dependencies": {
                    "blocked_by": ["task-1-2"],  # Circular: 1 → 2 → 3 → 1
                    "depends": [],
                    "blocks": ["task-1-1"]
                },
                "metadata": {"file_path": "task-1-3.md"}
            }
        }
    }

    spec_file = specs_structure.parent / "circular_deps_spec.json"
    spec_file.write_text(json.dumps(spec_data, indent=2))
    return spec_file


# =============================================================================
# Project Structure Fixtures
# =============================================================================

@pytest.fixture
def sample_node_project(tmp_path):
    """Create a sample Node.js project structure."""
    project_dir = tmp_path / "node_project"
    project_dir.mkdir()

    # package.json
    package_json = {
        "name": "test-project",
        "version": "1.0.0",
        "dependencies": {
            "express": "^4.18.0",
            "lodash": "^4.17.21"
        },
        "devDependencies": {
            "jest": "^29.0.0",
            "eslint": "^8.0.0"
        },
        "scripts": {
            "test": "jest",
            "lint": "eslint ."
        }
    }
    (project_dir / "package.json").write_text(json.dumps(package_json, indent=2))

    # Create some source files
    (project_dir / "src").mkdir()
    (project_dir / "src" / "index.js").write_text("console.log('Hello');")

    # Create some test files
    (project_dir / "tests").mkdir()
    (project_dir / "tests" / "index.test.js").write_text("test('example', () => {});")

    return project_dir


@pytest.fixture
def sample_python_project(tmp_path):
    """Create a sample Python project structure."""
    project_dir = tmp_path / "python_project"
    project_dir.mkdir()

    # requirements.txt
    requirements = "requests>=2.31.0\nflask>=3.0.0\n"
    (project_dir / "requirements.txt").write_text(requirements)

    # requirements-dev.txt
    requirements_dev = "pytest>=7.4.0\nblack>=23.0.0\nmypy>=1.7.0\n"
    (project_dir / "requirements-dev.txt").write_text(requirements_dev)

    # Create source files
    (project_dir / "src").mkdir()
    (project_dir / "src" / "__init__.py").write_text("")
    (project_dir / "src" / "main.py").write_text("def hello():\n    return 'world'")

    # Create test files
    (project_dir / "tests").mkdir()
    (project_dir / "tests" / "__init__.py").write_text("")
    (project_dir / "tests" / "test_main.py").write_text("def test_hello():\n    pass")

    return project_dir


# =============================================================================
# Data Fixtures
# =============================================================================

@pytest.fixture
def sample_frontmatter():
    """Sample frontmatter data."""
    return {
        "spec_id": "test-spec-2025-01-01-001",
        "title": "Test Specification",
        "created": "2025-01-01",
        "author": "Test Author",
        "estimated_hours": 10.0,
        "status": "active"
    }


@pytest.fixture
def sample_task_data():
    """Sample task data."""
    return {
        "id": "task-1-1",
        "type": "task",
        "title": "Sample Task",
        "status": "pending",
        "parent": "phase-1",
        "children": [],
        "dependencies": {
            "blocked_by": [],
            "depends": [],
            "blocks": []
        },
        "metadata": {
            "file_path": "src/sample.py",
            "estimated_hours": 2.5
        }
    }


# =============================================================================
# Mock Fixtures
# =============================================================================

@pytest.fixture
def mock_printer(mocker):
    """Mock PrettyPrinter for testing output."""
    from claude_skills.common import PrettyPrinter
    mock = mocker.Mock(spec=PrettyPrinter)
    return mock


# =============================================================================
# Test Helpers
# =============================================================================

@pytest.fixture
def assert_json_structure():
    """Helper to assert JSON structure."""
    def _assert(data: Dict, expected_keys: list):
        """Assert that data contains all expected keys."""
        for key in expected_keys:
            assert key in data, f"Expected key '{key}' not found in {data.keys()}"
    return _assert


@pytest.fixture
def create_temp_spec_file(tmp_path):
    """Factory fixture to create temporary JSON spec files."""
    def _create(data: Dict, filename: str = "test-spec.json") -> Path:
        spec_file = tmp_path / filename
        spec_file.write_text(json.dumps(data, indent=2))
        return spec_file
    return _create


@pytest.fixture
def create_temp_json_spec(tmp_path):
    """Factory fixture to create temporary JSON specs."""
    def _create(data: Dict, filename: str = "test-spec.json") -> Path:
        json_spec_file = tmp_path / filename
        json_spec_file.parent.mkdir(parents=True, exist_ok=True)
        json_spec_file.write_text(json.dumps(data, indent=2))
        return json_spec_file
    return _create


# =============================================================================
# SDD-Plan Specific Fixtures
# =============================================================================

@pytest.fixture
def sample_spec_invalid_frontmatter(create_temp_spec_file):
    """Create a spec missing required top-level fields."""
    spec_data = {
        # Missing required fields like spec_id/title/hierarchy
        "metadata": {
            "owner": "Test Author"
        }
    }
    return create_temp_spec_file(spec_data, "no-frontmatter-spec.json")


@pytest.fixture
def sample_spec_invalid_phases(create_temp_spec_file):
    """Create a spec with invalid phase structure."""
    spec_data = _build_spec_json(
        spec_id="test-invalid-phases-2025-01-01-003",
        title="Test Invalid Phases",
        hierarchy={
            "spec-root": {
                "id": "spec-root",
                "type": "spec",
                "title": "Test Invalid Phases",
                "status": "in_progress",
                "parent": None,
                "children": ["phase-A", "task-orphan"],
                "total_tasks": 2,
                "completed_tasks": 0,
                "metadata": {}
            },
            # Phase with invalid ID format
            "phase-A": {
                "id": "phase-A",
                "type": "phase",
                "title": "Phase A",
                "status": "pending",
                "parent": "spec-root",
                "children": ["task-1-1"],
                "total_tasks": 1,
                "completed_tasks": 0,
                "metadata": {}
            },
            # Task directly under spec-root (invalid parent relationship)
            "task-orphan": {
                "id": "task-orphan",
                "type": "task",
                "title": "Orphan Task",
                "status": "pending",
                "parent": "spec-root",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "dependencies": {
                    "blocked_by": [],
                    "depends": [],
                    "blocks": []
                },
                "metadata": {}
            },
            "task-1-1": {
                "id": "task-1-1",
                "type": "task",
                "title": "Do something",
                "status": "pending",
                "parent": "phase-A",
                "children": [],
                "total_tasks": 1,
                "completed_tasks": 0,
                "dependencies": {
                    "blocked_by": [],
                    "depends": [],
                    "blocks": []
                },
                "metadata": {
                    "file_path": "src/test.py"
                }
            }
        }
    )
    return create_temp_spec_file(spec_data, "invalid-phases-spec.json")


# =============================================================================
# AI Config Isolation Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def mock_ai_config_enabled_tools(request, monkeypatch):
    """
    Mock AI config to return all available tools as enabled.

    This prevents tests from being affected by the user's .claude/ai_config.yaml
    settings, ensuring tests are isolated and reproducible.

    Skips mocking for tests in test_ai_config_models.py and test_ai_config_setup.py
    which specifically test ai_config behavior.
    """
    # Skip mocking for tests that are specifically testing ai_config behavior
    test_module = request.node.fspath.basename
    if test_module in ["test_ai_config_models.py", "test_ai_config_setup.py"]:
        return

    def mock_get_enabled_tools(skill_name: str):
        """Return all available tools as enabled, ignoring user config."""
        # Use detect_available_tools directly to avoid circular dependency
        # (get_available_tools() internally calls get_enabled_and_available_tools,
        # which calls ai_config.get_enabled_tools(), creating infinite recursion)
        from claude_skills.common.ai_tools import detect_available_tools
        # Return a reasonable set of common tools
        available = detect_available_tools(["gemini", "cursor-agent", "codex", "claude"])
        # Return a dict mapping tool names to minimal config dicts
        return {tool: {"enabled": True, "command": tool} for tool in available}

    monkeypatch.setattr(
        "claude_skills.common.ai_config.get_enabled_tools",
        mock_get_enabled_tools
    )
