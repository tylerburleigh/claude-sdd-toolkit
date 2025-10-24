"""
Tool Checking Operations

Checks availability of external CLI tools (Gemini, Codex, Cursor) and provides
routing suggestions for test debugging workflows.
"""

import shutil
import yaml
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path to import sdd_common

from claude_skills.common import PrettyPrinter

# Default tool configuration (fallback if config file not found)
DEFAULT_TOOLS = {
    "gemini": {
        "description": "Strategic analysis and hypothesis validation",
        "command": "gemini",
        "enabled": True
    },
    "codex": {
        "description": "Code-level review and bug fixes",
        "command": "codex",
        "enabled": True
    },
    "cursor-agent": {
        "description": "Repository-wide pattern discovery",
        "command": "cursor-agent",
        "enabled": True
    }
}


def get_config_path() -> Path:
    """
    Get the path to the config.yaml file.

    Returns:
        Path to config.yaml in the skill root directory
    """
    # This file is in skills/run-tests/scripts/tool_checking.py
    # Config is at skills/run-tests/config.yaml
    return Path(__file__).parent.parent / "config.yaml"


def load_tool_config() -> Dict:
    """
    Load tool configuration from config.yaml with fallback to defaults.

    Returns:
        Dict with tool configuration
    """
    config_path = get_config_path()

    try:
        if not config_path.exists():
            # Config file doesn't exist, use defaults
            return DEFAULT_TOOLS

        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        if not config_data or 'tools' not in config_data:
            # Malformed config, use defaults
            return DEFAULT_TOOLS

        tools = config_data['tools']

        # Validate and normalize tool entries
        normalized = {}
        for tool_name, tool_config in tools.items():
            if not isinstance(tool_config, dict):
                continue

            # Default command to tool name if not specified
            command = tool_config.get('command', tool_name)
            description = tool_config.get('description', '')
            enabled = tool_config.get('enabled', True)

            normalized[tool_name] = {
                'command': command,
                'description': description,
                'enabled': enabled
            }

        return normalized if normalized else DEFAULT_TOOLS

    except (yaml.YAMLError, IOError, KeyError) as e:
        # Error loading config, fall back to defaults
        return DEFAULT_TOOLS


def get_enabled_tools() -> Dict:
    """
    Get only the enabled tools from configuration.

    Returns:
        Dict with only enabled tools
    """
    all_tools = load_tool_config()
    return {
        name: config
        for name, config in all_tools.items()
        if config.get('enabled', True)
    }


def check_tool_availability() -> Dict[str, bool]:
    """
    Check which external tools are installed and enabled.

    Only checks tools that are enabled in the configuration.

    Returns:
        Dict mapping tool names to availability status
    """
    enabled_tools = get_enabled_tools()
    tools = {}

    for tool_name, tool_config in enabled_tools.items():
        command = tool_config.get('command', tool_name)
        tools[tool_name] = shutil.which(command) is not None

    return tools


def get_available_tools() -> List[str]:
    """
    Get list of available external tools.

    Returns:
        List of tool names that are installed
    """
    tools = check_tool_availability()
    return [tool for tool, is_available in tools.items() if is_available]


def get_missing_tools() -> List[str]:
    """
    Get list of missing external tools.

    Returns:
        List of tool names that are not installed
    """
    tools = check_tool_availability()
    return [tool for tool, is_available in tools.items() if not is_available]


def get_routing_suggestions(available_tools: List[str]) -> List[str]:
    """
    Provide routing suggestions based on available tools.

    Args:
        available_tools: List of tool names that are available

    Returns:
        List of suggestion strings
    """
    if not available_tools:
        return [
            "No external tools available - proceed with:",
            "  • Your own analysis",
            "  • Optional web search for complex issues",
            "  • Make smaller, safer changes and test frequently"
        ]

    # Load tool config to get descriptions
    tool_config = load_tool_config()

    suggestions = ["Available tools and their best uses:"]

    # Dynamically build suggestions from config
    for tool_name in available_tools:
        if tool_name in tool_config:
            description = tool_config[tool_name].get('description', 'No description available')
            suggestions.append(f"  • {tool_name}: {description}")
        else:
            suggestions.append(f"  • {tool_name}: Available")

    # Add fallback suggestions
    suggestions.append("\nFallback strategies:")

    if "gemini" not in available_tools and available_tools:
        if "codex" in available_tools:
            suggestions.append(
                "  • For strategic questions: Use codex with extra context"
            )
        if "cursor-agent" in available_tools:
            suggestions.append(
                "  • For explanations: Use cursor-agent + web search"
            )

    if "codex" not in available_tools and available_tools:
        if "gemini" in available_tools:
            suggestions.append(
                "  • For code review: Ask gemini for very specific code examples"
            )

    if "cursor-agent" not in available_tools and available_tools:
        if "gemini" in available_tools:
            suggestions.append(
                "  • For pattern discovery: Use Grep + ask gemini to analyze findings"
            )

    return suggestions


