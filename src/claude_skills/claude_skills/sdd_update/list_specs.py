"""List specification files with filtering and formatting options."""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from claude_skills.common import load_json_spec, find_specs_directory, PrettyPrinter


def list_specs(
    *,
    status: Optional[str] = None,
    specs_dir: Path,
    output_format: str = "text",
    verbose: bool = False,
    printer: Optional[PrettyPrinter] = None,
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
        print(json.dumps(specs_info, indent=2))
    else:
        _print_specs_text(specs_info, verbose, printer)

    return specs_info


def _print_specs_text(
    specs_info: List[Dict[str, Any]],
    verbose: bool,
    printer: PrettyPrinter,
) -> None:
    """Print specs in human-readable text format."""

    if not specs_info:
        printer.info("No specifications found.")
        return

    # Group by status
    by_status: Dict[str, List[Dict[str, Any]]] = {}
    for spec in specs_info:
        status = spec["status"]
        if status not in by_status:
            by_status[status] = []
        by_status[status].append(spec)

    # Print each status group
    for status in ["active", "pending", "completed", "archived"]:
        if status not in by_status:
            continue

        specs = by_status[status]
        status_label = status.title()

        printer.success(f"\n{status_label} Specifications ({len(specs)}):")

        for spec in specs:
            print(f"  {spec['spec_id']}")
            print(f"    Title: {spec['title']}")

            if spec['total_tasks'] > 0:
                progress_str = f"{spec['completed_tasks']}/{spec['total_tasks']} tasks ({spec['progress_percentage']}%)"
                print(f"    Progress: {progress_str}")
            else:
                print("    Progress: No tasks defined")

            if spec.get('current_phase'):
                print(f"    Phase: {spec['current_phase']}")

            if verbose:
                if spec.get('version'):
                    print(f"    Version: {spec['version']}")
                if spec.get('description'):
                    print(f"    Description: {spec['description']}")
                if spec.get('author'):
                    print(f"    Author: {spec['author']}")
                if spec.get('created_at'):
                    print(f"    Created: {spec['created_at']}")
                if spec.get('updated_at'):
                    print(f"    Updated: {spec['updated_at']}")
                if spec.get('file_path'):
                    print(f"    File: {spec['file_path']}")

            print()  # Blank line between specs
