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


def get_bool_arg(args, name: str, default: bool = False) -> bool:
    """Safely read a boolean argparse flag from args.

    Handles mock objects and missing attributes by falling back to default.
    """
    if args is None:
        return default
    value = getattr(args, name, default)
    return value if isinstance(value, bool) else default


def is_json_mode(args) -> bool:
    """Return True when --json (or json mode) is explicitly enabled."""
    return get_bool_arg(args, 'json', False)


def is_quiet_mode(args) -> bool:
    """Return True when quiet mode is explicitly enabled."""
    return get_bool_arg(args, 'quiet', False)


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
    'version', 'created_at', 'updated_at',
    'description', 'author', 'file_path'
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
PREPARE_TASK_ESSENTIAL = {
    'task_id', 'task_data', 'dependencies', 'context',
    'needs_branch_creation', 'suggested_branch_name',
    'dirty_tree_status', 'validation_warnings',
    'spec_complete'
}
PREPARE_TASK_STANDARD = {
    'success', 'task_id', 'task_data', 'dependencies', 'context',
    'repo_root', 'needs_branch_creation', 'dirty_tree_status',
    'needs_commit_cadence', 'spec_complete',
    'completion_info', 'doc_context'
}

# validate command
VALIDATE_ESSENTIAL = {'status', 'errors', 'warnings', 'auto_fixable_issues'}
VALIDATE_STANDARD = {
    'status', 'spec_id', 'errors', 'warnings',
    'auto_fixable_issues', 'schema'
}

# fix command (sdd_validate)
FIX_SPEC_ESSENTIAL = {'spec_id', 'applied_action_count', 'post_status', 'remaining_issues'}
FIX_SPEC_STANDARD = {
    'spec_id', 'applied_action_count', 'skipped_action_count',
    'migration_action_count', 'backup_path', 'remaining_errors',
    'remaining_warnings', 'remaining_issues', 'post_status', 'migrated_tasks'
}

# stats command (sdd_validate)
STATS_ESSENTIAL = {'spec_id', 'totals', 'status_counts'}
STATS_STANDARD = {
    'spec_id', 'title', 'version', 'status', 'totals',
    'status_counts', 'max_depth', 'avg_tasks_per_phase',
    'verification_coverage', 'progress', 'file_size_kb'
}

# analyze-deps command (sdd_validate)
ANALYZE_DEPS_ESSENTIAL = {'status'}
ANALYZE_DEPS_STANDARD = {
    'cycles', 'orphaned', 'deadlocks', 'bottlenecks', 'status'
}

# context command (context_tracker)
CONTEXT_ESSENTIAL = {'context_percentage_used'}
CONTEXT_STANDARD = {
    'context_length', 'context_percentage', 'max_context',
    'input_tokens', 'output_tokens', 'cached_tokens',
    'total_tokens', 'transcript_path', 'context_percentage_used'
}

# cache-clear command (cache)
CACHE_CLEAR_ESSENTIAL = {'entries_deleted'}
CACHE_CLEAR_STANDARD = {'entries_deleted', 'filters'}

# cache-stats command (cache)
CACHE_STATS_ESSENTIAL = {'total_entries', 'active_entries'}
CACHE_STATS_STANDARD = {
    'cache_dir', 'total_entries', 'active_entries',
    'expired_entries', 'total_size_mb', 'total_size_bytes'
}

# list-plan-review-tools command (sdd_plan_review)
LIST_TOOLS_ESSENTIAL = {'available_count', 'total'}
LIST_TOOLS_STANDARD = {'available', 'disabled', 'not_installed', 'total', 'available_count'}

# check-deps command
CHECK_DEPS_ESSENTIAL = {'can_start', 'blocked_by'}
CHECK_DEPS_STANDARD = {
    'task_id', 'can_start', 'blocked_by',
    'soft_depends', 'blocks'
}

# list-blockers command
LIST_BLOCKERS_ESSENTIAL = {
    'id', 'title', 'type', 'blocked_at',
    'blocker_type', 'blocker_description'
}
LIST_BLOCKERS_STANDARD = {
    'id', 'title', 'type', 'blocked_at',
    'blocker_type', 'blocker_description',
    'blocker_ticket', 'blocked_by_external'
}

# find-specs command
FIND_SPECS_ESSENTIAL = {'specs_dir'}
FIND_SPECS_STANDARD = {'specs_dir', 'auto_detected', 'exists'}

