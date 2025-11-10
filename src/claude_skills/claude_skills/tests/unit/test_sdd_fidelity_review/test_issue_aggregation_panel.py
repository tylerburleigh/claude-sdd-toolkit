from __future__ import annotations

from typing import Any, Dict, List

import pytest
from rich.console import Console

from claude_skills.sdd_fidelity_review.report import FidelityReport


pytestmark = pytest.mark.unit


def _render_issue_panel(report: FidelityReport, parsed_responses: List[Dict[str, Any]]) -> str:
    """Helper to render the issue aggregation panel and return captured text."""
    console = Console(record=True, width=120)
    report._print_issue_aggregation_panel(console, parsed_responses)  # type: ignore[attr-defined]
    return console.export_text(clear=False)


@pytest.fixture
def multi_model_results() -> Dict[str, Any]:
    return {
        "spec_id": "test-spec-001",
        "consensus": {
            "consensus_verdict": "partial",
            "agreement_rate": 0.67,
            "consensus_issues": [],
            "consensus_recommendations": [],
        },
        "categorized_issues": [],
        "parsed_responses": [
            {
                "verdict": "fail",
                "issues": [
                    "Missing error handling in auth module",
                    "Insufficient test coverage",
                    "API endpoints lack rate limiting",
                ],
                "recommendations": [],
            },
            {
                "verdict": "partial",
                "issues": [
                    "Missing error handling in auth module",
                    "Database queries not optimized",
                    "API endpoints lack rate limiting",
                ],
                "recommendations": [],
            },
            {
                "verdict": "fail",
                "issues": [
                    "Missing error handling in auth module",
                    "Insufficient test coverage",
                    "Security vulnerabilities in input validation",
                ],
                "recommendations": [],
            },
        ],
        "models_consulted": 3,
    }


@pytest.fixture
def single_model_results() -> Dict[str, Any]:
    return {
        "spec_id": "test-spec-002",
        "consensus": {"consensus_verdict": "pass", "agreement_rate": 1.0},
        "categorized_issues": [],
        "parsed_responses": [
            {"verdict": "pass", "issues": ["Minor documentation gap"], "recommendations": []}
        ],
        "models_consulted": 1,
    }


@pytest.fixture
def no_issues_results() -> Dict[str, Any]:
    return {
        "spec_id": "test-spec-003",
        "consensus": {"consensus_verdict": "pass", "agreement_rate": 1.0},
        "categorized_issues": [],
        "parsed_responses": [
            {"verdict": "pass", "issues": [], "recommendations": []},
            {"verdict": "pass", "issues": [], "recommendations": []},
        ],
        "models_consulted": 2,
    }


