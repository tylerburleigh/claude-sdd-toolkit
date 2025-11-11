"""Shared AI configuration loader for skills.

Loads configuration from the centralized `.claude/ai_config.yaml`, merging global defaults
with any skill-specific overrides that live in the same file. The legacy per-skill
`config.yaml` files have been retired and are only referenced for backwards compatibility
checks.

This module provides a common interface for all skills to load their AI tool configurations.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from claude_skills.common.ai_tools import build_tool_command


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
        "priority": ["gemini-2.5-pro"]
    },
    "cursor-agent": {
        "priority": ["composer-1"]
    },
    "codex": {
        "priority": ["gpt-5-codex"]
    }
}


DEFAULT_CONSENSUS_AGENTS: List[str] = ["cursor-agent", "gemini", "codex"]

DEFAULT_AUTO_TRIGGER_RULES: Dict[str, bool] = {
    "default": False,
    "assertion": True,
    "exception": True,
    "fixture": True,
    "import": False,
    "timeout": True,
    "flaky": False,
    "multi-file": True,
}


def _normalize_priority_entry(entry: object) -> List[str]:
    """Normalize model priority definition to a clean list of strings."""
    if isinstance(entry, dict):
        values = entry.get("priority")
        return _normalize_priority_entry(values)
    if isinstance(entry, (list, tuple)):
        normalized: List[str] = []
        for item in entry:
            if isinstance(item, str):
                stripped = item.strip()
                if stripped:
                    normalized.append(stripped)
        return normalized
    if isinstance(entry, str):
        stripped = entry.strip()
        return [stripped] if stripped else []
    return []


def _dedupe_preserve_order(items: Sequence[str]) -> List[str]:
    """Remove duplicates while preserving the original order."""
    seen: set[str] = set()
    result: List[str] = []
    for item in items:
        if not item or not isinstance(item, str):
            continue
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def get_preferred_model(skill_name: str, tool_name: str) -> Optional[str]:
    """Return the highest-priority configured model for a tool if available."""
    config = load_skill_config(skill_name)
    models = config.get("models", {})
    priority = _normalize_priority_entry(models.get(tool_name))

    if priority:
        return priority[0]

    # Fall back to builtin defaults if present
    default_priority = _normalize_priority_entry(DEFAULT_MODELS.get(tool_name))
    return default_priority[0] if default_priority else None


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
    """Locate the legacy per-skill `config.yaml` file if it still exists.

    All live configuration now resides in `.claude/ai_config.yaml`; this helper is retained
    for backwards compatibility with historical tooling that expected a file under
    `skills/{skill_name}/config.yaml`.

    Args:
        skill_name: Name of the skill (e.g., 'run-tests', 'sdd-render')

    Returns:
        Path to the historical config.yaml location for the skill (may not exist)
    """
    # This file is in src/claude_skills/claude_skills/common/ai_config.py
    # We need to find the legacy skills/{skill_name}/config.yaml path.

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

    model_priority: Sequence[str] = ()
    model_config = models.get(agent_name)
    if isinstance(model_config, dict):
        priority_value = model_config.get('priority')
        if isinstance(priority_value, (list, tuple)):
            model_priority = priority_value
    elif isinstance(model_config, (list, tuple)):
        model_priority = model_config

    preferred_model = model_priority[0] if model_priority else None

    try:
        return build_tool_command(agent_name, prompt, model=preferred_model)
    except ValueError:
        # Unknown tool - fall back to minimal command to maintain backwards compatibility
        return [agent_name, prompt]


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


def _normalize_auto_trigger_value(value: object) -> bool:
    """Convert legacy or malformed auto-trigger values into booleans."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        stripped = value.strip().lower()
        if stripped in {"", "false", "0", "no", "off", "none"}:
            return False
        # Legacy configs used pair names; any non-empty string should be treated as enabled.
        return True
    if isinstance(value, (int, float)):
        return bool(value)
    return bool(value)


def get_consensus_agents(skill_name: str) -> List[str]:
    """Return the prioritized list of agents to use for consensus consultations.

    Reads the flat `consensus.agents` list from `.claude/ai_config.yaml`.
    Falls back to legacy pair definitions (flattened) or built-in defaults
    when the configuration is missing or malformed.
    """
    config = load_skill_config(skill_name)
    consensus_config = config.get("consensus", {})

    agents = consensus_config.get("agents")
    if isinstance(agents, (list, tuple)):
        agent_list = _dedupe_preserve_order(agents)
        if agent_list:
            return agent_list

    # Legacy support: flatten pairs into a single list while preserving order.
    pairs = consensus_config.get("pairs")
    if isinstance(pairs, dict):
        flattened: List[str] = []
        for pair_members in pairs.values():
            if isinstance(pair_members, (list, tuple)):
                flattened.extend(str(agent) for agent in pair_members)
        flattened_agents = _dedupe_preserve_order(flattened)
        if flattened_agents:
            return flattened_agents

    return DEFAULT_CONSENSUS_AGENTS.copy()


def get_routing_config(skill_name: str) -> Dict[str, bool]:
    """Return the auto-trigger configuration for multi-agent consensus.

    The configuration is stored under `consensus.auto_trigger` in `.claude/ai_config.yaml`
    as a map of failure type -> boolean. Legacy configurations that map failure types to
    pair names are coerced to `True` so consensus still triggers automatically.
    """
    config = load_skill_config(skill_name)
    consensus_config = config.get("consensus", {})

    routing_config = DEFAULT_AUTO_TRIGGER_RULES.copy()

    auto_trigger = consensus_config.get("auto_trigger")
    if isinstance(auto_trigger, dict):
        for key, value in auto_trigger.items():
            normalized = _normalize_auto_trigger_value(value)
            routing_config[key] = normalized

    return routing_config
