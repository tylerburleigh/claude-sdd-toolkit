from __future__ import annotations

import json
from io import StringIO

import pytest

from claude_skills.common.json_output import (
    format_json_output,
    output_json,
    print_json_output,
)


pytestmark = pytest.mark.unit


def test_output_json_pretty_prints_by_default(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"status": "ok", "count": 2}

    output_json(payload)

    captured = capsys.readouterr().out
    assert json.loads(captured) == payload
    assert "\n" in captured
    assert "  " in captured  # 2-space indent


def test_output_json_compact_mode_omits_whitespace(capsys: pytest.CaptureFixture[str]) -> None:
    output_json({"a": 1, "b": 2}, compact=True)
    captured = capsys.readouterr().out.strip()
    assert captured == '{"a":1,"b":2}'


def test_format_json_output_supports_sort_keys() -> None:
    result = format_json_output({"z": 1, "a": 2}, compact=True, sort_keys=True)
    assert result == '{"a":2,"z":1}'


def test_print_json_output_accepts_compact_flag(capsys: pytest.CaptureFixture[str]) -> None:
    print_json_output({"value": "x"}, compact=True)
    captured = capsys.readouterr().out.strip()
    assert captured == '{"value":"x"}'


def test_output_json_raises_for_unserialisable_data(monkeypatch: pytest.MonkeyPatch) -> None:
    # Preserve stdout to avoid polluting the test log
    buffer = StringIO()
    monkeypatch.setattr("sys.stdout", buffer)

    with pytest.raises(TypeError):
        output_json({"func": lambda x: x})


def test_output_json_handles_nested_structures(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {
        "task": {
            "id": "task-1",
            "metadata": {
                "estimated_hours": 2.5,
                "tags": ["auth", "backend"],
            },
        }
    }
    output_json(payload)
    captured = capsys.readouterr().out
    assert json.loads(captured) == payload
    assert "task" in captured
    assert "tags" in captured


def test_output_json_handles_lists(capsys: pytest.CaptureFixture[str]) -> None:
    payload = [{"id": 1}, {"id": 2}]
    output_json(payload)
    captured = capsys.readouterr().out
    assert json.loads(captured) == payload


def test_output_json_handles_empty_structures(capsys: pytest.CaptureFixture[str]) -> None:
    output_json({})
    captured = capsys.readouterr().out.strip()
    assert captured == "{}"

    output_json([])
    captured = capsys.readouterr().out.strip()
    assert captured == "[]"


def test_output_json_preserves_unicode(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"message": "Hello 世界", "emoji": "🎉"}
    output_json(payload)
    captured = capsys.readouterr().out
    assert json.loads(captured) == payload
    assert "世界" in captured
    assert "🎉" in captured


def test_output_json_special_values(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"null": None, "true": True, "false": False, "number": 42}
    output_json(payload)
    captured = capsys.readouterr().out
    parsed = json.loads(captured)
    assert parsed == payload


def test_output_json_compact_vs_pretty_size_difference(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {
        "level1": {
            "level2": {
                "level3": {
                    "key": "value",
                    "items": [1, 2, 3],
                }
            }
        }
    }
    output_json(payload, compact=False)
    pretty = capsys.readouterr().out

    output_json(payload, compact=True)
    compact = capsys.readouterr().out

    assert len(compact) < len(pretty)
    assert json.loads(compact) == json.loads(pretty)


def test_format_json_output_pretty_matches_compact_when_reparsed() -> None:
    payload = {"status": "ok", "count": 2}
    pretty = format_json_output(payload, compact=False)
    compact = format_json_output(payload, compact=True)
    assert json.loads(pretty) == payload
    assert json.loads(compact) == payload


def test_print_json_output_pretty(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"value": "x"}
    print_json_output(payload, compact=False)
    captured = capsys.readouterr().out
    assert json.loads(captured) == payload
    assert "\n" in captured


def test_output_json_large_numbers(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {
        "large_int": 2**63 - 1,
        "large_float": 1.79e308,
        "small_float": 5e-324,
    }
    output_json(payload)
    captured = capsys.readouterr().out
    assert json.loads(captured) == payload


def test_output_json_strings_with_quotes_and_newlines(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {
        "single": "It's a test",
        "double": 'He said "hello"',
        "multiline": "Line 1\nLine 2",
    }
    output_json(payload)
    captured = capsys.readouterr().out
    assert json.loads(captured) == payload


def test_output_json_accepts_positional_and_keyword_arguments(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"value": "x"}
    output_json(payload)
    assert json.loads(capsys.readouterr().out) == payload

    output_json(payload, compact=True)
    assert json.loads(capsys.readouterr().out.strip()) == payload

    output_json(data=payload, compact=False)
    assert json.loads(capsys.readouterr().out) == payload
