"""List specification files with filtering and formatting options."""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from claude_skills.common import load_json_spec, find_specs_directory, PrettyPrinter
from claude_skills.common.json_output import output_json
from claude_skills.common.ui_factory import create_ui
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    LIST_SPECS_ESSENTIAL,
    LIST_SPECS_STANDARD,
)


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


def list_specs(
    *,
    status: Optional[str] = None,
    specs_dir: Path,
    output_format: str = "text",
    verbose: bool = False,
    printer: Optional[PrettyPrinter] = None,
    compact: bool = False,
    ui=None,
    args=None,
) -> List[Dict[str, Any]]:
    """
    List specification files with optional filtering.

    Args:
        status: Filter by status folder (active, completed, archived, pending, all)
        specs_dir: Base specs directory
        output_format: Output format (text or json)
        verbose: Include detailed information
        printer: PrettyPrinter instance for output
        ui: UI instance for console output (optional)
        args: Command arguments (for verbosity filtering)

    Returns:
        List of spec info dictionaries
    """
    if not printer:
        printer = PrettyPrinter()

    # Determine which directories to scan
    if status and status != "all":
        status_dirs = [specs_dir / status]
    else:
        # Scan all standard status directories
        status_dirs = [
            specs_dir / "active",
            specs_dir / "completed",
            specs_dir / "archived",
            specs_dir / "pending",
        ]

    # Collect spec information
    specs_info = []

    for status_dir in status_dirs:
        if not status_dir.exists():
            continue

        status_name = status_dir.name

        # Find all JSON files in this directory
        json_files = sorted(status_dir.glob("*.json"))

        for json_file in json_files:
            spec_data = load_json_spec(json_file.stem, specs_dir)
            if not spec_data:
                continue

            metadata = spec_data.get("metadata", {})
            hierarchy = spec_data.get("hierarchy", {})

            # Calculate task counts
            total_tasks = len(hierarchy)
            completed_tasks = sum(
                1 for task in hierarchy.values()
                if task.get("status") == "completed"
            )

            # Calculate progress percentage
            progress_pct = 0
            if total_tasks > 0:
                progress_pct = int((completed_tasks / total_tasks) * 100)

            info = {
                "spec_id": json_file.stem,
                "status": status_name,
                "title": metadata.get("title", "Untitled"),
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "progress_percentage": progress_pct,
                "current_phase": metadata.get("current_phase"),
                "version": metadata.get("version"),
                "created_at": metadata.get("created_at"),
                "updated_at": metadata.get("updated_at"),
            }

            if verbose:
                info["description"] = metadata.get("description")
                info["author"] = metadata.get("author")
                info["file_path"] = str(json_file)

            specs_info.append(info)

    # Sort specs: active folder first, then by completion % (highest first)
    specs_info.sort(key=lambda s: (0 if s.get("status") == "active" else 1, -s.get("progress_percentage", 0)))

    # Output results
    if output_format == "json":
        # Apply verbosity filtering for JSON output
        if args:
            filtered_specs = [
                prepare_output(spec, args, LIST_SPECS_ESSENTIAL, LIST_SPECS_STANDARD)
                for spec in specs_info
            ]
            output_json(filtered_specs, compact=compact)
        else:
            output_json(specs_info, compact=compact)
    else:
        _print_specs_text(specs_info, verbose, printer, ui)

    return specs_info


def _print_specs_text(
    specs_info: List[Dict[str, Any]],
    verbose: bool,
    printer: PrettyPrinter,
    ui=None,
) -> None:
    """
    Print specs using unified UI protocol (works with RichUi and PlainUi).

    Prepares table data as a list of dictionaries, then renders using
    the appropriate backend (Rich Table for RichUi, ASCII table for PlainUi).
    """

    if not specs_info:
        printer.info("No specifications found.")
        return

    # Ensure we have a UI instance
    if ui is None:
        ui = create_ui()

    # 1. Prepare table data as List[Dict] (backend-agnostic)
    table_data = []

    for spec in specs_info:
        # Format progress with visual progress bar
        if spec['total_tasks'] > 0:
            progress_bar = _create_progress_bar_plain(spec['progress_percentage'], width=10)
            progress = f"{progress_bar} {spec['progress_percentage']}%\n{spec['completed_tasks']}/{spec['total_tasks']} tasks"
        else:
            progress = "No tasks"

        # Format status with emoji
        status = spec['status']
        status_map = {
            "active": "⚡ Active",
            "completed": "✅ Complete",
            "pending": "⏸️  Pending",
            "archived": "📦 Archived"
        }
        status_display = status_map.get(status, status.title())

        # Format phase
        phase = spec.get('current_phase', '-')

        # Format updated timestamp
        updated = spec.get('updated_at', '-')
        if updated and updated != '-':
            updated = updated.split('T')[0] if 'T' in updated else updated

        # Build row dictionary
        row = {
            "ID": spec['spec_id'],
            "Title": spec['title'],
            "Progress": progress,
            "Status": status_display,
            "Phase": phase,
            "Updated": updated
        }

        table_data.append(row)

    # 2. Define columns
    columns = ["ID", "Title", "Progress", "Status", "Phase", "Updated"]

    # 3. Render based on UI backend
    if ui.console is None:
        # PlainUi backend - use native print_table()
        ui.print_table(data=table_data, columns=columns, title="📋 Specifications")
    else:
        # RichUi backend - convert to Rich Table and render
        from rich.table import Table

        table = Table(
            title="📋 Specifications",
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
            title_style="bold magenta",
        )

        # Column configuration for Rich rendering
        column_config = {
            "ID": {"style": "cyan", "no_wrap": True, "overflow": "ignore", "min_width": 30},
            "Title": {"style": "white", "no_wrap": True, "overflow": "ignore", "min_width": 25},
            "Progress": {"style": "yellow", "no_wrap": True, "overflow": "ignore", "min_width": 12, "justify": "right"},
            "Status": {"style": "green", "no_wrap": True, "overflow": "ignore", "min_width": 10, "justify": "center"},
            "Phase": {"style": "blue", "no_wrap": True, "overflow": "ignore", "min_width": 10},
            "Updated": {"style": "dim", "no_wrap": True, "overflow": "ignore", "min_width": 10}
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

    # 4. Print verbose details if requested
    if verbose:
        # Format verbose output for both backends
        verbose_text = "\n📊 Verbose Details:\n"
        for spec in specs_info:
            verbose_text += f"\n{spec['spec_id']}:\n"
            if spec.get('version'):
                verbose_text += f"  Version: {spec['version']}\n"
            if spec.get('description'):
                verbose_text += f"  Description: {spec['description']}\n"
            if spec.get('author'):
                verbose_text += f"  Author: {spec['author']}\n"
            if spec.get('created_at'):
                verbose_text += f"  Created: {spec['created_at']}\n"
            if spec.get('file_path'):
                verbose_text += f"  File: {spec['file_path']}\n"

        printer.info(verbose_text)
