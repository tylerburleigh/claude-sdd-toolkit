"""Tests for AI consultation integration."""

import pytest
from unittest.mock import Mock, patch
from claude_skills.llm_doc_gen.ai_consultation import (
    ConsultationResult,
    get_available_providers,
    consult_llm,
    consult_multi_agent,
    AIConsultationError,
)


def test_consultation_result_dataclass():
    """Test ConsultationResult dataclass."""
    result = ConsultationResult(
        success=True, output="Test output", tool_used="test-tool", duration=1.5
    )

    assert result.success is True
    assert result.output == "Test output"
    assert result.tool_used == "test-tool"
    assert result.duration == 1.5
    assert result.error is None


def test_consultation_result_with_error():
    """Test ConsultationResult with error."""
    result = ConsultationResult(success=False, output="", error="Test error")

    assert result.success is False
    assert result.output == ""
    assert result.error == "Test error"


@patch("claude_skills.common.ai_tools.get_enabled_and_available_tools")
def test_get_available_providers_with_import(mock_get_tools):
    """Test getting available providers using imported function."""
    mock_get_tools.return_value = ["cursor-agent", "gemini"]

    providers = get_available_providers()

    assert providers == ["cursor-agent", "gemini"]
    mock_get_tools.assert_called_once_with("llm-doc-gen")


def test_get_available_providers_returns_list():
    """Test that get_available_providers returns a list."""
    providers = get_available_providers()

    # Should always return a list (may be empty)
    assert isinstance(providers, list)


@patch("claude_skills.common.ai_tools.execute_tool_with_fallback")
def test_consult_llm_success(mock_execute):
    """Test successful LLM consultation."""
    # Mock successful response
    mock_response = Mock()
    mock_response.success = True
    mock_response.output = "Test response"
    mock_response.error = None
    mock_execute.return_value = mock_response

    result = consult_llm("Test prompt", provider="cursor-agent")

    assert result.success is True
    assert result.output == "Test response"
    assert result.tool_used == "cursor-agent"
    assert result.error is None
    mock_execute.assert_called_once()


@patch("claude_skills.common.ai_tools.execute_tool_with_fallback")
def test_consult_llm_failure(mock_execute):
    """Test LLM consultation failure."""
    # Mock failed response
    mock_response = Mock()
    mock_response.success = False
    mock_response.output = ""
    mock_response.error = "Connection timeout"
    mock_execute.return_value = mock_response

    result = consult_llm("Test prompt", provider="cursor-agent")

    assert result.success is False
    assert result.output == ""
    assert "Connection timeout" in result.error
    assert result.tool_used == "cursor-agent"


@patch("claude_skills.llm_doc_gen.ai_consultation.get_available_providers")
def test_consult_llm_no_providers(mock_get_providers):
    """Test consultation when no providers available."""
    mock_get_providers.return_value = []

    result = consult_llm("Test prompt")

    assert result.success is False
    assert "No AI providers available" in result.error


@patch("claude_skills.common.ai_tools.execute_tool_with_fallback")
def test_consult_llm_auto_select_provider(mock_execute):
    """Test auto-selection of provider when none specified."""
    with patch("claude_skills.llm_doc_gen.ai_consultation.get_available_providers", return_value=["gemini", "cursor-agent"]):
        mock_response = Mock()
        mock_response.success = True
        mock_response.output = "Response"
        mock_execute.return_value = mock_response

        result = consult_llm("Test prompt")

        # Should use first available provider
        assert result.tool_used == "gemini"


@patch("subprocess.run")
@patch("shutil.which")
def test_consult_llm_direct_fallback(mock_which, mock_run):
    """Test direct CLI fallback when import fails."""
    # Simulate import error
    with patch(
        "claude_skills.common.ai_tools.execute_tool_with_fallback",
        side_effect=ImportError,
    ):
        mock_which.return_value = "/usr/bin/cursor-agent"
        mock_run.return_value = Mock(returncode=0, stdout="Response", stderr="")

        with patch(
            "claude_skills.llm_doc_gen.ai_consultation.get_available_providers",
            return_value=["cursor-agent"],
        ):
            result = consult_llm("Test prompt", provider="cursor-agent")

            assert result.success is True
            assert result.output == "Response"
            mock_run.assert_called_once()


@patch("claude_skills.common.ai_tools.execute_tools_parallel")
def test_consult_multi_agent_success(mock_execute_parallel):
    """Test multi-agent consultation."""
    with patch("claude_skills.llm_doc_gen.ai_consultation.get_available_providers", return_value=["cursor-agent", "gemini", "codex"]):
        # Mock parallel responses
        mock_response1 = Mock()
        mock_response1.success = True
        mock_response1.output = "Response 1"
        mock_response1.duration = 1.0

        mock_response2 = Mock()
        mock_response2.success = True
        mock_response2.output = "Response 2"
        mock_response2.duration = 1.5

        mock_multi_response = Mock()
        mock_multi_response.responses = {
            "cursor-agent": mock_response1,
            "gemini": mock_response2,
        }
        mock_execute_parallel.return_value = mock_multi_response

        results = consult_multi_agent("Test prompt")

        assert len(results) == 2
        assert results["cursor-agent"].success is True
        assert results["cursor-agent"].output == "Response 1"
        assert results["gemini"].success is True
        assert results["gemini"].output == "Response 2"


@patch("claude_skills.llm_doc_gen.ai_consultation.get_available_providers")
def test_consult_multi_agent_insufficient_providers(mock_get_providers):
    """Test multi-agent falls back to single when <2 providers."""
    mock_get_providers.return_value = ["cursor-agent"]

    with patch("claude_skills.llm_doc_gen.ai_consultation.consult_llm") as mock_consult:
        mock_consult.return_value = ConsultationResult(
            success=True, output="Single response", tool_used="cursor-agent"
        )

        results = consult_multi_agent("Test prompt")

        assert len(results) == 1
        assert results["cursor-agent"].success is True
        mock_consult.assert_called_once()


@patch("claude_skills.common.ai_tools.execute_tools_parallel")
def test_consult_multi_agent_with_specified_providers(mock_execute_parallel):
    """Test multi-agent with user-specified providers."""
    with patch("claude_skills.llm_doc_gen.ai_consultation.get_available_providers", return_value=["cursor-agent", "gemini", "codex"]):
        mock_response = Mock()
        mock_response.success = True
        mock_response.output = "Response"
        mock_response.duration = 1.0

        mock_multi_response = Mock()
        mock_multi_response.responses = {"gemini": mock_response, "codex": mock_response}
        mock_execute_parallel.return_value = mock_multi_response

        results = consult_multi_agent("Test prompt", providers=["gemini", "codex"])

        assert len(results) == 2
        assert "gemini" in results
        assert "codex" in results
        assert "cursor-agent" not in results
