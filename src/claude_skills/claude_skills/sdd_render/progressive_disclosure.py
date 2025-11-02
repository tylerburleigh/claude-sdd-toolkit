"""Progressive disclosure for spec rendering.

This module implements progressive disclosure techniques to make large specifications
more manageable. It provides:
- Detail level calculation based on task context
- Collapsible markdown generation
- Smart content summarization
- User-adaptive content display

Progressive disclosure helps users focus on what matters most by showing
high-level summaries initially and allowing drill-down for details.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class DetailLevel(Enum):
    """Level of detail to show for a task or section."""
    SUMMARY = "summary"      # Minimal: title, status, key metrics only
    MEDIUM = "medium"        # Moderate: add description, basic dependencies
    FULL = "full"           # Complete: all details, verification steps, notes


@dataclass
class DetailContext:
    """Context for determining detail level.

    Attributes:
        task_status: Current task status (pending, in_progress, completed, blocked)
        priority_score: Priority score from PriorityRanker (0-10)
        risk_level: Risk level (low, medium, high, critical)
        is_blocking: Whether this task blocks other tasks
        has_blockers: Whether this task is blocked
        user_focus: Optional user-specified focus area
        depth_level: Nesting depth in hierarchy (0=phase, 1=task, 2=subtask)
    """
    task_status: str
    priority_score: float
    risk_level: str
    is_blocking: bool
    has_blockers: bool
    user_focus: Optional[str] = None
    depth_level: int = 0


class DetailLevelCalculator:
    """Calculates appropriate detail level for tasks and sections.

    The calculator uses multiple factors to determine how much detail
    to show for each task:

    1. Status-based:
       - in_progress: FULL (need complete context)
       - blocked: MEDIUM (show blockers, but not all details)
       - completed: SUMMARY (just show what was done)
       - pending: Depends on other factors

    2. Priority-based:
       - High priority (>7): FULL (important to understand)
       - Medium priority (4-7): MEDIUM
       - Low priority (<4): SUMMARY

    3. Risk-based:
       - Critical/High risk: FULL (need all context)
       - Medium risk: MEDIUM
       - Low/No risk: SUMMARY

    4. Dependency-based:
       - Blocking many tasks: FULL (critical path)
       - Has blockers: MEDIUM (show dependencies)
       - Independent: SUMMARY

    5. User focus:
       - Matching user focus area: FULL
       - Related to focus: MEDIUM
       - Unrelated: SUMMARY

    Attributes:
        spec_data: Complete JSON spec dictionary
        priority_ranker: Optional PriorityRanker for priority scores
        user_focus: Optional user-specified focus area
    """

    def __init__(
        self,
        spec_data: Optional[Dict[str, Any]] = None,
        priority_ranker: Optional[Any] = None,
        user_focus: Optional[str] = None
    ):
        """Initialize detail level calculator.

        Args:
            spec_data: Optional complete JSON spec dictionary (defaults to empty dict)
            priority_ranker: Optional PriorityRanker instance
            user_focus: Optional user focus (e.g., "phase-2", "authentication")
        """
        self.spec_data = spec_data or {}
        self.hierarchy = self.spec_data.get('hierarchy', {})
        self.priority_ranker = priority_ranker
        self.user_focus = user_focus

    def calculate_detail_level(self, task_id_or_context) -> DetailLevel:
        """Calculate appropriate detail level for a task.

        Args:
            task_id_or_context: Either a task identifier string or a DetailContext object

        Returns:
            DetailLevel enum (SUMMARY, MEDIUM, or FULL)

        Example:
            >>> calculator = DetailLevelCalculator(spec_data)
            >>> level = calculator.calculate_detail_level("task-2-1")
            >>> print(level)
            DetailLevel.FULL

            >>> context = DetailContext(task_status='in_progress', priority_score=5.0, ...)
            >>> level = calculator.calculate_detail_level(context)
        """
        # Check if argument is a DetailContext object or a task_id string
        if isinstance(task_id_or_context, DetailContext):
            context = task_id_or_context
        else:
            task_id = task_id_or_context
            task_data = self.hierarchy.get(task_id, {})
            # Build context
            context = self._build_context(task_id, task_data)

        # Calculate detail level using rules
        return self._apply_detail_rules(context)

    def _build_context(self, task_id: str, task_data: Dict[str, Any]) -> DetailContext:
        """Build context for detail level calculation.

        Args:
            task_id: Task identifier
            task_data: Task data from hierarchy

        Returns:
            DetailContext with all relevant factors
        """
        status = task_data.get('status', 'pending')

        # Get priority score if ranker available
        priority_score = 5.0  # Default medium priority
        if self.priority_ranker:
            try:
                priority = self.priority_ranker.calculate_priority(task_id)
                priority_score = priority.score
            except:
                pass

        # Get risk level
        metadata = task_data.get('metadata', {})
        risk_level = metadata.get('risk_level', 'medium')

        # Check if blocking other tasks
        dependencies = task_data.get('dependencies', {})
        blocks = dependencies.get('blocks', [])
        is_blocking = len(blocks) > 0

        # Check if this task has blockers
        blocked_by = dependencies.get('blocked_by', [])
        has_blockers = len(blocked_by) > 0

        # Calculate depth level
        depth_level = self._calculate_depth(task_id)

        return DetailContext(
            task_status=status,
            priority_score=priority_score,
            risk_level=risk_level,
            is_blocking=is_blocking,
            has_blockers=has_blockers,
            user_focus=self.user_focus,
            depth_level=depth_level
        )

    def _calculate_depth(self, task_id: str) -> int:
        """Calculate nesting depth of a task.

        Args:
            task_id: Task identifier

        Returns:
            Depth level (0=phase, 1=task, 2=subtask, etc.)
        """
        task_data = self.hierarchy.get(task_id, {})
        task_type = task_data.get('type', '')

        # Map types to depth
        depth_map = {
            'phase': 0,
            'group': 1,
            'task': 1,
            'subtask': 2,
            'verify': 2
        }

        return depth_map.get(task_type, 1)

    def _apply_detail_rules(self, context: DetailContext) -> DetailLevel:
        """Apply rules to determine detail level.

        Args:
            context: DetailContext with all factors

        Returns:
            DetailLevel enum
        """
        # Rule 1: In-progress tasks always get full detail
        if context.task_status == 'in_progress':
            return DetailLevel.FULL

        # Rule 2: Blocked tasks get medium detail (show blockers)
        if context.task_status == 'blocked' or context.has_blockers:
            return DetailLevel.MEDIUM

        # Rule 3: Critical/high risk tasks get full detail
        if context.risk_level in ('critical', 'high'):
            return DetailLevel.FULL

        # Rule 4: High priority tasks get full detail
        if context.priority_score >= 7.0:
            return DetailLevel.FULL

        # Rule 5: Tasks blocking many others get full detail
        if context.is_blocking:
            return DetailLevel.FULL

        # Rule 6: User focus match gets full detail
        if context.user_focus and self._matches_focus(context.user_focus):
            return DetailLevel.FULL

        # Rule 7: Completed tasks at deep nesting get summary
        if context.task_status == 'completed' and context.depth_level >= 2:
            return DetailLevel.SUMMARY

        # Rule 8: Medium priority pending tasks get medium detail
        if context.task_status == 'pending' and 4.0 <= context.priority_score < 7.0:
            return DetailLevel.MEDIUM

        # Rule 9: Low priority or completed tasks get summary
        if context.priority_score < 4.0 or context.task_status == 'completed':
            return DetailLevel.SUMMARY

        # Default: medium detail
        return DetailLevel.MEDIUM

    def _matches_focus(self, user_focus: str) -> bool:
        """Check if current task matches user focus.

        Args:
            user_focus: User-specified focus area

        Returns:
            True if task matches focus
        """
        # TODO: Implement focus matching
        # Could check if task_id, parent phase, or file path matches focus
        return False

    def calculate_all_detail_levels(self) -> Dict[str, DetailLevel]:
        """Calculate detail levels for all tasks in spec.

        Returns:
            Dictionary mapping task_id to DetailLevel

        Example:
            >>> calculator = DetailLevelCalculator(spec_data)
            >>> levels = calculator.calculate_all_detail_levels()
            >>> for task_id, level in levels.items():
            ...     print(f"{task_id}: {level.value}")
        """
        levels = {}

        for task_id in self.hierarchy:
            if task_id == 'spec-root':
                continue

            levels[task_id] = self.calculate_detail_level(task_id)

        return levels

    def get_summary_tasks(self, max_count: int = 10) -> List[str]:
        """Get tasks that should be shown in summary view.

        Selects most important tasks based on status, priority, and risk.
        Useful for creating executive summaries or dashboards.

        Args:
            max_count: Maximum number of tasks to return

        Returns:
            List of task IDs for summary view

        Example:
            >>> calculator = DetailLevelCalculator(spec_data)
            >>> summary_tasks = calculator.get_summary_tasks(max_count=5)
            >>> print(f"Top 5 tasks: {summary_tasks}")
        """
        # Get all tasks with FULL detail level
        levels = self.calculate_all_detail_levels()
        full_detail_tasks = [
            task_id for task_id, level in levels.items()
            if level == DetailLevel.FULL
        ]

        # If we have too many, prioritize by status
        if len(full_detail_tasks) > max_count:
            # Sort by status priority: in_progress > blocked > pending > completed
            status_priority = {
                'in_progress': 4,
                'blocked': 3,
                'pending': 2,
                'completed': 1
            }

            def get_status_priority(task_id):
                task_data = self.hierarchy.get(task_id, {})
                status = task_data.get('status', 'pending')
                return status_priority.get(status, 0)

            full_detail_tasks.sort(key=get_status_priority, reverse=True)
            return full_detail_tasks[:max_count]

        return full_detail_tasks


class CollapsibleMarkdownGenerator:
    """Generates collapsible markdown sections for progressive disclosure.

    Creates markdown with summary/expand patterns that can be rendered
    as collapsible sections in viewers that support HTML details/summary
    or custom markdown extensions.

    Supports multiple output formats:
    - HTML details/summary tags (widely supported)
    - Markdown extension format (for tools like MkDocs)
    - Custom markers for post-processing
    """

    def __init__(self, detail_calculator: DetailLevelCalculator):
        """Initialize collapsible markdown generator.

        Args:
            detail_calculator: DetailLevelCalculator instance
        """
        self.calculator = detail_calculator

    def generate_collapsible_section(
        self,
        title: str,
        summary_content: str,
        full_content: str,
        detail_level: DetailLevel,
        format: str = 'html'
    ) -> str:
        """Generate collapsible markdown section.

        Args:
            title: Section title
            summary_content: Content shown in collapsed state
            full_content: Content shown when expanded
            detail_level: Current detail level
            format: Output format ('html', 'markdown', 'custom')

        Returns:
            Formatted markdown string

        Example:
            >>> generator = CollapsibleMarkdownGenerator(calculator)
            >>> section = generator.generate_collapsible_section(
            ...     title="Phase 2 Tasks",
            ...     summary_content="3/10 tasks completed",
            ...     full_content="Detailed task list...",
            ...     detail_level=DetailLevel.MEDIUM,
            ...     format='html'
            ... )
        """
        if detail_level == DetailLevel.FULL:
            # Show everything, no collapsing
            return f"### {title}\n\n{full_content}\n"

        elif detail_level == DetailLevel.SUMMARY:
            # Show only summary
            return f"### {title}\n\n{summary_content}\n"

        else:  # MEDIUM
            # Generate collapsible section
            if format == 'html':
                return self._generate_html_details(title, summary_content, full_content)
            elif format == 'markdown':
                return self._generate_markdown_extension(title, summary_content, full_content)
            else:  # custom
                return self._generate_custom_markers(title, summary_content, full_content)

    def _generate_html_details(
        self,
        title: str,
        summary_content: str,
        full_content: str
    ) -> str:
        """Generate HTML details/summary tags.

        Returns:
            HTML-formatted collapsible section
        """
        return f"""<details>
<summary><strong>{title}</strong> - {summary_content}</summary>

{full_content}

</details>
"""

    def _generate_markdown_extension(
        self,
        title: str,
        summary_content: str,
        full_content: str
    ) -> str:
        """Generate markdown extension format (MkDocs style).

        Returns:
            Markdown extension formatted section
        """
        return f"""??? note "{title} - {summary_content}"
    {full_content.replace(chr(10), chr(10) + '    ')}
"""

    def _generate_custom_markers(
        self,
        title: str,
        summary_content: str,
        full_content: str
    ) -> str:
        """Generate custom marker format for post-processing.

        Returns:
            Custom marker formatted section
        """
        return f"""<!-- COLLAPSIBLE_START: {title} -->
**{title}** - {summary_content}

<!-- EXPANDED_CONTENT -->
{full_content}
<!-- COLLAPSIBLE_END -->
"""
