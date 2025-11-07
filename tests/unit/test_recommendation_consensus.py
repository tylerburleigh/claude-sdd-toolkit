"""
Tests for recommendation consensus indicators in fidelity review reports.

Tests the _print_recommendation_consensus method that displays
recommendations with agreement level indicators.
"""

import pytest
from io import StringIO
from rich.console import Console
from claude_skills.sdd_fidelity_review.report import FidelityReport


@pytest.fixture
def sample_with_recommendations():
    """Create sample review results with recommendations from multiple models."""
    return {
        "spec_id": "test-spec-001",
        "consensus": {
            "consensus_verdict": "partial",
            "agreement_rate": 0.67,
            "consensus_issues": [],
            "consensus_recommendations": []
        },
        "categorized_issues": [],
        "parsed_responses": [
            {
                "verdict": "fail",
                "issues": [],
                "recommendations": [
                    "Add comprehensive error handling",
                    "Increase test coverage to 80%",
                    "Implement rate limiting"
                ]
            },
            {
                "verdict": "partial",
                "issues": [],
                "recommendations": [
                    "Add comprehensive error handling",
                    "Optimize database queries",
                    "Implement rate limiting"
                ]
            },
            {
                "verdict": "fail",
                "issues": [],
                "recommendations": [
                    "Add comprehensive error handling",
                    "Increase test coverage to 80%",
                    "Improve input validation"
                ]
            }
        ],
        "models_consulted": 3
    }


@pytest.fixture
def single_model_recommendations():
    """Create review results with only one model's recommendations."""
    return {
        "spec_id": "test-spec-002",
        "consensus": {"consensus_verdict": "pass", "agreement_rate": 1.0},
        "categorized_issues": [],
        "parsed_responses": [
            {
                "verdict": "pass",
                "issues": [],
                "recommendations": ["Minor documentation improvements"]
            }
        ],
        "models_consulted": 1
    }


@pytest.fixture
def no_recommendations():
    """Create review results with no recommendations."""
    return {
        "spec_id": "test-spec-003",
        "consensus": {"consensus_verdict": "pass", "agreement_rate": 1.0},
        "categorized_issues": [],
        "parsed_responses": [
            {"verdict": "pass", "issues": [], "recommendations": []},
            {"verdict": "pass", "issues": [], "recommendations": []}
        ],
        "models_consulted": 2
    }


def test_recommendation_consensus_all_agree(sample_with_recommendations):
    """Test recommendation with 100% agreement shows all-agree indicator."""
    report = FidelityReport(sample_with_recommendations)

    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)

    parsed_responses = report._convert_to_dict(report.parsed_responses)
    report._print_recommendation_consensus(console, parsed_responses)

    output = string_io.getvalue()

    # Verify header
    assert "RECOMMENDATIONS (with consensus)" in output
    assert "Recommendations with agreement levels from AI models" in output

    # Recommendation mentioned by all 3 models should show 100%
    assert "Add comprehensive error handling" in output
    assert "100%" in output


def test_recommendation_consensus_majority(sample_with_recommendations):
    """Test recommendation with majority agreement shows majority indicator."""
    report = FidelityReport(sample_with_recommendations)

    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)

    parsed_responses = report._convert_to_dict(report.parsed_responses)
    report._print_recommendation_consensus(console, parsed_responses)

    output = string_io.getvalue()

    # Recommendations mentioned by 2 of 3 models should show 67%
    assert "Increase test coverage to 80%" in output
    assert "67%" in output


def test_recommendation_consensus_sorted_by_agreement(sample_with_recommendations):
    """Test recommendations are sorted by consensus (highest first)."""
    report = FidelityReport(sample_with_recommendations)

    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)

    parsed_responses = report._convert_to_dict(report.parsed_responses)
    report._print_recommendation_consensus(console, parsed_responses)

    output = string_io.getvalue()

    # Find positions
    pos_all_agree = output.find("Add comprehensive error handling")
    pos_majority_1 = output.find("Increase test coverage to 80%")
    pos_majority_2 = output.find("Implement rate limiting")
    pos_minority_1 = output.find("Optimize database queries")
    pos_minority_2 = output.find("Improve input validation")

    # All-agree (100%) should come before majority (67%)
    assert pos_all_agree < pos_majority_1
    assert pos_all_agree < pos_majority_2

    # Majority should come before minority (33%)
    assert pos_majority_1 < pos_minority_1 or pos_majority_1 < pos_minority_2


