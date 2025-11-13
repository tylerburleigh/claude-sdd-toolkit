from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from claude_skills.common import PrettyPrinter
from claude_skills.sdd_plan_review.cli import cmd_review


pytestmark = pytest.mark.integration


@pytest.fixture
def plan_review_spec(tmp_path: Path) -> Path:
    specs_dir = tmp_path / "specs"
    (specs_dir / "active").mkdir(parents=True, exist_ok=True)

    spec_path = specs_dir / "active" / "integration-spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "spec_id": "integration-spec",
                "title": "Integration Plan Review Spec",
            }
        ),
        encoding="utf-8",
    )
    return specs_dir


def make_args(specs_dir: Path, output: str | None = None) -> argparse.Namespace:
    return argparse.Namespace(
        spec_id="integration-spec",
        type="full",
        tools=None,
        output=output,
        cache=False,
        dry_run=False,
        specs_dir=str(specs_dir),
        path=None,
    )


def fake_results() -> dict:
    return {
        "execution_time": 2.0,
        "parsed_responses": [{"tool": "mock", "summary": "ok"}],
        "failures": [],
        "consensus": {
            "success": True,
            "summary": "Integration path validated.",
            "recommendation": "merge",
        },
    }


def test_cli_creates_dual_artifacts(plan_review_spec: Path) -> None:
    printer = PrettyPrinter(use_color=False, verbose=True)
    args = make_args(plan_review_spec)
    json_payload = {"artifact": "integration-json"}

    with patch("claude_skills.sdd_plan_review.cli.get_enabled_and_available_tools", return_value=["mock"]), \
         patch("claude_skills.sdd_plan_review.cli.review_with_tools", return_value=fake_results()), \
         patch("claude_skills.sdd_plan_review.cli.generate_markdown_report", return_value="Integration markdown\n"), \
         patch("claude_skills.sdd_plan_review.cli.generate_json_report", return_value=json_payload):
        exit_code = cmd_review(args, printer)

    assert exit_code == 0

    reviews_dir = plan_review_spec / ".reviews"
    markdown_path = reviews_dir / "integration-spec-review-full.md"
    json_path = reviews_dir / "integration-spec-review-full.json"

    assert markdown_path.exists()
    assert markdown_path.read_text(encoding="utf-8") == "Integration markdown\n"

    assert json_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8")) == json_payload


def test_cli_keeps_explicit_output(plan_review_spec: Path, tmp_path: Path) -> None:
    printer = PrettyPrinter(use_color=False)
    custom_output = tmp_path / "custom-artifacts" / "report.json"
    args = make_args(plan_review_spec, output=str(custom_output))
    json_payload = {"artifact": "custom-json"}

    with patch("claude_skills.sdd_plan_review.cli.get_enabled_and_available_tools", return_value=["mock"]), \
         patch("claude_skills.sdd_plan_review.cli.review_with_tools", return_value=fake_results()), \
         patch("claude_skills.sdd_plan_review.cli.generate_markdown_report", return_value="Integration markdown\n"), \
         patch("claude_skills.sdd_plan_review.cli.generate_json_report", return_value=json_payload):
        exit_code = cmd_review(args, printer)

    assert exit_code == 0

    reviews_dir = plan_review_spec / ".reviews"
    markdown_path = reviews_dir / "integration-spec-review-full.md"
    json_path = reviews_dir / "integration-spec-review-full.json"

    assert markdown_path.exists()
    assert json_path.exists()

    assert custom_output.exists()
    assert json.loads(custom_output.read_text(encoding="utf-8")) == json_payload
