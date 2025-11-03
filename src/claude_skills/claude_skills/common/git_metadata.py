"""Git metadata management and helper functions for SDD toolkit.

This module provides utilities for git operations and metadata synchronization.
All git commands execute with subprocess.run and include basic error handling.

Functions are organized into categories:
- Git Utilities: find_git_root, check_dirty_tree, parse_git_status, detect_git_drift
- Metadata Updates: update_branch_metadata, add_commit_metadata, update_pr_metadata
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

logger = logging.getLogger(__name__)


# ============================================================================
# Git Utility Functions
# ============================================================================

def find_git_root(start_path: Optional[Path] = None) -> Optional[Path]:
    """Find the git repository root by traversing up directories.

    Searches for a .git directory starting from start_path and moving up
    through parent directories until found or filesystem root is reached.

    Args:
        start_path: Path to start searching from. Defaults to current working directory.

    Returns:
        Path to git repository root (directory containing .git) if found, None otherwise
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()

    current = start_path

    # Traverse up directories looking for .git
    while True:
        git_dir = current / ".git"
        if git_dir.exists():
            logger.debug(f"Found git root at {current}")
            return current

        # Check if we've reached the filesystem root
        parent = current.parent
        if parent == current:
            # Reached root without finding .git
            logger.debug(f"No git root found starting from {start_path}")
            return None

        current = parent


def check_dirty_tree(repo_root: Path) -> Tuple[bool, str]:
    """Check if the working tree has uncommitted changes.

    Runs 'git status --porcelain' to detect any uncommitted changes,
    including staged, unstaged, and untracked files.

    Args:
        repo_root: Path to git repository root

    Returns:
        Tuple of (is_dirty, message):
        - is_dirty: True if there are uncommitted changes, False otherwise
        - message: Description of the dirty state or "Clean" if no changes
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )

        output = result.stdout.strip()

        if not output:
            return (False, "Clean")

        # Count types of changes
        lines = output.split('\n')
        staged = sum(1 for line in lines if line[0] in 'MADRC')
        unstaged = sum(1 for line in lines if line[1] in 'MD')
        untracked = sum(1 for line in lines if line.startswith('??'))

        # Build descriptive message
        parts = []
        if staged > 0:
            parts.append(f"{staged} staged")
        if unstaged > 0:
            parts.append(f"{unstaged} unstaged")
        if untracked > 0:
            parts.append(f"{untracked} untracked")

        message = f"Dirty: {', '.join(parts)}"
        return (True, message)

    except subprocess.TimeoutExpired:
        logger.warning(f"Git status check timed out at {repo_root}")
        return (True, "Unknown (timeout)")

    except subprocess.CalledProcessError as e:
        logger.warning(f"Git status failed at {repo_root}: {e.stderr}")
        return (True, f"Unknown (git error: {e.returncode})")

    except FileNotFoundError:
        logger.error("Git command not found - is git installed?")
        return (True, "Unknown (git not found)")

    except Exception as e:
        logger.warning(f"Unexpected error checking git status: {e}")
        return (True, f"Unknown (error: {type(e).__name__})")


def parse_git_status(repo_root: Path) -> List[Dict[str, str]]:
    """Parse git status output into structured list of file changes.

    Runs 'git status --porcelain' and parses the output into a list of
    dictionaries, where each dictionary represents a file with its status.

    Git porcelain format: "XY path"
    - X = index status (left column)
    - Y = worktree status (right column)

    Common status codes:
    - 'M ' = staged modification
    - ' M' = unstaged modification
    - 'MM' = staged AND unstaged modification
    - 'A ' = added (new file, staged)
    - 'D ' = deleted (staged)
    - ' D' = deleted (unstaged)
    - 'R ' = renamed (staged)
    - '??' = untracked file
    - 'AM' = added (staged) with unstaged modifications

    Args:
        repo_root: Path to git repository root

    Returns:
        List of dictionaries with keys:
        - 'status': Two-character status code (e.g., 'M ', '??', 'MM')
        - 'path': File path relative to repo root

        Returns empty list if there are no changes or if an error occurs.

    Example:
        >>> parse_git_status(Path('/repo'))
        [
            {'status': 'M ', 'path': 'src/main.py'},
            {'status': '??', 'path': 'test.txt'},
            {'status': 'MM', 'path': 'lib/utils.py'}
        ]
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )

        # Don't strip leading whitespace as git porcelain format uses leading spaces
        # for status codes (e.g., " M" means unstaged modification)
        output = result.stdout.rstrip()

        if not output:
            return []

        # Parse each line of porcelain output
        # Format: "XY PATH" where XY is 2-char status code, space, then path
        # Example: "M  file.py" means M (staged), space (unchanged in worktree), space separator, then path
        # Example: " M file.py" means space (not staged), M (modified in worktree), space separator, then path
        parsed_files = []
        for line in output.split('\n'):
            if len(line) < 3:
                # Invalid line, skip
                continue

            # First 2 characters are status code
            status = line[0:2]
            # Path starts at character 3 (after the space separator)
            path = line[3:]

            # Handle quoted paths (paths with special characters are quoted)
            if path.startswith('"') and path.endswith('"'):
                # Remove quotes - for simplicity, just strip them
                # Git uses C-style escaping in quotes, but for basic cases this works
                path = path[1:-1]

            parsed_files.append({
                'status': status,
                'path': path
            })

        logger.debug(f"Parsed {len(parsed_files)} file(s) from git status")
        return parsed_files

    except subprocess.TimeoutExpired:
        logger.warning(f"Git status parsing timed out at {repo_root}")
        return []

    except subprocess.CalledProcessError as e:
        logger.warning(f"Git status parsing failed at {repo_root}: {e.stderr}")
        return []

    except FileNotFoundError:
        logger.error("Git command not found - is git installed?")
        return []

    except Exception as e:
        logger.warning(f"Unexpected error parsing git status: {e}")
        return []


