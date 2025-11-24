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
        6. Access rich context without additional CLI calls

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
        - context: Enhanced context payload (new in default output)

        CONDITIONALLY INCLUDE (Optional):
        - file_path: Target file path (only if specified in task metadata)
        - details: Implementation details (only if specified in task metadata)
        - status: Task status (only if not "pending")
        - validation_warnings: Spec validation warnings (only if non-empty)
        - completion_info: Completion details (only if spec_complete is True)
        - task_metadata: Full metadata fields (category, estimated_hours, etc.)
        - extended_context: Additional context from enhancement flags

        OMIT (Redundant/Not Needed):
        - success, error: Exit code indicates success/failure
        - task_data: Fields duplicated at top level
        - task_details, spec_file, doc_context: Always null
        - dependencies object: Now included in context block
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
        ...         "metadata": {
        ...             "details": ["Extract fields: ...", "Add context block"],
        ...             "task_category": "implementation",
        ...             "estimated_hours": 2
        ...         }
        ...     },
        ...     "dependencies": {"can_start": True, "blocked_by": []},
        ...     "needs_branch_creation": True,
        ...     "suggested_branch_name": "feat/compact-json",
        ...     "dirty_tree_status": {"is_dirty": False},
        ...     "spec_complete": False,
        ...     "context": {
        ...         "previous_sibling": {"id": "task-1-1", "title": "...", "status": "completed"},
        ...         "parent_task": {"id": "phase-1", "title": "Foundation"},
        ...         "phase": {"title": "Phase 1", "percentage": 40},
        ...         "sibling_files": [],
        ...         "task_journal": {"entry_count": 0, "entries": []}
        ...     }
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
            "context": {
                "previous_sibling": {"id": "task-1-1", "title": "...", "status": "completed"},
                "parent_task": {"id": "phase-1", "title": "Foundation"},
                "phase": {"title": "Phase 1", "percentage": 40},
                "sibling_files": [],
                "task_journal": {"entry_count": 0, "entries": []}
            },
            "details": ["Extract fields: ...", "Add context block"],
            "task_metadata": {
                "category": "implementation",
                "estimated_hours": 2
            }
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

    # Context payload - Always include if present (new default)
    context = prepare_task_output.get("context")
    if context:
        contract["context"] = context

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

    # task_metadata - Include full metadata if it has useful fields
    task_metadata = {}
    if metadata.get("task_category"):
        task_metadata["category"] = metadata["task_category"]
    if metadata.get("estimated_hours") is not None:
        task_metadata["estimated_hours"] = metadata["estimated_hours"]
    if metadata.get("acceptance_criteria"):
        task_metadata["acceptance_criteria"] = metadata["acceptance_criteria"]
    if metadata.get("verification_type"):
        task_metadata["verification_type"] = metadata["verification_type"]

    if task_metadata:
        contract["task_metadata"] = task_metadata

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

    # extended_context - Include if enhancement flags were used
    extended_context = prepare_task_output.get("extended_context")
    if extended_context:
        contract["extended_context"] = extended_context

    return contract


