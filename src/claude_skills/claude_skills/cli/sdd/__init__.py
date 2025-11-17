#!/usr/bin/env python3
"""
Unified SDD CLI - Single entry point for all SDD commands.
"""
import sys
import argparse
import io
from pathlib import Path

from claude_skills.common import PrettyPrinter
from claude_skills.common.metrics import track_metrics
from claude_skills.common.sdd_config import load_sdd_config
from claude_skills.cli.sdd.options import add_global_options, create_global_parent_parser, get_verbosity_level
from claude_skills.cli.sdd.registry import register_all_subcommands


def _get_version():
    """Get package version from metadata."""
    try:
        from importlib.metadata import version
        return version('claude-skills')
    except Exception:
        return '0.0.0-dev'


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

    # Load config for consistent defaults
    config = load_sdd_config()

    # Create a temporary parser with only global options
    temp_parser = argparse.ArgumentParser(add_help=False)
    add_global_options(temp_parser, config)

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
    defaults = {
        'path': '.',
        'quiet': False,
        'json': None,
        'compact': None,
        'debug': False,
        'verbose': False,
        'no_color': False,
        'refresh': False,
        'skip_refresh': False,
        'no_staleness_check': False,
        'specs_dir': None,
        'docs_path': None
    }

    for opt, value in vars(known_args).items():
        # Skip None and default values to avoid cluttering the command line
        if value is None or value == defaults.get(opt):
            continue
        if value is True:
            # Boolean flag set to True
            opt_name = f"--{opt.replace('_', '-')}"
            global_opts.append(opt_name)
        elif value is False:
            # Boolean flag set to False (use --no- prefix)
            opt_name = f"--no-{opt.replace('_', '-')}"
            global_opts.append(opt_name)
        else:
            # Option with value
            opt_name = f"--{opt.replace('_', '-')}"
            global_opts.append(opt_name)
            global_opts.append(str(value))

    # Check if there's a nested subcommand (e.g., "doc stats")
    # If after_subcommand starts with a non-option argument, it's likely a nested subcommand
    # In this case, put global options at the END for proper argparse handling with nested subparsers
    has_nested_subcommand = False
    if after_subcommand and not after_subcommand[0].startswith('-'):
        # First argument after subcommand doesn't start with '-', likely a nested subcommand
        has_nested_subcommand = True

    if has_nested_subcommand:
        # For nested subparsers: subcommand, before options, nested args, then global options at end
        return [subcommand] + before_subcommand + after_subcommand + global_opts
    else:
        # For single-level subparsers: subcommand, global options, before options, then remaining args
        return [subcommand] + global_opts + before_subcommand + after_subcommand


# Common command mistakes and their corrections
COMMAND_SUGGESTIONS = {
    'update': 'update-status',
}


@track_metrics('sdd')
def main():
    """Main entry point for unified SDD CLI."""
    # Store original command line for --no-json detection
    original_cmd_line = sys.argv[1:]
    # Reorder arguments to support global options before subcommand
    cmd_line = reorder_args_for_subcommand(original_cmd_line)

    # Check for common --entry-type completion mistake BEFORE parsing
    # This allows us to provide a better error message
    if 'add-journal' in cmd_line and '--entry-type' in cmd_line:
        try:
            entry_type_idx = cmd_line.index('--entry-type')
            if entry_type_idx + 1 < len(cmd_line) and cmd_line[entry_type_idx + 1] == 'completion':
                # Provide custom helpful error message immediately
                print(f"\n❌ Invalid entry type: 'completion'", file=sys.stderr)
                print(f"💡 Did you mean: --entry-type status_change?", file=sys.stderr)
                print(f"\nNote: 'completion' is a template option for bulk-journal, not an entry type.", file=sys.stderr)
                print(f"Valid entry types: status_change, deviation, blocker, decision, note\n", file=sys.stderr)
                sys.exit(2)
        except (ValueError, IndexError):
            pass

    # Load SDD configuration first
    # Config values are used as defaults, but CLI args override them
    config = load_sdd_config()

    parser = argparse.ArgumentParser(
        prog='sdd',
        description='Spec-Driven Development unified CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Add version flag
    parser.add_argument('--version', action='version',
                        version=f'%(prog)s {_get_version()}')

    # Add global options to main parser so they work in any position
    # Pass config so defaults are applied
    add_global_options(parser, config)

    # Create parent parser with global options for inheritance by subcommands
    # Pass config so nested subcommands also get config defaults
    global_parent = create_global_parent_parser(config)

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

        # If --path was provided, reload config from that location
        # This allows config-driven testing with temporary configs
        if hasattr(args, 'path') and args.path and args.path != '.':
            from pathlib import Path
            project_root = Path(args.path)
            project_config = project_root / ".claude" / "sdd_config.json"
            if project_config.exists():
                config = load_sdd_config(project_path=project_root)

        # Apply config defaults for args that weren't specified (are None)
        # Only apply default if json was not explicitly set (None means not set)
        # False means --no-json was used, True means --json was used
        # Check both original and reordered command line for --no-json to handle case
        # where it appears before subcommand and argparse sets args.json to None instead of False
        if '--no-json' in original_cmd_line or '--no-json' in cmd_line:
            args.json = False
        elif args.json is None:
            args.json = config['output']['default_mode'] == 'json'
        if args.compact is None:
            args.compact = config['output']['json_compact']

        # Determine verbosity level from flags and store in args for command handlers
        args.verbosity_level = get_verbosity_level(args, config)

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
    from claude_skills.cli.sdd.verbosity import VerbosityLevel
    verbosity = args.verbosity_level
    if getattr(args, 'json', False):
        # Force quiet mode when JSON output is enabled
        verbosity = VerbosityLevel.QUIET

    printer = PrettyPrinter(
        verbosity_level=verbosity,
        use_color=not getattr(args, 'no_color', False)
    )
    # Note: JSON output is handled by individual handlers checking args.json

    # Execute command handler (handlers receive both args and printer)
    try:
        exit_code = args.func(args, printer)
        sys.exit(exit_code or 0)
    except BrokenPipeError:
        # Silently exit when pipe is closed (e.g., when using head/tail)
        # This is standard Unix behavior - not an error
        sys.exit(0)
    except Exception as e:
        printer.error(f"Command failed: {e}")
        if getattr(args, 'debug', False):
            raise
        sys.exit(1)


if __name__ == '__main__':
    main()
