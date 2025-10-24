"""Shared argument groups for unified CLI."""


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
