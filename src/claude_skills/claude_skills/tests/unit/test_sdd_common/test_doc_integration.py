"""
Unit tests for sdd_common.doc_integration module.

Tests the DocStatus enum, check_doc_availability() function, and caching behavior.
"""

import pytest
from unittest.mock import patch, Mock
import subprocess
import json
from datetime import datetime, timezone, timedelta
from claude_skills.common.doc_integration import (
    DocStatus,
    check_doc_availability,
    clear_doc_status_cache,
    _determine_status_from_stats,
    prompt_for_generation,
    _build_generation_prompt,
    get_staleness_threshold,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the cache before each test."""
    clear_doc_status_cache()
    yield
    clear_doc_status_cache()


class TestDocStatus:
    """Tests for DocStatus enum."""

    def test_enum_values(self):
        """Test that all expected enum values exist."""
        assert DocStatus.AVAILABLE.value == "available"
        assert DocStatus.MISSING.value == "missing"
        assert DocStatus.STALE.value == "stale"
        assert DocStatus.ERROR.value == "error"

    def test_enum_comparison(self):
        """Test that enum values can be compared."""
        assert DocStatus.AVAILABLE == DocStatus.AVAILABLE
        assert DocStatus.AVAILABLE != DocStatus.MISSING


class TestCheckDocAvailability:
    """Tests for check_doc_availability function."""

    @patch("claude_skills.common.doc_integration.subprocess.run")
    def test_available_success(self, mock_run):
        """Test when documentation is available and current."""
        # Use a recent timestamp (within 7 days)
        recent_date = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        stats = {
            "generated_at": recent_date,
            "statistics": {
                "total_files": 50,
                "total_classes": 100
            }
        }
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(stats)
        )

        result = check_doc_availability()

        assert result == DocStatus.AVAILABLE
        mock_run.assert_called_once_with(
            ["sdd", "doc", "stats", "--json"],
            capture_output=True,
            text=True,
            timeout=5
        )

    @patch("claude_skills.common.doc_integration.subprocess.run")
    def test_missing_returncode_1(self, mock_run):
        """Test when documentation is missing (returncode 1)."""
        mock_run.return_value = Mock(
            returncode=1,
            stdout=""
        )

        result = check_doc_availability()

        assert result == DocStatus.MISSING

    @patch("claude_skills.common.doc_integration.subprocess.run")
    def test_error_other_returncode(self, mock_run):
        """Test when command returns non-0/1 exit code."""
        mock_run.return_value = Mock(
            returncode=2,
            stdout="",
            stderr="Unknown error"
        )

        result = check_doc_availability()

        assert result == DocStatus.ERROR

    @patch("claude_skills.common.doc_integration.subprocess.run")
    def test_error_command_not_found(self, mock_run):
        """Test when sdd command is not found."""
        mock_run.side_effect = FileNotFoundError()

        result = check_doc_availability()

        assert result == DocStatus.ERROR

    @patch("claude_skills.common.doc_integration.subprocess.run")
    def test_error_timeout(self, mock_run):
        """Test when command times out."""
        mock_run.side_effect = subprocess.TimeoutExpired("sdd", 5)

        result = check_doc_availability()

        assert result == DocStatus.ERROR

    @patch("claude_skills.common.doc_integration.subprocess.run")
    def test_error_invalid_json(self, mock_run):
        """Test when command returns invalid JSON."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="Not valid JSON output"
        )

        result = check_doc_availability()

        assert result == DocStatus.ERROR

    @patch("claude_skills.common.doc_integration.subprocess.run")
    def test_error_unexpected_exception(self, mock_run):
        """Test when an unexpected exception occurs."""
        mock_run.side_effect = RuntimeError("Unexpected error")

        result = check_doc_availability()

        assert result == DocStatus.ERROR

    @patch("claude_skills.common.doc_integration.subprocess.run")
    def test_stale_with_staleness_field(self, mock_run):
        """Test when documentation is stale (using staleness field)."""
        stats = {
            "generated_at": "2025-01-01T12:00:00Z",
            "staleness": {
                "is_stale": True,
                "reason": "Source files modified"
            }
        }
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(stats)
        )

        result = check_doc_availability()

        assert result == DocStatus.STALE

    @patch("claude_skills.common.doc_integration.subprocess.run")
    def test_stale_by_age(self, mock_run):
        """Test when documentation is stale based on age (>7 days)."""
        old_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        stats = {
            "generated_at": old_date,
            "statistics": {"total_files": 50}
        }
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(stats)
        )

        result = check_doc_availability()

        assert result == DocStatus.STALE

    @patch("claude_skills.common.doc_integration.subprocess.run")
    def test_available_recent_docs(self, mock_run):
        """Test when documentation is recent (within 7 days)."""
        recent_date = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        stats = {
            "generated_at": recent_date,
            "statistics": {"total_files": 50}
        }
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(stats)
        )

        result = check_doc_availability()

        assert result == DocStatus.AVAILABLE


