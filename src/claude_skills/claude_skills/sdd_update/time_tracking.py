"""
Time tracking operations for SDD workflows.

All operations work with JSON spec files only. No markdown files are used.
"""

from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

# Import from sdd-common
from claude_skills.common.spec import load_json_spec, save_json_spec, update_node
from claude_skills.common.printer import PrettyPrinter


def validate_timestamp_pair(
    start_timestamp: Optional[str],
    end_timestamp: Optional[str],
    allow_negative: bool = True,
    printer: Optional[PrettyPrinter] = None
) -> tuple[bool, Optional[str]]:
    """
    Validate a pair of timestamps for time calculation.

    Args:
        start_timestamp: Start timestamp string
        end_timestamp: End timestamp string
        allow_negative: If False, returns invalid for negative durations
        printer: Optional printer for error messages

    Returns:
        Tuple of (is_valid, error_message)
    """
    if printer is None:
        printer = PrettyPrinter()

    # Check for None/empty
    if not start_timestamp:
        return False, "Start timestamp is required"
    if not end_timestamp:
        return False, "End timestamp is required"

    # Try parsing
    try:
        start = datetime.fromisoformat(start_timestamp.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_timestamp.replace('Z', '+00:00'))
    except (ValueError, AttributeError) as e:
        return False, f"Invalid timestamp format: {str(e)}"

    # Check for negative duration if not allowed
    if not allow_negative and end < start:
        return False, f"End timestamp ({end_timestamp}) is before start timestamp ({start_timestamp})"

    return True, None


def calculate_time_from_timestamps(
    start_timestamp: str,
    end_timestamp: str,
    printer: Optional[PrettyPrinter] = None
) -> Optional[float]:
    """
    Calculate decimal hours between two ISO 8601 timestamps.

    Args:
        start_timestamp: ISO 8601 timestamp string (e.g., "2025-10-27T10:00:00Z")
        end_timestamp: ISO 8601 timestamp string (e.g., "2025-10-27T13:30:00Z")
        printer: Optional printer for error messages

    Returns:
        Decimal hours between timestamps, or None if parsing fails

    Examples:
        >>> calculate_time_from_timestamps("2025-10-27T10:00:00Z", "2025-10-27T13:30:00Z")
        3.5
    """
    if printer is None:
        printer = PrettyPrinter()

    # Validate inputs are not None or empty
    if not start_timestamp or not end_timestamp:
        printer.error("Both timestamps are required (received None or empty string)")
        return None

    try:
        # Parse timestamps, handling 'Z' suffix
        start = datetime.fromisoformat(start_timestamp.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_timestamp.replace('Z', '+00:00'))

        # Calculate timedelta
        delta = end - start

        # Convert to decimal hours (total_seconds() / 3600)
        hours = delta.total_seconds() / 3600

        # Warn if negative duration (end before start)
        if hours < 0:
            printer.warning(f"Negative duration detected: end timestamp ({end_timestamp}) is before start ({start_timestamp})")

        # Round to 0.001 hour precision (3.6 second increments) for accurate tracking
        return round(hours, 3)

    except ValueError as e:
        printer.error(f"Invalid timestamp format: {str(e)}")
        return None
    except AttributeError as e:
        printer.error(f"Invalid timestamp type: {str(e)}")
        return None


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
        if printer:
            printer.warning("No time tracking data found")
        # Return empty report structure for JSON consumers
        return {
            "spec_id": spec_id,
            "total_estimated": 0.0,
            "total_actual": 0.0,
            "total_variance": 0.0,
            "variance_percentage": 0.0,
            "tasks": []
        }

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

    if printer:
        printer.header("Time Report")
        printer.result("Total Estimated", f"{total_estimated:.1f}h")
        printer.result("Total Actual", f"{total_actual:.1f}h")
        printer.result("Variance", f"{total_variance:+.1f}h ({variance_pct:+.1f}%)")

        printer.info("\nTask Breakdown:")
        for task in sorted(tasks_with_time, key=lambda t: abs(t["variance"]), reverse=True):
            variance_str = f"{task['variance']:+.1f}h" if task['estimated'] > 0 else "N/A"
            printer.detail(f"{task['task_id']}: {task['actual']:.1f}h ({variance_str})")

    return report


def aggregate_task_times(
    spec_id: str,
    specs_dir: Path,
    printer: Optional[PrettyPrinter] = None
) -> Optional[float]:
    """
    Aggregate actual_hours from all tasks in the spec hierarchy.

    Traverses the hierarchy recursively and sums all actual_hours values
    from task-level nodes that have time tracking data.

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs/active directory
        printer: Optional printer for error messages

    Returns:
        Total actual hours across all tasks, or None if no time data found

    Examples:
        >>> aggregate_task_times("user-auth-2025-10-18-001", Path("specs/active"))
        18.5
    """
    if not printer:
        printer = PrettyPrinter()

    # Load state
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return None

    hierarchy = spec_data.get("hierarchy", {})

    total_actual = 0.0
    tasks_found = 0

    # Collect time data from all tasks
    for node_id, node_data in hierarchy.items():
        if node_data.get("type") != "task":
            continue

        metadata = node_data.get("metadata", {})
        actual = metadata.get("actual_hours")

        if actual:
            try:
                actual_val = float(actual)
                total_actual += actual_val
                tasks_found += 1
            except (ValueError, TypeError) as e:
                printer.warning(f"Invalid actual_hours value for {node_id}: {actual} ({e})")
                continue

    if tasks_found == 0:
        return None

    return round(total_actual, 3)
