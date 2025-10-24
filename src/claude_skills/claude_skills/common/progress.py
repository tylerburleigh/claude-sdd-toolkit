"""
Progress calculation utilities for SDD JSON specs.
Provides hierarchical progress recalculation and status updates.
"""

from typing import Dict, List


def recalculate_progress(spec_data: Dict, node_id: str = "spec-root") -> Dict:
    """
    Recursively recalculate progress for a node and all its parents.

    Modifies spec_data in-place by updating completed_tasks, total_tasks,
    and status fields for the node and all ancestors.

    Args:
        spec_data: JSON spec file data dictionary
        node_id: Node to start recalculation from (default: spec-root)

    Returns:
        The modified spec_data dictionary (for convenience/chaining)
    """
    if not spec_data:
        return {}

    hierarchy = spec_data.get("hierarchy", {})

    if node_id not in hierarchy:
        return spec_data

    node = hierarchy[node_id]
    children = node.get("children", [])

    if not children:
        # Leaf node - set based on own status
        node["completed_tasks"] = 1 if node.get("status") == "completed" else 0
        node["total_tasks"] = 1
    else:
        # Non-leaf node - recursively calculate from children
        total_completed = 0
        total_tasks = 0

        for child_id in children:
            # Recursively recalculate child first
            recalculate_progress(spec_data, child_id)

            child = hierarchy.get(child_id, {})
            total_completed += child.get("completed_tasks", 0)
            total_tasks += child.get("total_tasks", 0)

        node["completed_tasks"] = total_completed
        node["total_tasks"] = total_tasks

    # Update node status based on progress
    update_node_status(node, hierarchy)

    return spec_data


def update_node_status(node: Dict, hierarchy: Dict = None) -> None:
    """
    Update a node's status based on its children's progress.

    Modifies node in-place. Does not affect manually set statuses
    for leaf nodes (tasks).

    Args:
        node: Node dictionary from hierarchy
        hierarchy: Full hierarchy dictionary (needed to check child statuses)
    """
    # Don't auto-update status for leaf tasks (they're set manually)
    if node.get("type") == "task" and not node.get("children"):
        return

    # Track if node is blocked (we'll skip status changes but allow parent updates)
    is_blocked = node.get("status") == "blocked"

    # Handle manually-completed tasks with children
    if node.get("metadata", {}).get("completed_at") and node.get("children"):
        node["status"] = "completed"
        # Update children's completion counts if needed
        if node.get("children"):
            # Mark all children as completed to maintain consistency
            # This happens when a parent is manually marked complete
            # but children weren't individually marked
            total = node.get("total_tasks", 0)
            node["completed_tasks"] = total
        # Don't return early - allow parent chain to update

    # If blocked, don't change status but continue to allow count updates
    if is_blocked:
        return

    # Check if any children are in_progress (takes priority over count-based logic)
    if hierarchy and node.get("children"):
        for child_id in node.get("children", []):
            child = hierarchy.get(child_id, {})
            if child.get("status") == "in_progress":
                node["status"] = "in_progress"
                return

    completed = node.get("completed_tasks", 0)
    total = node.get("total_tasks", 0)

    if total == 0:
        node["status"] = "pending"
    elif completed == 0:
        node["status"] = "pending"
    elif completed == total:
        node["status"] = "completed"
    else:
        node["status"] = "in_progress"


def update_parent_status(spec_data: Dict, node_id: str) -> Dict:
    """
    Update status and progress for a node's parent chain.

    Use this after updating a task status to propagate changes up the hierarchy.

    Args:
        spec_data: JSON spec file data dictionary
        node_id: Node whose parents should be updated

    Returns:
        The modified spec_data dictionary (for convenience/chaining)
    """
    if not spec_data:
        return {}

    hierarchy = spec_data.get("hierarchy", {})

    if node_id not in hierarchy:
        return spec_data

    node = hierarchy[node_id]
    parent_id = node.get("parent")

    # Walk up the parent chain
    while parent_id and parent_id in hierarchy:
        # Recalculate progress for parent
        recalculate_progress(spec_data, parent_id)

        # Move to next parent
        parent = hierarchy[parent_id]
        parent_id = parent.get("parent")

    return spec_data


def get_progress_summary(spec_data: Dict, node_id: str = "spec-root") -> Dict:
    """
    Get progress summary for a node.

    Args:
        spec_data: JSON spec file data
        node_id: Node to get progress for (default: spec-root)

    Returns:
        Dictionary with progress information
    """
    if not spec_data:
        return {"error": "No state data provided"}

    # Recalculate progress to ensure counts are up-to-date
    recalculate_progress(spec_data, node_id)

    hierarchy = spec_data.get("hierarchy", {})
    node = hierarchy.get(node_id)

    if not node:
        return {"error": f"Node {node_id} not found"}

    total = node.get("total_tasks", 0)
    completed = node.get("completed_tasks", 0)
    percentage = int((completed / total * 100)) if total > 0 else 0

    # Extract spec_id from spec_data
    spec_id = spec_data.get("spec_id", "")

    # Find current phase (first in_progress, or first pending if none)
    current_phase = None
    for key, value in hierarchy.items():
        if value.get("type") == "phase":
            if value.get("status") == "in_progress":
                current_phase = {
                    "id": key,
                    "title": value.get("title", ""),
                    "completed": value.get("completed_tasks", 0),
                    "total": value.get("total_tasks", 0)
                }
                break
            elif current_phase is None and value.get("status") == "pending":
                current_phase = {
                    "id": key,
                    "title": value.get("title", ""),
                    "completed": value.get("completed_tasks", 0),
                    "total": value.get("total_tasks", 0)
                }

    return {
        "node_id": node_id,
        "spec_id": spec_id,
        "title": node.get("title", ""),
        "type": node.get("type", ""),
        "status": node.get("status", ""),
        "total_tasks": total,
        "completed_tasks": completed,
        "percentage": percentage,
        "remaining_tasks": total - completed,
        "current_phase": current_phase
    }


def list_phases(spec_data: Dict) -> List[Dict]:
    """
    List all phases with their status and progress.

    Args:
        spec_data: JSON spec file data

    Returns:
        List of phase dictionaries
    """
    if not spec_data:
        return []

    hierarchy = spec_data.get("hierarchy", {})

    phases = []
    for key, value in hierarchy.items():
        if value.get("type") == "phase":
            total = value.get("total_tasks", 0)
            completed = value.get("completed_tasks", 0)
            percentage = int((completed / total * 100)) if total > 0 else 0

            phases.append({
                "id": key,
                "title": value.get("title", ""),
                "status": value.get("status", ""),
                "completed_tasks": completed,
                "total_tasks": total,
                "percentage": percentage
            })

    # Sort by phase ID (phase-1, phase-2, etc.)
    phases.sort(key=lambda p: p["id"])

    return phases


def get_task_counts_by_status(spec_data: Dict) -> Dict[str, int]:
    """
    Count tasks by their status.

    Args:
        spec_data: JSON spec file data

    Returns:
        Dictionary mapping status to count
    """
    if not spec_data:
        return {"pending": 0, "in_progress": 0, "completed": 0, "blocked": 0}

    hierarchy = spec_data.get("hierarchy", {})

    counts = {
        "pending": 0,
        "in_progress": 0,
        "completed": 0,
        "blocked": 0
    }

    for node in hierarchy.values():
        if node.get("type") == "task":
            status = node.get("status", "pending")
            if status in counts:
                counts[status] += 1

    return counts
