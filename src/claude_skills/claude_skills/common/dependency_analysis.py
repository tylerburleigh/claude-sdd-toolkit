"""Dependency analysis and validation for SDD JSON specs."""

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple


@dataclass
class DependencyAnalysis:
    """Structured dependency diagnostics used by sdd-validate."""

    cycles: List[List[str]]
    orphaned: List[Dict[str, str]]
    deadlocks: List[Dict[str, Iterable[str]]]
    bottlenecks: List[Dict[str, object]]
    status: str


DEFAULT_BOTTLENECK_THRESHOLD = 3


def analyze_dependencies(
    spec_data: Dict,
    *,
    bottleneck_threshold: Optional[int] = None,
) -> DependencyAnalysis:
    """
    Detect circular dependencies in JSON spec.

    Performs comprehensive analysis of the dependency graph including:
    - Circular dependency chains
    - Orphaned tasks (references to non-existent dependencies)
    - Impossible chains (mutual blocking scenarios)

    Args:
        spec_data: JSON spec file data dictionary with 'hierarchy' key

    Returns:
        Dictionary with analysis results:
        - has_circular: bool - True if any circular dependencies found
        - circular_chains: list - List of circular dependency chains
        - orphaned_tasks: list - Tasks with missing dependencies
        - impossible_chains: list - Tasks in deadlock situations

    Example:
        >>> result = find_circular_dependencies(spec_data)
        >>> if result['has_circular']:
        ...     print(f"Found {len(result['circular_chains'])} circular chains")
    """
    hierarchy = spec_data.get("hierarchy", {}) or {}
    threshold = bottleneck_threshold or DEFAULT_BOTTLENECK_THRESHOLD
    cycles: List[List[str]] = []
    orphaned: List[Dict[str, str]] = []
    deadlocks: List[Dict[str, Iterable[str]]] = []
    bottlenecks: List[Dict[str, object]] = []

    # Build dependency graph (only for tasks)
    graph: Dict[str, List[str]] = {}
    for task_id, task_data in hierarchy.items():
        if task_data.get("type") == "task":
            deps = task_data.get("dependencies", {}) or {}
            # Handle both dict format and malformed list format
            if isinstance(deps, dict):
                graph[task_id] = [dep for dep in deps.get("blocked_by", []) if dep in hierarchy]
            else:
                # Malformed: dependencies is a list or other type, skip
                graph[task_id] = []

    # Detect circular dependencies using DFS
    def has_cycle(node: str, visited: Set[str], rec_stack: Set[str], path: List[str]) -> bool:
        """
        DFS-based cycle detection.

        Args:
            node: Current node to explore
            visited: Set of all visited nodes
            rec_stack: Set of nodes in current recursion stack
            path: Current path being explored

        Returns:
            True if cycle detected, False otherwise
        """
        visited.add(node)
        rec_stack.add(node)
        current_path = path + [node]

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor, visited, rec_stack, current_path):
                    return True
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = current_path.index(neighbor)
                cycle = current_path[cycle_start:] + [neighbor]
                cycles.append(cycle)

        rec_stack.remove(node)
        return False

    # Check all nodes for cycles
    visited = set()
    for node in graph:
        if node not in visited:
            has_cycle(node, visited, set(), [])

    # Find orphaned tasks (tasks with dependencies that don't exist)
    # Check original task dependencies from hierarchy, not the filtered graph
    for task_id, task_data in hierarchy.items():
        if task_data.get("type") == "task":
            deps = task_data.get("dependencies", {}) or {}
            if isinstance(deps, dict):
                blocked_by = deps.get("blocked_by", []) or []
                for dep in blocked_by:
                    if dep not in hierarchy:
                        orphaned.append({"task": task_id, "missing_dependency": dep})

    # Find impossible chains (blocked_by tasks that are also pending)
    for task_id, task_data in hierarchy.items():
        if task_data.get("type") != "task":
            continue
        deps = task_data.get("dependencies", {}) or {}
        # Handle both dict format and malformed list format
        if isinstance(deps, dict):
            blocked_by = deps.get("blocked_by", []) or []
        else:
            blocked_by = []
        if blocked_by:
            pending_blockers = [
                blocker_id
                for blocker_id in blocked_by
                if hierarchy.get(blocker_id, {}).get("status") == "pending"
            ]
            if pending_blockers:
                deadlocks.append(
                    {
                        "task": task_id,
                        "blocked_by": pending_blockers,
                    }
                )

        blocks_count = len([candidate for candidate, deps in graph.items() if task_id in deps and candidate != task_id])
        if blocks_count >= threshold:
            bottlenecks.append(
                {
                    "task": task_id,
                    "blocks": blocks_count,
                    "threshold": threshold,
                }
            )

    status = "issues" if (cycles or orphaned or deadlocks or bottlenecks) else "ok"

    return DependencyAnalysis(
        cycles=cycles,
        orphaned=orphaned,
        deadlocks=deadlocks,
        bottlenecks=bottlenecks,
        status=status,
    )


def find_circular_dependencies(spec_data: Dict) -> Dict[str, object]:
    """Backward-compatible wrapper returning legacy dependency analysis format."""

    analysis = analyze_dependencies(spec_data)

    return {
        "has_circular": bool(analysis.cycles),
        "circular_chains": analysis.cycles,
        "orphaned_tasks": analysis.orphaned,
        "impossible_chains": analysis.deadlocks,
        "bottlenecks": analysis.bottlenecks,
        "status": analysis.status,
    }


