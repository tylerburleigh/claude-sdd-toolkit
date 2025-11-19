"""
Tests for the OpenCode provider implementation.
"""

from __future__ import annotations

import json
import socket
from pathlib import Path
from typing import Dict, List, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

from claude_skills.common.providers import (
    GenerationRequest,
    ProviderExecutionError,
    ProviderHooks,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from claude_skills.common.providers.opencode import (
    DEFAULT_SERVER_URL,
    OPENCODE_METADATA,
    OpenCodeProvider,
    create_provider,
    is_opencode_available,
)


class FakeProcess:
    def __init__(self, *, stdout: str = "", stderr: str = "", returncode: int = 0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _payload(content: str = "OpenCode output", model: str = "default") -> str:
    """Create a line-delimited JSON response matching OpenCode wrapper format."""
    lines = []

    # Stream chunk
    lines.append(json.dumps({
        "type": "chunk",
        "content": content
    }))

    # Final done message
    lines.append(json.dumps({
        "type": "done",
        "response": {
            "text": content,
            "model": model,
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 50,
                "total_tokens": 60
            }
        }
    }))

    return "\n".join(lines)


def test_opencode_provider_executes_command_with_json_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that OpenCode provider executes wrapper with JSON payload via stdin."""
    captured: Dict[str, object] = {}
    stream_chunks: List[str] = []

    def runner(command, *, timeout=None, env=None, input_data=None):
        captured["command"] = list(command)
        captured["timeout"] = timeout
        captured["env"] = env
        captured["input_data"] = input_data
        return FakeProcess(stdout=_payload())

    # Mock server already running (port open)
    monkeypatch.setattr("claude_skills.common.providers.opencode.OpenCodeProvider._is_port_open", lambda self, port, host="localhost": True)

    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(on_stream_chunk=lambda chunk: stream_chunks.append(chunk.content)),
        model="default",
        runner=runner,
        binary="node",
    )

    request = GenerationRequest(
        prompt="Hello",
        system_prompt="System",
        metadata={},
        stream=True,
        timeout=30,
    )

    result = provider.generate(request)

    # Verify command structure
    assert captured["command"][0] == "node"
    assert captured["command"][-1] == "--stream"
    assert captured["timeout"] == 30

    # Verify JSON payload sent via stdin
    payload = json.loads(captured["input_data"])
    assert payload["prompt"] == "Hello"
    assert payload["system_prompt"] == "System"
    assert payload["config"]["model"] == "default"

    # Verify streaming and result
    assert stream_chunks == ["OpenCode output"]
    assert result.content == "OpenCode output"
    assert result.model_fqn == "opencode:default"
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 50
    assert result.usage.total_tokens == 60


def test_prepare_subprocess_env_merges_environments() -> None:
    """Test that _prepare_subprocess_env properly merges environments."""
    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
        env={"OPENCODE_API_KEY": "test-key", "CUSTOM_VAR": "value"}
    )

    # Verify environment was merged
    assert provider._env["OPENCODE_API_KEY"] == "test-key"
    assert provider._env["CUSTOM_VAR"] == "value"
    assert provider._env["OPENCODE_SERVER_URL"] == DEFAULT_SERVER_URL


def test_prepare_subprocess_env_preserves_server_url() -> None:
    """Test that custom OPENCODE_SERVER_URL is preserved."""
    custom_url = "http://localhost:5000"
    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
        env={"OPENCODE_SERVER_URL": custom_url}
    )

    assert provider._env["OPENCODE_SERVER_URL"] == custom_url


def test_is_port_open_detects_open_port() -> None:
    """Test that _is_port_open correctly detects an open port."""
    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
    )

    # Mock socket to simulate open port
    with patch("socket.socket") as mock_socket_class:
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0  # Port open
        mock_socket_class.return_value.__enter__.return_value = mock_sock

        assert provider._is_port_open(4096) is True


def test_is_port_open_detects_closed_port() -> None:
    """Test that _is_port_open correctly detects a closed port."""
    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
    )

    # Mock socket to simulate closed port
    with patch("socket.socket") as mock_socket_class:
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 1  # Port closed
        mock_socket_class.return_value.__enter__.return_value = mock_sock

        assert provider._is_port_open(4096) is False


def test_is_port_open_handles_socket_error() -> None:
    """Test that _is_port_open handles socket errors gracefully."""
    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
    )

    # Mock socket to raise error
    with patch("socket.socket") as mock_socket_class:
        mock_socket_class.return_value.__enter__.side_effect = socket.error("Connection refused")

        assert provider._is_port_open(4096) is False


def test_ensure_server_running_skips_if_port_open(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that _ensure_server_running skips startup if server already running."""
    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
    )

    # Mock port as open
    monkeypatch.setattr(provider, "_is_port_open", lambda port, host="localhost": True)

    # Should not raise, should not start server
    provider._ensure_server_running()
    assert provider._server_process is None


