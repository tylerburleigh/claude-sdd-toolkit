#!/usr/bin/env python3
"""
Spec-Driven Development Tools - Next Task Discovery
A modular CLI utility for working with spec-driven development workflows.

Refactored to use sdd-common utilities and modular operations.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
import os

from rich.console import Console

# Clean imports - no sys.path manipulation needed!

# Import from common utilities
from claude_skills.common import (
    find_specs_directory,
    load_json_spec,
    get_progress_summary,
    list_phases,
    PrettyPrinter,
    ensure_reports_directory,
    # Query operations
    query_tasks,
    check_complete,
    list_blockers as list_blocked_tasks,
    # JSON output formatting
    print_json_output,
)
from claude_skills.common.ui_factory import create_ui
from claude_skills.common.json_output import output_json
from claude_skills.common.completion import format_completion_prompt
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    PREPARE_TASK_ESSENTIAL,
    PREPARE_TASK_STANDARD,
    PROGRESS_ESSENTIAL,
    PROGRESS_STANDARD,
    CHECK_DEPS_ESSENTIAL,
    CHECK_DEPS_STANDARD,
    FIND_SPECS_ESSENTIAL,
    FIND_SPECS_STANDARD,
    NEXT_TASK_ESSENTIAL,
    NEXT_TASK_STANDARD,
    TASK_INFO_ESSENTIAL,
    TASK_INFO_STANDARD,
    INIT_ENV_ESSENTIAL,
    INIT_ENV_STANDARD,
    VALIDATE_SPEC_ESSENTIAL,
    VALIDATE_SPEC_STANDARD,
    FIND_PATTERN_ESSENTIAL,
    FIND_PATTERN_STANDARD,
    DETECT_PROJECT_ESSENTIAL,
    DETECT_PROJECT_STANDARD,
    FIND_TESTS_ESSENTIAL,
    FIND_TESTS_STANDARD,
    CHECK_ENVIRONMENT_ESSENTIAL,
    CHECK_ENVIRONMENT_STANDARD,
    FIND_CIRCULAR_DEPS_ESSENTIAL,
    FIND_CIRCULAR_DEPS_STANDARD,
    FIND_RELATED_FILES_ESSENTIAL,
    FIND_RELATED_FILES_STANDARD,
    VALIDATE_PATHS_ESSENTIAL,
    VALIDATE_PATHS_STANDARD,
    SPEC_STATS_ESSENTIAL,
    SPEC_STATS_STANDARD,
    FORMAT_PLAN_ESSENTIAL,
    FORMAT_PLAN_STANDARD,
)

# Import from sdd_next module
from claude_skills.sdd_next.discovery import (
    get_next_task,
    get_task_info,
    check_dependencies,
    prepare_task,
)
from claude_skills.sdd_next.project import (
    detect_project,
    find_tests,
    check_environment,
    find_related_files,
)
from claude_skills.sdd_next.validation import (
    validate_spec,
    find_circular_deps,
    validate_paths,
    spec_stats,
)
from claude_skills.sdd_next.workflow import (
    init_environment,
    find_pattern,
)


def format_execution_plan(spec_id: str, task_id: str, specs_dir: Path) -> str:
    """
    Format an execution plan for a task with proper newlines and structure.

    Args:
        spec_id: Specification ID
        task_id: Task ID to format
        specs_dir: Path to specs directory

    Returns:
        Formatted execution plan string ready for display
    """
    # Load state and task data
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return f"Error: Could not load JSON spec for {spec_id}"

    # Get task information
    task_prep = prepare_task(spec_id, specs_dir, task_id)
    if not task_prep.get("success"):
        return f"Error: {task_prep.get('error', 'Failed to prepare task')}"

    task_data = task_prep['task_data']
    deps = task_prep['dependencies']

    # Get progress data
    progress = get_progress_summary(spec_data)

    # Get parent phase info
    parent_id = task_data.get('parent', '')
    phase_data = spec_data['hierarchy'].get(parent_id, {})
    phase_title = phase_data.get('title', 'Unknown Phase')
    phase_num = parent_id.replace('phase-', '') if parent_id.startswith('phase-') else ''

    # Build the formatted plan
    lines = []

    # Header
    lines.append(f"# Execution Plan Ready: {task_id}\n")

    # Task Summary
    lines.append("## 📋 Task Summary")

    file_path = task_data.get('metadata', {}).get('file_path', 'N/A')
    lines.append(f"**File:** {file_path}")

    title = task_data.get('title', 'Unknown Task')
    lines.append(f"**Purpose:** {title}")

    if phase_num:
        phase_display = f"Phase {phase_num} - {phase_title}"
    else:
        phase_display = phase_title

    total_tasks = progress.get('total', 0)
    completed_tasks = progress.get('completed', 0)
    percentage = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0
    lines.append(f"**Phase:** {phase_display} ({completed_tasks}/{total_tasks} tasks, {percentage}%)")

    estimated_hours = task_data.get('metadata', {}).get('estimated_hours', 0)
    if estimated_hours:
        lines.append(f"**Estimated Time:** {estimated_hours} hours")

    lines.append("")  # Blank line

    # Readiness & dependencies
    lines.append("## ✅ Readiness Check")

    if deps:
        if deps.get('can_start'):
            lines.append("- Ready to begin: no blocking dependencies")
        else:
            lines.append("- ⚠️  Blocked: resolve dependencies before starting")

        if deps.get('blocked_by'):
            lines.append("")
            lines.append("**Hard Dependencies**")
            for dep in deps['blocked_by']:
                status = dep.get('status', 'unknown')
                lines.append(f"- {dep['id']}: {dep['title']} ({status})")

        if deps.get('soft_depends'):
            lines.append("")
            lines.append("**Recommended Pre-work**")
            for dep in deps['soft_depends']:
                status_symbol = "✓" if dep.get('status') == 'completed' else "○"
                lines.append(f"- {status_symbol} {dep['id']}: {dep['title']} ({dep.get('status', 'unknown')})")

    lines.append("")

    # Task metadata summary
    metadata = task_data.get('metadata', {}) or {}
    description = task_data.get('description') or metadata.get('description')
    additional_notes = metadata.get('notes')
    if description or additional_notes or metadata:
        lines.append("## 🎯 Implementation Details")
        lines.append("")

        if description:
            lines.append(description.strip())
            lines.append("")

        key_order = [
            ('file_path', 'Target File'),
            ('test_path', 'Related Test'),
            ('command', 'Command'),
            ('expected', 'Expected Outcome'),
            ('estimated_hours', 'Estimated Hours'),
            ('risk_level', 'Risk Level'),
        ]

        shown_keys = set()
        for key, label in key_order:
            if key in metadata and metadata[key] not in (None, ""):
                lines.append(f"- {label}: {metadata[key]}")
                shown_keys.add(key)

        # Include any remaining metadata fields
        for key, value in metadata.items():
            if key in shown_keys or value in (None, ""):
                continue
            pretty_key = key.replace('_', ' ').title()
            lines.append(f"- {pretty_key}: {value}")

        if additional_notes:
            lines.append("")
            lines.append("**Notes**")
            lines.append(additional_notes.strip())

        lines.append("")

    # Success Criteria
    lines.append("## ✓ Success Criteria")
    lines.append("")
    lines.append("Task complete when:")
    task_type = task_data.get('type', 'task')
    if task_type == 'verify':
        lines.append("- Verification steps pass successfully")
        lines.append("- No errors or warnings reported")
    else:
        lines.append("- All changes implemented as specified")
        lines.append("- Code compiles/runs without errors")
        if 'test' in title.lower() or metadata.get('test_path'):
            lines.append("- Associated tests updated and passing")
    lines.append("")  # Blank line

    # Next Tasks
    if deps and deps.get('blocks'):
        lines.append("## 📦 Next Tasks After This")
        for blocked_task in deps['blocks']:
            lines.append(f"- {blocked_task['id']}: {blocked_task['title']} (blocked by this)")
        lines.append("")  # Blank line

    # Doc Context (from doc-query integration)
    if task_prep.get('doc_context'):
        doc_ctx = task_prep['doc_context']
        lines.append("## 📚 Codebase Context")
        lines.append("")
        if doc_ctx.get('message'):
            lines.append(doc_ctx['message'])
            lines.append("")

        if doc_ctx.get('files'):
            lines.append("**Relevant Files:**")
            for file_path in doc_ctx['files'][:5]:  # Show top 5
                lines.append(f"- {file_path}")
            if len(doc_ctx['files']) > 5:
                lines.append(f"- ... and {len(doc_ctx['files']) - 5} more")
            lines.append("")

        if doc_ctx.get('similar'):
            lines.append("**Similar Implementations:**")
            for impl in doc_ctx['similar'][:3]:
                lines.append(f"- {impl}")
            lines.append("")

    # Validation Warnings
    if task_prep.get('validation_warnings'):
        lines.append("## ⚠️  Validation Warnings")
        lines.append("")
        for warning in task_prep['validation_warnings'][:3]:
            lines.append(f"- {warning}")
        lines.append("")

    # Note: Interactive prompt handled by Claude using AskUserQuestion tool
    # The CLI just returns the execution plan details

    return '\n'.join(lines)


def cmd_verify_tools(args, printer):
    """Verify required tools are available."""
    # Collect data
    required_tools = {"python": True}  # Always available since we're running
    optional_tools_status = {}

    optional_tools = ["git", "grep", "cat"]
    for tool in optional_tools:
        is_available = os.system(f"command -v {tool} > /dev/null 2>&1") == 0
        optional_tools_status[tool] = is_available

    # JSON output mode
    if args.json:
        output = {
            "required": required_tools,
            "optional": optional_tools_status,
            "all_available": all(optional_tools_status.values())
        }
        output_json(output, compact=getattr(args, 'compact', False))
        return 0

    # Rich UI mode
    printer.action("Checking required tools...")
    printer.success("Python 3 is available")

    for tool, available in optional_tools_status.items():
        if available:
            printer.success(f"{tool} is available")
        else:
            printer.warning(f"{tool} not found (optional)")

    printer.success("All required tools verified")
    return 0


def cmd_find_specs(args, printer):
    """Find specs directories."""
    # Check if verbose mode requests JSON output
    verbose_json = args.verbose and getattr(args, 'json', False)

    if not verbose_json:
        printer.action("Searching for specs directory...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))

    if not specs_dir:
        if not verbose_json:
            printer.error("No specs/active directory found")
        return 1

    # VERBOSE mode with JSON output
    if verbose_json:
        # Build payload with metadata
        payload = {
            "specs_dir": str(specs_dir),
            "exists": specs_dir.exists(),
            "auto_detected": True,  # find_specs_directory auto-detects
        }

        # Apply verbosity filtering
        filtered_output = prepare_output(payload, args, FIND_SPECS_ESSENTIAL, FIND_SPECS_STANDARD)
        output_json(filtered_output, compact=getattr(args, 'compact', False))
        return 0

    # QUIET/NORMAL mode - plain text output
    printer.success("Found specs directory")
    print(f"{specs_dir}")

    if args.verbose:
        # List spec files from all subdirectories
        spec_files = []
        for subdir in ["active", "completed", "archived"]:
            subdir_path = specs_dir / subdir
            if subdir_path.is_dir():
                spec_files.extend([(spec, subdir) for spec in subdir_path.glob("*.json")])

        if spec_files:
            printer.info(f"Found {len(spec_files)} spec file(s):")
            for spec, status in sorted(spec_files, key=lambda x: (x[1], x[0].name)):
                printer.detail(f"• [{status}] {spec.name}")

    return 0


def cmd_next_task(args, printer):
    """Find next actionable task."""
    if not args.json:
        printer.action("Finding next actionable task...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    spec_data = load_json_spec(args.spec_id, specs_dir)
    if not spec_data:
        return 1

    # Check if spec is in pending folder
    from ..common.paths import find_spec_file
    spec_path = find_spec_file(args.spec_id, specs_dir)
    if spec_path and '/pending/' in str(spec_path):
        printer.error(
            f"This spec is in your pending backlog. "
            f"Run 'sdd activate-spec {args.spec_id}' to move it to active/ before starting work."
        )
        return 1

    next_task = get_next_task(spec_data)

    if not next_task:
        printer.error("No actionable tasks found")
        return 1

    task_id, task_data = next_task

    if args.json:
        output = {
            "task_id": task_id,
            "title": task_data.get("title", ""),
            "status": task_data.get("status", ""),
            "file_path": task_data.get("metadata", {}).get("file_path", ""),
            "estimated_hours": task_data.get("metadata", {}).get("estimated_hours", 0)
        }
        output = prepare_output(output, args, NEXT_TASK_ESSENTIAL, NEXT_TASK_STANDARD)
        print_json_output(output, compact=args.compact)
    else:
        printer.success("Next task identified")
        printer.result("Task ID", task_id)
        printer.result("Title", task_data.get('title', ''))
        file_path = task_data.get("metadata", {}).get("file_path", "")
        if file_path:
            printer.result("File", file_path)

    return 0


def cmd_task_info(args, printer):
    """Get detailed task information."""
    if not args.json:
        printer.action(f"Retrieving information for task {args.task_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    spec_data = load_json_spec(args.spec_id, specs_dir)
    if not spec_data:
        return 1

    task_data = get_task_info(spec_data, args.task_id)

    if not task_data:
        printer.error(f"Task {args.task_id} not found")
        return 1

    if args.json:
        # Include the requested task ID explicitly so callers don't have to
        # infer it from context (the hierarchy nodes don't store their id).
        output_data = dict(task_data)
        output_data.setdefault("id", args.task_id)
        output = prepare_output(output_data, args, TASK_INFO_ESSENTIAL, TASK_INFO_STANDARD)
        print_json_output(output, compact=args.compact)
    else:
        printer.success("Task information retrieved")
        printer.result("Task ID", args.task_id)
        printer.result("Title", task_data.get('title', ''))
        printer.result("Status", task_data.get('status', ''))
        printer.result("Type", task_data.get('type', ''))
        printer.result("Parent", task_data.get('parent', ''))

        file_path = task_data.get("metadata", {}).get("file_path", "")
        if file_path:
            printer.result("File", file_path)

        estimated = task_data.get("metadata", {}).get("estimated_hours", 0)
        if estimated:
            printer.result("Estimated", f"{estimated} hours")

    return 0


def _print_dependency_tree(deps: Dict[str, Any], task_id: str, ui) -> None:
    """
    Print dependency tree visualization using UI abstraction.

    Supports both RichUi (Rich.Tree with colors) and PlainUi (plain text tree).
    Uses ui.print_tree() abstraction for backend-agnostic rendering.

    Args:
        deps: Dependency information dictionary from check_dependencies()
        task_id: The task ID being analyzed
        ui: UI instance for console output
    """
    # Prepare tree data in nested dict format for ui.print_tree()
    tree_data: Dict[str, Any] = {}

    # Determine if we're in Rich mode for conditional markup
    use_rich = ui.console is not None

    # Add blocked_by dependencies (hard blockers)
    if deps.get('blocked_by'):
        if use_rich:
            blocked_key = "✗ [red bold]Blocked by[/red bold]"
        else:
            blocked_key = "✗ Blocked by"

        tree_data[blocked_key] = {}
        for dep in deps['blocked_by']:
            dep_id = dep.get('id', 'unknown')
            dep_title = dep.get('title', 'Untitled')
            dep_status = dep.get('status', 'unknown')
            # Truncate long titles
            if len(dep_title) > 60:
                dep_title = dep_title[:57] + "..."

            if use_rich:
                tree_data[blocked_key][f"[red]{dep_id}[/red]"] = f"{dep_title} [dim]({dep_status})[/dim]"
            else:
                tree_data[blocked_key][dep_id] = f"{dep_title} ({dep_status})"

    # Add soft dependencies (recommended pre-work)
    if deps.get('soft_depends'):
        if use_rich:
            soft_key = "⚠️  [yellow bold]Soft dependencies[/yellow bold]"
        else:
            soft_key = "⚠️  Soft dependencies"

        tree_data[soft_key] = {}
        for dep in deps['soft_depends']:
            dep_id = dep.get('id', 'unknown')
            dep_title = dep.get('title', 'Untitled')
            dep_status = dep.get('status', 'unknown')
            status_mark = "✓" if dep_status == 'completed' else "○"
            # Truncate long titles
            if len(dep_title) > 60:
                dep_title = dep_title[:57] + "..."

            if use_rich:
                tree_data[soft_key][f"{status_mark} [yellow]{dep_id}[/yellow]"] = f"{dep_title} [dim]({dep_status})[/dim]"
            else:
                tree_data[soft_key][f"{status_mark} {dep_id}"] = f"{dep_title} ({dep_status})"

    # Add blocks (tasks blocked by this one)
    if deps.get('blocks'):
        if use_rich:
            blocks_key = "⏳ [blue bold]This task blocks[/blue bold]"
        else:
            blocks_key = "⏳ This task blocks"

        tree_data[blocks_key] = {}
        for dep in deps['blocks']:
            dep_id = dep.get('id', 'unknown')
            dep_title = dep.get('title', 'Untitled')
            # Truncate long titles
            if len(dep_title) > 60:
                dep_title = dep_title[:57] + "..."

            if use_rich:
                tree_data[blocks_key][f"[blue]{dep_id}[/blue]"] = dep_title
            else:
                tree_data[blocks_key][dep_id] = dep_title

    # If no dependencies at all, add a note
    if not tree_data:
        if use_rich:
            tree_data["[dim]No dependencies[/dim]"] = {}
        else:
            tree_data["No dependencies"] = {}

    # Build root label with status indicator
    can_start_indicator = "✅" if deps.get('can_start') else "🚫"
    if use_rich:
        root_label = f"{can_start_indicator} [bold]{task_id}[/bold]"
    else:
        root_label = f"{can_start_indicator} {task_id}"

    # Use ui.print_tree() abstraction instead of manual rendering
    ui.print_tree(tree_data, label=root_label)


def cmd_check_deps(args, printer, ui=None):
    """Check task dependencies."""
    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    spec_data = load_json_spec(args.spec_id, specs_dir)
    if not spec_data:
        return 1

    # If no task_id provided, check all tasks
    if args.task_id is None:
        return _check_all_task_deps(spec_data, args, printer, ui)

    # Single task check (existing behavior)
    if not args.json:
        printer.action(f"Checking dependencies for {args.task_id}...")

    deps = check_dependencies(spec_data, args.task_id)

    if "error" in deps:
        printer.error(deps["error"])
        return 1

    if args.json:
        # Apply verbosity filtering for JSON output
        filtered_output = prepare_output(deps, args, CHECK_DEPS_ESSENTIAL, CHECK_DEPS_STANDARD)
        output_json(filtered_output, compact=args.compact)
    else:
        printer.success("Dependency analysis complete")
        readiness_message = (
            "Task can start: no blocking dependencies detected."
            if deps.get("can_start")
            else "Task cannot start yet: resolve blocking dependencies."
        )
        printer.result("Readiness", readiness_message)
        print()  # Blank line for spacing

        # Print the dependency tree using UI abstraction
        if ui is None:
            ui = create_ui(force_rich=True)
        _print_dependency_tree(deps, args.task_id, ui)

    return 0


def _check_all_task_deps(spec_data, args, printer, ui=None):
    """Check dependencies for all tasks in the spec."""
    if not args.json:
        printer.action("Checking dependencies for all tasks...")

    hierarchy = spec_data.get("hierarchy", {})
    all_results = []

    # Iterate through hierarchy and check only task nodes
    for task_id, task_data in hierarchy.items():
        if task_data.get("type") == "task":
            deps = check_dependencies(spec_data, task_id)
            if "error" not in deps:
                all_results.append(deps)

    if args.json:
        print_json_output(all_results, compact=args.compact)
    else:
        # Categorize tasks
        ready = [d for d in all_results if d['can_start']]
        blocked = [d for d in all_results if not d['can_start']]
        has_soft_deps = [d for d in all_results if d['soft_depends']]

        printer.success("Dependency analysis complete")
        printer.result("Total tasks", str(len(all_results)))
        printer.result("Ready to start", str(len(ready)))
        printer.result("Blocked", str(len(blocked)))
        printer.result("With soft dependencies", str(len(has_soft_deps)))
        print()  # Blank line for spacing

        # Use Rich Console for colored output
        # Skip Rich visualization if using PlainUi (console would be None)
        if ui and ui.console is None:
            printer.info("Colored dependency visualization not available in plain mode.")
            return 0

        console = ui.console if ui else create_ui(force_rich=True).console

        if ready:
            console.print("\n✅ [bold green]Ready to start:[/bold green]")
            for dep in ready:
                console.print(f"  • [green]{dep['task_id']}[/green]")

        if blocked:
            console.print("\n🚫 [bold red]Blocked:[/bold red]")
            for dep in blocked:
                blockers = ", ".join([b['id'] for b in dep['blocked_by']])
                console.print(f"  • [red]{dep['task_id']}[/red] [dim](blocked by: {blockers})[/dim]")

        if has_soft_deps:
            console.print("\n⚠️  [bold yellow]With soft dependencies:[/bold yellow]")
            for dep in has_soft_deps:
                soft = ", ".join([s['id'] for s in dep['soft_depends']])
                console.print(f"  • [yellow]{dep['task_id']}[/yellow] [dim](depends on: {soft})[/dim]")

    return 0


def cmd_progress(args, printer):
    """Show overall progress."""
    if not args.json:
        printer.action("Calculating progress...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    spec_data = load_json_spec(args.spec_id, specs_dir)
    if not spec_data:
        return 1

    progress = get_progress_summary(spec_data)

    if args.json:
        # Apply verbosity filtering for JSON output
        filtered_output = prepare_output(progress, args, PROGRESS_ESSENTIAL, PROGRESS_STANDARD)
        output_json(filtered_output, compact=args.compact)
    else:
        printer.success("Progress calculated")
        printer.result("Spec", f"{progress['title']} ({progress['spec_id']})")
        printer.result("Progress", f"{progress['completed_tasks']}/{progress['total_tasks']} tasks ({progress['percentage']}%)")

        if progress['current_phase']:
            phase = progress['current_phase']
            phase_pct = int((phase['completed'] / phase['total'] * 100)) if phase['total'] > 0 else 0
            printer.result("Current Phase", f"{phase['title']} ({phase['completed']}/{phase['total']}, {phase_pct}%)")

    return 0




def cmd_init_env(args, printer):
    """Initialize development environment."""
    if not args.json and not args.export:
        printer.action("Initializing development environment...")

    env = init_environment(args.spec_path)

    if not env["success"]:
        printer.error(env['error'])
        return 1

    if args.json:
        output = prepare_output(env, args, INIT_ENV_ESSENTIAL, INIT_ENV_STANDARD)
        output_json(output, compact=getattr(args, "compact", False))
    elif args.export:
        # Output as shell export statements
        print(f"export SPECS_DIR='{env['specs_dir']}'")
        print(f"export ACTIVE_DIR='{env['active_dir']}'")
    else:
        printer.success("Environment initialized")
        printer.result("Specs Directory", env['specs_dir'])
        printer.result("Active Directory", env['active_dir'])

    return 0


def cmd_prepare_task(args, printer):
    """
    Prepare task for implementation.

    This command integrates with the automatic completion detection system.
    It calls prepare_task() from discovery.py which returns completion signals
    when all tasks in a spec are finished.

    Completion Signal Handling (from prepare_task() in discovery.py):
    ----------------------------------------------------------------
    prepare_task() performs completion detection and returns different signals
    based on the spec's state:

    Scenario 1: No Actionable Tasks Available
        - Returned when: No pending/unblocked tasks found
        - Signal: success=False, spec_complete=False
        - completion_info present if tasks are blocked
        - Indicates: Tasks exist but are blocked by dependencies

    Scenario 2: Spec/Phase Complete
        - Returned when: All tasks completed, no blocked tasks
        - Signal: success=True, spec_complete=True
        - completion_info contains should_prompt=True
        - Indicates: Ready to finalize and move to completed/

    Scenario 3: Normal Task Found
        - Returned when: Found actionable task to work on
        - Signal: success=True, task_id set, spec_complete=False
        - Indicates: Continue normal workflow with returned task

    The completion_info dict structure (from should_prompt_completion):
        {
            "should_prompt": bool,      # True if ready to complete
            "reason": str,               # Human-readable explanation
            "is_complete": bool,         # All tasks done
            "blocked_count": int,        # Number of blocked tasks
            "blocked_tasks": List[str],  # IDs of blocked tasks
            "node_id": str,              # Node that was checked
            "error": Optional[str]       # Error if check failed
        }
    """
    if not args.json:
        printer.action("Preparing task for implementation...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    # Ensure .reports/ directory exists (defensive)
    ensure_reports_directory(specs_dir)

    # Call prepare_task() - this is where completion detection happens
    # Returns completion signals when spec is finished or blocked
    include_full_journal = getattr(args, 'include_full_journal', False)
    include_phase_history = getattr(args, 'include_phase_history', False)
    include_spec_overview = getattr(args, 'include_spec_overview', False)
    task_prep = prepare_task(
        args.spec_id,
        specs_dir,
        args.task_id,
        include_full_journal=include_full_journal,
        include_phase_history=include_phase_history,
        include_spec_overview=include_spec_overview,
    )
    requested_extended_context = include_full_journal or include_phase_history or include_spec_overview

    # ==========================================
    # Documentation Generation Prompt (Proactive)
    # ==========================================
    # If documentation is missing or stale, prompt user to generate it
    # This happens before task processing to provide context for implementation
    if task_prep.get('doc_prompt_needed') and not args.json:
        from claude_skills.common.doc_integration import prompt_for_generation

        doc_status = task_prep.get('doc_status', 'unknown')
        context = f"Documentation is {doc_status}. Generating docs enables automated file suggestions and dependency analysis."

        if prompt_for_generation(skill_name="sdd-next", context=context):
            # User accepted - suggest running sdd doc generate
            print("\n✅ To generate documentation, run:")
            print("   sdd doc generate")
            print("\n📝 After generation completes, re-run prepare-task to use the new documentation.\n")
        else:
            # User declined - continue with manual exploration
            print("\n📝 Continuing without documentation. Manual file exploration will be used.\n")

    if not task_prep["success"]:
        # ==========================================
        # SCENARIO 1: No Actionable Tasks Available
        # ==========================================
        # This occurs when:
        #   - No pending tasks exist, OR
        #   - All pending tasks are blocked by dependencies
        #
        # The completion_info will be present if tasks are blocked,
        # helping distinguish between "truly done" vs "stuck on blockers"
        completion_info = task_prep.get('completion_info')
        if completion_info:
            # Enhanced error messaging with completion context
            printer.error(task_prep['error'])
            reason = completion_info.get('reason', '')
            if reason:
                printer.detail(f"Reason: {reason}")

            # Show blocked task details if available
            blocked_count = completion_info.get('blocked_count', 0)
            blocked_task_ids = completion_info.get('blocked_tasks', [])
            if blocked_count > 0 and blocked_task_ids:
                printer.detail(f"Blocked tasks: {blocked_count}")

                # Load spec to get task details
                try:
                    spec_data = load_json_spec(args.spec_id, specs_dir)
                    hierarchy = spec_data.get("hierarchy", {})

                    print("\n✗ Blocked Task Details:")
                    for task_id in blocked_task_ids:
                        task = hierarchy.get(task_id, {})
                        title = task.get("title", "")
                        metadata = task.get("metadata", {})

                        printer.detail(f"  • {task_id}: {title}")

                        blocker_desc = metadata.get("blocker_description", "")
                        if blocker_desc:
                            printer.detail(f"    Reason: {blocker_desc}")

                        blocker_ticket = metadata.get("blocker_ticket", "")
                        if blocker_ticket:
                            printer.detail(f"    Ticket: {blocker_ticket}")

                        blocker_type = metadata.get("blocker_type", "")
                        if blocker_type:
                            printer.detail(f"    Type: {blocker_type}")
                except Exception as e:
                    # Fallback to just showing count if we can't load details
                    printer.detail(f"  (Run 'sdd list-blockers {args.spec_id}' for full details)")
            elif blocked_count > 0:
                # Has count but no task IDs - show fallback message
                printer.detail(f"Blocked tasks: {blocked_count}")
                print(f"\n💡 Run 'sdd list-blockers {args.spec_id}' for details")
        else:
            # Original error handling (no completion info available)
            # This path is rare - usually for validation errors
            printer.error(task_prep['error'])
        return 1

    # ==========================================
    # SCENARIO 2: Spec/Phase Complete
    # ==========================================
    # This is the COMPLETION SIGNAL from automatic detection!
    #
    # This occurs when:
    #   - All tasks in the spec are marked "completed"
    #   - No tasks are in "blocked" state
    #   - should_prompt_completion() returned should_prompt=True
    #
    # At this point, the spec is ready to be finalized and moved
    # to the completed/ directory. This displays a user-friendly
    # completion prompt (task-3-2-2).
    if task_prep.get('spec_complete'):
        completion_info = task_prep.get('completion_info', {})

        if args.json:
            # Apply verbosity filtering for JSON output
            filtered_output = prepare_output(task_prep, args, PREPARE_TASK_ESSENTIAL, PREPARE_TASK_STANDARD)
            output_json(filtered_output, compact=args.compact)
        else:
            # Show completion message
            printer.success("All tasks completed!")
            printer.result("Status", "Spec is complete and ready to finalize")

            reason = completion_info.get('reason', '')
            if reason:
                printer.detail(reason)

            # Display formatted completion prompt (task-3-2-2)
            # Load spec data for prompt formatting
            spec_data = load_json_spec(args.spec_id, specs_dir)
            if spec_data:
                # Generate formatted completion prompt
                prompt_result = format_completion_prompt(spec_data, phase_id=None, show_hours_input=False)

                if prompt_result.get('error'):
                    # Fallback to simple message if prompt generation fails
                    printer.warning(f"Could not generate completion prompt: {prompt_result['error']}")
                    print(f"\n💡 Run 'sdd complete-spec {args.spec_id}' to mark as complete and move to completed/ folder")
                else:
                    # Display the formatted prompt
                    print(f"\n{prompt_result['prompt_text']}")
                    print(f"\n💡 To complete this spec, run: sdd complete-spec {args.spec_id}")
            else:
                # Fallback if spec data cannot be loaded
                print(f"\n💡 Run 'sdd complete-spec {args.spec_id}' to mark as complete and move to completed/ folder")

        return 0

    # ==========================================
    # SCENARIO 3: Normal Task Found
    # ==========================================
    # This is the standard workflow path.
    #
    # This occurs when:
    #   - Found a pending task that is unblocked
    #   - Task is ready to be worked on
    #   - Spec still has work remaining
    #
    # The returned task_prep includes:
    #   - task_id: The next task to work on
    #   - task_data: Full task metadata from JSON spec
    #   - dependencies: Dependency analysis (blocked_by, soft_depends, blocks)
    #   - doc_context: Optional codebase context from doc-query
    if args.json:
        # Apply verbosity filtering for JSON output
        filtered_output = prepare_output(task_prep, args, PREPARE_TASK_ESSENTIAL, PREPARE_TASK_STANDARD)
        if requested_extended_context and task_prep.get('extended_context'):
            filtered_output['extended_context'] = task_prep['extended_context']
        output_json(filtered_output, compact=args.compact)
    else:
        printer.success(f"Task prepared: {task_prep['task_id']}")
        printer.result("Task", task_prep['task_data'].get('title', ''))
        printer.result("Status", task_prep['task_data'].get('status', ''))

        file_path = task_prep['task_data'].get('metadata', {}).get('file_path', '')
        if file_path:
            printer.result("File", file_path)

        # Dependencies
        deps = task_prep['dependencies']
        if deps and not deps.get('error'):
            can_start = "Yes" if deps['can_start'] else "No"
            printer.result("Can start", can_start)

            if deps.get('blocked_by'):
                print("\n✗ Blocked by:")
                for dep in deps['blocked_by']:
                    printer.detail(f"• {dep['id']}: {dep['title']}")

            if deps.get('soft_depends'):
                print("\n⚠️  Dependencies:")
                for dep in deps['soft_depends']:
                    status_mark = "✓" if dep['status'] == 'completed' else "○"
                    printer.detail(f"{status_mark} {dep['id']}: {dep['title']}")

        if requested_extended_context and task_prep.get('extended_context'):
            ext = task_prep['extended_context']
            print("\n🔎 Extended Context")
            prev_entries = ext.get('previous_sibling_journal')
            if prev_entries is not None:
                print(f"  Previous sibling journal entries: {len(prev_entries)}")
                for entry in prev_entries:
                    printer.detail(
                        f"    {entry.get('timestamp', 'unknown')} [{entry.get('entry_type', 'note')}] "
                        f"{entry.get('title', '')}"
                    )
            phase_entries = ext.get('phase_journal')
            if phase_entries is not None:
                print(f"  Phase journal entries: {len(phase_entries)}")
            spec_overview = ext.get('spec_overview')
            if spec_overview:
                print("  Spec overview:")
                printer.detail(
                    f"    {spec_overview.get('completed_tasks', 0)}/"
                    f"{spec_overview.get('total_tasks', 0)} tasks completed"
                )
                current_phase = spec_overview.get('current_phase') or {}
                if current_phase:
                    printer.detail(
                        f"    Current phase: {current_phase.get('title', '')}"
                        f" ({current_phase.get('completed', 0)}/"
                        f"{current_phase.get('total', 0)})"
                    )

    return 0


def cmd_format_plan(args, printer):
    """Format execution plan for display."""
    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    formatted = format_execution_plan(args.spec_id, args.task_id, specs_dir)

    # Check if it's an error message
    if formatted.startswith("Error:"):
        printer.error(formatted)
        return 1

    # Print the formatted plan directly
    print(formatted)
    return 0


def cmd_validate_spec(args, printer):
    """Validate spec file."""
    if not args.json:
        printer.action("Validating spec file...")

    spec_file = Path(args.spec_file).resolve()
    validation = validate_spec(spec_file)

    if args.json:
        output = prepare_output(validation, args, VALIDATE_SPEC_ESSENTIAL, VALIDATE_SPEC_STANDARD)
        output_json(output, compact=getattr(args, 'compact', False))
    else:
        printer.result("Validating", validation['spec_file'])

        if validation['spec_id']:
            printer.result("Spec ID", validation['spec_id'])

        if validation['json_spec_file']:
            printer.result("JSON spec file", validation['json_spec_file'])

        if validation['errors']:
            print(f"\n✗ Errors ({len(validation['errors'])}):")
            for error in validation['errors']:
                printer.detail(f"• {error}")

        if validation['warnings']:
            print(f"\n⚠️  Warnings ({len(validation['warnings'])}):")
            for warning in validation['warnings']:
                printer.detail(f"• {warning}")

        if validation['valid']:
            printer.success("Validation passed")
        else:
            printer.error("Validation failed")

    return 0 if validation['valid'] else 1


def cmd_find_pattern(args, printer):
    """Find files matching a pattern."""
    if not args.json:
        printer.action(f"Searching for files matching '{args.pattern}'...")

    directory = Path(args.directory).resolve() if args.directory else None
    matches = find_pattern(args.pattern, directory)

    if args.json:
        data = {"pattern": args.pattern, "matches": matches}
        output = prepare_output(data, args, FIND_PATTERN_ESSENTIAL, FIND_PATTERN_STANDARD)
        output_json(output, compact=getattr(args, 'compact', False))
    else:
        if matches:
            printer.success(f"Found {len(matches)} file(s) matching '{args.pattern}'")
            for match in matches:
                printer.detail(f"• {match}")
        else:
            printer.warning(f"No files found matching '{args.pattern}'")

    return 0


def cmd_detect_project(args, printer):
    """Detect project type and dependencies."""
    if not args.json:
        printer.action("Detecting project type...")

    directory = Path(args.directory).resolve() if args.directory else None
    project = detect_project(directory)

    if args.json:
        output = prepare_output(project, args, DETECT_PROJECT_ESSENTIAL, DETECT_PROJECT_STANDARD)
        output_json(output, compact=getattr(args, 'compact', False))
    else:
        printer.success("Project analyzed")
        printer.result("Project Type", project['project_type'])

        if project['dependency_manager']:
            printer.result("Dependency Manager", project['dependency_manager'])

        if project['config_files']:
            print("\nConfiguration Files:")
            for config in project['config_files']:
                printer.detail(f"• {config}")

        if project['dependencies']:
            print(f"\nDependencies ({len(project['dependencies'])}):")
            for name, version in list(project['dependencies'].items())[:10]:
                printer.detail(f"• {name}: {version}")
            if len(project['dependencies']) > 10:
                printer.detail(f"... and {len(project['dependencies']) - 10} more")

        if project['dev_dependencies']:
            print(f"\nDev Dependencies ({len(project['dev_dependencies'])}):")
            for name, version in list(project['dev_dependencies'].items())[:10]:
                printer.detail(f"• {name}: {version}")
            if len(project['dev_dependencies']) > 10:
                printer.detail(f"... and {len(project['dev_dependencies']) - 10} more")

    return 0


def cmd_find_tests(args, printer):
    """Find test files and patterns."""
    if not args.json:
        printer.action("Searching for test files...")

    directory = Path(args.directory).resolve() if args.directory else None
    tests = find_tests(directory, args.source_file)

    if args.json:
        output = prepare_output(tests, args, FIND_TESTS_ESSENTIAL, FIND_TESTS_STANDARD)
        output_json(output, compact=getattr(args, 'compact', False))
    else:
        if tests['test_framework']:
            printer.success("Tests discovered")
            printer.result("Test Framework", tests['test_framework'])
        else:
            printer.info("No test framework detected")

        if args.source_file and tests['corresponding_test']:
            printer.result("Corresponding Test", tests['corresponding_test'])

        if tests['test_files']:
            print(f"\nFound {len(tests['test_files'])} test file(s):")
            for test_file in tests['test_files'][:20]:
                printer.detail(f"• {test_file}")
            if len(tests['test_files']) > 20:
                printer.detail(f"... and {len(tests['test_files']) - 20} more")
        else:
            printer.warning("No test files found")

    return 0


def cmd_check_environment(args, printer):
    """Check environmental requirements."""
    if not args.json:
        printer.action("Checking environment...")

    directory = Path(args.directory).resolve() if args.directory else None
    required_deps = args.required.split(',') if args.required else []

    env = check_environment(directory, required_deps)

    if args.json:
        output = prepare_output(env, args, CHECK_ENVIRONMENT_ESSENTIAL, CHECK_ENVIRONMENT_STANDARD)
        output_json(output, compact=getattr(args, 'compact', False))
    else:
        if env['valid']:
            printer.success("Environment is valid")
        else:
            printer.error("Environment has issues")

        if env['missing_dependencies']:
            print("\n✗ Missing Dependencies:")
            for dep in env['missing_dependencies']:
                printer.detail(f"• {dep}")

        if env['installed_dependencies']:
            print(f"\n✓ Installed Dependencies ({len(env['installed_dependencies'])}):")
            for name, version in list(env['installed_dependencies'].items())[:10]:
                printer.detail(f"• {name}: {version}")
            if len(env['installed_dependencies']) > 10:
                printer.detail(f"... and {len(env['installed_dependencies']) - 10} more")

        if env['config_files_found']:
            print("\n✓ Configuration Files Found:")
            for config in env['config_files_found']:
                printer.detail(f"• {config}")

        if env['warnings']:
            print("\n⚠️  Warnings:")
            for warning in env['warnings']:
                printer.detail(f"• {warning}")

    return 0 if env['valid'] else 1


def cmd_find_circular_deps(args, printer):
    """Find circular dependencies in JSON spec."""
    if not args.json:
        printer.action("Analyzing dependency graph...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    spec_data = load_json_spec(args.spec_id, specs_dir)
    if not spec_data:
        return 1

    circular = find_circular_deps(spec_data)

    if args.json:
        output = prepare_output(circular, args, FIND_CIRCULAR_DEPS_ESSENTIAL, FIND_CIRCULAR_DEPS_STANDARD)
        output_json(output, compact=getattr(args, 'compact', False))
    else:
        if circular['has_circular']:
            printer.error("Circular dependencies detected!")
            print(f"\nCircular Chains ({len(circular['circular_chains'])}):")
            for chain in circular['circular_chains']:
                printer.detail(f"• {' → '.join(chain)}")
        else:
            printer.success("No circular dependencies found")

        if circular['orphaned_tasks']:
            print(f"\n⚠️  Orphaned Tasks ({len(circular['orphaned_tasks'])}):")
            for orphan in circular['orphaned_tasks']:
                printer.detail(f"• {orphan['task']} depends on missing {orphan['missing_dependency']}")

        if circular['impossible_chains']:
            print(f"\n⚠️  Impossible Chains ({len(circular['impossible_chains'])}):")
            for chain in circular['impossible_chains']:
                printer.detail(f"• {chain['task']} blocked by {chain['blocked_by']} (also blocked)")

    return 1 if circular['has_circular'] else 0


def cmd_find_related_files(args, printer):
    """Find files related to a source file."""
    if not args.json:
        printer.action(f"Finding files related to {args.file}...")

    directory = Path(args.directory).resolve() if args.directory else None
    related = find_related_files(args.file, directory)

    if args.json:
        output = prepare_output(related, args, FIND_RELATED_FILES_ESSENTIAL, FIND_RELATED_FILES_STANDARD)
        output_json(output, compact=getattr(args, 'compact', False))
    else:
        printer.success("Related files found")
        printer.result("Source", related['source_file'])

        if related['test_files']:
            print("\nTest Files:")
            for test_file in related['test_files']:
                printer.detail(f"• {test_file}")

        if related['same_directory']:
            print(f"\nSame Directory ({len(related['same_directory'])} files):")
            for file in related['same_directory'][:10]:
                printer.detail(f"• {file}")
            if len(related['same_directory']) > 10:
                printer.detail(f"... and {len(related['same_directory']) - 10} more")

        if related['similar_files']:
            print(f"\nSimilar Files ({len(related['similar_files'])} files):")
            for file in related['similar_files'][:10]:
                printer.detail(f"• {file}")
            if len(related['similar_files']) > 10:
                printer.detail(f"... and {len(related['similar_files']) - 10} more")

    return 0


def cmd_validate_paths(args, printer):
    """Validate and normalize paths."""
    if not args.json:
        printer.action("Validating paths...")

    paths = args.paths
    base_dir = Path(args.base_directory).resolve() if args.base_directory else None
    validation = validate_paths(paths, base_dir)

    if args.json:
        output = prepare_output(validation, args, VALIDATE_PATHS_ESSENTIAL, VALIDATE_PATHS_STANDARD)
        output_json(output, compact=getattr(args, 'compact', False))
    else:
        if validation['valid_paths']:
            printer.success(f"Valid Paths ({len(validation['valid_paths'])})")
            for path in validation['valid_paths']:
                printer.detail(f"✓ {path['original']}")
                printer.detail(f"  → {path['normalized']} ({path['type']})", indent=2)

        if validation['invalid_paths']:
            print(f"\n✗ Invalid Paths ({len(validation['invalid_paths'])}):")
            for path in validation['invalid_paths']:
                printer.detail(f"✗ {path['original']}")
                printer.detail(f"  → {path['normalized']} (not found)", indent=2)

    return 0 if not validation['invalid_paths'] else 1


def cmd_spec_stats(args, printer):
    """Show spec file statistics."""
    if not args.json:
        printer.action("Gathering spec statistics...")

    spec_file = Path(args.spec_file).resolve()
    json_spec_file = Path(args.spec_file_json).resolve() if args.spec_file_json else None
    stats = spec_stats(spec_file, json_spec_file)

    if args.json:
        output = prepare_output(stats, args, SPEC_STATS_ESSENTIAL, SPEC_STATS_STANDARD)
        output_json(output, args.compact)
    else:
        if stats['exists']:
            printer.success("Spec file analyzed")
        else:
            printer.error("Spec file not found")

        printer.result("Spec File", stats['spec_file'])
        printer.result("Exists", 'Yes' if stats['exists'] else 'No')

        if stats['exists']:
            print("\nFile Statistics:")
            printer.detail(f"Size: {stats['file_size']} bytes")
            printer.detail(f"Lines: {stats['line_count']}")
            printer.detail(f"Phases: {stats['phase_count']}")
            printer.detail(f"Tasks: {stats['task_count']}")
            printer.detail(f"Verification Steps: {stats['verify_count']}")

            if stats['frontmatter'] and not 'error' in stats['frontmatter']:
                print("\nFrontmatter:")
                for key, value in stats['frontmatter'].items():
                    if len(str(value)) > 100:
                        printer.detail(f"{key}: {str(value)[:100]}...")
                    else:
                        printer.detail(f"{key}: {value}")

            if stats['state_info']:
                print("\nState Information:")
                printer.detail(f"Spec ID: {stats['state_info']['spec_id']}")
                printer.detail(f"Generated: {stats['state_info']['generated']}")
                printer.detail(f"Last Updated: {stats['state_info']['last_updated']}")

    return 0 if stats['exists'] else 1




def register_next(subparsers, parent_parser):
    """
    Register 'next' subcommands for unified CLI.
    """
    # verify-tools
    parser_verify = subparsers.add_parser('verify-tools', parents=[parent_parser], help='Verify required tools')
    parser_verify.set_defaults(func=cmd_verify_tools)

    # find-specs
    parser_find = subparsers.add_parser('find-specs', parents=[parent_parser], help='Find specs directory')
    parser_find.set_defaults(func=cmd_find_specs)

    # next-task
    parser_next = subparsers.add_parser('next-task', parents=[parent_parser], help='Find next actionable task')
    parser_next.add_argument('spec_id', help='Specification ID')
    parser_next.set_defaults(func=cmd_next_task)

    # task-info
    parser_info = subparsers.add_parser('task-info', parents=[parent_parser], help='Get task information')
    parser_info.add_argument('spec_id', help='Specification ID')
    parser_info.add_argument('task_id', help='Task ID')
    parser_info.set_defaults(func=cmd_task_info)

    # check-deps
    parser_deps = subparsers.add_parser('check-deps', parents=[parent_parser], help='Check task dependencies')
    parser_deps.add_argument('spec_id', help='Specification ID')
    parser_deps.add_argument('task_id', nargs='?', help='Task ID (optional, checks all tasks if not provided)')
    parser_deps.set_defaults(func=cmd_check_deps)

    # progress
    parser_progress = subparsers.add_parser('progress', parents=[parent_parser], help='Show overall progress')
    parser_progress.add_argument('spec_id', help='Specification ID')
    parser_progress.set_defaults(func=cmd_progress)


    # init-env
    parser_init_env = subparsers.add_parser('init-env', parents=[parent_parser], help='Initialize development environment')
    parser_init_env.add_argument('--spec-path', dest='spec_path', help='Optional path to spec file or directory')
    parser_init_env.add_argument('--export', action='store_true', help='Output as shell export statements')
    parser_init_env.set_defaults(func=cmd_init_env)

    # prepare-task
    parser_prepare = subparsers.add_parser('prepare-task', parents=[parent_parser], help='Prepare task for implementation')
    parser_prepare.add_argument('spec_id', help='Specification ID')
    parser_prepare.add_argument('task_id', nargs='?', help='Task ID (optional, finds next task if not provided)')
    parser_prepare.add_argument(
        '--include-full-journal',
        action='store_true',
        help='Add full previous-sibling journal entries to extended_context (default output only shows summaries)'
    )
    parser_prepare.add_argument(
        '--include-phase-history',
        action='store_true',
        help='Include all journal entries for tasks in the current phase (extended_context.phase_journal)'
    )
    parser_prepare.add_argument(
        '--include-spec-overview',
        action='store_true',
        help='Attach spec-wide progress snapshot (extended_context.spec_overview) for quick reporting'
    )
    parser_prepare.set_defaults(func=cmd_prepare_task)

    # format-plan
    parser_format_plan = subparsers.add_parser('format-plan', parents=[parent_parser], help='Format execution plan for display')
    parser_format_plan.add_argument('spec_id', help='Specification ID')
    parser_format_plan.add_argument('task_id', help='Task ID')
    parser_format_plan.set_defaults(func=cmd_format_plan)

    # validate-spec
    parser_validate = subparsers.add_parser('validate-spec', parents=[parent_parser], help='Validate spec file')
    parser_validate.add_argument('spec_file', help='Path to spec markdown file')
    parser_validate.set_defaults(func=cmd_validate_spec)

    # find-pattern
    parser_find_pattern = subparsers.add_parser('find-pattern', parents=[parent_parser], help='Find files matching a pattern')
    parser_find_pattern.add_argument('pattern', help='Glob pattern (e.g., "*.ts", "src/**/*.spec.ts")')
    parser_find_pattern.add_argument('--directory', help='Directory to search (defaults to current directory)')
    parser_find_pattern.set_defaults(func=cmd_find_pattern)

    # detect-project
    parser_detect_project = subparsers.add_parser('detect-project', parents=[parent_parser], help='Detect project type and dependencies')
    parser_detect_project.add_argument('--directory', help='Directory to analyze (defaults to current directory)')
    parser_detect_project.set_defaults(func=cmd_detect_project)

    # find-tests
    parser_find_tests = subparsers.add_parser('find-tests', parents=[parent_parser], help='Find test files and patterns')
    parser_find_tests.add_argument('--directory', help='Directory to search (defaults to current directory)')
    parser_find_tests.add_argument('--source-file', dest='source_file', help='Source file to find corresponding test')
    parser_find_tests.set_defaults(func=cmd_find_tests)

    # check-environment
    parser_check_env = subparsers.add_parser('check-environment', parents=[parent_parser], help='Check environmental requirements')
    parser_check_env.add_argument('--directory', help='Directory to check (defaults to current directory)')
    parser_check_env.add_argument('--required', help='Comma-separated list of required dependencies')
    parser_check_env.set_defaults(func=cmd_check_environment)

    # find-circular-deps
    parser_circular = subparsers.add_parser('find-circular-deps', parents=[parent_parser], help='Find circular dependencies in JSON spec')
    parser_circular.add_argument('spec_id', help='Specification ID')
    parser_circular.set_defaults(func=cmd_find_circular_deps)

    # find-related-files
    parser_related = subparsers.add_parser('find-related-files', parents=[parent_parser], help='Find files related to a source file')
    parser_related.add_argument('file', help='Source file path')
    parser_related.add_argument('--directory', help='Project directory (defaults to current directory)')
    parser_related.set_defaults(func=cmd_find_related_files)

    # validate-paths
    parser_validate_paths = subparsers.add_parser('validate-paths', parents=[parent_parser], help='Validate and normalize paths')
    parser_validate_paths.add_argument('paths', nargs='+', help='Paths to validate')
    parser_validate_paths.add_argument('--base-directory', dest='base_directory', help='Base directory for relative paths')
    parser_validate_paths.set_defaults(func=cmd_validate_paths)

    # spec-stats
    parser_spec_stats = subparsers.add_parser('spec-stats', parents=[parent_parser], help='Show spec file statistics')
    parser_spec_stats.add_argument('spec_file', help='Path to spec markdown file')
    parser_spec_stats.add_argument('--spec-file', dest='spec_file_json', help='Optional path to JSON spec')
    parser_spec_stats.set_defaults(func=cmd_spec_stats)
