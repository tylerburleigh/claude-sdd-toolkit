"""Auto-fix helpers for the `sdd-validate` CLI.

This module translates validation findings into concrete fix actions that can
be previewed or applied directly to SDD spec JSON files.
"""

from __future__ import annotations

import re
import copy
from dataclasses import asdict, dataclass, field
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set

from claude_skills.common import (
    backup_json_spec,
    find_specs_directory,
    recalculate_progress,
    save_json_spec,
    validate_status,
    validate_spec_hierarchy,
)
from claude_skills.common.validation import EnhancedError, JsonSpecValidationResult
from claude_skills.sdd_validate.formatting import normalize_validation_result


@dataclass
class FixAction:
    """Represents a candidate auto-fix operation."""

    id: str
    description: str
    category: str
    severity: str
    auto_apply: bool
    preview: str
    apply: Callable[[Dict[str, Any]], None]


@dataclass
class FixReport:
    """Outcome of applying a set of fix actions."""

    spec_path: Optional[str] = None
    backup_path: Optional[str] = None
    applied_actions: List[FixAction] = field(default_factory=list)
    skipped_actions: List[FixAction] = field(default_factory=list)
    post_validation: Optional[Dict[str, Any]] = None
    before_state: Optional[Dict[str, Any]] = None  # State before fixes
    after_state: Optional[Dict[str, Any]] = None  # State after fixes


def collect_fix_actions(result: JsonSpecValidationResult) -> List[FixAction]:
    """Translate a validation result into fix actions."""

    actions: List[FixAction] = []
    seen_ids: Set[str] = set()

    enhanced: Sequence[EnhancedError] = getattr(result, "enhanced_errors", []) or []
    spec_data = result.spec_data or {}

    # All available builders
    all_builders = [
        _build_counts_action,
        _build_leaf_count_action,
        _build_metadata_action,
        _build_verification_type_action,
        _build_hierarchy_action,
        _build_orphan_action,
        _build_date_action,
        _build_status_action,
        _build_missing_fields_action,
        _build_empty_title_action,
        _build_invalid_type_action,
        _build_bidirectional_deps_action,
        _build_missing_deps_structure_action,
    ]

    for error in enhanced:
        if not error.auto_fixable:
            continue

        # Try all builders to see which ones apply
        for builder in all_builders:
            try:
                action = builder(error, spec_data)
                if action and action.id not in seen_ids:
                    actions.append(action)
                    seen_ids.add(action.id)
            except Exception:
                # Builder doesn't apply to this error, continue
                continue

    return actions


def apply_fix_actions(
    actions: Iterable[FixAction],
    spec_path: str,
    *,
    dry_run: bool = False,
    create_backup: bool = True,
    capture_diff: bool = False,
) -> FixReport:
    """Apply fix actions to a spec file."""
    report = FixReport(spec_path=spec_path)

    if dry_run:
        report.skipped_actions.extend(actions)
        return report

    try:
        with open(spec_path, "r") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return report

    # Capture before state if diff requested
    if capture_diff:
        report.before_state = copy.deepcopy(data)

    if create_backup:
        # Try using backup_json_spec first (for standard spec directory structure)
        backup = backup_json_spec(Path(spec_path).stem, find_specs_directory(str(spec_path)) or Path(spec_path).parent)

        # If that fails (e.g., file not in active/completed/archived), create backup directly
        if not backup:
            try:
                import shutil
                backup_path = Path(spec_path).with_suffix(Path(spec_path).suffix + ".backup")
                shutil.copy2(spec_path, backup_path)
                backup = backup_path
            except (IOError, OSError):
                pass

        if backup:
            report.backup_path = str(backup)

    for action in actions:
        try:
            action.apply(data)
            report.applied_actions.append(action)
        except Exception:
            report.skipped_actions.append(action)

    if report.applied_actions:
        recalculate_progress(data)

    # Capture after state if diff requested
    if capture_diff:
        report.after_state = copy.deepcopy(data)

    post_validation = validate_spec_hierarchy(data)
    report.post_validation = asdict(normalize_validation_result(post_validation))

    save_json_spec(Path(spec_path).stem, find_specs_directory(str(spec_path)) or Path(spec_path).parent, data, backup=False, validate=False)

    return report


