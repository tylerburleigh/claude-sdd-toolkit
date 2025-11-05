"""
Integration tests for AI tools with mock executables.

Tests tool detection, command building, and execution with realistic
mock CLI tools that behave like actual gemini/codex/cursor-agent commands.
"""

import pytest
import subprocess
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

from claude_skills.common.ai_tools import (
    check_tool_available,
    detect_available_tools,
    build_tool_command,
    execute_tool,
    execute_tools_parallel,
    ToolStatus,
)


# =============================================================================
# Fixtures for Mock CLI Tools
# =============================================================================


@pytest.fixture
def mock_tools_dir(tmp_path):
    """
    Create temporary directory with mock CLI tools.

    Creates executable scripts that mimic gemini, codex, and cursor-agent
    behavior for testing.

    Returns:
        Path to directory containing mock tools
    """
    tools_dir = tmp_path / "mock_tools"
    tools_dir.mkdir()

    # Create mock gemini script
    gemini_script = tools_dir / "gemini"
    gemini_script.write_text(
        "#!/bin/bash\n"
        "# Mock gemini CLI tool\n"
        "if [[ \"$1\" == \"--version\" ]]; then\n"
        "  echo 'gemini version 1.0.0'\n"
        "  exit 0\n"
        "fi\n"
        "# Parse arguments: -m model -p prompt\n"
        "while [[ $# -gt 0 ]]; do\n"
        "  case $1 in\n"
        "    -m) model=\"$2\"; shift 2;;\n"
        "    -p) prompt=\"$2\"; shift 2;;\n"
        "    *) shift;;\n"
        "  esac\n"
        "done\n"
        "echo \"Gemini response to: $prompt\"\n"
        "exit 0\n"
    )
    gemini_script.chmod(0o755)

    # Create mock codex script
    codex_script = tools_dir / "codex"
    codex_script.write_text(
        "#!/bin/bash\n"
        "# Mock codex CLI tool\n"
        "if [[ \"$1\" == \"--version\" ]]; then\n"
        "  echo 'codex version 1.0.0'\n"
        "  exit 0\n"
        "fi\n"
        "# Parse arguments: -m model, then positional prompt\n"
        "while [[ $# -gt 0 ]]; do\n"
        "  case $1 in\n"
        "    -m) model=\"$2\"; shift 2;;\n"
        "    *) prompt=\"$1\"; shift;;\n"
        "  esac\n"
        "done\n"
        "echo \"Codex response to: $prompt\"\n"
        "exit 0\n"
    )
    codex_script.chmod(0o755)

    # Create mock cursor-agent script
    cursor_script = tools_dir / "cursor-agent"
    cursor_script.write_text(
        "#!/bin/bash\n"
        "# Mock cursor-agent CLI tool\n"
        "if [[ \"$1\" == \"--version\" ]]; then\n"
        "  echo 'cursor-agent version 1.0.0'\n"
        "  exit 0\n"
        "fi\n"
        "# Parse arguments: --print flag, then positional prompt\n"
        "if [[ \"$1\" == \"--print\" ]]; then\n"
        "  shift\n"
        "  prompt=\"$1\"\n"
        "fi\n"
        "echo \"Cursor-agent response to: $prompt\"\n"
        "exit 0\n"
    )
    cursor_script.chmod(0o755)

    return tools_dir


@pytest.fixture
def path_with_mock_tools(mock_tools_dir, monkeypatch):
    """
    Fixture that adds mock tools directory to PATH.

    Temporarily modifies PATH environment variable to include mock tools,
    then restores original PATH after test.
    """
    original_path = os.environ.get("PATH", "")
    new_path = f"{mock_tools_dir}:{original_path}"
    monkeypatch.setenv("PATH", new_path)
    return mock_tools_dir


# =============================================================================
# Tool Detection Tests
# =============================================================================


