"""
Spec lifecycle management operations for SDD workflows.

All operations work with JSON spec files only. No markdown files are used.
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone

# Import from sdd-common
from claude_skills.common.spec import load_json_spec, save_json_spec
from claude_skills.common.paths import ensure_directory, find_spec_file
from claude_skills.common.printer import PrettyPrinter

# Import from sdd_update
from claude_skills.sdd_update.time_tracking import aggregate_task_times
from claude_skills.sdd_update.git_pr import (
    check_pr_readiness,
    generate_pr_body,
    push_branch,
    create_pull_request,
)
from claude_skills.common.git_config import load_git_config


def move_spec(
    spec_file: Path,
    target_folder: str,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> bool:
    """
    Move a spec file between lifecycle folders.

    Args:
        spec_file: Path to current spec file
        target_folder: Target folder name (active, completed, archived)
        dry_run: If True, show move without executing
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    if not spec_file.exists():
        printer.error(f"Spec file not found: {spec_file}")
        return False

    valid_folders = ["active", "completed", "archived"]
    if target_folder not in valid_folders:
        printer.error(f"Invalid target folder '{target_folder}'. Must be one of: {', '.join(valid_folders)}")
        return False

    # Get specs directory (parent of current folder)
    current_folder = spec_file.parent
    specs_base = current_folder.parent
    target_path = specs_base / target_folder

    # Ensure target directory exists
    if not ensure_directory(target_path):
        printer.error(f"Could not create target directory: {target_path}")
        return False

    target_file = target_path / spec_file.name

    if target_file.exists():
        printer.error(f"File already exists at target: {target_file}")
        return False

    printer.info(f"Moving: {spec_file}")
    printer.info(f"To: {target_file}")

    if dry_run:
        printer.warning("DRY RUN - No changes made")
        return True

    try:
        shutil.move(str(spec_file), str(target_file))
        printer.success(f"Spec moved to {target_folder}/")
        return True
    except Exception as e:
        printer.error(f"Failed to move spec: {e}")
        return False


