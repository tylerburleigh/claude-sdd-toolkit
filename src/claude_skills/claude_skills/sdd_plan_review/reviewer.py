#!/usr/bin/env python3
"""
Multi-model review orchestration for sdd-plan-review.

Handles parallel execution of AI CLI tools and response collection.
"""

import subprocess
import json
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed, wait

from claude_skills.sdd_plan_review.prompts import generate_review_prompt
from claude_skills.sdd_plan_review.synthesis import parse_response, build_consensus
from claude_skills.common.ai_tools import check_tool_available


# Available AI CLI tools
AVAILABLE_TOOLS = {
    "gemini": {
        "command": "gemini",
        "version_flag": "--version",
        "timeout": 600,
    },
    "codex": {
        "command": "codex",
        "version_flag": "--version",
        "timeout": 600,
    },
    "cursor-agent": {
        "command": "cursor-agent",
        "version_flag": "--help",
        "timeout": 600,
    },
}


def detect_available_tools() -> List[str]:
    """
    Detect which AI CLI tools are installed and available.

    Returns:
        List of available tool names
    """
    available = []
    for tool_name in AVAILABLE_TOOLS.keys():
        if check_tool_available(tool_name, check_version=True):
            available.append(tool_name)
    return available


def call_tool(
    tool_name: str,
    prompt: str,
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    Call an AI CLI tool with a prompt.

    Args:
        tool_name: Name of tool to call
        prompt: Prompt to send
        timeout: Optional timeout override

    Returns:
        Result dictionary with success, output, error
    """
    tool_config = AVAILABLE_TOOLS.get(tool_name)
    if not tool_config:
        return {
            "success": False,
            "tool": tool_name,
            "error": f"Unknown tool: {tool_name}",
            "output": None,
            "duration": 0,
        }

    timeout = timeout or tool_config["timeout"]
    start_time = time.time()

    try:
        # Build command based on tool-specific CLI interface
        # Each tool has different requirements for non-interactive use

        if tool_name == "codex":
            # Codex: Use exec subcommand for non-interactive mode
            # Note: Don't use --json as it outputs JSONL stream; let it output markdown
            cmd = [
                tool_config["command"],
                "exec",                    # Non-interactive subcommand
                "--color", "never",        # No color codes in captured output
                prompt                     # Prompt as positional argument
            ]
            stdin_input = None

        elif tool_name == "gemini":
            # Gemini: Use plain text output (AI synthesis doesn't need JSON)
            cmd = [
                tool_config["command"],
                "-m", "gemini-2.5-pro",  # Model specification
                "--telemetry", "false",   # Disable telemetry for cleaner output
                "-p", prompt              # Prompt argument
            ]
            stdin_input = None

        elif tool_name == "cursor-agent":
            # Cursor Agent: Use --print for non-interactive mode with JSON output
            cmd = [
                tool_config["command"],
                "--print",                    # Non-interactive mode with all tools
                "--output-format", "json",    # JSON output for parsing
                prompt                         # Positional prompt argument
            ]
            stdin_input = None

        else:
            # Generic approach: pass prompt via stdin
            cmd = [tool_config["command"]]
            stdin_input = prompt

        # Execute the command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            input=stdin_input
        )

        duration = time.time() - start_time

        # Return structured response
        return {
            "success": result.returncode == 0,
            "tool": tool_name,
            "output": result.stdout if result.returncode == 0 else None,
            "error": result.stderr if result.returncode != 0 else None,
            "duration": duration,
        }

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return {
            "success": False,
            "tool": tool_name,
            "error": f"Timeout after {timeout}s",
            "output": None,
            "duration": duration,
        }

    except Exception as e:
        duration = time.time() - start_time
        return {
            "success": False,
            "tool": tool_name,
            "error": str(e),
            "output": None,
            "duration": duration,
        }


def review_with_tools(
    spec_content: str,
    tools: List[str],
    review_type: str = "full",
    spec_id: str = "unknown",
    spec_title: str = "Specification",
    parallel: bool = True
) -> Dict[str, Any]:
    """
    Review a spec using multiple AI tools with full synthesis.

    Args:
        spec_content: Specification content to review
        tools: List of tool names to use
        review_type: Type of review (quick, full, security, feasibility)
        spec_id: Specification ID
        spec_title: Specification title
        parallel: Run tools in parallel (vs sequential)

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
        "quick": "Completeness, Clarity",
        "full": "Completeness, Clarity, Feasibility, Architecture, Risk Management, Verification",
        "security": "Security vulnerabilities, Authentication, Authorization, Data handling, Risk Management",
        "feasibility": "Time estimates, Dependencies, Complexity, Resource requirements, Feasibility"
    }

    dimensions = review_dimensions.get(review_type, "All standard dimensions")

    print(f"\n   Sending {review_type} review to {len(tools)} external AI model(s): {', '.join(tools)}")
    print(f"   Evaluating: {dimensions}")

    # Execute tools
    if parallel and len(tools) > 1:
        # Parallel execution
        with ThreadPoolExecutor(max_workers=len(tools)) as executor:
            futures = {
                executor.submit(call_tool, tool, prompt): tool
                for tool in tools
            }

            for future in as_completed(futures):
                tool = futures[future]
                try:
                    result = future.result(timeout=150)
                    if result["success"]:
                        results["raw_responses"].append(result)
                        # Show progress as each tool completes
                        duration = result.get("duration", 0)
                        print(f"   ✓ {tool} completed ({duration:.1f}s)")
                    else:
                        results["failures"].append(result)
                        # Show failure
                        error = result.get("error", "unknown error")
                        print(f"   ✗ {tool} failed: {error}")
                except Exception as e:
                    results["failures"].append({
                        "success": False,
                        "tool": tool,
                        "error": str(e),
                        "output": None,
                        "duration": 0,
                    })
                    print(f"   ✗ {tool} exception: {str(e)}")
    else:
        # Sequential execution
        for tool in tools:
            result = call_tool(tool, prompt)
            if result["success"]:
                results["raw_responses"].append(result)
                # Show progress as each tool completes
                duration = result.get("duration", 0)
                print(f"   ✓ {tool} completed ({duration:.1f}s)")
            else:
                results["failures"].append(result)
                # Show failure
                error = result.get("error", "unknown error")
                print(f"   ✗ {tool} failed: {error}")

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

    return results