def _build_counts_action(error: EnhancedError, spec_data: Dict[str, Any]) -> Optional[FixAction]:
    hierarchy = spec_data.get("hierarchy") or {}
    if not hierarchy:
        return None

    description = error.suggested_fix or "Recalculate task rollups"
    preview = "Recalculate total/completed task rollups across the hierarchy"

    def apply(data: Dict[str, Any]) -> None:
        recalculate_progress(data)

    return FixAction(
        id="counts.recalculate",
        description=description,
        category="counts",
        severity=error.severity,
        auto_apply=True,
        preview=preview,
        apply=apply,
    )


def _build_metadata_action(error: EnhancedError, spec_data: Dict[str, Any]) -> Optional[FixAction]:
    hierarchy = spec_data.get("hierarchy") or {}
    node_id = _resolve_node_id(error, hierarchy)
    if not node_id:
        return None

    node = hierarchy.get(node_id)
    if not node:
        return None

    preview = f"Ensure metadata defaults for {node_id}"

    def apply(data: Dict[str, Any]) -> None:
        hierarchy = data.setdefault("hierarchy", {})
        node = hierarchy.get(node_id)
        if not node:
            return
        metadata = node.setdefault("metadata", {})
        node_type = node.get("type")
        if node_type == "task":
            metadata.setdefault("file_path", f"{node_id}.md")
        if node_type == "verify":
            metadata.setdefault("verification_type", "manual")
            metadata.setdefault("command", "")
            metadata.setdefault("expected", "")

    return FixAction(
        id=f"metadata.ensure:{node_id}",
        description=error.suggested_fix or f"Add metadata defaults for {node_id}",
        category="metadata",
        severity=error.severity,
        auto_apply=True,
        preview=preview,
        apply=apply,
    )


_PARENT_CHILD_RE = re.compile(
    r"'(?P<parent>[^']+)' lists '(?P<child>[^']+)' as child, but '(?P=child)' has parent='(?P<actual>[^']*)'"
)


def _build_hierarchy_action(error: EnhancedError, spec_data: Dict[str, Any]) -> Optional[FixAction]:
    hierarchy = spec_data.get("hierarchy") or {}
    match = _PARENT_CHILD_RE.search(error.message)
    if not match:
        return None

    parent_id = match.group("parent")
    child_id = match.group("child")

    if parent_id not in hierarchy or child_id not in hierarchy:
        return None

    preview = f"Align {child_id} parent reference with {parent_id}"

    def apply(data: Dict[str, Any]) -> None:
        hierarchy = data.setdefault("hierarchy", {})
        parent = hierarchy.get(parent_id)
        child = hierarchy.get(child_id)
        if not parent or not child:
            return
        children = parent.setdefault("children", [])
        if child_id not in children:
            children.append(child_id)
        child["parent"] = parent_id

    return FixAction(
        id=f"hierarchy.align:{parent_id}->{child_id}",
        description=error.suggested_fix or preview,
        category="hierarchy",
        severity=error.severity,
        auto_apply=True,
        preview=preview,
        apply=apply,
    )


def _build_date_action(error: EnhancedError, spec_data: Dict[str, Any]) -> Optional[FixAction]:
    fields = [field for field in ("generated", "last_updated") if field in error.message]
    if not fields:
        fields = ["generated", "last_updated"]

    preview = f"Normalize timestamp fields: {', '.join(fields)}"

    def apply(data: Dict[str, Any]) -> None:
        for field in fields:
            value = data.get(field)
            normalized = _normalize_timestamp(value)
            if normalized:
                data[field] = normalized

    return FixAction(
        id=f"structure.normalize_dates:{'+'.join(fields)}",
        description=error.suggested_fix or preview,
        category="structure",
        severity=error.severity,
        auto_apply=True,
        preview=preview,
        apply=apply,
    )


def _build_status_action(error: EnhancedError, spec_data: Dict[str, Any]) -> Optional[FixAction]:
    hierarchy = spec_data.get("hierarchy") or {}
    node_id = _resolve_node_id(error, hierarchy)
    if not node_id:
        return None

    node = hierarchy.get(node_id)
    if not node:
        return None

    old_status = node.get("status", "")
    new_status = _normalize_status(old_status)
    if new_status == old_status and validate_status(old_status):
        return None

    preview = f"Normalize status for {node_id}: {old_status!r} -> {new_status!r}"

    def apply(data: Dict[str, Any]) -> None:
        hierarchy = data.setdefault("hierarchy", {})
        node = hierarchy.get(node_id)
        if not node:
            return
        node["status"] = _normalize_status(node.get("status"))

    return FixAction(
        id=f"status.normalize:{node_id}",
        description=error.suggested_fix or preview,
        category="node",
        severity=error.severity,
        auto_apply=True,
        preview=preview,
        apply=apply,
    )


