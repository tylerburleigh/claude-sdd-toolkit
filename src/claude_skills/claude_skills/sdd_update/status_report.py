"""
Enhanced status reporting with Rich layouts and panels.

Provides dashboard-style status reports for SDD workflows with:
- Phase overview panel
- Progress metrics panel
- Blockers and dependencies panel
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from rich.console import Console, Group
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from claude_skills.common.ui_factory import create_ui


def create_progress_bar(percentage: float, width: int = 20, use_markup: bool = True) -> str:
    """
    Create a visual progress bar using Unicode box characters.

    Args:
        percentage: Progress percentage (0-100)
        width: Width of progress bar in characters
        use_markup: Whether to include Rich markup tags (True for RichUi, False for PlainUi)

    Returns:
        Formatted progress bar string with optional color coding
    """
    filled_width = int((percentage / 100) * width)
    empty_width = width - filled_width

    filled_char = "█"
    empty_char = "░"

    bar = filled_char * filled_width + empty_char * empty_width

    # Color based on progress (only if markup enabled)
    if use_markup:
        if percentage >= 100:
            return f"[green]{bar}[/green]"
        elif percentage > 0:
            return f"[yellow]{bar}[/yellow]"
        else:
            return f"[dim]{bar}[/dim]"
    else:
        return bar


def _prepare_phases_table_data(spec_data: Dict[str, Any], use_markup: bool = True) -> Tuple[List[Dict[str, str]], int]:
    """
    Prepare phases data for table display.

    Args:
        spec_data: Loaded JSON spec data
        use_markup: Whether to include Rich markup tags (True for RichUi, False for PlainUi)

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
            progress_bar = create_progress_bar(percentage, width=15, use_markup=use_markup)
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


def create_phases_panel(
    spec_data: Dict[str, Any],
    *,
    phases_data: Optional[List[Dict[str, str]]] = None,
    phases_count: Optional[int] = None,
    use_markup: bool = True
) -> Panel:
    """
    Create a Rich panel summarizing phases.

    Args:
        spec_data: Loaded JSON spec data
        phases_data: Optional precomputed rows from _prepare_phases_table_data
        phases_count: Optional precomputed phase count
        use_markup: Whether to generate markup-aware progress bars

    Returns:
        Rich Panel renderable
    """
    if phases_data is None or phases_count is None:
        phases_data, phases_count = _prepare_phases_table_data(
            spec_data,
            use_markup=use_markup
        )

    if not phases_data:
        return Panel(
            Text("No phases defined", style="dim"),
            title="📋 Phases (0 total)",
            border_style="blue"
        )

    phases_table = Table(
        show_header=True,
        header_style="bold cyan",
        show_edge=False,
        expand=True,
        pad_edge=False
    )
    phases_table.add_column("Phase", style="bold", no_wrap=True)
    phases_table.add_column("Status", justify="center", no_wrap=True)
    phases_table.add_column("Progress", justify="left", no_wrap=True)

    for row in phases_data:
        phases_table.add_row(row["Phase"], row["Status"], row["Progress"])

    return Panel(
        phases_table,
        title=f"📋 Phases ({phases_count} total)",
        border_style="blue"
    )


def create_progress_panel(
    spec_data: Dict[str, Any],
    *,
    progress_data: Optional[List[Dict[str, str]]] = None,
    progress_subtitle: Optional[str] = None
) -> Panel:
    """
    Create a Rich panel with progress metrics.

    Args:
        spec_data: Loaded JSON spec data
        progress_data: Optional precomputed rows from _prepare_progress_data
        progress_subtitle: Optional subtitle describing progress summary

    Returns:
        Rich Panel renderable
    """
    if progress_data is None or progress_subtitle is None:
        progress_data, progress_subtitle = _prepare_progress_data(spec_data)

    progress_table = Table(
        show_header=False,
        show_edge=False,
        expand=True,
        pad_edge=False
    )
    progress_table.add_column("Metric", style="bold", width=18)
    progress_table.add_column("Value", justify="right")

    for row in progress_data:
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
        elif metric == "Blocked":
            value = f"[dim]{value}[/dim]"

        progress_table.add_row(metric, value)

    return Panel(
        progress_table,
        title=f"📊 Progress ({progress_subtitle})",
        border_style="green"
    )


