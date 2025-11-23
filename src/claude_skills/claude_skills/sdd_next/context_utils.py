"""
Helper utilities for building prepare-task context payloads.

Currently includes sibling discovery that surfaces the task executed
immediately before the active task to reduce redundant CLI calls.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def get_parent_context(spec_data: Dict[str, Any], task_id: str) -> Optional[Dict[str, Any]]:
    """
    Return contextual information about the parent node for a task.

    Args:
        spec_data: Loaded JSON spec dictionary.
        task_id: ID of the current task.

    Returns:
        Dictionary with parent metadata or None if the task has no parent.
        The dictionary contains:
            - id, title, type, status
            - description (metadata.description or metadata.note)
            - notes: list of note strings (if provided)
            - position_label: e.g., "2 of 3 subtasks"
            - children: list of {id, title, status}
    """
    if not spec_data:
        return None

    hierarchy = spec_data.get("hierarchy", {})
    task = hierarchy.get(task_id)
    if not task:
        return None

    parent_id = task.get("parent")
    if not parent_id:
        return None

    parent = hierarchy.get(parent_id)
    if not parent:
        return None

    parent_metadata = parent.get("metadata", {}) or {}
    description = (
        parent_metadata.get("description")
        or parent_metadata.get("note")
        or parent.get("description")
    )

    notes = []
    metadata_notes = parent_metadata.get("notes")
    if isinstance(metadata_notes, list):
        notes.extend(str(note) for note in metadata_notes if note)
    elif isinstance(metadata_notes, str):
        notes.append(metadata_notes)

    single_note = parent_metadata.get("note")
    if single_note and single_note not in notes:
        notes.append(single_note)

    children_ids = _get_sibling_ids(hierarchy, parent_id, parent)
    children_entries = [
        {
            "id": child_id,
            "title": hierarchy.get(child_id, {}).get("title", ""),
            "status": hierarchy.get(child_id, {}).get("status", ""),
        }
        for child_id in children_ids
    ]

    position_label = None
    if children_ids and task_id in children_ids:
        index = children_ids.index(task_id) + 1
        total = len(children_ids)
        label = "subtasks" if parent.get("type") == "task" else "children"
        position_label = f"{index} of {total} {label}"

    remaining_tasks = None
    completed_tasks = parent.get("completed_tasks")
    total_tasks = parent.get("total_tasks")
    if isinstance(completed_tasks, int) and isinstance(total_tasks, int):
        remaining_tasks = max(total_tasks - completed_tasks, 0)

    return {
        "id": parent_id,
        "title": parent.get("title", ""),
        "type": parent.get("type", ""),
        "status": parent.get("status", ""),
        "description": description,
        "notes": notes,
        "completed_tasks": completed_tasks,
        "total_tasks": total_tasks,
        "remaining_tasks": remaining_tasks,
        "position_label": position_label,
        "children": children_entries,
    }


def get_previous_sibling(spec_data: Dict[str, Any], task_id: str) -> Optional[Dict[str, Any]]:
    """
    Return metadata about the previous sibling for the given task.

    Args:
        spec_data: Loaded JSON spec dictionary.
        task_id: ID of the current task.

    Returns:
        Dictionary describing the previous sibling or None when the task is
        first in its group / has no siblings. The dictionary contains:
            - id, title, status, type
            - file_path, completed_at (from metadata)
            - journal_excerpt: Optional dict with timestamp, entry_type, summary
    """
    if not spec_data:
        return None

    hierarchy = spec_data.get("hierarchy", {})
    task = hierarchy.get(task_id)
    if not task:
        return None

    parent_id = task.get("parent")
    if not parent_id:
        return None

    parent = hierarchy.get(parent_id, {})
    sibling_ids = _get_sibling_ids(hierarchy, parent_id, parent)
    if not sibling_ids:
        return None

    try:
        task_index = sibling_ids.index(task_id)
    except ValueError:
        return None

    if task_index == 0:
        return None

    previous_id = sibling_ids[task_index - 1]
    previous_task = hierarchy.get(previous_id)
    if not previous_task:
        return None

    metadata = previous_task.get("metadata", {}) or {}
    journal_excerpt = _get_latest_journal_excerpt(
        spec_data.get("journal", []),
        previous_id,
    )

    return {
        "id": previous_id,
        "title": previous_task.get("title", ""),
        "status": previous_task.get("status", ""),
        "type": previous_task.get("type", ""),
        "file_path": metadata.get("file_path"),
        "completed_at": metadata.get("completed_at"),
        "journal_excerpt": journal_excerpt,
    }


def _get_sibling_ids(
    hierarchy: Dict[str, Dict[str, Any]],
    parent_id: str,
    parent_node: Dict[str, Any],
) -> List[str]:
    """Return sibling IDs for a parent, falling back to scanning the hierarchy."""
    children = parent_node.get("children", [])
    if isinstance(children, list) and children:
        return [child_id for child_id in children if child_id in hierarchy]

    return [
        node_id
        for node_id, node in hierarchy.items()
        if node.get("parent") == parent_id
    ]


def _get_latest_journal_excerpt(
    journal_entries: List[Dict[str, Any]],
    task_id: str,
    limit: int = None,
) -> Optional[Dict[str, Any]]:
    """
    Return the most recent journal entry for the given task.

    Args:
        journal_entries: List of journal entries
        task_id: Task identifier
        limit: Optional character limit for summary (None = no limit)

    Returns:
        Full journal entry by default (no truncation unless limit specified)
    """
    if not journal_entries:
        return None

    filtered = [
        entry for entry in journal_entries if entry.get("task_id") == task_id
    ]
    if not filtered:
        return None

    filtered.sort(key=lambda entry: entry.get("timestamp") or "", reverse=True)
    latest = filtered[0]
    summary = (latest.get("content") or "").strip()

    # Only truncate if limit explicitly provided
    if limit is not None and len(summary) > limit:
        summary = summary[:limit]

    return {
        "timestamp": latest.get("timestamp"),
        "entry_type": latest.get("entry_type"),
        "summary": summary,
    }


def get_phase_context(spec_data: Dict[str, Any], task_id: str) -> Optional[Dict[str, Any]]:
    """
    Return phase-level context for a task, including progress metrics.

    Args:
        spec_data: Loaded JSON spec dictionary.
        task_id: ID of the current task.

    Returns:
        Dictionary with phase data (id/title/status/progress) or None if the
        task does not belong to a phase.
    """
    if not spec_data:
        return None

    hierarchy = spec_data.get("hierarchy", {})
    task = hierarchy.get(task_id)
    if not task:
        return None

    phase_node = _find_phase_node(hierarchy, task)
    if not phase_node:
        return None

    phase_id = phase_node.get("id")
    phase_metadata = phase_node.get("metadata", {}) or {}
    summary = (
        phase_metadata.get("description")
        or phase_metadata.get("note")
        or phase_node.get("description")
    )
    blockers = phase_node.get("dependencies", {}).get("blocked_by", []) or []

    completed = phase_node.get("completed_tasks")
    total = phase_node.get("total_tasks")
    percentage = _calculate_percentage(completed, total)

    spec_root = hierarchy.get("spec-root", {})
    sequence_index = None
    phase_list = spec_root.get("children", [])
    if isinstance(phase_list, list) and phase_id in phase_list:
        sequence_index = phase_list.index(phase_id) + 1

    return {
        "id": phase_id,
        "title": phase_node.get("title", ""),
        "status": phase_node.get("status", ""),
        "sequence_index": sequence_index,
        "completed_tasks": completed,
        "total_tasks": total,
        "percentage": percentage,
        "summary": summary,
        "blockers": blockers,
    }


def _find_phase_node(hierarchy: Dict[str, Dict[str, Any]], task_node: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Walk ancestor chain to find the nearest phase node."""
    current = task_node
    while current:
        parent_id = current.get("parent")
        if not parent_id:
            return None
        parent = hierarchy.get(parent_id)
        if not parent:
            return None
        if parent.get("type") == "phase":
            return parent
        current = parent
    return None


