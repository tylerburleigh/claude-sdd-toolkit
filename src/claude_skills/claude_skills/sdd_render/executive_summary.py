"""Executive summary generation for spec analysis.

This module generates executive summaries for SDD specifications using AI agents.
It creates concise overviews that help stakeholders quickly understand:
- Project objectives and scope
- Key phases and milestones
- Critical path and dependencies
- Estimated effort and timeline
- Major risks and blockers

The module uses AI prompts to generate natural language summaries from spec data,
making complex specifications accessible at-a-glance.
"""

from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import json
import inspect

from claude_skills.common import get_agent_priority, get_timeout, get_enabled_tools, consultation_limits
from claude_skills.common.ai_config import resolve_tool_model
from claude_skills.common import ai_tools
from claude_skills.common.ai_tools import ToolStatus


@dataclass
class ExecutiveSummary:
    """An executive summary for a specification.

    Attributes:
        objectives: High-level project objectives and goals
        scope: Project scope and boundaries
        key_phases: Summary of major phases and milestones
        critical_path: Critical path tasks and dependencies
        estimated_effort: Total estimated hours and timeline
        major_risks: Key risks and mitigation strategies
        next_steps: Recommended immediate actions
        metadata: Additional summary metadata
    """
    objectives: str
    scope: str
    key_phases: str
    critical_path: str
    estimated_effort: str
    major_risks: str
    next_steps: str
    metadata: Dict[str, Any]


