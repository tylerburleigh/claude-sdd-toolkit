from __future__ import annotations

import argparse
from argparse import Namespace
from typing import Any, Dict, List, Optional

import pytest
from unittest.mock import MagicMock

from claude_skills.common.ai_tools import ToolResponse, ToolStatus
from claude_skills.sdd_fidelity_review.cli import _handle_fidelity_review, register_fidelity_review_command


pytestmark = pytest.mark.unit


def _make_args(**overrides: Any) -> Namespace:
    """Create a CLI namespace with sane defaults for unit tests."""
    defaults: Dict[str, Any] = dict(
        spec_id="demo-spec",
        task=None,
        phase=None,
        files=None,
        ai_tools=None,
        no_ai=True,  # most tests exercise the --no-ai branch to avoid extra stubbing
        model=None,
        timeout=120,
        no_stream_progress=False,
        no_tests=False,
        base_branch="main",
        consensus_threshold=2,
        incremental=False,
        output=None,
        format="text",
        verbose=False,
    )
    defaults.update(overrides)
    return Namespace(**defaults)


def _install_reviewer_stub(
    monkeypatch: pytest.MonkeyPatch,
    *,
    incremental_expected: Optional[bool] = None,
    cached_artifacts: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Replace FidelityReviewer with a lightweight stub for CLI tests.

    Args:
        monkeypatch: pytest monkeypatch fixture
        incremental_expected: Optional expectation for the incremental flag. When
            provided, the stub asserts the CLI passes the expected value.
        cached_artifacts: Optional list representing cached artefacts the reviewer
            should expose. Used to verify incremental runs surface cached context.

    Returns:
        Dictionary capturing invocation metadata for assertions.
    """
    captured: Dict[str, Any] = {}

    class StubFidelityReviewer:
        instances: List["StubFidelityReviewer"] = []

        def __init__(self, spec_id: str, spec_path=None, incremental: bool = False) -> None:
            if incremental_expected is not None:
                assert incremental is incremental_expected, "Unexpected incremental flag"
            captured["spec_id"] = spec_id
            captured["incremental"] = incremental
            self.spec_id = spec_id
            self.spec_path = spec_path
            self.incremental = incremental
            self.spec_data = {"title": "Demo Spec"}
            self.cached_artifacts = cached_artifacts[:] if cached_artifacts else []
            StubFidelityReviewer.instances.append(self)

        def generate_review_prompt(self, **kwargs: Any) -> str:  # type: ignore[override]
            captured["generate_kwargs"] = kwargs
            captured["cached_artifacts_seen"] = list(self.cached_artifacts)
            return "FAKE_PROMPT"

    StubFidelityReviewer.instances.clear()
    monkeypatch.setattr("claude_skills.sdd_fidelity_review.cli.FidelityReviewer", StubFidelityReviewer)
    monkeypatch.setattr("claude_skills.sdd_fidelity_review.cli.find_specs_directory", lambda: None)
    monkeypatch.setattr("claude_skills.sdd_fidelity_review.cli.ensure_fidelity_reviews_directory", lambda *_a, **_k: None)

    return captured


def test_incremental_flag_registered() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    register_fidelity_review_command(subparsers)
    args = parser.parse_args(["fidelity-review", "spec-123", "--incremental", "--no-ai"])

    assert hasattr(args, "incremental")
    assert args.incremental is True


def test_incremental_flag_defaults_false() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    register_fidelity_review_command(subparsers)
    args = parser.parse_args(["fidelity-review", "spec-123", "--no-ai"])

    assert hasattr(args, "incremental")
    assert args.incremental is False


def test_incremental_flag_passed_to_reviewer(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    captured = _install_reviewer_stub(monkeypatch, incremental_expected=True)

    exit_code = _handle_fidelity_review(_make_args(incremental=True))
    stdio = capsys.readouterr()

    assert exit_code == 0
    assert "FAKE_PROMPT" in stdio.out  # --no-ai prints the generated prompt
    assert captured["incremental"] is True


def test_incremental_false_passed_to_reviewer(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    captured = _install_reviewer_stub(monkeypatch, incremental_expected=False)

    exit_code = _handle_fidelity_review(_make_args(incremental=False))
    stdio = capsys.readouterr()

    assert exit_code == 0
    assert "FAKE_PROMPT" in stdio.out
    assert captured["incremental"] is False


def test_incremental_flag_help_text_mentions_incremental() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register_fidelity_review_command(subparsers)

    fidelity_parser = None
    for action in parser._subparsers._actions:
        if hasattr(action, "choices") and action.choices and "fidelity-review" in action.choices:
            fidelity_parser = action.choices["fidelity-review"]
            break

    assert fidelity_parser is not None, "fidelity-review subcommand not found"

    help_text = fidelity_parser.format_help()
    assert "--incremental" in help_text
    assert "incremental mode" in help_text.lower()


def test_incremental_flag_backward_compatible() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register_fidelity_review_command(subparsers)

    args = parser.parse_args(["fidelity-review", "spec-789", "--phase", "phase-1", "--no-ai"])

    assert args.spec_id == "spec-789"
    assert args.phase == "phase-1"
    assert args.incremental is False


def test_incremental_hasattr_check_handles_missing_attribute(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _install_reviewer_stub(monkeypatch, incremental_expected=False)
    args = _make_args()
    delattr(args, "incremental")

    exit_code = _handle_fidelity_review(args)

    assert exit_code == 0
    assert captured["incremental"] is False


def test_incremental_cached_artifacts_exposed_to_prompt(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    cached_items = ["diff-a", "diff-b"]
    captured = _install_reviewer_stub(monkeypatch, incremental_expected=True, cached_artifacts=cached_items)

    exit_code = _handle_fidelity_review(_make_args(incremental=True))
    stdio = capsys.readouterr()

    assert exit_code == 0
    assert "FAKE_PROMPT" in stdio.out
    assert captured["cached_artifacts_seen"] == cached_items


def test_incremental_flag_passed_to_reviewer_when_ai_runs(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _install_reviewer_stub(monkeypatch, incremental_expected=True)

    def fake_consult(prompt: str, **_kwargs: Any) -> List[ToolResponse]:
        captured["prompt_sent"] = prompt
        return [
            ToolResponse(tool="mock-tool", status=ToolStatus.SUCCESS, output="Looks good")
        ]

    def fake_parse(responses: List[ToolResponse]) -> List[ToolResponse]:
        return responses

    def fake_consensus(_responses: List[ToolResponse], *, min_agreement: int) -> MagicMock:
        mock_consensus = MagicMock()
        mock_consensus.consensus_issues = []
        mock_consensus.consensus_recommendations = []
        mock_consensus.consensus_verdict = MagicMock(value="pass")
        mock_consensus.agreement_rate = 1.0
        return mock_consensus

    def fake_categorize(_issues: Any) -> List[Any]:
        return []

    monkeypatch.setattr("claude_skills.sdd_fidelity_review.cli.consult_multiple_ai_on_fidelity", fake_consult)
    monkeypatch.setattr("claude_skills.sdd_fidelity_review.cli.parse_multiple_responses", fake_parse)
    monkeypatch.setattr("claude_skills.sdd_fidelity_review.cli.detect_consensus", fake_consensus)
    monkeypatch.setattr("claude_skills.sdd_fidelity_review.cli.categorize_issues", fake_categorize)
    monkeypatch.setattr("claude_skills.sdd_fidelity_review.cli.output_json", lambda *_a, **_k: None)
    monkeypatch.setattr("claude_skills.sdd_fidelity_review.cli.FidelityReport", MagicMock())

    args = _make_args(incremental=True, no_ai=False, format="json", consensus_threshold=3)

    exit_code = _handle_fidelity_review(args)

    assert exit_code == 0
    assert captured["incremental"] is True
    assert captured["prompt_sent"] == "FAKE_PROMPT"
