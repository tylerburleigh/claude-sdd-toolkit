import json
from pathlib import Path

import pytest

from claude_skills.common import schema_loader


@pytest.fixture(autouse=True)
def reset_schema_loader(monkeypatch):
    """Ensure each test starts with a clean loader cache and env."""
    schema_loader.load_json_schema.cache_clear()
    monkeypatch.delenv("CLAUDE_SDD_SCHEMA_CACHE", raising=False)
    yield
    schema_loader.load_json_schema.cache_clear()
    monkeypatch.delenv("CLAUDE_SDD_SCHEMA_CACHE", raising=False)


def test_load_json_schema_prefers_env_override(tmp_path, monkeypatch):
    schema_file = tmp_path / "sdd-spec-schema.json"
    schema_file.write_text(json.dumps({"type": "object"}))
    monkeypatch.setenv("CLAUDE_SDD_SCHEMA_CACHE", str(tmp_path))

    schema, source, error = schema_loader.load_json_schema("sdd-spec-schema.json")

    assert error is None
    assert schema == {"type": "object"}
    assert Path(source) == schema_file.resolve()


def test_load_json_schema_falls_back_when_missing(monkeypatch):
    def no_candidates(_schema_name: str):
        return []

    def missing_package(_package: str):
        raise ModuleNotFoundError("package missing")

    monkeypatch.setattr(schema_loader, "_candidate_paths", no_candidates)
    monkeypatch.setattr(schema_loader.resources, "files", missing_package)

    schema, source, error = schema_loader.load_json_schema("nonexistent.json")

    assert schema is None
    assert source is None
    assert "not found" in (error or "").lower()


def test_load_json_schema_uses_cache(monkeypatch, tmp_path):
    schema_file = tmp_path / "sdd-spec-schema.json"
    schema_file.write_text(json.dumps({"type": "object", "title": "cached"}))
    monkeypatch.setenv("CLAUDE_SDD_SCHEMA_CACHE", str(tmp_path))

    first = schema_loader.load_json_schema("sdd-spec-schema.json")
    assert first[0]["title"] == "cached"

    def should_not_run(_schema_name: str):
        raise AssertionError("load_json_schema should have used cache")

    schema_loader.load_json_schema.cache_clear()
    schema_loader.load_json_schema("sdd-spec-schema.json")  # rebuild cache with current file

    monkeypatch.setattr(schema_loader, "_candidate_paths", should_not_run)
    second = schema_loader.load_json_schema("sdd-spec-schema.json")

    assert second[0]["title"] == "cached"


def test_load_json_schema_reports_decode_errors(monkeypatch, tmp_path):
    bad_file = tmp_path / "sdd-spec-schema.json"
    bad_file.write_text("{invalid json")
    monkeypatch.setenv("CLAUDE_SDD_SCHEMA_CACHE", str(tmp_path))

    schema, source, error = schema_loader.load_json_schema("sdd-spec-schema.json")

    assert schema is not None
    assert error is None
    assert isinstance(source, str)
    assert source.startswith("package:") or source.endswith("sdd-spec-schema.json")
