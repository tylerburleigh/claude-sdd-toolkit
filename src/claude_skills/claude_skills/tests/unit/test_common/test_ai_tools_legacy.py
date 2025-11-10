from __future__ import annotations

"""
Legacy tests for `claude_skills.common.ai_tools`, migrated from `tests/unit/test_ai_tools.py`.
"""

import subprocess
from dataclasses import FrozenInstanceError
from unittest.mock import MagicMock, Mock, patch

import pytest

from claude_skills.common.ai_tools import (
    MultiToolResponse,
    ToolResponse,
    ToolStatus,
    build_tool_command,
    check_tool_available,
    detect_available_tools,
    execute_tool,
    execute_tools_parallel,
)


pytestmark = pytest.mark.unit


# =============================================================================
# ToolResponse Tests
# =============================================================================


def test_tool_response_immutable() -> None:
    """ToolResponse should be immutable (frozen dataclass)."""
    response = ToolResponse(tool="gemini", status=ToolStatus.SUCCESS)

    with pytest.raises(FrozenInstanceError):
        response.output = "modified"  # type: ignore[misc]


def test_tool_response_success_property() -> None:
    response = ToolResponse(tool="gemini", status=ToolStatus.SUCCESS)
    assert response.success is True
    assert response.failed is False


def test_tool_response_failed_property() -> None:
    failing_statuses = [
        ToolStatus.TIMEOUT,
        ToolStatus.NOT_FOUND,
        ToolStatus.INVALID_OUTPUT,
        ToolStatus.ERROR,
    ]

    for status in failing_statuses:
        response = ToolResponse(tool="gemini", status=status)
        assert response.failed is True
        assert response.success is False


def test_tool_response_serialization() -> None:
    original = ToolResponse(
        tool="gemini",
        status=ToolStatus.SUCCESS,
        output="test output",
        error=None,
        duration=1.5,
        model="gemini-exp-1114",
        exit_code=0,
    )
    data = original.to_dict()
    restored = ToolResponse.from_dict(data)

    assert restored.tool == original.tool
    assert restored.status == original.status
    assert restored.output == original.output
    assert restored.duration == original.duration
    assert restored.model == original.model
    assert restored.exit_code == original.exit_code


# =============================================================================
# MultiToolResponse Tests
# =============================================================================


def test_multi_tool_response_success_property() -> None:
    responses = {
        "gemini": ToolResponse(tool="gemini", status=ToolStatus.SUCCESS),
        "codex": ToolResponse(tool="codex", status=ToolStatus.ERROR),
    }
    multi = MultiToolResponse(responses=responses, success_count=1, failure_count=1)
    assert multi.success is True
    assert multi.all_failed is False
    assert multi.all_succeeded is False


def test_multi_tool_response_all_failed() -> None:
    responses = {
        "gemini": ToolResponse(tool="gemini", status=ToolStatus.ERROR),
        "codex": ToolResponse(tool="codex", status=ToolStatus.TIMEOUT),
    }
    multi = MultiToolResponse(responses=responses, success_count=0, failure_count=2)
    assert multi.all_failed is True
    assert multi.success is False


def test_multi_tool_response_all_succeeded() -> None:
    responses = {
        "gemini": ToolResponse(tool="gemini", status=ToolStatus.SUCCESS),
        "codex": ToolResponse(tool="codex", status=ToolStatus.SUCCESS),
    }
    multi = MultiToolResponse(responses=responses, success_count=2, failure_count=0)
    assert multi.all_succeeded is True


def test_multi_tool_response_filter_successful() -> None:
    responses = {
        "gemini": ToolResponse(tool="gemini", status=ToolStatus.SUCCESS),
        "codex": ToolResponse(tool="codex", status=ToolStatus.ERROR),
        "cursor-agent": ToolResponse(tool="cursor-agent", status=ToolStatus.SUCCESS),
    }

    multi = MultiToolResponse(responses=responses, success_count=2, failure_count=1)
    successful = multi.get_successful_responses()
    assert len(successful) == 2
    assert "gemini" in successful
    assert "cursor-agent" in successful
    assert "codex" not in successful


def test_multi_tool_response_filter_failed() -> None:
    responses = {
        "gemini": ToolResponse(tool="gemini", status=ToolStatus.SUCCESS),
        "codex": ToolResponse(tool="codex", status=ToolStatus.ERROR),
        "cursor-agent": ToolResponse(tool="cursor-agent", status=ToolStatus.TIMEOUT),
    }

    multi = MultiToolResponse(responses=responses, success_count=1, failure_count=2)
    failed = multi.get_failed_responses()
    assert len(failed) == 2
    assert "codex" in failed
    assert "cursor-agent" in failed
    assert "gemini" not in failed


# =============================================================================
# Tool Availability Tests
# =============================================================================


def test_check_tool_available_found(mocker) -> None:
    mocker.patch("shutil.which", return_value="/usr/bin/gemini")
    assert check_tool_available("gemini") is True


