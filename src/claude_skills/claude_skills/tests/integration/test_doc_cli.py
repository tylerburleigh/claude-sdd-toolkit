"""Integration tests for the unified doc CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SDD_ENTRY = REPO_ROOT / "claude_skills" / "cli" / "sdd" / "__init__.py"


def run_doc_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run doc CLI via sdd."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    cmd = [sys.executable, str(SDD_ENTRY), "doc", *args]
    return subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)


def test_doc_help_lists_key_subcommands() -> None:
    result = run_doc_cli("--help")
    assert result.returncode == 0
    stdout = result.stdout.lower()
    for subcommand in [
        "generate",
        "validate-json",
        "analyze",
        "find-class",
        "find-function",
        "list-modules",
    ]:
        assert subcommand in stdout


def test_doc_requires_subcommand() -> None:
    result = run_doc_cli()
    assert result.returncode != 0
    combined = (result.stderr or result.stdout).lower()
    assert "usage:" in combined
