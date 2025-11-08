"""
Rich.Table formatting for task query operations.

This module provides Rich-powered table output for displaying task lists
with status badges, dependency indicators, and formatted columns.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any

from rich.table import Table
from rich.console import Console

from claude_skills.common import load_json_spec, PrettyPrinter


def format_tasks_table(
    spec_id: str,
    specs_dir: Path,
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    parent: Optional[str] = None,
    printer: Optional[PrettyPrinter] = None,
    limit: Optional[int] = 20
) -> Optional[List[Dict]]:
    """
    Query and display tasks using Rich.Table format.

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs directory
        status: Filter by status (pending/in_progress/completed/blocked)
        task_type: Filter by type (task/verify/group/phase)
        parent: Filter by parent node ID
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

        # Get metadata for additional info
        metadata = node_data.get("metadata", {})
        deps = node_data.get("dependencies", {})

        matches.append({
            "id": node_id,
            "title": node_data.get("title", ""),
            "type": node_data.get("type", ""),
            "status": node_data.get("status", ""),
            "parent": node_data.get("parent", ""),
            "completed_tasks": node_data.get("completed_tasks", 0),
            "total_tasks": node_data.get("total_tasks", 0),
            "file_path": metadata.get("file_path", ""),
            "dependencies": deps,
            "metadata": metadata
        })

    # Apply limit if specified
    total_count = len(matches)
    limited = False
    if limit and limit > 0 and len(matches) > limit:
        matches = matches[:limit]
        limited = True

    # Display using Rich.Table (only if printer is provided)
    if printer:
        _print_tasks_table(
            matches=matches,
            total_count=total_count,
            limited=limited,
            status_filter=status,
            type_filter=task_type,
            parent_filter=parent,
            limit=limit
        )

    return matches


def _print_tasks_table(
    matches: List[Dict[str, Any]],
    total_count: int,
    limited: bool,
    status_filter: Optional[str],
    type_filter: Optional[str],
    parent_filter: Optional[str],
    limit: Optional[int]
) -> None:
    """Print tasks using Rich.Table for structured output."""

    if not matches:
        console = Console()
        console.print("[yellow]No tasks found matching the specified filters.[/yellow]")
        return

    # Create Rich console
    console = Console()

    # Build title with filter info
    title_parts = ["📋 Tasks"]
    if limited:
        title_parts.append(f"(showing {len(matches)} of {total_count})")
    else:
        title_parts.append(f"(found {len(matches)})")

    title = " ".join(title_parts)

    # Create Rich.Table with specified columns
    table = Table(
        title=title,
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        title_style="bold magenta",
    )

    # Add columns: Task ID, Status, Title, Dependencies, File
    table.add_column("Task ID", style="cyan", no_wrap=True, overflow="ignore", min_width=12)
    table.add_column("Status", justify="center", style="white", no_wrap=True, overflow="ignore", min_width=12)
    table.add_column("Title", style="white", no_wrap=True, overflow="ignore", min_width=25)
    table.add_column("Dependencies", style="yellow", no_wrap=True, overflow="ignore", min_width=12)
    table.add_column("File", style="dim", no_wrap=True, overflow="ignore", min_width=15)

    # Add filter info if filters are active
    if status_filter or type_filter or parent_filter:
        console.print("\n[bold]Active Filters:[/bold]")
        if status_filter:
            console.print(f"  Status: [cyan]{status_filter}[/cyan]")
        if type_filter:
            console.print(f"  Type: [cyan]{type_filter}[/cyan]")
        if parent_filter:
            console.print(f"  Parent: [cyan]{parent_filter}[/cyan]")
        console.print()

    if limited and limit:
        console.print(f"[dim]💡 Use --limit=0 to see all {total_count} results[/dim]\n")

    # Add rows for each task
    for task in matches:
        # Format status with badge/emoji
        status = task["status"]
        task_type = task["type"]

        # Status badge
        status_badges = {
            "completed": "✅ Complete",
            "in_progress": "🔄 In Progress",
            "pending": "⏳ Pending",
            "blocked": "🚫 Blocked"
        }
        status_display = status_badges.get(status, f"❓ {status.title()}")

        # Dependencies indicator
        deps = task.get("dependencies", {})
        blocked_by = deps.get("blocked_by", [])
        blocks = deps.get("blocks", [])

        dep_parts = []
        if blocked_by:
            dep_parts.append(f"⬅️ {len(blocked_by)}")
        if blocks:
            dep_parts.append(f"➡️ {len(blocks)}")

        dependencies_display = " ".join(dep_parts) if dep_parts else "-"

        # File path (truncate if too long)
        file_path = task.get("file_path", "")
        if file_path:
            # Show only filename if path is too long
            if len(file_path) > 40:
                file_display = "..." + file_path[-37:]
            else:
                file_display = file_path
        else:
            file_display = "-"

        # Title with type indicator
        title = task["title"]
        if task_type in ["phase", "group"]:
            # Show progress for phases/groups
            completed = task.get("completed_tasks", 0)
            total = task.get("total_tasks", 0)
            if total > 0:
                title = f"{title}\n({completed}/{total} tasks)"

        # Add row to table
        table.add_row(
            task["id"],
            status_display,
            title,
            dependencies_display,
            file_display
        )

    # Print table
    console.print(table)
