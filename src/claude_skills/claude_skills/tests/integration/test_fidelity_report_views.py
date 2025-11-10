from __future__ import annotations

from io import StringIO

import pytest
from rich.console import Console

from claude_skills.sdd_fidelity_review.report import FidelityReport


pytestmark = pytest.mark.integration


def _make_report(parsed_responses=None, consensus=None, categorized_issues=None) -> FidelityReport:
    """Helper to build a report with sensible defaults for rendering tests."""
    report_data = {
        "spec_id": "integration-spec",
        "parsed_responses": parsed_responses or [
            {
                "model": "gemini",
                "verdict": "pass",
                "issues": [],
                "recommendations": ["Ship it!"],
            },
            {
                "model": "codex",
                "verdict": "partial",
                "issues": [{"severity": "medium", "description": "Tighten validation"}],
                "recommendations": ["Add edge-case tests"],
            },
        ],
        "consensus": consensus
        or {
            "consensus_verdict": "partial",
            "agreement_rate": 0.75,
            "consensus_issues": ["Validation coverage could improve"],
            "consensus_recommendations": ["Expand test matrix"],
        },
        "categorized_issues": categorized_issues
        or [
            {
                "issue": "Missing rate limiting",
                "severity": "high",
                "category": "reliability",
                "agreed_by": ["gemini", "codex"],
                "agreement_count": 2,
            },
            {
                "issue": "Document error handling policy",
                "severity": "medium",
                "category": "quality",
                "agreed_by": ["codex"],
                "agreement_count": 1,
            },
        ],
    }
    return FidelityReport(report_data)


def test_model_comparison_table_renders_expected_sections() -> None:
    """Ensure the Rich comparison table renders without raising and includes key headers."""
    report = _make_report()
    console = Console(file=StringIO(), width=100, legacy_windows=False)

    report._print_model_comparison_table(console)

    output = console.file.getvalue()
    assert "MODEL RESPONSE COMPARISON" in output
    assert "Model 1" in output
    assert "Model 2" in output
    assert "Verdict" in output


def test_consensus_matrix_handles_categorised_issues() -> None:
    """Consensus matrix should reflect issue rows and agreement columns."""
    report = _make_report()
    console = Console(file=StringIO(), width=120, legacy_windows=False)

    report._print_consensus_matrix(console, report.categorized_issues)

    output = console.file.getvalue()
    assert "CONSENSUS MATRIX" in output
    assert "Issue" in output
    assert "Agreement" in output
    # Ensure at least one issue description surfaced
    assert "Missing rate limiting" in output or "Document error handling policy" in output


def test_generate_json_contains_metadata_and_responses() -> None:
    """JSON output should include metadata, consensus, and individual responses."""
    report = _make_report()
    payload = report.generate_json()

    assert payload["spec_id"] == "integration-spec"
    assert "metadata" in payload
    assert "generated_at" in payload["metadata"]
    assert payload["metadata"]["spec_id"] == "integration-spec"

    assert isinstance(payload["individual_responses"], list)
    assert len(payload["individual_responses"]) == 2

    assert payload["consensus"]["consensus_verdict"] == "partial"
    assert "categorized_issues" in payload
