from __future__ import annotations

from typing import Any, Dict, List

import pytest
from rich.console import Console

from claude_skills.sdd_fidelity_review.report import FidelityReport


pytestmark = pytest.mark.unit


def _render_recommendations(report: FidelityReport, parsed_responses: List[Dict[str, Any]]) -> Console:
    """Render the recommendation consensus panel into a recording console."""
    console = Console(record=True, width=120)
    report._print_recommendation_consensus(console, parsed_responses)  # type: ignore[attr-defined]
    return console


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
                "issues": [],
                "recommendations": [
                    "Add comprehensive error handling",
                    "Increase test coverage to 80%",
                    "Implement rate limiting",
                ],
            },
            {
                "verdict": "partial",
                "issues": [],
                "recommendations": [
                    "Add comprehensive error handling",
                    "Optimize database queries",
                    "Implement rate limiting",
                ],
            },
            {
                "verdict": "fail",
                "issues": [],
                "recommendations": [
                    "Add comprehensive error handling",
                    "Increase test coverage to 80%",
                    "Improve input validation",
                ],
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
            {
                "verdict": "pass",
                "issues": [],
                "recommendations": ["Minor documentation improvements"],
            }
        ],
        "models_consulted": 1,
    }


@pytest.fixture
def no_recommendations() -> Dict[str, Any]:
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


class TestRecommendationConsensusPanel:
    def test_all_agree_indicator_present(self, multi_model_results: Dict[str, Any]) -> None:
        report = FidelityReport(multi_model_results)
        parsed = report._convert_to_dict(report.parsed_responses)  # type: ignore[attr-defined]

        console = _render_recommendations(report, parsed)
        output = console.export_text(clear=False)

        assert "RECOMMENDATIONS (with consensus)" in output
        assert "Add comprehensive error handling" in output
        assert "100%" in output

    def test_majority_indicator_present(self, multi_model_results: Dict[str, Any]) -> None:
        report = FidelityReport(multi_model_results)
        parsed = report._convert_to_dict(report.parsed_responses)  # type: ignore[attr-defined]

        output = _render_recommendations(report, parsed).export_text(clear=False)

        assert "Increase test coverage to 80%" in output
        assert "67%" in output

    def test_sorted_by_agreement_desc(self, multi_model_results: Dict[str, Any]) -> None:
        report = FidelityReport(multi_model_results)
        parsed = report._convert_to_dict(report.parsed_responses)  # type: ignore[attr-defined]

        output = _render_recommendations(report, parsed).export_text(clear=False)

        positions = {
            "all": output.find("Add comprehensive error handling"),
            "majority_one": output.find("Increase test coverage to 80%"),
            "majority_two": output.find("Implement rate limiting"),
            "minority_one": output.find("Optimize database queries"),
            "minority_two": output.find("Improve input validation"),
        }

        assert positions["all"] != -1
        assert positions["majority_one"] != -1
        assert positions["minority_one"] != -1
        assert positions["all"] < positions["majority_one"]
        assert positions["majority_one"] < positions["minority_one"]

    def test_handles_absence_of_recommendations(self, no_recommendations: Dict[str, Any]) -> None:
        report = FidelityReport(no_recommendations)
        parsed = report._convert_to_dict(report.parsed_responses)  # type: ignore[attr-defined]

        output = _render_recommendations(report, parsed).export_text(clear=False)

        assert "RECOMMENDATIONS (with consensus)" not in output

    def test_single_model_fallback(self, single_model_results: Dict[str, Any]) -> None:
        report = FidelityReport(single_model_results)
        parsed = report._convert_to_dict(report.parsed_responses)  # type: ignore[attr-defined]

        output = _render_recommendations(report, parsed).export_text(clear=False)

        assert "RECOMMENDATIONS" in output
        assert "Minor documentation improvements" in output

    def test_percentage_calculation(self, multi_model_results: Dict[str, Any]) -> None:
        report = FidelityReport(multi_model_results)
        parsed = report._convert_to_dict(report.parsed_responses)  # type: ignore[attr-defined]

        output = _render_recommendations(report, parsed).export_text(clear=False)

        assert "100%" in output
        assert "67%" in output
        assert "33%" in output

    def test_limits_to_top_ten_recommendations(self) -> None:
        results = {
            "spec_id": "test-spec-004",
            "consensus": {"consensus_verdict": "fail", "agreement_rate": 0.5},
            "categorized_issues": [],
            "parsed_responses": [
                {"verdict": "fail", "issues": [], "recommendations": [f"Recommendation {i}" for i in range(15)]}
            ],
            "models_consulted": 1,
        }
        report = FidelityReport(results)
        parsed = report._convert_to_dict(report.parsed_responses)  # type: ignore[attr-defined]

        output = _render_recommendations(report, parsed).export_text(clear=False)

        for i in range(10):
            assert f"Recommendation {i}" in output
        assert "Recommendation 10" not in output
        assert "Recommendation 14" not in output

    def test_color_coding_in_html(self, multi_model_results: Dict[str, Any]) -> None:
        report = FidelityReport(multi_model_results)
        parsed = report._convert_to_dict(report.parsed_responses)  # type: ignore[attr-defined]

        console = _render_recommendations(report, parsed)
        html = console.export_html(inline_styles=True)

        assert "Add comprehensive error handling" in html
        assert "100" in html
        assert "67" in html


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

    def test_panel_included_with_multiple_models(
        self,
        monkeypatch: pytest.MonkeyPatch,
        multi_model_results: Dict[str, Any],
    ) -> None:
        console = self._install_rich_ui(monkeypatch)

        report = FidelityReport(multi_model_results)
        report.print_console_rich(verbose=False)

        output = console.export_text(clear=False)
        assert "RECOMMENDATIONS (with consensus)" in output
        assert "Add comprehensive error handling" in output

    def test_panel_omitted_with_single_model(
        self,
        monkeypatch: pytest.MonkeyPatch,
        single_model_results: Dict[str, Any],
    ) -> None:
        console = self._install_rich_ui(monkeypatch)

        report = FidelityReport(single_model_results)
        report.print_console_rich(verbose=False)

        output = console.export_text(clear=False)
        assert "RECOMMENDATIONS (with consensus)" not in output
        assert "Minor documentation improvements" not in output