def _normalize_timestamp(value: Any) -> Optional[str]:
    if not value:
        return None

    text = str(value).strip()
    candidate = text.replace("Z", "")

    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            dt = datetime.strptime(candidate, fmt)
            return dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
        except ValueError:
            continue

    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    except ValueError:
        return None


def _resolve_node_id(error: EnhancedError, hierarchy: Dict[str, Any]) -> Optional[str]:
    if error.location and error.location in hierarchy:
        return error.location

    for candidate in re.findall(r"'([^']+)'", error.message):
        if candidate in hierarchy:
            return candidate
    return None


def _normalize_status(value: Any) -> str:
    if not value:
        return "pending"

    text = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    mapping = {
        "inprogress": "in_progress",
        "in__progress": "in_progress",
        "todo": "pending",
        "to_do": "pending",
        "complete": "completed",
        "done": "completed",
    }
    text = mapping.get(text, text)

    if text in {"pending", "in_progress", "completed", "blocked"}:
        return text

    return "pending"


def _build_missing_fields_action(error: EnhancedError, spec_data: Dict[str, Any]) -> Optional[FixAction]:
    """Add missing required node fields with sensible defaults."""
    hierarchy = spec_data.get("hierarchy") or {}
    node_id = _resolve_node_id(error, hierarchy)
    if not node_id:
        return None

    node = hierarchy.get(node_id)
    if not node:
        return None

    # Determine which fields are missing
    required_fields = ['type', 'title', 'status', 'parent', 'children', 'total_tasks', 'completed_tasks', 'metadata']
    missing_fields = [f for f in required_fields if f not in node]

    if not missing_fields:
        return None

    preview = f"Add missing fields to {node_id}: {', '.join(missing_fields)}"

    def apply(data: Dict[str, Any]) -> None:
        hierarchy = data.setdefault("hierarchy", {})
        node = hierarchy.get(node_id)
        if not node:
            return

        # Add defaults for missing fields
        if 'type' not in node:
            node['type'] = 'task'  # Default to task
        if 'title' not in node:
            node['title'] = node_id.replace('-', ' ').title()
        if 'status' not in node:
            node['status'] = 'pending'
        if 'parent' not in node:
            node['parent'] = 'spec-root'  # Attach to root by default
        if 'children' not in node:
            node['children'] = []
        if 'total_tasks' not in node:
            node['total_tasks'] = 1 if node.get('type') in {'task', 'subtask', 'verify'} else 0
        if 'completed_tasks' not in node:
            node['completed_tasks'] = 0
        if 'metadata' not in node:
            node['metadata'] = {}

    return FixAction(
        id=f"node.add_missing_fields:{node_id}",
        description=error.suggested_fix or preview,
        category="node",
        severity=error.severity,
        auto_apply=True,
        preview=preview,
        apply=apply,
    )


def _build_empty_title_action(error: EnhancedError, spec_data: Dict[str, Any]) -> Optional[FixAction]:
    """Generate title from node ID for nodes with empty titles."""
    hierarchy = spec_data.get("hierarchy") or {}
    node_id = _resolve_node_id(error, hierarchy)
    if not node_id:
        return None

    node = hierarchy.get(node_id)
    if not node or node.get("title", "").strip():
        return None

    generated_title = node_id.replace('-', ' ').replace('_', ' ').title()
    preview = f"Generate title for {node_id}: '{generated_title}'"

    def apply(data: Dict[str, Any]) -> None:
        hierarchy = data.setdefault("hierarchy", {})
        node = hierarchy.get(node_id)
        if not node:
            return
        node['title'] = node_id.replace('-', ' ').replace('_', ' ').title()

    return FixAction(
        id=f"node.generate_title:{node_id}",
        description=error.suggested_fix or preview,
        category="node",
        severity=error.severity,
        auto_apply=True,
        preview=preview,
        apply=apply,
    )


