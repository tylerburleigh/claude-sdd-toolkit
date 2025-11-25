"""
Spec-Driven Development Common Utilities

Shared functionality for all SDD skills (sdd-plan, sdd-next, sdd-update).
Provides JSON spec file operations, spec parsing, progress calculation, and path discovery.
"""

from .spec import (
    load_json_spec,
    save_json_spec,
    backup_json_spec,
    get_node,
    update_node,
    extract_frontmatter,
)

# Spec modification operations (CRUD for spec hierarchy)
from claude_skills.sdd_spec_mod.modification import (
    add_node,
    remove_node,
    update_node_field,
    move_node,
    spec_transaction,
    transactional_modify,
    update_task_counts,
)
from .progress import recalculate_progress, update_parent_status, get_progress_summary, list_phases
from .completion import check_spec_completion, should_prompt_completion, format_completion_prompt
from .paths import (
    find_specs_directory,
    find_spec_file,
    resolve_spec_file,
    validate_path,
    validate_and_normalize_paths,
    normalize_path,
    batch_check_paths_exist,
    find_files_by_pattern,
    ensure_directory,
    ensure_reports_directory,
    generate_reports_readme_content,
    ensure_reviews_directory,
    generate_reviews_readme_content,
    ensure_backups_directory,
    generate_backups_readme_content,
    ensure_human_readable_directory,
    generate_human_readable_readme_content
)
from .printer import PrettyPrinter
from .ui_protocol import Ui, Message, MessageLevel
from .rich_ui import RichUi
from .plain_ui import PlainUi
from .ui_factory import (
    create_ui,
    create_ui_from_args,
    is_tty_available,
    is_ci_environment,
    should_use_plain_ui,
    get_backend_name,
    format_backend_info,
    ui,
)
from .validation import (
    EnhancedError,
    SpecValidationResult,
    JsonSpecValidationResult,
    validate_status,
    validate_node_type,
    validate_spec_id_format,
    validate_iso8601_date,
    normalize_message_text,
)
from .schema_loader import load_json_schema
# Validation modules (comprehensive spec and state validation)
from .hierarchy_validation import (
    validate_spec_hierarchy,
    validate_structure,
    validate_hierarchy,
    validate_nodes,
    validate_task_counts,
    validate_dependencies,
    validate_metadata
)
# Backward compatibility alias

from .reporting import (
    generate_spec_report,
    generate_json_spec_report,
    generate_combined_report
)

# Dependency analysis
from .dependency_analysis import (
    analyze_dependencies,
    DEFAULT_BOTTLENECK_THRESHOLD,
    has_dependency_cycle,
    validate_dependency_graph,
    get_dependency_chain,
    find_blocking_tasks,
    find_circular_dependencies,
)

# Query operations (read-only)
from .query_operations import (
    query_tasks,
    get_task,
    list_phases as list_phases_query,
    check_complete,
    list_blockers
)

# Metrics collection
from .metrics import (
    track_metrics,
    capture_metrics,
    record_metric,
    get_metrics_file_path,
    is_metrics_enabled
)

# Documentation helpers
from .doc_helper import (
    check_doc_query_available,
    check_sdd_integration_available,
    get_task_context_from_docs,
    get_call_context_from_docs,
    get_test_context_from_docs,
    get_complexity_hotspots_from_docs,
    should_generate_docs,
    ensure_documentation_exists,
)

# Cross-skill integrations
from .integrations import (
    validate_spec_before_proceed,
    execute_verify_task,
    get_session_state,
)

# AI configuration
from .ai_config import (
    load_skill_config,
    get_enabled_tools,
    get_agent_priority,
    get_agent_command,
    get_timeout,
    get_tool_config,
    is_tool_enabled,
    resolve_tool_model,
    resolve_models_for_tools,
)

# Contract extraction
from .contracts import (
    extract_prepare_task_contract,
    extract_task_info_contract,
    extract_check_deps_contract,
    extract_progress_contract,
    extract_next_task_contract,
)

# JSON output formatting
from .json_output import (
    output_json,
    format_json_output,
    format_compact_output,
    print_json_output,
    CommandType,
)

# CLI utilities (ANSI stripping, JSON helpers, argparse decorators)
from .cli_utils import (
    strip_ansi_codes,
    format_json_output as format_json_with_ansi_stripping,
    add_format_flag,
)

