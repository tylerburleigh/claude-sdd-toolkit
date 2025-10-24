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
from .progress import recalculate_progress, update_parent_status, get_progress_summary, list_phases
from .paths import (
    find_specs_directory,
    validate_path,
    validate_and_normalize_paths,
    normalize_path,
    batch_check_paths_exist,
    find_files_by_pattern,
    ensure_directory
)
from .printer import PrettyPrinter
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
    should_generate_docs,
    ensure_documentation_exists,
)

# Cross-skill integrations
from .integrations import (
    validate_spec_before_proceed,
    execute_verify_task,
    get_session_state,
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

    # Progress calculation
    "recalculate_progress",
    "update_parent_status",
    "get_progress_summary",
    "list_phases",

    # Path utilities
    "find_specs_directory",
    "validate_path",
    "validate_and_normalize_paths",
    "normalize_path",
    "batch_check_paths_exist",
    "find_files_by_pattern",
    "ensure_directory",

    # Output formatting
    "PrettyPrinter",

    # Validation utilities
    "EnhancedError",
    "SpecValidationResult",
    "JsonSpecValidationResult",
    "validate_status",
    "validate_node_type",
    "validate_spec_id_format",
    "validate_iso8601_date",
    "normalize_message_text",

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
    "should_generate_docs",
    "ensure_documentation_exists",

    # Cross-skill integrations
    "validate_spec_before_proceed",
    "execute_verify_task",
    "get_session_state",
]
