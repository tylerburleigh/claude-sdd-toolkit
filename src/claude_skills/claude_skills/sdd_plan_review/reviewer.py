#!/usr/bin/env python3
"""
Multi-model review orchestration for sdd-plan-review.

Orchestrates parallel execution of AI CLI tools for specification review.
Uses shared implementations from common.ai_tools for tool detection and
execution, with response synthesis and consensus building.
"""

import subprocess
import json
import time
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from claude_skills.sdd_plan_review.prompts import generate_review_prompt
from claude_skills.sdd_plan_review.synthesis import parse_response, build_consensus
from claude_skills.common.ai_tools import check_tool_available, execute_tools_parallel
from claude_skills.common import ai_config


def review_with_tools(
    spec_content: str,
    tools: List[str],
    review_type: str = "full",
    spec_id: str = "unknown",
    spec_title: str = "Specification",
    parallel: bool = True,
    model_override: Any = None,
    silent: bool = False,
) -> Dict[str, Any]:
    """
    Review a spec using multiple AI tools with full synthesis.

    Uses execute_tools_parallel() from common.ai_tools for parallel execution.

    Args:
        spec_content: Specification content to review
        tools: List of tool names to use
        review_type: Type of review (quick, full, security, feasibility)
        spec_id: Specification ID
        spec_title: Specification title
        parallel: Deprecated - tools always run in parallel (kept for compatibility)

    Returns:
        Review results with parsed responses and consensus
    """
    results = {
        "review_type": review_type,
        "spec_id": spec_id,
        "spec_title": spec_title,
        "tools_used": tools,
        "raw_responses": [],
        "parsed_responses": [],
        "failures": [],
        "execution_time": 0,
        "consensus": None,
    }

    start_time = time.time()

    # Generate review prompt using new prompts module
    prompt = generate_review_prompt(spec_content, review_type, spec_id, spec_title)

    # Show what we're asking the external AI models to evaluate
    review_dimensions = {
        "quick": "Critical blockers, Questions for clarification",
        "full": "Completeness, Architecture, Data Model, Interface Design, Security, Verification",
        "security": "Security vulnerabilities, Authentication, Authorization, Data protection",
        "feasibility": "Technical complexity, Dependencies, Integration challenges, Implementation risks"
    }

    dimensions = review_dimensions.get(review_type, "All standard dimensions")

    enabled_tools = [tool for tool in tools if tool]
    if not enabled_tools:
        raise ValueError("No tools specified for plan review execution.")

    if not silent:
        print(f"\n   Sending {review_type} review to {len(enabled_tools)} external AI model(s): {', '.join(enabled_tools)}")
        print(f"   Evaluating: {dimensions}")

    resolved_models = ai_config.resolve_models_for_tools(
        "sdd-plan-review",
        enabled_tools,
        override=model_override,
        context={"review_type": review_type} if review_type else None,
    )

    # Execute tools in parallel using shared implementation
    multi_response = execute_tools_parallel(
        tools=enabled_tools,
        prompt=prompt,
        models=dict(resolved_models),
        timeout=600
    )

    # Process responses - convert to dict format for backward compatibility
    for tool, response in multi_response.responses.items():
        result = {
            "success": response.success,
            "tool": response.tool,
            "output": response.output if response.success else None,
            "error": response.error if not response.success else None,
            "duration": response.duration,
        }

        if response.success:
            results["raw_responses"].append(result)
            if not silent:
                print(f"   ✓ {tool} completed ({response.duration:.1f}s)")
        else:
            results["failures"].append(result)
            if not silent:
                print(f"   ✗ {tool} failed: {response.error or 'unknown error'}")

    # Parse responses using synthesis module
    for raw_response in results["raw_responses"]:
        if raw_response.get("output"):
            parsed = parse_response(raw_response["output"], raw_response["tool"])
            if parsed["success"]:
                results["parsed_responses"].append(parsed["parsed_data"])
            else:
                results["failures"].append({
                    "success": False,
                    "tool": raw_response["tool"],
                    "error": f"Parse failed: {parsed.get('error')}",
                    "output": None,
                    "duration": raw_response.get("duration", 0),
                })

    # Build consensus from parsed responses using AI synthesis
    if results["parsed_responses"]:
        results["consensus"] = build_consensus(
            results["parsed_responses"],
            spec_id=spec_id,
            spec_title=spec_title
        )
    else:
        results["consensus"] = {
            "success": False,
            "error": "No valid responses to synthesize",
        }

    results["execution_time"] = time.time() - start_time
    results["models"] = dict(resolved_models)

    return results
