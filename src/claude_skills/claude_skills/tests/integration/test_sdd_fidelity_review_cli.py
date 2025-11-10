from __future__ import annotations

import json
from argparse import Namespace
from types import SimpleNamespace
from typing import Any, Dict, List

import pytest

from claude_skills.common.ai_tools import ToolResponse, ToolStatus
from claude_skills.sdd_fidelity_review.cli import (
    _handle_fidelity_review,
    _build_output_basename,
)


pytestmark = pytest.mark.integration


def _make_args(**overrides: Any) -> Namespace:
    """Create a CLI namespace with sensible defaults."""
    defaults = dict(
        spec_id="simple-spec-2025-01-01-001",
        task=None,
        phase=None,
        files=None,
        ai_tools=None,
        no_ai=False,
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


@pytest.fixture
def stubbed_reviewer(
    monkeypatch: pytest.MonkeyPatch,
) -> Dict[str, Any]:
    """
    Replace FidelityReviewer with a lightweight stub so the CLI can run without
    touching the real spec loader or git integration.
    """

    captured: Dict[str, Any] = {}

    class StubFidelityReviewer:
        instances: List[Dict[str, Any]] = []

        def __init__(self, spec_id: str, spec_path=None, incremental: bool = False) -> None:
            self.spec_id = spec_id
            self.spec_path = spec_path
            self.incremental = incremental
            self.spec_data = {"spec_id": spec_id, "hierarchy": {}}
            StubFidelityReviewer.instances.append(
                {"spec_id": spec_id, "spec_path": spec_path, "incremental": incremental}
            )

        def generate_review_prompt(self, **kwargs: Any) -> str:  # type: ignore[override]
            captured["generate_kwargs"] = kwargs
            return "FAKE_FIDELITY_PROMPT"

    StubFidelityReviewer.instances.clear()
    monkeypatch.setattr(
        "claude_skills.sdd_fidelity_review.cli.FidelityReviewer",
        StubFidelityReviewer,
    )
    monkeypatch.setattr(
        "claude_skills.sdd_fidelity_review.cli.find_specs_directory",
        lambda: None,
    )

    return {"captured": captured, "cls": StubFidelityReviewer}


def test_fidelity_review_no_ai_outputs_prompt(
    stubbed_reviewer: Dict[str, Any],
    sample_json_spec_simple,
    capfd,
) -> None:
    """`--no-ai` should surface the generated prompt without consulting tools."""
    args = _make_args(no_ai=True)
    exit_code = _handle_fidelity_review(args)
    captured = capfd.readouterr()

    assert exit_code == 0
    assert "FAKE_FIDELITY_PROMPT" in captured.out


def _install_cli_stubs(monkeypatch: pytest.MonkeyPatch) -> Dict[str, Any]:
    """Install helper stubs for the CLI execution path that consults AI tools."""
    captured: Dict[str, Any] = {}

    def fake_consult(
        prompt: str,
        tools=None,
        model=None,
        timeout=None,
        progress_emitter=None,
    ):
        captured["prompt"] = prompt
        captured["progress_emitter"] = progress_emitter
        return [
            ToolResponse(
                tool="mock-tool",
                status=ToolStatus.SUCCESS,
                output="Mock review output",
            )
        ]

    def fake_parse(responses):
        captured["parsed_responses"] = list(responses)
        return []

    class FakeConsensus(SimpleNamespace):
        def __init__(self):
            super().__init__(
                consensus_verdict="pass",
                agreement_rate=1.0,
                consensus_issues=[],
                consensus_recommendations=[],
            )

        def to_dict(self) -> Dict[str, Any]:
            return {
                "consensus_verdict": "pass",
                "agreement_rate": 1.0,
                "consensus_issues": [],
                "consensus_recommendations": [],
            }

    def fake_detect(parsed, min_agreement):
        captured["min_agreement"] = min_agreement
        return FakeConsensus()

    def fake_categorize(issues):
        captured["categorized"] = list(issues)
        return []

    def fake_print_console_rich(self, verbose=False, ui=None):
        captured["output_called"] = True

    monkeypatch.setattr(
        "claude_skills.sdd_fidelity_review.cli.consult_multiple_ai_on_fidelity",
        fake_consult,
    )
    monkeypatch.setattr(
        "claude_skills.sdd_fidelity_review.cli.parse_multiple_responses",
        fake_parse,
    )
    monkeypatch.setattr(
        "claude_skills.sdd_fidelity_review.cli.detect_consensus",
        fake_detect,
    )
    monkeypatch.setattr(
        "claude_skills.sdd_fidelity_review.cli.categorize_issues",
        fake_categorize,
    )
    monkeypatch.setattr(
        "claude_skills.sdd_fidelity_review.cli.FidelityReport.print_console_rich",
        fake_print_console_rich,
    )

    return captured


def test_fidelity_review_streams_progress_by_default(
    stubbed_reviewer: Dict[str, Any],
    sample_json_spec_simple,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without `--no-stream-progress`, the CLI should provision a progress emitter."""
    captured = _install_cli_stubs(monkeypatch)

    args = _make_args()
    exit_code = _handle_fidelity_review(args)

    assert exit_code == 0
    assert captured.get("output_called") is True
    assert captured.get("progress_emitter") is not None


def test_fidelity_review_can_disable_streaming(
    stubbed_reviewer: Dict[str, Any],
    sample_json_spec_simple,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`--no-stream-progress` should pass a null emitter to the consultation helper."""
    captured = _install_cli_stubs(monkeypatch)

    args = _make_args(no_stream_progress=True)
    exit_code = _handle_fidelity_review(args)

    assert exit_code == 0
    assert captured.get("output_called") is True
    assert captured.get("progress_emitter") is None


def test_default_run_persists_markdown_and_json(
    stubbed_reviewer: Dict[str, Any],
    sample_json_spec_simple,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """By default the CLI should auto-save both markdown and JSON artifacts."""
    captured = _install_cli_stubs(monkeypatch)

    specs_dir = sample_json_spec_simple.parent.parent

    monkeypatch.setattr(
        "claude_skills.sdd_fidelity_review.cli.find_specs_directory",
        lambda: specs_dir,
    )

    args = _make_args()
    exit_code = _handle_fidelity_review(args)

    assert exit_code == 0

    base_name = _build_output_basename(args.spec_id, args.task, args.phase, args.files)
    fidelity_dir = specs_dir / ".fidelity-reviews"
    markdown_path = fidelity_dir / f"{base_name}.md"
    json_path = fidelity_dir / f"{base_name}.json"

    assert markdown_path.exists(), "Expected markdown artifact to be created"
    assert json_path.exists(), "Expected JSON artifact to be created"
    assert markdown_path.read_text().strip(), "Markdown artifact should not be empty"

    saved_json = json.loads(json_path.read_text())
    assert saved_json.get("spec_id") == args.spec_id

    assert captured.get("output_called") is True


def test_fidelity_review_respects_incremental_flag(
    stubbed_reviewer: Dict[str, Any],
    sample_json_spec_simple,
) -> None:
    """Ensure the CLI forwards the incremental toggle down to the reviewer."""
    reviewer_cls = stubbed_reviewer["cls"]

    args = _make_args(no_ai=True, incremental=True)
    exit_code = _handle_fidelity_review(args)

    assert exit_code == 0
    assert reviewer_cls.instances, "Stub reviewer was never instantiated"
    assert reviewer_cls.instances[-1]["incremental"] is True
