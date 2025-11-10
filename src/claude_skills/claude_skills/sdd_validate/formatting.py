"""Output formatting utilities for the `sdd-validate` CLI."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from claude_skills.common.validation import EnhancedError, JsonSpecValidationResult


@dataclass
class NormalizedValidationResult:
    """Aggregated validation statistics derived from a raw validation result."""

    spec_id: str
    status: str
    error_count: int
    warning_count: int
    auto_fixable_error_count: int
    auto_fixable_warning_count: int
    issues: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def auto_fixable_total(self) -> int:
        return self.auto_fixable_error_count + self.auto_fixable_warning_count

    @property
    def has_errors(self) -> bool:  # backwards compatibility convenience
        return self.error_count > 0

    @property
    def has_warnings(self) -> bool:
        return self.warning_count > 0 and not self.has_errors


_ERROR_FIELDS: Sequence[str] = (
    "schema_errors",
    "structure_errors",
    "hierarchy_errors",
    "node_errors",
    "count_errors",
    "dependency_errors",
    "metadata_errors",
    "cross_val_errors",
)

_WARNING_FIELDS: Sequence[str] = (
    "schema_warnings",
    "structure_warnings",
    "hierarchy_warnings",
    "node_warnings",
    "count_warnings",
    "dependency_warnings",
    "metadata_warnings",
    "cross_val_warnings",
)


def _category_from_field(field: str) -> str:
    if field.endswith("_errors"):
        field = field[: -len("_errors")]
    elif field.endswith("_warnings"):
        field = field[: -len("_warnings")]
    return field.replace("_", "-")


def _collect_messages(
    result: JsonSpecValidationResult, fields: Iterable[str], severity: str
) -> List[Dict[str, Any]]:
    collected: List[Dict[str, Any]] = []
    for field_name in fields:
        for message in getattr(result, field_name, []) or []:
            collected.append(
                {
                    "message": message,
                    "severity": severity,
                    "category": _category_from_field(field_name),
                    "location": None,
                    "auto_fixable": False,
                }
            )
    return collected


def _merge_enhanced_issues(
    issues: List[Dict[str, Any]], enhanced_errors: List[EnhancedError]
) -> Tuple[List[Dict[str, Any]], int, int]:
    auto_fixable_error_count = 0
    auto_fixable_warning_count = 0

    seen = {
        (issue["message"], issue["severity"], issue["category"], issue.get("location"))
        for issue in issues
    }

    for error in enhanced_errors or []:
        record = {
            "message": error.message,
            "severity": error.severity,
            "category": error.category,
            "location": error.location,
            "auto_fixable": error.auto_fixable,
            "suggested_fix": error.suggested_fix,
        }
        key = (
            record["message"],
            record["severity"],
            record["category"],
            record.get("location"),
        )
        if key in seen:
            # replace existing entry with enhanced metadata
            for existing in issues:
                if (
                    existing["message"],
                    existing["severity"],
                    existing["category"],
                    existing.get("location"),
                ) == key:
                    existing.update(record)
                    break
        else:
            issues.append(record)
            seen.add(key)

        if error.auto_fixable:
            if error.severity in {"critical", "error"}:
                auto_fixable_error_count += 1
            else:
                auto_fixable_warning_count += 1

    return issues, auto_fixable_error_count, auto_fixable_warning_count


def normalize_validation_result(result: JsonSpecValidationResult) -> NormalizedValidationResult:
    """Convert a raw validation result into aggregate counts and issue metadata."""

    issues: List[Dict[str, Any]] = []
    issues.extend(_collect_messages(result, _ERROR_FIELDS, "error"))
    issues.extend(_collect_messages(result, _WARNING_FIELDS, "warning"))

    issues, auto_fixable_error_count, auto_fixable_warning_count = _merge_enhanced_issues(
        issues, getattr(result, "enhanced_errors", [])
    )

    error_count = sum(1 for issue in issues if issue["severity"] in {"error", "critical"})
    warning_count = sum(1 for issue in issues if issue["severity"] == "warning")

    status = "valid"
    if error_count:
        status = "errors"
    elif warning_count:
        status = "warnings"

    return NormalizedValidationResult(
        spec_id=getattr(result, "spec_id", "unknown"),
        status=status,
        error_count=error_count,
        warning_count=warning_count,
        auto_fixable_error_count=auto_fixable_error_count,
        auto_fixable_warning_count=auto_fixable_warning_count,
        issues=sorted(
            issues,
            key=lambda issue: (
                {"critical": 0, "error": 1, "warning": 2}.get(issue["severity"], 3),
                issue["category"],
                issue["message"],
            ),
        ),
    )


def format_validation_summary(result: NormalizedValidationResult, *, verbose: bool = False) -> str:
    """Render a human-readable summary of validation findings."""

    lines = [
        f"Errors: {result.error_count}",
        f"Warnings: {result.warning_count}",
        f"Auto-fix candidates: {result.auto_fixable_total}",
    ]

    if verbose and result.issues:
        lines.append("")
        lines.append("Issues:")
        for issue in result.issues:
            prefix = {
                "critical": "CRITICAL",
                "error": "ERROR",
                "warning": "WARN",
            }.get(issue["severity"], issue["severity"].upper())
            components = [f"- [{prefix}] {issue['message']}"]
            if issue.get("category"):
                components.append(f"category={issue['category']}")
            if issue.get("location"):
                components.append(f"location={issue['location']}")
            if issue.get("auto_fixable"):
                components.append("auto-fixable")
            lines.append(" ".join(components))

    return "\n".join(lines)

