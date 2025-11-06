"""
SDD Spec Modification Module.

Provides utilities for modifying SDD JSON specification files,
including adding/removing nodes, updating task hierarchies, and
maintaining spec integrity.
"""

from .modification import (
    add_node,
    remove_node,
    move_node,
    update_node_field,
    update_task_counts,
    spec_transaction,
    transactional_modify,
    apply_modifications,
)

from .revision import (
    create_revision,
    get_revision_history,
    rollback_to_version,
)

from .review_parser import (
    parse_review_report,
    suggest_modifications,
)

__all__ = [
    "add_node",
    "apply_modifications",
    "create_revision",
    "get_revision_history",
    "move_node",
    "parse_review_report",
    "remove_node",
    "rollback_to_version",
    "spec_transaction",
    "suggest_modifications",
    "transactional_modify",
    "update_node_field",
    "update_task_counts",
]
