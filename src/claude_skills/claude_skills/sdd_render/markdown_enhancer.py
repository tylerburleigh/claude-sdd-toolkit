"""Markdown enhancement injector for AI-enhanced spec rendering.

This module takes parsed markdown sections and injects AI-generated enhancements:
- Executive summary at the top
- Visualizations after objectives
- Narrative transitions between phases
- Insights in sidebar callouts
- Progressive disclosure markers

The enhancer coordinates with all AI analysis modules to create rich, enhanced markdown.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .markdown_parser import ParsedSpec, ParsedPhase, ParsedGroup, ParsedTask, MarkdownParser
from .executive_summary import ExecutiveSummaryGenerator
from .visualization_builder import VisualizationBuilder
from .narrative_enhancer import NarrativeEnhancer
from .insight_generator import InsightGenerator, Insight, InsightSeverity
from .spec_analyzer import SpecAnalyzer


@dataclass
class EnhancementOptions:
    """Options for markdown enhancement.

    Attributes:
        include_executive_summary: Include AI-generated executive summary
        include_visualizations: Include dependency graphs and progress charts
        include_narrative_transitions: Add narrative flow between phases
        include_insights: Add AI-generated insights and warnings
        include_progressive_disclosure: Add progressive disclosure markers
        executive_summary_agent: AI agent to use for summary (None = auto)
        max_insights: Maximum number of insights to include (0 = all)
        insight_severity_threshold: Minimum severity level to include
    """
    include_executive_summary: bool = True
    include_visualizations: bool = True
    include_narrative_transitions: bool = True
    include_insights: bool = True
    include_progressive_disclosure: bool = True
    executive_summary_agent: Optional[str] = None
    max_insights: int = 10
    insight_severity_threshold: str = "info"  # info, warning, critical


class MarkdownEnhancer:
    """Injects AI enhancements into parsed markdown sections.

    The enhancer takes parsed markdown (from MarkdownParser) and injects
    AI-generated content at strategic locations:

    1. Executive Summary (at top, after title):
       - AI-generated project overview
       - Quick stats and metrics
       - Key highlights and risks

    2. Visualizations (after objectives):
       - Dependency graph (Mermaid)
       - Progress chart
       - Timeline/Gantt chart

    3. Narrative Transitions (between phases):
       - Contextual explanations
       - Flow between phases
       - Implementation rationale

    4. Insights (in sidebar callouts):
       - Risk warnings
       - Time estimates
       - Next step recommendations
       - Dependency conflicts

    5. Progressive Disclosure (throughout):
       - Collapsible sections for details
       - Summary/detail toggles
       - Focused views

    Attributes:
        spec_data: Complete JSON spec dictionary
        parsed_spec: Parsed markdown structure
        options: Enhancement options
        summary_generator: Executive summary generator
        viz_builder: Visualization builder
        narrative_enhancer: Narrative enhancer
        insight_generator: Insight generator

    Example:
        >>> from claude_skills.sdd_render import MarkdownParser, MarkdownEnhancer
        >>>
        >>> # Parse base markdown
        >>> parser = MarkdownParser(base_markdown)
        >>> parsed_spec = parser.parse()
        >>>
        >>> # Enhance with AI content
        >>> enhancer = MarkdownEnhancer(spec_data, parsed_spec)
        >>> enhanced_markdown = enhancer.enhance()
        >>> print(enhanced_markdown)
    """

    def __init__(
        self,
        spec_data: Dict[str, Any],
        parsed_spec: ParsedSpec,
        options: Optional[EnhancementOptions] = None,
        *,
        model_override: Any = None,
    ):
        """Initialize markdown enhancer.

        Args:
            spec_data: Complete JSON spec dictionary
            parsed_spec: Parsed markdown structure from MarkdownParser
            options: Enhancement options (uses defaults if None)
        """
        self.spec_data = spec_data
        self.parsed_spec = parsed_spec
        self.options = options or EnhancementOptions()
        self.model_override = model_override

        # Initialize AI enhancement modules
        self.summary_generator = ExecutiveSummaryGenerator(
            spec_data,
            model_override=model_override,
        )
        self.viz_builder = VisualizationBuilder(spec_data)
        self.narrative_enhancer = NarrativeEnhancer(
            spec_data,
            model_override=model_override,
        )
        self.insight_generator = InsightGenerator(
            spec_data,
            analyzer=SpecAnalyzer(spec_data)
        )

    def enhance(self) -> str:
        """Generate enhanced markdown with all AI improvements.

        Returns:
            Complete enhanced markdown string

        Example:
            >>> enhancer = MarkdownEnhancer(spec_data, parsed_spec)
            >>> enhanced = enhancer.enhance()
            >>> with open('enhanced_spec.md', 'w') as f:
            ...     f.write(enhanced)
        """
        sections = []

        # 1. Header section (title, metadata)
        sections.append(self._render_enhanced_header())

        # 2. Executive summary (AI-generated)
        if self.options.include_executive_summary:
            exec_summary = self._generate_executive_summary()
            if exec_summary:
                sections.append(exec_summary)

        # 3. Quick stats/metrics
        sections.append(self._render_quick_stats())

        # 4. Objectives
        sections.append(self._render_objectives())

        # 5. Visualizations (after objectives)
        if self.options.include_visualizations:
            visualizations = self._generate_visualizations()
            if visualizations:
                sections.append(visualizations)

        # 6. Critical insights (top-level)
        if self.options.include_insights:
            critical_insights = self._render_critical_insights()
            if critical_insights:
                sections.append(critical_insights)

        # 7. Enhanced phases (with narratives and insights)
        sections.extend(self._render_enhanced_phases())

        return '\n\n'.join(sections)

    def _render_enhanced_header(self) -> str:
        """Render enhanced header with metadata."""
        spec = self.parsed_spec
        lines = [
            f"# {spec.title}",
            "",
            f"**Spec ID:** `{spec.spec_id}`  ",
            f"**Status:** {spec.status}  ",
            f"**Progress:** {spec.completed_tasks}/{spec.total_tasks} tasks ({spec.progress_pct:.0f}%)  ",
        ]

        if spec.estimated_hours:
            lines.append(f"**Estimated Effort:** {spec.estimated_hours} hours  ")

        if spec.complexity:
            lines.append(f"**Complexity:** {spec.complexity}  ")

        if spec.description:
            lines.extend(["", spec.description])

        return '\n'.join(lines)

    def _generate_executive_summary(self) -> Optional[str]:
        """Generate AI-powered executive summary.

        Returns:
            Executive summary markdown or None if generation fails
        """
        # Try to generate summary with AI
        success, summary = self.summary_generator.generate_summary_with_fallback()

        if not success:
            # Fallback: use metrics summary
            return self.summary_generator.format_metrics_summary()

        # Progressive disclosure removed - always show summary directly
        # Note: summary already includes its own "## Executive Summary: ..." header
        return summary

    def _render_quick_stats(self) -> str:
        """Render quick stats section."""
        return self.summary_generator.format_metrics_summary()

    def _render_objectives(self) -> str:
        """Render objectives section."""
        if not self.parsed_spec.objectives:
            return ""

        lines = ["## Objectives", ""]
        for obj in self.parsed_spec.objectives:
            lines.append(f"- {obj}")

        return '\n'.join(lines)

    def _generate_visualizations(self) -> Optional[str]:
        """Generate visualizations (dependency graph, progress chart, etc.).

        Returns:
            Visualization markdown or None if generation fails
        """
        viz_sections = []

        # Progress chart (already includes mermaid code block)
        try:
            progress_chart = self.viz_builder.build_progress_chart_mermaid()
            viz_sections.append(f"""### Progress Overview

