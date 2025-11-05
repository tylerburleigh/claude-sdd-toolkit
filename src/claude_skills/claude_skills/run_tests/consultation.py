"""
External Tool Consultation Operations

Handles consultation with external CLI tools (Gemini, Codex, Cursor) for test
debugging. Provides auto-routing based on failure type and prompt formatting.
"""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, NamedTuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# Add parent directory to path to import sdd_common

from claude_skills.common import PrettyPrinter
from claude_skills.common.ai_tools import build_tool_command
from claude_skills.run_tests.tool_checking import check_tool_availability, get_available_tools, get_config_path


# =============================================================================
# MODEL CONFIGURATION LOADING
# =============================================================================

def load_model_config() -> Dict:
    """
    Load model configuration from config.yaml.

    Returns fallback to DEFAULT_MODELS if config not found or invalid.

    Returns:
        Dict with model configuration including priorities and overrides
    """
    import yaml

    config_path = get_config_path()

    try:
        if not config_path.exists():
            return {}

        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        if not config_data or 'models' not in config_data:
            return {}

        return config_data['models']

    except (yaml.YAMLError, IOError, KeyError) as e:
        return {}


def get_model_for_tool(tool: str, failure_type: Optional[str] = None) -> str:
    """
    Get the best model for a tool, considering priority and failure-type overrides.

    Falls back to hardcoded defaults if configuration not available.

    Args:
        tool: Tool name (gemini, codex, cursor-agent)
        failure_type: Optional failure type for override lookup

    Returns:
        Model name to use
    """
    # Load config
    model_config = load_model_config()

    # If no config, use hardcoded defaults (defined below in DEFAULT_MODELS)
    if not model_config:
        return DEFAULT_MODELS.get(tool, "")

    # Check for failure-type override first
    if failure_type and 'overrides' in model_config:
        overrides = model_config['overrides']
        if failure_type in overrides and tool in overrides[failure_type]:
            priority_list = overrides[failure_type][tool]
            if priority_list and len(priority_list) > 0:
                return priority_list[0]  # Return first in override priority

    # Use global priority for tool
    if tool in model_config:
        tool_config = model_config[tool]
        if 'priority' in tool_config and len(tool_config['priority']) > 0:
            return tool_config['priority'][0]  # Return first in priority

    # Fallback to hardcoded default
    return DEFAULT_MODELS.get(tool, "")


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
    return tool_config.get('flags', TOOL_FLAGS.get(tool, []))


# =============================================================================
# CONSENSUS CONFIGURATION LOADING
# =============================================================================

def load_consensus_config() -> Dict:
    """
    Load consensus configuration from config.yaml.

    Returns:
        Dict with consensus configuration (pairs and auto_trigger)
    """
    import yaml

    config_path = get_config_path()

    try:
        if not config_path.exists():
            return {}

        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        if not config_data or 'consensus' not in config_data:
            return {}

        return config_data['consensus']

    except (yaml.YAMLError, IOError, KeyError) as e:
        return {}


def should_auto_trigger_consensus(failure_type: str) -> bool:
    """
    Check if a failure type should automatically trigger multi-agent consensus.

    Checks in order:
    1. Explicit entry for failure_type
    2. Default setting for undefined types
    3. Fallback to False (single-agent)

    Args:
        failure_type: Type of test failure

    Returns:
        True if consensus should be auto-triggered, False otherwise
    """
    consensus_config = load_consensus_config()

    if not consensus_config or 'auto_trigger' not in consensus_config:
        return False

    auto_trigger = consensus_config['auto_trigger']

    # Check for explicit entry first
    if failure_type in auto_trigger:
        return auto_trigger[failure_type] is not None

    # Check for default setting
    if 'default' in auto_trigger:
        return auto_trigger['default'] is not None

    # No config, no auto-trigger
    return False


