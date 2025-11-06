"""
Unit tests for suggest_modifications function in review_parser module.
"""

import pytest
from claude_skills.sdd_spec_mod.review_parser import suggest_modifications, _suggest_for_issue


class TestSuggestModifications:
    """Test the suggest_modifications function."""

    def test_empty_issues_returns_empty_list(self):
        """Test that empty issues dict returns empty modifications list."""
        issues = {"critical": [], "high": [], "medium": [], "low": []}
        result = suggest_modifications(issues)
        assert result == []

    def test_processes_critical_issues_first(self):
        """Test that critical issues are processed before others."""
        issues = {
            "critical": [
                {
                    "title": "task-1-1 missing description",
                    "description": "Add more details",
                    "fix": "Add description",
                    "severity": "critical"
                }
            ],
            "high": [],
            "medium": [],
            "low": []
        }
        result = suggest_modifications(issues)
        assert len(result) == 1
        assert result[0]["node_id"] == "task-1-1"
        assert "critical" in result[0]["reason"].lower()

    def test_handles_missing_severity_keys(self):
        """Test graceful handling of missing severity keys."""
        issues = {"critical": []}  # Missing high, medium, low
        result = suggest_modifications(issues)
        assert result == []

    def test_processes_multiple_issues(self):
        """Test processing multiple issues from different severity levels."""
        issues = {
            "critical": [
                {
                    "title": "task-1-1 missing description",
                    "description": "Add details",
                    "fix": "Add description",
                    "severity": "critical"
                }
            ],
            "high": [
                {
                    "title": "task-2-1 estimate incorrect",
                    "description": "Should be 2 hours",
                    "fix": "Update to 2 hours",
                    "severity": "high"
                }
            ],
            "medium": [],
            "low": []
        }
        result = suggest_modifications(issues)
        assert len(result) >= 2


