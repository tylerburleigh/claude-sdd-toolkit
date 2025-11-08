"""Shared argument groups for unified CLI."""
import argparse


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

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress non-essential output'
    )

    # JSON output - use mutually exclusive group for proper default handling
    # Check new config format first, then fall back to deprecated keys
    default_mode = config['output'].get('default_mode', config['output'].get('default_format', 'text'))
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
    # Set default based on config - important: use actual boolean, not None!
    parser.set_defaults(json=is_json_default)

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
    # Set default based on config - important: use actual boolean, not None!
    parser.set_defaults(compact=json_compact)
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
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output (info messages)'
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
