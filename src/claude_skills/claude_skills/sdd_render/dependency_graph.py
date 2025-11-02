"""Dependency graph generation for spec visualization.

This module generates Mermaid diagram syntax from spec dependency relationships,
enabling visual understanding of task dependencies, critical paths, and
workflow structure.

Features:
- Mermaid flowchart/graph generation
- Critical path highlighting
- Phase-based filtering
- Collapsible subgraphs for phases
- Status-based node styling
- Bottleneck highlighting
"""

from typing import Dict, Any, List, Optional, Set
from enum import Enum


class GraphStyle(Enum):
    """Graph visualization styles."""
    FLOWCHART = "flowchart"  # Top-down flowchart
    GRAPH = "graph"          # Left-right graph
    SIMPLIFIED = "simplified" # Show only high-level tasks


class NodeShape(Enum):
    """Mermaid node shapes for different task types."""
    TASK = "[]"           # Rectangle
    PHASE = "[()]"        # Stadium/rounded rectangle
    VERIFY = "{{}}"       # Diamond
    GROUP = "[/\\/]"      # Parallelogram
    SUBTASK = "()"        # Circle/rounded


class DependencyGraphGenerator:
    """Generates Mermaid dependency graphs from spec data.

    The generator creates visual representations of task dependencies using
    Mermaid diagram syntax, which can be rendered in markdown viewers.

    Graph Features:

    1. Node Styling:
       - Completed tasks: Green fill
       - In-progress tasks: Yellow fill
       - Pending tasks: Gray fill
       - Blocked tasks: Red fill
       - Critical path: Bold border

    2. Edge Styling:
       - Normal dependencies: Solid arrow
       - Soft dependencies: Dashed arrow
       - Critical path edges: Thicker line

    3. Grouping:
       - Phases as subgraphs
       - Collapsible groups for complex hierarchies
       - Phase-level filtering

    4. Highlighting:
       - Critical path tasks emphasized
       - Bottlenecks marked
       - Blockers indicated

    Attributes:
        spec_data: Complete JSON spec dictionary
        analyzer: SpecAnalyzer instance
        hierarchy: Task hierarchy from spec

    Example:
        >>> from claude_skills.sdd_render import DependencyGraphGenerator, SpecAnalyzer
        >>> analyzer = SpecAnalyzer(spec_data)
        >>> generator = DependencyGraphGenerator(spec_data, analyzer)
        >>> mermaid = generator.generate_graph()
        >>> print(mermaid)
        ```mermaid
        flowchart TD
            task-1-1[Task 1.1]
            task-1-2[Task 1.2]
            task-1-1 --> task-1-2
        ```
    """

    def __init__(self, spec_data: Dict[str, Any], analyzer: Optional[Any] = None):
        """Initialize dependency graph generator.

        Args:
            spec_data: Complete JSON spec dictionary
            analyzer: Optional SpecAnalyzer instance
        """
        self.spec_data = spec_data
        self.hierarchy = spec_data.get('hierarchy', {})

        # Create analyzer if not provided
        if analyzer is None:
            from .spec_analyzer import SpecAnalyzer
            analyzer = SpecAnalyzer(spec_data)

        self.analyzer = analyzer
        self.task_graph = analyzer.task_graph
        self.reverse_graph = analyzer.reverse_graph

    def generate_graph(self,
                      style: GraphStyle = GraphStyle.FLOWCHART,
                      phase_filter: Optional[str] = None,
                      highlight_critical_path: bool = True,
                      show_status: bool = True,
                      simplify: bool = False,
                      group_by_phase: bool = False) -> str:
        """Generate Mermaid graph syntax.

        Args:
            style: Graph layout style
            phase_filter: Optional phase ID to filter by
            highlight_critical_path: Emphasize critical path tasks
            show_status: Apply status-based styling
            simplify: Show only major tasks (skip subtasks)
            group_by_phase: Group tasks by phase (currently ignored for compatibility)

        Returns:
            Mermaid diagram syntax as string

        Example:
            >>> generator = DependencyGraphGenerator(spec_data, analyzer)
            >>> graph = generator.generate_graph(
            ...     style=GraphStyle.FLOWCHART,
            ...     highlight_critical_path=True
            ... )
        """
        lines = []

        # Header
        if style == GraphStyle.FLOWCHART:
            lines.append("```mermaid")
            lines.append("flowchart TD")
        elif style == GraphStyle.GRAPH:
            lines.append("```mermaid")
            lines.append("graph LR")
        else:
            lines.append("```mermaid")
            lines.append("flowchart TD")

        # Get tasks to include
        if phase_filter:
            tasks = self._get_phase_tasks(phase_filter)
        else:
            tasks = [t for t in self.hierarchy.keys() if t != 'spec-root']

        if simplify:
            tasks = self._filter_major_tasks(tasks)

        # Get critical path if highlighting
        critical_path_set = set()
        if highlight_critical_path:
            critical_path = self.analyzer.get_critical_path()
            critical_path_set = set(critical_path)

        # If grouping by phase, organize tasks by their phase
        if group_by_phase:
            phases = [t for t in tasks if self.hierarchy.get(t, {}).get('type') == 'phase']

            for phase_id in phases:
                phase_data = self.hierarchy.get(phase_id, {})
                phase_title = phase_data.get('title', phase_id)

                # Start subgraph for this phase
                lines.append(f"    subgraph {phase_id} [\"{phase_title}\"]")

                # Get tasks in this phase
                phase_tasks = phase_data.get('children', [])

                # Generate nodes for tasks in this phase
                for task_id in phase_tasks:
                    if task_id in tasks:
                        task_data = self.hierarchy.get(task_id, {})
                        node_line = self._generate_node(
                            task_id,
                            task_data,
                            in_critical_path=task_id in critical_path_set
                        )
                        if node_line:
                            lines.append(f"        {node_line}")

                # End subgraph
                lines.append("    end")

            # Generate all edges (outside subgraphs)
            for task_id in tasks:
                deps = self.task_graph.get(task_id, [])
                for dep_id in deps:
                    if dep_id in tasks:
                        edge_line = self._generate_edge(
                            task_id,
                            dep_id,
                            is_critical=task_id in critical_path_set and dep_id in critical_path_set
                        )
                        lines.append(f"    {edge_line}")
        else:
            # Generate nodes (no grouping)
            for task_id in tasks:
                task_data = self.hierarchy.get(task_id, {})
                node_line = self._generate_node(
                    task_id,
                    task_data,
                    in_critical_path=task_id in critical_path_set
                )
                if node_line:
                    lines.append(f"    {node_line}")

            # Generate edges
            for task_id in tasks:
                deps = self.task_graph.get(task_id, [])
                for dep_id in deps:
                    if dep_id in tasks:  # Only show edge if both nodes visible
                        edge_line = self._generate_edge(
                            task_id,
                            dep_id,
                            is_critical=task_id in critical_path_set and dep_id in critical_path_set
                        )
                        lines.append(f"    {edge_line}")

        # Apply styling
        if show_status:
            style_lines = self._generate_styles(tasks, critical_path_set)
            lines.extend(style_lines)

        lines.append("```")

        return "\n".join(lines)

    def generate(self, **kwargs) -> str:
        """Alias for generate_graph() for backward compatibility.

        Accepts all the same parameters as generate_graph().

        Returns:
            Mermaid diagram syntax as string
        """
        return self.generate_graph(**kwargs)

    def generate_phase_graph(self, phase_id: str) -> str:
        """Generate graph for a specific phase.

        Args:
            phase_id: Phase identifier

        Returns:
            Mermaid diagram showing only tasks in this phase

        Example:
            >>> generator = DependencyGraphGenerator(spec_data, analyzer)
            >>> phase_graph = generator.generate_phase_graph('phase-2')
        """
        return self.generate_graph(
            phase_filter=phase_id,
            highlight_critical_path=True,
            show_status=True
        )

    def generate_simplified_graph(self) -> str:
        """Generate simplified graph showing only major tasks.

        Returns:
            Mermaid diagram with high-level overview

        Example:
            >>> generator = DependencyGraphGenerator(spec_data, analyzer)
            >>> overview = generator.generate_simplified_graph()
        """
        return self.generate_graph(
            simplify=True,
            highlight_critical_path=True,
            show_status=True
        )

    def _generate_node(self,
                      task_id: str,
                      task_data: Dict[str, Any],
                      in_critical_path: bool = False) -> str:
        """Generate Mermaid node syntax.

        Args:
            task_id: Task identifier
            task_data: Task data from hierarchy
            in_critical_path: Whether task is on critical path

        Returns:
            Mermaid node definition string
        """
        task_type = task_data.get('type', 'task')
        title = task_data.get('title', task_id)

        # Truncate long titles
        if len(title) > 40:
            title = title[:37] + "..."

        # Escape special characters
        title = title.replace('"', '\\"')

        # Choose node shape based on type
        if task_type == 'phase':
            shape_start, shape_end = "[(", ")]"
        elif task_type == 'verify':
            shape_start, shape_end = "{", "}"
        elif task_type == 'group':
            shape_start, shape_end = "[/", "/]"
        elif task_type == 'subtask':
            shape_start, shape_end = "(", ")"
        else:
            shape_start, shape_end = "[", "]"

        # Build node definition
        node_def = f"{task_id}{shape_start}\"{title}\"{shape_end}"

        return node_def

    def _generate_edge(self,
                      from_id: str,
                      to_id: str,
                      is_critical: bool = False) -> str:
        """Generate Mermaid edge syntax.

        Args:
            from_id: Source task ID
            to_id: Target task ID
            is_critical: Whether edge is on critical path

        Returns:
            Mermaid edge definition string
        """
        if is_critical:
            # Thicker arrow for critical path
            return f"{from_id} ==> {to_id}"
        else:
            # Normal arrow
            return f"{from_id} --> {to_id}"

    def _generate_styles(self,
                        tasks: List[str],
                        critical_path: Set[str]) -> List[str]:
        """Generate CSS styling for nodes.

        Args:
            tasks: List of task IDs to style
            critical_path: Set of critical path task IDs

        Returns:
            List of Mermaid style definition lines
        """
        lines = []

        # Group tasks by status
        completed = []
        in_progress = []
        pending = []
        blocked = []

        for task_id in tasks:
            task_data = self.hierarchy.get(task_id, {})
            status = task_data.get('status', 'pending')

            if status == 'completed':
                completed.append(task_id)
            elif status == 'in_progress':
                in_progress.append(task_id)
            elif status == 'blocked':
                blocked.append(task_id)
            else:
                pending.append(task_id)

        # Apply status styles
        if completed:
            lines.append(f"    classDef completed fill:#90EE90,stroke:#2E7D32,stroke-width:2px")
            for task_id in completed:
                lines.append(f"    class {task_id} completed")

        if in_progress:
            lines.append(f"    classDef inProgress fill:#FFE082,stroke:#F57C00,stroke-width:2px")
            for task_id in in_progress:
                lines.append(f"    class {task_id} inProgress")

        if blocked:
            lines.append(f"    classDef blocked fill:#FFCDD2,stroke:#C62828,stroke-width:2px")
            for task_id in blocked:
                lines.append(f"    class {task_id} blocked")

        if pending:
            lines.append(f"    classDef pending fill:#E0E0E0,stroke:#616161,stroke-width:1px")
            for task_id in pending:
                if task_id not in critical_path:  # Don't override critical path style
                    lines.append(f"    class {task_id} pending")

        # Apply critical path style (overrides status for emphasis)
        if critical_path:
            critical_in_view = [t for t in critical_path if t in tasks]
            if critical_in_view:
                lines.append(f"    classDef critical stroke:#1565C0,stroke-width:4px")
                for task_id in critical_in_view:
                    lines.append(f"    class {task_id} critical")

        return lines

    def _get_phase_tasks(self, phase_id: str) -> List[str]:
        """Get all task IDs under a phase.

        Args:
            phase_id: Phase identifier

        Returns:
            List of task IDs in this phase
        """
        phase_data = self.hierarchy.get(phase_id, {})
        children = phase_data.get('children', [])

        tasks = [phase_id]  # Include phase itself

        for child_id in children:
            child_data = self.hierarchy.get(child_id, {})
            child_type = child_data.get('type', '')

            tasks.append(child_id)

            # Recursively add children of groups
            if child_type == 'group':
                tasks.extend(self._get_phase_tasks(child_id))

        return tasks

    def _filter_major_tasks(self, tasks: List[str]) -> List[str]:
        """Filter to show only major tasks (exclude subtasks).

        Args:
            tasks: Full list of task IDs

        Returns:
            Filtered list with only phases, groups, and top-level tasks
        """
        major_tasks = []

        for task_id in tasks:
            task_data = self.hierarchy.get(task_id, {})
            task_type = task_data.get('type', 'task')

            # Include phases, groups, and top-level tasks
            if task_type in ('phase', 'group', 'task'):
                major_tasks.append(task_id)
            # Exclude subtasks and verify tasks in simplified view

        return major_tasks

    def generate_critical_path_graph(self) -> str:
        """Generate graph showing only critical path.

        Returns:
            Mermaid diagram with only critical path tasks

        Example:
            >>> generator = DependencyGraphGenerator(spec_data, analyzer)
            >>> critical_graph = generator.generate_critical_path_graph()
        """
        critical_path = self.analyzer.get_critical_path()

        if not critical_path:
            return "```mermaid\nflowchart TD\n    note[No critical path found]\n```"

        lines = [
            "```mermaid",
            "flowchart TD"
        ]

        # Generate nodes for critical path
        for task_id in critical_path:
            task_data = self.hierarchy.get(task_id, {})
            node_line = self._generate_node(task_id, task_data, in_critical_path=True)
            if node_line:
                lines.append(f"    {node_line}")

        # Generate edges (sequential through critical path)
        for i in range(len(critical_path) - 1):
            from_id = critical_path[i]
            to_id = critical_path[i + 1]
            lines.append(f"    {from_id} ==> {to_id}")

        # Style all as critical
        lines.append("    classDef critical fill:#FFE082,stroke:#1565C0,stroke-width:4px")
        for task_id in critical_path:
            lines.append(f"    class {task_id} critical")

        lines.append("```")

        return "\n".join(lines)

    def generate_bottleneck_graph(self, min_dependents: int = 3) -> str:
        """Generate graph highlighting bottleneck tasks.

        Args:
            min_dependents: Minimum dependents to qualify as bottleneck

        Returns:
            Mermaid diagram with bottleneck tasks emphasized

        Example:
            >>> generator = DependencyGraphGenerator(spec_data, analyzer)
            >>> bottleneck_graph = generator.generate_bottleneck_graph()
        """
        bottlenecks = self.analyzer.get_bottlenecks(min_dependents=min_dependents)
        bottleneck_ids = [task_id for task_id, _ in bottlenecks]

        # Get all tasks involved with bottlenecks (bottleneck + its dependents)
        involved_tasks = set(bottleneck_ids)
        for task_id in bottleneck_ids:
            dependents = self.task_graph.get(task_id, [])
            involved_tasks.update(dependents)

        lines = [
            "```mermaid",
            "flowchart TD"
        ]

        # Generate nodes
        for task_id in involved_tasks:
            task_data = self.hierarchy.get(task_id, {})
            node_line = self._generate_node(task_id, task_data)
            if node_line:
                lines.append(f"    {node_line}")

        # Generate edges
        for task_id in involved_tasks:
            deps = self.task_graph.get(task_id, [])
            for dep_id in deps:
                if dep_id in involved_tasks:
                    lines.append(f"    {task_id} --> {dep_id}")

        # Highlight bottlenecks
        if bottleneck_ids:
            lines.append("    classDef bottleneck fill:#FFCDD2,stroke:#C62828,stroke-width:4px")
            for task_id in bottleneck_ids:
                lines.append(f"    class {task_id} bottleneck")

        lines.append("```")

        return "\n".join(lines)
