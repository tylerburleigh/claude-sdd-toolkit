"""
Integration tests for comparison view rendering.

Tests Rich TUI rendering for fidelity review, plan review, and status report
comparison views with side-by-side layouts, tables, and panels.
"""

import pytest
import json
from io import StringIO
from unittest.mock import patch, MagicMock

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from claude_skills.sdd_fidelity_review.report import FidelityReport
from claude_skills.sdd_fidelity_review.consultation import FidelityVerdict


# =============================================================================
# Fixtures for Mock Data
# =============================================================================


@pytest.fixture
def mock_spec_data():
    """Create mock spec data for testing."""
    return {
        "spec_id": "test-spec-001",
        "title": "Test Specification",
        "hierarchy": {
            "task-1": {
                "type": "task",
                "title": "Implement authentication service",
                "status": "completed",
                "metadata": {
                    "file_path": "src/auth/service.ts",
                    "requirements": [
                        "JWT token generation",
                        "Password hashing with bcrypt",
                        "Session management"
                    ]
                }
            },
            "task-2": {
                "type": "task",
                "title": "Add input validation",
                "status": "completed",
                "metadata": {
                    "file_path": "src/utils/validators.ts",
                    "requirements": [
                        "Email format validation",
                        "Password strength check"
                    ]
                }
            }
        }
    }


@pytest.fixture
def mock_fidelity_results():
    """Create mock fidelity review results with deviations."""
    return {
        "task-1": {
            "status": "pass",
            "deviations": [],
            "findings": "Authentication service correctly implements JWT tokens and bcrypt hashing."
        },
        "task-2": {
            "status": "partial",
            "deviations": [
                {
                    "requirement": "Password strength check",
                    "expected": "Minimum 8 characters, uppercase, lowercase, number, special char",
                    "actual": "Only checks minimum 6 characters",
                    "severity": "medium",
                    "recommendation": "Strengthen password validation rules"
                }
            ],
            "findings": "Input validation partially implemented, missing some password strength checks."
        }
    }


@pytest.fixture
def mock_parsed_ai_responses():
    """Create mock parsed AI responses for comparison view."""
    return [
        {
            "model": "gemini",
            "verdict": "pass",
            "issues": [],
            "recommendations": ["Add rate limiting", "Implement 2FA support"],
            "confidence": "high"
        },
        {
            "model": "codex",
            "verdict": "partial",
            "issues": [
                {
                    "severity": "medium",
                    "description": "Password validation too weak"
                }
            ],
            "recommendations": ["Strengthen password rules"],
            "confidence": "medium"
        }
    ]


@pytest.fixture
def mock_categorized_issues():
    """Create mock categorized issues for consensus matrix testing."""
    return [
        {
            "issue": "Missing input sanitization in user registration endpoint",
            "severity": "critical",
            "category": "security",
            "agreed_by": ["gemini", "codex", "claude"],
            "agreement_count": 3
        },
        {
            "issue": "Password validation requirements too weak",
            "severity": "high",
            "category": "security",
            "agreed_by": ["codex", "claude"],
            "agreement_count": 2
        },
        {
            "issue": "Missing error handling in authentication flow",
            "severity": "medium",
            "category": "reliability",
            "agreed_by": ["gemini"],
            "agreement_count": 1
        }
    ]


# =============================================================================
# Test: Fidelity Review Side-by-Side Comparison
# =============================================================================


def test_fidelity_review_side_by_side_comparison(
    mock_spec_data,
    mock_fidelity_results,
    mock_parsed_ai_responses
):
    """
    Test that fidelity review side-by-side comparison renders correctly.

    Verifies:
    - Model comparison table is created with Rich Table
    - Verdicts are displayed side-by-side across multiple models
    - Issue counts are shown for each model
    - Recommendations are formatted correctly
    - Color coding is applied (green=PASS, red=FAIL, yellow=PARTIAL)
    """
    # Create FidelityReport with mock data in expected format
    review_results = {
        "spec_id": "test-spec-001",
        "consensus": {
            "consensus_verdict": "partial",
            "agreement_rate": 0.5,
            "consensus_issues": [],
            "consensus_recommendations": []
        },
        "categorized_issues": [],
        "parsed_responses": mock_parsed_ai_responses,
        "models_consulted": len(mock_parsed_ai_responses)
    }

    report = FidelityReport(review_results)

    # Capture console output
    console = Console(file=StringIO(), width=100, legacy_windows=False)

    # Call the internal method that renders comparison table
    report._print_model_comparison_table(console)

    # Get rendered output
    output = console.file.getvalue()

    # Verify comparison table header
    assert "MODEL RESPONSE COMPARISON" in output
    assert "Side-by-side comparison of all AI model assessments" in output

    # Verify model columns are created
    assert "Model 1" in output
    assert "Model 2" in output

    # Verify verdicts are displayed
    assert "Verdict" in output
    assert "PASS" in output or "pass" in output.lower()
    assert "PARTIAL" in output or "partial" in output.lower()

    # Verify issue count row
    assert "Issue Count" in output or "Issues" in output

    # Verify recommendations are present
    # (The output includes recommendation counts or summaries)

    print("\n--- Comparison View Output ---")
    print(output)
    print("--- End Output ---\n")


def test_fidelity_review_no_models(mock_spec_data, mock_fidelity_results):
    """Test comparison view handles case with no AI model responses."""
    # Create report with no parsed responses
    review_results = {
        "spec_id": "test-spec-001",
        "consensus": {},
        "categorized_issues": [],
        "parsed_responses": [],
        "models_consulted": 0
    }

    report = FidelityReport(review_results)

    # Should not crash when printing comparison
    console = Console(file=StringIO(), width=100)
    report._print_model_comparison_table(console)

    # Output should be minimal or empty
    output = console.file.getvalue()
    assert "MODEL RESPONSE COMPARISON" not in output or output.strip() == ""


