"""Integration tests for the unified test CLI."""

from __future__ import annotations

from .cli_runner import run_cli


def run_test_cli(*args: object):
    """Run test CLI via shared runner."""
    return run_cli("test", *args)


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
