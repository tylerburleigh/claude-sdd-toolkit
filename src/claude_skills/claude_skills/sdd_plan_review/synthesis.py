#!/usr/bin/env python3
"""
Multi-model response synthesis for spec reviews.

Parses AI tool responses, extracts structured data, builds consensus,
and generates overall recommendations.
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from statistics import mean, median

from claude_skills.common import ai_config
from claude_skills.common.ai_tools import execute_tool_with_fallback, ToolStatus
from claude_skills.common import consultation_limits


def parse_response(tool_output: str, tool_name: str) -> Dict[str, Any]:
    """
    Extract raw response from tool output.

    Handles wrapper formats (like gemini CLI) but returns raw markdown/text.
    No parsing or structuring - that's done by AI synthesis.

    Args:
        tool_output: Raw output from AI tool
        tool_name: Name of the tool for logging

    Returns:
        Response dictionary with raw text
    """
    result = {
        "success": True,
        "tool": tool_name,
        "raw_output": tool_output,
        "parsed_data": None,
        "error": None,
    }

    # Handle gemini CLI wrapper format
    if '{"response":' in tool_output and '"stats":' in tool_output:
        try:
            # Extract JSON wrapper
            start = tool_output.find('{')
            end = tool_output.rfind('}') + 1
            if start != -1 and end > start:
                wrapper_data = json.loads(tool_output[start:end])
                if isinstance(wrapper_data, dict) and "response" in wrapper_data:
                    tool_output = wrapper_data["response"]
                    result["raw_output"] = tool_output
        except (json.JSONDecodeError, ValueError):
            # If unwrapping fails, use original output
            pass

    # Store raw text - AI will synthesize it
    result["parsed_data"] = {
        "tool": tool_name,
        "raw_review": tool_output
    }

    return result


def synthesize_with_ai(
    responses: List[Dict[str, Any]],
    spec_id: str,
    spec_title: str,
    working_dir: str = "/tmp",
) -> Dict[str, Any]:
    """
    Use AI to synthesize multiple model reviews into consensus.

    Instead of fragile regex parsing, let AI read natural language reviews
    and create structured synthesis.

    Note: Synthesis always uses exactly 1 tool call (no retries, no fallback)
    to avoid overcomplexity in the synthesis step.

    Args:
        responses: List of response dicts with "tool" and "raw_review" keys
        spec_id: Specification ID
        spec_title: Specification title
        working_dir: Working directory for AI tool

    Returns:
        Synthesized consensus dictionary
    """
    if not responses:
        return {
            "success": False,
            "error": "No responses to synthesize"
        }

    # Build synthesis prompt
    prompt_parts = [
        f"You are synthesizing {len(responses)} independent AI reviews of a specification.",
        "",
        f"**Specification**: {spec_title} (`{spec_id}`)",
        "",
        "**Your Task**: Read all reviews below and create a comprehensive synthesis.",
        "",
        "**Required Output** (Markdown format):",
        "",
        "```markdown",
        "# Synthesis",
        "",
        "## Overall Assessment",
        "- **Consensus Level**: Strong/Moderate/Weak/Conflicted (based on agreement across models)",
        "",
        "## Critical Blockers",
        "Issues that must be fixed before implementation (identified by multiple models):",
        "- **[Category]** Issue title - flagged by: [model names]",
        "  - Impact: ...",
        "  - Recommended fix: ...",
        "",
        "## Major Suggestions",
        "Significant improvements that enhance quality, maintainability, or design:",
        "- **[Category]** Issue title - flagged by: [model names]",
        "  - Description: ...",
        "  - Recommended fix: ...",
        "",
        "## Questions for Author",
        "Clarifications needed (common questions across models):",
        "- **[Category]** Question - flagged by: [model names]",
        "  - Context: Why this matters",
        "",
        "## Design Strengths",
        "What the spec does well (areas of agreement):",
        "- **[Category]** Strength - noted by: [model names]",
        "  - Why this is effective",
        "",
        "## Points of Agreement",
        "- What all/most models agree on",
        "",
        "## Points of Disagreement",
        "- Where models conflict",
        "- Your assessment of the disagreement",
        "",
        "## Synthesis Notes",
        "- Overall themes across reviews",
        "- Actionable next steps",
        "```",
        "",
        "**Important**:",
        "- Attribute issues to specific models (e.g., \"flagged by: gemini, codex\")",
        "- Note where models agree vs. disagree",
        "- Focus on synthesizing actionable feedback across all reviews",
        "",
        "---",
        ""
    ]

    # Add each model's review
    for i, resp in enumerate(responses, 1):
        tool_name = resp.get("tool", f"Model {i}")
        raw_review = resp.get("raw_review", "")

        prompt_parts.append(f"## Review {i}: {tool_name}")
        prompt_parts.append("")
        prompt_parts.append("```")
        prompt_parts.append(raw_review)
        prompt_parts.append("```")
        prompt_parts.append("")

    prompt = "\n".join(prompt_parts)

    agent_priority = ai_config.get_agent_priority("sdd-plan-review")
    tool_name = agent_priority[0] if agent_priority else "gemini"
    model = ai_config.resolve_tool_model(
        "sdd-plan-review",
        tool_name,
        context={"feature": "synthesis"},
    )
    timeout = ai_config.get_timeout("sdd-plan-review", "narrative")

    # Synthesis: fallback allowed but no retries (1 attempt per tool)
    # Uses separate tracker so it doesn't count against parallel review limit
    # Config has max_retries_per_tool: 0 for sdd-plan-review to enforce this
    synthesis_tracker = consultation_limits.ConsultationTracker()

    response = execute_tool_with_fallback(
        skill_name="sdd-plan-review",
        tool=tool_name,
        prompt=prompt,
        model=model,
        timeout=timeout,
        context={"feature": "synthesis"},
        tracker=synthesis_tracker,
    )

    if not response.success:
        if response.status == ToolStatus.TIMEOUT:
            error = f"{tool_name} timed out after {timeout}s"
        elif response.status == ToolStatus.NOT_FOUND:
            error = f"{tool_name} provider not available for synthesis"
        else:
            error = response.error or f"{tool_name} synthesis failed (status={response.status.value})"
        return {
            "success": False,
            "error": error,
        }

    synthesis_text = response.output

    # Handle gemini wrapper format for backwards compatibility
    if '{"response":' in synthesis_text and '"stats":' in synthesis_text:
        try:
            start = synthesis_text.find('{')
            end = synthesis_text.rfind('}') + 1
            wrapper = json.loads(synthesis_text[start:end])
            if "response" in wrapper:
                synthesis_text = wrapper["response"]
        except (json.JSONDecodeError, ValueError):
            pass

    return {
        "success": True,
        "synthesis_text": synthesis_text,
        "num_models": len(responses),
        "models": [r.get("tool") for r in responses],
    }



def _parse_synthesis_text(synthesis_text: str) -> Dict[str, Any]:
    """
    Parse structured data from AI-generated synthesis markdown.

    Uses regex to extract key metrics and lists from the synthesis text.

    Args:
        synthesis_text: Markdown text from AI synthesis

    Returns:
        Dictionary with structured data
    """
    data = {}

    # Consensus level
    level_match = re.search(r"Consensus Level\*\*:\s*(Strong|Moderate|Weak|Conflicted)", synthesis_text, re.IGNORECASE)
    if level_match:
        data["consensus_level"] = level_match.group(1)

    # Section parsing
    def _extract_section_list(section_name: str) -> List[str]:
        """Extract list items from a markdown section."""
        section_pattern = re.compile(
            rf"##\s*{re.escape(section_name)}\s*\n(.*?)(?=\n##\s*|$)",
            re.DOTALL | re.IGNORECASE
        )
        section_match = section_pattern.search(synthesis_text)
        if not section_match:
            return []

        content = section_match.group(1)
        items = re.findall(r"^\s*[-*]\s*(.*)", content, re.MULTILINE)
        return [item.strip() for item in items]

    # Extract feedback by category
    data["critical_blockers"] = _extract_section_list("Critical Blockers")
    data["major_suggestions"] = _extract_section_list("Major Suggestions")
    data["questions"] = _extract_section_list("Questions for Author")
    data["design_strengths"] = _extract_section_list("Design Strengths")
    data["agreements"] = _extract_section_list("Points of Agreement")
    data["disagreements"] = _extract_section_list("Points of Disagreement")
    data["synthesis_notes"] = _extract_section_list("Synthesis Notes")

    return data


def build_consensus(
    responses: List[Dict[str, Any]],
    spec_id: str = "unknown",
    spec_title: str = "Specification",
) -> Dict[str, Any]:
    """
    Build consensus from multiple model responses using AI synthesis.

    This replaces fragile regex parsing with AI-based natural language synthesis.

    Args:
        responses: List of response dicts from parse_response()
        spec_id: Specification ID
        spec_title: Specification title

    Returns:
        Consensus dictionary with synthesis results
    """
    if not responses:
        return {
            "success": False,
            "error": "No valid responses to synthesize",
        }

    # Call AI synthesis (always 1 tool call, no fallback)
    synthesis_result = synthesize_with_ai(
        responses=responses,
        spec_id=spec_id,
        spec_title=spec_title,
        working_dir="/tmp",
    )

    if not synthesis_result.get("success"):
        return {
            "success": False,
            "error": synthesis_result.get("error", "Synthesis failed"),
        }

    synthesis_text = synthesis_result.get("synthesis_text", "")
    parsed_data = _parse_synthesis_text(synthesis_text)

    # Return synthesis in format expected by downstream code
    # The synthesis_text contains the full markdown synthesis
    return {
        "success": True,
        "num_models": synthesis_result.get("num_models", 0),
        "models": synthesis_result.get("models", []),
        "synthesis_text": synthesis_text,
        "consensus_level": parsed_data.get("consensus_level"),
        "critical_blockers": parsed_data.get("critical_blockers", []),
        "major_suggestions": parsed_data.get("major_suggestions", []),
        "questions": parsed_data.get("questions", []),
        "design_strengths": parsed_data.get("design_strengths", []),
        "agreements": parsed_data.get("agreements", []),
        "disagreements": parsed_data.get("disagreements", []),
        "synthesis_notes": parsed_data.get("synthesis_notes", []),
    }
