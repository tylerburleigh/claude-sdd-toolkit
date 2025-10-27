"""
Query operations for SDD JSON specs.
Provides filtering, searching, and retrieval of tasks and nodes.
These are pure read operations that don't modify state.
"""

from pathlib import Path
from typing import Optional, Dict, List

from .spec import load_json_spec, get_node
from .progress import list_phases as get_phases_list
from .printer import PrettyPrinter


def query_tasks(
    spec_id: str,
    specs_dir: Path,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    parent: Optional[str] = None,
    format_type: str = "table",
    printer: Optional[PrettyPrinter] = None,
    limit: Optional[int] = 20
) -> Optional[List[Dict]]:
    """
    Query and filter tasks by various criteria.

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs directory
        status: Filter by status (pending/in_progress/completed/blocked)
        task_type: Filter by type (task/verify/group/phase)
        parent: Filter by parent node ID
        format_type: Output format (table/json/simple)
        printer: Optional printer for output
        limit: Maximum number of results to return (default 20, use 0 for unlimited)

    Returns:
        List of matching task dictionaries, or None on error
    """
    # Load state
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return None

    hierarchy = spec_data.get("hierarchy", {})
    matches = []

    # Filter tasks
    for node_id, node_data in hierarchy.items():
        # Apply filters
        if status and node_data.get("status") != status:
            continue
        if task_type and node_data.get("type") != task_type:
            continue
        if parent and node_data.get("parent") != parent:
            continue

        # Skip spec-root unless specifically requested
        if node_id == "spec-root" and not parent and not task_type:
            continue

        matches.append({
            "id": node_id,
            "title": node_data.get("title", ""),
            "type": node_data.get("type", ""),
            "status": node_data.get("status", ""),
            "parent": node_data.get("parent", ""),
            "completed_tasks": node_data.get("completed_tasks", 0),
            "total_tasks": node_data.get("total_tasks", 0),
            "metadata": node_data.get("metadata", {})
        })

    # Apply limit if specified
    total_count = len(matches)
    limited = False
    if limit and limit > 0 and len(matches) > limit:
        matches = matches[:limit]
        limited = True

    # Display based on format (only if printer is provided)
    if printer:
        if format_type == "table":
            if limited:
                printer.header(f"Tasks matching filters (showing {len(matches)} of {total_count})")
            else:
                printer.header(f"Tasks matching filters (found {len(matches)})")

            if limited:
                printer.detail(f"💡 Use --limit=0 to see all {total_count} results")
                printer.info("")

            if status:
                printer.detail(f"Status: {status}")
            if task_type:
                printer.detail(f"Type: {task_type}")
            if parent:
                printer.detail(f"Parent: {parent}")

            printer.info("")
            for task in matches:
                status_symbol = {
                    "completed": "✓",
                    "in_progress": "→",
                    "pending": "○",
                    "blocked": "✗"
                }.get(task["status"], "?")

                printer.detail(f"{status_symbol} {task['id']}: {task['title']} [{task['type']}]")
                if task['type'] in ['phase', 'group']:
                    printer.detail(f"  Progress: {task['completed_tasks']}/{task['total_tasks']}")

        elif format_type == "simple":
            for task in matches:
                printer.info(task["id"])

    return matches


def get_task(
    spec_id: str,
    task_id: str,
    specs_dir: Path,
    printer: Optional[PrettyPrinter] = None,
    include_journal: bool = False
) -> Optional[Dict]:
    """
    Get detailed information about a specific task.

    Args:
        spec_id: Specification ID
        task_id: Task ID to retrieve
        specs_dir: Path to specs directory
        printer: Optional printer for output
        include_journal: If True, include journal entries for this task

    Returns:
        Task data dictionary, or None if not found
    """
    # Load state
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return None

    # Get the task
    task = get_node(spec_data, task_id)
    if not task:
        if printer:
            printer.error(f"Task '{task_id}' not found")
        return None

    # Get journal entries if requested
    journal_entries = None
    if include_journal:
        all_entries = spec_data.get("journal", [])
        journal_entries = [entry for entry in all_entries if entry.get("task_id") == task_id]
        # Add to task dict for JSON output
        task["journal_entries"] = journal_entries

    # Display task details (only if printer is provided)
    if printer:
        printer.header(f"Task: {task_id}")
        printer.result("Title", task.get("title", ""))
        printer.result("Type", task.get("type", ""))
        printer.result("Status", task.get("status", ""))
        printer.result("Parent", task.get("parent", ""))

        if task.get("children"):
            printer.result("Children", ", ".join(task["children"]))

        printer.result("Progress", f"{task.get('completed_tasks', 0)}/{task.get('total_tasks', 0)}")

        # Display metadata if present
        metadata = task.get("metadata", {})
        if metadata:
            printer.info("\nMetadata:")
            for key, value in metadata.items():
                if key in ["started_at", "completed_at", "blocked_at"]:
                    printer.detail(f"{key}: {value}")
                elif key in ["file_path", "command", "expected"]:
                    printer.detail(f"{key}: {value}")
                elif key == "notes":
                    printer.detail(f"notes: {value}")

        # Display dependencies if present
        deps = task.get("dependencies", {})
        if deps:
            printer.info("\nDependencies:")
            if deps.get("blocked_by"):
                printer.detail(f"Blocked by: {', '.join(deps['blocked_by'])}")

        # Display journal entries if included
        if include_journal and journal_entries:
            printer.info(f"\nJournal Entries ({len(journal_entries)}):")
            for entry in journal_entries:
                # Format timestamp
                timestamp_str = entry.get("timestamp", "Unknown")
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(str(timestamp_str).replace('Z', '+00:00'))
                    timestamp_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass

                printer.detail(f"• {timestamp_str} - {entry.get('title', 'Untitled')} [{entry.get('entry_type', 'note')}]")
                content = entry.get("content", "")
                if len(content) > 150:
                    printer.detail(f"  {content[:150]}...")
                else:
                    printer.detail(f"  {content}")

    return task


