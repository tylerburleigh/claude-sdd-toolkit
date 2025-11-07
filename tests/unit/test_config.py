"""
Unit tests for configuration management.
"""

import json
import os
import pytest
from pathlib import Path
from claude_skills.common.config import (
    load_config,
    get_setting,
    get_cache_config,
    is_cache_enabled,
    DEFAULT_CONFIG
)


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary .claude directory."""
    config_dir = tmp_path / ".claude"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def clean_env(monkeypatch):
    """Clean environment variables for testing."""
    env_vars = [
        "SDD_CACHE_ENABLED",
        "SDD_CACHE_DIR",
        "SDD_CACHE_TTL_HOURS",
        "SDD_CACHE_MAX_SIZE_MB",
        "SDD_CACHE_AUTO_CLEANUP"
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)


def test_load_config_defaults(tmp_path, clean_env):
    """Test loading config with no config file uses defaults."""
    config = load_config(project_path=tmp_path)
    assert config == DEFAULT_CONFIG


def test_load_config_from_file(temp_config_dir, clean_env):
    """Test loading config from file."""
    config_file = temp_config_dir / "config.json"
    custom_config = {
        "cache": {
            "enabled": False,
            "ttl_hours": 48
        }
    }
    config_file.write_text(json.dumps(custom_config))

    config = load_config(project_path=temp_config_dir.parent)

    assert config["cache"]["enabled"] is False
    assert config["cache"]["ttl_hours"] == 48
    # Defaults should still be present
    assert "max_size_mb" in config["cache"]


def test_load_config_merges_with_defaults(temp_config_dir, clean_env):
    """Test partial config is merged with defaults."""
    config_file = temp_config_dir / "config.json"
    partial_config = {
        "cache": {
            "ttl_hours": 12
        }
    }
    config_file.write_text(json.dumps(partial_config))

    config = load_config(project_path=temp_config_dir.parent)

    # Custom value
    assert config["cache"]["ttl_hours"] == 12
    # Default values still present
    assert config["cache"]["enabled"] is True
    assert config["cache"]["max_size_mb"] == 1000


def test_load_config_invalid_json(temp_config_dir, clean_env):
    """Test loading config with invalid JSON uses defaults."""
    config_file = temp_config_dir / "config.json"
    config_file.write_text("{invalid json}")

    config = load_config(project_path=temp_config_dir.parent)
    assert config == DEFAULT_CONFIG


def test_env_override_cache_enabled(tmp_path, monkeypatch, clean_env):
    """Test environment variable overrides cache enabled setting."""
    monkeypatch.setenv("SDD_CACHE_ENABLED", "false")

    config = load_config(project_path=tmp_path)
    assert config["cache"]["enabled"] is False


def test_env_override_cache_dir(tmp_path, monkeypatch, clean_env):
    """Test environment variable overrides cache directory."""
    custom_dir = "/custom/cache/dir"
    monkeypatch.setenv("SDD_CACHE_DIR", custom_dir)

    config = load_config(project_path=tmp_path)
    assert config["cache"]["directory"] == custom_dir


def test_env_override_ttl_hours(tmp_path, monkeypatch, clean_env):
    """Test environment variable overrides TTL hours."""
    monkeypatch.setenv("SDD_CACHE_TTL_HOURS", "48")

    config = load_config(project_path=tmp_path)
    assert config["cache"]["ttl_hours"] == 48.0


def test_env_override_max_size(tmp_path, monkeypatch, clean_env):
    """Test environment variable overrides max size."""
    monkeypatch.setenv("SDD_CACHE_MAX_SIZE_MB", "500")

    config = load_config(project_path=tmp_path)
    assert config["cache"]["max_size_mb"] == 500.0


def test_env_override_auto_cleanup(tmp_path, monkeypatch, clean_env):
    """Test environment variable overrides auto cleanup."""
    monkeypatch.setenv("SDD_CACHE_AUTO_CLEANUP", "false")

    config = load_config(project_path=tmp_path)
    assert config["cache"]["auto_cleanup"] is False


def test_env_overrides_config_file(temp_config_dir, monkeypatch, clean_env):
    """Test environment variables take precedence over config file."""
    config_file = temp_config_dir / "config.json"
    file_config = {
        "cache": {
            "enabled": True,
            "ttl_hours": 24
        }
    }
    config_file.write_text(json.dumps(file_config))

    # Override with env var
    monkeypatch.setenv("SDD_CACHE_ENABLED", "false")
    monkeypatch.setenv("SDD_CACHE_TTL_HOURS", "48")

    config = load_config(project_path=temp_config_dir.parent)

    # Env vars should win
    assert config["cache"]["enabled"] is False
    assert config["cache"]["ttl_hours"] == 48.0


def test_get_setting_basic(tmp_path, clean_env):
    """Test getting a specific setting."""
    enabled = get_setting("cache.enabled", project_path=tmp_path)
    assert enabled is True


def test_get_setting_nested(tmp_path, clean_env):
    """Test getting nested setting."""
    ttl = get_setting("cache.ttl_hours", project_path=tmp_path)
    assert ttl == 24


def test_get_setting_with_default(tmp_path, clean_env):
    """Test getting setting with default value."""
    value = get_setting("nonexistent.key", project_path=tmp_path, default="default_value")
    assert value == "default_value"


def test_get_setting_nonexistent(tmp_path, clean_env):
    """Test getting nonexistent setting returns None."""
    value = get_setting("nonexistent.key", project_path=tmp_path)
    assert value is None


def test_get_cache_config(tmp_path, clean_env):
    """Test getting cache configuration section."""
    cache_config = get_cache_config(project_path=tmp_path)

    assert "enabled" in cache_config
    assert "directory" in cache_config
    assert "ttl_hours" in cache_config
    assert "max_size_mb" in cache_config
    assert "auto_cleanup" in cache_config


def test_is_cache_enabled_default(tmp_path, clean_env):
    """Test cache is enabled by default."""
    assert is_cache_enabled(project_path=tmp_path) is True


def test_is_cache_enabled_disabled(temp_config_dir, clean_env):
    """Test cache disabled via config file."""
    config_file = temp_config_dir / "config.json"
    config = {
        "cache": {
            "enabled": False
        }
    }
    config_file.write_text(json.dumps(config))

    assert is_cache_enabled(project_path=temp_config_dir.parent) is False


def test_is_cache_enabled_env_override(tmp_path, monkeypatch, clean_env):
    """Test cache disabled via environment variable."""
    monkeypatch.setenv("SDD_CACHE_ENABLED", "false")
    assert is_cache_enabled(project_path=tmp_path) is False


def test_config_validation_invalid_ttl(temp_config_dir, clean_env):
    """Test invalid TTL value is rejected."""
    config_file = temp_config_dir / "config.json"
    invalid_config = {
        "cache": {
            "ttl_hours": -5  # Invalid: negative
        }
    }
    config_file.write_text(json.dumps(invalid_config))

    config = load_config(project_path=temp_config_dir.parent)

    # Should use default
    assert config["cache"]["ttl_hours"] == DEFAULT_CONFIG["cache"]["ttl_hours"]


def test_config_validation_invalid_max_size(temp_config_dir, clean_env):
    """Test invalid max_size value is rejected."""
    config_file = temp_config_dir / "config.json"
    invalid_config = {
        "cache": {
            "max_size_mb": 0  # Invalid: zero
        }
    }
    config_file.write_text(json.dumps(invalid_config))

    config = load_config(project_path=temp_config_dir.parent)

    # Should use default
    assert config["cache"]["max_size_mb"] == DEFAULT_CONFIG["cache"]["max_size_mb"]
