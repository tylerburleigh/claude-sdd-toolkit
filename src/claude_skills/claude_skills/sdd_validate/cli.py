#!/usr/bin/env python3
"""
Standalone Spec Validation CLI

Validates JSON spec files using sdd_common validation modules.
Provides detailed reports for compliance issues.

Part of the Spec-Driven Development (SDD) workflow.
"""

import argparse
import json
import sys
from pathlib import Path
from dataclasses import asdict
from typing import Any, Dict

try:
    from claude_skills.common import (
        validate_spec_hierarchy,
        analyze_dependencies,
        DEFAULT_BOTTLENECK_THRESHOLD,
        PrettyPrinter,
    )
    from claude_skills.sdd_validate import (
        NormalizedValidationResult,
        format_validation_summary,
        normalize_validation_result,
        collect_fix_actions,
        apply_fix_actions,
        calculate_statistics,
        render_statistics,
        generate_report,
        compute_diff,
        format_diff_markdown,
        format_diff_json,
    )
except ImportError as e:
    print(f"ERROR: Could not import dependencies for sdd-validate CLI: {e}", file=sys.stderr)
    sys.exit(2)


def _stats_to_dict(stats) -> Dict[str, Any]:
    return asdict(stats) if stats else {}


def _dependencies_to_dict(analysis) -> Dict[str, Any]:
    if not analysis:
        return {}
    return {
        "cycles": analysis.cycles,
        "orphaned": analysis.orphaned,
        "deadlocks": analysis.deadlocks,
        "bottlenecks": analysis.bottlenecks,
        "status": analysis.status,
    }


def _normalized_to_dict(normalized: NormalizedValidationResult) -> Dict[str, Any]:
    return asdict(normalized)


def _serialize_fix_action(action) -> Dict[str, Any]:
    return {
        "id": action.id,
        "description": action.description,
        "category": action.category,
        "severity": action.severity,
        "auto_apply": action.auto_apply,
        "preview": action.preview,
    }


def _status_to_exit_code(status: str) -> int:
    if status == "errors":
        return 2
    if status == "warnings":
        return 1
    return 0


def _filter_actions_by_selection(actions, selection_criteria):
    """Filter actions based on ID or category selection."""
    selected = []

    for action in actions:
        for criterion in selection_criteria:
            # Match by exact ID
            if action.id == criterion:
                selected.append(action)
                break
            # Match by category (e.g., 'metadata' matches all metadata.* fixes)
            elif action.id.startswith(f"{criterion}.") or action.category == criterion:
                selected.append(action)
                break

    return selected