# next-task command
NEXT_TASK_ESSENTIAL = {'task_id', 'title'}
NEXT_TASK_STANDARD = {'task_id', 'title', 'status', 'file_path', 'estimated_hours'}

# task-info command
TASK_INFO_ESSENTIAL = {'title', 'status', 'dependencies', 'metadata'}
TASK_INFO_STANDARD = {
    'id', 'type', 'title', 'status', 'parent', 'children',
    'dependencies', 'total_tasks', 'completed_tasks', 'metadata'
}

# init-env command
INIT_ENV_ESSENTIAL = {'success', 'specs_dir', 'active_dir'}
INIT_ENV_STANDARD = {'success', 'specs_dir', 'active_dir', 'state_dir'}

# validate-spec command
VALIDATE_SPEC_ESSENTIAL = {'valid', 'errors'}
VALIDATE_SPEC_STANDARD = {'valid', 'errors', 'warnings', 'spec_id', 'schema_version'}

# find-pattern command
FIND_PATTERN_ESSENTIAL = {'pattern', 'matches'}
FIND_PATTERN_STANDARD = {'pattern', 'matches', 'files_searched', 'search_paths'}

# detect-project command
DETECT_PROJECT_ESSENTIAL = {'project_type'}
DETECT_PROJECT_STANDARD = {'project_type', 'confidence', 'indicators', 'project_root'}

# find-tests command
FIND_TESTS_ESSENTIAL = {'test_files'}
FIND_TESTS_STANDARD = {'test_files', 'test_framework', 'test_count', 'test_directories'}

# check-environment command
CHECK_ENVIRONMENT_ESSENTIAL = {'status'}
CHECK_ENVIRONMENT_STANDARD = {'status', 'python_version', 'dependencies', 'missing', 'warnings'}

# find-circular-deps command
FIND_CIRCULAR_DEPS_ESSENTIAL = {'has_cycles', 'cycles'}
FIND_CIRCULAR_DEPS_STANDARD = {'has_cycles', 'cycles', 'total_tasks', 'analyzed'}

# find-related-files command
FIND_RELATED_FILES_ESSENTIAL = {'task_id', 'related_files'}
FIND_RELATED_FILES_STANDARD = {'task_id', 'related_files', 'file_types', 'relationships'}

# validate-paths command
VALIDATE_PATHS_ESSENTIAL = {'valid', 'invalid_paths'}
VALIDATE_PATHS_STANDARD = {'valid', 'invalid_paths', 'validated_count', 'warnings'}

# spec-stats command
SPEC_STATS_ESSENTIAL = {'spec_id', 'total_tasks', 'completed_tasks'}
SPEC_STATS_STANDARD = {
    'spec_id', 'total_tasks', 'completed_tasks', 'percentage',
    'phases', 'task_types', 'estimated_hours', 'actual_hours'
}

# format-plan command
FORMAT_PLAN_ESSENTIAL = {'formatted'}
FORMAT_PLAN_STANDARD = {'formatted', 'plan_structure', 'sections', 'word_count'}

# sdd-plan commands
PLAN_CREATE_ESSENTIAL = {'success', 'spec_id', 'spec_path', 'message'}
PLAN_CREATE_STANDARD = {
    'success', 'spec_id', 'spec_path', 'message',
    'template', 'phase_count', 'estimated_hours', 'default_category'
}
PLAN_ANALYZE_ESSENTIAL = {'directory', 'has_specs', 'documentation_available'}
PLAN_ANALYZE_STANDARD = {
    'directory', 'has_specs', 'specs_directory',
    'documentation_available', 'analysis_success',
    'analysis_error', 'doc_stats'
}
PLAN_TEMPLATE_LIST_ESSENTIAL = {'templates'}
PLAN_TEMPLATE_LIST_STANDARD = {'templates', 'count', 'usage_hint'}
PLAN_TEMPLATE_SHOW_ESSENTIAL = {'template_id', 'template', 'message'}
PLAN_TEMPLATE_SHOW_STANDARD = {'template_id', 'template', 'message'}

# sdd-render command
RENDER_SPEC_ESSENTIAL = {'spec_id', 'output_path', 'mode', 'enhancement_level', 'fallback_used'}
RENDER_SPEC_STANDARD = {
    'spec_id', 'output_path', 'mode', 'enhancement_level',
    'fallback_used', 'fallback_reason', 'model_override',
    'output_size', 'task_count'
}

