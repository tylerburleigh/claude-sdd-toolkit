"""Shared AI configuration loader for skills.

Loads configuration from config.yaml in skill directories (run-tests, sdd-render, etc.),
with fallback to sensible defaults if config is missing or malformed.

This module provides a common interface for all skills to load their AI tool configurations.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional


# Default tool configuration (fallback if config file not found)
DEFAULT_TOOLS = {
    "gemini": {
        "description": "Strategic analysis and hypothesis validation",
        "command": "gemini",
        "enabled": True
    },
    "cursor-agent": {
        "description": "Repository-wide pattern discovery",
        "command": "cursor-agent",
        "enabled": True
    },
    "codex": {
        "description": "Code-level review and bug fixes",
        "command": "codex",
        "enabled": False
    }
}

DEFAULT_MODELS = {
    "gemini": {
        "priority": ["gemini-2.5-pro"],
        "flags": ["-m", "gemini-2.5-pro", "-p"]
    },
    "cursor-agent": {
        "priority": ["cheetah"],
        "flags": ["-p", "--model", "cheetah"]
    },
    "codex": {
        "priority": ["gpt-5-codex"],
        "flags": ["exec", "--model", "gpt-5-codex", "--skip-git-repo-check"]
    }
}


def get_config_path(skill_name: str) -> Path:
    """Get the path to the config.yaml file for a skill.

    Args:
        skill_name: Name of the skill (e.g., 'run-tests', 'sdd-render')

    Returns:
        Path to config.yaml in the skill directory
    """
    # This file is in src/claude_skills/claude_skills/common/ai_config.py
    # We need to find skills/{skill_name}/config.yaml

    # Try multiple possible locations
    possible_paths = [
        # From installed package location
        Path(__file__).parent.parent.parent.parent.parent / "skills" / skill_name / "config.yaml",
        # From development location
        Path(__file__).parent.parent.parent.parent / "skills" / skill_name / "config.yaml",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # Return first path even if it doesn't exist (will use defaults)
    return possible_paths[0]


def load_skill_config(skill_name: str) -> Dict:
    """Load full configuration from config.yaml with fallback to defaults.

    Args:
        skill_name: Name of the skill (e.g., 'run-tests', 'sdd-render')

    Returns:
        Dict with complete configuration
    """
    config_path = get_config_path(skill_name)

    try:
        if not config_path.exists():
            # Config file doesn't exist, use defaults
            return {
                "tools": DEFAULT_TOOLS.copy(),
                "models": DEFAULT_MODELS.copy()
            }

        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        if not config_data:
            # Empty config, use defaults
            return {
                "tools": DEFAULT_TOOLS.copy(),
                "models": DEFAULT_MODELS.copy()
            }

        return config_data

    except (yaml.YAMLError, IOError, KeyError) as e:
        # Error loading config, fall back to defaults
        return {
            "tools": DEFAULT_TOOLS.copy(),
            "models": DEFAULT_MODELS.copy()
        }


def get_enabled_tools(skill_name: str) -> Dict[str, Dict]:
    """Get only the enabled tools from configuration.

    Args:
        skill_name: Name of the skill

    Returns:
        Dict mapping tool name to tool configuration (only enabled tools)
    """
    config = load_skill_config(skill_name)
    tools = config.get('tools', DEFAULT_TOOLS)

    return {
        name: tool_config
        for name, tool_config in tools.items()
        if tool_config.get('enabled', True)
    }


def get_agent_priority(skill_name: str, default_order: Optional[List[str]] = None) -> List[str]:
    """Get the priority-ordered list of agents to try.

    Args:
        skill_name: Name of the skill
        default_order: Default priority order if not in config

    Returns:
        List of agent names in priority order (highest first)
    """
    config = load_skill_config(skill_name)

    # Try skill-specific rendering config first
    if 'rendering' in config:
        rendering_config = config['rendering']
        if 'agent_priority' in rendering_config:
            return rendering_config['agent_priority']

    # Fall back to consultation config (for run-tests compatibility)
    if 'consultation' in config:
        consultation_config = config['consultation']
        if 'agent_priority' in consultation_config:
            return consultation_config['agent_priority']

    # Use provided default or sensible fallback
    return default_order or ['gemini', 'cursor-agent', 'codex']


def get_agent_command(skill_name: str, agent_name: str, prompt: str) -> List[str]:
    """Build the command list for invoking an agent.

    Args:
        skill_name: Name of the skill
        agent_name: Name of the agent (gemini, cursor-agent, codex)
        prompt: The prompt to send to the agent

    Returns:
        List of command arguments for subprocess.run
    """
    config = load_skill_config(skill_name)
    models = config.get('models', DEFAULT_MODELS)

    if agent_name not in models:
        # Fallback to basic command
        return [agent_name, prompt]

    model_config = models[agent_name]
    flags = model_config.get('flags', [])

    # Build command: [agent_name, *flags, prompt]
    # Note: Command is already in flags for most tools
    # Extract command from first flag if it's the tool name
    if flags and flags[0] != agent_name:
        return [agent_name] + flags + [prompt]
    else:
        return [agent_name] + flags[1:] + [prompt] if len(flags) > 1 else [agent_name, prompt]


def get_timeout(skill_name: str, timeout_type: str = 'default') -> int:
    """Get timeout value in seconds.

    Args:
        skill_name: Name of the skill
        timeout_type: Type of timeout ('default', 'narrative', 'consultation')

    Returns:
        Timeout in seconds
    """
    config = load_skill_config(skill_name)

    # Try rendering config (sdd-render)
    if 'rendering' in config:
        rendering_config = config['rendering']
        if timeout_type == 'narrative':
            return rendering_config.get('narrative_timeout_seconds', 30)
        return rendering_config.get('timeout_seconds', 90)

    # Try consultation config (run-tests)
    if 'consultation' in config:
        consultation_config = config['consultation']
        return consultation_config.get('timeout_seconds', 90)

    # Default fallback
    return 90 if timeout_type == 'default' else 30


def get_tool_config(skill_name: str, tool_name: str) -> Optional[Dict]:
    """Get configuration for a specific tool.

    Args:
        skill_name: Name of the skill
        tool_name: Name of the tool

    Returns:
        Tool configuration dict or None if not found
    """
    config = load_skill_config(skill_name)
    tools = config.get('tools', {})
    return tools.get(tool_name)


def is_tool_enabled(skill_name: str, tool_name: str) -> bool:
    """Check if a specific tool is enabled.

    Args:
        skill_name: Name of the skill
        tool_name: Name of the tool

    Returns:
        True if enabled, False otherwise
    """
    tool_config = get_tool_config(skill_name, tool_name)
    if not tool_config:
        return False
    return tool_config.get('enabled', True)
