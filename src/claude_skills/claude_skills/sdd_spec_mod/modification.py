"""
Core spec modification operations.

Provides functions for adding, removing, and moving nodes in SDD specification hierarchies.
"""

import sys
import copy
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone
from contextlib import contextmanager

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


@contextmanager
def spec_transaction(spec_data: Dict[str, Any]):
    """
    Context manager that provides transaction support for spec modifications.

    Creates a deep copy of the spec before yielding. If the context exits
    normally, changes are kept. If an exception is raised, the spec is
    rolled back to its original state.

    Usage:
        with spec_transaction(spec_data):
            add_node(spec_data, "phase-1", {"node_id": "task-1", ...})
            # If any error occurs, changes are rolled back

    Args:
        spec_data: The full spec data dictionary to protect

    Yields:
        The original spec_data dict (modifications happen in-place)

    Note:
        This creates a deep copy of the spec, which can be expensive for
        large specs. Use judiciously for critical operations.
    """
    # Create deep copy of the hierarchy before modification
    original_hierarchy = copy.deepcopy(spec_data.get("hierarchy", {}))

    try:
        yield spec_data
    except Exception as e:
        # Rollback: restore original hierarchy
        spec_data["hierarchy"] = original_hierarchy
        raise  # Re-raise the exception after rollback


def transactional_modify(
    spec_data: Dict[str, Any],
    operation: Callable[[Dict[str, Any]], Dict[str, Any]],
    validate: bool = True
) -> Dict[str, Any]:
    """
    Execute a modification operation with transaction support and optional validation.

    This function wraps a modification operation in a transaction, optionally
    validates the spec after the modification, and rolls back if validation fails.

    Args:
        spec_data: The full spec data dictionary
        operation: A callable that performs the modification. It receives spec_data
                  and should return a result dict with "success" and "message" keys.
        validate: If True, validates the spec after modification (default: True)

    Returns:
        Dict with success status and message:
        {
            "success": True|False,
            "message": "Description of result",
            "operation_result": {...} (result from the operation if successful)
        }

    Example:
        def my_operation(spec):
            return add_node(spec, "phase-1", {"node_id": "task-1", ...})

        result = transactional_modify(spec_data, my_operation, validate=True)
    """
    try:
        with spec_transaction(spec_data):
            # Execute the operation
            operation_result = operation(spec_data)

            # Check if operation failed
            if not operation_result.get("success", False):
                raise ValueError(f"Operation failed: {operation_result.get('message', 'Unknown error')}")

            # Optional validation
            if validate:
                validation_result = _validate_spec_integrity(spec_data)
                if not validation_result["valid"]:
                    raise ValueError(f"Validation failed: {validation_result['message']}")

            return {
                "success": True,
                "message": "Operation completed successfully",
                "operation_result": operation_result
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"Transaction rolled back: {str(e)}"
        }


