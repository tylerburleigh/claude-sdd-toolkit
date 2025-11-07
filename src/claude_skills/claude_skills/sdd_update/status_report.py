"""
Enhanced status reporting with Rich layouts and panels.

Provides dashboard-style status reports for SDD workflows with:
- Phase overview panel
- Progress metrics panel
- Blockers and dependencies panel
"""

from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def create_phases_panel(spec_data: Dict[str, Any]) -> Panel:
    """
    Create a panel showing all phases with status indicators.

    Args:
        spec_data: Loaded JSON spec data

    Returns:
        Rich Panel with phases table
    """
    hierarchy = spec_data.get("hierarchy", {})

    # Find all phase nodes
    phases = {}
    for node_id, node_data in hierarchy.items():
        if node_data.get("type") == "phase":
            phases[node_id] = node_data

    if not phases:
        return Panel(
            "[dim]No phases defined[/dim]",
            title="📋 Phases",
            subtitle="0 total",
            border_style="blue",
            title_align="left",
            subtitle_align="right",
            padding=(1, 2),
            expand=True
        )

    # Create phases table
    table = Table(show_header=True, box=None, padding=(0, 1))
    table.add_column("Phase", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Progress", justify="right")

    # Sort phases by ID
    sorted_phases = sorted(phases.items(), key=lambda x: x[0])

    for phase_id, phase_data in sorted_phases:
        # Extract phase info
        title = phase_data.get("title", phase_id)
        status = phase_data.get("status", "pending")
        total_tasks = phase_data.get("total_tasks", 0)
        completed_tasks = phase_data.get("completed_tasks", 0)

        # Status indicator
        if status == "completed":
            status_indicator = "[green]✓ Complete[/green]"
        elif status == "in_progress":
            status_indicator = "[yellow]● In Progress[/yellow]"
        elif status == "blocked":
            status_indicator = "[red]⚠ Blocked[/red]"
        else:  # pending
            status_indicator = "[dim]○ Pending[/dim]"

        # Progress
        if total_tasks > 0:
            percentage = (completed_tasks / total_tasks) * 100
            progress_text = f"{completed_tasks}/{total_tasks} ({percentage:.0f}%)"
        else:
            progress_text = "—"

        # Truncate title if too long
        if len(title) > 40:
            title = title[:37] + "..."

        table.add_row(title, status_indicator, progress_text)

    return Panel(
        table,
        title="📋 Phases",
        subtitle=f"{len(phases)} total",
        border_style="blue",
        title_align="left",
        subtitle_align="right",
        padding=(1, 2),
        expand=True
    )


def create_progress_panel(spec_data: Dict[str, Any]) -> Panel:
    """
    Create a panel showing overall and phase-specific progress metrics.

    Args:
        spec_data: Loaded JSON spec data

    Returns:
        Rich Panel with progress metrics
    """
    hierarchy = spec_data.get("hierarchy", {})

    # Calculate overall metrics
    total_tasks = 0
    completed_tasks = 0
    in_progress_tasks = 0
    blocked_tasks = 0

    for node_id, node_data in hierarchy.items():
        node_type = node_data.get("type", "")
        if node_type in ("task", "subtask"):
            total_tasks += 1
            status = node_data.get("status", "pending")
            if status == "completed":
                completed_tasks += 1
            elif status == "in_progress":
                in_progress_tasks += 1
            elif status == "blocked":
                blocked_tasks += 1

    # Create metrics table
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Metric", style="bold", width=18)
    table.add_column("Value", justify="right")

    # Overall progress
    if total_tasks > 0:
        percentage = (completed_tasks / total_tasks) * 100
        table.add_row("Overall", f"[cyan]{percentage:.1f}%[/cyan]")
        table.add_row("Completed", f"[green]{completed_tasks}[/green]")
        table.add_row("In Progress", f"[yellow]{in_progress_tasks}[/yellow]")
        table.add_row("Blocked", f"[red]{blocked_tasks}[/red]" if blocked_tasks > 0 else "[dim]0[/dim]")
        table.add_row("Remaining", f"{total_tasks - completed_tasks}")
        subtitle_text = f"{percentage:.0f}% complete"
    else:
        table.add_row("Overall", "[dim]No tasks[/dim]")
        subtitle_text = "No tasks"

    return Panel(
        table,
        title="📊 Progress",
        subtitle=subtitle_text,
        border_style="green",
        title_align="left",
        subtitle_align="right",
        padding=(1, 2),
        expand=True
    )


def create_blockers_panel(spec_data: Dict[str, Any]) -> Panel:
    """
    Create a panel showing blocked tasks with reasons.

    Args:
        spec_data: Loaded JSON spec data

    Returns:
        Rich Panel with blockers list
    """
    hierarchy = spec_data.get("hierarchy", {})

    # Find all blocked tasks
    blocked_tasks = []
    for node_id, node_data in hierarchy.items():
        node_type = node_data.get("type", "")
        if node_type in ("task", "subtask") and node_data.get("status") == "blocked":
            blocked_tasks.append((node_id, node_data))

    if not blocked_tasks:
        return Panel(
            "[green]✓ No blockers[/green]",
            title="🚧 Blockers",
            subtitle="None",
            border_style="green",
            title_align="left",
            subtitle_align="right",
            padding=(1, 2),
            expand=True
        )

    # Create blockers content
    lines = []
    for task_id, task_data in blocked_tasks[:10]:  # Limit to 10 blockers
        title = task_data.get("title", task_id)
        if len(title) > 50:
            title = title[:47] + "..."

        # Get blocker reason from metadata or dependencies
        metadata = task_data.get("metadata", {})
        blocker_reason = metadata.get("blocker_reason", "")

        # Check dependencies
        dependencies = task_data.get("dependencies", {})
        blocked_by = dependencies.get("blocked_by", [])

        if blocker_reason:
            reason_text = f"[dim]{blocker_reason}[/dim]"
        elif blocked_by:
            reason_text = f"[dim]Depends on: {', '.join(blocked_by[:3])}[/dim]"
        else:
            reason_text = "[dim]Reason not specified[/dim]"

        lines.append(f"[bold]{task_id}[/bold]: {title}")
        lines.append(f"  {reason_text}")
        lines.append("")  # Blank line

    content = "\n".join(lines).rstrip()

    return Panel(
        content,
        title="🚧 Blockers",
        subtitle=f"{len(blocked_tasks)} blocked",
        border_style="red",
        title_align="left",
        subtitle_align="right",
        padding=(1, 2),
        expand=True
    )


def create_status_layout(spec_data: Dict[str, Any]) -> Layout:
    """
    Create a Rich.Layout with multiple panels for status dashboard.

    Layout structure:
    ┌─────────────────────────┬──────────────┐
    │                         │              │
    │   Phases Panel          │   Progress   │
    │                         │   Panel      │
    │                         │              │
    ├─────────────────────────┴──────────────┤
    │                                         │
    │   Blockers Panel                        │
    │                                         │
    └─────────────────────────────────────────┘

    Args:
        spec_data: Loaded JSON spec data

    Returns:
        Rich Layout with populated panels
    """
    # Create main layout
    layout = Layout()

    # Split into top and bottom
    layout.split_column(
        Layout(name="top", ratio=2),
        Layout(name="bottom", ratio=1)
    )

    # Split top into left and right
    layout["top"].split_row(
        Layout(name="phases", ratio=2),
        Layout(name="progress", ratio=1)
    )

    # Populate panels
    layout["phases"].update(create_phases_panel(spec_data))
    layout["progress"].update(create_progress_panel(spec_data))
    layout["bottom"].update(create_blockers_panel(spec_data))

    return layout


def print_status_report(spec_data: Dict[str, Any], title: Optional[str] = None) -> None:
    """
    Print a dashboard-style status report to console.

    Args:
        spec_data: Loaded JSON spec data
        title: Optional title for the report
    """
    console = Console()

    # Print title if provided
    if title:
        console.print()
        console.print(f"[bold cyan]{title}[/bold cyan]")
        console.print()

    # Create and print layout
    layout = create_status_layout(spec_data)
    console.print(layout)
    console.print()


def get_status_summary(spec_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a dictionary summary of status metrics.

    Useful for programmatic access to status data without printing.

    Args:
        spec_data: Loaded JSON spec data

    Returns:
        Dictionary with status metrics:
        - total_tasks: Total number of tasks
        - completed_tasks: Number of completed tasks
        - in_progress_tasks: Number of in-progress tasks
        - blocked_tasks: Number of blocked tasks
        - phases: List of phase summaries
        - blockers: List of blocked task details
    """
    hierarchy = spec_data.get("hierarchy", {})

    # Calculate task metrics
    total_tasks = 0
    completed_tasks = 0
    in_progress_tasks = 0
    blocked_tasks = 0

    for node_id, node_data in hierarchy.items():
        node_type = node_data.get("type", "")
        if node_type in ("task", "subtask"):
            total_tasks += 1
            status = node_data.get("status", "pending")
            if status == "completed":
                completed_tasks += 1
            elif status == "in_progress":
                in_progress_tasks += 1
            elif status == "blocked":
                blocked_tasks += 1

    # Collect phase summaries
    phases = []
    for node_id, node_data in hierarchy.items():
        if node_data.get("type") == "phase":
            phases.append({
                "id": node_id,
                "title": node_data.get("title", ""),
                "status": node_data.get("status", "pending"),
                "total_tasks": node_data.get("total_tasks", 0),
                "completed_tasks": node_data.get("completed_tasks", 0)
            })

    # Collect blocker details
    blockers = []
    for node_id, node_data in hierarchy.items():
        node_type = node_data.get("type", "")
        if node_type in ("task", "subtask") and node_data.get("status") == "blocked":
            metadata = node_data.get("metadata", {})
            dependencies = node_data.get("dependencies", {})
            blockers.append({
                "id": node_id,
                "title": node_data.get("title", ""),
                "reason": metadata.get("blocker_reason", ""),
                "blocked_by": dependencies.get("blocked_by", [])
            })

    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "blocked_tasks": blocked_tasks,
        "phases": sorted(phases, key=lambda x: x["id"]),
        "blockers": blockers
    }
