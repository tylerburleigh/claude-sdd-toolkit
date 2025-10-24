"""
Workflow operations for sdd-next.

This module provides functions for initializing the development environment
and performing file pattern searches.
"""

from pathlib import Path
from typing import Dict, List, Optional

# Clean imports from common package
from claude_skills.common import find_specs_directory, ensure_directory


def init_environment(spec_path: Optional[str] = None) -> Dict:
    """
    Initialize development environment with complete setup.

    Args:
        spec_path: Optional path to spec file or directory

    Returns:
        Dictionary with environment paths and validation status
    """
    result = {
        "success": False,
        "specs_dir": None,
        "active_dir": None,
        "state_dir": None,
        "error": None
    }

    # Discover specs directory
    specs_dir = find_specs_directory(spec_path)
    if not specs_dir:
        result["error"] = "No specs/active directory found"
        return result

    result["specs_dir"] = str(specs_dir)
    result["active_dir"] = str(specs_dir / "active")
    result["state_dir"] = str(specs_dir / ".state")

    # Validate structure
    active_dir = Path(result["active_dir"])
    if not ensure_directory(active_dir):
        result["error"] = f"Active directory not accessible: {active_dir}"
        return result

    # Ensure state directory exists
    state_dir = Path(result["state_dir"])
    ensure_directory(state_dir)

    result["success"] = True
    return result


def find_pattern(pattern: str, directory: Optional[Path] = None) -> List[str]:
    """
    Find files matching a pattern.

    Args:
        pattern: Glob pattern (e.g., "*.ts", "src/**/*.spec.ts")
        directory: Directory to search (defaults to current directory)

    Returns:
        List of matching file paths
    """
    if not directory:
        directory = Path.cwd()
    else:
        directory = Path(directory)

    if not directory.exists():
        return []

    # Use rglob for recursive patterns
    if "**" in pattern:
        matches = directory.glob(pattern)
    else:
        # For non-recursive, check both current dir and recursive
        matches = list(directory.glob(pattern)) + list(directory.rglob(pattern))
        # Remove duplicates
        matches = list(set(matches))

    return [str(m.resolve()) for m in matches if m.is_file()]