def list_phases(
    spec_id: str,
    specs_dir: Path,
    printer: Optional[PrettyPrinter] = None
) -> Optional[List[Dict]]:
    """
    List all phases with their progress.

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs directory
        printer: Optional printer for output

    Returns:
        List of phase dictionaries, or None on error
    """
    # Load state
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return None

    # Get phases using sdd_common utility
    phases = get_phases_list(spec_data)

    if not phases:
        if printer:
            printer.warning("No phases found in spec")
        return []

    # Display phases (only if printer is provided)
    if printer:
        printer.header("Phases")
        printer.info("")

        for phase in phases:
            status_symbol = {
                "completed": "✓",
                "in_progress": "→",
                "pending": "○",
                "blocked": "✗"
            }.get(phase["status"], "?")

            printer.detail(
                f"{status_symbol} {phase['id']}: {phase['title']} "
                f"[{phase['completed_tasks']}/{phase['total_tasks']} - {phase['percentage']}%]"
            )

    return phases


def check_complete(
    spec_id: str,
    specs_dir: Path,
    phase_id: Optional[str] = None,
    task_id: Optional[str] = None,
    printer: Optional[PrettyPrinter] = None
) -> Dict:
    """
    Check if spec, phase, or task is ready to be marked complete.

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs directory
        phase_id: Optional phase ID to check (if None, checks entire spec)
        task_id: Optional task ID to check (mutually exclusive with phase_id)
        printer: Optional printer for output

    Returns:
        Dictionary with completion status and incomplete tasks
    """
    # Load state
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return {"error": "Failed to load state"}

    hierarchy = spec_data.get("hierarchy", {})

    # Validate mutually exclusive parameters
    if phase_id and task_id:
        if printer:
            printer.error("Cannot specify both --phase and --task")
        return {"error": "Cannot specify both phase_id and task_id"}

    # Determine what to check
    if task_id:
        if task_id not in hierarchy:
            if printer:
                printer.error(f"Task '{task_id}' not found")
            return {"error": f"Task not found: {task_id}"}
        root_node_id = task_id
        node_type = hierarchy[task_id].get("type", "node")
        check_label = f"{node_type.capitalize()} {task_id}"
    elif phase_id:
        if phase_id not in hierarchy:
            if printer:
                printer.error(f"Phase '{phase_id}' not found")
            return {"error": f"Phase not found: {phase_id}"}
        root_node_id = phase_id
        check_label = f"Phase {phase_id}"
    else:
        root_node_id = "spec-root"
        check_label = "Spec"

    # Find all incomplete tasks under this node
    incomplete = []

    def find_incomplete(node_id):
        """Recursively find incomplete tasks."""
        node = hierarchy.get(node_id)
        if not node:
            return

        # Check if this is an incomplete leaf task
        node_type = node.get("type")
        status = node.get("status")

        if node_type in ["task", "verify"]:
            if status != "completed":
                incomplete.append({
                    "id": node_id,
                    "title": node.get("title", ""),
                    "type": node_type,
                    "status": status
                })

        # Recurse to children
        for child_id in node.get("children", []):
            find_incomplete(child_id)

    find_incomplete(root_node_id)

    # Determine if complete
    is_complete = len(incomplete) == 0

    # Display results (only if printer is provided)
    if printer:
        if is_complete:
            printer.success(f"{check_label} is ready to be marked complete!")
        else:
            printer.warning(f"{check_label} has {len(incomplete)} incomplete task(s):")
            for task in incomplete[:10]:  # Show first 10
                status_symbol = {
                    "in_progress": "→",
                    "pending": "○",
                    "blocked": "✗"
                }.get(task["status"], "?")
                printer.detail(f"{status_symbol} {task['id']}: {task['title']} [{task['status']}]")

            if len(incomplete) > 10:
                printer.detail(f"... and {len(incomplete) - 10} more")

    return {
        "is_complete": is_complete,
        "incomplete_count": len(incomplete),
        "incomplete_tasks": incomplete
    }


