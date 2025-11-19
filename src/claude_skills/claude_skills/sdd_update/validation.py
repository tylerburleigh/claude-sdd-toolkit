"""
JSON spec validation and reporting operations for SDD workflows.
"""

from pathlib import Path
from typing import Optional, Dict, List, Union

# Import from sdd-common
from claude_skills.common.spec import load_json_spec
from claude_skills.common.progress import get_progress_summary, list_phases, get_task_counts_by_status
from claude_skills.common.printer import PrettyPrinter
from claude_skills.common.dependency_analysis import find_circular_dependencies
from claude_skills.common.hierarchy_validation import validate_spec_hierarchy
from claude_skills.common.completion import check_spec_completion

# Import panel-based status report
from claude_skills.sdd_update.status_report import print_status_report


def validate_spec(
    spec_id: str,
    specs_dir: Path,
    printer: Optional[PrettyPrinter] = None
) -> bool:
    """
    Validate JSON spec consistency using comprehensive hierarchy validator.

    Checks for:
    - Valid JSON structure
    - Required fields present
    - Parent-child relationships valid
    - No orphaned nodes
    - No circular dependencies
    - Progress calculations correct

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs/active directory
        printer: Optional printer for output

    Returns:
        True if valid, False if issues found
    """
    if not printer:
        printer = PrettyPrinter()

    printer.action("Validating JSON spec...")

    # Load spec (includes basic validation)
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return False

    # Use comprehensive hierarchy validator
    validation = validate_spec_hierarchy(spec_data)

    # Collect all errors
    all_errors = (
        validation.structure_errors +
        validation.hierarchy_errors +
        validation.node_errors
    )

    # Report results
    if not validation.is_valid():
        printer.error(f"Found {len(all_errors)} validation issue(s):")
        for error in all_errors[:10]:  # Show first 10 errors
            printer.detail(error)
        if len(all_errors) > 10:
            printer.detail(f"... and {len(all_errors) - 10} more errors")
        return False
    else:
        printer.success("JSON spec file is valid")
        return True


def get_status_report(
    spec_id: str,
    specs_dir: Path,
    printer: Optional[PrettyPrinter] = None
) -> Optional[Dict]:
    """
    Generate comprehensive status report.

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs/active directory
        printer: Optional printer for output (None = JSON mode, no printing)

    Returns:
        Dictionary with status information, or None on error
    """
    # Load spec
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return None

    # Get overall progress
    progress = get_progress_summary(spec_data)

    # Get phase breakdown
    phases = list_phases(spec_data)

    # Get task counts
    task_counts = get_task_counts_by_status(spec_data)

    report = {
        "spec_id": spec_id,
        "overall_progress": progress,
        "phases": phases,
        "task_counts": task_counts
    }

    # Check for unjournaled tasks
    unjournaled = detect_unjournaled_tasks(spec_id, specs_dir, printer=None)
    unjournaled_count = len(unjournaled) if unjournaled else 0

    # Add to report
    report["unjournaled_tasks"] = unjournaled_count
    if unjournaled:
        report["unjournaled_task_list"] = unjournaled

    # Check if spec is complete
    completion_result = check_spec_completion(spec_data)

    # Add completion status to report
    report["completion_status"] = {
        "is_complete": completion_result["is_complete"],
        "percentage": completion_result["percentage"],
        "incomplete_tasks": completion_result["incomplete_tasks"],
        "can_finalize": completion_result["can_finalize"]
    }

    # Only print if printer was provided (not in JSON mode)
    if printer:
        # Use the new panel-based status report display
        title = f"Status Report: {progress['title']}"
        print_status_report(spec_data, title=title)

        # Add journaling warning if needed (not part of main dashboard)
        if unjournaled_count > 0:
            printer.warning(f"⚠️  {unjournaled_count} completed task(s) need journal entries")
            printer.detail(f"    Run 'check-journaling {spec_id}' for details")
            print()

        # Display completion status if relevant (not part of main dashboard)
        if completion_result["is_complete"]:
            printer.success("✅ Spec is complete! All tasks finished.")
            printer.detail("  Run 'sdd complete-spec' command to finalize and move to completed folder")
        elif completion_result["percentage"] >= 90:
            remaining = len(completion_result["incomplete_tasks"])
            printer.info(f"⏳ Almost there! {remaining} task(s) remaining")

    return report


def audit_spec(
    spec_id: str,
    specs_dir: Path,
    printer: Optional[PrettyPrinter] = None
) -> Dict:
    """
    Perform deep audit of JSON spec.

    More comprehensive than validate_spec, includes:
    - Circular dependency detection
    - Progress calculation verification
    - Metadata completeness checks

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs/active directory
        printer: Optional printer for output

    Returns:
        Dictionary with audit results
    """
    if printer:
        printer.action("Auditing JSON spec...")

    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return {"error": "Failed to load spec"}

    hierarchy = spec_data.get("hierarchy", {})
    issues = []
    warnings = []

    # Check for circular dependencies using shared function
    dep_result = find_circular_dependencies(spec_data)

    if dep_result["has_circular"]:
        for chain in dep_result["circular_chains"]:
            chain_str = " → ".join(chain)
            issues.append(f"Circular dependency detected: {chain_str}")

    if dep_result["orphaned_tasks"]:
        for orphan in dep_result["orphaned_tasks"]:
            issues.append(
                f"Task '{orphan['task']}' references missing dependency '{orphan['missing_dependency']}'"
            )

    # Check metadata completeness
    for node_id, node_data in hierarchy.items():
        if node_data.get("type") == "task":
            metadata = node_data.get("metadata", {})
            if not metadata.get("file_path"):
                warnings.append(f"Task '{node_id}' missing file_path in metadata")

    result = {
        "spec_id": spec_id,
        "validation_passed": len(issues) == 0,
        "issues": issues,
        "warnings": warnings
    }

    if printer:
        printer.info(f"Issues: {len(issues)}")
        printer.info(f"Warnings: {len(warnings)}")

        if issues:
            printer.error("Critical issues found:")
            for issue in issues:
                printer.detail(issue)

        if warnings:
            printer.warning("Warnings:")
            for warning in warnings[:5]:
                printer.detail(warning)

        if not issues and not warnings:
            printer.success("Audit passed with no issues")

    return result


