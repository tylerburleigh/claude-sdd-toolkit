"""
Unit tests for sdd_common.doc_helper module.

Tests documentation integration functions: check_doc_query_available,
check_sdd_integration_available, get_task_context_from_docs,
should_generate_docs, and ensure_documentation_exists.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
import subprocess
from claude_skills.common.doc_helper import (
    check_doc_query_available,
    check_sdd_integration_available,
    get_task_context_from_docs,
    should_generate_docs,
    ensure_documentation_exists,
)


class TestCheckDocQueryAvailable:
    """Tests for check_doc_query_available function."""

    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_doc_query_available(self, mock_run):
        """Test when doc-query is available and working."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Documentation location: /path/to/docs\nClasses: 50\nFunctions: 120\n"
        )

        result = check_doc_query_available()

        assert result["available"] is True
        assert result["message"] == "Documentation available"
        assert result["location"] == "/path/to/docs"
        assert result["stats"] is not None
        assert result["stats"]["Classes"] == 50

    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_doc_query_not_found(self, mock_run):
        """Test when doc-query returns error."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="Error")

        result = check_doc_query_available()

        assert result["available"] is False
        assert "not found" in result["message"]
        assert result["location"] is None

    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_doc_query_command_not_found(self, mock_run):
        """Test when doc-query command doesn't exist."""
        mock_run.side_effect = FileNotFoundError()

        result = check_doc_query_available()

        assert result["available"] is False
        assert "not found in PATH" in result["message"]

    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_doc_query_timeout(self, mock_run):
        """Test when doc-query command times out."""
        mock_run.side_effect = subprocess.TimeoutExpired("doc-query", 5)

        result = check_doc_query_available()

        assert result["available"] is False
        assert "timed out" in result["message"]


class TestCheckSddIntegrationAvailable:
    """Tests for check_sdd_integration_available function."""

    @patch("claude_skills.common.doc_helper.shutil.which")
    def test_sdd_integration_available(self, mock_which):
        """Test when sdd-integration command is available."""
        mock_which.return_value = "/usr/local/bin/sdd-integration"

        result = check_sdd_integration_available()

        assert result is True
        mock_which.assert_called_once_with("sdd-integration")

    @patch("claude_skills.common.doc_helper.shutil.which")
    def test_sdd_integration_not_available(self, mock_which):
        """Test when sdd-integration command is not available."""
        mock_which.return_value = None

        result = check_sdd_integration_available()

        assert result is False


class TestGetTaskContextFromDocs:
    """Tests for get_task_context_from_docs function."""

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_get_context_success(self, mock_run, mock_check):
        """Test successful context retrieval."""
        mock_check.return_value = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"files": ["app/auth.py"], "dependencies": ["jwt"], "similar": [], "complexity": {}}'
        )

        result = get_task_context_from_docs("implement auth")

        assert result is not None
        assert "files" in result
        assert result["files"] == ["app/auth.py"]
        assert result["dependencies"] == ["jwt"]

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    def test_get_context_tool_unavailable(self, mock_check):
        """Test when sdd-integration is not available."""
        mock_check.return_value = False

        result = get_task_context_from_docs("implement auth")

        assert result is None

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_get_context_command_failed(self, mock_run, mock_check):
        """Test when command fails."""
        mock_check.return_value = True
        mock_run.return_value = Mock(returncode=1, stdout="")

        result = get_task_context_from_docs("implement auth")

        assert result is None

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_get_context_timeout(self, mock_run, mock_check):
        """Test when command times out."""
        mock_check.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("sdd-integration", 30)

        result = get_task_context_from_docs("implement auth")

        assert result is None

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_get_context_invalid_json(self, mock_run, mock_check):
        """Test when output is not valid JSON."""
        mock_check.return_value = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Not valid JSON"
        )

        result = get_task_context_from_docs("implement auth")

        assert result is not None
        assert "raw_output" in result
        assert result["raw_output"] == "Not valid JSON"