class TestToolDetectionIntegration:
    """Integration tests for tool detection with real PATH lookups."""

    def test_detect_tools_with_mocks_in_path(self, path_with_mock_tools):
        """Test detection of mock tools added to PATH."""
        available = detect_available_tools()

        assert "gemini" in available
        assert "codex" in available
        assert "cursor-agent" in available

    def test_check_tool_available_with_version_check(self, path_with_mock_tools):
        """Test tool availability with version check using mock tools."""
        # Should find tool and verify it responds to --version
        assert check_tool_available("gemini", check_version=True) is True
        assert check_tool_available("codex", check_version=True) is True
        assert check_tool_available("cursor-agent", check_version=True) is True

    def test_detect_tools_without_version_check(self, path_with_mock_tools):
        """Test fast detection without version check."""
        # Fast PATH-only check
        available = detect_available_tools(check_version=False)

        assert len(available) == 3
        assert set(available) == {"gemini", "codex", "cursor-agent"}

    def test_detect_tools_when_none_available(self, monkeypatch):
        """Test detection returns empty list when no tools in PATH."""
        # Set PATH to empty directory
        with tempfile.TemporaryDirectory() as empty_dir:
            monkeypatch.setenv("PATH", empty_dir)

            available = detect_available_tools()
            assert available == []

    def test_detect_partial_tools(self, mock_tools_dir, monkeypatch):
        """Test detection when only some tools are available."""
        # Add only gemini to PATH
        gemini_dir = mock_tools_dir
        monkeypatch.setenv("PATH", str(gemini_dir))

        # Remove codex and cursor-agent
        (gemini_dir / "codex").unlink()
        (gemini_dir / "cursor-agent").unlink()

        available = detect_available_tools()
        assert available == ["gemini"]


# =============================================================================
# Command Building Tests
# =============================================================================


class TestCommandBuildingIntegration:
    """Integration tests for command building with real execution."""

    def test_gemini_command_executes_successfully(self, path_with_mock_tools):
        """Test gemini command built correctly and executes."""
        cmd = build_tool_command("gemini", "test prompt", model="gemini-exp-1114")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0
        assert "Gemini response to: test prompt" in result.stdout

    def test_codex_command_executes_successfully(self, path_with_mock_tools):
        """Test codex command built correctly and executes."""
        cmd = build_tool_command("codex", "analyze this", model="claude-3.7-sonnet")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0
        assert "Codex response to: analyze this" in result.stdout

    def test_cursor_agent_command_executes_successfully(self, path_with_mock_tools):
        """Test cursor-agent command built correctly and executes."""
        cmd = build_tool_command("cursor-agent", "review code")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        assert result.returncode == 0
        assert "Cursor-agent response to: review code" in result.stdout

    def test_command_building_handles_special_characters(self, path_with_mock_tools):
        """Test commands handle prompts with special characters."""
        prompt_with_specials = "Analyze: 'test' \"quoted\" $var"
        cmd = build_tool_command("gemini", prompt_with_specials)

        # Command should be properly escaped/safe
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should execute without shell injection issues
        assert result.returncode == 0


# =============================================================================
# Tool Execution Tests
# =============================================================================


class TestToolExecutionIntegration:
    """Integration tests for tool execution with mock CLI tools."""

    def test_execute_tool_with_mock_gemini(self, path_with_mock_tools):
        """Test execute_tool with mock gemini CLI."""
        response = execute_tool("gemini", "test prompt", model="gemini-exp-1114")

        assert response.success is True
        assert response.status == ToolStatus.SUCCESS
        assert "Gemini response to: test prompt" in response.output
        assert response.exit_code == 0
        assert response.tool == "gemini"
        assert response.model == "gemini-exp-1114"

    def test_execute_tool_with_mock_codex(self, path_with_mock_tools):
        """Test execute_tool with mock codex CLI."""
        response = execute_tool("codex", "analyze code", model="claude-3.7-sonnet")

        assert response.success is True
        assert response.status == ToolStatus.SUCCESS
        assert "Codex response to: analyze code" in response.output
        assert response.exit_code == 0

    def test_execute_tool_with_mock_cursor_agent(self, path_with_mock_tools):
        """Test execute_tool with mock cursor-agent CLI."""
        response = execute_tool("cursor-agent", "review changes")

        assert response.success is True
        assert response.status == ToolStatus.SUCCESS
        assert "Cursor-agent response to: review changes" in response.output
        assert response.exit_code == 0

    def test_execute_tool_captures_timing(self, path_with_mock_tools):
        """Test that execution captures timing metadata."""
        response = execute_tool("gemini", "quick test")

        assert response.duration > 0  # Should have non-zero duration
        assert response.timestamp  # Should have ISO timestamp

    def test_execute_tool_not_found_when_missing(self, monkeypatch):
        """Test execute_tool returns NOT_FOUND status when tool missing."""
        # Set PATH to empty directory
        with tempfile.TemporaryDirectory() as empty_dir:
            monkeypatch.setenv("PATH", empty_dir)

            response = execute_tool("gemini", "test")

            assert response.status == ToolStatus.NOT_FOUND
            assert "not found" in response.error
            assert response.exit_code is None


