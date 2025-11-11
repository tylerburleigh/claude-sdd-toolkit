"""
Resource package marker and metadata for setup templates.

This makes the `setup` directory importable so `importlib.resources` (and
similar utilities) can locate bundled setup templates programmatically.
The exported constants list each template filename for downstream helpers.
"""

from __future__ import annotations

AI_CONFIG_TEMPLATE = "ai_config.yaml"
GIT_CONFIG_TEMPLATE = "git_config.json"
SDD_CONFIG_TEMPLATE = "sdd_config.json"
SETTINGS_LOCAL_TEMPLATE = "settings.local.json"

ALL_SETUP_TEMPLATES = (
    AI_CONFIG_TEMPLATE,
    GIT_CONFIG_TEMPLATE,
    SDD_CONFIG_TEMPLATE,
    SETTINGS_LOCAL_TEMPLATE,
)

__all__ = [
    "AI_CONFIG_TEMPLATE",
    "GIT_CONFIG_TEMPLATE",
    "SDD_CONFIG_TEMPLATE",
    "SETTINGS_LOCAL_TEMPLATE",
    "ALL_SETUP_TEMPLATES",
]
