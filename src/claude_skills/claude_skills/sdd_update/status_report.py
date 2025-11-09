"""
Enhanced status reporting with Rich layouts and panels.

Provides dashboard-style status reports for SDD workflows with:
- Phase overview panel
- Progress metrics panel
- Blockers and dependencies panel
"""

from typing import Dict, Any, List, Optional, Tuple
from rich.console import Console
from rich.table import Table
from claude_skills.common.ui_factory import create_ui


def create_progress_bar(percentage: float, width: int = 20) -> str:
    """
    Create a visual progress bar using Unicode box characters.

    Args:
        percentage: Progress percentage (0-100)
        width: Width of progress bar in characters

    Returns:
        Formatted progress bar string with color coding
    """
    filled_width = int((percentage / 100) * width)
    empty_width = width - filled_width

    filled_char = "█"
    empty_char = "░"

    bar = filled_char * filled_width + empty_char * empty_width

    # Color based on progress
    if percentage >= 100:
        return f"[green]{bar}[/green]"
    elif percentage > 0:
        return f"[yellow]{bar}[/yellow]"
    else:
        return f"[dim]{bar}[/dim]"


def _prepare_phases_table_data(spec_data: Dict[str, Any]) -> Tuple[List[Dict[str, str]], int]:
    """
    Prepare phases data for table display.

    Args:
        spec_data: Loaded JSON spec data

    Returns:
        Tuple of (table_data, phase_count) where table_data is a list of row dicts
    """
    hierarchy = spec_data.get("hierarchy", {})

    # Find all phase nodes
    phases = {}
    for node_id, node_data in hierarchy.items():
        if node_data.get("type") == "phase":
            phases[node_id] = node_data

    if not phases:
        return [], 0

    # Sort phases by ID
    sorted_phases = sorted(phases.items(), key=lambda x: x[0])

    # Prepare table data
    table_data = []
    for phase_id, phase_data in sorted_phases:
        # Extract phase info
        title = phase_data.get("title", phase_id)
        status = phase_data.get("status", "pending")
        total_tasks = phase_data.get("total_tasks", 0)
        completed_tasks = phase_data.get("completed_tasks", 0)

        # Status indicator
        if status == "completed":
            status_indicator = "✓ Complete"
        elif status == "in_progress":
            status_indicator = "● In Progress"
        elif status == "blocked":
            status_indicator = "⚠ Blocked"
        else:  # pending
            status_indicator = "○ Pending"

        # Progress with visual bar
        if total_tasks > 0:
            percentage = (completed_tasks / total_tasks) * 100
            progress_bar = create_progress_bar(percentage, width=15)
            progress_text = f"{progress_bar} {percentage:.0f}%"
        else:
            progress_text = "—"

        # Truncate title if too long
        if len(title) > 50:
            title = title[:47] + "..."

        table_data.append({
            "Phase": title,
            "Status": status_indicator,
            "Progress": progress_text
        })

    return table_data, len(phases)