def reconcile_state(
    spec_id: str,
    specs_dir: Path,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> Union[bool, Dict]:
    """
    Reconcile JSON spec by fixing inconsistent task statuses.

    Finds tasks where metadata.completed_at exists but status != "completed",
    and updates their status to match the metadata. This fixes issues where
    a task was marked complete but the status wasn't properly updated.

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs/active directory
        dry_run: If True, don't save changes
        printer: Optional printer for output

    Returns:
        Dictionary with reconciliation data when printer is None (JSON mode),
        or boolean for backward compatibility (True if successful, False otherwise)
    """
    from claude_skills.common.spec import save_json_spec
    from claude_skills.common.progress import recalculate_progress

    if printer:
        printer.action("Reconciling JSON spec...")

    # Load spec
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return False

    hierarchy = spec_data.get("hierarchy", {})
    fixes_made = []

    # Find inconsistencies
    for node_id, node_data in hierarchy.items():
        metadata = node_data.get("metadata", {})
        current_status = node_data.get("status")

        # Case 1: Has completed_at timestamp but status isn't completed
        if metadata.get("completed_at") and current_status != "completed":
            fixes_made.append({
                "node_id": node_id,
                "title": node_data.get("title", ""),
                "old_status": current_status,
                "new_status": "completed",
                "reason": "Has completed_at metadata"
            })
            if not dry_run:
                node_data["status"] = "completed"

        # Case 2: Has started_at but not completed_at, and status is completed
        elif metadata.get("started_at") and not metadata.get("completed_at") and current_status == "completed":
            fixes_made.append({
                "node_id": node_id,
                "title": node_data.get("title", ""),
                "old_status": current_status,
                "new_status": "in_progress",
                "reason": "Status completed but no completed_at timestamp"
            })
            if not dry_run:
                node_data["status"] = "in_progress"

    import json

    # Recalculate progress and detect changes (count mismatches, etc.)
    # We do this BEFORE reporting findings so we can report count fixes too
    if printer:
        printer.action("Recalculating progress...")

    # Capture state before recalculation to detect changes
    # (recalculate_progress modifies in-place)
    before_state = json.dumps(spec_data.get("hierarchy", {}), sort_keys=True)
    recalculate_progress(spec_data)
    after_state = json.dumps(spec_data.get("hierarchy", {}), sort_keys=True)
    
    if before_state != after_state:
        fixes_made.append({
            "node_id": "hierarchy",
            "title": "Global Progress",
            "old_status": "N/A",
            "new_status": "Recalculated",
            "reason": "Count mismatch or inconsistency detected and resolved"
        })

    # Prepare result data
    result_data = {
        "spec_id": spec_id,
        "fixes_applied": len(fixes_made),
        "fixes": fixes_made,
        "dry_run": dry_run
    }

    # Report findings (only if printer is provided)
    if not fixes_made:
        if printer:
            printer.success("No inconsistencies found - JSON spec is coherent")
        # Return data for JSON mode or boolean for backward compatibility
        return result_data if not printer else True

    if printer:
        printer.warning(f"Found {len(fixes_made)} inconsistencies:")
        for fix in fixes_made:
            printer.detail(f"{fix['node_id']} ({fix['title']})")
            printer.detail(f"  Status: {fix['old_status']} → {fix['new_status']}")
            printer.detail(f"  Reason: {fix['reason']}")

    if dry_run:
        if printer:
            printer.warning("DRY RUN - No changes saved")
        return result_data if not printer else True

    # Save JSON spec with backup
    if printer:
        printer.action("Saving reconciled spec...")
    if not save_json_spec(spec_id, specs_dir, spec_data, backup=True):
        if printer:
            printer.error("Failed to save JSON spec")
        result_data["error"] = "Failed to save spec"
        return result_data if not printer else False

    if printer:
        printer.success(f"Reconciled {len(fixes_made)} task statuses")
    return result_data if not printer else True


def detect_unjournaled_tasks(
    spec_id: str,
    specs_dir: Path,
    printer: Optional[PrettyPrinter] = None
) -> List[Dict]:
    """
    Find completed tasks that need journal entries.

    Returns list of tasks with:
    - task_id
    - title
    - completed_at timestamp
    - parent_id (for context)

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs directory
        printer: Optional printer for output

    Returns:
        List of unjournaled task dictionaries, or None on error
    """
    if not printer:
        printer = PrettyPrinter()

    # Load JSON spec
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return None

    hierarchy = spec_data.get("hierarchy", {})
    unjournaled_tasks = []

    # Find completed tasks that need journaling
    for node_id, node_data in hierarchy.items():
        status = node_data.get("status")
        metadata = node_data.get("metadata", {})
        node_type = node_data.get("type")

        # Only check actual tasks (not phases or groups)
        if node_type not in ["task", "verify"]:
            continue

        # Check if task is completed and needs journaling
        if status == "completed" and metadata.get("needs_journaling", False):
            unjournaled_tasks.append({
                "task_id": node_id,
                "title": node_data.get("title", ""),
                "completed_at": metadata.get("completed_at", "Unknown"),
                "parent_id": node_data.get("parent"),
                "type": node_type
            })

    return unjournaled_tasks
