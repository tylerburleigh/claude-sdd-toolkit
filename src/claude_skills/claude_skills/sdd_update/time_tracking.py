"""
Time tracking operations for SDD workflows.

All operations work with JSON spec files only. No markdown files are used.
"""

from pathlib import Path
from typing import Optional, Dict

# Import from sdd-common
from claude_skills.common.spec import load_json_spec, save_json_spec, update_node
from claude_skills.common.printer import PrettyPrinter


def track_time(
    spec_id: str,
    task_id: str,
    actual_hours: float,
    specs_dir: Path,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> bool:
    """
    Record actual time spent on a task.

    Args:
        spec_id: Specification ID
        task_id: Task identifier
        actual_hours: Actual hours spent on task
        specs_dir: Path to specs/active directory
        dry_run: If True, show change without saving
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    if actual_hours <= 0:
        printer.error("Actual hours must be positive")
        return False

    # Load state
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return False

    hierarchy = spec_data.get("hierarchy", {})
    if task_id not in hierarchy:
        printer.error(f"Task '{task_id}' not found")
        return False

    task = hierarchy[task_id]
    estimated = task.get("metadata", {}).get("estimated_hours")

    updates = {
        "metadata": {
            **task.get("metadata", {}),
            "actual_hours": actual_hours
        }
    }

    printer.info(f"Task: {task.get('title', task_id)}")
    printer.info(f"Actual hours: {actual_hours}")
    if estimated:
        variance = actual_hours - float(estimated)
        printer.info(f"Estimated: {estimated}h (variance: {variance:+.1f}h)")

    if dry_run:
        printer.warning("DRY RUN - No changes saved")
        return True

    if not update_node(spec_data, task_id, updates):
        return False

    if not save_json_spec(spec_id, specs_dir, spec_data, backup=True):
        return False

    printer.success("Time tracked")
    return True


def generate_time_report(
    spec_id: str,
    specs_dir: Path,
    printer: Optional[PrettyPrinter] = None
) -> Optional[Dict]:
    """
    Generate time variance report for a spec.

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs/active directory
        printer: Optional printer for output

    Returns:
        Dictionary with time analysis, or None on error
    """
    if not printer:
        printer = PrettyPrinter()

    # Load state
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return None

    hierarchy = spec_data.get("hierarchy", {})

    total_estimated = 0.0
    total_actual = 0.0
    tasks_with_time = []

    # Collect time data from all tasks
    for node_id, node_data in hierarchy.items():
        if node_data.get("type") != "task":
            continue

        metadata = node_data.get("metadata", {})
        estimated = metadata.get("estimated_hours")
        actual = metadata.get("actual_hours")

        if actual:
            actual_val = float(actual)
            total_actual += actual_val

            estimated_val = float(estimated) if estimated else 0
            if estimated:
                total_estimated += estimated_val

            tasks_with_time.append({
                "task_id": node_id,
                "title": node_data.get("title", "Unknown"),
                "estimated": estimated_val,
                "actual": actual_val,
                "variance": actual_val - estimated_val if estimated else 0
            })

    if not tasks_with_time:
        printer.warning("No time tracking data found")
        return None

    # Calculate metrics
    total_variance = total_actual - total_estimated
    variance_pct = (total_variance / total_estimated * 100) if total_estimated > 0 else 0

    report = {
        "spec_id": spec_id,
        "total_estimated": total_estimated,
        "total_actual": total_actual,
        "total_variance": total_variance,
        "variance_percentage": variance_pct,
        "tasks": tasks_with_time
    }

    printer.header("Time Report")
    printer.result("Total Estimated", f"{total_estimated:.1f}h")
    printer.result("Total Actual", f"{total_actual:.1f}h")
    printer.result("Variance", f"{total_variance:+.1f}h ({variance_pct:+.1f}%)")

    printer.info("\nTask Breakdown:")
    for task in sorted(tasks_with_time, key=lambda t: abs(t["variance"]), reverse=True):
        variance_str = f"{task['variance']:+.1f}h" if task['estimated'] > 0 else "N/A"
        printer.detail(f"{task['task_id']}: {task['actual']:.1f}h ({variance_str})")

    return report
