"""
Tests for the Gemini provider implementation.
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
from claude_skills.common.providers.gemini import (
    ALLOWED_TOOLS,
    GEMINI_METADATA,
    GeminiProvider,
    PIPED_COMMAND_WARNING,
    create_provider,
    is_gemini_available,
)


class FakeProcess:
    def __init__(self, *, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _payload(content: str = "Gemini output") -> str:
    return json.dumps(
        {
            "response": content,
            "model": "gemini-2.5-flash",
            "stats": {
                "models": {
                    "gemini-2.5-flash": {
                        "tokens": {"prompt": 10, "candidates": 50, "total": 60}
                    }
                }
            },
        }
    )


def test_gemini_provider_executes_command_and_streams(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: Dict[str, object] = {}
    stream_chunks: List[str] = []

    def runner(command, *, timeout=None, env=None):
        captured["command"] = list(command)
        captured["timeout"] = timeout
        captured["env"] = env
        return FakeProcess(stdout=_payload())

    provider = GeminiProvider(
        GEMINI_METADATA,
        ProviderHooks(on_stream_chunk=lambda chunk: stream_chunks.append(chunk.content)),
        model="pro",
        runner=runner,
        binary="gemini",
    )

    request = GenerationRequest(
        prompt="Hello",
        system_prompt="System",
        metadata={},
        stream=True,
        timeout=30,
    )

    result = provider.generate(request)

    # Verify command structure includes allowed tools
    command = captured["command"]
    assert command[0] == "gemini"
    assert "-m" in command
    assert "pro" in command
    assert "--output-format" in command
    assert "json" in command
    assert "-p" in command

    # Verify all allowed tools are included
    allowed_tools_in_command = [
        command[i + 1] for i in range(len(command) - 1) if command[i] == "--allowed-tools"
    ]
    assert len(allowed_tools_in_command) == len(ALLOWED_TOOLS)
    assert set(allowed_tools_in_command) == set(ALLOWED_TOOLS)

    # Verify the prompt includes the piped command warning
    prompt_index = command.index("-p") + 1
    prompt = command[prompt_index]
    assert PIPED_COMMAND_WARNING.strip() in prompt
    assert "System" in prompt
    assert "Hello" in prompt

    assert captured["timeout"] == 30
    assert stream_chunks == ["Gemini output"]
    assert result.content == "Gemini output"
    assert result.model_fqn == "gemini:gemini-2.5-flash"
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 50
    assert result.usage.total_tokens == 60


def test_gemini_provider_rejects_unsupported_fields() -> None:
    provider = GeminiProvider(
        GEMINI_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
    )

    request = GenerationRequest(
        prompt="hi",
        temperature=0.2,
        max_tokens=100,
        attachments=["file.txt"],
        continuation_id="abc",
        metadata={},
    )

    with pytest.raises(ProviderExecutionError) as excinfo:
        provider.generate(request)

    assert "does not support" in str(excinfo.value)


def test_gemini_provider_validates_json_output() -> None:
    provider = GeminiProvider(
        GEMINI_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout="not-json"),
    )

    with pytest.raises(ProviderExecutionError):
        provider.generate(GenerationRequest(prompt="test"))


def test_create_provider_injects_custom_runner_and_model(monkeypatch: pytest.MonkeyPatch) -> None:
    runner_called = False

    def runner(command, *, timeout=None, env=None):
        nonlocal runner_called
        runner_called = True
        return FakeProcess(stdout=_payload(content="Override"))

    provider = create_provider(
        hooks=ProviderHooks(),
        dependencies={"runner": runner},
        overrides={"model": "pro", "binary": "gemini"},
    )

    result = provider.generate(GenerationRequest(prompt="test"))
    assert runner_called is True
    assert result.content == "Override"
    assert result.model_fqn == "gemini:gemini-2.5-flash"


def test_is_gemini_available_respects_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_CLI_AVAILABLE_OVERRIDE", "0")
    assert is_gemini_available() is False

    monkeypatch.setenv("GEMINI_CLI_AVAILABLE_OVERRIDE", "1")
    assert is_gemini_available() is True
