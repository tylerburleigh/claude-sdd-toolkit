from __future__ import annotations

import json
from textwrap import dedent
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
    with patch("claude_skills.common.ai_tools.get_enabled_and_available_tools", return_value=[]):
        with pytest.raises(NoToolsAvailableError):
            consult_ai_on_fidelity("review prompt", tool=None)


def test_consult_ai_on_fidelity_validates_requested_tool() -> None:
    with patch("claude_skills.common.ai_tools.check_tool_available", return_value=False):
        with pytest.raises(NoToolsAvailableError):
            consult_ai_on_fidelity("review prompt", tool="gemini")


def test_consult_ai_on_fidelity_raises_on_timeout() -> None:
    with patch("claude_skills.common.ai_tools.check_tool_available", return_value=True):
        with patch(
            "claude_skills.common.ai_tools.execute_tool_with_fallback",
            return_value=_make_response("gemini", ToolStatus.TIMEOUT),
        ):
            with pytest.raises(ConsultationTimeoutError):
                consult_ai_on_fidelity("prompt", tool="gemini", timeout=30)


def test_consult_ai_on_fidelity_returns_response_on_success() -> None:
    success_response = _make_response("gemini", ToolStatus.SUCCESS, output="Looks good")
    with patch("claude_skills.common.ai_tools.check_tool_available", return_value=True):
        with patch(
            "claude_skills.common.ai_tools.execute_tool_with_fallback",
            return_value=success_response,
        ):
            response = consult_ai_on_fidelity("prompt", tool="gemini")
    assert response is success_response


def test_consult_ai_on_fidelity_auto_detects_available_tool() -> None:
    success_response = _make_response("codex", ToolStatus.SUCCESS, output="OK")
    with patch("claude_skills.common.ai_tools.get_enabled_and_available_tools", return_value=["codex"]):
        with patch("claude_skills.common.ai_tools.check_tool_available", return_value=True):
            with patch("claude_skills.sdd_fidelity_review.consultation.ai_config.resolve_tool_model", return_value=None):
                with patch(
                    "claude_skills.common.ai_tools.execute_tool_with_fallback",
                    return_value=success_response,
                ) as mock_execute:
                    response = consult_ai_on_fidelity("prompt", tool=None)
    assert response is success_response
    mock_execute.assert_called_once()


def test_consult_ai_on_fidelity_wraps_unexpected_errors() -> None:
    with patch("claude_skills.common.ai_tools.get_enabled_and_available_tools", side_effect=RuntimeError("boom")):
        with pytest.raises(ConsultationError):
            consult_ai_on_fidelity("prompt", tool=None)


@patch("claude_skills.sdd_fidelity_review.consultation.get_enabled_fidelity_tools", return_value={"gemini": {}, "codex": {}})
def test_consult_multiple_ai_on_fidelity_returns_responses(_mock_enabled_tools) -> None:
    multi_response = MagicMock()
    multi_response.responses = {
        "gemini": _make_response("gemini", ToolStatus.SUCCESS, output="A"),
        "codex": _make_response("codex", ToolStatus.SUCCESS, output="B"),
    }
    with patch("claude_skills.common.ai_tools.get_enabled_and_available_tools", return_value=["gemini", "codex"]):
        with patch("claude_skills.common.ai_tools.check_tool_available", return_value=True):
            with patch(
                "claude_skills.common.ai_tools.execute_tools_parallel",
                return_value=multi_response,
            ):
                responses = consult_multiple_ai_on_fidelity("prompt", timeout=120)
    assert len(responses) == 2
    assert {resp.tool for resp in responses} == {"gemini", "codex"}


def test_consult_multiple_ai_on_fidelity_raises_when_no_tools_available() -> None:
    with patch("claude_skills.common.ai_tools.get_enabled_and_available_tools", return_value=[]):
        with pytest.raises(NoToolsAvailableError):
            consult_multiple_ai_on_fidelity("prompt", tools=None)


