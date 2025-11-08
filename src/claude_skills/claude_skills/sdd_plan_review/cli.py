#!/usr/bin/env python3
"""
SDD Plan Review CLI - Multi-model specification review commands.

Uses external AI CLI tools (gemini, codex, cursor-agent) to review specs
from multiple perspectives and provide actionable feedback.
"""

import argparse
import sys
import json
from pathlib import Path
from claude_skills.common import (
    PrettyPrinter,
    load_json_spec,
    find_specs_directory,
    find_spec_file,
    ensure_reviews_directory
)
from claude_skills.sdd_plan_review import (
    check_tool_available,
    detect_available_tools,
    review_with_tools,
)
from claude_skills.sdd_plan_review.reporting import (
    generate_markdown_report,
    generate_json_report,
)


def cmd_review(args, printer):
    """Review a specification file using multiple AI models."""
    # Find specs directory
    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        printer.detail("Looked for specs/active/, specs/completed/, specs/archived/")
        return 1

    # Find spec file from spec ID
    spec_file = find_spec_file(args.spec_id, specs_dir)
    if not spec_file:
        printer.error(f"Spec file not found for: {args.spec_id}")
        printer.detail(f"Searched in: {specs_dir}/active, {specs_dir}/completed, {specs_dir}/archived")
        return 1

    printer.info(f"Reviewing specification: {spec_file}")

    # Detect available tools
    available_tools = detect_available_tools()

    if not available_tools:
        printer.error("No AI CLI tools available")
        printer.detail("\nPlease install at least one tool:")
        printer.detail("  - gemini: npm install -g @google/generative-ai-cli")
        printer.detail("  - codex: npm install -g @anthropic/codex")
        printer.detail("  - cursor-agent: See cursor.com for installation")
        return 1

    # Determine which tools to use
    if args.tools:
        requested_tools = [t.strip() for t in args.tools.split(',')]
        tools_to_use = [t for t in requested_tools if t in available_tools]
        if not tools_to_use:
            printer.error(f"None of the requested tools are available: {requested_tools}")
            printer.detail(f"Available tools: {', '.join(available_tools)}")
            return 1
    else:
        tools_to_use = available_tools

    printer.info(f"Using {len(tools_to_use)} tool(s): {', '.join(tools_to_use)}")

    # Dry run mode
    if args.dry_run:
        printer.info("\n[DRY RUN MODE]")
        printer.detail(f"Would review: {spec_file}")
        printer.detail(f"Review type: {args.type}")
        printer.detail(f"Tools: {', '.join(tools_to_use)}")
        printer.detail(f"Parallel: Yes")
        if args.output:
            printer.detail(f"Output: {args.output}")
        printer.detail(f"Cache: {'Yes' if args.cache else 'No'}")
        return 0

    # Load spec
    try:
        with open(spec_file, 'r') as f:
            spec_content = f.read()
    except Exception as e:
        printer.error(f"Failed to read spec: {str(e)}")
        return 1

    # Try to extract spec_id and title from JSON
    spec_id = spec_file.stem  # Use filename as fallback
    spec_title = "Specification"

    try:
        spec_data = json.loads(spec_content)
        spec_id = spec_data.get("spec_id", spec_id)
        spec_title = spec_data.get("title", spec_title)
    except json.JSONDecodeError:
        # Not JSON, use defaults
        pass

    # Run review
    printer.info(f"\nStarting {args.type} review...")

    results = review_with_tools(
        spec_content=spec_content,
        tools=tools_to_use,
        review_type=args.type,
        spec_id=spec_id,
        spec_title=spec_title,
        parallel=True
    )

    # Display execution summary
    printer.header("\nReview Complete")
    printer.info(f"Execution time: {results['execution_time']:.1f}s")
    printer.success(f"Models responded: {len(results['parsed_responses'])}/{len(tools_to_use)}")

    if results['failures']:
        printer.warning(f"Failed: {len(results['failures'])} tool(s)")
        for failure in results['failures']:
            printer.detail(f"  {failure['tool']}: {failure['error']}")

    # Check if we have consensus
    consensus = results.get('consensus')
    if not consensus or not consensus.get('success'):
        printer.error("\nFailed to build consensus from model responses")
        if consensus:
            printer.detail(f"Error: {consensus.get('error')}")
        return 1

    # Generate and display markdown report
    printer.info("\n" + "=" * 60)
    markdown_report = generate_markdown_report(
        consensus,
        spec_id,
        spec_title,
        args.type,
        parsed_responses=results.get('parsed_responses', [])
    )
    print(markdown_report)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        # Find specs directory and use .reviews/ for default output
        specs_dir = find_specs_directory(str(spec_file))
        if specs_dir:
            reviews_dir = ensure_reviews_directory(specs_dir)
            output_path = reviews_dir / f"{spec_file.stem}-review.md"
        else:
            # Fallback to spec file's parent directory
            output_path = spec_file.parent / f"{spec_file.stem}-review.md"

    # Save output
    try:
        # Determine output format based on extension
        if output_path.suffix == '.json':
            # JSON report
            json_report = generate_json_report(
                consensus,
                spec_id,
                spec_title,
                args.type
            )
            with open(output_path, 'w') as f:
                json.dump(json_report, f, indent=2)
        else:
            # Markdown report (default)
            with open(output_path, 'w') as f:
                f.write(markdown_report)

        printer.success(f"\nReport saved to: {output_path}")
    except Exception as e:
        printer.error(f"Failed to save output: {str(e)}")

    return 0


