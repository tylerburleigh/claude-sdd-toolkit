"""Visualization builder for spec rendering.

This module creates various visualizations to help understand spec status:
- Dependency graphs (Mermaid)
- Progress charts (ASCII/Mermaid)
- Timeline/Gantt charts (Mermaid)
- Category distribution charts
- Risk heatmaps

Visualizations make complex specs more accessible and highlight important patterns.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ProgressData:
    """Progress data for visualization.

    Attributes:
        total_tasks: Total number of tasks
        completed_tasks: Number of completed tasks
        in_progress_tasks: Number of in-progress tasks
        pending_tasks: Number of pending tasks
        blocked_tasks: Number of blocked tasks
        completion_percentage: Overall completion percentage
    """
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    pending_tasks: int
    blocked_tasks: int
    completion_percentage: float


class VisualizationBuilder:
    """Builds visualizations for spec rendering.

    The builder creates various chart types and diagrams to help visualize
    spec structure, progress, and dependencies.

    Supported Visualizations:
    1. Dependency Graphs (Mermaid flowchart)
    2. Progress Charts (ASCII bar charts, Mermaid pie charts)
    3. Timeline/Gantt Charts (Mermaid gantt)
    4. Category Distribution (ASCII/Mermaid)
    5. Risk Heatmaps (ASCII tables)

    Attributes:
        spec_data: Complete JSON spec dictionary
        hierarchy: Task hierarchy from spec
        metadata: Spec metadata

    Example:
        >>> from claude_skills.sdd_render import VisualizationBuilder
        >>> builder = VisualizationBuilder(spec_data)
        >>> progress_chart = builder.build_progress_chart(format='ascii')
        >>> print(progress_chart)
    """

    def __init__(self, spec_data: Dict[str, Any]):
        """Initialize visualization builder.

        Args:
            spec_data: Complete JSON spec dictionary
        """
        self.spec_data = spec_data
        self.hierarchy = spec_data.get('hierarchy', {})
        self.metadata = spec_data.get('metadata', {})

    def get_progress_data(self) -> ProgressData:
        """Extract progress data from spec.

        Returns:
            ProgressData object with task counts and percentages

        Example:
            >>> builder = VisualizationBuilder(spec_data)
            >>> progress = builder.get_progress_data()
            >>> print(f"Completion: {progress.completion_percentage}%")
        """
        root = self.hierarchy.get('spec-root', {})
        total_tasks = root.get('total_tasks', 0)
        completed_tasks = root.get('completed_tasks', 0)

        # Count tasks by status
        status_counts = {
            'pending': 0,
            'in_progress': 0,
            'blocked': 0,
            'completed': completed_tasks
        }

        for task_id, task_data in self.hierarchy.items():
            if task_id == 'spec-root':
                continue

            # Only count actual tasks
            if task_data.get('type') not in ('task', 'subtask', 'verify'):
                continue

            status = task_data.get('status', 'pending')
            if status in status_counts and status != 'completed':
                status_counts[status] += 1

        completion_pct = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return ProgressData(
            total_tasks=total_tasks,
            completed_tasks=status_counts['completed'],
            in_progress_tasks=status_counts['in_progress'],
            pending_tasks=status_counts['pending'],
            blocked_tasks=status_counts['blocked'],
            completion_percentage=round(completion_pct, 1)
        )

    def build_progress_chart_ascii(self, width: int = 50) -> str:
        """Build ASCII progress bar chart.

        Args:
            width: Width of progress bar in characters

        Returns:
            ASCII art progress bar

        Example:
            >>> builder = VisualizationBuilder(spec_data)
            >>> chart = builder.build_progress_chart_ascii(width=40)
            >>> print(chart)
            Progress: [████████████░░░░░░░░░░░░░░░░] 35%
        """
        progress = self.get_progress_data()
        pct = progress.completion_percentage / 100
        filled = int(width * pct)
        empty = width - filled

        bar = '█' * filled + '░' * empty
        return f"Progress: [{bar}] {progress.completion_percentage}%"

    def build_progress_chart_detailed_ascii(self) -> str:
        """Build detailed ASCII progress chart with status breakdown.

        Returns:
            Multi-line ASCII chart with status details

        Example:
            >>> builder = VisualizationBuilder(spec_data)
            >>> chart = builder.build_progress_chart_detailed_ascii()
            >>> print(chart)
        """
        progress = self.get_progress_data()

        total = progress.total_tasks
        completed = progress.completed_tasks
        in_progress = progress.in_progress_tasks
        pending = progress.pending_tasks
        blocked = progress.blocked_tasks

        # Calculate bar lengths
        max_bar_width = 40
        completed_bar = int((completed / total * max_bar_width)) if total > 0 else 0
        in_progress_bar = int((in_progress / total * max_bar_width)) if total > 0 else 0
        pending_bar = int((pending / total * max_bar_width)) if total > 0 else 0
        blocked_bar = int((blocked / total * max_bar_width)) if total > 0 else 0

        chart = f"""## Progress Overview

