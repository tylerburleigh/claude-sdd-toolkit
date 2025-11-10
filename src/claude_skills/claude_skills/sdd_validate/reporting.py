"""Report generation helpers for the `sdd-validate` CLI."""

from __future__ import annotations

from typing import Any, Dict, Optional

from claude_skills.common import JsonSpecValidationResult
from claude_skills.common.json_output import format_json_output
from claude_skills.sdd_validate.formatting import NormalizedValidationResult, normalize_validation_result


def generate_report(
    result: JsonSpecValidationResult,
    *,
    format: str = "markdown",
    stats: Optional[Dict[str, Any]] = None,
    dependency_analysis: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a validation report in the requested format."""

    if format not in {"markdown", "json"}:
        raise ValueError(f"Unsupported report format: {format}")

    normalized = normalize_validation_result(result)

    if format == "json":
        # Normalize dependency analysis keys for JSON output
        deps = {}
        if dependency_analysis:
            deps = {
                "cycles": dependency_analysis.get("cycles") or dependency_analysis.get("circular_chains") or [],
                "orphaned": dependency_analysis.get("orphaned") or dependency_analysis.get("orphaned_tasks") or [],
                "deadlocks": dependency_analysis.get("deadlocks") or dependency_analysis.get("impossible_chains") or [],
                "bottlenecks": dependency_analysis.get("bottlenecks") or [],
                "status": dependency_analysis.get("status", "ok"),
            }

        schema_info = {
            "source": getattr(result, "schema_source", None),
            "errors": list(getattr(result, "schema_errors", []) or []),
            "warnings": list(getattr(result, "schema_warnings", []) or []),
        }

        payload = {
            "summary": {
                "spec_id": normalized.spec_id,
                "status": normalized.status,
                "errors": normalized.error_count,
                "warnings": normalized.warning_count,
                "auto_fixable_errors": normalized.auto_fixable_error_count,
                "auto_fixable_warnings": normalized.auto_fixable_warning_count,
            },
            "errors": [issue for issue in normalized.issues if issue["severity"] in {"critical", "error"}],
            "warnings": [issue for issue in normalized.issues if issue["severity"] == "warning"],
            "auto_fix_suggestions": [issue for issue in normalized.issues if issue["auto_fixable"]],
            "stats": stats or {},
            "dependencies": deps,
        }

        if schema_info["source"] or schema_info["errors"] or schema_info["warnings"]:
            payload["schema"] = schema_info

        return format_json_output(payload)

    lines = [
        "# Validation Report",
        "",
        f"**Spec ID:** {normalized.spec_id}",
        f"**Status:** {normalized.status}",
        "",
        "## Summary",
        f"- Errors: {normalized.error_count}",
        f"- Warnings: {normalized.warning_count}",
        f"- Auto-fixable: {normalized.auto_fixable_error_count + normalized.auto_fixable_warning_count}",
    ]

    schema_info = {
        "source": getattr(result, "schema_source", None),
        "errors": list(getattr(result, "schema_errors", []) or []),
        "warnings": list(getattr(result, "schema_warnings", []) or []),
    }

    if normalized.issues:
        lines.append("")
        lines.append("## Issues")
        for issue in normalized.issues:
            line = f"- {issue['severity'].upper()}: {issue['message']}"
            if issue.get("location"):
                line += f" ({issue['location']})"
            if issue.get("auto_fixable"):
                line += " [auto-fixable]"
            lines.append(line)

    if not normalized.issues:
        lines.append("")
        lines.append("No validation issues detected.")

    if stats:
        lines.append("")
        lines.append("## Statistics Snapshot")
        for key, value in stats.items():
            lines.append(f"- {key}: {value}")

    if dependency_analysis:
        lines.append("")
        lines.append("## Dependency Findings")

        # Handle cycles (from CLI: "cycles", legacy: "circular_chains")
        cycles = dependency_analysis.get("cycles") or dependency_analysis.get("circular_chains") or []
        if cycles:
            lines.append("- Cycles:")
            for cycle in cycles:
                lines.append(f"  - {' -> '.join(cycle)}")

        # Handle orphaned deps (from CLI: "orphaned", legacy: "orphaned_tasks")
        orphaned = dependency_analysis.get("orphaned") or dependency_analysis.get("orphaned_tasks") or []
        if orphaned:
            lines.append("- Orphaned dependencies:")
            for orphan in orphaned:
                task = orphan.get('task') or orphan.get('id', 'unknown')
                missing = orphan.get('missing_dependency') or orphan.get('missing', 'unknown')
                lines.append(f"  - {task} references missing {missing}")

        # Handle deadlocks (from CLI: "deadlocks", legacy: "impossible_chains")
        deadlocks = dependency_analysis.get("deadlocks") or dependency_analysis.get("impossible_chains") or []
        if deadlocks:
            lines.append("- Potential deadlocks:")
            for deadlock in deadlocks:
                task = deadlock.get('task') or deadlock.get('id', 'unknown')
                blocked_by = deadlock.get('blocked_by', [])
                if isinstance(blocked_by, list):
                    blocked_str = ', '.join(blocked_by)
                else:
                    blocked_str = str(blocked_by)
                lines.append(f"  - {task} blocked by {blocked_str}")

        # Handle bottlenecks (from CLI only)
        bottlenecks = dependency_analysis.get("bottlenecks") or []
        if bottlenecks:
            lines.append("- Bottleneck tasks:")
            for bottleneck in bottlenecks:
                task = bottleneck.get('task') or bottleneck.get('id', 'unknown')
                blocks = bottleneck.get('blocks', 0)
                threshold = bottleneck.get('threshold', 'N/A')
                lines.append(f"  - {task} blocks {blocks} tasks (threshold: {threshold})")

    if schema_info["source"] or schema_info["errors"] or schema_info["warnings"]:
        lines.append("")
        lines.append("## Schema Validation")
        if schema_info["source"]:
            lines.append(f"- Source: {schema_info['source']}")
        if schema_info["errors"]:
            lines.append("- Errors:")
            for message in schema_info["errors"]:
                lines.append(f"  - {message}")
        if schema_info["warnings"]:
            lines.append("- Warnings:")
            for message in schema_info["warnings"]:
                lines.append(f"  - {message}")

    return "\n".join(lines)

