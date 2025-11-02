"""
Unit tests for doc integration in run-tests skill.

Tests verify that the run-tests skill properly integrates with
the documentation system (code-doc/doc-query).
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add skills/run-tests to path so we can import run_tests
skill_path = Path(__file__).parent.parent.parent / "skills" / "run-tests"
sys.path.insert(0, str(skill_path))

from run_tests import analyze_failures


class TestDocIntegration(unittest.TestCase):
    """Test suite for documentation integration in run-tests."""

    @patch('run_tests.check_doc_availability')
    def test_proactive_check_is_called(self, mock_check_doc):
        """Test that analyze_failures() calls check_doc_availability()."""
        # Arrange: Mock the doc status check to return AVAILABLE
        from claude_skills.common.doc_integration import DocStatus
        mock_check_doc.return_value = DocStatus.AVAILABLE

        # Act: Call analyze_failures with test results
        test_results = {"status": "failure", "failed_tests": 3}
        analyze_failures(test_results)

        # Assert: Verify check_doc_availability was called
        mock_check_doc.assert_called_once()

    @patch('run_tests.prompt_for_generation')
    @patch('run_tests.check_doc_availability')
    def test_graceful_degradation_user_declines(self, mock_check_doc, mock_prompt):
        """Test that workflow continues when user declines doc generation."""
        # Arrange: Mock doc status as MISSING and user declines
        from claude_skills.common.doc_integration import DocStatus
        mock_check_doc.return_value = DocStatus.MISSING
        mock_prompt.return_value = False  # User declines

        # Act: Call analyze_failures with test results
        test_results = {"status": "failure", "failed_tests": 3}
        result = analyze_failures(test_results)

        # Assert: Function completes and returns result despite user declining
        self.assertIsNotNone(result)
        self.assertIn("doc_status", result)
        self.assertEqual(result["doc_status"], "missing")
        mock_prompt.assert_called_once()

    @patch('run_tests.prompt_for_generation')
    @patch('run_tests.check_doc_availability')
    def test_graceful_degradation_docs_unavailable(self, mock_check_doc, mock_prompt):
        """Test that workflow continues when documentation is unavailable."""
        # Arrange: Mock doc status as MISSING, user accepts but docs unavailable
        from claude_skills.common.doc_integration import DocStatus
        mock_check_doc.return_value = DocStatus.MISSING
        mock_prompt.return_value = True  # User accepts (but we continue anyway)

        # Act: Call analyze_failures with test results
        test_results = {"status": "failure", "failed_tests": 2}
        result = analyze_failures(test_results)

        # Assert: Function completes gracefully despite docs being unavailable
        self.assertIsNotNone(result)
        self.assertIn("analysis", result)

    @patch('run_tests.prompt_for_generation')
    @patch('run_tests.check_doc_availability')
    def test_graceful_degradation_docs_stale(self, mock_check_doc, mock_prompt):
        """Test that workflow continues when documentation is stale."""
        # Arrange: Mock doc status as STALE
        from claude_skills.common.doc_integration import DocStatus
        mock_check_doc.return_value = DocStatus.STALE
        mock_prompt.return_value = False  # User declines to regenerate

        # Act: Call analyze_failures with test results
        test_results = {"status": "failure", "failed_tests": 5}
        result = analyze_failures(test_results)

        # Assert: Function continues with stale docs rather than failing
        self.assertIsNotNone(result)
        self.assertEqual(result["doc_status"], "stale")


if __name__ == '__main__':
    unittest.main()
