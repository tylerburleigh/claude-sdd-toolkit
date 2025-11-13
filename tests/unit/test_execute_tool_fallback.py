import pytest
from unittest.mock import Mock, patch
from claude_skills.common.ai_tools import execute_tool_with_fallback, ToolStatus, ToolResponse
from claude_skills.common.consultation_limits import ConsultationTracker


@patch('claude_skills.common.ai_tools.execute_tool')
def test_fallback_success_first_tool(mock_execute):
    """Test successful consultation on first tool doesn't trigger fallback."""
    mock_execute.return_value = ToolResponse(
        tool="gemini",
        status=ToolStatus.SUCCESS,
        output="Analysis complete"
    )

    tracker = ConsultationTracker()
    response = execute_tool_with_fallback(
        skill_name="run-tests",
        tool="gemini",
        prompt="Test prompt",
        tracker=tracker
    )

    assert response.success
    assert response.tool == "gemini"
    assert tracker.get_count() == 1
    assert mock_execute.call_count == 1


@patch('claude_skills.common.ai_tools.execute_tool')
def test_fallback_on_timeout(mock_execute):
    """Test fallback to next tool on timeout."""
    # First tool ('gemini') times out on initial call + all retries, second succeeds
    mock_execute.side_effect = [
        ToolResponse(tool="gemini", status=ToolStatus.TIMEOUT, error="Timed out"),
        ToolResponse(tool="gemini", status=ToolStatus.TIMEOUT, error="Timed out"),
        ToolResponse(tool="gemini", status=ToolStatus.TIMEOUT, error="Timed out"),
        ToolResponse(tool="gemini", status=ToolStatus.TIMEOUT, error="Timed out"),
        ToolResponse(tool="cursor-agent", status=ToolStatus.SUCCESS, output="Done")
    ]

    tracker = ConsultationTracker()
    response = execute_tool_with_fallback(
        skill_name="run-tests",
        tool="gemini",
        prompt="Test prompt",
        tracker=tracker
    )

    assert response.success
    assert response.tool == "cursor-agent"
    assert tracker.get_count() == 2  # Both tools attempted
    assert mock_execute.call_count > 1  # Retries + fallback


@patch('claude_skills.common.ai_tools.execute_tool')
@patch('claude_skills.common.ai_tools.time.sleep')
def test_retry_on_timeout(mock_sleep, mock_execute):
    """Test retries same tool on timeout before fallback."""
    # Timeout twice, then succeed
    mock_execute.side_effect = [
        ToolResponse(tool="gemini", status=ToolStatus.TIMEOUT),
        ToolResponse(tool="gemini", status=ToolStatus.TIMEOUT),
        ToolResponse(tool="gemini", status=ToolStatus.SUCCESS, output="Done"),
    ]

    tracker = ConsultationTracker()
    response = execute_tool_with_fallback(
        skill_name="run-tests",
        tool="gemini",
        prompt="Test prompt",
        tracker=tracker
    )

    assert response.success
    assert mock_execute.call_count == 3  # 1 initial + 2 retries
    assert mock_sleep.call_count == 2  # Delay between retries
    assert tracker.get_count() == 1  # Only gemini used


@patch('claude_skills.common.ai_tools.execute_tool')
def test_skip_on_not_found(mock_execute):
    """Test immediately skips to next tool on NOT_FOUND."""
    mock_execute.side_effect = [
        ToolResponse(tool="gemini", status=ToolStatus.NOT_FOUND),
        ToolResponse(tool="cursor-agent", status=ToolStatus.SUCCESS, output="Done"),
    ]

    tracker = ConsultationTracker()
    response = execute_tool_with_fallback(
        skill_name="run-tests",
        tool="gemini",
        prompt="Test prompt",
        tracker=tracker
    )

    assert response.success
    assert response.tool == "cursor-agent"
    # Should not retry gemini, just move to next tool
    assert mock_execute.call_count == 2


@patch('claude_skills.common.ai_tools.execute_tool')
def test_respects_consultation_limit(mock_execute):
    """Test respects max_tools_per_run limit."""
    # All tools fail
    mock_execute.return_value = ToolResponse(
        tool="any",
        status=ToolStatus.ERROR,
        error="Failed"
    )

    tracker = ConsultationTracker()
    response = execute_tool_with_fallback(
        skill_name="run-tests",  # Has max_tools_per_run: 2
        tool="gemini",
        prompt="Test prompt",
        tracker=tracker
    )

    # Should try gemini and cursor-agent, but not codex (limit of 2)
    assert tracker.get_count() <= 2


@patch('claude_skills.common.ai_tools.execute_tool')
def test_fallback_disabled(mock_execute):
    """Test fallback can be disabled."""
    mock_execute.return_value = ToolResponse(
        tool="gemini",
        status=ToolStatus.TIMEOUT
    )

    response = execute_tool_with_fallback(
        skill_name="run-tests",
        tool="gemini",
        prompt="Test prompt",
        fallback_enabled=False
    )

    assert not response.success
    assert mock_execute.call_count == 1  # No retries or fallback
