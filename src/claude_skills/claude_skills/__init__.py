"""Claude Code Skills - Spec-Driven Development Implementation

A professional Python package for SDD workflows.
"""

# Get version from installed package metadata
try:
    from importlib.metadata import version
    __version__ = version("claude-skills")
except Exception:
    # Fallback if package not installed (development mode)
    __version__ = "0.0.0-dev"

__author__ = "Claude Code Team"

# Export commonly used functions for convenience
from claude_skills.common import (
    find_specs_directory,
    load_json_spec,
    PrettyPrinter,
)

# SDD Render - Convert JSON specs to human-readable markdown
from claude_skills.sdd_render import SpecRenderer, AIEnhancedRenderer

__all__ = [
    "__version__",
    "find_specs_directory",
    "load_json_spec",
    "PrettyPrinter",
    "SpecRenderer",
    "AIEnhancedRenderer",
]