def _build_invalid_type_action(error: EnhancedError, spec_data: Dict[str, Any]) -> Optional[FixAction]:
    """Normalize invalid node types."""
    hierarchy = spec_data.get("hierarchy") or {}
    node_id = _resolve_node_id(error, hierarchy)
    if not node_id:
        return None

    node = hierarchy.get(node_id)
    if not node:
        return None

    old_type = node.get("type", "")
    # Try to normalize common variations
    normalized_type = _normalize_node_type(old_type)

    preview = f"Normalize type for {node_id}: {old_type!r} -> {normalized_type!r}"

    def apply(data: Dict[str, Any]) -> None:
        hierarchy = data.setdefault("hierarchy", {})
        node = hierarchy.get(node_id)
        if not node:
            return
        node['type'] = _normalize_node_type(node.get('type', ''))

    return FixAction(
        id=f"node.normalize_type:{node_id}",
        description=error.suggested_fix or preview,
        category="node",
        severity=error.severity,
        auto_apply=True,
        preview=preview,
        apply=apply,
    )


def _normalize_node_type(value: Any) -> str:
    """Normalize node type to valid value."""
    if not value:
        return "task"

    text = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    mapping = {
        "tasks": "task",
        "sub_task": "subtask",
        "verification": "verify",
        "validate": "verify",
    }
    text = mapping.get(text, text)

    valid_types = {'spec', 'phase', 'group', 'task', 'subtask', 'verify'}
    if text in valid_types:
        return text

    return "task"  # Default fallback


def _build_verification_type_action(error: EnhancedError, spec_data: Dict[str, Any]) -> Optional[FixAction]:
    """Fix verification_type for verify nodes."""
    hierarchy = spec_data.get("hierarchy") or {}
    node_id = _resolve_node_id(error, hierarchy)
    if not node_id:
        return None

    node = hierarchy.get(node_id)
    if not node or node.get("type") != "verify":
        return None

    preview = f"Set verification_type to 'manual' for {node_id}"

    def apply(data: Dict[str, Any]) -> None:
        hierarchy = data.setdefault("hierarchy", {})
        node = hierarchy.get(node_id)
        if not node:
            return
        metadata = node.setdefault("metadata", {})
        if "verification_type" not in metadata or metadata["verification_type"] not in {"auto", "manual"}:
            metadata["verification_type"] = "manual"  # Safe default

    return FixAction(
        id=f"metadata.fix_verification_type:{node_id}",
        description=error.suggested_fix or preview,
        category="metadata",
        severity=error.severity,
        auto_apply=True,
        preview=preview,
        apply=apply,
    )


def _build_bidirectional_deps_action(error: EnhancedError, spec_data: Dict[str, Any]) -> Optional[FixAction]:
    """Synchronize bidirectional dependency relationships."""
    import re
    hierarchy = spec_data.get("hierarchy") or {}

    # Parse the error message to extract node IDs and relationship type
    # Format: "Node 'A' blocks 'B', but 'B' doesn't list 'A' in blocked_by"
    blocks_pattern = re.compile(r"'([^']+)' blocks '([^']+)'")
    blocked_by_pattern = re.compile(r"'([^']+)' blocked_by '([^']+)'")

    match = blocks_pattern.search(error.message)
    if match:
        blocker_id = match.group(1)
        blocked_id = match.group(2)
        dep_type = "blocks"
    else:
        match = blocked_by_pattern.search(error.message)
        if match:
            blocked_id = match.group(1)
            blocker_id = match.group(2)
            dep_type = "blocked_by"
        else:
            return None

    if blocker_id not in hierarchy or blocked_id not in hierarchy:
        return None

    preview = f"Sync bidirectional dependency: {blocker_id} blocks {blocked_id}"

    def apply(data: Dict[str, Any]) -> None:
        hierarchy = data.setdefault("hierarchy", {})
        blocker = hierarchy.get(blocker_id)
        blocked = hierarchy.get(blocked_id)
        if not blocker or not blocked:
            return

        # Ensure dependencies dicts exist
        blocker_deps = blocker.setdefault("dependencies", {})
        blocked_deps = blocked.setdefault("dependencies", {})

        # Sync blocks/blocked_by
        blocks_list = blocker_deps.setdefault("blocks", [])
        if blocked_id not in blocks_list:
            blocks_list.append(blocked_id)

        blocked_by_list = blocked_deps.setdefault("blocked_by", [])
        if blocker_id not in blocked_by_list:
            blocked_by_list.append(blocker_id)

    return FixAction(
        id=f"dependency.sync_bidirectional:{blocker_id}-{blocked_id}",
        description=error.suggested_fix or preview,
        category="dependency",
        severity=error.severity,
        auto_apply=True,
        preview=preview,
        apply=apply,
    )


