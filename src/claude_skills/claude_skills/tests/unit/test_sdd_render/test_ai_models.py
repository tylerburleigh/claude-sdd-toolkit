from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Dict

import pytest

from claude_skills.sdd_render.executive_summary import ExecutiveSummaryGenerator
from claude_skills.sdd_render.narrative_enhancer import NarrativeEnhancer


def _minimal_spec() -> Dict[str, Any]:
    return {
        "metadata": {"title": "Demo"},
        "hierarchy": {
            "spec-root": {
                "type": "root",
                "children": [],
                "total_tasks": 0,
                "completed_tasks": 0,
            }
        },
    }


def test_executive_summary_uses_model_override(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: Dict[str, Any] = {}

    def _mock_resolve(self, agent, *, feature):
        captured["agent"] = agent
        captured["feature"] = feature
        captured["model_override"] = self.model_override
        return "demo-model"

    monkeypatch.setattr(
        "claude_skills.sdd_render.executive_summary.ExecutiveSummaryGenerator._resolve_model",
        _mock_resolve,
    )
    def _mock_execute(agent, prompt, *, model=None, timeout=None):
        captured["invoked_agent"] = agent
        captured["timeout"] = timeout
        return SimpleNamespace(success=True, output="Summary", status=None)

    monkeypatch.setattr(
        "claude_skills.common.ai_tools.execute_tool_with_fallback",
        _mock_execute,
    )
    monkeypatch.setattr(
        "claude_skills.sdd_render.executive_summary.ExecutiveSummaryGenerator.get_available_agents",
        lambda self: ["gemini"],
    )

    generator = ExecutiveSummaryGenerator(
        _minimal_spec(),
        model_override={"gemini": "demo-model"},
    )

    success, output = generator.generate_summary(agent="gemini")

    assert success is True
    assert output == "Summary"
    assert captured["agent"] == "gemini"
    assert captured["feature"] == "executive_summary"
    assert captured["model_override"] == {"gemini": "demo-model"}
    assert captured["invoked_agent"] == "gemini"


def test_narrative_enhancer_uses_model_override(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: Dict[str, Any] = {}

    def _mock_resolve(self, agent, *, feature):
        captured["agent"] = agent
        captured["feature"] = feature
        captured["model_override"] = self.model_override
        return "demo-model"

    monkeypatch.setattr(
        "claude_skills.sdd_render.narrative_enhancer.NarrativeEnhancer._resolve_model",
        _mock_resolve,
    )
    monkeypatch.setattr(
        "claude_skills.common.ai_tools.execute_tool_with_fallback",
        lambda agent, prompt, *, model=None, timeout=None: SimpleNamespace(
            success=True,
            output="Narrative",
            status=None,
        ),
    )
    monkeypatch.setattr(
        "claude_skills.sdd_render.narrative_enhancer.get_agent_priority",
        lambda _: ["gemini"],
    )
    monkeypatch.setattr(
        "claude_skills.sdd_render.narrative_enhancer.NarrativeEnhancer._get_available_agents",
        lambda self: ["gemini"],
    )

    enhancer = NarrativeEnhancer(
        _minimal_spec(),
        model_override={"gemini": "demo-model"},
    )

    result = enhancer._generate_narrative_ai("Explain phase flow")

    assert result == "Narrative"
    assert captured["agent"] == "gemini"
    assert captured["feature"] == "narrative"
    assert captured["model_override"] == {"gemini": "demo-model"}