class TestShouldGenerateDocs:
    """Tests for should_generate_docs function."""

    @patch("claude_skills.common.doc_helper.check_doc_query_available")
    def test_should_not_generate_if_available(self, mock_check):
        """Test recommendation when docs are already available."""
        mock_check.return_value = {"available": True}

        result = should_generate_docs()

        assert result["should_generate"] is False
        assert result["available"] is True
        assert "already available" in result["reason"]

    @patch("claude_skills.common.doc_helper.check_doc_query_available")
    def test_should_generate_if_missing(self, mock_check):
        """Test recommendation when docs are missing."""
        mock_check.return_value = {"available": False}

        result = should_generate_docs()

        assert result["should_generate"] is True
        assert result["available"] is False
        assert "recommended" in result["reason"]

    @patch("claude_skills.common.doc_helper.check_doc_query_available")
    def test_interactive_mode(self, mock_check):
        """Test interactive mode (prompting)."""
        mock_check.return_value = {"available": False}

        result = should_generate_docs(interactive=True)

        assert result["should_generate"] is True
        # user_confirmed should be None (not actually prompted in this implementation)
        assert result["user_confirmed"] is None


class TestEnsureDocumentationExists:
    """Tests for ensure_documentation_exists function."""

    @patch("claude_skills.common.doc_helper.check_doc_query_available")
    def test_fast_path_docs_exist(self, mock_check):
        """Test fast path when docs already exist."""
        mock_check.return_value = {
            "available": True,
            "location": "/path/to/docs"
        }

        success, message = ensure_documentation_exists()

        assert success is True
        assert message == "/path/to/docs"

    @patch("claude_skills.common.doc_helper.should_generate_docs")
    @patch("claude_skills.common.doc_helper.check_doc_query_available")
    def test_docs_missing_no_generation(self, mock_check, mock_should):
        """Test when docs are missing and generation not recommended."""
        mock_check.return_value = {"available": False}
        mock_should.return_value = {
            "should_generate": False,
            "reason": "Not recommended"
        }

        success, message = ensure_documentation_exists(auto_generate=False, prompt_user=False)

        assert success is False
        assert "not available" in message.lower()

    @patch("claude_skills.common.doc_helper.subprocess.run")
    @patch("claude_skills.common.doc_helper.should_generate_docs")
    @patch("claude_skills.common.doc_helper.check_doc_query_available")
    def test_auto_generate_success(self, mock_check, mock_should, mock_run):
        """Test successful auto-generation."""
        # First call: docs not available
        # Second call: docs available after generation
        mock_check.side_effect = [
            {"available": False},
            {"available": True, "location": "/path/to/docs"}
        ]
        mock_should.return_value = {"should_generate": True}
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")

        success, message = ensure_documentation_exists(auto_generate=True)

        assert success is True
        assert message == "/path/to/docs"
        mock_run.assert_called_once()

    @patch("claude_skills.common.doc_helper.subprocess.run")
    @patch("claude_skills.common.doc_helper.should_generate_docs")
    @patch("claude_skills.common.doc_helper.check_doc_query_available")
    def test_auto_generate_failure(self, mock_check, mock_should, mock_run):
        """Test failed auto-generation."""
        mock_check.return_value = {"available": False}
        mock_should.return_value = {"should_generate": True}
        mock_run.return_value = Mock(returncode=1, stderr="Generation error")

        success, message = ensure_documentation_exists(auto_generate=True)

        assert success is False
        assert "failed" in message.lower()

    @patch("claude_skills.common.doc_helper.subprocess.run")
    @patch("claude_skills.common.doc_helper.should_generate_docs")
    @patch("claude_skills.common.doc_helper.check_doc_query_available")
    def test_auto_generate_timeout(self, mock_check, mock_should, mock_run):
        """Test auto-generation timeout."""
        mock_check.return_value = {"available": False}
        mock_should.return_value = {"should_generate": True}
        mock_run.side_effect = subprocess.TimeoutExpired("code-doc", 300)

        success, message = ensure_documentation_exists(auto_generate=True)

        assert success is False
        assert "timed out" in message.lower()

    @patch("claude_skills.common.doc_helper.should_generate_docs")
    @patch("claude_skills.common.doc_helper.check_doc_query_available")
    def test_prompt_user_mode(self, mock_check, mock_should):
        """Test prompt user mode (returns recommendation)."""
        mock_check.return_value = {"available": False}
        mock_should.return_value = {"should_generate": True}

        success, message = ensure_documentation_exists(prompt_user=True, auto_generate=False)

        assert success is False
        assert "recommend" in message.lower()
