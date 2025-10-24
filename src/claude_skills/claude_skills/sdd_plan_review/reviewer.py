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


def check_tool_available(tool_name: str) -> bool:
    """
    Check if an AI CLI tool is available.

    Args:
        tool_name: Name of the tool (gemini, codex, cursor-agent)

    Returns:
        True if tool is available, False otherwise
    """
    tool_config = AVAILABLE_TOOLS.get(tool_name)
    if not tool_config:
        return False

    try:
        # Check if command exists
        result = subprocess.run(
            ["which", tool_config["command"]],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return False

        # Quick version check
        result = subprocess.run(
            [tool_config["command"], tool_config["version_flag"]],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False


def detect_available_tools() -> List[str]:
    """
    Detect which AI CLI tools are installed and available.

    Returns:
        List of available tool names
    """
    available = []
    for tool_name in AVAILABLE_TOOLS.keys():
        if check_tool_available(tool_name):
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
        # Write prompt to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt)
            prompt_file = f.name

        try:
            # Attempt to call the tool
            # Note: Real implementation would vary by tool's actual CLI interface
            # This is a simplified version that may need tool-specific adjustments
            if tool_name == "codex":
                # Codex CLI: codex chat "prompt"
                cmd = [tool_config["command"], "chat", prompt[:1000]]  # Truncate for safety
            elif tool_name == "gemini":
                # Gemini CLI might use: gemini generate --prompt "..."
                cmd = [tool_config["command"], "generate", "--prompt", prompt[:1000]]
            else:
                # Generic approach: pass prompt as stdin
                cmd = [tool_config["command"]]

            # For now, just return a placeholder response indicating the tool was called
            # Real implementation would parse actual tool output
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                input=prompt if tool_name not in ["codex", "gemini"] else None
            )

            duration = time.time() - start_time

            # Note: In production, this would parse the actual tool response
            # For now, return a structured response indicating success
            return {
                "success": result.returncode == 0,
                "tool": tool_name,
                "output": result.stdout if result.returncode == 0 else None,
                "error": result.stderr if result.returncode != 0 else None,
                "duration": duration,
            }

        finally:
            # Clean up temp file
            try:
                Path(prompt_file).unlink()
            except:
                pass

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
                    else:
                        results["failures"].append(result)
                except Exception as e:
                    results["failures"].append({
                        "success": False,
                        "tool": tool,
                        "error": str(e),
                        "output": None,
                        "duration": 0,
                    })
    else:
        # Sequential execution
        for tool in tools:
            result = call_tool(tool, prompt)
            if result["success"]:
                results["raw_responses"].append(result)
            else:
                results["failures"].append(result)

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

    # Build consensus from parsed responses
    if results["parsed_responses"]:
        results["consensus"] = build_consensus(results["parsed_responses"])
    else:
        results["consensus"] = {
            "success": False,
            "error": "No valid responses to synthesize",
        }

    results["execution_time"] = time.time() - start_time

    return results
