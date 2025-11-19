#!/usr/bin/env python3
"""
Implementation Fidelity Review CLI

Command-line interface for reviewing implementation fidelity against SDD specifications.
"""

import argparse
import sys
import json
import re
from collections import OrderedDict
from typing import Optional, List, Callable, Dict, Any
from pathlib import Path

from .review import FidelityReviewer
from .report import FidelityReport
from .consultation import (
    consult_multiple_ai_on_fidelity,
    parse_multiple_responses,
    detect_consensus,
    categorize_issues,
    NoToolsAvailableError,
    ConsultationTimeoutError,
    ConsultationError
)
from claude_skills.common.ai_tools import (
    get_enabled_and_available_tools,
    check_tool_available
)
from claude_skills.common.ai_config import ALL_SUPPORTED_TOOLS
from claude_skills.common.progress import ProgressEmitter
from claude_skills.common.sdd_config import get_default_format, get_json_compact
from claude_skills.common.json_output import output_json
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    is_json_mode,
    LIST_TOOLS_ESSENTIAL,
    LIST_TOOLS_STANDARD,
    FIDELITY_REVIEW_ESSENTIAL,
    FIDELITY_REVIEW_STANDARD,
)
from claude_skills.common import ai_config
from claude_skills.common.paths import find_specs_directory, ensure_fidelity_reviews_directory


def _fidelity_output_json(data: Dict[str, Any], args) -> int:
    """Emit fidelity summary respecting verbosity settings."""
    payload = prepare_output(data, args, FIDELITY_REVIEW_ESSENTIAL, FIDELITY_REVIEW_STANDARD)
    
    compact = getattr(args, "compact", None)
    if compact is None:
        compact = get_json_compact()
        
    output_json(payload, compact)
    return 0


def _slugify_component(value: Optional[str]) -> str:
    if value is None:
        return ""
    sanitized = re.sub(r"[^\w\-]+", "-", str(value))
    sanitized = sanitized.strip("-")
    return sanitized or "value"


def _build_output_basename(
    spec_id: str,
    task_id: Optional[str],
    phase_id: Optional[str],
    file_paths: Optional[List[str]],
) -> str:
    components: List[str] = [_slugify_component(spec_id)]

    if task_id:
        components.append(f"task-{_slugify_component(task_id)}")
    elif phase_id:
        components.append(f"phase-{_slugify_component(phase_id)}")
    elif file_paths:
        components.append("files")
        sanitized_files: List[str] = []
        for file_path in file_paths[:2]:
            if not file_path:
                continue
            sanitized_files.append(_slugify_component(Path(file_path).stem))
        components.extend([part for part in sanitized_files if part])
        if len(file_paths) > 2:
            components.append(f"{len(file_paths)}-files")
    else:
        components.append("full")

    components.append("fidelity-review")
    base_name = "-".join(filter(None, components))
    base_name = re.sub(r"-{2,}", "-", base_name)
    return base_name


def _create_fidelity_report(
    reviewer,
    parsed_responses,
    consensus,
    categorized_issues,
    models_metadata: Dict[str, Any],
) -> FidelityReport:
    review_results = {
        "spec_id": reviewer.spec_id,
        "models_consulted": models_metadata,
        "consensus": consensus,
        "categorized_issues": categorized_issues,
        "parsed_responses": parsed_responses,
    }
    return FidelityReport(review_results)


def _write_report_artifact(
    path: Path,
    format: str,
    get_markdown: Callable[[], str],
    get_json_text: Callable[[], str],
) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if format == "json":
            path.write_text(get_json_text())
        else:
            path.write_text(get_markdown())
        return True
    except (OSError, PermissionError) as e:
        print(f"Error writing to {path}: {e}", file=sys.stderr)
        return False


