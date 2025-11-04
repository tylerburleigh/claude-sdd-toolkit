"""Context gathering functions for AI-powered PR generation.

This module collects all relevant information needed for generating comprehensive
PR descriptions: spec metadata, git diffs, commit history, and journal entries.
"""

from __future__ import annotations

import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from claude_skills.common.spec import load_json_spec
from claude_skills.common.git_metadata import find_git_root

logger = logging.getLogger(__name__)


def get_spec_git_diffs(repo_root: Path, base_branch: str, max_size_kb: int = 50) -> str:
    """Get git diff between current branch and base branch.

    Args:
        repo_root: Path to repository root directory
        base_branch: Base branch name (e.g., 'main', 'develop')
        max_size_kb: Maximum diff size in KB (truncate if larger)

    Returns:
        Git diff output as string, or empty string if error occurs.
        Large diffs (>max_size_kb) are truncated with a summary message.
    """
    try:
        result = subprocess.run(
            ['git', 'diff', f'{base_branch}...HEAD'],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
            timeout=30
        )

        if result.returncode != 0:
            logger.warning(f"Git diff failed: {result.stderr}")
            return ""

        diff_output = result.stdout

        # Check size and truncate if necessary
        diff_size_kb = len(diff_output.encode('utf-8')) / 1024
        if diff_size_kb > max_size_kb:
            logger.info(f"Diff size ({diff_size_kb:.1f}KB) exceeds limit ({max_size_kb}KB), truncating")
            # Get file-level summary instead
            result = subprocess.run(
                ['git', 'diff', '--stat', f'{base_branch}...HEAD'],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
                timeout=10
            )

            if result.returncode == 0:
                return (
                    f"[Diff too large ({diff_size_kb:.1f}KB), showing summary instead]\n\n"
                    f"{result.stdout}\n\n"
                    f"[Full diff omitted for brevity]"
                )
            else:
                return f"[Diff too large ({diff_size_kb:.1f}KB), summary unavailable]"

        return diff_output

    except subprocess.TimeoutExpired:
        logger.warning("Git diff timed out (>30s)")
        return "[Git diff timed out]"
    except Exception as e:
        logger.warning(f"Failed to get git diff: {e}")
        return ""


