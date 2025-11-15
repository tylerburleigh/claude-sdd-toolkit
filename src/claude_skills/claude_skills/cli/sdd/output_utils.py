"""Output utilities for SDD command handlers.

This module provides helpers for command handlers to respect verbosity levels
when generating output. All handlers receive args.verbosity_level automatically.
"""

from typing import Any, Dict, Set, Optional
from claude_skills.cli.sdd.verbosity import (
    VerbosityLevel,
    should_omit_empty_fields,
    should_include_debug_info,
    filter_output_fields
)


def prepare_output(data: Dict[str, Any], args,
                   essential_fields: Optional[Set[str]] = None,
                   standard_fields: Optional[Set[str]] = None) -> Dict[str, Any]:
    """Prepare command output based on verbosity level.

    This is the main entry point for command handlers to filter their
    output according to the user's requested verbosity level.

    Args:
        data: Raw output dictionary from command
        args: Parsed command arguments (contains verbosity_level)
        essential_fields: Fields to always include (even in QUIET mode)
        standard_fields: Fields to include in NORMAL/VERBOSE modes

    Returns:
        Filtered output dictionary based on verbosity level

    Example:
        >>> from claude_skills.cli.sdd.output_utils import prepare_output
        >>> data = {
        ...     'spec_id': 'my-spec',
        ...     'status': 'active',
        ...     'title': 'My Spec',
        ...     'total_tasks': 10,
        ...     'metadata': {}  # empty
        ... }
        >>> essential = {'spec_id', 'status', 'title'}
        >>> output = prepare_output(data, args, essential)
        # In QUIET mode: only spec_id, status, title (metadata omitted)
        # In NORMAL mode: all fields except empty ones
        # In VERBOSE mode: all fields including empty ones
    """
    verbosity_level = getattr(args, 'verbosity_level', VerbosityLevel.NORMAL)
    return filter_output_fields(data, verbosity_level, essential_fields, standard_fields)


def should_show_field(args, field_name: str, value: Any,
                     is_essential: bool = False,
                     is_standard: bool = True) -> bool:
    """Check if a field should be included in output.

    Useful for conditional output building in command handlers.

    Args:
        args: Parsed command arguments (contains verbosity_level)
        field_name: Name of the field
        value: Value of the field
        is_essential: True if field is essential (always show in QUIET)
        is_standard: True if field is standard (show in NORMAL/VERBOSE)

    Returns:
        True if field should be included in output

    Example:
        >>> if should_show_field(args, 'metadata', metadata, is_standard=True):
        ...     output['metadata'] = metadata
    """
    verbosity_level = getattr(args, 'verbosity_level', VerbosityLevel.NORMAL)

    # VERBOSE: show everything
    if verbosity_level == VerbosityLevel.VERBOSE:
        return True

    # QUIET: only essential fields, and omit empty values
    if verbosity_level == VerbosityLevel.QUIET:
        if not is_essential:
            return False
        # Omit empty values even for essential fields
        if value is None or value == [] or value == {}:
            return False
        return True

    # NORMAL: essential + standard fields
    if is_essential or is_standard:
        return True

    return False


def add_debug_info(data: Dict[str, Any], args, debug_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add debug information to output if in VERBOSE mode.

    Args:
        data: Output dictionary to add debug info to
        args: Parsed command arguments (contains verbosity_level)
        debug_data: Debug information dictionary

    Returns:
        Output dictionary with _debug section added if appropriate

    Example:
        >>> output = {'spec_id': 'my-spec', 'status': 'active'}
        >>> debug = {'query_time_ms': 15, 'cache_hit': True}
        >>> output = add_debug_info(output, args, debug)
        # In VERBOSE mode: output['_debug'] = debug
        # In other modes: output unchanged
    """
    verbosity_level = getattr(args, 'verbosity_level', VerbosityLevel.NORMAL)

    if should_include_debug_info(verbosity_level):
        data['_debug'] = debug_data

    return data


# Field sets for common commands (based on essential-messages-per-level.md)

# list-specs command
LIST_SPECS_ESSENTIAL = {'spec_id', 'status', 'title', 'progress_percentage'}
LIST_SPECS_STANDARD = {
    'spec_id', 'status', 'title', 'progress_percentage',
    'total_tasks', 'completed_tasks', 'current_phase',
    'version', 'created_at', 'updated_at'
}

# query-tasks command
QUERY_TASKS_ESSENTIAL = {'id', 'title', 'type', 'status', 'parent'}
QUERY_TASKS_STANDARD = {
    'id', 'title', 'type', 'status', 'parent',
    'completed_tasks', 'total_tasks', 'metadata'
}

# progress command
PROGRESS_ESSENTIAL = {'spec_id', 'total_tasks', 'completed_tasks', 'percentage', 'current_phase'}
PROGRESS_STANDARD = {
    'spec_id', 'title', 'status', 'total_tasks', 'completed_tasks',
    'percentage', 'remaining_tasks', 'current_phase', 'node_id', 'type'
}

# prepare-task command
PREPARE_TASK_ESSENTIAL = {'success', 'task_id', 'task_data', 'dependencies'}
PREPARE_TASK_STANDARD = {
    'success', 'task_id', 'task_data', 'dependencies',
    'repo_root', 'needs_branch_creation', 'dirty_tree_status',
    'needs_commit_cadence', 'spec_complete'
}

# validate command
VALIDATE_ESSENTIAL = {'status'}
VALIDATE_STANDARD = {
    'status', 'spec_id', 'errors', 'warnings',
    'auto_fixable_issues', 'schema'
}

# check-deps command
CHECK_DEPS_ESSENTIAL = {'task_id', 'can_start'}
CHECK_DEPS_STANDARD = {
    'task_id', 'can_start', 'blocked_by',
    'soft_depends', 'blocks'
}
