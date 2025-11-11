"""
Integration-style tests exercising multi-provider orchestration flows.

These tests stitch together the tool detection helpers plus the parallel
execution utilities to validate fallbacks, parallel success/failure mixes,
and no-tool failure handling.
"""

from __future__ import annotations

from typing import Dict, Iterable, List

import pytest

from claude_skills.common.ai_tools import (
    MultiToolResponse,
    ToolResponse,
    ToolStatus,
    detect_available_tools,
    execute_tools_parallel,
)


def _orchestrate(prompt: str, preferred_tools: Iterable[str]) -> MultiToolResponse:
    """
    Simple orchestrator used by the integration tests.

    It discovers available tools via detect_available_tools, then executes
    them in parallel using execute_tools_parallel.
    """
    available = detect_available_tools(list(preferred_tools), check_version=True)
    if not available:
        raise RuntimeError("No providers available for orchestration")

    multi = execute_tools_parallel(list(available), prompt)
    return multi


def test_parallel_execution_handles_mixed_results(mocker) -> None:
    responses: Dict[str, ToolResponse] = {
        "gemini": ToolResponse(tool="gemini", status=ToolStatus.SUCCESS, output="ok"),
        "codex": ToolResponse(tool="codex", status=ToolStatus.ERROR, error="boom"),
        "cursor-agent": ToolResponse(tool="cursor-agent", status=ToolStatus.TIMEOUT),
        "claude": ToolResponse(tool="claude", status=ToolStatus.SUCCESS, output="claude ok"),
    }

    mocker.patch(
        "claude_skills.common.ai_tools.execute_tool",
        side_effect=lambda tool, *_args, **_kwargs: responses[tool],
    )
    mocker.patch(
        "claude_skills.common.ai_tools.detect_available_tools",
        return_value=list(responses.keys()),
    )

    multi = execute_tools_parallel(list(responses.keys()), "prompt")

    assert multi.success_count == 2
    assert multi.failure_count == 2
    assert multi.responses["gemini"].success is True
    assert multi.responses["claude"].success is True
    assert multi.responses["codex"].status == ToolStatus.ERROR
    assert multi.responses["cursor-agent"].status == ToolStatus.TIMEOUT


def test_orchestrator_falls_back_to_available_tool(mocker) -> None:
    preferred = ["gemini", "codex", "cursor-agent", "claude"]

    def fake_check(tool: str, check_version: bool = False) -> bool:
        return tool == "codex"

    mocker.patch(
        "claude_skills.common.ai_tools.check_tool_available",
        side_effect=fake_check,
    )
    mocker.patch(
        "claude_skills.common.ai_tools.execute_tool",
        return_value=ToolResponse(tool="codex", status=ToolStatus.SUCCESS, output="codex"),
    )

    multi = _orchestrate("fallback prompt", preferred)

    assert multi.success_count == 1
    assert list(multi.responses.keys()) == ["codex"]


def test_orchestrator_raises_when_no_tools_available(mocker) -> None:
    mocker.patch(
        "claude_skills.common.ai_tools.check_tool_available",
        return_value=False,
    )

    with pytest.raises(RuntimeError):
        _ = _orchestrate("no tools", ["gemini", "codex", "claude"])
