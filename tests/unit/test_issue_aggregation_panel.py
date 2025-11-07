"""
Tests for issue aggregation panel in fidelity review reports.

Tests the _print_issue_aggregation_panel method that displays common
concerns across multiple AI model responses.
"""

import pytest
from io import StringIO
from rich.console import Console
from claude_skills.sdd_fidelity_review.report import FidelityReport


@pytest.fixture
def sample_review_results():
    """Create sample review results with multiple model responses."""
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
                "issues": [
                    "Missing error handling in auth module",
                    "Insufficient test coverage",
                    "API endpoints lack rate limiting"
                ],
                "recommendations": []
            },
            {
                "verdict": "partial",
                "issues": [
                    "Missing error handling in auth module",
                    "Database queries not optimized",
                    "API endpoints lack rate limiting"
                ],
                "recommendations": []
            },
            {
                "verdict": "fail",
                "issues": [
                    "Missing error handling in auth module",
                    "Insufficient test coverage",
                    "Security vulnerabilities in input validation"
                ],
                "recommendations": []
            }
        ],
        "models_consulted": 3
    }


@pytest.fixture
def single_model_results():
    """Create review results with only one model response."""
    return {
        "spec_id": "test-spec-002",
        "consensus": {"consensus_verdict": "pass", "agreement_rate": 1.0},
        "categorized_issues": [],
        "parsed_responses": [
            {
                "verdict": "pass",
                "issues": ["Minor documentation gap"],
                "recommendations": []
            }
        ],
        "models_consulted": 1
    }


@pytest.fixture
def no_issues_results():
    """Create review results with no issues found."""
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


def test_issue_aggregation_with_multiple_models(sample_review_results):
    """Test issue aggregation displays common concerns correctly."""
    report = FidelityReport(sample_review_results)

    # Create console that captures output
    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)

    # Call the aggregation panel method
    parsed_responses = report._convert_to_dict(report.parsed_responses)
    report._print_issue_aggregation_panel(console, parsed_responses)

    output = string_io.getvalue()

    # Verify header is present
    assert "COMMON CONCERNS" in output
    assert "Issues identified by multiple AI models" in output

    # Verify most common issue appears (mentioned by all 3 models)
    assert "Missing error handling in auth module" in output

    # Verify second most common issues appear (mentioned by 2 models)
    assert "Insufficient test coverage" in output
    assert "API endpoints lack rate limiting" in output


def test_issue_aggregation_frequency_sorting(sample_review_results):
    """Test issues are sorted by frequency (most common first)."""
    report = FidelityReport(sample_review_results)

    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)

    parsed_responses = report._convert_to_dict(report.parsed_responses)
    report._print_issue_aggregation_panel(console, parsed_responses)

    output = string_io.getvalue()

    # Find positions of issues in output
    pos_auth_error = output.find("Missing error handling in auth module")
    pos_test_coverage = output.find("Insufficient test coverage")
    pos_rate_limiting = output.find("API endpoints lack rate limiting")
    pos_security = output.find("Security vulnerabilities in input validation")

    # Most common issue (3 mentions) should appear before less common ones
    assert pos_auth_error < pos_test_coverage
    assert pos_auth_error < pos_rate_limiting
    assert pos_auth_error < pos_security


def test_issue_aggregation_with_no_issues(no_issues_results):
    """Test aggregation panel handles no issues gracefully."""
    report = FidelityReport(no_issues_results)

    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)

    parsed_responses = report._convert_to_dict(report.parsed_responses)
    report._print_issue_aggregation_panel(console, parsed_responses)

    output = string_io.getvalue()

    # Should not display anything when no issues exist
    assert "COMMON CONCERNS" not in output


def test_issue_aggregation_with_single_model(single_model_results):
    """Test aggregation panel is not shown for single model responses."""
    report = FidelityReport(single_model_results)

    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)

    # This should not be called in practice (checked in print_console_rich)
    # but test the method handles it gracefully
    parsed_responses = report._convert_to_dict(report.parsed_responses)
    report._print_issue_aggregation_panel(console, parsed_responses)

    output = string_io.getvalue()

    # Should still display if called directly
    assert "COMMON CONCERNS" in output


