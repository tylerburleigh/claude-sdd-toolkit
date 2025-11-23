"""
Tests for the Claude provider implementation.
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional

import pytest

from claude_skills.common.providers import (
    GenerationRequest,
    ProviderExecutionError,
    ProviderHooks,
)
from claude_skills.common.providers.claude import (
    ALLOWED_TOOLS,
    CLAUDE_METADATA,
    ClaudeProvider,
    DISALLOWED_TOOLS,
    SHELL_COMMAND_WARNING,
    create_provider,
    is_claude_available,
)


class FakeProcess:
    def __init__(self, *, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _payload(content: str = "Claude output", model: str = "claude-sonnet-4-5-20250929") -> str:
    """Create a mock Claude CLI JSON response."""
    return json.dumps(
        {
            "type": "result",
            "subtype": "success",
            "result": content,
            "usage": {
                "input_tokens": 15,
                "output_tokens": 75,
                "cached_input_tokens": 5,
            },
            "modelUsage": {
                model: {
                    "inputTokens": 15,
                    "outputTokens": 75,
                    "cachedInputTokens": 5,
                }
            },
            "duration_ms": 1234,
            "total_cost_usd": 0.0042,
        }
    )


def test_claude_provider_executes_command_with_read_only_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that Claude provider builds commands with read-only tool restrictions."""
    captured: Dict[str, object] = {}
    stream_chunks: List[str] = []

    def runner(command, *, timeout=None, env=None):
        captured["command"] = list(command)
        captured["timeout"] = timeout
        captured["env"] = env
        return FakeProcess(stdout=_payload())

    provider = ClaudeProvider(
        CLAUDE_METADATA,
        ProviderHooks(on_stream_chunk=lambda chunk: stream_chunks.append(chunk.content)),
        model="sonnet",
        runner=runner,
        binary="claude",
    )

    request = GenerationRequest(
        prompt="Analyze this code",
        system_prompt="You are a code reviewer",
        metadata={},
        stream=True,
        timeout=60,
    )

    result = provider.generate(request)

    # Verify command structure with read-only tool restrictions
    command = captured["command"]
    assert command[0] == "claude"
    assert command[1] == "--print"
    assert command[2] == "Analyze this code"
    assert "--output-format" in command
    assert "json" in command
    assert "--allowed-tools" in command
    assert "--disallowed-tools" in command
    assert "--system-prompt" in command

    # Verify system prompt includes both custom prompt and security warning
    system_prompt_index = command.index("--system-prompt") + 1
    system_prompt_value = command[system_prompt_index]
    assert "You are a code reviewer" in system_prompt_value
    assert SHELL_COMMAND_WARNING.strip() in system_prompt_value

    # Verify all allowed tools are in the command
    for tool in ALLOWED_TOOLS:
        assert tool in command

    # Verify all disallowed tools are in the command
    for tool in DISALLOWED_TOOLS:
        assert tool in command

    assert captured["timeout"] == 60
    assert stream_chunks == ["Claude output"]
    assert result.content == "Claude output"
    assert result.model_fqn.startswith("claude:")
    assert result.usage.input_tokens == 15
    assert result.usage.output_tokens == 75
    assert result.usage.cached_input_tokens == 5
    assert result.usage.total_tokens == 90


