"""Unit tests for sdd_validate.formatting module."""

import pytest
from claude_skills.common.validation import JsonSpecValidationResult
from claude_skills.sdd_validate.formatting import (
    normalize_validation_result,
    format_validation_summary,
    NormalizedValidationResult,
)


def test_normalize_validation_result_clean():
    """Test normalization of a clean validation result."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-001",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
    )

    normalized = normalize_validation_result(result)

    assert normalized.spec_id == "test-spec-001"
    assert normalized.status == "valid"
    assert normalized.error_count == 0
    assert normalized.warning_count == 0
    assert normalized.auto_fixable_error_count == 0
    assert normalized.auto_fixable_warning_count == 0
    assert not normalized.has_errors
    assert not normalized.has_warnings


def test_normalize_validation_result_with_errors():
    """Test normalization with errors."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-002",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
        structure_errors=["Missing required field"],
        hierarchy_errors=["Invalid parent reference"],
    )

    normalized = normalize_validation_result(result)

    assert normalized.spec_id == "test-spec-002"
    assert normalized.status == "errors"
    assert normalized.error_count == 2
    assert normalized.warning_count == 0
    assert normalized.has_errors
    assert not normalized.has_warnings


def test_normalize_validation_result_with_warnings():
    """Test normalization with warnings only."""
    result = JsonSpecValidationResult(
        spec_id="test-spec-003",
        generated="2025-01-20T10:00:00Z",
        last_updated="2025-01-20T10:00:00Z",
        structure_warnings=["Spec ID format not recommended"],
    )

    normalized = normalize_validation_result(result)

    assert normalized.spec_id == "test-spec-003"
    assert normalized.status == "warnings"
    assert normalized.error_count == 0
    assert normalized.warning_count == 1
    assert not normalized.has_errors
    assert normalized.has_warnings


def test_format_validation_summary_basic():
    """Test basic summary formatting."""
    normalized = NormalizedValidationResult(
        spec_id="test-spec-001",
        status="valid",
        error_count=0,
        warning_count=0,
        auto_fixable_error_count=0,
        auto_fixable_warning_count=0,
        issues=[],
    )

    summary = format_validation_summary(normalized, verbose=False)

    assert "Errors: 0" in summary
    assert "Warnings: 0" in summary
    assert "Auto-fix candidates: 0" in summary


def test_format_validation_summary_verbose():
    """Test verbose summary formatting."""
    normalized = NormalizedValidationResult(
        spec_id="test-spec-001",
        status="errors",
        error_count=1,
        warning_count=1,
        auto_fixable_error_count=1,
        auto_fixable_warning_count=0,
        issues=[
            {
                "message": "Missing required field",
                "severity": "error",
                "category": "structure",
                "location": "spec-root",
                "auto_fixable": True,
            },
            {
                "message": "Non-standard format",
                "severity": "warning",
                "category": "structure",
                "location": None,
                "auto_fixable": False,
            },
        ],
    )

    summary = format_validation_summary(normalized, verbose=True)

    assert "Errors: 1" in summary
    assert "Warnings: 1" in summary
    assert "Auto-fix candidates: 1" in summary
    assert "Issues:" in summary
    assert "Missing required field" in summary
    assert "Non-standard format" in summary
    assert "auto-fixable" in summary


def test_normalized_validation_result_properties():
    """Test NormalizedValidationResult computed properties."""
    normalized = NormalizedValidationResult(
        spec_id="test-spec-001",
        status="errors",
        error_count=2,
        warning_count=1,
        auto_fixable_error_count=1,
        auto_fixable_warning_count=1,
        issues=[],
    )

    assert normalized.auto_fixable_total == 2
    assert normalized.has_errors is True
    assert normalized.has_warnings is False  # False when has_errors is True