def get_consensus_pair_for_failure(failure_type: str) -> str:
    """
    Get the consensus pair to use for a specific failure type.

    Checks in order:
    1. Explicit entry for failure_type
    2. Default setting for undefined types
    3. Fallback to "default" pair

    Args:
        failure_type: Type of test failure

    Returns:
        Pair name (e.g., 'default', 'code-focus', 'discovery-focus')
        Returns 'default' if not configured
    """
    consensus_config = load_consensus_config()

    if not consensus_config or 'auto_trigger' not in consensus_config:
        return "default"

    auto_trigger = consensus_config['auto_trigger']

    # Check for explicit entry first
    if failure_type in auto_trigger:
        pair = auto_trigger[failure_type]
        return pair if pair is not None else "default"

    # Check for default setting
    if 'default' in auto_trigger:
        pair = auto_trigger['default']
        return pair if pair is not None else "default"

    # Fallback
    return "default"


def get_consensus_pairs() -> Dict[str, List[str]]:
    """
    Get defined consensus pairs from configuration.

    Falls back to hardcoded MULTI_AGENT_PAIRS if not configured.

    Returns:
        Dict mapping pair names to lists of tools
    """
    consensus_config = load_consensus_config()

    if not consensus_config or 'pairs' not in consensus_config:
        # Fallback to hardcoded MULTI_AGENT_PAIRS (defined below)
        return MULTI_AGENT_PAIRS

    return consensus_config['pairs']


def get_consultation_timeout() -> int:
    """
    Get consultation timeout from config (default: 90 seconds).

    Returns:
        Timeout in seconds
    """
    import yaml

    config_path = get_config_path()

    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                if config and 'consultation' in config:
                    return config['consultation'].get('timeout_seconds', 90)
    except (yaml.YAMLError, IOError, KeyError):
        pass

    return 90  # Default 90 seconds


# =============================================================================
# CONFIGURATION - Customize these settings for your environment
# =============================================================================

# Default models to use for each tool
# Modify these if you want to use different models or if the defaults are unavailable
DEFAULT_MODELS = {
    "gemini": "gemini-2.5-pro",      # Can also use: gemini-2.0-flash-exp, etc.
    "codex": "gpt-5-codex",           # Can also use: gpt-5, gpt-5-mini, etc.
    "cursor-agent": "gpt-5-codex",    # Can also use: gpt-5, claude-sonnet-4, etc.
}

# Additional flags for each tool
# Customize these if you need different behavior
TOOL_FLAGS = {
    "gemini": [],                     # Additional flags for gemini CLI
    "codex": ["--skip-git-repo-check"],  # Additional flags for codex CLI
    "cursor-agent": [],               # Additional flags for cursor-agent CLI
}

# Multi-agent consultation pairs
# Defines which tool combinations to use for multi-agent analysis
MULTI_AGENT_PAIRS = {
    "default": ["gemini", "cursor-agent"],       # Strategic + discovery focus
    "code-focus": ["codex", "gemini"],           # Code review + strategic validation
    "discovery-focus": ["cursor-agent", "gemini"], # Pattern discovery + strategic analysis
}


