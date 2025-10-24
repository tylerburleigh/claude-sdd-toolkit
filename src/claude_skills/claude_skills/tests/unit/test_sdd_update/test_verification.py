"""
Tests for verification.py - JSON-only verification result operations.
"""
import pytest
from pathlib import Path

from claude_skills.sdd_update.verification import (
    add_verification_result,
    format_verification_summary
)
from claude_skills.common.spec import load_json_spec


class TestAddVerificationResult:
    """Test add_verification_result() function."""

    def test_add_verification_result_passed(self, specs_structure, valid_json_spec):
        """Test adding a PASSED verification result."""
        spec_id = "test-anchors-2025-01-01-001"

        # Load and save the fixture state data
        import json
        from claude_skills.common.spec import save_json_spec
        spec_data = json.loads(valid_json_spec.read_text())
        save_json_spec(spec_id, specs_structure, spec_data)

        result = add_verification_result(
            spec_id=spec_id,
            verify_id="verify-1-1",
            status="PASSED",
            command="pytest tests/",
            output="All tests passed",
            notes="Tests ran successfully",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        # Verify result was stored in hierarchy node metadata
        spec_data = load_json_spec(spec_id, specs_structure)
        verify_node = spec_data["hierarchy"]["verify-1-1"]
        assert "metadata" in verify_node
        assert "verification_result" in verify_node["metadata"]

        vr = verify_node["metadata"]["verification_result"]
        assert vr["status"] == "PASSED"
        assert vr["command"] == "pytest tests/"
        assert vr["output"] == "All tests passed"
        assert vr["notes"] == "Tests ran successfully"
        assert "date" in vr

    def test_add_verification_result_failed(self, specs_structure, valid_json_spec):
        """Test adding a FAILED verification result."""
        spec_id = "test-anchors-2025-01-01-001"

        # Load and save the fixture state data
        import json
        from claude_skills.common.spec import save_json_spec
        spec_data = json.loads(valid_json_spec.read_text())
        save_json_spec(spec_id, specs_structure, spec_data)

        result = add_verification_result(
            spec_id=spec_id,
            verify_id="verify-1-1",
            status="FAILED",
            command="pytest tests/",
            output="2 tests failed",
            issues="Test failures in test_main.py",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        vr = spec_data["hierarchy"]["verify-1-1"]["metadata"]["verification_result"]
        assert vr["status"] == "FAILED"
        assert vr["issues"] == "Test failures in test_main.py"

    def test_add_verification_result_partial(self, specs_structure, valid_json_spec):
        """Test adding a PARTIAL verification result."""
        spec_id = "test-anchors-2025-01-01-001"

        # Load and save the fixture state data
        import json
        from claude_skills.common.spec import save_json_spec
        spec_data = json.loads(valid_json_spec.read_text())
        save_json_spec(spec_id, specs_structure, spec_data)

        result = add_verification_result(
            spec_id=spec_id,
            verify_id="verify-1-1",
            status="PARTIAL",
            notes="Some manual steps remaining",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        vr = spec_data["hierarchy"]["verify-1-1"]["metadata"]["verification_result"]
        assert vr["status"] == "PARTIAL"

    def test_add_verification_result_updates_timestamp(self, specs_structure, valid_json_spec):
        """Test that adding verification result updates last_updated."""
        spec_id = "test-anchors-2025-01-01-001"

        # Load and save the fixture state data
        import json
        from claude_skills.common.spec import save_json_spec
        spec_data = json.loads(valid_json_spec.read_text())
        save_json_spec(spec_id, specs_structure, spec_data)

        spec_data_before = load_json_spec(spec_id, specs_structure)
        original_timestamp = spec_data_before.get("last_updated")

        result = add_verification_result(
            spec_id=spec_id,
            verify_id="verify-1-1",
            status="PASSED",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data_after = load_json_spec(spec_id, specs_structure)
        new_timestamp = spec_data_after.get("last_updated")

        assert new_timestamp != original_timestamp

    def test_add_verification_result_invalid_status(self, specs_structure, valid_json_spec):
        """Test adding verification result with invalid status."""
        spec_id = "test-anchors-2025-01-01-001"

        result = add_verification_result(
            spec_id=spec_id,
            verify_id="verify-1-1",
            status="INVALID",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is False

    def test_add_verification_result_nonexistent_verify_id(self, specs_structure, valid_json_spec):
        """Test adding verification result for non-existent verify node."""
        spec_id = "test-anchors-2025-01-01-001"

        result = add_verification_result(
            spec_id=spec_id,
            verify_id="verify-99-99",
            status="PASSED",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is False

    def test_add_verification_result_dry_run(self, specs_structure, valid_json_spec):
        """Test dry run doesn't save changes."""
        spec_id = "test-anchors-2025-01-01-001"

        # Load and save the fixture state data
        import json
        from claude_skills.common.spec import save_json_spec
        spec_data = json.loads(valid_json_spec.read_text())
        save_json_spec(spec_id, specs_structure, spec_data)

        result = add_verification_result(
            spec_id=spec_id,
            verify_id="verify-1-1",
            status="PASSED",
            specs_dir=specs_structure,
            dry_run=True,
            printer=None
        )

        assert result is True

        # Verify result was not saved
        spec_data = load_json_spec(spec_id, specs_structure)
        verify_node = spec_data["hierarchy"]["verify-1-1"]
        assert "verification_result" not in verify_node.get("metadata", {})

    def test_add_verification_result_minimal(self, specs_structure, valid_json_spec):
        """Test adding verification result with minimal information."""
        spec_id = "test-anchors-2025-01-01-001"

        # Load and save the fixture state data
        import json
        from claude_skills.common.spec import save_json_spec
        spec_data = json.loads(valid_json_spec.read_text())
        save_json_spec(spec_id, specs_structure, spec_data)

        result = add_verification_result(
            spec_id=spec_id,
            verify_id="verify-1-1",
            status="PASSED",
            specs_dir=specs_structure,
            printer=None
        )

        assert result is True

        spec_data = load_json_spec(spec_id, specs_structure)
        vr = spec_data["hierarchy"]["verify-1-1"]["metadata"]["verification_result"]
        assert vr["status"] == "PASSED"
        assert "date" in vr
        # Optional fields should not be present
        assert "command" not in vr
        assert "output" not in vr
        assert "issues" not in vr
        assert "notes" not in vr


class TestFormatVerificationSummary:
    """Test format_verification_summary() function."""

    def test_format_verification_summary_all_passed(self):
        """Test formatting summary with all tests passed."""
        verification_results = [
            {
                "verify_id": "verify-1-1",
                "title": "Run unit tests",
                "status": "PASSED",
                "command": "pytest tests/",
                "result": "All 10 tests passed"
            },
            {
                "verify_id": "verify-1-2",
                "title": "Run integration tests",
                "status": "PASSED",
                "command": "pytest tests/integration/",
                "result": "All 5 tests passed"
            }
        ]

        summary = format_verification_summary(verification_results)

        assert "✅ Phase Verification Complete!" in summary
        assert "All 2 verification steps executed successfully" in summary
        assert "verify-1-1: Run unit tests" in summary
        assert "verify-1-2: Run integration tests" in summary

    def test_format_verification_summary_mixed_results(self):
        """Test formatting summary with mixed results."""
        verification_results = [
            {
                "verify_id": "verify-1-1",
                "title": "Run tests",
                "status": "PASSED"
            },
            {
                "verify_id": "verify-1-2",
                "title": "Lint code",
                "status": "FAILED",
                "notes": "3 linting errors found"
            },
            {
                "verify_id": "verify-1-3",
                "title": "Manual check",
                "status": "PARTIAL",
                "notes": "Some manual steps remaining"
            }
        ]

        summary = format_verification_summary(verification_results)

        assert "⚠️ Phase Verification Results" in summary
        assert "Total: 3 | Passed: 1 | Failed: 1 | Partial: 1" in summary
        assert "✅" in summary
        assert "❌" in summary
        assert "⚠️" in summary

    def test_format_verification_summary_empty_list(self):
        """Test formatting summary with empty list."""
        verification_results = []

        summary = format_verification_summary(verification_results)

        assert "All 0 verification steps" in summary

    def test_format_verification_summary_includes_command(self):
        """Test that summary includes command information."""
        verification_results = [
            {
                "verify_id": "verify-1-1",
                "title": "Run tests",
                "status": "PASSED",
                "command": "pytest tests/ -v"
            }
        ]

        summary = format_verification_summary(verification_results)

        assert "Command: pytest tests/ -v" in summary

    def test_format_verification_summary_includes_notes(self):
        """Test that summary includes notes."""
        verification_results = [
            {
                "verify_id": "verify-1-1",
                "title": "Check config",
                "status": "PASSED",
                "notes": "Configuration verified manually"
            }
        ]

        summary = format_verification_summary(verification_results)

        assert "Notes: Configuration verified manually" in summary