def find_circular_dependencies(spec_data: Dict) -> Dict[str, object]:
    """Backward-compatible wrapper returning legacy dependency analysis format."""

    analysis = analyze_dependencies(spec_data)

    return {
        "has_circular": bool(analysis.cycles),
        "circular_chains": analysis.cycles,
        "orphaned_tasks": analysis.orphaned,
        "impossible_chains": analysis.deadlocks,
        "bottlenecks": analysis.bottlenecks,
        "status": analysis.status,
    }


def has_dependency_cycle(graph: Dict[str, List[str]], node: str) -> Tuple[bool, Optional[List[str]]]:
    """
    Check if a specific node is part of a circular dependency.

    Args:
        graph: Dependency graph mapping node IDs to their dependencies
        node: Node ID to check

    Returns:
        Tuple of (has_cycle: bool, cycle_path: List[str] or None)

    Example:
        >>> graph = {"task-1": ["task-2"], "task-2": ["task-1"]}
        >>> has_cycle, path = has_dependency_cycle(graph, "task-1")
        >>> print(has_cycle)  # True
        >>> print(path)  # ["task-1", "task-2", "task-1"]
    """
    def dfs(current: str, visited: Set[str], rec_stack: Set[str], path: List[str]) -> Tuple[bool, Optional[List[str]]]:
        """DFS helper for cycle detection."""
        visited.add(current)
        rec_stack.add(current)
        current_path = path + [current]

        for neighbor in graph.get(current, []):
            if neighbor not in visited:
                found, cycle_path = dfs(neighbor, visited, rec_stack, current_path)
                if found:
                    return True, cycle_path
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = current_path.index(neighbor)
                return True, current_path[cycle_start:] + [neighbor]

        rec_stack.remove(current)
        return False, None

    if node not in graph:
        return False, None

    return dfs(node, set(), set(), [])


def validate_dependency_graph(spec_data: Dict) -> Tuple[bool, List[str]]:
    """
    Quick validation that dependency graph is valid.

    Checks for:
    - No circular dependencies
    - No orphaned dependencies
    - Valid dependency references

    Args:
        spec_data: JSON spec file data dictionary

    Returns:
        Tuple of (is_valid: bool, error_messages: List[str])

    Example:
        >>> valid, errors = validate_dependency_graph(spec_data)
        >>> if not valid:
        ...     for error in errors:
        ...         print(f"Error: {error}")
    """
    errors = []

    # Run comprehensive analysis
    result = analyze_dependencies(spec_data)

    # Check for circular dependencies
    if result.cycles:
        for chain in result.cycles:
            chain_str = " → ".join(chain)
            errors.append(f"Circular dependency: {chain_str}")

    # Check for orphaned tasks
    if result.orphaned:
        for orphan in result.orphaned:
            errors.append(
                f"Task '{orphan['task']}' references missing dependency '{orphan['missing_dependency']}'"
            )

    # Check for impossible chains (warnings, not errors)
    if result.deadlocks:
        for deadlock in result.deadlocks:
            errors.append(
                f"Potential deadlock: Task '{deadlock['task']}' blocked by {deadlock['blocked_by']}"
            )

    is_valid = len(errors) == 0
    return is_valid, errors


def get_dependency_chain(spec_data: Dict, task_id: str) -> List[str]:
    """
    Get the full dependency chain for a task.

    Returns list of task IDs that must be completed before the given task,
    in order from immediate dependencies to transitive dependencies.

    Args:
        spec_data: JSON spec file data dictionary
        task_id: Task ID to analyze

    Returns:
        List of task IDs in dependency order

    Example:
        >>> chain = get_dependency_chain(spec_data, "task-3-1")
        >>> print(chain)  # ["task-1-1", "task-2-1", "task-3-1"]
    """
    hierarchy = spec_data.get("hierarchy", {})
    task_data = hierarchy.get(task_id, {})

    if not task_data:
        return []

    # Get immediate dependencies
    deps = task_data.get("dependencies", {})
    # Handle both dict format and malformed list format
    if isinstance(deps, dict):
        blocked_by = deps.get("blocked_by", [])
    else:
        blocked_by = []

    # Recursively get dependencies
    chain = []
    visited = set()

    def collect_deps(current_id: str):
        """Recursively collect all dependencies."""
        if current_id in visited:
            return
        visited.add(current_id)

        current_data = hierarchy.get(current_id, {})
        current_deps = current_data.get("dependencies", {})
        # Handle both dict format and malformed list format
        if isinstance(current_deps, dict):
            current_blocked_by = current_deps.get("blocked_by", [])
        else:
            current_blocked_by = []

        # First collect dependencies of dependencies
        for dep in current_blocked_by:
            collect_deps(dep)

        # Then add current task
        if current_id not in chain:
            chain.append(current_id)

    collect_deps(task_id)
    return chain


def find_blocking_tasks(spec_data: Dict, task_id: str) -> List[str]:
    """
    Find all tasks that are blocked by the given task.

    Args:
        spec_data: JSON spec file data dictionary
        task_id: Task ID to analyze

    Returns:
        List of task IDs that are blocked by this task

    Example:
        >>> blocked = find_blocking_tasks(spec_data, "task-1-1")
        >>> print(f"{task_id} blocks {len(blocked)} tasks")
    """
    hierarchy = spec_data.get("hierarchy", {})
    blocked_tasks = []

    for candidate_id, candidate_data in hierarchy.items():
        if candidate_data.get("type") == "task":
            deps = candidate_data.get("dependencies", {})
            # Handle both dict format and malformed list format
            if isinstance(deps, dict):
                blocked_by = deps.get("blocked_by", [])
            else:
                blocked_by = []

            if task_id in blocked_by:
                blocked_tasks.append(candidate_id)

    return blocked_tasks
