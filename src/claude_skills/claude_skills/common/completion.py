"""
Completion detection utilities for SDD JSON specs.
Provides functions to check if specs/phases are complete and ready for finalization.
"""

from typing import Dict, List, Optional


def check_spec_completion(spec_data: Dict, phase_id: Optional[str] = None) -> Dict:
    """
    Check if a spec (or specific phase) is complete.

    Analyzes the task hierarchy to determine if all tasks in the spec (or a
    specific phase) have been completed. Returns comprehensive metadata about
    completion status, progress, and any incomplete tasks.

    Args:
        spec_data: JSON spec file data containing hierarchy and task information
        phase_id: Optional phase ID to check specific phase completion.
                 If None, checks entire spec completion.

    Returns:
        Dictionary with completion status and metadata:
        {
            "is_complete": bool,           # True if all tasks completed
            "total_tasks": int,            # Total task count in scope
            "completed_tasks": int,        # Number of completed tasks
            "percentage": int,             # Completion percentage (0-100)
            "incomplete_tasks": List[str], # IDs of incomplete tasks
            "node_id": str,                # The node checked (spec-root or phase-id)
            "can_finalize": bool,          # True if ready to mark as complete
            "error": Optional[str]         # Error message if check failed
        }

    Example:
        >>> from claude_skills.common.spec import load_spec
        >>> from claude_skills.common.completion import check_spec_completion
        >>>
        >>> spec_data = load_spec("specs/active/my-spec.json")
        >>> result = check_spec_completion(spec_data)
        >>>
        >>> if result["is_complete"]:
        ...     print(f"Spec is complete! {result['completed_tasks']}/{result['total_tasks']} tasks done")
        ... else:
        ...     print(f"Incomplete tasks: {result['incomplete_tasks']}")
    """
    # Validate input
    if not spec_data:
        return {
            "is_complete": False,
            "total_tasks": 0,
            "completed_tasks": 0,
            "percentage": 0,
            "incomplete_tasks": [],
            "node_id": phase_id or "spec-root",
            "can_finalize": False,
            "error": "No spec data provided"
        }

    hierarchy = spec_data.get("hierarchy", {})

    if not hierarchy:
        return {
            "is_complete": False,
            "total_tasks": 0,
            "completed_tasks": 0,
            "percentage": 0,
            "incomplete_tasks": [],
            "node_id": phase_id or "spec-root",
            "can_finalize": False,
            "error": "No hierarchy found in spec data"
        }

    # Determine target node
    target_node_id = phase_id if phase_id else "spec-root"

    if target_node_id not in hierarchy:
        return {
            "is_complete": False,
            "total_tasks": 0,
            "completed_tasks": 0,
            "percentage": 0,
            "incomplete_tasks": [],
            "node_id": target_node_id,
            "can_finalize": False,
            "error": f"Node '{target_node_id}' not found in hierarchy"
        }

    # Get all tasks in the subtree
    all_task_ids = get_all_tasks_in_subtree(hierarchy, target_node_id)

    if not all_task_ids:
        # No tasks means technically complete (empty spec/phase)
        return {
            "is_complete": True,
            "total_tasks": 0,
            "completed_tasks": 0,
            "percentage": 100,
            "incomplete_tasks": [],
            "node_id": target_node_id,
            "can_finalize": True,
            "error": None
        }

    # Check each task's completion status
    completed_tasks = []
    incomplete_tasks = []

    for task_id in all_task_ids:
        task_node = hierarchy.get(task_id)
        if task_node and is_task_complete(task_node):
            completed_tasks.append(task_id)
        else:
            incomplete_tasks.append(task_id)

    total = len(all_task_ids)
    completed = len(completed_tasks)
    percentage = int((completed / total * 100)) if total > 0 else 0
    is_complete = completed == total

    return {
        "is_complete": is_complete,
        "total_tasks": total,
        "completed_tasks": completed,
        "percentage": percentage,
        "incomplete_tasks": incomplete_tasks,
        "node_id": target_node_id,
        "can_finalize": is_complete,
        "error": None
    }


def get_all_tasks_in_subtree(hierarchy: Dict, node_id: str) -> List[str]:
    """
    Recursively collect all task IDs under a node.

    Traverses the hierarchy tree starting from the given node and collects
    all descendant nodes that are of type "task". This includes tasks at
    any depth in the tree.

    Args:
        hierarchy: The hierarchy dictionary from spec data
        node_id: Starting node ID to search from

    Returns:
        List of task IDs found in the subtree (only nodes with type="task")
    """
    if node_id not in hierarchy:
        return []

    node = hierarchy[node_id]
    task_ids = []

    # If this node is a task, include it
    if node.get("type") == "task":
        task_ids.append(node_id)

    # Recursively check all children
    children = node.get("children", [])
    for child_id in children:
        task_ids.extend(get_all_tasks_in_subtree(hierarchy, child_id))

    return task_ids


