"""
Integration tests for run-tests skill doc integration.

Tests verify end-to-end integration between run-tests skill and
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


class TestRunTestsDocIntegration(unittest.TestCase):
    """Integration test suite for run-tests doc integration."""

    @patch('run_tests.check_doc_availability')
    def test_docs_available(self, mock_check_doc):
        """
        Integration test: Verify workflow uses docs when available.

        When documentation is available, the workflow should:
        1. Check doc availability
        2. Skip prompting for generation (docs already exist)
        3. Continue with test analysis
        4. Return results successfully
        """
        # Arrange: Mock documentation as available
        from claude_skills.common.doc_integration import DocStatus
        mock_check_doc.return_value = DocStatus.AVAILABLE

        # Act: Call analyze_failures with test results
        test_results = {
            "status": "failure",
            "failed_tests": 3,
            "test_output": "AssertionError: expected 5, got 3"
        }
        result = analyze_failures(test_results)

        # Assert: Verify workflow completed successfully
        self.assertIsNotNone(result, "Function should return a result")
        self.assertIn("doc_status", result, "Result should include doc status")
        self.assertEqual(
            result["doc_status"],
            "available",
            "Doc status should be 'available'"
        )
        self.assertIn("analysis", result, "Result should include analysis")

        # Verify check_doc_availability was called
        mock_check_doc.assert_called_once()

    @patch('run_tests.prompt_for_generation')
    @patch('run_tests.check_doc_availability')
    def test_docs_missing_user_accepts(self, mock_check_doc, mock_prompt):
        """
        Integration test: Verify workflow when docs missing and user accepts.

        When documentation is missing and user accepts generation:
        1. Check doc availability (returns MISSING)
        2. Prompt user for generation
        3. User accepts (returns True)
        4. Print message about invoking code-doc skill
        5. Continue with test analysis
        """
        # Arrange: Mock documentation as missing, user accepts
        from claude_skills.common.doc_integration import DocStatus
        mock_check_doc.return_value = DocStatus.MISSING
        mock_prompt.return_value = True  # User accepts

        # Act: Call analyze_failures with test results
        test_results = {"status": "failure", "failed_tests": 2}
        result = analyze_failures(test_results)

        # Assert: Verify workflow completed
        self.assertIsNotNone(result)
        self.assertEqual(result["doc_status"], "missing")

        # Verify both functions were called
        mock_check_doc.assert_called_once()
        mock_prompt.assert_called_once()

    @patch('run_tests.prompt_for_generation')
    @patch('run_tests.check_doc_availability')
    def test_docs_missing_user_declines(self, mock_check_doc, mock_prompt):
        """
        Integration test: Verify graceful degradation when user declines.

        When documentation is missing and user declines generation:
        1. Check doc availability (returns MISSING)
        2. Prompt user for generation
        3. User declines (returns False)
        4. Print skip message
        5. Continue with test analysis using available context
        """
        # Arrange: Mock documentation as missing, user declines
        from claude_skills.common.doc_integration import DocStatus
        mock_check_doc.return_value = DocStatus.MISSING
        mock_prompt.return_value = False  # User declines

        # Act: Call analyze_failures with test results
        test_results = {"status": "failure", "failed_tests": 1}
        result = analyze_failures(test_results)

        # Assert: Verify graceful degradation
        self.assertIsNotNone(result, "Workflow should complete despite user declining")
        self.assertEqual(result["doc_status"], "missing")
        self.assertIn("analysis", result, "Analysis should still be provided")

        # Verify both functions were called
        mock_check_doc.assert_called_once()
        mock_prompt.assert_called_once()


if __name__ == '__main__':
    unittest.main()
