"""Shared argument groups for unified CLI."""
import argparse


def create_global_parent_parser():
    """
    Create a parent parser with global options that can be inherited by subparsers.

    This allows global options like --verbose, --debug, etc. to work universally
    across all command levels, including nested subcommands.

    Returns:
        ArgumentParser configured with global options and add_help=False
    """
    parent_parser = argparse.ArgumentParser(add_help=False)
    add_global_options(parent_parser)
    return parent_parser


def add_global_options(parser):
    """Add global options available to all commands."""
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress non-essential output'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output in JSON format'
    )
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