def _handle_fidelity_review(args: argparse.Namespace, printer=None) -> int:
    """
    Handle fidelity-review command execution.

    Orchestrates the fidelity review workflow:
    1. Load specification and extract requirements
    2. Generate review prompt with implementation artifacts
    3. Optionally consult AI tools for review
    4. Parse and analyze responses
    5. Generate and display report

    Args:
        args: Parsed command-line arguments
        printer: Optional PrettyPrinter instance (for unified CLI compatibility)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    json_requested = is_json_mode(args)

    try:
        # Step 1: Initialize FidelityReviewer
        if hasattr(args, 'verbose') and args.verbose:
            print(f"Loading specification: {args.spec_id}", file=sys.stderr)

        specs_hint = getattr(args, 'specs_dir', None) or getattr(args, 'path', '.')
        try:
            base_specs_dir = find_specs_directory(specs_hint)
        except TypeError:
            # Support test stubs that don't accept parameters
            base_specs_dir = find_specs_directory()

        # Check if incremental mode is requested
        incremental = args.incremental if hasattr(args, 'incremental') else False
        reviewer = FidelityReviewer(args.spec_id, spec_path=base_specs_dir, incremental=incremental)

        if reviewer.spec_data is None:
            print(f"Error: Failed to load specification {args.spec_id}", file=sys.stderr)
            return 1

        # Step 2: Generate review prompt
        if hasattr(args, 'verbose') and args.verbose:
            print("Generating review prompt...", file=sys.stderr)

        task_id = args.task if hasattr(args, 'task') and args.task else None
        phase_id = args.phase if hasattr(args, 'phase') and args.phase else None
        file_paths = args.files if hasattr(args, 'files') and args.files else None

        prompt = reviewer.generate_review_prompt(
            task_id=task_id,
            phase_id=phase_id,
            file_paths=file_paths,
            include_tests=not args.no_tests,
            base_branch=args.base_branch
        )

        scope_info = {
            "task": task_id,
            "phase": phase_id,
            "files": file_paths,
        }

        # If no-ai flag, just show prompt and exit
        if args.no_ai:
            summary_payload = {
                "spec_id": args.spec_id,
                "mode": "no-ai",
                "format": "prompt",
                "artifacts": [],
                "issue_counts": {},
                "models_consulted": {},
                "consensus": {},
                "scope": scope_info,
                "prompt_included": True,
                "recommendation": None,
            }
            if json_requested:
                summary_payload["prompt_excerpt"] = prompt[:200]
                return _fidelity_output_json(summary_payload, args)

            print("\n" + "=" * 80)
            print("REVIEW PROMPT (--no-ai mode)")
            print("=" * 80)
            print(prompt)
            return 0

        # Step 3: Consult AI tools
        if hasattr(args, 'verbose') and args.verbose:
            ai_tools = args.ai_tools if hasattr(args, 'ai_tools') and args.ai_tools else None
            tool_list = ', '.join(ai_tools) if ai_tools else 'all available'
            print(f"Consulting AI tools: {tool_list}", file=sys.stderr)

        # Create ProgressEmitter (enabled by default, unless --no-stream-progress)
        progress_emitter = None
        should_stream = not (hasattr(args, 'no_stream_progress') and args.no_stream_progress)
        if should_stream:
            # Determine output stream based on format mode
            output_format = args.format if hasattr(args, 'format') else 'text'

            # For json/markdown modes, emit progress to stderr to avoid corrupting stdout
            # For text mode, emit to stdout (existing behavior)
            progress_stream = sys.stderr if output_format in ['json', 'markdown'] else sys.stdout

            progress_emitter = ProgressEmitter(
                output=progress_stream,
                enabled=True,
                auto_detect_tty=False
            )

        try:
            responses = consult_multiple_ai_on_fidelity(
                prompt=prompt,
                tools=args.ai_tools if hasattr(args, 'ai_tools') else None,
                model=args.model if hasattr(args, 'model') else None,
                timeout=args.timeout,
                progress_emitter=progress_emitter
            )
        except NoToolsAvailableError as e:
            print(f"Error: {e}", file=sys.stderr)
            print(f"Tip: Install AI consultation tools ({', '.join(ALL_SUPPORTED_TOOLS)})", file=sys.stderr)
            return 1
        except ConsultationTimeoutError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except ConsultationError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        # Step 4: Parse responses
        # responses is already a list of ToolResponse objects
        response_list = responses

        if hasattr(args, 'verbose') and args.verbose:
            print(f"Parsing {len(response_list)} AI responses...", file=sys.stderr)

        parsed_responses = parse_multiple_responses(response_list)

        # Step 5: Detect consensus
        consensus_threshold = args.consensus_threshold if hasattr(args, 'consensus_threshold') else 2
        consensus = detect_consensus(parsed_responses, min_agreement=consensus_threshold)

        # Step 6 & 7: Categorize issues and prepare report/artifacts
        consensus_issues = getattr(consensus, "consensus_issues", None)
        if consensus_issues is None and isinstance(consensus, dict):
            consensus_issues = consensus.get("consensus_issues", [])
        categorized = categorize_issues(consensus_issues or [])
        if isinstance(categorized, dict):
            categorized_issues = categorized
        elif isinstance(categorized, list):
            categorized_issues = {"uncategorized": categorized}
        else:
            categorized_issues = {"uncategorized": [categorized] if categorized else []}
        models_ordered = OrderedDict(
            (resp.tool, resp.model)
            for resp in response_list
        )
        models_metadata = {
            "count": len(models_ordered),
            "tools": models_ordered,
        }

        report = _create_fidelity_report(
            reviewer,
            parsed_responses,
            consensus,
            categorized_issues,
            models_metadata,
        )

        compact = getattr(args, "compact", None)
        if compact is None:
            compact = get_json_compact()
        
        output_format = args.format if hasattr(args, "format") else "text"

        json_payload_cache = None
        json_text_cache: Optional[str] = None

        def get_json_payload():
            nonlocal json_payload_cache
            if json_payload_cache is None:
                json_payload_cache = report.generate_json()
            return json_payload_cache

        def get_json_text() -> str:
            nonlocal json_text_cache
            if json_text_cache is None:
                payload = get_json_payload()
                if compact:
                    json_text_cache = json.dumps(payload, separators=(",", ":"))
                else:
                    json_text_cache = json.dumps(payload, indent=2)
            return json_text_cache

        saved_paths: List[Path] = []

        if hasattr(args, "output") and args.output:
            requested_path = Path(args.output)
            if requested_path.suffix == "":
                if output_format == "json":
                    requested_path = requested_path.with_suffix(".json")
                else:
                    requested_path = requested_path.with_suffix(".txt")
            
            # Only support writing JSON or text artifacts manually if needed, 
            # but for now only JSON is fully supported via get_json_text
            if output_format == "json" or requested_path.suffix == ".json":
                 try:
                    requested_path.parent.mkdir(parents=True, exist_ok=True)
                    requested_path.write_text(get_json_text())
                    saved_paths.append(requested_path)
                 except (OSError, PermissionError) as e:
                    print(f"Error writing to {requested_path}: {e}", file=sys.stderr)
        else:
            specs_dir = base_specs_dir or find_specs_directory()
            if specs_dir:
                fidelity_dir = ensure_fidelity_reviews_directory(specs_dir)
                base_name = _build_output_basename(args.spec_id, task_id, phase_id, file_paths)
                json_path = fidelity_dir / f"{base_name}.json"
                try:
                    json_path.parent.mkdir(parents=True, exist_ok=True)
                    json_path.write_text(get_json_text())
                    saved_paths.append(json_path)
                except (OSError, PermissionError) as e:
                    print(f"Error writing to {json_path}: {e}", file=sys.stderr)

        report_data = getattr(report, "results", {})
        metadata = report_data.get("metadata")

        issue_counts = {key: len(value) for key, value in categorized_issues.items()}
        recommendation = metadata.get("recommendation") if metadata else None
        models_summary = {
            "count": models_metadata.get("count"),
            "tools": dict(models_metadata.get("tools", {})),
        }
        if isinstance(consensus, dict):
            consensus_verdict = consensus.get("consensus_verdict")
            agreement_rate = consensus.get("agreement_rate")
            model_count = consensus.get("model_count")
            recommendations = consensus.get("consensus_recommendations")
        else:
            consensus_verdict = getattr(consensus, "consensus_verdict", None)
            agreement_rate = getattr(consensus, "agreement_rate", None)
            model_count = getattr(consensus, "model_count", None)
            recommendations = getattr(consensus, "consensus_recommendations", None)

        if hasattr(consensus_verdict, "value"):
            consensus_verdict = consensus_verdict.value

        consensus_info = {
            "verdict": consensus_verdict,
            "agreement_rate": agreement_rate,
            "model_count": model_count,
            "recommendations": recommendations,
        }

        summary_payload = {
            "spec_id": args.spec_id,
            "mode": "no-ai" if args.no_ai else "full",
            "format": args.format if hasattr(args, "format") else "text",
            "artifacts": [str(path) for path in saved_paths],
            "issue_counts": issue_counts,
            "models_consulted": models_summary,
            "consensus": consensus_info,
            "scope": scope_info,
            "prompt_included": not args.no_ai,
            "recommendation": recommendation,
        }

        if json_requested:
            return _fidelity_output_json(summary_payload, args)

        # Step 8: Emit console output in requested format
        if output_format == "json":
            output_json(get_json_payload(), compact)
        else:
            report.print_console_rich(verbose=getattr(args, "verbose", False))

        if saved_paths:
            print("\nFidelity review artifact(s) saved to:", file=sys.stderr)
            for path in saved_paths:
                print(f"  {path}", file=sys.stderr)

        return 0

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def _handle_list_review_tools(args: argparse.Namespace, printer=None) -> int:
    """
    Handle list-review-tools command execution.

    Detects and displays available AI consultation tools with their status.

    Args:
        args: Parsed command-line arguments
        printer: Optional PrettyPrinter instance (for unified CLI compatibility)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Detect tools that are both enabled and available
        ready_tools = get_enabled_and_available_tools("sdd-fidelity-review")
        all_tools = ALL_SUPPORTED_TOOLS

        # Categorize tools based on configuration and availability
        tool_status = []
        disabled_tools = []
        not_installed_tools = []

        for tool in all_tools:
            is_enabled = ai_config.is_tool_enabled("sdd-fidelity-review", tool)
            is_installed = check_tool_available(tool)
            is_ready = tool in ready_tools

            if not is_enabled:
                status = "disabled"
                disabled_tools.append({
                    "tool": tool,
                    "available": False,
                    "status": status
                })
            elif is_ready and is_installed:
                status = "available"
                tool_status.append({
                    "tool": tool,
                    "available": True,
                    "status": status
                })
            else:
                status = "not found"
                not_installed_tools.append({
                    "tool": tool,
                    "available": False,
                    "status": status
                })

        result = {
            "available": tool_status,
            "disabled": disabled_tools,
            "not_installed": not_installed_tools,
            "available_count": len(tool_status),
            "total": len(all_tools),
        }

        json_requested = is_json_mode(args)
        output_format = args.format if hasattr(args, 'format') else 'text'
        if json_requested:
            output_format = 'json'

        if output_format == 'json':
            payload = prepare_output(result, args, LIST_TOOLS_ESSENTIAL, LIST_TOOLS_STANDARD)
            output_json(payload, getattr(args, 'compact', False))
        else:  # text format
            print("\n" + "=" * 60)
            print("AI CONSULTATION TOOLS STATUS")
            print("=" * 60)
            print()

            # Show ready to use tools
            if tool_status:
                print("  ✓ Ready to Use:")
                for status_info in tool_status:
                    print(f"    • {status_info['tool']}")
                print()

            # Show disabled tools
            if disabled_tools:
                print("  ⊘ Disabled in Config:")
                for status_info in disabled_tools:
                    print(f"    • {status_info['tool']}")
                print("    → Enable in .claude/ai_config.yaml")
                print()

            # Show not installed tools
            if not_installed_tools:
                print("  ✗ Not Installed:")
                for status_info in not_installed_tools:
                    print(f"    • {status_info['tool']}")
                print()

            print(f"Summary: {len(tool_status)}/{len(all_tools)} tools ready to use")
            print()

            if len(tool_status) == 0:
                if disabled_tools:
                    print("Hint: Some tools are disabled - enable them in .claude/ai_config.yaml")
                else:
                    print("No AI consultation tools found.")
                    print(f"Install at least one: {', '.join(ALL_SUPPORTED_TOOLS)}")
            elif hasattr(args, 'verbose') and args.verbose:
                print("\nUsage:")
                print("  Use --ai-tools to specify which tools to consult")
                print("  Example: sdd fidelity-review SPEC_ID --ai-tools gemini codex")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def register_fidelity_review_command(subparsers: argparse._SubParsersAction, parent_parser: Optional[argparse.ArgumentParser] = None) -> None:
    """Register the fidelity-review command."""
    # Load default timeout from config
    default_timeout = ai_config.get_timeout('sdd-fidelity-review', 'consultation')

    parents = [parent_parser] if parent_parser is not None else []
    parser = subparsers.add_parser(
        "fidelity-review",
        parents=parents,
        help="Review implementation fidelity against SDD specifications",
        description="Compare implementation against specification and identify deviations",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Required arguments
    parser.add_argument(
        "spec_id",
        help="Specification ID to review against"
    )

    # Scope arguments (mutually exclusive)
    scope_group = parser.add_mutually_exclusive_group()
    scope_group.add_argument(
        "--task",
        metavar="TASK_ID",
        help="Review specific task implementation"
    )
    scope_group.add_argument(
        "--phase",
        metavar="PHASE_ID",
        help="Review entire phase implementation"
    )
    scope_group.add_argument(
        "--files",
        nargs="+",
        metavar="FILE",
        help="Review specific file(s)"
    )

    # AI consultation options
    parser.add_argument(
        "--ai-tools",
        nargs="+",
        choices=ALL_SUPPORTED_TOOLS,
        metavar="TOOL",
        help="AI tools to consult (default: all available)"
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip AI consultation, show only extracted data"
    )
    parser.add_argument(
        "--model",
        help="Specific model to use for AI consultation"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=default_timeout,
        metavar="SECONDS",
        help=f"Timeout for AI consultation (default: {default_timeout} from config)"
    )
    parser.add_argument(
        "--no-stream-progress",
        action="store_true",
        help="Disable structured JSON progress events during AI consultation. "
             "Progress streaming is enabled by default."
    )

    # Review options
    parser.add_argument(
        "--no-tests",
        action="store_true",
        help="Skip test results in review"
    )
    parser.add_argument(
        "--base-branch",
        default="main",
        help="Base branch for git diff (default: main)"
    )
    parser.add_argument(
        "--consensus-threshold",
        type=int,
        default=2,
        metavar="N",
        help="Minimum models that must agree for consensus (default: 2)"
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Enable incremental mode (only review changed files since last run)"
    )

    # Output options
    parser.add_argument(
        "--output",
        "-o",
        metavar="FILE",
        help="Save review results to file"
    )

    # Get default format from config
    default_format = get_default_format()
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default=default_format,
        help=f"Output format (default: {default_format} from config)"
    )
    # Note: --verbose inherited from parent_parser (global option)

    # Set handler function
    parser.set_defaults(func=_handle_fidelity_review)


