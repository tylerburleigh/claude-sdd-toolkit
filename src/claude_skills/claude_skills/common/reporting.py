"""
Reporting operations for sdd-plan.
Generates comprehensive validation reports for spec and JSON specs.
"""

from pathlib import Path
from datetime import datetime
from typing import List

# Add parent directories to path for imports

from claude_skills.common import (
    SpecValidationResult,
    JsonSpecValidationResult
)


def generate_spec_report(result: SpecValidationResult) -> str:
    """
    Generate a comprehensive spec validation report.

    Args:
        result: SpecValidationResult from validation

    Returns:
        Formatted report string
    """
    report = ["# Spec Document Validation Report\n"]

    # Header with spec info
    report.append(f"**Specification**: {result.spec_title}")
    report.append(f"**Spec ID**: {result.spec_id}")
    report.append(f"**Version**: {result.spec_version}")
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Overall validation status
    error_count, warning_count = result.count_all_issues()

    report.append("## Validation Summary\n")
    report.append(f"- **Total Errors**: {error_count}")
    report.append(f"- **Total Warnings**: {warning_count}")
    report.append(f"- **Tasks**: {result.task_count}")
    report.append(f"- **Phases**: {result.phase_count}")
    report.append(f"- **Verifications**: {result.verification_count}\n")

    # Overall status
    if error_count == 0 and warning_count == 0:
        report.append("**Status**: ✅ Spec is fully valid and ready for use with sdd-next\n")
    elif error_count == 0:
        report.append(f"**Status**: ⚠️  Spec is valid but has {warning_count} warning(s)\n")
    else:
        report.append(f"**Status**: ❌ Spec has {error_count} critical error(s) - NOT ready for sdd-next\n")

    # Add detailed sections for each category with errors/warnings
    if result.frontmatter_errors or result.frontmatter_warnings:
        report.append("## YAML Frontmatter Validation\n")
        for error in result.frontmatter_errors:
            report.append(f"{error}")
        for warning in result.frontmatter_warnings:
            report.append(f"{warning}")
        report.append("")

    if result.anchor_errors:
        report.append("## Task Anchor Placement (CRITICAL)\n")
        for error in result.anchor_errors:
            report.append(f"{error}\n")

    if result.task_detail_errors or result.task_detail_warnings:
        report.append("## Task Detail Validation\n")
        for error in result.task_detail_errors:
            report.append(f"{error}\n")
        for warning in result.task_detail_warnings:
            report.append(f"{warning}\n")

    if result.structure_errors or result.structure_warnings:
        report.append("## Document Structure Validation\n")
        for error in result.structure_errors:
            report.append(f"{error}")
        for warning in result.structure_warnings:
            report.append(f"{warning}")
        report.append("")

    if result.phase_errors or result.phase_warnings:
        report.append("## Phase Format Validation\n")
        for error in result.phase_errors:
            report.append(f"{error}")
        for warning in result.phase_warnings:
            report.append(f"{warning}")
        report.append("")

    return "\n".join(report)


def generate_json_spec_report(result: JsonSpecValidationResult) -> str:
    """
    Generate a comprehensive JSON spec validation report.

    Args:
        result: JsonSpecValidationResult from JSON spec validation

    Returns:
        Formatted report string
    """
    report = ["# JSON Spec Validation Report\n"]

    # Header with JSON spec info
    report.append(f"**Spec ID**: {result.spec_id}")
    report.append(f"**Generated**: {result.generated}")
    report.append(f"**Last Updated**: {result.last_updated}")
    report.append(f"**Validation Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Overall validation status
    error_count, warning_count = result.count_all_issues()

    report.append("## Validation Summary\n")
    report.append(f"- **Total Errors**: {error_count}")
    report.append(f"- **Total Warnings**: {warning_count}")
    report.append(f"- **Total Nodes**: {result.total_nodes}")
    report.append(f"- **Total Tasks**: {result.total_tasks}\n")

    # Overall status
    if error_count == 0 and warning_count == 0:
        report.append("**Status**: ✅ JSON spec file is fully valid and ready for use\n")
    elif error_count == 0:
        report.append(f"**Status**: ⚠️  JSON spec file is valid but has {warning_count} warning(s)\n")
    else:
        report.append(f"**Status**: ❌ JSON spec file has {error_count} critical error(s) - NOT ready for use\n")

    # Add detailed sections for each category with errors/warnings
    for category_name, errors, warnings in [
        ("JSON Structure", result.structure_errors, result.structure_warnings),
        ("Hierarchy Integrity", result.hierarchy_errors, result.hierarchy_warnings),
        ("Node Structure", result.node_errors, result.node_warnings),
        ("Task Count Accuracy", result.count_errors, result.count_warnings),
        ("Dependency Graph", result.dependency_errors, result.dependency_warnings),
        ("Type-Specific Metadata", result.metadata_errors, result.metadata_warnings),
        ("Spec Cross-Validation", result.cross_val_errors, result.cross_val_warnings)
    ]:
        if errors or warnings:
            report.append(f"## {category_name} Validation\n")
            for error in errors:
                report.append(f"{error}\n")
            for warning in warnings:
                report.append(f"{warning}\n")

    return "\n".join(report)


def generate_combined_report(spec_result: SpecValidationResult, json_spec_result: JsonSpecValidationResult) -> str:
    """
    Generate a combined validation report for markdown spec and JSON spec.

    Args:
        spec_result: SpecValidationResult from markdown spec validation
        json_spec_result: JsonSpecValidationResult from JSON spec validation

    Returns:
        Formatted combined report string
    """
    report = ["# Combined Validation Report\n"]
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    spec_errors, spec_warnings = spec_result.count_all_issues()
    json_errors, json_warnings = json_spec_result.count_all_issues()

    total_errors = spec_errors + spec_errors
    total_warnings = spec_warnings + spec_warnings

    report.append("## Overall Summary\n")
    report.append(f"- **Total Errors**: {total_errors}")
    report.append(f"- **Total Warnings**: {total_warnings}\n")

    report.append("### Spec Document")
    report.append(f"- Errors: {spec_errors}")
    report.append(f"- Warnings: {spec_warnings}")
    report.append(f"- Status: {'✅ Valid' if spec_errors == 0 else '❌ Invalid'}\n")

    report.append("### JSON Spec")
    report.append(f"- Errors: {spec_errors}")
    report.append(f"- Warnings: {spec_warnings}")
    report.append(f"- Status: {'✅ Valid' if spec_errors == 0 else '❌ Invalid'}\n")

    if total_errors == 0 and total_warnings == 0:
        report.append("**Status**: ✅ VALIDATION PASSED - Ready for development!\n")
    elif total_errors == 0:
        report.append(f"**Status**: ⚠️  VALIDATION PASSED with {total_warnings} warning(s)\n")
    else:
        report.append(f"**Status**: ❌ VALIDATION FAILED - {total_errors} critical error(s)\n")

    return "\n".join(report)
