"""Integration tests for the unified skills-dev CLI."""

from __future__ import annotations

from .cli_runner import run_cli


def run_skills_dev_cli(*args: object):
    """Run skills-dev CLI via shared runner."""
    return run_cli("skills-dev", *args)


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