def is_task_complete(task_node: Dict) -> bool:
    """
    Check if a single task is marked complete.

    A task is considered complete if its status is explicitly set to "completed".
    Tasks with status "in_progress", "pending", "blocked", or any other value
    are not considered complete.

    Args:
        task_node: Task node dictionary from hierarchy

    Returns:
        True if task status is "completed", False otherwise
    """
    if not task_node:
        return False

    return task_node.get("status") == "completed"


def should_prompt_completion(spec_data: Dict, phase_id: Optional[str] = None) -> Dict:
    """
    Determine if completion prompt should be shown to user.

    A completion prompt should only be shown if the spec/phase is fully
    complete AND there are no blocked tasks. Blocked tasks indicate
    unresolved dependencies or issues that prevent true completion.

    This function prevents premature completion by checking both:
    1. All tasks are completed (via check_spec_completion)
    2. No tasks are currently blocked (blocked = incomplete dependencies)

    Args:
        spec_data: JSON spec file data containing hierarchy and task information
        phase_id: Optional phase ID to check specific phase completion.
                 If None, checks entire spec.

    Returns:
        Dictionary with prompt decision and reasoning:
        {
            "should_prompt": bool,        # True if should show completion prompt
            "reason": str,                 # Explanation for the decision
            "is_complete": bool,           # Whether all tasks are complete
            "blocked_count": int,          # Number of blocked tasks
            "blocked_tasks": List[str],    # IDs of blocked tasks
            "node_id": str,                # Node that was checked
            "error": Optional[str]         # Error if check failed
        }

    Example:
        >>> from claude_skills.common.spec import load_spec
        >>> from claude_skills.common.completion import should_prompt_completion
        >>>
        >>> spec_data = load_spec("specs/active/my-spec.json")
        >>> result = should_prompt_completion(spec_data)
        >>>
        >>> if result["should_prompt"]:
        ...     print("Ready to mark spec as complete!")
        ...     print(result["reason"])
        ... else:
        ...     print(f"Not ready: {result['reason']}")
        ...     if result["blocked_tasks"]:
        ...         print(f"Blocked tasks: {result['blocked_tasks']}")
    """
    # First check if spec/phase is complete
    completion_result = check_spec_completion(spec_data, phase_id)

    # If there was an error checking completion, propagate it
    if completion_result.get("error"):
        return {
            "should_prompt": False,
            "reason": f"Cannot check completion: {completion_result['error']}",
            "is_complete": False,
            "blocked_count": 0,
            "blocked_tasks": [],
            "node_id": completion_result["node_id"],
            "error": completion_result["error"]
        }

    is_complete = completion_result["is_complete"]
    node_id = completion_result["node_id"]

    # If not complete, don't prompt
    if not is_complete:
        incomplete_count = len(completion_result["incomplete_tasks"])
        return {
            "should_prompt": False,
            "reason": f"Not all tasks are complete. {incomplete_count} task(s) remaining.",
            "is_complete": False,
            "blocked_count": 0,
            "blocked_tasks": [],
            "node_id": node_id,
            "error": None
        }

    # Check for blocked tasks
    hierarchy = spec_data.get("hierarchy", {})
    blocked_count, blocked_task_ids = count_blocked_tasks(hierarchy, node_id)

    # If blocked tasks exist, don't prompt
    if blocked_count > 0:
        return {
            "should_prompt": False,
            "reason": f"Cannot complete: {blocked_count} task(s) are blocked. Resolve blocked tasks before marking as complete.",
            "is_complete": True,
            "blocked_count": blocked_count,
            "blocked_tasks": blocked_task_ids,
            "node_id": node_id,
            "error": None
        }

    # All tasks complete and no blocked tasks - ready to prompt!
    return {
        "should_prompt": True,
        "reason": "All tasks completed and no blocked tasks. Ready to mark as complete.",
        "is_complete": True,
        "blocked_count": 0,
        "blocked_tasks": [],
        "node_id": node_id,
        "error": None
    }


def count_blocked_tasks(hierarchy: Dict, node_id: str) -> tuple:
    """
    Count blocked tasks under a node.

    Traverses the hierarchy tree starting from the given node and counts
    all descendant tasks that have status="blocked". This is used to
    prevent completion when there are unresolved blocking issues.

    Args:
        hierarchy: The hierarchy dictionary from spec data
        node_id: Starting node ID to search from

    Returns:
        Tuple of (count: int, blocked_task_ids: List[str])
        - count: Number of blocked tasks found
        - blocked_task_ids: List of task IDs with status="blocked"
    """
    if node_id not in hierarchy:
        return (0, [])

    node = hierarchy[node_id]
    blocked_tasks = []

    # If this node is a blocked task, include it
    if node.get("type") == "task" and node.get("status") == "blocked":
        blocked_tasks.append(node_id)

    # Recursively check all children
    children = node.get("children", [])
    for child_id in children:
        child_count, child_blocked = count_blocked_tasks(hierarchy, child_id)
        blocked_tasks.extend(child_blocked)

    return (len(blocked_tasks), blocked_tasks)


