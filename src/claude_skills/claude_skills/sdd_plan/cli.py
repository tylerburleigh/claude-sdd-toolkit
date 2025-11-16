#!/usr/bin/env python3
"""
SDD Plan CLI - Specification creation and planning commands.
"""

import argparse
import sys
from pathlib import Path
from claude_skills.common import PrettyPrinter, find_specs_directory, ensure_reports_directory
from claude_skills.common.json_output import output_json
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    PLAN_CREATE_ESSENTIAL,
    PLAN_CREATE_STANDARD,
    PLAN_ANALYZE_ESSENTIAL,
    PLAN_ANALYZE_STANDARD,
    PLAN_TEMPLATE_LIST_ESSENTIAL,
    PLAN_TEMPLATE_LIST_STANDARD,
    PLAN_TEMPLATE_SHOW_ESSENTIAL,
    PLAN_TEMPLATE_SHOW_STANDARD,
)
from claude_skills.sdd_plan import (
    list_templates,
    get_template_description,
    create_spec_interactive,
    analyze_codebase,
    get_project_context,
)


def _plan_output_json(data, args, essential_fields, standard_fields):
    """Output filtered JSON if --json is enabled."""
    if getattr(args, 'json', False):
        payload = prepare_output(data, args, essential_fields, standard_fields)
        output_json(payload, getattr(args, 'compact', False))
        return True
    return False


def cmd_create(args, printer):
    """Create a new specification."""
    if getattr(args, 'verbose', False) and not getattr(args, 'json', False):
        printer.action(f"Creating new specification: {args.name}")

    template = args.template or "medium"
    default_category = getattr(args, 'category', None)

    base_path = getattr(args, 'specs_dir', None) or getattr(args, 'path', '.')
    specs_dir = find_specs_directory(base_path)
    if not specs_dir:
        specs_dir = Path(base_path) / "specs"

    ensure_reports_directory(specs_dir)

    pending_dir = specs_dir / "pending"
    success, message, spec = create_spec_interactive(
        title=args.name,
        template=template,
        specs_dir=pending_dir,
        default_category=default_category
    )

    spec_path = pending_dir / f"{spec['spec_id']}.json" if success and spec else None
    phase_count = len([node for node in spec.get('hierarchy', {}).values() if node.get('type') == 'phase']) if spec else 0
    estimated_hours = spec.get('metadata', {}).get('estimated_hours') if spec else None

    result = {
        'success': success,
        'spec_id': spec['spec_id'] if spec else None,
        'spec_path': str(spec_path.resolve()) if spec_path else None,
        'message': message,
        'template': template,
        'phase_count': phase_count,
        'estimated_hours': estimated_hours,
        'default_category': default_category,
    }

    if not success:
        printer.error(message)
        _plan_output_json(result, args, PLAN_CREATE_ESSENTIAL, PLAN_CREATE_STANDARD)
        return 1

    if _plan_output_json(result, args, PLAN_CREATE_ESSENTIAL, PLAN_CREATE_STANDARD):
        return 0

    printer.success(f"Created spec {result['spec_id']} using '{template}' template")
    printer.info(f"Phases: {phase_count} • Estimated hours: {estimated_hours}")
    printer.info(f"Saved to: {result['spec_path']}")
    printer.info(f"Next: sdd validate {result['spec_id']} → sdd activate-spec {result['spec_id']}")

    return 0


def cmd_analyze(args, printer):
    """Analyze codebase for planning."""
    directory = Path(args.directory).resolve()

    if not directory.exists():
        printer.error(f"Directory not found: {directory}")
        return 1

    context = get_project_context(directory)
    analysis = context.get("codebase_analysis") or {}
    doc_available = analysis.get("has_documentation", False)
    result = {
        'directory': str(directory),
        'has_specs': context.get("has_specs", False),
        'specs_directory': context.get("specs_directory"),
        'documentation_available': doc_available,
        'analysis_success': analysis.get("success", False),
        'analysis_error': analysis.get("error"),
        'doc_stats': analysis.get("stats", {}),
    }

    if _plan_output_json(result, args, PLAN_ANALYZE_ESSENTIAL, PLAN_ANALYZE_STANDARD):
        return 0

    specs_line = (
        f"Specs directory: {context['specs_directory']}"
        if context.get("has_specs")
        else "Specs directory: not found"
    )
    (printer.success if context.get("has_specs") else printer.warning)(specs_line)

    if doc_available:
        printer.success("Documentation: available via doc-query")
    else:
        reason = analysis.get("error") or "No doc-query data detected"
        printer.warning(f"Documentation: missing ({reason})")
        printer.info("Tip: run 'codebase-documentation generate' for richer planning data")

    if doc_available and getattr(args, 'verbose', False):
        stats = analysis.get("stats", {})
        printer.detail(
            f"Modules: {stats.get('total_modules', 'N/A')} • "
            f"Classes: {stats.get('total_classes', 'N/A')} • "
            f"Functions: {stats.get('total_functions', 'N/A')} • "
            f"Avg. complexity: {stats.get('average_complexity', 'N/A')}"
        )

    return 0


def cmd_template(args, printer):
    """Work with spec templates."""
    action = args.action

    if action == "list":
        templates = list_templates()
        condensed = [
            {
                'id': template_id,
                'name': template_info['name'],
                'phases': template_info['phases'],
                'estimated_hours': template_info['estimated_hours'],
                'recommended_for': template_info['recommended_for'],
            }
            for template_id, template_info in sorted(templates.items())
        ]
        data = {
            'templates': condensed,
            'count': len(condensed),
            'usage_hint': "sdd create <name> --template <template-id>",
        }

        if _plan_output_json(data, args, PLAN_TEMPLATE_LIST_ESSENTIAL, PLAN_TEMPLATE_LIST_STANDARD):
            return 0

        printer.info("Templates:")
        for entry in condensed:
            printer.info(
                f"{entry['id']:<8} {entry['phases']} phases / "
                f"{entry['estimated_hours']}h — {entry['recommended_for']}"
            )
        printer.info("Use: sdd create <name> --template <template-id>")

    elif action == "show":
        # Require template name
        if not hasattr(args, 'template_name') or not args.template_name:
            printer.error("Template name required for 'show' action")
            printer.detail("Usage: sdd template show <template-name>")
            return 1

        templates = list_templates()
        template = templates.get(args.template_name)
        if not template:
            message = f"Template not found: {args.template_name}"
            printer.error(message)
            _plan_output_json(
                {'template_id': args.template_name, 'template': None, 'message': message},
                args,
                PLAN_TEMPLATE_SHOW_ESSENTIAL,
                PLAN_TEMPLATE_SHOW_STANDARD,
            )
            return 1

        payload = {'template_id': args.template_name, 'template': template, 'message': "ok"}
        if _plan_output_json(payload, args, PLAN_TEMPLATE_SHOW_ESSENTIAL, PLAN_TEMPLATE_SHOW_STANDARD):
            return 0

        printer.info(get_template_description(args.template_name))

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
    parser_create.add_argument(
        '--category',
        choices=['investigation', 'implementation', 'refactoring', 'decision', 'research'],
        default=None,
        help='Default task category (overrides automatic inference). Options: investigation, implementation, refactoring, decision, research'
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