def test_recommendation_consensus_with_no_recommendations(no_recommendations):
    """Test consensus display handles no recommendations gracefully."""
    report = FidelityReport(no_recommendations)

    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)

    parsed_responses = report._convert_to_dict(report.parsed_responses)
    report._print_recommendation_consensus(console, parsed_responses)

    output = string_io.getvalue()

    # Should not display anything when no recommendations
    assert "RECOMMENDATIONS" not in output


def test_recommendation_consensus_with_single_model(single_model_recommendations):
    """Test consensus display with single model response."""
    report = FidelityReport(single_model_recommendations)

    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)

    # This should not be called in practice (checked in print_console_rich)
    # but test the method handles it gracefully
    parsed_responses = report._convert_to_dict(report.parsed_responses)
    report._print_recommendation_consensus(console, parsed_responses)

    output = string_io.getvalue()

    # Should still display if called directly
    assert "RECOMMENDATIONS" in output
    assert "Minor documentation improvements" in output


def test_recommendation_consensus_percentage_calculation(sample_with_recommendations):
    """Test percentage calculations are correct."""
    report = FidelityReport(sample_with_recommendations)

    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)

    parsed_responses = report._convert_to_dict(report.parsed_responses)
    report._print_recommendation_consensus(console, parsed_responses)

    output = string_io.getvalue()

    # All 3 models (100%)
    assert "100%" in output

    # 2 of 3 models (67%)
    assert "67%" in output

    # 1 of 3 models (33%)
    assert "33%" in output


def test_recommendation_consensus_limits_display():
    """Test consensus display limits to top 10 recommendations."""
    # Create results with more than 10 unique recommendations
    results = {
        "spec_id": "test-spec-004",
        "consensus": {"consensus_verdict": "fail", "agreement_rate": 0.5},
        "categorized_issues": [],
        "parsed_responses": [
            {
                "verdict": "fail",
                "issues": [],
                "recommendations": [f"Recommendation {i}" for i in range(15)]
            }
        ],
        "models_consulted": 1
    }

    report = FidelityReport(results)

    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)

    parsed_responses = report._convert_to_dict(report.parsed_responses)
    report._print_recommendation_consensus(console, parsed_responses)

    output = string_io.getvalue()

    # Should show "Recommendation 0" through "Recommendation 9" (10 items)
    for i in range(10):
        assert f"Recommendation {i}" in output

    # Should not show recommendations beyond top 10
    assert "Recommendation 10" not in output
    assert "Recommendation 14" not in output


def test_recommendation_consensus_in_print_console_rich(sample_with_recommendations):
    """Test recommendation consensus is called within print_console_rich."""
    import sys

    report = FidelityReport(sample_with_recommendations)

    captured_output = StringIO()
    sys.stdout = captured_output

    try:
        report.print_console_rich(verbose=False)
        output = captured_output.getvalue()

        # Verify consensus-aware recommendations appear
        assert "RECOMMENDATIONS (with consensus)" in output
        assert "Add comprehensive error handling" in output
        assert "100%" in output

    finally:
        sys.stdout = sys.__stdout__


def test_recommendation_consensus_not_shown_for_single_model(single_model_recommendations):
    """Test consensus display is NOT shown for single model in print_console_rich."""
    import sys

    report = FidelityReport(single_model_recommendations)

    captured_output = StringIO()
    sys.stdout = captured_output

    try:
        report.print_console_rich(verbose=False)
        output = captured_output.getvalue()

        # Consensus-aware display should NOT appear (only 1 model)
        # Fallback to simple list instead
        assert "RECOMMENDATIONS (with consensus)" not in output
        # Should still show recommendations, just without consensus indicators
        # (This depends on whether consensus_recommendations is populated)

    finally:
        sys.stdout = sys.__stdout__


def test_recommendation_consensus_visual_indicators():
    """Test visual indicators are correctly applied based on agreement level."""
    results = {
        "spec_id": "test-spec-005",
        "consensus": {"consensus_verdict": "fail", "agreement_rate": 0.67},
        "categorized_issues": [],
        "parsed_responses": [
            {"verdict": "fail", "issues": [], "recommendations": ["Rec A", "Rec B"]},
            {"verdict": "fail", "issues": [], "recommendations": ["Rec A", "Rec C"]},
            {"verdict": "fail", "issues": [], "recommendations": ["Rec A"]}
        ],
        "models_consulted": 3
    }

    report = FidelityReport(results)

    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)

    parsed_responses = report._convert_to_dict(report.parsed_responses)
    report._print_recommendation_consensus(console, parsed_responses)

    output = string_io.getvalue()

    # Rec A mentioned by all 3 models (100%)
    assert "Rec A" in output
    assert "100%" in output

    # Rec B and C mentioned by 1 of 3 models (33%)
    assert ("Rec B" in output or "Rec C" in output)
    assert "33%" in output