# SDD configuration
from .sdd_config import (
    load_sdd_config,
    DEFAULT_SDD_CONFIG,
    get_sdd_setting,
)

__version__ = "1.0.0"

__all__ = [
    # JSON spec operations
    "load_json_spec",
    "save_json_spec",
    "backup_json_spec",
    "get_node",
    "update_node",
    "extract_frontmatter",

    # Spec modification operations
    "add_node",
    "remove_node",
    "update_node_field",
    "move_node",
    "spec_transaction",
    "transactional_modify",
    "update_task_counts",

    # Progress calculation
    "recalculate_progress",
    "update_parent_status",
    "get_progress_summary",
    "list_phases",

    # Completion detection
    "check_spec_completion",
    "should_prompt_completion",
    "format_completion_prompt",

    # Path utilities
    "find_specs_directory",
    "find_spec_file",
    "validate_path",
    "validate_and_normalize_paths",
    "normalize_path",
    "batch_check_paths_exist",
    "find_files_by_pattern",
    "ensure_directory",
    "ensure_reports_directory",
    "generate_reports_readme_content",
    "ensure_reviews_directory",
    "generate_reviews_readme_content",
    "ensure_backups_directory",
    "generate_backups_readme_content",
    "ensure_human_readable_directory",
    "generate_human_readable_readme_content",

    # Output formatting
    "PrettyPrinter",
    "Ui",
    "Message",
    "MessageLevel",
    "RichUi",
    "PlainUi",
    "create_ui",
    "create_ui_from_args",
    "is_tty_available",
    "is_ci_environment",
    "should_use_plain_ui",
    "get_backend_name",
    "format_backend_info",
    "ui",

    # Validation utilities
    "EnhancedError",
    "SpecValidationResult",
    "JsonSpecValidationResult",
    "validate_status",
    "validate_node_type",
    "validate_spec_id_format",
    "validate_iso8601_date",
    "normalize_message_text",
    "load_json_schema",

    # Hierarchy validation
    "validate_spec_hierarchy",
    "validate_structure",
    "validate_hierarchy",
    "validate_nodes",
    "validate_task_counts",
    "validate_dependencies",
    "validate_metadata",

    # Reporting
    "generate_spec_report",
    "generate_json_spec_report",
    "generate_combined_report",

    # Dependency analysis
    "analyze_dependencies",
    "DEFAULT_BOTTLENECK_THRESHOLD",
    "has_dependency_cycle",
    "validate_dependency_graph",
    "get_dependency_chain",
    "find_blocking_tasks",
    "find_circular_dependencies",

    # Query operations
    "query_tasks",
    "get_task",
    "list_phases_query",
    "check_complete",
    "list_blockers",

    # Metrics collection
    "track_metrics",
    "capture_metrics",
    "record_metric",
    "get_metrics_file_path",
    "is_metrics_enabled",

    # Documentation helpers
    "check_doc_query_available",
    "check_sdd_integration_available",
    "get_task_context_from_docs",
    "get_call_context_from_docs",
    "get_test_context_from_docs",
    "get_complexity_hotspots_from_docs",
    "should_generate_docs",
    "ensure_documentation_exists",

    # Cross-skill integrations
    "validate_spec_before_proceed",
    "execute_verify_task",
    "get_session_state",

    # AI configuration
    "load_skill_config",
    "get_enabled_tools",
    "get_agent_priority",
    "get_agent_command",
    "get_timeout",
    "get_tool_config",
    "is_tool_enabled",
    "resolve_tool_model",
    "resolve_models_for_tools",

    # Contract extraction
    "extract_prepare_task_contract",
    "extract_task_info_contract",
    "extract_check_deps_contract",
    "extract_progress_contract",
    "extract_next_task_contract",

    # JSON output formatting
    "output_json",
    "format_json_output",
    "format_compact_output",
    "print_json_output",
    "CommandType",

    # CLI utilities
    "strip_ansi_codes",
    "format_json_with_ansi_stripping",
    "add_format_flag",

    # SDD configuration
    "load_sdd_config",
    "DEFAULT_SDD_CONFIG",
    "get_sdd_setting",
]
