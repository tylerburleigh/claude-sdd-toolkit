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
from datetime import datetime, timezone

# Add parent directory to path for sdd_common imports

# Import shared utilities
from claude_skills.common import find_specs_directory, find_spec_file, PrettyPrinter
from claude_skills.common import execute_verify_task, load_json_spec
from claude_skills.common.spec import update_node, save_json_spec
from claude_skills.common.sdd_config import get_default_format
from claude_skills.common.json_output import output_json
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    ADD_ASSUMPTION_ESSENTIAL,
    ADD_ASSUMPTION_STANDARD,
    LIST_ASSUMPTIONS_ESSENTIAL,
    LIST_ASSUMPTIONS_STANDARD,
    UPDATE_ESTIMATE_ESSENTIAL,
    UPDATE_ESTIMATE_STANDARD,
    ADD_TASK_ESSENTIAL,
    ADD_TASK_STANDARD,
    REMOVE_TASK_ESSENTIAL,
    REMOVE_TASK_STANDARD,
    TIME_REPORT_ESSENTIAL,
    TIME_REPORT_STANDARD,
    STATUS_REPORT_ESSENTIAL,
    STATUS_REPORT_STANDARD,
    AUDIT_SPEC_ESSENTIAL,
    AUDIT_SPEC_STANDARD,
    GET_TASK_ESSENTIAL,
    GET_TASK_STANDARD,
    GET_JOURNAL_ESSENTIAL,
    GET_JOURNAL_STANDARD,
    LIST_PHASES_ESSENTIAL,
    LIST_PHASES_STANDARD,
    CHECK_COMPLETE_ESSENTIAL,
    CHECK_COMPLETE_STANDARD,
    PHASE_TIME_ESSENTIAL,
    PHASE_TIME_STANDARD,
    RECONCILE_STATE_ESSENTIAL,
    RECONCILE_STATE_STANDARD,
    CHECK_JOURNALING_ESSENTIAL,
    CHECK_JOURNALING_STANDARD,
    COMPLETE_TASK_ESSENTIAL,
    COMPLETE_TASK_STANDARD,
    CREATE_TASK_COMMIT_ESSENTIAL,
    CREATE_TASK_COMMIT_STANDARD,
    UPDATE_STATUS_ESSENTIAL,
    UPDATE_STATUS_STANDARD,
    MARK_BLOCKED_ESSENTIAL,
    MARK_BLOCKED_STANDARD,
    UNBLOCK_TASK_ESSENTIAL,
    UNBLOCK_TASK_STANDARD,
    ADD_JOURNAL_ESSENTIAL,
    ADD_JOURNAL_STANDARD,
    ADD_REVISION_ESSENTIAL,
    ADD_REVISION_STANDARD,
    UPDATE_FRONTMATTER_ESSENTIAL,
    UPDATE_FRONTMATTER_STANDARD,
    ADD_VERIFICATION_ESSENTIAL,
    ADD_VERIFICATION_STANDARD,
    EXECUTE_VERIFY_ESSENTIAL,
    EXECUTE_VERIFY_STANDARD,
    FORMAT_VERIFICATION_SUMMARY_ESSENTIAL,
    FORMAT_VERIFICATION_SUMMARY_STANDARD,
    MOVE_SPEC_ESSENTIAL,
    MOVE_SPEC_STANDARD,
    ACTIVATE_SPEC_ESSENTIAL,
    ACTIVATE_SPEC_STANDARD,
    COMPLETE_SPEC_ESSENTIAL,
    COMPLETE_SPEC_STANDARD,
    BULK_JOURNAL_ESSENTIAL,
    BULK_JOURNAL_STANDARD,
    SYNC_METADATA_ESSENTIAL,
    SYNC_METADATA_STANDARD,
    UPDATE_TASK_METADATA_ESSENTIAL,
    UPDATE_TASK_METADATA_STANDARD,
)
from claude_skills.cli.sdd.verbosity import VerbosityLevel

# Import operations from scripts directory
from claude_skills.sdd_update.status import (
    update_task_status,
    mark_task_blocked,
    unblock_task,
)
from claude_skills.sdd_update.workflow import complete_task_workflow
from claude_skills.sdd_update.list_specs import list_specs
from claude_skills.sdd_update.journal import (
    add_journal_entry,
    update_metadata,
    bulk_journal_tasks,
    sync_metadata_from_state,
    add_revision_entry,
)
from claude_skills.sdd_update.verification import add_verification_result, format_verification_summary
from claude_skills.sdd_update.lifecycle import move_spec, move_spec_by_id, complete_spec, activate_spec
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
from claude_skills.sdd_update.query_tasks import format_tasks_table
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    QUERY_TASKS_ESSENTIAL,
    QUERY_TASKS_STANDARD,
    LIST_BLOCKERS_ESSENTIAL,
    LIST_BLOCKERS_STANDARD,
)
from claude_skills.sdd_update.list_phases import format_phases_table
from claude_skills.sdd_spec_mod.assumptions import add_assumption, list_assumptions
from claude_skills.sdd_spec_mod.estimates import update_task_estimate
from claude_skills.sdd_spec_mod.task_operations import add_task, remove_task


def _emit_json_output(data, args, essential_fields=None, standard_fields=None):
    """
    Helper to emit JSON respecting compact flag and verbosity filtering.
    """
    if not getattr(args, 'json', False):
        return

    payload = data
    if essential_fields or standard_fields:
        payload = prepare_output(
            data,
            args,
            essential_fields,
            standard_fields,
        )

    output_json(payload, getattr(args, 'compact', False))


def cmd_execute_verify(args, printer):
    """Execute a verification task automatically (Priority 1 Integration)."""
    use_json = getattr(args, 'json', False)

    if not use_json:
        printer.action(f"Executing verification task {args.verify_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        if not use_json:
            printer.error("Specs directory not found")
        return 1

    # Load JSON spec file
    spec_data = load_json_spec(args.spec_id, specs_dir)
    if not spec_data:
        if not use_json:
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
        if not use_json:
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
                printer=printer if not use_json else None
            )

        if use_json:
            json_result = {
                'success': True,
                'task_id': args.verify_id,
                'result': 'PASSED',
                'spec_id': args.spec_id,
                'verification_type': 'auto',
                'executed_at': datetime.now(timezone.utc).isoformat(),
                'details': {
                    'output': result["output"][:500] if result["output"] else None,
                    'skill_used': result.get("skill_used"),
                    'duration': result['duration'],
                    'retry_count': result.get("retry_count", 0),
                    'actions_taken': result.get("actions_taken", [])
                }
            }
            output = prepare_output(json_result, args, EXECUTE_VERIFY_ESSENTIAL, EXECUTE_VERIFY_STANDARD)
            output_json(output, args.compact)

        return 0
    else:
        if not use_json:
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
                printer=printer if not use_json else None
            )

        if use_json:
            json_result = {
                'success': False,
                'task_id': args.verify_id,
                'result': 'FAILED',
                'spec_id': args.spec_id,
                'verification_type': 'auto',
                'executed_at': datetime.now(timezone.utc).isoformat(),
                'details': {
                    'errors': result["errors"],
                    'output': result["output"][:500] if result["output"] else None,
                    'skill_used': result.get("skill_used"),
                    'duration': result.get('duration'),
                    'retry_count': result.get("retry_count", 0),
                    'actions_taken': result.get("actions_taken", []),
                    'on_failure': result.get("on_failure")
                }
            }
            output = prepare_output(json_result, args, EXECUTE_VERIFY_ESSENTIAL, EXECUTE_VERIFY_STANDARD)
            output_json(output, args.compact)

        return 1


