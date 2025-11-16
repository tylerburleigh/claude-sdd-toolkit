"""Shared argument groups for unified CLI."""
import argparse
from claude_skills.cli.sdd.verbosity import VerbosityLevel


def create_global_parent_parser(config=None):
    """
    Create a parent parser with global options that can be inherited by subparsers.

    This allows global options like --verbose, --debug, etc. to work universally
    across all command levels, including nested subcommands.

    Args:
        config: Optional config dict with defaults (loaded from sdd_config.json)

    Returns:
        ArgumentParser configured with global options and add_help=False
    """
    parent_parser = argparse.ArgumentParser(add_help=False)
    add_global_options(parent_parser, config)
    return parent_parser


def add_global_options(parser, config=None):
    """Add global options available to all commands.

    Args:
        parser: ArgumentParser instance to add options to
        config: Optional config dict with defaults (loaded from sdd_config.json)
    """
    # Load config defaults if not provided
    if config is None:
        from claude_skills.common.sdd_config import load_sdd_config
        config = load_sdd_config()

    # Verbosity options - mutually exclusive
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Minimal output - essential data only, omit empty fields'
    )
    verbosity_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Detailed output - includes debug information and metrics'
    )

    # JSON output - use mutually exclusive group for proper default handling
    # Check new config format first, then fall back to deprecated keys
    default_mode = config['output'].get('default_mode', config['output'].get('default_format', 'rich'))
    is_json_default = default_mode == 'json'

    json_group = parser.add_mutually_exclusive_group()
    json_group.add_argument(
        '--json',
        action='store_const',
        const=True,
        dest='json',
        help=f"Output in JSON format (default: {'enabled' if is_json_default else 'disabled'} from config)"
    )
    json_group.add_argument(
        '--no-json',
        action='store_const',
        const=False,
        dest='json',
        help='Disable JSON output (override config)'
    )
    # Don't set default here - will be set after config reload in main()
    parser.set_defaults(json=None)

    # Compact formatting - use mutually exclusive group
    # Check new config format first, then fall back to deprecated key
    json_compact = config['output'].get('json_compact', config['output'].get('compact', True))

    compact_group = parser.add_mutually_exclusive_group()
    compact_group.add_argument(
        '--compact',
        action='store_const',
        const=True,
        dest='compact',
        help=f"Use compact JSON formatting (default: {'enabled' if json_compact else 'disabled'} from config)"
    )
    compact_group.add_argument(
        '--no-compact',
        action='store_const',
        const=False,
        dest='compact',
        help='Disable compact formatting (override config)'
    )
    # Don't set default here - will be set after config reload in main()
    parser.set_defaults(compact=None)
    parser.add_argument(
        '--path',
        type=str,
        default='.',
        help='Project root path (default: current directory)'
    )
    parser.add_argument(
        '--specs-dir',
        type=str,
        help='Specs directory (auto-detected if not specified)'
    )
    parser.add_argument(
        '--docs-path',
        type=str,
        help='Path to generated documentation (auto-detected when omitted, used by doc commands)'
    )
    parser.add_argument(
        '--refresh',
        action='store_true',
        help='(Deprecated: now default behavior) Auto-regenerate documentation if stale before querying (doc commands only)'
    )
    parser.add_argument(
        '--skip-refresh',
        action='store_true',
        help='Skip auto-regeneration of stale documentation for faster queries (doc commands only)'
    )
    parser.add_argument(
        '--no-staleness-check',
        action='store_true',
        help='Skip documentation staleness check entirely (implies --skip-refresh, doc commands only)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode with full stack traces'
    )
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )


def add_spec_options(parser):
    """Add common spec-related arguments."""
    parser.add_argument(
        'spec_id',
        help='Specification ID'
    )


def add_task_options(parser):
    """Add common task-related arguments."""
    parser.add_argument(
        'task_id',
        help='Task ID'
    )


def get_verbosity_level(args, config=None):
    """Get the verbosity level from parsed arguments.

    Args:
        args: Parsed argparse.Namespace
        config: Optional config dict (for default level)

    Returns:
        VerbosityLevel enum value
    """
    try:
        return VerbosityLevel.from_args(args, config)
    except ValueError as e:
        # Both --quiet and --verbose specified
        raise argparse.ArgumentTypeError(str(e))
