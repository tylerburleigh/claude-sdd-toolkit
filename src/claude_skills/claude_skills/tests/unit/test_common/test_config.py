from __future__ import annotations

"""
Legacy configuration tests migrated from `tests/unit/test_config.py`.
"""

import json
import os
from pathlib import Path
from typing import Iterator

import pytest

from claude_skills.common.config import (
    DEFAULT_CONFIG,
    get_cache_config,
    get_setting,
    is_cache_enabled,
    load_config,
)


pytestmark = pytest.mark.unit


@pytest.fixture
def temp_config_dir(tmp_path: Path) -> Path:
    config_dir = tmp_path / ".claude"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    env_vars = [
        "SDD_CACHE_ENABLED",
        "SDD_CACHE_DIR",
        "SDD_CACHE_TTL_HOURS",
        "SDD_CACHE_MAX_SIZE_MB",
        "SDD_CACHE_AUTO_CLEANUP",
    ]
    original = {var: os.environ.get(var) for var in env_vars}
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)
    try:
        yield
    finally:
        for var, value in original.items():
            if value is None:
                monkeypatch.delenv(var, raising=False)
            else:
                monkeypatch.setenv(var, value)


def test_load_config_defaults(tmp_path: Path, clean_env: None) -> None:
    config = load_config(project_path=tmp_path)
    assert config == DEFAULT_CONFIG


def test_load_config_from_file(temp_config_dir: Path, clean_env: None) -> None:
    config_file = temp_config_dir / "config.json"
    custom_config = {"cache": {"enabled": False, "ttl_hours": 48}}
    config_file.write_text(json.dumps(custom_config))

    config = load_config(project_path=temp_config_dir.parent)
    assert config["cache"]["enabled"] is False
    assert config["cache"]["ttl_hours"] == 48
    assert "max_size_mb" in config["cache"]


def test_load_config_merges_with_defaults(temp_config_dir: Path, clean_env: None) -> None:
    config_file = temp_config_dir / "config.json"
    partial_config = {"cache": {"ttl_hours": 12}}
    config_file.write_text(json.dumps(partial_config))

    config = load_config(project_path=temp_config_dir.parent)
    assert config["cache"]["ttl_hours"] == 12
    assert config["cache"]["enabled"] is True
    assert config["cache"]["max_size_mb"] == 1000


def test_load_config_invalid_json(temp_config_dir: Path, clean_env: None) -> None:
    config_file = temp_config_dir / "config.json"
    config_file.write_text("{invalid json}")

    config = load_config(project_path=temp_config_dir.parent)
    assert config == DEFAULT_CONFIG


def test_env_override_cache_enabled(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_env: None) -> None:
    monkeypatch.setenv("SDD_CACHE_ENABLED", "false")
    config = load_config(project_path=tmp_path)
    assert config["cache"]["enabled"] is False


def test_env_override_cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_env: None) -> None:
    custom_dir = "/custom/cache/dir"
    monkeypatch.setenv("SDD_CACHE_DIR", custom_dir)
    config = load_config(project_path=tmp_path)
    assert config["cache"]["directory"] == custom_dir


def test_env_override_ttl_hours(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_env: None) -> None:
    monkeypatch.setenv("SDD_CACHE_TTL_HOURS", "48")
    config = load_config(project_path=tmp_path)
    assert config["cache"]["ttl_hours"] == 48.0


def test_env_override_max_size(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_env: None) -> None:
    monkeypatch.setenv("SDD_CACHE_MAX_SIZE_MB", "500")
    config = load_config(project_path=tmp_path)
    assert config["cache"]["max_size_mb"] == 500.0


def test_env_override_auto_cleanup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_env: None) -> None:
    monkeypatch.setenv("SDD_CACHE_AUTO_CLEANUP", "false")
    config = load_config(project_path=tmp_path)
    assert config["cache"]["auto_cleanup"] is False


def test_env_overrides_config_file(temp_config_dir: Path, monkeypatch: pytest.MonkeyPatch, clean_env: None) -> None:
    config_file = temp_config_dir / "config.json"
    file_config = {"cache": {"enabled": True, "ttl_hours": 24}}
    config_file.write_text(json.dumps(file_config))

    monkeypatch.setenv("SDD_CACHE_ENABLED", "false")
    monkeypatch.setenv("SDD_CACHE_TTL_HOURS", "48")

    config = load_config(project_path=temp_config_dir.parent)
    assert config["cache"]["enabled"] is False
    assert config["cache"]["ttl_hours"] == 48.0


def test_get_setting_basic(tmp_path: Path, clean_env: None) -> None:
    enabled = get_setting("cache.enabled", project_path=tmp_path)
    assert enabled is True


def test_get_setting_nested(tmp_path: Path, clean_env: None) -> None:
    ttl = get_setting("cache.ttl_hours", project_path=tmp_path)
    assert ttl == 24


def test_get_setting_with_default(tmp_path: Path, clean_env: None) -> None:
    value = get_setting("nonexistent.key", project_path=tmp_path, default="default_value")
    assert value == "default_value"


def test_get_setting_nonexistent(tmp_path: Path, clean_env: None) -> None:
    value = get_setting("nonexistent.key", project_path=tmp_path)
    assert value is None


def test_get_cache_config(tmp_path: Path, clean_env: None) -> None:
    cache_config = get_cache_config(project_path=tmp_path)
    assert "enabled" in cache_config
    assert "directory" in cache_config
    assert "ttl_hours" in cache_config
    assert "max_size_mb" in cache_config
    assert "auto_cleanup" in cache_config


def test_is_cache_enabled_default(tmp_path: Path, clean_env: None) -> None:
    assert is_cache_enabled(project_path=tmp_path) is True


def test_is_cache_enabled_disabled(temp_config_dir: Path, clean_env: None) -> None:
    config_file = temp_config_dir / "config.json"
    config_file.write_text(json.dumps({"cache": {"enabled": False}}))
    assert is_cache_enabled(project_path=temp_config_dir.parent) is False


def test_is_cache_enabled_env_override(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clean_env: None) -> None:
    monkeypatch.setenv("SDD_CACHE_ENABLED", "false")
    assert is_cache_enabled(project_path=tmp_path) is False
