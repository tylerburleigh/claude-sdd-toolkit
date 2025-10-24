"""
SDD Update Operations

Modular operations for spec-driven development progress tracking.
"""

from .status import update_task_status, mark_task_blocked, unblock_task
from .journal import add_journal_entry, update_metadata
from .verification import add_verification_result
from .lifecycle import move_spec, complete_spec
from .time_tracking import track_time, generate_time_report
from .validation import validate_spec, get_status_report, audit_spec
from .query import (
    query_tasks,
    get_task,
    list_phases,
    check_complete,
    phase_time,
    list_blockers
)

__all__ = [
    # Status operations
    "update_task_status",
    "mark_task_blocked",
    "unblock_task",

    # Journal operations
    "add_journal_entry",
    "update_metadata",

    # Verification operations
    "add_verification_result",

    # Lifecycle operations
    "move_spec",
    "complete_spec",

    # Time tracking
    "track_time",
    "generate_time_report",

    # Validation
    "validate_spec",
    "get_status_report",
    "audit_spec",

    # Query operations
    "query_tasks",
    "get_task",
    "list_phases",
    "check_complete",
    "phase_time",
    "list_blockers",
]
