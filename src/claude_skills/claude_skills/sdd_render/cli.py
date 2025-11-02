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
from .orchestrator import AIEnhancedRenderer


def cmd_render(args, printer: PrettyPrinter) -> int:
    """Render JSON spec to human-readable markdown.

    Supports multiple rendering modes:
    - basic: Base markdown using SpecRenderer (fast, no AI features)
    - enhanced: AI-enhanced markdown with analysis, insights, visualizations (slower, richer output)

    Args:
        args: Command line arguments
        printer: Output printer

    Returns:
        Exit code (0 for success, 1 for error)
    """
    mode = getattr(args, 'mode', 'basic')
    enhancement_level = getattr(args, 'enhancement_level', 'full')

    if mode == 'enhanced':
        if enhancement_level == 'summary':
            printer.action("Rendering spec with executive summary only...")
        elif enhancement_level == 'standard':
            printer.action("Rendering spec with standard enhancements...")
        else:  # full
            printer.action("Rendering spec with full AI enhancements...")
    else:
        printer.action("Rendering spec to markdown...")

    spec_id = args.spec_id

    # Check if spec_id is a direct path to JSON file
    if spec_id.endswith('.json') and Path(spec_id).exists():
        spec_file = Path(spec_id)
        spec_id = spec_file.stem  # Extract spec_id from filename
        try:
            with open(spec_file) as f:
                spec_data = json.load(f)
        except json.JSONDecodeError as e:
            printer.error(f"Invalid JSON in spec file: {e}")
            printer.info("The spec file contains malformed JSON. Please check the file syntax.")
            return 1
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

    # Validate spec structure
    if not isinstance(spec_data, dict):
        printer.error("Invalid spec format: expected JSON object")
        return 1

    if 'hierarchy' not in spec_data:
        printer.warning("Spec missing 'hierarchy' field - using minimal structure")
        # Create minimal hierarchy to allow rendering
        spec_data['hierarchy'] = {
            'spec-root': {
                'type': 'root',
                'title': spec_data.get('project_metadata', {}).get('name', 'Untitled Spec'),
                'total_tasks': 0,
                'completed_tasks': 0
            }
        }

    if 'spec-root' not in spec_data.get('hierarchy', {}):
        printer.warning("Spec hierarchy missing 'spec-root' - adding default root")
        spec_data['hierarchy']['spec-root'] = {
            'type': 'root',
            'title': spec_data.get('project_metadata', {}).get('name', 'Untitled Spec'),
            'total_tasks': 0,
            'completed_tasks': 0
        }

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
        # Choose renderer based on mode
        if mode == 'enhanced':
            # Try AI-enhanced rendering with fallback to basic
            try:
                # Use AI-enhanced renderer with full pipeline
                renderer = AIEnhancedRenderer(spec_data)
                # Enable AI features with specified enhancement level
                markdown = renderer.render(
                    output_format='markdown',
                    enable_ai=True,
                    enhancement_level=enhancement_level
                )

                if args.verbose:
                    printer.detail("AI enhancement pipeline:")
                    pipeline_status = renderer.get_pipeline_status()
                    for stage, implemented in pipeline_status.items():
                        status = "✓ Implemented" if implemented else "⧗ Planned"
                        printer.detail(f"  - {stage}: {status}")

                    printer.detail(f"Enhancement level: {enhancement_level}")
                    if enhancement_level == 'summary':
                        printer.detail("  Features: Executive summary only")
                    elif enhancement_level == 'standard':
                        printer.detail("  Features: Base markdown + narrative enhancements")
                    else:  # full
                        printer.detail("  Features: All AI enhancements (analysis, insights, visualizations)")

            except Exception as ai_error:
                # AI enhancement failed - fall back to basic rendering
                printer.warning(f"AI enhancement failed: {ai_error}")
                printer.info("Falling back to basic rendering...")

                if args.debug:
                    import traceback
                    traceback.print_exc()

                # Fallback to basic renderer
                renderer = SpecRenderer(spec_data)
                markdown = renderer.to_markdown()

                if args.verbose:
                    printer.detail("Fallback: Using basic SpecRenderer")

        else:
            # Use basic renderer (fast, no AI features)
            renderer = SpecRenderer(spec_data)
            markdown = renderer.to_markdown()

        # Write output
        output_path.write_text(markdown, encoding='utf-8')

        printer.success(f"✓ Rendered spec to {output_path}")

        if args.verbose:
            total_tasks = spec_data.get('hierarchy', {}).get('spec-root', {}).get('total_tasks', 0)
            printer.detail(f"Total tasks: {total_tasks}")
            printer.detail(f"Output size: {len(markdown)} characters")
            printer.detail(f"Rendering mode: {mode}")

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

    parser.add_argument(
        '--mode',
        choices=['basic', 'enhanced'],
        default='basic',
        help='Rendering mode: basic (fast, SpecRenderer) or enhanced (AI features, slower)'
    )

    parser.add_argument(
        '--enhancement-level',
        choices=['full', 'standard', 'summary'],
        default='full',
        help='Enhancement level for enhanced mode: full (all AI features), standard (base + narrative), summary (executive summary only)'
    )

    parser.set_defaults(func=cmd_render)