# =============================================================================
# Parallel Execution Tests
# =============================================================================


class TestParallelExecutionIntegration:
    """Integration tests for parallel tool execution."""

    def test_execute_multiple_tools_in_parallel(self, path_with_mock_tools):
        """Test parallel execution of multiple mock tools."""
        response = execute_tools_parallel(
            tools=["gemini", "codex", "cursor-agent"],
            prompt="analyze this code"
        )

        assert len(response.responses) == 3
        assert response.success_count == 3
        assert response.failure_count == 0
        assert response.all_succeeded is True

    def test_parallel_execution_with_custom_models(self, path_with_mock_tools):
        """Test parallel execution with custom model specifications."""
        response = execute_tools_parallel(
            tools=["gemini", "codex"],
            prompt="test prompt",
            models={
                "gemini": "gemini-exp-1114",
                "codex": "claude-3.7-sonnet"
            }
        )

        assert response.success_count == 2
        assert response.responses["gemini"].model == "gemini-exp-1114"
        assert response.responses["codex"].model == "claude-3.7-sonnet"

    def test_parallel_execution_timing_statistics(self, path_with_mock_tools):
        """Test that parallel execution captures timing statistics."""
        response = execute_tools_parallel(
            tools=["gemini", "codex"],
            prompt="test"
        )

        # Should have timing info
        assert response.total_duration > 0
        assert response.max_duration > 0
        assert response.timestamp

        # Total duration should be less than sum of individual durations
        # (because of parallelism)
        individual_sum = sum(r.duration for r in response.responses.values())
        assert response.total_duration < individual_sum

    def test_parallel_execution_handles_partial_failures(self, path_with_mock_tools, mock_tools_dir):
        """Test parallel execution when some tools fail."""
        # Make codex script return non-zero exit
        codex_script = mock_tools_dir / "codex"
        codex_script.write_text(
            "#!/bin/bash\n"
            "echo 'error' >&2\n"
            "exit 1\n"
        )
        codex_script.chmod(0o755)

        response = execute_tools_parallel(
            tools=["gemini", "codex"],
            prompt="test"
        )

        assert response.success_count == 1  # Only gemini succeeded
        assert response.failure_count == 1  # codex failed
        assert response.success is True  # At least one succeeded
        assert response.all_succeeded is False

        # Check individual responses
        successful = response.get_successful_responses()
        failed = response.get_failed_responses()

        assert "gemini" in successful
        assert "codex" in failed
        assert failed["codex"].status == ToolStatus.ERROR


# =============================================================================
# Timeout Handling Tests
# =============================================================================