Total Tasks: {total}

✅ Completed: {completed}/{total} ({completed/total*100 if total > 0 else 0:.1f}%)
{'█' * completed_bar}

🔄 In Progress: {in_progress}/{total} ({in_progress/total*100 if total > 0 else 0:.1f}%)
{'█' * in_progress_bar}

⏸️  Pending: {pending}/{total} ({pending/total*100 if total > 0 else 0:.1f}%)
{'░' * pending_bar}

🚧 Blocked: {blocked}/{total} ({blocked/total*100 if total > 0 else 0:.1f}%)
{'▓' * blocked_bar}

Overall: {progress.completion_percentage}%
"""
        return chart

    def build_progress_chart_mermaid(self) -> str:
        """Build Mermaid pie chart for progress.

        Returns:
            Mermaid pie chart syntax

        Example:
            >>> builder = VisualizationBuilder(spec_data)
            >>> chart = builder.build_progress_chart_mermaid()
            >>> print(chart)
            ```mermaid
            pie title Task Status Distribution
                "Completed" : 15
                "In Progress" : 3
                "Pending" : 22
                "Blocked" : 1
            ```
        """
        progress = self.get_progress_data()

        mermaid = f"""```mermaid
pie title Task Status Distribution
    "Completed" : {progress.completed_tasks}
    "In Progress" : {progress.in_progress_tasks}
    "Pending" : {progress.pending_tasks}
    "Blocked" : {progress.blocked_tasks}
```"""
        return mermaid

    def build_dependency_graph_mermaid(
        self,
        phase_id: Optional[str] = None,
        show_completed: bool = False
    ) -> str:
        """Build Mermaid dependency graph.

        Args:
            phase_id: Optional phase to filter by
            show_completed: Whether to include completed tasks

        Returns:
            Mermaid flowchart syntax

        Example:
            >>> builder = VisualizationBuilder(spec_data)
            >>> graph = builder.build_dependency_graph_mermaid(phase_id="phase-2")
            >>> print(graph)
        """
        # Use DependencyGraphGenerator if available
        try:
            from .dependency_graph import DependencyGraphGenerator, GraphStyle
            from .spec_analyzer import SpecAnalyzer

            analyzer = SpecAnalyzer(self.spec_data)
            generator = DependencyGraphGenerator(self.spec_data, analyzer)

            # Generate graph with filters
            # Note: DependencyGraphGenerator doesn't have show_completed parameter
            # Instead, use simplify parameter to show only major tasks
            return generator.generate_graph(
                style=GraphStyle.FLOWCHART,
                phase_filter=phase_id,
                highlight_critical_path=True,
                show_status=True,
                simplify=not show_completed  # Invert: if show_completed=False, simplify=True
            )

        except (ImportError, Exception):
            # Fallback: simple graph
            return self._build_simple_dependency_graph(phase_id, show_completed)

    def _build_simple_dependency_graph(
        self,
        phase_id: Optional[str] = None,
        show_completed: bool = False
    ) -> str:
        """Build simple dependency graph without full DependencyGraphGenerator.

        Args:
            phase_id: Optional phase to filter by
            show_completed: Whether to include completed tasks

        Returns:
            Simple Mermaid flowchart
        """
        tasks_to_show = []

        for task_id, task_data in self.hierarchy.items():
            if task_id == 'spec-root':
                continue

            # Filter by phase if specified
            if phase_id and task_data.get('parent') != phase_id:
                continue

            # Filter completed tasks if requested
            status = task_data.get('status', 'pending')
            if not show_completed and status == 'completed':
                continue

            tasks_to_show.append((task_id, task_data))

        # Build mermaid syntax
        mermaid = "```mermaid\nflowchart TD\n"

        # Add nodes
        for task_id, task_data in tasks_to_show:
            title = task_data.get('title', task_id)
            status = task_data.get('status', 'pending')

            # Add node with styling
            node_style = self._get_node_style(status)
            mermaid += f"    {task_id}[\"{title}\"]:::{node_style}\n"

        # Add edges
        for task_id, task_data in tasks_to_show:
            dependencies = task_data.get('dependencies', {})
            blocks = dependencies.get('blocks', [])

            for target_id in blocks:
                # Only add edge if target is also shown
                if any(t[0] == target_id for t in tasks_to_show):
                    mermaid += f"    {task_id} --> {target_id}\n"

        # Add style classes
        mermaid += "\n    classDef completed fill:#90EE90\n"
        mermaid += "    classDef inProgress fill:#FFD700\n"
        mermaid += "    classDef pending fill:#D3D3D3\n"
        mermaid += "    classDef blocked fill:#FF6B6B\n"
        mermaid += "```"

        return mermaid

    def _get_node_style(self, status: str) -> str:
        """Get Mermaid style class for task status.

        Args:
            status: Task status

        Returns:
            Style class name
        """
        style_map = {
            'completed': 'completed',
            'in_progress': 'inProgress',
            'pending': 'pending',
            'blocked': 'blocked'
        }
        return style_map.get(status, 'pending')

    def build_timeline_gantt(self, estimate_dates: bool = True) -> str:
        """Build Mermaid Gantt chart for timeline visualization.

        Args:
            estimate_dates: Whether to estimate dates based on current progress

        Returns:
            Mermaid Gantt chart syntax

        Example:
            >>> builder = VisualizationBuilder(spec_data)
            >>> gantt = builder.build_timeline_gantt()
            >>> print(gantt)
        """
        # Get phases
        root = self.hierarchy.get('spec-root', {})
        phase_ids = root.get('children', [])

        mermaid = "```mermaid\ngantt\n"
        mermaid += f"    title {self.metadata.get('title', 'Spec Timeline')}\n"
        mermaid += "    dateFormat YYYY-MM-DD\n\n"

        # Estimate start date (use created_at or today)
        start_date_str = self.metadata.get('created_at', '')
        if start_date_str:
            try:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            except:
                start_date = datetime.now()
        else:
            start_date = datetime.now()

        current_date = start_date

        for phase_id in phase_ids:
            phase_data = self.hierarchy.get(phase_id, {})
            if phase_data.get('type') != 'phase':
                continue

            phase_title = phase_data.get('title', phase_id)
            mermaid += f"    section {phase_title}\n"

            # Get phase tasks
            phase_tasks = self._get_phase_tasks(phase_id)

            for task_id, task_data in phase_tasks:
                title = task_data.get('title', task_id)
                status = task_data.get('status', 'pending')
                metadata = task_data.get('metadata', {})
                estimated_hours = metadata.get('estimated_hours', 8)

                # Estimate task duration
                days = max(1, int(estimated_hours / 8))  # Assume 8 hour work days

                # Format status for Gantt
                status_map = {
                    'completed': 'done',
                    'in_progress': 'active',
                    'pending': 'crit' if metadata.get('risk_level') == 'high' else '',
                    'blocked': 'crit'
                }
                gantt_status = status_map.get(status, '')

                # Add task to gantt
                end_date = current_date + timedelta(days=days)
                mermaid += f"    {title} :{gantt_status}, {current_date.strftime('%Y-%m-%d')}, {days}d\n"

                if estimate_dates:
                    current_date = end_date

        mermaid += "```"
        return mermaid

    def _get_phase_tasks(self, phase_id: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Get all tasks under a phase.

        Args:
            phase_id: Phase identifier

        Returns:
            List of (task_id, task_data) tuples
        """
        phase_data = self.hierarchy.get(phase_id, {})
        children = phase_data.get('children', [])

        tasks = []
        for child_id in children:
            child_data = self.hierarchy.get(child_id, {})
            child_type = child_data.get('type', '')

            if child_type in ('task', 'subtask', 'verify'):
                tasks.append((child_id, child_data))
            elif child_type == 'group':
                # Recursively get tasks from group
                tasks.extend(self._get_phase_tasks(child_id))

        return tasks

    def build_category_distribution(self) -> str:
        """Build category distribution chart.

        Returns:
            ASCII table showing task distribution by category

        Example:
            >>> builder = VisualizationBuilder(spec_data)
            >>> dist = builder.build_category_distribution()
            >>> print(dist)
        """
        # Count tasks by category
        categories = {}

        for task_id, task_data in self.hierarchy.items():
            if task_id == 'spec-root':
                continue

            if task_data.get('type') not in ('task', 'subtask', 'verify'):
                continue

            metadata = task_data.get('metadata', {})
            category = metadata.get('task_category', 'unknown')

            if category not in categories:
                categories[category] = {'total': 0, 'completed': 0}

            categories[category]['total'] += 1
            if task_data.get('status') == 'completed':
                categories[category]['completed'] += 1

        # Build table
        table = "## Task Distribution by Category\n\n"
        table += "| Category | Total | Completed | Progress |\n"
        table += "|----------|-------|-----------|----------|\n"

        for category, counts in sorted(categories.items()):
            total = counts['total']
            completed = counts['completed']
            pct = (completed / total * 100) if total > 0 else 0
            bar_length = int(pct / 10)
            bar = '█' * bar_length + '░' * (10 - bar_length)

            table += f"| {category} | {total} | {completed} | {bar} {pct:.1f}% |\n"

        return table

    def build_risk_heatmap(self) -> str:
        """Build risk heatmap showing high-risk tasks.

        Returns:
            ASCII table with risk levels and task counts

        Example:
            >>> builder = VisualizationBuilder(spec_data)
            >>> heatmap = builder.build_risk_heatmap()
            >>> print(heatmap)
        """
        # Count tasks by risk level
        risk_counts = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'none': []
        }

        for task_id, task_data in self.hierarchy.items():
            if task_id == 'spec-root':
                continue

            if task_data.get('type') not in ('task', 'subtask', 'verify'):
                continue

            metadata = task_data.get('metadata', {})
            risk_level = metadata.get('risk_level', 'medium')
            status = task_data.get('status', 'pending')

            if status != 'completed':  # Only show incomplete tasks
                risk_counts[risk_level].append(task_id)

        # Build heatmap
        heatmap = "## Risk Heatmap (Incomplete Tasks)\n\n"
        heatmap += "| Risk Level | Count | Tasks |\n"
        heatmap += "|------------|-------|-------|\n"

        risk_order = ['critical', 'high', 'medium', 'low', 'none']
        risk_icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢',
            'none': '⚪'
        }

        for risk_level in risk_order:
            tasks = risk_counts[risk_level]
            count = len(tasks)
            icon = risk_icons[risk_level]

            if count > 0:
                task_list = ', '.join(tasks[:3])  # Show first 3
                if count > 3:
                    task_list += f", +{count-3} more"

                heatmap += f"| {icon} {risk_level.title()} | {count} | {task_list} |\n"

        return heatmap

    def build_all_visualizations(self) -> Dict[str, str]:
        """Build all available visualizations.

        Returns:
            Dictionary of visualization_name -> visualization_markdown

        Example:
            >>> builder = VisualizationBuilder(spec_data)
            >>> viz = builder.build_all_visualizations()
            >>> for name, content in viz.items():
            ...     print(f"## {name}")
            ...     print(content)
        """
        return {
            'progress_ascii': self.build_progress_chart_ascii(),
            'progress_detailed': self.build_progress_chart_detailed_ascii(),
            'progress_pie': self.build_progress_chart_mermaid(),
            'dependency_graph': self.build_dependency_graph_mermaid(),
            'timeline_gantt': self.build_timeline_gantt(),
            'category_distribution': self.build_category_distribution(),
            'risk_heatmap': self.build_risk_heatmap()
        }