def test_check_tool_available_not_found(mocker) -> None:
    mocker.patch("shutil.which", return_value=None)
    assert check_tool_available("nonexistent") is False


def test_detect_available_tools_returns_expected(mocker) -> None:
    def fake_which(name: str) -> str | None:
        return f"/usr/bin/{name}" if name != "cursor-agent" else None

    mocker.patch("shutil.which", side_effect=fake_which)
    available = detect_available_tools()
    assert "gemini" in available
    assert "codex" in available
    assert "cursor-agent" not in available


def test_detect_available_tools_with_version_check() -> None:
    with patch(
        "claude_skills.common.ai_tools.check_tool_available",
        side_effect=lambda tool, check_version=False: tool != "cursor-agent",
    ):
        available = detect_available_tools(check_version=True)
        assert available == ["gemini", "codex"]


def test_detect_available_tools_handles_version_failures() -> None:
    with patch(
        "claude_skills.common.ai_tools.check_tool_available",
        side_effect=lambda tool, check_version=False: False,
    ):
        available = detect_available_tools(check_version=True)
        assert available == []


# =============================================================================
# Command Building Tests
# =============================================================================


def test_build_tool_command_simple() -> None:
    command = build_tool_command(
        tool="gemini",
        prompt="Hello world",
        model="model-1",
    )
    assert command == ["gemini", "-m", "model-1", "--output-format", "json", "-p", "Hello world"]


def test_build_tool_command_handles_whitespace() -> None:
    command = build_tool_command(
        tool="gemini",
        prompt="  spaced prompt  ",
    )
    assert command == ["gemini", "--output-format", "json", "-p", "  spaced prompt  "]


# =============================================================================
# Tool Execution Tests
# =============================================================================


def test_execute_tool_success(mocker) -> None:
    completed = subprocess.CompletedProcess(args=["gemini"], returncode=0, stdout="output")
    mocker.patch("subprocess.run", return_value=completed)

    result = execute_tool("gemini", "hello")
    assert result.success is True
    assert result.output == "output"
    assert result.exit_code == 0


def test_execute_tool_timeout(mocker) -> None:
    mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="gemini", timeout=1))
    result = execute_tool("gemini", "hello")
    assert result.status == ToolStatus.TIMEOUT
    assert result.success is False


def test_execute_tool_not_found(mocker) -> None:
    mocker.patch("subprocess.run", side_effect=FileNotFoundError("gemini"))
    result = execute_tool("gemini", "hello")
    assert result.status == ToolStatus.NOT_FOUND
    assert result.success is False


def test_execute_tool_error_status(mocker) -> None:
    completed = subprocess.CompletedProcess(args=["gemini"], returncode=1, stdout="", stderr="boom")
    mocker.patch("subprocess.run", return_value=completed)
    result = execute_tool("gemini", "hello")
    assert result.status == ToolStatus.ERROR
    assert result.success is False


def test_execute_tools_parallel_success(mocker) -> None:
    responses = [
        ToolResponse(tool="gemini", status=ToolStatus.SUCCESS),
        ToolResponse(tool="codex", status=ToolStatus.SUCCESS),
    ]
    mock_execute = MagicMock(side_effect=responses)
    mocker.patch("claude_skills.common.ai_tools.execute_tool", mock_execute)

    result = execute_tools_parallel(["gemini", "codex"], "hello")

    assert len(result.responses) == 2
    assert result.responses["gemini"].success is True
    assert result.responses["codex"].success is True
    assert mock_execute.call_count == 2


def test_execute_tools_parallel_handles_failures(mocker) -> None:
    responses = [
        ToolResponse(tool="gemini", status=ToolStatus.SUCCESS),
        ToolResponse(tool="codex", status=ToolStatus.ERROR, error="Failed"),
        ToolResponse(tool="cursor-agent", status=ToolStatus.SUCCESS),
    ]
    mock_execute = MagicMock(side_effect=responses)
    mocker.patch("claude_skills.common.ai_tools.execute_tool", mock_execute)

    result = execute_tools_parallel(["gemini", "codex", "cursor-agent"], "hello")

    assert len(result.responses) == 3
    assert result.responses["codex"].failed is True
    assert mock_execute.call_count == 3


def test_execute_tool_captures_duration(mocker) -> None:
    completed = subprocess.CompletedProcess(args=["gemini"], returncode=0, stdout="hi")
    mocker.patch("subprocess.run", return_value=completed)
    result = execute_tool("gemini", "hello")
    assert result.duration is not None


def test_detect_available_tools_parallel_invocation(mocker) -> None:
    mock_execute = MagicMock(return_value=ToolResponse(tool="gemini", status=ToolStatus.SUCCESS))
    mocker.patch("claude_skills.common.ai_tools.execute_tool", mock_execute)
    execute_tools_parallel(["gemini"], "version check")
    mock_execute.assert_called_once_with("gemini", "version check", model=None, timeout=90)


def test_build_tool_command_handles_model_only() -> None:
    command = build_tool_command(
        tool="codex",
        prompt="prompt",
        model="model",
    )
    assert "--json" in command
    assert "model" in command