class TestIssueAggregationPanel:
    def test_multiple_models_render_common_concerns(self, multi_model_results: Dict[str, Any]) -> None:
        report = FidelityReport(multi_model_results)
        parsed = report._convert_to_dict(report.parsed_responses)  # type: ignore[attr-defined]

        rendered = _render_issue_panel(report, parsed)

        assert "COMMON CONCERNS" in rendered
        assert "Issues identified by multiple AI models" in rendered
        assert "Missing error handling in auth module" in rendered
        assert "Insufficient test coverage" in rendered
        assert "API endpoints lack rate limiting" in rendered

    def test_frequency_sorting_keeps_most_common_first(self, multi_model_results: Dict[str, Any]) -> None:
        report = FidelityReport(multi_model_results)
        parsed = report._convert_to_dict(report.parsed_responses)  # type: ignore[attr-defined]

        rendered = _render_issue_panel(report, parsed)

        pos_auth = rendered.find("Missing error handling in auth module")
        pos_test = rendered.find("Insufficient test coverage")
        pos_rate = rendered.find("API endpoints lack rate limiting")
        pos_security = rendered.find("Security vulnerabilities in input validation")

        assert pos_auth != -1
        assert pos_auth < pos_test < pos_security or pos_auth < pos_security
        assert pos_auth < pos_rate

    def test_handles_no_issues_gracefully(self, no_issues_results: Dict[str, Any]) -> None:
        report = FidelityReport(no_issues_results)
        parsed = report._convert_to_dict(report.parsed_responses)  # type: ignore[attr-defined]

        rendered = _render_issue_panel(report, parsed)

        assert rendered.strip() == ""

    def test_single_model_still_renders_panel(self, single_model_results: Dict[str, Any]) -> None:
        report = FidelityReport(single_model_results)
        parsed = report._convert_to_dict(report.parsed_responses)  # type: ignore[attr-defined]

        rendered = _render_issue_panel(report, parsed)

        assert "COMMON CONCERNS" in rendered
        assert "Minor documentation gap" in rendered

    def test_percentage_calculation_matches_counts(self, multi_model_results: Dict[str, Any]) -> None:
        report = FidelityReport(multi_model_results)
        parsed = report._convert_to_dict(report.parsed_responses)  # type: ignore[attr-defined]

        rendered = _render_issue_panel(report, parsed)

        assert "100%" in rendered
        assert "67%" in rendered

    def test_limits_to_top_ten_issues(self) -> None:
        results = {
            "spec_id": "test-spec-004",
            "consensus": {"consensus_verdict": "fail", "agreement_rate": 0.5},
            "categorized_issues": [],
            "parsed_responses": [
                {"verdict": "fail", "issues": [f"Issue {i}" for i in range(15)], "recommendations": []}
            ],
            "models_consulted": 1,
        }
        report = FidelityReport(results)
        parsed = report._convert_to_dict(report.parsed_responses)  # type: ignore[attr-defined]

        rendered = _render_issue_panel(report, parsed)

        for i in range(10):
            assert f"Issue {i}" in rendered
        assert "Issue 10" not in rendered
        assert "Issue 14" not in rendered

    def test_truncates_long_issue_descriptions(self) -> None:
        long_issue = "A" * 100
        results = {
            "spec_id": "test-spec-005",
            "consensus": {"consensus_verdict": "fail", "agreement_rate": 1.0},
            "categorized_issues": [],
            "parsed_responses": [
                {"verdict": "fail", "issues": [long_issue], "recommendations": []}
            ],
            "models_consulted": 1,
        }
        report = FidelityReport(results)
        parsed = report._convert_to_dict(report.parsed_responses)  # type: ignore[attr-defined]

        rendered = _render_issue_panel(report, parsed)

        assert "..." in rendered
        assert long_issue not in rendered

    def test_color_coding_reflected_in_counts(self, multi_model_results: Dict[str, Any]) -> None:
        report = FidelityReport(multi_model_results)
        parsed = report._convert_to_dict(report.parsed_responses)  # type: ignore[attr-defined]

        console = Console(record=True, width=120)
        report._print_issue_aggregation_panel(console, parsed)  # type: ignore[attr-defined]
        html = console.export_html(inline_styles=True)

        assert "Missing error handling in auth module" in html
        assert "100%" in html
        assert "67%" in html


class TestIntegrationWithPrintConsoleRich:
    def _install_rich_ui(self, monkeypatch: pytest.MonkeyPatch) -> Console:
        console = Console(record=True, width=120)

        class StubUi:
            def __init__(self, console: Console) -> None:
                self.console = console

        monkeypatch.setattr(
            "claude_skills.sdd_fidelity_review.report.create_ui",
            lambda: StubUi(console),
        )
        return console

    def test_panel_included_for_multiple_models(
        self,
        monkeypatch: pytest.MonkeyPatch,
        multi_model_results: Dict[str, Any],
    ) -> None:
        console = self._install_rich_ui(monkeypatch)

        report = FidelityReport(multi_model_results)
        report.print_console_rich(verbose=False)

        output = console.export_text(clear=False)
        assert "COMMON CONCERNS" in output
        assert "Missing error handling in auth module" in output

    def test_panel_omitted_for_single_model(
        self,
        monkeypatch: pytest.MonkeyPatch,
        single_model_results: Dict[str, Any],
    ) -> None:
        console = self._install_rich_ui(monkeypatch)

        report = FidelityReport(single_model_results)
        report.print_console_rich(verbose=False)

        output = console.export_text(clear=False)
        assert "COMMON CONCERNS" not in output
