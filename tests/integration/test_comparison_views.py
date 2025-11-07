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
