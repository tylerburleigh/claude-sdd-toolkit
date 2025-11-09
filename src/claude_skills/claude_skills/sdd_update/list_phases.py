"""
Unified table formatting for phase listing operations.

This module provides table output for displaying phase information
with status indicators, progress bars, and dependency counts.
Works with both RichUi and PlainUi backends.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any

from claude_skills.common import load_json_spec, PrettyPrinter
from claude_skills.common.progress import list_phases as get_phases_list
from claude_skills.common.ui_factory import create_ui
from claude_skills.common.ui_protocol import MessageLevel


def _create_progress_bar_plain(percentage: int, width: int = 10) -> str:
    """
    Create a visual progress bar using block characters.

    Works with both Rich and plain text backends.

    Args:
        percentage: Completion percentage (0-100)
        width: Width of the progress bar in characters

    Returns:
        Progress bar string using block characters (no color codes)
    """
    # Calculate filled and empty portions
    filled = int((percentage / 100) * width)
    empty = width - filled

    # Build the bar using block characters (no Rich markup)
    # Use filled (█) and empty (░) block characters
    bar = f"{'█' * filled}{'░' * empty}"

    return bar


def format_phases_table(
    spec_id: str,
    specs_dir: Path,
    printer: Optional[PrettyPrinter] = None,
    ui=None
) -> Optional[List[Dict]]:
    """
    List all phases using unified UI protocol.

    Works with both RichUi and PlainUi backends.

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
            printer.info("No phases found in spec.")
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

    # Display using unified UI protocol (works with both RichUi and PlainUi)
    if printer:
        _print_phases_table(phases, ui)

    return phases


def _print_phases_table(phases: List[Dict[str, Any]], ui=None) -> None:
    """
    Print phases using unified UI protocol (works with RichUi and PlainUi).

    Prepares table data as a list of dictionaries, then renders using
    the appropriate backend (Rich Table for RichUi, ASCII table for PlainUi).
    """

    if not phases:
        if ui:
            ui.print_status("No phases to display.", level=MessageLevel.WARNING)
        return

    # Ensure we have a UI instance
    if ui is None:
        ui = create_ui()

    # 1. Prepare table data as List[Dict] (backend-agnostic)
    table_data = []

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
        progress_bar = _create_progress_bar_plain(percentage, width=10)
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

        # Build row dictionary
        row = {
            "Phase": phase_display,
            "Status": status_display,
            "Tasks": tasks_display,
            "Progress": progress_display,
            "Dependencies": dependencies_display
        }

        table_data.append(row)

    # 2. Define columns
    columns = ["Phase", "Status", "Tasks", "Progress", "Dependencies"]

    # 3. Render based on UI backend
    if ui.console is None:
        # PlainUi backend - use native print_table()
        ui.print_table(data=table_data, columns=columns, title="📋 Phases")
    else:
        # RichUi backend - convert to Rich Table and render
        from rich.table import Table

        table = Table(
            title="📋 Phases",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            title_style="bold magenta",
        )

        # Column configuration for Rich rendering
        column_config = {
            "Phase": {"style": "cyan", "no_wrap": True, "overflow": "ignore", "min_width": 15},
            "Status": {"style": "white", "no_wrap": True, "overflow": "ignore", "min_width": 12, "justify": "center"},
            "Tasks": {"style": "yellow", "no_wrap": True, "overflow": "ignore", "min_width": 10, "justify": "center"},
            "Progress": {"style": "white", "no_wrap": True, "overflow": "ignore", "min_width": 18, "justify": "left"},
            "Dependencies": {"style": "yellow", "no_wrap": True, "overflow": "ignore", "min_width": 12}
        }

        # Add columns
        for col in columns:
            config = column_config.get(col, {})
            table.add_column(col, **config)

        # Add rows
        for row_data in table_data:
            table.add_row(*[row_data.get(col, "") for col in columns])

        # Render table
        ui.console.print(table)
