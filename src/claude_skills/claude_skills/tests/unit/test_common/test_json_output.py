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


def test_output_json_pretty_print_default(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"status": "success", "count": 42}
    output_json(payload)
    captured = capsys.readouterr().out
    assert json.loads(captured) == payload
    assert "\n" in captured
    assert "  " in captured


def test_output_json_compact_mode(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"status": "success", "count": 42}
    output_json(payload, compact=True)
    captured = capsys.readouterr().out.strip()
    assert captured == '{"status":"success","count":42}'


def test_output_json_nested_structures(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {
        "task": {
            "id": "task-1-1",
            "metadata": {
                "estimated_hours": 2.5,
                "tags": ["test", "example"],
            },
        }
    }
    output_json(payload)
    captured = capsys.readouterr().out
    assert json.loads(captured) == payload
    assert "task" in captured
    assert "tags" in captured


def test_output_json_list_data(capsys: pytest.CaptureFixture[str]) -> None:
    payload = [{"id": 1}, {"id": 2}]
    output_json(payload)
    captured = capsys.readouterr().out
    assert json.loads(captured) == payload


def test_output_json_empty_structures(capsys: pytest.CaptureFixture[str]) -> None:
    output_json({})
    assert capsys.readouterr().out.strip() == "{}"
    output_json([])
    assert capsys.readouterr().out.strip() == "[]"


def test_output_json_unicode_characters(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"message": "Hello 世界", "emoji": "🎉"}
    output_json(payload)
    captured = capsys.readouterr().out
    assert json.loads(captured) == payload
    assert "世界" in captured
    assert "🎉" in captured


def test_output_json_special_values(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"null_value": None, "true_value": True, "false_value": False, "number": 123}
    output_json(payload)
    captured = capsys.readouterr().out
    assert json.loads(captured) == payload


def test_output_json_compact_vs_pretty_size(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"nested": {"key": "value", "items": [1, 2, 3]}}
    output_json(payload, compact=False)
    pretty_output = capsys.readouterr().out
    output_json(payload, compact=True)
    compact_output = capsys.readouterr().out
    assert len(compact_output) < len(pretty_output)
    assert json.loads(pretty_output) == json.loads(compact_output)


def test_format_json_output_variants() -> None:
    payload = {"status": "success", "count": 42}
    pretty = format_json_output(payload, compact=False)
    compact = format_json_output(payload, compact=True)
    assert json.loads(pretty) == payload
    assert compact == '{"status":"success","count":42}'
    sorted_json = format_json_output({"z": 1, "a": 2}, compact=True, sort_keys=True)
    assert sorted_json == '{"a":2,"z":1}'


def test_print_json_output_modes(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"key": "value"}
    print_json_output(payload, compact=False)
    assert json.loads(capsys.readouterr().out) == payload
    print_json_output(payload, compact=True)
    assert capsys.readouterr().out.strip() == '{"key":"value"}'


def test_output_json_handles_strings(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {
        "single": "It's a test",
        "double": 'He said "hello"',
        "multiline": "Line 1\nLine 2\nLine 3",
    }
    output_json(payload)
    captured = capsys.readouterr().out
    assert json.loads(captured) == payload
    assert "Line 1\\nLine 2\\nLine 3" in captured


def test_output_json_non_serialisable_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    buffer = StringIO()
    monkeypatch.setattr("sys.stdout", buffer)
    with pytest.raises(TypeError):
        output_json({"function": lambda x: x})


def test_output_json_deeply_nested(capsys: pytest.CaptureFixture[str]) -> None:
    data = {"level": 0}
    node = data
    for i in range(1, 10):
        node["nested"] = {"level": i}
        node = node["nested"]
    output_json(data)
    assert json.loads(capsys.readouterr().out) == data


def test_output_json_large_numbers(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {
        "large_int": 9223372036854775807,
        "large_float": 1.7976931348623157e308,
        "small_float": 2.2250738585072014e-308,
    }
    output_json(payload)
    assert json.loads(capsys.readouterr().out) == payload


def test_output_json_accepts_kwargs_and_positionals(capsys: pytest.CaptureFixture[str]) -> None:
    payload = {"value": "x"}
    output_json(payload)
    assert json.loads(capsys.readouterr().out) == payload
    output_json(payload, compact=True)
    assert json.loads(capsys.readouterr().out.strip()) == payload
    output_json(data=payload, compact=False)
    assert json.loads(capsys.readouterr().out) == payload


def test_output_json_prepare_task_context_fields(capsys: pytest.CaptureFixture[str]) -> None:
    """Test that prepare-task payload with enhanced context fields serializes correctly."""
    payload = {
        "task_id": "task-2-1",
        "task_data": {
            "title": "Extend context_utils for default payload",
            "status": "pending",
            "metadata": {
                "file_path": "src/context_utils.py",
                "task_category": "implementation"
            }
        },
        "dependencies": {
            "can_start": True,
            "blocked_by": [],
            "soft_depends": []
        },
        "context": {
            "previous_sibling": {
                "id": "task-2-0",
                "title": "Previous task",
                "status": "completed"
            },
            "parent_task": {
                "id": "phase-2",
                "title": "File Modifications",
                "position_label": "1 of 10 children"
            },
            "phase": {
                "title": "Implementation",
                "percentage": 35,
                "blockers": []
            },
            "sibling_files": [],
            "task_journal": {
                "entry_count": 0,
                "entries": []
            },
            "dependencies": {
                "blocking": [],
                "blocked_by_details": [],
                "soft_depends": []
            },
            "plan_validation": {
                "has_plan": False,
                "plan_items": [],
                "completed_steps": 0,
                "total_steps": 0
            }
        }
    }

    # Test pretty-print mode
    output_json(payload)
    pretty_output = capsys.readouterr().out
    assert json.loads(pretty_output) == payload
    assert "context" in pretty_output
    assert "dependencies" in pretty_output
    assert "plan_validation" in pretty_output

    # Test compact mode
    output_json(payload, compact=True)
    compact_output = capsys.readouterr().out.strip()
    # Verify it's valid JSON
    assert json.loads(compact_output) == payload
    # Verify it's actually compact (no extra whitespace)
    assert "\n" not in compact_output
    assert "  " not in compact_output


def test_output_json_enhanced_context_edge_cases(capsys: pytest.CaptureFixture[str]) -> None:
    """Test edge cases in enhanced context serialization."""
    # Test with populated dependencies.blocked_by_details
    payload = {
        "context": {
            "dependencies": {
                "blocking": [
                    {"id": "task-3-1", "title": "Blocker task", "status": "pending", "file_path": ""}
                ],
                "blocked_by_details": [
                    {"id": "task-1-5", "title": "Dependency", "status": "completed", "file_path": "src/foo.py"}
                ],
                "soft_depends": []
            }
        }
    }

    output_json(payload, compact=True)
    output = capsys.readouterr().out.strip()
    parsed = json.loads(output)

    # Verify nested arrays serialize correctly
    assert len(parsed["context"]["dependencies"]["blocking"]) == 1
    assert parsed["context"]["dependencies"]["blocking"][0]["id"] == "task-3-1"
    assert len(parsed["context"]["dependencies"]["blocked_by_details"]) == 1
    assert parsed["context"]["dependencies"]["blocked_by_details"][0]["file_path"] == "src/foo.py"
