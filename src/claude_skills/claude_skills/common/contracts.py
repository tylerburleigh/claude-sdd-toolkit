"""
Contract extraction functions for SDD CLI commands.

This module provides functions to extract minimal, functional contracts from
full CLI command outputs. These contracts preserve all decision-enabling
information while significantly reducing token usage (typically 60-88% savings).

The contracts follow the principle of "smart defaults":
- Omit null/empty values
- Omit fields with default values
- Include only fields needed for agent decision-making
- Conditionally include optional fields when they have meaningful values

For detailed contract specifications, see /tmp/functional-contracts-analysis.md
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


def extract_prepare_task_contract(prepare_task_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract minimal contract from `sdd prepare-task` output.

    Purpose:
        Enable the agent to:
        1. Identify the next task to work on
        2. Determine if the task can be started
        3. Understand what work needs to be done
        4. Prepare the git environment appropriately
        5. Detect if the spec is complete

    Field Inclusion Rules:

        ALWAYS INCLUDE (Essential):
        - task_id: Task identifier for referencing in subsequent commands
        - title: Concise description of what to do
        - can_start: Boolean indicating if task can be started now
        - blocked_by: List of blocking task IDs (if can't start)
        - git.needs_branch: Whether a new branch should be created
        - git.suggested_branch: Branch name to use
        - git.dirty: Whether working tree has uncommitted changes
        - spec_complete: Whether the spec is finished

        CONDITIONALLY INCLUDE (Optional):
        - file_path: Target file path (only if specified in task metadata)
        - details: Implementation details (only if specified in task metadata)
        - status: Task status (only if not "pending")
        - validation_warnings: Spec validation warnings (only if non-empty)
        - completion_info: Completion details (only if spec_complete is True)

        OMIT (Redundant/Not Needed):
        - success, error: Exit code indicates success/failure
        - task_data: Fields duplicated at top level
        - task_details, spec_file, doc_context: Always null
        - dependencies object: Flattened to top-level fields
        - repo_root: Agent knows from environment
        - needs_branch_creation: Duplicate of git.needs_branch
        - dirty_tree_status: Verbose, git.dirty is sufficient
        - UI-only fields: needs_commit_cadence, commit_cadence_options, etc.

    Args:
        prepare_task_output: Full output from sdd prepare-task command

    Returns:
        Minimal contract dict with essential and conditionally-included fields

    Example:
        >>> full_output = {
        ...     "success": True,
        ...     "task_id": "task-1-1-1",
        ...     "task_data": {
        ...         "title": "Implement extract_prepare_task_contract()",
        ...         "metadata": {"details": "Extract fields: ..."}
        ...     },
        ...     "dependencies": {"can_start": True, "blocked_by": []},
        ...     "needs_branch_creation": True,
        ...     "suggested_branch_name": "feat/compact-json",
        ...     "dirty_tree_status": {"is_dirty": False},
        ...     "spec_complete": False,
        ...     # ... many other fields
        ... }
        >>> contract = extract_prepare_task_contract(full_output)
        >>> contract
        {
            "task_id": "task-1-1-1",
            "title": "Implement extract_prepare_task_contract()",
            "can_start": True,
            "blocked_by": [],
            "git": {
                "needs_branch": True,
                "suggested_branch": "feat/compact-json",
                "dirty": False
            },
            "spec_complete": False,
            "details": "Extract fields: ..."
        }
    """
    contract = {}

    # Essential fields - Always include
    contract["task_id"] = prepare_task_output.get("task_id")

    # Get title from task_data
    task_data = prepare_task_output.get("task_data", {})
    contract["title"] = task_data.get("title", "")

    # Get dependency info
    dependencies = prepare_task_output.get("dependencies", {})
    contract["can_start"] = dependencies.get("can_start", False)
    contract["blocked_by"] = dependencies.get("blocked_by", [])

    # Build git object
    git_info = {}
    git_info["needs_branch"] = prepare_task_output.get("needs_branch_creation", False)
    git_info["suggested_branch"] = prepare_task_output.get("suggested_branch_name", "")

    # Get dirty status from dirty_tree_status object
    dirty_tree = prepare_task_output.get("dirty_tree_status", {})
    git_info["dirty"] = dirty_tree.get("is_dirty", False) if dirty_tree else False

    contract["git"] = git_info

    # Spec completion status
    contract["spec_complete"] = prepare_task_output.get("spec_complete", False)

    # Conditional fields - Include only if present and non-empty

    # file_path from task_data.metadata
    metadata = task_data.get("metadata", {})
    file_path = metadata.get("file_path")
    if file_path:
        contract["file_path"] = file_path

    # details from task_data.metadata
    details = metadata.get("details")
    if details:
        contract["details"] = details

    # status - only if not "pending" (default for next task)
    status = task_data.get("status")
    if status and status != "pending":
        contract["status"] = status

    # validation_warnings - only if non-empty
    validation_warnings = prepare_task_output.get("validation_warnings", [])
    if validation_warnings:
        contract["validation_warnings"] = validation_warnings

    # completion_info - only if spec is complete
    if contract["spec_complete"]:
        completion_info = prepare_task_output.get("completion_info")
        if completion_info:
            # Extract minimal completion info
            contract["completion_info"] = {
                "is_complete": completion_info.get("should_prompt", False),
                "reason": completion_info.get("reason", "")
            }

    return contract
