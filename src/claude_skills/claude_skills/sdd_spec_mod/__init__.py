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
)

__all__ = [
    "add_node",
    "remove_node",
    "move_node",
    "update_node_field",
    "update_task_counts",
    "spec_transaction",
    "transactional_modify",
]
