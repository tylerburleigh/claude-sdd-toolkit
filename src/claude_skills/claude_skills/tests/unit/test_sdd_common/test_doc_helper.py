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
    get_call_context_from_docs,
    get_test_context_from_docs,
    get_complexity_hotspots_from_docs,
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


class TestGetCallContextFromDocs:
    """Tests for get_call_context_from_docs function."""

    def test_call_context_requires_params(self):
        """Test that ValueError is raised when neither param is provided."""
        with pytest.raises(ValueError) as exc_info:
            get_call_context_from_docs()

        assert "Either function_name or file_path must be provided" in str(exc_info.value)

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    def test_call_context_tool_unavailable(self, mock_check):
        """Test when sdd-integration is not available."""
        mock_check.return_value = False

        result = get_call_context_from_docs(function_name="test_func")

        assert result is None

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_call_context_with_function_name(self, mock_run, mock_check):
        """Test successful call context retrieval with function_name."""
        mock_check.return_value = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"function_name": "test_func", "file_path": null, "callers": [{"name": "caller1", "file": "a.py", "line": 10}], "callees": [{"name": "callee1", "file": "b.py", "line": 20}], "functions_found": ["test_func"]}'
        )

        result = get_call_context_from_docs(function_name="test_func")

        assert result is not None
        assert result["function_name"] == "test_func"
        assert len(result["callers"]) == 1
        assert result["callers"][0]["name"] == "caller1"
        assert len(result["callees"]) == 1
        assert result["callees"][0]["name"] == "callee1"

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_call_context_with_file_path(self, mock_run, mock_check):
        """Test successful call context retrieval with file_path."""
        mock_check.return_value = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"function_name": null, "file_path": "src/app.py", "callers": [], "callees": [], "functions_found": ["func1", "func2"]}'
        )

        result = get_call_context_from_docs(file_path="src/app.py")

        assert result is not None
        assert result["file_path"] == "src/app.py"
        assert result["functions_found"] == ["func1", "func2"]

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_call_context_command_failed(self, mock_run, mock_check):
        """Test when command fails."""
        mock_check.return_value = True
        mock_run.return_value = Mock(returncode=1, stdout="")

        result = get_call_context_from_docs(function_name="test_func")

        assert result is None

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_call_context_timeout(self, mock_run, mock_check):
        """Test when command times out."""
        mock_check.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("sdd-integration", 30)

        result = get_call_context_from_docs(function_name="test_func")

        assert result is None

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_call_context_invalid_json(self, mock_run, mock_check):
        """Test when output is not valid JSON."""
        mock_check.return_value = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Not valid JSON"
        )

        result = get_call_context_from_docs(function_name="test_func")

        assert result is None


class TestGetTestContextFromDocs:
    """Tests for get_test_context_from_docs function."""

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    def test_test_context_tool_unavailable(self, mock_check):
        """Test when sdd-integration is not available."""
        mock_check.return_value = False

        result = get_test_context_from_docs("src/auth.py")

        assert result is None

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_test_context_success(self, mock_run, mock_check):
        """Test successful test context retrieval."""
        mock_check.return_value = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"module": "src/auth.py", "test_files": ["tests/test_auth.py"], "test_functions": ["test_login", "test_logout"], "test_classes": ["TestAuth"]}'
        )

        result = get_test_context_from_docs("src/auth.py")

        assert result is not None
        assert result["module"] == "src/auth.py"
        assert len(result["test_files"]) == 1
        assert result["test_files"][0] == "tests/test_auth.py"
        assert len(result["test_functions"]) == 2
        assert result["test_classes"] == ["TestAuth"]

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_test_context_command_failed(self, mock_run, mock_check):
        """Test when command fails."""
        mock_check.return_value = True
        mock_run.return_value = Mock(returncode=1, stdout="")

        result = get_test_context_from_docs("src/auth.py")

        assert result is None

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_test_context_timeout(self, mock_run, mock_check):
        """Test when command times out."""
        mock_check.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("sdd-integration", 30)

        result = get_test_context_from_docs("src/auth.py")

        assert result is None

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_test_context_invalid_json(self, mock_run, mock_check):
        """Test when output is not valid JSON."""
        mock_check.return_value = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Not valid JSON"
        )

        result = get_test_context_from_docs("src/auth.py")

        assert result is None


class TestGetComplexityHotspotsFromDocs:
    """Tests for get_complexity_hotspots_from_docs function."""

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    def test_complexity_tool_unavailable(self, mock_check):
        """Test when sdd-integration is not available."""
        mock_check.return_value = False

        result = get_complexity_hotspots_from_docs()

        assert result is None

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_complexity_success_no_filter(self, mock_run, mock_check):
        """Test successful complexity hotspots retrieval without file filter."""
        mock_check.return_value = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"file_path": null, "threshold": 5, "hotspots": [{"name": "complex_func", "complexity": 12, "line": 45, "file": "src/core.py"}], "total_count": 1}'
        )

        result = get_complexity_hotspots_from_docs()

        assert result is not None
        assert result["threshold"] == 5
        assert len(result["hotspots"]) == 1
        assert result["hotspots"][0]["name"] == "complex_func"
        assert result["hotspots"][0]["complexity"] == 12
        assert result["total_count"] == 1

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_complexity_with_file_filter(self, mock_run, mock_check):
        """Test complexity hotspots retrieval with file filter."""
        mock_check.return_value = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"file_path": "src/auth.py", "threshold": 5, "hotspots": [{"name": "validate_token", "complexity": 8, "line": 100, "file": "src/auth.py"}], "total_count": 1}'
        )

        result = get_complexity_hotspots_from_docs(file_path="src/auth.py")

        assert result is not None
        assert result["file_path"] == "src/auth.py"
        assert len(result["hotspots"]) == 1
        assert result["hotspots"][0]["name"] == "validate_token"

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_complexity_with_custom_threshold(self, mock_run, mock_check):
        """Test complexity hotspots with custom threshold."""
        mock_check.return_value = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"file_path": null, "threshold": 10, "hotspots": [], "total_count": 0}'
        )

        result = get_complexity_hotspots_from_docs(threshold=10)

        assert result is not None
        assert result["threshold"] == 10
        assert result["total_count"] == 0

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_complexity_command_failed(self, mock_run, mock_check):
        """Test when command fails."""
        mock_check.return_value = True
        mock_run.return_value = Mock(returncode=1, stdout="")

        result = get_complexity_hotspots_from_docs()

        assert result is None

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_complexity_timeout(self, mock_run, mock_check):
        """Test when command times out."""
        mock_check.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("sdd-integration", 30)

        result = get_complexity_hotspots_from_docs()

        assert result is None

    @patch("claude_skills.common.doc_helper.check_sdd_integration_available")
    @patch("claude_skills.common.doc_helper.subprocess.run")
    def test_complexity_invalid_json(self, mock_run, mock_check):
        """Test when output is not valid JSON."""
        mock_check.return_value = True
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Not valid JSON"
        )

        result = get_complexity_hotspots_from_docs()

        assert result is None
