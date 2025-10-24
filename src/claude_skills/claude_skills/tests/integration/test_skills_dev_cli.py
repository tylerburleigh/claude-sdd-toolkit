"""Integration tests for the unified skills-dev CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SDD_ENTRY = REPO_ROOT / "claude_skills" / "cli" / "sdd" / "__init__.py"


def run_skills_dev_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run skills-dev CLI via sdd."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    cmd = [sys.executable, str(SDD_ENTRY), "skills-dev", *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)


def test_skills_dev_help_lists_key_subcommands() -> None:
    result = run_skills_dev_cli("--help")
    assert result.returncode == 0
    stdout = result.stdout.lower()
    for subcommand in [
        "gendocs",
        "start-helper",
        "setup-permissions",
        "migrate",
    ]:
        assert subcommand in stdout


def test_skills_dev_requires_subcommand() -> None:
    result = run_skills_dev_cli()
    assert result.returncode != 0
    combined = (result.stderr or result.stdout).lower()
    assert "usage:" in combined


def test_skills_dev_migrate_shows_guidance() -> None:
    result = run_skills_dev_cli("migrate")
    assert result.returncode == 0
    stdout = result.stdout.lower()
    assert "skills-dev" in stdout
    assert "legacy" in stdout
