"""
Pytest Runner Operations

Smart pytest runner with presets for common testing scenarios.
Simplifies running pytest with appropriate flags for different debugging and testing needs.
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path to import sdd_common

from claude_skills.common import PrettyPrinter


def _detect_source_directory() -> Optional[str]:
    """
    Auto-detect the source directory for coverage reporting.

    Returns:
        Source directory path if found, None otherwise
    """
    # Common source directory names in order of preference
    common_dirs = ["src", "lib", "app", "package"]

    cwd = Path.cwd()

    # Check for common source directories
    for dirname in common_dirs:
        src_path = cwd / dirname
        if src_path.is_dir():
            # Verify it contains Python files
            if any(src_path.rglob("*.py")):
                return dirname

    # Check if the current directory contains Python files (flat structure)
    if any(cwd.glob("*.py")):
        # Check if there's a setup.py or pyproject.toml
        if (cwd / "setup.py").exists() or (cwd / "pyproject.toml").exists():
            return "."

    return None


# Pytest preset configurations
# Note: The coverage preset will auto-detect the source directory at runtime
def _get_presets() -> Dict[str, Dict]:
    """
    Get preset configurations.

    The coverage preset auto-detects the source directory to avoid hard-coding.

    Returns:
        Dictionary of preset configurations
    """
    # Detect source directory for coverage
    src_dir = _detect_source_directory()
    cov_flags = ["--cov-report=html", "--cov-report=term"]
    if src_dir:
        cov_flags.insert(0, f"--cov={src_dir}")
    else:
        # Fallback: try to cover tests directory's parent
        cov_flags.insert(0, "--cov=.")

    return {
        "quick": {
            "description": "Quick run - stop on first failure",
            "flags": ["-x", "-v"],
        },
        "debug": {
            "description": "Debug mode - verbose output with local variables and print statements",
            "flags": ["-vv", "-l", "-s"],
        },
        "verbose": {
            "description": "Verbose output with full details",
            "flags": ["-vv"],
        },
        "coverage": {
            "description": "Run with coverage report (auto-detects source directory)",
            "flags": cov_flags,
        },
        "pdb": {
            "description": "Drop into debugger on failures",
            "flags": ["-x", "--pdb"],
        },
        "markers": {
            "description": "Show available test markers",
            "flags": ["--markers"],
        },
        "fixtures": {
            "description": "Show available fixtures",
            "flags": ["--fixtures"],
        },
        "setup": {
            "description": "Show fixture setup and teardown",
            "flags": ["--setup-show"],
        },
        "fast": {
            "description": "Skip slow tests",
            "flags": ["-m", "not slow", "-v"],
        },
        "slow": {
            "description": "Run only slow tests",
            "flags": ["-m", "slow", "-v"],
        },
        "unit": {
            "description": "Run only unit tests",
            "flags": ["-m", "unit", "-v"],
        },
        "integration": {
            "description": "Run only integration tests",
            "flags": ["-m", "integration", "-v"],
        },
        "parallel": {
            "description": "Run tests in parallel (requires pytest-xdist)",
            "flags": ["-n", "auto", "-v"],
        },
        "ci": {
            "description": "CI-friendly output",
            "flags": ["--tb=short", "--junitxml=test-results.xml"],
        },
    }

# Initialize presets once at module load
PRESETS = _get_presets()


def build_pytest_command(
    preset: Optional[str] = None,
    path: Optional[str] = None,
    pattern: Optional[str] = None,
    extra_args: Optional[List[str]] = None
) -> List[str]:
    """
    Build the pytest command with the specified configuration.

    Args:
        preset: Name of the preset to use
        path: Specific test file or directory to run
        pattern: Pattern to match test names (used with -k)
        extra_args: Additional arguments to pass to pytest

    Returns:
        List of command arguments
    """
    cmd = ["pytest"]

    # Add preset flags
    if preset and preset in PRESETS:
        cmd.extend(PRESETS[preset]["flags"])

    # Add pattern matching
    if pattern:
        cmd.extend(["-k", pattern])

    # Add path if specified
    if path:
        cmd.append(path)

    # Add any extra arguments
    if extra_args:
        cmd.extend(extra_args)

    return cmd


def run_pytest(
    preset: Optional[str] = None,
    path: Optional[str] = None,
    pattern: Optional[str] = None,
    extra_args: Optional[List[str]] = None,
    printer: Optional[PrettyPrinter] = None
) -> int:
    """
    Run pytest with the specified configuration.

    Args:
        preset: Name of the preset to use
        path: Specific test file or directory to run
        pattern: Pattern to match test names (used with -k)
        extra_args: Additional arguments to pass to pytest
        printer: PrettyPrinter instance (creates default if None)

    Returns:
        Exit code from pytest
    """
    if printer is None:
        printer = PrettyPrinter()

    # Validate path if provided
    if path:
        path_obj = Path(path)
        # Check if it's a specific test (contains ::)
        if "::" not in path and not path_obj.exists():
            printer.error(f"Path not found: {path}")
            return 1

    cmd = build_pytest_command(preset, path, pattern, extra_args)

    # Print the command being run
    printer.action(f"Running: {' '.join(cmd)}")
    printer.blank()

    # Run pytest
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        printer.error("pytest not found. Is it installed?")
        printer.info("Install with: pip install pytest")
        return 1
    except KeyboardInterrupt:
        printer.warning("\nTest run interrupted by user")
        return 130
    except Exception as e:
        printer.error(f"Unexpected error running pytest: {e}")
        return 1


def get_presets() -> Dict[str, Dict[str, str]]:
    """
    Get all available presets.

    Returns:
        Dictionary of preset configurations
    """
    return PRESETS.copy()


def list_presets(printer: Optional[PrettyPrinter] = None) -> None:
    """
    Display all available presets.

    Args:
        printer: PrettyPrinter instance (creates default if None)
    """
    if printer is None:
        printer = PrettyPrinter()

    printer.header("Available pytest presets")
    printer.blank()

    max_name_len = max(len(name) for name in PRESETS.keys())

    for name, config in sorted(PRESETS.items()):
        flags_str = " ".join(config["flags"])
        print(f"  {name:<{max_name_len}}  {config['description']}")
        print(f"  {' ' * max_name_len}  Flags: {flags_str}")
        print()


def validate_preset(preset: str) -> bool:
    """
    Check if a preset name is valid.

    Args:
        preset: Preset name to validate

    Returns:
        True if valid, False otherwise
    """
    return preset in PRESETS


def get_preset_description(preset: str) -> Optional[str]:
    """
    Get description for a preset.

    Args:
        preset: Preset name

    Returns:
        Description string or None if preset doesn't exist
    """
    if preset in PRESETS:
        return PRESETS[preset]["description"]
    return None


def get_preset_flags(preset: str) -> Optional[List[str]]:
    """
    Get flags for a preset.

    Args:
        preset: Preset name

    Returns:
        List of flag strings or None if preset doesn't exist
    """
    if preset in PRESETS:
        return PRESETS[preset]["flags"].copy()
    return None
