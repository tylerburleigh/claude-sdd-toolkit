"""Core rendering logic for converting JSON specs to markdown."""

from typing import Dict, Any, List, Optional
from pathlib import Path


class SpecRenderer:
    """Renders JSON spec data to human-readable markdown."""

    def __init__(self, spec_data: Dict[str, Any]):
        """Initialize renderer with spec data.

        Args:
            spec_data: Complete JSON spec dictionary
        """
        self.spec_data = spec_data
        self.hierarchy = spec_data.get('hierarchy', {})
        self.metadata = spec_data.get('metadata', {})
        self.spec_id = spec_data.get('spec_id', 'unknown')

    def to_markdown(self) -> str:
        """Generate complete markdown documentation.

        Returns:
            Formatted markdown string
        """
        sections = []

        # Header section
        sections.append(self._render_header())

        # Objectives section
        if self.metadata.get('objectives'):
            sections.append(self._render_objectives())

        # Phases section
        root = self.hierarchy.get('spec-root', {})
        phase_ids = root.get('children', [])

        for phase_id in phase_ids:
            sections.append(self._render_phase(phase_id))

        return '\n\n'.join(sections)

    def _render_header(self) -> str:
        """Render spec header with metadata."""
        root = self.hierarchy.get('spec-root', {})
        title = self.metadata.get('title') or root.get('title', 'Untitled Specification')
        status = root.get('status', 'pending')
        total_tasks = root.get('total_tasks', 0)
        completed_tasks = root.get('completed_tasks', 0)

        progress_pct = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        lines = [
            f"# {title}",
            "",
            f"**Spec ID:** `{self.spec_id}`  ",
            f"**Status:** {status} ({completed_tasks}/{total_tasks} tasks, {progress_pct:.0f}%)  ",
        ]

        if self.metadata.get('estimated_hours'):
            lines.append(f"**Estimated Effort:** {self.metadata['estimated_hours']} hours  ")

        if self.metadata.get('complexity'):
            lines.append(f"**Complexity:** {self.metadata['complexity']}  ")

        if self.metadata.get('description'):
            lines.extend([
                "",
                self.metadata['description']
            ])

        return '\n'.join(lines)

    def _render_objectives(self) -> str:
        """Render objectives section."""
        objectives = self.metadata.get('objectives', [])
        lines = ["## Objectives", ""]

        for obj in objectives:
            lines.append(f"- {obj}")

        return '\n'.join(lines)

    def _render_phase(self, phase_id: str) -> str:
        """Render a complete phase with all its tasks.

        Args:
            phase_id: ID of the phase node

        Returns:
            Formatted markdown for the phase
        """
        phase = self.hierarchy.get(phase_id, {})
        title = phase.get('title', 'Untitled Phase')
        total_tasks = phase.get('total_tasks', 0)
        completed_tasks = phase.get('completed_tasks', 0)
        progress_pct = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        phase_metadata = phase.get('metadata', {})

        lines = [
            f"## {title} ({completed_tasks}/{total_tasks} tasks, {progress_pct:.0f}%)",
            ""
        ]

        # Add phase metadata if available
        if phase_metadata.get('purpose'):
            lines.append(f"**Purpose:** {phase_metadata['purpose']}  ")
        if phase_metadata.get('risk_level'):
            lines.append(f"**Risk Level:** {phase_metadata['risk_level']}  ")
        if phase_metadata.get('estimated_hours'):
            lines.append(f"**Estimated Hours:** {phase_metadata['estimated_hours']}  ")

        if any([phase_metadata.get('purpose'), phase_metadata.get('risk_level'), phase_metadata.get('estimated_hours')]):
            lines.append("")

        # Render dependencies if any
        deps = phase.get('dependencies', {})
        if deps.get('blocked_by'):
            lines.append(f"**Blocked by:** {', '.join(deps['blocked_by'])}  ")
        if deps.get('depends'):
            lines.append(f"**Depends on:** {', '.join(deps['depends'])}  ")

        # Render child groups (file modifications, verification, etc.)
        group_ids = phase.get('children', [])
        for group_id in group_ids:
            lines.append("")
            lines.append(self._render_group(group_id))

        return '\n'.join(lines)

    def _render_group(self, group_id: str) -> str:
        """Render a task group (file modifications, verification, etc.).

        Args:
            group_id: ID of the group node

        Returns:
            Formatted markdown for the group
        """
        group = self.hierarchy.get(group_id, {})
        title = group.get('title', 'Tasks')
        total_tasks = group.get('total_tasks', 0)
        completed_tasks = group.get('completed_tasks', 0)

        lines = [
            f"### {title} ({completed_tasks}/{total_tasks} tasks)",
            ""
        ]

        # Render dependencies if any
        deps = group.get('dependencies', {})
        if deps.get('blocked_by'):
            lines.append(f"**Blocked by:** {', '.join(deps['blocked_by'])}  ")
            lines.append("")

        # Render child tasks
        task_ids = group.get('children', [])
        for task_id in task_ids:
            task = self.hierarchy.get(task_id, {})
            task_type = task.get('type', 'task')

            if task_type == 'verify':
                lines.append(self._render_verification(task_id))
            else:
                lines.append(self._render_task(task_id))

        return '\n'.join(lines)

    def _render_task(self, task_id: str, level: int = 4) -> str:
        """Render a task or subtask.

        Args:
            task_id: ID of the task node
            level: Heading level (4 for task, 5 for subtask, etc.)

        Returns:
            Formatted markdown for the task
        """
        task = self.hierarchy.get(task_id, {})
        title = task.get('title', 'Untitled Task')
        status = task.get('status', 'pending')
        task_metadata = task.get('metadata', {})

        heading = '#' * level
        status_icon = self._get_status_icon(status)

        lines = [
            f"{heading} {status_icon} {title}",
            ""
        ]

        # Add task metadata
        if task_metadata.get('file_path'):
            lines.append(f"**File:** `{task_metadata['file_path']}`  ")

        lines.append(f"**Status:** {status}  ")

        if task_metadata.get('estimated_hours'):
            lines.append(f"**Estimated:** {task_metadata['estimated_hours']} hours  ")

        if task_metadata.get('changes'):
            lines.append(f"**Changes:** {task_metadata['changes']}  ")

        if task_metadata.get('reasoning'):
            lines.append(f"**Reasoning:** {task_metadata['reasoning']}  ")

        if task_metadata.get('details'):
            details = task_metadata['details']
            lines.append("")
            if isinstance(details, list):
                lines.append("**Details:**")
                for detail in details:
                    lines.append(f"- {detail}")
            else:
                lines.append(f"**Details:** {details}")

        # Render dependencies
        deps = task.get('dependencies', {})
        if deps.get('depends'):
            lines.extend([
                "",
                f"**Depends on:** {', '.join(deps['depends'])}"
            ])
        if deps.get('blocked_by'):
            lines.extend([
                "",
                f"**Blocked by:** {', '.join(deps['blocked_by'])}"
            ])

        lines.append("")

        # Render subtasks if any
        subtask_ids = task.get('children', [])
        if subtask_ids:
            for subtask_id in subtask_ids:
                lines.append(self._render_task(subtask_id, level=level + 1))

        return '\n'.join(lines)

    def _render_verification(self, verify_id: str) -> str:
        """Render a verification step.

        Args:
            verify_id: ID of the verification node

        Returns:
            Formatted markdown for the verification
        """
        verify = self.hierarchy.get(verify_id, {})
        title = verify.get('title', 'Untitled Verification')
        status = verify.get('status', 'pending')
        verify_metadata = verify.get('metadata', {})

        status_icon = self._get_status_icon(status)

        lines = [
            f"#### {status_icon} {title}",
            "",
            f"**Status:** {status}  "
        ]

        verification_type = verify_metadata.get('verification_type', 'manual')
        lines.append(f"**Type:** {verification_type}  ")

        if verify_metadata.get('command'):
            lines.extend([
                "",
                "**Command:**",
                "```bash",
                verify_metadata['command'],
                "```"
            ])

        if verify_metadata.get('expected'):
            lines.extend([
                "",
                f"**Expected:** {verify_metadata['expected']}"
            ])

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
