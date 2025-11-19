"""
Progress calculation utilities for SDD JSON specs.
Provides hierarchical progress recalculation and status updates.
"""

import json
import sys
from datetime import datetime, timezone
from typing import Dict, List, Optional, TextIO


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
        # Check if actual children progress matches the "completed" state
        # Note: node["completed_tasks"] has already been summed from children in recalculate_progress
        actual_completed = node.get("completed_tasks", 0)
        total = node.get("total_tasks", 0)

        if actual_completed < total:
            # Inconsistent state: parent marked complete but children aren't.
            # This happens if new subtasks were added after completion, or children weren't marked.
            # We must respect the children's state to avoid validation errors.
            # Remove completed_at to allow normal status calculation to take over below.
            if "metadata" in node and "completed_at" in node["metadata"]:
                del node["metadata"]["completed_at"]
        else:
            # Consistent state, enforce completion
            node["status"] = "completed"
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
        # Check if status is changing to completed (auto-completion)
        was_completed = node.get("status") == "completed"
        node["status"] = "completed"

        # Set needs_journaling flag for parent nodes (groups, phases)
        # when they auto-complete (not manually set)
        if not was_completed and node.get("type") in ["group", "phase"]:
            if "metadata" not in node:
                node["metadata"] = {}
            node["metadata"]["needs_journaling"] = True
            node["metadata"]["completed_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
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


class ProgressEmitter:
    """
    Emits structured JSON progress events for AI agents and automation tools.

    This class provides a programmatic interface for emitting progress updates
    as JSON events to stdout or a specified stream. Events are newline-delimited
    JSON objects that can be parsed by consuming tools.

    Example usage:
        emitter = ProgressEmitter()
        emitter.emit("task_started", {"task_id": "task-1-1", "title": "Setup"})
        emitter.emit("progress", {"completed": 5, "total": 10, "percentage": 50})
        emitter.emit("task_completed", {"task_id": "task-1-1", "duration": 120})

    Event format:
        {
            "type": "event_type",
            "timestamp": "2025-11-07T19:00:00.000Z",
            "data": {...}
        }
    """

    def __init__(self, output: Optional[TextIO] = None, enabled: Optional[bool] = None, auto_detect_tty: bool = True):
        """
        Initialize the ProgressEmitter.

        Args:
            output: Output stream for events (default: sys.stdout)
            enabled: Whether emission is enabled. If None, auto-detect based on TTY (default: None)
            auto_detect_tty: Automatically disable in non-TTY environments (default: True)
        """
        self.output = output or sys.stdout
        self.auto_detect_tty = auto_detect_tty

        # Auto-detect TTY if enabled is not explicitly set
        if enabled is None and auto_detect_tty:
            # Disable in non-interactive environments (pipes, redirects, CI/CD)
            self.enabled = not self._is_interactive()
        else:
            self.enabled = enabled if enabled is not None else True

    def _is_interactive(self) -> bool:
        """
        Check if the output stream is interactive (TTY).

        Returns:
            True if output is a TTY (interactive terminal), False otherwise
        """
        try:
            return hasattr(self.output, 'isatty') and self.output.isatty()
        except (AttributeError, ValueError):
            # If isatty() raises or doesn't exist, assume non-interactive
            return False

    def emit(self, event_type: str, data: Optional[Dict] = None) -> None:
        """
        Emit a structured JSON event.

        Args:
            event_type: Type of event (e.g., "task_started", "progress", "error")
            data: Event data dictionary (optional)

        Emits a newline-delimited JSON object with:
            - type: The event type
            - timestamp: ISO 8601 timestamp with UTC timezone
            - data: The provided data dictionary (or empty dict if None)

        Example:
            emitter.emit("task_started", {"task_id": "task-1-1", "title": "Setup"})
            # Output: {"type":"task_started","timestamp":"2025-11-07T19:00:00.000Z","data":{"task_id":"task-1-1","title":"Setup"}}
        """
        if not self.enabled:
            return

        event = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "data": data or {}
        }

        try:
            json_str = json.dumps(event, separators=(',', ':'))
            self.output.write(json_str + '\n')
            self.output.flush()
        except (IOError, OSError):
            # Silently handle output errors (e.g., broken pipe)
            pass

    def disable(self) -> None:
        """Disable event emission."""
        self.enabled = False

    def enable(self) -> None:
        """Enable event emission."""
        self.enabled = True