# sdd-pr command
PR_CONTEXT_ESSENTIAL = {'spec_id', 'mode', 'branch_name', 'context_counts'}
PR_CONTEXT_STANDARD = {
    'spec_id', 'mode', 'branch_name', 'base_branch',
    'context_counts', 'diff_bytes', 'repo_root'
}
PR_CREATE_ESSENTIAL = {'success', 'spec_id', 'pr_url', 'pr_number'}
PR_CREATE_STANDARD = {
    'success', 'spec_id', 'pr_url', 'pr_number',
    'branch_name', 'base_branch', 'pr_title', 'error'
}

# sdd-spec-mod commands
SPEC_MOD_APPLY_ESSENTIAL = {
    'success', 'spec_id', 'total_operations',
    'successful_operations', 'failed_operations', 'dry_run'
}
SPEC_MOD_APPLY_STANDARD = {
    'success', 'spec_id', 'total_operations',
    'successful_operations', 'failed_operations', 'dry_run',
    'output_file', 'source_file', 'operation_summary', 'error'
}
SPEC_MOD_DRY_RUN_ESSENTIAL = {'spec_id', 'dry_run', 'operation_count'}
SPEC_MOD_DRY_RUN_STANDARD = {
    'spec_id', 'dry_run', 'operation_count',
    'sample_operations', 'source_file'
}
SPEC_MOD_PARSE_REVIEW_ESSENTIAL = {
    'spec_id', 'suggestion_count', 'issues_total',
    'recommendation', 'display_mode'
}
SPEC_MOD_PARSE_REVIEW_STANDARD = {
    'spec_id', 'suggestion_count', 'issues_total',
    'recommendation', 'display_mode',
    'issues_by_severity', 'output_file', 'review_file'
}

# sdd-fidelity-review command
FIDELITY_REVIEW_ESSENTIAL = {
    'spec_id', 'mode', 'format', 'artifacts',
    'issue_counts', 'consensus', 'recommendation'
}
FIDELITY_REVIEW_STANDARD = {
    'spec_id', 'mode', 'format', 'artifacts',
    'issue_counts', 'models_consulted',
    'consensus', 'scope', 'prompt_included',
    'recommendation'
}

# add-assumption command
ADD_ASSUMPTION_ESSENTIAL = {'success', 'assumption_id'}
ADD_ASSUMPTION_STANDARD = {'success', 'assumption_id', 'spec_id', 'task_id', 'assumption_text', 'message'}

# list-assumptions command
LIST_ASSUMPTIONS_ESSENTIAL = {'assumptions'}
LIST_ASSUMPTIONS_STANDARD = {'assumptions', 'spec_id', 'count', 'filtered'}

# update-estimate command
UPDATE_ESTIMATE_ESSENTIAL = {'success', 'task_id'}
UPDATE_ESTIMATE_STANDARD = {'success', 'task_id', 'old_estimate', 'new_estimate', 'updated_at'}

# add-task command
ADD_TASK_ESSENTIAL = {'success', 'task_id'}
ADD_TASK_STANDARD = {'success', 'task_id', 'parent', 'title', 'type', 'spec_id'}

# remove-task command
REMOVE_TASK_ESSENTIAL = {'success', 'task_id'}
REMOVE_TASK_STANDARD = {'success', 'task_id', 'removed_count', 'spec_id'}

# time-report command
TIME_REPORT_ESSENTIAL = {'spec_id', 'total_hours'}
TIME_REPORT_STANDARD = {
    'spec_id', 'total_hours', 'estimated_hours', 'variance',
    'by_phase', 'by_task_type', 'completion_rate'
}

# status-report command
STATUS_REPORT_ESSENTIAL = {'spec_id', 'status', 'progress'}
STATUS_REPORT_STANDARD = {
    'spec_id', 'status', 'progress', 'current_phase',
    'blockers', 'recent_activity', 'next_tasks'
}

# audit-spec command
AUDIT_SPEC_ESSENTIAL = {'spec_id', 'issues'}
AUDIT_SPEC_STANDARD = {
    'spec_id', 'issues', 'warnings', 'suggestions',
    'integrity_checks', 'metadata_health'
}

# get-task command
GET_TASK_ESSENTIAL = {'task_id', 'title', 'status'}
GET_TASK_STANDARD = {
    'task_id', 'title', 'status', 'type', 'parent',
    'metadata', 'dependencies', 'children'
}

# get-journal command
GET_JOURNAL_ESSENTIAL = {'entries'}
GET_JOURNAL_STANDARD = {'entries', 'spec_id', 'count', 'date_range'}

