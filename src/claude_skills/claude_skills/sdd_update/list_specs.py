"""List specification files with filtering and formatting options."""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from rich.table import Table
from rich.console import Console

from claude_skills.common import load_json_spec, find_specs_directory, PrettyPrinter
from claude_skills.common.json_output import output_json


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


def list_specs(
    *,
    status: Optional[str] = None,
    specs_dir: Path,
    output_format: str = "text",
    verbose: bool = False,
    printer: Optional[PrettyPrinter] = None,
    compact: bool = False,
) -> List[Dict[str, Any]]:
    """
    List specification files with optional filtering.

    Args:
        status: Filter by status folder (active, completed, archived, pending, all)
        specs_dir: Base specs directory
        output_format: Output format (text or json)
        verbose: Include detailed information
        printer: PrettyPrinter instance for output

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

    # Output results
    if output_format == "json":
        output_json(specs_info, compact=compact)
    else:
        _print_specs_text(specs_info, verbose, printer)

    return specs_info


def _print_specs_text(
    specs_info: List[Dict[str, Any]],
    verbose: bool,
    printer: PrettyPrinter,
) -> None:
    """Print specs using Rich.Table for structured output."""

    if not specs_info:
        printer.info("No specifications found.")
        return

    # Create Rich console
    console = Console(width=20000, force_terminal=True)

    # Create Rich.Table with specified columns
    table = Table(
        title="📋 Specifications",
        show_header=True,
        header_style="bold cyan",
        border_style="blue",
        title_style="bold magenta",
    )

    # Add columns: ID, Title, Progress, Status, Phase, Updated
    table.add_column("ID", style="cyan", no_wrap=True, overflow="ignore", min_width=30)
    table.add_column("Title", style="white", no_wrap=True, overflow="ignore", min_width=25)
    table.add_column("Progress", justify="right", style="yellow", no_wrap=True, overflow="ignore", min_width=12)
    table.add_column("Status", justify="center", style="green", no_wrap=True, overflow="ignore", min_width=10)
    table.add_column("Phase", style="blue", no_wrap=True, overflow="ignore", min_width=10)
    table.add_column("Updated", style="dim", no_wrap=True, overflow="ignore", min_width=10)

    # Add rows for each spec
    for spec in specs_info:
        # Format progress with visual progress bar
        if spec['total_tasks'] > 0:
            # Create visual progress bar
            progress_bar = _create_progress_bar(spec['progress_percentage'], width=10)
            # Combine bar with text
            progress = f"{progress_bar} {spec['progress_percentage']}%\n{spec['completed_tasks']}/{spec['total_tasks']} tasks"
        else:
            progress = "No tasks"

        # Format status with color/emoji
        status = spec['status']
        if status == "active":
            status_display = "⚡ Active"
        elif status == "completed":
            status_display = "✅ Complete"
        elif status == "pending":
            status_display = "⏸️  Pending"
        elif status == "archived":
            status_display = "📦 Archived"
        else:
            status_display = status.title()

        # Format phase
        phase = spec.get('current_phase', '-')

        # Format updated timestamp
        updated = spec.get('updated_at', '-')
        if updated and updated != '-':
            # Truncate to date only for brevity
            updated = updated.split('T')[0] if 'T' in updated else updated

        # Add row to table
        table.add_row(
            spec['spec_id'],
            spec['title'],
            progress,
            status_display,
            phase,
            updated
        )

    # Print table
    console.print(table)

    # Print verbose details if requested
    if verbose:
        console.print("\n[bold]Verbose Details:[/bold]")
        for spec in specs_info:
            console.print(f"\n[cyan]{spec['spec_id']}[/cyan]:")
            if spec.get('version'):
                console.print(f"  Version: {spec['version']}")
            if spec.get('description'):
                console.print(f"  Description: {spec['description']}")
            if spec.get('author'):
                console.print(f"  Author: {spec['author']}")
            if spec.get('created_at'):
                console.print(f"  Created: {spec['created_at']}")
            if spec.get('file_path'):
                console.print(f"  File: {spec['file_path']}")
