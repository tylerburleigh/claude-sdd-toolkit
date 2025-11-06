"""
Core spec modification operations.

Provides functions for adding, removing, and moving nodes in SDD specification hierarchies.
"""

import sys
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from claude_skills.common.spec import get_node, update_node


def add_node(
    spec_data: Dict[str, Any],
    parent_id: str,
    node_data: Dict[str, Any],
    position: Optional[int] = None
) -> Dict[str, Any]:
    """
    Add a new task/subtask/phase to the spec hierarchy at a specified position.

    This function creates a new node in the specification hierarchy, ensuring that
    all required fields are present and that the hierarchy remains valid.

    Args:
        spec_data: The full spec data dictionary (must include 'hierarchy' key)
        parent_id: ID of the parent node to add the child to
        node_data: Dictionary containing the new node's data. Must include:
            - node_id: Unique identifier for the new node
            - type: Node type (phase, task, subtask, verify, group)
            - title: Human-readable title
            Optional fields:
            - description: Detailed description
            - status: Node status (default: 'pending')
            - metadata: Additional metadata dict
            - dependencies: Dependencies dict with blocks/blocked_by/depends
        position: Optional position in parent's children list (0-indexed).
                 If None, appends to end. If negative, counts from end.

    Returns:
        Dict with success status and message:
        {
            "success": True|False,
            "message": "Description of result",
            "node_id": "ID of created node" (only if success=True)
        }

    Raises:
        ValueError: If required fields are missing or invalid
        KeyError: If parent_id doesn't exist in hierarchy
    """
    # Validate spec_data structure
    if not isinstance(spec_data, dict):
        raise ValueError("spec_data must be a dictionary")

    if "hierarchy" not in spec_data:
        raise ValueError("spec_data must contain 'hierarchy' key")

    hierarchy = spec_data["hierarchy"]
    if not isinstance(hierarchy, dict):
        raise ValueError("spec_data['hierarchy'] must be a dictionary")

    # Validate node_data required fields
    if not isinstance(node_data, dict):
        raise ValueError("node_data must be a dictionary")

    required_fields = ["node_id", "type", "title"]
    missing_fields = [f for f in required_fields if f not in node_data]
    if missing_fields:
        raise ValueError(f"node_data missing required fields: {', '.join(missing_fields)}")

    node_id = node_data["node_id"]
    node_type = node_data["type"]
    title = node_data["title"]

    # Validate node_id uniqueness
    if node_id in hierarchy:
        return {
            "success": False,
            "message": f"Node ID '{node_id}' already exists in hierarchy"
        }

    # Validate node type
    valid_types = ["phase", "task", "subtask", "verify", "group", "spec"]
    if node_type not in valid_types:
        return {
            "success": False,
            "message": f"Invalid node type '{node_type}'. Must be one of: {', '.join(valid_types)}"
        }

    # Validate title is not empty
    if not title or not title.strip():
        return {
            "success": False,
            "message": "Node title cannot be empty"
        }

    # Validate parent exists
    parent_node = get_node(spec_data, parent_id)
    if parent_node is None:
        raise KeyError(f"Parent node '{parent_id}' not found in hierarchy")

    # Create the new node with required structure
    new_node = {
        "type": node_type,
        "title": title.strip(),
        "description": node_data.get("description", ""),
        "status": node_data.get("status", "pending"),
        "parent": parent_id,
        "children": [],
        "total_tasks": 0,
        "completed_tasks": 0,
        "metadata": node_data.get("metadata", {}),
    }

    # Add dependencies if provided, otherwise create empty structure
    if "dependencies" in node_data:
        new_node["dependencies"] = node_data["dependencies"]
    else:
        new_node["dependencies"] = {
            "blocks": [],
            "blocked_by": [],
            "depends": []
        }

    # Validate dependencies structure
    deps = new_node["dependencies"]
    if not isinstance(deps, dict):
        return {
            "success": False,
            "message": "dependencies must be a dictionary"
        }

    for dep_key in ["blocks", "blocked_by", "depends"]:
        if dep_key not in deps:
            deps[dep_key] = []
        if not isinstance(deps[dep_key], list):
            return {
                "success": False,
                "message": f"dependencies['{dep_key}'] must be a list"
            }

    # Set total_tasks for leaf nodes (non-container types)
    leaf_types = ["task", "subtask", "verify"]
    if node_type in leaf_types:
        new_node["total_tasks"] = 1
        # Note: completed_tasks stays 0 until task is completed

    # Add node to hierarchy
    hierarchy[node_id] = new_node

    # Update parent's children list
    parent_children = parent_node.get("children", [])
    if not isinstance(parent_children, list):
        parent_children = []
        parent_node["children"] = parent_children

    # Insert at specified position
    if position is None:
        # Append to end
        parent_children.append(node_id)
    else:
        # Insert at specified position (handles negative indices)
        try:
            parent_children.insert(position, node_id)
        except (IndexError, TypeError) as e:
            # Roll back the node addition
            del hierarchy[node_id]
            return {
                "success": False,
                "message": f"Invalid position {position}: {str(e)}"
            }

    # Update parent node's task counts (propagate upward)
    if node_type in leaf_types:
        _propagate_task_count_increase(spec_data, parent_id, total_increase=1)

    return {
        "success": True,
        "message": f"Successfully added node '{node_id}' as child of '{parent_id}'",
        "node_id": node_id
    }


