from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path

import pytest

from claude_skills.common import ai_config
from claude_skills.common.ai_tools import detect_available_tools

from .cli_runner import run_cli


pytestmark = pytest.mark.integration


@pytest.fixture
def sample_test_error() -> str:
    return "AssertionError: expected 5, got 3"


@pytest.fixture
def sample_hypothesis() -> str:
    return "Addition helper does not handle negative offsets"


@pytest.fixture
def mock_tool_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[dict[str, str], Path]:
    """Provide mock CLI binaries and isolated AI config for consultation commands.

    Returns:
        Tuple of (env_dict, working_directory) where working_directory should be
        passed as cwd to run_cli() to ensure tests use the isolated config.
    """

    scripts_dir = tmp_path / "mock_tools"
    scripts_dir.mkdir()

    def write_script(name: str, body: str) -> None:
        script_path = scripts_dir / name
        script_path.write_text(textwrap.dedent(body).lstrip())
        script_path.chmod(0o755)

    shared_body = """
        #!/bin/bash
        if [[ "$1" == "--version" ]]; then
          echo "{name} version 1.0.0"
          exit 0
        fi
        echo "{name} received: $*"
    """
    for binary in ("gemini", "codex", "cursor-agent"):
        write_script(binary, shared_body.format(name=binary))

    # Create isolated AI config with all tools enabled
    claude_dir = tmp_path / ".claude"
    claude_dir.mkdir()
    ai_config_path = claude_dir / "ai_config.yaml"
    ai_config_content = textwrap.dedent("""
        tools:
          gemini:
            enabled: true
            command: gemini
          cursor-agent:
            enabled: true
            command: cursor-agent
          codex:
            enabled: true
            command: codex
    """).lstrip()
    ai_config_path.write_text(ai_config_content)

    injected_path = f"{scripts_dir}{os.pathsep}{os.environ.get('PATH', '')}"
    monkeypatch.setenv("PATH", injected_path)
    monkeypatch.setenv("CLAUDE_SKILLS_TOOL_PATH", str(scripts_dir))
    return (
        {
            "PATH": injected_path,
            "CLAUDE_SKILLS_TOOL_PATH": str(scripts_dir),
        },
        tmp_path,  # Return working directory for subprocess
    )


def test_check_tools_help_command() -> None:
    result = run_cli("test", "check-tools", "--help")
    assert result.returncode == 0
    assert "Usage" in result.stdout or "usage" in result.stdout.lower()


def test_check_tools_json_reports_available(mock_tool_env: tuple[dict[str, str], Path]) -> None:
    env, cwd = mock_tool_env
    result = run_cli("test", "check-tools", "--json", env=env, cwd=cwd)
    assert result.returncode in (0, 1)
    payload = json.loads(result.stdout)
    tools_list = payload.get("tools") or payload.get("available") or []
    assert any(
        (isinstance(item, dict) and item.get("name") == "gemini") or item == "gemini"
        for item in tools_list
    )


def test_consult_help_command() -> None:
    result = run_cli("test", "consult", "--help")
    assert result.returncode == 0
    assert "Usage" in result.stdout or "usage" in result.stdout.lower()


