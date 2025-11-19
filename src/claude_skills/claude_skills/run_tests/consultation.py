"""
External Tool Consultation Operations

Handles consultation with external CLI tools (Gemini, Codex, Cursor) for test
debugging. Provides auto-routing based on failure type and prompt formatting.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, NamedTuple, Sequence
import time

# Add parent directory to path to import sdd_common

from claude_skills.common import PrettyPrinter
from claude_skills.common.ai_tools import (
    build_tool_command, execute_tool_with_fallback, execute_tools_parallel,
    ToolResponse, ToolStatus, MultiToolResponse, detect_available_tools,
    get_enabled_and_available_tools,
)
from claude_skills.common import ai_config
from claude_skills.common.ai_config import ALL_SUPPORTED_TOOLS
from claude_skills.common import consultation_limits


# =============================================================================
# MODEL CONFIGURATION LOADING
# =============================================================================

def load_model_config() -> Dict:
    """
    Load model configuration from `.claude/ai_config.yaml` using the shared ai_config module.

    Returns:
        Dict with model configuration including priorities and overrides
    """
    config = ai_config.load_skill_config('run-tests')
    return config.get('models', {})


def get_model_for_tool(
    tool: str,
    failure_type: Optional[str] = None,
    override: Any = None,
) -> Optional[str]:
    """
    Get the best model for a tool, considering priority and failure-type overrides.

    Args:
        tool: Tool name (gemini, codex, cursor-agent)
        failure_type: Optional failure type for override lookup
        override: Optional CLI override (string or mapping)

    Returns:
        Model name to use, or None if no model is configured
    """
    context: Optional[Dict[str, Any]] = None
    if failure_type:
        context = {"failure_type": failure_type}

    return ai_config.resolve_tool_model(
        "run-tests",
        tool,
        override=override,
        context=context,
    )


def get_flags_for_tool(tool: str) -> List[str]:
    """
    Get additional CLI flags for a tool from configuration.

    Args:
        tool: Tool name

    Returns:
        List of additional flags
    """
    # Load config
    model_config = load_model_config()

    if not model_config or tool not in model_config:
        # Fallback to hardcoded TOOL_FLAGS (defined below)
        return TOOL_FLAGS.get(tool, [])

    tool_config = model_config[tool]

    # Handle case where tool_config is a string (e.g., just a model name)
    if isinstance(tool_config, dict):
        return tool_config.get('flags', TOOL_FLAGS.get(tool, []))

    # If not a dict, it can't have flags, so use default
    return TOOL_FLAGS.get(tool, [])


# =============================================================================
# CONSENSUS CONFIGURATION
# =============================================================================

def _resolve_consensus_agents(agents_override: Optional[Sequence[str]] = None) -> List[str]:
    """
    Determine the ordered list of agents to use for consensus consultation.

    Args:
        agents_override: Optional explicit agent order supplied by the caller.

    Returns:
        List of agent names in consultation order.
    """
    if agents_override:
        normalized = _dedupe_preserve_order(list(agents_override))
        if normalized:
            return normalized

    configured_agents = ai_config.get_consensus_agents('run-tests')
    if configured_agents:
        return configured_agents

    return ai_config.DEFAULT_CONSENSUS_AGENTS.copy()


def should_auto_trigger_consensus(failure_type: str) -> bool:
    """
    Check if a failure type should automatically trigger multi-agent consensus.

    Args:
        failure_type: Type of test failure

    Returns:
        True if consensus should be auto-triggered, False otherwise.
        Uses the boolean map defined in `consensus.auto_trigger`, falling back
        to the default entry when a specific failure type is not present.
    """
    routing = ai_config.get_routing_config('run-tests')
    if failure_type in routing:
        return routing[failure_type]
    return routing.get("default", False)


def get_consultation_timeout() -> int:
    """
    Get consultation timeout from config using shared ai_config module.

    Returns:
        Timeout in seconds (default: 90)
    """
    return ai_config.get_timeout('run-tests', 'consultation')


# =============================================================================
# CONFIGURATION - Customize these settings for your environment
# =============================================================================

# Additional flags for each tool
# Customize these if you need different behavior
TOOL_FLAGS = {
    "gemini": [],                     # Additional flags for gemini CLI
    "codex": ["--skip-git-repo-check"],  # Additional flags for codex CLI
    "cursor-agent": [],               # Additional flags for cursor-agent CLI
}


# Tool routing matrix based on failure type
ROUTING_MATRIX = {
    "assertion": ("cursor-agent", "gemini"),  # Primary, fallback
    "exception": ("codex", "gemini"),
    "import": ("gemini", "cursor-agent"),
    "fixture": ("gemini", "cursor-agent"),
    "timeout": ("gemini", "cursor-agent"),
    "flaky": ("gemini", "cursor-agent"),
    "multi-file": ("cursor-agent", "gemini"),
    "unclear-error": ("gemini", "web"),
    "validation": ("gemini", "codex"),
}

# Tool-specific command templates
# These are built dynamically from configuration with fallback to defaults
def _build_tool_commands(
    failure_type: Optional[str] = None,
    override: Any = None,
) -> Dict[str, List[str]]:
    """
    Build tool command templates from configuration.

    Args:
        failure_type: Optional failure type for model override selection

    Returns:
        Dict mapping tool names to command templates
    """
    commands: Dict[str, List[str]] = {}

    def _extend_with_model(cmd: List[str], model: Optional[str], flag: List[str]) -> None:
        if model:
            cmd.extend(flag + [model])

    gemini_model = get_model_for_tool("gemini", failure_type, override=override)
    gemini_cmd: List[str] = ["gemini"]
    _extend_with_model(gemini_cmd, gemini_model, ["-m"])
    gemini_cmd.extend(get_flags_for_tool("gemini"))
    gemini_cmd.append("-p")
    commands["gemini"] = gemini_cmd

    codex_model = get_model_for_tool("codex", failure_type, override=override)
    codex_cmd: List[str] = ["codex", "exec"]
    # Legacy tool flags expect --model for codex template
    _extend_with_model(codex_cmd, codex_model, ["--model"])
    codex_cmd.extend(get_flags_for_tool("codex"))
    commands["codex"] = codex_cmd

    cursor_model = get_model_for_tool("cursor-agent", failure_type, override=override)
    cursor_cmd: List[str] = ["cursor-agent"]
    cursor_cmd.append("-p")
    _extend_with_model(cursor_cmd, cursor_model, ["--model"])
    cursor_cmd.extend(get_flags_for_tool("cursor-agent"))
    commands["cursor-agent"] = cursor_cmd

    return commands

# Backward compatibility: Keep TOOL_COMMANDS for code that doesn't pass failure_type
TOOL_COMMANDS = _build_tool_commands()


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    """Return a list with duplicates removed while preserving order."""
    seen: set[str] = set()
    result: List[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _routing_plan_for_failure(failure_type: Optional[str]) -> List[str]:
    """Return the primary/fallback routing plan for a failure type."""
    if not failure_type:
        return []
    if failure_type not in ROUTING_MATRIX:
        return []
    candidates = [
        tool for tool in ROUTING_MATRIX[failure_type]
        if tool and tool != "web"
    ]
    return _dedupe_preserve_order(candidates)


def _mask_prompt_argument(command: List[str], prompt: str) -> List[str]:
    """Replace the prompt argument with a placeholder for dry-run output."""
    masked: List[str] = []
    replaced = False
    for part in command:
        if not replaced and part == prompt:
            masked.append("<prompt>")
            replaced = True
        else:
            masked.append(part)
    return masked


def _print_consultation_plan(
    plan_tools: List[str],
    available_tools: List[str],
    primary_tool: str,
    prompt: str,
    model: Optional[str]
) -> None:
    """Emit a human-readable consultation plan for dry-run output."""
    print("Consultation plan:")
    for tool_name in plan_tools:
        annotations: List[str] = []
        if tool_name == primary_tool:
            annotations.append("primary")
        else:
            annotations.append("fallback")
        if tool_name not in available_tools:
            annotations.append("missing")

        suffix = f" ({', '.join(annotations)})" if annotations else ""
        print(f"• {tool_name}{suffix}")

    print()
    print(f"Prompt length: {len(prompt)} characters")
    print()

    command = build_tool_command(primary_tool, prompt, model=model)
    masked_command = _mask_prompt_argument(command, prompt)

    print("Command preview:")
    print(" ".join(masked_command))
    print(f"<prompt with {len(prompt)} characters>")
    if model is not None:
        print(f"Resolved model: {model}")


def get_best_tool(failure_type: str, available_tools: Optional[List[str]] = None) -> Optional[str]:
    """
    Get the best available tool for a given failure type.

    Args:
        failure_type: Type of test failure
        available_tools: List of available tool names (auto-detected if None)

    Returns:
        Tool name to use, or None if no tools available
    """
    if available_tools is None:
        available_tools = get_enabled_and_available_tools("run-tests")

    if not available_tools:
        return None

    if failure_type not in ROUTING_MATRIX:
        # Default to first available tool
        return available_tools[0]

    primary, fallback = ROUTING_MATRIX[failure_type]

    if primary in available_tools:
        return primary
    elif fallback in available_tools and fallback != "web":
        return fallback
    elif available_tools:
        return available_tools[0]
    else:
        return None


def format_prompt(
    failure_type: str,
    error_message: str,
    hypothesis: str,
    test_code: Optional[str] = None,
    impl_code: Optional[str] = None,
    context: Optional[str] = None,
    question: Optional[str] = None
) -> str:
    """
    Format a prompt for external tool consultation.

    Args:
        failure_type: Type of test failure
        error_message: The full error message from pytest
        hypothesis: Your hypothesis about the root cause
        test_code: Test code snippet (optional)
        impl_code: Implementation code snippet (optional)
        context: Additional context (optional)
        question: Specific question to ask (optional)

    Returns:
        Formatted prompt string
    """
    prompt_parts = []

    # Start with failure context
    prompt_parts.append(f"I'm debugging a pytest {failure_type} failure:")
    prompt_parts.append("")
    prompt_parts.append("# ERROR:")
    prompt_parts.append(error_message)
    prompt_parts.append("")

    # Add code if provided
    if test_code:
        prompt_parts.append("# TEST CODE:")
        prompt_parts.append("```python")
        prompt_parts.append(test_code)
        prompt_parts.append("```")
        prompt_parts.append("")

    if impl_code:
        prompt_parts.append("# IMPLEMENTATION CODE:")
        prompt_parts.append("```python")
        prompt_parts.append(impl_code)
        prompt_parts.append("```")
        prompt_parts.append("")

    # Add context
    if context:
        prompt_parts.append("# CONTEXT:")
        prompt_parts.append(context)
        prompt_parts.append("")

    # Add hypothesis (most important!)
    prompt_parts.append("# MY HYPOTHESIS:")
    prompt_parts.append(hypothesis)
    prompt_parts.append("")

    # Add question or use default structured analysis request
    prompt_parts.append("# PLEASE PROVIDE:")
    if question:
        prompt_parts.append(question)
    else:
        # Request structured analysis for better multi-agent synthesis
        prompt_parts.append("1. Root cause of the failure")
        prompt_parts.append("2. Expected vs actual behavior")
        prompt_parts.append("3. Specific code location to fix (file:line)")
        prompt_parts.append("4. Recommended fix approach")
        prompt_parts.append("")

        # Add failure-specific follow-up questions
        followup_questions = {
            "assertion": "Additional: Are there edge cases I'm missing?",
            "exception": "Additional: Are there other related issues I should check?",
            "import": "Additional: What other files might be affected?",
            "fixture": "Additional: Are there other fixtures with similar issues?",
            "multi-file": "Additional: What's the full impact scope across the codebase?",
            "validation": "Additional: Are there risks or side effects to this approach?",
            "flaky": "Additional: What might cause non-determinism in this test?",
            "timeout": "Additional: What's the likely performance bottleneck?",
        }
        if failure_type in followup_questions:
            prompt_parts.append(followup_questions[failure_type])

    return "\n".join(prompt_parts)


def read_code_file(file_path: str) -> Optional[str]:
    """
    Read code from a file path.

    Args:
        file_path: Path to the file

    Returns:
        File contents, or None if file doesn't exist or can't be read
    """
    try:
        path = Path(file_path)

        # Validate path exists
        if not path.exists():
            return None

        # Validate it's a file (not a directory)
        if not path.is_file():
            return None

        # Try to read the file
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    except FileNotFoundError:
        return None
    except PermissionError:
        # File exists but can't be read
        return None
    except UnicodeDecodeError:
        # File is not text or has encoding issues
        return None
    except Exception:
        # Any other error
        return None


def run_consultation(
    tool: str,
    prompt: str,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None,
    failure_type: Optional[str] = None,
    model_override: Any = None,
    tracker: Optional[consultation_limits.ConsultationTracker] = None,
) -> int:
    """
    Run the external tool consultation.

    Args:
        tool: Tool name (gemini, codex, cursor-agent)
        prompt: Formatted prompt
        dry_run: If True, just print the command without running
        printer: PrettyPrinter instance (creates default if None)
        failure_type: Optional failure type for model selection
        model_override: Optional explicit model override (string or mapping)
        tracker: Optional ConsultationTracker instance for limiting tool usage

    Returns:
        Exit code from the tool
    """
    if printer is None:
        printer = PrettyPrinter()

    # Validate tool
    if tool not in ALL_SUPPORTED_TOOLS:
        printer.error(f"Unknown tool '{tool}'")
        printer.info(f"Available tools: {', '.join(ALL_SUPPORTED_TOOLS)}")
        return 1

    # Validate prompt
    if not prompt or not prompt.strip():
        printer.error("Prompt cannot be empty")
        return 1

    # Get model for tool
    model = get_model_for_tool(tool, failure_type, override=model_override)

    if dry_run:
        printer.info("Would run:")
        cmd = build_tool_command(tool, prompt, model=model)
        print(" ".join(cmd[:4]))  # Don't print full prompt in dry run
        print(f"<prompt with {len(prompt)} characters>")
        return 0

    printer.action(f"Consulting {tool}...")
    print("=" * 60)
    print()

    # Use shared execute_tool_with_fallback() implementation
    timeout = get_consultation_timeout()
    response = execute_tool_with_fallback(
        skill_name="run-tests",
        tool=tool,
        prompt=prompt,
        model=model,
        timeout=timeout,
        context={"failure_type": failure_type} if failure_type else None,
        tracker=tracker,
    )

    # Handle user interrupt (Ctrl+C) - execute_tool doesn't catch this
    # so we need to keep the try/except here
    try:
        # Print output
        if response.output:
            print(response.output)

        # Handle different status codes
        if response.status == ToolStatus.SUCCESS:
            return 0
        elif response.status == ToolStatus.TIMEOUT:
            printer.warning(f"\n{tool} timed out after {timeout} seconds")
            printer.info("The external tool may be unresponsive or processing a large request")
            printer.info("Try again with a simpler prompt or check tool availability")
            return 124
        elif response.status == ToolStatus.NOT_FOUND:
            printer.error(f"{tool} not found. Is it installed?")
            printer.info(f"Install instructions:")
            if tool == "gemini":
                printer.info("  npm install -g @google/generative-ai-cli")
            elif tool == "codex":
                printer.info("  npm install -g @anthropic/codex")
            elif tool == "cursor-agent":
                printer.info("  Check cursor.com for installation instructions")
            return 1
        else:  # ToolStatus.ERROR or other
            if response.exit_code is not None:
                printer.warning(f"\n{tool} exited with code {response.exit_code}")
                return response.exit_code
            else:
                printer.error(f"Error running {tool}: {response.error}")
                return 1
    except KeyboardInterrupt:
        printer.warning("\nConsultation interrupted by user")
        return 130


def print_routing_matrix(printer: Optional[PrettyPrinter] = None) -> None:
    """
    Print the routing matrix showing which tools to use for each failure type.

    Args:
        printer: PrettyPrinter instance (creates default if None)
    """
    if printer is None:
        printer = PrettyPrinter()

    printer.header("Failure Type Routing Matrix")
    printer.blank()

    for failure, (primary, fallback) in sorted(ROUTING_MATRIX.items()):
        print(f"  {failure:15} → {primary:13} (fallback: {fallback})")


def consult_with_auto_routing(
    failure_type: str,
    error_message: str,
    hypothesis: str,
    test_code_path: Optional[str] = None,
    impl_code_path: Optional[str] = None,
    context: Optional[str] = None,
    question: Optional[str] = None,
    tool: str = "auto",
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None,
    model_override: Any = None,
) -> int:
    """
    High-level consultation function with auto-routing.

    Args:
        failure_type: Type of test failure
        error_message: Error message from pytest
        hypothesis: Your hypothesis about the root cause
        test_code_path: Path to test code file (optional)
        impl_code_path: Path to implementation code file (optional)
        context: Additional context (optional)
        question: Specific question (optional)
        tool: Tool to use ("auto" for auto-selection)
        dry_run: If True, show command without running
        printer: PrettyPrinter instance (creates default if None)
        model_override: Optional explicit model override (string or mapping)

    Returns:
        Exit code from consultation
    """
    if printer is None:
        printer = PrettyPrinter()

    routing_plan = _routing_plan_for_failure(failure_type)

    # Check tool availability
    available_tools = get_enabled_and_available_tools("run-tests")

    if not available_tools:
        printer.error("No tools available for consultation")
        if routing_plan:
            print(f"Needed: {', '.join(routing_plan)}")
        else:
            print(f"Needed: {', '.join(ALL_SUPPORTED_TOOLS)}")
        print("Available: none")
        return 1

    # Determine which tool to use
    if tool == "auto":
        selected_tool = get_best_tool(failure_type, available_tools)
        if not selected_tool:
            printer.error("No tools available for consultation")
            if routing_plan:
                print(f"Needed: {', '.join(routing_plan)}")
            else:
                print(f"Needed: {', '.join(ALL_SUPPORTED_TOOLS)}")
            print(f"Available: {', '.join(available_tools)}" if available_tools else "Available: none")
            return 1
    else:
        selected_tool = tool
        if selected_tool not in available_tools:
            printer.error("No tools available for consultation")
            print(f"Needed: {selected_tool}")
            print(f"Available: {', '.join(available_tools)}")
            return 1

    if tool == "auto":
        tool = selected_tool

    plan_tools = _dedupe_preserve_order([selected_tool] + routing_plan)

    # Read code files if paths provided
    test_code = None
    impl_code = None

    if test_code_path:
        test_code = read_code_file(test_code_path)
        if test_code is None:
            # Treat as inline code
            test_code = test_code_path

    if impl_code_path:
        impl_code = read_code_file(impl_code_path)
        if impl_code is None:
            # Treat as inline code
            impl_code = impl_code_path

    # Format the prompt
    prompt = format_prompt(
        failure_type=failure_type,
        error_message=error_message,
        hypothesis=hypothesis,
        test_code=test_code,
        impl_code=impl_code,
        context=context,
        question=question
    )

    if dry_run:
        model = get_model_for_tool(selected_tool, failure_type, override=model_override)
        _print_consultation_plan(plan_tools, available_tools, selected_tool, prompt, model)
        return 0

    # Run the consultation
    return run_consultation(
        selected_tool,
        prompt,
        dry_run,
        printer,
        failure_type,
        model_override=model_override,
    )


# Valid failure types
FAILURE_TYPES = list(ROUTING_MATRIX.keys())


# =============================================================================
# MULTI-AGENT CONSULTATION
# =============================================================================

class ConsultationResponse(NamedTuple):
    """Represents a response from a tool consultation."""
    tool: str
    success: bool
    output: str
    error: Optional[str] = None
    duration: float = 0.0


def run_tool_parallel(
    tool: str,
    prompt: str,
    failure_type: Optional[str] = None,
    model_override: Any = None,
    tracker: Optional[consultation_limits.ConsultationTracker] = None,
) -> ConsultationResponse:
    """
    Run a single tool consultation and capture output.

    Args:
        tool: Tool name (gemini, codex, cursor-agent)
        prompt: Formatted prompt
        failure_type: Optional failure type for model selection
        model_override: Optional explicit model override (string or mapping)
        tracker: Optional ConsultationTracker instance for limiting tool usage

    Returns:
        ConsultationResponse with results
    """
    # Get model for tool
    model = get_model_for_tool(tool, failure_type, override=model_override)
    timeout = get_consultation_timeout()

    # Use shared execute_tool_with_fallback() implementation
    response = execute_tool_with_fallback(
        skill_name="run-tests",
        tool=tool,
        prompt=prompt,
        model=model,
        timeout=timeout,
        context={"failure_type": failure_type} if failure_type else None,
        tracker=tracker,
    )

    # Convert ToolResponse to ConsultationResponse for backward compatibility
    return ConsultationResponse(
        tool=response.tool,
        success=response.success,
        output=response.output,
        error=response.error,
        duration=response.duration
    )


def analyze_response_similarity(response1: str, response2: str) -> List[str]:
    """
    Simple heuristic to find consensus points between two responses.

    Args:
        response1: First response text
        response2: Second response text

    Returns:
        List of consensus points (simplified)
    """
    # This is a simple implementation. In a more sophisticated version,
    # we could use NLP techniques to identify semantic similarity.

    consensus = []

    # Common keywords that indicate agreement
    agreement_indicators = [
        "root cause",
        "missing return",
        "undefined variable",
        "type error",
        "fixture scope",
        "import error",
        "circular import",
        "async",
        "await",
        "timeout",
        "race condition",
    ]

    # Check for common indicators in both responses
    r1_lower = response1.lower()
    r2_lower = response2.lower()

    for indicator in agreement_indicators:
        if indicator in r1_lower and indicator in r2_lower:
            consensus.append(f"Both identify: {indicator}")

    # Check for common file references
    # Simple pattern: looks for .py files
    import re
    files1 = set(re.findall(r'[\w/]+\.py', response1))
    files2 = set(re.findall(r'[\w/]+\.py', response2))
    common_files = files1.intersection(files2)

    if common_files:
        consensus.append(f"Both reference files: {', '.join(list(common_files)[:3])}")

    return consensus if consensus else ["Responses require manual comparison"]


def synthesize_responses(responses: List[ConsultationResponse]) -> Dict[str, any]:
    """
    Synthesize multiple consultation responses into unified insights.

    Args:
        responses: List of ConsultationResponse objects

    Returns:
        Dictionary with synthesis including consensus, unique insights, etc.
    """
    synthesis = {
        "successful_consultations": [],
        "failed_consultations": [],
        "consensus": [],
        "unique_insights": {},
        "synthesis_text": "",
        "recommendations": []
    }

    # Separate successful and failed consultations
    successful = [r for r in responses if r.success]
    failed = [r for r in responses if not r.success]

    synthesis["successful_consultations"] = [r.tool for r in successful]
    synthesis["failed_consultations"] = [(r.tool, r.error) for r in failed]

    if len(successful) == 0:
        synthesis["synthesis_text"] = "All consultations failed. No synthesis available."
        return synthesis

    if len(successful) == 1:
        # Only one successful consultation
        single = successful[0]
        synthesis["synthesis_text"] = f"Only {single.tool} consultation succeeded."
        synthesis["recommendations"].append(f"Review {single.tool}'s analysis below")
        return synthesis

    # Multiple successful consultations - find consensus
    if len(successful) >= 2:
        # Compare first two responses for consensus
        consensus_points = analyze_response_similarity(
            successful[0].output,
            successful[1].output
        )
        synthesis["consensus"] = consensus_points

        # Extract unique insights (simplified)
        for resp in successful:
            # Get first few sentences as "unique insight"
            lines = resp.output.split('\n')
            insight = ' '.join(lines[:3])  # First 3 lines as summary
            synthesis["unique_insights"][resp.tool] = insight[:200] + "..."  # Truncate

        # Generate synthesis text
        tool_names = [r.tool for r in successful]
        synthesis["synthesis_text"] = f"Consulted {len(successful)} agents: {', '.join(tool_names)}"

        if consensus_points:
            synthesis["recommendations"].append(
                f"High confidence: {len(consensus_points)} consensus point(s) found"
            )
        else:
            synthesis["recommendations"].append(
                "Review individual responses for different perspectives"
            )

    return synthesis


def format_synthesis_output(
    synthesis: Dict[str, any],
    responses: List[ConsultationResponse],
    printer: Optional[PrettyPrinter] = None
) -> None:
    """
    Format and print the synthesis output in a structured way.

    Args:
        synthesis: Synthesis dictionary from synthesize_responses()
        responses: List of all ConsultationResponse objects
        printer: PrettyPrinter instance (creates default if None)
    """
    if printer is None:
        printer = PrettyPrinter()

    print()
    print("┌─ Multi-Agent Analysis " + "─" * 40 + "┐")
    print()

    # Show successful consultations
    if synthesis["successful_consultations"]:
        print("│ CONSULTED AGENTS:")
        for tool in synthesis["successful_consultations"]:
            # Find duration
            resp = next((r for r in responses if r.tool == tool and r.success), None)
            duration = f" ({resp.duration:.1f}s)" if resp else ""
            print(f"│ ✓ {tool}{duration}")
        print("│")

    # Show failed consultations
    if synthesis["failed_consultations"]:
        print("│ FAILED CONSULTATIONS:")
        for tool, error in synthesis["failed_consultations"]:
            print(f"│ ✗ {tool}: {error}")
        print("│")

    # Show consensus
    if synthesis["consensus"]:
        print("│ CONSENSUS (Agents agree):")
        for point in synthesis["consensus"]:
            print(f"│ • {point}")
        print("│")

    # Show unique insights
    if synthesis["unique_insights"]:
        for tool, insight in synthesis["unique_insights"].items():
            print(f"│ {tool.upper()} INSIGHTS:")
            # Wrap long lines
            words = insight.split()
            line = "│ • "
            for word in words:
                if len(line) + len(word) + 1 > 70:
                    print(line)
                    line = "│   "
                line += word + " "
            if line.strip() != "│":
                print(line)
            print("│")

    # Show synthesis and recommendations
    if synthesis["synthesis_text"]:
        print("│ SYNTHESIS:")
        print(f"│ {synthesis['synthesis_text']}")
        print("│")

    if synthesis["recommendations"]:
        print("│ RECOMMENDATIONS:")
        for rec in synthesis["recommendations"]:
            print(f"│ → {rec}")
        print("│")

    print("└" + "─" * 60 + "┘")
    print()

    # Print full responses from each agent
    successful_responses = [r for r in responses if r.success]
    if successful_responses:
        print("=" * 60)
        print("DETAILED RESPONSES:")
        print("=" * 60)
        print()

        for resp in successful_responses:
            print(f"─── {resp.tool.upper()} " + "─" * (54 - len(resp.tool)))
            print()
            print(resp.output)
            print()


def consult_multi_agent(
    failure_type: str,
    error_message: str,
    hypothesis: str,
    test_code_path: Optional[str] = None,
    impl_code_path: Optional[str] = None,
    context: Optional[str] = None,
    question: Optional[str] = None,
    agents: Optional[Sequence[str]] = None,
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None,
    model_override: Any = None,
) -> int:
    """
    Consult multiple agents in parallel and synthesize their responses.

    Args:
        failure_type: Type of test failure.
        error_message: Error message from pytest.
        hypothesis: Your hypothesis about the root cause.
        test_code_path: Path to test code file (optional).
        impl_code_path: Path to implementation code file (optional).
        context: Additional context (optional).
        question: Specific question (optional).
        agents: Optional explicit list of agents to consult. When omitted, the
            configured consensus agent order from `.claude/ai_config.yaml` is
            used, falling back to built-in defaults if necessary.
        dry_run: If True, show what would be run without executing.
        printer: PrettyPrinter instance (creates default if None).
        model_override: Optional explicit model override (string or mapping).

    Returns:
        Exit code (0 if at least one consultation succeeded).
    """
    if printer is None:
        printer = PrettyPrinter()

    configured_agents = _resolve_consensus_agents(agents)
    available_tools = get_enabled_and_available_tools("run-tests")

    if not available_tools:
        printer.error("No tools available for multi-agent consultation")
        printer.info(f"Configured agents: {', '.join(configured_agents) if configured_agents else 'none'}")
        printer.info("Available: none")
        return 1

    agents_to_consult = _dedupe_preserve_order(
        [tool for tool in configured_agents if tool in available_tools]
    )

    if not agents_to_consult:
        agents_to_consult = _dedupe_preserve_order(list(available_tools))

    if len(agents_to_consult) < 2 and len(available_tools) >= 2:
        # Supplement with additional available tools to reach at least two agents
        supplemental = [
            tool for tool in available_tools
            if tool not in agents_to_consult
        ]
        agents_to_consult.extend(supplemental[: (2 - len(agents_to_consult))])
        agents_to_consult = _dedupe_preserve_order(agents_to_consult)

    if len(agents_to_consult) < 2 and len(available_tools) > len(agents_to_consult):
        # As a final fallback, include all available tools
        agents_to_consult = _dedupe_preserve_order(list(available_tools))

    if len(agents_to_consult) < 2:
        printer.info("Falling back to single-agent consultation")
        single_tool = agents_to_consult[0]
        return consult_with_auto_routing(
            failure_type=failure_type,
            error_message=error_message,
            hypothesis=hypothesis,
            test_code_path=test_code_path,
            impl_code_path=impl_code_path,
            context=context,
            question=question,
            tool=single_tool,
            dry_run=dry_run,
            printer=printer,
            model_override=model_override,
        )

    # Read code files if paths provided
    test_code = None
    impl_code = None

    if test_code_path:
        test_code = read_code_file(test_code_path)
        if test_code is None:
            test_code = test_code_path

    if impl_code_path:
        impl_code = read_code_file(impl_code_path)
        if impl_code is None:
            impl_code = impl_code_path

    # Format the prompt (same for all agents)
    prompt = format_prompt(
        failure_type=failure_type,
        error_message=error_message,
        hypothesis=hypothesis,
        test_code=test_code,
        impl_code=impl_code,
        context=context,
        question=question
    )

    model_context: Optional[Dict[str, Any]] = None
    if failure_type:
        model_context = {"failure_type": failure_type}

    resolved_models = ai_config.resolve_models_for_tools(
        "run-tests",
        agents_to_consult,
        override=model_override,
        context=model_context,
    )

    if dry_run:
        printer.info(f"Would consult {len(agents_to_consult)} agents in parallel:")
        for tool in agents_to_consult:
            model = resolved_models.get(tool)
            suffix = f" (model: {model})" if model else ""
            print(f"  • {tool}{suffix}")
        print()
        print(f"Prompt length: {len(prompt)} characters")
        return 0

    # Run consultations in parallel using shared implementation
    enabled_tools_map = ai_config.get_enabled_tools("run-tests")
    final_agents_to_consult = [
        agent for agent in agents_to_consult if agent in enabled_tools_map
    ]

    printer.action(f"Consulting {len(final_agents_to_consult)} agents in parallel...")
    print(f"Agents: {', '.join(final_agents_to_consult)}")
    print("=" * 60)
    print()

    timeout = get_consultation_timeout()

    # Use shared execute_tools_parallel() implementation
    multi_response = execute_tools_parallel(
        tools=final_agents_to_consult,
        prompt=prompt,
        models=dict(resolved_models),
        timeout=timeout
    )

    # Print progress as tools complete
    for tool, response in multi_response.responses.items():
        status = "✓" if response.success else "✗"
        print(f"{status} {tool} completed ({response.duration:.1f}s)")

    print()

    # Convert MultiToolResponse to list of ConsultationResponse for backward compatibility
    responses = [
        ConsultationResponse(
            tool=resp.tool,
            success=resp.success,
            output=resp.output,
            error=resp.error,
            duration=resp.duration
        )
        for resp in multi_response.responses.values()
    ]

    # Synthesize responses
    synthesis = synthesize_responses(responses)

    # Format and display synthesis
    format_synthesis_output(synthesis, responses, printer)

    # Return success if at least one consultation succeeded
    return 0 if synthesis["successful_consultations"] else 1
