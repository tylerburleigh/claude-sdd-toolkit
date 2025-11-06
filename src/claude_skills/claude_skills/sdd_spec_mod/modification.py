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
    cascade: bool = False
) -> Dict[str, Any]:
    """
    Remove a node from the spec hierarchy.

    This function removes a node and optionally its descendants (cascade mode).
    It also updates parent-child relationships, cleans up dependencies, and
    propagates task count decreases up the hierarchy.

    Args:
        spec_data: The full spec data dictionary
        node_id: ID of the node to remove
        cascade: If True, recursively removes all descendants (default: False)
                If False and node has children, operation fails

    Returns:
        Dict with success status and message:
        {
            "success": True|False,
            "message": "Description of result",
            "removed_nodes": [...] (only if success=True)
        }

    Raises:
        KeyError: If node_id doesn't exist in hierarchy
        ValueError: If trying to remove spec-root
    """
    # Validate spec_data structure
    if not isinstance(spec_data, dict):
        raise ValueError("spec_data must be a dictionary")

    if "hierarchy" not in spec_data:
        raise ValueError("spec_data must contain 'hierarchy' key")

    hierarchy = spec_data["hierarchy"]

    # Prevent removal of spec-root
    if node_id == "spec-root":
        raise ValueError("Cannot remove spec-root node")

    # Check if node exists
    node = get_node(spec_data, node_id)
    if node is None:
        raise KeyError(f"Node '{node_id}' not found in hierarchy")

    # Check if node has children
    children = node.get("children", [])
    if children and not cascade:
        return {
            "success": False,
            "message": f"Node '{node_id}' has {len(children)} children. Use cascade=True to remove node and its descendants."
        }

    # Collect all nodes to remove (node + descendants if cascade)
    nodes_to_remove = []
    if cascade:
        # Recursively collect all descendants
        _collect_descendants(spec_data, node_id, nodes_to_remove)
    else:
        nodes_to_remove = [node_id]

    # Calculate task count decrease for propagation
    # (sum of total_tasks for all leaf nodes being removed)
    leaf_types = ["task", "subtask", "verify"]
    total_decrease = sum(
        hierarchy[nid].get("total_tasks", 0)
        for nid in nodes_to_remove
        if hierarchy.get(nid, {}).get("type") in leaf_types
    )
    completed_decrease = sum(
        hierarchy[nid].get("completed_tasks", 0)
        for nid in nodes_to_remove
        if hierarchy.get(nid, {}).get("type") in leaf_types
    )

    # Remove node from parent's children list
    parent_id = node.get("parent")
    if parent_id and parent_id in hierarchy:
        parent = hierarchy[parent_id]
        parent_children = parent.get("children", [])
        if node_id in parent_children:
            parent_children.remove(node_id)

    # Clean up dependencies referencing the removed nodes
    _cleanup_dependencies(spec_data, nodes_to_remove)

    # Remove all nodes from hierarchy
    for nid in nodes_to_remove:
        if nid in hierarchy:
            del hierarchy[nid]

    # Propagate task count decrease up the hierarchy
    if parent_id and total_decrease > 0:
        _propagate_task_count_decrease(spec_data, parent_id, total_decrease, completed_decrease)

    return {
        "success": True,
        "message": f"Successfully removed {len(nodes_to_remove)} node(s)",
        "removed_nodes": nodes_to_remove
    }


def _collect_descendants(
    spec_data: Dict[str, Any],
    node_id: str,
    result: List[str]
) -> None:
    """
    Recursively collect all descendants of a node.

    Args:
        spec_data: The full spec data dictionary
        node_id: Starting node ID
        result: List to append descendant IDs to (modified in place)
    """
    result.append(node_id)

    hierarchy = spec_data.get("hierarchy", {})
    node = hierarchy.get(node_id)
    if node is None:
        return

    children = node.get("children", [])
    for child_id in children:
        _collect_descendants(spec_data, child_id, result)