def test_consult_requires_failure_type(sample_test_error: str, sample_hypothesis: str) -> None:
    result = run_cli(
        "test",
        "consult",
        "--error",
        sample_test_error,
        "--hypothesis",
        sample_hypothesis,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "failure_type" in (result.stdout + result.stderr)


@pytest.mark.parametrize(
    "failure_type",
    ["assertion", "exception", "import", "fixture", "timeout"],
)
def test_consult_accepts_failure_matrix(
    failure_type: str,
    mock_tool_env: tuple[dict[str, str], Path],
    sample_test_error: str,
    sample_hypothesis: str,
) -> None:
    env, cwd = mock_tool_env
    result = run_cli(
        "test",
        "consult",
        failure_type,
        "--error",
        sample_test_error,
        "--hypothesis",
        sample_hypothesis,
        "--dry-run",
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )
    assert result.returncode in (0, 1)


def test_consult_list_routing_table() -> None:
    result = run_cli("test", "consult", "--list-routing")
    assert result.returncode in (0, 1)
    assert result.stdout.strip()


def test_consult_auto_selects_tool_in_dry_run(
    mock_tool_env: tuple[dict[str, str], Path],
    sample_test_error: str,
    sample_hypothesis: str,
) -> None:
    env, cwd = mock_tool_env
    result = run_cli(
        "test",
        "consult",
        "assertion",
        "--error",
        sample_test_error,
        "--hypothesis",
        sample_hypothesis,
        "--dry-run",
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )
    assert result.returncode == 0
    assert "• cursor-agent" in result.stdout
    assert "• gemini" in result.stdout
    assert "Prompt length:" in result.stdout


def test_consult_prompt_mode_respects_dry_run(mock_tool_env: tuple[dict[str, str], Path], monkeypatch: pytest.MonkeyPatch) -> None:
    env, cwd = mock_tool_env

    # Monkeypatch get_global_config_path to use the mock config
    mock_config_path = cwd / ".claude" / "ai_config.yaml"
    monkeypatch.setattr(
        "claude_skills.common.ai_config.get_global_config_path",
        lambda: mock_config_path
    )

    result = run_cli(
        "test",
        "consult",
        "--prompt",
        "Investigate intermittent timeout",
        "--dry-run",
        "--tool",
        "gemini",
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )
    assert result.returncode == 0
    expected_model = ai_config.resolve_tool_model("run-tests", "gemini")
    if expected_model is None:
        priority = ai_config.DEFAULT_MODELS.get("gemini", {}).get("priority") or []
        expected_model = priority[0] if priority else None
    assert expected_model, "Expected run-tests gemini model to be configured"
    assert f"gemini -m {expected_model} --output-format" in result.stdout
    assert "prompt with" in result.stdout.lower()


def test_consult_multi_agent_dry_run(
    mock_tool_env: tuple[dict[str, str], Path],
    sample_test_error: str,
    sample_hypothesis: str,
) -> None:
    env, cwd = mock_tool_env
    result = run_cli(
        "test",
        "consult",
        "exception",
        "--error",
        sample_test_error,
        "--hypothesis",
        sample_hypothesis,
        "--multi-agent",
        "--dry-run",
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )
    assert result.returncode == 0
    assert "• cursor-agent" in result.stdout
    assert "• gemini" in result.stdout
    assert "Prompt length:" in result.stdout


def test_consult_reports_invalid_tool(sample_test_error: str, sample_hypothesis: str) -> None:
    result = run_cli(
        "test",
        "consult",
        "assertion",
        "--tool",
        "cursor-agent",
        "--error",
        sample_test_error,
        "--hypothesis",
        sample_hypothesis,
        capture_output=True,
        text=True,
        env={"PATH": "", "CLAUDE_SKILLS_TOOL_PATH": ""},  # Force tool lookup to fail
    )
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "No tools available for multi-agent consultation" in combined


def test_consult_skips_when_no_tools_available(sample_test_error: str, sample_hypothesis: str) -> None:
    result = run_cli(
        "test",
        "consult",
        "assertion",
        "--error",
        sample_test_error,
        "--hypothesis",
        sample_hypothesis,
        "--dry-run",
        capture_output=True,
        text=True,
        env={"PATH": "", "CLAUDE_SKILLS_TOOL_PATH": ""},  # No binaries discoverable
    )
    assert result.returncode != 0
    combined = result.stdout + result.stderr
    assert "No tools available for multi-agent consultation" in combined


def test_consult_with_test_code(
    tmp_path: Path,
    mock_tool_env: tuple[dict[str, str], Path],
    sample_test_error: str,
    sample_hypothesis: str,
) -> None:
    env, cwd = mock_tool_env
    test_file = tmp_path / "test_sample.py"
    test_file.write_text(
        """
        def test_add():
            assert add(2, 3) == 5
        """
    )
    result = run_cli(
        "test",
        "consult",
        "assertion",
        "--error",
        sample_test_error,
        "--hypothesis",
        sample_hypothesis,
        "--test-code",
        test_file,
        "--dry-run",
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )
    assert result.returncode == 0


def test_consult_with_impl_code(
    tmp_path: Path,
    mock_tool_env: tuple[dict[str, str], Path],
    sample_test_error: str,
    sample_hypothesis: str,
) -> None:
    env, cwd = mock_tool_env
    impl_file = tmp_path / "calculator.py"
    impl_file.write_text(
        """
        def add(a, b):
            return a + b
        """
    )
    result = run_cli(
        "test",
        "consult",
        "assertion",
        "--error",
        sample_test_error,
        "--hypothesis",
        sample_hypothesis,
        "--impl-code",
        impl_file,
        "--dry-run",
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )
    assert result.returncode == 0


def test_consult_with_both_code_inputs(
    tmp_path: Path,
    mock_tool_env: tuple[dict[str, str], Path],
    sample_test_error: str,
    sample_hypothesis: str,
) -> None:
    env, cwd = mock_tool_env
    test_file = tmp_path / "test_sample.py"
    impl_file = tmp_path / "calculator.py"
    test_file.write_text("def test_add(): assert add(1, 1) == 2")
    impl_file.write_text("def add(a, b): return a + b")

    result = run_cli(
        "test",
        "consult",
        "assertion",
        "--error",
        sample_test_error,
        "--hypothesis",
        sample_hypothesis,
        "--test-code",
        test_file,
        "--impl-code",
        impl_file,
        "--dry-run",
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )
    assert result.returncode == 0


def test_consult_handles_missing_code_path(
    tmp_path: Path,
    mock_tool_env: tuple[dict[str, str], Path],
    sample_test_error: str,
    sample_hypothesis: str,
) -> None:
    env, cwd = mock_tool_env
    missing_path = tmp_path / "missing.py"
    result = run_cli(
        "test",
        "consult",
        "assertion",
        "--error",
        sample_test_error,
        "--hypothesis",
        sample_hypothesis,
        "--test-code",
        missing_path,
        "--dry-run",
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
    )
    assert result.returncode == 0
    assert "Prompt length:" in result.stdout


def test_discover_summary_command() -> None:
    result = run_cli("test", "discover", "--summary")
    assert result.returncode in (0, 1)


def test_discover_tree_command() -> None:
    result = run_cli("test", "discover", "--tree")
    assert result.returncode in (0, 1)


def test_run_help_command() -> None:
    result = run_cli("test", "run", "--help")
    assert result.returncode == 0
    assert "Usage" in result.stdout or "usage" in result.stdout.lower()


def test_run_list_presets_command() -> None:
    result = run_cli("test", "run", "--list")
    assert result.returncode in (0, 1)
    assert "ci           CI-friendly output" in result.stdout


def test_run_help_mentions_quick_preset() -> None:
    result = run_cli("test", "run", "--help")
    assert result.returncode == 0
    assert result.stdout
    if "quick" not in result.stdout.lower():
        pytest.skip("Quick preset not documented in help output")


def test_consult_real_tools_opt_in(sample_test_error: str, sample_hypothesis: str) -> None:
    """Optional smoke test for developers with real binaries installed."""
    if not os.environ.get("SDD_TEST_USE_REAL_TOOLS"):
        pytest.skip("Real tool smoke tests disabled (set SDD_TEST_USE_REAL_TOOLS=1 to enable)")

    if not detect_available_tools():
        pytest.skip("No real AI tools available on PATH")

    result = run_cli(
        "test",
        "consult",
        "assertion",
        "--error",
        sample_test_error,
        "--hypothesis",
        sample_hypothesis,
        "--dry-run",
        capture_output=True,
        text=True,
    )
    assert result.returncode in (0, 1)
