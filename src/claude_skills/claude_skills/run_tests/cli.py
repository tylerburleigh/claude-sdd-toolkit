#!/usr/bin/env python3
"""Testing tools CLI with unified CLI integration."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Optional

from claude_skills.common import PrettyPrinter
from claude_skills.common.metrics import track_metrics
from claude_skills.common.ai_tools import detect_available_tools
from claude_skills.run_tests.consultation import (
    consult_with_auto_routing,
    consult_multi_agent,
    run_consultation,
    print_routing_matrix,
    should_auto_trigger_consensus,
    get_consensus_pair_for_failure,
    FAILURE_TYPES as CONSULT_FAILURE_TYPES,
    MULTI_AGENT_PAIRS,
)
from claude_skills.run_tests.test_discovery import print_discovery_report
from claude_skills.run_tests.pytest_runner import (
    run_pytest,
    list_presets,
    get_presets,
    validate_preset,
)


def _dump_json(payload: Any) -> None:
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")


def _maybe_json(args: argparse.Namespace, payload: Any) -> bool:
    if getattr(args, 'json', False):
        _dump_json(payload)
        return True
    return False


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def cmd_check_tools(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    """Check availability of external AI tools."""
    available_tools = detect_available_tools()

    if getattr(args, 'json', False):
        result = {
            "tools": {tool: True for tool in available_tools},
            "available_count": len(available_tools),
            "available_tools": available_tools
        }
        _dump_json(result)
        return 0

    # Pretty print tool status
    printer.header("External Tool Availability")
    printer.blank()

    if not available_tools:
        printer.warning("No external tools found")
        printer.info("Install at least one: gemini, codex, or cursor-agent")
        return 1

    printer.success(f"Found {len(available_tools)} tool(s):")
    for tool in available_tools:
        printer.info(f"  ✓ {tool}")

    return 0


def cmd_consult(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    if args.list_routing:
        print_routing_matrix(printer)
        return 0

    if args.prompt:
        tool = args.tool if args.tool != "auto" else None
        if tool is None:
            available_tools = detect_available_tools()
            if not available_tools:
                if _maybe_json(args, {"status": "error", "message": "No external tools found"}):
                    return 1
                printer.error("No external tools found")
                printer.info("Install at least one: gemini, codex, or cursor-agent")
                return 1
            tool = available_tools[0]
        return run_consultation(tool, args.prompt, args.dry_run, printer)

    if not args.failure_type:
        if _maybe_json(args, {"status": "error", "message": "failure_type is required"}):
            return 1
        printer.error("failure_type is required when not using --prompt")
        return 1

    if not args.error or not args.hypothesis:
        if _maybe_json(args, {"status": "error", "message": "--error and --hypothesis are required"}):
            return 1
        printer.error("--error and --hypothesis are required for auto-formatting")
        return 1

    auto_triggered = False
    consensus_pair = args.pair
    if not args.multi_agent and should_auto_trigger_consensus(args.failure_type):
        auto_triggered = True
        consensus_pair = get_consensus_pair_for_failure(args.failure_type)
        printer.info(f"Auto-triggering multi-agent consensus for '{args.failure_type}' failure")
        printer.info(f"Using consensus pair: {consensus_pair}")
        printer.blank()

    if args.multi_agent or auto_triggered:
        return consult_multi_agent(
            failure_type=args.failure_type,
            error_message=args.error,
            hypothesis=args.hypothesis,
            test_code_path=args.test_code,
            impl_code_path=args.impl_code,
            context=args.context,
            question=args.question,
            pair=consensus_pair,
            dry_run=args.dry_run,
            printer=printer,
        )

    return consult_with_auto_routing(
        failure_type=args.failure_type,
        error_message=args.error,
        hypothesis=args.hypothesis,
        test_code_path=args.test_code,
        impl_code_path=args.impl_code,
        context=args.context,
        question=args.question,
        tool=args.tool,
        dry_run=args.dry_run,
        printer=printer,
    )


def cmd_discover(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    return print_discovery_report(
        root_dir=args.directory,
        show_summary=args.summary,
        show_tree=args.tree,
        show_fixtures=args.fixtures,
        show_markers=args.markers,
        show_detailed=args.detailed,
        printer=printer,
    )


def cmd_run(args: argparse.Namespace, printer: PrettyPrinter) -> int:
    if args.list:
        list_presets(printer)
        return 0

    if args.preset and not validate_preset(args.preset):
        if _maybe_json(args, {"status": "error", "message": f"Unknown preset: {args.preset}"}):
            return 1
        printer.error(f"Unknown preset: {args.preset}")
        printer.info("Use --list to see available presets")
        return 1

    return run_pytest(
        preset=args.preset,
        path=args.path,
        pattern=args.pattern,
        extra_args=args.extra_args,
        printer=printer,
    )


# ---------------------------------------------------------------------------
# Unified CLI registration
# ---------------------------------------------------------------------------


def register_run_tests(subparsers: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser) -> None:  # type: ignore[attr-defined]
    check_parser = subparsers.add_parser(
        "check-tools",
        parents=[parent_parser],
        help="Check availability of external CLI tools",
        description="Check which external AI CLI tools are available",
    )
    check_parser.set_defaults(func=cmd_check_tools)

    consult_parser = subparsers.add_parser(
        "consult",
        parents=[parent_parser],
        help="Consult external AI tools for test debugging",
        description="Consult external AI tools with auto-routing and prompt formatting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Failure types:
  assertion     - Assertion mismatch (expected vs actual)
  exception     - Runtime exceptions (AttributeError, KeyError, etc.)
  import        - Import/packaging errors
  fixture       - Pytest fixture issues
  timeout       - Performance/timeout issues
  flaky         - Non-deterministic test failures
  multi-file    - Issues affecting multiple files
  unclear-error - Unclear error messages
  validation    - Validate a proposed fix
""",
    )
    consult_parser.add_argument("failure_type", nargs="?", choices=CONSULT_FAILURE_TYPES, help="Type of test failure")
    consult_parser.add_argument("--error", "-e", help="Error message from pytest")
    consult_parser.add_argument("--hypothesis", "-H", help="Your hypothesis about the root cause")
    consult_parser.add_argument("--test-code", help="Path to file containing test code, or inline code")
    consult_parser.add_argument("--impl-code", help="Path to file containing implementation code, or inline code")
    consult_parser.add_argument("--context", help="Additional context about the issue")
    consult_parser.add_argument("--question", help="Specific question to ask (overrides defaults)")
    consult_parser.add_argument("--tool", "-t", choices=["gemini", "codex", "cursor-agent", "auto"], default="auto")
    consult_parser.add_argument("--prompt", "-p", help="Use a custom prompt instead of auto-formatting")
    consult_parser.add_argument("--dry-run", action="store_true", help="Show what would be run without executing")
    consult_parser.add_argument("--list-routing", action="store_true", help="Show the routing matrix")
    consult_parser.add_argument("--multi-agent", action="store_true", help="Consult multiple agents in parallel")
    consult_parser.add_argument("--pair", choices=list(MULTI_AGENT_PAIRS.keys()), default="default", help="Multi-agent pair to use")
    consult_parser.set_defaults(func=cmd_consult)

    discover_parser = subparsers.add_parser(
        "discover",
        parents=[parent_parser],
        help="Discover and analyze test structure",
        description="Discover test files, fixtures, markers, and project structure",
    )
    discover_parser.add_argument("directory", nargs="?", default=".", help="Directory to analyze")
    discover_parser.add_argument("--summary", action="store_true", help="Show summary only")
    discover_parser.add_argument("--tree", action="store_true", help="Show directory tree structure")
    discover_parser.add_argument("--fixtures", action="store_true", help="Show all fixtures")
    discover_parser.add_argument("--markers", action="store_true", help="Show all markers found")
    discover_parser.add_argument("--detailed", action="store_true", help="Show detailed information about each test file")
    discover_parser.set_defaults(func=cmd_discover)

    run_parser = subparsers.add_parser(
        "run",
        help="Run pytest with presets or custom configuration",
        description="Smart pytest runner with presets for common scenarios",
        parents=[parent_parser],
    )

    preset_group = run_parser.add_mutually_exclusive_group()
    for preset_name, preset_config in get_presets().items():
        option_flag = f"--{preset_name}"
        if preset_name in {"debug", "verbose"}:
            option_flag = f"--preset-{preset_name}"
        preset_group.add_argument(
            option_flag,
            action="store_const",
            const=preset_name,
            dest="preset",
            help=preset_config["description"],
        )

    run_parser.add_argument("--list", action="store_true", help="List all available presets")
    run_parser.add_argument("--pattern", "-k", help="Pattern to match test names")
    run_parser.add_argument("path", nargs="?", help="Test file, directory, or specific test to run")
    run_parser.add_argument("extra_args", nargs="*", help="Additional arguments to pass to pytest")
    run_parser.set_defaults(func=cmd_run)