def test_claude_provider_streams_content(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test streaming functionality."""
    stream_chunks: List[str] = []

    provider = ClaudeProvider(
        CLAUDE_METADATA,
        ProviderHooks(on_stream_chunk=lambda chunk: stream_chunks.append(chunk.content)),
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload("Streaming response")),
    )

    request = GenerationRequest(
        prompt="Test streaming",
        stream=True,
        metadata={},
    )

    result = provider.generate(request)

    assert stream_chunks == ["Streaming response"]
    assert result.content == "Streaming response"


def test_claude_provider_extracts_usage_metadata() -> None:
    """Test that usage statistics and cost metadata are properly extracted."""
    provider = ClaudeProvider(
        CLAUDE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
    )

    request = GenerationRequest(prompt="test", metadata={})
    result = provider.generate(request)

    assert result.usage.input_tokens == 15
    assert result.usage.output_tokens == 75
    assert result.usage.cached_input_tokens == 5
    assert result.usage.total_tokens == 90
    assert result.usage.metadata["duration_ms"] == 1234
    assert result.usage.metadata["total_cost_usd"] == 0.0042
    assert "model_usage" in result.usage.metadata


def test_claude_provider_rejects_unsupported_fields() -> None:
    """Test that Claude provider rejects unsupported request fields."""
    provider = ClaudeProvider(
        CLAUDE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
    )

    request = GenerationRequest(
        prompt="test",
        temperature=0.7,
        max_tokens=1000,
        attachments=["file.txt"],
        continuation_id="xyz",
        metadata={},
    )

    with pytest.raises(ProviderExecutionError) as excinfo:
        provider.generate(request)

    assert "does not support" in str(excinfo.value)


def test_claude_provider_validates_json_output() -> None:
    """Test that invalid JSON output raises an error."""
    provider = ClaudeProvider(
        CLAUDE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout="not-valid-json"),
    )

    with pytest.raises(ProviderExecutionError) as excinfo:
        provider.generate(GenerationRequest(prompt="test"))

    assert "invalid JSON" in str(excinfo.value)


def test_claude_provider_validates_empty_output() -> None:
    """Test that empty output raises an error."""
    provider = ClaudeProvider(
        CLAUDE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=""),
    )

    with pytest.raises(ProviderExecutionError) as excinfo:
        provider.generate(GenerationRequest(prompt="test"))

    assert "empty output" in str(excinfo.value)


def test_claude_provider_handles_cli_errors() -> None:
    """Test that CLI errors are properly handled."""
    provider = ClaudeProvider(
        CLAUDE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(
            stdout="",
            stderr="Claude CLI error: invalid arguments",
            returncode=1,
        ),
    )

    with pytest.raises(ProviderExecutionError) as excinfo:
        provider.generate(GenerationRequest(prompt="test"))

    assert "exited with code 1" in str(excinfo.value)
    assert "invalid arguments" in str(excinfo.value)


def test_claude_provider_supports_sonnet_model() -> None:
    """Test that Sonnet model is properly supported."""
    provider = ClaudeProvider(
        CLAUDE_METADATA,
        ProviderHooks(),
        model="sonnet",
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
    )

    result = provider.generate(GenerationRequest(prompt="test"))
    assert result.model_fqn.startswith("claude:")


def test_claude_provider_supports_haiku_model() -> None:
    """Test that Haiku model is properly supported."""
    provider = ClaudeProvider(
        CLAUDE_METADATA,
        ProviderHooks(),
        model="haiku",
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
    )

    result = provider.generate(GenerationRequest(prompt="test"))
    assert result.model_fqn.startswith("claude:")


def test_claude_provider_rejects_unsupported_model() -> None:
    """Test that unsupported models are rejected."""
    with pytest.raises(ProviderExecutionError) as excinfo:
        ClaudeProvider(
            CLAUDE_METADATA,
            ProviderHooks(),
            model="claude-opus-5",  # Invalid model
            runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
        )

    assert "Unsupported Claude model" in str(excinfo.value)


def test_claude_provider_respects_model_override_in_request() -> None:
    """Test that model can be overridden via request metadata."""
    captured: Dict[str, object] = {}

    def runner(command, *, timeout=None, env=None):
        captured["command"] = list(command)
        return FakeProcess(stdout=_payload())

    provider = ClaudeProvider(
        CLAUDE_METADATA,
        ProviderHooks(),
        model="sonnet",
        runner=runner,
    )

    request = GenerationRequest(
        prompt="test",
        metadata={"model": "haiku"},
    )

    provider.generate(request)

    command = captured["command"]
    assert "--model" in command
    assert "haiku" in command


def test_create_provider_injects_custom_runner_and_model() -> None:
    """Test factory function with custom dependencies."""
    runner_called = False

    def runner(command, *, timeout=None, env=None):
        nonlocal runner_called
        runner_called = True
        return FakeProcess(stdout=_payload(content="Factory test"))

    provider = create_provider(
        hooks=ProviderHooks(),
        dependencies={"runner": runner},
        overrides={"model": "sonnet", "binary": "claude"},
    )

    result = provider.generate(GenerationRequest(prompt="test"))
    assert runner_called is True
    assert result.content == "Factory test"
    assert result.model_fqn.startswith("claude:")


def test_create_provider_respects_timeout_override() -> None:
    """Test that timeout override is respected."""
    captured: Dict[str, object] = {}

    def runner(command, *, timeout=None, env=None):
        captured["timeout"] = timeout
        return FakeProcess(stdout=_payload())

    provider = create_provider(
        hooks=ProviderHooks(),
        dependencies={"runner": runner},
        overrides={"timeout": 500},
    )

    provider.generate(GenerationRequest(prompt="test"))
    assert captured["timeout"] == 500


def test_is_claude_available_respects_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that environment override controls availability detection."""
    monkeypatch.setenv("CLAUDE_CLI_AVAILABLE_OVERRIDE", "0")
    assert is_claude_available() is False

    monkeypatch.setenv("CLAUDE_CLI_AVAILABLE_OVERRIDE", "1")
    assert is_claude_available() is True


def test_claude_provider_uses_default_model_when_none_specified() -> None:
    """Test that default model is used when no model is specified."""
    provider = ClaudeProvider(
        CLAUDE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
    )

    result = provider.generate(GenerationRequest(prompt="test"))
    assert result.model_fqn.startswith("claude:")


def test_claude_provider_includes_system_prompt_in_command() -> None:
    """Test that system prompts are properly included in commands with security warning."""
    captured: Dict[str, object] = {}

    def runner(command, *, timeout=None, env=None):
        captured["command"] = list(command)
        return FakeProcess(stdout=_payload())

    provider = ClaudeProvider(
        CLAUDE_METADATA,
        ProviderHooks(),
        runner=runner,
    )

    request = GenerationRequest(
        prompt="User prompt",
        system_prompt="Custom system instructions",
        metadata={},
    )

    provider.generate(request)

    command = captured["command"]
    assert "--system-prompt" in command

    # Verify both custom prompt and security warning are included
    system_prompt_index = command.index("--system-prompt") + 1
    system_prompt_value = command[system_prompt_index]
    assert "Custom system instructions" in system_prompt_value
    assert SHELL_COMMAND_WARNING.strip() in system_prompt_value


def test_claude_provider_uses_default_timeout() -> None:
    """Test that default timeout of 360s is used."""
    captured: Dict[str, object] = {}

    def runner(command, *, timeout=None, env=None):
        captured["timeout"] = timeout
        return FakeProcess(stdout=_payload())

    provider = ClaudeProvider(
        CLAUDE_METADATA,
        ProviderHooks(),
        runner=runner,
    )

    provider.generate(GenerationRequest(prompt="test"))
    assert captured["timeout"] == 360  # DEFAULT_TIMEOUT_SECONDS


def test_claude_metadata_has_read_only_flag() -> None:
    """Test that metadata correctly indicates read-only restrictions."""
    assert CLAUDE_METADATA.security_flags["writes_allowed"] is False
    assert CLAUDE_METADATA.security_flags["read_only"] is True
    assert CLAUDE_METADATA.extra["allowed_tools"] == ALLOWED_TOOLS


def test_claude_provider_extracts_model_from_model_usage() -> None:
    """Test that model name is extracted from modelUsage field."""
    custom_model = "claude-sonnet-4-5-custom"
    payload = _payload(model=custom_model)

    provider = ClaudeProvider(
        CLAUDE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=payload),
    )

    result = provider.generate(GenerationRequest(prompt="test"))
    assert result.model_fqn == f"claude:{custom_model}"