def _calculate_percentage(completed: Optional[int], total: Optional[int]) -> Optional[int]:
    """Calculate completion percentage, handling None inputs."""
    if not isinstance(completed, int) or not isinstance(total, int) or total <= 0:
        return None
    return int((completed / total) * 100)


def collect_phase_task_ids(
    spec_data: Dict[str, Any],
    phase_id: Optional[str],
) -> List[str]:
    """Collect all task IDs that belong to the given phase (including nested groups)."""
    if not spec_data or not phase_id:
        return []

    hierarchy = spec_data.get("hierarchy", {})
    phase_node = hierarchy.get(phase_id)
    if not phase_node:
        return []

    task_ids: List[str] = []
    stack = list(phase_node.get("children", []) or [])

    while stack:
        node_id = stack.pop()
        node = hierarchy.get(node_id)
        if not node:
            continue

        node_type = node.get("type")
        if node_type in {"task", "subtask", "verify"}:
            task_ids.append(node_id)

        stack.extend(node.get("children", []) or [])

    return task_ids


def get_sibling_files(spec_data: Dict[str, Any], task_id: str) -> List[Dict[str, Any]]:
    """
    Return file metadata for siblings that have metadata.file_path entries.

    Args:
        spec_data: Loaded JSON spec dictionary.
        task_id: ID of the current task.

    Returns:
        List of dictionaries with:
            - task_id, title, status
            - file_path
            - last_modified_by (metadata or None)
            - last_activity (metadata or None)
    """
    if not spec_data:
        return []

    hierarchy = spec_data.get("hierarchy", {})
    task = hierarchy.get(task_id)
    if not task:
        return []

    parent_id = task.get("parent")
    if not parent_id:
        return []

    parent = hierarchy.get(parent_id, {})
    sibling_ids = _get_sibling_ids(hierarchy, parent_id, parent)
    entries: List[Dict[str, Any]] = []
    seen_paths = set()

    for sibling_id in sibling_ids:
        sibling = hierarchy.get(sibling_id)
        if not sibling:
            continue

        metadata = sibling.get("metadata", {}) or {}
        file_path = metadata.get("file_path")
        if not file_path or file_path in seen_paths:
            continue

        seen_paths.add(file_path)
        entries.append({
            "task_id": sibling_id,
            "title": sibling.get("title", ""),
            "status": sibling.get("status", ""),
            "file_path": file_path,
            "last_modified_by": metadata.get("last_modified_by"),
            "last_activity": metadata.get("last_activity") or metadata.get("completed_at"),
        })

    return entries