# Tool routing matrix based on failure type
ROUTING_MATRIX = {
    "assertion": ("codex", "gemini"),  # Primary, fallback
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
def _build_tool_commands(failure_type: Optional[str] = None) -> Dict[str, List[str]]:
    """
    Build tool command templates from configuration.

    Args:
        failure_type: Optional failure type for model override selection

    Returns:
        Dict mapping tool names to command templates
    """
    return {
        "gemini": [
            "gemini",
            "-m", get_model_for_tool("gemini", failure_type)
        ] + get_flags_for_tool("gemini") + ["-p"],
        "codex": [
            "codex",
            "exec",
            "--model", get_model_for_tool("codex", failure_type)
        ] + get_flags_for_tool("codex"),
        "cursor-agent": [
            "cursor-agent",
            "-p",
            "--model", get_model_for_tool("cursor-agent", failure_type)
        ] + get_flags_for_tool("cursor-agent"),
    }

# Backward compatibility: Keep TOOL_COMMANDS for code that doesn't pass failure_type
TOOL_COMMANDS = _build_tool_commands()


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
        available_tools = get_available_tools()

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
    failure_type: Optional[str] = None
) -> int:
    """
    Run the external tool consultation.

    Args:
        tool: Tool name (gemini, codex, cursor-agent)
        prompt: Formatted prompt
        dry_run: If True, just print the command without running
        printer: PrettyPrinter instance (creates default if None)
        failure_type: Optional failure type for model selection

    Returns:
        Exit code from the tool
    """
    if printer is None:
        printer = PrettyPrinter()

    # Validate tool
    known_tools = ["gemini", "codex", "cursor-agent"]
    if tool not in known_tools:
        printer.error(f"Unknown tool '{tool}'")
        printer.info(f"Available tools: {', '.join(known_tools)}")
        return 1

    # Validate prompt
    if not prompt or not prompt.strip():
        printer.error("Prompt cannot be empty")
        return 1

    # Build command using shared implementation
    model = get_model_for_tool(tool, failure_type)
    cmd = build_tool_command(tool, prompt, model=model)

    if dry_run:
        printer.info("Would run:")
        print(" ".join(cmd[:4]))  # Don't print full prompt in dry run
        print(f"<prompt with {len(prompt)} characters>")
        return 0

    printer.action(f"Consulting {tool}...")
    print("=" * 60)
    print()

    try:
        timeout = get_consultation_timeout()
        result = subprocess.run(cmd, check=False, timeout=timeout)
        if result.returncode != 0:
            printer.warning(f"\n{tool} exited with code {result.returncode}")
        return result.returncode
    except subprocess.TimeoutExpired:
        printer.warning(f"\n{tool} timed out after {get_consultation_timeout()} seconds")
        printer.info("The external tool may be unresponsive or processing a large request")
        printer.info("Try again with a simpler prompt or check tool availability")
        return 124
    except FileNotFoundError:
        printer.error(f"{tool} not found. Is it installed?")
        printer.info(f"Install instructions:")
        if tool == "gemini":
            printer.info("  npm install -g @google/generative-ai-cli")
        elif tool == "codex":
            printer.info("  npm install -g @anthropic/codex")
        elif tool == "cursor-agent":
            printer.info("  Check cursor.com for installation instructions")
        return 1
    except KeyboardInterrupt:
        printer.warning("\nConsultation interrupted by user")
        return 130
    except Exception as e:
        printer.error(f"Unexpected error running {tool}: {e}")
        return 1


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
    printer: Optional[PrettyPrinter] = None
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

    Returns:
        Exit code from consultation
    """
    if printer is None:
        printer = PrettyPrinter()

    # Check tool availability
    available_tools = get_available_tools()

    if not available_tools:
        printer.error("No external tools found")
        printer.info("Install at least one: gemini, codex, or cursor-agent")
        return 1

    # Determine which tool to use
    if tool == "auto":
        tool = get_best_tool(failure_type, available_tools)
        if not tool:
            printer.error("No suitable tool found")
            return 1
        printer.info(f"Auto-selected tool: {tool}")
        printer.blank()
    else:
        if tool not in available_tools:
            printer.error(f"{tool} is not available")
            printer.info(f"Available tools: {', '.join(available_tools)}")
            return 1

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

    # Run the consultation
    return run_consultation(tool, prompt, dry_run, printer, failure_type)


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


def run_tool_parallel(tool: str, prompt: str, failure_type: Optional[str] = None) -> ConsultationResponse:
    """
    Run a single tool consultation and capture output.

    Args:
        tool: Tool name (gemini, codex, cursor-agent)
        prompt: Formatted prompt
        failure_type: Optional failure type for model selection

    Returns:
        ConsultationResponse with results
    """
    # Validate tool
    known_tools = ["gemini", "codex", "cursor-agent"]
    if tool not in known_tools:
        return ConsultationResponse(
            tool=tool,
            success=False,
            output="",
            error=f"Unknown tool '{tool}'"
        )

    # Build command using shared implementation
    model = get_model_for_tool(tool, failure_type)
    cmd = build_tool_command(tool, prompt, model=model)

    start_time = time.time()

    try:
        timeout = get_consultation_timeout()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout
        )
        duration = time.time() - start_time

        return ConsultationResponse(
            tool=tool,
            success=(result.returncode == 0),
            output=result.stdout if result.stdout else result.stderr,
            error=result.stderr if result.returncode != 0 else None,
            duration=duration
        )
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return ConsultationResponse(
            tool=tool,
            success=False,
            output="",
            error=f"{tool} timed out after {get_consultation_timeout()} seconds. Try again or check tool availability.",
            duration=duration
        )
    except FileNotFoundError:
        return ConsultationResponse(
            tool=tool,
            success=False,
            output="",
            error=f"{tool} not found. Is it installed?"
        )
    except Exception as e:
        return ConsultationResponse(
            tool=tool,
            success=False,
            output="",
            error=f"Unexpected error: {e}"
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
    pair: str = "default",
    dry_run: bool = False,
    printer: Optional[PrettyPrinter] = None
) -> int:
    """
    Consult multiple agents in parallel and synthesize their responses.

    Args:
        failure_type: Type of test failure
        error_message: Error message from pytest
        hypothesis: Your hypothesis about the root cause
        test_code_path: Path to test code file (optional)
        impl_code_path: Path to implementation code file (optional)
        context: Additional context (optional)
        question: Specific question (optional)
        pair: Which multi-agent pair to use (default, code-focus, discovery-focus)
        dry_run: If True, show what would be run without running
        printer: PrettyPrinter instance (creates default if None)

    Returns:
        Exit code (0 if at least one consultation succeeded)
    """
    if printer is None:
        printer = PrettyPrinter()

    # Get the tool pair to use from configuration
    consensus_pairs = get_consensus_pairs()

    if pair not in consensus_pairs:
        printer.error(f"Unknown multi-agent pair '{pair}'")
        printer.info(f"Available pairs: {', '.join(consensus_pairs.keys())}")
        return 1

    tools_to_use = consensus_pairs[pair]

    # Check which tools are available
    available_tools = get_available_tools()
    available_from_pair = [t for t in tools_to_use if t in available_tools]

    if len(available_from_pair) < 2:
        printer.warning(f"Only {len(available_from_pair)} tool(s) available from '{pair}' pair")
        if len(available_from_pair) == 0:
            printer.error("No tools available from selected pair")
            printer.info(f"Needed: {', '.join(tools_to_use)}")
            printer.info(f"Available: {', '.join(available_tools) if available_tools else 'none'}")
            return 1
        elif len(available_tools) >= 2:
            # Use first two available tools
            available_from_pair = available_tools[:2]
            printer.info(f"Using available tools instead: {', '.join(available_from_pair)}")
        else:
            printer.info("Falling back to single-agent consultation")
            # Use the single available tool
            return consult_with_auto_routing(
                failure_type=failure_type,
                error_message=error_message,
                hypothesis=hypothesis,
                test_code_path=test_code_path,
                impl_code_path=impl_code_path,
                context=context,
                question=question,
                tool=available_from_pair[0],
                dry_run=dry_run,
                printer=printer
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

    if dry_run:
        printer.info(f"Would consult {len(available_from_pair)} agents in parallel:")
        for tool in available_from_pair:
            print(f"  • {tool}")
        print()
        print(f"Prompt length: {len(prompt)} characters")
        return 0

    # Run consultations in parallel
    printer.action(f"Consulting {len(available_from_pair)} agents in parallel...")
    print(f"Tools: {', '.join(available_from_pair)}")
    print("=" * 60)
    print()

    responses = []

    with ThreadPoolExecutor(max_workers=len(available_from_pair)) as executor:
        # Submit all consultations
        future_to_tool = {
            executor.submit(run_tool_parallel, tool, prompt, failure_type): tool
            for tool in available_from_pair
        }

        # Collect results as they complete
        for future in as_completed(future_to_tool):
            tool = future_to_tool[future]
            try:
                response = future.result()
                responses.append(response)
                status = "✓" if response.success else "✗"
                print(f"{status} {tool} completed ({response.duration:.1f}s)")
            except Exception as e:
                printer.error(f"Error consulting {tool}: {e}")
                responses.append(ConsultationResponse(
                    tool=tool,
                    success=False,
                    output="",
                    error=str(e)
                ))

    print()

    # Synthesize responses
    synthesis = synthesize_responses(responses)

    # Format and display synthesis
    format_synthesis_output(synthesis, responses, printer)

    # Return success if at least one consultation succeeded
    return 0 if synthesis["successful_consultations"] else 1
