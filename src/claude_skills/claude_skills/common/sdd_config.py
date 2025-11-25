"""SDD CLI configuration loader for SDD toolkit.

Loads SDD CLI output settings from configuration files with fallback to sensible defaults.
Supports both per-project and global configurations.

Configuration Locations (in order of precedence):
1. Project-local: {project_root}/.claude/sdd_config.json
2. Global: ~/.claude/sdd_config.json
3. Defaults: Built-in DEFAULT_SDD_CONFIG

This module provides a common interface for all CLI commands to load output settings.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


# Default SDD configuration (fallback if config file not found)
DEFAULT_SDD_CONFIG = {
    "work_mode": "single",  # Work mode for sdd-next: "single" (one task at a time with approval) or "autonomous" (complete phase automatically)
    "output": {
        "default_mode": "rich",  # Unified output format: "rich" (formatted), "plain" (simple text), or "json"
        "json_compact": True,  # Use compact JSON formatting (only affects JSON output)
        "default_verbosity": "quiet",  # Default verbosity level: "quiet", "normal", or "verbose"

        # Deprecated (kept for backward compatibility - will be removed in future version)
        "json": None,  # DEPRECATED: Use default_mode="json" instead
        "compact": None,  # DEPRECATED: Use json_compact instead
        "default_format": None,  # DEPRECATED: Use default_mode instead
    },
    "doc_context": {
        # Controls which enrichments are gathered for prepare-task context
        # All enabled by default - disable to reduce token usage or latency
        "call_graph": True,       # Include caller/callee information
        "test_context": True,     # Include test files
    }
}


def get_config_path(project_path: Optional[Path] = None) -> Optional[Path]:
    """Get the path to the sdd_config.json file.

    Checks multiple locations in order of precedence:
    1. Project-local: {project_path}/.claude/sdd_config.json
    2. Global: ~/.claude/sdd_config.json

    Args:
        project_path: Path to project root (optional). If not provided,
                     will attempt to find project root or use cwd.

    Returns:
        Path to sdd_config.json if found, None otherwise
    """
    paths_to_check = []

    # Check project-local config first
    if project_path:
        project_config = Path(project_path) / ".claude" / "sdd_config.json"
        paths_to_check.append(project_config)
    else:
        # Try to find project root by looking for .claude directory
        cwd = Path.cwd()
        # Check current directory and up to 3 levels up
        for path in [cwd] + list(cwd.parents[:3]):
            project_config = path / ".claude" / "sdd_config.json"
            if project_config.exists():
                paths_to_check.append(project_config)
                break
        else:
            # If not found, still add cwd path as candidate
            paths_to_check.append(cwd / ".claude" / "sdd_config.json")

    # Check global config
    home = Path.home()
    global_config = home / ".claude" / "sdd_config.json"
    paths_to_check.append(global_config)

    # Return first existing path
    for path in paths_to_check:
        if path.exists():
            return path

    # Return None if no config found (will use defaults)
    return None


def _validate_sdd_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize SDD configuration values.

    Ensures all configuration values have correct types and valid values.
    Invalid values are replaced with defaults and warnings are logged.

    Handles migration from old config format (json/default_format) to new format (default_mode).

    Args:
        config: Raw configuration dictionary

    Returns:
        Validated configuration dictionary
    """
    import copy
    validated = {"output": {}}

    # Validate work_mode field
    if "work_mode" in config:
        value = config["work_mode"]
        allowed_modes = ["single", "autonomous"]
        if isinstance(value, str) and value in allowed_modes:
            validated["work_mode"] = value
        else:
            logger.warning(
                f"Invalid value for sdd config 'work_mode': expected one of {allowed_modes}, "
                f"got {value!r}. Using default: 'single'"
            )
            validated["work_mode"] = "single"
    else:
        # Not specified, use default
        validated["work_mode"] = "single"

    # Validate output section
    if "output" in config and isinstance(config["output"], dict):
        output = config["output"]

        # MIGRATION LOGIC: Convert old config format to new unified format
        if "default_mode" not in output:
            # Old config detected - migrate to new format
            if "json" in output and output["json"] is True:
                # Old config had json:true, use JSON mode
                validated["output"]["default_mode"] = "json"
                logger.debug("Migrated config: output.json=true -> output.default_mode='json'")
            elif "default_format" in output and output["default_format"] in ["text", "json", "markdown"]:
                # Use old default_format value, migrating old mode names
                old_format = output["default_format"]
                if old_format == "text" or old_format == "markdown":
                    validated["output"]["default_mode"] = "rich"
                    logger.debug(f"Migrated config: output.default_format='{old_format}' -> output.default_mode='rich'")
                else:  # json
                    validated["output"]["default_mode"] = old_format
                    logger.debug(f"Migrated config: output.default_format='{old_format}' -> output.default_mode='{old_format}'")
            else:
                # Neither setting found or valid, use default
                validated["output"]["default_mode"] = "rich"
        else:
            # New config with default_mode
            value = output["default_mode"]

            # Migrate old mode names to new ones
            if value == "text":
                value = "rich"
                logger.debug("Migrated config: output.default_mode='text' -> 'rich'")
            elif value == "markdown":
                value = "rich"
                logger.debug("Migrated config: output.default_mode='markdown' -> 'rich'")

            allowed_modes = ["rich", "plain", "json"]
            if isinstance(value, str) and value in allowed_modes:
                validated["output"]["default_mode"] = value
            else:
                logger.warning(
                    f"Invalid value for sdd config 'output.default_mode': expected one of {allowed_modes}, "
                    f"got {value!r}. Using default: 'rich'"
                )
                validated["output"]["default_mode"] = "rich"

        # Validate json_compact field (new name for compact)
        if "json_compact" in output:
            value = output["json_compact"]
            if isinstance(value, bool):
                validated["output"]["json_compact"] = value
            else:
                logger.warning(
                    f"Invalid type for sdd config 'output.json_compact': expected bool, got {type(value).__name__}. "
                    f"Using default: True"
                )
                validated["output"]["json_compact"] = True
        elif "compact" in output:
            # Old config - migrate compact -> json_compact
            value = output["compact"]
            if isinstance(value, bool):
                validated["output"]["json_compact"] = value
                logger.debug(f"Migrated config: output.compact={value} -> output.json_compact={value}")
            else:
                validated["output"]["json_compact"] = True
        else:
            validated["output"]["json_compact"] = True

        # Validate default_verbosity field
        if "default_verbosity" in output:
            value = output["default_verbosity"]
            allowed_levels = ["quiet", "normal", "verbose"]
            if isinstance(value, str) and value in allowed_levels:
                validated["output"]["default_verbosity"] = value
            else:
                logger.warning(
                    f"Invalid value for sdd config 'output.default_verbosity': expected one of {allowed_levels}, "
                    f"got {value!r}. Using default: 'quiet'"
                )
                validated["output"]["default_verbosity"] = "quiet"
        else:
            # Not specified, use default
            validated["output"]["default_verbosity"] = "quiet"

        # Store deprecated values for backward compatibility (set to None to mark as deprecated)
        validated["output"]["json"] = None
        validated["output"]["compact"] = None
        validated["output"]["default_format"] = None

    else:
        # No output section - use all defaults
        validated["output"]["default_mode"] = "rich"
        validated["output"]["json_compact"] = True
        validated["output"]["default_verbosity"] = "quiet"
        validated["output"]["json"] = None
        validated["output"]["compact"] = None
        validated["output"]["default_format"] = None

    # Validate doc_context section
    if "doc_context" in config and isinstance(config["doc_context"], dict):
        doc_context = config["doc_context"]
        validated["doc_context"] = {}

        # Validate each enrichment toggle
        enrichment_keys = ["call_graph", "test_context"]
        for key in enrichment_keys:
            if key in doc_context:
                value = doc_context[key]
                if isinstance(value, bool):
                    validated["doc_context"][key] = value
                else:
                    logger.warning(
                        f"Invalid type for sdd config 'doc_context.{key}': expected bool, "
                        f"got {type(value).__name__}. Using default: True"
                    )
                    validated["doc_context"][key] = True
            else:
                # Not specified, use default (enabled)
                validated["doc_context"][key] = True
    else:
        # No doc_context section - use all defaults (all enabled)
        validated["doc_context"] = {
            "call_graph": True,
            "test_context": True,
        }

    # Warn about unknown keys (but don't fail)
    known_keys = {"output", "work_mode", "doc_context", "_comment", "_description", "_work_mode_options", "_doc_context_description"}
    unknown_keys = set(config.keys()) - known_keys
    if unknown_keys:
        logger.warning(
            f"Unknown keys in sdd config will be ignored: {', '.join(unknown_keys)}"
        )

    return validated


