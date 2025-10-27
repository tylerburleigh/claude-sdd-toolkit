"""
Task discovery and analysis operations for SDD workflows.
"""

from pathlib import Path
from typing import Optional, Dict, Tuple

# Clean imports
from claude_skills.common import load_json_spec, get_node
from claude_skills.common import (
    validate_spec_before_proceed,
    get_task_context_from_docs,
    check_doc_query_available,
)


def is_unblocked(spec_data: Dict, task_id: str, task_data: Dict) -> bool:
    """
    Check if all blocking dependencies are completed.

    This checks both task-level dependencies and phase-level dependencies.
    A task is blocked if:
    1. Any of its direct task dependencies are not completed, OR
    2. Its parent phase is blocked by an incomplete phase

    Args:
        spec_data: JSON spec file data
        task_id: Task identifier
        task_data: Task data dictionary

    Returns:
        True if task has no blockers or all blockers are completed
    """
    hierarchy = spec_data.get("hierarchy", {})

    # Check task-level dependencies
    blocked_by = task_data.get("dependencies", {}).get("blocked_by", [])
    for blocker_id in blocked_by:
        blocker = hierarchy.get(blocker_id)
        if not blocker or blocker.get("status") != "completed":
            return False

    # Check phase-level dependencies
    # Walk up to find the parent phase
    parent_phase_id = None
    current = task_data
    while current:
        parent_id = current.get("parent")
        if not parent_id:
            break
        parent = hierarchy.get(parent_id)
        if not parent:
            break
        if parent.get("type") == "phase":
            parent_phase_id = parent_id
            break
        current = parent

    # If task belongs to a phase, check if that phase is blocked
    if parent_phase_id:
        parent_phase = hierarchy.get(parent_phase_id)
        if parent_phase:
            phase_blocked_by = parent_phase.get("dependencies", {}).get("blocked_by", [])
            for blocker_id in phase_blocked_by:
                blocker = hierarchy.get(blocker_id)
                if not blocker or blocker.get("status") != "completed":
                    return False

    return True


def is_in_current_phase(spec_data: Dict, task_id: str, phase_id: str) -> bool:
    """
    Check if task belongs to current phase (including nested groups).

    Args:
        spec_data: JSON spec file data
        task_id: Task identifier
        phase_id: Phase identifier to check against

    Returns:
        True if task is within the phase hierarchy
    """
    hierarchy = spec_data.get("hierarchy", {})
    task = hierarchy.get(task_id)
    if not task:
        return False

    # Walk up parent chain to find phase
    current = task
    while current:
        parent_id = current.get("parent")
        if parent_id == phase_id:
            return True
        if not parent_id:
            return False
        current = hierarchy.get(parent_id)
    return False


def get_next_task(spec_data: Dict) -> Optional[Tuple[str, Dict]]:
    """
    Find the next actionable task.

    Args:
        spec_data: JSON spec file data

    Returns:
        Tuple of (task_id, task_data) or None if no task available
    """
    hierarchy = spec_data.get("hierarchy", {})

    # Get all phases in order
    spec_root = hierarchy.get("spec-root", {})
    phase_order = spec_root.get("children", [])

    # Build list of phases to check: in_progress first, then pending
    phases_to_check = []

    # First, add any in_progress phases
    for phase_id in phase_order:
        phase = hierarchy.get(phase_id, {})
        if phase.get("type") == "phase" and phase.get("status") == "in_progress":
            phases_to_check.append(phase_id)

    # Then add pending phases
    for phase_id in phase_order:
        phase = hierarchy.get(phase_id, {})
        if phase.get("type") == "phase" and phase.get("status") == "pending":
            phases_to_check.append(phase_id)

    if not phases_to_check:
        return None

    # Try each phase until we find actionable tasks
    for current_phase in phases_to_check:
        # Find first available task or subtask in current phase
        # Prefer leaf tasks (no children) over parent tasks
        candidates = []
        for key, value in hierarchy.items():
            if (value.get("type") in ["task", "subtask"] and
                value.get("status") == "pending" and
                is_unblocked(spec_data, key, value) and
                is_in_current_phase(spec_data, key, current_phase)):
                has_children = len(value.get("children", [])) > 0
                candidates.append((key, value, has_children))

        if candidates:
            # Sort: leaf tasks first (has_children=False), then by ID
            candidates.sort(key=lambda x: (x[2], x[0]))
            return (candidates[0][0], candidates[0][1])

    # No actionable tasks found in any phase
    return None


def get_task_info(spec_data: Dict, task_id: str) -> Optional[Dict]:
    """
    Get detailed information about a task.

    Args:
        spec_data: JSON spec file data
        task_id: Task identifier

    Returns:
        Task data dictionary or None
    """
    return get_node(spec_data, task_id)