def test_ensure_server_running_passes_environment_to_server(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that _ensure_server_running passes environment variables to server process."""
    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
        env={"OPENCODE_API_KEY": "test-key"}
    )

    # Track what environment was passed to Popen
    captured_env = {}

    def mock_popen(*args, **kwargs):
        captured_env.update(kwargs.get("env", {}))
        mock_proc = MagicMock()
        mock_proc.terminate = MagicMock()
        return mock_proc

    # Mock dependencies
    monkeypatch.setattr(provider, "_is_port_open", lambda port, host="localhost": False)
    monkeypatch.setattr(Path, "exists", lambda self: True)

    with patch("subprocess.Popen", side_effect=mock_popen):
        with patch("time.sleep"):  # Skip sleep
            # Mock port as open after startup
            call_count = [0]
            def mock_port_check(port, host="localhost"):
                call_count[0] += 1
                return call_count[0] > 1  # Second call returns True

            monkeypatch.setattr(provider, "_is_port_open", mock_port_check)
            provider._ensure_server_running()

    # Verify environment was passed to server
    assert "OPENCODE_API_KEY" in captured_env
    assert captured_env["OPENCODE_API_KEY"] == "test-key"
    assert "OPENCODE_SERVER_URL" in captured_env


def test_ensure_server_running_raises_if_binary_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that _ensure_server_running raises error if opencode binary not found."""
    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
    )

    # Mock port as closed, binary not found
    monkeypatch.setattr(provider, "_is_port_open", lambda port, host="localhost": False)
    monkeypatch.setattr(Path, "exists", lambda self: False)

    with patch("subprocess.run", return_value=FakeProcess(returncode=1)):
        with pytest.raises(ProviderUnavailableError) as excinfo:
            provider._ensure_server_running()

        assert "binary not found" in str(excinfo.value)


def test_ensure_server_running_raises_timeout_if_server_fails_to_start(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that _ensure_server_running raises timeout if server doesn't start."""
    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=_payload()),
    )

    # Mock port always closed, binary exists
    monkeypatch.setattr(provider, "_is_port_open", lambda port, host="localhost": False)
    monkeypatch.setattr(Path, "exists", lambda self: True)

    mock_proc = MagicMock()
    mock_proc.terminate = MagicMock()

    with patch("subprocess.Popen", return_value=mock_proc):
        with patch("time.time", side_effect=[0, 100]):  # Simulate timeout
            with pytest.raises(ProviderTimeoutError) as excinfo:
                provider._ensure_server_running()

            assert "failed to start" in str(excinfo.value)
            # Verify server process was terminated
            mock_proc.terminate.assert_called_once()


def test_provider_handles_error_messages_from_wrapper() -> None:
    """Test that provider raises error when wrapper returns error type."""
    error_response = json.dumps({"type": "error", "message": "API key invalid"})

    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=error_response),
    )

    # Mock server already running
    with patch.object(provider, "_ensure_server_running"):
        with pytest.raises(ProviderExecutionError) as excinfo:
            provider.generate(GenerationRequest(prompt="test"))

        assert "API key invalid" in str(excinfo.value)


