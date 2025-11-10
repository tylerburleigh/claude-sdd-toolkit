"""
Unit tests for claude_skills.common.ai_tools module.

Tests for ToolResponse, MultiToolResponse, tool availability checking,
command building, and tool execution functions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from dataclasses import FrozenInstanceError
import subprocess

from claude_skills.common.ai_tools import (
    ToolStatus,
    ToolResponse,
    MultiToolResponse,
    check_tool_available,
    detect_available_tools,
    build_tool_command,
    execute_tool,
    execute_tools_parallel,
)


# =============================================================================
# ToolResponse Tests
# =============================================================================


def test_tool_response_immutable():
    """ToolResponse should be immutable (frozen dataclass)."""
    response = ToolResponse(tool="gemini", status=ToolStatus.SUCCESS)

    with pytest.raises(FrozenInstanceError):
        response.output = "modified"


def test_tool_response_success_property():
    """success property should match ToolStatus.SUCCESS."""
    response = ToolResponse(tool="gemini", status=ToolStatus.SUCCESS)
    assert response.success is True
    assert response.failed is False


def test_tool_response_failed_property():
    """failed property should be True for non-success statuses."""
    statuses_that_fail = [
        ToolStatus.TIMEOUT,
        ToolStatus.NOT_FOUND,
        ToolStatus.INVALID_OUTPUT,
        ToolStatus.ERROR,
    ]

    for status in statuses_that_fail:
        response = ToolResponse(tool="gemini", status=status)
        assert response.failed is True
        assert response.success is False


def test_tool_response_serialization():
    """ToolResponse should serialize to/from dict."""
    original = ToolResponse(
        tool="gemini",
        status=ToolStatus.SUCCESS,
        output="test output",
        error=None,
        duration=1.5,
        model="gemini-exp-1114",
        exit_code=0
    )

    # Serialize
    data = original.to_dict()

    # Deserialize
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


def test_multi_tool_response_success_property():
    """success property should be True if at least one tool succeeded."""
    responses = {
        "gemini": ToolResponse(tool="gemini", status=ToolStatus.SUCCESS),
        "codex": ToolResponse(tool="codex", status=ToolStatus.ERROR),
    }

    multi = MultiToolResponse(
        responses=responses,
        success_count=1,
        failure_count=1
    )

    assert multi.success is True
    assert multi.all_failed is False
    assert multi.all_succeeded is False


def test_multi_tool_response_all_failed():
    """all_failed should be True when all tools failed."""
    responses = {
        "gemini": ToolResponse(tool="gemini", status=ToolStatus.ERROR),
        "codex": ToolResponse(tool="codex", status=ToolStatus.TIMEOUT),
    }

    multi = MultiToolResponse(
        responses=responses,
        success_count=0,
        failure_count=2
    )

    assert multi.all_failed is True
    assert multi.success is False


def test_multi_tool_response_all_succeeded():
    """all_succeeded should be True when all tools succeeded."""
    responses = {
        "gemini": ToolResponse(tool="gemini", status=ToolStatus.SUCCESS),
        "codex": ToolResponse(tool="codex", status=ToolStatus.SUCCESS),
    }

    multi = MultiToolResponse(
        responses=responses,
        success_count=2,
        failure_count=0
    )

    assert multi.all_succeeded is True


def test_multi_tool_response_filter_successful():
    """get_successful_responses should filter by success."""
    responses = {
        "gemini": ToolResponse(tool="gemini", status=ToolStatus.SUCCESS),
        "codex": ToolResponse(tool="codex", status=ToolStatus.ERROR),
        "cursor-agent": ToolResponse(tool="cursor-agent", status=ToolStatus.SUCCESS),
    }

    multi = MultiToolResponse(
        responses=responses,
        success_count=2,
        failure_count=1
    )

    successful = multi.get_successful_responses()
    assert len(successful) == 2
    assert "gemini" in successful
    assert "cursor-agent" in successful
    assert "codex" not in successful


def test_multi_tool_response_filter_failed():
    """get_failed_responses should filter by failure."""
    responses = {
        "gemini": ToolResponse(tool="gemini", status=ToolStatus.SUCCESS),
        "codex": ToolResponse(tool="codex", status=ToolStatus.ERROR),
        "cursor-agent": ToolResponse(tool="cursor-agent", status=ToolStatus.TIMEOUT),
    }

    multi = MultiToolResponse(
        responses=responses,
        success_count=1,
        failure_count=2
    )

    failed = multi.get_failed_responses()
    assert len(failed) == 2
    assert "codex" in failed
    assert "cursor-agent" in failed
    assert "gemini" not in failed


# =============================================================================
# Tool Availability Tests
# =============================================================================


def test_check_tool_available_found(mocker):
    """check_tool_available should return True when tool in PATH."""
    mocker.patch("shutil.which", return_value="/usr/bin/gemini")

    assert check_tool_available("gemini") is True


def test_check_tool_available_not_found(mocker):
    """check_tool_available should return False when tool not in PATH."""
    mocker.patch("shutil.which", return_value=None)

    assert check_tool_available("nonexistent") is False


def test_check_tool_available_with_version_check(mocker):
    """check_tool_available with version check should verify tool works."""
    mocker.patch("shutil.which", return_value="/usr/bin/gemini")
    mock_result = Mock(returncode=0)
    mocker.patch("subprocess.run", return_value=mock_result)

    assert check_tool_available("gemini", check_version=True) is True


def test_check_tool_available_version_check_fails(mocker):
    """check_tool_available should return False if version check fails."""
    mocker.patch("shutil.which", return_value="/usr/bin/gemini")
    mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 5))

    assert check_tool_available("gemini", check_version=True) is False


def test_detect_available_tools_all_found(mocker):
    """detect_available_tools should find all available tools."""
    mocker.patch("shutil.which", return_value="/usr/bin/tool")

    available = detect_available_tools()

    assert "gemini" in available
    assert "codex" in available
    assert "cursor-agent" in available


def test_detect_available_tools_partial(mocker):
    """detect_available_tools should find only available tools."""
    def which_side_effect(tool):
        if tool == "gemini":
            return "/usr/bin/gemini"
        return None

    mocker.patch("shutil.which", side_effect=which_side_effect)

    available = detect_available_tools()

    assert available == ["gemini"]


def test_detect_available_tools_custom_list(mocker):
    """detect_available_tools should check custom tool list."""
    mocker.patch("shutil.which", return_value="/usr/bin/tool")

    available = detect_available_tools(tools=["gemini", "custom-tool"])

    assert "gemini" in available
    assert "custom-tool" in available
    assert "codex" not in available


# =============================================================================
# Command Building Tests
# =============================================================================


def test_build_tool_command_gemini():
    """build_tool_command should build gemini command correctly."""
    cmd = build_tool_command("gemini", "test prompt", model="gemini-exp-1114")

    assert cmd == ["gemini", "-m", "gemini-exp-1114", "--output-format", "json", "-p", "test prompt"]


def test_build_tool_command_gemini_no_model():
    """build_tool_command should handle gemini without model."""
    cmd = build_tool_command("gemini", "test prompt")

    assert cmd == ["gemini", "--output-format", "json", "-p", "test prompt"]


def test_build_tool_command_codex():
    """build_tool_command should build codex command correctly."""
    cmd = build_tool_command("codex", "test prompt", model="claude-3.7-sonnet")

    assert cmd == ["codex", "exec", "--sandbox", "read-only", "--ask-for-approval", "never", "--json", "-m", "claude-3.7-sonnet", "test prompt"]


def test_build_tool_command_cursor_agent():
    """build_tool_command should build cursor-agent command correctly."""
    cmd = build_tool_command("cursor-agent", "test prompt")

    assert cmd == ["cursor-agent", "--print", "--json", "test prompt"]


def test_build_tool_command_unknown_tool():
    """build_tool_command should raise ValueError for unknown tool."""
    with pytest.raises(ValueError, match="Unknown tool"):
        build_tool_command("unknown", "test prompt")


# =============================================================================
# Tool Execution Tests
# =============================================================================


def test_execute_tool_success(mocker):
    """execute_tool should return success response for successful execution."""
    mock_result = Mock(returncode=0, stdout="output", stderr="")
    mocker.patch("subprocess.run", return_value=mock_result)

    response = execute_tool("gemini", "test prompt")

    assert response.success is True
    assert response.status == ToolStatus.SUCCESS
    assert response.output == "output"
    assert response.error is None
    assert response.exit_code == 0


def test_execute_tool_cursor_agent_retries_without_json(mocker):
    """execute_tool should retry cursor-agent without --json when unsupported."""
    first_result = Mock(returncode=2, stdout="", stderr="Error: unrecognized option '--json'")
    second_result = Mock(returncode=0, stdout="Cursor response to prompt", stderr="")
    mock_run = mocker.patch("subprocess.run", side_effect=[first_result, second_result])

    response = execute_tool("cursor-agent", "review code")

    assert response.success is True
    assert response.output == "Cursor response to prompt"
    assert response.metadata.get("cursor_agent_retry_without_json") is True
    assert mock_run.call_count == 2

    first_command = mock_run.call_args_list[0].args[0]
    second_command = mock_run.call_args_list[1].args[0]

    assert "--json" in first_command
    assert "--json" not in second_command


def test_execute_tool_non_zero_exit(mocker):
    """execute_tool should return error response for non-zero exit."""
    mock_result = Mock(returncode=1, stdout="", stderr="error message")
    mocker.patch("subprocess.run", return_value=mock_result)

    response = execute_tool("gemini", "test prompt")

    assert response.failed is True
    assert response.status == ToolStatus.ERROR
    assert response.error == "error message"
    assert response.exit_code == 1


def test_execute_tool_timeout(mocker):
    """execute_tool should return timeout response when tool times out."""
    mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("cmd", 90))

    response = execute_tool("gemini", "test prompt", timeout=90)

    assert response.status == ToolStatus.TIMEOUT
    assert "timed out" in response.error
    assert response.exit_code is None


def test_execute_tool_not_found(mocker):
    """execute_tool should return not_found response when tool missing."""
    mocker.patch("subprocess.run", side_effect=FileNotFoundError())

    response = execute_tool("gemini", "test prompt")

    assert response.status == ToolStatus.NOT_FOUND
    assert "not found" in response.error
    assert response.exit_code is None


def test_execute_tool_unknown_tool():
    """execute_tool should return error response for unknown tool."""
    response = execute_tool("unknown", "test prompt")

    assert response.status == ToolStatus.ERROR
    assert "Unknown tool" in response.error


def test_execute_tool_captures_metadata(mocker):
    """execute_tool should capture model, prompt, and timing metadata."""
    mock_result = Mock(returncode=0, stdout="output", stderr="")
    mocker.patch("subprocess.run", return_value=mock_result)

    response = execute_tool("gemini", "test prompt", model="gemini-exp-1114", timeout=60)

    assert response.tool == "gemini"
    assert response.model == "gemini-exp-1114"
    assert response.prompt == "test prompt"
    assert response.duration > 0  # Should capture timing
    assert response.timestamp  # Should have timestamp


# =============================================================================
# Parallel Execution Tests
# =============================================================================


def test_execute_tools_parallel_empty_list():
    """execute_tools_parallel should handle empty tool list."""
    response = execute_tools_parallel(tools=[], prompt="test")

    assert len(response.responses) == 0
    assert response.success_count == 0
    assert response.failure_count == 0


def test_execute_tools_parallel_all_succeed(mocker):
    """execute_tools_parallel should handle all tools succeeding."""
    mock_result = Mock(returncode=0, stdout="output", stderr="")
    mocker.patch("subprocess.run", return_value=mock_result)

    response = execute_tools_parallel(
        tools=["gemini", "codex"],
        prompt="test prompt"
    )

    assert len(response.responses) == 2
    assert response.success_count == 2
    assert response.failure_count == 0
    assert response.all_succeeded is True


def test_execute_tools_parallel_partial_success(mocker):
    """execute_tools_parallel should handle mixed success/failure."""
    def run_side_effect(cmd, **kwargs):
        if "gemini" in cmd:
            return Mock(returncode=0, stdout="success", stderr="")
        else:
            return Mock(returncode=1, stdout="", stderr="error")

    mocker.patch("subprocess.run", side_effect=run_side_effect)

    response = execute_tools_parallel(
        tools=["gemini", "codex"],
        prompt="test prompt"
    )

    assert response.success_count == 1
    assert response.failure_count == 1
    assert response.success is True  # At least one succeeded
    assert response.all_succeeded is False


def test_execute_tools_parallel_statistics(mocker):
    """execute_tools_parallel should calculate statistics correctly."""
    mock_result = Mock(returncode=0, stdout="output", stderr="")
    mocker.patch("subprocess.run", return_value=mock_result)

    response = execute_tools_parallel(
        tools=["gemini", "codex"],
        prompt="test prompt"
    )

    assert response.total_duration > 0  # Wall-clock time
    assert response.max_duration > 0  # Longest tool duration
    assert response.timestamp  # Has timestamp


def test_execute_tools_parallel_with_models(mocker):
    """execute_tools_parallel should use custom models when provided."""
    captured_commands = []

    def run_side_effect(cmd, **kwargs):
        captured_commands.append(cmd)
        return Mock(returncode=0, stdout="output", stderr="")

    mocker.patch("subprocess.run", side_effect=run_side_effect)

    execute_tools_parallel(
        tools=["gemini", "codex"],
        prompt="test prompt",
        models={"gemini": "custom-model", "codex": "another-model"}
    )

    # Check that models were used in commands
    gemini_cmd = [c for c in captured_commands if "gemini" in c[0]][0]
    assert "custom-model" in gemini_cmd

    codex_cmd = [c for c in captured_commands if "codex" in c[0]][0]
    assert "another-model" in codex_cmd
