#!/usr/bin/env python3
"""
SDD Spec Modification CLI - Commands for modifying specification files.
"""

import argparse
import sys
import json
from pathlib import Path
from claude_skills.common import PrettyPrinter, find_spec_file, find_specs_directory, load_json_spec
from claude_skills.common.json_output import output_json
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    is_json_mode,
    SPEC_MOD_APPLY_ESSENTIAL,
    SPEC_MOD_APPLY_STANDARD,
    SPEC_MOD_DRY_RUN_ESSENTIAL,
    SPEC_MOD_DRY_RUN_STANDARD,
    SPEC_MOD_PARSE_REVIEW_ESSENTIAL,
    SPEC_MOD_PARSE_REVIEW_STANDARD,
)
from claude_skills.sdd_spec_mod import apply_modifications, parse_review_report, suggest_modifications


def _spec_mod_output_json(data, args, essential_fields, standard_fields):
    """Emit filtered JSON output when --json flag is present."""
    if is_json_mode(args):
        payload = prepare_output(data, args, essential_fields, standard_fields)
        output_json(payload, getattr(args, 'compact', False))
        return True
    return False


def cmd_apply_modifications(args, printer):
    """
    Apply batch modifications from a JSON file to a spec.

    Command: sdd apply-modifications <spec> --from <file.json>

    Args:
        args: Parsed command-line arguments
            - spec_id: Spec ID to modify
            - from_file: Path to modifications JSON file
            - dry_run: If True, show what would be modified without applying
            - output: Optional output path for modified spec
        printer: PrettyPrinter instance for formatted output

    Returns:
        Exit code (0 for success, 1 for error)
    """
    json_mode = is_json_mode(args)

    # Find specs directory
    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        printer.detail("Looked for specs/active/, specs/completed/, specs/archived/")
        printer.info("\nTroubleshooting:")
        printer.detail("1. Verify you're in the correct project directory")
        printer.detail("2. Check that specs/ folder exists with subfolders: pending/, active/, completed/, archived/")
        printer.detail("3. Or specify path explicitly: --specs-dir /path/to/specs")
        return 1

    # Find spec file
    spec_file = find_spec_file(args.spec_id, specs_dir)
    if not spec_file:
        printer.error(f"Spec file not found for: {args.spec_id}")
        printer.detail(f"Searched in: {specs_dir}/active, {specs_dir}/completed, {specs_dir}/archived, {specs_dir}/pending")
        printer.info("\nNext steps:")
        printer.detail("1. List available specs: sdd list-specs")
        printer.detail(f"2. Verify spec ID format matches filename (without .json)")
        printer.detail(f"3. Check if spec is in pending/ folder: {specs_dir}/pending/")
        return 1

    # Verify modifications file exists
    mod_file = Path(args.from_file)
    if not mod_file.exists():
        printer.error(f"Modifications file not found: {args.from_file}")
        printer.info("\nNext steps:")
        printer.detail("1. Verify the file path is correct (use absolute path or relative to current directory)")
        printer.detail("2. Parse review feedback first: sdd parse-review <spec-id> --review report.md --output mods.json")
        printer.detail("3. Or create manually - see format: sdd apply-modifications --help")
        return 1

    # Load spec
    spec_data = load_json_spec(args.spec_id, specs_dir)
    if not spec_data:
        printer.error("Failed to load spec file")
        return 1

    # Dry run mode - preview changes
    if args.dry_run:
        try:
            with open(mod_file, 'r') as f:
                mod_data = json.load(f)
        except Exception as e:
            printer.error(f"Failed to parse modifications file: {str(e)}")
            return 1

        modifications = mod_data.get("modifications", [])
        sample_ops = []
        for mod in modifications[:10]:
            sample_ops.append({
                'operation': mod.get('operation', 'unknown'),
                'node_id': mod.get('node_id') or mod.get('task_id'),
                'field': mod.get('field'),
                'parent_id': mod.get('parent_id') or mod.get('new_parent_id'),
            })

        dry_run_payload = {
            'spec_id': args.spec_id,
            'dry_run': True,
            'source_file': str(mod_file),
            'operation_count': len(modifications),
            'sample_operations': sample_ops,
        }

        if _spec_mod_output_json(dry_run_payload, args, SPEC_MOD_DRY_RUN_ESSENTIAL, SPEC_MOD_DRY_RUN_STANDARD):
            return 0

        printer.info(f"Dry run: {len(modifications)} operation(s) parsed from {mod_file}")
        for i, entry in enumerate(sample_ops, 1):
            op = entry['operation'].upper()
            details = entry['node_id'] or entry['parent_id'] or ''
            suffix = f" ({details})" if details else ""
            printer.detail(f"  {i}. {op}{suffix}")
            if entry['field']:
                printer.detail(f"     Field: {entry['field']}")

        remaining = len(modifications) - len(sample_ops)
        if remaining > 0:
            printer.detail(f"  ...and {remaining} more operation(s)")

        printer.info("No changes were made (dry run).")
        return 0

    # Apply modifications
    try:
        result = apply_modifications(spec_data, str(mod_file))
    except FileNotFoundError as e:
        printer.error(str(e))
        return 1
    except json.JSONDecodeError as e:
        printer.error(f"Invalid JSON in modifications file: {str(e)}")
        printer.info("\nNext steps:")
        printer.detail("1. Validate JSON syntax: Use a JSON validator or 'python -m json.tool < file.json'")
        printer.detail("2. Check for common issues: trailing commas, unescaped quotes, missing brackets")
        printer.detail("3. See format documentation in MODIFICATIONS_FORMAT.md")
        return 1
    except ValueError as e:
        printer.error(f"Invalid modification format: {str(e)}")
        printer.info("\nNext steps:")
        printer.detail("1. Verify operation type is one of: add_node, remove_node, update_node_field, move_node")
        printer.detail("2. Check required fields for your operation type")
        printer.detail("3. Use --dry-run first to preview changes without applying")
        printer.detail("4. See examples in MODIFICATIONS_FORMAT.md")
        return 1
    except Exception as e:
        printer.error(f"Failed to apply modifications: {str(e)}")
        return 1

    # Display results
    total = result["total_operations"]
    successful = result["successful"]
    failed = result["failed"]
    output_path = None

    op_summary = {}
    for op_result in result["results"]:
        if op_result.get("success"):
            op_type = op_result["operation"].get("operation", "unknown")
            op_summary[op_type] = op_summary.get(op_type, 0) + 1

    if not json_mode:
        if result["success"]:
            printer.success(f"✓ Applied {successful}/{total} modifications successfully")
        else:
            printer.warning(f"⚠ Applied {successful}/{total} modifications ({failed} failed)")

        if failed > 0:
            printer.header("\nFailed Operations:")
            for i, op_result in enumerate(result["results"]):
                if not op_result.get("success"):
                    operation = op_result["operation"]
                    printer.error(f"  {i+1}. {operation.get('operation', 'unknown')}")
                    printer.detail(f"     Error: {op_result.get('error', 'Unknown error')}")

    # Save modified spec
    if successful > 0:
        output_file = Path(args.output) if args.output else spec_file

        try:
            with open(output_file, 'w') as f:
                json.dump(spec_data, f, indent=2)

            output_path = str(output_file)

            if not json_mode:
                printer.success(f"\n✓ Saved modified spec to: {output_file}")
                if op_summary:
                    printer.header("\nModification Summary:")
                    for op_type, count in op_summary.items():
                        printer.detail(f"  {op_type}: {count} operation(s)")

        except Exception as e:
            printer.error(f"Failed to save modified spec: {str(e)}")
            return 1

    apply_payload = {
        'spec_id': args.spec_id,
        'success': result["success"],
        'total_operations': total,
        'successful_operations': successful,
        'failed_operations': failed,
        'dry_run': False,
        'output_file': output_path,
        'source_file': str(mod_file),
        'operation_summary': op_summary,
        'error': None if result["success"] else "Some modifications failed",
    }

    if _spec_mod_output_json(apply_payload, args, SPEC_MOD_APPLY_ESSENTIAL, SPEC_MOD_APPLY_STANDARD):
        return 0 if result["success"] else 1

    return 0 if result["success"] else 1


