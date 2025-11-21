"""
AI Consultation for Documentation Generation

Shells out to external AI CLI tools to generate contextual documentation
(e.g., architecture.md and supporting guidance) based on structural analysis.

Uses shared AI tool utilities from claude_skills.common.ai_tools and the
provider abstraction so consultations are routed through a consistent
registry and response envelope.

This module provides documentation-specific functionality:
- Prompt formatting for architecture and AI context research
- Document composition with proper formatting
- High-level orchestration for documentation generation workflows
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
import time

from claude_skills.common.ai_tools import (
    detect_available_tools,
    get_enabled_and_available_tools,
    execute_tools_parallel,
    execute_tool_with_fallback,
    ToolStatus,
)
from claude_skills.common import ai_config
from claude_skills.common.ai_config import ALL_SUPPORTED_TOOLS
from claude_skills.common import consultation_limits

# =============================================================================
# CONFIGURATION
# =============================================================================

# Documentation type routing (which tool is best for which doc type)
DOC_TYPE_ROUTING = {
    "architecture": ("cursor-agent", "gemini"),   # cursor-agent good for architecture
    "ai_context": ("gemini", "cursor-agent"),     # gemini good for quick context
    "developer_guide": ("codex", "gemini"),       # codex good for code examples
}


def _build_context(doc_type: Optional[str]) -> Optional[Dict[str, Any]]:
    if not doc_type:
        return None
    return {"doc_type": doc_type}


def get_model_for_tool(
    tool: str,
    doc_type: Optional[str] = None,
    override: Any = None,
) -> Optional[str]:
    """
    Resolve the preferred model for a given tool, honoring CLI overrides and config.
    """
    context = _build_context(doc_type)
    return ai_config.resolve_tool_model(
        "llm-doc-gen",
        tool,
        override=override,
        context=context,
    )


def resolve_models_for_tools(
    tools: Sequence[str],
    doc_type: Optional[str] = None,
    override: Any = None,
) -> Dict[str, Optional[str]]:
    """
    Resolve models for multiple tools while preserving order.
    """
    context = _build_context(doc_type)
    ordered = ai_config.resolve_models_for_tools(
        "llm-doc-gen",
        tools,
        override=override,
        context=context,
    )
    return dict(ordered)

def get_available_tools() -> List[str]:
    """
    Check which AI CLI tools are available.

    Delegates to shared utility function for consistency across skills.

    Returns:
        List of available tool names
    """
    return get_enabled_and_available_tools("llm-doc-gen")


def get_best_tool(doc_type: str, available_tools: Optional[List[str]] = None) -> Optional[str]:
    """
    Get the best available tool for a documentation type.

    Args:
        doc_type: Type of documentation (architecture, ai_context, developer_guide)
        available_tools: List of available tools (auto-detected if None)

    Returns:
        Tool name or None if no tools available
    """
    if available_tools is None:
        available_tools = get_available_tools()

    if not available_tools:
        return None

    if doc_type not in DOC_TYPE_ROUTING:
        return available_tools[0]

    primary, fallback = DOC_TYPE_ROUTING[doc_type]

    if primary in available_tools:
        return primary
    elif fallback in available_tools:
        return fallback
    else:
        return available_tools[0] if available_tools else None


def format_architecture_research_prompt(
    context_summary: str,
    key_files: List[str],
    project_root: Path
) -> str:
    """
    Format prompt for architecture research (read-only analysis).

    Args:
        context_summary: Structured codebase context summary
        key_files: List of key file paths to read
        project_root: Project root directory

    Returns:
        Formatted prompt string asking for research findings only
    """
    prompt_parts = []

    prompt_parts.append("# Task: Architecture Research (Read-Only)")
    prompt_parts.append("")
    prompt_parts.append("**IMPORTANT: You have READ-ONLY access. Do not attempt to write files.**")
    prompt_parts.append("Analyze this codebase and provide research findings about its architecture.")
    prompt_parts.append("Your findings will be used by another agent to compose the final documentation.")
    prompt_parts.append("")

    # Add context summary
    prompt_parts.append("## Codebase Context")
    prompt_parts.append(context_summary)

    # Add key files for AI to read
    prompt_parts.append("## Key Files to Analyze")
    prompt_parts.append("")
    prompt_parts.append("Please read and analyze these files:")
    for file in key_files[:10]:  # Top 10 files
        file_path = project_root / file
        if file_path.exists():
            prompt_parts.append(f"- {file}")
    prompt_parts.append("")

    # Instructions for research output
    prompt_parts.append("## Research Findings to Provide")
    prompt_parts.append("")
    prompt_parts.append("Analyze the code and provide findings for each of these areas:")
    prompt_parts.append("")
    prompt_parts.append("### 1. System Overview")
    prompt_parts.append("- What does this system do? (2-3 sentences)")
    prompt_parts.append("- Who are the intended users?")
    prompt_parts.append("- What problem does it solve?")
    prompt_parts.append("")
    prompt_parts.append("### 2. Component Identification")
    prompt_parts.append("- List the major components/modules you identified")
    prompt_parts.append("- Describe the responsibility of each component")
    prompt_parts.append("- Note key relationships between components")
    prompt_parts.append("")
    prompt_parts.append("### 3. Data Flow Observations")
    prompt_parts.append("- How does data move through the system?")
    prompt_parts.append("- What is the request/response lifecycle (if applicable)?")
    prompt_parts.append("- How is state managed?")
    prompt_parts.append("")
    prompt_parts.append("### 4. Design Patterns Detected")
    prompt_parts.append("- Which design patterns do you see in use?")
    prompt_parts.append("- Where are they applied?")
    prompt_parts.append("- Why might they have been chosen?")
    prompt_parts.append("")
    prompt_parts.append("### 5. Technology Stack Analysis")
    prompt_parts.append("- What are the core technologies used?")
    prompt_parts.append("- What are the key dependencies and their purposes?")
    prompt_parts.append("- Why might these choices have been made?")
    prompt_parts.append("")
    prompt_parts.append("### 6. Architectural Decisions")
    prompt_parts.append("- What important architectural decisions can you identify?")
    prompt_parts.append("- What trade-offs were made?")
    prompt_parts.append("- Are there any notable constraints or limitations?")
    prompt_parts.append("")
    prompt_parts.append("## Output Format")
    prompt_parts.append("")
    prompt_parts.append("Provide your research findings as structured text with clear section headers.")
    prompt_parts.append("Use markdown formatting for readability (headers, lists, code references).")
    prompt_parts.append("Be specific and reference actual code when making observations.")
    prompt_parts.append("")
    prompt_parts.append("**DO NOT write files or attempt to create architecture.md yourself.**")
    prompt_parts.append("Just return your research findings as text output.")

    return "\n".join(prompt_parts)


def format_ai_context_research_prompt(
    context_summary: str,
    key_files: List[str],
    project_root: Path
) -> str:
    """
    Format prompt for AI context research (read-only analysis).

    Args:
        context_summary: Structured codebase context summary
        key_files: List of key file paths
        project_root: Project root directory

    Returns:
        Formatted prompt string asking for research findings only
    """
    prompt_parts = []

    prompt_parts.append("# Task: AI Context Research (Read-Only)")
    prompt_parts.append("")
    prompt_parts.append("**IMPORTANT: You have READ-ONLY access. Do not attempt to write files.**")
    prompt_parts.append("Analyze this codebase and identify key information that would help AI coding assistants.")
    prompt_parts.append("Your findings will be used by another agent to compose the final AI context guidance.")
    prompt_parts.append("")

    # Add context
    prompt_parts.append("## Codebase Context")
    prompt_parts.append(context_summary)

    prompt_parts.append("## Key Files to Analyze")
    for file in key_files[:8]:  # Top 8 files
        prompt_parts.append(f"- {file}")
    prompt_parts.append("")

    # Instructions
    prompt_parts.append("## Research Findings to Provide")
    prompt_parts.append("")
    prompt_parts.append("Analyze the code and provide findings for each of these areas:")
    prompt_parts.append("")
    prompt_parts.append("### 1. Project Overview")
    prompt_parts.append("- What is this project? (3-4 sentences)")
    prompt_parts.append("- What does it do?")
    prompt_parts.append("- Who uses it?")
    prompt_parts.append("")
    prompt_parts.append("### 2. Domain Concepts")
    prompt_parts.append("- Identify 5-10 domain-specific terms AI assistants should know")
    prompt_parts.append("- Provide brief definitions for each")
    prompt_parts.append("- Note where these concepts are used in the code")
    prompt_parts.append("")
    prompt_parts.append("### 3. Critical Files Analysis")
    prompt_parts.append("- List the 5-10 most important files")
    prompt_parts.append("- Describe what each file does and why it's critical")
    prompt_parts.append("- Note dependencies between critical files")
    prompt_parts.append("")
    prompt_parts.append("### 4. Common Workflow Patterns")
    prompt_parts.append("- Identify 3-5 common development tasks")
    prompt_parts.append("- Describe how each task is typically accomplished")
    prompt_parts.append("- Examples: 'Adding a new endpoint', 'Adding validation', etc.")
    prompt_parts.append("")
    prompt_parts.append("### 5. Potential Gotchas")
    prompt_parts.append("- Identify 3-5 things AI assistants should watch out for")
    prompt_parts.append("- Note common mistakes or tricky patterns")
    prompt_parts.append("- Explain why these are potential pitfalls")
    prompt_parts.append("")
    prompt_parts.append("### 6. Extension Patterns")
    prompt_parts.append("- Describe the general pattern for extending the codebase")
    prompt_parts.append("- Where do new features typically go?")
    prompt_parts.append("- What conventions should be followed?")
    prompt_parts.append("")
    prompt_parts.append("## Output Format")
    prompt_parts.append("")
    prompt_parts.append("Provide your research findings as structured text with clear section headers.")
    prompt_parts.append("Keep it concise - this is a quick reference, not comprehensive documentation.")
    prompt_parts.append("Use markdown formatting for readability.")
    prompt_parts.append("")
    prompt_parts.append("**DO NOT write files or attempt to create dedicated AI context docs yourself.**")
    prompt_parts.append("Just return your research findings as text output.")

    return "\n".join(prompt_parts)


def compose_architecture_doc(
    research_findings: str,
    project_name: str,
    version: str = "1.0.0"
) -> str:
    """
    Compose architecture.md from research findings.

    Args:
        research_findings: Raw research output from AI consultation
        project_name: Project name for header
        version: Project version

    Returns:
        Formatted architecture.md content
    """
    from datetime import datetime

    doc_parts = []

    # Header
    doc_parts.append(f"# {project_name} - Architecture Documentation")
    doc_parts.append("")
    doc_parts.append(f"**Version:** {version}")
    doc_parts.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    doc_parts.append("")
    doc_parts.append("---")
    doc_parts.append("")

    # Introduction
    doc_parts.append("## Introduction")
    doc_parts.append("")
    doc_parts.append("This document describes the architecture of the codebase, including system design,")
    doc_parts.append("component structure, data flow, and key design decisions.")
    doc_parts.append("")
    doc_parts.append("---")
    doc_parts.append("")

    # Research findings
    doc_parts.append("## Architecture Analysis")
    doc_parts.append("")
    doc_parts.append(research_findings)
    doc_parts.append("")

    # Footer
    doc_parts.append("---")
    doc_parts.append("")
    doc_parts.append("*This documentation was generated with assistance from AI analysis.*")

    return "\n".join(doc_parts)


def compose_ai_context_doc(
    research_findings: str,
    project_name: str,
    version: str = "1.0.0"
) -> str:
    """
    Compose AI context guidance from research findings.

    Args:
        research_findings: Raw research output from AI consultation
        project_name: Project name for header
        version: Project version

    Returns:
        Formatted AI context guidance content
    """
    from datetime import datetime

    doc_parts = []

    # Header
    doc_parts.append(f"# {project_name} - AI Assistant Context")
    doc_parts.append("")
    doc_parts.append(f"**Version:** {version}")
    doc_parts.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    doc_parts.append("")
    doc_parts.append("---")
    doc_parts.append("")

    # Introduction
    doc_parts.append("## About This Document")
    doc_parts.append("")
    doc_parts.append("This is a quick reference guide for AI coding assistants working with this codebase.")
    doc_parts.append("It provides essential context, key concepts, and common patterns to help AI assistants")
    doc_parts.append("provide better suggestions and understand the codebase structure.")
    doc_parts.append("")
    doc_parts.append("---")
    doc_parts.append("")

    # Research findings
    doc_parts.append(research_findings)
    doc_parts.append("")

    # Footer
    doc_parts.append("---")
    doc_parts.append("")
    doc_parts.append("*This context was generated with assistance from AI analysis.*")

    return "\n".join(doc_parts)


def run_consultation(
    tool: str,
    prompt: str,
    dry_run: bool = False,
    verbose: bool = False,
    printer: Optional['PrettyPrinter'] = None,
    doc_type: Optional[str] = None,
    model_override: Any = None,
    tracker: Optional[consultation_limits.ConsultationTracker] = None,
) -> Tuple[bool, str]:
    """
    Run consultation with an AI tool.

    Args:
        tool: Tool name (cursor-agent, gemini, codex)
        prompt: Formatted prompt
        dry_run: If True, show command without running
        verbose: Enable verbose output
        printer: Optional PrettyPrinter for consistent output (falls back to print if None)
        doc_type: Optional documentation type for contextual model overrides
        model_override: Optional CLI override (string or mapping)
        tracker: Optional ConsultationTracker instance for limiting tool usage

    Returns:
        Tuple of (success: bool, output: str)
    """
    resolved_model = get_model_for_tool(tool, doc_type=doc_type, override=model_override)
    timeout = ai_config.get_timeout("code-doc", "consultation")

    if tool not in ALL_SUPPORTED_TOOLS:
        return False, f"Unknown tool '{tool}'. Available tools: {', '.join(ALL_SUPPORTED_TOOLS)}"

    if dry_run:
        model_note = f"model={resolved_model}" if resolved_model else "default model"
        msg = (
            f"Would consult {tool} ({model_note}) "
            f"with prompt length {len(prompt)} chars [timeout={timeout}s]"
        )
        if printer:
            printer.detail(msg)
        else:
            print(msg)
            sys.stdout.flush()
        return True, msg

    # Determine what type of research from prompt
    if "Architecture" in prompt:
        task_type = "architecture analysis"
        task_areas = "System Overview, Components, Data Flow, Design Patterns, Technology Stack, Decisions"
    elif "AI Context" in prompt:
        task_type = "AI context generation"
        task_areas = "Project Overview, Domain Concepts, Critical Files, Workflows, Gotchas, Extensions"
    else:
        task_type = "analysis"
        task_areas = "code structure and patterns"

    # Print status message before running (this may take a while)
    if printer:
        printer.detail(f"\n🤖 Consulting {tool} for {task_type}...")
        printer.detail(f"   Analyzing: {task_areas}")
        if verbose:
            printer.info("=" * 60)
    else:
        print(f"\n🤖 Consulting {tool} for {task_type}...")
        print(f"   Analyzing: {task_areas}")
        if verbose:
            print("=" * 60)
        sys.stdout.flush()

    response = execute_tool_with_fallback(
        skill_name="code-doc",
        tool=tool,
        prompt=prompt,
        model=resolved_model,
        timeout=timeout,
        context={"doc_type": doc_type} if doc_type else None,
        tracker=tracker,
    )

    if response.success:
        return True, response.output

    if response.status == ToolStatus.TIMEOUT:
        message = f"{tool} timed out after {timeout} seconds"
    elif response.status == ToolStatus.NOT_FOUND:
        message = (
            f"{tool} not found. Install one of {', '.join(ALL_SUPPORTED_TOOLS)} "
            "and ensure it is on PATH."
        )
    else:
        message = response.error or f"{tool} consultation failed (status={response.status.value})"

    return False, message


def consult_multi_agent(
    doc_type: str,
    prompt: str,
    agents: Optional[Sequence[str]] = None,
    dry_run: bool = False,
    verbose: bool = False,
    printer: Optional['PrettyPrinter'] = None,
    model_override: Any = None,
) -> Dict[str, any]:
    """
    Consult multiple AI tools in parallel and synthesize responses.

    Args:
        doc_type: Documentation type (architecture, ai_context)
        prompt: Formatted prompt
        agents: Optional sequence of agent names to consult. Defaults to the
            configured consensus agent list for code-doc.
        dry_run: If True, show what would run
        verbose: Enable verbose output
        printer: Optional PrettyPrinter for consistent output (falls back to print if None)

    Returns:
        Dictionary with synthesis results
    """
    configured_agents = ai_config.get_consensus_agents("code-doc")
    available_tools = get_available_tools()

    if not available_tools:
        return {
            "success": False,
            "error": "No AI tools available",
            "responses": []
        }

    if agents:
        override_list: List[str] = []
        seen = set()
        for entry in agents:
            for token in str(entry).split(","):
                token = token.strip()
                if token and token not in seen:
                    override_list.append(token)
                    seen.add(token)
        candidate_agents = override_list or configured_agents
    else:
        candidate_agents = configured_agents

    selected_agents = [tool for tool in candidate_agents if tool in available_tools]

    if not selected_agents:
        selected_agents = [tool for tool in available_tools]

    if len(selected_agents) < 2 and len(available_tools) >= 2:
        supplemental = [tool for tool in available_tools if tool not in selected_agents]
        selected_agents.extend(supplemental[: 2 - len(selected_agents)])

    # Deduplicate while preserving order
    seen_agents: set[str] = set()
    ordered_agents: List[str] = []
    for tool in selected_agents:
        if tool not in seen_agents:
            seen_agents.add(tool)
            ordered_agents.append(tool)

    if len(ordered_agents) < 2:
        # Fall back to single-tool consultation
        single_tool = ordered_agents[0]
        success, output = run_consultation(
            single_tool,
            prompt,
            dry_run=dry_run,
            verbose=verbose,
            printer=printer,
            doc_type=doc_type,
            model_override=model_override,
        )
        return {
            "success": success,
            "primary_tool": single_tool,
            "output": output,
            "responses": [{
                "tool": single_tool,
                "success": success,
                "output": output
            }]
        }

    resolved_models = resolve_models_for_tools(
        ordered_agents,
        doc_type=doc_type,
        override=model_override,
    )

    if dry_run:
        if printer:
            printer.detail(f"Would consult {len(ordered_agents)} tools in parallel:")
            for tool in ordered_agents:
                model = resolved_models.get(tool)
                suffix = f" (model: {model})" if model else ""
                printer.detail(f"  - {tool}{suffix}")
        else:
            print(f"Would consult {len(ordered_agents)} tools in parallel:")
            for tool in ordered_agents:
                model = resolved_models.get(tool)
                suffix = f" (model: {model})" if model else ""
                print(f"  - {tool}{suffix}")
            sys.stdout.flush()
        return {"success": True, "responses": []}

    # Determine task description and areas (always show, regardless of verbose)
    task_desc = "architecture analysis" if "Architecture" in prompt else "AI context generation"
    if "Architecture" in prompt:
        task_areas = "System Overview, Component Identification, Data Flow, Design Patterns, Technology Stack, Architectural Decisions"
    else:
        task_areas = "Project Overview, Domain Concepts, Critical Files, Common Workflows, Potential Gotchas, Extension Patterns"

    # Print status message before running (this may take a while)
    enabled_tools_map = ai_config.get_enabled_tools("code-doc")
    final_agents = [agent for agent in ordered_agents if agent in enabled_tools_map]

    if printer:
        printer.detail(f"\n🤖 Consulting {len(final_agents)} AI models in parallel for {task_desc}...")
        printer.detail(f"   Tools: {', '.join(final_agents)}")
        printer.detail(f"   Analyzing: {task_areas}")
        if verbose:
            printer.info("=" * 60)
    else:
        print(f"\n🤖 Consulting {len(final_agents)} AI models in parallel for {task_desc}...")
        print(f"   Tools: {', '.join(final_agents)}")
        print(f"   Analyzing: {task_areas}")
        if verbose:
            print("=" * 60)
        sys.stdout.flush()

    # Use shared utility for parallel execution
    start_time = time.time()
    multi_response = execute_tools_parallel(
        tools=final_agents,
        prompt=prompt,
        models=resolved_models,
    )
    total_duration = time.time() - start_time

    # Print completion messages if verbose
    if verbose:
        for tool, response in multi_response.responses.items():
            status = "✓" if response.success else "✗"
            msg = f"{status} {response.tool} completed ({response.duration:.1f}s)"
            if printer:
                printer.info(msg)
            else:
                print(msg)
                sys.stdout.flush()

    # Convert to code-doc's expected format
    if multi_response.success:
        # Build responses_by_tool dict from successful responses
        responses_by_tool = {
            r.tool: r.output
            for r in multi_response.responses.values()
            if r.success
        }

        # Convert responses to dict format for backwards compatibility
        responses = [
            {
                "tool": r.tool,
                "success": r.success,
                "output": r.output,
                "duration": r.duration
            }
            for r in multi_response.responses.values()
        ]

        return {
            "success": True,
            "tools_consulted": list(responses_by_tool.keys()),
            "responses_by_tool": responses_by_tool,
            "responses": responses,
            "total_duration": total_duration
        }
    else:
        # Convert failed responses to dict format
        responses = [
            {
                "tool": r.tool,
                "success": r.success,
                "output": r.output,
                "duration": r.duration
            }
            for r in multi_response.responses.values()
        ]

        return {
            "success": False,
            "error": "All consultations failed",
            "responses": responses,
            "total_duration": total_duration
        }


# _run_tool_capture() removed - now using execute_tools_parallel() from ai_tools


def generate_architecture_docs(
    context_summary: str,
    key_files: List[str],
    project_root: Path,
    tool: str = "auto",
    use_multi_agent: bool = True,
    dry_run: bool = False,
    verbose: bool = False,
    printer: Optional['PrettyPrinter'] = None,
    model_override: Any = None,
) -> Tuple[bool, Dict]:
    """
    Get architecture research findings from AI consultation.

    Args:
        context_summary: Codebase context summary
        key_files: List of key files
        project_root: Project root directory
        tool: Specific tool to use ("auto" for auto-selection)
        use_multi_agent: Use multiple agents if available
        dry_run: Show what would run without running
        verbose: Enable verbose output
        printer: Optional PrettyPrinter for consistent output

    Returns:
        Tuple of (success: bool, result: Dict with responses_by_tool)
    """
    prompt = format_architecture_research_prompt(context_summary, key_files, project_root)

    if use_multi_agent:
        result = consult_multi_agent(
            "architecture",
            prompt,
            agents=None,
            dry_run=dry_run,
            verbose=verbose,
            printer=printer,
            model_override=model_override,
        )
        return result["success"], result
    else:
        if tool == "auto":
            tool = get_best_tool("architecture")
            if not tool:
                return False, {"error": "No AI tools available"}

        success, output = run_consultation(
            tool,
            prompt,
            dry_run,
            verbose,
            printer,
            doc_type="architecture",
            model_override=model_override,
        )
        return success, {"responses_by_tool": {tool: output} if success else {}}


def generate_ai_context_docs(
    context_summary: str,
    key_files: List[str],
    project_root: Path,
    tool: str = "auto",
    use_multi_agent: bool = True,
    dry_run: bool = False,
    verbose: bool = False,
    printer: Optional['PrettyPrinter'] = None,
    model_override: Any = None,
) -> Tuple[bool, Dict]:
    """
    Get AI context research findings from AI consultation.

    Args:
        context_summary: Codebase context summary
        key_files: List of key files
        project_root: Project root directory
        tool: Specific tool to use ("auto" for auto-selection)
        use_multi_agent: Use multiple agents if available
        dry_run: Show what would run without running
        verbose: Enable verbose output
        printer: Optional PrettyPrinter for consistent output

    Returns:
        Tuple of (success: bool, result: Dict with responses_by_tool)
    """
    prompt = format_ai_context_research_prompt(context_summary, key_files, project_root)

    if use_multi_agent:
        result = consult_multi_agent(
            "ai_context",
            prompt,
            agents=None,
            dry_run=dry_run,
            verbose=verbose,
            printer=printer,
            model_override=model_override,
        )
        return result["success"], result
    else:
        if tool == "auto":
            tool = get_best_tool("ai_context")
            if not tool:
                return False, {"error": "No AI tools available"}

        success, output = run_consultation(
            tool,
            prompt,
            dry_run,
            verbose,
            printer,
            doc_type="ai_context",
            model_override=model_override,
        )
        return success, {"responses_by_tool": {tool: output} if success else {}}
