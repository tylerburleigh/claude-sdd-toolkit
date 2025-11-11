from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest

from claude_skills.sdd_render import cli


class StubPrinter:
    def __init__(self) -> None:
        self.messages: List[Tuple[str, str]] = []

    def action(self, msg: str) -> None:
        self.messages.append(("action", msg))

    def success(self, msg: str) -> None:
        self.messages.append(("success", msg))

    def detail(self, msg: str) -> None:
        self.messages.append(("detail", msg))

    def warning(self, msg: str) -> None:
        self.messages.append(("warning", msg))

    def error(self, msg: str) -> None:
        self.messages.append(("error", msg))


def _write_spec(tmp_path: Path) -> Path:
    spec = {
        "spec_id": "demo-plan",
        "metadata": {"title": "Demo Spec"},
        "hierarchy": {
            "spec-root": {
                "type": "root",
                "children": [],
                "total_tasks": 0,
                "completed_tasks": 0,
            }
        },
    }
    spec_path = tmp_path / "demo-plan.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    return spec_path


def test_parse_model_override_helper() -> None:
    assert cli._parse_model_override(None) is None
    assert cli._parse_model_override([]) is None
    assert cli._parse_model_override(["global-model"]) == "global-model"
    assert cli._parse_model_override(["gemini=demo", "cursor-agent:cursor"]) == {
        "gemini": "demo",
        "cursor-agent": "cursor",
    }
    assert cli._parse_model_override(["gemini=demo", "fallback"]) == {
        "gemini": "demo",
        "default": "fallback",
    }


def test_cmd_render_passes_model_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    spec_path = _write_spec(tmp_path)
    output_path = tmp_path / "render.md"

    captured: Dict[str, Any] = {}

    class FakeRenderer:
        def __init__(self, spec_data: Dict[str, Any], *, model_override: Any = None) -> None:
            captured["model_override"] = model_override

        def render(self, **kwargs: Any) -> str:
            return "# Rendered"

        def get_pipeline_status(self) -> Dict[str, bool]:
            return {}

    monkeypatch.setattr(cli, "AIEnhancedRenderer", FakeRenderer)

    printer = StubPrinter()
    args = Namespace(
        spec_id=str(spec_path),
        output=str(output_path),
        path=None,
        format="markdown",
        mode=None,
        enhancement_level=None,
        verbose=False,
        debug=False,
        model=["gemini=demo", "fallback"],
    )

    exit_code = cli.cmd_render(args, printer)

    assert exit_code == 0
    assert output_path.exists()
    assert captured["model_override"] == {"gemini": "demo", "default": "fallback"}