def _propagate_task_count_increase(
    spec_data: Dict[str, Any],
    node_id: str,
    total_increase: int = 0,
    completed_increase: int = 0
) -> None:
    """
    Propagate task count increases up the hierarchy tree.

    This is called when a new leaf task is added or a task is completed.
    It updates total_tasks and/or completed_tasks for all ancestors.

    Args:
        spec_data: The full spec data dictionary
        node_id: Starting node ID (typically the parent of the added/completed task)
        total_increase: Amount to increase total_tasks by (default: 0)
        completed_increase: Amount to increase completed_tasks by (default: 0)
    """
    hierarchy = spec_data.get("hierarchy", {})

    current_id = node_id
    while current_id and current_id != "spec-root":
        node = hierarchy.get(current_id)
        if node is None:
            # Reached end of chain or invalid parent reference
            break

        # Update counts
        if total_increase > 0:
            node["total_tasks"] = node.get("total_tasks", 0) + total_increase
        if completed_increase > 0:
            node["completed_tasks"] = node.get("completed_tasks", 0) + completed_increase

        # Move to parent
        current_id = node.get("parent")

    # Update spec-root if it exists
    if "spec-root" in hierarchy:
        spec_root = hierarchy["spec-root"]
        if total_increase > 0:
            spec_root["total_tasks"] = spec_root.get("total_tasks", 0) + total_increase
        if completed_increase > 0:
            spec_root["completed_tasks"] = spec_root.get("completed_tasks", 0) + completed_increase


def remove_node(
    spec_data: Dict[str, Any],
    node_id: str,
    recursive: bool = False
) -> Dict[str, Any]:
    """
    Remove a node from the spec hierarchy.

    Args:
        spec_data: The full spec data dictionary
        node_id: ID of the node to remove
        recursive: If True, removes all descendants as well (default: False)

    Returns:
        Dict with success status and message
    """
    # Placeholder implementation
    return {
        "success": False,
        "message": "remove_node not yet implemented"
    }


def move_node(
    spec_data: Dict[str, Any],
    node_id: str,
    new_parent_id: str,
    position: Optional[int] = None
) -> Dict[str, Any]:
    """
    Move a node to a different parent in the hierarchy.

    Args:
        spec_data: The full spec data dictionary
        node_id: ID of the node to move
        new_parent_id: ID of the new parent node
        position: Optional position in new parent's children list

    Returns:
        Dict with success status and message
    """
    # Placeholder implementation
    return {
        "success": False,
        "message": "move_node not yet implemented"
    }


def update_task_counts(spec_data: Dict[str, Any], node_id: str) -> Dict[str, Any]:
    """
    Recalculate and update task counts for a node and its ancestors.

    This function recursively calculates total_tasks and completed_tasks
    for a node based on its descendants, then propagates the counts upward.

    Args:
        spec_data: The full spec data dictionary
        node_id: ID of the node to recalculate (typically after modifications)

    Returns:
        Dict with success status and updated counts
    """
    # Placeholder implementation
    return {
        "success": False,
        "message": "update_task_counts not yet implemented"
    }