def cmd_update_status(args, printer):
    """Update task status."""
    use_json = getattr(args, 'json', False)

    if not use_json:
        printer.action(f"Updating status for {args.task_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        if not use_json:
            printer.error("Specs directory not found")
        return 1

    #  Load spec to get old status before update
    spec_data = load_json_spec(args.spec_id, specs_dir)
    old_status = None
    if spec_data:
        hierarchy = spec_data.get("hierarchy", {})
        if args.task_id in hierarchy:
            old_status = hierarchy[args.task_id].get("status", "unknown")

    success = update_task_status(
        spec_id=args.spec_id,
        task_id=args.task_id,
        new_status=args.status,
        specs_dir=specs_dir,
        note=args.note,
        dry_run=args.dry_run,
        verify=args.verify if hasattr(args, 'verify') else False,
        printer=printer  # Always pass printer (it's already configured for quiet mode when JSON is enabled)
    )

    if use_json:
        result = {
            'success': success,
            'task_id': args.task_id,
            'new_status': args.status,
            'old_status': old_status,
            'updated_at': datetime.now(timezone.utc).isoformat() if success else None,
            'spec_id': args.spec_id,
            'status_note': args.note
        }
        output = prepare_output(result, args, UPDATE_STATUS_ESSENTIAL, UPDATE_STATUS_STANDARD)
        output_json(output, args.compact)

    return 0 if success else 1


def cmd_mark_blocked(args, printer):
    """Mark task as blocked."""
    use_json = getattr(args, 'json', False)

    if not use_json:
        printer.action(f"Marking task {args.task_id} as blocked...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        if not use_json:
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
        printer=printer if not use_json else None
    )

    if use_json:
        result = {
            'success': success,
            'task_id': args.task_id,
            'spec_id': args.spec_id,
            'blocked_by': args.reason,
            'reason': args.reason,
            'marked_at': datetime.now(timezone.utc).isoformat() if success else None
        }
        output = prepare_output(result, args, MARK_BLOCKED_ESSENTIAL, MARK_BLOCKED_STANDARD)
        output_json(output, args.compact)

    return 0 if success else 1


def cmd_unblock_task(args, printer):
    """Unblock a task."""
    use_json = getattr(args, 'json', False)

    if not use_json:
        printer.action(f"Unblocking task {args.task_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        if not use_json:
            printer.error("Specs directory not found")
        return 1

    success = unblock_task(
        spec_id=args.spec_id,
        task_id=args.task_id,
        resolution=args.resolution,
        specs_dir=specs_dir,
        dry_run=args.dry_run,
        printer=printer if not use_json else None
    )

    if use_json:
        result = {
            'success': success,
            'task_id': args.task_id,
            'spec_id': args.spec_id,
            'unblocked_at': datetime.now(timezone.utc).isoformat() if success else None,
            'previously_blocked_by': args.resolution
        }
        output = prepare_output(result, args, UNBLOCK_TASK_ESSENTIAL, UNBLOCK_TASK_STANDARD)
        output_json(output, args.compact)

    return 0 if success else 1


def cmd_add_journal(args, printer):
    """Add journal entry."""
    use_json = getattr(args, 'json', False)

    if not use_json:
        printer.action("Adding journal entry...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        if not use_json:
            printer.error("Specs directory not found")
        return 1

    # Generate entry ID
    timestamp = datetime.now(timezone.utc)
    entry_id = f"journal-{timestamp.strftime('%Y%m%d%H%M%S')}"

    success = add_journal_entry(
        spec_id=args.spec_id,
        title=args.title,
        content=args.content,
        task_id=args.task_id,
        entry_type=args.entry_type,
        author=args.author,
        specs_dir=specs_dir,
        dry_run=args.dry_run,
        printer=printer if not use_json else None
    )

    if use_json:
        result = {
            'success': success,
            'entry_id': entry_id if success else None,
            'spec_id': args.spec_id,
            'task_id': args.task_id,
            'timestamp': timestamp.isoformat() if success else None,
            'entry_text': args.content
        }
        output = prepare_output(result, args, ADD_JOURNAL_ESSENTIAL, ADD_JOURNAL_STANDARD)
        output_json(output, args.compact)

    return 0 if success else 1


def cmd_add_revision(args, printer):
    """Add revision entry."""
    use_json = getattr(args, 'json', False)

    if not use_json:
        printer.action("Adding revision entry...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        if not use_json:
            printer.error("Specs directory not found")
        return 1

    # Generate revision ID
    timestamp = datetime.now(timezone.utc)
    revision_id = f"revision-{args.version.replace('.', '-')}"

    success = add_revision_entry(
        spec_id=args.spec_id,
        version=args.version,
        changes=args.changes,
        author=args.author,
        specs_dir=specs_dir,
        dry_run=args.dry_run,
        printer=printer if not use_json else None,
    )

    if use_json:
        result = {
            'success': success,
            'revision_id': revision_id if success else None,
            'spec_id': args.spec_id,
            'task_id': None,  # Revisions are spec-level, not task-level
            'timestamp': timestamp.isoformat() if success else None,
            'revision_text': args.changes,
            'revision_type': 'manual'
        }
        output = prepare_output(result, args, ADD_REVISION_ESSENTIAL, ADD_REVISION_STANDARD)
        output_json(output, args.compact)

    return 0 if success else 1


def cmd_add_assumption(args, printer):
    """Add assumption to spec metadata."""
    printer.action("Adding assumption...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    # Load spec
    spec_data = load_json_spec(args.spec_id, specs_dir)
    if not spec_data:
        printer.error(f"Could not load spec: {args.spec_id}")
        return 1

    # Add assumption
    try:
        result = add_assumption(
            spec_data=spec_data,
            text=args.text,
            assumption_type=args.type,
            added_by=getattr(args, 'author', 'claude-code')
        )

        if args.dry_run:
            printer.info("[DRY RUN] Would add assumption:")
            printer.detail(f"  ID: {result['assumption_id']}")
            printer.detail(f"  Type: {args.type}")
            printer.detail(f"  Text: {args.text}")
            dry_run_result = dict(result)
            dry_run_result["dry_run"] = True
            _emit_json_output(
                dry_run_result,
                args,
                ADD_ASSUMPTION_ESSENTIAL,
                ADD_ASSUMPTION_STANDARD,
            )
            return 0

        # Save spec
        save_json_spec(args.spec_id, specs_dir, spec_data)

        printer.success(result['message'])
        printer.info(f"Assumption ID: {result['assumption_id']}")

        _emit_json_output(
            result,
            args,
            ADD_ASSUMPTION_ESSENTIAL,
            ADD_ASSUMPTION_STANDARD,
        )

        return 0

    except ValueError as e:
        printer.error(f"Failed to add assumption: {e}")
        return 1


def cmd_list_assumptions(args, printer):
    """List assumptions from spec metadata."""
    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    # Load spec
    spec_data = load_json_spec(args.spec_id, specs_dir)
    if not spec_data:
        printer.error(f"Could not load spec: {args.spec_id}")
        return 1

    # Get assumptions
    try:
        assumption_type = getattr(args, 'type', None)
        assumptions = list_assumptions(spec_data, assumption_type=assumption_type)
    except (KeyError, TypeError, ValueError) as e:
        printer.error(f"Failed to list assumptions: {e}")
        return 1

    # Check if JSON output is enabled (set by options.py from config)
    use_json = getattr(args, 'json', False)
    verbosity_level = getattr(args, 'verbosity_level', VerbosityLevel.NORMAL)
    verbose_flag = getattr(args, 'verbose', False)

    # Only show metadata when BOTH --verbose flag is explicitly set AND verbosity_level is VERBOSE AND using JSON output
    # When --json is used without --verbose, always output a plain list
    # This ensures we never show metadata unless explicitly requested
    show_metadata = verbose_flag and use_json and verbosity_level == VerbosityLevel.VERBOSE

    def _emit_json_output(items):
        """Emit JSON either as a bare list (quiet/normal) or detailed dict (verbose)."""
        if show_metadata:
            data = {
                'assumptions': items,
                'spec_id': args.spec_id,
                'count': len(items),
                'filtered': bool(assumption_type)
            }
            output = prepare_output(data, args, LIST_ASSUMPTIONS_ESSENTIAL, LIST_ASSUMPTIONS_STANDARD)
            output_json(output, getattr(args, 'compact', False))
        else:
            output_json(items, getattr(args, 'compact', False))

    if not assumptions:
        if use_json:
            _emit_json_output([])
        else:
            if assumption_type:
                printer.info(f"No {assumption_type} assumptions found")
            else:
                printer.info("No assumptions found")
        return 0

    # Display assumptions
    if not use_json:
        if assumption_type:
            printer.success(f"Found {len(assumptions)} {assumption_type} assumption(s):")
        else:
            printer.success(f"Found {len(assumptions)} assumption(s):")

    if use_json:
        _emit_json_output(assumptions)
        return 0

    # Pretty print for human readability
    for i, assumption in enumerate(assumptions, 1):
        # Handle both legacy string format and new structured format
        if isinstance(assumption, str):
            # Legacy format: just a string
            print(f"\n{i}. {assumption}")
        elif isinstance(assumption, dict):
            # New structured format
            print(f"\n{assumption.get('id', f'assumption-{i}')}:")
            printer.detail(f"Type: {assumption.get('type', 'unknown')}")
            printer.detail(f"Text: {assumption.get('text', '')}")
            printer.detail(f"Added by: {assumption.get('added_by', 'unknown')}")
            printer.detail(f"Added at: {assumption.get('added_at', 'unknown')}")
            if 'updated_at' in assumption:
                printer.detail(f"Updated at: {assumption['updated_at']}")
        else:
            printer.warning(f"\n{i}. Invalid assumption format: {type(assumption)}")

    return 0


def cmd_update_estimate(args, printer):
    """Update task estimate (hours and/or complexity)."""
    printer.action(f"Updating estimate for task {args.task_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    # Load spec
    spec_data = load_json_spec(args.spec_id, specs_dir)
    if not spec_data:
        printer.error(f"Could not load spec: {args.spec_id}")
        return 1

    # Update estimate
    try:
        result = update_task_estimate(
            spec_data=spec_data,
            task_id=args.task_id,
            estimated_hours=args.hours if hasattr(args, 'hours') and args.hours is not None else None,
            complexity=args.complexity if hasattr(args, 'complexity') and args.complexity else None
        )

        if args.dry_run:
            printer.info("[DRY RUN] Would update estimate:")
            printer.detail(f"  Task: {result['task_id']} - {result['task_title']}")
            for key, value in result['updates'].items():
                printer.detail(f"  {key}: {value}")
            dry_run_result = dict(result)
            dry_run_result["dry_run"] = True
            _emit_json_output(
                dry_run_result,
                args,
                UPDATE_ESTIMATE_ESSENTIAL,
                UPDATE_ESTIMATE_STANDARD,
            )
            return 0

        # Save spec
        save_json_spec(args.spec_id, specs_dir, spec_data)

        printer.success(result['message'])

        _emit_json_output(
            result,
            args,
            UPDATE_ESTIMATE_ESSENTIAL,
            UPDATE_ESTIMATE_STANDARD,
        )

        return 0

    except ValueError as e:
        printer.error(f"Failed to update estimate: {e}")
        return 1


def cmd_add_task(args, printer):
    """Add a new task to the spec hierarchy."""
    printer.action(f"Adding task to {args.parent}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    # Load spec
    spec_data = load_json_spec(args.spec_id, specs_dir)
    if not spec_data:
        printer.error(f"Could not load spec: {args.spec_id}")
        return 1

    # Add task
    try:
        result = add_task(
            spec_data=spec_data,
            parent_id=args.parent,
            title=args.title,
            description=args.description if hasattr(args, 'description') and args.description else None,
            position=args.position if hasattr(args, 'position') and args.position is not None else None,
            task_type=args.type if hasattr(args, 'type') and args.type else "task",
            estimated_hours=args.hours if hasattr(args, 'hours') and args.hours is not None else None
        )

        if args.dry_run:
            printer.info("[DRY RUN] Would add task:")
            printer.detail(f"  ID: {result['task_id']}")
            printer.detail(f"  Title: {result['task_title']}")
            printer.detail(f"  Parent: {result['parent_id']}")
            if args.description:
                printer.detail(f"  Description: {args.description[:50]}...")
            dry_run_result = dict(result)
            dry_run_result["dry_run"] = True
            _emit_json_output(
                dry_run_result,
                args,
                ADD_TASK_ESSENTIAL,
                ADD_TASK_STANDARD,
            )
            return 0

        # Save spec
        save_json_spec(args.spec_id, specs_dir, spec_data)

        printer.success(result['message'])
        printer.info(f"Task ID: {result['task_id']}")

        _emit_json_output(
            result,
            args,
            ADD_TASK_ESSENTIAL,
            ADD_TASK_STANDARD,
        )

        return 0

    except ValueError as e:
        printer.error(f"Failed to add task: {e}")
        return 1


def cmd_remove_task(args, printer):
    """Remove a task from the spec hierarchy."""
    printer.action(f"Removing task {args.task_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    # Load spec
    spec_data = load_json_spec(args.spec_id, specs_dir)
    if not spec_data:
        printer.error(f"Could not load spec: {args.spec_id}")
        return 1

    # Remove task
    try:
        result = remove_task(
            spec_data=spec_data,
            task_id=args.task_id,
            cascade=args.cascade if hasattr(args, 'cascade') and args.cascade else False
        )

        if args.dry_run:
            printer.info("[DRY RUN] Would remove task:")
            printer.detail(f"  ID: {result['task_id']}")
            printer.detail(f"  Title: {result['task_title']}")
            printer.detail(f"  Removed count: {result['removed_count']}")
            dry_run_result = dict(result)
            dry_run_result["dry_run"] = True
            _emit_json_output(
                dry_run_result,
                args,
                REMOVE_TASK_ESSENTIAL,
                REMOVE_TASK_STANDARD,
            )
            return 0

        # Save spec
        save_json_spec(args.spec_id, specs_dir, spec_data)

        printer.success(result['message'])
        if result['removed_count'] > 1:
            printer.info(f"Removed {result['removed_count']} task(s) total (including children)")

        _emit_json_output(
            result,
            args,
            REMOVE_TASK_ESSENTIAL,
            REMOVE_TASK_STANDARD,
        )

        return 0

    except ValueError as e:
        printer.error(f"Failed to remove task: {e}")
        return 1


def cmd_update_frontmatter(args, printer):
    """Update metadata field in JSON spec."""
    use_json = getattr(args, 'json', False)

    if not use_json:
        printer.action(f"Updating metadata field '{args.key}'...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        if not use_json:
            printer.error("Specs directory not found")
        return 1

    success = update_metadata(
        spec_id=args.spec_id,
        key=args.key,
        value=args.value,
        specs_dir=specs_dir,
        dry_run=args.dry_run,
        printer=printer if not use_json else None
    )

    if use_json:
        result = {
            'success': success,
            'spec_id': args.spec_id,
            'updated_fields': [args.key] if success else [],
            'updated_at': datetime.now(timezone.utc).isoformat() if success else None
        }
        output = prepare_output(result, args, UPDATE_FRONTMATTER_ESSENTIAL, UPDATE_FRONTMATTER_STANDARD)
        output_json(output, args.compact)

    return 0 if success else 1


def cmd_add_verification(args, printer):
    """Add verification result."""
    use_json = getattr(args, 'json', False)

    if not use_json:
        printer.action(f"Recording verification result for {args.verify_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        if not use_json:
            printer.error("Specs directory not found")
        return 1

    # Generate verification ID
    timestamp = datetime.now(timezone.utc)
    verification_id = f"{args.verify_id}-{timestamp.strftime('%Y%m%d%H%M%S')}"

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
        printer=printer if not use_json else None
    )

    if use_json:
        result = {
            'success': success,
            'verification_id': verification_id if success else None,
            'spec_id': args.spec_id,
            'task_id': args.verify_id,
            'verification_type': args.status.lower(),
            'created_at': timestamp.isoformat() if success else None
        }
        output = prepare_output(result, args, ADD_VERIFICATION_ESSENTIAL, ADD_VERIFICATION_STANDARD)
        output_json(output, args.compact)

    return 0 if success else 1


def cmd_format_verification_summary(args, printer):
    """Format verification results summary."""
    use_json = getattr(args, 'json', False)

    # Read JSON input
    if args.json_file:
        try:
            with open(args.json_file, 'r') as f:
                verification_results = json.load(f)
        except Exception as e:
            if not use_json:
                printer.error(f"Failed to read JSON file: {e}")
            return 1
    elif args.json_input:
        try:
            verification_results = json.loads(args.json_input)
        except Exception as e:
            if not use_json:
                printer.error(f"Failed to parse JSON input: {e}")
            return 1
    else:
        if not use_json:
            printer.error("Must provide either --json-file or --json-input")
        return 1

    # Validate input
    if not isinstance(verification_results, list):
        if not use_json:
            printer.error("JSON input must be a list of verification results")
        return 1

    # Format the summary
    formatted = format_verification_summary(verification_results)

    if use_json:
        # Calculate summary stats
        total_verifications = len(verification_results)
        passed = sum(1 for v in verification_results if v.get('status') == 'PASSED')
        failed = sum(1 for v in verification_results if v.get('status') == 'FAILED')

        result = {
            'formatted': formatted,
            'spec_id': verification_results[0].get('spec_id') if verification_results else None,
            'total_verifications': total_verifications,
            'passed': passed,
            'failed': failed,
            'summary_type': 'verification'
        }
        output = prepare_output(result, args, FORMAT_VERIFICATION_SUMMARY_ESSENTIAL, FORMAT_VERIFICATION_SUMMARY_STANDARD)
        output_json(output, args.compact)
    else:
        # Print the formatted summary
        print(formatted)

    return 0


def cmd_move_spec(args, printer):
    """Move spec to another folder."""
    use_json = getattr(args, 'json', False)

    if not use_json:
        printer.action(f"Moving spec to {args.target}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        if not use_json:
            printer.error("Specs directory not found")
        return 1

    # Find the spec file to determine old location before moving
    spec_file = find_spec_file(args.spec_id, specs_dir)
    old_location = str(spec_file.parent.name) if spec_file else "unknown"
    new_location = args.target

    success = move_spec_by_id(
        spec_id=args.spec_id,
        target_folder=args.target,
        specs_dir=specs_dir,
        dry_run=args.dry_run,
        printer=printer
    )

    if use_json:
        result = {
            'success': success,
            'spec_id': args.spec_id,
            'old_location': old_location,
            'new_location': new_location,
            'moved_at': datetime.now(timezone.utc).isoformat() if success else None,
            'backup_created': False  # move_spec doesn't create backups
        }
        output = prepare_output(result, args, MOVE_SPEC_ESSENTIAL, MOVE_SPEC_STANDARD)
        output_json(output, args.compact)

    return 0 if success else 1


def cmd_activate_spec(args, printer):
    """Activate a pending spec by moving it to active folder."""
    use_json = getattr(args, 'json', False)

    if not use_json:
        printer.action(f"Activating spec {args.spec_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        if not use_json:
            printer.error("Specs directory not found")
        return 1

    success = activate_spec(
        spec_id=args.spec_id,
        specs_dir=specs_dir,
        dry_run=args.dry_run,
        printer=printer
    )

    if success and not use_json:
        printer.success("Spec activated and moved to active/. You can now start working on it with sdd next-task.")

    if use_json:
        result = {
            'success': success,
            'spec_id': args.spec_id,
            'old_folder': 'pending',
            'new_folder': 'active',
            'activated_at': datetime.now(timezone.utc).isoformat() if success else None
        }
        output = prepare_output(result, args, ACTIVATE_SPEC_ESSENTIAL, ACTIVATE_SPEC_STANDARD)
        output_json(output, args.compact)

    return 0 if success else 1


def cmd_complete_spec(args, printer):
    """Mark spec as completed and move to completed folder."""
    use_json = getattr(args, 'json', False)

    if not use_json:
        printer.action(f"Completing spec {args.spec_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        if not use_json:
            printer.error("Specs directory not found")
        return 1

    # If spec_file is provided, use it; otherwise let complete_spec find it
    spec_file = Path(args.spec_file).resolve() if args.spec_file else None

    # Load spec to get task count
    spec_data = load_json_spec(args.spec_id, specs_dir)
    total_tasks = 0
    if spec_data:
        hierarchy = spec_data.get("hierarchy", {})
        total_tasks = sum(1 for node in hierarchy.values() if node.get("type") == "task")

    success = complete_spec(
        spec_id=args.spec_id,
        spec_file=spec_file,
        specs_dir=specs_dir,
        skip_doc_regen=getattr(args, 'skip_doc_regen', False),
        dry_run=args.dry_run,
        printer=printer
    )

    if use_json:
        result = {
            'success': success,
            'spec_id': args.spec_id,
            'completed_at': datetime.now(timezone.utc).isoformat() if success else None,
            'total_tasks': total_tasks,
            'completion_time': None,  # Would need to calculate from spec metadata
            'moved_to': 'completed'
        }
        output = prepare_output(result, args, COMPLETE_SPEC_ESSENTIAL, COMPLETE_SPEC_STANDARD)
        output_json(output, args.compact)

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

    if args.json:
        if report is not None:
            _emit_json_output(
                report,
                args,
                TIME_REPORT_ESSENTIAL,
                TIME_REPORT_STANDARD,
            )
        else:
            # Fallback for None (shouldn't happen with updated generate_time_report)
            _emit_json_output({"error": "Failed to generate report"}, args)
            return 1

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
        _emit_json_output(
            report,
            args,
            STATUS_REPORT_ESSENTIAL,
            STATUS_REPORT_STANDARD,
        )

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
        _emit_json_output(
            result,
            args,
            AUDIT_SPEC_ESSENTIAL,
            AUDIT_SPEC_STANDARD,
        )

    return 0 if result.get("validation_passed", False) else 1


def cmd_query_tasks(args, printer):
    """Query and filter tasks."""
    # Determine output mode: simple takes precedence, then json, then text/table
    simple_mode = getattr(args, 'simple', False)
    json_mode = getattr(args, 'json', False) and not simple_mode

    if not json_mode and not simple_mode:
        printer.action("Querying tasks...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    # Use Rich.Table formatter for text mode (default)
    if not json_mode and not simple_mode:
        from claude_skills.common.ui_factory import create_ui
        ui = create_ui()
        results = format_tasks_table(
            spec_id=args.spec_id,
            specs_dir=specs_dir,
            status=args.status,
            task_type=args.type,
            parent=args.parent,
            printer=printer,
            limit=args.limit,
            ui=ui
        )
    else:
        # For simple or JSON mode, use original query_tasks
        use_printer = not json_mode and not simple_mode

        results = query_tasks(
            spec_id=args.spec_id,
            specs_dir=specs_dir,
            status=args.status,
            task_type=args.type,
            parent=args.parent,
            format_type="simple" if simple_mode else "json",
            printer=printer if use_printer else None,
            limit=args.limit
        )

    # Handle output for simple format (just task IDs)
    if simple_mode and results:
        for task in results:
            print(task["id"])
    elif json_mode and results:
        # Apply verbosity filtering for JSON output
        filtered_tasks = [
            prepare_output(task, args, QUERY_TASKS_ESSENTIAL, QUERY_TASKS_STANDARD)
            for task in results
        ]
        output_json(filtered_tasks, args.compact)

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
        output_json(task, args.compact)

    return 0 if task else 1


def cmd_get_journal(args, printer):
    """Get journal entries for a spec or task."""
    # Support both positional task_id and deprecated --task-id flag
    # Positional argument takes precedence
    task_id = getattr(args, 'task_id', None) or getattr(args, 'task_id_flag', None)

    if not args.json:
        if task_id:
            printer.action(f"Retrieving journal entries for task {task_id}...")
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
        task_id=task_id,
        printer=printer if not args.json else None
    )

    if args.json and entries is not None:
        output_json(entries, args.compact)

    return 0 if entries is not None else 1


def cmd_list_phases(args, printer):
    """List all phases."""
    from claude_skills.common.ui_factory import create_ui

    # Use global --json/--no-json flag to determine output format
    json_mode = getattr(args, 'json', False)

    if not json_mode:
        printer.action("Listing phases...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    if json_mode:
        # Use original list_phases for JSON output
        phases = list_phases(
            spec_id=args.spec_id,
            specs_dir=specs_dir,
            printer=None
        )
        if phases:
            output_json(phases, args.compact)
    else:
        # Create UI instance (respects FORCE_PLAIN environment variable)
        ui = create_ui()

        # Use unified table formatter for text output (works with both RichUi and PlainUi)
        phases = format_phases_table(
            spec_id=args.spec_id,
            specs_dir=specs_dir,
            printer=printer,
            ui=ui
        )

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
        _emit_json_output(
            result,
            args,
            CHECK_COMPLETE_ESSENTIAL,
            CHECK_COMPLETE_STANDARD,
        )

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
        _emit_json_output(
            result,
            args,
            PHASE_TIME_ESSENTIAL,
            PHASE_TIME_STANDARD,
        )

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

    if args.json and blockers is not None:
        # Apply verbosity filtering for JSON output
        filtered_blockers = [
            prepare_output(blocker, args, LIST_BLOCKERS_ESSENTIAL, LIST_BLOCKERS_STANDARD)
            for blocker in blockers
        ]
        output_json(filtered_blockers, args.compact)

    return 0 if blockers is not None else 1


def cmd_reconcile_state(args, printer):
    """Reconcile JSON spec to fix inconsistent task statuses."""
    if not args.json:
        printer.action(f"Reconciling state for {args.spec_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        if not args.json:
            printer.error("Specs directory not found")
        else:
            _emit_json_output({"error": "Specs directory not found"}, args)
        return 1

    # Pass None for printer in JSON mode
    result = reconcile_state(
        spec_id=args.spec_id,
        specs_dir=specs_dir,
        dry_run=args.dry_run,
        printer=printer if not args.json else None
    )

    # Handle JSON output
    if args.json:
        if isinstance(result, dict):
            _emit_json_output(
                result,
                args,
                RECONCILE_STATE_ESSENTIAL,
                RECONCILE_STATE_STANDARD,
            )
            # Return error if there was an error in the result
            return 1 if "error" in result else 0
        else:
            # Fallback for unexpected return type
            _emit_json_output({"success": bool(result)}, args)
            return 0 if result else 1

    # Non-JSON mode returns boolean
    return 0 if result else 1


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
        output_json(unjournaled, args.compact)
        return 0

    if not unjournaled:
        printer.success("All completed tasks have been journaled!")
        return 0

    # Display unjournaled tasks
    printer.warning(f"Found {len(unjournaled)} completed task(s) without journal entries:\n")
    for i, task in enumerate(unjournaled, 1):
        printer.item(f"Task ID: {task['task_id']} - {task['title']}")
        printer.detail(f"Completed: {task['completed_at']}", indent=2)

    printer.blank()
    printer.detail("To journal these tasks, run:")
    printer.detail(f"  sdd bulk-journal {args.spec_id}", indent=1)

    return 1  # Exit with error code to indicate action needed


def cmd_bulk_journal(args, printer):
    """Bulk journal completed tasks."""
    use_json = getattr(args, 'json', False)

    if not use_json:
        printer.action("Bulk journaling tasks...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        if not use_json:
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
        printer=printer if not use_json else None,
        template=args.template,
        template_metadata={"author": args.template_author} if args.template_author else None,
    )

    if use_json:
        result = {
            'success': success,
            'entries_added': len(task_ids) if task_ids and success else 0,
            'spec_id': args.spec_id,
            'task_ids': task_ids if task_ids else [],
            'timestamp': datetime.now(timezone.utc).isoformat() if success else None,
            'entry_count': len(task_ids) if task_ids and success else 0
        }
        output = prepare_output(result, args, BULK_JOURNAL_ESSENTIAL, BULK_JOURNAL_STANDARD)
        output_json(output, args.compact)

    return 0 if success else 1


def cmd_create_task_commit(args, printer):
    """Create commit from staged files for a task (two-step workflow)."""
    printer.action(f"Creating commit from staged files for task {args.task_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    # Load JSON spec file
    spec_data = load_json_spec(args.spec_id, specs_dir)
    if not spec_data:
        printer.error(f"Could not load JSON spec file for {args.spec_id}")
        return 1

    # Verify task exists in hierarchy
    hierarchy = spec_data.get("hierarchy", {})
    if args.task_id not in hierarchy:
        printer.error(f"Task '{args.task_id}' not found in spec {args.spec_id}")
        return 1

    # Get task info for validation
    task = hierarchy[args.task_id]
    task_title = task.get("title", "Untitled")
    task_status = task.get("status", "pending")

    # Optional: Warn if task is not completed (but don't block)
    if task_status != "completed" and not args.skip_status_check:
        printer.warning(f"Task {args.task_id} is not marked as completed (status: {task_status})")
        printer.warning("Consider completing the task first with 'sdd complete-task'")
        if not args.force:
            printer.error("Use --force to create commit anyway, or --skip-status-check to disable this check")
            return 1

    # Find repository root
    from claude_skills.common.git_metadata import find_git_root, create_commit_from_staging

    repo_root = find_git_root(specs_dir)
    if not repo_root:
        printer.error("No git repository found")
        return 1

    # Create commit from staged files
    printer.info(f"Creating commit for: {task_title}")
    printer.info(f"Repository: {repo_root}")

    success, commit_sha, error_msg = create_commit_from_staging(
        repo_root=repo_root,
        spec_id=args.spec_id,
        task_id=args.task_id,
        printer=printer
    )

    if not success:
        printer.error(f"Failed to create commit: {error_msg}")
        return 1

    # Success!
    printer.success(f"Commit created successfully: {commit_sha[:8] if commit_sha else 'unknown'}")

    # Output JSON if requested
    if args.json:
        result = {
            "success": True,
            "commit_sha": commit_sha,
            "spec_id": args.spec_id,
            "task_id": args.task_id,
            "task_title": task_title
        }
        _emit_json_output(
            result,
            args,
            CREATE_TASK_COMMIT_ESSENTIAL,
            CREATE_TASK_COMMIT_STANDARD,
        )

    return 0


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
        output_json(success, args.compact)
        return 0

    return 0 if success else 1


def cmd_list_specs(args, printer):
    """List specification files with optional filtering."""
    # Use global --json/--no-json flag to determine output format
    output_format = 'json' if getattr(args, 'json', False) else 'text'

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        printer.error("Specs directory not found")
        return 1

    list_specs(
        status=args.status,
        specs_dir=specs_dir,
        output_format=output_format,
        verbose=args.detailed,
        printer=printer,
        compact=getattr(args, 'compact', False),
        args=args,
    )

    return 0


def cmd_sync_metadata(args, printer):
    """Synchronize spec metadata with hierarchy data."""
    use_json = getattr(args, 'json', False)

    if not use_json:
        printer.action("Synchronizing metadata from hierarchy...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        if not use_json:
            printer.error("Specs directory not found")
        return 1

    success = sync_metadata_from_state(
        spec_id=args.spec_id,
        specs_dir=specs_dir,
        dry_run=args.dry_run,
        printer=printer if not use_json else None
    )

    if use_json:
        result = {
            'success': success,
            'spec_id': args.spec_id,
            'synced_fields': ['status', 'progress', 'current_phase'] if success else [],
            'updated_at': datetime.now(timezone.utc).isoformat() if success else None,
            'changes_made': success
        }
        output = prepare_output(result, args, SYNC_METADATA_ESSENTIAL, SYNC_METADATA_STANDARD)
        output_json(output, args.compact)

    return 0 if success else 1


def cmd_update_task_metadata(args, printer):
    """Update task metadata fields."""
    use_json = getattr(args, 'json', False)

    if not use_json:
        printer.action(f"Updating metadata for task {args.task_id}...")

    specs_dir = find_specs_directory(getattr(args, 'specs_dir', None) or getattr(args, 'path', '.'))
    if not specs_dir:
        if not use_json:
            printer.error("Specs directory not found")
            printer.info("\nNext steps:")
            printer.detail("1. Verify you're in the project root directory")
            printer.detail("2. Check that specs/ folder exists with subfolders: pending/, active/, completed/, archived/")
            printer.detail("3. Or specify path: --specs-dir /path/to/specs")
        return 1

    # Collect metadata updates from args
    metadata_updates = {}

    # First, parse --metadata JSON if provided
    if hasattr(args, 'metadata_json') and args.metadata_json:
        try:
            parsed_metadata = json.loads(args.metadata_json)

            # Validate it's a dictionary
            if not isinstance(parsed_metadata, dict):
                printer.error("--metadata must be a JSON object (dictionary), not a list, string, or other type")
                printer.info("\nExample usage:")
                printer.detail('  --metadata \'{"focus_areas": ["performance", "security"], "priority": "high"}\'')
                return 1

            # Merge parsed metadata
            metadata_updates.update(parsed_metadata)

        except json.JSONDecodeError as e:
            printer.error(f"Invalid JSON in --metadata argument: {str(e)}")
            printer.info("\nExpected format:")
            printer.detail('  --metadata \'{"field_name": "value", "array_field": ["item1", "item2"]}\'')
            printer.info("\nCommon issues:")
            printer.detail("  - Use single quotes around the JSON string")
            printer.detail("  - Use double quotes for JSON keys and string values")
            printer.detail("  - Ensure all brackets/braces are balanced")
            return 1
        except Exception as e:
            printer.error(f"Error parsing --metadata argument: {str(e)}")
            return 1

    # Collect individual field flags (these take precedence over --metadata)
    if hasattr(args, 'file_path') and args.file_path:
        metadata_updates['file_path'] = args.file_path
    if hasattr(args, 'description') and args.description:
        metadata_updates['description'] = args.description
    if hasattr(args, 'task_category') and args.task_category:
        metadata_updates['task_category'] = args.task_category
    if hasattr(args, 'actual_hours') and args.actual_hours is not None:
        metadata_updates['actual_hours'] = args.actual_hours
    if hasattr(args, 'status_note') and args.status_note:
        metadata_updates['status_note'] = args.status_note
    if hasattr(args, 'verification_type') and args.verification_type:
        metadata_updates['verification_type'] = args.verification_type
    if hasattr(args, 'command') and args.command:
        metadata_updates['command'] = args.command

    # Validate that at least one metadata field was provided
    if not metadata_updates:
        printer.error("No metadata fields provided. Use --help to see available options.")
        printer.info("\nYou can use either:")
        printer.detail("  - Individual flags: --file-path, --description, --task-category, etc.")
        printer.detail('  - JSON metadata: --metadata \'{"custom_field": "value"}\'')
        printer.detail("  - Or both together (individual flags take precedence)")
        return 1

    # Load JSON spec file
    spec_data = load_json_spec(args.spec_id, specs_dir)
    if not spec_data:
        printer.error(f"Could not load JSON spec file for {args.spec_id}")
        printer.info("\nNext steps:")
        printer.detail("1. List available specs: sdd list-specs")
        printer.detail(f"2. Verify spec ID format: '{args.spec_id}' (without .json extension)")
        printer.detail("3. Check all spec folders: pending/, active/, completed/, archived/")
        return 1

    # Verify task exists in hierarchy
    hierarchy = spec_data.get("hierarchy", {})
    if args.task_id not in hierarchy:
        printer.error(f"Task '{args.task_id}' not found in spec {args.spec_id}")
        printer.info("\nNext steps:")
        printer.detail(f"1. List tasks: sdd query-tasks {args.spec_id}")
        printer.detail(f"2. Get task details: sdd get-task {args.spec_id} <task-id>")
        printer.detail("3. Verify task ID format (e.g., 'task-1-2-3' not 'Task 1.2.3')")
        return 1

    # Show preview of changes
    task = hierarchy[args.task_id]
    current_metadata = task.get("metadata", {})

    if args.dry_run:
        printer.info(f"Would update task {args.task_id} ({task.get('title', 'Untitled')})")
        printer.info("Metadata changes:")
        for key, new_value in metadata_updates.items():
            old_value = current_metadata.get(key, "(not set)")
            printer.detail(f"  {key}: {old_value} → {new_value}")
        printer.info("\nNo changes made (--dry-run mode)")
        return 0

    # Update the task metadata
    updates = {"metadata": metadata_updates}
    if not update_node(spec_data, args.task_id, updates):
        printer.error(f"Failed to update task {args.task_id}")
        return 1

    # Save the updated spec file with backup
    if not save_json_spec(args.spec_id, specs_dir, spec_data, backup=True):
        printer.error(f"Failed to save spec file for {args.spec_id}")
        return 1

    # Success message
    if not use_json:
        printer.success(f"Task {args.task_id} metadata updated successfully")
        printer.info("Updated fields:")
        for key, value in metadata_updates.items():
            printer.detail(f"  {key}: {value}")

    if use_json:
        result = {
            'success': True,
            'task_id': args.task_id,
            'spec_id': args.spec_id,
            'updated_fields': list(metadata_updates.keys()),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'metadata': metadata_updates
        }
        output = prepare_output(result, args, UPDATE_TASK_METADATA_ESSENTIAL, UPDATE_TASK_METADATA_STANDARD)
        output_json(output, args.compact)

    return 0


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
    p_front.add_argument("spec_id", help="Specification ID")
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
    p_move.add_argument("spec_id", help="Specification ID")
    p_move.add_argument("target", choices=["active", "completed", "archived"])
    p_move.add_argument("--dry-run", action="store_true", help="Preview move")
    p_move.set_defaults(func=cmd_move_spec)

    # complete-spec command
    p_complete = subparsers.add_parser("complete-spec", help="Mark spec as completed", parents=[parent_parser])
    p_complete.add_argument("spec_id", help="Specification ID")
    p_complete.add_argument("spec_file", nargs='?', help="Path to spec file (optional - will be auto-detected if not provided)")
    p_complete.add_argument("--skip-doc-regen", action="store_true", help="Skip documentation regeneration for faster completion")
    p_complete.add_argument("--dry-run", action="store_true", help="Preview changes")
    p_complete.set_defaults(func=cmd_complete_spec)

    # activate-spec command
    p_activate = subparsers.add_parser("activate-spec", help="Activate a pending spec", parents=[parent_parser])
    p_activate.add_argument("spec_id", help="Specification ID")
    p_activate.add_argument("--dry-run", action="store_true", help="Preview changes")
    p_activate.set_defaults(func=cmd_activate_spec)

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
    p_query.add_argument("--simple", action="store_true", help="Output only task IDs (one per line)")
    p_query.add_argument("--limit", type=int, default=20, help="Maximum number of results to return (use 0 for unlimited, default: 20)")
    p_query.set_defaults(func=cmd_query_tasks)

    # get-task command
    p_get_task = subparsers.add_parser("get-task", help="Get detailed task information", parents=[parent_parser])
    p_get_task.add_argument("spec_id", help="Specification ID")
    p_get_task.add_argument("task_id", help="Task ID to retrieve")
    p_get_task.add_argument("--include-journal", action="store_true", help="Include journal entries for this task")
    p_get_task.set_defaults(func=cmd_get_task)

    # get-journal command
    p_get_journal = subparsers.add_parser(
        "get-journal",
        help="Get journal entries for a spec or task (usage: sdd get-journal SPEC_ID [TASK_ID])",
        parents=[parent_parser]
    )
    p_get_journal.add_argument("spec_id", help="Specification ID")
    p_get_journal.add_argument("task_id", nargs='?', help="Optional task ID to filter journal entries (positional)")
    p_get_journal.add_argument("--task-id", dest="task_id_flag", help="Filter by task ID (deprecated, use positional argument)")
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

    # add-assumption command
    p_assumption = subparsers.add_parser("add-assumption", help="Add assumption to spec metadata", parents=[parent_parser])
    p_assumption.add_argument("spec_id", help="Specification ID")
    p_assumption.add_argument("text", help="Assumption text/description")
    p_assumption.add_argument("--type", default="requirement", choices=["constraint", "requirement"], help="Assumption type")
    p_assumption.add_argument("--author", default="claude-code", help="Author who added the assumption")
    p_assumption.add_argument("--dry-run", action="store_true", help="Preview assumption without saving")
    p_assumption.set_defaults(func=cmd_add_assumption)

    # list-assumptions command
    p_list_assumptions = subparsers.add_parser("list-assumptions", help="List assumptions from spec metadata", parents=[parent_parser])
    p_list_assumptions.add_argument("spec_id", help="Specification ID")
    p_list_assumptions.add_argument("--type", choices=["constraint", "requirement"], help="Filter by assumption type")
    p_list_assumptions.set_defaults(func=cmd_list_assumptions)

    # update-estimate command
    p_estimate = subparsers.add_parser("update-estimate", help="Update task estimate (hours and/or complexity)", parents=[parent_parser])
    p_estimate.add_argument("spec_id", help="Specification ID")
    p_estimate.add_argument("task_id", help="Task ID to update")
    p_estimate.add_argument("--hours", type=float, help="Estimated hours (float)")
    p_estimate.add_argument("--complexity", choices=["low", "medium", "high"], help="Complexity level")
    p_estimate.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    p_estimate.set_defaults(func=cmd_update_estimate)

    # add-task command
    p_add_task = subparsers.add_parser("add-task", help="Add a new task to the spec hierarchy", parents=[parent_parser])
    p_add_task.add_argument("spec_id", help="Specification ID")
    p_add_task.add_argument("--parent", required=True, help="Parent node ID (e.g., phase-1, task-2-1)")
    p_add_task.add_argument("--title", required=True, help="Task title")
    p_add_task.add_argument("--description", help="Task description")
    p_add_task.add_argument("--type", default="task", choices=["task", "subtask", "verify"], help="Task type")
    p_add_task.add_argument("--hours", type=float, help="Estimated hours")
    p_add_task.add_argument("--position", type=int, help="Position in parent's children list (0-based)")
    p_add_task.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    p_add_task.set_defaults(func=cmd_add_task)

    # remove-task command
    p_remove_task = subparsers.add_parser("remove-task", help="Remove a task from the spec hierarchy", parents=[parent_parser])
    p_remove_task.add_argument("spec_id", help="Specification ID")
    p_remove_task.add_argument("task_id", help="Task ID to remove")
    p_remove_task.add_argument("--cascade", action="store_true", help="Also remove all child tasks recursively")
    p_remove_task.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    p_remove_task.set_defaults(func=cmd_remove_task)

    # bulk-journal command
    p_bulk_journal = subparsers.add_parser("bulk-journal", help="Bulk journal completed tasks", parents=[parent_parser])
    p_bulk_journal.add_argument("spec_id", help="Specification ID")
    p_bulk_journal.add_argument("--tasks", help="Comma-separated list of task IDs (if omitted, journals all unjournaled tasks)")
    p_bulk_journal.add_argument("--template", choices=["completion", "decision", "blocker"], help="Apply a journal template")
    p_bulk_journal.add_argument("--template-author", help="Override author for templated entries")
    p_bulk_journal.add_argument("--dry-run", action="store_true", help="Preview journal entries without saving")
    p_bulk_journal.set_defaults(func=cmd_bulk_journal)

    # create-task-commit command
    p_create_commit = subparsers.add_parser(
        "create-task-commit",
        help="Create commit from staged files for a task (two-step workflow)",
        parents=[parent_parser],
    )
    p_create_commit.add_argument("spec_id", help="Specification ID")
    p_create_commit.add_argument("task_id", help="Task ID to commit")
    p_create_commit.add_argument("--skip-status-check", action="store_true", help="Skip checking if task is completed")
    p_create_commit.add_argument("--force", action="store_true", help="Force commit even if task is not completed")
    p_create_commit.set_defaults(func=cmd_create_task_commit)

    # complete-task command
    p_complete_task = subparsers.add_parser(
        "complete-task",
        help="Complete task with optional journaling and metadata updates. Time is automatically calculated from started_at and completed_at timestamps.",
        parents=[parent_parser],
    )
    p_complete_task.add_argument("spec_id", help="Specification ID")
    p_complete_task.add_argument("task_id", help="Task ID to complete")
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

    # list-specs command
    p_list_specs = subparsers.add_parser(
        "list-specs",
        help="List specification files with optional filtering",
        parents=[parent_parser],
    )
    p_list_specs.add_argument(
        "--status",
        choices=["active", "completed", "archived", "pending", "all"],
        help="Filter by status folder (default: all)",
    )
    p_list_specs.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed information",
    )
    p_list_specs.set_defaults(func=cmd_list_specs)

    # sync-metadata command
    p_sync_meta = subparsers.add_parser("sync-metadata", help="Synchronize spec metadata with hierarchy data", parents=[parent_parser])
    p_sync_meta.add_argument("spec_id", help="Specification ID")
    p_sync_meta.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    p_sync_meta.set_defaults(func=cmd_sync_metadata)

    # update-task-metadata command
    p_update_meta = subparsers.add_parser(
        "update-task-metadata",
        help="Update task metadata fields",
        parents=[parent_parser]
    )
    p_update_meta.add_argument("spec_id", help="Specification ID")
    p_update_meta.add_argument("task_id", help="Task ID to update")

    # The metadata field flags
    p_update_meta.add_argument("--file-path", dest="file_path", help="File path for this task")
    p_update_meta.add_argument("--description", help="Task description")
    p_update_meta.add_argument("--task-category", dest="task_category", help="Task category (implementation, testing, etc.)")
    p_update_meta.add_argument("--actual-hours", dest="actual_hours", type=float, help="Actual hours spent on task")
    p_update_meta.add_argument("--status-note", dest="status_note", help="Status note or completion note")
    p_update_meta.add_argument("--verification-type", dest="verification_type", help="Verification type (auto, manual, none)")
    p_update_meta.add_argument("--command", help="Command executed")

    # JSON metadata flag for arbitrary custom fields
    p_update_meta.add_argument(
        "--metadata",
        dest="metadata_json",
        help="JSON string with custom metadata fields (e.g., '{\"focus_areas\": [\"performance\"], \"priority\": \"high\"}'). "
             "Merges with individual flags; individual flags take precedence on conflict."
    )

    # Standard flags
    p_update_meta.add_argument("--dry-run", action="store_true", help="Preview changes without saving")

    p_update_meta.set_defaults(func=cmd_update_task_metadata)