def _interactive_select_fixes(actions, printer):
    """Interactively prompt user to select fixes."""
    if not actions:
        return []

    print()
    printer.info("Select fixes to apply (use space to toggle, enter to confirm):")
    print()

    # Display available fixes
    for idx, action in enumerate(actions, 1):
        prefix = "ERROR" if action.severity in {"error", "critical"} else "WARN"
        print(f"{idx}. [{prefix}] [{action.id}]")
        print(f"   {action.description}")
        print(f"   Preview: {action.preview}")
        print()

    # Simple prompt-based selection (not using curses for portability)
    print("Enter fix numbers to apply (e.g., '1 3 5' or 'all' or 'none'):")
    try:
        user_input = input("> ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return []

    if user_input == "none" or not user_input:
        return []

    if user_input == "all":
        return actions

    # Parse selection
    selected = []
    try:
        indices = [int(x.strip()) for x in user_input.split()]
        for idx in indices:
            if 1 <= idx <= len(actions):
                selected.append(actions[idx - 1])
    except ValueError:
        printer.warning("Invalid input, no fixes selected")
        return []

    return selected


def cmd_validate(args, printer):
    """Validate JSON spec file."""
    spec_file = Path(args.spec_file).resolve()

    if not args.json and not args.quiet:
        printer.action("Validating JSON spec...")
        printer.info(f"Spec: {spec_file}")

    if not spec_file.exists():
        printer.error(f"Spec file not found: {spec_file}")
        return 2

    if not spec_file.suffix == '.json':
        printer.error(f"Expected JSON file, got: {spec_file.suffix}")
        printer.info("JSON specs are now the single source of truth")
        return 2

    # Load and validate spec
    try:
        with open(spec_file, 'r') as f:
            spec_data = json.load(f)
    except json.JSONDecodeError as e:
        printer.error(f"Invalid JSON in spec file: {e}")
        return 2

    result = validate_spec_hierarchy(spec_data)

    normalized = normalize_validation_result(result)

    if args.json:
        payload = {
            "spec_id": normalized.spec_id,
            "errors": normalized.error_count,
            "warnings": normalized.warning_count,
            "status": normalized.status,
            "auto_fixable_issues": normalized.auto_fixable_error_count + normalized.auto_fixable_warning_count,
        }
        if args.verbose:
            payload["issues"] = normalized.issues

        print(json.dumps(payload, indent=2))
    else:
        if not args.quiet:
            print()

        if normalized.status == "errors":
            printer.error("❌ Validation FAILED")
        elif normalized.status == "warnings":
            printer.warning("⚠️  Validation PASSED with warnings")
        else:
            printer.success("✅ Validation PASSED")

        summary = format_validation_summary(normalized, verbose=args.verbose)
        if summary:
            print(summary)

        # Generate report if requested
        if args.report:
            report_format = args.report_format
            stats = calculate_statistics(spec_data)
            dependencies = analyze_dependencies(spec_data)
            report = generate_report(
                result,
                format=report_format,
                stats=asdict(stats),
                dependency_analysis={
                    "cycles": dependencies.cycles,
                    "orphaned": dependencies.orphaned,
                    "deadlocks": dependencies.deadlocks,
                    "bottlenecks": dependencies.bottlenecks,
                    "status": dependencies.status,
                },
            )
            suffix = ".md" if report_format == "markdown" else ".json"
            report_file = spec_file.parent / f"{spec_file.stem}-validation-report{suffix}"
            with open(report_file, 'w') as f:
                f.write(report)
            printer.success(f"\nReport saved to: {report_file}")

    if normalized.status == "errors":
        return 2
    if normalized.status == "warnings":
        return 1
    return 0


def cmd_fix(args, printer):
    """Auto-fix validation issues in spec file."""
    spec_file = Path(args.spec_file).resolve()

    if not args.quiet and not args.json:
        printer.action(f"Analyzing spec for auto-fixable issues: {spec_file}")

    if not spec_file.exists():
        printer.error(f"Spec file not found: {spec_file}")
        return 2

    # Load and validate spec
    try:
        with open(spec_file, 'r') as f:
            spec_data = json.load(f)
    except json.JSONDecodeError as e:
        printer.error(f"Invalid JSON: {e}")
        return 2

    result = validate_spec_hierarchy(spec_data)
    actions = collect_fix_actions(result)

    if not actions:
        if not args.quiet and not args.json:
            printer.success("No auto-fixable issues found")
        return 0

    # Filter actions based on selection
    if args.select:
        selected_actions = _filter_actions_by_selection(actions, args.select)
        if not selected_actions:
            printer.warning("No fixes matched your selection criteria")
            return 0
        actions = selected_actions

    # Interactive mode
    if args.interactive and not (args.preview or args.dry_run):
        actions = _interactive_select_fixes(actions, printer)
        if not actions:
            printer.info("No fixes selected")
            return 0

    # Preview mode
    if args.preview or args.dry_run:
        if args.json:
            payload = {
                "spec_id": getattr(result, "spec_id", "unknown"),
                "actions": [_serialize_fix_action(action) for action in actions],
                "applied": 0,
                "skipped": len(actions),
                "status": "preview",
            }
            print(json.dumps(payload, indent=2))
        else:
            printer.info(f"Found {len(actions)} auto-fixable issue(s):")
            print()
            for action in actions:
                prefix = "ERROR" if action.severity in {"error", "critical"} else "WARN"
                print(f"- [{prefix}] [{action.id}] {action.description}")
                if args.verbose:
                    print(f"  Category: {action.category}")
                    print(f"  Preview: {action.preview}")
                    print()
        return 0

    # Apply fixes
    if not args.quiet and not args.json:
        printer.action(f"Applying {len(actions)} fix(es)...")

    report = apply_fix_actions(
        actions,
        str(spec_file),
        dry_run=False,
        create_backup=not args.no_backup,
        capture_diff=args.diff,
    )

    # Display diff if requested
    if args.diff and report.before_state and report.after_state:
        diff_report = compute_diff(report.before_state, report.after_state)
        spec_id = report.before_state.get("spec_id", "unknown")

        if args.diff_format == "json":
            print()
            print(format_diff_json(diff_report))
        else:
            print()
            print(format_diff_markdown(diff_report, spec_id))
        print()

    if args.json:
        payload = {
            "spec_id": getattr(result, "spec_id", "unknown"),
            "applied_action_count": len(report.applied_actions),
            "skipped_action_count": len(report.skipped_actions),
            "backup_path": report.backup_path,
            "remaining_errors": report.post_validation.get("error_count", 0) if report.post_validation else 0,
            "remaining_warnings": report.post_validation.get("warning_count", 0) if report.post_validation else 0,
            "post_status": report.post_validation.get("status", "unknown") if report.post_validation else "unknown",
        }
        print(json.dumps(payload, indent=2))
    else:
        if report.applied_actions:
            printer.success(f"Applied {len(report.applied_actions)} fix(es)")
            if report.backup_path:
                printer.info(f"Backup saved: {report.backup_path}")
        if report.skipped_actions:
            printer.warning(f"Skipped {len(report.skipped_actions)} fix(es)")

        if report.post_validation:
            print()
            printer.info("Post-fix validation:")
            status = report.post_validation.get("status", "unknown")
            error_count = report.post_validation.get("error_count", 0)
            warning_count = report.post_validation.get("warning_count", 0)

            if status == "errors":
                printer.error(f"  Errors: {error_count}")
            elif status == "warnings":
                printer.warning(f"  Warnings: {warning_count}")
            else:
                printer.success("  All issues resolved!")

    # Exit code based on post-validation status
    if report.post_validation:
        return _status_to_exit_code(report.post_validation.get("status", "valid"))
    return 0


def cmd_report(args, printer):
    """Generate detailed validation report."""
    spec_file = Path(args.spec_file).resolve()

    if not args.quiet and args.format != "json":
        printer.action(f"Generating validation report: {spec_file}")

    if not spec_file.exists():
        printer.error(f"Spec file not found: {spec_file}")
        return 2

    # Load and validate spec
    try:
        with open(spec_file, 'r') as f:
            spec_data = json.load(f)
    except json.JSONDecodeError as e:
        printer.error(f"Invalid JSON: {e}")
        return 2

    result = validate_spec_hierarchy(spec_data)
    stats = calculate_statistics(spec_data)
    dependencies = analyze_dependencies(spec_data, bottleneck_threshold=args.bottleneck_threshold)

    report = generate_report(
        result,
        format=args.format,
        stats=asdict(stats),
        dependency_analysis={
            "cycles": dependencies.cycles,
            "orphaned": dependencies.orphaned,
            "deadlocks": dependencies.deadlocks,
            "bottlenecks": dependencies.bottlenecks,
            "status": dependencies.status,
        },
    )

    if args.output == "-":
        print(report)
        return 0

    output_path = Path(args.output) if args.output else spec_file.parent / f"{spec_file.stem}-validation-report"
    if args.format == "markdown":
        output_path = output_path.with_suffix(".md")
    elif args.format == "json":
        output_path = output_path.with_suffix(".json")

    with open(output_path, "w") as f:
        f.write(report)

    printer.success(f"Report saved to: {output_path}")
    return 0


def cmd_stats(args, printer):
    """Show spec statistics and complexity metrics."""
    spec_file = Path(args.spec_file).resolve()

    if not args.json:
        printer.action(f"Analyzing: {spec_file}")

    if not spec_file.exists():
        printer.error(f"Spec file not found: {spec_file}")
        return 2

    try:
        with open(spec_file, "r") as f:
            spec_data = json.load(f)
    except json.JSONDecodeError as e:
        printer.error(f"Invalid JSON: {e}")
        return 2

    stats = calculate_statistics(spec_data)
    output = render_statistics(stats, json_output=args.json)

    if args.json:
        print(output)
    else:
        print()
        print(output)

    return 0


def cmd_check_deps(args, printer):
    """Check for circular dependencies."""
    spec_file = Path(args.spec_file).resolve()

    if not args.quiet and not args.json:
        printer.action(f"Checking dependencies: {spec_file}")

    if not spec_file.exists():
        printer.error(f"Spec file not found: {spec_file}")
        return 2

    # Load spec
    try:
        with open(spec_file, 'r') as f:
            spec_data = json.load(f)
    except json.JSONDecodeError as e:
        printer.error(f"Invalid JSON: {e}")
        return 2

    analysis = analyze_dependencies(spec_data, bottleneck_threshold=args.bottleneck_threshold)

    if args.json:
        payload = {
            "cycles": analysis.cycles,
            "orphaned": analysis.orphaned,
            "deadlocks": analysis.deadlocks,
            "bottlenecks": analysis.bottlenecks,
            "status": analysis.status,
        }
        print(json.dumps(payload, indent=2))
    else:
        printer.success("Dependency Analysis:")
        if analysis.cycles:
            printer.error("❌ Cycles detected")
            print("Cycles found:")
            for cycle in analysis.cycles:
                print("   " + " -> ".join(cycle))
        if analysis.orphaned:
            printer.warning("⚠️  Orphaned dependencies found")
            print("Orphaned tasks (dependencies on non-existent tasks):")
            for orphan in analysis.orphaned:
                print(f"   {orphan['task']} references missing {orphan['missing_dependency']}")
        if analysis.deadlocks:
            printer.warning("⚠️  Potential deadlocks detected")
            print("Deadlock warnings:")
            for deadlock in analysis.deadlocks:
                print(f"   {deadlock['task']} blocked by {', '.join(deadlock['blocked_by'])}")
        if analysis.bottlenecks:
            printer.info("ℹ️  Bottleneck tasks above threshold:")
            print("Bottleneck warnings:")
            for bottleneck in analysis.bottlenecks:
                print(
                    f"   {bottleneck['task']} blocks {bottleneck['blocks']} tasks (threshold {bottleneck['threshold']})"
                )

    if analysis.cycles or analysis.orphaned or analysis.deadlocks or analysis.bottlenecks:
        return 1
    return 0


def register_validate(subparsers, parent_parser):
    """
    Register 'validate' subcommand for unified CLI.

    Args:
        subparsers: ArgumentParser subparsers object
        parent_parser: Parent parser with global options

    Note:
        Handlers receive (args, printer) when invoked from main().
    """
    # Validate command
    parser_validate = subparsers.add_parser('validate',
                                            parents=[parent_parser],
                                            help='Validate JSON spec file')
    parser_validate.add_argument('spec_file', help='Path to JSON spec file')
    parser_validate.add_argument('--report', action='store_true',
                                 help='Generate validation report')
    parser_validate.add_argument('--report-format', dest='report_format',
                                 choices=['markdown', 'json'], default='markdown',
                                 help='Report format (default: markdown)')
    parser_validate.set_defaults(func=cmd_validate)

    # Fix command
    parser_fix = subparsers.add_parser('fix',
                                       parents=[parent_parser],
                                       help='Auto-fix validation issues')
    parser_fix.add_argument('spec_file', help='Path to JSON spec file')
    parser_fix.add_argument('--preview', action='store_true',
                           help='Preview fixes without applying (alias for --dry-run)')
    parser_fix.add_argument('--dry-run', action='store_true',
                           help='Preview fixes without applying')
    parser_fix.add_argument('--no-backup', action='store_true',
                           help='Disable backup creation before applying fixes')
    parser_fix.add_argument('--select', nargs='+', metavar='ID',
                           help='Select specific fixes by ID or category (e.g., counts.recalculate or metadata)')
    parser_fix.add_argument('--interactive', '-i', action='store_true',
                           help='Interactively select fixes to apply')
    parser_fix.add_argument('--diff', action='store_true',
                           help='Show before/after diff of changes made')
    parser_fix.add_argument('--diff-format', choices=['markdown', 'json'], default='markdown',
                           help='Diff output format (default: markdown)')
    parser_fix.set_defaults(func=cmd_fix)

    # Report command
    parser_report = subparsers.add_parser('report',
                                          parents=[parent_parser],
                                          help='Generate detailed validation report')
    parser_report.add_argument('spec_file', help='Path to JSON spec file')
    parser_report.add_argument('--output', '-o', help='Output file path (use "-" for stdout)')
    parser_report.add_argument('--format', choices=['markdown', 'json'], default='markdown',
                               help='Report format (default: markdown)')
    parser_report.add_argument('--bottleneck-threshold', type=int, default=DEFAULT_BOTTLENECK_THRESHOLD,
                               help=f'Minimum tasks blocked to flag bottleneck (default: {DEFAULT_BOTTLENECK_THRESHOLD})')
    parser_report.set_defaults(func=cmd_report)

    # Stats command
    parser_stats = subparsers.add_parser('stats',
                                         parents=[parent_parser],
                                         help='Show spec statistics')
    parser_stats.add_argument('spec_file', help='Path to JSON spec file')
    parser_stats.set_defaults(func=cmd_stats)

    # Analyze dependencies command (renamed from check-deps to avoid conflict with sdd-next)
    parser_deps = subparsers.add_parser('analyze-deps',
                                        parents=[parent_parser],
                                        help='Analyze dependencies for circular dependencies and bottlenecks')
    parser_deps.add_argument('spec_file', help='Path to JSON spec file')
    parser_deps.add_argument('--bottleneck-threshold', type=int, default=DEFAULT_BOTTLENECK_THRESHOLD,
                            help=f'Minimum tasks blocked to flag bottleneck (default: {DEFAULT_BOTTLENECK_THRESHOLD})')
    parser_deps.set_defaults(func=cmd_check_deps)
