"""
Unit tests for doc integration in sdd-next.

Tests that prepare_task() properly integrates with documentation checking.
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from claude_skills.sdd_next.discovery import prepare_task
from claude_skills.common.doc_integration import DocStatus


class TestDocIntegration:
    """Tests for documentation integration in sdd-next."""

    def test_prepare_task_calls_check_doc_availability(self, sample_json_spec_simple, specs_structure):
        """Test that prepare_task() calls check_doc_availability() proactively."""
        with patch('claude_skills.sdd_next.discovery.check_doc_availability') as mock_check_doc:
            with patch('claude_skills.sdd_next.discovery.check_doc_query_available') as mock_check_query:
                # Setup mocks
                mock_check_doc.return_value = DocStatus.AVAILABLE
                mock_check_query.return_value = {"available": False}

                # Call prepare_task
                result = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-1")

                # Verify check_doc_availability was called
                mock_check_doc.assert_called_once()

                # Verify result is successful
                assert result.get("success") is True
                assert "task_id" in result

    def test_prepare_task_sets_flag_when_docs_missing(self, sample_json_spec_simple, specs_structure):
        """Test that prepare_task() sets doc_prompt_needed flag when docs are missing."""
        with patch('claude_skills.sdd_next.discovery.check_doc_availability') as mock_check_doc:
            with patch('claude_skills.sdd_next.discovery.check_doc_query_available') as mock_check_query:
                # Setup mocks - docs are missing
                mock_check_doc.return_value = DocStatus.MISSING
                mock_check_query.return_value = {"available": False}

                # Call prepare_task
                result = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-1")

                # Verify flags are set
                assert result.get("doc_prompt_needed") is True
                assert result.get("doc_status") == "missing"

    def test_prepare_task_sets_flag_when_docs_stale(self, sample_json_spec_simple, specs_structure):
        """Test that prepare_task() sets doc_prompt_needed flag when docs are stale."""
        with patch('claude_skills.sdd_next.discovery.check_doc_availability') as mock_check_doc:
            with patch('claude_skills.sdd_next.discovery.check_doc_query_available') as mock_check_query:
                # Setup mocks - docs are stale
                mock_check_doc.return_value = DocStatus.STALE
                mock_check_query.return_value = {"available": False}

                # Call prepare_task
                result = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-1")

                # Verify flags are set
                assert result.get("doc_prompt_needed") is True
                assert result.get("doc_status") == "stale"

    def test_prepare_task_no_flag_when_docs_available(self, sample_json_spec_simple, specs_structure):
        """Test that prepare_task() does not set flag when docs are available."""
        with patch('claude_skills.sdd_next.discovery.check_doc_availability') as mock_check_doc:
            with patch('claude_skills.sdd_next.discovery.check_doc_query_available') as mock_check_query:
                # Setup mocks - docs are available
                mock_check_doc.return_value = DocStatus.AVAILABLE
                mock_check_query.return_value = {"available": True}

                # Mock get_task_context_from_docs to avoid actual doc queries
                with patch('claude_skills.sdd_next.discovery.get_task_context_from_docs') as mock_get_context:
                    mock_get_context.return_value = None

                    # Call prepare_task
                    result = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-1")

                    # Verify flag is NOT set
                    assert result.get("doc_prompt_needed") is not True
                    assert "doc_status" not in result or result.get("doc_status") != "missing"

    def test_graceful_degradation_continues_workflow(self, sample_json_spec_simple, specs_structure):
        """Test that workflow continues with manual exploration if docs are unavailable."""
        with patch('claude_skills.sdd_next.discovery.check_doc_availability') as mock_check_doc:
            with patch('claude_skills.sdd_next.discovery.check_doc_query_available') as mock_check_query:
                # Setup mocks - docs are missing but we continue anyway
                mock_check_doc.return_value = DocStatus.MISSING
                mock_check_query.return_value = {"available": False}

                # Call prepare_task - should succeed even without docs
                result = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-1")

                # Verify workflow continues successfully
                assert result.get("success") is True
                assert "task_id" in result
                assert result["task_id"] == "task-1-1"

                # Doc prompt flag is set, but execution doesn't fail
                assert result.get("doc_prompt_needed") is True

    def test_graceful_degradation_with_error_status(self, sample_json_spec_simple, specs_structure):
        """Test that workflow continues even when doc check returns ERROR status."""
        with patch('claude_skills.sdd_next.discovery.check_doc_availability') as mock_check_doc:
            with patch('claude_skills.sdd_next.discovery.check_doc_query_available') as mock_check_query:
                # Setup mocks - doc check errors but we continue
                mock_check_doc.return_value = DocStatus.ERROR
                mock_check_query.return_value = {"available": False}

                # Call prepare_task - should succeed despite error
                result = prepare_task("simple-spec-2025-01-01-001", specs_structure, "task-1-1")

                # Verify workflow continues successfully
                assert result.get("success") is True
                assert "task_id" in result

                # Error status should not set the prompt flag
                assert result.get("doc_prompt_needed") is not True
