from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from claude_skills.common.ai_tools import ToolResponse, ToolStatus
from claude_skills.sdd_fidelity_review.consultation import (
    ConsultationError,
    ConsultationTimeoutError,
    FidelityVerdict,
    IssueSeverity,
    NoToolsAvailableError,
    ParsedReviewResponse,
    categorize_issues,
    consult_ai_on_fidelity,
    consult_multiple_ai_on_fidelity,
    detect_consensus,
    parse_multiple_responses,
    parse_review_response,
)


pytestmark = pytest.mark.unit


def _make_response(tool: str, status: ToolStatus, output: str = "", error: str | None = None) -> ToolResponse:
    return ToolResponse(tool=tool, status=status, output=output, error=error)


def test_consult_ai_on_fidelity_raises_when_no_tools_available() -> None:
    with patch("claude_skills.sdd_fidelity_review.consultation.detect_available_tools", return_value=[]):
        with pytest.raises(NoToolsAvailableError):
            consult_ai_on_fidelity("review prompt", tool=None)


def test_consult_ai_on_fidelity_validates_requested_tool() -> None:
    with patch("claude_skills.sdd_fidelity_review.consultation.check_tool_available", return_value=False):
        with pytest.raises(NoToolsAvailableError):
            consult_ai_on_fidelity("review prompt", tool="gemini")


def test_consult_ai_on_fidelity_raises_on_timeout() -> None:
    with patch("claude_skills.sdd_fidelity_review.consultation.check_tool_available", return_value=True):
        with patch(
            "claude_skills.sdd_fidelity_review.consultation.execute_tool",
            return_value=_make_response("gemini", ToolStatus.TIMEOUT),
        ):
            with pytest.raises(ConsultationTimeoutError):
                consult_ai_on_fidelity("prompt", tool="gemini", timeout=30)


def test_consult_ai_on_fidelity_returns_response_on_success() -> None:
    success_response = _make_response("gemini", ToolStatus.SUCCESS, output="Looks good")
    with patch("claude_skills.sdd_fidelity_review.consultation.check_tool_available", return_value=True):
        with patch(
            "claude_skills.sdd_fidelity_review.consultation.execute_tool",
            return_value=success_response,
        ):
            response = consult_ai_on_fidelity("prompt", tool="gemini")
    assert response is success_response


def test_consult_ai_on_fidelity_auto_detects_available_tool() -> None:
    success_response = _make_response("codex", ToolStatus.SUCCESS, output="OK")
    with patch("claude_skills.sdd_fidelity_review.consultation.detect_available_tools", return_value=["codex"]):
        with patch("claude_skills.sdd_fidelity_review.consultation.check_tool_available", return_value=True):
            with patch(
                "claude_skills.sdd_fidelity_review.consultation.execute_tool",
                return_value=success_response,
            ) as mock_execute:
                response = consult_ai_on_fidelity("prompt", tool=None)
    assert response is success_response
    mock_execute.assert_called_once_with(tool="codex", prompt="prompt", model=None, timeout=600)


def test_consult_ai_on_fidelity_wraps_unexpected_errors() -> None:
    with patch("claude_skills.sdd_fidelity_review.consultation.detect_available_tools", side_effect=RuntimeError("boom")):
        with pytest.raises(ConsultationError):
            consult_ai_on_fidelity("prompt", tool=None)


@patch("claude_skills.sdd_fidelity_review.consultation.get_enabled_fidelity_tools", return_value={"gemini": {}, "codex": {}})
def test_consult_multiple_ai_on_fidelity_returns_responses(_mock_enabled_tools) -> None:
    multi_response = MagicMock()
    multi_response.responses = {
        "gemini": _make_response("gemini", ToolStatus.SUCCESS, output="A"),
        "codex": _make_response("codex", ToolStatus.SUCCESS, output="B"),
    }
    with patch("claude_skills.sdd_fidelity_review.consultation.detect_available_tools", return_value=["gemini", "codex"]):
        with patch("claude_skills.sdd_fidelity_review.consultation.check_tool_available", return_value=True):
            with patch(
                "claude_skills.sdd_fidelity_review.consultation.execute_tools_parallel",
                return_value=multi_response,
            ):
                responses = consult_multiple_ai_on_fidelity("prompt", timeout=120)
    assert len(responses) == 2
    assert {resp.tool for resp in responses} == {"gemini", "codex"}


def test_consult_multiple_ai_on_fidelity_raises_when_no_tools_available() -> None:
    with patch("claude_skills.sdd_fidelity_review.consultation.detect_available_tools", return_value=[]):
        with pytest.raises(NoToolsAvailableError):
            consult_multiple_ai_on_fidelity("prompt", tools=None)


def test_consult_multiple_ai_on_fidelity_handles_partial_failures() -> None:
    multi_response = MagicMock()
    multi_response.responses = {
        "gemini": _make_response("gemini", ToolStatus.SUCCESS, output="A"),
        "codex": _make_response("codex", ToolStatus.ERROR, error="boom"),
    }
    with patch("claude_skills.sdd_fidelity_review.consultation.get_enabled_fidelity_tools", return_value={"gemini": {}, "codex": {}}):
        with patch("claude_skills.sdd_fidelity_review.consultation.detect_available_tools", return_value=["gemini", "codex"]):
            with patch("claude_skills.sdd_fidelity_review.consultation.check_tool_available", return_value=True):
                with patch(
                    "claude_skills.sdd_fidelity_review.consultation.execute_tools_parallel",
                    return_value=multi_response,
                ):
                    responses = consult_multiple_ai_on_fidelity("prompt")
    assert len(responses) == 2
    assert any(resp.status is ToolStatus.ERROR for resp in responses)


