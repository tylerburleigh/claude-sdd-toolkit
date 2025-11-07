"""
General configuration management for SDD toolkit.

Provides configuration settings for various features including cache, AI tools, etc.
Supports both environment variables and config file settings.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


# Default configuration (fallback if no config found)
DEFAULT_CONFIG = {
    "cache": {
        "enabled": True,
        "directory": None,  # None means use default (~/.cache/sdd-toolkit/consultations/)
        "ttl_hours": 24,
        "max_size_mb": 1000,  # Maximum cache size in MB
        "auto_cleanup": True
    }
}


def get_config_path(project_path: Optional[Path] = None) -> Optional[Path]:
    """
    Get path to config.json file.

    Checks multiple locations in order of precedence:
    1. Project-local: {project_path}/.claude/config.json
    2. Global: ~/.claude/config.json

    Args:
        project_path: Path to project root (optional)

    Returns:
        Path to config.json if found, None otherwise
    """
    paths_to_check = []

    # Check project-local config first
    if project_path:
        project_config = Path(project_path) / ".claude" / "config.json"
        paths_to_check.append(project_config)
    else:
        # Try to find project root by looking for .claude directory
        cwd = Path.cwd()
        for path in [cwd] + list(cwd.parents[:3]):
            project_config = path / ".claude" / "config.json"
            if project_config.exists():
                paths_to_check.append(project_config)
                break
        else:
            paths_to_check.append(cwd / ".claude" / "config.json")

    # Check global config
    home = Path.home()
    global_config = home / ".claude" / "config.json"
    paths_to_check.append(global_config)

    # Return first existing path
    for path in paths_to_check:
        if path.exists():
            return path

    return None


def _merge_with_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge loaded config with defaults.

    Args:
        config: Loaded configuration dictionary

    Returns:
        Merged configuration with defaults
    """
    import copy
    merged = copy.deepcopy(DEFAULT_CONFIG)

    # Merge cache config
    if "cache" in config and isinstance(config["cache"], dict):
        cache_config = config["cache"]

        if "enabled" in cache_config and isinstance(cache_config["enabled"], bool):
            merged["cache"]["enabled"] = cache_config["enabled"]

        if "directory" in cache_config:
            value = cache_config["directory"]
            if value is None or isinstance(value, str):
                merged["cache"]["directory"] = value

        if "ttl_hours" in cache_config:
            value = cache_config["ttl_hours"]
            if isinstance(value, (int, float)) and value > 0:
                merged["cache"]["ttl_hours"] = value
            else:
                logger.warning(f"Invalid cache.ttl_hours: {value}. Using default.")

        if "max_size_mb" in cache_config:
            value = cache_config["max_size_mb"]
            if isinstance(value, (int, float)) and value > 0:
                merged["cache"]["max_size_mb"] = value
            else:
                logger.warning(f"Invalid cache.max_size_mb: {value}. Using default.")

        if "auto_cleanup" in cache_config and isinstance(cache_config["auto_cleanup"], bool):
            merged["cache"]["auto_cleanup"] = cache_config["auto_cleanup"]

    return merged


def load_config(project_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from file with fallback to defaults.

    Attempts to load from:
    1. Project-local config ({project_path}/.claude/config.json)
    2. Global config (~/.claude/config.json)
    3. Environment variables (override config file)
    4. Built-in defaults

    Args:
        project_path: Path to project root (optional)

    Returns:
        Complete configuration dictionary
    """
    config_path = get_config_path(project_path)

    if not config_path:
        logger.debug("No config file found, using defaults")
        config = DEFAULT_CONFIG.copy()
    else:
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)

            if not isinstance(config_data, dict):
                logger.warning(f"Invalid config at {config_path}, using defaults")
                config = DEFAULT_CONFIG.copy()
            else:
                config = _merge_with_defaults(config_data)
                logger.debug(f"Loaded config from {config_path}")

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse config at {config_path}: {e}. Using defaults.")
            config = DEFAULT_CONFIG.copy()
        except (IOError, OSError) as e:
            logger.warning(f"Failed to read config at {config_path}: {e}. Using defaults.")
            config = DEFAULT_CONFIG.copy()

    # Apply environment variable overrides
    config = _apply_env_overrides(config)

    return config


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to config.

    Environment variables take precedence over config file settings.

    Supported environment variables:
    - SDD_CACHE_ENABLED: "true" or "false"
    - SDD_CACHE_DIR: Path to cache directory
    - SDD_CACHE_TTL_HOURS: Number (hours)
    - SDD_CACHE_MAX_SIZE_MB: Number (MB)
    - SDD_CACHE_AUTO_CLEANUP: "true" or "false"

    Args:
        config: Configuration dictionary

    Returns:
        Configuration with environment overrides applied
    """
    import copy
    config = copy.deepcopy(config)

    # Cache enabled
    if "SDD_CACHE_ENABLED" in os.environ:
        value = os.environ["SDD_CACHE_ENABLED"].lower()
        if value in ("true", "1", "yes"):
            config["cache"]["enabled"] = True
        elif value in ("false", "0", "no"):
            config["cache"]["enabled"] = False

    # Cache directory
    if "SDD_CACHE_DIR" in os.environ:
        config["cache"]["directory"] = os.environ["SDD_CACHE_DIR"]

    # TTL hours
    if "SDD_CACHE_TTL_HOURS" in os.environ:
        try:
            value = float(os.environ["SDD_CACHE_TTL_HOURS"])
            if value > 0:
                config["cache"]["ttl_hours"] = value
        except ValueError:
            logger.warning("Invalid SDD_CACHE_TTL_HOURS value, ignoring")

    # Max size
    if "SDD_CACHE_MAX_SIZE_MB" in os.environ:
        try:
            value = float(os.environ["SDD_CACHE_MAX_SIZE_MB"])
            if value > 0:
                config["cache"]["max_size_mb"] = value
        except ValueError:
            logger.warning("Invalid SDD_CACHE_MAX_SIZE_MB value, ignoring")

    # Auto cleanup
    if "SDD_CACHE_AUTO_CLEANUP" in os.environ:
        value = os.environ["SDD_CACHE_AUTO_CLEANUP"].lower()
        if value in ("true", "1", "yes"):
            config["cache"]["auto_cleanup"] = True
        elif value in ("false", "0", "no"):
            config["cache"]["auto_cleanup"] = False

    return config


def get_setting(
    key: str,
    project_path: Optional[Path] = None,
    default: Optional[Any] = None
) -> Any:
    """
    Get a specific configuration setting.

    Args:
        key: Configuration key (supports nested keys with dots, e.g., 'cache.enabled')
        project_path: Path to project root (optional)
        default: Default value if key not found

    Returns:
        Configuration value

    Examples:
        enabled = get_setting('cache.enabled')
        ttl = get_setting('cache.ttl_hours', default=24)
    """
    config = load_config(project_path)

    # Support nested keys
    keys = key.split('.')
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default if default is not None else None

    return value


def get_cache_config(project_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get cache configuration section.

    Args:
        project_path: Path to project root (optional)

    Returns:
        Dictionary with cache configuration settings

    Example:
        cache_config = get_cache_config()
        if cache_config['enabled']:
            cache_dir = cache_config.get('directory')
            ttl_hours = cache_config['ttl_hours']
    """
    config = load_config(project_path)
    return config.get("cache", DEFAULT_CONFIG["cache"])


def is_cache_enabled(project_path: Optional[Path] = None) -> bool:
    """
    Check if caching is enabled.

    Args:
        project_path: Path to project root (optional)

    Returns:
        True if caching is enabled
    """
    return get_setting("cache.enabled", project_path, default=True)
