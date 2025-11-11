from __future__ import annotations

import json
from pathlib import Path

import pytest

from claude_skills.common.setup_templates import (
    copy_template_to,
    get_template,
    load_json_template,
    load_yaml_template,
)


pytestmark = pytest.mark.unit


def test_get_template_returns_cached_path() -> None:
    first_path = get_template("ai_config.yaml")
    second_path = get_template("ai_config.yaml")

    assert isinstance(first_path, Path)
    assert first_path.exists()
    assert first_path.is_file()
    assert second_path is first_path


def test_get_template_missing_raises() -> None:
    with pytest.raises(FileNotFoundError):
        get_template("does-not-exist.yaml")


def test_load_json_template_parses_expected_fields() -> None:
    data = load_json_template("git_config.json")

    assert isinstance(data, dict)
    assert data["enabled"] is False
    assert data["auto_branch"] is True
    assert "commit_cadence" in data


def test_load_yaml_template_reads_models_section() -> None:
    data = load_yaml_template("ai_config.yaml")

    assert isinstance(data, dict)
    assert "models" in data
    assert data["models"]["gemini"]["priority"][0] == "gemini-2.5-pro"


def test_copy_template_to_supports_directory_and_file_paths(tmp_path: Path) -> None:
    copied_from_dir = copy_template_to("sdd_config.json", tmp_path)
    assert copied_from_dir.exists()

    copied_data = json.loads(copied_from_dir.read_text())
    assert copied_data["output"]["json"] is True

    destination_file = tmp_path / "custom_settings.json"
    copy_template_to("settings.local.json", destination_file)
    assert destination_file.exists()


def test_copy_template_to_respects_overwrite_flag(tmp_path: Path) -> None:
    destination = tmp_path / "settings.local.json"
    copy_template_to("settings.local.json", destination)

    with pytest.raises(FileExistsError):
        copy_template_to("settings.local.json", destination)

    overwritten = copy_template_to("settings.local.json", destination, overwrite=True)
    assert overwritten.exists()