def test_consult_multiple_ai_on_fidelity_cache_hit_short_circuits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("claude_skills.sdd_fidelity_review.consultation._CACHE_AVAILABLE", True)
    cached_payload = [
        {"tool": "gemini", "status": "success", "output": "Cached", "error": None, "exit_code": 0, "model": None, "metadata": {}}
    ]
    cache_mock = MagicMock()
    cache_mock.get.return_value = cached_payload

    with patch("claude_skills.sdd_fidelity_review.consultation.CacheManager", return_value=cache_mock):
        with patch("claude_skills.sdd_fidelity_review.consultation.generate_fidelity_review_key", return_value="cache-key"):
            with patch("claude_skills.sdd_fidelity_review.consultation.is_cache_enabled", return_value=True):
                responses = consult_multiple_ai_on_fidelity(
                    "prompt",
                    cache_key_params={"spec_id": "spec", "scope": "task", "target": "task-1"},
                    use_cache=True,
                )
    assert len(responses) == 1
    assert responses[0].tool == "gemini"
    cache_mock.get.assert_called_once_with("cache-key")


def test_consult_multiple_ai_on_fidelity_cache_save_failure_nonfatal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("claude_skills.sdd_fidelity_review.consultation._CACHE_AVAILABLE", True)
    cache_mock = MagicMock()
    cache_mock.get.return_value = None
    cache_mock.set.side_effect = RuntimeError("disk full")
    multi_response = MagicMock()
    multi_response.responses = {"gemini": _make_response("gemini", ToolStatus.SUCCESS, output="fresh")}

    with patch("claude_skills.sdd_fidelity_review.consultation.CacheManager", return_value=cache_mock):
        with patch("claude_skills.sdd_fidelity_review.consultation.generate_fidelity_review_key", return_value="cache-key"):
            with patch("claude_skills.sdd_fidelity_review.consultation.is_cache_enabled", return_value=True):
                with patch("claude_skills.sdd_fidelity_review.consultation.detect_available_tools", return_value=["gemini"]):
                    with patch("claude_skills.sdd_fidelity_review.consultation.check_tool_available", return_value=True):
                        with patch(
                            "claude_skills.sdd_fidelity_review.consultation.execute_tools_parallel",
                            return_value=multi_response,
                        ):
                            responses = consult_multiple_ai_on_fidelity(
                                "prompt",
                                cache_key_params={"spec_id": "spec", "scope": "task", "target": "task-1"},
                                use_cache=True,
                            )
    assert len(responses) == 1
    assert responses[0].tool == "gemini"
    cache_mock.set.assert_called_once()


def test_parse_review_response_extracts_pass_verdict() -> None:
    raw = """
    VERDICT: PASS

    RECOMMENDATIONS:
    - Add more tests
    """
    response = _make_response("gemini", ToolStatus.SUCCESS, output=raw)
    parsed = parse_review_response(response)
    assert parsed.verdict is FidelityVerdict.PASS
    assert parsed.recommendations


def test_parse_review_response_extracts_fail_with_issues() -> None:
    raw = """
    VERDICT: FAIL
    ISSUES:
    - Missing validation
    """
    response = _make_response("gemini", ToolStatus.SUCCESS, output=raw)
    parsed = parse_review_response(response)
    assert parsed.verdict is FidelityVerdict.FAIL
    assert any("Missing validation" in issue for issue in parsed.issues)


def test_parse_review_response_defaults_to_unknown() -> None:
    response = _make_response("gemini", ToolStatus.SUCCESS, output="No verdict provided.")
    parsed = parse_review_response(response)
    assert parsed.verdict is FidelityVerdict.UNKNOWN


def test_parse_multiple_responses() -> None:
    responses = [
        _make_response("gemini", ToolStatus.SUCCESS, output="VERDICT: PASS"),
        _make_response("codex", ToolStatus.SUCCESS, output="VERDICT: FAIL\nISSUES:\n- Bug"),
    ]
    parsed = parse_multiple_responses(responses)
    assert len(parsed) == 2
    assert parsed[0].verdict is FidelityVerdict.PASS
    assert parsed[1].verdict is FidelityVerdict.FAIL


def test_detect_consensus_majority() -> None:
    parsed = [
        ParsedReviewResponse(verdict=FidelityVerdict.FAIL, issues=["Bug"], recommendations=[]),
        ParsedReviewResponse(verdict=FidelityVerdict.FAIL, issues=["Bug"], recommendations=[]),
        ParsedReviewResponse(verdict=FidelityVerdict.PASS, issues=[], recommendations=[]),
    ]
    consensus = detect_consensus(parsed, min_agreement=2)
    assert consensus.consensus_verdict is FidelityVerdict.FAIL
    assert "bug" in consensus.consensus_issues


def test_categorize_issues_assigns_severity() -> None:
    issues = [
        "Security vulnerability: SQL injection possible",
        "Missing tests for edge cases",
        "Minor typo in message",
    ]
    categorized = categorize_issues(issues)
    severities = {item.issue: item.severity for item in categorized}
    assert any(sev is IssueSeverity.CRITICAL for issue, sev in severities.items() if "Security" in issue)
    assert any(sev in {IssueSeverity.MEDIUM, IssueSeverity.HIGH} for issue, sev in severities.items() if "Missing tests" in issue)
    assert any(sev is IssueSeverity.LOW for issue, sev in severities.items() if "typo" in issue.lower())
