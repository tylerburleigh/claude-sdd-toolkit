#!/usr/bin/env python3
"""
SDD Spec Modification CLI - Commands for modifying specification files.
"""

import argparse
import sys
import json
from pathlib import Path
from claude_skills.common import PrettyPrinter, find_spec_file, find_specs_directory, load_json_spec
from claude_skills.sdd_spec_mod import apply_modifications


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
    # Find specs directory
    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        printer.detail("Looked for specs/active/, specs/completed/, specs/archived/")
        return 1

    # Find spec file
    spec_file = find_spec_file(args.spec_id, specs_dir)
    if not spec_file:
        printer.error(f"Spec file not found for: {args.spec_id}")
        printer.detail(f"Searched in: {specs_dir}/active, {specs_dir}/completed, {specs_dir}/archived")
        return 1

    # Verify modifications file exists
    mod_file = Path(args.from_file)
    if not mod_file.exists():
        printer.error(f"Modifications file not found: {args.from_file}")
        return 1

    printer.info(f"Applying modifications to: {spec_file}")
    printer.detail(f"From: {mod_file}")

    # Load spec
    spec_data = load_json_spec(str(spec_file))
    if not spec_data:
        printer.error("Failed to load spec file")
        return 1

    # Dry run mode - preview changes
    if args.dry_run:
        printer.info("\n[DRY RUN MODE]")
        printer.detail("Changes that would be applied:")

        try:
            with open(mod_file, 'r') as f:
                mod_data = json.load(f)

            modifications = mod_data.get("modifications", [])
            printer.detail(f"\nTotal operations: {len(modifications)}")

            for i, mod in enumerate(modifications[:10], 1):  # Show first 10
                op = mod.get("operation", "unknown")
                printer.detail(f"  {i}. {op}")
                if op == "add_node":
                    printer.detail(f"     → Add {mod.get('node_data', {}).get('node_id', 'N/A')} to {mod.get('parent_id', 'N/A')}")
                elif op == "remove_node":
                    printer.detail(f"     → Remove {mod.get('node_id', 'N/A')}")
                elif op == "update_node_field":
                    printer.detail(f"     → Update {mod.get('node_id', 'N/A')}.{mod.get('field', 'N/A')}")
                elif op == "move_node":
                    printer.detail(f"     → Move {mod.get('node_id', 'N/A')} to {mod.get('new_parent_id', 'N/A')}")

            if len(modifications) > 10:
                printer.detail(f"  ... and {len(modifications) - 10} more operations")

        except Exception as e:
            printer.error(f"Failed to parse modifications file: {str(e)}")
            return 1

        printer.info("\nNo changes were made (dry run)")
        return 0

    # Apply modifications
    try:
        result = apply_modifications(spec_data, str(mod_file))
    except FileNotFoundError as e:
        printer.error(str(e))
        return 1
    except json.JSONDecodeError as e:
        printer.error(f"Invalid JSON in modifications file: {str(e)}")
        return 1
    except ValueError as e:
        printer.error(f"Invalid modification format: {str(e)}")
        return 1
    except Exception as e:
        printer.error(f"Failed to apply modifications: {str(e)}")
        return 1

    # Display results
    total = result["total_operations"]
    successful = result["successful"]
    failed = result["failed"]

    if result["success"]:
        printer.success(f"✓ Applied {successful}/{total} modifications successfully")
    else:
        printer.warning(f"⚠ Applied {successful}/{total} modifications ({failed} failed)")

    # Show details for failed operations
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

            printer.success(f"\n✓ Saved modified spec to: {output_file}")

            # Show summary of changes
            printer.header("\nModification Summary:")
            operations = {}
            for op_result in result["results"]:
                if op_result.get("success"):
                    op_type = op_result["operation"].get("operation", "unknown")
                    operations[op_type] = operations.get(op_type, 0) + 1

            for op_type, count in operations.items():
                printer.detail(f"  {op_type}: {count} operation(s)")

        except Exception as e:
            printer.error(f"Failed to save modified spec: {str(e)}")
            return 1

    return 0 if result["success"] else 1


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