# list-phases command
LIST_PHASES_ESSENTIAL = {'phases'}
LIST_PHASES_STANDARD = {'phases', 'spec_id', 'total_phases', 'current_phase'}

# check-complete command
CHECK_COMPLETE_ESSENTIAL = {'complete', 'node_id'}
CHECK_COMPLETE_STANDARD = {
    'complete', 'node_id', 'total_tasks', 'completed_tasks',
    'percentage', 'remaining_tasks'
}

# phase-time command
PHASE_TIME_ESSENTIAL = {'phase_id', 'total_hours'}
PHASE_TIME_STANDARD = {
    'phase_id', 'total_hours', 'estimated_hours', 'variance',
    'task_breakdown', 'completion_rate'
}

# reconcile-state command
RECONCILE_STATE_ESSENTIAL = {'success', 'changes_made'}
RECONCILE_STATE_STANDARD = {
    'success', 'changes_made', 'spec_id', 'issues_fixed',
    'warnings', 'backup_created'
}

# check-journaling command
CHECK_JOURNALING_ESSENTIAL = {'needs_journaling', 'task_count'}
CHECK_JOURNALING_STANDARD = {
    'needs_journaling', 'task_count', 'spec_id',
    'tasks', 'last_journal_entry'
}

# complete-task command
COMPLETE_TASK_ESSENTIAL = {'success', 'task_id'}
COMPLETE_TASK_STANDARD = {
    'success', 'task_id', 'completed_at', 'actual_hours',
    'spec_progress', 'parent_status'
}

# create-task-commit command
CREATE_TASK_COMMIT_ESSENTIAL = {'success', 'commit_hash'}
CREATE_TASK_COMMIT_STANDARD = {
    'success', 'commit_hash', 'task_id', 'files_committed',
    'commit_message', 'branch'
}

# ============================================================================
# doc_query commands - 18 field set pairs
# ============================================================================

# find-class command (doc_query)
FIND_CLASS_ESSENTIAL = {'name', 'entity_type', 'file', 'line'}
FIND_CLASS_STANDARD = {'name', 'entity_type', 'file', 'line'}

# find-function command (doc_query)
FIND_FUNCTION_ESSENTIAL = {'name', 'entity_type', 'file', 'line'}
FIND_FUNCTION_STANDARD = {'name', 'entity_type', 'file', 'line'}

# find-module command (doc_query)
FIND_MODULE_ESSENTIAL = {'name', 'entity_type', 'file', 'line'}
FIND_MODULE_STANDARD = {'name', 'entity_type', 'file', 'line'}

# complexity command (doc_query)
COMPLEXITY_ESSENTIAL = {'name', 'complexity', 'entity_type', 'file', 'line'}
COMPLEXITY_STANDARD = {'name', 'complexity', 'entity_type', 'file', 'line'}

# dependencies command (doc_query)
DEPENDENCIES_ESSENTIAL = {'name', 'imports', 'imported_by', 'entity_type', 'file'}
DEPENDENCIES_STANDARD = {'name', 'imports', 'imported_by', 'entity_type', 'file'}

# search command (doc_query)
SEARCH_ESSENTIAL = {'name', 'entity_type', 'file', 'line', 'relevance_score'}
SEARCH_STANDARD = {'name', 'entity_type', 'file', 'line', 'relevance_score'}

# context command (doc_query)
CONTEXT_DOC_QUERY_ESSENTIAL = {'name', 'entity_type', 'file', 'line'}
CONTEXT_DOC_QUERY_STANDARD = {'name', 'entity_type', 'file', 'line'}

# describe-module command (doc_query)
DESCRIBE_MODULE_ESSENTIAL = {
    'name', 'file', 'classes', 'functions',
    'imports', 'docstring', 'line_count', 'complexity'
}
DESCRIBE_MODULE_STANDARD = {
    'name', 'file', 'classes', 'functions', 'imports',
    'docstring', 'line_count', 'complexity'
}

# scope command (doc_query)
SCOPE_ESSENTIAL = {'preset', 'module', 'output'}
SCOPE_STANDARD = {'preset', 'module', 'function', 'output'}

# stats command (doc_query)
STATS_DOC_QUERY_ESSENTIAL = {
    'total_files', 'total_modules', 'total_classes', 'total_functions',
    'generated_at', 'metadata', 'statistics'
}
STATS_DOC_QUERY_STANDARD = {
    'total_files', 'total_modules', 'total_classes', 'total_functions',
    'total_lines', 'avg_complexity', 'max_complexity', 'high_complexity_count',
    'generated_at', 'metadata', 'statistics'
}

