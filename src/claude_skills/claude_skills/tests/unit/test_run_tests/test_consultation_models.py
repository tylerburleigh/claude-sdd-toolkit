from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import patch

import pytest

from claude_skills.common.ai_tools import MultiToolResponse, ToolResponse, ToolStatus
from claude_skills.run_tests import consultation


class DummyPrinter:
    """Minimal PrettyPrinter replacement for tests."""

    def __init__(self) -> None:
        self.messages: List[Tuple[str, Optional[str]]] = []

    def action(self, message: str) -> None:
        self.messages.append(("action", message))

    def info(self, message: str) -> None:
        self.messages.append(("info", message))

    def warning(self, message: str) -> None:
        self.messages.append(("warning", message))

    def error(self, message: str) -> None:
        self.messages.append(("error", message))

    def blank(self) -> None:
        self.messages.append(("blank", None))


@pytest.fixture
def dummy_printer() -> DummyPrinter:
    return DummyPrinter()


def test_get_model_for_tool_delegates_to_shared_resolver(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: List[Tuple[str, str, Any, Optional[Dict[str, Any]]]] = []

    def _fake_resolver(skill_name: str, tool: str, override: Any = None, context: Optional[Dict[str, Any]] = None) -> str:
        captured.append((skill_name, tool, override, context))
        return f"{tool}-resolved"

    monkeypatch.setattr(consultation.ai_config, "resolve_tool_model", _fake_resolver)

    result = consultation.get_model_for_tool("gemini", failure_type="assertion", override={"gemini": "cli"})

    assert result == "gemini-resolved"
    assert captured == [("run-tests", "gemini", {"gemini": "cli"}, {"failure_type": "assertion"})]


def test_get_model_for_tool_without_failure_type_omits_context(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: List[Tuple[str, str, Any, Optional[Dict[str, Any]]]] = []

    def _fake_resolver(skill_name: str, tool: str, override: Any = None, context: Optional[Dict[str, Any]] = None) -> str:
        captured.append((skill_name, tool, override, context))
        return "resolved"

    monkeypatch.setattr(consultation.ai_config, "resolve_tool_model", _fake_resolver)

    result = consultation.get_model_for_tool("codex", failure_type=None, override=None)

    assert result == "resolved"
    assert captured == [("run-tests", "codex", None, None)]


def test_consult_multi_agent_uses_resolved_models(monkeypatch: pytest.MonkeyPatch, dummy_printer: DummyPrinter) -> None:
    # Use patch to mock the function in both the original module and where it's imported
    # This ensures the mock works even when the function is imported directly
    mock_func = lambda skill_name: ["gemini", "codex"]
    with patch("claude_skills.common.ai_tools.get_enabled_and_available_tools", mock_func), \
         patch("claude_skills.run_tests.consultation.get_enabled_and_available_tools", mock_func):
        # Mock get_enabled_tools to return a dict that includes both tools
        # This is needed because consult_multi_agent filters agents through enabled_tools_map
        monkeypatch.setattr(consultation.ai_config, "get_enabled_tools", lambda skill_name: {"gemini": {}, "codex": {}})
        monkeypatch.setattr(consultation, "_resolve_consensus_agents", lambda agents: ["gemini", "codex"])
        monkeypatch.setattr(consultation, "format_prompt", lambda **_: "formatted-prompt")
        monkeypatch.setattr(consultation, "get_consultation_timeout", lambda: 42)
        monkeypatch.setattr(consultation, "synthesize_responses", lambda responses: {"successful_consultations": len(responses)})
        monkeypatch.setattr(consultation, "format_synthesis_output", lambda *args, **kwargs: None)

        resolved_models = OrderedDict([("gemini", "gemini-model"), ("codex", "codex-model")])
        resolve_calls: List[Tuple[str, Tuple[str, ...], Any, Optional[Dict[str, Any]]]] = []

        def _fake_resolve_models(
            skill_name: str,
            tools: List[str],
            override: Any = None,
            context: Optional[Dict[str, Any]] = None,
        ) -> OrderedDict[str, Optional[str]]:
            resolve_calls.append((skill_name, tuple(tools), override, context))
            return resolved_models

        monkeypatch.setattr(consultation.ai_config, "resolve_models_for_tools", _fake_resolve_models)

        execute_calls: List[Tuple[Tuple[str, ...], str, Dict[str, Optional[str]], int]] = []

        def _fake_execute_tools_parallel(
            tools: List[str],
            prompt: str,
            models: Dict[str, Optional[str]],
            timeout: int,
        ) -> MultiToolResponse:
            execute_calls.append((tuple(tools), prompt, models, timeout))
            responses = {
                tool: ToolResponse(tool=tool, status=ToolStatus.SUCCESS)
                for tool in tools
            }
            return MultiToolResponse(
                responses=responses,
                success_count=len(responses),
                failure_count=0,
                total_duration=1.0,
                max_duration=0.5,
            )

        monkeypatch.setattr(consultation, "execute_tools_parallel", _fake_execute_tools_parallel)

        result = consultation.consult_multi_agent(
            failure_type="assertion",
            error_message="Assertion failed",
            hypothesis="Bug in logic",
            context=None,
            question=None,
            agents=None,
            dry_run=False,
            printer=dummy_printer,
            model_override={"gemini": "cli-model"},
        )

        assert result == 0
        assert resolve_calls == [
            ("run-tests", ("gemini", "codex"), {"gemini": "cli-model"}, {"failure_type": "assertion"})
        ]
        assert execute_calls == [
            (("gemini", "codex"), "formatted-prompt", dict(resolved_models), 42)
        ]
