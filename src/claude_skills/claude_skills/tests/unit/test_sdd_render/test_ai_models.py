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

    def _mock_get_agent_command(skill, agent, prompt, *, model_override=None, context=None):
        captured["skill"] = skill
        captured["agent"] = agent
        captured["model_override"] = model_override
        captured["context"] = context
        return ["echo", "summary"]

    monkeypatch.setattr(
        "claude_skills.sdd_render.executive_summary.get_agent_command",
        _mock_get_agent_command,
    )

    monkeypatch.setattr(
        "claude_skills.sdd_render.executive_summary.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="Summary", stderr=""),
    )

    generator = ExecutiveSummaryGenerator(
        _minimal_spec(),
        model_override={"gemini": "demo-model"},
    )

    success, output = generator.generate_summary(agent="gemini")

    assert success is True
    assert output == "Summary"
    assert captured == {
        "skill": "sdd-render",
        "agent": "gemini",
        "model_override": {"gemini": "demo-model"},
        "context": {"feature": "executive_summary"},
    }


def test_narrative_enhancer_uses_model_override(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: Dict[str, Any] = {}

    def _mock_get_agent_command(skill, agent, prompt, *, model_override=None, context=None):
        captured["skill"] = skill
        captured["agent"] = agent
        captured["model_override"] = model_override
        captured["context"] = context
        return ["echo", "narrative"]

    monkeypatch.setattr(
        "claude_skills.sdd_render.narrative_enhancer.get_agent_command",
        _mock_get_agent_command,
    )
    monkeypatch.setattr(
        "claude_skills.sdd_render.narrative_enhancer.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout="Narrative", stderr=""),
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
    assert captured == {
        "skill": "sdd-render",
        "agent": "gemini",
        "model_override": {"gemini": "demo-model"},
        "context": {"feature": "narrative"},
    }