# list-classes command (doc_query)
LIST_CLASSES_ESSENTIAL = {'name', 'file', 'line', 'methods', 'bases'}
LIST_CLASSES_STANDARD = {'name', 'file', 'line', 'methods', 'bases'}

# list-functions command (doc_query)
LIST_FUNCTIONS_ESSENTIAL = {'name', 'file', 'line', 'complexity', 'params'}
LIST_FUNCTIONS_STANDARD = {'name', 'file', 'line', 'complexity', 'params'}

# list-modules command (doc_query)
LIST_MODULES_ESSENTIAL = {'name', 'file', 'classes', 'functions'}
LIST_MODULES_STANDARD = {'name', 'file', 'classes', 'functions'}

# callers command (doc_query)
CALLERS_ESSENTIAL = {'name', 'entity_type', 'file', 'line'}
CALLERS_STANDARD = {'name', 'entity_type', 'file', 'line'}

# callees command (doc_query)
CALLEES_ESSENTIAL = {'name', 'entity_type', 'file', 'line'}
CALLEES_STANDARD = {'name', 'entity_type', 'file', 'line'}

# call-graph command (doc_query)
CALL_GRAPH_ESSENTIAL = {'nodes', 'edges', 'entry_points', 'stats'}
CALL_GRAPH_STANDARD = {'nodes', 'edges', 'entry_points', 'stats'}

# trace-entry command (doc_query)
TRACE_ENTRY_ESSENTIAL = {'entry_point', 'call_depth', 'execution_paths', 'total_functions', 'leaf_functions'}
TRACE_ENTRY_STANDARD = {
    'entry_point', 'call_depth', 'execution_paths',
    'total_functions', 'leaf_functions'
}

# trace-data command (doc_query)
TRACE_DATA_ESSENTIAL = {
    'data_item', 'lifecycle_stages',
    'read_locations', 'write_locations', 'total_references'
}
TRACE_DATA_STANDARD = {
    'data_item', 'lifecycle_stages', 'read_locations',
    'write_locations', 'total_references'
}

# impact command (doc_query)
IMPACT_ESSENTIAL = {
    'target', 'direct_impact', 'indirect_impact',
    'affected_modules', 'affected_classes', 'affected_functions',
    'risk_level', 'total_affected'
}
IMPACT_STANDARD = {
    'target', 'direct_impact', 'indirect_impact',
    'affected_modules', 'affected_classes', 'affected_functions',
    'risk_level', 'total_affected'
}

# refactor-candidates command (doc_query) - combined with impact as task-1-18
REFACTOR_CANDIDATES_ESSENTIAL = {
    'candidates', 'total_candidates',
    'high_priority', 'medium_priority', 'low_priority'
}
REFACTOR_CANDIDATES_STANDARD = {
    'candidates', 'total_candidates', 'high_priority',
    'medium_priority', 'low_priority'
}

# ============================================================================
# sdd_update metadata commands - 15 field set pairs
# ============================================================================

# update-status command (sdd_update)
UPDATE_STATUS_ESSENTIAL = {'success', 'task_id', 'new_status'}
UPDATE_STATUS_STANDARD = {
    'success', 'task_id', 'new_status', 'old_status',
    'updated_at', 'spec_id', 'status_note'
}

# mark-blocked command (sdd_update)
MARK_BLOCKED_ESSENTIAL = {'success', 'task_id'}
MARK_BLOCKED_STANDARD = {
    'success', 'task_id', 'spec_id', 'blocked_by',
    'reason', 'marked_at'
}

# unblock-task command (sdd_update)
UNBLOCK_TASK_ESSENTIAL = {'success', 'task_id'}
UNBLOCK_TASK_STANDARD = {
    'success', 'task_id', 'spec_id', 'unblocked_at',
    'previously_blocked_by'
}

# add-journal command (sdd_update)
ADD_JOURNAL_ESSENTIAL = {'success', 'entry_id'}
ADD_JOURNAL_STANDARD = {
    'success', 'entry_id', 'spec_id', 'task_id',
    'timestamp', 'entry_text'
}

# add-revision command (sdd_update)
ADD_REVISION_ESSENTIAL = {'success', 'revision_id'}
ADD_REVISION_STANDARD = {
    'success', 'revision_id', 'spec_id', 'task_id',
    'timestamp', 'revision_text', 'revision_type'
}

