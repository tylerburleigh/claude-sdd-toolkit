"""
Task estimate management for SDD specifications.

Provides functions for updating task estimates (estimated_hours and complexity).
"""

from typing import Dict, Any, Optional


def update_task_estimate(
    spec_data: Dict[str, Any],
    task_id: str,
    estimated_hours: Optional[float] = None,
    complexity: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update estimated_hours and/or complexity for a task.

    Args:
        spec_data: The full spec data dictionary (modified in-place)
        task_id: Task ID to update (e.g., "task-2-1", "phase-1")
        estimated_hours: New estimated hours value (if provided)
        complexity: New complexity level (if provided): "low", "medium", "high"

    Returns:
        Dict with success status and details:
        {
            "success": True,
            "task_id": "task-2-1",
            "message": "Updated estimate for task-2-1",
            "updates": {"estimated_hours": 3.5, "complexity": "medium"}
        }

    Raises:
        ValueError: If spec data is invalid, task not found, or invalid values
    """
    # Validate spec structure
    if not isinstance(spec_data, dict):
        raise ValueError("spec_data must be a dictionary")

    if "hierarchy" not in spec_data:
        raise ValueError("spec_data must have 'hierarchy' key")

    if not isinstance(spec_data["hierarchy"], dict):
        raise ValueError("hierarchy must be a dictionary")

    # Validate that at least one update was provided
    if estimated_hours is None and complexity is None:
        raise ValueError("Must provide at least one of: estimated_hours, complexity")

    # Find the task in hierarchy
    hierarchy = spec_data["hierarchy"]
    if task_id not in hierarchy:
        raise ValueError(f"Task '{task_id}' not found in spec hierarchy")

    task_node = hierarchy[task_id]

    # Initialize metadata if it doesn't exist
    if "metadata" not in task_node:
        task_node["metadata"] = {}

    metadata = task_node["metadata"]
    updates = {}

    # Update estimated_hours
    if estimated_hours is not None:
        if not isinstance(estimated_hours, (int, float)):
            raise ValueError(f"estimated_hours must be a number, got {type(estimated_hours).__name__}")
        if estimated_hours < 0:
            raise ValueError(f"estimated_hours must be non-negative, got {estimated_hours}")

        metadata["estimated_hours"] = float(estimated_hours)
        updates["estimated_hours"] = float(estimated_hours)

    # Update complexity
    if complexity is not None:
        valid_complexity_levels = ["low", "medium", "high"]
        if complexity not in valid_complexity_levels:
            raise ValueError(
                f"Invalid complexity level: '{complexity}'. "
                f"Must be one of: {', '.join(valid_complexity_levels)}"
            )

        metadata["complexity"] = complexity
        updates["complexity"] = complexity

    # Build message
    task_title = task_node.get("title", "Untitled")
    update_parts = []
    if "estimated_hours" in updates:
        update_parts.append(f"estimated_hours={updates['estimated_hours']}h")
    if "complexity" in updates:
        update_parts.append(f"complexity={updates['complexity']}")

    message = f"Updated {task_id} ({task_title}): {', '.join(update_parts)}"

    return {
        "success": True,
        "task_id": task_id,
        "task_title": task_title,
        "message": message,
        "updates": updates
    }


def get_task_estimate(
    spec_data: Dict[str, Any],
    task_id: str
) -> Dict[str, Any]:
    """
    Get estimate information for a task.

    Args:
        spec_data: The full spec data dictionary
        task_id: Task ID to query

    Returns:
        Dict with estimate information:
        {
            "task_id": "task-2-1",
            "estimated_hours": 3.5,
            "complexity": "medium",
            "actual_hours": 4.2  # if available
        }

    Raises:
        ValueError: If task not found
    """
    if not isinstance(spec_data, dict) or "hierarchy" not in spec_data:
        raise ValueError("Invalid spec data")

    hierarchy = spec_data["hierarchy"]
    if task_id not in hierarchy:
        raise ValueError(f"Task '{task_id}' not found in spec hierarchy")

    task_node = hierarchy[task_id]
    metadata = task_node.get("metadata", {})

    result = {
        "task_id": task_id,
        "task_title": task_node.get("title", "Untitled"),
        "estimated_hours": metadata.get("estimated_hours"),
        "complexity": metadata.get("complexity"),
    }

    # Include actual_hours if available
    if "actual_hours" in metadata:
        result["actual_hours"] = metadata["actual_hours"]

    return result