def _build_missing_deps_structure_action(error: EnhancedError, spec_data: Dict[str, Any]) -> Optional[FixAction]:
    """Create dependencies dict structure."""
    hierarchy = spec_data.get("hierarchy") or {}
    node_id = _resolve_node_id(error, hierarchy)
    if not node_id:
        return None

    node = hierarchy.get(node_id)
    if not node:
        return None

    preview = f"Create dependencies structure for {node_id}"

    def apply(data: Dict[str, Any]) -> None:
        hierarchy = data.setdefault("hierarchy", {})
        node = hierarchy.get(node_id)
        if not node:
            return
        if not isinstance(node.get("dependencies"), dict):
            node["dependencies"] = {
                "blocks": [],
                "blocked_by": [],
                "depends": [],
            }

    return FixAction(
        id=f"dependency.create_structure:{node_id}",
        description=error.suggested_fix or preview,
        category="dependency",
        severity=error.severity,
        auto_apply=True,
        preview=preview,
        apply=apply,
    )


def _build_leaf_count_action(error: EnhancedError, spec_data: Dict[str, Any]) -> Optional[FixAction]:
    """Fix leaf node total_tasks to be 1."""
    hierarchy = spec_data.get("hierarchy") or {}
    node_id = _resolve_node_id(error, hierarchy)
    if not node_id:
        return None

    node = hierarchy.get(node_id)
    if not node or node.get("type") not in {"task", "subtask", "verify"}:
        return None

    current_value = node.get("total_tasks", 0)
    preview = f"Set total_tasks=1 for leaf node {node_id} (currently {current_value})"

    def apply(data: Dict[str, Any]) -> None:
        hierarchy = data.setdefault("hierarchy", {})
        node = hierarchy.get(node_id)
        if not node:
            return
        if node.get("type") in {"task", "subtask", "verify"} and not node.get("children"):
            node["total_tasks"] = 1

    return FixAction(
        id=f"counts.fix_leaf_count:{node_id}",
        description=error.suggested_fix or preview,
        category="counts",
        severity=error.severity,
        auto_apply=True,
        preview=preview,
        apply=apply,
    )


def _build_orphan_action(error: EnhancedError, spec_data: Dict[str, Any]) -> Optional[FixAction]:
    """Handle orphaned nodes by attaching to spec-root."""
    import re
    hierarchy = spec_data.get("hierarchy") or {}

    # Extract orphaned node IDs from error message
    # Format: "Found N orphaned node(s) not reachable from spec-root: node1, node2, ..."
    match = re.search(r"not reachable from spec-root:\s*(.+)$", error.message)
    if not match:
        return None

    orphan_list_str = match.group(1)
    orphan_ids = [nid.strip() for nid in orphan_list_str.split(",")]

    if not orphan_ids:
        return None

    preview = f"Attach {len(orphan_ids)} orphaned node(s) to spec-root"

    def apply(data: Dict[str, Any]) -> None:
        hierarchy = data.setdefault("hierarchy", {})
        spec_root = hierarchy.get("spec-root")
        if not spec_root:
            return

        root_children = spec_root.setdefault("children", [])

        for orphan_id in orphan_ids:
            if orphan_id in hierarchy:
                orphan_node = hierarchy[orphan_id]
                # Attach to spec-root
                orphan_node["parent"] = "spec-root"
                if orphan_id not in root_children:
                    root_children.append(orphan_id)

    return FixAction(
        id=f"hierarchy.attach_orphans:{len(orphan_ids)}",
        description=error.suggested_fix or preview,
        category="hierarchy",
        severity=error.severity,
        auto_apply=True,
        preview=preview,
        apply=apply,
    )


_FALLBACK_BUILDERS: Dict[str, Callable[[EnhancedError, Dict[str, Any]], Optional[FixAction]]] = {
    "counts": _build_counts_action,
    "metadata": _build_metadata_action,
    "hierarchy": _build_hierarchy_action,
    "structure": _build_date_action,
    "node": _build_status_action,
    "dependency": _build_bidirectional_deps_action,
}

