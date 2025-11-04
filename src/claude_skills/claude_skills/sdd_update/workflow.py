"""Workflow utilities for orchestrating compound SDD update operations."""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from claude_skills.common.printer import PrettyPrinter
from claude_skills.common.spec import load_json_spec

from .journal import (
    add_journal_entry,
    add_revision_entry,
    mark_task_journaled,
    sync_metadata_from_state,
    _build_journal_entry,
    _ensure_journal_container,
)
from .status import update_task_status
from .time_tracking import track_time, calculate_time_from_timestamps
from .git_commit import (
    check_git_commit_readiness,
    generate_commit_message,
    stage_and_commit,
)
from claude_skills.common.git_metadata import show_commit_preview_and_wait, find_git_root
from claude_skills.common.git_config import load_git_config


def _get_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _journal_completed_parents(
    spec_id: str,
    task_id: str,
    specs_dir: Path,
    author: str,
    printer: Optional[PrettyPrinter]
) -> None:
    """
    Journal parent nodes (phases, groups) that were auto-completed.

    When a leaf task is completed, parent nodes may automatically transition
    to "completed" status via progress recalculation. This function walks up
    the parent chain and creates journal entries for any parents that were
    auto-completed and flagged with needs_journaling.

    Args:
        spec_id: Spec identifier
        task_id: ID of the task that was just completed
        specs_dir: Directory containing spec files
        author: Author name for journal entries
        printer: Optional printer for output
    """
    state = load_json_spec(spec_id, specs_dir)
    if not state:
        return

    hierarchy = state.get("hierarchy", {})
    current_id = task_id
    journaled_parents = []

    # Walk up the parent chain
    while current_id:
        node = hierarchy.get(current_id)
        if not node:
            break

        parent_id = node.get("parent")
        if not parent_id:
            break

        parent = hierarchy.get(parent_id)
        if (parent and
            parent.get("status") == "completed" and
            parent.get("metadata", {}).get("needs_journaling")):

            # Create journal entry for auto-completed parent
            parent_type = parent.get("type", "node").title()
            parent_title = parent.get("title", parent_id)

            add_journal_entry(
                spec_id=spec_id,
                title=f"{parent_type} Completed: {parent_title}",
                content=f"All child tasks in {parent.get('type', 'node')} {parent_id} have been completed.",
                task_id=parent_id,
                entry_type="status_change",
                author=author,
                specs_dir=specs_dir,
                dry_run=False,
                printer=None  # Suppress individual output to avoid clutter
            )
            journaled_parents.append(parent_id)

        current_id = parent_id

    if journaled_parents and printer:
        printer.info(f"Auto-journaled {len(journaled_parents)} parent node(s): {', '.join(journaled_parents)}")


def _derive_default_journal(
    task_id: str,
    task_title: str,
    actual_hours: Optional[float],
    note: Optional[str],
) -> Tuple[str, str]:
    title = f"Task Completed: {task_title or task_id}"

    parts = [f"Task {task_id} marked as completed."]
    if actual_hours is not None:
        parts.append(f"Actual hours: {actual_hours:.2f}")
    if note:
        parts.append(f"Note: {note}")

    content = " \n".join(parts)
    return title, content


def _bump_version(current_version: Optional[str], bump: str) -> Optional[str]:
    """Determine the next semantic version based on bump type."""

    if not current_version:
        current_version = "1.0"

    try:
        parts = [int(p) for p in str(current_version).split(".")]
    except ValueError:
        return None

    while len(parts) < 2:
        parts.append(0)

    major, minor = parts[0], parts[1]

    if bump == "major":
        major += 1
        minor = 0
    else:
        minor += 1

    return f"{major}.{minor}"


