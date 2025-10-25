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


def reorder_args_for_subcommand(cmd_line):
    """
    Reorder command line arguments to support global options anywhere.

    Uses argparse.parse_known_args() to robustly extract global options,
    then reorders to place them after the subcommand.

    Args:
        cmd_line: List of command line arguments

    Returns:
        Reordered list of arguments
    """
    if not cmd_line:
        return cmd_line

    # Create a temporary parser with only global options
    temp_parser = argparse.ArgumentParser(add_help=False)
    add_global_options(temp_parser)

    # Parse known global options, leaving everything else in remaining_args
    try:
        known_args, remaining_args = temp_parser.parse_known_args(cmd_line)
    except SystemExit:
        # If parsing fails (e.g., -h/--help), return as-is and let main parser handle it
        return cmd_line

    # Find the subcommand (first non-option argument in remaining_args)
    # Skip unknown options and their potential values
    subcommand = None
    subcommand_idx = None
    i = 0
    while i < len(remaining_args):
        arg = remaining_args[i]
        if arg.startswith('-'):
            # Unknown option - skip it and potentially its value
            # Peek ahead: if next arg doesn't start with -, it's likely the option's value
            if i + 1 < len(remaining_args) and not remaining_args[i + 1].startswith('-'):
                i += 2  # Skip option and its value
            else:
                i += 1  # Skip just the option
        else:
            # Found potential subcommand
            subcommand = arg
            subcommand_idx = i
            break

    # If no subcommand found, return as-is
    if subcommand is None:
        return cmd_line

    # Extract unknown options before subcommand and args after
    before_subcommand = remaining_args[:subcommand_idx]
    after_subcommand = remaining_args[subcommand_idx + 1:]

    # Reconstruct global options as list of arguments (only non-default values)
    global_opts = []
    defaults = {'path': '.', 'quiet': False, 'json': False, 'debug': False, 'verbose': False, 'no_color': False}

    for opt, value in vars(known_args).items():
        # Skip None and default values to avoid cluttering the command line
        if value is None or value == defaults.get(opt):
            continue
        if value is True:
            # Boolean flag
            opt_name = f"--{opt.replace('_', '-')}"
            global_opts.append(opt_name)
        else:
            # Option with value
            opt_name = f"--{opt.replace('_', '-')}"
            global_opts.append(opt_name)
            global_opts.append(str(value))

    # Reconstruct: subcommand, global options, unknown options, then remaining args
    return [subcommand] + global_opts + before_subcommand + after_subcommand


# Common command mistakes and their corrections
COMMAND_SUGGESTIONS = {
    'update': 'update-status',
}


@track_metrics('sdd')
def main():
    """Main entry point for unified SDD CLI."""
    # Reorder arguments to support global options before subcommand
    cmd_line = reorder_args_for_subcommand(sys.argv[1:])

    parser = argparse.ArgumentParser(
        prog='sdd',
        description='Spec-Driven Development unified CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Add global options to main parser so they work in any position
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

    # Parse args with reordered command line
    try:
        args = parser.parse_args(cmd_line)
    except SystemExit as e:
        # Check if it's an invalid command error and provide helpful suggestion
        if e.code != 0 and len(cmd_line) > 0:
            attempted_cmd = cmd_line[0]
            if attempted_cmd in COMMAND_SUGGESTIONS:
                suggestion = COMMAND_SUGGESTIONS[attempted_cmd]

                # For 'update', check second word for context-aware suggestion
                if attempted_cmd == 'update' and len(cmd_line) > 1:
                    second_word = cmd_line[1].lower()
                    if second_word in ['frontmatter', 'metadata']:
                        suggestion = 'update-frontmatter'
                    # else: keep default 'update-status' for task/status/etc

                print(f"\n❌ Unknown command: '{attempted_cmd}'", file=sys.stderr)
                print(f"💡 Did you mean: sdd {suggestion}?", file=sys.stderr)
                print(f"\nRun 'sdd --help' to see all available commands.\n", file=sys.stderr)
        raise

    # Initialize printer based on parsed global flags
    # When JSON output is requested, suppress all printer output (quiet mode)
    printer = PrettyPrinter(
        quiet=getattr(args, 'quiet', False) or getattr(args, 'json', False),
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
