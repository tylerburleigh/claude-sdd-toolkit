"""Statistics helpers for the `sdd-validate` CLI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from claude_skills.common.json_output import format_json_output

STATUS_FIELDS = {"pending", "in_progress", "completed", "blocked"}


@dataclass
class SpecStatistics:
    """Calculated statistics for a spec file."""

    spec_id: str
    title: str
    version: str
    status: str
    totals: Dict[str, int]
    status_counts: Dict[str, int]
    max_depth: int
    avg_tasks_per_phase: float
    verification_coverage: float
    progress: float
    file_size_kb: float


def calculate_statistics(spec_data: Dict[str, Any]) -> SpecStatistics:
    """Compute statistics for a spec file."""

    hierarchy = spec_data.get("hierarchy", {}) or {}

    totals = {
        "nodes": len(hierarchy),
        "tasks": 0,
        "phases": 0,
        "verifications": 0,
    }

    status_counts = {status: 0 for status in STATUS_FIELDS}
    max_depth = 0

    def traverse(node_id: str, depth: int) -> None:
        nonlocal max_depth
        node = hierarchy.get(node_id, {})
        node_type = node.get("type")

        max_depth = max(max_depth, depth)

        if node_type in {"task", "subtask"}:
            totals["tasks"] += 1
            status = node.get("status", "").lower()
            normalized_status = status.replace(" ", "_").replace("-", "_")
            if normalized_status in status_counts:
                status_counts[normalized_status] += 1
        elif node_type == "phase":
            totals["phases"] += 1
        elif node_type == "verify":
            totals["verifications"] += 1

        for child_id in node.get("children", []) or []:
            if child_id in hierarchy:
                traverse(child_id, depth + 1)

    if "spec-root" in hierarchy:
        traverse("spec-root", 0)

    total_tasks = totals["tasks"]
    phase_count = totals["phases"] or 1
    avg_tasks_per_phase = round(total_tasks / phase_count, 2)

    root = hierarchy.get("spec-root", {})
    root_total_tasks = root.get("total_tasks", total_tasks)
    root_completed = root.get("completed_tasks", 0)

    verification_count = totals["verifications"]
    verification_coverage = (verification_count / total_tasks) if total_tasks else 0.0
    progress = (root_completed / root_total_tasks) if root_total_tasks else 0.0

    file_size = 0.0
    file_path = spec_data.get("__file_path__")
    if file_path:
        try:
            file_size = Path(file_path).stat().st_size / 1024
        except OSError:
            file_size = 0.0

    return SpecStatistics(
        spec_id=spec_data.get("spec_id", "unknown"),
        title=spec_data.get("title", ""),
        version=spec_data.get("version", ""),
        status=root.get("status", "unknown"),
        totals=totals,
        status_counts=status_counts,
        max_depth=max_depth,
        avg_tasks_per_phase=avg_tasks_per_phase,
        verification_coverage=verification_coverage,
        progress=progress,
        file_size_kb=file_size,
    )


def render_statistics(stats: SpecStatistics, *, json_output: bool = False) -> str:
    """Render statistics for display."""

    if json_output:
        return format_json_output(
            {
                "spec_id": stats.spec_id,
                "title": stats.title,
                "version": stats.version,
                "status": stats.status,
                "totals": stats.totals,
                "status_counts": stats.status_counts,
                "max_depth": stats.max_depth,
                "avg_tasks_per_phase": stats.avg_tasks_per_phase,
                "verification_coverage": stats.verification_coverage,
                "progress": stats.progress,
                "file_size_kb": stats.file_size_kb,
            }
        )

    lines = [
        f"Spec ID: {stats.spec_id}",
        f"Title: {stats.title or 'N/A'}",
        f"Version: {stats.version or 'N/A'}",
        f"Status: {stats.status or 'unknown'}",
        "",
        "Totals:",
        f"  Nodes: {stats.totals['nodes']}",
        f"  Tasks: {stats.totals['tasks']}",
        f"  Phases: {stats.totals['phases']}",
        f"  Verifications: {stats.totals['verifications']}",
        "",
        "Status counts:",
    ]
    for status, count in stats.status_counts.items():
        lines.append(f"  {status}: {count}")

    lines.extend(
        [
            "",
            f"Max depth: {stats.max_depth}",
            f"Avg tasks per phase: {stats.avg_tasks_per_phase:.2f}",
            f"Verification coverage: {stats.verification_coverage:.2%}",
            f"Progress: {stats.progress:.2%}",
            f"File size: {stats.file_size_kb:.1f} KB" if stats.file_size_kb else "File size: N/A",
        ]
    )

    return "\n".join(lines)

