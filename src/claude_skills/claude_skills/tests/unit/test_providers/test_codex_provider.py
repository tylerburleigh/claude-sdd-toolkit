"""
Tests for the Codex provider implementation.
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
from claude_skills.common.providers.codex import (
    CODEX_METADATA,
    SANDBOX_WARNING,
    CodexProvider,
    create_provider,
    is_codex_available,
)


class FakeProcess:
    def __init__(self, *, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _event(event_type: str, **payload: Dict) -> str:
    body = {"type": event_type}
    body.update(payload)
    return json.dumps(body)


def test_codex_provider_parses_jsonl_and_streams() -> None:
    stream_chunks: List[str] = []
    captured_command: Dict[str, List[str]] = {}

    stdout = "\n".join(
        [
            _event("thread.started", thread_id="thread-123"),
            _event("item.delta", delta={"text": "Hello"}),
            _event("item.delta", delta={"text": " world"}),
            _event(
                "item.completed",
                agent_message={"content": "Hello world"},
                model="gpt-5.1-codex",
            ),
            _event(
                "turn.completed",
                usage={
                    "input_tokens": 10,
                    "output_tokens": 20,
                    "cached_input_tokens": 2,
                    "total_tokens": 32,
                },
            ),
        ]
    )

    def runner(command, *, timeout=None, env=None):
        captured_command["args"] = list(command)
        captured_command["timeout"] = timeout
        captured_command["env"] = env
        return FakeProcess(stdout=stdout)

    provider = CodexProvider(
        CODEX_METADATA,
        ProviderHooks(on_stream_chunk=lambda chunk: stream_chunks.append(chunk.content)),
        model="gpt-5.1-codex",
        runner=runner,
        binary="codex",
    )

    request = GenerationRequest(
        prompt="Solve",
        system_prompt="System",
        metadata={},
        attachments=["diagram.png"],
        stream=True,
        timeout=45,
    )

    result = provider.generate(request)

    # Verify command structure
    args = captured_command["args"]
    assert args[0:8] == [
        "codex",
        "exec",
        "--sandbox",
        "read-only",
        "--json",
        "-m",
        "gpt-5.1-codex",
        "--image",
    ]
    assert args[8] == "diagram.png"

    # Verify prompt includes sandbox warning
    prompt = args[9]
    assert "System" in prompt
    assert SANDBOX_WARNING.strip() in prompt
    assert "Solve" in prompt
    assert prompt.startswith("System\n\n")
    assert prompt.endswith("\n\nSolve")

    assert captured_command["timeout"] == 45
    assert stream_chunks == ["Hello", " world"]
    assert result.content == "Hello world"
    assert result.model_fqn == "codex:gpt-5.1-codex"
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 20
    assert result.usage.cached_input_tokens == 2
    assert result.usage.total_tokens == 32
    assert result.raw_payload["thread_id"] == "thread-123"
    assert len(result.raw_payload["events"]) == 5


def test_codex_provider_rejects_unsupported_fields() -> None:
    provider = CodexProvider(
        CODEX_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout="{}"),
    )

    request = GenerationRequest(
        prompt="hi",
        temperature=0.5,
        max_tokens=100,
        continuation_id="abc",
        metadata={},
    )

    with pytest.raises(ProviderExecutionError) as excinfo:
        provider.generate(request)

    assert "does not support" in str(excinfo.value)


def test_codex_provider_handles_invalid_json() -> None:
    provider = CodexProvider(
        CODEX_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout="not-json"),
    )

    with pytest.raises(ProviderExecutionError):
        provider.generate(GenerationRequest(prompt="test"))


def test_codex_provider_handles_non_zero_exit() -> None:
    provider = CodexProvider(
        CODEX_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout="", stderr="boom", returncode=2),
    )

    with pytest.raises(ProviderExecutionError) as excinfo:
        provider.generate(GenerationRequest(prompt="test"))

    assert "code 2" in str(excinfo.value)


def test_codex_provider_injects_sandbox_warning() -> None:
    """Test that SANDBOX_WARNING is always injected into prompts."""
    captured_prompts: List[str] = []

    def runner(command, *, timeout=None, env=None):
        # Capture the prompt (last argument)
        captured_prompts.append(command[-1])
        return FakeProcess(
            stdout=_event(
                "item.completed",
                agent_message={"content": "done"},
                model="gpt-5.1-codex",
            )
        )

    provider = CodexProvider(
        CODEX_METADATA,
        ProviderHooks(),
        runner=runner,
        binary="codex",
    )

    # Test 1: With system prompt
    provider.generate(
        GenerationRequest(
            prompt="User prompt",
            system_prompt="Custom system prompt",
        )
    )

    assert len(captured_prompts) == 1
    prompt_with_system = captured_prompts[0]
    assert "Custom system prompt" in prompt_with_system
    assert SANDBOX_WARNING.strip() in prompt_with_system
    assert "User prompt" in prompt_with_system
    # Order should be: system prompt, warning, user prompt
    assert prompt_with_system.index("Custom system prompt") < prompt_with_system.index(SANDBOX_WARNING.strip())
    assert prompt_with_system.index(SANDBOX_WARNING.strip()) < prompt_with_system.index("User prompt")

    # Test 2: Without system prompt
    captured_prompts.clear()
    provider.generate(
        GenerationRequest(
            prompt="Just a prompt",
        )
    )

    assert len(captured_prompts) == 1
    prompt_without_system = captured_prompts[0]
    assert SANDBOX_WARNING.strip() in prompt_without_system
    assert "Just a prompt" in prompt_without_system
    assert prompt_without_system.index(SANDBOX_WARNING.strip()) < prompt_without_system.index("Just a prompt")


def test_create_provider_and_availability_override(monkeypatch: pytest.MonkeyPatch) -> None:
    runner_called = False

    def runner(command, *, timeout=None, env=None):
        nonlocal runner_called
        runner_called = True
        return FakeProcess(stdout=_event("turn.completed"))

    provider = create_provider(
        hooks=ProviderHooks(),
        dependencies={"runner": runner},
        overrides={"model": "gpt-5.1-codex", "binary": "codex"},
    )

    with pytest.raises(ProviderExecutionError):
        provider.generate(GenerationRequest(prompt="test"))

    assert runner_called is True

    monkeypatch.setenv("CODEX_CLI_AVAILABLE_OVERRIDE", "0")
    assert is_codex_available() is False
    monkeypatch.setenv("CODEX_CLI_AVAILABLE_OVERRIDE", "1")
    assert is_codex_available() is True