def create_blockers_panel(
    spec_data: Dict[str, Any],
    *,
    blockers_content: Optional[str] = None,
    blockers_count: Optional[int] = None
) -> Panel:
    """
    Create a Rich panel showing blockers information.

    Args:
        spec_data: Loaded JSON spec data
        blockers_content: Optional precomputed content from _prepare_blockers_data
        blockers_count: Optional number of blocked tasks

    Returns:
        Rich Panel renderable
    """
    if blockers_content is None or blockers_count is None:
        blockers_content, blockers_count = _prepare_blockers_data(spec_data)

    if blockers_count == 0:
        return Panel(
            Text("✓ No blockers", style="green"),
            title="🚧 Blockers (None)",
            border_style="green"
        )

    rendered_lines: List[Text] = []
    for line in blockers_content.splitlines():
        if not line:
            rendered_lines.append(Text(""))
            continue

        if line.startswith("  "):
            rendered_lines.append(Text(line, style="dim"))
            continue

        match = re.match(r"^([\w-]+):(.*)$", line)
        if match:
            task_id, remainder = match.groups()
            text_line = Text()
            text_line.append(task_id, style="bold")
            text_line.append(":")
            text_line.append(remainder)
            rendered_lines.append(text_line)
        else:
            rendered_lines.append(Text(line))

    blockers_group = Group(*rendered_lines) if rendered_lines else Text("")

    return Panel(
        blockers_group,
        title=f"🚧 Blockers ({blockers_count} blocked)",
        border_style="red"
    )


def create_status_layout(
    spec_data: Dict[str, Any],
    *,
    phases_panel: Optional[Panel] = None,
    progress_panel: Optional[Panel] = None,
    blockers_panel: Optional[Panel] = None,
    use_markup: bool = True
) -> Layout:
    """
    Arrange Rich panels into a cohesive dashboard layout.

    Args:
        spec_data: Loaded JSON spec data
        phases_panel: Optional precomputed phases panel
        progress_panel: Optional precomputed progress panel
        blockers_panel: Optional precomputed blockers panel
        use_markup: Whether to render markup-aware content

    Returns:
        Rich Layout renderable combining all panels
    """
    if phases_panel is None or progress_panel is None or blockers_panel is None:
        phases_data, phases_count = _prepare_phases_table_data(
            spec_data,
            use_markup=use_markup
        )
        progress_data, progress_subtitle = _prepare_progress_data(spec_data)
        blockers_content, blockers_count = _prepare_blockers_data(spec_data)

        phases_panel = create_phases_panel(
            spec_data,
            phases_data=phases_data,
            phases_count=phases_count,
            use_markup=use_markup
        )
        progress_panel = create_progress_panel(
            spec_data,
            progress_data=progress_data,
            progress_subtitle=progress_subtitle
        )
        blockers_panel = create_blockers_panel(
            spec_data,
            blockers_content=blockers_content,
            blockers_count=blockers_count
        )

    layout = Layout(name="status_dashboard")
    layout.split_column(
        Layout(name="top", ratio=2),
        Layout(name="bottom", ratio=1)
    )
    layout["top"].split_row(
        Layout(name="phases", ratio=2),
        Layout(name="progress", ratio=1)
    )

    layout["phases"].update(phases_panel)
    layout["progress"].update(progress_panel)
    layout["bottom"].update(blockers_panel)

    return layout


def _print_status_dashboard(spec_data: Dict[str, Any], ui) -> None:
    """
    Print status dashboard using UI protocol (supports both RichUi and PlainUi).

    Uses sequential panels for PlainUi and Rich layout helpers for RichUi
    backends.

    Args:
        spec_data: Loaded JSON spec data
        ui: UI instance for console output
    """
    # Determine if we should use markup based on UI backend
    use_markup = ui.console is not None  # True for RichUi, False for PlainUi

    # Prepare all data
    phases_data, phases_count = _prepare_phases_table_data(spec_data, use_markup=use_markup)
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
        # RichUi backend - compose layout using helper builders
        console = ui.console

        phases_panel = create_phases_panel(
            spec_data,
            phases_data=phases_data,
            phases_count=phases_count,
            use_markup=True
        )
        progress_panel = create_progress_panel(
            spec_data,
            progress_data=progress_data,
            progress_subtitle=progress_subtitle
        )
        blockers_panel = create_blockers_panel(
            spec_data,
            blockers_content=blockers_content,
            blockers_count=blockers_count
        )

        layout = create_status_layout(
            spec_data,
            phases_panel=phases_panel,
            progress_panel=progress_panel,
            blockers_panel=blockers_panel,
            use_markup=True
        )
        console.print(layout)


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
