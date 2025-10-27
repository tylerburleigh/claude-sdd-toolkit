#!/usr/bin/env python3
"""
SDD Update Tools - Progress tracking and documentation for spec-driven development.

Provides commands for updating task status, journaling decisions, tracking time,
and managing spec lifecycle.
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent directory to path for sdd_common imports

# Import shared utilities
from claude_skills.common import find_specs_directory, PrettyPrinter
from claude_skills.common import execute_verify_task, load_json_spec

# Import operations from scripts directory
from claude_skills.sdd_update.status import (
    update_task_status,
    mark_task_blocked,
    unblock_task,
)
from claude_skills.sdd_update.workflow import complete_task_workflow
from claude_skills.sdd_update.journal import (
    add_journal_entry,
    update_metadata,
    bulk_journal_tasks,
    sync_metadata_from_state,
    add_revision_entry,
)
from claude_skills.sdd_update.verification import add_verification_result, format_verification_summary
from claude_skills.sdd_update.lifecycle import move_spec, complete_spec
from claude_skills.sdd_update.time_tracking import track_time, generate_time_report
from claude_skills.sdd_update.validation import validate_spec, get_status_report, audit_spec, reconcile_state, detect_unjournaled_tasks
from claude_skills.sdd_update.query import (
    query_tasks,
    get_task,
    list_phases,
    check_complete,
    phase_time,
    list_blockers,
)


def cmd_execute_verify(args, printer):
    """Execute a verification task automatically (Priority 1 Integration)."""
    printer.action(f"Executing verification task {args.verify_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    # Load JSON spec file
    spec_data = load_json_spec(args.spec_id, specs_dir)
    if not spec_data:
        printer.error(f"Could not load JSON spec file for {args.spec_id}")
        return 1

    # Show on_failure configuration before execution
    hierarchy = spec_data.get("hierarchy", {})
    if args.verify_id in hierarchy:
        verify_task = hierarchy[args.verify_id]
        on_failure = verify_task.get("metadata", {}).get("on_failure")
        if on_failure:
            printer.info("on_failure configuration:")
            if on_failure.get("revert_status"):
                printer.info(f"  • Revert to: {on_failure['revert_status']}")
            if on_failure.get("max_retries", 0) > 0:
                printer.info(f"  • Max retries: {on_failure['max_retries']}")
            if on_failure.get("consult"):
                printer.info("  • AI consultation: enabled")
            if on_failure.get("continue_on_failure"):
                printer.info("  • Continue on failure: enabled")
            if on_failure.get("notify") and on_failure["notify"] != "none":
                printer.info(f"  • Notification: {on_failure['notify']}")
            printer.info("")  # Blank line for spacing

    # Execute the verification task
    result = execute_verify_task(spec_data, args.verify_id, spec_root=str(specs_dir))

    # Display results
    if result["success"]:
        printer.success(f"Verification {args.verify_id} PASSED")
        if result.get("retry_count", 0) > 0:
            printer.info(f"Succeeded after {result['retry_count']} retry attempt(s)")
        if result["output"]:
            printer.detail(f"Output:\n{result['output'][:500]}")
        if result["skill_used"]:
            printer.info(f"Executed using skill: {result['skill_used']}")
        printer.info(f"Duration: {result['duration']:.2f}s")

        # Show actions taken if any
        if result.get("actions_taken"):
            printer.info(f"Actions: {', '.join(result['actions_taken'])}")

        # Automatically record the result if --record flag is set
        if args.record:
            from claude_skills.sdd_update.verification import add_verification_result
            add_verification_result(
                spec_id=args.spec_id,
                verify_id=args.verify_id,
                status="PASSED",
                command=result.get("skill_used") or "automated execution",
                output=result["output"][:500] if result["output"] else None,
                specs_dir=specs_dir,
                printer=printer
            )

        return 0
    else:
        printer.error(f"Verification {args.verify_id} FAILED")
        if result["errors"]:
            printer.error("Errors:")
            for error in result["errors"]:
                printer.error(f"  - {error}")
        if result["output"]:
            printer.detail(f"Output:\n{result['output'][:500]}")
        if result.get("retry_count", 0) > 0:
            printer.warning(f"Failed after {result['retry_count']} retry attempt(s)")

        # Show actions taken if any
        if result.get("actions_taken"):
            printer.info(f"Actions taken: {', '.join(result['actions_taken'])}")

        # Show on_failure recommendations
        if result.get("on_failure"):
            on_failure = result["on_failure"]
            printer.info("\nFailure handling:")
            if on_failure.get("consult"):
                printer.info("💡 AI consultation recommended - consider using run-tests skill")
            if on_failure.get("revert_status"):
                printer.info(f"🔄 Task will revert to: {on_failure['revert_status']}")

        # Auto-record failure if --record flag is set
        if args.record:
            from claude_skills.sdd_update.verification import add_verification_result
            add_verification_result(
                spec_id=args.spec_id,
                verify_id=args.verify_id,
                status="FAILED",
                command=result.get("skill_used") or "automated execution",
                output=result["output"][:500] if result["output"] else None,
                issues="\n".join(result["errors"]),
                specs_dir=specs_dir,
                printer=printer
            )

        return 1


def cmd_update_status(args, printer):
    """Update task status."""
    printer.action(f"Updating status for {args.task_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    success = update_task_status(
        spec_id=args.spec_id,
        task_id=args.task_id,
        new_status=args.status,
        specs_dir=specs_dir,
        note=args.note,
        dry_run=args.dry_run,
        verify=args.verify if hasattr(args, 'verify') else False,
        printer=printer
    )

    return 0 if success else 1


def cmd_mark_blocked(args, printer):
    """Mark task as blocked."""
    printer.action(f"Marking task {args.task_id} as blocked...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    success = mark_task_blocked(
        spec_id=args.spec_id,
        task_id=args.task_id,
        reason=args.reason,
        specs_dir=specs_dir,
        blocker_type=args.type,
        ticket=args.ticket,
        dry_run=args.dry_run,
        printer=printer
    )

    return 0 if success else 1


def cmd_unblock_task(args, printer):
    """Unblock a task."""
    printer.action(f"Unblocking task {args.task_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    success = unblock_task(
        spec_id=args.spec_id,
        task_id=args.task_id,
        resolution=args.resolution,
        specs_dir=specs_dir,
        dry_run=args.dry_run,
        printer=printer
    )

    return 0 if success else 1


def cmd_add_journal(args, printer):
    """Add journal entry."""
    printer.action("Adding journal entry...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    success = add_journal_entry(
        spec_id=args.spec_id,
        title=args.title,
        content=args.content,
        task_id=args.task_id,
        entry_type=args.entry_type,
        author=args.author,
        specs_dir=specs_dir,
        dry_run=args.dry_run,
        printer=printer
    )

    return 0 if success else 1


def cmd_add_revision(args, printer):
    """Add revision entry."""
    printer.action("Adding revision entry...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    success = add_revision_entry(
        spec_id=args.spec_id,
        version=args.version,
        changes=args.changes,
        author=args.author,
        specs_dir=specs_dir,
        dry_run=args.dry_run,
        printer=printer,
    )

    return 0 if success else 1


def cmd_update_frontmatter(args, printer):
    """Update metadata field in JSON spec."""
    printer.action(f"Updating metadata field '{args.key}'...")

    spec_file = Path(args.spec_file).resolve()

    # Extract spec_id from file path (remove .json or .md extension)
    spec_id = spec_file.stem

    # Get specs directory (parent of spec file)
    specs_dir = spec_file.parent

    success = update_metadata(
        spec_id=spec_id,
        key=args.key,
        value=args.value,
        specs_dir=specs_dir,
        dry_run=args.dry_run,
        printer=printer
    )

    return 0 if success else 1


def cmd_add_verification(args, printer):
    """Add verification result."""
    printer.action(f"Recording verification result for {args.verify_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    success = add_verification_result(
        spec_id=args.spec_id,
        verify_id=args.verify_id,
        status=args.status,
        command=args.command,
        output=args.output,
        issues=args.issues,
        notes=args.notes,
        specs_dir=specs_dir,
        dry_run=args.dry_run,
        printer=printer
    )

    return 0 if success else 1


def cmd_format_verification_summary(args, printer):
    """Format verification results summary."""
    # Read JSON input
    if args.json_file:
        try:
            with open(args.json_file, 'r') as f:
                verification_results = json.load(f)
        except Exception as e:
            printer.error(f"Failed to read JSON file: {e}")
            return 1
    elif args.json_input:
        try:
            verification_results = json.loads(args.json_input)
        except Exception as e:
            printer.error(f"Failed to parse JSON input: {e}")
            return 1
    else:
        printer.error("Must provide either --json-file or --json-input")
        return 1

    # Validate input
    if not isinstance(verification_results, list):
        printer.error("JSON input must be a list of verification results")
        return 1

    # Format the summary
    formatted = format_verification_summary(verification_results)

    # Print the formatted summary
    print(formatted)
    return 0


def cmd_move_spec(args, printer):
    """Move spec to another folder."""
    printer.action(f"Moving spec to {args.target}...")

    spec_file = Path(args.spec_file).resolve()

    success = move_spec(
        spec_file=spec_file,
        target_folder=args.target,
        dry_run=args.dry_run,
        printer=printer
    )

    return 0 if success else 1


def cmd_complete_spec(args, printer):
    """Mark spec as completed and move to completed folder."""
    printer.action(f"Completing spec {args.spec_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    spec_file = Path(args.spec_file).resolve()

    success = complete_spec(
        spec_id=args.spec_id,
        spec_file=spec_file,
        specs_dir=specs_dir,
        actual_hours=args.actual_hours,
        dry_run=args.dry_run,
        printer=printer
    )

    return 0 if success else 1


def cmd_track_time(args, printer):
    """Track time spent on task."""
    printer.action(f"Recording time for task {args.task_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    success = track_time(
        spec_id=args.spec_id,
        task_id=args.task_id,
        actual_hours=args.actual,
        specs_dir=specs_dir,
        dry_run=args.dry_run,
        printer=printer
    )

    return 0 if success else 1


def cmd_time_report(args, printer):
    """Generate time tracking report."""
    if not args.json:
        printer.action("Generating time report...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    report = generate_time_report(
        spec_id=args.spec_id,
        specs_dir=specs_dir,
        printer=printer if not args.json else None
    )

    if args.json and report:
        print(json.dumps(report, indent=2))

    return 0 if report else 1




def cmd_status_report(args, printer):
    """Get status report."""
    if not args.json:
        printer.action(f"Generating status report for {args.spec_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    report = get_status_report(
        spec_id=args.spec_id,
        specs_dir=specs_dir,
        printer=printer if not args.json else None
    )

    if args.json and report:
        print(json.dumps(report, indent=2))

    return 0 if report else 1


def cmd_audit_spec(args, printer):
    """Perform deep audit of JSON spec."""
    if not args.json:
        printer.action(f"Auditing JSON spec for {args.spec_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    result = audit_spec(
        spec_id=args.spec_id,
        specs_dir=specs_dir,
        printer=printer if not args.json else None
    )

    if args.json:
        print(json.dumps(result, indent=2))

    return 0 if result.get("validation_passed", False) else 1


def cmd_query_tasks(args, printer):
    """Query and filter tasks."""
    if not args.json and args.format != "simple":
        printer.action("Querying tasks...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    # For simple format or JSON, don't pass printer (we'll handle output ourselves)
    use_printer = not args.json and args.format != "simple"

    results = query_tasks(
        spec_id=args.spec_id,
        specs_dir=specs_dir,
        status=args.status,
        task_type=args.type,
        parent=args.parent,
        format_type=args.format,
        printer=printer if use_printer else None,
        limit=args.limit
    )

    # Handle output for simple format
    if args.format == "simple" and results:
        for task in results:
            print(task["id"])
    elif args.json and results:
        print(json.dumps(results, indent=2))

    return 0 if results is not None else 1


def cmd_get_task(args, printer):
    """Get detailed task information."""
    if not args.json:
        printer.action(f"Retrieving task {args.task_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    task = get_task(
        spec_id=args.spec_id,
        task_id=args.task_id,
        specs_dir=specs_dir,
        printer=printer if not args.json else None,
        include_journal=getattr(args, 'include_journal', False)
    )

    if args.json and task:
        print(json.dumps(task, indent=2))

    return 0 if task else 1


def cmd_get_journal(args, printer):
    """Get journal entries for a spec or task."""
    if not args.json:
        if args.task_id:
            printer.action(f"Retrieving journal entries for task {args.task_id}...")
        else:
            printer.action(f"Retrieving journal entries for {args.spec_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    # Import the function here to avoid circular imports
    from claude_skills.common.query_operations import get_journal_entries

    entries = get_journal_entries(
        spec_id=args.spec_id,
        specs_dir=specs_dir,
        task_id=getattr(args, 'task_id', None),
        printer=printer if not args.json else None
    )

    if args.json and entries is not None:
        print(json.dumps(entries, indent=2))

    return 0 if entries is not None else 1


def cmd_list_phases(args, printer):
    """List all phases."""
    if not args.json:
        printer.action("Listing phases...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    phases = list_phases(
        spec_id=args.spec_id,
        specs_dir=specs_dir,
        printer=printer if not args.json else None
    )

    if args.json and phases:
        print(json.dumps(phases, indent=2))

    return 0 if phases is not None else 1


def cmd_check_complete(args, printer):
    """Check if spec, phase, or task is ready to complete."""
    if not args.json:
        printer.action("Checking completion status...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    result = check_complete(
        spec_id=args.spec_id,
        specs_dir=specs_dir,
        phase_id=getattr(args, 'phase', None),
        task_id=getattr(args, 'task', None),
        printer=printer if not args.json else None
    )

    if args.json:
        print(json.dumps(result, indent=2))

    return 0 if result.get("is_complete", False) else 1


def cmd_phase_time(args, printer):
    """Calculate time for a phase."""
    if not args.json:
        printer.action(f"Calculating time for phase {args.phase_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    result = phase_time(
        spec_id=args.spec_id,
        phase_id=args.phase_id,
        specs_dir=specs_dir,
        printer=printer if not args.json else None
    )

    if args.json and result:
        print(json.dumps(result, indent=2))

    return 0 if result else 1


def cmd_list_blockers(args, printer):
    """List all blocked tasks."""
    if not args.json:
        printer.action("Finding blocked tasks...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    blockers = list_blockers(
        spec_id=args.spec_id,
        specs_dir=specs_dir,
        printer=printer if not args.json else None
    )

    if args.json and blockers:
        print(json.dumps(blockers, indent=2))

    return 0 if blockers is not None else 1


def cmd_reconcile_state(args, printer):
    """Reconcile JSON spec to fix inconsistent task statuses."""
    printer.action(f"Reconciling state for {args.spec_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    success = reconcile_state(
        spec_id=args.spec_id,
        specs_dir=specs_dir,
        dry_run=args.dry_run,
        printer=printer
    )

    return 0 if success else 1


def cmd_check_journaling(args, printer):
    """Check for unjournaled completed tasks."""
    if not args.json:
        printer.action(f"Checking for unjournaled tasks in {args.spec_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    unjournaled = detect_unjournaled_tasks(
        spec_id=args.spec_id,
        specs_dir=specs_dir,
        printer=printer if not args.json else None
    )

    if unjournaled is None:
        return 1

    if args.json:
        print(json.dumps(unjournaled, indent=2))
        return 0

    if not unjournaled:
        printer.success("All completed tasks have been journaled!")
        return 0

    # Display unjournaled tasks
    printer.warning(f"Found {len(unjournaled)} completed task(s) without journal entries:\n")
    for i, task in enumerate(unjournaled, 1):
        printer.info(f"{i}. {task['task_id']}: {task['title']}")
        printer.detail(f"   Completed: {task['completed_at']}")

    printer.info(f"\nTo journal these tasks, run:")
    printer.info(f"  bulk-journal {args.spec_id} <spec-file>")

    return 1  # Exit with error code to indicate action needed


def cmd_bulk_journal(args, printer):
    """Bulk journal completed tasks."""
    printer.action("Bulk journaling tasks...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    # Parse task_ids if provided
    task_ids = None
    if args.tasks:
        task_ids = [t.strip() for t in args.tasks.split(',')]

    success = bulk_journal_tasks(
        spec_id=args.spec_id,
        specs_dir=specs_dir,
        task_ids=task_ids,
        dry_run=args.dry_run,
        printer=printer,
        template=args.template,
        template_metadata={"author": args.template_author} if args.template_author else None,
    )

    return 0 if success else 1


def cmd_complete_task(args, printer):
    """Complete task workflow (status, journaling, metadata sync)."""
    printer.action(f"Completing task {args.task_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    success = complete_task_workflow(
        spec_id=args.spec_id,
        task_id=args.task_id,
        specs_dir=specs_dir,
        actual_hours=args.actual_hours,
        note=args.note,
        journal_title=args.journal_title,
        journal_content=args.journal_content,
        journal_entry_type=args.entry_type,
        author=args.author,
        bump=args.bump,
        version=args.version,
        dry_run=args.dry_run,
        printer=printer,
        show_diff=args.dry_run or args.show_diff,
        output_format="json" if args.json else "text",
    )

    if args.json and success:
        print(json.dumps(success, indent=2))
        return 0

    return 0 if success else 1


def cmd_sync_metadata(args, printer):
    """Synchronize spec metadata with hierarchy data."""
    printer.action("Synchronizing metadata from hierarchy...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    success = sync_metadata_from_state(
        spec_id=args.spec_id,
        specs_dir=specs_dir,
        dry_run=args.dry_run,
        printer=printer
    )

    return 0 if success else 1


def register_update(subparsers, parent_parser):
    """
    Register 'update' subcommands for unified CLI.

    Args:
        subparsers: The subparsers object to add commands to
        parent_parser: Parent parser with global options (--json, --quiet, --verbose, etc.)
    """
    # update-status command
    p_update = subparsers.add_parser("update-status", help="Update task status", parents=[parent_parser])
    p_update.add_argument("spec_id", help="Specification ID")
    p_update.add_argument("task_id", help="Task ID")
    p_update.add_argument("status", choices=["pending", "in_progress", "completed", "blocked"])
    p_update.add_argument("--note", help="Optional note about status change")
    p_update.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    p_update.add_argument("--verify", action="store_true", help="Run associated verify tasks after marking as completed")
    p_update.set_defaults(func=cmd_update_status)

    # mark-blocked command
    p_blocked = subparsers.add_parser("mark-blocked", help="Mark task as blocked", parents=[parent_parser])
    p_blocked.add_argument("spec_id", help="Specification ID")
    p_blocked.add_argument("task_id", help="Task ID")
    p_blocked.add_argument("--reason", required=True, help="Description of blocker")
    p_blocked.add_argument("--type", default="dependency", choices=["dependency", "technical", "resource", "decision"], help="Blocker type")
    p_blocked.add_argument("--ticket", help="Related ticket/issue number")
    p_blocked.add_argument("--dry-run", action="store_true", help="Preview changes")
    p_blocked.set_defaults(func=cmd_mark_blocked)

    # unblock-task command
    p_unblock = subparsers.add_parser("unblock-task", help="Unblock a task", parents=[parent_parser])
    p_unblock.add_argument("spec_id", help="Specification ID")
    p_unblock.add_argument("task_id", help="Task ID")
    p_unblock.add_argument("--resolution", help="How the blocker was resolved")
    p_unblock.add_argument("--dry-run", action="store_true", help="Preview changes")
    p_unblock.set_defaults(func=cmd_unblock_task)

    # add-journal command
    p_journal = subparsers.add_parser("add-journal", help="Add journal entry", parents=[parent_parser])
    p_journal.add_argument("spec_id", help="Specification ID")
    p_journal.add_argument("--title", required=True, help="Entry title")
    p_journal.add_argument("--content", required=True, help="Entry content")
    p_journal.add_argument("--task-id", help="Related task ID")
    p_journal.add_argument("--entry-type", default="note", choices=["status_change", "deviation", "blocker", "decision", "note"], help="Entry type")
    p_journal.add_argument("--author", default="claude-code", help="Author of the entry")
    p_journal.add_argument("--dry-run", action="store_true", help="Preview entry")
    p_journal.set_defaults(func=cmd_add_journal)

    # update-frontmatter command
    p_front = subparsers.add_parser("update-frontmatter", help="Update spec frontmatter", parents=[parent_parser])
    p_front.add_argument("spec_file", help="Path to spec file")
    p_front.add_argument("key", help="Frontmatter key")
    p_front.add_argument("value", help="New value")
    p_front.add_argument("--dry-run", action="store_true", help="Preview change")
    p_front.set_defaults(func=cmd_update_frontmatter)

    # add-verification command
    p_verify = subparsers.add_parser("add-verification", help="Add verification result", parents=[parent_parser])
    p_verify.add_argument("spec_id", help="Specification ID")
    p_verify.add_argument("verify_id", help="Verification ID (e.g., verify-1-1)")
    p_verify.add_argument("status", choices=["PASSED", "FAILED", "PARTIAL"])
    p_verify.add_argument("--command", help="Command that was run")
    p_verify.add_argument("--output", help="Command output or test results")
    p_verify.add_argument("--issues", help="Issues found")
    p_verify.add_argument("--notes", help="Additional notes")
    p_verify.add_argument("--dry-run", action="store_true", help="Preview result")
    p_verify.set_defaults(func=cmd_add_verification)

    # execute-verify command (Priority 1 Integration)
    p_exec_verify = subparsers.add_parser("execute-verify", help="Execute verification task automatically", parents=[parent_parser])
    p_exec_verify.add_argument("spec_id", help="Specification ID")
    p_exec_verify.add_argument("verify_id", help="Verification ID (e.g., verify-1-1)")
    p_exec_verify.add_argument("--record", action="store_true", help="Automatically record result to spec")
    p_exec_verify.set_defaults(func=cmd_execute_verify)

    # format-verification-summary command
    p_verify_summary = subparsers.add_parser("format-verification-summary", help="Format verification results summary", parents=[parent_parser])
    group = p_verify_summary.add_mutually_exclusive_group(required=True)
    group.add_argument("--json-file", help="Path to JSON file with verification results")
    group.add_argument("--json-input", help="JSON string with verification results")
    p_verify_summary.set_defaults(func=cmd_format_verification_summary)

    # move-spec command
    p_move = subparsers.add_parser("move-spec", help="Move spec to another folder", parents=[parent_parser])
    p_move.add_argument("spec_file", help="Path to spec file")
    p_move.add_argument("target", choices=["active", "completed", "archived"])
    p_move.add_argument("--dry-run", action="store_true", help="Preview move")
    p_move.set_defaults(func=cmd_move_spec)

    # complete-spec command
    p_complete = subparsers.add_parser("complete-spec", help="Mark spec as completed", parents=[parent_parser])
    p_complete.add_argument("spec_id", help="Specification ID")
    p_complete.add_argument("spec_file", help="Path to spec file")
    p_complete.add_argument("--actual-hours", type=float, help="Actual hours spent")
    p_complete.add_argument("--dry-run", action="store_true", help="Preview changes")
    p_complete.set_defaults(func=cmd_complete_spec)

    # track-time command
    p_time = subparsers.add_parser("track-time", help="Track time spent on task", parents=[parent_parser])
    p_time.add_argument("spec_id", help="Specification ID")
    p_time.add_argument("task_id", help="Task ID")
    p_time.add_argument("--actual", type=float, required=True, help="Actual hours spent")
    p_time.add_argument("--dry-run", action="store_true", help="Preview change")
    p_time.set_defaults(func=cmd_track_time)

    # time-report command
    p_report = subparsers.add_parser("time-report", help="Generate time tracking report", parents=[parent_parser])
    p_report.add_argument("spec_id", help="Specification ID")
    p_report.set_defaults(func=cmd_time_report)


    # status-report command
    p_status = subparsers.add_parser("status-report", help="Get status report", parents=[parent_parser])
    p_status.add_argument("spec_id", help="Specification ID")
    p_status.set_defaults(func=cmd_status_report)

    # audit-spec command
    p_audit = subparsers.add_parser("audit-spec", help="Deep audit of JSON spec", parents=[parent_parser])
    p_audit.add_argument("spec_id", help="Specification ID")
    p_audit.set_defaults(func=cmd_audit_spec)

    # query-tasks command
    p_query = subparsers.add_parser("query-tasks", help="Query and filter tasks", parents=[parent_parser])
    p_query.add_argument("spec_id", help="Specification ID")
    p_query.add_argument("--status", choices=["pending", "in_progress", "completed", "blocked"], help="Filter by status")
    p_query.add_argument("--type", choices=["task", "verify", "group", "phase", "spec"], help="Filter by type")
    p_query.add_argument("--parent", help="Filter by parent node ID")
    p_query.add_argument("--format", default="table", choices=["table", "json", "simple"], help="Output format")
    p_query.add_argument("--limit", type=int, default=20, help="Maximum number of results to return (use 0 for unlimited, default: 20)")
    p_query.set_defaults(func=cmd_query_tasks)

    # get-task command
    p_get_task = subparsers.add_parser("get-task", help="Get detailed task information", parents=[parent_parser])
    p_get_task.add_argument("spec_id", help="Specification ID")
    p_get_task.add_argument("task_id", help="Task ID to retrieve")
    p_get_task.add_argument("--include-journal", action="store_true", help="Include journal entries for this task")
    p_get_task.set_defaults(func=cmd_get_task)

    # get-journal command
    p_get_journal = subparsers.add_parser("get-journal", help="Get journal entries", parents=[parent_parser])
    p_get_journal.add_argument("spec_id", help="Specification ID")
    p_get_journal.add_argument("--task-id", help="Filter by task ID")
    p_get_journal.set_defaults(func=cmd_get_journal)

    # list-phases command
    p_phases = subparsers.add_parser("list-phases", help="List all phases with progress", parents=[parent_parser])
    p_phases.add_argument("spec_id", help="Specification ID")
    p_phases.set_defaults(func=cmd_list_phases)

    # check-complete command
    p_check = subparsers.add_parser("check-complete", help="Check if spec/phase/task is ready to complete", parents=[parent_parser])
    p_check.add_argument("spec_id", help="Specification ID")
    check_group = p_check.add_mutually_exclusive_group()
    check_group.add_argument("--phase", help="Optional phase ID to check")
    check_group.add_argument("--task", help="Optional task ID to check")
    p_check.set_defaults(func=cmd_check_complete)

    # phase-time command
    p_phasetime = subparsers.add_parser("phase-time", help="Calculate time breakdown for a phase", parents=[parent_parser])
    p_phasetime.add_argument("spec_id", help="Specification ID")
    p_phasetime.add_argument("phase_id", help="Phase ID")
    p_phasetime.set_defaults(func=cmd_phase_time)

    # list-blockers command
    p_blockers = subparsers.add_parser("list-blockers", help="List all blocked tasks", parents=[parent_parser])
    p_blockers.add_argument("spec_id", help="Specification ID")
    p_blockers.set_defaults(func=cmd_list_blockers)

    # reconcile-state command
    p_reconcile = subparsers.add_parser("reconcile-state", help="Reconcile JSON spec inconsistencies", parents=[parent_parser])
    p_reconcile.add_argument("spec_id", help="Specification ID")
    p_reconcile.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    p_reconcile.set_defaults(func=cmd_reconcile_state)

    # check-journaling command
    p_check_journal = subparsers.add_parser("check-journaling", help="Check for unjournaled completed tasks", parents=[parent_parser])
    p_check_journal.add_argument("spec_id", help="Specification ID")
    p_check_journal.set_defaults(func=cmd_check_journaling)

    # add-revision command
    p_revision = subparsers.add_parser("add-revision", help="Add revision metadata entry", parents=[parent_parser])
    p_revision.add_argument("spec_id", help="Specification ID")
    p_revision.add_argument("version", help="Revision version (e.g., 1.1, 2.0)")
    p_revision.add_argument("changes", help="Summary of changes")
    p_revision.add_argument("--author", default="claude-code", help="Revision author")
    p_revision.add_argument("--dry-run", action="store_true", help="Preview revision without saving")
    p_revision.set_defaults(func=cmd_add_revision)

    # bulk-journal command
    p_bulk_journal = subparsers.add_parser("bulk-journal", help="Bulk journal completed tasks", parents=[parent_parser])
    p_bulk_journal.add_argument("spec_id", help="Specification ID")
    p_bulk_journal.add_argument("--tasks", help="Comma-separated list of task IDs (if omitted, journals all unjournaled tasks)")
    p_bulk_journal.add_argument("--template", choices=["completion", "decision", "blocker"], help="Apply a journal template")
    p_bulk_journal.add_argument("--template-author", help="Override author for templated entries")
    p_bulk_journal.add_argument("--dry-run", action="store_true", help="Preview journal entries without saving")
    p_bulk_journal.set_defaults(func=cmd_bulk_journal)

    # complete-task command
    p_complete_task = subparsers.add_parser(
        "complete-task",
        help="Complete task with optional journaling and metadata updates",
        parents=[parent_parser],
    )
    p_complete_task.add_argument("spec_id", help="Specification ID")
    p_complete_task.add_argument("task_id", help="Task ID to complete")
    p_complete_task.add_argument("--actual-hours", type=float, help="Actual hours spent")
    p_complete_task.add_argument("--note", help="Status note")
    p_complete_task.add_argument("--author", default="claude-code", help="Journal author")
    p_complete_task.add_argument("--journal-title", help="Journal entry title")
    p_complete_task.add_argument("--journal-content", help="Journal entry content")
    p_complete_task.add_argument(
        "--entry-type",
        default="status_change",
        choices=["status_change", "deviation", "blocker", "decision", "note"],
        help="Journal entry type",
    )
    p_complete_task.add_argument(
        "--bump",
        choices=["major", "minor"],
        help="Automatically bump revision version (requires existing version)",
    )
    p_complete_task.add_argument("--version", help="Explicit version to set")
    p_complete_task.add_argument("--show-diff", action="store_true", help="Show diff of metadata changes")
    p_complete_task.add_argument("--dry-run", action="store_true", help="Preview workflow without saving")
    p_complete_task.set_defaults(func=cmd_complete_task)

    # sync-metadata command
    p_sync_meta = subparsers.add_parser("sync-metadata", help="Synchronize spec metadata with hierarchy data", parents=[parent_parser])
    p_sync_meta.add_argument("spec_id", help="Specification ID")
    p_sync_meta.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    p_sync_meta.set_defaults(func=cmd_sync_metadata)
