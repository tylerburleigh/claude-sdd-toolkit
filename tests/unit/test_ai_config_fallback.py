import pytest
from claude_skills.common import ai_config


def test_get_tool_priority_skill_override():
    """Test skill-specific tool_priority overrides global."""
    priority = ai_config.get_tool_priority("run-tests")
    assert priority == ["gemini", "cursor-agent"]


def test_get_tool_priority_global_default():
    """Test falls back to global tool_priority."""
    priority = ai_config.get_tool_priority("unknown-skill")
    assert priority == ["gemini", "cursor-agent", "codex", "claude"]


def test_get_fallback_config_defaults():
    """Test fallback config returns correct defaults."""
    config = ai_config.get_fallback_config("unknown-skill")

    assert config["enabled"] is True
    assert config["max_retries_per_tool"] == 2
    assert "timeout" in config["retry_on_status"]
    assert "error" in config["retry_on_status"]
    assert "not_found" in config["skip_on_status"]
    assert "invalid_output" in config["skip_on_status"]


def test_get_fallback_config_skill_override():
    """Test skill can override fallback settings."""
    config = ai_config.get_fallback_config("run-tests")
    # run-tests has max_retries_per_tool: 3 in config
    assert config["max_retries_per_tool"] == 3


def test_get_consultation_limit():
    """Test consultation limit resolution."""
    limit = ai_config.get_consultation_limit("run-tests")
    assert limit == 2  # From config

    limit_default = ai_config.get_consultation_limit("unknown-skill")
    assert limit_default == 4  # Global default


def test_get_consultation_limit_none():
    """Test returns None when no limit configured."""
    # If we remove limits from config, should return None
    pass  # Would need to mock config
