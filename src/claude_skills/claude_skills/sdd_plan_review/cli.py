#!/usr/bin/env python3
"""
SDD Plan Review CLI - Multi-model specification review commands.

Uses external AI CLI tools to review specs from multiple perspectives
and provide actionable feedback.
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional
from claude_skills.common import (
    PrettyPrinter,
    load_json_spec,
    find_specs_directory,
    find_spec_file,
    ensure_reviews_directory
)
from claude_skills.sdd_plan_review import (
    check_tool_available,
    review_with_tools,
)
from claude_skills.common.ai_tools import get_enabled_and_available_tools
from claude_skills.common import ai_config
from claude_skills.common.ai_config import ALL_SUPPORTED_TOOLS
from claude_skills.sdd_plan_review.reporting import (
    generate_markdown_report,
    generate_json_report,
)
from claude_skills.common.json_output import output_json
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    LIST_TOOLS_ESSENTIAL,
    LIST_TOOLS_STANDARD,
    PLAN_REVIEW_SUMMARY_ESSENTIAL,
    PLAN_REVIEW_SUMMARY_STANDARD,
)


def _plan_review_output_json(data, args):
    payload = prepare_output(data, args, PLAN_REVIEW_SUMMARY_ESSENTIAL, PLAN_REVIEW_SUMMARY_STANDARD)
    output_json(payload, getattr(args, 'compact', False))
    return 0


def _parse_model_override(values: Optional[list[str]]) -> Optional[object]:
    """
    Normalize repeated model override arguments into a form accepted by ai_config.
    """
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


def cmd_review(args, printer):
    """Review a specification file using multiple AI models."""
    json_requested = getattr(args, 'json', False)

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

    if not json_requested:
        printer.info(f"Reviewing specification: {spec_file}")

    # Detect available tools
    available_tools = get_enabled_and_available_tools("sdd-plan-review")

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

    if not json_requested:
        printer.info(f"Using {len(tools_to_use)} tool(s): {', '.join(tools_to_use)}")

    model_override = _parse_model_override(getattr(args, "model", None))

    # Dry run mode
    if args.dry_run:
        printer.info("\n[DRY RUN MODE]")
        printer.detail(f"Would review: {spec_file}")
        printer.detail(f"Review type: {args.type}")
        printer.detail(f"Tools: {', '.join(tools_to_use)}")
        if model_override:
            printer.detail(f"Model override: {model_override}")
        printer.detail(f"Parallel: Yes")
        if args.output:
            printer.detail(f"Output: {args.output}")
        printer.detail(f"Cache: {'Yes' if args.cache else 'No'}")
        if json_requested:
            dry_payload = {
                'spec_id': args.spec_id,
                'review_type': args.type,
                'artifacts': [],
                'blocker_count': 0,
                'suggestion_count': 0,
                'question_count': 0,
                'models_responded': 0,
                'models_requested': len(tools_to_use),
                'models_consulted': {},
                'failures': 0,
                'execution_time': 0,
                'consensus_level': None,
                'dry_run': True,
            }
            return _plan_review_output_json(dry_payload, args)
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
    if not json_requested:
        printer.info(f"\nStarting {args.type} review...")

    results = review_with_tools(
        spec_content=spec_content,
        tools=tools_to_use,
        review_type=args.type,
        spec_id=spec_id,
        spec_title=spec_title,
        parallel=True,
        model_override=model_override,
        silent=json_requested,
    )

    # Display execution summary
    if not json_requested:
        printer.header("\nReview Complete")
        printer.info(f"Execution time: {results['execution_time']:.1f}s")
        printer.success(f"Models responded: {len(results['parsed_responses'])}/{len(tools_to_use)}")
        resolved_models = results.get("models")
        if resolved_models:
            printer.detail(f"Resolved models: {resolved_models}")

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
    if not json_requested:
        printer.info("\n" + "=" * 60)
    markdown_report = generate_markdown_report(
        consensus,
        spec_id,
        spec_title,
        args.type,
        parsed_responses=results.get('parsed_responses', [])
    )
    if not json_requested:
        print(markdown_report)

    def sanitize_component(component: str) -> str:
        cleaned = "".join(c if c.isalnum() or c in ("-", "_") else "-" for c in component.strip())
        return cleaned or "spec"

    # Determine default artifact directory (prefer specs/.reviews)
    artifact_base_dir = spec_file.parent
    reviews_dir = ensure_reviews_directory(specs_dir)
    if reviews_dir.exists() and reviews_dir.is_dir():
        artifact_base_dir = reviews_dir
    else:
        printer.warning(
            f"Unable to write to reviews directory at {reviews_dir}. "
            f"Falling back to {artifact_base_dir}."
        )

    safe_spec_id = sanitize_component(spec_id)
    artifact_basename = f"{safe_spec_id}-review-{sanitize_component(args.type)}"
    default_markdown_path = artifact_base_dir / f"{artifact_basename}.md"
    default_json_path = artifact_base_dir / f"{artifact_basename}.json"

    json_report = generate_json_report(
        consensus,
        spec_id,
        spec_title,
        args.type
    )

    json_report_text = json.dumps(json_report, indent=2) + "\n"

    artifact_tasks = [
        ("Markdown", default_markdown_path, lambda path: path.write_text(markdown_report, encoding="utf-8")),
        ("JSON", default_json_path, lambda path: path.write_text(json_report_text, encoding="utf-8")),
    ]

    if args.output:
        user_output = Path(args.output)
        if user_output.suffix.lower() == ".json":
            artifact_tasks.append(
                ("--output JSON", user_output, lambda path: path.write_text(json_report_text, encoding="utf-8"))
            )
        else:
            artifact_tasks.append(
                ("--output Markdown", user_output, lambda path: path.write_text(markdown_report, encoding="utf-8"))
            )

    saved_artifacts = []
    failed_artifacts = []
    written_paths = set()

    for label, destination, writer in artifact_tasks:
        # Avoid duplicate writes to the same path
        destination = destination.resolve()
        if destination in written_paths:
            continue
        written_paths.add(destination)

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as mkdir_error:
            printer.warning(f"Could not create directory for {label} at {destination}: {mkdir_error}")
            failed_artifacts.append((label, destination, mkdir_error))
            continue

        try:
            writer(destination)
            saved_artifacts.append((label, destination))
        except (OSError, PermissionError, ValueError) as write_error:
            printer.warning(f"Failed to write {label} artifact to {destination}: {write_error}")
            failed_artifacts.append((label, destination, write_error))

    artifact_paths = [str(path) for _, path in saved_artifacts]

    summary_payload = {
        'spec_id': spec_id,
        'review_type': args.type,
        'artifacts': artifact_paths,
        'blocker_count': len(consensus.get('critical_blockers') or []),
        'suggestion_count': len(consensus.get('major_suggestions') or []),
        'question_count': len(consensus.get('questions') or []),
        'models_responded': len(results['parsed_responses']),
        'models_requested': len(tools_to_use),
        'models_consulted': results.get('models', {}),
        'failures': len(results['failures']),
        'execution_time': results.get('execution_time'),
        'consensus_level': consensus.get('consensus_level'),
        'dry_run': False,
    }
    if failed_artifacts:
        summary_payload['artifact_failures'] = len(failed_artifacts)

    if json_requested:
        return _plan_review_output_json(summary_payload, args)

    if saved_artifacts:
        printer.success("\nSaved review artifacts:")
        for label, path in saved_artifacts:
            printer.detail(f"{label}: {path}")
    else:
        printer.warning("\nNo review artifacts were saved. See warnings above for details.")

    if failed_artifacts:
        for label, path, error in failed_artifacts:
            printer.warning(f"Artifact write skipped for {label} ({path}): {error}")

    # Exit code mapping for automation (replaces APPROVE/REVISE/REJECT verdicts)
    # Exit 1: Critical blockers found (equivalent to REJECT)
    # Exit 2: Multiple major suggestions (equivalent to REVISE)
    # Exit 0: No significant issues (equivalent to APPROVE)
    blocker_count = summary_payload.get('blocker_count', 0)
    suggestion_count = summary_payload.get('suggestion_count', 0)

    if blocker_count > 0:
        return 1  # Critical blockers must be fixed
    elif suggestion_count > 3:
        return 2  # Significant revisions recommended
    else:
        return 0  # Ready to proceed


def cmd_list_tools(args, printer):
    """List available AI CLI tools, respecting enabled configuration."""
    tools_to_check = ALL_SUPPORTED_TOOLS

    # Categorize tools based on configuration and availability
    ready = []          # Enabled and executable exists
    disabled = []       # Explicitly disabled in config
    not_installed = []  # Enabled but executable not found

    for tool in tools_to_check:
        is_enabled = ai_config.is_tool_enabled("sdd-plan-review", tool)
        is_installed = check_tool_available(tool)

        if not is_enabled:
            disabled.append(tool)
        elif is_installed:
            ready.append(tool)
        else:
            not_installed.append(tool)

    # JSON output mode
    if args.json:
        payload = {
            "available": ready,
            "disabled": disabled,
            "not_installed": not_installed,
            "total": len(tools_to_check),
            "available_count": len(ready)
        }

        # Apply verbosity filtering
        filtered_output = prepare_output(payload, args, LIST_TOOLS_ESSENTIAL, LIST_TOOLS_STANDARD)
        output_json(filtered_output, args.compact)
        if len(ready) == 0:
            return 1
        else:
            return 0

    # Rich UI mode
    printer.header("AI CLI Tools for Reviews")

    if ready:
        printer.success(f"\n✓ Ready to Use ({len(ready)}):")
        for tool in ready:
            printer.detail(f"  {tool}")

    if disabled:
        printer.warning(f"\n⊘ Disabled in Config ({len(disabled)}):")
        for tool in disabled:
            printer.detail(f"  {tool}")
            printer.detail(f"     To enable: set 'enabled: true' in .claude/ai_config.yaml")

    if not_installed:
        printer.warning(f"\n✗ Not Installed ({len(not_installed)}):")
        for tool in not_installed:
            printer.detail(f"  {tool}")

    # Installation instructions
    if not_installed:
        printer.info("\nInstallation Instructions:")

        for tool in not_installed:
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
    total_usable = len(ready)
    printer.info(f"\nSummary: {total_usable}/{len(tools_to_check)} tools ready to use")

    if len(ready) == 0:
        printer.warning("No tools ready - cannot run reviews")
        if disabled:
            printer.info("Hint: Some tools are disabled in config - enable them in .claude/ai_config.yaml")
        return 1
    elif len(ready) == 1:
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
        '--model',
        action='append',
        metavar='MODEL',
        help='Override model selection (repeat for per-tool overrides, e.g., gemini=gemini-pro)',
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