def load_sdd_config(project_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load SDD configuration from file with fallback to defaults.

    Attempts to load configuration from:
    1. Project-local config ({project_path}/.claude/sdd_config.json)
    2. Global config (~/.claude/sdd_config.json)
    3. Built-in defaults (DEFAULT_SDD_CONFIG)

    Args:
        project_path: Path to project root (optional). If not provided,
                     will attempt to find project root.

    Returns:
        Dict with complete SDD configuration (validated and merged with defaults)
    """
    config_path = get_config_path(project_path)

    if not config_path:
        # No config file found, use defaults
        logger.debug("No sdd config file found, using defaults")
        return DEFAULT_SDD_CONFIG.copy()

    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)

        if not config_data or not isinstance(config_data, dict):
            # Empty or invalid config, use defaults
            logger.warning(f"Empty or invalid sdd config at {config_path}, using defaults")
            return DEFAULT_SDD_CONFIG.copy()

        # Validate and merge with defaults
        validated_config = _validate_sdd_config(config_data)
        logger.debug(f"Loaded sdd config from {config_path}")
        return validated_config

    except json.JSONDecodeError as e:
        # JSON parsing error, use defaults
        logger.warning(
            f"Failed to parse sdd config at {config_path}: {e}. Using defaults."
        )
        return DEFAULT_SDD_CONFIG.copy()

    except (IOError, OSError) as e:
        # File read error, use defaults
        logger.warning(
            f"Failed to read sdd config at {config_path}: {e}. Using defaults."
        )
        return DEFAULT_SDD_CONFIG.copy()


def get_sdd_setting(
    key: str,
    project_path: Optional[Path] = None,
    default: Optional[Any] = None
) -> Any:
    """Get a specific SDD configuration setting with validation.

    Args:
        key: Configuration key to retrieve (supports nested keys with dots, e.g., 'output.json')
        project_path: Path to project root (optional)
        default: Default value to return if key not found (optional).
                If not provided, uses DEFAULT_SDD_CONFIG default.

    Returns:
        Configuration value for the specified key
    """
    config = load_sdd_config(project_path)

    # Support nested keys like 'output.json'
    keys = key.split('.')
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            # Key not found, return default
            if default is not None:
                return default
            # Try to get from DEFAULT_SDD_CONFIG
            default_value = DEFAULT_SDD_CONFIG
            for dk in keys:
                if isinstance(default_value, dict) and dk in default_value:
                    default_value = default_value[dk]
                else:
                    return None
            return default_value

    return value


def get_default_format(project_path: Optional[Path] = None) -> str:
    """Get the default output format from configuration.

    Uses the unified default_mode setting. For backward compatibility,
    also checks the deprecated default_format setting.

    Args:
        project_path: Path to project root (optional)

    Returns:
        Default format string: "rich", "plain", or "json"

    Example:
        default_format = get_default_format()
        parser.add_argument('--format', default=default_format, ...)
    """
    return get_sdd_setting("output.default_mode", project_path, default="rich")


def get_json_compact(project_path: Optional[Path] = None) -> bool:
    """Get the JSON compact formatting preference from configuration.

    Args:
        project_path: Path to project root (optional)

    Returns:
        Boolean indicating whether to use compact JSON formatting

    Example:
        compact = get_json_compact()
        json.dumps(data, indent=None if compact else 2)
    """
    return get_sdd_setting("output.json_compact", project_path, default=True)


def get_work_mode(project_path: Optional[Path] = None) -> str:
    """Get the work mode preference from configuration.

    The work mode controls how sdd-next executes tasks:
    - "single": Plan and execute one task at a time with explicit approval
    - "autonomous": Complete all tasks in current phase automatically

    Args:
        project_path: Path to project root (optional)

    Returns:
        Work mode string: "single" or "autonomous"

    Example:
        work_mode = get_work_mode()
        if work_mode == "autonomous":
            # Execute all phase tasks automatically
        else:
            # Request approval for each task
    """
    return get_sdd_setting("work_mode", project_path, default="single")


def get_doc_context_settings(project_path: Optional[Path] = None) -> Dict[str, bool]:
    """Get doc context enrichment settings from configuration.

    Controls which enrichments are gathered during prepare-task:
    - call_graph: Include caller/callee information
    - test_context: Include test files

    All enrichments are enabled by default. Disable to reduce token usage
    or improve latency.

    Args:
        project_path: Path to project root (optional)

    Returns:
        Dict with boolean flags for each enrichment type

    Example:
        settings = get_doc_context_settings()
        if settings["call_graph"]:
            # Gather call graph context
        if settings["test_context"]:
            # Gather test context
    """
    config = load_sdd_config(project_path)
    return config.get("doc_context", {
        "call_graph": True,
        "test_context": True,
    })
