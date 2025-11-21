import builtins
import json
import sys
from argparse import Namespace
from types import SimpleNamespace

import pytest

from claude_skills.llm_doc_gen.analysis import cli


class _StubPrinter:
    def __init__(self):
        self.messages = {"success": [], "error": [], "warning": []}

    def success(self, msg: str) -> None:
        self.messages["success"].append(msg)

    def error(self, msg: str) -> None:
        self.messages["error"].append(msg)

    def warning(self, msg: str) -> None:
        self.messages["warning"].append(msg)

    def info(self, msg: str) -> None:  # pragma: no cover - unused in tests
        self.messages.setdefault("info", []).append(msg)

    def detail(self, msg: str) -> None:  # pragma: no cover - unused in tests
        self.messages.setdefault("detail", []).append(msg)

    def action(self, msg: str) -> None:  # pragma: no cover - unused in tests
        self.messages.setdefault("action", []).append(msg)


def _doc_payload() -> dict:
    return {
        "metadata": {"title": "Example"},
        "statistics": {},
        "modules": [],
        "classes": [],
        "functions": [],
        "dependencies": {},
    }


def _make_args(json_path: str) -> Namespace:
    return Namespace(json_file=json_path, json=True, verbose=False, quiet=False)


def test_validate_uses_schema_loader(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys):
    doc_path = tmp_path / "codebase.json"
    doc_path.write_text(json.dumps(_doc_payload()))

    schema = {"type": "object"}
    monkeypatch.setattr(cli, "load_json_schema", lambda name: (schema, "package://schema", None))

    class FakeDraft7Validator:
        def __init__(self, _schema):
            self.schema = _schema

        def iter_errors(self, _doc):
            return []

    fake_jsonschema = SimpleNamespace(Draft7Validator=FakeDraft7Validator)
    monkeypatch.setitem(sys.modules, "jsonschema", fake_jsonschema)

    args = _make_args(str(doc_path))
    printer = _StubPrinter()

    result = cli.cmd_validate(args, printer)
    assert result == 0

    stdout = capsys.readouterr().out
    payload = json.loads(stdout)
    assert payload["status"] == "ok"
    assert payload["message"] == "JSON documentation is valid"
    assert payload["schema"]["source"] == "package://schema"
    assert payload["schema"]["warnings"] == []
    assert payload["schema"]["errors"] == []
    assert payload["schema"].get("validated") is True


def test_validate_handles_missing_schema(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys):
    doc_path = tmp_path / "codebase.json"
    doc_path.write_text(json.dumps(_doc_payload()))

    monkeypatch.setattr(cli, "load_json_schema", lambda name: (None, None, "schema not found"))

    args = _make_args(str(doc_path))
    printer = _StubPrinter()

    result = cli.cmd_validate(args, printer)
    assert result == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert "Basic validation passed" in payload["message"]
    warnings = payload["schema"]["warnings"]
    assert "schema not found" in warnings[0]
    assert any("unavailable" in warning for warning in warnings)
    assert payload["schema"]["errors"] == []


def test_validate_missing_keys_fails(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys):
    doc_path = tmp_path / "codebase.json"
    invalid_payload = _doc_payload()
    invalid_payload.pop("statistics")
    doc_path.write_text(json.dumps(invalid_payload))

    monkeypatch.setattr(cli, "load_json_schema", lambda name: (None, None, "schema missing"))

    args = _make_args(str(doc_path))
    printer = _StubPrinter()

    result = cli.cmd_validate(args, printer)
    assert result == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "error"
    assert "Missing required keys" in payload["message"]
    assert "statistics" in payload["message"]
    assert "schema missing" in payload["schema"]["warnings"][0]


def test_validate_missing_jsonschema_uses_basic_checks(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys):
    doc_path = tmp_path / "codebase.json"
    doc_path.write_text(json.dumps(_doc_payload()))

    monkeypatch.setattr(cli, "load_json_schema", lambda name: ({"type": "object"}, "package://schema", None))

    monkeypatch.delitem(sys.modules, "jsonschema", raising=False)
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "jsonschema":
            raise ImportError("jsonschema unavailable")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    args = _make_args(str(doc_path))
    printer = _StubPrinter()

    result = cli.cmd_validate(args, printer)
    assert result == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "ok"
    assert "install jsonschema" in payload["message"]
    assert payload["schema"]["source"] == "package://schema"
    assert any("jsonschema" in warning for warning in payload["schema"]["warnings"])


def test_parse_model_override_accepts_none() -> None:
    assert cli._parse_model_override(None) is None
    assert cli._parse_model_override([]) is None


def test_parse_model_override_single_value() -> None:
    assert cli._parse_model_override(["gemini-pro"]) == "gemini-pro"


def test_parse_model_override_per_tool_values() -> None:
    result = cli._parse_model_override(["gemini=gemini-pro", "cursor-agent:cursor-model"])
    assert result == {"gemini": "gemini-pro", "cursor-agent": "cursor-model"}


def test_parse_model_override_mixed_with_default() -> None:
    result = cli._parse_model_override(["gemini=model-a", "shared-model"])
    assert result == {"gemini": "model-a", "default": "shared-model"}
