"""Diff computation and formatting for before/after spec fix comparisons."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class FieldChange:
    """Represents a single field change."""
    location: str  # node_id or "root"
    field_path: str  # e.g., "status", "metadata.file_path", "dependencies.blocks"
    old_value: Any
    new_value: Any
    change_type: str  # "added", "removed", "modified"


@dataclass
class DiffReport:
    """Complete diff report between before and after states."""
    changes: List[FieldChange] = field(default_factory=list)
    nodes_added: List[str] = field(default_factory=list)
    nodes_removed: List[str] = field(default_factory=list)
    total_changes: int = 0


def compute_diff(before: Dict[str, Any], after: Dict[str, Any]) -> DiffReport:
    """
    Compute differences between before and after spec states.

    Args:
        before: Spec data before fixes
        after: Spec data after fixes

    Returns:
        DiffReport with all detected changes
    """
    report = DiffReport()

    # Check top-level field changes
    for field in ["spec_id", "title", "version", "generated", "last_updated"]:
        before_val = before.get(field)
        after_val = after.get(field)

        if before_val != after_val:
            if before_val is None:
                change_type = "added"
            elif after_val is None:
                change_type = "removed"
            else:
                change_type = "modified"

            report.changes.append(FieldChange(
                location="root",
                field_path=field,
                old_value=before_val,
                new_value=after_val,
                change_type=change_type,
            ))

    # Check hierarchy changes
    before_hierarchy = before.get("hierarchy", {})
    after_hierarchy = after.get("hierarchy", {})

    # Find added/removed nodes
    before_nodes = set(before_hierarchy.keys())
    after_nodes = set(after_hierarchy.keys())

    report.nodes_added = list(after_nodes - before_nodes)
    report.nodes_removed = list(before_nodes - after_nodes)

    # Check changes in existing nodes
    common_nodes = before_nodes & after_nodes
    for node_id in sorted(common_nodes):
        before_node = before_hierarchy[node_id]
        after_node = after_hierarchy[node_id]

        node_changes = _compare_nodes(node_id, before_node, after_node)
        report.changes.extend(node_changes)

    report.total_changes = len(report.changes) + len(report.nodes_added) + len(report.nodes_removed)

    return report


def _compare_nodes(node_id: str, before: Dict[str, Any], after: Dict[str, Any]) -> List[FieldChange]:
    """Compare two node dicts and return list of changes."""
    changes = []

    # Simple fields
    simple_fields = ["type", "title", "status", "parent", "total_tasks", "completed_tasks"]
    for field in simple_fields:
        before_val = before.get(field)
        after_val = after.get(field)

        if before_val != after_val:
            if before_val is None:
                change_type = "added"
            elif after_val is None:
                change_type = "removed"
            else:
                change_type = "modified"

            changes.append(FieldChange(
                location=node_id,
                field_path=field,
                old_value=before_val,
                new_value=after_val,
                change_type=change_type,
            ))

    # Children list
    before_children = before.get("children", [])
    after_children = after.get("children", [])
    if before_children != after_children:
        changes.append(FieldChange(
            location=node_id,
            field_path="children",
            old_value=before_children,
            new_value=after_children,
            change_type="modified",
        ))

    # Metadata changes
    before_metadata = before.get("metadata", {})
    after_metadata = after.get("metadata", {})
    metadata_changes = _compare_dicts(node_id, "metadata", before_metadata, after_metadata)
    changes.extend(metadata_changes)

    # Dependencies changes
    before_deps = before.get("dependencies", {})
    after_deps = after.get("dependencies", {})
    dep_changes = _compare_dicts(node_id, "dependencies", before_deps, after_deps)
    changes.extend(dep_changes)

    return changes


def _compare_dicts(node_id: str, dict_name: str, before: Dict[str, Any], after: Dict[str, Any]) -> List[FieldChange]:
    """Compare two dictionaries and return field changes."""
    changes = []

    all_keys = set(before.keys()) | set(after.keys())

    for key in sorted(all_keys):
        before_val = before.get(key)
        after_val = after.get(key)

        if before_val != after_val:
            if before_val is None:
                change_type = "added"
            elif after_val is None:
                change_type = "removed"
            else:
                change_type = "modified"

            changes.append(FieldChange(
                location=node_id,
                field_path=f"{dict_name}.{key}",
                old_value=before_val,
                new_value=after_val,
                change_type=change_type,
            ))

    return changes


def format_diff_markdown(report: DiffReport, spec_id: str = "unknown") -> str:
    """Format diff report as markdown."""
    lines = [
        "# Fix Diff Report",
        "",
        f"**Spec ID:** {spec_id}",
        f"**Total Changes:** {report.total_changes}",
        "",
    ]

    if not report.total_changes:
        lines.append("No changes detected.")
        return "\n".join(lines)

    # Group changes by location
    changes_by_location: Dict[str, List[FieldChange]] = {}
    for change in report.changes:
        if change.location not in changes_by_location:
            changes_by_location[change.location] = []
        changes_by_location[change.location].append(change)

    # Show changes
    if changes_by_location:
        lines.append("## Changes")
        lines.append("")

        for location in sorted(changes_by_location.keys()):
            changes = changes_by_location[location]
            lines.append(f"### {location}")
            lines.append("")

            for change in changes:
                if change.change_type == "added":
                    lines.append(f"- **{change.field_path}:** (added)")
                    lines.append(f"  - New value: `{_format_value(change.new_value)}`")
                elif change.change_type == "removed":
                    lines.append(f"- **{change.field_path}:** (removed)")
                    lines.append(f"  - Old value: `{_format_value(change.old_value)}`")
                else:  # modified
                    lines.append(f"- **{change.field_path}:**")
                    lines.append(f"  - Before: `{_format_value(change.old_value)}`")
                    lines.append(f"  - After: `{_format_value(change.new_value)}`")

            lines.append("")

    # Show added/removed nodes
    if report.nodes_added:
        lines.append("## Nodes Added")
        lines.append("")
        for node_id in sorted(report.nodes_added):
            lines.append(f"- {node_id}")
        lines.append("")

    if report.nodes_removed:
        lines.append("## Nodes Removed")
        lines.append("")
        for node_id in sorted(report.nodes_removed):
            lines.append(f"- {node_id}")
        lines.append("")

    return "\n".join(lines)


def format_diff_json(report: DiffReport) -> str:
    """Format diff report as JSON."""
    changes_data = []
    for change in report.changes:
        changes_data.append({
            "location": change.location,
            "field_path": change.field_path,
            "old_value": change.old_value,
            "new_value": change.new_value,
            "change_type": change.change_type,
        })

    payload = {
        "total_changes": report.total_changes,
        "changes": changes_data,
        "nodes_added": report.nodes_added,
        "nodes_removed": report.nodes_removed,
    }

    return json.dumps(payload, indent=2)


def _format_value(value: Any) -> str:
    """Format a value for display in diff output."""
    if value is None:
        return "null"
    if isinstance(value, (list, dict)):
        return json.dumps(value)
    if isinstance(value, str):
        return value
    return str(value)