def test_provider_validates_json_output() -> None:
    """Test that provider raises error on invalid JSON from wrapper."""
    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout="not-json"),
    )

    # Mock server already running
    with patch.object(provider, "_ensure_server_running"):
        with pytest.raises(ProviderExecutionError) as excinfo:
            provider.generate(GenerationRequest(prompt="test"))

        assert "Invalid JSON" in str(excinfo.value)


def test_provider_handles_non_zero_exit_code() -> None:
    """Test that provider raises error when wrapper exits with non-zero code."""
    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(returncode=1, stderr="Wrapper crashed"),
    )

    # Mock server already running
    with patch.object(provider, "_ensure_server_running"):
        with pytest.raises(ProviderExecutionError) as excinfo:
            provider.generate(GenerationRequest(prompt="test"))

        assert "exited with code 1" in str(excinfo.value)
        assert "Wrapper crashed" in str(excinfo.value)


def test_create_provider_injects_custom_runner_and_env() -> None:
    """Test that factory function properly injects dependencies."""
    runner_called = False

    def runner(command, *, timeout=None, env=None, input_data=None):
        nonlocal runner_called
        runner_called = True
        # Verify environment was injected
        assert env is not None
        assert env.get("TEST_KEY") == "test-value"
        return FakeProcess(stdout=_payload(content="Override"))

    provider = create_provider(
        hooks=ProviderHooks(),
        dependencies={"runner": runner, "env": {"TEST_KEY": "test-value"}},
        overrides={"model": "default", "binary": "node"},
    )

    # Mock server already running
    with patch.object(provider, "_ensure_server_running"):
        result = provider.generate(GenerationRequest(prompt="test"))
        assert runner_called is True
        assert result.content == "Override"
        assert result.model_fqn == "opencode:default"


def test_is_opencode_available_checks_node_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that availability check verifies Node.js runtime."""
    # Mock Node.js not found
    with patch("subprocess.run", side_effect=FileNotFoundError):
        assert is_opencode_available() is False


def test_is_opencode_available_checks_wrapper_script(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that availability check verifies wrapper script exists."""
    # Mock Node.js OK, wrapper missing
    with patch("subprocess.run", return_value=FakeProcess(returncode=0)):
        with patch("pathlib.Path.exists", return_value=False):
            assert is_opencode_available() is False


def test_is_opencode_available_checks_sdk_and_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that availability check verifies SDK and opencode binary."""
    # Mock Node.js OK, wrapper exists
    with patch("subprocess.run", return_value=FakeProcess(returncode=0)):
        def mock_exists(self):
            # Wrapper exists, SDK exists, binary in node_modules
            path_str = str(self)
            if "opencode_wrapper.js" in path_str:
                return True
            if "@opencode-ai/sdk" in path_str:
                return True
            if "node_modules/.bin/opencode" in path_str:
                return True
            return False

        with patch("pathlib.Path.exists", mock_exists):
            assert is_opencode_available() is True


def test_is_opencode_available_checks_global_binary(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that availability check falls back to global opencode binary."""
    # Mock Node.js OK, wrapper exists, SDK exists, binary in PATH
    def mock_run(command, **kwargs):
        if command[0] == "node":
            return FakeProcess(returncode=0)
        if command[0] == "which":
            return FakeProcess(returncode=0, stdout="/usr/local/bin/opencode\n")
        return FakeProcess(returncode=1)

    with patch("subprocess.run", side_effect=mock_run):
        def mock_exists(self):
            path_str = str(self)
            # Wrapper and SDK exist, but not local binary
            if "opencode_wrapper.js" in path_str:
                return True
            if "@opencode-ai/sdk" in path_str:
                return True
            if "node_modules/.bin/opencode" in path_str:
                return False
            return False

        with patch("pathlib.Path.exists", mock_exists):
            assert is_opencode_available() is True


