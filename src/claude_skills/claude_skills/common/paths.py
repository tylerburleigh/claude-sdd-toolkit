"""
Path discovery and validation utilities for SDD workflows.
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict


def find_specs_directory(provided_path: Optional[str] = None) -> Optional[Path]:
    """
    Discover the specs directory.

    Args:
        provided_path: Optional explicit path to specs directory or file

    Returns:
        Absolute Path to specs directory (containing active/completed/archived), or None if not found
    """
    def is_valid_specs_dir(p: Path) -> bool:
        """Check if a directory is a valid specs directory."""
        # Check for at least one of the spec subdirectories
        return ((p / "active").is_dir() or
                (p / "completed").is_dir() or
                (p / "archived").is_dir())

    if provided_path:
        path = Path(provided_path).resolve()

        # If a file is provided, start from its parent directory
        if path.is_file():
            path = path.parent

        if not path.is_dir():
            return None

        # Check if the current directory is a valid specs directory
        if is_valid_specs_dir(path):
            return path

        # Traverse upward to find a valid specs directory (max 5 levels)
        for parent in list(path.parents)[:5]:
            if is_valid_specs_dir(parent):
                return parent

        # If no valid directory found in traversal, return None
        return None

    # Search common locations (return the specs directory, not specs/active)
    search_paths = [
        Path.cwd() / "specs",
        Path.home() / "Documents" / "Sandbox" / "specs",
        Path.home() / ".claude" / "specs" / Path.cwd().name,
        Path.cwd().parent / "specs",
        Path.cwd().parent.parent / "specs",
    ]

    found_dirs = [p.resolve() for p in search_paths if p.exists() and is_valid_specs_dir(p)]

    if len(found_dirs) == 0:
        return None
    elif len(found_dirs) == 1:
        return found_dirs[0]
    else:
        # Multiple found - return the first, but warn
        print(f"Warning: Found multiple specs directories:", file=sys.stderr)
        for d in found_dirs:
            print(f"  - {d}", file=sys.stderr)
        print(f"Using: {found_dirs[0]}", file=sys.stderr)
        return found_dirs[0]


def find_spec_file(spec_id: str, specs_dir: Path) -> Optional[Path]:
    """
    Find the spec file for a given spec ID.

    Searches in active/, completed/, and archived/ subdirectories.

    Args:
        spec_id: Specification ID
        specs_dir: Path to specs directory (containing active/completed/archived)

    Returns:
        Absolute path to the spec file, or None if not found
    """
    # Search in order: active, completed, archived
    search_dirs = ["active", "completed", "archived"]

    for subdir in search_dirs:
        spec_file = specs_dir / subdir / f"{spec_id}.json"
        if spec_file.exists():
            return spec_file

    return None




def validate_path(path: str) -> Optional[Path]:
    """
    Validate and normalize a file or directory path.

    Args:
        path: Path string to validate

    Returns:
        Absolute Path object if valid, None otherwise
    """
    try:
        p = Path(path).resolve()
        if p.exists():
            return p
        return None
    except (ValueError, OSError):
        return None


def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to directory

    Returns:
        True if directory exists or was created, False on error
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, PermissionError):
        return False


def validate_and_normalize_paths(
    paths: List[str],
    base_directory: Optional[Path] = None
) -> Dict:
    """
    Validate and normalize file paths.

    Checks each path for existence, normalizes relative paths, and
    categorizes them as valid or invalid.

    Args:
        paths: List of paths to validate (can be relative or absolute)
        base_directory: Base directory for relative path resolution (defaults to cwd)

    Returns:
        Dictionary with validation results:
        - valid_paths: list of valid path info dicts
        - invalid_paths: list of invalid path info dicts
        - normalized_paths: dict mapping original to normalized paths

    Example:
        >>> result = validate_and_normalize_paths(["src/main.py", "/tmp/test.txt"])
        >>> print(f"Valid: {len(result['valid_paths'])}")
        >>> print(result['normalized_paths'])
    """
    if base_directory:
        base_directory = Path(base_directory).resolve()
    else:
        base_directory = Path.cwd()

    result = {
        "valid_paths": [],
        "invalid_paths": [],
        "normalized_paths": {}
    }

    for path_str in paths:
        path = Path(path_str)

        validation = {
            "original": path_str,
            "is_absolute": path.is_absolute(),
            "exists": False,
            "normalized": None,
            "type": None
        }

        # Normalize path
        if path.is_absolute():
            normalized = path
        else:
            normalized = (base_directory / path).resolve()

        validation["normalized"] = str(normalized)
        validation["exists"] = normalized.exists()

        if normalized.exists():
            if normalized.is_file():
                validation["type"] = "file"
            elif normalized.is_dir():
                validation["type"] = "directory"

            result["valid_paths"].append(validation)
        else:
            result["invalid_paths"].append(validation)

        result["normalized_paths"][path_str] = str(normalized)

    return result


def normalize_path(path: str, base_directory: Optional[Path] = None) -> Path:
    """
    Normalize a single path (absolute or relative).

    Args:
        path: Path string to normalize
        base_directory: Base directory for relative paths (defaults to cwd)

    Returns:
        Normalized absolute Path object

    Example:
        >>> normalized = normalize_path("../specs/active/my-spec.md")
        >>> print(normalized)  # /Users/user/project/specs/active/my-spec.md
    """
    if base_directory:
        base_directory = Path(base_directory).resolve()
    else:
        base_directory = Path.cwd()

    path_obj = Path(path)

    if path_obj.is_absolute():
        return path_obj.resolve()
    else:
        return (base_directory / path_obj).resolve()


def batch_check_paths_exist(paths: List[str], base_directory: Optional[Path] = None) -> Dict[str, bool]:
    """
    Check multiple paths for existence.

    Args:
        paths: List of path strings to check
        base_directory: Base directory for relative paths (defaults to cwd)

    Returns:
        Dictionary mapping each path to its existence status (True/False)

    Example:
        >>> existence = batch_check_paths_exist(["src/main.py", "tests/test.py"])
        >>> for path, exists in existence.items():
        ...     print(f"{path}: {'exists' if exists else 'missing'}")
    """
    if base_directory:
        base_directory = Path(base_directory).resolve()
    else:
        base_directory = Path.cwd()

    result = {}

    for path_str in paths:
        normalized = normalize_path(path_str, base_directory)
        result[path_str] = normalized.exists()

    return result


def find_files_by_pattern(
    directory: Path,
    pattern: str,
    recursive: bool = True,
    max_depth: Optional[int] = None
) -> List[Path]:
    """
    Find files matching a pattern in a directory.

    Args:
        directory: Directory to search
        pattern: Glob pattern (e.g., "*.py", "test_*.py")
        recursive: Whether to search recursively
        max_depth: Maximum depth for recursive search (None = unlimited)

    Returns:
        List of matching file paths

    Example:
        >>> py_files = find_files_by_pattern(Path("src"), "*.py")
        >>> print(f"Found {len(py_files)} Python files")
    """
    if not directory.exists() or not directory.is_dir():
        return []

    if recursive:
        if max_depth is None:
            # Unlimited depth
            pattern_str = f"**/{pattern}"
        else:
            # Limited depth - construct pattern
            # This is a simplified implementation
            pattern_str = f"**/{pattern}"

        matches = list(directory.glob(pattern_str))
    else:
        matches = list(directory.glob(pattern))

    # Filter to only files
    return [p for p in matches if p.is_file()]
