"""
Task status update operations for SDD workflows.
"""

from pathlib import Path
from typing import Optional, List
from datetime import datetime, timezone

# Import from sdd-common
# sdd_update.status
from claude_skills.common.spec import load_json_spec, save_json_spec, update_node
from claude_skills.common.progress import recalculate_progress
from claude_skills.common.printer import PrettyPrinter
from claude_skills.common import execute_verify_task
from claude_skills.common.completion import check_spec_completion


def find_verify_tasks_for_task(spec_data: dict, task_id: str) -> List[str]:
    """
    Find all verify tasks associated with a given task.

    Verify tasks are identified by:
    1. Having type="verify"
    2. Being a sibling or child of the task (same parent or task is parent)
    3. Having an ID pattern like verify-X-Y where X matches task-X-Y

    Args:
        spec_data: Loaded JSON spec data
        task_id: Task ID to find verify tasks for (e.g., "task-1-1")

    Returns:
        List of verify task IDs
    """
    hierarchy = spec_data.get("hierarchy", {})
    verify_tasks = []

    # Extract task number pattern (e.g., "task-1-1" -> "1-1")
    if not task_id.startswith("task-"):
        return verify_tasks

    task_number = task_id.replace("task-", "")

    # Look for verify tasks with matching pattern
    for node_id, node_data in hierarchy.items():
        if node_data.get("type") == "verify":
            # Check if verify task ID matches pattern (verify-1-1 for task-1-1)
            if node_id.startswith(f"verify-{task_number}"):
                verify_tasks.append(node_id)

    return verify_tasks


