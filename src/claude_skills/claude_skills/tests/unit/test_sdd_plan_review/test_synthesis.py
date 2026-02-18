from __future__ import annotations

import pytest

from claude_skills.common.ai_tools import ToolResponse, ToolStatus
from claude_skills.sdd_plan_review import synthesis


pytestmark = pytest.mark.unit


def test_synthesize_with_ai_prefers_available_review_tool(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, str] = {}

    monkeypatch.setattr(
        synthesis.ai_config,
        "get_tool_priority",
        lambda *_args, **_kwargs: ["codex", "opencode"],
    )
    monkeypatch.setattr(
        synthesis.ai_config,
        "get_agent_priority",
        lambda *_args, **_kwargs: ["gemini"],
    )
    monkeypatch.setattr(
        synthesis.ai_config,
        "resolve_tool_model",
        lambda *_args, **_kwargs: "demo-model",
    )
    monkeypatch.setattr(
        synthesis.ai_config,
        "get_timeout",
        lambda *_args, **_kwargs: 30,
    )

    def _fake_execute_tool_with_fallback(
        *,
        skill_name: str,
        tool: str,
        prompt: str,
        model: str | None = None,
        timeout: int = 90,
        context: dict | None = None,
        tracker=None,
    ) -> ToolResponse:
        captured["tool"] = tool
        return ToolResponse(
            tool=tool,
            status=ToolStatus.SUCCESS,
            output="# Synthesis\n\n## Critical Blockers\n- blocker",
            duration=0.1,
        )

    monkeypatch.setattr(
        synthesis, "execute_tool_with_fallback", _fake_execute_tool_with_fallback
    )

    responses = [
        {"tool": "opencode", "raw_review": "review from opencode"},
        {"tool": "codex", "raw_review": "review from codex"},
    ]

    result = synthesis.synthesize_with_ai(
        responses=responses,
        spec_id="spec-1",
        spec_title="Spec 1",
    )

    assert result["success"] is True
    assert captured["tool"] == "codex"


def test_build_consensus_uses_fallback_when_synthesis_output_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        synthesis,
        "synthesize_with_ai",
        lambda **_kwargs: {
            "success": True,
            "synthesis_text": "   ",
            "num_models": 2,
            "models": ["codex", "opencode"],
        },
    )
    monkeypatch.setattr(
        synthesis.ai_config,
        "get_tool_priority",
        lambda *_args, **_kwargs: ["codex", "opencode"],
    )

    responses = [
        {
            "tool": "codex",
            "raw_review": "## Critical Blockers\n- **[Security]** Missing audit checks",
        },
        {
            "tool": "opencode",
            "raw_review": "## Major Suggestions\n- Add explicit owner mapping",
        },
    ]

    result = synthesis.build_consensus(
        responses=responses,
        spec_id="spec-1",
        spec_title="Spec 1",
    )

    assert result["success"] is True
    assert result["fallback_used"] is True
    assert "Built deterministic summary from all model outputs." in result["synthesis_text"]
    assert "Models included: codex, opencode" in result["synthesis_text"]
    assert "[codex] **[Security]** Missing audit checks" in result["synthesis_text"]
    assert result["critical_blockers"]