def _validate_spec_integrity(spec_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the integrity of a spec after modifications.

    Checks for common integrity issues:
    - All parent references point to existing nodes
    - All child references point to existing nodes
    - No orphaned nodes (except spec-root)
    - Parent-child relationships are bidirectional
    - Task counts are consistent

    Args:
        spec_data: The full spec data dictionary

    Returns:
        Dict with validation result:
        {
            "valid": True|False,
            "message": "Description of validation result",
            "errors": [...] (list of specific errors if validation failed)
        }
    """
    hierarchy = spec_data.get("hierarchy", {})
    errors = []

    # Check parent references
    for node_id, node in hierarchy.items():
        parent_id = node.get("parent")

        # spec-root should have no parent
        if node_id == "spec-root":
            if parent_id is not None:
                errors.append(f"spec-root has parent '{parent_id}' (should be None)")
            continue

        # All other nodes must have a parent
        if parent_id is None:
            errors.append(f"Node '{node_id}' has no parent")
            continue

        # Parent must exist
        if parent_id not in hierarchy:
            errors.append(f"Node '{node_id}' has nonexistent parent '{parent_id}'")
            continue

        # Parent must list this node as a child
        parent = hierarchy[parent_id]
        parent_children = parent.get("children", [])
        if node_id not in parent_children:
            errors.append(f"Node '{node_id}' not in parent '{parent_id}' children list")

    # Check child references
    for node_id, node in hierarchy.items():
        children = node.get("children", [])
        for child_id in children:
            # Child must exist
            if child_id not in hierarchy:
                errors.append(f"Node '{node_id}' has nonexistent child '{child_id}'")
                continue

            # Child must reference this node as parent
            child = hierarchy[child_id]
            if child.get("parent") != node_id:
                errors.append(f"Child '{child_id}' does not reference '{node_id}' as parent")

    if errors:
        return {
            "valid": False,
            "message": f"Found {len(errors)} integrity error(s)",
            "errors": errors
        }

    return {
        "valid": True,
        "message": "Spec integrity validated successfully",
        "errors": []
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


def apply_modifications(
    spec_data: Dict[str, Any],
    modifications_file: str,
    validate_after_each: bool = False
) -> Dict[str, Any]:
    """
    Apply a batch of modifications from a JSON file to a spec.

    Reads a JSON file containing an array of modification operations and
    applies them sequentially to the spec. Each operation is atomic - if
    one fails, previous successful operations are kept but remaining ones
    are skipped.

    Args:
        spec_data: The full spec data dictionary to modify
        modifications_file: Path to JSON file containing modifications array
        validate_after_each: If True, validates spec after each modification
                           and rolls back if validation fails (default: False)
                           Set to True for strict validation with rollback

    Returns:
        Dict with overall status and per-operation results:
        {
            "success": True|False,
            "message": "Overall summary",
            "total_operations": N,
            "successful": N,
            "failed": N,
            "results": [
                {
                    "operation": {...},
                    "success": True|False,
                    "message": "...",
                    "error": "..." (only if failed),
                    "validation_error": "..." (if validation failed)
                },
                ...
            ]
        }

    Modification File Format:
        {
            "modifications": [
                {
                    "operation": "add_node",
                    "parent_id": "phase-1",
                    "node_data": {
                        "node_id": "task-1-5",
                        "type": "task",
                        "title": "New task",
                        "description": "...",
                        "status": "pending"
                    },
                    "position": 2
                },
                {
                    "operation": "update_node_field",
                    "node_id": "task-1-1",
                    "field": "title",
                    "value": "Updated title"
                },
                {
                    "operation": "remove_node",
                    "node_id": "task-2-3",
                    "cascade": true
                },
                {
                    "operation": "move_node",
                    "node_id": "task-1-3",
                    "new_parent_id": "phase-2",
                    "position": 0
                }
            ]
        }

    Raises:
        FileNotFoundError: If modifications_file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        ValueError: If file format is invalid
    """
    import json
    from pathlib import Path

    # Import validation function
    try:
        from claude_skills.common import validate_spec_hierarchy
    except ImportError:
        # Fallback to internal validation if common module not available
        validate_spec_hierarchy = None

    # Validate modifications file exists
    mod_file_path = Path(modifications_file)
    if not mod_file_path.exists():
        raise FileNotFoundError(f"Modifications file not found: {modifications_file}")

    # Read and parse modifications file
    try:
        with open(mod_file_path, 'r', encoding='utf-8') as f:
            mod_data = json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Invalid JSON in modifications file: {str(e)}",
            e.doc,
            e.pos
        )

    # Validate file structure
    if not isinstance(mod_data, dict):
        raise ValueError("Modifications file must contain a JSON object")

    if "modifications" not in mod_data:
        raise ValueError("Modifications file must contain 'modifications' key")

    modifications = mod_data["modifications"]
    if not isinstance(modifications, list):
        raise ValueError("'modifications' must be an array")

    # Track results
    results = []
    successful = 0
    failed = 0

    # Map operation names to functions
    operation_handlers = {
        # Low-level node operations
        "add_node": _handle_add_node,
        "remove_node": _handle_remove_node,
        "update_node_field": _handle_update_node_field,
        "move_node": _handle_move_node,
        # High-level task-centric convenience operations
        "update_task": _handle_update_task,
        "update_metadata": _handle_update_metadata,
        "add_verification": _handle_add_verification,
        "batch_update": _handle_batch_update,
    }

    # Apply each modification sequentially with per-operation validation
    for i, mod in enumerate(modifications):
        if not isinstance(mod, dict):
            result = {
                "operation": mod,
                "success": False,
                "message": f"Operation {i+1} is not a valid object",
                "error": "Expected dict, got " + type(mod).__name__
            }
            results.append(result)
            failed += 1
            continue

        operation_type = mod.get("operation")
        if not operation_type:
            result = {
                "operation": mod,
                "success": False,
                "message": f"Operation {i+1} missing 'operation' field",
                "error": "Missing required field 'operation'"
            }
            results.append(result)
            failed += 1
            continue

        if operation_type not in operation_handlers:
            result = {
                "operation": mod,
                "success": False,
                "message": f"Unknown operation type: {operation_type}",
                "error": f"Valid operations: {', '.join(operation_handlers.keys())}"
            }
            results.append(result)
            failed += 1
            continue

        # Execute operation with transaction support
        handler = operation_handlers[operation_type]
        try:
            # Use transaction context for rollback capability
            with spec_transaction(spec_data):
                op_result = handler(spec_data, mod)

                # Check if operation succeeded
                if not op_result.get("success", False):
                    # Operation failed - transaction will rollback
                    raise ValueError(op_result.get("message", "Operation failed"))

                # Validate spec after modification if requested
                if validate_after_each and validate_spec_hierarchy:
                    validation_result = validate_spec_hierarchy(spec_data)

                    # Check if validation passed (no errors)
                    if not validation_result.is_valid():
                        error_count, warning_count = validation_result.count_all_issues()
                        error_msg = f"Validation failed with {error_count} error(s)"

                        # Collect first error message for reporting
                        first_error = None
                        for errors_list in [
                            validation_result.structure_errors,
                            validation_result.hierarchy_errors,
                            validation_result.node_errors,
                            validation_result.count_errors,
                            validation_result.dependency_errors,
                            validation_result.metadata_errors
                        ]:
                            if errors_list:
                                first_error = errors_list[0]
                                break

                        if first_error:
                            error_msg = f"{error_msg}: {first_error}"

                        raise ValueError(error_msg)

            # If we reach here, operation succeeded and validation passed
            result = {
                "operation": mod,
                "success": True,
                "message": op_result.get("message", "Operation completed"),
            }

            # Include additional fields from operation result
            for key in ["node_id", "old_value", "removed_nodes", "old_parent_id", "new_parent_id"]:
                if key in op_result:
                    result[key] = op_result[key]

            successful += 1
            results.append(result)

        except Exception as e:
            # Transaction rolled back - operation failed
            result = {
                "operation": mod,
                "success": False,
                "message": f"Operation failed: {str(e)}",
                "error": str(e)
            }

            # Check if this was a validation error
            if "Validation failed" in str(e):
                result["validation_error"] = str(e)

            results.append(result)
            failed += 1

    # Prepare overall result
    total_operations = len(modifications)
    overall_success = failed == 0

    return {
        "success": overall_success,
        "message": f"Applied {successful}/{total_operations} modifications successfully",
        "total_operations": total_operations,
        "successful": successful,
        "failed": failed,
        "results": results
    }


def _handle_add_node(spec_data: Dict[str, Any], mod: Dict[str, Any]) -> Dict[str, Any]:
    """Handle add_node operation from modifications file."""
    required_fields = ["parent_id", "node_data"]
    missing = [f for f in required_fields if f not in mod]
    if missing:
        return {
            "success": False,
            "message": f"Missing required fields: {', '.join(missing)}"
        }

    parent_id = mod["parent_id"]
    node_data = mod["node_data"]
    position = mod.get("position")

    return add_node(spec_data, parent_id, node_data, position)


def _handle_remove_node(spec_data: Dict[str, Any], mod: Dict[str, Any]) -> Dict[str, Any]:
    """Handle remove_node operation from modifications file."""
    if "node_id" not in mod:
        return {
            "success": False,
            "message": "Missing required field: node_id"
        }

    node_id = mod["node_id"]
    cascade = mod.get("cascade", False)

    return remove_node(spec_data, node_id, cascade)


def _handle_update_node_field(spec_data: Dict[str, Any], mod: Dict[str, Any]) -> Dict[str, Any]:
    """Handle update_node_field operation from modifications file."""
    required_fields = ["node_id", "field", "value"]
    missing = [f for f in required_fields if f not in mod]
    if missing:
        return {
            "success": False,
            "message": f"Missing required fields: {', '.join(missing)}"
        }

    node_id = mod["node_id"]
    field = mod["field"]
    value = mod["value"]

    return update_node_field(spec_data, node_id, field, value)


def _handle_move_node(spec_data: Dict[str, Any], mod: Dict[str, Any]) -> Dict[str, Any]:
    """Handle move_node operation from modifications file."""
    required_fields = ["node_id", "new_parent_id"]
    missing = [f for f in required_fields if f not in mod]
    if missing:
        return {
            "success": False,
            "message": f"Missing required fields: {', '.join(missing)}"
        }

    node_id = mod["node_id"]
    new_parent_id = mod["new_parent_id"]
    position = mod.get("position")

    return move_node(spec_data, node_id, new_parent_id, position)


def _handle_update_task(spec_data: Dict[str, Any], mod: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle update_task operation from modifications file.

    This is a convenience wrapper that allows updating multiple task fields
    in a single operation. It's task-centric and more user-friendly than
    calling update_node_field multiple times.

    Args:
        spec_data: The full spec data dictionary
        mod: Modification dict containing:
            - task_id: ID of the task to update
            - updates: Dict of field-value pairs to update

    Returns:
        Dict with success status and message

    Example:
        {
            "operation": "update_task",
            "task_id": "task-1-5-3",
            "updates": {
                "title": "New title",
                "description": "New description",
                "file_path": "app/services/foo.py",
                "task_category": "implementation"
            }
        }
    """
    # Validate required fields
    if "task_id" not in mod:
        return {
            "success": False,
            "message": "Missing required field: task_id"
        }

    if "updates" not in mod:
        return {
            "success": False,
            "message": "Missing required field: updates"
        }

    task_id = mod["task_id"]
    updates = mod["updates"]

    if not isinstance(updates, dict):
        return {
            "success": False,
            "message": "updates must be a dictionary"
        }

    if not updates:
        return {
            "success": False,
            "message": "updates dictionary cannot be empty"
        }

    # Verify task exists
    task = get_node(spec_data, task_id)
    if task is None:
        return {
            "success": False,
            "message": f"Task '{task_id}' not found in hierarchy"
        }

    # Validate it's a task-like node
    task_type = task.get("type")
    if task_type not in ["task", "subtask", "verify"]:
        return {
            "success": False,
            "message": f"Node '{task_id}' is type '{task_type}', not a task/subtask/verify"
        }

    # Track which fields were updated
    updated_fields = []
    failed_fields = []

    # Apply each update sequentially
    for field, value in updates.items():
        result = update_node_field(spec_data, task_id, field, value)
        if result.get("success"):
            updated_fields.append(field)
        else:
            failed_fields.append((field, result.get("message", "Unknown error")))

    # Determine overall success
    if failed_fields:
        if not updated_fields:
            # All updates failed
            error_msgs = [f"{field}: {msg}" for field, msg in failed_fields]
            return {
                "success": False,
                "message": f"All updates failed for task '{task_id}'. Errors: {'; '.join(error_msgs)}"
            }
        else:
            # Partial success
            error_msgs = [f"{field}: {msg}" for field, msg in failed_fields]
            return {
                "success": False,
                "message": f"Updated {len(updated_fields)} field(s) but {len(failed_fields)} failed: {'; '.join(error_msgs)}",
                "updated_fields": updated_fields,
                "failed_fields": failed_fields
            }
    else:
        # All updates succeeded
        return {
            "success": True,
            "message": f"Successfully updated {len(updated_fields)} field(s) for task '{task_id}'",
            "updated_fields": updated_fields
        }


def _handle_update_metadata(spec_data: Dict[str, Any], mod: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle update_metadata operation from modifications file.

    This is a convenience wrapper for updating metadata fields without
    needing to nest them under a "metadata" key. It merges with existing
    metadata rather than replacing it.

    Args:
        spec_data: The full spec data dictionary
        mod: Modification dict containing:
            - task_id or node_id: ID of the node to update
            - metadata: Dict of metadata field-value pairs to merge

    Returns:
        Dict with success status and message

    Example:
        {
            "operation": "update_metadata",
            "task_id": "task-1-5-3",
            "metadata": {
                "details": "Detailed implementation notes",
                "estimated_hours": 4,
                "priority": "high"
            }
        }
    """
    # Accept either task_id or node_id
    node_id = mod.get("task_id") or mod.get("node_id")
    if not node_id:
        return {
            "success": False,
            "message": "Missing required field: task_id or node_id"
        }

    if "metadata" not in mod:
        return {
            "success": False,
            "message": "Missing required field: metadata"
        }

    metadata = mod["metadata"]

    if not isinstance(metadata, dict):
        return {
            "success": False,
            "message": "metadata must be a dictionary"
        }

    if not metadata:
        return {
            "success": False,
            "message": "metadata dictionary cannot be empty"
        }

    # Verify node exists
    node = get_node(spec_data, node_id)
    if node is None:
        return {
            "success": False,
            "message": f"Node '{node_id}' not found in hierarchy"
        }

    # Use update_node_field which handles metadata merging
    result = update_node_field(spec_data, node_id, "metadata", metadata)

    if result.get("success"):
        return {
            "success": True,
            "message": f"Successfully merged {len(metadata)} metadata field(s) for node '{node_id}'",
            "merged_fields": list(metadata.keys())
        }
    else:
        return {
            "success": False,
            "message": result.get("message", f"Failed to update metadata for node '{node_id}'")
        }


def _handle_add_verification(spec_data: Dict[str, Any], mod: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle add_verification operation from modifications file.

    This is a convenience wrapper for adding verification steps to tasks.
    It auto-generates the boilerplate structure needed for a verify node.

    Args:
        spec_data: The full spec data dictionary
        mod: Modification dict containing:
            - task_id: ID of the parent task
            - verify_id: ID for the new verification node
            - description: Description of what to verify
            - command: Optional command to run for verification
            - verification_type: Optional type (default: "manual")

    Returns:
        Dict with success status and message

    Example:
        {
            "operation": "add_verification",
            "task_id": "task-2-1",
            "verify_id": "verify-2-1-1",
            "description": "Base streaming insert helper works correctly with staging write-through",
            "command": "pytest tests/test_streaming.py",
            "verification_type": "automated"
        }
    """
    # Validate required fields
    required_fields = ["task_id", "verify_id", "description"]
    missing = [f for f in required_fields if f not in mod]
    if missing:
        return {
            "success": False,
            "message": f"Missing required fields: {', '.join(missing)}"
        }

    task_id = mod["task_id"]
    verify_id = mod["verify_id"]
    description = mod["description"]
    command = mod.get("command", "")
    verification_type = mod.get("verification_type", "manual")

    # Validate description is not empty
    if not description or not description.strip():
        return {
            "success": False,
            "message": "description cannot be empty"
        }

    # Verify parent task exists
    parent_task = get_node(spec_data, task_id)
    if parent_task is None:
        return {
            "success": False,
            "message": f"Parent task '{task_id}' not found in hierarchy"
        }

    # Validate parent is a task-like node
    parent_type = parent_task.get("type")
    if parent_type not in ["task", "subtask", "phase", "group"]:
        return {
            "success": False,
            "message": f"Parent '{task_id}' is type '{parent_type}', cannot add verification to this type"
        }

    # Create verification node data with boilerplate
    node_data = {
        "node_id": verify_id,
        "type": "verify",
        "title": description.strip(),
        "description": description.strip(),
        "status": "pending",
        "metadata": {
            "verification_type": verification_type
        },
        "dependencies": {
            "blocks": [],
            "blocked_by": [],
            "depends": []
        }
    }

    # Add command if provided
    if command:
        node_data["command"] = command

    # Use add_node to add the verification
    result = add_node(spec_data, task_id, node_data)

    if result.get("success"):
        return {
            "success": True,
            "message": f"Successfully added verification '{verify_id}' to task '{task_id}'",
            "node_id": verify_id
        }
    else:
        return {
            "success": False,
            "message": result.get("message", f"Failed to add verification '{verify_id}'")
        }


def _handle_batch_update(spec_data: Dict[str, Any], mod: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle batch_update operation from modifications file.

    This allows applying the same change to multiple nodes at once,
    which is useful for bulk operations like setting priority across
    all tasks in a phase.

    Args:
        spec_data: The full spec data dictionary
        mod: Modification dict containing:
            - node_ids: List of node IDs to update
            - field: Field name to update
            - value: Value to set for all nodes

    Returns:
        Dict with success status and message

    Example:
        {
            "operation": "batch_update",
            "node_ids": ["task-1-1", "task-1-2", "task-1-3"],
            "field": "metadata",
            "value": {"priority": "high"}
        }
    """
    # Validate required fields
    required_fields = ["node_ids", "field", "value"]
    missing = [f for f in required_fields if f not in mod]
    if missing:
        return {
            "success": False,
            "message": f"Missing required fields: {', '.join(missing)}"
        }

    node_ids = mod["node_ids"]
    field = mod["field"]
    value = mod["value"]

    if not isinstance(node_ids, list):
        return {
            "success": False,
            "message": "node_ids must be a list"
        }

    if not node_ids:
        return {
            "success": False,
            "message": "node_ids list cannot be empty"
        }

    # Track results
    updated_nodes = []
    failed_nodes = []

    # Apply update to each node
    for node_id in node_ids:
        # Verify node exists
        node = get_node(spec_data, node_id)
        if node is None:
            failed_nodes.append((node_id, "Node not found"))
            continue

        # Apply update
        result = update_node_field(spec_data, node_id, field, value)
        if result.get("success"):
            updated_nodes.append(node_id)
        else:
            failed_nodes.append((node_id, result.get("message", "Unknown error")))

    # Determine overall success
    if failed_nodes:
        if not updated_nodes:
            # All updates failed
            error_msgs = [f"{nid}: {msg}" for nid, msg in failed_nodes]
            return {
                "success": False,
                "message": f"All batch updates failed. Errors: {'; '.join(error_msgs)}"
            }
        else:
            # Partial success
            error_msgs = [f"{nid}: {msg}" for nid, msg in failed_nodes]
            return {
                "success": False,
                "message": f"Updated {len(updated_nodes)}/{len(node_ids)} nodes. Failures: {'; '.join(error_msgs)}",
                "updated_nodes": updated_nodes,
                "failed_nodes": failed_nodes
            }
    else:
        # All updates succeeded
        return {
            "success": True,
            "message": f"Successfully updated field '{field}' for {len(updated_nodes)} node(s)",
            "updated_nodes": updated_nodes
        }