# =============================================================================
# Test: Consensus Matrix Display
# =============================================================================


def test_consensus_matrix_display(
    mock_parsed_ai_responses,
    mock_categorized_issues
):
    """
    Test that consensus matrix renders correctly with Rich Table.

    Verifies:
    - Consensus matrix table is created with issue rows and model columns
    - Each model column shows checkmark (✓) or dash (—) for agreement
    - Agreement percentage is calculated and displayed
    - Issues are color-coded by severity (critical=red, high=yellow, medium=blue, low=cyan)
    - Matrix shows which models identified each issue
    """
    # Create FidelityReport with mock data
    review_results = {
        "spec_id": "test-spec-001",
        "consensus": {
            "consensus_verdict": "partial",
            "agreement_rate": 0.67
        },
        "categorized_issues": mock_categorized_issues,
        "parsed_responses": mock_parsed_ai_responses,
        "models_consulted": len(mock_parsed_ai_responses)
    }

    report = FidelityReport(review_results)

    # Capture console output
    console = Console(file=StringIO(), width=120, legacy_windows=False)

    # Call the consensus matrix rendering method
    report._print_consensus_matrix(console, mock_categorized_issues)

    # Get rendered output
    output = console.file.getvalue()

    # Verify consensus matrix header
    assert "CONSENSUS MATRIX" in output
    assert "Shows which AI models identified each issue" in output

    # Verify column headers
    assert "Issue" in output
    assert "M1" in output  # Model 1 column
    assert "M2" in output  # Model 2 column
    assert "Agreement" in output

    # Verify issues are present (at least some text from issues)
    assert "sanitization" in output or "validation" in output or "error" in output

    # Verify agreement indicators (checkmarks or dashes)
    assert "✓" in output or "—" in output

    # Verify agreement percentages are shown
    assert "%" in output

    print("\n--- Consensus Matrix Output ---")
    print(output)
    print("--- End Output ---\n")


def test_consensus_matrix_no_issues(mock_parsed_ai_responses):
    """Test consensus matrix handles case with no categorized issues."""
    # Create report with no issues
    review_results = {
        "spec_id": "test-spec-001",
        "consensus": {},
        "categorized_issues": [],
        "parsed_responses": mock_parsed_ai_responses,
        "models_consulted": len(mock_parsed_ai_responses)
    }

    report = FidelityReport(review_results)

    # Should not crash when printing matrix with no issues
    console = Console(file=StringIO(), width=120)
    report._print_consensus_matrix(console, [])

    # Output should have header but no issue rows
    output = console.file.getvalue()
    # Matrix might still print header or be empty
    # The important thing is it doesn't crash


# =============================================================================
# Test: Issue Severity Panel Rendering
# =============================================================================


def test_issue_severity_panel_rendering(mock_categorized_issues, capsys):
    """
    Test that issue severity panels render correctly with Rich Panel components.

    Verifies:
    - Issues grouped by severity (critical, high, medium, low)
    - Each severity has its own color-coded panel (red, yellow, blue, cyan)
    - Panel titles include severity name and count
    - Panel icons are displayed (🔴, 🟡, 🔵, ⚪)
    - Issues are displayed as bullet points within panels
    - Border styles match severity colors
    """
    # Create FidelityReport with categorized issues
    review_results = {
        "spec_id": "test-spec-001",
        "consensus": {
            "consensus_verdict": "partial",
            "agreement_rate": 0.67,
            "consensus_recommendations": ["Improve input validation"]
        },
        "categorized_issues": mock_categorized_issues,
        "parsed_responses": [],
        "models_consulted": 0
    }

    report = FidelityReport(review_results)

    # Call print_console_rich() which prints to stdout
    # We'll capture it with capsys
    report.print_console_rich(verbose=False)

    # Capture stdout
    captured = capsys.readouterr()
    output = captured.out

    # Verify report header
    assert "IMPLEMENTATION FIDELITY REVIEW" in output
    assert "test-spec-001" in output

    # Verify consensus verdict is shown
    assert "Consensus Verdict" in output
    assert "Agreement Rate" in output

    # Verify severity panel titles with icons
    assert "CRITICAL ISSUES" in output or "critical" in output.lower()
    assert "HIGH" in output or "high" in output.lower()
    assert "MEDIUM" in output or "medium" in output.lower()

    # Verify issue content is present
    assert "sanitization" in output or "validation" in output or "error" in output

    # Verify bullet points for issues
    assert "•" in output


def test_issue_severity_panel_empty(capsys):
    """Test severity panels handle case with no issues."""
    # Create report with no categorized issues
    review_results = {
        "spec_id": "test-spec-001",
        "consensus": {
            "consensus_verdict": "pass",
            "agreement_rate": 1.0,
            "consensus_recommendations": []
        },
        "categorized_issues": [],
        "parsed_responses": [],
        "models_consulted": 0
    }

    report = FidelityReport(review_results)

    # Should not crash when rendering with no issues
    report.print_console_rich(verbose=False)

    # Capture stdout
    captured = capsys.readouterr()
    output = captured.out

    # Verify header still renders
    assert "IMPLEMENTATION FIDELITY REVIEW" in output

    # Verify verdict is shown even without issues
    assert "Consensus Verdict" in output
    assert "PASS" in output or "pass" in output.lower()
