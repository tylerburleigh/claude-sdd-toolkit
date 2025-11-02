"""
Integration tests for sdd-plan skill doc integration.

Tests verify end-to-end integration between sdd-plan skill and
the documentation system (code-doc/doc-query).
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add skills/sdd-plan to path so we can import sdd_plan
skill_path = Path(__file__).parent.parent.parent / "skills" / "sdd-plan"
sys.path.insert(0, str(skill_path))

from sdd_plan import analyze_codebase


class TestSddPlanDocIntegration(unittest.TestCase):
    """Integration test suite for sdd-plan doc integration."""

    @patch('sdd_plan.check_doc_availability')
    def test_docs_available(self, mock_check_doc):
        """
        Integration test: Verify workflow uses docs when available.

        When documentation is available, the workflow should:
        1. Check doc availability
        2. Skip prompting for generation (docs already exist)
        3. Continue with planning analysis
        4. Return results successfully
        """
        # Arrange: Mock documentation as available
        from claude_skills.common.doc_integration import DocStatus
        mock_check_doc.return_value = DocStatus.AVAILABLE

        # Act: Call analyze_codebase
        result = analyze_codebase()

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

    @patch('sdd_plan.prompt_for_generation')
    @patch('sdd_plan.check_doc_availability')
    def test_docs_missing_user_accepts(self, mock_check_doc, mock_prompt):
        """
        Integration test: Verify workflow when docs missing and user accepts.

        When documentation is missing and user accepts generation:
        1. Check doc availability (returns MISSING)
        2. Prompt user for generation
        3. User accepts (returns True)
        4. Print message about invoking code-doc skill
        5. Continue with planning analysis
        """
        # Arrange: Mock documentation as missing, user accepts
        from claude_skills.common.doc_integration import DocStatus
        mock_check_doc.return_value = DocStatus.MISSING
        mock_prompt.return_value = True  # User accepts

        # Act: Call analyze_codebase
        result = analyze_codebase()

        # Assert: Verify workflow completed
        self.assertIsNotNone(result)
        self.assertEqual(result["doc_status"], "missing")

        # Verify both functions were called
        mock_check_doc.assert_called_once()
        mock_prompt.assert_called_once()

    @patch('sdd_plan.prompt_for_generation')
    @patch('sdd_plan.check_doc_availability')
    def test_docs_missing_user_declines(self, mock_check_doc, mock_prompt):
        """
        Integration test: Verify graceful degradation when user declines.

        When documentation is missing and user declines generation:
        1. Check doc availability (returns MISSING)
        2. Prompt user for generation
        3. User declines (returns False)
        4. Print skip message
        5. Continue with planning analysis using available context
        """
        # Arrange: Mock documentation as missing, user declines
        from claude_skills.common.doc_integration import DocStatus
        mock_check_doc.return_value = DocStatus.MISSING
        mock_prompt.return_value = False  # User declines

        # Act: Call analyze_codebase
        result = analyze_codebase()

        # Assert: Verify graceful degradation
        self.assertIsNotNone(result, "Workflow should complete despite user declining")
        self.assertEqual(result["doc_status"], "missing")
        self.assertIn("analysis", result, "Analysis should still be provided")

        # Verify both functions were called
        mock_check_doc.assert_called_once()
        mock_prompt.assert_called_once()


if __name__ == '__main__':
    unittest.main()
