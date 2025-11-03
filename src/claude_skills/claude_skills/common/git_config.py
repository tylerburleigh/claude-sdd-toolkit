"""Git integration configuration loader for SDD toolkit.

Loads git integration settings from configuration files with fallback to sensible defaults.
Supports both per-project and global configurations.

Configuration Locations (in order of precedence):
1. Project-local: {project_root}/.claude/git_config.json
2. Global: ~/.claude/git_config.json
3. Defaults: Built-in DEFAULT_GIT_CONFIG

This module provides a common interface for all skills to load git integration settings.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


# Default git configuration (fallback if config file not found)
DEFAULT_GIT_CONFIG = {
    "enabled": False,  # Git integration disabled by default for safety
    "auto_branch": True,  # Automatically create feature branches when starting specs
    "auto_commit": True,  # Automatically commit after completing tasks
    "auto_push": False,  # Do NOT automatically push (requires user confirmation)
    "auto_pr": False,  # Do NOT automatically create PRs (requires user confirmation)
    "commit_cadence": "task",  # When to commit: "task", "phase", or "manual"
    "file_staging": {  # File staging behavior for commits
        "show_before_commit": True,  # Show preview of files before committing (default: true)
    },
    "ai_pr": {  # AI-powered PR creation settings
        "enabled": False,  # Use AI to generate comprehensive PR descriptions (default: false)
        "model": "sonnet",  # AI model to use for PR generation (sonnet recommended for better writing)
        "include_journals": True,  # Include journal entries in context analysis
        "include_diffs": True,  # Include git diffs in context analysis
        "max_diff_size_kb": 50,  # Maximum diff size in KB before truncation
    }
}

# Valid values for commit_cadence setting
VALID_COMMIT_CADENCE = ["task", "phase", "manual"]


def get_config_path(project_path: Optional[Path] = None) -> Optional[Path]:
    """Get the path to the git_config.json file.

    Checks multiple locations in order of precedence:
    1. Project-local: {project_path}/.claude/git_config.json
    2. Global: ~/.claude/git_config.json

    Args:
        project_path: Path to project root (optional). If not provided,
                     will attempt to find project root or use cwd.

    Returns:
        Path to git_config.json if found, None otherwise
    """
    paths_to_check = []

    # Check project-local config first
    if project_path:
        project_config = Path(project_path) / ".claude" / "git_config.json"
        paths_to_check.append(project_config)
    else:
        # Try to find project root by looking for .claude directory
        cwd = Path.cwd()
        # Check current directory and up to 3 levels up
        for path in [cwd] + list(cwd.parents[:3]):
            project_config = path / ".claude" / "git_config.json"
            if project_config.exists():
                paths_to_check.append(project_config)
                break
        else:
            # If not found, still add cwd path as candidate
            paths_to_check.append(cwd / ".claude" / "git_config.json")

    # Check global config
    home = Path.home()
    global_config = home / ".claude" / "git_config.json"
    paths_to_check.append(global_config)

    # Return first existing path
    for path in paths_to_check:
        if path.exists():
            return path

    # Return None if no config found (will use defaults)
    return None


def _validate_git_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize git configuration values.

    Ensures all configuration values have correct types and valid values.
    Invalid values are replaced with defaults and warnings are logged.

    Args:
        config: Raw configuration dictionary

    Returns:
        Validated configuration dictionary
    """
    validated = DEFAULT_GIT_CONFIG.copy()

    # Validate boolean fields
    bool_fields = ["enabled", "auto_branch", "auto_commit", "auto_push", "auto_pr"]
    for field in bool_fields:
        if field in config:
            value = config[field]
            if isinstance(value, bool):
                validated[field] = value
            else:
                logger.warning(
                    f"Invalid type for git config '{field}': expected bool, got {type(value).__name__}. "
                    f"Using default: {DEFAULT_GIT_CONFIG[field]}"
                )

    # Validate commit_cadence
    if "commit_cadence" in config:
        value = config["commit_cadence"]
        if isinstance(value, str) and value in VALID_COMMIT_CADENCE:
            validated["commit_cadence"] = value
        else:
            logger.warning(
                f"Invalid value for git config 'commit_cadence': {value}. "
                f"Must be one of {VALID_COMMIT_CADENCE}. "
                f"Using default: {DEFAULT_GIT_CONFIG['commit_cadence']}"
            )

    # Validate file_staging section
    if "file_staging" in config and isinstance(config["file_staging"], dict):
        file_staging = config["file_staging"]
        if "show_before_commit" in file_staging:
            value = file_staging["show_before_commit"]
            if isinstance(value, bool):
                validated["file_staging"]["show_before_commit"] = value

    # Validate ai_pr section
    if "ai_pr" in config and isinstance(config["ai_pr"], dict):
        ai_pr = config["ai_pr"]

        # Validate boolean fields
        if "enabled" in ai_pr and isinstance(ai_pr["enabled"], bool):
            validated["ai_pr"]["enabled"] = ai_pr["enabled"]
        if "include_journals" in ai_pr and isinstance(ai_pr["include_journals"], bool):
            validated["ai_pr"]["include_journals"] = ai_pr["include_journals"]
        if "include_diffs" in ai_pr and isinstance(ai_pr["include_diffs"], bool):
            validated["ai_pr"]["include_diffs"] = ai_pr["include_diffs"]

        # Validate string fields
        if "model" in ai_pr and isinstance(ai_pr["model"], str):
            validated["ai_pr"]["model"] = ai_pr["model"]

        # Validate numeric fields
        if "max_diff_size_kb" in ai_pr:
            value = ai_pr["max_diff_size_kb"]
            if isinstance(value, (int, float)) and value > 0:
                validated["ai_pr"]["max_diff_size_kb"] = int(value)
            else:
                logger.warning(
                    f"Invalid value for ai_pr.max_diff_size_kb: {value}. "
                    f"Must be a positive number. Using default: {DEFAULT_GIT_CONFIG['ai_pr']['max_diff_size_kb']}"
                )

    # Warn about unknown keys (but don't fail)
    known_keys = set(DEFAULT_GIT_CONFIG.keys())
    unknown_keys = set(config.keys()) - known_keys
    if unknown_keys:
        logger.warning(
            f"Unknown keys in git config will be ignored: {', '.join(unknown_keys)}"
        )

    return validated