{progress_chart}""")
        except Exception:
            # Fallback to ASCII if Mermaid fails
            try:
                progress_chart = self.viz_builder.build_progress_chart_ascii()
                viz_sections.append(f"""### Progress Overview

```
{progress_chart}
```""")
            except Exception:
                pass

        # Dependency graph (already includes mermaid code block)
        try:
            dep_graph = self.viz_builder.build_dependency_graph_mermaid(show_completed=False)
            viz_sections.append(f"""### Dependency Overview

{dep_graph}""")
        except Exception:
            pass

        if not viz_sections:
            return None

        # Progressive disclosure removed - always show visualizations directly
        header = "## Visualizations"
        return f"{header}\n\n" + '\n\n'.join(viz_sections)

    def _render_critical_insights(self) -> Optional[str]:
        """Render critical insights at top level.

        Returns:
            Critical insights markdown or None if no critical insights
        """
        # Generate all insights
        insights = self.insight_generator.generate_all_insights()

        # Filter for critical severity
        critical = [
            i for i in insights
            if i.severity.value == "critical"
        ]

        if not critical:
            return None

        lines = ["## ⚠️  Critical Insights", ""]

        for insight in critical[:5]:  # Limit to top 5
            lines.append(f"### {insight.title}")
            lines.append("")
            lines.append(insight.description)
            lines.append("")
            lines.append(f"**Recommendation:** {insight.recommendation}")
            lines.append("")

        return '\n'.join(lines)

    def _render_enhanced_phases(self) -> List[str]:
        """Render all phases with enhancements.

        Returns:
            List of enhanced phase markdown strings
        """
        enhanced_phases = []

        for i, phase in enumerate(self.parsed_spec.phases):
            # Add narrative transition before phase (except first)
            if i > 0 and self.options.include_narrative_transitions:
                transition = self._generate_phase_transition(
                    self.parsed_spec.phases[i-1],
                    phase
                )
                if transition:
                    enhanced_phases.append(transition)

            # Render enhanced phase
            enhanced_phases.append(self._render_enhanced_phase(phase))

        return enhanced_phases

    def _generate_phase_transition(
        self,
        prev_phase: ParsedPhase,
        next_phase: ParsedPhase
    ) -> Optional[str]:
        """Generate narrative transition between phases.

        Args:
            prev_phase: Previous phase
            next_phase: Next phase

        Returns:
            Transition markdown or None if generation fails
        """
        # Use narrative enhancer to generate transition
        transitions = self.narrative_enhancer.generate_phase_transitions()

        # Find transition for this phase
        for trans in transitions:
            if next_phase.title in trans.target_id or trans.target_id in next_phase.raw_markdown:
                return f"""---

