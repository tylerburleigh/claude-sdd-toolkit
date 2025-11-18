"""Integration tests for the unified skills-dev CLI."""

from __future__ import annotations

import json
from pathlib import Path

from claude_skills.common.setup_templates import load_json_template

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


def test_setup_permissions_bootstraps_ai_config(tmp_path: Path) -> None:
    project_root = tmp_path / "proj"
    project_root.mkdir()

    result = run_skills_dev_cli("setup-permissions", "update", project_root, "--json")
    assert result.returncode == 0

    claude_dir = project_root / ".claude"
    settings_path = claude_dir / "settings.local.json"

    # Note: sdd_config.json creation was moved to 'sdd skills-dev start-helper ensure-sdd-config'
    # This test only checks that settings.local.json is created with correct permissions

    assert settings_path.exists()

    settings_data = json.loads(settings_path.read_text())
    permissions = settings_data.get("permissions", {})
    allow_list = permissions.get("allow", [])
    assert "Skill(sdd-toolkit:sdd-plan)" in allow_list