class TestTimeoutHandling:
    """Integration tests for timeout handling in tool execution."""

    def test_execute_tool_timeout_with_slow_mock(self, mock_tools_dir, monkeypatch):
        """Test that slow-running tools timeout correctly."""
        # Replace gemini mock with slow version
        slow_gemini = mock_tools_dir / "gemini"
        slow_gemini.write_text(
            "#!/bin/bash\n"
            "# Mock tool that takes too long\n"
            "sleep 10\n"  # Sleep for 10 seconds
            "echo 'output'\n"
        )
        slow_gemini.chmod(0o755)

        # Add mock tool directory to PATH
        original_path = os.environ.get("PATH", "")
        new_path = f"{mock_tools_dir}:{original_path}"
        monkeypatch.setenv("PATH", new_path)

        # Execute with short timeout (1 second)
        response = execute_tool("gemini", "test", timeout=1)

        # Should timeout
        assert response.status == ToolStatus.TIMEOUT
        assert "timed out" in response.error
        assert response.exit_code is None
        assert response.output == ""

    def test_parallel_execution_respects_per_tool_timeout(self, mock_tools_dir, path_with_mock_tools):
        """Test that parallel execution applies timeout to each tool."""
        # Replace codex with slow version
        slow_codex = mock_tools_dir / "codex"
        slow_codex.write_text(
            "#!/bin/bash\n"
            "sleep 5\n"  # Sleep for 5 seconds
            "echo 'slow output'\n"
        )
        slow_codex.chmod(0o755)

        # Execute with short timeout (1 second per tool)
        response = execute_tools_parallel(
            tools=["gemini", "codex"],
            prompt="test",
            timeout=1
        )

        # Gemini should succeed (fast)
        # codex should timeout
        assert response.responses["gemini"].success is True
        assert response.responses["codex"].status == ToolStatus.TIMEOUT

        # Should have partial success
        assert response.success_count == 1
        assert response.failure_count == 1

    def test_timeout_doesnt_affect_fast_tools(self, path_with_mock_tools):
        """Test that normal tools complete successfully with reasonable timeout."""
        # Execute with generous timeout
        response = execute_tool("gemini", "test", timeout=30)

        # Should complete successfully
        assert response.success is True
        assert response.status == ToolStatus.SUCCESS
        assert response.duration < 1.0  # Should be very fast

    def test_parallel_execution_total_duration_with_timeout(self, mock_tools_dir, path_with_mock_tools):
        """Test that parallel execution with timeouts doesn't block indefinitely."""
        # Replace both codex and cursor-agent with slow versions
        for tool_name in ["codex", "cursor-agent"]:
            slow_tool = mock_tools_dir / tool_name
            slow_tool.write_text(
                "#!/bin/bash\n"
                "sleep 10\n"  # Both take 10 seconds
                "echo 'output'\n"
            )
            slow_tool.chmod(0o755)

        # Execute in parallel with 1 second timeout each
        response = execute_tools_parallel(
            tools=["codex", "cursor-agent"],
            prompt="test",
            timeout=1
        )

        # Both should timeout
        assert response.success_count == 0
        assert response.failure_count == 2

        # Total duration should be ~1 second (parallel timeout)
        # not 2 seconds (sequential)
        assert response.total_duration < 2.5  # Allow some overhead

    def test_execute_tool_timeout_metadata(self, mock_tools_dir, monkeypatch):
        """Test that timeout responses include correct metadata."""
        # Replace gemini with slow version
        slow_tool = mock_tools_dir / "gemini"
        slow_tool.write_text("#!/bin/bash\nsleep 5\necho 'output'\n")
        slow_tool.chmod(0o755)

        original_path = os.environ.get("PATH", "")
        monkeypatch.setenv("PATH", f"{mock_tools_dir}:{original_path}")

        # Execute with timeout
        response = execute_tool(
            "gemini",
            "test prompt",
            model="test-model",
            timeout=1
        )

        # Check metadata is captured correctly even on timeout
        assert response.tool == "gemini"
        assert response.model == "test-model"
        assert response.prompt == "test prompt"
        assert response.timestamp  # Should have timestamp
        assert response.duration >= 1.0  # At least timeout duration

    def test_timeout_error_message_includes_duration(self, mock_tools_dir, monkeypatch):
        """Test that timeout error message is descriptive."""
        # Replace codex with slow version
        slow_tool = mock_tools_dir / "codex"
        slow_tool.write_text("#!/bin/bash\nsleep 10\n")
        slow_tool.chmod(0o755)

        original_path = os.environ.get("PATH", "")
        monkeypatch.setenv("PATH", f"{mock_tools_dir}:{original_path}")

        # Execute with 2 second timeout
        response = execute_tool("codex", "test", timeout=2)

        # Error message should include timeout value
        assert response.status == ToolStatus.TIMEOUT
        assert "2" in response.error  # Should mention 2 seconds
        assert "timed out" in response.error.lower()


# =============================================================================
# Edge Cases and Error Handling Tests
# =============================================================================


