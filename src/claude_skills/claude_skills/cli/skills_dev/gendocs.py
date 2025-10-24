"""
Generate Documentation Commands

Generate SKILL.md documentation from CLI argparse definitions.
Wraps the existing generate_docs.py functionality.
"""

import sys
from pathlib import Path

from claude_skills.common import PrettyPrinter


def cmd_gendocs(args, printer: PrettyPrinter) -> int:
    """Generate documentation for a skill."""
    # Import and use the existing generate_docs module
    from claude_skills.dev_tools import generate_docs

    # Build args for generate_docs.main()
    sys_argv_backup = sys.argv
    sys.argv = ['gendocs', args.skill_name]

    if args.output_file:
        sys.argv.extend(['--output-file', args.output_file])

    if args.sections:
        sys.argv.extend(['--sections'] + args.sections)

    try:
        # Call the existing generate_docs main function
        result = generate_docs.main()
        return result if result is not None else 0
    except SystemExit as e:
        return e.code if e.code is not None else 0
    finally:
        sys.argv = sys_argv_backup


def register_gendocs(subparsers, parent_parser):
    """Register gendocs command."""
    gendocs_parser = subparsers.add_parser(
        'gendocs',
        parents=[parent_parser],
        help='Generate skill documentation',
        description='Generate SKILL.md documentation from CLI argparse definitions'
    )

    gendocs_parser.add_argument(
        'skill_name',
        help='Skill name to generate docs for (e.g., sdd-validate, sdd-next)'
    )
    gendocs_parser.add_argument(
        '--output-file',
        help='Output file path (default: stdout)'
    )
    gendocs_parser.add_argument(
        '--sections',
        nargs='+',
        help='Sections to generate (global, commands)'
    )
    gendocs_parser.set_defaults(func=cmd_gendocs)