class TestCaching:
    """Tests for caching behavior."""

    @patch("claude_skills.common.doc_integration.subprocess.run")
    def test_caching_works(self, mock_run):
        """Test that results are cached and subprocess is only called once."""
        # Use a recent timestamp (within 7 days)
        recent_date = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        stats = {"generated_at": recent_date}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(stats)
        )

        # First call - should invoke subprocess
        result1 = check_doc_availability()
        assert result1 == DocStatus.AVAILABLE
        assert mock_run.call_count == 1

        # Second call - should use cache
        result2 = check_doc_availability()
        assert result2 == DocStatus.AVAILABLE
        assert mock_run.call_count == 1  # Still only called once

    @patch("claude_skills.common.doc_integration.subprocess.run")
    def test_force_refresh_bypasses_cache(self, mock_run):
        """Test that force_refresh=True bypasses the cache."""
        # Use a recent timestamp (within 7 days)
        recent_date = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        stats = {"generated_at": recent_date}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(stats)
        )

        # First call
        result1 = check_doc_availability()
        assert result1 == DocStatus.AVAILABLE
        assert mock_run.call_count == 1

        # Second call with force_refresh - should call subprocess again
        result2 = check_doc_availability(force_refresh=True)
        assert result2 == DocStatus.AVAILABLE
        assert mock_run.call_count == 2  # Called twice

    @patch("claude_skills.common.doc_integration.subprocess.run")
    def test_clear_cache_function(self, mock_run):
        """Test that clear_doc_status_cache() clears the cache."""
        # Use a recent timestamp (within 7 days)
        recent_date = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        stats = {"generated_at": recent_date}
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(stats)
        )

        # First call
        result1 = check_doc_availability()
        assert result1 == DocStatus.AVAILABLE
        assert mock_run.call_count == 1

        # Clear cache
        clear_doc_status_cache()

        # Second call - should invoke subprocess again
        result2 = check_doc_availability()
        assert result2 == DocStatus.AVAILABLE
        assert mock_run.call_count == 2  # Called twice


class TestDetermineStatusFromStats:
    """Tests for _determine_status_from_stats helper function."""

    def test_available_with_staleness_false(self):
        """Test when staleness info indicates docs are current."""
        stats = {
            "staleness": {"is_stale": False},
            "generated_at": "2025-01-15T12:00:00Z"
        }
        result = _determine_status_from_stats(stats)
        assert result == DocStatus.AVAILABLE

    def test_stale_with_staleness_true(self):
        """Test when staleness info indicates docs are stale."""
        stats = {
            "staleness": {"is_stale": True},
            "generated_at": "2025-01-15T12:00:00Z"
        }
        result = _determine_status_from_stats(stats)
        assert result == DocStatus.STALE

    def test_available_no_generated_at(self):
        """Test when no generated_at timestamp is present."""
        stats = {"statistics": {"total_files": 50}}
        result = _determine_status_from_stats(stats)
        assert result == DocStatus.AVAILABLE

    def test_available_invalid_timestamp(self):
        """Test when timestamp cannot be parsed."""
        stats = {"generated_at": "invalid-timestamp"}
        result = _determine_status_from_stats(stats)
        # Should default to AVAILABLE when can't determine staleness
        assert result == DocStatus.AVAILABLE

    def test_stale_old_timestamp(self):
        """Test when timestamp is very old (>7 days)."""
        old_date = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
        stats = {"generated_at": old_date}
        result = _determine_status_from_stats(stats)
        assert result == DocStatus.STALE

    def test_available_recent_timestamp(self):
        """Test when timestamp is recent (<7 days)."""
        recent_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        stats = {"generated_at": recent_date}
        result = _determine_status_from_stats(stats)
        assert result == DocStatus.AVAILABLE

    @patch("claude_skills.common.doc_integration.get_current_git_commit")
    @patch("claude_skills.common.doc_integration.count_commits_between")
    @patch("claude_skills.common.doc_integration.get_staleness_threshold")
    def test_git_based_staleness_exceeds_threshold(self, mock_threshold, mock_count, mock_current):
        """Test when commits since generation exceed threshold (should be STALE)."""
        mock_current.return_value = "current_commit_sha"
        mock_count.return_value = 15  # More than threshold
        mock_threshold.return_value = 10

        stats = {
            "metadata": {
                "generated_at_commit": "old_commit_sha",
                "generated_at": "2025-01-15T12:00:00Z"
            }
        }
        result = _determine_status_from_stats(stats)

        assert result == DocStatus.STALE
        mock_count.assert_called_once_with("old_commit_sha", "current_commit_sha")

    @patch("claude_skills.common.doc_integration.get_current_git_commit")
    @patch("claude_skills.common.doc_integration.count_commits_between")
    @patch("claude_skills.common.doc_integration.get_staleness_threshold")
    def test_git_based_staleness_within_threshold(self, mock_threshold, mock_count, mock_current):
        """Test when commits since generation are within threshold (should be AVAILABLE)."""
        mock_current.return_value = "current_commit_sha"
        mock_count.return_value = 5  # Less than threshold
        mock_threshold.return_value = 10

        stats = {
            "metadata": {
                "generated_at_commit": "old_commit_sha",
                "generated_at": "2025-01-15T12:00:00Z"
            }
        }
        result = _determine_status_from_stats(stats)

        assert result == DocStatus.AVAILABLE

    @patch("claude_skills.common.doc_integration.get_current_git_commit")
    def test_git_based_same_commit(self, mock_current):
        """Test when current commit matches generation commit (should be AVAILABLE)."""
        mock_current.return_value = "same_commit_sha"

        stats = {
            "metadata": {
                "generated_at_commit": "same_commit_sha",
                "generated_at": "2025-01-15T12:00:00Z"
            }
        }
        result = _determine_status_from_stats(stats)

        assert result == DocStatus.AVAILABLE

    @patch("claude_skills.common.doc_integration.get_current_git_commit")
    def test_fallback_to_time_when_no_git_metadata(self, mock_current):
        """Test fallback to time-based staleness when no git metadata present."""
        mock_current.return_value = "current_commit_sha"

        # Old timestamp but no generated_at_commit
        old_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
        stats = {
            "metadata": {},
            "generated_at": old_date
        }
        result = _determine_status_from_stats(stats)

        assert result == DocStatus.STALE

    @patch("claude_skills.common.doc_integration.get_current_git_commit")
    def test_fallback_when_current_commit_unavailable(self, mock_current):
        """Test when generated_at_commit exists but can't get current commit."""
        mock_current.return_value = None  # Can't get current commit

        stats = {
            "metadata": {
                "generated_at_commit": "old_commit_sha",
                "generated_at": "2025-01-15T12:00:00Z"
            }
        }
        result = _determine_status_from_stats(stats)

        # Should treat as available when we can't determine staleness
        assert result == DocStatus.AVAILABLE


