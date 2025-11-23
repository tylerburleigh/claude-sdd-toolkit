"""
Tests for the Cursor Agent provider implementation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import pytest

from claude_skills.common.providers import (
    GenerationRequest,
    ProviderExecutionError,
    ProviderHooks,
)
from claude_skills.common.providers.cursor_agent import (
    CURSOR_METADATA,
    SHELL_COMMAND_WARNING,
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
            "working_directory": "/tmp/project",  # Will be ignored in favor of config dir
            "cursor_agent_flags": ["--quiet", "--print"],
        },
        stream=True,
        timeout=30,
    )

    result = provider.generate(request)

    # Verify command structure (working_directory will be config dir, not user-provided)
    command = captured["command"]
    assert command[0] == "cursor-agent"
    assert command[1] == "chat"
    assert command[2] == "--json"
    assert "--working-directory" in command

    # Working directory should be a temp directory (cursor_readonly_*)
    wd_idx = command.index("--working-directory")
    working_dir = command[wd_idx + 1]
    assert "cursor_readonly_" in working_dir

    # Verify config file was created
    config_path = Path(working_dir) / ".cursor" / "cli-config.json"
    # Note: Config is cleaned up in finally block, so it won't exist after execution

    assert "--temperature" in command
    assert "0.4" in command
    assert "--max-tokens" in command
    assert "600" in command
    assert "--model" in command
    assert "composer-1" in command
    assert "--system" in command

    # System prompt should include security warning
    system_idx = command.index("--system")
    system_prompt = command[system_idx + 1]
    assert "System instructions" in system_prompt
    assert SHELL_COMMAND_WARNING.strip() in system_prompt

    assert "--quiet" in command
    assert "--print" in command
    assert "--prompt" in command
    assert "Explain code" in command

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


def test_cursor_agent_provider_creates_readonly_config() -> None:
    """Test that the provider creates a read-only config file."""
    config_path_captured = None

    def runner(command, *, timeout=None, env=None):
        nonlocal config_path_captured
        # Capture the working directory (config directory)
        if "--working-directory" in command:
            wd_idx = command.index("--working-directory")
            config_dir = Path(command[wd_idx + 1])
            config_path_captured = config_dir / ".cursor" / "cli-config.json"

            # Verify config file exists during execution
            assert config_path_captured.exists()

            # Verify config file content
            with open(config_path_captured) as f:
                config_data = json.load(f)

            assert "permissions" in config_data
            assert "description" in config_data
            assert config_data["description"] == "Read-only mode enforced by claude-sdd-toolkit"

            permissions = config_data["permissions"]
            assert "Read(**/*)" in permissions  # Allow all reads
            assert "Write()" in permissions  # Deny all writes

            # Verify shell commands are present
            shell_perms = [p for p in permissions if p.startswith("Shell(")]
            assert len(shell_perms) > 0
            assert any("git" in p for p in shell_perms)
            assert any("cat" in p for p in shell_perms)

        return FakeProcess(stdout=_payload())

    provider = CursorAgentProvider(
        CURSOR_METADATA,
        ProviderHooks(),
        runner=runner,
        binary="cursor-agent",
    )

    provider.generate(GenerationRequest(prompt="test"))

    # Verify config was captured
    assert config_path_captured is not None

    # Verify config was cleaned up after execution
    assert not config_path_captured.exists()


def test_cursor_agent_provider_cleans_up_config_on_error() -> None:
    """Test that config is cleaned up even when execution fails."""
    config_path_captured = None

    def runner(command, *, timeout=None, env=None):
        nonlocal config_path_captured
        if "--working-directory" in command:
            wd_idx = command.index("--working-directory")
            config_dir = Path(command[wd_idx + 1])
            config_path_captured = config_dir / ".cursor" / "cli-config.json"
            assert config_path_captured.exists()

        # Simulate an error
        return FakeProcess(stdout="error", stderr="command failed", returncode=1)

    provider = CursorAgentProvider(
        CURSOR_METADATA,
        ProviderHooks(),
        runner=runner,
        binary="cursor-agent",
    )

    with pytest.raises(ProviderExecutionError):
        provider.generate(GenerationRequest(prompt="test"))

    # Verify config was captured
    assert config_path_captured is not None

    # Verify config was cleaned up even after error
    assert not config_path_captured.exists()


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