def _cleanup_dependencies(
    spec_data: Dict[str, Any],
    removed_nodes: List[str]
) -> None:
    """
    Remove references to removed nodes from all dependency lists.

    Args:
        spec_data: The full spec data dictionary
        removed_nodes: List of node IDs being removed
    """
    hierarchy = spec_data.get("hierarchy", {})
    removed_set = set(removed_nodes)

    for node_id, node in hierarchy.items():
        if node_id in removed_set:
            continue  # Skip nodes being removed

        deps = node.get("dependencies", {})
        if not isinstance(deps, dict):
            continue

        # Clean up blocks, blocked_by, and depends lists
        for dep_key in ["blocks", "blocked_by", "depends"]:
            if dep_key in deps and isinstance(deps[dep_key], list):
                deps[dep_key] = [
                    dep_id for dep_id in deps[dep_key]
                    if dep_id not in removed_set
                ]


def _propagate_task_count_decrease(
    spec_data: Dict[str, Any],
    node_id: str,
    total_decrease: int = 0,
    completed_decrease: int = 0
) -> None:
    """
    Propagate task count decreases up the hierarchy tree.

    This is called when nodes are removed from the hierarchy.
    It updates total_tasks and/or completed_tasks for all ancestors.

    Args:
        spec_data: The full spec data dictionary
        node_id: Starting node ID (typically the parent of removed nodes)
        total_decrease: Amount to decrease total_tasks by (default: 0)
        completed_decrease: Amount to decrease completed_tasks by (default: 0)
    """
    hierarchy = spec_data.get("hierarchy", {})

    current_id = node_id
    while current_id and current_id != "spec-root":
        node = hierarchy.get(current_id)
        if node is None:
            break

        # Update counts (ensure they don't go negative)
        if total_decrease > 0:
            node["total_tasks"] = max(0, node.get("total_tasks", 0) - total_decrease)
        if completed_decrease > 0:
            node["completed_tasks"] = max(0, node.get("completed_tasks", 0) - completed_decrease)

        # Move to parent
        current_id = node.get("parent")

    # Update spec-root if it exists
    if "spec-root" in hierarchy:
        spec_root = hierarchy["spec-root"]
        if total_decrease > 0:
            spec_root["total_tasks"] = max(0, spec_root.get("total_tasks", 0) - total_decrease)
        if completed_decrease > 0:
            spec_root["completed_tasks"] = max(0, spec_root.get("completed_tasks", 0) - completed_decrease)