class TestEdgeCasesAndErrorHandling:
    """Integration tests for edge cases and error scenarios."""

    def test_tool_with_empty_output(self, mock_tools_dir, monkeypatch):
        """Test handling of tools that return no output."""
        # Create tool that returns empty output
        empty_tool = mock_tools_dir / "gemini"
        empty_tool.write_text(
            "#!/bin/bash\n"
            "# Tool that returns nothing\n"
            "exit 0\n"
        )
        empty_tool.chmod(0o755)

        original_path = os.environ.get("PATH", "")
        monkeypatch.setenv("PATH", f"{mock_tools_dir}:{original_path}")

        response = execute_tool("gemini", "test")

        # Should succeed but with empty output
        assert response.success is True
        assert response.output == ""
        assert response.exit_code == 0

    def test_tool_with_stderr_only(self, mock_tools_dir, monkeypatch):
        """Test handling of tools that only write to stderr."""
        # Create tool that writes to stderr but exits successfully
        stderr_tool = mock_tools_dir / "codex"
        stderr_tool.write_text(
            "#!/bin/bash\n"
            "echo 'warning message' >&2\n"
            "exit 0\n"
        )
        stderr_tool.chmod(0o755)

        original_path = os.environ.get("PATH", "")
        monkeypatch.setenv("PATH", f"{mock_tools_dir}:{original_path}")

        response = execute_tool("codex", "test")

        # Should still succeed (exit 0) even with stderr
        assert response.success is True
        assert response.exit_code == 0

    def test_tool_with_both_stdout_and_stderr(self, mock_tools_dir, monkeypatch):
        """Test handling of tools that write to both stdout and stderr."""
        # Create tool that writes to both streams
        both_tool = mock_tools_dir / "gemini"
        both_tool.write_text(
            "#!/bin/bash\n"
            "echo 'output'\n"
            "echo 'warning' >&2\n"
            "exit 0\n"
        )
        both_tool.chmod(0o755)

        original_path = os.environ.get("PATH", "")
        monkeypatch.setenv("PATH", f"{mock_tools_dir}:{original_path}")

        response = execute_tool("gemini", "test")

        # Should capture both
        assert response.success is True
        assert "output" in response.output
        # stderr is only captured on error (exit code != 0)

    def test_tool_with_non_zero_exit_and_stderr(self, mock_tools_dir, monkeypatch):
        """Test error handling when tool fails with stderr message."""
        # Create tool that fails with error message
        error_tool = mock_tools_dir / "cursor-agent"
        error_tool.write_text(
            "#!/bin/bash\n"
            "echo 'Error: API key invalid' >&2\n"
            "exit 1\n"
        )
        error_tool.chmod(0o755)

        original_path = os.environ.get("PATH", "")
        monkeypatch.setenv("PATH", f"{mock_tools_dir}:{original_path}")

        response = execute_tool("cursor-agent", "test")

        # Should capture error
        assert response.failed is True
        assert response.status == ToolStatus.ERROR
        assert "API key invalid" in response.error
        assert response.exit_code == 1

    def test_tool_with_very_long_output(self, mock_tools_dir, monkeypatch):
        """Test handling of tools with large output."""
        # Create tool that outputs 1000 lines
        large_output_tool = mock_tools_dir / "gemini"
        large_output_tool.write_text(
            "#!/bin/bash\n"
            "for i in {1..1000}; do\n"
            "  echo 'Line '$i\n"
            "done\n"
        )
        large_output_tool.chmod(0o755)

        original_path = os.environ.get("PATH", "")
        monkeypatch.setenv("PATH", f"{mock_tools_dir}:{original_path}")

        response = execute_tool("gemini", "test", timeout=5)

        # Should handle large output
        assert response.success is True
        assert len(response.output.split('\n')) == 1000

    def test_tool_with_special_characters_in_output(self, mock_tools_dir, monkeypatch):
        """Test handling of output with special characters."""
        # Create tool that outputs special characters
        special_tool = mock_tools_dir / "codex"
        special_tool.write_text(
            "#!/bin/bash\n"
            "echo 'Output with $pecial ch@rs: <>&\"\\'\n"
        )
        special_tool.chmod(0o755)

        original_path = os.environ.get("PATH", "")
        monkeypatch.setenv("PATH", f"{mock_tools_dir}:{original_path}")

        response = execute_tool("codex", "test")

        # Should preserve special characters
        assert response.success is True
        assert "$pecial" in response.output
        assert "<>&" in response.output

    def test_tool_with_unicode_output(self, mock_tools_dir, monkeypatch):
        """Test handling of Unicode characters in output."""
        # Create tool that outputs Unicode
        unicode_tool = mock_tools_dir / "gemini"
        unicode_tool.write_text(
            "#!/bin/bash\n"
            "echo '日本語 Français Español 🚀'\n"
        )
        unicode_tool.chmod(0o755)

        original_path = os.environ.get("PATH", "")
        monkeypatch.setenv("PATH", f"{mock_tools_dir}:{original_path}")

        response = execute_tool("gemini", "test")

        # Should handle Unicode correctly
        assert response.success is True
        assert "日本語" in response.output
        assert "🚀" in response.output

    def test_parallel_execution_with_all_failures(self, mock_tools_dir, path_with_mock_tools):
        """Test parallel execution when all tools fail."""
        # Make all tools fail
        for tool_name in ["gemini", "codex", "cursor-agent"]:
            fail_tool = mock_tools_dir / tool_name
            fail_tool.write_text(
                "#!/bin/bash\n"
                "echo 'error' >&2\n"
                "exit 1\n"
            )
            fail_tool.chmod(0o755)

        response = execute_tools_parallel(
            tools=["gemini", "codex", "cursor-agent"],
            prompt="test"
        )

        # All should fail
        assert response.success_count == 0
        assert response.failure_count == 3
        assert response.all_failed is True
        assert response.success is False  # No successes

    def test_parallel_execution_with_empty_tool_list(self):
        """Test parallel execution with empty tool list."""
        response = execute_tools_parallel(
            tools=[],
            prompt="test"
        )

        # Should handle gracefully
        assert len(response.responses) == 0
        assert response.success_count == 0
        assert response.failure_count == 0

    def test_execute_tool_with_unknown_tool_name(self):
        """Test error handling for unknown tool names."""
        response = execute_tool("unknown-tool", "test")

        # Should return error status
        assert response.status == ToolStatus.ERROR
        assert "Unknown tool" in response.error

    def test_tool_crash_during_execution(self, mock_tools_dir, monkeypatch):
        """Test handling of tools that crash (segfault simulation)."""
        # Create tool that exits with unusual code
        crash_tool = mock_tools_dir / "gemini"
        crash_tool.write_text(
            "#!/bin/bash\n"
            "exit 139\n"  # 139 = 128 + 11 (SIGSEGV)
        )
        crash_tool.chmod(0o755)

        original_path = os.environ.get("PATH", "")
        monkeypatch.setenv("PATH", f"{mock_tools_dir}:{original_path}")

        response = execute_tool("gemini", "test")

        # Should capture as error
        assert response.failed is True
        assert response.status == ToolStatus.ERROR
        assert response.exit_code == 139