def cmd_parse_review(args, printer):
    """
    Parse a review report and generate modification suggestions.

    Command: sdd parse-review <spec> --review <report.md> [--output suggestions.json]

    Args:
        args: Parsed command-line arguments
            - spec_id: Spec ID being reviewed
            - review: Path to review report file (markdown or JSON)
            - output: Optional output path for suggestions JSON
            - show: If True, display suggestions instead of saving
        printer: PrettyPrinter instance for formatted output

    Returns:
        Exit code (0 for success, 1 for error)
    """
    json_mode = is_json_mode(args)

    # Verify review report exists
    review_file = Path(args.review)
    if not review_file.exists():
        printer.error(f"Review report not found: {args.review}")
        return 1

    if not json_mode:
        printer.info(f"Parsing review report: {review_file}")

    # Parse review report
    try:
        result = parse_review_report(str(review_file))
    except FileNotFoundError as e:
        printer.error(str(e))
        return 1
    except Exception as e:
        printer.error(f"Failed to parse review report: {str(e)}")
        return 1

    if not result.get("success"):
        printer.error(f"Failed to parse review report: {result.get('error', 'Unknown error')}")
        return 1

    # Display metadata
    metadata = result.get("metadata", {})
    issues = result.get("issues", {})
    total_issues = sum(len(issues.get(severity, [])) for severity in ["critical", "high", "medium", "low"])
    issues_by_severity = {severity: len(issues.get(severity, [])) for severity in ["critical", "high", "medium", "low"]}
    recommendation = metadata.get("recommendation")

    if not json_mode:
        printer.success(
            f"Issues found: {total_issues} • Recommendation: {recommendation or 'UNKNOWN'}"
        )
        score = metadata.get("overall_score")
        if score is not None:
            printer.detail(f"Overall Score: {score}")
        if recommendation:
            printer.warning(f"Recommendation: {recommendation}")

        severity_handlers = {
            'critical': printer.error,
            'high': printer.warning,
            'medium': printer.detail,
            'low': printer.detail,
        }
        for severity, count in issues_by_severity.items():
            if not count:
                continue
            label = severity.upper()
            handler = severity_handlers.get(severity, printer.detail)
            handler(f"{label}: {count} issue(s)")

    # Generate modification suggestions
    if not json_mode:
        printer.info("\nGenerating modification suggestions...")
    suggestions = suggest_modifications(issues)

    if not json_mode:
        printer.success(f"✓ Generated {len(suggestions)} modification suggestion(s)")

    # Display or save suggestions
    output_path = None
    if args.show:
        # Display suggestions to console
        if not json_mode:
            if suggestions:
                printer.header("\nModification Suggestions:")
                for i, mod in enumerate(suggestions, 1):
                    printer.detail(f"\n{i}. {mod.get('operation', 'unknown').upper()}")
                    if mod.get('node_id'):
                        printer.detail(f"   Node: {mod['node_id']}")
                    if mod.get('field'):
                        printer.detail(f"   Field: {mod['field']}")
                    if mod.get('reason'):
                        printer.detail(f"   Reason: {mod['reason']}")
                    if mod.get('parent_id'):
                        printer.detail(f"   Parent: {mod['parent_id']}")
            else:
                printer.info("No modifications suggested")
        output_path = None
    else:
        # Save to file
        output_file = Path(args.output) if args.output else review_file.with_suffix('.suggestions.json')

        suggestions_data = {
            "spec_id": metadata.get("spec_id", args.spec_id),
            "review_file": str(review_file),
            "generated_at": metadata.get("recommendation", ""),
            "modifications": suggestions
        }

        try:
            with open(output_file, 'w') as f:
                json.dump(suggestions_data, f, indent=2)

            output_path = str(output_file)
            if not json_mode:
                printer.success(f"\n✓ Saved {len(suggestions)} suggestion(s) to: {output_file}")

        except Exception as e:
            printer.error(f"Failed to save suggestions: {str(e)}")
            return 1

    review_payload = {
        'spec_id': metadata.get("spec_id", args.spec_id),
        'review_file': str(review_file),
        'recommendation': recommendation,
        'issues_total': total_issues,
        'issues_by_severity': issues_by_severity,
        'suggestion_count': len(suggestions),
        'display_mode': 'show' if args.show else 'save',
        'output_file': output_path if not args.show else None,
    }

    if _spec_mod_output_json(
        review_payload,
        args,
        SPEC_MOD_PARSE_REVIEW_ESSENTIAL,
        SPEC_MOD_PARSE_REVIEW_STANDARD,
    ):
        return 0

    return 0