def update_node_field(
    spec_data: Dict[str, Any],
    node_id: str,
    field: str,
    value: Any
) -> Dict[str, Any]:
    """
    Update a specific field on a node in the spec hierarchy.

    This function provides a safe way to update node fields with validation.
    For metadata updates, it merges with existing metadata rather than replacing it.

    Args:
        spec_data: The full spec data dictionary
        node_id: ID of the node to update
        field: Name of the field to update (e.g., 'title', 'description', 'status', 'metadata')
        value: New value for the field

    Returns:
        Dict with success status and message:
        {
            "success": True|False,
            "message": "Description of result",
            "old_value": previous_value (only if success=True)
        }

    Raises:
        KeyError: If node_id doesn't exist in hierarchy
        ValueError: If attempting to update protected fields
    """
    # Validate spec_data structure
    if not isinstance(spec_data, dict):
        raise ValueError("spec_data must be a dictionary")

    if "hierarchy" not in spec_data:
        raise ValueError("spec_data must contain 'hierarchy' key")

    # Check if node exists
    node = get_node(spec_data, node_id)
    if node is None:
        raise KeyError(f"Node '{node_id}' not found in hierarchy")

    # Protected fields that cannot be updated via this function
    protected_fields = ["parent", "children", "total_tasks", "completed_tasks"]
    if field in protected_fields:
        raise ValueError(
            f"Cannot update protected field '{field}'. "
            f"Use appropriate modification functions instead."
        )

    # Store old value for return
    old_value = node.get(field)

    # Special handling for metadata field (merge instead of replace)
    if field == "metadata":
        if not isinstance(value, dict):
            return {
                "success": False,
                "message": "metadata value must be a dictionary"
            }

        # Use update_node which handles metadata merging
        success = update_node(spec_data, node_id, {"metadata": value})
        if success:
            return {
                "success": True,
                "message": f"Successfully merged metadata for node '{node_id}'",
                "old_value": old_value
            }
        else:
            return {
                "success": False,
                "message": f"Failed to update metadata for node '{node_id}'"
            }

    # Validate status field
    if field == "status":
        valid_statuses = ["pending", "in_progress", "completed", "blocked"]
        if value not in valid_statuses:
            return {
                "success": False,
                "message": f"Invalid status '{value}'. Must be one of: {', '.join(valid_statuses)}"
            }

    # Validate type field
    if field == "type":
        valid_types = ["phase", "task", "subtask", "verify", "group", "spec"]
        if value not in valid_types:
            return {
                "success": False,
                "message": f"Invalid type '{value}'. Must be one of: {', '.join(valid_types)}"
            }

    # Validate title field (cannot be empty)
    if field == "title":
        if not value or (isinstance(value, str) and not value.strip()):
            return {
                "success": False,
                "message": "title cannot be empty"
            }
        # Strip whitespace from title
        value = value.strip() if isinstance(value, str) else value

    # Validate dependencies field
    if field == "dependencies":
        if not isinstance(value, dict):
            return {
                "success": False,
                "message": "dependencies must be a dictionary"
            }

        # Ensure required keys exist
        for dep_key in ["blocks", "blocked_by", "depends"]:
            if dep_key not in value:
                value[dep_key] = []
            if not isinstance(value[dep_key], list):
                return {
                    "success": False,
                    "message": f"dependencies['{dep_key}'] must be a list"
                }

    # Update the field
    node[field] = value

    return {
        "success": True,
        "message": f"Successfully updated field '{field}' for node '{node_id}'",
        "old_value": old_value
    }


