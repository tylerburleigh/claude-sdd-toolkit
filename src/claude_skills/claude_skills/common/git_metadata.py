"""Git utility functions for SDD toolkit.

This module provides utilities for git operations including finding repository roots,
checking working tree status, parsing git status output, and managing commits.
All git commands execute with subprocess.run and include basic error handling.
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


def show_commit_preview(repo_root: Path, printer=None) -> Dict[str, List[str]]:
    """Display uncommitted files grouped by status with staging instructions.

    Uses parse_git_status() to get file changes and groups them by type
    (modified, added, deleted, untracked) with emoji markers for better visibility.

    Args:
        repo_root: Path to git repository root
        printer: Optional PrettyPrinter instance for output. If None, creates one.

    Returns:
        Dictionary with status categories as keys and file lists as values:
        {
            'staged_modified': [...],
            'unstaged_modified': [...],
            'added': [...],
            'deleted': [...],
            'untracked': [...]
        }

    Example:
        >>> show_commit_preview(Path('/repo'))
        📝 Modified (2):
          • src/main.py
          • lib/utils.py

        ✨ Added (1):
          • tests/new_test.py

        To stage all changes: git add .
        To stage specific files: git add <file>
    """
    from claude_skills.common.printer import PrettyPrinter

    if printer is None:
        printer = PrettyPrinter()

    # Get parsed status
    files = parse_git_status(repo_root)

    if not files:
        printer.info("No uncommitted changes")
        return {}

    # Group files by status category
    categories = {
        'staged_modified': [],      # M  (staged modification)
        'unstaged_modified': [],    #  M (unstaged modification)
        'both_modified': [],        # MM (staged and unstaged)
        'added': [],                # A  (added/new, staged)
        'deleted_staged': [],       # D  (deleted, staged)
        'deleted_unstaged': [],     #  D (deleted, unstaged)
        'untracked': [],            # ?? (untracked)
        'renamed': [],              # R  (renamed)
        'copied': [],               # C  (copied)
        'other': []                 # Other status codes
    }

    # Categorize each file
    for file_info in files:
        status = file_info['status']
        path = file_info['path']

        if status == 'M ':
            categories['staged_modified'].append(path)
        elif status == ' M':
            categories['unstaged_modified'].append(path)
        elif status == 'MM':
            categories['both_modified'].append(path)
        elif status == 'A ' or status.startswith('A'):
            categories['added'].append(path)
        elif status == 'D ':
            categories['deleted_staged'].append(path)
        elif status == ' D':
            categories['deleted_unstaged'].append(path)
        elif status == '??':
            categories['untracked'].append(path)
        elif status == 'R ' or status.startswith('R'):
            categories['renamed'].append(path)
        elif status == 'C ' or status.startswith('C'):
            categories['copied'].append(path)
        else:
            categories['other'].append(path)

    # Display grouped files with emojis
    printer.blank()
    printer.header("Uncommitted Changes")

    displayed_any = False

    if categories['staged_modified']:
        printer.result("📝 Staged (Modified)", f"{len(categories['staged_modified'])} file(s)")
        for path in categories['staged_modified']:
            printer.item(path, indent=1)
        printer.blank()
        displayed_any = True

    if categories['added']:
        printer.result("✨ Staged (Added)", f"{len(categories['added'])} file(s)")
        for path in categories['added']:
            printer.item(path, indent=1)
        printer.blank()
        displayed_any = True

    if categories['deleted_staged']:
        printer.result("❌ Staged (Deleted)", f"{len(categories['deleted_staged'])} file(s)")
        for path in categories['deleted_staged']:
            printer.item(path, indent=1)
        printer.blank()
        displayed_any = True

    if categories['unstaged_modified']:
        printer.result("📝 Unstaged (Modified)", f"{len(categories['unstaged_modified'])} file(s)")
        for path in categories['unstaged_modified']:
            printer.item(path, indent=1)
        printer.blank()
        displayed_any = True

    if categories['deleted_unstaged']:
        printer.result("❌ Unstaged (Deleted)", f"{len(categories['deleted_unstaged'])} file(s)")
        for path in categories['deleted_unstaged']:
            printer.item(path, indent=1)
        printer.blank()
        displayed_any = True

    if categories['both_modified']:
        printer.result("📝 Modified (Staged + Unstaged)", f"{len(categories['both_modified'])} file(s)")
        for path in categories['both_modified']:
            printer.item(path, indent=1)
        printer.blank()
        displayed_any = True

    if categories['untracked']:
        printer.result("❓ Untracked", f"{len(categories['untracked'])} file(s)")
        for path in categories['untracked']:
            printer.item(path, indent=1)
        printer.blank()
        displayed_any = True

    if categories['renamed']:
        printer.result("🔄 Renamed", f"{len(categories['renamed'])} file(s)")
        for path in categories['renamed']:
            printer.item(path, indent=1)
        printer.blank()
        displayed_any = True

    if categories['copied']:
        printer.result("📋 Copied", f"{len(categories['copied'])} file(s)")
        for path in categories['copied']:
            printer.item(path, indent=1)
        printer.blank()
        displayed_any = True

    if categories['other']:
        printer.result("❔ Other", f"{len(categories['other'])} file(s)")
        for path in categories['other']:
            printer.item(path, indent=1)
        printer.blank()
        displayed_any = True

    # Show staging instructions
    if displayed_any:
        printer.info("To stage all changes: git add .")
        printer.info("To stage specific files: git add <file>")
        printer.info("To commit staged changes: git commit -m \"message\"")

    return categories


def show_commit_preview_and_wait(
    repo_root: Path,
    spec_id: str,
    task_id: str,
    printer=None
) -> None:
    """Show uncommitted file preview and exit for agent-controlled staging (Step 1).

    This is step 1 of the two-step commit workflow. It displays uncommitted files
    grouped by status, then exits to allow the agent to stage files using git add.
    After staging, the agent should call create_commit_from_staging() to complete
    the commit (step 2).

    Workflow:
    1. Agent calls this function to see what files have changed
    2. Agent reviews changes and decides which files to stage
    3. Agent uses git add commands to stage selected files
    4. Agent calls create_commit_from_staging() to create the commit

    Args:
        repo_root: Path to git repository root
        spec_id: Specification ID (e.g., 'user-auth-2025-10-24-001')
        task_id: Task ID (e.g., 'task-2-1')
        printer: Optional PrettyPrinter instance for output. If None, creates one.

    Returns:
        None (displays output and exits)

    Example:
        >>> show_commit_preview_and_wait(Path('/repo'), 'user-auth-001', 'task-2-1')
        Uncommitted Changes
        📝 Modified (2):
          • src/main.py
          • lib/utils.py

        To stage files: git add <file>
        After staging, create commit with: sdd create-task-commit user-auth-001 task-2-1
    """
    from claude_skills.common.printer import PrettyPrinter

    if printer is None:
        printer = PrettyPrinter()

    # Check for uncommitted changes
    files = parse_git_status(repo_root)

    if not files:
        printer.info("No uncommitted changes")
        return

    # Show the preview (grouped by status with emojis)
    show_commit_preview(repo_root, printer)

    # Display next step instruction
    printer.blank()
    printer.info(f"After staging files, create commit with:")
    printer.result("Command", f"sdd create-task-commit {spec_id} {task_id}")


def create_commit_from_staging(
    repo_root: Path,
    spec_id: str,
    task_id: str,
    printer=None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Create commit from currently staged files (Step 2 of two-step workflow).

    This is step 2 of the two-step commit workflow. After the agent has staged
    files using git add, this function creates a commit with those staged files.

    Workflow:
    1. Agent calls show_commit_preview_and_wait() to see changes (step 1)
    2. Agent stages selected files with git add
    3. Agent calls this function to create the commit (step 2)

    Args:
        repo_root: Path to git repository root
        spec_id: Specification ID (e.g., 'user-auth-2025-10-24-001')
        task_id: Task ID (e.g., 'task-2-1')
        printer: Optional PrettyPrinter instance for output. If None, creates one.

    Returns:
        Tuple of (success, commit_sha, error_msg):
        - success: True if commit created successfully, False otherwise
        - commit_sha: Full commit SHA if successful, None otherwise
        - error_msg: Error message if failed, None if successful

    Example:
        >>> create_commit_from_staging(Path('/repo'), 'user-auth-001', 'task-2-1')
        (True, 'a1b2c3d4e5f6...', None)

        >>> # No files staged:
        >>> create_commit_from_staging(Path('/repo'), 'user-auth-001', 'task-2-1')
        (False, None, 'No files staged for commit')
    """
    from claude_skills.common.printer import PrettyPrinter

    if printer is None:
        printer = PrettyPrinter()

    # Check if there are files staged
    staged_files = get_staged_files(repo_root)

    if not staged_files:
        error_msg = "No files staged for commit"
        printer.error(error_msg)
        printer.info("Stage files with: git add <file>")
        return (False, None, error_msg)

    # Show what will be committed
    printer.blank()
    printer.header("Creating Commit")
    printer.result("Task", task_id)
    printer.result("Staged Files", f"{len(staged_files)} file(s)")
    for file_path in staged_files:
        printer.item(file_path, indent=1)

    # Create commit message
    commit_message = f"{task_id}: Implement task from spec {spec_id}"

    try:
        # Execute git commit
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )

        # Extract commit SHA from output
        # Git commit output typically includes "[branch commit_sha]" in first line
        output_lines = result.stdout.strip().split('\n')
        commit_sha = None

        for line in output_lines:
            # Look for pattern like "[main a1b2c3d]" or "[branch a1b2c3d]"
            if '[' in line and ']' in line:
                # Extract text between brackets
                bracket_content = line[line.find('[')+1:line.find(']')]
                parts = bracket_content.split()
                if len(parts) >= 2:
                    # Second part is the abbreviated SHA
                    commit_sha = parts[1]
                    break

        # If we couldn't parse SHA from output, get it from git log
        if not commit_sha:
            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            commit_sha = sha_result.stdout.strip()

        printer.blank()
        printer.success(f"Commit created: {commit_sha}")
        return (True, commit_sha, None)

    except subprocess.TimeoutExpired:
        error_msg = "Git commit command timed out"
        printer.error(error_msg)
        logger.warning(f"Git commit timed out at {repo_root}")
        return (False, None, error_msg)

    except subprocess.CalledProcessError as e:
        error_msg = f"Git commit failed: {e.stderr.strip()}"
        printer.error(error_msg)
        logger.warning(f"Git commit failed at {repo_root}: {e.stderr}")
        return (False, None, error_msg)

    except FileNotFoundError:
        error_msg = "Git command not found - is git installed?"
        printer.error(error_msg)
        logger.error("Git command not found")
        return (False, None, error_msg)

    except Exception as e:
        error_msg = f"Unexpected error creating commit: {type(e).__name__}"
        printer.error(error_msg)
        logger.warning(f"Unexpected error creating commit: {e}")
        return (False, None, error_msg)


def get_staged_files(repo_root: Path) -> List[str]:
    """Get list of files currently staged for commit.

    Runs 'git diff --cached --name-only' to get files in the staging area.

    Args:
        repo_root: Path to git repository root

    Returns:
        List of file paths (relative to repo root) that are currently staged.
        Returns empty list if no files are staged or if an error occurs.

    Example:
        >>> get_staged_files(Path('/repo'))
        ['src/main.py', 'tests/test_main.py']
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )

        output = result.stdout.strip()

        if not output:
            return []

        # Split by newlines to get list of files
        files = [line.strip() for line in output.split('\n') if line.strip()]
        logger.debug(f"Found {len(files)} staged file(s)")
        return files

    except subprocess.TimeoutExpired:
        logger.warning(f"Git diff check timed out at {repo_root}")
        return []

    except subprocess.CalledProcessError as e:
        logger.warning(f"Git diff check failed at {repo_root}: {e.stderr}")
        return []

    except FileNotFoundError:
        logger.error("Git command not found - is git installed?")
        return []

    except Exception as e:
        logger.warning(f"Unexpected error checking staged files: {e}")
        return []
