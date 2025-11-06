"""
Integration tests for bulk modification operations.

Tests the complete workflow:
1. Parse review report -> 2. Generate suggestions -> 3. Apply modifications
"""

import json
import pytest
import tempfile
from pathlib import Path
from claude_skills.sdd_spec_mod import (
    parse_review_report,
    suggest_modifications,
    apply_modifications
)


class TestBulkModificationWorkflow:
    """Integration tests for the complete modification workflow."""

    @pytest.fixture
    def sample_spec(self):
        """Create a sample spec for testing."""
        return {
            "spec_id": "test-spec-001",
            "title": "Test Specification",
            "metadata": {
                "created_at": "2025-10-01T00:00:00Z",
                "estimated_hours": 10
            },
            "hierarchy": {
                "spec-root": {
                    "type": "spec",
                    "title": "Test Spec",
                    "parent": None,
                    "children": ["phase-1"],
                    "total_tasks": 2,
                    "completed_tasks": 0
                },
                "phase-1": {
                    "type": "phase",
                    "title": "Phase 1",
                    "parent": "spec-root",
                    "children": ["task-1-1", "task-1-2"],
                    "total_tasks": 2,
                    "completed_tasks": 0
                },
                "task-1-1": {
                    "type": "task",
                    "title": "Task 1.1",
                    "description": "Original description",
                    "parent": "phase-1",
                    "children": [],
                    "status": "pending",
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "dependencies": {"blocks": [], "blocked_by": [], "depends": []},
                    "metadata": {"estimated_hours": 2}
                },
                "task-1-2": {
                    "type": "task",
                    "title": "Task 1.2",
                    "description": "Another task",
                    "parent": "phase-1",
                    "children": [],
                    "status": "pending",
                    "total_tasks": 1,
                    "completed_tasks": 0,
                    "dependencies": {"blocks": [], "blocked_by": [], "depends": []},
                    "metadata": {}
                }
            }
        }

    @pytest.fixture
    def markdown_review(self):
        """Create a sample markdown review report."""
        return """
# Specification Review Report

**Spec**: Test Specification (`test-spec-001`)
**Models Consulted**: 2 (gemini, codex)
**Consensus Score**: 7.5/10
**Final Recommendation**: REVISE
**Consensus Level**: Strong

## Executive Summary

The specification needs revision to address critical description gaps.

### Critical Issues (Must Fix)

- task-1-1 missing description - flagged by: [gemini, codex]
  - Impact: Cannot implement without context
  - Recommended fix: Add detailed description

### High Priority Issues

- task-1-2 estimate missing - flagged by: [gemini]
  - Impact: Poor planning
  - Recommended fix: Should be 3 hours based on complexity

### Medium/Low Priority

- None found
"""

    def test_complete_workflow_markdown_to_modifications(self, sample_spec, markdown_review):
        """Test the complete workflow from markdown review to applied modifications."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Step 1: Write review report to file
            review_file = tmpdir_path / "review.md"
            review_file.write_text(markdown_review)

            # Step 2: Parse review report
            parse_result = parse_review_report(str(review_file))

            assert parse_result["success"] is True
            assert parse_result["format"] == "markdown"
            assert parse_result["metadata"]["spec_id"] == "test-spec-001"
            assert parse_result["metadata"]["overall_score"] == 7.5

            issues = parse_result["issues"]
            assert len(issues["critical"]) == 1
            assert len(issues["high"]) == 1

            # Step 3: Generate modification suggestions
            suggestions = suggest_modifications(issues)

            assert len(suggestions) >= 2  # At least one for each issue
            assert any(mod["node_id"] == "task-1-1" for mod in suggestions)
            assert any(mod["node_id"] == "task-1-2" for mod in suggestions)

            # Step 4: Create modifications file
            mods_file = tmpdir_path / "modifications.json"
            mods_data = {
                "modifications": suggestions
            }
            with open(mods_file, 'w') as f:
                json.dump(mods_data, f, indent=2)

            # Step 5: Apply modifications
            result = apply_modifications(sample_spec, str(mods_file))

            assert result["success"] is True
            assert result["successful"] >= 2
            assert result["failed"] == 0

            # Verify modifications were applied
            task_1_1 = sample_spec["hierarchy"]["task-1-1"]
            task_1_2 = sample_spec["hierarchy"]["task-1-2"]

            # task-1-1 should have updated description
            assert "[UPDATE REQUIRED]" in task_1_1["description"] or task_1_1["description"] != "Original description"

            # task-1-2 should have estimated_hours metadata
            assert "estimated_hours" in task_1_2["metadata"]
            assert task_1_2["metadata"]["estimated_hours"] == 3.0

    def test_parse_json_review_format(self):
        """Test parsing JSON format review reports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create JSON review
            review_data = {
                "metadata": {
                    "spec_id": "test-spec-002",
                    "spec_title": "JSON Test Spec"
                },
                "consensus": {
                    "overall_score": 8.5,
                    "recommendation": "APPROVE",
                    "consensus_level": "Strong",
                    "models": ["gemini", "codex", "cursor"],
                    "synthesis_text": """
### Critical Issues (Must Fix)

- task-2-1 missing verification - flagged by: [gemini]
  - Impact: No testing coverage
  - Recommended fix: Add unit tests
"""
                }
            }

            review_file = tmpdir_path / "review.json"
            with open(review_file, 'w') as f:
                json.dump(review_data, f, indent=2)

            # Parse JSON review
            parse_result = parse_review_report(str(review_file))

            assert parse_result["success"] is True
            assert parse_result["format"] == "json"
            assert parse_result["metadata"]["spec_id"] == "test-spec-002"
            assert parse_result["metadata"]["overall_score"] == 8.5
            assert parse_result["metadata"]["recommendation"] == "APPROVE"

    def test_empty_review_produces_no_suggestions(self):
        """Test that reviews with no issues produce no suggestions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create empty review
            empty_review = """