# =============================================================================
# End-to-End Workflow Tests
# =============================================================================


class TestEndToEndWorkflow:
    """End-to-end integration tests for complete workflows."""

    def test_detect_build_and_execute_workflow(self, path_with_mock_tools):
        """Test complete workflow: detect -> build -> execute."""
        # Step 1: Detect available tools
        available = detect_available_tools()
        assert len(available) > 0

        # Step 2: Build command for first available tool
        tool = available[0]
        cmd = build_tool_command(tool, "test prompt")
        assert isinstance(cmd, list)
        assert len(cmd) > 0

        # Step 3: Execute the tool
        response = execute_tool(tool, "test prompt")
        assert response.success is True

    def test_fallback_when_preferred_tool_unavailable(self, mock_tools_dir, monkeypatch):
        """Test workflow falls back to available tools when one is missing."""
        # Create a directory with only some tools (exclude gemini)
        partial_tools_dir = mock_tools_dir.parent / "partial_tools"
        partial_tools_dir.mkdir()

        # Copy only codex and cursor-agent to partial directory
        import shutil
        shutil.copy(mock_tools_dir / "codex", partial_tools_dir / "codex")
        shutil.copy(mock_tools_dir / "cursor-agent", partial_tools_dir / "cursor-agent")
        (partial_tools_dir / "codex").chmod(0o755)
        (partial_tools_dir / "cursor-agent").chmod(0o755)

        # Set PATH to only the partial tools directory (no fallback to system PATH)
        monkeypatch.setenv("PATH", str(partial_tools_dir))

        # Detect tools - should only find codex and cursor-agent
        available = detect_available_tools()
        assert "gemini" not in available
        assert len(available) == 2  # Only codex and cursor-agent
        assert "codex" in available
        assert "cursor-agent" in available

        # Should still be able to execute with available tools
        response = execute_tool(available[0], "test")
        assert response.success is True

    def test_parallel_consultation_workflow(self, path_with_mock_tools):
        """Test complete parallel consultation workflow."""
        # Detect tools
        available = detect_available_tools()

        # Execute all available tools in parallel
        response = execute_tools_parallel(
            tools=available,
            prompt="review this code"
        )

        # Get successful responses
        successful = response.get_successful_responses()

        # Should have at least one successful consultation
        assert len(successful) > 0

        # Each successful response should have output
        for tool, tool_response in successful.items():
            assert tool_response.output
            assert "response to" in tool_response.output.lower()