_{trans.content}_

---"""

        # Fallback: simple connector
        return f"""---

_Having completed {prev_phase.title}, we now move to {next_phase.title}._

---"""

    def _render_enhanced_phase(self, phase: ParsedPhase) -> str:
        """Render enhanced phase with insights and progressive disclosure.

        Args:
            phase: Parsed phase object

        Returns:
            Enhanced phase markdown
        """
        # Calculate detail level for this phase
        from .progressive_disclosure import DetailLevelCalculator, DetailLevel

        detail_calculator = DetailLevelCalculator(self.spec_data)
        # Get phase ID from parsed phase (extract from title or raw markdown)
        phase_id = self._extract_phase_id(phase)
        detail_level = detail_calculator.calculate_detail_level(phase_id) if phase_id else DetailLevel.FULL

        lines = [
            f"## {phase.title} ({phase.completed_tasks}/{phase.total_tasks} tasks, {phase.progress_pct:.0f}%)",
            ""
        ]

        # Phase metadata
        if phase.purpose:
            lines.append(f"**Purpose:** {phase.purpose}  ")
        if phase.risk_level:
            lines.append(f"**Risk Level:** {phase.risk_level}  ")
        if phase.estimated_hours:
            lines.append(f"**Estimated Hours:** {phase.estimated_hours}  ")

        if any([phase.purpose, phase.risk_level, phase.estimated_hours]):
            lines.append("")

        # Phase-specific insights
        if self.options.include_insights:
            phase_insights = self._get_phase_insights(phase)
            if phase_insights:
                lines.append(phase_insights)
                lines.append("")

        # Apply progressive disclosure to phase content if enabled
        if self.options.include_progressive_disclosure and detail_level == DetailLevel.MEDIUM:
            # Wrap phase groups in collapsible section
            summary_content = f"{phase.completed_tasks}/{phase.total_tasks} tasks completed"

            group_lines = []
            for group in phase.groups:
                group_lines.append(self._render_group(group))

            full_content = '\n\n'.join(group_lines)

            # Progressive disclosure removed - show content directly
            lines.append(full_content)
        else:
            # Render groups normally (FULL or SUMMARY)
            for group in phase.groups:
                lines.append("")
                lines.append(self._render_group(group))

        return '\n'.join(lines)

    def _extract_phase_id(self, phase: ParsedPhase) -> Optional[str]:
        """Extract phase ID from parsed phase.

        Args:
            phase: Parsed phase object

        Returns:
            Phase ID or None if not found
        """
        # Try to extract phase ID from raw markdown or title
        # Look for patterns like "phase-1", "phase-2", etc.
        import re

        # Search in raw markdown first
        if phase.raw_markdown:
            match = re.search(r'(phase-\d+)', phase.raw_markdown, re.IGNORECASE)
            if match:
                return match.group(1)

        # Search in title
        if phase.title:
            match = re.search(r'(phase-\d+)', phase.title, re.IGNORECASE)
            if match:
                return match.group(1)

        # Try to find in hierarchy by matching title
        hierarchy = self.spec_data.get('hierarchy', {})
        for node_id, node_data in hierarchy.items():
            if node_data.get('type') == 'phase':
                node_title = node_data.get('title', '')
                if node_title and node_title.lower() in phase.title.lower():
                    return node_id

        return None

    def _extract_task_id(self, task: ParsedTask) -> Optional[str]:
        """Extract task ID from parsed task.

        Args:
            task: Parsed task object

        Returns:
            Task ID or None if not found
        """
        # Try to extract task ID from raw markdown or title
        # Look for patterns like "task-1-1", "task-2-3", etc.
        import re

        # Search in raw markdown first
        if hasattr(task, 'raw_markdown') and task.raw_markdown:
            match = re.search(r'(task-\d+-\d+(?:-\d+)?)', task.raw_markdown, re.IGNORECASE)
            if match:
                return match.group(1)

        # Search in title
        if task.title:
            match = re.search(r'(task-\d+-\d+(?:-\d+)?)', task.title, re.IGNORECASE)
            if match:
                return match.group(1)

        # Try to find in hierarchy by matching title
        hierarchy = self.spec_data.get('hierarchy', {})
        for node_id, node_data in hierarchy.items():
            if node_data.get('type') in ('task', 'subtask', 'verify'):
                node_title = node_data.get('title', '')
                if node_title and node_title.lower() == task.title.lower():
                    return node_id

        return None

    def _get_phase_insights(self, phase: ParsedPhase) -> Optional[str]:
        """Get insights specific to this phase.

        Args:
            phase: Parsed phase object

        Returns:
            Insights markdown or None
        """
        # Generate insights for all tasks in phase
        all_insights = self.insight_generator.generate_all_insights()

        # Filter insights relevant to this phase
        # (This is simplified - in production would match against phase task IDs)
        phase_insights = [
            i for i in all_insights
            if i.severity.value in ("warning", "critical")
        ][:3]  # Top 3 insights

        if not phase_insights:
            return None

        lines = ["> **Phase Insights:**"]
        for insight in phase_insights:
            lines.append(f"> - ⚠️  **{insight.title}**: {insight.description}")

        return '\n'.join(lines)

    def _render_group(self, group: ParsedGroup) -> str:
        """Render task group.

        Args:
            group: Parsed group object

        Returns:
            Group markdown
        """
        lines = [
            f"### {group.title} ({group.completed_tasks}/{group.total_tasks} tasks)",
            ""
        ]

        if group.blocked_by:
            lines.append(f"**Blocked by:** {', '.join(group.blocked_by)}  ")
            lines.append("")

        # Render tasks
        for task in group.tasks:
            lines.append(self._render_task(task))

        # Render verifications
        for verify in group.verifications:
            lines.append(self._render_verification(verify))

        return '\n'.join(lines)

    def _render_task(self, task: ParsedTask, level: int = 4) -> str:
        """Render task with enhancements and progressive disclosure.

        Args:
            task: Parsed task object
            level: Heading level

        Returns:
            Task markdown
        """
        from .progressive_disclosure import DetailLevelCalculator, DetailLevel

        heading = '#' * level
        status_icon = self._get_status_icon(task.status)

        # Calculate detail level for this task if progressive disclosure is enabled
        detail_level = DetailLevel.FULL
        task_id = self._extract_task_id(task)

        if self.options.include_progressive_disclosure and task_id:
            detail_calculator = DetailLevelCalculator(self.spec_data)
            detail_level = detail_calculator.calculate_detail_level(task_id)

        # Build summary line (always shown)
        summary_parts = [task.title]
        if task.file_path:
            summary_parts.append(f"`{task.file_path}`")
        if task.estimated_hours:
            summary_parts.append(f"({task.estimated_hours}h)")

        summary_line = f"{heading} {status_icon} {' - '.join(summary_parts)}"

        # For SUMMARY level, only show the heading
        if detail_level == DetailLevel.SUMMARY:
            lines = [summary_line, ""]

            # Still render subtasks if they exist
            for subtask in task.subtasks:
                lines.append(self._render_task(subtask, level=level + 1))

            return '\n'.join(lines)

        # Build detail content for MEDIUM/FULL levels
        detail_lines = []

        if task.file_path:
            detail_lines.append(f"**File:** `{task.file_path}`  ")

        detail_lines.append(f"**Status:** {task.status}  ")

        if task.estimated_hours:
            detail_lines.append(f"**Estimated:** {task.estimated_hours} hours  ")

        if task.changes:
            detail_lines.append(f"**Changes:** {task.changes}  ")

        if task.reasoning:
            detail_lines.append(f"**Reasoning:** {task.reasoning}  ")

        if task.details:
            detail_lines.extend(["", f"**Details:** {task.details}"])

        if task.depends_on:
            detail_lines.extend(["", f"**Depends on:** {', '.join(task.depends_on)}"])

        if task.blocked_by:
            detail_lines.extend(["", f"**Blocked by:** {', '.join(task.blocked_by)}"])

        # For MEDIUM level, wrap details in collapsible section
        if detail_level == DetailLevel.MEDIUM:
            lines = [summary_line, ""]

            # Progressive disclosure removed - show details directly
            detail_content = '\n'.join(detail_lines)
            lines.append(detail_content)

            # Render subtasks
            for subtask in task.subtasks:
                lines.append(self._render_task(subtask, level=level + 1))

            return '\n'.join(lines)

        # For FULL level, show everything normally
        lines = [summary_line, ""]
        lines.extend(detail_lines)
        lines.append("")

        # Render subtasks
        for subtask in task.subtasks:
            lines.append(self._render_task(subtask, level=level + 1))

        return '\n'.join(lines)

    def _render_verification(self, verify) -> str:
        """Render verification step.

        Args:
            verify: Parsed verification object

        Returns:
            Verification markdown
        """
        status_icon = self._get_status_icon(verify.status)

        lines = [
            f"#### {status_icon} {verify.title}",
            "",
            f"**Status:** {verify.status}  ",
            f"**Type:** {verify.verification_type}  "
        ]

        if verify.command:
            lines.extend([
                "",
                "**Command:**",
                "```bash",
                verify.command,
                "```"
            ])

        if verify.expected:
            lines.extend(["", f"**Expected:** {verify.expected}"])

        lines.append("")

        return '\n'.join(lines)

    def _get_status_icon(self, status: str) -> str:
        """Get icon for task status.

        Args:
            status: Task status string

        Returns:
            Icon character
        """
        icons = {
            'pending': '⏳',
            'in_progress': '🔄',
            'completed': '✅',
            'blocked': '🚫',
            'failed': '❌'
        }
        return icons.get(status, '❓')