# Specification Review Report

**Spec**: Clean Spec (`clean-spec-001`)
**Consensus Score**: 9.5/10
**Final Recommendation**: APPROVE

## Executive Summary

Specification is excellent and ready for implementation.

### Critical Issues (Must Fix)

None found.

### High Priority Issues

None found.
"""

            review_file = tmpdir_path / "review.md"
            review_file.write_text(empty_review)

            # Parse and generate suggestions
            parse_result = parse_review_report(str(review_file))
            assert parse_result["success"] is True

            suggestions = suggest_modifications(parse_result["issues"])
            assert len(suggestions) == 0

    def test_malformed_suggestions_handled_gracefully(self, sample_spec):
        """Test that malformed modification files are handled properly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create malformed modifications file
            mods_file = tmpdir_path / "bad_mods.json"
            bad_mods = {
                "modifications": [
                    {
                        "operation": "update_node_field",
                        "node_id": "nonexistent-task",
                        "field": "description",
                        "value": "Updated"
                    },
                    {
                        "operation": "invalid_operation",
                        "foo": "bar"
                    }
                ]
            }
            with open(mods_file, 'w') as f:
                json.dump(bad_mods, f, indent=2)

            # Apply modifications
            result = apply_modifications(sample_spec, str(mods_file))

            # Should fail some operations but continue
            assert result["total_operations"] == 2
            assert result["failed"] == 2
            assert result["successful"] == 0

    def test_review_to_verification_node_creation(self, sample_spec):
        """Test that missing verification issues create verify nodes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Review with missing verification
            review = """
### Critical Issues (Must Fix)

- task-1-1 missing verification steps - flagged by: [gemini]
  - Impact: No testing coverage
  - Recommended fix: Add unit tests for Task 1.1
"""

            review_file = tmpdir_path / "review.md"
            review_file.write_text(review)

            # Parse and generate suggestions
            parse_result = parse_review_report(str(review_file))
            suggestions = suggest_modifications(parse_result["issues"])

            # Should suggest adding a verify node
            verify_suggestions = [s for s in suggestions if s["operation"] == "add_node"]
            assert len(verify_suggestions) > 0

            # The suggestion should have proper structure
            for sugg in verify_suggestions:
                assert "node_data" in sugg
                assert sugg["node_data"]["type"] == "verify"

            # Note: The parent_id extraction may not work perfectly for all cases
            # This test verifies the suggestion is generated correctly
            # Actual application would need the parent_id to be correct in the spec


class TestErrorHandling:
    """Test error handling in the workflow."""

    def test_nonexistent_review_file(self):
        """Test handling of nonexistent review files."""
        with pytest.raises(FileNotFoundError):
            parse_review_report("/nonexistent/review.md")

    def test_invalid_json_review(self):
        """Test handling of invalid JSON review files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            bad_json_file = tmpdir_path / "bad.json"
            bad_json_file.write_text("{invalid json")

            result = parse_review_report(str(bad_json_file))
            assert result["success"] is False
            assert "Invalid JSON" in result["error"]

    def test_unsupported_file_format(self):
        """Test handling of unsupported file formats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Use .pdf which is truly unsupported (txt/markdown are treated the same)
            bad_file = tmpdir_path / "review.pdf"
            bad_file.write_bytes(b"PDF content")

            result = parse_review_report(str(bad_file))
            assert result["success"] is False
            assert "Unsupported file format" in result["error"]

    def test_modifications_file_not_found(self, sample_spec):
        """Test handling of missing modifications file."""
        with pytest.raises(FileNotFoundError):
            apply_modifications(sample_spec(), "/nonexistent/mods.json")

    @pytest.fixture
    def sample_spec(self):
        """Fixture factory for sample spec."""
        def _sample_spec():
            return {
                "spec_id": "test",
                "hierarchy": {
                    "spec-root": {
                        "type": "spec",
                        "title": "Test",
                        "children": [],
                        "total_tasks": 0,
                        "completed_tasks": 0
                    }
                }
            }
        return _sample_spec
