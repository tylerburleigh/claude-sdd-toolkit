"""
UI backend factory with automatic TTY detection.

This module provides intelligent backend selection logic that automatically
chooses between RichUi (interactive TTY) and PlainUi (non-TTY/CI) based on
the runtime environment.

Key Features:
- Automatic TTY detection via sys.stdout.isatty()
- CI/CD environment detection (GITHUB_ACTIONS, CI, etc.)
- Force backend selection via --plain flag or config settings
- Consistent API regardless of backend

Usage:
    from claude_skills.common.ui_factory import create_ui

    # Automatic selection
    ui = create_ui()

    # Force plain mode
    ui = create_ui(force_plain=True)

    # With collection mode
    ui = create_ui(collect_messages=True)
"""

import os
import sys
from typing import Optional, Union

from .ui_protocol import Ui
from .rich_ui import RichUi
from .plain_ui import PlainUi


def is_tty_available() -> bool:
    """
    Check if stdout is connected to a TTY.

    Returns True if stdout is an interactive terminal that supports
    rich formatting. Returns False for pipes, files, CI environments.

    Returns:
        True if TTY available, False otherwise

    Example:
        if is_tty_available():
            print("Interactive terminal")
        else:
            print("Non-interactive (pipe, file, CI)")
    """
    return sys.stdout.isatty()


def is_ci_environment() -> bool:
    """
    Detect if running in a CI/CD environment.

    Checks common CI environment variables to determine if
    the code is running in an automated CI/CD pipeline.

    Detected CI systems:
    - GitHub Actions (GITHUB_ACTIONS)
    - GitLab CI (GITLAB_CI)
    - Travis CI (TRAVIS)
    - CircleCI (CIRCLECI)
    - Jenkins (JENKINS_URL)
    - Generic CI (CI=true)

    Returns:
        True if running in CI, False otherwise

    Example:
        if is_ci_environment():
            print("Running in CI/CD pipeline")
    """
    ci_vars = [
        "CI",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "TRAVIS",
        "CIRCLECI",
        "JENKINS_URL",
        "BUILDKITE",
        "DRONE",
    ]
    return any(os.getenv(var) for var in ci_vars)


def should_use_plain_ui(force_plain: bool = False) -> bool:
    """
    Determine if PlainUi should be used instead of RichUi.

    Decision logic:
    1. If force_plain=True → Use PlainUi
    2. If not TTY (piped/redirected) → Use PlainUi
    3. If CI environment detected → Use PlainUi
    4. Otherwise → Use RichUi

    Args:
        force_plain: Explicitly force PlainUi backend

    Returns:
        True if PlainUi should be used, False for RichUi

    Example:
        # Check decision logic
        if should_use_plain_ui():
            print("Will use PlainUi")
        else:
            print("Will use RichUi")

        # Force plain mode
        should_use_plain_ui(force_plain=True)  # → True
    """
    # 1. Explicit force flag
    if force_plain:
        return True

    # 2. No TTY available (piped, redirected, file)
    if not is_tty_available():
        return True

    # 3. Running in CI/CD
    if is_ci_environment():
        return True

    # 4. Default to RichUi for interactive terminals
    return False