def update_task_status(
    spec_id: str,
    task_id: str,
    new_status: str,
    specs_dir: Path,
    note: Optional[str] = None,
    dry_run: bool = False,
    verify: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> bool:
    """
    Update a task's status with automatic progress recalculation.

    Args:
        spec_id: Specification ID
        task_id: Task identifier
        new_status: New status (pending, in_progress, completed, blocked)
        specs_dir: Path to specs/active directory
        note: Optional note about the status change
        dry_run: If True, don't save changes
        verify: If True and new_status is 'completed', run associated verify tasks
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    # Validate status value
    valid_statuses = ["pending", "in_progress", "completed", "blocked"]
    if new_status not in valid_statuses:
        printer.error(f"Invalid status '{new_status}'. Must be one of: {', '.join(valid_statuses)}")
        return False

    # Load JSON spec
    printer.action(f"Loading state for {spec_id}...")
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return False

    # Check if task exists
    hierarchy = spec_data.get("hierarchy", {})
    if task_id not in hierarchy:
        printer.error(f"Task '{task_id}' not found in JSON spec")
        return False

    task = hierarchy[task_id]
    old_status = task.get("status", "unknown")

    # Prepare updates
    updates = {"status": new_status}

    # Add timestamps
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if "metadata" not in task:
        task["metadata"] = {}

    if new_status == "in_progress":
        updates.setdefault("metadata", {})["started_at"] = timestamp
    elif new_status == "completed":
        updates.setdefault("metadata", {})["completed_at"] = timestamp
        # Mark that this task needs a journal entry
        updates.setdefault("metadata", {})["needs_journaling"] = True

    if note:
        updates.setdefault("metadata", {})["status_note"] = note

    # Show what will change
    printer.info(f"Task: {task.get('title', task_id)}")
    printer.info(f"Status: {old_status} → {new_status}")
    if note:
        printer.info(f"Note: {note}")

    if dry_run:
        printer.warning("DRY RUN - No changes saved")
        return True

    # Update the task
    if not update_node(spec_data, task_id, updates):
        printer.error("Failed to update task")
        return False

    # Recalculate progress up the hierarchy
    printer.action("Recalculating progress...")
    recalculate_progress(spec_data)

    # Save JSON spec with backup
    printer.action("Saving JSON spec...")
    if not save_json_spec(spec_id, specs_dir, spec_data, backup=True):
        printer.error("Failed to save JSON spec")
        return False

    printer.success(f"Task {task_id} status updated to '{new_status}'")

    # Check if spec is complete after marking task as completed
    completion_result = None
    if new_status == "completed" and not dry_run:
        completion_result = check_spec_completion(spec_data)

        # Display completion prompt if appropriate
        from claude_skills.common.completion import should_prompt_completion, format_completion_prompt

        # Check if we should prompt
        prompt_decision = should_prompt_completion(spec_data)

        if prompt_decision.get("should_prompt"):
            # Format the prompt
            prompt_data = format_completion_prompt(spec_data, show_hours_input=True)

            if not prompt_data.get("error"):
                # Display informational message (non-blocking)
                printer.blank()
                printer.info("=" * 60)
                printer.success(prompt_data["prompt_text"])
                printer.info("=" * 60)
                printer.blank()

                # Provide actionable next step for Claude/user
                printer.info("To mark this spec as complete, run:")
                printer.info(f"  sdd complete-spec {spec_id}")

                # Show estimated hours hint if available
                metadata = spec_data.get("metadata", {})
                estimated_hours = metadata.get("estimated_hours")
                if estimated_hours:
                    printer.info(f"  --actual-hours <hours>  (estimated: {estimated_hours}h)")

                printer.blank()
        else:
            # Inform user why completion prompt was not shown
            reason = prompt_decision.get("reason", "Unknown reason")
            if "blocked" in reason.lower():
                printer.warning(f"\n⚠️  Spec completion not available: {reason}")

    # Run verification if requested and task is completed
    if verify and new_status == "completed" and not dry_run:
        printer.action("Running verification tasks...")

        # Find associated verify tasks
        verify_tasks = find_verify_tasks_for_task(spec_data, task_id)

        if not verify_tasks:
            printer.info(f"No verification tasks found for {task_id}")
        else:
            printer.info(f"Found {len(verify_tasks)} verification task(s)")

            # Execute each verify task
            all_passed = True
            should_continue = True
            consult_recommended = False
            actions_summary = []

            for verify_id in verify_tasks:
                if not should_continue:
                    printer.warning(f"Skipping {verify_id} due to previous failure")
                    continue

                printer.info(f"Executing {verify_id}...")
                result = execute_verify_task(spec_data, verify_id, spec_root=str(specs_dir.parent))

                if result["success"]:
                    printer.success(f"✓ {verify_id} passed")
                    if result.get("retry_count", 0) > 0:
                        printer.info(f"  (succeeded after {result['retry_count']} retries)")
                else:
                    printer.error(f"✗ {verify_id} failed")
                    if result.get("errors"):
                        for error in result["errors"]:
                            printer.error(f"  {error}")

                    all_passed = False

                    # Check on_failure configuration
                    on_failure = result.get("on_failure")
                    if on_failure:
                        # Record actions taken
                        if result.get("actions_taken"):
                            actions_summary.extend(result["actions_taken"])
                            printer.info(f"  Actions: {', '.join(result['actions_taken'])}")

                        # Check if should consult AI
                        if on_failure.get("consult", False):
                            consult_recommended = True

                        # Check if should continue with other verifications
                        if not on_failure.get("continue_on_failure", False):
                            should_continue = False
                            printer.warning("  Stopping further verifications due to failure")

            # If any verification failed, handle based on on_failure config
            if not all_passed:
                # Determine revert status (default to in_progress if not specified)
                revert_status = "in_progress"

                # Check first failed verify task for custom revert status
                for verify_id in verify_tasks:
                    hierarchy = spec_data.get("hierarchy", {})
                    if verify_id in hierarchy:
                        verify_task = hierarchy[verify_id]
                        on_failure = verify_task.get("metadata", {}).get("on_failure", {})
                        if on_failure.get("revert_status"):
                            revert_status = on_failure["revert_status"]
                            break

                printer.warning(f"Verification failed - reverting {task_id} to '{revert_status}'")

                # Revert status
                revert_updates = {
                    "status": revert_status,
                    "metadata": {
                        **task.get("metadata", {}),
                        "verification_failed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "verification_failure_note": "Automatic verification failed after completion",
                        "verification_actions": actions_summary
                    }
                }

                # Remove completed_at timestamp since we're reverting
                if "completed_at" in revert_updates["metadata"]:
                    del revert_updates["metadata"]["completed_at"]

                update_node(spec_data, task_id, revert_updates)
                recalculate_progress(spec_data)
                save_json_spec(spec_id, specs_dir, spec_data, backup=True)

                printer.error(f"Task {task_id} reverted to '{revert_status}' due to verification failure")

                # Recommend AI consultation if configured
                if consult_recommended:
                    printer.info("\n💡 AI consultation recommended - consider using run-tests skill for debugging")

                return False
            else:
                printer.success("All verification tasks passed!")

    # Remind user to add journal entry if marking as completed
    if new_status == "completed" and not dry_run:
        hierarchy = spec_data.get("hierarchy", {})
        needs_journal = hierarchy.get(task_id, {}).get("metadata", {}).get("needs_journaling", True)
        if needs_journal:
            printer.info("💡 Remember to add a journal entry documenting this completion")
            printer.info(f"   Run: add-journal {spec_id} --task-id {task_id} --title \"Task Completed\" --content \"...\"")

    return True


def mark_task_blocked(
    spec_id: str,
    task_id: str,
    reason: str,
    specs_dir: Path,
    blocker_type: str = "dependency",
    ticket: Optional[str] = None,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> bool:
    """
    Mark a task as blocked with detailed blocker information.

    Args:
        spec_id: Specification ID
        task_id: Task identifier
        reason: Description of why task is blocked
        specs_dir: Path to specs/active directory
        blocker_type: Type of blocker (dependency, technical, resource, decision)
        ticket: Optional ticket/issue reference
        dry_run: If True, don't save changes
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    valid_blocker_types = ["dependency", "technical", "resource", "decision"]
    if blocker_type not in valid_blocker_types:
        printer.warning(f"Unusual blocker type '{blocker_type}'. Expected: {', '.join(valid_blocker_types)}")

    # Load JSON spec
    printer.action(f"Loading state for {spec_id}...")
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return False

    # Check if task exists
    hierarchy = spec_data.get("hierarchy", {})
    if task_id not in hierarchy:
        printer.error(f"Task '{task_id}' not found in JSON spec")
        return False

    task = hierarchy[task_id]

    # Prepare blocker metadata
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    blocker_info = {
        "blocked_at": timestamp,
        "blocker_type": blocker_type,
        "blocker_description": reason,
        "blocked_by_external": blocker_type in ["resource", "dependency"]
    }

    if ticket:
        blocker_info["blocker_ticket"] = ticket

    # Update task
    updates = {
        "status": "blocked",
        "metadata": {**task.get("metadata", {}), **blocker_info}
    }

    printer.info(f"Task: {task.get('title', task_id)}")
    printer.info(f"Blocker: {blocker_type} - {reason}")
    if ticket:
        printer.info(f"Ticket: {ticket}")

    if dry_run:
        printer.warning("DRY RUN - No changes saved")
        return True

    # Update the task
    if not update_node(spec_data, task_id, updates):
        printer.error("Failed to update task")
        return False

    # Recalculate progress
    printer.action("Recalculating progress...")
    recalculate_progress(spec_data)

    # Save JSON spec
    printer.action("Saving JSON spec...")
    if not save_json_spec(spec_id, specs_dir, spec_data, backup=True):
        printer.error("Failed to save JSON spec")
        return False

    printer.success(f"Task {task_id} marked as blocked")
    printer.info("Don't forget to add a journal entry documenting the blocker!")
    return True


def unblock_task(
    spec_id: str,
    task_id: str,
    resolution: Optional[str] = None,
    specs_dir: Path = None,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> bool:
    """
    Unblock a task and optionally set it to pending or in_progress.

    Args:
        spec_id: Specification ID
        task_id: Task identifier
        resolution: Optional description of how blocker was resolved
        specs_dir: Path to specs/active directory
        dry_run: If True, don't save changes
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    # Load JSON spec
    printer.action(f"Loading state for {spec_id}...")
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return False

    # Check if task exists
    hierarchy = spec_data.get("hierarchy", {})
    if task_id not in hierarchy:
        printer.error(f"Task '{task_id}' not found in JSON spec")
        return False

    task = hierarchy[task_id]

    if task.get("status") != "blocked":
        printer.warning(f"Task {task_id} is not blocked (current status: {task.get('status')})")
        return False

    # Prepare updates
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    metadata = task.get("metadata", {}).copy()

    # Move blocker info to resolved_blockers
    if "blocker_description" in metadata:
        if "resolved_blockers" not in metadata:
            metadata["resolved_blockers"] = []

        metadata["resolved_blockers"].append({
            "blocked_at": metadata.get("blocked_at"),
            "blocker_type": metadata.get("blocker_type"),
            "description": metadata.get("blocker_description"),
            "ticket": metadata.get("blocker_ticket"),
            "resolved_at": timestamp,
            "resolution": resolution or "Blocker resolved"
        })

        # Remove active blocker fields
        for key in ["blocked_at", "blocker_type", "blocker_description", "blocker_ticket", "blocked_by_external"]:
            metadata.pop(key, None)

    updates = {
        "status": "pending",  # Reset to pending, user can set to in_progress if needed
        "metadata": metadata
    }

    printer.info(f"Task: {task.get('title', task_id)}")
    printer.info(f"Unblocking task and setting status to 'pending'")
    if resolution:
        printer.info(f"Resolution: {resolution}")

    if dry_run:
        printer.warning("DRY RUN - No changes saved")
        return True

    # Update the task
    if not update_node(spec_data, task_id, updates):
        printer.error("Failed to update task")
        return False

    # Recalculate progress
    printer.action("Recalculating progress...")
    recalculate_progress(spec_data)

    # Save JSON spec
    printer.action("Saving JSON spec...")
    if not save_json_spec(spec_id, specs_dir, spec_data, backup=True):
        printer.error("Failed to save JSON spec")
        return False

    printer.success(f"Task {task_id} unblocked and set to 'pending'")
    printer.info("You can now mark it as 'in_progress' to resume work")
    return True