def check_dependencies(spec_data: Dict, task_id: str) -> Dict:
    """
    Check dependency status for a task.

    Args:
        spec_data: JSON spec file data
        task_id: Task identifier

    Returns:
        Dictionary with dependency analysis
    """
    hierarchy = spec_data.get("hierarchy", {})
    task = hierarchy.get(task_id)

    if not task:
        return {"error": f"Task {task_id} not found"}

    deps = task.get("dependencies", {})
    blocked_by = deps.get("blocked_by", [])
    depends = deps.get("depends", [])
    blocks = deps.get("blocks", [])

    result = {
        "task_id": task_id,
        "can_start": is_unblocked(spec_data, task_id, task),
        "blocked_by": [],
        "soft_depends": [],
        "blocks": []
    }

    # Get info for blocking tasks
    for dep_id in blocked_by:
        dep_task = hierarchy.get(dep_id)
        if dep_task:
            result["blocked_by"].append({
                "id": dep_id,
                "title": dep_task.get("title", ""),
                "status": dep_task.get("status", ""),
                "file": dep_task.get("metadata", {}).get("file_path", "")
            })

    # Get info for soft dependencies
    for dep_id in depends:
        dep_task = hierarchy.get(dep_id)
        if dep_task:
            result["soft_depends"].append({
                "id": dep_id,
                "title": dep_task.get("title", ""),
                "status": dep_task.get("status", ""),
                "file": dep_task.get("metadata", {}).get("file_path", "")
            })

    # Get info for tasks this blocks
    for dep_id in blocks:
        dep_task = hierarchy.get(dep_id)
        if dep_task:
            result["blocks"].append({
                "id": dep_id,
                "title": dep_task.get("title", ""),
                "status": dep_task.get("status", ""),
                "file": dep_task.get("metadata", {}).get("file_path", "")
            })

    return result


def prepare_task(spec_id: str, specs_dir: Path, task_id: Optional[str] = None) -> Dict:
    """
    Prepare complete context for task implementation.

    Combines task discovery, dependency checking, and detail extraction.
    Now includes automatic spec validation and doc-query context gathering.

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs/active directory
        task_id: Optional task ID (auto-discovers if not provided)

    Returns:
        Complete task preparation data with validation and context
    """
    result = {
        "success": False,
        "task_id": task_id,
        "task_data": None,
        "task_details": None,
        "dependencies": None,
        "spec_file": None,
        "doc_context": None,
        "validation_warnings": [],
        "error": None
    }

    # Phase 1: Validate spec before proceeding (Priority 1 Integration)
    spec_path = specs_dir / "active" / f"{spec_id}.json"
    validation_result = validate_spec_before_proceed(str(spec_path), quiet=True)

    if not validation_result["valid"]:
        # Spec has critical errors - suggest fixing before proceeding
        error_summary = f"Spec validation failed with {len(validation_result['errors'])} error(s)"
        if validation_result["can_autofix"]:
            error_summary += f"\n\nSuggested fix: {validation_result['autofix_command']}"
        else:
            error_summary += "\n\nErrors:\n" + "\n".join([
                f"  - {err['message']}" for err in validation_result['errors'][:3]
            ])
        result["error"] = error_summary
        return result

    # Store any warnings for reporting (non-blocking)
    if validation_result["warnings"]:
        result["validation_warnings"] = [w["message"] for w in validation_result["warnings"]]

    # Load state
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        result["error"] = "Failed to load JSON spec"
        return result

    # Get task ID if not provided
    if not task_id:
        next_task = get_next_task(spec_data)
        if not next_task:
            result["error"] = "No actionable tasks found"
            return result
        task_id, _ = next_task
        result["task_id"] = task_id

    # Get task info from state
    task_data = get_task_info(spec_data, task_id)
    if not task_data:
        result["error"] = f"Task {task_id} not found in state"
        return result

    result["task_data"] = task_data

    # Check dependencies
    deps = check_dependencies(spec_data, task_id)
    result["dependencies"] = deps

    # Phase 3: Context gathering from doc-query (Priority 1 Integration)
    # Automatically gather codebase context if documentation is available
    doc_check = check_doc_query_available()
    if doc_check["available"]:
        # Extract task description for context gathering
        task_title = task_data.get("title", "")
        task_description = task_data.get("description", task_title)

        # Get context from documentation
        doc_context = get_task_context_from_docs(task_description)
        if doc_context:
            result["doc_context"] = doc_context

            # Add helpful message
            if doc_context.get("files"):
                result["doc_context"]["message"] = (
                    f"Found {len(doc_context['files'])} relevant files from codebase documentation"
                )

    # Note: All task details are already in task_data from the JSON spec
    # The spec_file and task_details fields are kept for backwards compatibility
    # but remain None as specs are now JSON format, not markdown

    result["success"] = True
    return result
