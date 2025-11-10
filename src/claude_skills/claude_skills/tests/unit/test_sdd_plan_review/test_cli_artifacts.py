from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Tuple
from unittest.mock import patch

import pytest

from claude_skills.sdd_plan_review.cli import cmd_review


pytestmark = pytest.mark.unit


class DummyPrinter:
    """Minimal printer implementation for exercising CLI flows in tests."""

    def __init__(self) -> None:
        self.messages: List[Tuple[str, str]] = []

    def info(self, msg: str) -> None:
        self.messages.append(("info", msg))

    def success(self, msg: str) -> None:
        self.messages.append(("success", msg))

    def warning(self, msg: str) -> None:
        self.messages.append(("warning", msg))

    def error(self, msg: str) -> None:
        self.messages.append(("error", msg))

    def header(self, msg: str) -> None:
        self.messages.append(("header", msg))

    def detail(self, msg: str, indent: int = 1) -> None:
        self.messages.append(("detail", f"{'  ' * indent}{msg}"))


@pytest.fixture
def spec_setup(tmp_path: Path) -> Path:
    specs_dir = tmp_path / "specs"
    active_dir = specs_dir / "active"
    active_dir.mkdir(parents=True, exist_ok=True)

    spec_content = {
        "spec_id": "demo-plan",
        "title": "Demo Plan Review Spec",
    }
    (active_dir / "demo-plan.json").write_text(json.dumps(spec_content), encoding="utf-8")
    return specs_dir


def make_args(specs_dir: Path, output: str | None = None) -> argparse.Namespace:
    return argparse.Namespace(
        spec_id="demo-plan",
        type="quick",
        tools=None,
        output=output,
        cache=False,
        dry_run=False,
        specs_dir=str(specs_dir),
        path=None,
    )


def mock_review_results() -> dict:
    return {
        "execution_time": 1.2,
        "parsed_responses": [{"tool": "mock-tool", "summary": "ok"}],
        "failures": [],
        "consensus": {
            "success": True,
            "summary": "All systems go.",
            "recommendation": "proceed",
        },
    }


def test_cmd_review_persists_markdown_and_json(tmp_path: Path, spec_setup: Path) -> None:
    printer = DummyPrinter()
    args = make_args(spec_setup)
    expected_json = {
        "artifact": "plan-review",
        "spec_id": "demo-plan",
        "type": "quick",
    }

    with patch("claude_skills.sdd_plan_review.cli.detect_available_tools", return_value=["mock-tool"]), \
         patch("claude_skills.sdd_plan_review.cli.review_with_tools", return_value=mock_review_results()), \
         patch("claude_skills.sdd_plan_review.cli.generate_markdown_report", return_value="# Mock Report\n"), \
         patch("claude_skills.sdd_plan_review.cli.generate_json_report", return_value=expected_json):
        exit_code = cmd_review(args, printer)

    assert exit_code == 0

    reviews_dir = spec_setup / ".reviews"
    markdown_path = reviews_dir / "demo-plan-review-quick.md"
    json_path = reviews_dir / "demo-plan-review-quick.json"

    assert markdown_path.exists()
    assert markdown_path.read_text(encoding="utf-8") == "# Mock Report\n"

    assert json_path.exists()
    persisted_json = json.loads(json_path.read_text(encoding="utf-8"))
    assert persisted_json == expected_json


def test_cmd_review_respects_output_flag_while_persisting_defaults(tmp_path: Path, spec_setup: Path) -> None:
    printer = DummyPrinter()
    user_output = tmp_path / "artifacts" / "custom.md"
    args = make_args(spec_setup, output=str(user_output))

    expected_json = {"artifact": "plan-review-json"}

    with patch("claude_skills.sdd_plan_review.cli.detect_available_tools", return_value=["mock-tool"]), \
         patch("claude_skills.sdd_plan_review.cli.review_with_tools", return_value=mock_review_results()), \
         patch("claude_skills.sdd_plan_review.cli.generate_markdown_report", return_value="*Mock*\n"), \
         patch("claude_skills.sdd_plan_review.cli.generate_json_report", return_value=expected_json):
        exit_code = cmd_review(args, printer)

    assert exit_code == 0

    reviews_dir = spec_setup / ".reviews"
    markdown_path = reviews_dir / "demo-plan-review-quick.md"
    json_path = reviews_dir / "demo-plan-review-quick.json"

    assert markdown_path.exists()
    assert markdown_path.read_text(encoding="utf-8") == "*Mock*\n"

    assert json_path.exists()
    persisted_json = json.loads(json_path.read_text(encoding="utf-8"))
    assert persisted_json == expected_json

    assert user_output.exists()
    assert user_output.read_text(encoding="utf-8") == "*Mock*\n"