class TestStalenessThreshold:
    """Tests for get_staleness_threshold configuration."""

    def test_default_threshold(self):
        """Test that default threshold is 10 when env var not set."""
        with patch.dict('os.environ', {}, clear=True):
            threshold = get_staleness_threshold()
            assert threshold == 10

    def test_custom_threshold_from_env(self):
        """Test that threshold can be configured via environment variable."""
        with patch.dict('os.environ', {'SDD_STALENESS_COMMIT_THRESHOLD': '20'}):
            threshold = get_staleness_threshold()
            assert threshold == 20

    def test_invalid_threshold_uses_default(self):
        """Test that invalid env var value falls back to default."""
        with patch.dict('os.environ', {'SDD_STALENESS_COMMIT_THRESHOLD': 'invalid'}):
            threshold = get_staleness_threshold()
            assert threshold == 10


class TestPromptForGeneration:
    """Tests for prompt_for_generation function."""

    @patch("claude_skills.common.doc_integration.input")
    def test_prompt_returns_true_for_yes(self, mock_input):
        """Test that 'yes' returns True."""
        mock_input.return_value = "yes"
        result = prompt_for_generation()
        assert result is True

    @patch("claude_skills.common.doc_integration.input")
    def test_prompt_returns_true_for_y(self, mock_input):
        """Test that 'y' returns True."""
        mock_input.return_value = "y"
        result = prompt_for_generation()
        assert result is True

    @patch("claude_skills.common.doc_integration.input")
    def test_prompt_returns_true_for_empty(self, mock_input):
        """Test that empty input (Enter) returns True (default)."""
        mock_input.return_value = ""
        result = prompt_for_generation()
        assert result is True

    @patch("claude_skills.common.doc_integration.input")
    def test_prompt_returns_false_for_no(self, mock_input):
        """Test that 'no' returns False."""
        mock_input.return_value = "no"
        result = prompt_for_generation()
        assert result is False

    @patch("claude_skills.common.doc_integration.input")
    def test_prompt_returns_false_for_n(self, mock_input):
        """Test that 'n' returns False."""
        mock_input.return_value = "n"
        result = prompt_for_generation()
        assert result is False

    @patch("claude_skills.common.doc_integration.input")
    @patch("builtins.print")
    def test_prompt_returns_false_for_invalid(self, mock_print, mock_input):
        """Test that invalid input returns False."""
        mock_input.return_value = "maybe"
        result = prompt_for_generation()
        assert result is False
        # Should print error message
        mock_print.assert_called_with("Invalid input. Treating as 'no'.")

    @patch("claude_skills.common.doc_integration.input")
    @patch("builtins.print")
    def test_prompt_keyboard_interrupt(self, mock_print, mock_input):
        """Test that KeyboardInterrupt (Ctrl+C) returns False."""
        mock_input.side_effect = KeyboardInterrupt()
        result = prompt_for_generation()
        assert result is False
        # Should print cancellation message
        mock_print.assert_called_with("\nPrompt cancelled.")

    @patch("claude_skills.common.doc_integration.input")
    @patch("builtins.print")
    def test_prompt_eof_error(self, mock_print, mock_input):
        """Test that EOFError (Ctrl+D) returns False."""
        mock_input.side_effect = EOFError()
        result = prompt_for_generation()
        assert result is False
        # Should print EOF message
        mock_print.assert_called_with("\nEnd of input reached. Treating as 'no'.")

    @patch("claude_skills.common.doc_integration.input")
    @patch("claude_skills.common.doc_integration._build_generation_prompt")
    def test_prompt_with_skill_name(self, mock_build, mock_input):
        """Test that skill_name is passed to prompt builder."""
        mock_build.return_value = "Test prompt: "
        mock_input.return_value = "y"

        result = prompt_for_generation(skill_name="sdd-plan")

        assert result is True
        mock_build.assert_called_once_with("sdd-plan", None)

    @patch("claude_skills.common.doc_integration.input")
    @patch("claude_skills.common.doc_integration._build_generation_prompt")
    def test_prompt_with_context(self, mock_build, mock_input):
        """Test that context is passed to prompt builder."""
        mock_build.return_value = "Test prompt: "
        mock_input.return_value = "y"

        result = prompt_for_generation(context="Task requires 15 files")

        assert result is True
        mock_build.assert_called_once_with(None, "Task requires 15 files")

    @patch("claude_skills.common.doc_integration.input")
    def test_prompt_case_insensitive(self, mock_input):
        """Test that responses are case-insensitive."""
        # Test uppercase YES
        mock_input.return_value = "YES"
        assert prompt_for_generation() is True

        # Test uppercase NO
        mock_input.return_value = "NO"
        assert prompt_for_generation() is False

        # Test mixed case
        mock_input.return_value = "Yes"
        assert prompt_for_generation() is True

    @patch("claude_skills.common.doc_integration.input")
    def test_prompt_strips_whitespace(self, mock_input):
        """Test that whitespace is stripped from input."""
        # Test with leading/trailing spaces
        mock_input.return_value = "  yes  "
        assert prompt_for_generation() is True

        mock_input.return_value = "  n  "
        assert prompt_for_generation() is False