def register_list_review_tools_command(subparsers: argparse._SubParsersAction, parent_parser: Optional[argparse.ArgumentParser] = None) -> None:
    """Register the list-review-tools command."""
    parents = [parent_parser] if parent_parser is not None else []
    list_tools_parser = subparsers.add_parser(
        "list-review-tools",
        parents=parents,
        help="List available AI consultation tools",
        description=f"Show which AI tools ({', '.join(ALL_SUPPORTED_TOOLS)}) are available for fidelity review",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Output options
    # Get default format from config, fallback to "text" for text/json only commands
    default_format = get_default_format()
    if default_format not in ["text", "json"]:
        default_format = "text"  # Fallback for commands that don't support markdown

    list_tools_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default=default_format,
        help=f"Output format (default: {default_format} from config)"
    )
    # Note: --verbose inherited from parent_parser (global option)

    # Set handler function
    list_tools_parser.set_defaults(func=_handle_list_review_tools)


def register_commands(subparsers: argparse._SubParsersAction, parent_parser: Optional[argparse.ArgumentParser] = None) -> None:
    """
    Register all fidelity review commands with the main CLI parser.

    This function will be called by the main SDD CLI to register
    fidelity review commands as subcommands.

    Args:
        subparsers: The subparser object from the main argument parser
        parent_parser: Parent parser with global options to inherit (optional)

    Note:
        Registers both fidelity-review and list-review-tools commands.
    """
    register_fidelity_review_command(subparsers, parent_parser)
    register_list_review_tools_command(subparsers, parent_parser)


def main() -> int:
    """
    Main entry point for standalone CLI execution.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="Review implementation fidelity against SDD specifications",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--version",
        action="version",
        version="sdd-fidelity-review 0.1.0"
    )

    # Register subcommands using the same registration function
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    register_commands(subparsers)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute the command handler
    if hasattr(args, 'func'):
        return args.func(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