def get_commit_history(repo_root: Path, base_branch: str) -> List[Dict[str, str]]:
    """Query git for commit history between base branch and current HEAD.

    Args:
        repo_root: Path to repository root directory
        base_branch: Base branch name (e.g., 'main', 'develop')

    Returns:
        List of commit dictionaries with keys: sha, message, timestamp.
        Returns empty list if no commits found or on error.
    """
    try:
        result = subprocess.run(
            ["git", "log", f"{base_branch}...HEAD", "--format=%H|%s|%aI", "--reverse"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
            check=True
        )

        commits = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            parts = line.split('|', 2)
            if len(parts) >= 3:
                commits.append({
                    'sha': parts[0],
                    'message': parts[1],
                    'timestamp': parts[2]
                })

        return commits

    except subprocess.TimeoutExpired:
        logger.warning("Git log command timed out")
        return []
    except subprocess.CalledProcessError as e:
        logger.warning(f"Failed to get git log: {e}")
        return []
    except Exception as e:
        logger.warning(f"Unexpected error getting commit history: {e}")
        return []


def get_journal_entries(
    spec_data: Dict[str, Any],
    task_id: Optional[str] = None,
    include_internal: bool = False
) -> List[Dict[str, Any]]:
    """Extract journal entries from spec.

    Args:
        spec_data: Loaded spec JSON data
        task_id: Optional task ID to filter by
        include_internal: If True, include internal entries (default: False)

    Returns:
        List of journal entry dictionaries. Each entry contains:
        - timestamp: ISO format timestamp
        - entry_type: Type of entry (e.g., 'status_change', 'note')
        - title: Entry title
        - content: Entry content
        - task_id: Associated task ID (if any)
    """
    journals = spec_data.get('journal', [])

    # Filter by task_id if specified
    if task_id:
        journals = [j for j in journals if j.get('task_id') == task_id]

    # Filter out internal entries unless explicitly requested
    if not include_internal:
        journals = [j for j in journals if j.get('entry_type') != 'internal']

    return journals


def get_completed_tasks(spec_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get all completed tasks from spec hierarchy.

    Args:
        spec_data: Loaded spec JSON data

    Returns:
        List of task dictionaries with keys: id, title, metadata.
        Only includes tasks with status='completed'.
    """
    hierarchy = spec_data.get('hierarchy', {})
    tasks = []

    for node_id, node in hierarchy.items():
        if node.get('type') == 'task' and node.get('status') == 'completed':
            tasks.append({
                'id': node_id,
                'title': node.get('title', node_id),
                'metadata': node.get('metadata', {}),
                'file_path': node.get('metadata', {}).get('file_path', ''),
                'changes': node.get('metadata', {}).get('changes', ''),
            })

    return tasks


def get_phase_summary(spec_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get phase completion summary from spec hierarchy.

    Args:
        spec_data: Loaded spec JSON data

    Returns:
        List of phase dictionaries with keys:
        - id: Phase node ID
        - title: Phase title
        - status: Phase status (completed/in_progress/pending)
        - completed_tasks: Number of completed tasks
        - total_tasks: Total number of tasks
        - completion_percentage: Percentage complete (0-100)
    """
    hierarchy = spec_data.get('hierarchy', {})
    phases = []

    for node_id, node in hierarchy.items():
        if node.get('type') == 'phase':
            completed = node.get('completed_tasks', 0)
            total = node.get('total_tasks', 0)
            percentage = int((completed / total * 100)) if total > 0 else 0

            phases.append({
                'id': node_id,
                'title': node.get('title', node_id),
                'status': node.get('status', 'unknown'),
                'completed_tasks': completed,
                'total_tasks': total,
                'completion_percentage': percentage,
                'purpose': node.get('metadata', {}).get('purpose', ''),
            })

    return phases


def gather_pr_context(
    spec_id: str,
    spec_path: Path,
    specs_dir: Path,
    max_diff_size_kb: int = 50
) -> Dict[str, Any]:
    """Gather all context needed for AI-powered PR generation.

    This is the main orchestrator function that collects:
    - Spec metadata (title, description, objectives)
    - Completed tasks and phases
    - Git commit history
    - Journal entries (implementation notes)
    - Git diffs showing code changes

    Args:
        spec_id: Specification ID
        spec_path: Path to spec file
        specs_dir: Path to specs directory
        max_diff_size_kb: Maximum diff size in KB before truncation

    Returns:
        Dictionary with all collected context:
        - spec_data: Full spec JSON
        - metadata: Spec metadata section
        - commits: List of commit dicts
        - journals: List of journal entries
        - tasks: List of completed tasks
        - phases: List of phase summaries
        - git_diff: String of git diff output
        - branch_name: Feature branch name
        - base_branch: Base branch name
        - repo_root: Repository root path
        - spec_id: Specification ID
        - spec_path: Path to spec file

    Raises:
        FileNotFoundError: If spec file not found
        ValueError: If required git metadata missing
    """
    # Load spec data
    spec_data = load_json_spec(spec_id, specs_dir)
    if not spec_data:
        raise FileNotFoundError(f"Spec file not found: {spec_id}")

    # Find repository root
    repo_root = find_git_root(spec_path.parent)
    if not repo_root:
        raise ValueError("Git repository not found")

    # Query git for current branch
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        branch_name = result.stdout.strip()
        if not branch_name:
            raise ValueError("Could not determine current branch")
    except Exception as e:
        raise ValueError(f"Failed to get current branch: {e}")

    # Get base branch from git config or default to main
    try:
        result = subprocess.run(
            ["git", "config", "--get", f"branch.{branch_name}.base"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10
        )
        base_branch = result.stdout.strip() or 'main'
    except Exception:
        # If git config fails, try to detect from common base branches
        for candidate in ['main', 'master', 'develop']:
            try:
                subprocess.run(
                    ["git", "rev-parse", "--verify", candidate],
                    cwd=repo_root,
                    capture_output=True,
                    timeout=10,
                    check=True
                )
                base_branch = candidate
                break
            except Exception:
                continue
        else:
            base_branch = 'main'  # Final fallback

    # Gather git diff and commit history
    git_diff = get_spec_git_diffs(repo_root, base_branch, max_diff_size_kb)
    commits = get_commit_history(repo_root, base_branch)

    # Gather all context
    context = {
        'spec_data': spec_data,
        'metadata': spec_data.get('metadata', {}),
        'commits': commits,
        'journals': get_journal_entries(spec_data, include_internal=False),
        'tasks': get_completed_tasks(spec_data),
        'phases': get_phase_summary(spec_data),
        'git_diff': git_diff,
        'branch_name': branch_name,
        'base_branch': base_branch,
        'repo_root': repo_root,
        'spec_id': spec_id,
        'spec_path': spec_path,
    }

    logger.info(f"Gathered PR context for {spec_id}:")
    logger.info(f"  - {len(context['commits'])} commits")
    logger.info(f"  - {len(context['journals'])} journal entries")
    logger.info(f"  - {len(context['tasks'])} completed tasks")
    logger.info(f"  - {len(context['phases'])} phases")
    logger.info(f"  - Git diff size: {len(git_diff)} bytes")

    return context