def _prepare_progress_data(spec_data: Dict[str, Any]) -> Tuple[List[Dict[str, str]], str]:
    """
    Prepare progress metrics data for table display.

    Args:
        spec_data: Loaded JSON spec data

    Returns:
        Tuple of (table_data, subtitle) where table_data is a list of metric dicts
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

    # Prepare table data
    table_data = []
    if total_tasks > 0:
        percentage = (completed_tasks / total_tasks) * 100
        table_data.append({"Metric": "Overall", "Value": f"{percentage:.1f}%"})
        table_data.append({"Metric": "Completed", "Value": str(completed_tasks)})
        table_data.append({"Metric": "In Progress", "Value": str(in_progress_tasks)})
        table_data.append({"Metric": "Blocked", "Value": str(blocked_tasks) if blocked_tasks > 0 else "0"})
        table_data.append({"Metric": "Remaining", "Value": str(total_tasks - completed_tasks)})
        subtitle_text = f"{percentage:.0f}% complete"
    else:
        table_data.append({"Metric": "Overall", "Value": "No tasks"})
        subtitle_text = "No tasks"

    return table_data, subtitle_text


def _prepare_blockers_data(spec_data: Dict[str, Any]) -> Tuple[str, int]:
    """
    Prepare blockers data for panel display.

    Args:
        spec_data: Loaded JSON spec data

    Returns:
        Tuple of (content_text, blocker_count) where content_text is formatted string
    """
    hierarchy = spec_data.get("hierarchy", {})

    # Find all blocked tasks
    blocked_tasks = []
    for node_id, node_data in hierarchy.items():
        node_type = node_data.get("type", "")
        if node_type in ("task", "subtask") and node_data.get("status") == "blocked":
            blocked_tasks.append((node_id, node_data))

    if not blocked_tasks:
        return "✓ No blockers", 0

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
            reason_text = blocker_reason
        elif blocked_by:
            reason_text = f"Depends on: {', '.join(blocked_by[:3])}"
        else:
            reason_text = "Reason not specified"

        lines.append(f"{task_id}: {title}")
        lines.append(f"  {reason_text}")
        lines.append("")  # Blank line

    content = "\n".join(lines).rstrip()
    return content, len(blocked_tasks)


def _print_status_dashboard(spec_data: Dict[str, Any], ui) -> None:
    """
    Print status dashboard using UI protocol (supports both RichUi and PlainUi).

    Instead of creating a Rich.Layout, we print panels and tables sequentially,
    which works in both rich and plain modes.

    Args:
        spec_data: Loaded JSON spec data
        ui: UI instance for console output
    """
    # Prepare all data
    phases_data, phases_count = _prepare_phases_table_data(spec_data)
    progress_data, progress_subtitle = _prepare_progress_data(spec_data)
    blockers_content, blockers_count = _prepare_blockers_data(spec_data)

    # Print based on backend type
    if ui.console is None:
        # PlainUi backend - use native UI protocol methods

        # Phases table
        if phases_data:
            ui.print_table(
                data=phases_data,
                columns=["Phase", "Status", "Progress"],
                title=f"📋 Phases ({phases_count} total)"
            )
        else:
            ui.print_panel(
                content="No phases defined",
                title="📋 Phases (0 total)",
                style="default"
            )

        print()  # Spacing

        # Progress table
        ui.print_table(
            data=progress_data,
            columns=["Metric", "Value"],
            title=f"📊 Progress ({progress_subtitle})"
        )

        print()  # Spacing

        # Blockers panel
        if blockers_count > 0:
            ui.print_panel(
                content=blockers_content,
                title=f"🚧 Blockers ({blockers_count} blocked)",
                style="warning"
            )
        else:
            ui.print_panel(
                content=blockers_content,
                title="🚧 Blockers (None)",
                style="success"
            )
    else:
        # RichUi backend - use Rich.Table and Rich.Panel for enhanced display
        console = ui.console

        # Phases table
        if phases_data:
            phases_table = Table(
                title=f"📋 Phases ({phases_count} total)",
                show_header=True,
                header_style="bold cyan",
                border_style="blue",
                title_style="bold magenta"
            )
            phases_table.add_column("Phase", style="bold", no_wrap=True)
            phases_table.add_column("Status", justify="center", no_wrap=True)
            phases_table.add_column("Progress", justify="left", no_wrap=True)

            for row in phases_data:
                phases_table.add_row(row["Phase"], row["Status"], row["Progress"])

            console.print(phases_table)
        else:
            from rich.panel import Panel
            console.print(Panel(
                "[dim]No phases defined[/dim]",
                title="📋 Phases (0 total)",
                border_style="blue"
            ))

        console.print()  # Spacing

        # Progress table
        progress_table = Table(
            title=f"📊 Progress ({progress_subtitle})",
            show_header=False,
            border_style="green",
            title_style="bold magenta"
        )
        progress_table.add_column("Metric", style="bold", width=18)
        progress_table.add_column("Value", justify="right")

        for row in progress_data:
            # Add Rich markup for colored values
            metric = row["Metric"]
            value = row["Value"]

            if metric == "Overall":
                value = f"[cyan]{value}[/cyan]"
            elif metric == "Completed":
                value = f"[green]{value}[/green]"
            elif metric == "In Progress":
                value = f"[yellow]{value}[/yellow]"
            elif metric == "Blocked" and value != "0":
                value = f"[red]{value}[/red]"
            elif metric == "Blocked" and value == "0":
                value = f"[dim]{value}[/dim]"

            progress_table.add_row(metric, value)

        console.print(progress_table)
        console.print()  # Spacing

        # Blockers panel
        from rich.panel import Panel
        if blockers_count > 0:
            # Add Rich markup to blockers content
            formatted_content = blockers_content.replace("\n  ", "\n  [dim]").replace("[dim]", "[dim]", 1)
            # Bold task IDs
            import re
            formatted_content = re.sub(r'^([\w-]+):', r'[bold]\1[/bold]:', formatted_content, flags=re.MULTILINE)

            console.print(Panel(
                formatted_content,
                title=f"🚧 Blockers ({blockers_count} blocked)",
                border_style="red"
            ))
        else:
            console.print(Panel(
                "[green]✓ No blockers[/green]",
                title="🚧 Blockers (None)",
                border_style="green"
            ))


def print_status_report(spec_data: Dict[str, Any], title: Optional[str] = None, ui=None) -> None:
    """
    Print a dashboard-style status report to console.

    Works with both RichUi (rich formatting) and PlainUi (plain text) backends.

    Args:
        spec_data: Loaded JSON spec data
        title: Optional title for the report
        ui: UI instance for console output (optional)
    """
    # Ensure we have a UI instance
    if ui is None:
        ui = create_ui()

    # Print title if provided
    if title:
        if ui.console is None:
            # PlainUi
            print()
            print(title)
            print()
        else:
            # RichUi
            ui.console.print()
            ui.console.print(f"[bold cyan]{title}[/bold cyan]")
            ui.console.print()

    # Print dashboard using UI protocol
    _print_status_dashboard(spec_data, ui)

    # Print closing newline
    if ui.console is None:
        print()
    else:
        ui.console.print()


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