class ExecutiveSummaryGenerator:
    """Generates executive summaries for SDD specifications.

    This class uses AI prompts to analyze spec data and generate concise,
    natural language summaries suitable for stakeholders and quick reviews.

    The generator creates prompts that ask an AI agent to:
    - Summarize project objectives and scope
    - Identify key phases and milestones
    - Analyze critical path and dependencies
    - Estimate effort and timeline
    - Highlight major risks and blockers
    - Recommend next steps

    Attributes:
        spec_data: Complete JSON spec dictionary
        metadata: Spec metadata including title, version, dates

    Example:
        >>> from claude_skills.sdd_render import ExecutiveSummaryGenerator
        >>> import json
        >>>
        >>> with open('specs/active/my-spec.json') as f:
        ...     spec_data = json.load(f)
        >>>
        >>> generator = ExecutiveSummaryGenerator(spec_data)
        >>> prompt = generator.build_summary_prompt()
        >>> # Pass prompt to AI agent to generate summary
        >>> # summary = agent.run(prompt, spec_data)
    """

    def __init__(self, spec_data: Dict[str, Any], *, model_override: Any = None):
        """Initialize executive summary generator.

        Args:
            spec_data: Complete JSON spec dictionary
        """
        self.spec_data = spec_data
        self.metadata = spec_data.get('metadata', {})
        self.hierarchy = spec_data.get('hierarchy', {})
        self.model_override = model_override

    def build_summary_prompt(self) -> str:
        """Build AI prompt template for generating executive summary.

        Creates a structured prompt that asks the AI agent to analyze the spec
        and generate a concise executive summary covering:
        - Objectives: What the project aims to achieve
        - Scope: What's included and excluded
        - Key phases: Major milestones and deliverables
        - Critical path: Dependencies and blocking tasks
        - Estimated effort: Time and resource requirements
        - Major risks: Potential blockers and mitigation strategies

        Returns:
            Formatted prompt string ready for AI agent

        Example:
            >>> generator = ExecutiveSummaryGenerator(spec_data)
            >>> prompt = generator.build_summary_prompt()
            >>> print(prompt[:100])
            Generate an executive summary for this software development specification...
        """
        prompt = """Generate an executive summary for this software development specification.

Analyze the provided spec data and create a concise overview suitable for stakeholders and quick reviews.

Your summary should include:

1. **Objectives** (2-3 sentences)
   - What does this project aim to achieve?
   - What problem does it solve?
   - What are the key deliverables?

2. **Scope** (2-3 sentences)
   - What's included in this specification?
   - What's explicitly out of scope?
   - What are the boundaries and constraints?

3. **Key Phases** (3-5 bullet points)
   - List the major phases with their primary goals
   - Note key milestones and deliverables for each phase
   - Indicate estimated effort per phase

4. **Critical Path** (2-3 sentences)
   - Which tasks are on the critical path?
   - What are the key dependencies?
   - Where are the potential bottlenecks?

5. **Estimated Effort** (2-3 sentences)
   - Total estimated hours/days
   - Current progress percentage
   - Expected completion timeline
   - Resource requirements

6. **Major Risks** (3-5 bullet points)
   - Identify high-risk tasks or areas
   - Note external dependencies or blockers
   - Highlight technical complexity concerns
   - Suggest mitigation strategies

7. **Next Steps** (2-4 bullet points)
   - What should be done immediately?
   - What are the recommended priorities?
   - Are there any blockers to resolve first?

Format the summary in clear, professional markdown. Use:
- Clear section headers (##)
- Bullet points for lists
- **Bold** for emphasis on key points
- Concise language (avoid jargon where possible)

Keep the entire summary under 500 words to ensure it's truly an "executive summary" -
quick to read and understand.

Base your analysis on the spec data provided, including:
- hierarchy: Task structure and dependencies
- metadata: Project information, estimates, risks
- Current progress and status
"""
        return prompt

    def extract_key_metrics(self) -> Dict[str, Any]:
        """Extract key metrics from spec for executive summary.

        Extracts at-a-glance metrics that are commonly needed in summaries:
        - Total tasks vs completed tasks
        - Number of phases
        - Total estimated hours
        - Tasks by status (pending, in_progress, blocked, completed)
        - High-risk task count
        - Critical path length

        Returns:
            Dictionary of key metrics

        Example:
            >>> generator = ExecutiveSummaryGenerator(spec_data)
            >>> metrics = generator.extract_key_metrics()
            >>> print(f"Progress: {metrics['completed_tasks']}/{metrics['total_tasks']}")
            Progress: 15/45
        """
        # Get root node to calculate totals
        root = self.hierarchy.get('spec-root', {})
        total_tasks = root.get('total_tasks', 0)
        completed_tasks = root.get('completed_tasks', 0)

        # Count phases
        phases = [
            task_id for task_id, task_data in self.hierarchy.items()
            if task_data.get('type') == 'phase'
        ]
        phase_count = len(phases)

        # Calculate estimated hours
        total_hours = 0.0
        completed_hours = 0.0
        pending_hours = 0.0
        in_progress_hours = 0.0

        # Count tasks by status
        status_counts = {
            'pending': 0,
            'in_progress': 0,
            'blocked': 0,
            'completed': 0
        }

        # Count high-risk tasks
        high_risk_count = 0

        for task_id, task_data in self.hierarchy.items():
            if task_id == 'spec-root':
                continue

            # Skip non-task nodes
            if task_data.get('type') not in ('task', 'subtask', 'verify'):
                continue

            # Get status
            status = task_data.get('status', 'pending')
            if status in status_counts:
                status_counts[status] += 1

            # Get estimated hours
            metadata = task_data.get('metadata', {})
            hours = metadata.get('estimated_hours', 0)
            total_hours += hours

            if status == 'completed':
                completed_hours += hours
            elif status == 'pending':
                pending_hours += hours
            elif status == 'in_progress':
                in_progress_hours += hours

            # Check for high-risk tasks
            risk_level = metadata.get('risk_level', '')
            if risk_level == 'high':
                high_risk_count += 1

        # Calculate progress percentage
        progress_pct = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': status_counts['pending'],
            'in_progress_tasks': status_counts['in_progress'],
            'blocked_tasks': status_counts['blocked'],
            'progress_percentage': round(progress_pct, 1),
            'phase_count': phase_count,
            'total_estimated_hours': round(total_hours, 1),
            'completed_hours': round(completed_hours, 1),
            'pending_hours': round(pending_hours, 1),
            'in_progress_hours': round(in_progress_hours, 1),
            'high_risk_task_count': high_risk_count,
            'spec_title': self.metadata.get('title', 'Untitled Spec'),
            'spec_version': self.metadata.get('version', '1.0.0'),
            'created_date': self.metadata.get('created_at', ''),
            'last_updated': self.metadata.get('updated_at', '')
        }

    def format_metrics_summary(self) -> str:
        """Format key metrics as a markdown summary block.

        Creates a formatted markdown block with key metrics that can be
        included at the top of an executive summary for quick reference.

        Returns:
            Formatted markdown string with metrics

        Example:
            >>> generator = ExecutiveSummaryGenerator(spec_data)
            >>> print(generator.format_metrics_summary())
            ### Quick Stats

            - **Progress**: 15/45 tasks (33.3%)
            - **Phases**: 4 phases
            ...
        """
        metrics = self.extract_key_metrics()

        summary = "### Quick Stats\n\n"
        summary += f"- **Progress**: {metrics['completed_tasks']}/{metrics['total_tasks']} tasks "
        summary += f"({metrics['progress_percentage']}%)\n"
        summary += f"- **Phases**: {metrics['phase_count']} phases\n"
        summary += f"- **Estimated Effort**: {metrics['total_estimated_hours']} hours total\n"
        summary += f"  - Completed: {metrics['completed_hours']}h\n"
        summary += f"  - In Progress: {metrics['in_progress_hours']}h\n"
        summary += f"  - Remaining: {metrics['pending_hours']}h\n"
        summary += f"- **Status Breakdown**:\n"
        summary += f"  - ✅ Completed: {metrics['completed_tasks']}\n"
        summary += f"  - 🔄 In Progress: {metrics['in_progress_tasks']}\n"
        summary += f"  - ⏸️  Pending: {metrics['pending_tasks']}\n"
        summary += f"  - 🚧 Blocked: {metrics['blocked_tasks']}\n"

        if metrics['high_risk_task_count'] > 0:
            summary += f"- **High-Risk Tasks**: {metrics['high_risk_task_count']} require extra attention\n"

        return summary

    def generate_summary_context(self) -> Dict[str, Any]:
        """Generate complete context for AI summary generation.

        Combines the summary prompt with key metrics and spec data to create
        a complete context package for AI agent invocation.

        Returns:
            Dictionary with prompt, metrics, and spec data

        Example:
            >>> generator = ExecutiveSummaryGenerator(spec_data)
            >>> context = generator.generate_summary_context()
            >>> # Pass to AI agent
            >>> # summary = agent.run(context['prompt'], context['spec_data'])
        """
        return {
            'prompt': self.build_summary_prompt(),
            'metrics': self.extract_key_metrics(),
            'metrics_summary': self.format_metrics_summary(),
            'spec_data': self.spec_data,
            'metadata': self.metadata
        }

    def get_available_agents(self) -> List[str]:
        """Check which AI CLI tools are available.

        Checks for availability of external AI agents (gemini, codex, cursor-agent)
        that can be used to generate summaries.

        Returns:
            List of available agent names

        Example:
            >>> generator = ExecutiveSummaryGenerator(spec_data)
            >>> agents = generator.get_available_agents()
            >>> print(f"Available agents: {', '.join(agents)}")
            Available agents: gemini, cursor-agent
        """
        return ai_tools.get_enabled_and_available_tools("sdd-render")

    def _resolve_model(self, agent: str, *, feature: str) -> Optional[str]:
        return resolve_tool_model(
            "sdd-render",
            agent,
            override=self.model_override,
            context={"feature": feature},
        )

    def _invoke_agent(
        self,
        agent: str,
        prompt: str,
        *,
        feature: str,
        timeout: int,
        tracker: Optional[consultation_limits.ConsultationTracker] = None,
    ):
        model = self._resolve_model(agent, feature=feature)
        executor = ai_tools.execute_tool_with_fallback
        params = inspect.signature(executor).parameters
        if "skill_name" in params:
            return executor(
                skill_name="sdd-render",
                tool=agent,
                prompt=prompt,
                model=model,
                timeout=timeout,
                context={"feature": feature},
                tracker=tracker,
            )
        return executor(
            agent,
            prompt,
            model=model,
            timeout=timeout,
        )

    @staticmethod
    def _format_failure(agent: str, response, timeout: int) -> str:
        if response.status == ToolStatus.TIMEOUT:
            return f"{agent} timed out after {timeout} seconds"
        if response.status == ToolStatus.NOT_FOUND:
            return f"{agent} provider is not available. Install the CLI or configure the provider registry."
        return response.error or f"{agent} returned status {response.status.value}"

    def generate_summary(
        self,
        agent: Optional[str] = None,
        dry_run: bool = False
    ) -> Tuple[bool, str]:
        """Generate executive summary using an AI agent.

        Calls an external AI CLI tool with the summary prompt and spec data
        to generate a natural language executive summary.

        Args:
            agent: Specific agent to use (cursor-agent, gemini, codex).
                  If None, uses first available agent.
            dry_run: If True, returns the command that would be run without executing

        Returns:
            Tuple of (success: bool, summary_markdown: str)

        Example:
            >>> generator = ExecutiveSummaryGenerator(spec_data)
            >>>
            >>> # Use default agent
            >>> success, summary = generator.generate_summary()
            >>> if success:
            ...     print(summary)
            >>>
            >>> # Use specific agent
            >>> success, summary = generator.generate_summary(agent="gemini")
            >>>
            >>> # Dry run to see command
            >>> success, cmd = generator.generate_summary(dry_run=True)
            >>> print(f"Would run: {cmd}")
        """
        # Determine which agent to use
        available = self.get_available_agents()

        if not available:
            return False, "No AI agents available. Install cursor-agent, gemini, or codex."

        if agent and agent not in available:
            return False, f"Agent '{agent}' not available. Available: {', '.join(available)}"

        agent_to_use = agent if agent else available[0]

        # Build the full prompt with context
        base_prompt = self.build_summary_prompt()
        metrics_summary = self.format_metrics_summary()

        # Add spec data as JSON context
        spec_json = json.dumps(self.spec_data, indent=2)

        full_prompt = f"""{base_prompt}

## Spec Data (JSON)

```json
{spec_json}
```

## Current Metrics

{metrics_summary}

---

Please analyze the above spec data and generate the executive summary following the structure outlined.
"""

        timeout = get_timeout('sdd-render', 'default')

        if dry_run:
            model_note = self._resolve_model(agent_to_use, feature="executive_summary") or "default model"
            return True, (
                f"Would consult {agent_to_use} (model={model_note}) "
                f"with prompt length {len(full_prompt)} chars [timeout={timeout}s]"
            )

        response = self._invoke_agent(
            agent_to_use,
            full_prompt,
            feature="executive_summary",
            timeout=timeout,
        )

        if response.success:
            return True, response.output

        return False, self._format_failure(agent_to_use, response, timeout)

    def generate_summary_with_fallback(self) -> Tuple[bool, str]:
        """Generate summary with automatic fallback to available agents.

        Tries agents in config priority order until one succeeds.
        If all fail, returns formatted metrics summary as fallback.

        Returns:
            Tuple of (success: bool, summary_markdown: str)

        Example:
            >>> generator = ExecutiveSummaryGenerator(spec_data)
            >>> success, summary = generator.generate_summary_with_fallback()
            >>> print(summary)
        """
        # Get priority order from config
        priority_order = get_agent_priority('sdd-render')
        available = self.get_available_agents()

        for agent in priority_order:
            if agent in available:
                success, output = self.generate_summary(agent=agent)
                if success:
                    return True, output

        # Fallback: return metrics summary if no agents work
        enabled_tools = get_enabled_tools('sdd-render')
        tool_names = ', '.join(enabled_tools.keys())

        fallback = f"""# Executive Summary

## Overview

*AI-generated summary not available. See metrics below.*

{self.format_metrics_summary()}

**Note**: Install an AI agent ({tool_names}) for full executive summaries.
"""
        return False, fallback