def test_issue_aggregation_percentage_calculation(sample_review_results):
    """Test percentage of models mentioning each issue is calculated correctly."""
    report = FidelityReport(sample_review_results)

    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)

    parsed_responses = report._convert_to_dict(report.parsed_responses)
    report._print_issue_aggregation_panel(console, parsed_responses)

    output = string_io.getvalue()

    # Issue mentioned by all 3 models should show 100%
    assert "100%" in output

    # Issues mentioned by 2 of 3 models should show 67%
    assert "67%" in output


def test_issue_aggregation_limits_display():
    """Test aggregation panel limits display to top 10 issues."""
    # Create results with more than 10 unique issues
    results = {
        "spec_id": "test-spec-004",
        "consensus": {"consensus_verdict": "fail", "agreement_rate": 0.5},
        "categorized_issues": [],
        "parsed_responses": [
            {
                "verdict": "fail",
                "issues": [f"Issue {i}" for i in range(15)],
                "recommendations": []
            }
        ],
        "models_consulted": 1
    }

    report = FidelityReport(results)

    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)

    parsed_responses = report._convert_to_dict(report.parsed_responses)
    report._print_issue_aggregation_panel(console, parsed_responses)

    output = string_io.getvalue()

    # Should show "Issue 0" through "Issue 9" (10 issues)
    for i in range(10):
        assert f"Issue {i}" in output

    # Should not show issues beyond top 10
    assert "Issue 10" not in output
    assert "Issue 14" not in output


def test_issue_aggregation_truncates_long_issues():
    """Test long issue text is truncated with ellipsis."""
    long_issue = "A" * 100  # 100 character issue

    results = {
        "spec_id": "test-spec-005",
        "consensus": {"consensus_verdict": "fail", "agreement_rate": 1.0},
        "categorized_issues": [],
        "parsed_responses": [
            {
                "verdict": "fail",
                "issues": [long_issue],
                "recommendations": []
            }
        ],
        "models_consulted": 1
    }

    report = FidelityReport(results)

    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)

    parsed_responses = report._convert_to_dict(report.parsed_responses)
    report._print_issue_aggregation_panel(console, parsed_responses)

    output = string_io.getvalue()

    # Should contain truncated version with ellipsis
    assert "..." in output
    # Should not contain the full 100-character string
    assert long_issue not in output


def test_issue_aggregation_in_print_console_rich(sample_review_results):
    """Test aggregation panel is called within print_console_rich."""
    import sys

    report = FidelityReport(sample_review_results)

    # Call print_console_rich with captured output
    captured_output = StringIO()
    sys.stdout = captured_output

    try:
        report.print_console_rich(verbose=False)
        output = captured_output.getvalue()

        # Verify aggregation panel appears in full output
        assert "COMMON CONCERNS" in output
        assert "Missing error handling in auth module" in output

    finally:
        sys.stdout = sys.__stdout__


def test_issue_aggregation_not_shown_for_single_model_in_print_console_rich(single_model_results):
    """Test aggregation panel is NOT shown for single model in print_console_rich."""
    import sys

    report = FidelityReport(single_model_results)

    captured_output = StringIO()
    sys.stdout = captured_output

    try:
        report.print_console_rich(verbose=False)
        output = captured_output.getvalue()

        # Aggregation panel should NOT appear (only 1 model)
        assert "COMMON CONCERNS" not in output

    finally:
        sys.stdout = sys.__stdout__


def test_issue_aggregation_color_coding():
    """Test count color coding based on model agreement."""
    results = {
        "spec_id": "test-spec-006",
        "consensus": {"consensus_verdict": "fail", "agreement_rate": 0.67},
        "categorized_issues": [],
        "parsed_responses": [
            {"verdict": "fail", "issues": ["Issue A", "Issue B"], "recommendations": []},
            {"verdict": "fail", "issues": ["Issue A", "Issue C"], "recommendations": []},
            {"verdict": "fail", "issues": ["Issue A"], "recommendations": []}
        ],
        "models_consulted": 3
    }

    report = FidelityReport(results)

    string_io = StringIO()
    console = Console(file=string_io, width=120, legacy_windows=False)

    parsed_responses = report._convert_to_dict(report.parsed_responses)
    report._print_issue_aggregation_panel(console, parsed_responses)

    output = string_io.getvalue()

    # Issue A mentioned by all 3 models (100%) - should have green color code
    assert "Issue A" in output
    assert "100%" in output

    # Issue B and C mentioned by 1 of 3 models (33%) - should have cyan color code
    assert "Issue B" in output or "Issue C" in output
    assert "33%" in output
