"""Diff computation and formatting for before/after spec fix comparisons."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel
from rich.syntax import Syntax
from rich.text import Text
from rich.table import Table

from claude_skills.common.json_output import format_json_output
from claude_skills.common.ui_factory import create_ui


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

    return format_json_output(payload)


def _format_value(value: Any) -> str:
    """Format a value for display in diff output."""
    if value is None:
        return "null"
    if isinstance(value, (list, dict)):
        return format_json_output(value, compact=True)
    if isinstance(value, str):
        return value
    return str(value)


def _detect_code_language(field_path: str, value: Any) -> Optional[str]:
    """
    Detect programming language from field path or value content.

    Args:
        field_path: Field path like "metadata.command" or "verification.script"
        value: Value to analyze for language detection

    Returns:
        Language identifier for Rich.Syntax or None if not code
    """
    if not isinstance(value, str):
        return None

    value_lower = value.strip().lower()
    field_lower = field_path.lower()

    # Empty or very short strings are not code
    if len(value) < 3:
        return None

    # Check field path patterns
    if "command" in field_lower or "script" in field_lower or "bash" in field_lower:
        return "bash"
    if "python" in field_lower or ".py" in field_lower:
        return "python"
    if "sql" in field_lower:
        return "sql"
    if "json" in field_lower:
        return "json"
    if "yaml" in field_lower or "yml" in field_lower:
        return "yaml"

    # Check value content patterns
    # SQL queries (check before Python to avoid false positives with "from")
    if any(kw in value_lower for kw in ["select ", "insert ", "update ", "delete ", "create table", " where ", " join "]):
        return "sql"

    # Bash/shell commands
    if any(cmd in value_lower for cmd in ["#!/bin/", "&&", "||", "|", "echo ", "export ", "$("]):
        return "bash"

    # Python code
    if any(kw in value_lower for kw in ["def ", "class ", "import ", "from ", "if __name__"]):
        return "python"

    # JSON content (starts with { or [)
    if value_lower.startswith(("{", "[")):
        try:
            json.loads(value)
            return "json"
        except (json.JSONDecodeError, ValueError):
            pass

    return None


def _should_use_syntax_highlighting(value: Any, language: Optional[str]) -> bool:
    """
    Determine if value should use syntax highlighting.

    Args:
        value: Value to check
        language: Detected language or None

    Returns:
        True if syntax highlighting should be used
    """
    if not isinstance(value, str):
        return False
    if language is None:
        return False
    # Only highlight if the value has some complexity
    if len(value) < 10:
        return False
    if "\n" not in value and len(value) < 30:
        return False
    return True


def display_diff_side_by_side(
    report: DiffReport,
    spec_id: str = "unknown",
    ui=None
) -> None:
    """
    Display diff report using UI abstraction.

    Shows before/after values in parallel columns (RichUi) or sequentially (PlainUi).

    Args:
        report: DiffReport with changes to display
        spec_id: Spec identifier for display
        ui: UI instance for console output (optional)
    """
    # Create UI if not provided
    if ui is None:
        ui = create_ui(force_rich=True)

    # Determine backend type
    use_rich = ui.console is not None

    if use_rich:
        console = ui.console
    else:
        console = None

    # Header
    if use_rich:
        console.print()
        console.print(f"[bold]Spec Fix Comparison:[/bold] {spec_id}", style="cyan")
        console.print(f"[dim]Total Changes: {report.total_changes}[/dim]")
        console.print()

        if not report.total_changes:
            console.print("[green]✓ No changes detected[/green]")
            return
    else:
        print()
        print(f"===== Spec Fix Comparison: {spec_id} =====")
        print(f"Total Changes: {report.total_changes}")
        print()

        if not report.total_changes:
            print("✓ No changes detected")
            return

    # Group changes by location
    changes_by_location: Dict[str, List[FieldChange]] = {}
    for change in report.changes:
        if change.location not in changes_by_location:
            changes_by_location[change.location] = []
        changes_by_location[change.location].append(change)

    # Display changes grouped by location
    for location in sorted(changes_by_location.keys()):
        changes = changes_by_location[location]

        # Location header
        if use_rich:
            console.print(f"\n[bold cyan]Location:[/bold cyan] {location}")
        else:
            print(f"\nLocation: {location}")

        for change in changes:
            # Create before/after content
            before_content = _create_value_display(
                change.field_path,
                change.old_value,
                change.change_type,
                is_before=True
            )
            after_content = _create_value_display(
                change.field_path,
                change.new_value,
                change.change_type,
                is_before=False
            )

            # Style and titles based on change type
            if change.change_type == "added":
                before_style = "dim"
                after_style = "green"
                before_title = "Before (not present)"
                after_title = "After (added)"
            elif change.change_type == "removed":
                before_style = "red"
                after_style = "dim"
                before_title = "Before (removed)"
                after_title = "After (not present)"
            else:  # modified
                before_style = "yellow"
                after_style = "green"
                before_title = "Before"
                after_title = "After"

            if use_rich:
                # RichUi: Display side-by-side with Columns
                before_panel = Panel(
                    before_content,
                    title=before_title,
                    border_style=before_style,
                    padding=(0, 1)
                )
                after_panel = Panel(
                    after_content,
                    title=after_title,
                    border_style=after_style,
                    padding=(0, 1)
                )

                # Display side-by-side
                columns = Columns([before_panel, after_panel], equal=True, expand=True)
                console.print(columns)
                console.print()  # Spacing between changes
            else:
                # PlainUi: Display sequentially
                print(f"\n  Field: {change.field_path}")
                print(f"  {before_title}:")
                print(f"    {_format_plain_value(change.old_value)}")
                print(f"  {after_title}:")
                print(f"    {_format_plain_value(change.new_value)}")
                print()  # Spacing between changes

    # Display added/removed nodes
    if report.nodes_added or report.nodes_removed:
        if use_rich:
            console.print()
        else:
            print()

    if report.nodes_added:
        if use_rich:
            console.print("[bold green]Nodes Added:[/bold green]")
            for node_id in sorted(report.nodes_added):
                console.print(f"  [green]+ {node_id}[/green]")
            console.print()
        else:
            print("Nodes Added:")
            for node_id in sorted(report.nodes_added):
                print(f"  + {node_id}")
            print()

    if report.nodes_removed:
        if use_rich:
            console.print("[bold red]Nodes Removed:[/bold red]")
            for node_id in sorted(report.nodes_removed):
                console.print(f"  [red]- {node_id}[/red]")
            console.print()
        else:
            print("Nodes Removed:")
            for node_id in sorted(report.nodes_removed):
                print(f"  - {node_id}")
            print()


def _create_value_display(
    field_path: str,
    value: Any,
    change_type: str,
    is_before: bool
) -> Any:
    """
    Create formatted display for a value in the diff.

    Args:
        field_path: Path to the field (e.g., "status", "metadata.file_path")
        value: Value to display
        change_type: Type of change ("added", "removed", "modified")
        is_before: True if this is the "before" column, False for "after"

    Returns:
        Rich Text or Syntax object with formatted content
    """
    text = Text()

    # Field name
    text.append(f"{field_path}\n", style="bold")

    # Value display
    if value is None:
        if (change_type == "added" and is_before) or (change_type == "removed" and not is_before):
            text.append("(not present)", style="dim italic")
        else:
            text.append("null", style="dim")
        return text
    elif isinstance(value, (list, dict)):
        # Format complex values with indentation
        formatted = format_json_output(value)
        text.append(formatted, style="cyan")
        return text
    elif isinstance(value, bool):
        text.append(str(value).lower(), style="magenta")
        return text
    elif isinstance(value, (int, float)):
        text.append(str(value), style="cyan")
        return text
    else:
        # String values - check for code and apply syntax highlighting
        language = _detect_code_language(field_path, value)
        if _should_use_syntax_highlighting(value, language):
            # Create a group with field name and syntax-highlighted code
            from rich.console import Group

            field_text = Text(f"{field_path}\n", style="bold")
            syntax = Syntax(
                str(value),
                language,
                theme="monokai",
                line_numbers=False,
                word_wrap=True
            )
            return Group(field_text, syntax)
        else:
            # Plain string without syntax highlighting
            text.append(str(value), style="white")
            return text


def _format_plain_value(value: Any) -> str:
    """
    Format a value for plain text display.

    Args:
        value: Value to format

    Returns:
        Formatted string representation
    """
    if value is None:
        return "(not present)"
    elif isinstance(value, (list, dict)):
        return format_json_output(value)
    elif isinstance(value, bool):
        return str(value).lower()
    else:
        return str(value)