def register_spec_mod(subparsers, parent_parser):
    """
    Register spec modification commands.

    Args:
        subparsers: ArgumentParser subparsers object
        parent_parser: Parent parser with global options
    """
    # apply-modifications command
    parser_apply = subparsers.add_parser(
        'apply-modifications',
        parents=[parent_parser],
        help='Apply batch modifications from a JSON file to a spec'
    )
    parser_apply.add_argument(
        'spec_id',
        help='Spec ID to modify (e.g., user-auth-2025-10-01-001)'
    )
    parser_apply.add_argument(
        '--from',
        dest='from_file',
        required=True,
        help='Path to modifications JSON file'
    )
    parser_apply.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without applying them'
    )
    parser_apply.add_argument(
        '--output',
        help='Output path for modified spec (default: overwrite original)'
    )
    parser_apply.set_defaults(func=cmd_apply_modifications)

    # parse-review command
    parser_parse = subparsers.add_parser(
        'parse-review',
        parents=[parent_parser],
        help='Parse review report and generate modification suggestions'
    )
    parser_parse.add_argument(
        'spec_id',
        help='Spec ID being reviewed'
    )
    parser_parse.add_argument(
        '--review',
        required=True,
        help='Path to review report file (.md or .json)'
    )
    parser_parse.add_argument(
        '--output',
        help='Output path for suggestions JSON (default: <review>.suggestions.json)'
    )
    parser_parse.add_argument(
        '--show',
        action='store_true',
        help='Display suggestions instead of saving to file'
    )
    parser_parse.set_defaults(func=cmd_parse_review)
