"""
Tests for the Cursor Agent provider implementation.
"""

from __future__ import annotations

import json
from typing import Dict, List

import pytest

from claude_skills.common.providers import (
    GenerationRequest,
    ProviderExecutionError,
    ProviderHooks,
)
from claude_skills.common.providers.cursor_agent import (
    CURSOR_METADATA,
    CursorAgentProvider,
    create_provider,
    is_cursor_agent_available,
)


class FakeProcess:
    def __init__(self, *, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _payload(content: str = "Cursor response") -> str:
    return json.dumps(
        {
            "content": content,
            "model": "composer-1",
            "usage": {
                "input_tokens": 15,
                "output_tokens": 31,
                "total_tokens": 46,
            },
            "finish_reason": "stop",
        }
    )


def test_cursor_agent_provider_builds_command_and_parses_json() -> None:
    captured: Dict[str, List[str]] = {}
    streamed: List[str] = []

    def runner(command, *, timeout=None, env=None):
        captured["command"] = list(command)
        captured["timeout"] = timeout
        captured["env"] = env
        return FakeProcess(stdout=_payload())

    provider = CursorAgentProvider(
        CURSOR_METADATA,
        ProviderHooks(on_stream_chunk=lambda chunk: streamed.append(chunk.content)),
        model="composer-1",
        runner=runner,
        binary="cursor-agent",
    )

    request = GenerationRequest(
        prompt="Explain code",
        system_prompt="System instructions",
        temperature=0.4,
        max_tokens=600,
        metadata={
            "working_directory": "/tmp/project",
            "cursor_agent_flags": ["--quiet", "--print"],
        },
        stream=True,
        timeout=30,
    )

    result = provider.generate(request)

    assert captured["command"] == [
        "cursor-agent",
        "chat",
        "--json",
        "--working-directory",
        "/tmp/project",
        "--temperature",
        "0.4",
        "--max-tokens",
        "600",
        "--model",
        "composer-1",
        "--system",
        "System instructions",
        "--quiet",
        "--print",
        "--prompt",
        "Explain code",
    ]
    assert captured["timeout"] == 30
    assert streamed == ["Cursor response"]
    assert result.content == "Cursor response"
    assert result.model_fqn == "cursor-agent:composer-1"
    assert result.usage.input_tokens == 15
    assert result.usage.output_tokens == 31
    assert result.usage.total_tokens == 46


def test_cursor_agent_provider_retries_without_json_flag() -> None:
    calls: List[List[str]] = []

    def runner(command, *, timeout=None, env=None):
        calls.append(list(command))
        if "--json" in command:
            return FakeProcess(stderr="unknown option --json", returncode=2)
        return FakeProcess(stdout="Plain output")

    provider = CursorAgentProvider(
        CURSOR_METADATA,
        ProviderHooks(),
        runner=runner,
        binary="cursor-agent",
    )

    result = provider.generate(GenerationRequest(prompt="Hello"))

    assert len(calls) == 2
    assert "--json" in calls[0]
    assert "--json" not in calls[1]
    assert result.content == "Plain output"
    assert result.raw_payload["json_mode"] is False


def test_cursor_agent_provider_rejects_attachments() -> None:
    provider = CursorAgentProvider(
        CURSOR_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
    )

    request = GenerationRequest(prompt="hi", attachments=["file.txt"])

    with pytest.raises(ProviderExecutionError):
        provider.generate(request)


def test_cursor_agent_provider_handles_invalid_json() -> None:
    provider = CursorAgentProvider(
        CURSOR_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout="not-json"),
    )

    with pytest.raises(ProviderExecutionError):
        provider.generate(GenerationRequest(prompt="test"))


def test_create_provider_and_availability_override(monkeypatch: pytest.MonkeyPatch) -> None:
    runner_called = False

    def runner(command, *, timeout=None, env=None):
        nonlocal runner_called
        runner_called = True
        return FakeProcess(stdout=_payload())

    provider = create_provider(
        hooks=ProviderHooks(),
        dependencies={"runner": runner},
        overrides={"model": "composer-1", "binary": "cursor-agent"},
    )

    provider.generate(GenerationRequest(prompt="test"))
    assert runner_called is True

    monkeypatch.setenv("CURSOR_AGENT_CLI_AVAILABLE_OVERRIDE", "0")
    assert is_cursor_agent_available() is False
    monkeypatch.setenv("CURSOR_AGENT_CLI_AVAILABLE_OVERRIDE", "1")
    assert is_cursor_agent_available() is True