def _simulate_workflow(
    state: Dict[str, Any],
    task_id: str,
    actual_hours: Optional[float],
    note: Optional[str],
    journal_title: Optional[str],
    journal_content: Optional[str],
    journal_entry_type: str,
    author: str,
    revision_version: Optional[str],
    revision_changes: Optional[str],
) -> Dict[str, Any]:
    simulated = copy.deepcopy(state)

    hierarchy = simulated.get("hierarchy", {})
    task = hierarchy.get(task_id)
    if not task:
        return simulated

    metadata = task.setdefault("metadata", {})

    timestamp = _get_timestamp()

    # Handle actual_hours (manual or calculated)
    if actual_hours and actual_hours > 0:
        metadata["actual_hours"] = actual_hours
    else:
        # Simulate automatic calculation
        started_at = metadata.get("started_at")
        completed_at = timestamp  # Using simulated completion timestamp

        if started_at:
            calculated = calculate_time_from_timestamps(
                started_at,
                completed_at,
                printer=None  # Suppress output in simulation
            )
            if calculated is not None and calculated >= 0:
                metadata["actual_hours"] = calculated
    metadata["completed_at"] = timestamp
    metadata["needs_journaling"] = False
    if note:
        metadata["status_note"] = note

    task["status"] = "completed"

    # Fake journal entry
    journal_title_final, journal_content_final = journal_title, journal_content
    if not journal_title_final or not journal_content_final:
        journal_title_final, journal_content_final = _derive_default_journal(
            task_id,
            task.get("title", task_id),
            actual_hours,
            note,
        )

    entry, _ = _build_journal_entry(
        journal_title_final,
        journal_content_final,
        journal_entry_type,
        author,
        task_id,
    )

    _ensure_journal_container(simulated)
    simulated["journal"].append(entry)
    mark_task_journaled(
        spec_id=simulated.get("spec_id", ""),
        task_id=task_id,
        specs_dir=Path("."),
        printer=None,
        spec_data=simulated,
        save=False,
    )

    simulated["last_updated"] = timestamp

    metadata_section = simulated.setdefault("metadata", {})
    if revision_version and revision_changes:
        revisions = metadata_section.setdefault("revisions", [])
        revisions.append(
            {
                "version": revision_version,
                "date": timestamp,
                "author": author,
                "changes": revision_changes,
            }
        )
        metadata_section["version"] = revision_version

    # Local metadata sync (mirrors sync_metadata_from_state core logic)
    spec_root = hierarchy.get("spec-root", {})
    total_tasks = spec_root.get("total_tasks", 0)
    completed_tasks = spec_root.get("completed_tasks", 0)
    if total_tasks:
        metadata_section["progress_percentage"] = int((completed_tasks / total_tasks) * 100)
        metadata_section["status"] = (
            "completed" if completed_tasks == total_tasks else metadata_section.get("status", "active")
        )

    for node_id, node in hierarchy.items():
        if node.get("type") == "phase" and node.get("status") == "in_progress":
            metadata_section["current_phase"] = node_id
            break

    return simulated


def _calculate_diff(
    before: Dict[str, Any],
    after: Dict[str, Any],
    task_id: str,
) -> Dict[str, Any]:
    diff: Dict[str, Any] = {}

    before_task = before.get("hierarchy", {}).get(task_id, {})
    after_task = after.get("hierarchy", {}).get(task_id, {})

    if before_task.get("status") != after_task.get("status"):
        diff["status"] = {
            "before": before_task.get("status"),
            "after": after_task.get("status"),
        }

    before_meta = before_task.get("metadata", {})
    after_meta = after_task.get("metadata", {})

    for key in ["actual_hours", "completed_at", "status_note", "needs_journaling"]:
        if before_meta.get(key) != after_meta.get(key):
            diff.setdefault("task_metadata", {})[key] = {
                "before": before_meta.get(key),
                "after": after_meta.get(key),
            }

    before_spec_meta = before.get("metadata", {})
    after_spec_meta = after.get("metadata", {})

    metadata_changes = {}
    for key in sorted(set(before_spec_meta) | set(after_spec_meta)):
        if before_spec_meta.get(key) != after_spec_meta.get(key):
            metadata_changes[key] = {
                "before": before_spec_meta.get(key),
                "after": after_spec_meta.get(key),
            }
    if metadata_changes:
        diff["spec_metadata"] = metadata_changes

    before_journal = before.get("journal", [])
    after_journal = after.get("journal", [])
    if len(after_journal) > len(before_journal):
        new_entries = after_journal[len(before_journal) :]
        diff["journal_entries_added"] = new_entries

    return diff


