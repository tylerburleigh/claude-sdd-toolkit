"""Spec analyzer for AI-enhanced rendering.

This module provides analysis capabilities for JSON spec files, including:
- Critical path detection through dependency trees
- Bottleneck identification (tasks blocking many others)
- Task graph construction and traversal
- Dependency relationship analysis

The SpecAnalyzer is the core analysis engine used by AIEnhancedRenderer
to provide intelligent insights about spec structure and execution risks.
"""

from typing import Dict, Any, List, Set, Optional, Tuple
from collections import defaultdict, deque


class SpecAnalyzer:
    """Analyzes JSON spec structure for critical paths and bottlenecks.

    The analyzer builds an internal graph model of the spec's task hierarchy
    and dependency relationships, enabling detection of:
    - Critical paths (longest dependency chains)
    - Bottlenecks (tasks that block many others)
    - Parallelizable tasks
    - High-risk dependencies

    Attributes:
        spec_data: Complete JSON spec dictionary
        hierarchy: Task hierarchy from spec
        task_graph: Adjacency list representation of task dependencies
        reverse_graph: Reverse dependency graph (for bottleneck detection)

    Example:
        >>> analyzer = SpecAnalyzer(spec_data)
        >>> critical_path = analyzer.get_critical_path()
        >>> bottlenecks = analyzer.get_bottlenecks()
    """

    def __init__(self, spec_data: Dict[str, Any]):
        """Initialize analyzer with spec data.

        Args:
            spec_data: Complete JSON spec dictionary containing hierarchy,
                      metadata, and task information
        """
        self.spec_data = spec_data
        self.hierarchy = spec_data.get('hierarchy', {})

        # Build internal graph representations
        self.task_graph: Dict[str, List[str]] = {}  # task_id -> [dependent_ids]
        self.reverse_graph: Dict[str, List[str]] = {}  # task_id -> [blocker_ids]
        self._build_graphs()

    def _build_graphs(self) -> None:
        """Build task dependency graphs from hierarchy.

        Constructs both forward and reverse dependency graphs:
        - task_graph: Maps each task to tasks that depend on it
        - reverse_graph: Maps each task to tasks it depends on

        This enables efficient traversal for both critical path
        (forward) and bottleneck detection (reverse).
        """
        # Initialize graphs for all tasks
        for task_id, task_data in self.hierarchy.items():
            if task_id == 'spec-root':
                continue

            self.task_graph[task_id] = []
            self.reverse_graph[task_id] = []

        # Build edges from dependencies
        for task_id, task_data in self.hierarchy.items():
            if task_id == 'spec-root':
                continue

            deps = task_data.get('dependencies', {})

            # Process 'blocks' relationships
            blocks = deps.get('blocks', [])
            for blocked_task in blocks:
                if blocked_task in self.hierarchy:
                    self.task_graph[task_id].append(blocked_task)
                    self.reverse_graph[blocked_task].append(task_id)

            # Process 'blocked_by' relationships (reverse direction)
            blocked_by = deps.get('blocked_by', [])
            for blocker_task in blocked_by:
                if blocker_task in self.hierarchy:
                    self.reverse_graph[task_id].append(blocker_task)
                    self.task_graph[blocker_task].append(task_id)

    def get_critical_path(self) -> List[str]:
        """Detect the critical path through the dependency tree.

        The critical path is the longest chain of dependent tasks from
        any starting task to any ending task. Tasks on the critical path
        have zero slack time - any delay ripples through the entire project.

        Uses dynamic programming with topological sort to compute the
        longest path through the dependency graph.

        Returns:
            List of task IDs forming the critical path, in execution order.
            Empty list if no dependencies exist or graph has cycles.

        Algorithm:
            1. Compute topological ordering of tasks
            2. For each task in topo order, compute longest path ending at that task
            3. Track predecessors to reconstruct path
            4. Return longest path found

        Example:
            >>> analyzer = SpecAnalyzer(spec_data)
            >>> path = analyzer.get_critical_path()
            >>> print(path)
            ['task-1-1', 'task-2-3', 'task-3-1', 'task-4-2']
        """
        # Get topological ordering
        topo_order = self._topological_sort()
        if not topo_order:
            # Cycle detected or empty graph
            return []

        # Dynamic programming: compute longest path ending at each task
        longest_path_length: Dict[str, int] = defaultdict(int)
        predecessor: Dict[str, Optional[str]] = {}

        for task_id in topo_order:
            # Check all blockers (incoming edges)
            blockers = self.reverse_graph.get(task_id, [])

            if not blockers:
                # Starting task (no dependencies)
                longest_path_length[task_id] = 1
                predecessor[task_id] = None
            else:
                # Find blocker with longest path
                max_length = 0
                best_predecessor = None

                for blocker in blockers:
                    blocker_length = longest_path_length.get(blocker, 0)
                    if blocker_length > max_length:
                        max_length = blocker_length
                        best_predecessor = blocker

                longest_path_length[task_id] = max_length + 1
                predecessor[task_id] = best_predecessor

        # Find task with longest path
        if not longest_path_length:
            return []

        end_task = max(longest_path_length.keys(),
                      key=lambda t: longest_path_length[t])

        # Reconstruct path by following predecessors backward
        path = []
        current = end_task

        while current is not None:
            path.append(current)
            current = predecessor.get(current)

        # Reverse to get execution order (start to end)
        path.reverse()

        return path

    def get_bottlenecks(self, min_dependents: int = 3) -> List[Tuple[str, int]]:
        """Identify tasks that block many others (bottlenecks).

        Bottleneck tasks have high "fan-out" - many other tasks depend on them.
        Delays in bottleneck tasks have cascading impact across the project.

        Args:
            min_dependents: Minimum number of dependent tasks to qualify
                          as a bottleneck (default: 3)

        Returns:
            List of (task_id, dependent_count) tuples, sorted by dependent
            count descending. Only includes tasks meeting min_dependents threshold.

        Example:
            >>> analyzer = SpecAnalyzer(spec_data)
            >>> bottlenecks = analyzer.get_bottlenecks(min_dependents=2)
            >>> for task_id, count in bottlenecks:
            ...     print(f"{task_id}: blocks {count} tasks")
            task-1-3: blocks 5 tasks
            task-2-1: blocks 4 tasks
        """
        bottlenecks = []

        for task_id in self.task_graph:
            # Count direct dependents (tasks blocked by this task)
            direct_dependents = self.task_graph.get(task_id, [])
            dependent_count = len(direct_dependents)

            if dependent_count >= min_dependents:
                bottlenecks.append((task_id, dependent_count))

        # Sort by dependent count (descending)
        bottlenecks.sort(key=lambda x: x[1], reverse=True)

        return bottlenecks

    def _topological_sort(self) -> List[str]:
        """Perform topological sort on task dependency graph.

        Uses Kahn's algorithm (BFS-based topological sort) to order tasks
        such that all dependencies come before dependent tasks.

        Returns:
            List of task IDs in topological order, or empty list if
            graph contains cycles (invalid dependency structure).

        Algorithm:
            1. Find all tasks with no dependencies (in-degree = 0)
            2. Process each such task:
               - Add to result
               - Remove its edges (decrement dependents' in-degrees)
               - Add newly zero-in-degree tasks to queue
            3. If all tasks processed, return order; else cycle detected
        """
        # Calculate in-degrees (number of blockers for each task)
        in_degree: Dict[str, int] = defaultdict(int)

        for task_id in self.hierarchy:
            if task_id == 'spec-root':
                continue
            in_degree[task_id] = 0

        for task_id in self.reverse_graph:
            blockers = self.reverse_graph.get(task_id, [])
            in_degree[task_id] = len(blockers)

        # Find all tasks with no dependencies (in-degree = 0)
        queue: deque = deque()
        for task_id, degree in in_degree.items():
            if degree == 0:
                queue.append(task_id)

        # Process tasks in topological order
        topo_order = []

        while queue:
            current = queue.popleft()
            topo_order.append(current)

            # Process all tasks blocked by current task
            dependents = self.task_graph.get(current, [])
            for dependent in dependents:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check if all tasks were processed (no cycles)
        expected_count = len([t for t in self.hierarchy if t != 'spec-root'])
        if len(topo_order) != expected_count:
            # Cycle detected - return empty list
            return []

        return topo_order

    def get_task_depth(self, task_id: str) -> int:
        """Calculate the depth of a task in the dependency tree.

        Depth is the length of the longest path from any root task
        (task with no dependencies) to this task.

        Args:
            task_id: ID of the task to analyze

        Returns:
            Depth value (0 for root tasks, higher for deeper tasks).
            Returns -1 if task_id not found.

        Example:
            >>> analyzer = SpecAnalyzer(spec_data)
            >>> depth = analyzer.get_task_depth('task-3-2')
            >>> print(f"Task is {depth} levels deep")
        """
        if task_id not in self.hierarchy:
            return -1

        # BFS to find longest path to this task
        visited: Set[str] = set()
        queue: deque = deque([(task_id, 0)])
        max_depth = 0

        while queue:
            current, depth = queue.popleft()

            if current in visited:
                continue
            visited.add(current)

            max_depth = max(max_depth, depth)

            # Explore blockers (predecessors)
            blockers = self.reverse_graph.get(current, [])
            for blocker in blockers:
                if blocker not in visited:
                    queue.append((blocker, depth + 1))

        return max_depth

    def get_parallelizable_tasks(self, pending_only: bool = True) -> List[List[str]]:
        """Identify groups of tasks that can be executed in parallel.

        Tasks can be parallelized if they:
        1. Have no dependencies on each other
        2. All their dependencies are satisfied
        3. Are in pending status (if pending_only=True)

        Args:
            pending_only: Only include tasks with status='pending'

        Returns:
            List of task groups, where each group contains task IDs
            that can be executed in parallel. Groups are ordered by
            execution sequence (earlier groups must finish before later ones).

        Example:
            >>> analyzer = SpecAnalyzer(spec_data)
            >>> parallel_groups = analyzer.get_parallelizable_tasks()
            >>> for i, group in enumerate(parallel_groups):
            ...     print(f"Wave {i+1}: {', '.join(group)}")
            Wave 1: task-1-1, task-1-2, task-1-3
            Wave 2: task-2-1, task-2-2
            Wave 3: task-3-1
        """
        # Get topological ordering
        topo_order = self._topological_sort()
        if not topo_order:
            return []

        # Calculate in-degrees for current state
        in_degree: Dict[str, int] = {}
        for task_id in self.hierarchy:
            if task_id == 'spec-root':
                continue

            if pending_only:
                task_data = self.hierarchy[task_id]
                if task_data.get('status') != 'pending':
                    continue

            blockers = self.reverse_graph.get(task_id, [])
            in_degree[task_id] = len(blockers)

        # Group tasks into parallel waves
        waves = []
        processed: Set[str] = set()

        while len(processed) < len(in_degree):
            # Find all tasks that can start now (in-degree = 0)
            current_wave = []
            for task_id, degree in in_degree.items():
                if task_id not in processed and degree == 0:
                    current_wave.append(task_id)

            if not current_wave:
                # All remaining tasks are blocked - shouldn't happen with valid topo sort
                break

            waves.append(current_wave)

            # Mark wave as processed and update in-degrees
            for task_id in current_wave:
                processed.add(task_id)

                # Reduce in-degree for all dependents
                dependents = self.task_graph.get(task_id, [])
                for dependent in dependents:
                    if dependent in in_degree:
                        in_degree[dependent] -= 1

        return waves

    def get_stats(self) -> Dict[str, Any]:
        """Generate analysis statistics for the spec.

        Returns:
            Dictionary containing:
            - total_tasks: Total number of tasks
            - total_dependencies: Total number of dependency edges
            - max_fan_out: Maximum number of dependents for any task
            - max_fan_in: Maximum number of blockers for any task
            - avg_dependencies: Average dependencies per task
            - has_cycles: Whether dependency graph contains cycles

        Example:
            >>> analyzer = SpecAnalyzer(spec_data)
            >>> stats = analyzer.get_stats()
            >>> print(f"Total tasks: {stats['total_tasks']}")
            >>> print(f"Has cycles: {stats['has_cycles']}")
        """
        total_tasks = len([t for t in self.hierarchy if t != 'spec-root'])

        total_dependencies = sum(
            len(deps) for deps in self.task_graph.values()
        )

        max_fan_out = max(
            (len(deps) for deps in self.task_graph.values()),
            default=0
        )

        max_fan_in = max(
            (len(deps) for deps in self.reverse_graph.values()),
            default=0
        )

        avg_dependencies = (
            total_dependencies / total_tasks if total_tasks > 0 else 0
        )

        # Check for cycles using topological sort
        topo_order = self._topological_sort()
        has_cycles = len(topo_order) == 0 and total_tasks > 0

        return {
            'total_tasks': total_tasks,
            'total_dependencies': total_dependencies,
            'max_fan_out': max_fan_out,
            'max_fan_in': max_fan_in,
            'avg_dependencies': round(avg_dependencies, 2),
            'has_cycles': has_cycles
        }
