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


def get_global_config_path() -> Path:
    """Get the path to the global AI configuration file.

    Searches in multiple locations:
    1. .claude/ai_config.yaml in current working directory
    2. .claude/ai_config.yaml relative to project root

    Returns:
        Path to global ai_config.yaml (may not exist)
    """
    possible_paths = [
        Path.cwd() / ".claude" / "ai_config.yaml",
        Path(__file__).parent.parent.parent.parent / ".claude" / "ai_config.yaml",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # Return first path even if it doesn't exist
    return possible_paths[0]


def load_global_config() -> Dict:
    """Load the global AI configuration file.

    Returns:
        Dictionary with global configuration, or empty dict if file doesn't exist
    """
    config_path = get_global_config_path()

    try:
        if not config_path.exists():
            return {}

        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        if not config_data:
            return {}

        return config_data

    except (yaml.YAMLError, IOError) as e:
        # Error loading global config, continue without it
        return {}


def merge_configs(base: Dict, override: Dict) -> Dict:
    """Deep merge override configuration into base configuration.

    Arrays in override completely replace arrays in base (not merged).
    Nested dictionaries are merged recursively.

    Args:
        base: Base configuration dictionary
        override: Override configuration dictionary

    Returns:
        Merged configuration dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = merge_configs(result[key], value)
        else:
            # Override with value from override config (including arrays)
            result[key] = value

    return result


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
    """Load configuration from centralized global config with skill-specific overrides.

    All AI configuration is centralized in .claude/ai_config.yaml.
    This function extracts global defaults and merges in skill-specific settings.

    Configuration hierarchy:
    1. Code defaults (DEFAULT_TOOLS, DEFAULT_MODELS)
    2. Global settings from .claude/ai_config.yaml (shared across all skills)
    3. Skill-specific overrides from global config (keyed by skill_name)

    Args:
        skill_name: Name of the skill (e.g., 'run-tests', 'sdd-render')

    Returns:
        Dict with complete merged configuration for the skill
    """
    try:
        # Start with code defaults
        result = {
            "tools": DEFAULT_TOOLS.copy(),
            "models": DEFAULT_MODELS.copy()
        }

        # Load global config
        global_config = load_global_config()
        if not global_config:
            return result

        # Extract global defaults (tools, models, consensus, consultation, rendering, enhancement)
        # These are top-level keys that apply to all skills
        global_defaults = {k: v for k, v in global_config.items() if k not in [
            'run-tests', 'sdd-fidelity-review', 'sdd-render'
        ]}

        # Merge global defaults into result
        result = merge_configs(result, global_defaults)

        # Extract and merge skill-specific config if it exists in global config
        if skill_name in global_config:
            skill_specific = global_config[skill_name]
            result = merge_configs(result, skill_specific)

        return result

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


def get_multi_agent_pairs(skill_name: str) -> Dict[str, List[str]]:
    """Get multi-agent pair configurations for consensus-based consultation.

    Loads agent pair definitions from the skill's config.yaml file under the
    'consensus.pairs' section. Each pair defines which agents should be consulted
    together for multi-agent analysis.

    Args:
        skill_name: Name of the skill (e.g., 'run-tests', 'sdd-render')

    Returns:
        Dict mapping pair name to list of agent names. For example:
        {
            "default": ["gemini", "cursor-agent"],
            "code-focus": ["codex", "gemini"],
            "discovery-focus": ["cursor-agent", "gemini"]
        }

    Examples:
        >>> pairs = get_multi_agent_pairs('run-tests')
        >>> pairs['default']
        ['cursor-agent', 'gemini']

        >>> pairs = get_multi_agent_pairs('nonexistent-skill')
        >>> pairs['default']  # Falls back to sensible defaults
        ['gemini', 'cursor-agent']

    Notes:
        - If config.yaml is missing or doesn't have a 'consensus.pairs' section,
          returns sensible default pairs
        - Each pair should contain exactly 2 agents for optimal consensus analysis
        - Agent names must correspond to tools defined in the 'tools' section
    """
    config = load_skill_config(skill_name)

    # Try to load from consensus section
    if 'consensus' in config:
        consensus_config = config['consensus']
        if 'pairs' in consensus_config:
            pairs = consensus_config['pairs']
            # Validate that pairs is a dict and contains lists
            if isinstance(pairs, dict):
                return pairs

    # Return sensible defaults if not found or malformed
    return {
        "default": ["gemini", "cursor-agent"],
        "code-focus": ["codex", "gemini"],
        "discovery-focus": ["cursor-agent", "gemini"]
    }


def get_routing_config(skill_name: str) -> Dict[str, str]:
    """Get routing configuration that maps failure types to multi-agent pairs.

    Loads auto-trigger routing rules from the skill's config.yaml file under the
    'consensus.auto_trigger' section. These rules determine which agent pair should
    be used for different types of test failures or analysis scenarios.

    Args:
        skill_name: Name of the skill (e.g., 'run-tests', 'sdd-render')

    Returns:
        Dict mapping failure/scenario type to pair name. For example:
        {
            "default": "default",
            "fixture": "code-focus",
            "exception": "code-focus",
            "timeout": "default",
            "flaky": "default",
            "multi-file": "discovery-focus"
        }

    Examples:
        >>> routing = get_routing_config('run-tests')
        >>> routing['fixture']
        'code-focus'

        >>> routing = get_routing_config('nonexistent-skill')
        >>> routing['default']  # Falls back to sensible defaults
        'default'

    Notes:
        - If config.yaml is missing or doesn't have 'consensus.auto_trigger',
          returns sensible default routing rules
        - The pair names in routing values should correspond to keys in the
          pairs configuration from get_multi_agent_pairs()
        - The 'default' key is used as fallback when no specific rule matches
    """
    config = load_skill_config(skill_name)

    # Try to load from consensus section
    if 'consensus' in config:
        consensus_config = config['consensus']
        if 'auto_trigger' in consensus_config:
            routing = consensus_config['auto_trigger']
            # Validate that routing is a dict
            if isinstance(routing, dict):
                return routing

    # Return sensible defaults if not found or malformed
    return {
        "default": "default",
        "assertion": "code-focus",
        "exception": "code-focus",
        "fixture": "code-focus",
        "import": "default",
        "timeout": "default",
        "flaky": "default",
        "multi-file": "discovery-focus"
    }
