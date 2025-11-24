"""Shared AI configuration loader for skills.

Loads configuration from the centralized `.claude/ai_config.yaml`, merging global defaults
with any skill-specific overrides that live in the same file. The legacy per-skill
`config.yaml` files have been retired and are only referenced for backwards compatibility
checks.

This module provides a common interface for all skills to load their AI tool configurations.
"""

from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import yaml

from claude_skills.common.ai_tools import build_tool_command

# Default provider/tool configuration (fallback if config file not found)
DEFAULT_TOOLS = {
    "gemini": {
        "description": "Strategic analysis and hypothesis validation",
        "command": "gemini",
        "enabled": True,
    },
    "cursor-agent": {
        "description": "Repository-wide pattern discovery",
        "command": "cursor-agent",
        "enabled": True,
    },
    "codex": {
        "description": "Code-level review and bug fixes",
        "command": "codex",
        "enabled": True,
    },
    "claude": {
        "description": "Extended reasoning and analysis with read-only access",
        "command": "claude",
        "enabled": True,
    },
    "opencode": {
        "description": "User-configurable AI model routing and execution",
        "command": "opencode",
        "enabled": True,
    },
}

# Canonical list of all supported AI tools/providers
# This is the single source of truth for tool names across the toolkit
ALL_SUPPORTED_TOOLS = ["gemini", "cursor-agent", "codex", "claude", "opencode"]

DEFAULT_MODELS = {
    "gemini": {"priority": ["gemini-2.5-flash", "gemini-2.5-pro", "pro"]},
    "cursor-agent": {"priority": ["composer-1", "gpt-5.1-codex"]},
    "codex": {"priority": ["gpt-5.1-codex", "gpt-5.1-codex-mini"]},
    "claude": {"priority": ["sonnet", "haiku"]},
    "opencode": {"priority": ["gpt-5.1-codex", "gpt-5.1-codex-mini"]},
}


DEFAULT_CONSENSUS_AGENTS: List[str] = [
    "cursor-agent",
    "gemini",
    "codex",
    "claude",
    "opencode",
]

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


