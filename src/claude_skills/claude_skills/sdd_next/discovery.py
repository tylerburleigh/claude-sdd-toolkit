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


def get_next_task(spec_data: Dict) -> Optional[Tuple[str, Dict]]:
    """
    Find the next actionable task.

    Args:
        spec_data: JSON spec file data

    Returns:
        Tuple of (task_id, task_data) or None if no task available
    """
    hierarchy = spec_data.get("hierarchy", {})

    # Find current in_progress phase, or first pending phase
    current_phase = None
    for key, value in hierarchy.items():
        if value.get("type") == "phase" and value.get("status") == "in_progress":
            current_phase = key
            break

    if not current_phase:
        # No in_progress phase, find first pending
        for key, value in hierarchy.items():
            if value.get("type") == "phase" and value.get("status") == "pending":
                current_phase = key
                break

    if not current_phase:
        return None

    # Find first available task in current phase
    for key, value in hierarchy.items():
        if (value.get("type") == "task" and
            value.get("status") == "pending" and
            len(value.get("dependencies", {}).get("blocked_by", [])) == 0 and
            value.get("parent", "").startswith(current_phase)):
            return (key, value)

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
        "can_start": len(blocked_by) == 0,
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
