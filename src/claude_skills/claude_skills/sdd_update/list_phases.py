"""
Rich.Table formatting for phase listing operations.

This module provides Rich-powered table output for displaying phase information
with status indicators, progress bars, and dependency counts.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any

from rich.table import Table
from rich.console import Console

from claude_skills.common import load_json_spec, PrettyPrinter
from claude_skills.common.progress import list_phases as get_phases_list


def _create_progress_bar(percentage: int, width: int = 10) -> str:
    """
    Create a visual progress bar using block characters.

    Args:
        percentage: Completion percentage (0-100)
        width: Width of the progress bar in characters

    Returns:
        Rich markup string with colored progress bar
    """
    # Calculate filled and empty portions
    filled = int((percentage / 100) * width)
    empty = width - filled

    # Create bar with color coding based on progress
    if percentage >= 75:
        color = "green"
    elif percentage >= 50:
        color = "yellow"
    elif percentage >= 25:
        color = "orange1"
    else:
        color = "red"

    # Build the bar using block characters
    bar = f"[{color}]{'█' * filled}[/{color}]{'░' * empty}"

    return bar


def format_phases_table(
    spec_id: str,
    specs_dir: Path,
    printer: Optional[PrettyPrinter] = None,
    ui=None
) -> Optional[List[Dict]]:
    """
    List all phases using Rich.Table format.

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs directory
        printer: Optional printer for output
        ui: UI instance for console output (optional)

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
            console = ui.console if ui else Console()
            console.print("[yellow]No phases found in spec.[/yellow]")
        return []

    # Get hierarchy for dependency analysis
    hierarchy = spec_data.get("hierarchy", {})

    # Enhance phases with dependency information
    for phase in phases:
        phase_id = phase["id"]
        phase_node = hierarchy.get(phase_id, {})
        deps = phase_node.get("dependencies", {})

        phase["blocked_by"] = deps.get("blocked_by", [])
        phase["blocks"] = deps.get("blocks", [])

    # Display using Rich.Table
    if printer:
        _print_phases_table(phases, ui)

    return phases


def _print_phases_table(phases: List[Dict[str, Any]], ui=None) -> None:
    """Print phases using Rich.Table for structured output."""

    if not phases:
        console = ui.console if ui else Console()
        console.print("[yellow]No phases to display.[/yellow]")
        return

    # Create Rich console
    console = ui.console if ui else Console()

    # Create Rich.Table with specified columns
    table = Table(
        title="📋 Phases",
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        title_style="bold magenta",
    )

    # Add columns: Phase, Status, Tasks, Progress, Dependencies
    table.add_column("Phase", style="cyan", no_wrap=True, overflow="ignore", min_width=15)
    table.add_column("Status", justify="center", style="white", no_wrap=True, overflow="ignore", min_width=12)
    table.add_column("Tasks", justify="center", style="yellow", no_wrap=True, overflow="ignore", min_width=10)
    table.add_column("Progress", justify="left", style="white", no_wrap=True, overflow="ignore", min_width=18)
    table.add_column("Dependencies", style="yellow", no_wrap=True, overflow="ignore", min_width=12)

    # Add rows for each phase
    for phase in phases:
        # Format status with badge/emoji
        status = phase["status"]
        status_badges = {
            "completed": "✅ Complete",
            "in_progress": "🔄 In Progress",
            "pending": "⏳ Pending",
            "blocked": "🚫 Blocked"
        }
        status_display = status_badges.get(status, f"❓ {status.title()}")

        # Format tasks count
        completed = phase.get("completed_tasks", 0)
        total = phase.get("total_tasks", 0)
        tasks_display = f"{completed}/{total}"

        # Format progress with visual progress bar
        percentage = phase.get("percentage", 0)
        progress_bar = _create_progress_bar(percentage, width=10)
        progress_display = f"{progress_bar} {percentage}%"

        # Format dependencies
        blocked_by = phase.get("blocked_by", [])
        blocks = phase.get("blocks", [])

        dep_parts = []
        if blocked_by:
            dep_parts.append(f"⬅️ {len(blocked_by)}")
        if blocks:
            dep_parts.append(f"➡️ {len(blocks)}")

        dependencies_display = " ".join(dep_parts) if dep_parts else "-"

        # Format phase ID and title
        phase_id = phase["id"]
        title = phase.get("title", "")
        phase_display = f"{phase_id}\n{title}" if title else phase_id

        # Add row to table
        table.add_row(
            phase_display,
            status_display,
            tasks_display,
            progress_display,
            dependencies_display
        )

    # Print table
    console.print(table)
