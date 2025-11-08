#!/usr/bin/env python3
"""
Implementation Fidelity Review CLI

Command-line interface for reviewing implementation fidelity against SDD specifications.
"""

import argparse
import sys
import json
from typing import Optional
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
    detect_available_tools,
    check_tool_available
)
from claude_skills.common.progress import ProgressEmitter
from claude_skills.common.sdd_config import get_default_format
from claude_skills.common.json_output import output_json


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
    try:
        # Step 1: Initialize FidelityReviewer
        if args.verbose:
            print(f"Loading specification: {args.spec_id}", file=sys.stderr)

        # Check if incremental mode is requested
        incremental = args.incremental if hasattr(args, 'incremental') else False
        reviewer = FidelityReviewer(args.spec_id, incremental=incremental)

        if reviewer.spec_data is None:
            print(f"Error: Failed to load specification {args.spec_id}", file=sys.stderr)
            return 1

        # Step 2: Generate review prompt
        if args.verbose:
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

        # If no-ai flag, just show prompt and exit
        if args.no_ai:
            print("\n" + "=" * 80)
            print("REVIEW PROMPT (--no-ai mode)")
            print("=" * 80)
            print(prompt)
            return 0

        # Step 3: Consult AI tools
        if args.verbose:
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
            print("Tip: Install AI consultation tools (gemini, codex, or cursor-agent)", file=sys.stderr)
            return 1
        except ConsultationTimeoutError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except ConsultationError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        # Step 4: Parse responses
        # Extract list of ToolResponse objects from MultiToolResponse
        response_list = list(responses.responses.values())

        if args.verbose:
            print(f"Parsing {len(response_list)} AI responses...", file=sys.stderr)

        parsed_responses = parse_multiple_responses(response_list)

        # Step 5: Detect consensus
        consensus_threshold = args.consensus_threshold if hasattr(args, 'consensus_threshold') else 2
        consensus = detect_consensus(parsed_responses, min_agreement=consensus_threshold)

        # Step 6: Categorize issues
        categorized_issues = categorize_issues(consensus.consensus_issues)

        # Step 7: Generate output
        output_format = args.format if hasattr(args, 'format') else 'text'

        if output_format == 'json':
            _output_json(args, reviewer, parsed_responses, consensus, categorized_issues)
        elif output_format == 'markdown':
            _output_markdown(args, reviewer, parsed_responses, consensus, categorized_issues)
        else:  # text
            _output_text(args, reviewer, parsed_responses, consensus, categorized_issues)

        # If output file specified, write to file
        if hasattr(args, 'output') and args.output:
            if args.verbose:
                print(f"\nResults saved to: {args.output}", file=sys.stderr)

        return 0

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def _output_text(args, reviewer, parsed_responses, consensus, categorized_issues):
    """Generate text output format using Rich panels and formatting."""
    # Create review results dictionary for FidelityReport
    review_results = {
        "spec_id": reviewer.spec_id,
        "models_consulted": len(parsed_responses),
        "consensus": consensus,
        "categorized_issues": categorized_issues,
        "parsed_responses": parsed_responses
    }

    # Create FidelityReport instance and use Rich formatting
    report = FidelityReport(review_results)

    # Use Rich console output with enhanced visuals
    report.print_console_rich(verbose=args.verbose if hasattr(args, 'verbose') else False)


def _output_markdown(args, reviewer, parsed_responses, consensus, categorized_issues):
    """Generate markdown output format."""
    output = []
    output.append("# Implementation Fidelity Review\n")
    output.append(f"**Spec:** {reviewer.spec_id}\n")
    output.append(f"**Models Consulted:** {len(parsed_responses)}\n")
    output.append(f"\n## Consensus Verdict: {consensus.consensus_verdict.value.upper()}\n")
    output.append(f"**Agreement Rate:** {consensus.agreement_rate:.1%}\n")

    if categorized_issues:
        output.append("\n## Issues Identified (Consensus)\n")
        for cat_issue in categorized_issues:
            output.append(f"\n### [{cat_issue.severity.value.upper()}] {cat_issue.issue}\n")

    if consensus.consensus_recommendations:
        output.append("\n## Recommendations\n")
        for rec in consensus.consensus_recommendations:
            output.append(f"- {rec}\n")

    result = "".join(output)
    print(result)


def _output_json(args, reviewer, parsed_responses, consensus, categorized_issues):
    """Generate JSON output format using FidelityReport."""
    # Create review results dictionary for FidelityReport
    review_results = {
        "spec_id": reviewer.spec_id,
        "models_consulted": len(parsed_responses),
        "consensus": consensus,
        "categorized_issues": categorized_issues,
        "parsed_responses": parsed_responses
    }

    # Create FidelityReport instance and use generate_json() method
    report = FidelityReport(review_results)
    result = report.generate_json()

    output_json(result, getattr(args, 'compact', False))


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
        # Detect all available tools
        available_tools = detect_available_tools()
        all_tools = ["gemini", "codex", "cursor-agent"]

        # Build tool status information
        tool_status = []
        for tool in all_tools:
            is_available = tool in available_tools
            status = "available" if is_available else "not found"
            tool_status.append({
                "tool": tool,
                "available": is_available,
                "status": status
            })

        # Output in requested format
        output_format = args.format if hasattr(args, 'format') else 'text'

        if output_format == 'json':
            result = {
                "tools": tool_status,
                "available_count": len(available_tools),
                "total_count": len(all_tools)
            }
            output_json(result, getattr(args, 'compact', False))
        else:  # text format
            print("\n" + "=" * 60)
            print("AI CONSULTATION TOOLS STATUS")
            print("=" * 60)
            print()

            for status_info in tool_status:
                tool_name = status_info["tool"]
                available = status_info["available"]
                status_symbol = "✓" if available else "✗"
                status_text = "Available" if available else "Not Found"

                print(f"  {status_symbol} {tool_name:<15} {status_text}")

            print()
            print(f"Available: {len(available_tools)}/{len(all_tools)}")
            print()

            if len(available_tools) == 0:
                print("No AI consultation tools found.")
                print("Install at least one: gemini, codex, or cursor-agent")
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
        choices=["gemini", "codex", "cursor-agent"],
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
        default=120,
        metavar="SECONDS",
        help="Timeout for AI consultation (default: 120)"
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
        choices=["text", "json", "markdown"],
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
        description="Show which AI tools (gemini, codex, cursor-agent) are available for fidelity review",
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
