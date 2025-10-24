"""
Query operations for SDD JSON specs.
Provides filtering, searching, and retrieval of tasks and nodes.

Note: Core query operations have been moved to sdd_common.query_operations.
This module now provides time tracking queries and re-exports common operations.
"""

from pathlib import Path
from typing import Optional, Dict, List

# Import from sdd-common
# sdd_update.query
from claude_skills.common.query_operations import (
    query_tasks,
    get_task,
    list_phases,
    check_complete,
    list_blockers,
)
from claude_skills.common.spec import load_json_spec
from claude_skills.common.printer import PrettyPrinter

# Re-export common query operations for backward compatibility
__all__ = [
    'query_tasks',
    'get_task',
    'list_phases',
    'check_complete',
    'list_blockers',
    'phase_time'
]


def phase_time(
    spec_id: str,
    phase_id: str,
    specs_dir: Path,
    printer: Optional[PrettyPrinter] = None
) -> Optional[Dict]:
    """
    Calculate time spent on a specific phase.

    This is a time-tracking specific operation that remains in sdd-update.

    Args:
        spec_id: Specification ID
        phase_id: Phase ID to calculate time for
        specs_dir: Path to specs directory
        printer: Optional printer for output

    Returns:
        Dictionary with time breakdown, or None on error
    """
    # Load state
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return None

    hierarchy = spec_data.get("hierarchy", {})

    # Check phase exists
    if phase_id not in hierarchy:
        if printer:
            printer.error(f"Phase '{phase_id}' not found")
        return None

    phase = hierarchy[phase_id]

    # Calculate time from all tasks under this phase
    total_estimated = 0
    total_actual = 0
    task_times = []

    def collect_times(node_id):
        """Recursively collect time from tasks."""
        nonlocal total_estimated, total_actual

        node = hierarchy.get(node_id)
        if not node:
            return

        metadata = node.get("metadata", {})

        # Get time from this node if it's a task
        if node.get("type") == "task":
            estimated = metadata.get("estimated_hours", 0)
            actual = metadata.get("actual_hours", 0)

            if estimated > 0 or actual > 0:
                total_estimated += estimated
                total_actual += actual
                task_times.append({
                    "id": node_id,
                    "title": node.get("title", ""),
                    "estimated": estimated,
                    "actual": actual,
                    "variance": actual - estimated if actual > 0 else 0
                })

        # Recurse to children
        for child_id in node.get("children", []):
            collect_times(child_id)

    collect_times(phase_id)

    # Calculate variance
    variance = total_actual - total_estimated if total_actual > 0 else 0
    variance_pct = (variance / total_estimated * 100) if total_estimated > 0 else 0

    result = {
        "phase_id": phase_id,
        "phase_title": phase.get("title", ""),
        "total_estimated": total_estimated,
        "total_actual": total_actual,
        "variance": variance,
        "variance_percentage": variance_pct,
        "task_times": task_times
    }

    # Display results (only if printer is provided)
    if printer:
        printer.header(f"Time Report: {phase.get('title', phase_id)}")
        printer.result("Estimated", f"{total_estimated} hours")
        printer.result("Actual", f"{total_actual} hours")

        if total_actual > 0:
            variance_symbol = "+" if variance > 0 else ""
            printer.result("Variance", f"{variance_symbol}{variance:.1f} hours ({variance_symbol}{variance_pct:.1f}%)")

        if task_times:
            printer.info("\nTask Breakdown:")
            for task in task_times:
                if task["actual"] > 0:
                    var = task["variance"]
                    var_symbol = "+" if var > 0 else ""
                    printer.detail(f"{task['id']}: {task['actual']}h (est: {task['estimated']}h, {var_symbol}{var}h)")

    return result
