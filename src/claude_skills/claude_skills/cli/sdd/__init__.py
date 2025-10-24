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
    Reorder command line arguments to support global options before subcommand.
    
    Argparse doesn't natively support global options before subcommand names.
    This function reorders arguments to put global options after the subcommand.
    
    Args:
        cmd_line: List of command line arguments
        
    Returns:
        Reordered list of arguments
    """
    # Define global options that take values
    global_opts_with_values = {'--path', '--specs-dir', '--docs-path'}
    
    # Find the subcommand position (first non-option argument that's not a value)
    subcommand_pos = None
    i = 0
    while i < len(cmd_line):
        arg = cmd_line[i]
        if arg.startswith('-'):
            # This is an option
            if arg in global_opts_with_values and i + 1 < len(cmd_line):
                # Skip the option and its value
                i += 2
            else:
                # Boolean option, skip it
                i += 1
        else:
            # This is a non-option argument - it's the subcommand
            subcommand_pos = i
            break
    
    # If no subcommand found or it's already first, return as-is
    if subcommand_pos is None or subcommand_pos == 0:
        return cmd_line
    
    # Extract global options and their values
    global_opts = []
    i = 0
    while i < subcommand_pos:
        arg = cmd_line[i]
        if arg.startswith('-'):
            global_opts.append(arg)
            # If it's an option with a value, add the next arg too
            if arg in global_opts_with_values and i + 1 < subcommand_pos:
                global_opts.append(cmd_line[i + 1])
                i += 2
            else:
                i += 1
        else:
            i += 1
    
    # If no global options before subcommand, return as-is
    if not global_opts:
        return cmd_line
    
    # Reorder: subcommand first, then global options, then remaining args
    subcommand = cmd_line[subcommand_pos]
    remaining = cmd_line[subcommand_pos + 1:]
    
    # Remove global options from remaining (they're already in global_opts)
    remaining = [arg for arg in remaining if arg not in global_opts]
    
    return [subcommand] + global_opts + remaining


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
    args = parser.parse_args(cmd_line)

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