def move_spec_by_id(
    spec_id: str,
    target_folder: str,
    specs_dir: Path,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> bool:
    """
    Move a spec file between lifecycle folders using spec ID.

    Args:
        spec_id: Specification ID
        target_folder: Target folder name (active, completed, archived)
        specs_dir: Path to specs directory
        dry_run: If True, show move without executing
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    # Find the spec file by ID
    spec_file = find_spec_file(spec_id, specs_dir)
    if not spec_file:
        printer.error(f"Spec file not found: {spec_id}")
        return False

    # Call existing move_spec function
    return move_spec(spec_file, target_folder, dry_run, printer)


def activate_spec(
    spec_id: str,
    specs_dir: Path,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> bool:
    """
    Activate a pending spec by moving it to the active folder.

    Performs the following:
    1. Finds spec file in pending/ folder
    2. Updates metadata status to 'active'
    3. Adds activated_date timestamp
    4. Moves spec file to active/ folder

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs directory
        dry_run: If True, show changes without executing
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    # Check if spec exists and determine its current location
    current_spec_file = find_spec_file(spec_id, specs_dir)

    if not current_spec_file:
        printer.error(f"Spec file not found: {spec_id}")
        printer.detail(f"Searched in: pending/, active/, completed/, archived/")
        return False

    # Determine which folder the spec is currently in
    current_folder = current_spec_file.parent.name

    # Validate spec is in pending folder
    if current_folder == "active":
        printer.info(f"Spec is already active - no need to activate again.")
        return True
    elif current_folder == "completed":
        printer.error(f"Spec is already completed and cannot be activated.")
        printer.detail(f"Location: {current_spec_file}")
        return False
    elif current_folder == "archived":
        printer.error(f"Spec is archived and cannot be activated.")
        printer.detail(f"Location: {current_spec_file}")
        return False
    elif current_folder != "pending":
        printer.error(f"Spec is in unexpected location: {current_folder}/")
        printer.detail(f"Location: {current_spec_file}")
        return False

    # Spec is in pending folder - proceed with activation
    spec_file = current_spec_file

    # Load spec
    printer.action(f"Loading spec for {spec_id}...")
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return False

    # Update metadata
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if "metadata" not in spec_data:
        spec_data["metadata"] = {}

    spec_data["metadata"]["status"] = "active"
    spec_data["metadata"]["activated_date"] = timestamp

    # Update last_updated timestamp
    spec_data["last_updated"] = timestamp

    printer.info("Updating metadata:")
    printer.detail(f"status: active")
    printer.detail(f"activated_date: {timestamp}")

    if dry_run:
        printer.warning("DRY RUN - No changes made")
        return True

    # Save JSON spec file
    if not save_json_spec(spec_id, specs_dir, spec_data, backup=True):
        printer.error("Failed to save spec file with activation metadata")
        return False

    # Move to active folder
    printer.action("Moving spec to active/...")
    if not move_spec(spec_file, "active", dry_run=False, printer=printer):
        printer.error("Failed to move spec file")
        printer.warning("Metadata was updated but file was not moved")
        return False

    printer.success(f"Spec {spec_id} activated and moved to active/")
    return True


def _regenerate_documentation(specs_dir: Path, printer: PrettyPrinter) -> bool:
    """
    Regenerate codebase documentation.

    Args:
        specs_dir: Path to specs directory (used to locate project root)
        printer: Printer for output messages

    Returns:
        True if regeneration succeeded, False otherwise
    """
    # Determine project root and source directory
    project_root = specs_dir.parent
    source_dir = project_root / 'src'

    if not source_dir.exists():
        source_dir = project_root

    docs_dir = project_root / 'docs'

    printer.action("Regenerating codebase documentation...")

    try:
        result = subprocess.run(
            ['sdd', 'doc', 'generate', str(source_dir),
             '--output-dir', str(docs_dir)],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            printer.success("✅ Documentation regenerated successfully")
            return True
        else:
            printer.warning(f"⚠️  Documentation regeneration failed: {result.stderr}")
            printer.warning("Continuing with spec completion...")
            return False
    except subprocess.TimeoutExpired:
        printer.warning("⚠️  Documentation regeneration timed out (5 minutes)")
        printer.warning("Continuing with spec completion...")
        return False
    except Exception as e:
        printer.warning(f"⚠️  Error regenerating documentation: {e}")
        printer.warning("Continuing with spec completion...")
        return False


def complete_spec(
    spec_id: str,
    spec_file: Optional[Path],
    specs_dir: Path,
    skip_doc_regen: bool = False,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> bool:
    """
    Mark a spec as completed and move it to completed folder.

    Performs the following:
    1. Verifies all tasks are completed
    2. Updates JSON metadata (status, completed_date, actual_hours auto-calculated from tasks)
    3. Moves JSON spec file to completed/ folder
    4. Regenerates codebase documentation (unless skip_doc_regen is True)

    Args:
        spec_id: Specification ID
        spec_file: Path to JSON spec file (optional - will be auto-detected if not provided)
        specs_dir: Path to specs directory
        skip_doc_regen: If True, skip documentation regeneration
        dry_run: If True, show changes without executing
        printer: Optional printer for output

    Returns:
        True if successful, False otherwise
    """
    if not printer:
        printer = PrettyPrinter()

    # Find spec file if not provided
    if spec_file is None:
        spec_file = find_spec_file(spec_id, specs_dir)
        if not spec_file:
            printer.error(f"Spec file not found for {spec_id}")
            printer.error(f"Searched in: {specs_dir}/active, {specs_dir}/completed, {specs_dir}/archived")
            return False

    # Load and verify spec
    printer.action(f"Loading spec for {spec_id}...")
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        return False

    hierarchy = spec_data.get("hierarchy", {})

    # Check if all tasks are completed
    incomplete_tasks = []
    for node_id, node_data in hierarchy.items():
        if node_data.get("type") == "task" and node_data.get("status") != "completed":
            incomplete_tasks.append(f"{node_id}: {node_data.get('title', 'Unknown')}")

    if incomplete_tasks:
        printer.error(f"Cannot complete spec - {len(incomplete_tasks)} incomplete task(s):")
        for task in incomplete_tasks[:5]:  # Show first 5
            printer.detail(task)
        if len(incomplete_tasks) > 5:
            printer.detail(f"... and {len(incomplete_tasks) - 5} more")
        return False

    # Calculate completion progress
    spec_root = hierarchy.get("spec-root", {})
    total_tasks = spec_root.get("total_tasks", 0)
    completed_tasks = spec_root.get("completed_tasks", 0)

    printer.success(f"All {total_tasks} tasks completed!")

    # Update JSON metadata
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if "metadata" not in spec_data:
        spec_data["metadata"] = {}

    spec_data["metadata"]["status"] = "completed"
    spec_data["metadata"]["completed_date"] = timestamp

    # Auto-calculate from task-level actual_hours
    calculated_hours = aggregate_task_times(spec_id, specs_dir, printer)
    if calculated_hours:
        spec_data["metadata"]["actual_hours"] = calculated_hours

    # Update last_updated timestamp
    spec_data["last_updated"] = timestamp

    printer.info("Updating metadata:")
    printer.detail(f"status: completed")
    printer.detail(f"completed_date: {timestamp}")
    if "actual_hours" in spec_data["metadata"]:
        printer.detail(f"actual_hours: {spec_data['metadata']['actual_hours']} (auto-calculated)")

    if dry_run:
        printer.warning("DRY RUN - No changes made")
        return True

    # Save JSON spec file
    if not save_json_spec(spec_id, specs_dir, spec_data, backup=True):
        printer.error("Failed to save spec file with completion metadata")
        return False

    # Git PR workflow integration (after spec completion, before moving)
    # Check if PR workflow should be triggered
    pr_info = check_pr_readiness(spec_data, spec_file)

    if pr_info:
        repo_root = pr_info['repo_root']
        branch_name = pr_info['branch_name']
        base_branch = pr_info['base_branch']

        # Load git config to check PR preferences
        git_config = load_git_config(repo_root)
        ai_pr_enabled = git_config.get('ai_pr', {}).get('enabled', False)

        if ai_pr_enabled:
            # NEW: AI-powered PR creation via sdd-next skill handoff
            printer.info("")
            printer.header("="*70)
            printer.header("Spec Completion - Next Steps Available")
            printer.header("="*70)
            printer.info("")
            printer.info("Spec completed successfully. To determine next steps:")
            printer.info("")
            printer.result("  Skill(sdd-toolkit:sdd-next)", "Find next action")
            printer.info("")
            printer.detail(f"  Spec ID: {spec_id}")
            printer.detail(f"  Branch: {branch_name}")
            printer.detail(f"  Base: {base_branch}")
            printer.info("")
            printer.info("Suggested action: Create pull request")
            printer.info("")
            printer.info("sdd-next will:")
            printer.info("  1. Detect spec completion status")
            printer.info("  2. Suggest creating PR via sdd-pr skill")
            printer.info("  3. Guide you through PR creation workflow")
            printer.info("")
            printer.header("="*70)
            printer.info("")

            # Return True to signal handoff - agent will see output and invoke sdd-next
            # Spec will remain in active/ until next steps are taken
            return True
        else:
            # Existing auto_pr logic (backward compatible)
            printer.info("Git integration enabled - initiating PR workflow...")

            # Generate PR body from spec metadata
            pr_body = generate_pr_body(spec_data, repo_root, base_branch)
            pr_title = spec_data.get('metadata', {}).get('title', spec_id)

            # Push branch to remote
            printer.action(f"Pushing branch '{branch_name}' to remote...")
            push_success, push_error = push_branch(repo_root, branch_name)

            if push_success:
                printer.success(f"Branch '{branch_name}' pushed successfully")

                # Create PR via gh CLI
                printer.action("Creating pull request...")
                pr_success, pr_url, pr_number, pr_error = create_pull_request(
                    repo_root=repo_root,
                    title=pr_title,
                    body=pr_body,
                    base_branch=base_branch
                )

                if pr_success and pr_url and pr_number:
                    printer.success(f"Pull request created: {pr_url}")

                elif pr_error:
                    # Non-blocking failure - log warning but continue
                    printer.warning(f"PR creation failed: {pr_error}")
                    if "gh not found" in pr_error:
                        printer.info("Install GitHub CLI: https://cli.github.com/")
                    # Provide manual PR creation instructions
                    github_compare_url = f"https://github.com/{{owner}}/{{repo}}/compare/{branch_name}"
                    printer.info(f"Or create PR manually at: {github_compare_url}")

            elif push_error:
                # Non-blocking failure - log warning but continue
                printer.warning(f"Branch push failed: {push_error}")
                printer.info(f"Push manually with: git push -u origin {branch_name}")
                printer.info("Then create PR at: https://github.com/{{owner}}/{{repo}}/compare/{branch_name}")

    # Move to completed folder
    printer.action("Moving spec to completed/...")
    if not move_spec(spec_file, "completed", dry_run=False, printer=printer):
        printer.error("Failed to move spec file")
        printer.warning("Metadata was updated but file was not moved")
        return False

    printer.success(f"Spec {spec_id} marked as completed and moved to completed/")

    # Regenerate documentation unless skipped
    if not skip_doc_regen:
        _regenerate_documentation(specs_dir, printer)
        # Note: We don't fail the completion if doc regeneration fails
        # The spec completion is still successful

    return True
