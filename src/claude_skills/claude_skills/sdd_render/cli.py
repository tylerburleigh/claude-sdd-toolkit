"""CLI command handlers for sdd render."""

import json
from pathlib import Path
from typing import Optional

from claude_skills.common import (
    find_specs_directory,
    load_json_spec,
    ensure_human_readable_directory,
    PrettyPrinter
)
from .renderer import SpecRenderer


def cmd_render(args, printer: PrettyPrinter) -> int:
    """Render JSON spec to human-readable markdown.

    Args:
        args: Command line arguments
        printer: Output printer

    Returns:
        Exit code (0 for success, 1 for error)
    """
    printer.action("Rendering spec to markdown...")

    spec_id = args.spec_id

    # Check if spec_id is a direct path to JSON file
    if spec_id.endswith('.json') and Path(spec_id).exists():
        spec_file = Path(spec_id)
        spec_id = spec_file.stem  # Extract spec_id from filename
        try:
            with open(spec_file) as f:
                spec_data = json.load(f)
        except Exception as e:
            printer.error(f"Failed to load spec file: {e}")
            return 1
    else:
        # Find specs directory and load spec
        specs_dir = find_specs_directory(args.path)
        if not specs_dir:
            printer.error("Specs directory not found")
            printer.info("Expected directory structure: specs/active/, specs/completed/, or specs/archived/")
            return 1

        # Load spec using common utility
        spec_data = load_json_spec(spec_id, specs_dir)
        if not spec_data:
            printer.error(f"Spec not found: {spec_id}")
            return 1

    # Determine output path
    if args.output:
        output_path = Path(args.output)
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Default: specs/.human-readable/<spec_id>.md
        # Find specs directory and use .human-readable/ subdirectory
        specs_dir = find_specs_directory(args.path or '.')
        if specs_dir:
            hr_dir = ensure_human_readable_directory(specs_dir)
            output_path = hr_dir / f"{spec_data.get('spec_id', spec_id)}.md"
        else:
            # Fallback to old location if specs dir not found
            output_dir = Path('.specs') / 'human-readable'
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{spec_data.get('spec_id', spec_id)}.md"

    # Render spec to markdown
    try:
        renderer = SpecRenderer(spec_data)
        markdown = renderer.to_markdown()

        # Write output
        output_path.write_text(markdown, encoding='utf-8')

        printer.success(f"✓ Rendered spec to {output_path}")

        if args.verbose:
            total_tasks = spec_data.get('hierarchy', {}).get('spec-root', {}).get('total_tasks', 0)
            printer.detail(f"Total tasks: {total_tasks}")
            printer.detail(f"Output size: {len(markdown)} characters")

        return 0

    except Exception as e:
        printer.error(f"Failed to render spec: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1


def register_render(subparsers, parent_parser):
    """Register 'render' command for unified CLI.

    Args:
        subparsers: Subparser object from argparse
        parent_parser: Parent parser with global options
    """
    parser = subparsers.add_parser(
        'render',
        parents=[parent_parser],
        help='Render JSON spec to human-readable markdown documentation'
    )

    parser.add_argument(
        'spec_id',
        help='Specification ID or path to JSON file'
    )

    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: specs/.human-readable/<spec_id>.md)'
    )

    parser.add_argument(
        '--format',
        choices=['markdown', 'md'],
        default='markdown',
        help='Output format (currently only markdown supported)'
    )

    parser.set_defaults(func=cmd_render)