def get_quick_routing(failure_type: str, available_tools: Optional[List[str]] = None) -> str:
    """
    Get quick tool routing suggestion for a failure type.

    Args:
        failure_type: Type of test failure (assertion, exception, etc.)
        available_tools: List of available tools (auto-detected if None)

    Returns:
        Routing suggestion string
    """
    if available_tools is None:
        available_tools = get_available_tools()

    if not available_tools:
        return "No external tools available - proceed with own analysis"

    routing = {
        "assertion": ("codex", "gemini"),  # Primary, fallback
        "exception": ("codex", "gemini"),
        "import": ("gemini", "cursor-agent"),
        "fixture": ("gemini", "cursor-agent"),
        "timeout": ("gemini", "cursor-agent"),
        "flaky": ("gemini", "cursor-agent"),
        "multi-file": ("cursor-agent", "gemini"),
        "unclear-error": ("gemini", "codex"),
        "validation": ("gemini", "codex"),
    }

    if failure_type not in routing:
        return f"Unknown failure type '{failure_type}'"

    primary, fallback = routing[failure_type]

    if primary in available_tools:
        return f"Use: {primary} (primary)"
    elif fallback in available_tools:
        return f"Use: {fallback} (fallback - {primary} not available)"
    else:
        # Find any available tool
        for tool in available_tools:
            return f"Use: {tool} (both {primary} and {fallback} unavailable)"
        return "No suitable tools available"


def print_tool_status(
    printer: Optional[PrettyPrinter] = None,
    include_routing: Optional[str] = None
) -> int:
    """
    Print tool availability status to console.

    Args:
        printer: PrettyPrinter instance (creates default if None)
        include_routing: If provided, also show routing for this failure type

    Returns:
        Exit code: 0 if any tools available, 1 if none
    """
    if printer is None:
        printer = PrettyPrinter()

    available = get_available_tools()
    missing = get_missing_tools()

    printer.header("External CLI Tool Availability Check")
    printer.blank()

    if available:
        printer.success(f"Available: {', '.join(available)}")
    else:
        printer.error("No external tools found")

    if missing:
        printer.warning(f"Missing:   {', '.join(missing)}")

    printer.blank()

    # Quick routing for specific failure type
    if include_routing:
        printer.info(f"Routing for '{include_routing}' failure:")
        printer.item(get_quick_routing(include_routing, available))
        printer.blank()

    # General suggestions
    printer.blank()
    for suggestion in get_routing_suggestions(available):
        print(suggestion)

    return 0 if available else 1


def get_tool_status_dict() -> Dict:
    """
    Get tool status as a dictionary (for JSON output).

    Returns:
        Dict with 'available' and 'missing' keys
    """
    available = get_available_tools()
    missing = get_missing_tools()

    return {
        "available": available,
        "missing": missing,
    }


# Valid failure types for routing
FAILURE_TYPES = [
    "assertion",
    "exception",
    "import",
    "fixture",
    "timeout",
    "flaky",
    "multi-file",
    "unclear-error",
    "validation"
]


def load_consensus_config() -> Dict:
    """
    Load consensus configuration from config.yaml.

    Returns:
        Dict with consensus configuration
    """
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


def get_auto_trigger_failures() -> List[str]:
    """
    Get list of failure types that auto-trigger consensus.

    Returns:
        List of failure type names
    """
    consensus_config = load_consensus_config()

    if not consensus_config or 'auto_trigger' not in consensus_config:
        return []

    auto_trigger = consensus_config['auto_trigger']
    return [
        failure_type
        for failure_type, pair in auto_trigger.items()
        if pair is not None
    ]


def get_consensus_info() -> Dict:
    """
    Get consensus configuration info (for display/debugging).

    Returns:
        Dict with consensus pairs and auto-trigger info
    """
    consensus_config = load_consensus_config()

    if not consensus_config:
        return {
            "pairs": {},
            "auto_trigger": {}
        }

    return {
        "pairs": consensus_config.get('pairs', {}),
        "auto_trigger": consensus_config.get('auto_trigger', {})
    }