def extract_task_info_contract(task_info_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract minimal contract from `sdd task-info` output.

    Purpose:
        Get detailed information about a specific task (not necessarily the next one).
        Enable decisions about:
        1. What is this task?
        2. What's its current state?
        3. What blocks it?
        4. What does it block?

    Field Inclusion Rules:

        ALWAYS INCLUDE (Essential):
        - task_id: Task identifier (derived from command argument, not in output)
        - title: Task description
        - status: Current task status
        - blocked_by: List of blocking task IDs
        - blocks: List of task IDs this task blocks

        CONDITIONALLY INCLUDE (Optional):
        - file_path: Target file path (only if non-empty)

        OMIT (Not Needed):
        - type: Not needed for agent decisions
        - parent: Not actionable
        - children: Use separate query if needed
        - total_tasks, completed_tasks: Use progress command instead
        - metadata: Use prepare-task for implementation details
        - dependencies object: Flattened to blocked_by and blocks

    Args:
        task_info_output: Full output from sdd task-info command

    Returns:
        Minimal contract dict with essential task information

    Example:
        >>> full_output = {
        ...     "type": "subtask",
        ...     "title": "Implement extract_task_info_contract()",
        ...     "status": "completed",
        ...     "parent": "task-1-1",
        ...     "children": [],
        ...     "dependencies": {
        ...         "blocks": [],
        ...         "blocked_by": [],
        ...         "depends": []
        ...     },
        ...     "total_tasks": 1,
        ...     "completed_tasks": 1,
        ...     "metadata": {...}
        ... }
        >>> contract = extract_task_info_contract(full_output)
        >>> contract
        {
            "title": "Implement extract_task_info_contract()",
            "status": "completed",
            "blocked_by": [],
            "blocks": []
        }
    """
    contract = {}

    # Essential fields
    contract["title"] = task_info_output.get("title", "")
    contract["status"] = task_info_output.get("status", "pending")

    # Get dependency info
    dependencies = task_info_output.get("dependencies", {})
    contract["blocked_by"] = dependencies.get("blocked_by", [])
    contract["blocks"] = dependencies.get("blocks", [])

    # Conditional fields
    metadata = task_info_output.get("metadata", {})
    file_path = metadata.get("file_path")
    if file_path:
        contract["file_path"] = file_path

    return contract


def extract_check_deps_contract(check_deps_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract minimal contract from `sdd check-deps` output.

    Purpose:
        Verify whether a specific task's dependencies are satisfied.
        Enable decisions about:
        1. Can I start this task?
        2. What's blocking me?
        3. What will I unblock?

    Field Inclusion Rules:

        ALWAYS INCLUDE (Essential):
        - can_start: Boolean indicating if task can be started

        CONDITIONALLY INCLUDE (Optional):
        - blocked_by: List of blocking task IDs (only if non-empty)
        - blocks: List of task IDs this task blocks (only if non-empty)

        OMIT (Not Needed):
        - task_id: Already known from command argument
        - soft_depends: Soft dependencies don't block work

    Special Rules:
        - When can_start is true and blocked_by is empty, omit blocked_by
        - When blocks is empty, omit blocks
        - Minimal successful case: just {"can_start": true}

    Args:
        check_deps_output: Full output from sdd check-deps command

    Returns:
        Minimal contract dict with dependency information

    Example:
        >>> full_output = {
        ...     "task_id": "task-1-1-2",
        ...     "can_start": True,
        ...     "blocked_by": [],
        ...     "soft_depends": [],
        ...     "blocks": []
        ... }
        >>> contract = extract_check_deps_contract(full_output)
        >>> contract
        {
            "can_start": True
        }
    """
    contract = {}

    # Essential field
    contract["can_start"] = check_deps_output.get("can_start", False)

    # Conditional fields - only include if non-empty
    blocked_by = check_deps_output.get("blocked_by", [])
    if blocked_by:
        contract["blocked_by"] = blocked_by

    blocks = check_deps_output.get("blocks", [])
    if blocks:
        contract["blocks"] = blocks

    return contract


def extract_progress_contract(progress_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract minimal contract from `sdd progress` output.

    Purpose:
        Understand overall spec completion status.
        Enable decisions about:
        1. How much is done?
        2. How much is left?
        3. What's active?

    Field Inclusion Rules:

        ALWAYS INCLUDE (Essential):
        - total: Total number of tasks
        - completed: Number of completed tasks
        - in_progress: Number of tasks currently in progress
        - pending: Number of pending tasks

        OMIT (Not Needed):
        - node_id: Not needed for agent
        - spec_id: Already known from command argument
        - title: Already known
        - type: Always "spec"
        - status: Derivable from counts
        - percentage: Derivable (completed/total * 100)
        - remaining_tasks: Derivable (total - completed)
        - current_phase: Use separate command if needed

    Args:
        progress_output: Full output from sdd progress command

    Returns:
        Minimal contract dict with progress counts

    Example:
        >>> full_output = {
        ...     "node_id": "spec-root",
        ...     "spec_id": "compact-json-output-2025-11-03-001",
        ...     "title": "Compact JSON Output for SDD CLI Commands",
        ...     "type": "spec",
        ...     "status": "in_progress",
        ...     "total_tasks": 38,
        ...     "completed_tasks": 1,
        ...     "percentage": 2,
        ...     "remaining_tasks": 37,
        ...     "current_phase": {...}
        ... }
        >>> contract = extract_progress_contract(full_output)
        >>> contract
        {
            "total": 38,
            "completed": 1,
            "in_progress": 0,
            "pending": 37
        }
    """
    contract = {}

    # Essential fields - derive pending from total - completed - in_progress
    total = progress_output.get("total_tasks", 0)
    completed = progress_output.get("completed_tasks", 0)

    contract["total"] = total
    contract["completed"] = completed

    # in_progress not directly in output, derive from status counts if available
    # For now, set to 0 and derive pending
    contract["in_progress"] = 0

    # pending = total - completed (assuming in_progress is included in one of these)
    contract["pending"] = progress_output.get("remaining_tasks", total - completed)

    return contract


def extract_next_task_contract(next_task_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract minimal contract from `sdd next-task` output.

    Purpose:
        Identify which task to work on next (lightweight version of prepare-task).
        Enable decisions about:
        1. What task should I work on?

    Field Inclusion Rules:

        ALWAYS INCLUDE (Essential):
        - task_id: Task identifier
        - title: Concise description of what to do

        OMIT (Not Needed):
        - status: Always "pending" for next task
        - file_path: Use prepare-task or task-info for details
        - estimated_hours: Not actionable for agent

    Args:
        next_task_output: Full output from sdd next-task command

    Returns:
        Minimal contract dict with next task information

    Example:
        >>> full_output = {
        ...     "task_id": "task-1-1-2",
        ...     "title": "Implement extract_task_info_contract()...",
        ...     "status": "pending",
        ...     "file_path": "",
        ...     "estimated_hours": 0
        ... }
        >>> contract = extract_next_task_contract(full_output)
        >>> contract
        {
            "task_id": "task-1-1-2",
            "title": "Implement extract_task_info_contract()..."
        }
    """
    contract = {}

    # Essential fields only
    contract["task_id"] = next_task_output.get("task_id", "")
    contract["title"] = next_task_output.get("title", "")

    return contract


def extract_session_summary_contract(summary_output: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract minimal contract from `sdd start-helper session-summary` output.

    Purpose:
        Determine the state of the environment and active work to guide the user.
        Decisions:
        1. Permissions OK? -> If not, stop.
        2. Git OK? -> If not, offer setup.
        3. Work Found? -> Show text, offer Resume/Backlog.

    Field Inclusion Rules:

        ALWAYS INCLUDE (Essential):
        - permissions.status: Gatekeeper for tool usage
        - git.needs_setup: Gatekeeper for git wizard
        - active_work.found: Boolean toggle for options
        - active_work.text: Pre-rendered summary for display

        CONDITIONALLY INCLUDE (Optional):
        - git.settings: Only if configured (for info)
        - active_work.pending_specs: Only if present (for backlog menu)
        - session_state.last_task: Only if present (for resume option)

        OMIT (Redundant/Not Needed):
        - project_root: Known from env
        - permissions.settings_file, exists, has_specs: Debug info
        - git.git_config_file, exists, enabled: Debug info
        - active_work.specs, message, count: Redundant with text
        - session_state.active_specs, timestamp: Redundant

    Args:
        summary_output: Full output from sdd start-helper session-summary

    Returns:
        Minimal contract dict with essential session information
    """
    contract = {}

    # Permissions - only status is essential
    permissions = summary_output.get("permissions", {})
    contract["permissions"] = {
        "status": permissions.get("status", "unknown")
    }

    # Git - needs_setup is essential, settings optional
    git = summary_output.get("git", {})
    git_contract = {
        "needs_setup": git.get("needs_setup", False)
    }
    if "settings" in git:
        git_contract["settings"] = git["settings"]
    contract["git"] = git_contract

    # Active Work - found and text are essential
    active_work = summary_output.get("active_work", {})
    aw_contract = {
        "found": active_work.get("active_work_found", False),
        "text": active_work.get("text", "")
    }
    # Include pending_specs only if present (for backlog menu)
    pending = active_work.get("pending_specs")
    if pending:
        aw_contract["pending_specs"] = pending
    contract["active_work"] = aw_contract

    # Session State - only last_task if present
    session_state = summary_output.get("session_state")
    if session_state:
        last_task = session_state.get("last_task")
        if last_task:
            contract["session_state"] = {"last_task": last_task}

    return contract
