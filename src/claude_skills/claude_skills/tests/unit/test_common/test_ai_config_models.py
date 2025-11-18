from __future__ import annotations

from collections import OrderedDict
from typing import Any, Callable, Dict

import pytest

from claude_skills.common import ai_config


pytestmark = pytest.mark.unit


@pytest.fixture
def set_skill_config(monkeypatch: pytest.MonkeyPatch) -> Callable[[Dict[str, Any]], None]:
    """Provide a helper for overriding load_skill_config within tests."""

    def _apply(config: Dict[str, Any]) -> None:
        monkeypatch.setattr(
            ai_config,
            "load_skill_config",
            lambda _: config,
        )

    return _apply


def test_resolve_tool_model_prefers_cli_override_string(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    set_skill_config({"models": {}})
    result = ai_config.resolve_tool_model("some-skill", "gemini", override="cli-model")
    assert result == "cli-model"


def test_resolve_tool_model_prefers_cli_override_map(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    set_skill_config({"models": {}})
    override = {"gemini": "per-tool", "default": "ignored"}
    result = ai_config.resolve_tool_model("skill", "gemini", override=override)
    assert result == "per-tool"


def test_resolve_tool_model_uses_failure_type_override(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    set_skill_config(
        {
            "models": {
                "gemini": {"priority": ["base-gemini"]},
                "overrides": {
                    "failure_type": {
                        "assertion": {"gemini": "assertion-model"},
                        "timeout": {"gemini": {"priority": ["timeout-model"]}},
                    }
                },
            }
        }
    )

    result = ai_config.resolve_tool_model(
        "skill",
        "gemini",
        context={"failure_type": "assertion"},
    )
    assert result == "assertion-model"


def test_resolve_tool_model_falls_back_to_default_priority(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    set_skill_config({"models": {"gemini": " "}})
    result = ai_config.resolve_tool_model("skill", "gemini")
    assert result == ai_config.DEFAULT_MODELS["gemini"]["priority"][0]


def test_resolve_tool_model_returns_none_for_unknown_tool(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    set_skill_config({"models": {}})
    result = ai_config.resolve_tool_model("skill", "nonexistent")
    assert result is None


def test_resolve_tool_model_handles_empty_priority_lists(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    set_skill_config({"models": {"gemini": []}})
    result = ai_config.resolve_tool_model("skill", "gemini")
    assert result == ai_config.DEFAULT_MODELS["gemini"]["priority"][0]


def test_resolve_models_for_tools_shared_context_override(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    set_skill_config(
        {
            "models": {
                "gemini": {"priority": ["base-gemini"]},
                "cursor-agent": {"priority": ["base-cursor"]},
                "overrides": {
                    "failure_type": {
                        "assertion": {
                            "gemini": "gemini-assertion",
                            "cursor-agent": "cursor-assertion",
                        }
                    }
                },
            }
        }
    )

    models = ai_config.resolve_models_for_tools(
        "skill",
        ["gemini", "cursor-agent"],
        context={"failure_type": "assertion"},
    )
    assert models == OrderedDict(
        [
            ("gemini", "gemini-assertion"),
            ("cursor-agent", "cursor-assertion"),
        ]
    )


def test_resolve_models_for_tools_tool_specific_context(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    set_skill_config(
        {
            "models": {
                "gemini": {"priority": ["base-gemini"]},
                "cursor-agent": {"priority": ["base-cursor"]},
                "overrides": {
                    "failure_type": {
                        "assertion": {"gemini": "gemini-assertion"},
                        "timeout": {"cursor-agent": "cursor-timeout"},
                    }
                },
            }
        }
    )

    context = {
        "gemini": {"failure_type": "assertion"},
        "cursor-agent": {"failure_type": "timeout"},
    }

    models = ai_config.resolve_models_for_tools(
        "skill",
        ["gemini", "cursor-agent"],
        context=context,
    )
    assert models == OrderedDict(
        [
            ("gemini", "gemini-assertion"),
            ("cursor-agent", "cursor-timeout"),
        ]
    )


def test_resolve_models_for_tools_applies_override_map(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    set_skill_config({"models": {}})
    override = {"gemini": "cli-gemini", "cursor-agent": "cli-cursor"}
    models = ai_config.resolve_models_for_tools(
        "skill",
        ["gemini", "cursor-agent"],
        override=override,
    )
    assert models == OrderedDict(
        [
            ("gemini", "cli-gemini"),
            ("cursor-agent", "cli-cursor"),
        ]
    )


def test_resolve_models_for_tools_handles_default_override(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    set_skill_config({"models": {"gemini": ["base"], "cursor-agent": ["alt"]}})
    models = ai_config.resolve_models_for_tools(
        "skill",
        ["gemini", "cursor-agent"],
        override="global-model",
    )
    assert models == OrderedDict(
        [
            ("gemini", "global-model"),
            ("cursor-agent", "global-model"),
        ]
    )


def test_resolve_models_for_tools_empty_input_returns_empty(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    set_skill_config({"models": {}})
    models = ai_config.resolve_models_for_tools("skill", [])
    assert models == OrderedDict()


def test_get_enabled_tools_uses_provider_section(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ai_config,
        "load_skill_config",
        lambda _skill: {"providers": {"gemini": {"enabled": True}, "codex": {"enabled": False}}},
    )
    enabled = ai_config.get_enabled_tools("skill")
    assert "gemini" in enabled
    assert "codex" not in enabled


def test_get_tool_config_reads_from_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ai_config,
        "load_skill_config",
        lambda _skill: {"providers": {"custom": {"enabled": True}}},
    )
    config = ai_config.get_tool_config("skill", "custom")
    assert config == {"enabled": True}


def test_load_skill_config_promotes_tools_to_providers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ai_config,
        "load_global_config",
        lambda: {"tools": {"custom": {"enabled": False}}},
    )
    config = ai_config.load_skill_config("skill")
    assert config["providers"]["custom"]["enabled"] is False
    assert config["tools"]["custom"]["enabled"] is False


def test_resolve_tool_model_uses_skill_level_default_string(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    """Test that skill-level simple string defaults work."""
    set_skill_config(
        {
            "models": {
                "gemini": "skill-default-gemini",
                "codex": "skill-default-codex",
            }
        }
    )
    result = ai_config.resolve_tool_model("code-doc", "gemini")
    assert result == "skill-default-gemini"

    result = ai_config.resolve_tool_model("code-doc", "codex")
    assert result == "skill-default-codex"


def test_resolve_tool_model_skill_default_overrides_global(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    """Test that skill-level defaults override global defaults."""
    # Global defaults from DEFAULT_MODELS would be gemini-2.5-flash
    # But skill config should override it
    set_skill_config(
        {
            "models": {
                "gemini": "pro",  # Override global default
            }
        }
    )
    result = ai_config.resolve_tool_model("run-tests", "gemini")
    assert result == "pro"
    assert result != ai_config.DEFAULT_MODELS["gemini"]["priority"][0]


def test_resolve_tool_model_contextual_override_beats_skill_default(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    """Test that contextual overrides take precedence over skill-level defaults."""
    set_skill_config(
        {
            "models": {
                "gemini": "skill-default",  # Skill-level default
                "overrides": {
                    "failure_type": {
                        "assertion": {"gemini": "assertion-specific"}
                    }
                },
            }
        }
    )
    # Without context, should use skill default
    result = ai_config.resolve_tool_model("run-tests", "gemini")
    assert result == "skill-default"

    # With context, should use contextual override
    result = ai_config.resolve_tool_model(
        "run-tests", "gemini", context={"failure_type": "assertion"}
    )
    assert result == "assertion-specific"


def test_resolve_tool_model_skill_default_list(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    """Test that skill-level defaults can be lists (takes first item)."""
    set_skill_config(
        {
            "models": {
                "gemini": ["gemini-first", "gemini-second"],
            }
        }
    )
    result = ai_config.resolve_tool_model("skill", "gemini")
    assert result == "gemini-first"


def test_resolve_tool_model_fallback_to_global_when_skill_default_empty(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    """Test fallback to global defaults when skill default is empty."""
    set_skill_config(
        {
            "models": {
                "gemini": "",  # Empty string should be ignored
            }
        }
    )
    result = ai_config.resolve_tool_model("skill", "gemini")
    # Should fall back to DEFAULT_MODELS
    assert result == ai_config.DEFAULT_MODELS["gemini"]["priority"][0]


def test_resolve_tool_model_case_insensitive_skill_default(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    """Test that skill-level defaults work with lowercase tool names."""
    set_skill_config(
        {
            "models": {
                "gemini": "gemini-model",  # Lowercase key
            }
        }
    )
    # Should work with both cases
    result = ai_config.resolve_tool_model("skill", "gemini")
    assert result == "gemini-model"

    result = ai_config.resolve_tool_model("skill", "Gemini")
    assert result == "gemini-model"


def test_resolve_models_for_tools_respects_skill_defaults(
    set_skill_config: Callable[[Dict[str, Any]], None]
) -> None:
    """Test that resolve_models_for_tools uses skill-level defaults."""
    set_skill_config(
        {
            "models": {
                "gemini": "skill-gemini",
                "codex": "skill-codex",
                "cursor-agent": "skill-cursor",
            }
        }
    )
    models = ai_config.resolve_models_for_tools(
        "code-doc",
        ["gemini", "codex", "cursor-agent"],
    )
    assert models == OrderedDict(
        [
            ("gemini", "skill-gemini"),
            ("codex", "skill-codex"),
            ("cursor-agent", "skill-cursor"),
        ]
    )
