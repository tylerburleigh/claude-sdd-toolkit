"""
SDD Next Operations

Modular operations for spec-driven development task discovery and execution planning.
"""

from .discovery import get_next_task, get_task_info, check_dependencies, prepare_task
from .project import detect_project, find_tests, check_environment, find_related_files
from .validation import validate_spec, find_circular_deps, validate_paths, spec_stats
from .workflow import init_environment, find_pattern

__all__ = [
    # Task discovery
    "get_next_task",
    "get_task_info",
    "check_dependencies",
    "prepare_task",

    # Project analysis
    "detect_project",
    "find_tests",
    "check_environment",
    "find_related_files",

    # Validation
    "validate_spec",
    "find_circular_deps",
    "validate_paths",
    "spec_stats",

    # Workflow utilities
    "init_environment",
    "find_pattern",
]