def move_node(
    spec_data: Dict[str, Any],
    node_id: str,
    new_parent_id: str,
    position: Optional[int] = None
) -> Dict[str, Any]:
    """
    Move a node to a different parent in the hierarchy.

    This function moves a node (and its descendants) to a new location in the
    hierarchy. It updates parent-child relationships and recalculates task counts
    for all affected ancestors.

    Args:
        spec_data: The full spec data dictionary (must include 'hierarchy' key)
        node_id: ID of the node to move
        new_parent_id: ID of the new parent node
        position: Optional position in new parent's children list (0-indexed).
                 If None, appends to end. If negative, counts from end.

    Returns:
        Dict with success status and message:
        {
            "success": True|False,
            "message": "Description of result",
            "old_parent_id": "Previous parent ID" (only if success=True),
            "new_parent_id": "New parent ID" (only if success=True)
        }

    Raises:
        ValueError: If spec_data is invalid or trying to move spec-root
        KeyError: If node_id or new_parent_id doesn't exist in hierarchy
    """
    # Validate spec_data structure
    if not isinstance(spec_data, dict):
        raise ValueError("spec_data must be a dictionary")

    if "hierarchy" not in spec_data:
        raise ValueError("spec_data must contain 'hierarchy' key")

    hierarchy = spec_data["hierarchy"]
    if not isinstance(hierarchy, dict):
        raise ValueError("spec_data['hierarchy'] must be a dictionary")

    # Prevent moving spec-root
    if node_id == "spec-root":
        raise ValueError("Cannot move spec-root node")

    # Check if node exists
    node = get_node(spec_data, node_id)
    if node is None:
        raise KeyError(f"Node '{node_id}' not found in hierarchy")

    # Check if new parent exists
    new_parent = get_node(spec_data, new_parent_id)
    if new_parent is None:
        raise KeyError(f"New parent node '{new_parent_id}' not found in hierarchy")

    # Get current parent
    old_parent_id = node.get("parent")
    if old_parent_id is None:
        return {
            "success": False,
            "message": f"Node '{node_id}' has no parent (cannot move root node)"
        }

    # Check if already under this parent
    if old_parent_id == new_parent_id:
        # Just reposition within same parent if position is specified
        if position is not None:
            old_parent = hierarchy[old_parent_id]
            parent_children = old_parent.get("children", [])

            # Remove from current position
            if node_id in parent_children:
                parent_children.remove(node_id)

                # Insert at new position
                try:
                    parent_children.insert(position, node_id)
                except (IndexError, TypeError) as e:
                    # Roll back
                    parent_children.append(node_id)
                    return {
                        "success": False,
                        "message": f"Invalid position {position}: {str(e)}"
                    }

            return {
                "success": True,
                "message": f"Successfully repositioned node '{node_id}' within parent '{old_parent_id}'",
                "old_parent_id": old_parent_id,
                "new_parent_id": new_parent_id
            }
        else:
            return {
                "success": False,
                "message": f"Node '{node_id}' is already a child of '{new_parent_id}'"
            }

    # Check for circular dependency (can't move node under itself or its descendants)
    if _is_ancestor(spec_data, node_id, new_parent_id):
        return {
            "success": False,
            "message": f"Cannot move node '{node_id}' under its descendant '{new_parent_id}' (would create circular dependency)"
        }

    # Calculate task counts for the subtree being moved
    # Use the total_tasks/completed_tasks from the root of the moved subtree
    # (it already has the aggregated counts for all its descendants)
    total_tasks_moving = node.get("total_tasks", 0)
    completed_tasks_moving = node.get("completed_tasks", 0)

    # Remove node from old parent's children list
    if old_parent_id in hierarchy:
        old_parent = hierarchy[old_parent_id]
        old_parent_children = old_parent.get("children", [])
        if node_id in old_parent_children:
            old_parent_children.remove(node_id)

    # Add node to new parent's children list
    new_parent_children = new_parent.get("children", [])
    if not isinstance(new_parent_children, list):
        new_parent_children = []
        new_parent["children"] = new_parent_children

    # Insert at specified position
    if position is None:
        # Append to end
        new_parent_children.append(node_id)
    else:
        # Insert at specified position (handles negative indices)
        try:
            new_parent_children.insert(position, node_id)
        except (IndexError, TypeError) as e:
            # Roll back: add back to old parent
            if old_parent_id in hierarchy:
                hierarchy[old_parent_id]["children"].append(node_id)
            return {
                "success": False,
                "message": f"Invalid position {position}: {str(e)}"
            }

    # Update node's parent field
    node["parent"] = new_parent_id

    # Update task counts: decrease old parent lineage, increase new parent lineage
    if total_tasks_moving > 0:
        # Decrease counts in old parent lineage
        if old_parent_id:
            _propagate_task_count_decrease(spec_data, old_parent_id, total_tasks_moving, completed_tasks_moving)

        # Increase counts in new parent lineage
        _propagate_task_count_increase(spec_data, new_parent_id, total_tasks_moving, completed_tasks_moving)

    return {
        "success": True,
        "message": f"Successfully moved node '{node_id}' from '{old_parent_id}' to '{new_parent_id}'",
        "old_parent_id": old_parent_id,
        "new_parent_id": new_parent_id
    }


def _is_ancestor(
    spec_data: Dict[str, Any],
    ancestor_id: str,
    descendant_id: str
) -> bool:
    """
    Check if ancestor_id is an ancestor of descendant_id.

    This is used to prevent circular dependencies when moving nodes.

    Args:
        spec_data: The full spec data dictionary
        ancestor_id: Potential ancestor node ID
        descendant_id: Potential descendant node ID

    Returns:
        True if ancestor_id is an ancestor of descendant_id, False otherwise
    """
    hierarchy = spec_data.get("hierarchy", {})

    current_id = descendant_id
    visited = set()  # Prevent infinite loops in case of corrupted data

    while current_id and current_id not in visited:
        if current_id == ancestor_id:
            return True

        visited.add(current_id)
        current_node = hierarchy.get(current_id)
        if current_node is None:
            break

        current_id = current_node.get("parent")

    return False


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
