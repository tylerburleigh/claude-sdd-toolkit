"""
Journal and metadata operations for SDD workflows.

All operations work with JSON spec files only. No markdown files are used.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from string import Template

# sdd_update.journal
try:
    from importlib import resources as importlib_resources  # Python 3.9+
except ImportError:  # pragma: no cover - fallback for older Python
    import importlib_resources  # type: ignore

# Import from sdd-common
from claude_skills.common.printer import PrettyPrinter
from claude_skills.common.spec import load_json_spec, save_json_spec, update_node
from claude_skills.common.paths import find_specs_directory


def mark_task_journaled(
    spec_id: str,
    task_id: str,
    specs_dir: Path,
    printer: Optional[PrettyPrinter] = None,
    *,
    spec_data: Optional[Dict[str, Any]] = None,
    save: bool = True
) -> bool:
    """
    Mark a task as journaled by clearing the needs_journaling flag.

    Called automatically when add_journal_entry() includes a task_id.

    Args:
        spec_id: Specification ID
        task_id: Task identifier
        specs_dir: Path to specs directory
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    # Load JSON spec if not provided
    should_load_state = spec_data is None
    if should_load_state:
        spec_data = load_json_spec(spec_id, specs_dir)
        if not spec_data:
            printer.warning(f"Could not load JSON spec for {spec_id} - journaling flag not cleared")
            return False

    # Check if task exists
    hierarchy = spec_data.get("hierarchy", {})
    if task_id not in hierarchy:
        printer.warning(f"Task '{task_id}' not found in JSON spec - journaling flag not cleared")
        return False

    task = hierarchy[task_id]
    metadata = task.get("metadata", {})

    # Clear the needs_journaling flag
    if "needs_journaling" in metadata:
        updates = {
            "metadata": {**metadata, "needs_journaling": False, "journaled_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
        }

        if not update_node(spec_data, task_id, updates):
            printer.warning("Failed to update task journaling status")
            return False

        if save:
            # Save JSON spec (without backup, handled by caller if needed)
            if not save_json_spec(spec_id, specs_dir, spec_data, backup=False):
                printer.warning("Failed to save JSON spec after marking task journaled")
                return False

        printer.info(f"✓ Task {task_id} marked as journaled")

    return True


def _build_journal_entry(
    title: str,
    content: str,
    entry_type: str,
    author: str,
    task_id: Optional[str]
) -> Tuple[Dict[str, Any], str]:
    """Construct a journal entry payload and return entry plus timestamp."""

    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    entry = {
        "timestamp": timestamp,
        "entry_type": entry_type,
        "title": title,
        "author": author,
        "content": content,
        "metadata": {}
    }

    if task_id:
        entry["task_id"] = task_id

    return entry, timestamp


def _ensure_journal_container(spec_data: Dict[str, Any]) -> None:
    """Ensure spec_data has a journal container."""
    if "journal" not in spec_data or not isinstance(spec_data["journal"], list):
        spec_data["journal"] = []


def add_journal_entry(
    spec_id: str,
    title: str,
    content: str,
    task_id: Optional[str] = None,
    entry_type: str = "note",
    author: str = "claude-code",
    specs_dir: Optional[Path] = None,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> bool:
    """
    Add an entry to the journal array in the JSON spec file.

    Args:
        spec_id: Specification ID
        title: Entry title (e.g., "Task 1-2 Started", "Blocker: Redis Dependency")
        content: Entry content (plain text)
        task_id: Optional task ID to reference
        entry_type: Type of entry (status_change, deviation, blocker, decision, note)
        author: Author of the entry (default: claude-code)
        specs_dir: Optional specs directory (auto-detected if not provided)
        dry_run: If True, show entry without writing
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    # Find specs directory if not provided
    if specs_dir is None:
        specs_dir = find_specs_directory()
        if specs_dir is None:
            printer.error("Could not find specs directory")
            return False

    # Load JSON spec file
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        printer.error(f"Could not load spec file for {spec_id}")
        return False

    printer.info("Journal Entry:")
    printer.detail(f"  Type: {entry_type}")
    printer.detail(f"  Title: {title}")
    if task_id:
        printer.detail(f"  Task: {task_id}")
    printer.detail(f"  Content: {content[:100]}{'...' if len(content) > 100 else ''}")

    entry, timestamp = _build_journal_entry(title, content, entry_type, author, task_id)

    if dry_run:
        printer.warning("DRY RUN - No changes saved")
        return True

    try:
        _ensure_journal_container(spec_data)

        # Append new entry
        spec_data["journal"].append(entry)

        # Update last_updated timestamp
        spec_data["last_updated"] = timestamp

        # If task_id provided, clear journaling flag within same state
        if task_id:
            mark_task_journaled(
                spec_id,
                task_id,
                specs_dir,
                printer,
                spec_data=spec_data,
                save=False
            )

        # Save JSON spec file
        if not save_json_spec(spec_id, specs_dir, spec_data, backup=True):
            printer.error("Failed to save spec file")
            return False

        printer.success(f"Journal entry added to {spec_id}.json")
        return True

    except Exception as e:
        printer.error(f"Failed to add journal entry: {e}")
        return False


def update_metadata(
    spec_id: str,
    key: str,
    value: Any,
    specs_dir: Optional[Path] = None,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> bool:
    """
    Update a single field in the JSON spec metadata.

    Args:
        spec_id: Specification ID
        key: Metadata key to update
        value: New value (can be string, int, list, dict, etc.)
        specs_dir: Optional specs directory (auto-detected if not provided)
        dry_run: If True, show change without writing
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    # Find specs directory if not provided
    if specs_dir is None:
        specs_dir = find_specs_directory()
        if specs_dir is None:
            printer.error("Could not find specs directory")
            return False

    # Load JSON spec file
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        printer.error(f"Could not load spec file for {spec_id}")
        return False

    # Get or create metadata object
    if "metadata" not in spec_data:
        spec_data["metadata"] = {}

    old_value = spec_data["metadata"].get(key, "(not set)")
    printer.info(f"Updating metadata field '{key}'")
    printer.info(f"Old value: {old_value}")
    printer.info(f"New value: {value}")

    if dry_run:
        printer.warning("DRY RUN - No changes saved")
        return True

    try:
        # Update the field
        spec_data["metadata"][key] = value

        # Update last_updated timestamp
        spec_data["last_updated"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Save JSON spec file
        if not save_json_spec(spec_id, specs_dir, spec_data, backup=True):
            printer.error("Failed to save spec file")
            return False

        printer.success(f"Metadata field '{key}' updated in {spec_id}.json")
        return True

    except Exception as e:
        printer.error(f"Failed to update metadata: {e}")
        return False


def add_revision_entry(
    spec_id: str,
    version: str,
    changes: str,
    author: str = "claude-code",
    specs_dir: Optional[Path] = None,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> bool:
    """
    Add a revision entry to the JSON spec metadata.revisions array.

    Args:
        spec_id: Specification ID
        version: Version string (e.g., "1.1", "2.0")
        changes: Description of changes
        author: Author of the changes
        specs_dir: Optional specs directory (auto-detected if not provided)
        dry_run: If True, show entry without writing
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    # Find specs directory if not provided
    if specs_dir is None:
        specs_dir = find_specs_directory()
        if specs_dir is None:
            printer.error("Could not find specs directory")
            return False

    # Load JSON spec file
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        printer.error(f"Could not load spec file for {spec_id}")
        return False

    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Create revision entry
    revision = {
        "version": version,
        "date": timestamp,
        "author": author,
        "changes": changes
    }

    printer.info("Revision Entry:")
    printer.detail(f"  Version: {version}")
    printer.detail(f"  Author: {author}")
    printer.detail(f"  Changes: {changes}")

    if dry_run:
        printer.warning("DRY RUN - No changes saved")
        return True

    try:
        # Get or create metadata
        if "metadata" not in spec_data:
            spec_data["metadata"] = {}

        metadata = spec_data["metadata"]
        revisions = metadata.setdefault("revisions", [])

        # Ensure unique version
        existing_index = next((idx for idx, item in enumerate(revisions) if item.get("version") == version), None)
        if existing_index is not None:
            printer.warning(f"Revision version {version} already exists - overwriting entry")
            revisions[existing_index] = revision
        else:
            revisions.append(revision)

        # Update version in metadata
        metadata["version"] = version

        # Update last_updated timestamp
        spec_data["last_updated"] = timestamp

        # Save JSON spec file
        if not save_json_spec(spec_id, specs_dir, spec_data, backup=True):
            printer.error("Failed to save spec file")
            return False

        printer.success(f"Revision {version} recorded for {spec_id}.json")
        return True

    except Exception as e:
        printer.error(f"Failed to add revision entry: {e}")
        return False


def _render_template(template_name: str, context: Dict[str, Any]) -> str:
    """Render a journal template using string.Template."""
    try:
        template_path = importlib_resources.files(__package__) / "templates" / "bulk_journal" / f"{template_name}.md"
        template_text = template_path.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError):
        return ""

    return Template(template_text).safe_substitute(context)


def bulk_journal_tasks(
    spec_id: str,
    specs_dir: Optional[Path] = None,
    task_ids: Optional[List[str]] = None,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None,
    *,
    template: Optional[str] = None,
    template_metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Add journal entries for multiple completed tasks at once.

    Generates a journal entry for each task with:
    - Task ID and title
    - Completion timestamp
    - Status change note

    Args:
        spec_id: Specification ID
        specs_dir: Optional specs directory (auto-detected if not provided)
        task_ids: List of task IDs to journal (if None, journals all unjournaled tasks)
        dry_run: If True, show entries without writing
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    # Find specs directory if not provided
    if specs_dir is None:
        specs_dir = find_specs_directory()
        if specs_dir is None:
            printer.error("Could not find specs directory")
            return False

    # If no task_ids provided, find all unjournaled tasks
    if task_ids is None:
        from .validation import detect_unjournaled_tasks
        unjournaled = detect_unjournaled_tasks(spec_id, specs_dir, printer=None)
        if unjournaled is None:
            printer.error("Failed to detect unjournaled tasks")
            return False
        task_ids = [task["task_id"] for task in unjournaled]

    if not task_ids:
        printer.info("No tasks to journal")
        return True

    # Load state to get task details
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return False

    hierarchy = spec_data.get("hierarchy", {})
    journaled_tasks = []
    skipped_tasks = []

    printer.action(f"Journaling {len(task_ids)} task(s)...")

    _ensure_journal_container(spec_data)

    for task_id in task_ids:
        task = hierarchy.get(task_id)
        if not task:
            printer.warning(f"Task '{task_id}' not found in state - skipping")
            skipped_tasks.append(task_id)
            continue

        task_meta = task.get("metadata", {})
        completed_at_raw = task_meta.get("completed_at", "Unknown")

        # Format completion timestamp
        completed_str = "Unknown"
        if completed_at_raw not in (None, "Unknown"):
            try:
                dt = datetime.fromisoformat(str(completed_at_raw).replace('Z', '+00:00'))
                completed_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:  # pragma: no cover - fallback for invalid isoformat
                completed_str = str(completed_at_raw)

        entry_title = f"Task Completed: {task.get('title', task_id)}"
        entry_content = f"Task {task_id} completed at {completed_str}. Implementation finished and marked as completed."

        if template:
            template_context = {
                "task_id": task_id,
                "title": task.get("title", ""),
                "completed_at": completed_at_raw or "",
                "completed_at_human": completed_str,
                "phase": hierarchy.get(task.get("parent"), {}).get("title", ""),
                "spec_id": spec_id,
            }

            if template_metadata:
                template_context.update(template_metadata)

            rendered = _render_template(template, template_context)
            if rendered:
                entry_content = rendered.strip()

        entry, timestamp = _build_journal_entry(
            entry_title,
            entry_content,
            "status_change",
            author=template_metadata.get("author", "claude-code") if template_metadata else "claude-code",
            task_id=task_id,
        )

        printer.info(f"✓ Prepared journal entry for {task_id}")

        if dry_run:
            journaled_tasks.append((task_id, entry))
            continue

        spec_data["journal"].append(entry)

        # Clear journaling flag in-memory
        mark_task_journaled(
            spec_id,
            task_id,
            specs_dir,
            printer=None,
            spec_data=spec_data,
            save=False
        )

        journaled_tasks.append((task_id, entry))
        spec_data["last_updated"] = timestamp

    if dry_run:
        printer.warning("DRY RUN - No changes saved")
        printer.success(f"Would journal {len(journaled_tasks)}/{len(task_ids)} tasks")
        return len(journaled_tasks) > 0

    if not journaled_tasks:
        printer.warning("No journal entries were created")
        return False

    if not save_json_spec(spec_id, specs_dir, spec_data, backup=True):
        printer.error("Failed to save spec file with journal updates")
        return False

        printer.success(f"Journaled {len(journaled_tasks)}/{len(task_ids)} tasks")
        if skipped_tasks:
            printer.warning(f"Skipped {len(skipped_tasks)} task(s) - see logs for details")
    return True


def sync_metadata_from_state(
    spec_id: str,
    specs_dir: Optional[Path] = None,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> bool:
    """
    Automatically synchronize JSON metadata with hierarchy data.

    Updates:
    - last_updated: Current timestamp
    - progress_percentage: Calculated from hierarchy
    - status: "completed" when all tasks done, otherwise "active"
    - current_phase: ID of first in-progress phase

    Args:
        spec_id: Specification ID
        specs_dir: Optional specs directory (auto-detected if not provided)
        dry_run: If True, show changes without writing
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    # Find specs directory if not provided
    if specs_dir is None:
        specs_dir = find_specs_directory()
        if specs_dir is None:
            printer.error("Could not find specs directory")
            return False

    # Load JSON spec file
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        printer.error(f"Could not load spec file for {spec_id}")
        return False

    # Get or create metadata
    if "metadata" not in spec_data:
        spec_data["metadata"] = {}

    metadata = spec_data["metadata"]
    hierarchy = spec_data.get("hierarchy", {})
    spec_root = hierarchy.get("spec-root", {})

    updates_needed = {}

    # 1. Calculate and update progress percentage
    total_tasks = spec_root.get("total_tasks", 0)
    completed_tasks = spec_root.get("completed_tasks", 0)
    if total_tasks > 0:
        progress_pct = int((completed_tasks / total_tasks) * 100)
        if metadata.get("progress_percentage") != progress_pct:
            updates_needed["progress_percentage"] = progress_pct

    # 2. Update status based on completion
    new_status = "completed" if completed_tasks == total_tasks and total_tasks > 0 else "active"
    if metadata.get("status") != new_status:
        updates_needed["status"] = new_status

    # 3. Find current phase (first in-progress phase)
    current_phase = None
    for node_id, node_data in hierarchy.items():
        if node_data.get("type") == "phase" and node_data.get("status") == "in_progress":
            current_phase = node_id
            break

    if current_phase and metadata.get("current_phase") != current_phase:
        updates_needed["current_phase"] = current_phase

    # Check if any updates needed
    if not updates_needed:
        printer.info("Metadata is already up-to-date")
        return True

    # Show what will change
    printer.info("Metadata updates:")
    for key, new_value in updates_needed.items():
        old_value = metadata.get(key, "(not set)")
        printer.detail(f"  {key}: {old_value} → {new_value}")

    if dry_run:
        printer.warning("DRY RUN - No changes saved")
        return True

    try:
        # Apply updates
        for key, value in updates_needed.items():
            spec_data["metadata"][key] = value

        # Update last_updated timestamp
        spec_data["last_updated"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Save JSON spec file
        if not save_json_spec(spec_id, specs_dir, spec_data, backup=True):
            printer.error("Failed to save spec file")
            return False

        printer.success(f"Synchronized {len(updates_needed)} metadata field(s)")
        return True

    except Exception as e:
        printer.error(f"Failed to sync metadata: {e}")
        return False