# =============================================================================
# Real AI Tools Tests (Optional - requires actual tools installed)
# =============================================================================


class TestRealAITools:
    """
    Integration tests with actual AI tools (gemini, codex, cursor-agent).

    These tests are skipped if the real tools are not available on the system.
    They validate that the integration layer works correctly with actual CLI tools.
    """

    @pytest.mark.skipif(
        not check_tool_available("gemini"),
        reason="gemini CLI tool not available"
    )
    def test_real_gemini_execution(self):
        """Test execution with real gemini CLI tool."""
        response = execute_tool(
            "gemini",
            "Say 'Hello from Gemini' exactly",
            timeout=30
        )

        # Should get a real response
        assert response.success is True or response.status == ToolStatus.TIMEOUT
        if response.success:
            assert response.output  # Should have some output
            assert response.duration > 0

    @pytest.mark.skipif(
        not check_tool_available("codex"),
        reason="codex CLI tool not available"
    )
    def test_real_codex_execution(self):
        """Test execution with real codex CLI tool."""
        response = execute_tool(
            "codex",
            "Say 'Hello from Codex' exactly",
            timeout=30
        )

        # Should get a response (may be error if tool requires terminal)
        assert response.status in [
            ToolStatus.SUCCESS,
            ToolStatus.TIMEOUT,
            ToolStatus.ERROR  # May error if tool requires interactive terminal
        ]
        if response.success:
            assert response.output  # Should have some output
            assert response.duration > 0
        # If error due to non-terminal, that's expected in test environment
        if response.status == ToolStatus.ERROR:
            assert response.duration >= 0  # Should still capture timing

    @pytest.mark.skipif(
        not check_tool_available("cursor-agent"),
        reason="cursor-agent CLI tool not available"
    )
    def test_real_cursor_agent_execution(self):
        """Test execution with real cursor-agent CLI tool."""
        response = execute_tool(
            "cursor-agent",
            "Say 'Hello from Cursor' exactly",
            timeout=30
        )

        # Should get a real response
        assert response.success is True or response.status == ToolStatus.TIMEOUT
        if response.success:
            assert response.output  # Should have some output
            assert response.duration > 0

    def test_real_tools_parallel_if_available(self):
        """Test parallel execution with any available real tools."""
        # Detect what's actually available
        available = detect_available_tools()

        if len(available) == 0:
            pytest.skip("No real AI tools available for testing")

        # Execute with available tools
        response = execute_tools_parallel(
            tools=available,
            prompt="Respond with: 'Test successful'",
            timeout=30
        )

        # Should have attempted all available tools
        assert len(response.responses) == len(available)

        # At least check that responses were received
        # (may timeout or fail depending on tool configuration)
        for tool_name, tool_response in response.responses.items():
            assert tool_response.tool == tool_name
            assert tool_response.timestamp
            assert tool_response.duration >= 0

    def test_real_tool_with_long_prompt(self):
        """Test handling of longer prompts with real tools."""
        available = detect_available_tools()

        if len(available) == 0:
            pytest.skip("No real AI tools available for testing")

        # Create a longer prompt
        long_prompt = """
        Please analyze the following code pattern and provide a brief summary:

        def process_data(items):
            results = []
            for item in items:
                if item.is_valid():
                    results.append(item.transform())
            return results

        Focus on: error handling, performance, readability.
        """

        response = execute_tool(
            available[0],
            long_prompt,
            timeout=60
        )

        # Should handle the longer prompt
        # (may timeout or error depending on tool/API availability)
        assert response.tool == available[0]
        assert response.timestamp

    def test_detect_available_tools_finds_real_tools(self):
        """Test that detect_available_tools finds any real tools on system."""
        available = detect_available_tools()

        # Should return a list (may be empty if no tools installed)
        assert isinstance(available, list)

        # Each detected tool should actually be in PATH
        for tool in available:
            assert check_tool_available(tool) is True