def load_git_config(project_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load git configuration from file with fallback to defaults.

    Attempts to load configuration from:
    1. Project-local config ({project_path}/.claude/git_config.json)
    2. Global config (~/.claude/git_config.json)
    3. Built-in defaults (DEFAULT_GIT_CONFIG)

    Args:
        project_path: Path to project root (optional). If not provided,
                     will attempt to find project root.

    Returns:
        Dict with complete git configuration (validated and merged with defaults)
    """
    config_path = get_config_path(project_path)

    if not config_path:
        # No config file found, use defaults
        logger.debug("No git config file found, using defaults")
        return DEFAULT_GIT_CONFIG.copy()

    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)

        if not config_data or not isinstance(config_data, dict):
            # Empty or invalid config, use defaults
            logger.warning(f"Empty or invalid git config at {config_path}, using defaults")
            return DEFAULT_GIT_CONFIG.copy()

        # Validate and merge with defaults
        validated_config = _validate_git_config(config_data)
        logger.debug(f"Loaded git config from {config_path}")
        return validated_config

    except json.JSONDecodeError as e:
        # JSON parsing error, use defaults
        logger.warning(
            f"Failed to parse git config at {config_path}: {e}. Using defaults."
        )
        return DEFAULT_GIT_CONFIG.copy()

    except (IOError, OSError) as e:
        # File read error, use defaults
        logger.warning(
            f"Failed to read git config at {config_path}: {e}. Using defaults."
        )
        return DEFAULT_GIT_CONFIG.copy()


def is_git_enabled(project_path: Optional[Path] = None) -> bool:
    """Check if git integration is enabled.

    Quick convenience function to check the 'enabled' setting.

    Args:
        project_path: Path to project root (optional)

    Returns:
        True if git integration is enabled, False otherwise
    """
    config = load_git_config(project_path)
    return config.get('enabled', False)


def get_git_setting(
    key: str,
    project_path: Optional[Path] = None,
    default: Optional[Any] = None
) -> Any:
    """Get a specific git configuration setting with validation.

    Args:
        key: Configuration key to retrieve
        project_path: Path to project root (optional)
        default: Default value to return if key not found (optional).
                If not provided, uses DEFAULT_GIT_CONFIG default.

    Returns:
        Configuration value for the specified key
    """
    config = load_git_config(project_path)

    # Use provided default, or fall back to DEFAULT_GIT_CONFIG
    if default is not None:
        return config.get(key, default)
    else:
        return config.get(key, DEFAULT_GIT_CONFIG.get(key))