def _normalize_provider_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure provider-centric configuration is present with backwards compatibility."""
    providers_section: Dict[str, Any] = {}
    existing_providers = config.get("providers")
    if isinstance(existing_providers, dict):
        providers_section = existing_providers

    tools_section = config.get("tools")
    if isinstance(tools_section, dict):
        providers_section = merge_configs(providers_section, tools_section)

    normalized = merge_configs(DEFAULT_TOOLS, providers_section)
    config["providers"] = normalized
    config["tools"] = merge_configs({}, normalized)
    return config


def _get_provider_map(config: Mapping[str, Any]) -> Dict[str, Dict]:
    """Return the provider configuration map, falling back to tools/defaults."""
    providers = config.get("providers")
    if isinstance(providers, dict):
        return providers
    tools = config.get("tools")
    if isinstance(tools, dict):
        return tools
    return DEFAULT_TOOLS


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


def _normalize_context_values(value: Any) -> List[str]:
    """Normalize context values into a list of comparable strings."""
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped, stripped.lower()] if stripped else []
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        results: List[str] = []
        for item in value:
            if isinstance(item, str):
                stripped = item.strip()
                if stripped:
                    results.extend([stripped, stripped.lower()])
            elif item is not None:
                as_str = str(item).strip()
                if as_str:
                    results.extend([as_str, as_str.lower()])
        # Preserve order but dedupe
        deduped: List[str] = []
        seen: set[str] = set()
        for candidate in results:
            if candidate not in seen:
                seen.add(candidate)
                deduped.append(candidate)
        return deduped
    # Fallback to string representation
    as_str = str(value).strip()
    return [as_str, as_str.lower()] if as_str else []


def _extract_priority_from_value(value: Any, tool: str) -> List[str]:
    """Extract a normalized priority list from a configuration value."""
    if isinstance(value, Mapping):
        if tool in value:
            return _extract_priority_from_value(value[tool], tool)
        tool_lower = tool.lower()
        if tool_lower in value:
            return _extract_priority_from_value(value[tool_lower], tool)
        if "priority" in value:
            return _normalize_priority_entry(value.get("priority"))
        # Dictionaries with a single value might just wrap the priority.
        if len(value) == 1:
            only_value = next(iter(value.values()))
            return _extract_priority_from_value(only_value, tool)
    return _normalize_priority_entry(value)


def _extract_override_priority(
    overrides_config: Any,
    tool: str,
    context: Optional[Mapping[str, Any]],
) -> List[str]:
    """Attempt to resolve contextual override priorities for a tool."""
    if not isinstance(overrides_config, Mapping):
        return []

    direct_priority = _extract_priority_from_value(overrides_config.get(tool), tool)
    if direct_priority:
        return direct_priority

    direct_priority = _extract_priority_from_value(
        overrides_config.get(tool.lower()), tool
    )
    if direct_priority:
        return direct_priority

    if context:
        for context_key, context_value in context.items():
            key_map = overrides_config.get(context_key)
            if not isinstance(key_map, Mapping):
                key_map = overrides_config.get(context_key.lower())
            if not isinstance(key_map, Mapping):
                continue

            candidate_keys = _normalize_context_values(context_value)
            for candidate_key in candidate_keys:
                if not candidate_key:
                    continue
                candidate_value = key_map.get(candidate_key)
                if candidate_value is None:
                    candidate_value = key_map.get(candidate_key.lower())
                priority = _extract_priority_from_value(candidate_value, tool)
                if priority:
                    return priority

            for fallback_key in ("*", "default", "__default__"):
                candidate_value = key_map.get(fallback_key)
                priority = _extract_priority_from_value(candidate_value, tool)
                if priority:
                    return priority

    for fallback_key in ("*", "default", "__default__"):
        candidate_value = overrides_config.get(fallback_key)
        priority = _extract_priority_from_value(candidate_value, tool)
        if priority:
            return priority

    return []


def _extract_model_priority(
    models_config: Any,
    tool: str,
    context: Optional[Mapping[str, Any]] = None,
) -> List[str]:
    """Extract model priority list for a tool using configuration and context.

    Resolution order:
    1. Contextual overrides (models.overrides.*)
    2. Skill-level default (models.gemini: "model-name")
    3. Global default priority (fallback to DEFAULT_MODELS)
    """
    if isinstance(models_config, Mapping):
        # 1. Check contextual overrides first (highest priority)
        overrides = models_config.get("overrides")
        override_priority = _extract_override_priority(overrides, tool, context)
        if override_priority:
            return override_priority

        # 2. Check for simple skill-level default (e.g., models.gemini: "gemini-2.5-flash")
        # This is a direct string/list value at the tool key level
        skill_default = models_config.get(tool)
        if skill_default is not None:
            # Could be a simple string or a dict with priority key
            if isinstance(skill_default, str):
                normalized = skill_default.strip()
                if normalized:
                    return [normalized]
            elif isinstance(skill_default, Sequence) and not isinstance(
                skill_default, (str, bytes)
            ):
                priority = _normalize_priority_entry(skill_default)
                if priority:
                    return priority
            elif isinstance(skill_default, Mapping):
                # Support both simple defaults and legacy priority lists
                # e.g., models.gemini.priority: [...]
                priority = _extract_priority_from_value(skill_default, tool)
                if priority:
                    return priority

        # Try lowercase tool name for case-insensitive matching
        skill_default = models_config.get(tool.lower())
        if skill_default is not None:
            if isinstance(skill_default, str):
                normalized = skill_default.strip()
                if normalized:
                    return [normalized]
            elif isinstance(skill_default, Sequence) and not isinstance(
                skill_default, (str, bytes)
            ):
                priority = _normalize_priority_entry(skill_default)
                if priority:
                    return priority
            elif isinstance(skill_default, Mapping):
                priority = _extract_priority_from_value(skill_default, tool)
                if priority:
                    return priority

    elif isinstance(models_config, Sequence) and not isinstance(
        models_config, (str, bytes)
    ):
        # Legacy support where models config may just be a list of priorities.
        return _normalize_priority_entry(models_config)
    elif isinstance(models_config, str):
        return _normalize_priority_entry(models_config)

    return []


def _coerce_override_map(override: Any) -> Tuple[Optional[str], Dict[str, str]]:
    """
    Normalize override input into (default_override, per_tool_overrides).

    Supports:
        - None -> (None, {})
        - "model-name" -> ("model-name", {})
        - {"gemini": "model"} -> (None, {"gemini": "model"})
        - {"default": "model"} -> ("model", {})
        - {"gemini": ["model-a", "model-b"]} -> (None, {"gemini": "model-a"})
    """
    default_override: Optional[str] = None
    per_tool: Dict[str, str] = {}

    if override is None:
        return default_override, per_tool

    if isinstance(override, str):
        normalized = override.strip()
        if normalized:
            default_override = normalized
        return default_override, per_tool

    if not isinstance(override, Mapping):
        return default_override, per_tool

    for key, value in override.items():
        if not isinstance(key, str):
            continue
        normalized_key = key.strip()
        if not normalized_key:
            continue

        priority_list = _normalize_priority_entry(value)
        override_value = priority_list[0] if priority_list else None
        if not override_value:
            continue

        lowered_key = normalized_key.lower()

        if lowered_key in {"*", "default", "__default__"}:
            default_override = override_value
        else:
            per_tool[normalized_key] = override_value
            if lowered_key != normalized_key:
                per_tool[lowered_key] = override_value

    return default_override, per_tool


def _resolve_context_for_tool(
    context: Optional[Mapping[str, Any]], tool: str
) -> Optional[Mapping[str, Any]]:
    """Extract context applicable to a specific tool."""
    if not context or not isinstance(context, Mapping):
        return None

    tool_specific = context.get(tool)
    wildcard_specific = context.get("*")

    all_values_are_mappings = all(isinstance(v, Mapping) for v in context.values())

    if isinstance(tool_specific, Mapping):
        merged: Dict[str, Any] = {}
        if isinstance(wildcard_specific, Mapping):
            merged.update(wildcard_specific)
        merged.update(tool_specific)
        return merged

    if all_values_are_mappings:
        return None

    shared: Dict[str, Any] = {}
    for key, value in context.items():
        if key in {tool, "*"} and isinstance(value, Mapping):
            continue
        if isinstance(value, Mapping):
            continue
        shared[key] = value

    return shared if shared else None


def resolve_tool_model(
    skill_name: str,
    tool: str,
    override: Any = None,
    context: Optional[Mapping[str, Any]] = None,
) -> Optional[str]:
    """
    Resolve the model string for a given tool within a skill.

    Resolution order:
        1. CLI override (global or per-tool)
        2. Skill config contextual overrides (models.overrides.*)
        3. Skill-level default (e.g., code-doc.models.gemini: "gemini-2.5-flash")
        4. Global default priority (models.gemini.priority[0])
        5. DEFAULT_MODELS fallback (code defaults)

    The skill-level default provides a simple way to set a default model for a
    specific tool within a skill, without needing contextual overrides. This
    overrides the global default but still allows fallback if the model is
    unavailable.

    Returns:
        Model identifier string or None if no model is configured.
    """
    if not tool or not isinstance(tool, str):
        return None

    normalized_tool = tool.strip()
    if not normalized_tool:
        return None

    default_override, per_tool_overrides = _coerce_override_map(override)
    if normalized_tool in per_tool_overrides:
        return per_tool_overrides[normalized_tool]

    wildcard_override_key = normalized_tool.lower()
    if wildcard_override_key in per_tool_overrides:
        return per_tool_overrides[wildcard_override_key]

    if default_override:
        return default_override

    skill_config = load_skill_config(skill_name)
    models_config = (
        skill_config.get("models") if isinstance(skill_config, Mapping) else {}
    )
    tool_context = _resolve_context_for_tool(context, normalized_tool)

    priority = _extract_model_priority(models_config, normalized_tool, tool_context)
    if priority:
        return priority[0]

    default_priority = _normalize_priority_entry(DEFAULT_MODELS.get(normalized_tool))
    return default_priority[0] if default_priority else None


def resolve_models_for_tools(
    skill_name: str,
    tools: Iterable[str],
    override: Any = None,
    context: Optional[Mapping[str, Any]] = None,
) -> "OrderedDict[str, Optional[str]]":
    """
    Resolve models for a collection of tools, preserving input order.

    Args:
        skill_name: Name of the skill requesting tool models.
        tools: Iterable of tool names (strings).
        override: Optional CLI override (string or mapping).
        context: Optional shared context or dict-of-dicts keyed by tool.

    Returns:
        OrderedDict mapping tool names to resolved model strings (or None).
    """
    if tools is None:
        return OrderedDict()

    normalized_tools: List[str] = []
    seen: set[str] = set()
    for tool in tools:
        if not isinstance(tool, str):
            continue
        stripped = tool.strip()
        if not stripped or stripped in seen:
            continue
        seen.add(stripped)
        normalized_tools.append(stripped)

    default_override, per_tool_overrides = _coerce_override_map(override)

    resolved: "OrderedDict[str, Optional[str]]" = OrderedDict()
    for tool_name in normalized_tools:
        per_tool_override = per_tool_overrides.get(tool_name)
        if per_tool_override is None:
            per_tool_override = per_tool_overrides.get(tool_name.lower())

        tool_context = _resolve_context_for_tool(context, tool_name)
        resolved_model = resolve_tool_model(
            skill_name=skill_name,
            tool=tool_name,
            override=per_tool_override
            if per_tool_override is not None
            else default_override,
            context=tool_context,
        )
        resolved[tool_name] = resolved_model

    return resolved


def get_preferred_model(skill_name: str, tool_name: str) -> Optional[str]:
    """Return the highest-priority configured model for a tool if available."""
    return resolve_tool_model(skill_name, tool_name)


def get_global_config_path() -> Path:
    """
    Get the path to the global AI configuration file by searching upwards from the current directory.

    Searches for `.claude/ai_config.yaml` in the current directory and its parent
    directories until it finds the file or reaches the filesystem root. This makes
    the configuration discovery robust to the user's working directory.

    Returns:
        Path to the found ai_config.yaml, or the path where it would be expected
        in the current directory if not found anywhere.
    """
    current_dir = Path.cwd().resolve()

    # Search upwards from the current directory for the config file
    while True:
        potential_path = current_dir / ".claude" / "ai_config.yaml"
        if potential_path.exists():
            return potential_path

        # Stop if we've reached the root of the filesystem
        if current_dir.parent == current_dir:
            break

        current_dir = current_dir.parent

    # As a fallback for development, check relative to this source file.
    try:
        # This file is in src/claude_skills/claude_skills/common/ai_config.py
        # The project root is 5 levels up.
        dev_root = Path(__file__).resolve().parents[4]
        dev_path = dev_root / ".claude" / "ai_config.yaml"
        if dev_path.exists():
            return dev_path
    except IndexError:
        # This can fail if the file structure is not as expected.
        pass

    # If no config is found anywhere, return the default path in the CWD.
    # This is where a new config would be created.
    return Path.cwd() / ".claude" / "ai_config.yaml"


def load_global_config() -> Dict:
    """Load the global AI configuration file.

    Returns:
        Dictionary with global configuration, or empty dict if file doesn't exist
    """
    config_path = get_global_config_path()

    try:
        if not config_path.exists():
            return {}

        with open(config_path, "r") as f:
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
        Path(__file__).parent.parent.parent.parent.parent
        / "skills"
        / skill_name
        / "config.yaml",
        # From development location
        Path(__file__).parent.parent.parent.parent
        / "skills"
        / skill_name
        / "config.yaml",
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
        result = {"tools": DEFAULT_TOOLS.copy(), "models": DEFAULT_MODELS.copy()}

        # Load global config
        global_config = load_global_config()
        if not global_config:
            return result

        # These are top-level keys that apply to all skills
        KNOWN_GLOBAL_KEYS = {
            "tools",
            "models",
            "consensus",
            "consultation",
            "rendering",
            "enhancement",
        }

        # Extract global defaults
        global_defaults = {
            k: v for k, v in global_config.items() if k in KNOWN_GLOBAL_KEYS
        }

        # Merge global defaults into result
        result = merge_configs(result, global_defaults)

        # Extract and merge skill-specific config if it exists in global config
        if skill_name in global_config:
            skill_specific = global_config[skill_name]
            result = merge_configs(result, skill_specific)

        return _normalize_provider_settings(result)

    except (yaml.YAMLError, IOError, KeyError) as e:
        # Error loading config, fall back to defaults
        return _normalize_provider_settings(
            {"tools": DEFAULT_TOOLS.copy(), "models": DEFAULT_MODELS.copy()}
        )


def get_enabled_tools(skill_name: str) -> Dict[str, Dict]:
    """Get only the enabled tools from configuration.

    Args:
        skill_name: Name of the skill

    Returns:
        Dict mapping tool name to tool configuration (only enabled tools)
    """
    config = load_skill_config(skill_name)
    providers = _get_provider_map(config)

    return {
        name: tool_config
        for name, tool_config in providers.items()
        if tool_config.get("enabled", True)
    }


def get_agent_priority(
    skill_name: str, default_order: Optional[List[str]] = None
) -> List[str]:
    """Get the priority-ordered list of agents to try.

    Args:
        skill_name: Name of the skill
        default_order: Default priority order if not in config

    Returns:
        List of agent names in priority order (highest first)
    """
    config = load_skill_config(skill_name)

    # Try skill-specific rendering config first
    if "rendering" in config:
        rendering_config = config["rendering"]
        if "agent_priority" in rendering_config:
            return rendering_config["agent_priority"]

    # Fall back to consultation config (for run-tests compatibility)
    if "consultation" in config:
        consultation_config = config["consultation"]
        if "agent_priority" in consultation_config:
            return consultation_config["agent_priority"]

    # Use provided default or sensible fallback
    return default_order or ALL_SUPPORTED_TOOLS


def get_agent_command(
    skill_name: str,
    agent_name: str,
    prompt: str,
    *,
    model_override: Any = None,
    context: Optional[Mapping[str, Any]] = None,
) -> List[str]:
    """Build the command list for invoking an agent.

    Args:
        skill_name: Name of the skill
        agent_name: Name of the agent (gemini, cursor-agent, codex)
        prompt: The prompt to send to the agent
        model_override: Optional explicit model override (string or mapping)
        context: Optional context mapping used for contextual overrides

    Returns:
        List of command arguments for subprocess.run
    """
    preferred_model = resolve_tool_model(
        skill_name,
        agent_name,
        override=model_override,
        context=context,
    )

    try:
        return build_tool_command(agent_name, prompt, model=preferred_model)
    except ValueError:
        # Unknown tool - fall back to minimal command to maintain backwards compatibility
        return [agent_name, prompt]


def get_timeout(skill_name: str, timeout_type: str = "default") -> int:
    """Get timeout value in seconds.

    Args:
        skill_name: Name of the skill
        timeout_type: Type of timeout ('default', 'narrative', 'consultation')

    Returns:
        Timeout in seconds
    """
    config = load_skill_config(skill_name)

    # Try rendering config (sdd-render)
    if "rendering" in config:
        rendering_config = config["rendering"]
        if timeout_type == "narrative":
            return rendering_config.get("narrative_timeout_seconds", 30)
        return rendering_config.get("timeout_seconds", 90)

    # Try consultation config (run-tests)
    if "consultation" in config:
        consultation_config = config["consultation"]
        return consultation_config.get("timeout_seconds", 90)

    # Default fallback
    return 90 if timeout_type == "default" else 30


def get_tool_config(skill_name: str, tool_name: str) -> Optional[Dict]:
    """Get configuration for a specific tool.

    Args:
        skill_name: Name of the skill
        tool_name: Name of the tool

    Returns:
        Tool configuration dict or None if not found
    """
    config = load_skill_config(skill_name)
    providers = _get_provider_map(config)
    return providers.get(tool_name)


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
    return tool_config.get("enabled", True)


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


def get_tool_priority(
    skill_name: str, context: Optional[Mapping[str, Any]] = None
) -> List[str]:
    """Get the priority-ordered list of tools/providers for fallback.

    Tools are consulted in priority order when fallback is enabled. If a tool
    fails, the next tool in the list is tried automatically.

    Args:
        skill_name: Name of the skill
        context: Optional context for contextual overrides

    Returns:
        List of tool names in priority order (highest first)
    """
    config = load_skill_config(skill_name)
    global_config = load_global_config()

    # Try skill-specific tool_priority first
    if "tool_priority" in config:
        priority = config["tool_priority"]
        if isinstance(priority, (list, tuple)):
            return _dedupe_preserve_order(priority)

    # Try global tool_priority
    if "tool_priority" in global_config:
        global_tool_priority = global_config["tool_priority"]
        if isinstance(global_tool_priority, dict):
            # Check for context-specific priority
            if context:
                for context_key, context_value in context.items():
                    candidate_keys = _normalize_context_values(context_value)
                    for candidate_key in candidate_keys:
                        if candidate_key in global_tool_priority:
                            priority = global_tool_priority[candidate_key]
                            if isinstance(priority, (list, tuple)):
                                return _dedupe_preserve_order(priority)

            # Use default priority from global config
            if "default" in global_tool_priority:
                priority = global_tool_priority["default"]
                if isinstance(priority, (list, tuple)):
                    return _dedupe_preserve_order(priority)

        # Direct list in global config
        if isinstance(global_tool_priority, (list, tuple)):
            return _dedupe_preserve_order(global_tool_priority)

    # Fallback: return all enabled tools
    enabled_tools = get_enabled_tools(skill_name)
    return list(enabled_tools.keys())


def get_fallback_config(skill_name: str) -> Dict[str, Any]:
    """Get fallback configuration for the skill.

    Returns configuration for automatic fallback to alternative tools on failure.

    Args:
        skill_name: Name of the skill

    Returns:
        Dict with fallback configuration:
            - enabled (bool): Whether fallback is enabled
            - max_retries_per_tool (int): Number of retries before moving to next tool
            - retry_on_status (List[str]): Status codes that trigger retry
            - skip_on_status (List[str]): Status codes that skip to next tool
            - retry_delay_seconds (int): Delay between retry attempts
    """
    config = load_skill_config(skill_name)
    global_config = load_global_config()

    # Default fallback config
    default_fallback = {
        "enabled": True,
        "max_retries_per_tool": 2,
        "retry_on_status": ["timeout", "error"],
        "skip_on_status": ["not_found", "invalid_output"],
        "retry_delay_seconds": 1,
    }

    # Try global fallback config
    global_fallback = global_config.get("fallback", {})
    if global_fallback:
        default_fallback = merge_configs(default_fallback, global_fallback)

    # Try skill-specific fallback config (overrides global)
    skill_fallback = config.get("fallback", {})
    if skill_fallback:
        default_fallback = merge_configs(default_fallback, skill_fallback)

    return default_fallback


def get_consultation_limit(skill_name: str) -> Optional[int]:
    """Get the maximum number of unique tools allowed per skill run.

    This limit controls how many distinct AI tools/providers can be consulted
    during a single skill invocation. For example, with a limit of 2, the skill
    might consult gemini and cursor-agent but not codex.

    Args:
        skill_name: Name of the skill

    Returns:
        Maximum number of unique tools allowed, or None for unlimited
    """
    config = load_skill_config(skill_name)
    global_config = load_global_config()

    # Try skill-specific consultation_limits first
    if "consultation_limits" in config:
        limits = config["consultation_limits"]
        if isinstance(limits, dict):
            max_tools = limits.get("max_tools_per_run")
            if isinstance(max_tools, int) and max_tools > 0:
                return max_tools

    # Try global consultation_limits
    if "consultation_limits" in global_config:
        limits = global_config["consultation_limits"]
        if isinstance(limits, dict):
            max_tools = limits.get("max_tools_per_run")
            if isinstance(max_tools, int) and max_tools > 0:
                return max_tools

    # No limit configured
    return None