def cmd_list_tools(args, printer):
    """List available AI CLI tools."""
    tools_to_check = ["gemini", "codex", "cursor-agent"]

    available = []
    unavailable = []

    for tool in tools_to_check:
        is_available = check_tool_available(tool)
        if is_available:
            available.append(tool)
        else:
            unavailable.append(tool)

    # JSON output mode
    if args.json:
        output = {
            "available": available,
            "unavailable": unavailable,
            "total": len(tools_to_check),
            "available_count": len(available)
        }
        print(json.dumps(output, indent=2))
        if len(available) == 0:
            return 1
        else:
            return 0

    # Rich UI mode
    printer.header("AI CLI Tools for Reviews")

    if available:
        printer.success(f"\n✓ Available ({len(available)}):")
        for tool in available:
            printer.detail(f"  {tool}")

    if unavailable:
        printer.warning(f"\n✗ Not Available ({len(unavailable)}):")
        for tool in unavailable:
            printer.detail(f"  {tool}")

    # Installation instructions
    if unavailable:
        printer.info("\nInstallation Instructions:")

        for tool in unavailable:
            if tool == "gemini":
                printer.detail("\nGemini CLI:")
                printer.detail("  npm install -g @google/generative-ai-cli")
                printer.detail("  export GOOGLE_API_KEY='your-key'")
            elif tool == "codex":
                printer.detail("\nCodex CLI:")
                printer.detail("  npm install -g @anthropic/codex")
                printer.detail("  export ANTHROPIC_API_KEY='your-key'")
            elif tool == "cursor-agent":
                printer.detail("\nCursor Agent:")
                printer.detail("  Install Cursor IDE from cursor.com")
                printer.detail("  Cursor agent comes bundled with the IDE")

    # Summary
    printer.info(f"\nSummary: {len(available)}/{len(tools_to_check)} tools available")

    if len(available) == 0:
        printer.warning("No tools available - cannot run reviews")
        return 1
    elif len(available) == 1:
        printer.info("Single-model reviews available (limited confidence)")
        return 0
    else:
        printer.success("Multi-model reviews available")
        return 0


def register_plan_review(subparsers, parent_parser):
    """Register plan-review subcommands for unified CLI."""

    # review command
    parser_review = subparsers.add_parser(
        'review',
        parents=[parent_parser],
        help='Review specification with multiple AI models'
    )
    parser_review.add_argument('spec_id', help='Specification ID')
    parser_review.add_argument(
        '--type',
        choices=['quick', 'full', 'security', 'feasibility'],
        default='full',
        help='Review type (default: full)'
    )
    parser_review.add_argument(
        '--tools',
        help='Comma-separated list of tools to use (e.g., gemini,codex)'
    )
    parser_review.add_argument(
        '--output',
        help='Save review report to file'
    )
    parser_review.add_argument(
        '--cache',
        action='store_true',
        help='Use cached results if available'
    )
    parser_review.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing'
    )
    parser_review.set_defaults(func=cmd_review)

    # list-tools command
    parser_list = subparsers.add_parser(
        'list-plan-review-tools',
        parents=[parent_parser],
        help='List available AI CLI tools for plan reviews'
    )
    parser_list.set_defaults(func=cmd_list_tools)
