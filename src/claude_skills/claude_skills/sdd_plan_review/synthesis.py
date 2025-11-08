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
    working_dir: str = "/tmp"
) -> Dict[str, Any]:
    """
    Use AI to synthesize multiple model reviews into consensus.

    Instead of fragile regex parsing, let AI read natural language reviews
    and create structured synthesis.

    Args:
        responses: List of response dicts with "tool" and "raw_review" keys
        spec_id: Specification ID
        spec_title: Specification title
        working_dir: Working directory for AI tool

    Returns:
        Synthesized consensus dictionary
    """
    import subprocess
    import tempfile
    import os

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
        "- **Consensus Score**: X.X/10 (explain how you calculated from individual scores)",
        "- **Final Recommendation**: APPROVE/REVISE/REJECT",
        "- **Consensus Level**: Strong/Moderate/Weak/Conflicted (based on score variance)",
        "",
        "## Key Findings",
        "",
        "### Critical Issues (Must Fix)",
        "- Issue title - flagged by: [model names]",
        "  - Impact: ...",
        "  - Recommended fix: ...",
        "",
        "### High Priority Issues",
        "- Issue title - flagged by: [model names]",
        "",
        "### Medium/Low Priority",
        "- (Summarize briefly)",
        "",
        "## Points of Agreement",
        "- What all/most models agree on",
        "",
        "## Points of Disagreement  ",
        "- Where models conflict",
        "- Your assessment of the disagreement",
        "",
        "## Strengths Identified",
        "- Common strengths across reviews",
        "",
        "## Recommendations",
        "- Actionable next steps",
        "```",
        "",
        "**Important**:",
        "- Extract ALL scores mentioned and calculate consensus",
        "- Attribute issues to specific models (e.g., \"flagged by: gemini, codex\")",
        "- Note where models agree vs. disagree",
        "- Make a clear APPROVE/REVISE/REJECT recommendation with reasoning",
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

    # Call AI for synthesis using gemini (fast and capable)
    try:
        cmd = [
            "gemini",
            "-m", "gemini-2.5-pro",
            "-p", prompt
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=working_dir
        )

        if result.returncode != 0:
            return {
                "success": False,
                "error": f"AI synthesis failed: {result.stderr}"
            }

        synthesis_text = result.stdout

        # Handle gemini wrapper format
        if '{"response":' in synthesis_text and '"stats":' in synthesis_text:
            try:
                start = synthesis_text.find('{')
                end = synthesis_text.rfind('}') + 1
                wrapper = json.loads(synthesis_text[start:end])
                if "response" in wrapper:
                    synthesis_text = wrapper["response"]
            except:
                pass

        return {
            "success": True,
            "synthesis_text": synthesis_text,
            "num_models": len(responses),
            "models": [r.get("tool") for r in responses]
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "AI synthesis timed out after 120s"
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "gemini CLI not found - required for synthesis"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Synthesis error: {str(e)}"
        }



def build_consensus(
    responses: List[Dict[str, Any]],
    spec_id: str = "unknown",
    spec_title: str = "Specification"
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

    # Call AI synthesis
    synthesis_result = synthesize_with_ai(
        responses=responses,
        spec_id=spec_id,
        spec_title=spec_title,
        working_dir="/tmp"
    )

    if not synthesis_result.get("success"):
        return {
            "success": False,
            "error": synthesis_result.get("error", "Synthesis failed"),
        }

    # Return synthesis in format expected by downstream code
    # The synthesis_text contains the full markdown synthesis
    return {
        "success": True,
        "num_models": synthesis_result.get("num_models", 0),
        "models": synthesis_result.get("models", []),
        "synthesis_text": synthesis_result.get("synthesis_text", ""),
        # These are kept for compatibility but will be empty
        # The synthesis_text contains all the information
        "overall_score": None,
        "final_recommendation": None,
        "consensus_level": None,
        "all_issues": [],
        "all_strengths": [],
        "all_recommendations": [],
        "agreements": [],
        "disagreements": [],
    }
