#!/usr/bin/env python3
"""
SDD Plan CLI - Specification creation and planning commands.
"""

import argparse
import sys
import json
from pathlib import Path
from claude_skills.common import PrettyPrinter
from claude_skills.sdd_plan import (
    list_templates,
    get_template_description,
    create_spec_interactive,
    analyze_codebase,
    get_project_context,
    find_specs_directory,
)


def cmd_create(args, printer):
    """Create a new specification."""
    printer.info(f"Creating new specification: {args.name}")

    # Determine template
    template = args.template or "medium"

    # Find specs directory
    specs_dir = find_specs_directory()
    if not specs_dir:
        printer.warning("No specs/ directory found, creating specs/active/")
        specs_dir = Path("specs")

    # Create spec (in active subfolder)
    success, message, spec = create_spec_interactive(
        title=args.name,
        template=template,
        specs_dir=specs_dir / "active"
    )

    if not success:
        printer.error(message)
        return 1

    printer.success(message)

    # Show spec info
    printer.detail(f"Template: {template}")
    printer.detail(f"Spec ID: {spec['spec_id']}")
    printer.detail(f"Phases: {len([k for k in spec['hierarchy'] if k.startswith('phase-')])}")
    printer.detail(f"Estimated hours: {spec['metadata']['estimated_hours']}")

    printer.info("\nNext steps:")
    printer.detail("1. Edit the spec file to add detailed tasks")
    printer.detail(f"2. Validate: sdd validate {spec['spec_id']}.json")
    printer.detail("3. Review: sdd review (if sdd-plan-review is available)")
    printer.detail("4. Start work: sdd next-task")

    return 0


def cmd_analyze(args, printer):
    """Analyze codebase for planning."""
    directory = Path(args.directory).resolve()

    if not directory.exists():
        printer.error(f"Directory not found: {directory}")
        return 1

    printer.info(f"Analyzing codebase: {directory}")

    # Get project context
    context = get_project_context(directory)

    # Display results
    printer.header("Project Context")

    if context["has_specs"]:
        printer.success(f"✓ Specs directory: {context['specs_directory']}")
    else:
        printer.warning("✗ No specs directory found")
        printer.detail("  Consider creating: mkdir -p specs/active")

    # Codebase analysis
    analysis = context["codebase_analysis"]

    printer.header("\nCodebase Documentation")

    if analysis["success"] and analysis["has_documentation"]:
        printer.success("✓ Documentation available (doc-query)")

        stats = analysis["stats"]
        printer.detail(f"  Total modules: {stats.get('total_modules', 'N/A')}")
        printer.detail(f"  Total classes: {stats.get('total_classes', 'N/A')}")
        printer.detail(f"  Total functions: {stats.get('total_functions', 'N/A')}")
        printer.detail(f"  Average complexity: {stats.get('average_complexity', 'N/A')}")

        printer.info("\nYou can use doc-query for faster spec planning:")
        printer.detail("  doc-query search <keyword>")
        printer.detail("  doc-query context <feature>")
        printer.detail("  doc-query dependencies <file>")

    else:
        printer.warning("✗ No documentation found")
        printer.detail(f"  Reason: {analysis.get('error', 'Unknown')}")

        if analysis.get("error") == "doc-query not installed":
            printer.info("\nInstall doc-query for faster analysis:")
            printer.detail("  pip install tree-sitter tree-sitter-python")
            printer.detail("  Then run: codebase-documentation generate")
        else:
            printer.info("\nGenerate documentation for faster analysis:")
            printer.detail("  codebase-documentation generate")
            printer.detail("\nThis enables 10x faster spec planning")

    return 0


def cmd_template(args, printer):
    """Work with spec templates."""
    action = args.action

    if action == "list":
        printer.header("Available Templates")

        templates = list_templates()
        for template_id, template_info in templates.items():
            printer.info(f"\n{template_id}")
            printer.detail(f"  Name: {template_info['name']}")
            printer.detail(f"  Description: {template_info['description']}")
            printer.detail(f"  Phases: {template_info['phases']}")
            printer.detail(f"  Est. hours: {template_info['estimated_hours']}")
            printer.detail(f"  Recommended for: {template_info['recommended_for']}")

        printer.info("\nUsage: sdd create <name> --template <template-id>")

    elif action == "show":
        # Require template name
        if not hasattr(args, 'template_name') or not args.template_name:
            printer.error("Template name required for 'show' action")
            printer.detail("Usage: sdd template show <template-name>")
            return 1

        template_desc = get_template_description(args.template_name)
        printer.info(template_desc)

    elif action == "apply":
        printer.warning("'apply' action not yet implemented")
        printer.detail("Use 'sdd create <name> --template <template-id>' instead")

    return 0


def register_plan(subparsers, parent_parser):
    """Register plan subcommands for unified CLI."""

    # create command
    parser_create = subparsers.add_parser(
        'create',
        parents=[parent_parser],
        help='Create new specification'
    )
    parser_create.add_argument('name', help='Specification name')
    parser_create.add_argument(
        '--template',
        choices=['simple', 'medium', 'complex', 'security'],
        default='medium',
        help='Template to use (default: medium)'
    )
    parser_create.set_defaults(func=cmd_create)

    # analyze command
    parser_analyze = subparsers.add_parser(
        'analyze',
        parents=[parent_parser],
        help='Analyze codebase for planning'
    )
    parser_analyze.add_argument(
        'directory',
        nargs='?',
        default='.',
        help='Directory to analyze (default: current)'
    )
    parser_analyze.set_defaults(func=cmd_analyze)

    # template command
    parser_template = subparsers.add_parser(
        'template',
        parents=[parent_parser],
        help='Manage spec templates'
    )
    parser_template.add_argument(
        'action',
        choices=['list', 'show', 'apply'],
        help='Action to perform'
    )
    parser_template.add_argument(
        'template_name',
        nargs='?',
        help='Template name (required for show/apply)'
    )
    parser_template.set_defaults(func=cmd_template)
