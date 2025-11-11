from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, List

import pytest

from claude_skills.sdd_plan_review import reviewer
from claude_skills.common.ai_tools import ToolResponse, ToolStatus, MultiToolResponse


pytestmark = pytest.mark.unit


def _mock_response(tool: str) -> ToolResponse:
    return ToolResponse(tool=tool, status=ToolStatus.SUCCESS, output="ok", duration=1.0)


def _multi_response(tools: List[str]) -> MultiToolResponse:
    responses = {tool: _mock_response(tool) for tool in tools}
    return MultiToolResponse(
        responses=responses,
        success_count=len(responses),
        failure_count=0,
        total_duration=1.0,
        max_duration=1.0,
    )


def test_review_with_tools_uses_shared_model_resolver(monkeypatch: pytest.MonkeyPatch) -> None:
    tools = ["gemini", "codex"]

    captured_calls: Dict[str, Any] = {}

    def _fake_resolve_models(skill_name: str, tool_list: List[str], override=None, context=None):
        captured_calls["skill_name"] = skill_name
        captured_calls["tools"] = tuple(tool_list)
        captured_calls["override"] = override
        captured_calls["context"] = context
        return OrderedDict((tool, f"{tool}-model") for tool in tool_list)

    monkeypatch.setattr(reviewer.ai_config, "resolve_models_for_tools", _fake_resolve_models)

    execute_calls: Dict[str, Any] = {}

    def _fake_execute_tools_parallel(tools: List[str], prompt: str, models: Dict[str, str], timeout: int):
        execute_calls["tools"] = tuple(tools)
        execute_calls["models"] = models
        execute_calls["timeout"] = timeout
        return _multi_response(tools)

    monkeypatch.setattr(reviewer, "execute_tools_parallel", _fake_execute_tools_parallel)

    result = reviewer.review_with_tools(
        spec_content="{}",
        tools=tools,
        review_type="full",
        spec_id="id",
        spec_title="title",
        parallel=True,
        model_override={"gemini": "cli-model"},
    )

    assert captured_calls == {
        "skill_name": "sdd-plan-review",
        "tools": tuple(tools),
        "override": {"gemini": "cli-model"},
        "context": {"review_type": "full"},
    }
    assert execute_calls["tools"] == tuple(tools)
    assert execute_calls["models"] == {"gemini": "gemini-model", "codex": "codex-model"}
    assert result["models"] == {"gemini": "gemini-model", "codex": "codex-model"}