class TestBuildGenerationPrompt:
    """Tests for _build_generation_prompt helper function."""

    def test_build_prompt_sdd_plan(self):
        """Test prompt message for sdd-plan skill."""
        result = _build_generation_prompt("sdd-plan", None)

        assert "📚 Documentation Generation Recommended" in result
        assert "automated analysis of existing code patterns and architecture" in result
        assert "Would you like to generate documentation now? [Y/n]:" in result

    def test_build_prompt_sdd_next(self):
        """Test prompt message for sdd-next skill."""
        result = _build_generation_prompt("sdd-next", None)

        assert "📚 Documentation Generation Recommended" in result
        assert "automatic file suggestions and dependency analysis for tasks" in result
        assert "Would you like to generate documentation now? [Y/n]:" in result

    def test_build_prompt_sdd_update(self):
        """Test prompt message for sdd-update skill."""
        result = _build_generation_prompt("sdd-update", None)

        assert "📚 Documentation Generation Recommended" in result
        assert "automatic verification of implementation completeness" in result
        assert "Would you like to generate documentation now? [Y/n]:" in result

    def test_build_prompt_default(self):
        """Test prompt message for unknown/default skill."""
        result = _build_generation_prompt("unknown-skill", None)

        assert "📚 Documentation Generation Recommended" in result
        assert "faster codebase analysis and intelligent suggestions" in result
        assert "Would you like to generate documentation now? [Y/n]:" in result

    def test_build_prompt_with_context(self):
        """Test that context is included in prompt."""
        context = "Task requires understanding 15 related files"
        result = _build_generation_prompt("sdd-plan", context)

        assert "Context: Task requires understanding 15 related files" in result

    def test_build_prompt_without_context(self):
        """Test that prompt works without context."""
        result = _build_generation_prompt("sdd-plan", None)

        # Should not contain "Context:" line
        assert "Context:" not in result

    def test_build_prompt_none_skill_name(self):
        """Test that None skill_name uses default message."""
        result = _build_generation_prompt(None, None)

        assert "faster codebase analysis and intelligent suggestions" in result
