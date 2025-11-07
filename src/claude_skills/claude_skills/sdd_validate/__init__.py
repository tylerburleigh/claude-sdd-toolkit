"""Spec validation skill package."""

from .formatting import NormalizedValidationResult, format_validation_summary, normalize_validation_result
from .fix import FixAction, FixReport, collect_fix_actions, apply_fix_actions
from .stats import SpecStatistics, calculate_statistics, render_statistics
from .reporting import generate_report
from .diff import (
    DiffReport,
    compute_diff,
    format_diff_markdown,
    format_diff_json,
    display_diff_side_by_side,
)

__all__ = [
    "NormalizedValidationResult",
    "format_validation_summary",
    "normalize_validation_result",
    "FixAction",
    "FixReport",
    "collect_fix_actions",
    "apply_fix_actions",
    "SpecStatistics",
    "calculate_statistics",
    "render_statistics",
    "generate_report",
    "DiffReport",
    "compute_diff",
    "format_diff_markdown",
    "format_diff_json",
    "display_diff_side_by_side",
]