def get_task_journal_summary(
    spec_data: Dict[str, Any],
    task_id: str,
    max_entries: int = 3,
    summary_limit: int = 160,
) -> Dict[str, Any]:
    """
    Return a compact summary of journal entries for a task.

    Args:
        spec_data: Loaded JSON spec dictionary.
        task_id: Task identifier.
        max_entries: Maximum entries to include in summary.
        summary_limit: Max characters for entry summary.

    Returns:
        Dictionary with entry_count, last_entry_at, and entries[]
    """
    if not spec_data or not task_id:
        return {"entry_count": 0, "entries": []}

    journal = spec_data.get("journal", []) or []
    filtered = [
        entry for entry in journal
        if entry.get("task_id") == task_id
    ]

    if not filtered:
        return {"entry_count": 0, "entries": []}

    filtered.sort(key=lambda entry: entry.get("timestamp") or "", reverse=True)
    entries = []
    for entry in filtered[:max_entries]:
        summary = (entry.get("content") or "").strip()
        if summary_limit and len(summary) > summary_limit:
            summary = summary[:summary_limit]
        entries.append({
            "timestamp": entry.get("timestamp"),
            "entry_type": entry.get("entry_type"),
            "title": entry.get("title"),
            "summary": summary,
            "author": entry.get("author"),
        })

    return {
        "entry_count": len(filtered),
        "last_entry_at": filtered[0].get("timestamp"),
        "entries": entries,
    }