def format_completion_prompt(
    spec_data: Dict,
    phase_id: Optional[str] = None,
    show_hours_input: bool = True
) -> Dict:
    """
    Generate user-friendly completion prompt with optional hours input.

    Creates a formatted prompt message to present to users when a spec or
    phase is complete and ready to be marked as finalized. The prompt
    includes progress summary and optionally asks for actual hours spent
    if estimated hours were provided in the task metadata.

    This function is designed to be called by sdd-update, sdd-next, and
    status-report workflows when completion conditions are met (all tasks
    completed, no blocked tasks).

    Args:
        spec_data: JSON spec file data containing hierarchy and task information
        phase_id: Optional phase ID to format prompt for specific phase.
                 If None, formats prompt for entire spec.
        show_hours_input: Whether to include actual hours input prompt.
                         Default True. Set False to skip hours input.

    Returns:
        Dictionary with prompt information:
        {
            "prompt_text": str,           # Formatted completion message
            "requires_input": bool,        # True if hours input requested
            "completion_context": {        # Metadata about completion
                "node_id": str,            # Node that is complete
                "node_type": str,          # "spec" or "phase"
                "total_tasks": int,        # Total tasks in scope
                "completed_tasks": int,    # Number completed
                "estimated_hours": float,  # Estimated hours (if available)
                "has_hours_estimate": bool # Whether estimate exists
            },
            "error": Optional[str]         # Error message if prompt failed
        }

    Example:
        >>> from claude_skills.common.spec import load_spec
        >>> from claude_skills.common.completion import format_completion_prompt
        >>>
        >>> spec_data = load_spec("specs/active/my-spec.json")
        >>> result = format_completion_prompt(spec_data)
        >>>
        >>> if result["error"]:
        ...     print(f"Error: {result['error']}")
        ... else:
        ...     print(result["prompt_text"])
        ...     if result["requires_input"]:
        ...         actual_hours = input("Enter actual hours: ")

        Example prompt output (spec-level with hours):
        '''
        All tasks complete!

        Spec: User Authentication System
        Progress: 23/23 tasks (100%)
        Estimated: 15.5 hours

        How many actual hours did this take? (Enter a number or press Enter to skip)
        '''

        Example prompt output (phase-level without hours):
        '''
        Phase complete!

        Phase: Database Schema Setup
        Progress: 7/7 tasks (100%)

        Mark this phase as complete?
        '''
    """
    # Validate input
    if not spec_data:
        return {
            "prompt_text": "",
            "requires_input": False,
            "completion_context": {},
            "error": "No spec data provided"
        }

    # Get completion status
    completion_result = check_spec_completion(spec_data, phase_id)

    if completion_result.get("error"):
        return {
            "prompt_text": "",
            "requires_input": False,
            "completion_context": {},
            "error": f"Cannot generate prompt: {completion_result['error']}"
        }

    node_id = completion_result["node_id"]
    total_tasks = completion_result["total_tasks"]
    completed_tasks = completion_result["completed_tasks"]
    percentage = completion_result["percentage"]

    # Get node information
    hierarchy = spec_data.get("hierarchy", {})
    node = hierarchy.get(node_id, {})
    node_type = node.get("type", "spec")
    node_title = node.get("title", "Untitled")

    # Determine if this is spec or phase
    is_spec = node_type == "spec" or node_id == "spec-root"
    scope_label = "Spec" if is_spec else "Phase"

    # Check for estimated hours in metadata
    metadata = node.get("metadata", {})
    estimated_hours = metadata.get("estimated_hours", 0)
    has_hours_estimate = estimated_hours > 0

    # Build prompt message
    prompt_lines = []

    # Header
    if total_tasks == 0:
        prompt_lines.append(f"{scope_label} is ready to complete!")
    else:
        prompt_lines.append("All tasks complete!")

    prompt_lines.append("")  # Blank line

    # Scope and progress
    prompt_lines.append(f"{scope_label}: {node_title}")
    prompt_lines.append(f"Progress: {completed_tasks}/{total_tasks} tasks ({percentage}%)")

    # Estimated hours (if available)
    if has_hours_estimate:
        prompt_lines.append(f"Estimated: {estimated_hours} hours")

    # Hours input prompt (if enabled and estimate exists)
    requires_input = show_hours_input and has_hours_estimate

    if requires_input:
        prompt_lines.append("")  # Blank line
        prompt_lines.append("How many actual hours did this take? (Enter a number or press Enter to skip)")
    else:
        # Just confirmation
        prompt_lines.append("")  # Blank line
        prompt_lines.append(f"Mark this {scope_label.lower()} as complete?")

    prompt_text = "\n".join(prompt_lines)

    # Build completion context
    completion_context = {
        "node_id": node_id,
        "node_type": node_type,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "estimated_hours": estimated_hours if has_hours_estimate else None,
        "has_hours_estimate": has_hours_estimate
    }

    return {
        "prompt_text": prompt_text,
        "requires_input": requires_input,
        "completion_context": completion_context,
        "error": None
    }