class TestSuggestForIssue:
    """Test the _suggest_for_issue helper function."""

    def test_missing_description_generates_update(self):
        """Test that missing description issues generate update_node_field."""
        issue = {
            "title": "task-1-1 missing description",
            "description": "Needs more context",
            "fix": "Add description",
            "severity": "critical"
        }
        result = _suggest_for_issue(issue, severity="critical")
        assert len(result) == 1
        assert result[0]["operation"] == "update_node_field"
        assert result[0]["node_id"] == "task-1-1"
        assert result[0]["field"] == "description"

    def test_unclear_description_generates_update(self):
        """Test that unclear description issues generate update_node_field."""
        issue = {
            "title": "task-2-3 unclear requirements",
            "description": "Not enough detail",
            "fix": "Clarify requirements",
            "severity": "high"
        }
        result = _suggest_for_issue(issue, severity="high")
        assert len(result) == 1
        assert result[0]["node_id"] == "task-2-3"

    def test_missing_dependency_generates_update(self):
        """Test that missing dependency issues generate appropriate modification."""
        issue = {
            "title": "task-3-1 missing dependency on task-2-1",
            "description": "Should depend on task-2-1",
            "fix": "Add dependency to task-2-1",
            "severity": "critical"
        }
        result = _suggest_for_issue(issue, severity="critical")
        assert len(result) == 1
        assert result[0]["node_id"] == "task-3-1"
        assert "task-2-1" in result[0]["value"]

    def test_incorrect_estimate_generates_metadata_update(self):
        """Test that estimate issues generate metadata update."""
        issue = {
            "title": "task-1-2 estimate too low",
            "description": "Current estimate is 1 hour",
            "fix": "Should be 3 hours based on complexity",
            "severity": "medium"
        }
        result = _suggest_for_issue(issue, severity="medium")
        assert len(result) == 1
        assert result[0]["operation"] == "update_node_field"
        assert result[0]["field"] == "metadata"
        assert result[0]["value"]["estimated_hours"] == 3.0

    def test_missing_verification_generates_add_node(self):
        """Test that missing verification issues generate add_node."""
        issue = {
            "title": "task-1-1 missing verification steps",
            "description": "No tests defined",
            "fix": "Add unit tests for authentication",
            "severity": "high"
        }
        result = _suggest_for_issue(issue, severity="high")
        assert len(result) == 1
        assert result[0]["operation"] == "add_node"
        assert result[0]["node_data"]["type"] == "verify"
        assert "task-1-1" in result[0]["node_data"]["node_id"]

    def test_missing_task_generates_add_node(self):
        """Test that missing task issues generate add_node."""
        issue = {
            "title": "should include error handling task",
            "description": "Error handling not covered",
            "fix": "Add task for error handling in phase-2",
            "severity": "high"
        }
        result = _suggest_for_issue(issue, severity="high")
        assert len(result) == 1
        assert result[0]["operation"] == "add_node"
        assert result[0]["parent_id"] == "phase-2"
        assert result[0]["node_data"]["type"] == "task"

    def test_task_ordering_generates_note(self):
        """Test that task ordering issues generate description note."""
        issue = {
            "title": "task-2-1 should be before task-2-3",
            "description": "Wrong order",
            "fix": "Move task-2-1 before task-2-3",
            "severity": "medium"
        }
        result = _suggest_for_issue(issue, severity="medium")
        assert len(result) == 1
        assert result[0]["operation"] == "update_node_field"
        assert "ORDER" in result[0]["value"]

    def test_generic_update_generates_review_note(self):
        """Test that generic update issues generate review note."""
        issue = {
            "title": "task-1-1 needs update",
            "description": "Outdated information",
            "fix": "Update task description with current info",
            "severity": "low"
        }
        result = _suggest_for_issue(issue, severity="low")
        assert len(result) == 1
        assert result[0]["operation"] == "update_node_field"
        assert "REVIEW" in result[0]["value"]

    def test_no_node_id_returns_empty_list(self):
        """Test that issues without node IDs return empty list."""
        issue = {
            "title": "general concern about architecture",
            "description": "May need refactoring",
            "fix": "Consider refactoring",
            "severity": "low"
        }
        result = _suggest_for_issue(issue, severity="low")
        assert result == []

    def test_unmatched_pattern_returns_empty_list(self):
        """Test that issues not matching any pattern return empty list."""
        issue = {
            "title": "task-1-1 random concern",
            "description": "Something else",
            "fix": "Do something",
            "severity": "low"
        }
        result = _suggest_for_issue(issue, severity="low")
        assert result == []

    def test_reason_field_includes_severity_and_title(self):
        """Test that modification reason includes severity and title."""
        issue = {
            "title": "task-1-1 unclear requirements",
            "description": "Needs clarification",
            "fix": "Clarify",
            "severity": "critical"
        }
        result = _suggest_for_issue(issue, severity="critical")
        assert len(result) == 1
        assert "Critical" in result[0]["reason"]
        assert "unclear" in result[0]["reason"].lower()


class TestIntegrationScenarios:
    """Integration tests for realistic review scenarios."""

    def test_full_review_with_multiple_issue_types(self):
        """Test a realistic review report with various issue types."""
        issues = {
            "critical": [
                {
                    "title": "task-1-1 missing description",
                    "description": "No context provided",
                    "fix": "Add detailed description",
                    "severity": "critical"
                }
            ],
            "high": [
                {
                    "title": "task-2-1 missing verification",
                    "description": "No tests",
                    "fix": "Add unit tests",
                    "severity": "high"
                },
                {
                    "title": "task-2-3 estimate too low",
                    "description": "Underestimated",
                    "fix": "Should be 4 hours",
                    "severity": "high"
                }
            ],
            "medium": [
                {
                    "title": "task-3-1 unclear",
                    "description": "Vague requirements",
                    "fix": "Clarify",
                    "severity": "medium"
                }
            ],
            "low": []
        }
        result = suggest_modifications(issues)
        assert len(result) >= 4

        # Check operations are present
        operations = {mod["operation"] for mod in result}
        assert "update_node_field" in operations
        assert "add_node" in operations

        # Check all have reasons
        for mod in result:
            assert "reason" in mod
            assert len(mod["reason"]) > 0

    def test_handles_malformed_issue_gracefully(self):
        """Test that malformed issues don't crash the function."""
        issues = {
            "critical": [
                {
                    "title": "",  # Empty title
                    "description": "",
                    "fix": "",
                    "severity": "critical"
                },
                None,  # None issue (should be skipped by get)
            ],
            "high": [],
            "medium": [],
            "low": []
        }
        # Should not raise exception
        result = suggest_modifications(issues)
        assert isinstance(result, list)