def test_consult_multiple_ai_on_fidelity_handles_partial_failures() -> None:
    multi_response = MagicMock()
    multi_response.responses = {
        "gemini": _make_response("gemini", ToolStatus.SUCCESS, output="A"),
        "codex": _make_response("codex", ToolStatus.ERROR, error="boom"),
    }
    with patch("claude_skills.sdd_fidelity_review.consultation.get_enabled_fidelity_tools", return_value={"gemini": {}, "codex": {}}):
        with patch("claude_skills.common.ai_tools.get_enabled_and_available_tools", return_value=["gemini", "codex"]):
            with patch("claude_skills.common.ai_tools.check_tool_available", return_value=True):
                with patch(
                    "claude_skills.common.ai_tools.execute_tools_parallel",
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
                with patch("claude_skills.common.ai_tools.get_enabled_and_available_tools", return_value=["gemini"]):
                    with patch("claude_skills.common.ai_tools.check_tool_available", return_value=True):
                        with patch(
                            "claude_skills.common.ai_tools.execute_tools_parallel",
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


def test_parse_review_response_parses_json_schema() -> None:
    long_summary = (
        "This summary intentionally exceeds six hundred characters to verify that JSON responses are not truncated by the parser. "
        + ("Additional context ensures the length requirement is satisfied. " * 10)
    ).strip()
    payload = {
        "verdict": "fail",
        "summary": long_summary,
        "requirement_alignment": {
            "answer": "no",
            "details": "Required setup template file was not created."
        },
        "success_criteria": {
            "met": "no",
            "details": "Primary success criterion (presence of __init__.py) not satisfied."
        },
        "deviations": [
            {
                "description": "Missing src/claude_skills/claude_skills/common/templates/setup/__init__.py.",
                "severity": "blocking"
            }
        ],
        "test_coverage": {
            "status": "insufficient",
            "details": "No tests were run to exercise template loading."
        },
        "code_quality": {
            "issues": [
                "ALL_SETUP_TEMPLATES references files that do not exist."
            ],
            "details": "Importers will raise FileNotFoundError when iterating exports."
        },
        "documentation": {
            "status": "inadequate",
            "details": "The README still references missing template files."
        },
        "issues": [
            "Explicit issue entry: Missing setup template package marker."
        ],
        "recommendations": [
            "Create src/claude_skills/claude_skills/common/templates/setup/__init__.py and populate the export tuple.",
            "Add a regression test that imports ALL_SETUP_TEMPLATES."
        ],
        "next_steps": [
            "Document the new setup templates in the onboarding guide."
        ]
    }
    raw = json.dumps(payload, indent=2)
    response = _make_response("gemini", ToolStatus.SUCCESS, output=raw)
    parsed = parse_review_response(response)

    assert parsed.verdict is FidelityVerdict.FAIL
    assert parsed.summary == long_summary
    assert any("Missing setup template package marker" in issue for issue in parsed.issues)
    assert any("Requirement alignment" in issue for issue in parsed.issues)
    assert any("Code quality" in issue for issue in parsed.issues)
    assert any("Create src/claude_skills/claude_skills/common/templates/setup/__init__.py" in rec for rec in parsed.recommendations)
    assert any("regression test" in rec for rec in parsed.recommendations)
    assert any("Document the new setup templates" in rec for rec in parsed.recommendations)
    assert parsed.provider == "gemini"
    assert parsed.model is None


def test_parse_review_response_parses_nested_response_field() -> None:
    payload = {
        "verdict": "fail",
        "summary": "Nested payload summary.",
        "issues": ["Top level issue entry."],
        "recommendations": ["Top level recommendation."],
    }
    outer = {"response": json.dumps(payload)}
    raw = json.dumps(outer)
    response = _make_response("gemini", ToolStatus.SUCCESS, output=raw)
    parsed = parse_review_response(response)

    assert parsed.verdict is FidelityVerdict.FAIL
    assert parsed.summary == "Nested payload summary."
    assert parsed.issues == ["Top level issue entry."]
    assert parsed.recommendations == ["Top level recommendation."]
    assert parsed.structured_response == payload
    assert parsed.provider == "gemini"
    assert parsed.model is None


def test_parse_review_response_parses_json_code_block_entries() -> None:
    payload = {
        "verdict": "partial",
        "summary": "Implementation satisfies key requirements but lacks integration tests.",
        "requirement_alignment": {"answer": "partial", "details": "Core logic aligned, tests missing."},
        "issues": [
            {"description": "Integration tests not provided for new template loader.", "severity": "High"}
        ],
        "recommendations": [
            {"text": "Add integration tests covering template loader import paths."}
        ],
    }
    raw = f"```json\n{json.dumps(payload, indent=2)}\n```"
    response = _make_response("cursor-agent", ToolStatus.SUCCESS, output=raw)
    parsed = parse_review_response(response)

    assert parsed.verdict is FidelityVerdict.PARTIAL
    assert any("Integration tests not provided" in issue for issue in parsed.issues)
    assert any("Core logic aligned" in issue for issue in parsed.issues)
    assert any("Add integration tests covering template loader import paths." in rec for rec in parsed.recommendations)
    assert parsed.provider == "cursor-agent"
    assert parsed.model is None


def test_parse_review_response_handles_numbered_findings_section() -> None:
    raw = dedent(
        """
        VERDICT: FAIL

        {
          "response": "Detailed review summary:

        1.  **Requirement Alignment:** The implementation does not match the specification requirements; the required template file is missing.
        2.  **Success Criteria:** Not satisfied because nothing in the artifacts proves the templates were copied.

        ### Recommendations
        - Create the missing template files in src/claude_skills/claude_skills/common/templates/setup/.
        - Add a smoke test that loads ALL_SETUP_TEMPLATES to confirm the files exist.
        "
        }
        """
    )
    response = _make_response("gemini", ToolStatus.SUCCESS, output=raw)
    parsed = parse_review_response(response)

    assert parsed.verdict is FidelityVerdict.FAIL
    assert any("Requirement Alignment" in issue for issue in parsed.issues)
    assert any("Success Criteria" in issue for issue in parsed.issues)
    assert any("missing template files" in rec.lower() for rec in parsed.recommendations)
    assert len(parsed.recommendations) == 2


def test_parse_review_response_handles_findings_heading_with_bullets() -> None:
    raw = dedent(
        """
        ### Findings
        - Blocking – Module exports constants for setup templates that are absent on disk, so consumers crash when iterating ALL_SETUP_TEMPLATES.
        - Minor deviation – Documentation still references template names that no longer exist.

        ### Recommendations
        - Restore the missing template files under src/claude_skills/claude_skills/common/templates/setup/.
        - Update the documentation to match the actual file names.
        """
    )
    response = _make_response("gemini", ToolStatus.SUCCESS, output=raw)
    parsed = parse_review_response(response)

    assert any(issue.startswith("Blocking") for issue in parsed.issues)
    assert len(parsed.issues) == 2
    assert any(rec.startswith("Restore") for rec in parsed.recommendations)
    assert len(parsed.recommendations) == 2


def test_parse_review_response_keeps_full_first_paragraph_summary() -> None:
    first_paragraph = (
        "This is an intentionally long paragraph that should remain intact even when it exceeds two hundred characters. "
        "It describes the overall fidelity review context including the fact that required template files are missing "
        "and that downstream systems fail to load configuration defaults as a result."
    )
    raw = f"{first_paragraph}\n\n### Findings\n- Blocking – Missing template files prevent setup from completing."
    response = _make_response("gemini", ToolStatus.SUCCESS, output=raw)
    parsed = parse_review_response(response)

    assert parsed.summary == first_paragraph


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
    assert "Bug" in consensus.consensus_issues


def test_detect_consensus_preserves_original_text() -> None:
    parsed = [
        ParsedReviewResponse(
            verdict=FidelityVerdict.FAIL,
            issues=["Blocking – Missing template files"],
            recommendations=["Restore the missing template files"],
        ),
        ParsedReviewResponse(
            verdict=FidelityVerdict.FAIL,
            issues=["Blocking – Missing template files"],
            recommendations=["Restore the missing template files"],
        ),
    ]
    consensus = detect_consensus(parsed, min_agreement=2)

    assert consensus.consensus_issues == ["Blocking – Missing template files"]
    assert consensus.all_issues == ["Blocking – Missing template files"]
    assert consensus.consensus_recommendations == ["Restore the missing template files"]
    assert consensus.all_recommendations == ["Restore the missing template files"]


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