def list_blockers(
    spec_id: str,
    specs_dir: Path,
    printer: Optional[PrettyPrinter] = None
) -> Optional[List[Dict]]:
    """
    List all currently blocked tasks with their blocker details.

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs directory
        printer: Optional printer for output

    Returns:
        List of blocked task dictionaries, or None on error
    """
    # Load state
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return None

    hierarchy = spec_data.get("hierarchy", {})
    blockers = []

    # Find all blocked tasks
    for node_id, node_data in hierarchy.items():
        if node_data.get("status") == "blocked":
            metadata = node_data.get("metadata", {})

            blockers.append({
                "id": node_id,
                "title": node_data.get("title", ""),
                "type": node_data.get("type", ""),
                "blocked_at": metadata.get("blocked_at", ""),
                "blocker_type": metadata.get("blocker_type", ""),
                "blocker_description": metadata.get("blocker_description", ""),
                "blocker_ticket": metadata.get("blocker_ticket", ""),
                "blocked_by_external": metadata.get("blocked_by_external", False)
            })

    # Display results (only if printer is provided)
    if printer:
        if not blockers:
            printer.success("No blocked tasks found!")
        else:
            printer.header(f"Blocked Tasks ({len(blockers)})")
            printer.info("")

            for blocker in blockers:
                printer.detail(f"✗ {blocker['id']}: {blocker['title']}")
                if blocker.get("blocker_type"):
                    printer.detail(f"  Type: {blocker['blocker_type']}")
                if blocker.get("blocker_description"):
                    printer.detail(f"  Reason: {blocker['blocker_description']}")
                if blocker.get("blocker_ticket"):
                    printer.detail(f"  Ticket: {blocker['blocker_ticket']}")
                if blocker.get("blocked_at"):
                    printer.detail(f"  Since: {blocker['blocked_at']}")
                printer.info("")

    return blockers if blockers else []


def get_journal_entries(
    spec_id: str,
    specs_dir: Path,
    task_id: Optional[str] = None,
    printer: Optional[PrettyPrinter] = None
) -> Optional[List[Dict]]:
    """
    Get journal entries for a spec, optionally filtered by task_id.

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs directory
        task_id: Optional task ID to filter entries
        printer: Optional printer for output

    Returns:
        List of journal entry dictionaries, or None on error
    """
    # Load spec
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return None

    # Get journal entries
    all_entries = spec_data.get("journal", [])

    # Filter by task_id if provided
    if task_id:
        entries = [entry for entry in all_entries if entry.get("task_id") == task_id]
    else:
        entries = all_entries

    # Display results (only if printer is provided)
    if printer:
        if not entries:
            if task_id:
                printer.info(f"No journal entries found for task {task_id}")
            else:
                printer.info("No journal entries found")
        else:
            if task_id:
                printer.header(f"Journal Entries for Task {task_id} ({len(entries)})")
            else:
                printer.header(f"Journal Entries ({len(entries)})")
            printer.info("")

            for entry in entries:
                # Format timestamp
                timestamp_str = entry.get("timestamp", "Unknown")
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(str(timestamp_str).replace('Z', '+00:00'))
                    timestamp_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass

                # Entry type emoji
                entry_type = entry.get("entry_type", "note")
                type_emoji = {
                    "status_change": "📊",
                    "deviation": "⚠️",
                    "blocker": "🚫",
                    "decision": "💡",
                    "note": "📝"
                }.get(entry_type, "📝")

                printer.detail(f"{type_emoji} {timestamp_str} - {entry.get('title', 'Untitled')}")
                printer.detail(f"   Type: {entry_type}")
                if entry.get("author"):
                    printer.detail(f"   Author: {entry['author']}")
                if entry.get("task_id"):
                    printer.detail(f"   Task: {entry['task_id']}")

                # Show content (truncate if too long)
                content = entry.get("content", "")
                if len(content) > 200:
                    printer.detail(f"   {content[:200]}...")
                else:
                    printer.detail(f"   {content}")
                printer.info("")

    return entries


def get_task_journal(
    spec_id: str,
    task_id: str,
    specs_dir: Path,
    printer: Optional[PrettyPrinter] = None
) -> Optional[List[Dict]]:
    """
    Get journal entries specifically for a task.

    This is a convenience wrapper around get_journal_entries.

    Args:
        spec_id: Specification ID
        task_id: Task ID
        specs_dir: Path to specs directory
        printer: Optional printer for output

    Returns:
        List of journal entry dictionaries for the task, or None on error
    """
    return get_journal_entries(spec_id, specs_dir, task_id=task_id, printer=printer)
