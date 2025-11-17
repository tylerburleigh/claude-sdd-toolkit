#!/usr/bin/env python3
"""
Work Mode - Get the configured work mode for sdd-next.

Returns the work_mode setting from sdd_config.json which controls how sdd-next
executes tasks (single task with approval vs autonomous phase completion).

Usage:
  sdd get-work-mode --json

Returns:
  {
    "work_mode": "single"  // or "autonomous"
  }
"""

from claude_skills.common.sdd_config import get_work_mode
from claude_skills.common.json_output import output_json


def cmd_get_work_mode(args, printer):
    """
    Handler for 'sdd get-work-mode' command.

    Reads the work_mode setting from .claude/sdd_config.json and outputs it as JSON.

    Args:
        args: Parsed arguments from ArgumentParser
        printer: PrettyPrinter instance for output (not used for JSON-only command)
    """
    work_mode = get_work_mode()

    # Always output as JSON
    result = {"work_mode": work_mode}
    output_json(result, compact=getattr(args, 'compact', True))


def register_get_work_mode(subparsers, parent_parser):
    """
    Register 'get-work-mode' subcommand for unified SDD CLI.

    Args:
        subparsers: ArgumentParser subparsers object
        parent_parser: Parent parser with global options
    """
    parser = subparsers.add_parser(
        'get-work-mode',
        parents=[parent_parser],
        help='Get the configured work mode for sdd-next',
        description='Returns the work_mode setting from .claude/sdd_config.json (values: "single" or "autonomous")'
    )

    parser.set_defaults(func=cmd_get_work_mode)
