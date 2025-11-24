from __future__ import annotations

from claude_skills.run_tests import cli


def test_parse_model_override_returns_none_when_absent() -> None:
    assert cli._parse_model_override(None) is None
    assert cli._parse_model_override([]) is None


def test_parse_model_override_handles_global_value() -> None:
    assert cli._parse_model_override(["gpt-5.1-codex"]) == "gpt-5.1-codex"


def test_parse_model_override_handles_per_tool_entries() -> None:
    result = cli._parse_model_override(["gemini=gemini-pro", "codex:codex-dev"])
    assert result == {"gemini": "gemini-pro", "codex": "codex-dev"}


def test_parse_model_override_combines_per_tool_with_default() -> None:
    result = cli._parse_model_override(["gemini=model-a", "cursor-agent=model-b", "universal-model"])
    assert result == {
        "gemini": "model-a",
        "cursor-agent": "model-b",
        "default": "universal-model",
    }
