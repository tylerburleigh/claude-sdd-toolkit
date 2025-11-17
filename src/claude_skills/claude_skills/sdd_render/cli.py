"""CLI command handlers for sdd render."""

import json
from pathlib import Path
from typing import Any, Optional

from claude_skills.common import (
    find_specs_directory,
    load_json_spec,
    ensure_human_readable_directory,
    PrettyPrinter
)
from claude_skills.common.json_output import output_json
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    RENDER_SPEC_ESSENTIAL,
    RENDER_SPEC_STANDARD,
)
from .renderer import SpecRenderer
from .orchestrator import AIEnhancedRenderer


def _parse_model_override(values: Optional[list[str]]) -> Optional[object]:
    """Normalize CLI-provided model overrides."""
    if not values:
        return None

    overrides: dict[str, str] = {}
    default_override: Optional[str] = None

    for raw_value in values:
        if not raw_value:
            continue
        entry = raw_value.strip()
        if not entry:
            continue

        separator_index = -1
        for separator in ("=", ":"):
            if separator in entry:
                separator_index = entry.find(separator)
                break

        if separator_index > 0:
            key = entry[:separator_index].strip()
            value = entry[separator_index + 1 :].strip()
            if key and value:
                overrides[key] = value
            continue

        default_override = entry

    if overrides:
        if default_override:
            overrides.setdefault("default", default_override)
        return overrides

    return default_override


def _render_output_json(data: dict[str, Any], args) -> bool:
    """Emit filtered JSON output if requested."""
    if getattr(args, 'json', False):
        payload = prepare_output(data, args, RENDER_SPEC_ESSENTIAL, RENDER_SPEC_STANDARD)
        output_json(payload, getattr(args, 'compact', False))
        return True
    return False


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
    enhancement_level = getattr(args, 'enhancement_level', None)
    mode = getattr(args, 'mode', None)
    model_override = _parse_model_override(getattr(args, 'model', None))

    # If enhancement_level is specified, imply enhanced mode
    # This makes --mode truly optional when using --enhancement-level
    if enhancement_level is not None and mode is None:
        mode = 'enhanced'
    elif mode is None:
        # Default to enhanced mode with standard level
        mode = 'enhanced'
        if enhancement_level is None:
            enhancement_level = 'standard'

    # Set default enhancement level if not specified
    if enhancement_level is None:
        enhancement_level = 'standard'

    show_progress = getattr(args, 'verbose', False) and not getattr(args, 'json', False)
    if show_progress:
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
    # Try to resolve relative paths first, fall back to spec name lookup if not found
    spec_file = None
    if spec_id.endswith('.json'):
        path = Path(spec_id)
        # Resolve path (handles both absolute and relative paths)
        resolved_path = path.resolve()
        
        if resolved_path.exists():
            spec_file = resolved_path
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
        # If file doesn't exist at resolved path, fall through to spec name lookup
        # Extract spec name from path (e.g., "specs/pending/my-spec.json" -> "my-spec")
        if spec_file is None:
            spec_id = path.stem
    
    # If we didn't load from a direct file path, treat it as a spec name and search
    if spec_file is None:
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
    fallback_used = False
    fallback_reason: Optional[str] = None

    try:
        # Choose renderer based on mode
        if mode == 'enhanced':
            # Try AI-enhanced rendering with fallback to basic
            try:
                # Use AI-enhanced renderer with full pipeline
                renderer = AIEnhancedRenderer(
                    spec_data,
                    model_override=model_override,
                )
                # Enable AI features with specified enhancement level
                markdown = renderer.render(
                    output_format='markdown',
                    enable_ai=True,
                    enhancement_level=enhancement_level
                )

                if args.verbose:
                    if model_override:
                        printer.detail(f"Model override: {model_override}")
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
                fallback_used = True
                fallback_reason = str(ai_error)
                if show_progress:
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

        task_count = spec_data.get('hierarchy', {}).get('spec-root', {}).get('total_tasks', 0)
        result = {
            'spec_id': spec_data.get('spec_id', spec_id),
            'output_path': str(output_path),
            'mode': mode,
            'enhancement_level': enhancement_level,
            'fallback_used': fallback_used,
            'fallback_reason': fallback_reason,
            'model_override': model_override,
            'output_size': len(markdown),
            'task_count': task_count,
        }

        if _render_output_json(result, args):
            return 0

        printer.success(f"✓ Rendered spec to {output_path}")

        if args.verbose:
            printer.detail(f"Total tasks: {task_count}")
            printer.detail(f"Output size: {len(markdown)} characters")
            printer.detail(f"Rendering mode: {mode}")
            if fallback_used:
                printer.detail("Fallback renderer used due to AI enhancement failure")

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
        default=None,
        help='Rendering mode: basic (fast, SpecRenderer) or enhanced (AI features). Default: enhanced. Automatically set to enhanced when --enhancement-level is specified.'
    )

    parser.add_argument(
        '--enhancement-level',
        choices=['full', 'standard', 'summary'],
        default=None,
        help='AI enhancement level: summary (exec summary only), standard (base + narrative, default), full (all features). Automatically enables enhanced mode.'
    )
    parser.add_argument(
        '--model',
        action='append',
        metavar='MODEL',
        help='Override AI model selection (repeat for per-agent overrides, e.g., gemini=gemini-pro).',
    )

    parser.set_defaults(func=cmd_render)