def test_claude_provider_blocks_web_operations() -> None:
    """Test that WebSearch and WebFetch are explicitly blocked to prevent data exfiltration."""
    # Verify WebSearch and WebFetch are NOT in allowed tools
    assert "WebSearch" not in ALLOWED_TOOLS
    assert "WebFetch" not in ALLOWED_TOOLS

    # Verify WebSearch and WebFetch ARE in disallowed tools
    assert "WebSearch" in DISALLOWED_TOOLS
    assert "WebFetch" in DISALLOWED_TOOLS

    # Verify the tools are actually blocked in the command
    captured: Dict[str, object] = {}

    def runner(command, *, timeout=None, env=None):
        captured["command"] = list(command)
        return FakeProcess(stdout=_payload())

    provider = ClaudeProvider(
        CLAUDE_METADATA,
        ProviderHooks(),
        runner=runner,
    )

    provider.generate(GenerationRequest(prompt="test"))

    command = captured["command"]
    disallowed_index = command.index("--disallowed-tools") + 1
    disallowed_end = command.index("--system-prompt") if "--system-prompt" in command else len(command)
    disallowed_tools_in_command = command[disallowed_index:disallowed_end]

    # Verify WebSearch and WebFetch are in the disallowed tools section
    assert "WebSearch" in disallowed_tools_in_command
    assert "WebFetch" in disallowed_tools_in_command