# update-frontmatter command (sdd_update)
UPDATE_FRONTMATTER_ESSENTIAL = {'success', 'spec_id'}
UPDATE_FRONTMATTER_STANDARD = {
    'success', 'spec_id', 'updated_fields', 'updated_at'
}

# add-verification command (sdd_update)
ADD_VERIFICATION_ESSENTIAL = {'success', 'verification_id'}
ADD_VERIFICATION_STANDARD = {
    'success', 'verification_id', 'spec_id', 'task_id',
    'verification_type', 'created_at'
}

# execute-verify command (sdd_update)
EXECUTE_VERIFY_ESSENTIAL = {'success', 'task_id', 'result'}
EXECUTE_VERIFY_STANDARD = {
    'success', 'task_id', 'result', 'spec_id',
    'verification_type', 'executed_at', 'details'
}

# format-verification-summary command (sdd_update)
FORMAT_VERIFICATION_SUMMARY_ESSENTIAL = {'formatted'}
FORMAT_VERIFICATION_SUMMARY_STANDARD = {
    'formatted', 'spec_id', 'total_verifications',
    'passed', 'failed', 'summary_type'
}

# move-spec command (sdd_update)
MOVE_SPEC_ESSENTIAL = {'success', 'spec_id', 'new_location'}
MOVE_SPEC_STANDARD = {
    'success', 'spec_id', 'old_location', 'new_location',
    'moved_at', 'backup_created'
}

# activate-spec command (sdd_update)
ACTIVATE_SPEC_ESSENTIAL = {'success', 'spec_id'}
ACTIVATE_SPEC_STANDARD = {
    'success', 'spec_id', 'old_folder', 'new_folder',
    'activated_at'
}

# complete-spec command (sdd_update)
COMPLETE_SPEC_ESSENTIAL = {'success', 'spec_id'}
COMPLETE_SPEC_STANDARD = {
    'success', 'spec_id', 'completed_at', 'total_tasks',
    'completion_time', 'moved_to'
}

# bulk-journal command (sdd_update)
BULK_JOURNAL_ESSENTIAL = {'success', 'entries_added'}
BULK_JOURNAL_STANDARD = {
    'success', 'entries_added', 'spec_id', 'task_ids',
    'timestamp', 'entry_count'
}

# sync-metadata command (sdd_update)
SYNC_METADATA_ESSENTIAL = {'success', 'spec_id'}
SYNC_METADATA_STANDARD = {
    'success', 'spec_id', 'synced_fields', 'updated_at',
    'changes_made'
}

# update-task-metadata command (sdd_update)
UPDATE_TASK_METADATA_ESSENTIAL = {'success', 'task_id'}
UPDATE_TASK_METADATA_STANDARD = {
    'success', 'task_id', 'spec_id', 'updated_fields',
    'updated_at', 'metadata'
}

# code_doc generate command
DOC_GENERATE_ESSENTIAL = {'status', 'project', 'output_dir'}
DOC_GENERATE_STANDARD = {
    'status', 'project', 'output_dir', 'format'
}

# code_doc validate command
DOC_VALIDATE_ESSENTIAL = {'status', 'message'}
DOC_VALIDATE_STANDARD = {
    'status', 'message', 'schema'
}

# code_doc analyze command
DOC_ANALYZE_ESSENTIAL = {'status', 'project', 'statistics'}
DOC_ANALYZE_STANDARD = {
    'status', 'project', 'statistics'
}

# run_tests check-tools command
RUN_TESTS_CHECK_TOOLS_ESSENTIAL = {'available_count', 'available_tools'}
RUN_TESTS_CHECK_TOOLS_STANDARD = {
    'tools', 'available_count', 'available_tools'
}

# run_tests consult command (error responses)
RUN_TESTS_CONSULT_ESSENTIAL = {'status', 'message'}
RUN_TESTS_CONSULT_STANDARD = {
    'status', 'message'
}

# run_tests run command (error responses)
RUN_TESTS_RUN_ESSENTIAL = {'status', 'message'}
RUN_TESTS_RUN_STANDARD = {
    'status', 'message'
}
# sdd-plan-review command
PLAN_REVIEW_SUMMARY_ESSENTIAL = {
    'spec_id', 'review_type', 'blocker_count',
    'suggestion_count', 'models_responded', 'artifacts'
}
PLAN_REVIEW_SUMMARY_STANDARD = {
    'spec_id', 'review_type', 'artifacts',
    'blocker_count', 'suggestion_count', 'question_count',
    'models_responded', 'models_requested', 'models_consulted',
    'execution_time', 'consensus_level',
    'failures', 'dry_run'
}