def detect_git_drift(spec: Dict[str, Any], repo_root: Path) -> List[str]:
    """Detect drift between spec metadata and actual git state.

    Compares the git metadata stored in the spec with the actual git repository state.
    Returns a list of warnings for any discrepancies found.

    This is a non-blocking check - warnings are informational and don't prevent operations.

    Args:
        spec: Specification dictionary containing metadata.git section
        repo_root: Path to git repository root

    Returns:
        List of warning messages (empty list if no drift detected)
    """
    warnings = []

    # Check if spec has git metadata
    git_metadata = spec.get('metadata', {}).get('git')
    if not git_metadata:
        # No git metadata in spec - not necessarily an error
        logger.debug("No git metadata in spec")
        return warnings

    # Get current branch from git
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        current_branch = result.stdout.strip()
    except subprocess.TimeoutExpired:
        warnings.append("Could not check current branch (timeout)")
        return warnings
    except subprocess.CalledProcessError as e:
        warnings.append(f"Could not check current branch (git error: {e.returncode})")
        return warnings
    except Exception as e:
        warnings.append(f"Could not check current branch ({type(e).__name__})")
        return warnings

    # Compare metadata.git.branch_name with current branch
    expected_branch = git_metadata.get('branch_name')
    if expected_branch and current_branch != expected_branch:
        warnings.append(
            f"Branch drift detected: spec expects '{expected_branch}' "
            f"but current branch is '{current_branch}'"
        )

    # Check if branch exists
    if expected_branch:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", expected_branch],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                warnings.append(f"Branch '{expected_branch}' does not exist in repository")
        except Exception:
            pass  # Don't add warnings for verification failures

    # Check base branch exists
    base_branch = git_metadata.get('base_branch')
    if base_branch:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", base_branch],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                warnings.append(f"Base branch '{base_branch}' does not exist in repository")
        except Exception:
            pass  # Don't add warnings for verification failures

    # Verify commits in metadata exist in repository
    commits = git_metadata.get('commits', [])
    if commits:
        missing_commits = []
        for commit in commits:
            sha = commit.get('sha')
            if sha:
                try:
                    result = subprocess.run(
                        ["git", "cat-file", "-t", sha],
                        cwd=repo_root,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode != 0:
                        missing_commits.append(sha[:8])
                except Exception:
                    pass  # Don't add warnings for individual commit checks

        if missing_commits:
            warnings.append(
                f"Commits in spec not found in repository: {', '.join(missing_commits)}"
            )

    if warnings:
        logger.warning(f"Git drift detected: {len(warnings)} warning(s)")
        for warning in warnings:
            logger.warning(f"  - {warning}")
    else:
        logger.debug("No git drift detected")

    return warnings


# ============================================================================
# Metadata Update Functions
# ============================================================================

def update_branch_metadata(
    spec: Dict[str, Any],
    branch_name: str,
    base_branch: str
) -> Dict[str, Any]:
    """Update git branch metadata in spec.

    Updates the metadata.git section with branch information. Creates the section
    if it doesn't exist. Preserves existing commits and PR metadata.

    Args:
        spec: Specification dictionary to update
        branch_name: Name of the feature branch (e.g., 'feat/user-auth-001')
        base_branch: Name of the base branch (e.g., 'main', 'develop')

    Returns:
        Updated spec dictionary (modified in-place, but also returned for convenience)
    """
    # Ensure metadata section exists
    if 'metadata' not in spec:
        spec['metadata'] = {}

    # Get or create git metadata section
    if 'git' not in spec['metadata']:
        spec['metadata']['git'] = {
            'branch_name': branch_name,
            'base_branch': base_branch,
            'commits': [],
            'pr': None
        }
        logger.info(f"Created git metadata section with branch '{branch_name}'")
    else:
        # Update existing git metadata
        git_meta = spec['metadata']['git']
        git_meta['branch_name'] = branch_name
        git_meta['base_branch'] = base_branch
        # Preserve commits and PR metadata if they exist
        if 'commits' not in git_meta:
            git_meta['commits'] = []
        if 'pr' not in git_meta:
            git_meta['pr'] = None
        logger.info(f"Updated git metadata: branch='{branch_name}', base='{base_branch}'")

    return spec


def add_commit_metadata(
    spec: Dict[str, Any],
    sha: str,
    message: str,
    task_id: str,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """Add a commit record to spec git metadata.

    Appends a new commit object to the metadata.git.commits array. Creates the
    git metadata section if it doesn't exist.

    Args:
        spec: Specification dictionary to update
        sha: Git commit SHA hash (full or abbreviated)
        message: Commit message
        task_id: Task ID associated with this commit (e.g., 'task-1-1')
        timestamp: ISO 8601 timestamp string (optional, will use current time if not provided)

    Returns:
        Updated spec dictionary (modified in-place, but also returned for convenience)
    """
    from datetime import datetime, timezone

    # Ensure metadata.git section exists
    if 'metadata' not in spec:
        spec['metadata'] = {}
    if 'git' not in spec['metadata']:
        spec['metadata']['git'] = {
            'branch_name': None,
            'base_branch': None,
            'commits': [],
            'pr': None
        }
        logger.warning("Git metadata section did not exist, created with defaults")

    # Ensure commits array exists
    if 'commits' not in spec['metadata']['git']:
        spec['metadata']['git']['commits'] = []

    # Generate timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()

    # Create commit object
    commit_obj = {
        'sha': sha,
        'message': message,
        'task_id': task_id,
        'timestamp': timestamp
    }

    # Append to commits array
    spec['metadata']['git']['commits'].append(commit_obj)
    logger.info(f"Added commit {sha[:8]} for task {task_id}")

    return spec


def update_pr_metadata(
    spec: Dict[str, Any],
    pr_url: str,
    pr_number: int,
    status: str = 'open'
) -> Dict[str, Any]:
    """Update pull request metadata in spec.

    Updates or creates the metadata.git.pr section with PR information.

    Args:
        spec: Specification dictionary to update
        pr_url: Full URL to the pull request
        pr_number: Pull request number
        status: PR status ('open', 'closed', 'merged') - defaults to 'open'

    Returns:
        Updated spec dictionary (modified in-place, but also returned for convenience)
    """
    from datetime import datetime, timezone

    # Ensure metadata.git section exists
    if 'metadata' not in spec:
        spec['metadata'] = {}
    if 'git' not in spec['metadata']:
        spec['metadata']['git'] = {
            'branch_name': None,
            'base_branch': None,
            'commits': [],
            'pr': None
        }
        logger.warning("Git metadata section did not exist, created with defaults")

    # Create or update PR object
    spec['metadata']['git']['pr'] = {
        'url': pr_url,
        'number': pr_number,
        'status': status,
        'created_at': datetime.now(timezone.utc).isoformat()
    }

    logger.info(f"Updated PR metadata: #{pr_number} ({status})")

    return spec