def test_provider_parses_multiple_chunks() -> None:
    """Test that provider correctly aggregates multiple streaming chunks."""
    chunks = [
        json.dumps({"type": "chunk", "content": "Part 1 "}),
        json.dumps({"type": "chunk", "content": "Part 2 "}),
        json.dumps({"type": "chunk", "content": "Part 3"}),
        json.dumps({
            "type": "done",
            "response": {
                "text": "Part 1 Part 2 Part 3",
                "model": "default",
                "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
            }
        }),
    ]

    stream_chunks: List[str] = []
    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(on_stream_chunk=lambda chunk: stream_chunks.append(chunk.content)),
        runner=lambda *args, **kwargs: FakeProcess(stdout="\n".join(chunks)),
    )

    with patch.object(provider, "_ensure_server_running"):
        result = provider.generate(GenerationRequest(prompt="test", stream=True))

    assert result.content == "Part 1 Part 2 Part 3"
    assert stream_chunks == ["Part 1 ", "Part 2 ", "Part 3"]
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 15
    assert result.usage.total_tokens == 25


def test_provider_handles_missing_token_usage() -> None:
    """Test that provider handles responses without token usage gracefully."""
    response = json.dumps({
        "type": "done",
        "response": {
            "text": "Response without usage",
            "model": "default"
            # No usage field
        }
    })

    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=response),
    )

    with patch.object(provider, "_ensure_server_running"):
        result = provider.generate(GenerationRequest(prompt="test"))

    assert result.content == "Response without usage"
    assert result.usage.input_tokens == 0
    assert result.usage.output_tokens == 0
    assert result.usage.total_tokens == 0


def test_provider_extracts_text_from_done_message_only() -> None:
    """Test that provider extracts text when only done message is present (no chunks)."""
    response = json.dumps({
        "type": "done",
        "response": {
            "text": "Complete response",
            "model": "gpt-5.1-codex-mini",
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}
        }
    })

    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=response),
    )

    with patch.object(provider, "_ensure_server_running"):
        result = provider.generate(GenerationRequest(prompt="test"))

    assert result.content == "Complete response"
    assert result.model_fqn == "opencode:default"
    assert result.usage.total_tokens == 15


def test_provider_handles_empty_chunks_gracefully() -> None:
    """Test that provider handles empty chunk content without errors."""
    chunks = [
        json.dumps({"type": "chunk", "content": ""}),
        json.dumps({"type": "chunk", "content": "Actual content"}),
        json.dumps({"type": "chunk", "content": ""}),
        json.dumps({
            "type": "done",
            "response": {
                "text": "Actual content",
                "model": "default",
                "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10}
            }
        }),
    ]

    stream_chunks: List[str] = []
    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(on_stream_chunk=lambda chunk: stream_chunks.append(chunk.content)),
        runner=lambda *args, **kwargs: FakeProcess(stdout="\n".join(chunks)),
    )

    with patch.object(provider, "_ensure_server_running"):
        result = provider.generate(GenerationRequest(prompt="test", stream=True))

    assert result.content == "Actual content"
    assert stream_chunks == ["", "Actual content", ""]


def test_provider_extracts_model_from_response_metadata() -> None:
    """Test that provider extracts model information from response metadata."""
    response = json.dumps({
        "type": "done",
        "response": {
            "text": "Response",
            "model": "gpt-5.1-codex",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            }
        }
    })

    provider = OpenCodeProvider(
        OPENCODE_METADATA,
        ProviderHooks(),
        runner=lambda *args, **kwargs: FakeProcess(stdout=response),
    )

    with patch.object(provider, "_ensure_server_running"):
        result = provider.generate(GenerationRequest(prompt="test"))

    assert result.usage.metadata == {"model": "gpt-5.1-codex"}
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 20
