"""
Unit tests for parse-review CLI command.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from claude_skills.sdd_spec_mod.cli import cmd_parse_review


class TestCmdParseReview:
    """Test the cmd_parse_review CLI command."""

    @pytest.fixture
    def mock_printer(self):
        """Create a mock PrettyPrinter."""
        printer = Mock()
        printer.info = Mock()
        printer.error = Mock()
        printer.success = Mock()
        printer.detail = Mock()
        printer.warning = Mock()
        printer.header = Mock()
        return printer

    @pytest.fixture
    def sample_review_result(self):
        """Create a sample review report parse result."""
        return {
            "success": True,
            "format": "markdown",
            "metadata": {
                "spec_id": "test-spec-001",
                "spec_title": "Test Specification",
                "overall_score": 7.5,
                "recommendation": "REVISE",
                "consensus_level": "Strong",
                "models_consulted": ["gemini", "codex"]
            },
            "issues": {
                "critical": [
                    {
                        "title": "task-1-1 missing description",
                        "description": "No context provided",
                        "fix": "Add description",
                        "severity": "critical"
                    }
                ],
                "high": [
                    {
                        "title": "task-2-1 estimate too low",
                        "description": "Should be 3 hours",
                        "fix": "Update to 3 hours",
                        "severity": "high"
                    }
                ],
                "medium": [],
                "low": []
            }
        }

    def test_review_file_not_found(self, mock_printer):
        """Test error when review file doesn't exist."""
        args = Mock(
            spec_id="test-spec-001",
            review="/nonexistent/review.md",
            output=None,
            show=False
        )

        with patch('claude_skills.sdd_spec_mod.cli.Path') as mock_path_cls:
            mock_path_instance = Mock()
            mock_path_instance.exists.return_value = False
            mock_path_cls.return_value = mock_path_instance

            result = cmd_parse_review(args, mock_printer)

        assert result == 1
        mock_printer.error.assert_called_with("Review report not found: /nonexistent/review.md")

    @patch('claude_skills.sdd_spec_mod.cli.parse_review_report')
    @patch('claude_skills.sdd_spec_mod.cli.Path')
    def test_parse_failure(self, mock_path_cls, mock_parse, mock_printer):
        """Test handling of parse failure."""
        # Mock file exists
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_cls.return_value = mock_path_instance

        # Mock parse failure
        mock_parse.return_value = {
            "success": False,
            "error": "Invalid format"
        }

        args = Mock(
            spec_id="test-spec-001",
            review="/fake/review.md",
            output=None,
            show=False
        )

        result = cmd_parse_review(args, mock_printer)

        assert result == 1
        mock_printer.error.assert_called()

    @patch('claude_skills.sdd_spec_mod.cli.parse_review_report')
    @patch('claude_skills.sdd_spec_mod.cli.suggest_modifications')
    @patch('claude_skills.sdd_spec_mod.cli.Path')
    def test_show_mode(self, mock_path_cls, mock_suggest, mock_parse, mock_printer, sample_review_result):
        """Test displaying suggestions without saving."""
        # Mock file exists
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_cls.return_value = mock_path_instance

        mock_parse.return_value = sample_review_result

        # Mock suggestions
        suggestions = [
            {
                "operation": "update_node_field",
                "node_id": "task-1-1",
                "field": "description",
                "value": "Updated",
                "reason": "Critical: missing description"
            }
        ]
        mock_suggest.return_value = suggestions

        args = Mock(
            spec_id="test-spec-001",
            review="/fake/review.md",
            output=None,
            show=True
        )

        result = cmd_parse_review(args, mock_printer)

        assert result == 0
        mock_printer.success.assert_called()
        # Verify suggestions were displayed
        assert mock_printer.header.called
        assert mock_printer.detail.called

    @patch('claude_skills.sdd_spec_mod.cli.parse_review_report')
    @patch('claude_skills.sdd_spec_mod.cli.suggest_modifications')
    @patch('claude_skills.sdd_spec_mod.cli.Path')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_suggestions(self, mock_file, mock_path_cls, mock_suggest, mock_parse, mock_printer, sample_review_result):
        """Test saving suggestions to file."""
        # Mock file exists
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.with_suffix.return_value = Path("/fake/review.suggestions.json")
        mock_path_cls.return_value = mock_path_instance

        mock_parse.return_value = sample_review_result

        # Mock suggestions
        suggestions = [
            {
                "operation": "update_node_field",
                "node_id": "task-1-1",
                "field": "description",
                "value": "Updated",
                "reason": "Critical: missing description"
            }
        ]
        mock_suggest.return_value = suggestions

        args = Mock(
            spec_id="test-spec-001",
            review="/fake/review.md",
            output=None,
            show=False
        )

        result = cmd_parse_review(args, mock_printer)

        assert result == 0
        mock_printer.success.assert_called()
        # Verify file was written
        mock_file.assert_called()

    @patch('claude_skills.sdd_spec_mod.cli.parse_review_report')
    @patch('claude_skills.sdd_spec_mod.cli.suggest_modifications')
    @patch('claude_skills.sdd_spec_mod.cli.Path')
    @patch('builtins.open', new_callable=mock_open)
    def test_custom_output_path(self, mock_file, mock_path_cls, mock_suggest, mock_parse, mock_printer, sample_review_result):
        """Test saving suggestions to custom output path."""
        # Mock file exists
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_cls.return_value = mock_path_instance

        mock_parse.return_value = sample_review_result
        mock_suggest.return_value = []

        args = Mock(
            spec_id="test-spec-001",
            review="/fake/review.md",
            output="/custom/output.json",
            show=False
        )

        result = cmd_parse_review(args, mock_printer)

        assert result == 0
        # Verify custom path was used
        mock_path_cls.assert_any_call("/custom/output.json")

    @patch('claude_skills.sdd_spec_mod.cli.parse_review_report')
    @patch('claude_skills.sdd_spec_mod.cli.suggest_modifications')
    @patch('claude_skills.sdd_spec_mod.cli.Path')
    def test_no_suggestions(self, mock_path_cls, mock_suggest, mock_parse, mock_printer, sample_review_result):
        """Test handling when no suggestions are generated."""
        # Mock file exists
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_cls.return_value = mock_path_instance

        # Return empty issues
        empty_result = sample_review_result.copy()
        empty_result["issues"] = {"critical": [], "high": [], "medium": [], "low": []}
        mock_parse.return_value = empty_result

        mock_suggest.return_value = []

        args = Mock(
            spec_id="test-spec-001",
            review="/fake/review.md",
            output=None,
            show=True
        )

        result = cmd_parse_review(args, mock_printer)

        assert result == 0
        # Should show "No modifications suggested"
        assert any("No modifications" in str(call) or "0 suggestion" in str(call)
                   for call in mock_printer.info.call_args_list + mock_printer.success.call_args_list)

    @patch('claude_skills.sdd_spec_mod.cli.parse_review_report')
    @patch('claude_skills.sdd_spec_mod.cli.suggest_modifications')
    @patch('claude_skills.sdd_spec_mod.cli.Path')
    def test_displays_metadata(self, mock_path_cls, mock_suggest, mock_parse, mock_printer, sample_review_result):
        """Test that metadata is displayed correctly."""
        # Mock file exists
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_cls.return_value = mock_path_instance

        mock_parse.return_value = sample_review_result
        mock_suggest.return_value = []

        args = Mock(
            spec_id="test-spec-001",
            review="/fake/review.md",
            output=None,
            show=True
        )

        result = cmd_parse_review(args, mock_printer)

        assert result == 0
        # Verify metadata was displayed
        assert any("7.5" in str(call) for call in mock_printer.detail.call_args_list)
        assert any("REVISE" in str(call) for call in mock_printer.warning.call_args_list)

    @patch('claude_skills.sdd_spec_mod.cli.parse_review_report')
    @patch('claude_skills.sdd_spec_mod.cli.suggest_modifications')
    @patch('claude_skills.sdd_spec_mod.cli.Path')
    def test_displays_issues_summary(self, mock_path_cls, mock_suggest, mock_parse, mock_printer, sample_review_result):
        """Test that issues summary is displayed."""
        # Mock file exists
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_cls.return_value = mock_path_instance

        mock_parse.return_value = sample_review_result
        mock_suggest.return_value = []

        args = Mock(
            spec_id="test-spec-001",
            review="/fake/review.md",
            output=None,
            show=True
        )

        result = cmd_parse_review(args, mock_printer)

        assert result == 0
        # Verify issues were displayed
        assert any("CRITICAL" in str(call) for call in mock_printer.error.call_args_list)
        assert any("HIGH" in str(call) for call in mock_printer.warning.call_args_list)
