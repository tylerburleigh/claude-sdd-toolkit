from __future__ import annotations

import json
import os
import subprocess
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import pytest

from claude_skills.common.ai_tools import (
    ToolStatus,
    build_tool_command,
    check_tool_available,
    detect_available_tools,
    execute_tool,
    execute_tools_parallel,
)

from .cli_runner import run_cli


pytestmark = pytest.mark.integration


@dataclass
class MockToolSuite:
    directory: Path
    env: Mapping[str, str]

    def path_for(self, name: str) -> Path:
        return self.directory / name

    def rewrite(self, name: str, body: str) -> None:
        script = self.path_for(name)
        script.write_text(textwrap.dedent(body).lstrip())
        script.chmod(0o755)

    def remove(self, name: str) -> None:
        try:
            self.path_for(name).unlink()
        except FileNotFoundError:
            pass


@pytest.fixture
def mock_tools(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> MockToolSuite:
    """
    Create mock CLI binaries (gemini, codex, cursor-agent) that mimic common behaviours.
    """

    scripts_dir = tmp_path / "mock_tools"
    scripts_dir.mkdir()

    def write_script(name: str, body: str) -> None:
        script_path = scripts_dir / name
        script_path.write_text(textwrap.dedent(body).lstrip())
        script_path.chmod(0o755)

    write_script(
        "gemini",
        """
        #!/bin/bash
        if [[ "$1" == "--version" ]]; then
          echo "gemini version 1.0.0"
          exit 0
        fi

        model=""
        prompt=""
        while [[ $# -gt 0 ]]; do
          case "$1" in
            -m|--model)
              model="$2"
              shift 2
              ;;
            --output-format)
              shift 2
              ;;
            -p)
              prompt="$2"
              shift 2
              ;;
            *)
              prompt="$1"
              shift
              ;;
          esac
        done

        if [[ -z "$prompt" ]]; then
          prompt="(no prompt)"
        fi

        if [[ -z "$model" ]]; then
          model="gemini-2.0-pro"
        fi

        python3 - "$prompt" "$model" <<'PY'
import json
import sys

prompt = sys.argv[1]
model = sys.argv[2]
payload = {
    "response": f"Gemini response to: {prompt}",
    "model": model,
    "stats": {
        "models": {
            model: {
                "tokens": {
                    "prompt": 1,
                    "candidates": 1,
                    "total": 2,
                }
            }
        }
    },
}
print(json.dumps(payload))
PY
        """,
    )


    write_script(
        "codex",
        """
        #!/bin/bash
        if [[ "$1" == "--version" ]]; then
          echo "codex version 1.0.0"
          exit 0
        fi

        prompt=""
        while [[ $# -gt 0 ]]; do
          case "$1" in
            exec)
              shift
              ;;
            --sandbox|--ask-for-approval)
              shift 2
              ;;
            --json)
              shift
              ;;
            -m)
              shift 2
              ;;
            *)
              prompt="$1"
              shift
              ;;
          esac
        done

        if [[ -z "$prompt" ]]; then
          prompt="(no prompt)"
        fi

        python3 - "$prompt" <<'PY'
import json
import sys

prompt = sys.argv[1]
messages = [
    {"type": "thread.started", "thread_id": "thread-123"},
    {
        "type": "item.completed",
        "agent_message": {"content": f"Codex response to: {prompt}"},
        "model": "gpt-4o",
    },
    {
        "type": "turn.completed",
        "usage": {"input_tokens": 3, "output_tokens": 7, "total_tokens": 10},
    },
]
for message in messages:
    print(json.dumps(message))
PY
        """,
    )


    write_script(
        "cursor-agent",
        """
        #!/bin/bash
        if [[ "$1" == "--version" ]]; then
          echo "cursor-agent version 1.0.0"
          exit 0
        fi

        prompt=""
        while [[ $# -gt 0 ]]; do
          case "$1" in
            --print|--json)
              shift
              ;;
            --model)
              shift 2
              ;;
            --temperature|--max-tokens|--system|--working-directory)
              shift 2
              ;;
            --prompt)
              prompt="$2"
              shift 2
              ;;
            *)
              prompt="$1"
              shift
              ;;
          esac
        done

        if [[ -z "$prompt" ]]; then
          prompt="(no prompt)"
        fi

        python3 - "$prompt" <<'PY'
import json
import sys

prompt = sys.argv[1]
payload = {
    "content": f"Cursor-agent response to: {prompt}",
    "model": "cursor-default",
    "usage": {"input_tokens": 4, "output_tokens": 6, "total_tokens": 10},
}
print(json.dumps(payload))
PY
        """,
    )


    original_path = os.environ.get("PATH", "")
    injected_path = f"{scripts_dir}{os.pathsep}{original_path}"
    monkeypatch.setenv("PATH", injected_path)
    monkeypatch.setenv("CLAUDE_SKILLS_TOOL_PATH", str(scripts_dir))

    return MockToolSuite(
        directory=scripts_dir,
        env={
            "PATH": injected_path,
            "CLAUDE_SKILLS_TOOL_PATH": str(scripts_dir),
        },
    )


def test_detect_available_tools_discovers_mock_binaries(mock_tools: MockToolSuite) -> None:
    available = detect_available_tools()
    assert {"gemini", "codex", "cursor-agent"} <= set(available)


def test_check_tool_available_with_version(mock_tools: MockToolSuite) -> None:
    assert check_tool_available("gemini", check_version=True) is True
    assert check_tool_available("codex", check_version=True) is True
    assert check_tool_available("cursor-agent", check_version=True) is True


def test_detect_available_tools_without_version_check(mock_tools: MockToolSuite) -> None:
    available = detect_available_tools(check_version=False)
    assert set(available) == {"gemini", "codex", "cursor-agent"}


def test_detect_available_tools_when_none_available(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    monkeypatch.setenv("PATH", str(empty_dir))
    assert detect_available_tools() == []


def test_detect_available_tools_handles_partial_availability(mock_tools: MockToolSuite) -> None:
    mock_tools.remove("codex")
    mock_tools.remove("cursor-agent")
    available = detect_available_tools()
    assert set(available) == {"gemini"}


def test_build_tool_command_executes_successfully(mock_tools: MockToolSuite) -> None:
    command = build_tool_command("gemini", "test prompt", model="gemini-exp-1114")
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert "Gemini response to:" in result.stdout
    assert "test prompt" in result.stdout


def test_build_tool_command_handles_special_characters(mock_tools: MockToolSuite) -> None:
    prompt = "Analyze: 'quotes' \"double\" $VAR"
    command = build_tool_command("codex", prompt)
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    assert result.returncode == 0
    lines = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    item_event = next(event for event in lines if event.get("type") == "item.completed")
    assert item_event["agent_message"]["content"] == "Codex response to: Analyze: 'quotes' \"double\" $VAR"


def test_build_tool_command_uses_list_invocation(mock_tools: MockToolSuite) -> None:
    command = build_tool_command("codex", "inspect", model="codex-pro")
    assert command[0] == "codex"
    assert any(flag in ("-m", "--model") for flag in command)


def test_execute_tool_runs_mock_binary(mock_tools: MockToolSuite) -> None:
    response = execute_tool("gemini", "hello world", timeout=5)
    assert response.status is ToolStatus.SUCCESS
    assert "Gemini response to:" in response.output
    assert "hello world" in response.output
    assert response.exit_code is None


def test_execute_tool_captures_timing_metadata(mock_tools: MockToolSuite) -> None:
    response = execute_tool("codex", "collect timing", timeout=5)
    assert response.duration >= 0
    assert response.timestamp
    assert response.status is ToolStatus.SUCCESS


def test_execute_tool_handles_missing_tool(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))
    response = execute_tool("gemini", "test")
    assert response.status is ToolStatus.NOT_FOUND
    error_text = (response.error or "").lower()
    assert "not found" in error_text or "unavailable" in error_text


def test_execute_tool_handles_stderr_only_output(mock_tools: MockToolSuite) -> None:
    mock_tools.rewrite(
        "codex",
        """
        #!/bin/bash
        if [[ "$1" == "--version" ]]; then
          echo "codex mock"
          exit 0
        fi
        echo "warning message" >&2
        echo '{"type": "thread.started", "thread_id": "thread-123"}'
        echo '{"type": "item.completed", "agent_message": {"content": "Codex response to: stderr test"}, "model": "gpt-4o"}'
        echo '{"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2}}'
        """,
    )
    response = execute_tool("codex", "test")
    assert response.status is ToolStatus.SUCCESS
    assert response.output == "Codex response to: stderr test"
    assert response.metadata.get("stderr") == "warning message"
    assert response.error is None


def test_execute_tool_handles_large_output(mock_tools: MockToolSuite) -> None:
    mock_tools.rewrite(
        "gemini",
        """
        #!/bin/bash
        if [[ "$1" == "--version" || "$1" == "--help" ]]; then
          echo "gemini mock"
          exit 0
        fi
        python3 - <<'PY'
import json

content = chr(10).join(f"Line {i}" for i in range(1, 201))
payload = {
    "response": content,
    "model": "gemini-2.0-pro",
    "stats": {"models": {"gemini-2.0-pro": {"tokens": {"prompt": 1, "candidates": 1, "total": 2}}}},
}
print(json.dumps(payload))
PY
        """,
    )

    response = execute_tool("gemini", "big output", timeout=5)
    assert response.status is ToolStatus.SUCCESS
    assert len(response.output.splitlines()) == 200


def test_execute_tool_handles_unicode_output(mock_tools: MockToolSuite) -> None:
    mock_tools.rewrite(
        "codex",
        """
        #!/bin/bash
        if [[ "$1" == "--version" ]]; then
          echo "codex mock"
          exit 0
        fi
        echo '{"type": "thread.started", "thread_id": "thread-123"}'
        echo '{"type": "item.completed", "agent_message": {"content": "こんにちは 世界 🚀"}, "model": "gpt-4o"}'
        echo '{"type": "turn.completed", "usage": {"input_tokens": 2, "output_tokens": 2, "total_tokens": 4}}'
        """,
    )
    response = execute_tool("codex", "unicode")
    assert response.status is ToolStatus.SUCCESS
    assert "🚀" in response.output


def test_execute_tool_handles_non_zero_exit(mock_tools: MockToolSuite) -> None:
    mock_tools.rewrite(
        "cursor-agent",
        """
        #!/bin/bash
        if [[ "$1" == "--version" ]]; then
          echo "cursor mock"
          exit 0
        fi
        echo "Error: API key invalid" >&2
        exit 3
        """,
    )
    response = execute_tool("cursor-agent", "fail fast")
    assert response.status is ToolStatus.ERROR
    assert "api key invalid" in (response.error or "").lower()


def test_execute_tool_handles_timeout(mock_tools: MockToolSuite) -> None:
    mock_tools.rewrite(
        "gemini",
        """
        #!/bin/bash
        if [[ "$1" == "--version" || "$1" == "--help" ]]; then
          echo "gemini mock"
          exit 0
        fi
        sleep 2
        echo "slow"
        """,
    )
    response = execute_tool("gemini", "slow prompt", timeout=0.2)
    assert response.status is ToolStatus.TIMEOUT
    assert response.output == ""
    assert "timed out" in (response.error or "").lower()


def test_execute_tool_handles_crash_exit_code(mock_tools: MockToolSuite) -> None:
    mock_tools.rewrite(
        "gemini",
        """
        #!/bin/bash
        if [[ "$1" == "--version" || "$1" == "--help" ]]; then
          echo "gemini mock"
          exit 0
        fi
        exit 139
        """,
    )
    response = execute_tool("gemini", "crash soon")
    assert response.status is ToolStatus.ERROR


def test_execute_tools_parallel_all_success(mock_tools: MockToolSuite) -> None:
    result = execute_tools_parallel(
        tools=["gemini", "codex", "cursor-agent"],
        prompt="analyze",
    )
    assert result.success_count == 3
    assert result.failure_count == 0
    assert result.all_succeeded is True


def test_execute_tools_parallel_partial_failure(mock_tools: MockToolSuite) -> None:
    mock_tools.rewrite(
        "codex",
        """
        #!/bin/bash
        if [[ "$1" == "--version" ]]; then
          echo "codex mock"
          exit 0
        fi
        echo "error" >&2
        exit 1
        """,
    )
    result = execute_tools_parallel(
        tools=["gemini", "codex"],
        prompt="mixed",
        timeout=1,
    )
    assert result.success_count == 1
    assert result.failure_count == 1
    assert result.responses["codex"].status is ToolStatus.ERROR


def test_execute_tools_parallel_collects_statistics(mock_tools: MockToolSuite) -> None:
    result = execute_tools_parallel(
        tools=["gemini", "codex"],
        prompt="stats",
        timeout=2,
    )
    individual_sum = sum(r.duration for r in result.responses.values())
    assert result.total_duration <= individual_sum
    assert result.max_duration >= 0
    assert result.timestamp


def test_execute_tools_parallel_empty_tool_list() -> None:
    result = execute_tools_parallel(tools=[], prompt="noop")
    assert result.success_count == 0
    assert result.failure_count == 0
    assert result.responses == {}


def test_execute_tools_parallel_all_fail(mock_tools: MockToolSuite) -> None:
    failure_body = """
        #!/bin/bash
        echo "error" >&2
        exit 2
    """
    mock_tools.rewrite("gemini", failure_body)
    mock_tools.rewrite("codex", failure_body)
    result = execute_tools_parallel(
        tools=["gemini", "codex"],
        prompt="all fail",
    )
    assert result.success is False
    assert result.failure_count == 2
    assert result.all_failed is True


def test_cli_check_tools_reports_mock_binaries(mock_tools: MockToolSuite) -> None:
    result = run_cli("test", "check-tools", "--json", env=mock_tools.env)
    assert result.returncode in (0, 1)
    payload = json.loads(result.stdout)
    tools_list = payload.get("tools") or payload.get("available") or []
    assert any(
        (isinstance(tool, dict) and tool.get("name") == "gemini")
        or tool == "gemini"
        for tool in tools_list
    )


def test_cli_check_tools_handles_missing_binaries() -> None:
    result = run_cli("test", "check-tools", "--json", env={"PATH": ""})
    assert result.returncode in (0, 1)
    payload = json.loads(result.stdout)
    tools_list = payload.get("tools") or payload.get("available") or []
    assert tools_list == [] or len(tools_list) == 0


@pytest.mark.skipif(
    not os.environ.get("SDD_TEST_USE_REAL_TOOLS"),
    reason="Real tool smoke tests disabled (set SDD_TEST_USE_REAL_TOOLS=1 to enable)",
)
def test_real_tools_optional_smoke() -> None:
    available = detect_available_tools()
    if not available:
        pytest.skip("No real AI tools available on PATH")

    response = execute_tool(available[0], "Say 'Hello from real tool'", timeout=15)
    assert response.tool == available[0]
    assert response.timestamp
    assert response.status in {
        ToolStatus.SUCCESS,
        ToolStatus.TIMEOUT,
        ToolStatus.ERROR,
    }