def create_ui(
    force_plain: bool = False,
    force_rich: bool = False,
    collect_messages: bool = False,
    quiet: bool = False,
    project_path: Optional['Path'] = None,
    **kwargs
) -> Ui:
    """
    Create appropriate UI backend based on environment and configuration.

    Automatically selects RichUi or PlainUi based on:
    - User configuration (output.default_mode in .claude/sdd_config.json)
    - TTY availability
    - CI environment detection
    - Explicit force flags

    Args:
        force_plain: Force PlainUi backend (overrides auto-detection)
        force_rich: Force RichUi backend (overrides auto-detection)
        collect_messages: Enable message collection mode
        quiet: Enable quiet mode (errors only, PlainUi only)
        project_path: Path to project root for config loading (optional)
        **kwargs: Additional backend-specific options

    Returns:
        Ui implementation (RichUi or PlainUi)

    Raises:
        ValueError: If both force_plain and force_rich are True

    Examples:
        # Automatic selection (recommended)
        ui = create_ui()

        # Force plain mode (for testing)
        ui = create_ui(force_plain=True)

        # Force rich mode (for demos)
        ui = create_ui(force_rich=True)

        # Collection mode with automatic backend
        ui = create_ui(collect_messages=True)

        # Quiet mode for scripts
        ui = create_ui(quiet=True)

    Decision Flow:
        1. Check force_rich/force_plain flags
        2. Check user config (output.default_mode: "plain"→PlainUi, "rich"/"json"→RichUi)
        3. Check TTY availability
        4. Check CI environment
        5. Default to RichUi for interactive terminals
    """
    # Validate flags
    if force_plain and force_rich:
        raise ValueError("Cannot force both plain and rich backends")

    # Determine backend
    use_plain = False

    if force_rich:
        use_plain = False
    elif force_plain:
        use_plain = True
    else:
        # Check user config preference
        try:
            from .sdd_config import get_default_format
            default_mode = get_default_format(project_path)

            if default_mode == "plain":
                use_plain = True
            elif default_mode in ("rich", "json"):
                use_plain = False
            else:
                # Unknown value - fall back to auto-detection
                use_plain = should_use_plain_ui()
        except (ImportError, Exception):
            # If config loading fails, fall back to auto-detection
            use_plain = should_use_plain_ui()

    # Create appropriate backend
    if use_plain:
        return PlainUi(
            collect_messages=collect_messages,
            quiet=quiet,
            **kwargs
        )
    else:
        return RichUi(
            collect_messages=collect_messages,
            **kwargs
        )


def create_ui_from_args(args) -> Ui:
    """
    Create UI backend from parsed CLI arguments.

    Convenience function for CLI commands that use argparse.
    Expects args object with optional attributes:
    - plain: bool (force plain mode)
    - quiet: bool (suppress output)
    - collect: bool (collection mode)

    Args:
        args: argparse.Namespace with CLI arguments

    Returns:
        Ui implementation based on CLI flags

    Example:
        import argparse

        parser = argparse.ArgumentParser()
        parser.add_argument("--plain", action="store_true")
        parser.add_argument("--quiet", action="store_true")
        args = parser.parse_args()

        ui = create_ui_from_args(args)
        ui.print_status("Processing...", MessageLevel.ACTION)
    """
    force_plain = getattr(args, "plain", False)
    quiet = getattr(args, "quiet", False)
    collect = getattr(args, "collect", False)

    return create_ui(
        force_plain=force_plain,
        quiet=quiet,
        collect_messages=collect
    )


def get_backend_name(ui: Ui) -> str:
    """
    Get the name of the UI backend.

    Args:
        ui: Ui instance

    Returns:
        "RichUi" or "PlainUi"

    Example:
        ui = create_ui()
        print(f"Using {get_backend_name(ui)} backend")
        # Output: "Using RichUi backend" or "Using PlainUi backend"
    """
    return ui.__class__.__name__


def format_backend_info() -> str:
    """
    Get formatted information about backend selection.

    Returns diagnostic information about the runtime environment
    and which backend would be selected.

    Returns:
        Formatted string with backend selection details

    Example:
        print(format_backend_info())

        Output:
        Backend Selection Info:
        - TTY Available: Yes
        - CI Environment: No
        - Selected Backend: RichUi
    """
    lines = [
        "Backend Selection Info:",
        f"  - TTY Available: {'Yes' if is_tty_available() else 'No'}",
        f"  - CI Environment: {'Yes' if is_ci_environment() else 'No'}",
        f"  - Selected Backend: {'PlainUi' if should_use_plain_ui() else 'RichUi'}",
    ]
    return "\n".join(lines)


# Convenience function for quick access
def ui(
    force_plain: bool = False,
    collect_messages: bool = False,
    quiet: bool = False
) -> Ui:
    """
    Shorthand for create_ui().

    Args:
        force_plain: Force PlainUi backend
        collect_messages: Enable collection mode
        quiet: Enable quiet mode

    Returns:
        Ui implementation

    Example:
        from claude_skills.common.ui_factory import ui

        # Quick usage
        terminal = ui()
        terminal.print_status("Ready", MessageLevel.SUCCESS)
    """
    return create_ui(
        force_plain=force_plain,
        collect_messages=collect_messages,
        quiet=quiet
    )