def _print_diff(diff: Dict[str, Any], printer: PrettyPrinter) -> None:
    if not diff:
        printer.info("No observable changes")
        return

    printer.header("Planned Changes")

    if "status" in diff:
        printer.result("Status", f"{diff['status']['before']} → {diff['status']['after']}")

    for section in ["task_metadata", "spec_metadata"]:
        if section in diff:
            printer.info(f"\n{section.replace('_', ' ').title()}:")
            for key, change in diff[section].items():
                printer.detail(f"  {key}: {change['before']} → {change['after']}")

    if "journal_entries_added" in diff and diff["journal_entries_added"]:
        entry = diff["journal_entries_added"][0]
        printer.info("\nJournal Preview:")
        printer.detail(f"  Title: {entry.get('title')}")
        printer.detail(f"  Type: {entry.get('entry_type')}")
        printer.detail(f"  Content: {entry.get('content')}")


def complete_task_workflow(
    *,
    spec_id: str,
    task_id: str,
    specs_dir: Path,
    actual_hours: Optional[float] = None,
    note: Optional[str] = None,
    journal_title: Optional[str] = None,
    journal_content: Optional[str] = None,
    journal_entry_type: str = "status_change",
    author: str = "claude-code",
    bump: Optional[str] = None,
    version: Optional[str] = None,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None,
    show_diff: bool = False,
    output_format: str = "text",
) -> Optional[Dict[str, Any]]:
    """Complete a task with optional journaling, time tracking, and revision updates."""

    if not printer:
        printer = PrettyPrinter()

    state_before = load_json_spec(spec_id, specs_dir)
    if not state_before:
        printer.error("Failed to load spec state")
        return None

    hierarchy = state_before.get("hierarchy", {})
    task = hierarchy.get(task_id)
    if not task:
        printer.error(f"Task '{task_id}' not found")
        return None

    if bump and version:
        printer.error("Use either --bump or --version, not both")
        return None

    revision_version = None
    revision_changes = None

    if bump:
        revision_version = _bump_version(state_before.get("metadata", {}).get("version"), bump)
        if not revision_version:
            printer.error("Unable to bump version; existing version missing or invalid")
            return None
    elif version:
        revision_version = version

    # Handle journal title and content independently - don't overwrite user-provided values
    if not journal_title:
        journal_title_final = f"Task Completed: {task.get('title', task_id)}"
    else:
        journal_title_final = journal_title

    if not journal_content:
        # Derive default content if not provided
        parts = [f"Task {task_id} marked as completed."]
        if actual_hours is not None:
            parts.append(f"Actual hours: {actual_hours:.2f}")
        if note:
            parts.append(f"Note: {note}")
        journal_content_final = " \n".join(parts)
    else:
        journal_content_final = journal_content

    if revision_version:
        revision_changes = journal_title_final or f"Task {task_id} completed"
        if note:
            revision_changes = f"{revision_changes} ({note})"

    if dry_run:
        printer.info("Running in dry-run mode (no files will be modified)")
        simulated = _simulate_workflow(
            state_before,
            task_id,
            actual_hours,
            note,
            journal_title_final,
            journal_content_final,
            journal_entry_type,
            author,
            revision_version,
            revision_changes,
        )
        diff = _calculate_diff(state_before, simulated, task_id)
        if show_diff:
            _print_diff(diff, printer)

        return {
            "dry_run": True,
            "diff": diff,
            "task_id": task_id,
            "spec_id": spec_id,
        }

    # Actual execution path
    printer.action("Tracking updates...")

    if actual_hours:
        if actual_hours <= 0:
            printer.error("Actual hours must be positive")
            return None
        if not track_time(
            spec_id=spec_id,
            task_id=task_id,
            actual_hours=actual_hours,
            specs_dir=specs_dir,
            dry_run=False,
            printer=printer,
        ):
            return None

    if not update_task_status(
        spec_id=spec_id,
        task_id=task_id,
        new_status="completed",
        specs_dir=specs_dir,
        note=note,
        dry_run=False,
        printer=printer,
    ):
        return None

    # Automatic time calculation if actual_hours not manually provided
    if not actual_hours:
        # Reload spec to get updated timestamps from update_task_status()
        updated_state = load_json_spec(spec_id, specs_dir)
        if updated_state:
            updated_task = updated_state.get("hierarchy", {}).get(task_id, {})
            task_metadata = updated_task.get("metadata", {})

            started_at = task_metadata.get("started_at")
            completed_at = task_metadata.get("completed_at")

            if started_at and completed_at:
                # Calculate time from timestamps
                calculated_hours = calculate_time_from_timestamps(
                    started_at,
                    completed_at,
                    printer=printer
                )

                if calculated_hours is not None and calculated_hours >= 0:
                    # Store calculated time
                    if not track_time(
                        spec_id=spec_id,
                        task_id=task_id,
                        actual_hours=calculated_hours,
                        specs_dir=specs_dir,
                        dry_run=False,
                        printer=printer,
                    ):
                        printer.warning(f"Failed to store calculated time ({calculated_hours:.3f}h)")
                    else:
                        printer.info(f"Automatically calculated time: {calculated_hours:.3f}h")
                else:
                    printer.warning("Time calculation returned invalid result")
            else:
                # Missing timestamps - this is expected if task was never marked in_progress
                if not started_at:
                    printer.info("No started_at timestamp found; task may not have been marked in_progress")

    if not add_journal_entry(
        spec_id=spec_id,
        title=journal_title_final,
        content=journal_content_final,
        task_id=task_id,
        entry_type=journal_entry_type,
        author=author,
        specs_dir=specs_dir,
        dry_run=False,
        printer=printer,
    ):
        return None

    if revision_version and revision_changes:
        if not add_revision_entry(
            spec_id=spec_id,
            version=revision_version,
            changes=revision_changes,
            author=author,
            specs_dir=specs_dir,
            dry_run=False,
            printer=printer,
        ):
            return None

    if not sync_metadata_from_state(
        spec_id=spec_id,
        specs_dir=specs_dir,
        dry_run=False,
        printer=printer,
    ):
        return None

    # Auto-journal parent nodes that were completed
    _journal_completed_parents(
        spec_id=spec_id,
        task_id=task_id,
        specs_dir=specs_dir,
        author=author,
        printer=printer
    )

    # Git commit integration (after task completion)
    # Check if git commit should be offered based on commit cadence preference
    from claude_skills.common.paths import find_spec_file
    spec_path = find_spec_file(spec_id, specs_dir)
    if not spec_path:
        printer.warning(f"Could not locate spec file for {spec_id} to save commit metadata")
        return None

    updated_spec = load_json_spec(spec_id, specs_dir)
    if updated_spec:
        commit_info = check_git_commit_readiness(
            spec_data=updated_spec,
            spec_path=spec_path,
            event_type="task"
        )

        if commit_info:
            printer.info("Creating git commit for task completion...")

            # Generate commit message
            task_title = task.get('title', task_id)
            commit_message = generate_commit_message(task_id, task_title)

            # Check if preview should be shown before commit
            repo_root = commit_info['repo_root']
            git_config = load_git_config(repo_root)
            show_preview = git_config.get('file_staging', {}).get('show_before_commit', True)

            if show_preview:
                # Show preview of changes before staging/committing
                printer.info("Showing commit preview (configured via file_staging.show_before_commit)...")
                show_commit_preview_and_wait(
                    repo_root=repo_root,
                    spec_id=spec_id,
                    task_id=task_id,
                    printer=printer
                )

            # Stage and commit changes
            success, commit_sha, error_msg = stage_and_commit(
                repo_root=commit_info['repo_root'],
                commit_message=commit_message
            )

            if success and commit_sha:
                printer.success(f"Created commit: {commit_sha[:8]}")

                # Save updated spec
                try:
                    with open(spec_path, 'w') as f:
                        json.dump(updated_spec, f, indent=2)
                    printer.info("Saved updated spec")
                except Exception as e:
                    printer.warning(f"Failed to save commit metadata to spec: {e}")
            elif error_msg:
                # Non-blocking failure - log warning but continue
                printer.warning(f"Git commit failed: {error_msg}")

    # Load final state for diff / reporting
    state_after = load_json_spec(spec_id, specs_dir)
    if not state_after:
        printer.warning("Unable to reload state after updates")
        return {
            "dry_run": False,
            "task_id": task_id,
            "spec_id": spec_id,
        }

    diff = _calculate_diff(state_before, state_after, task_id)
    if show_diff:
        _print_diff(diff, printer)

    return {
        "dry_run": False,
        "task_id": task_id,
        "spec_id": spec_id,
        "diff": diff,
    }
