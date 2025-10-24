"""Integration tests for the unified test CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SDD_ENTRY = REPO_ROOT / "claude_skills" / "cli" / "sdd" / "__init__.py"


def run_test_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run test CLI via sdd."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    cmd = [sys.executable, str(SDD_ENTRY), "test", *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)


def test_test_help_lists_key_subcommands() -> None:
    result = run_test_cli("--help")
    assert result.returncode == 0
    stdout = result.stdout.lower()
    for subcommand in [
        "run",
        "check-tools",
        "discover",
        "consult",
    ]:
        assert subcommand in stdout


def test_test_requires_subcommand() -> None:
    result = run_test_cli()
    assert result.returncode != 0
    combined = (result.stderr or result.stdout).lower()
    assert "usage:" in combined


def test_test_run_list_presets_success() -> None:
    result = run_test_cli("run", "--list")
    assert result.returncode == 0
    stdout = result.stdout.lower()
    assert "available" in stdout or "preset" in stdout
