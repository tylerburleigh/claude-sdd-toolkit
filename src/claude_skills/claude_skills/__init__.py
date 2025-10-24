"""Claude Code Skills - Spec-Driven Development Implementation

A professional Python package for SDD workflows.
"""

__version__ = "0.1.0"
__author__ = "Claude Code Team"

# Export commonly used functions for convenience
from claude_skills.common import (
    find_specs_directory,
    load_json_spec,
    PrettyPrinter,
)

__all__ = [
    "__version__",
    "find_specs_directory",
    "load_json_spec",
    "PrettyPrinter",
]