def get_dependency_details(
    spec_data: Dict[str, Any],
    task_id: str,
) -> Dict[str, Any]:
    """
    Get detailed dependency information for a task.

    Provides richer context than just task IDs by including titles,
    status, and file paths for all dependency relationships.

    Args:
        spec_data: Loaded JSON spec dictionary.
        task_id: Task identifier.

    Returns:
        Dictionary with detailed blocker, soft dependency, and blocks info:
        {
            "blocking": List[Dict],  # Tasks this blocks
            "blocked_by_details": List[Dict],  # Tasks blocking this
            "soft_depends": List[Dict]  # Soft dependencies
        }
    """
    if not spec_data or not task_id:
        return {
            "blocking": [],
            "blocked_by_details": [],
            "soft_depends": []
        }

    hierarchy = spec_data.get("hierarchy", {})
    task = hierarchy.get(task_id)

    if not task:
        return {
            "blocking": [],
            "blocked_by_details": [],
            "soft_depends": []
        }

    deps = task.get("dependencies", {})
    blocked_by = deps.get("blocked_by", [])
    depends = deps.get("depends", [])
    blocks = deps.get("blocks", [])

    def get_task_detail(dep_id: str) -> Optional[Dict[str, Any]]:
        """Extract task details for a dependency."""
        dep_task = hierarchy.get(dep_id)
        if not dep_task:
            return None
        return {
            "id": dep_id,
            "title": dep_task.get("title", ""),
            "status": dep_task.get("status", ""),
            "file_path": dep_task.get("metadata", {}).get("file_path", "")
        }

    result = {
        "blocking": [
            detail for detail in (get_task_detail(dep_id) for dep_id in blocks)
            if detail is not None
        ],
        "blocked_by_details": [
            detail for detail in (get_task_detail(dep_id) for dep_id in blocked_by)
            if detail is not None
        ],
        "soft_depends": [
            detail for detail in (get_task_detail(dep_id) for dep_id in depends)
            if detail is not None
        ]
    }

    return result


def get_plan_validation_context(
    spec_data: Dict[str, Any],
    task_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Extract plan validation context for tasks with execution plans.

    Args:
        spec_data: Loaded JSON spec dictionary.
        task_id: Task identifier.

    Returns:
        Plan validation context if task has a plan, None otherwise:
        {
            "has_plan": bool,
            "plan_items": List[Dict],  # step, description, status
            "completed_steps": int,
            "total_steps": int,
            "current_step": Optional[Dict]
        }
    """
    if not spec_data or not task_id:
        return None

    hierarchy = spec_data.get("hierarchy", {})
    task = hierarchy.get(task_id)

    if not task:
        return None

    metadata = task.get("metadata", {}) or {}
    plan = metadata.get("plan")

    if not plan or not isinstance(plan, list):
        return None

    completed_steps = sum(1 for item in plan if item.get("status") == "completed")
    total_steps = len(plan)

    # Find current step (first non-completed step)
    current_step = None
    for item in plan:
        if item.get("status") != "completed":
            current_step = {
                "step": item.get("step", 0),
                "description": item.get("description", ""),
                "status": item.get("status", "pending")
            }
            break

    return {
        "has_plan": True,
        "plan_items": [
            {
                "step": item.get("step", idx + 1),
                "description": item.get("description", ""),
                "status": item.get("status", "pending")
            }
            for idx, item in enumerate(plan)
        ],
        "completed_steps": completed_steps,
        "total_steps": total_steps,
        "current_step": current_step
    }


def get_enhanced_sibling_files(
    spec_data: Dict[str, Any],
    task_id: str,
) -> List[Dict[str, Any]]:
    """
    Get enhanced file metadata for siblings with journal-based change summaries.

    Extends get_sibling_files() by adding change summaries and line counts
    extracted from journal entries.

    Args:
        spec_data: Loaded JSON spec dictionary.
        task_id: Task identifier.

    Returns:
        List of dictionaries with enhanced file metadata:
        - task_id, title, status, file_path (from get_sibling_files)
        - last_modified_by, last_activity (from get_sibling_files)
        - changes_summary: Optional summary from journal
        - lines_changed: Optional line count from journal metadata
    """
    # Get base sibling files
    base_files = get_sibling_files(spec_data, task_id)

    if not base_files:
        return []

    # Enhance with journal data
    journal = spec_data.get("journal", []) or []
    enhanced_files = []

    for file_entry in base_files:
        sibling_task_id = file_entry.get("task_id")
        enhanced_entry = dict(file_entry)

        # Find most recent journal entry for this sibling
        sibling_journals = [
            entry for entry in journal
            if entry.get("task_id") == sibling_task_id
        ]

        if sibling_journals:
            sibling_journals.sort(key=lambda e: e.get("timestamp") or "", reverse=True)
            latest = sibling_journals[0]

            # Extract changes summary (first 200 chars)
            content = (latest.get("content") or "").strip()
            if content:
                enhanced_entry["changes_summary"] = content[:200]

            # Extract lines changed if present in metadata
            journal_metadata = latest.get("metadata", {})
            if journal_metadata and "lines_changed" in journal_metadata:
                enhanced_entry["lines_changed"] = journal_metadata["lines_changed"]

        enhanced_files.append(enhanced_entry)

    return enhanced_files
