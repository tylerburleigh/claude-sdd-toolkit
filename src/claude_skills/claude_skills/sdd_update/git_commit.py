"""Git commit integration for sdd-update workflows.

Provides utilities for automatic git commits after task/phase completion based
on configured commit cadence preferences.
"""

from __future__ import annotations

import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, Any

from claude_skills.common.git_metadata import find_git_root, create_commit_from_staging
from claude_skills.common.git_config import is_git_enabled, get_git_setting

logger = logging.getLogger(__name__)


def should_offer_commit(
    spec_data: Dict[str, Any],
    event_type: str = "task"
) -> bool:
    """Check if commit should be offered based on commit cadence preference.

    Args:
        spec_data: JSON spec file data (unused, kept for backward compatibility)
        event_type: Type of completion event - "task" or "phase"

    Returns:
        True if commit should be offered for this event type, False otherwise
    """
    # Get commit cadence preference from git_config.json
    commit_cadence = get_git_setting('commit_cadence', default='task')

    # Determine if we should offer commit based on cadence
    # - "task": Commit after each task completion
    # - "phase": Commit after each phase completion
    # - "manual": Never auto-commit
    if event_type == "task":
        return commit_cadence == "task"
    elif event_type == "phase":
        return commit_cadence == "phase"

    # For manual or unknown event types, don't offer commit
    return False


def has_uncommitted_changes(repo_root: Path) -> Tuple[bool, str]:
    """Check if there are uncommitted changes in the git repository.

    Args:
        repo_root: Path to repository root directory

    Returns:
        Tuple of (has_changes: bool, status_output: str)
        - has_changes: True if there are uncommitted changes, False otherwise
        - status_output: Output from git status --porcelain
    """
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            logger.warning(f"git status failed: {result.stderr}")
            return False, ""

        status_output = result.stdout.strip()
        has_changes = bool(status_output)

        return has_changes, status_output

    except Exception as e:
        logger.warning(f"Failed to check git status: {e}")
        return False, ""


def generate_commit_message(task_id: str, task_title: str) -> str:
    """Generate commit message from task metadata.

    Args:
        task_id: Task identifier (e.g., "task-2-3")
        task_title: Human-readable task title

    Returns:
        Formatted commit message: "{task-id}: {task-title}"
    """
    return f"{task_id}: {task_title}"


def check_git_commit_readiness(
    spec_data: Dict[str, Any],
    spec_path: Path,
    event_type: str = "task"
) -> Optional[Dict[str, Any]]:
    """Check if git commit workflow should be triggered.

    This is the main entry point that orchestrates all git commit checks:
    1. Check if git integration is enabled
    2. Find repository root
    3. Check commit cadence preference
    4. Check for uncommitted changes

    Args:
        spec_data: JSON spec file data
        spec_path: Path to spec file
        event_type: Type of completion event - "task" or "phase"

    Returns:
        Dict with commit readiness info if commit should be offered:
        {
            "should_commit": True,
            "repo_root": Path to repository,
            "status_output": Git status output,
            "commit_cadence": Configured cadence
        }

        Returns None if commit should not be offered.
    """
    # Step 1: Find repository root
    repo_root = find_git_root(spec_path.parent)
    if repo_root is None:
        logger.debug("No git repository found, skipping commit workflow")
        return None

    # Step 2: Check if git integration is enabled
    if not is_git_enabled(repo_root):
        logger.debug("Git integration is disabled, skipping commit workflow")
        return None

    # Step 3: Check commit cadence preference
    if not should_offer_commit(spec_data, event_type):
        logger.debug(f"Commit cadence does not match event type '{event_type}', skipping commit")
        return None

    # Step 4: Check for uncommitted changes
    has_changes, status_output = has_uncommitted_changes(repo_root)
    if not has_changes:
        logger.debug("No uncommitted changes found, skipping commit")
        return None

    # All checks passed - commit should be offered
    commit_cadence = get_git_setting('commit_cadence', default='task')

    return {
        "should_commit": True,
        "repo_root": repo_root,
        "status_output": status_output,
        "commit_cadence": commit_cadence
    }


def stage_and_commit(
    repo_root: Path,
    commit_message: str
) -> Tuple[bool, Optional[str], str]:
    """Stage all changes and create a commit.

    This function maintains backward compatibility by automatically staging all
    changes (git add --all) and then creating a commit. It now uses the new
    create_commit_from_staging() workflow internally.

    Args:
        repo_root: Path to repository root directory
        commit_message: Commit message to use

    Returns:
        Tuple of (success: bool, commit_sha: Optional[str], error_message: str)
        - success: True if commit succeeded, False otherwise
        - commit_sha: SHA of created commit if successful, None otherwise
        - error_message: Error message if failed, empty string if successful
    """
    try:
        # Step 1: Stage all changes with git add --all
        add_result = subprocess.run(
            ['git', 'add', '--all'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False
        )

        if add_result.returncode != 0:
            error_msg = f"git add failed: {add_result.stderr}"
            logger.warning(error_msg)
            return False, None, error_msg

        # Step 2: Create commit using the new workflow
        # Note: create_commit_from_staging expects spec_id and task_id for commit message,
        # but we have a custom commit_message. We'll use git commit directly to preserve
        # the exact commit message format while still validating staging area.
        from claude_skills.common.git_metadata import get_staged_files

        # Check if there are files staged
        staged_files = get_staged_files(repo_root)
        if not staged_files:
            error_msg = "No files staged for commit (working tree clean)"
            logger.info(error_msg)
            return False, None, error_msg

        # Create commit with custom message
        commit_result = subprocess.run(
            ['git', 'commit', '-m', commit_message],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False
        )

        if commit_result.returncode != 0:
            error_msg = f"git commit failed: {commit_result.stderr}"
            logger.warning(error_msg)
            return False, None, error_msg

        # Get commit SHA
        sha_result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False
        )

        if sha_result.returncode != 0:
            logger.warning("Failed to get commit SHA, but commit succeeded")
            # Commit succeeded even if we couldn't get SHA
            return True, None, ""

        commit_sha = sha_result.stdout.strip()
        logger.info(f"Successfully created commit: {commit_sha[:8]}")

        return True, commit_sha, ""

    except Exception as e:
        error_msg = f"Git commit workflow failed: {e}"
        logger.warning(error_msg)
        return False, None, error_msg
