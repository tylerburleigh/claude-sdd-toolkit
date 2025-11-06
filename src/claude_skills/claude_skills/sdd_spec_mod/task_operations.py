"""
Task operations for SDD specifications.

Provides functions for adding, removing, and moving tasks in the spec hierarchy.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone


def add_task(
    spec_data: Dict[str, Any],
    parent_id: str,
    title: str,
    description: Optional[str] = None,
    position: Optional[int] = None,
    task_type: str = "task",
    estimated_hours: Optional[float] = None
) -> Dict[str, Any]:
    """
    Add a new task to the spec hierarchy.

    Args:
        spec_data: The full spec data dictionary (modified in-place)
        parent_id: Parent node ID (e.g., "phase-1", "task-1")
        title: Task title
        description: Optional task description
        position: Optional position index (0-based, appends if None)
        task_type: Task type ("task", "subtask", "verify")
        estimated_hours: Optional time estimate

    Returns:
        Dict with success status and details:
        {
            "success": True,
            "task_id": "task-3-5",
            "message": "Added task: <title>",
            "parent_id": "phase-3"
        }

    Raises:
        ValueError: If spec data is invalid, parent not found, or invalid values
    """
    # Validate spec structure
    if not isinstance(spec_data, dict):
        raise ValueError("spec_data must be a dictionary")

    if "hierarchy" not in spec_data:
        raise ValueError("spec_data must have 'hierarchy' key")

    if not isinstance(spec_data["hierarchy"], dict):
        raise ValueError("hierarchy must be a dictionary")

    # Validate inputs
    if not title or not title.strip():
        raise ValueError("title cannot be empty")

    # Find parent in hierarchy
    hierarchy = spec_data["hierarchy"]
    if parent_id not in hierarchy:
        raise ValueError(f"Parent '{parent_id}' not found in spec hierarchy")

    parent_node = hierarchy[parent_id]

    # Validate parent can have children
    parent_type = parent_node.get("type", "")
    if parent_type not in ["phase", "task", "group"]:
        raise ValueError(f"Cannot add child to node type '{parent_type}'. Parent must be phase, task, or group.")

    # Generate task ID based on parent structure
    task_id = _generate_task_id(hierarchy, parent_id, parent_node)

    # Initialize children list if needed
    if "children" not in parent_node:
        parent_node["children"] = []

    # Create task node
    task_node = {
        "type": task_type,
        "title": title.strip(),
        "status": "pending",
        "parent": parent_id,
        "children": [],
        "dependencies": {
            "blocks": [],
            "blocked_by": [],
            "depends": []
        },
        "total_tasks": 1,
        "completed_tasks": 0,
        "metadata": {}
    }

    # Add optional fields
    if description:
        task_node["description"] = description.strip()

    if estimated_hours is not None:
        if estimated_hours < 0:
            raise ValueError(f"estimated_hours must be non-negative, got {estimated_hours}")
        task_node["metadata"]["estimated_hours"] = float(estimated_hours)

    # Add task to hierarchy
    hierarchy[task_id] = task_node

    # Add task ID to parent's children list at specified position
    if position is not None:
        if position < 0 or position > len(parent_node["children"]):
            raise ValueError(f"position {position} out of range (0-{len(parent_node['children'])})")
        parent_node["children"].insert(position, task_id)
    else:
        parent_node["children"].append(task_id)

    # Update parent task counts
    _propagate_task_count_increase(hierarchy, parent_id)

    return {
        "success": True,
        "task_id": task_id,
        "task_title": title.strip(),
        "parent_id": parent_id,
        "message": f"Added {task_type}: {title.strip()}"
    }


def _generate_task_id(hierarchy: Dict[str, Any], parent_id: str, parent_node: Dict[str, Any]) -> str:
    """
    Generate a unique task ID based on parent structure.

    For phase parents: task-1-1, task-1-2, etc.
    For task parents: task-1-1-1, task-1-1-2, etc. (subtasks)
    For group parents: Similar nesting

    Args:
        hierarchy: Spec hierarchy
        parent_id: Parent node ID
        parent_node: Parent node data

    Returns:
        Generated task ID
    """
    # Count existing children to determine next number
    existing_children = parent_node.get("children", [])
    next_index = len(existing_children) + 1

    # Extract parent prefix
    if parent_id.startswith("phase-"):
        # Direct child of phase: task-{phase_num}-{child_num}
        phase_num = parent_id.split("-")[1]
        return f"task-{phase_num}-{next_index}"
    elif parent_id.startswith("task-"):
        # Subtask: extend parent ID with another level
        return f"{parent_id}-{next_index}"
    elif parent_id.startswith("verify-"):
        # Child of verify node - use similar pattern
        return f"{parent_id}-{next_index}"
    else:
        # Fallback: append to parent ID
        return f"{parent_id}-{next_index}"


def _propagate_task_count_increase(hierarchy: Dict[str, Any], node_id: str, increase: int = 1):
    """
    Propagate task count increase up the hierarchy.

    Args:
        hierarchy: Spec hierarchy
        node_id: Starting node ID
        increase: Amount to increase (default: 1)
    """
    if node_id not in hierarchy:
        return

    node = hierarchy[node_id]

    # Increase total_tasks for this node
    node["total_tasks"] = node.get("total_tasks", 0) + increase

    # Propagate to parent
    parent_id = node.get("parent")
    if parent_id:
        _propagate_task_count_increase(hierarchy, parent_id, increase)


def remove_task(
    spec_data: Dict[str, Any],
    task_id: str,
    cascade: bool = False
) -> Dict[str, Any]:
    """
    Remove a task from the spec hierarchy.

    Args:
        spec_data: The full spec data dictionary (modified in-place)
        task_id: Task ID to remove
        cascade: If True, also remove all child tasks recursively

    Returns:
        Dict with success status and details:
        {
            "success": True,
            "task_id": "task-3-5",
            "message": "Removed task: <title>",
            "removed_count": 1
        }

    Raises:
        ValueError: If spec data is invalid, task not found, or has children without cascade
    """
    # Validate spec structure
    if not isinstance(spec_data, dict):
        raise ValueError("spec_data must be a dictionary")

    if "hierarchy" not in spec_data:
        raise ValueError("spec_data must have 'hierarchy' key")

    hierarchy = spec_data["hierarchy"]

    # Find task in hierarchy
    if task_id not in hierarchy:
        raise ValueError(f"Task '{task_id}' not found in spec hierarchy")

    task_node = hierarchy[task_id]
    task_title = task_node.get("title", "Untitled")

    # Check for children
    children = task_node.get("children", [])
    if children and not cascade:
        raise ValueError(
            f"Task '{task_id}' has {len(children)} child task(s). "
            f"Use --cascade to remove task and all children, or remove children first."
        )

    # Remove children recursively if cascade=True
    removed_count = 0
    if cascade and children:
        for child_id in list(children):  # Copy list to avoid modification during iteration
            result = remove_task(spec_data, child_id, cascade=True)
            removed_count += result["removed_count"]

    # Remove task from parent's children list
    parent_id = task_node.get("parent")
    if parent_id and parent_id in hierarchy:
        parent_node = hierarchy[parent_id]
        parent_children = parent_node.get("children", [])
        if task_id in parent_children:
            parent_children.remove(task_id)

    # Get task count before removal (for propagation)
    task_total = task_node.get("total_tasks", 1)

    # Remove task from hierarchy
    del hierarchy[task_id]
    removed_count += 1

    # Propagate task count decrease up the hierarchy
    if parent_id:
        _propagate_task_count_decrease(hierarchy, parent_id, task_total)

    return {
        "success": True,
        "task_id": task_id,
        "task_title": task_title,
        "message": f"Removed task: {task_title}",
        "removed_count": removed_count
    }


def _propagate_task_count_decrease(hierarchy: Dict[str, Any], node_id: str, decrease: int = 1):
    """
    Propagate task count decrease up the hierarchy.

    Args:
        hierarchy: Spec hierarchy
        node_id: Starting node ID
        decrease: Amount to decrease (default: 1)
    """
    if node_id not in hierarchy:
        return

    node = hierarchy[node_id]

    # Decrease total_tasks for this node
    current_total = node.get("total_tasks", 0)
    node["total_tasks"] = max(0, current_total - decrease)

    # Also decrease completed_tasks proportionally if needed
    current_completed = node.get("completed_tasks", 0)
    if current_completed > node["total_tasks"]:
        node["completed_tasks"] = node["total_tasks"]

    # Propagate to parent
    parent_id = node.get("parent")
    if parent_id:
        _propagate_task_count_decrease(hierarchy, parent_id, decrease)
