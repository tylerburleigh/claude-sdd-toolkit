#!/usr/bin/env python3
"""
Unified SDD CLI - Single entry point for all SDD commands.
"""
import sys
import argparse
from pathlib import Path

from claude_skills.common import PrettyPrinter
from claude_skills.common.metrics import track_metrics
from claude_skills.cli.sdd.options import add_global_options, create_global_parent_parser
from claude_skills.cli.sdd.registry import register_all_subcommands


@track_metrics('sdd')
def main():
    """Main entry point for unified SDD CLI."""
    parser = argparse.ArgumentParser(
        prog='sdd',
        description='Spec-Driven Development unified CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Add global options to main parser
    add_global_options(parser)

    # Create parent parser with global options for inheritance by subcommands
    global_parent = create_global_parent_parser()

    # Create subparsers
    subparsers = parser.add_subparsers(
        title='commands',
        dest='command',
        required=True
    )

    # CRITICAL: Register subcommands BEFORE parsing
    # Pass parent parser so nested subcommands can inherit global options
    register_all_subcommands(subparsers, global_parent)

    # Parse args (single pass, after subcommands are registered)
    args = parser.parse_args()

    # Initialize printer based on parsed global flags
    printer = PrettyPrinter(
        quiet=getattr(args, 'quiet', False),
        verbose=getattr(args, 'verbose', False),
        use_color=not getattr(args, 'no_color', False)
    )
    # Note: JSON output is handled by individual handlers checking args.json

    # Execute command handler (handlers receive both args and printer)
    try:
        exit_code = args.func(args, printer)
        sys.exit(exit_code or 0)
    except Exception as e:
        printer.error(f"Command failed: {e}")
        if getattr(args, 'debug', False):
            raise
        sys.exit(1)


if __name__ == '__main__':
    main()
