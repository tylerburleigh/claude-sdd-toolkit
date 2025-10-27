"""
Spec lifecycle management operations for SDD workflows.

All operations work with JSON spec files only. No markdown files are used.
"""

import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

# Import from sdd-common
from claude_skills.common.spec import load_json_spec, save_json_spec
from claude_skills.common.paths import ensure_directory
from claude_skills.common.printer import PrettyPrinter


def move_spec(
    spec_file: Path,
    target_folder: str,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> bool:
    """
    Move a spec file between lifecycle folders.

    Args:
        spec_file: Path to current spec file
        target_folder: Target folder name (active, completed, archived)
        dry_run: If True, show move without executing
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    if not spec_file.exists():
        printer.error(f"Spec file not found: {spec_file}")
        return False

    valid_folders = ["active", "completed", "archived"]
    if target_folder not in valid_folders:
        printer.error(f"Invalid target folder '{target_folder}'. Must be one of: {', '.join(valid_folders)}")
        return False

    # Get specs directory (parent of current folder)
    current_folder = spec_file.parent
    specs_base = current_folder.parent
    target_path = specs_base / target_folder

    # Ensure target directory exists
    if not ensure_directory(target_path):
        printer.error(f"Could not create target directory: {target_path}")
        return False

    target_file = target_path / spec_file.name

    if target_file.exists():
        printer.error(f"File already exists at target: {target_file}")
        return False

    printer.info(f"Moving: {spec_file}")
    printer.info(f"To: {target_file}")

    if dry_run:
        printer.warning("DRY RUN - No changes made")
        return True

    try:
        shutil.move(str(spec_file), str(target_file))
        printer.success(f"Spec moved to {target_folder}/")
        return True
    except Exception as e:
        printer.error(f"Failed to move spec: {e}")
        return False


def complete_spec(
    spec_id: str,
    spec_file: Path,
    specs_dir: Path,
    actual_hours: Optional[float] = None,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> bool:
    """
    Mark a spec as completed and move it to completed folder.

    Performs the following:
    1. Verifies all tasks are completed
    2. Updates JSON metadata (status, completed_date, actual_hours)
    3. Moves JSON spec file to completed/ folder

    Args:
        spec_id: Specification ID
        spec_file: Path to JSON spec file
        specs_dir: Path to specs directory
        actual_hours: Optional actual hours spent
        dry_run: If True, show changes without executing
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    # Load and verify spec
    printer.action(f"Loading spec for {spec_id}...")
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return False

    hierarchy = spec_data.get("hierarchy", {})

    # Check if all tasks are completed
    incomplete_tasks = []
    for node_id, node_data in hierarchy.items():
        if node_data.get("type") == "task" and node_data.get("status") != "completed":
            incomplete_tasks.append(f"{node_id}: {node_data.get('title', 'Unknown')}")

    if incomplete_tasks:
        printer.error(f"Cannot complete spec - {len(incomplete_tasks)} incomplete task(s):")
        for task in incomplete_tasks[:5]:  # Show first 5
            printer.detail(task)
        if len(incomplete_tasks) > 5:
            printer.detail(f"... and {len(incomplete_tasks) - 5} more")
        return False

    # Calculate completion progress
    spec_root = hierarchy.get("spec-root", {})
    total_tasks = spec_root.get("total_tasks", 0)
    completed_tasks = spec_root.get("completed_tasks", 0)

    printer.success(f"All {total_tasks} tasks completed!")

    # Update JSON metadata
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if "metadata" not in spec_data:
        spec_data["metadata"] = {}

    spec_data["metadata"]["status"] = "completed"
    spec_data["metadata"]["completed_date"] = timestamp

    if actual_hours:
        spec_data["metadata"]["actual_hours"] = actual_hours

    # Update last_updated timestamp
    spec_data["last_updated"] = timestamp

    printer.info("Updating metadata:")
    printer.detail(f"status: completed")
    printer.detail(f"completed_date: {timestamp}")
    if actual_hours:
        printer.detail(f"actual_hours: {actual_hours}")

    if dry_run:
        printer.warning("DRY RUN - No changes made")
        return True

    # Save JSON spec file
    if not save_json_spec(spec_id, specs_dir, spec_data, backup=True):
        printer.error("Failed to save spec file with completion metadata")
        return False

    # Move to completed folder
    printer.action("Moving spec to completed/...")
    if not move_spec(spec_file, "completed", dry_run=False, printer=printer):
        printer.error("Failed to move spec file")
        printer.warning("Metadata was updated but file was not moved")
        return False

    printer.success(f"Spec {spec_id} marked as completed and moved to completed/")
    return True
