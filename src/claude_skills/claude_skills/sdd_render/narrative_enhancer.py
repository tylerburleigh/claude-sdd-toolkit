"""Narrative enhancement for spec rendering.

This module uses AI to enhance spec readability by adding narrative flow:
- Transitional text between phases
- Dependency rationale explanations
- Implementation order suggestions
- Context for architectural decisions

Transforms dry technical specs into engaging, story-like documents.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import json
import inspect

from claude_skills.common import get_agent_priority, get_timeout, get_enabled_tools, consultation_limits
from claude_skills.common.ai_config import resolve_tool_model
from claude_skills.common import ai_tools


@dataclass
class NarrativeElement:
    """A narrative element to enhance spec readability.

    Attributes:
        element_type: Type of narrative (transition, rationale, suggestion, context)
        content: Generated narrative text
        location: Where to insert (before_phase, after_task, etc.)
        target_id: ID of phase/task to insert near
        metadata: Additional context
    """
    element_type: str
    content: str
    location: str
    target_id: str
    metadata: Dict[str, Any]


class NarrativeEnhancer:
    """Enhances specs with AI-generated narrative elements.

    The enhancer uses AI agents to generate contextual narrative that makes
    specs more readable and engaging. Instead of dry lists of tasks, specs
    become stories that explain the "why" behind decisions.

    Narrative Types:

    1. Phase Transitions:
       - Connect phases with explanatory text
       - Explain why this phase follows the previous
       - Set context for upcoming work

    2. Dependency Rationale:
       - Explain why tasks depend on each other
       - Clarify technical reasons for ordering
       - Highlight architectural relationships

    3. Implementation Order Suggestions:
       - Recommend optimal task sequencing
       - Explain parallelization opportunities
       - Suggest quick wins vs. foundational work

    4. Decision Context:
       - Explain architectural choices
       - Provide historical context
       - Highlight trade-offs made

    Attributes:
        spec_data: Complete JSON spec dictionary
        hierarchy: Task hierarchy from spec
        metadata: Spec metadata

    Example:
        >>> from claude_skills.sdd_render import NarrativeEnhancer
        >>> enhancer = NarrativeEnhancer(spec_data)
        >>> transitions = enhancer.generate_phase_transitions()
        >>> for trans in transitions:
        ...     print(f"{trans.target_id}: {trans.content}")
    """

    def __init__(self, spec_data: Dict[str, Any], *, model_override: Any = None):
        """Initialize narrative enhancer.

        Args:
            spec_data: Complete JSON spec dictionary
        """
        self.spec_data = spec_data
        self.hierarchy = spec_data.get('hierarchy', {})
        self.metadata = spec_data.get('metadata', {})
        self.model_override = model_override

    def generate_phase_transitions(self) -> List[NarrativeElement]:
        """Generate transitional text between phases.

        Uses AI to create smooth transitions that explain the flow from one
        phase to the next.

        Returns:
            List of NarrativeElement objects for phase transitions

        Example:
            >>> enhancer = NarrativeEnhancer(spec_data)
            >>> transitions = enhancer.generate_phase_transitions()
            >>> for trans in transitions:
            ...     print(trans.content)
        """
        root = self.hierarchy.get('spec-root', {})
        phase_ids = root.get('children', [])

        transitions = []

        for i, phase_id in enumerate(phase_ids):
            if i == 0:
                # First phase - introduce what's coming
                prompt = self._build_phase_intro_prompt(phase_id)
            else:
                # Subsequent phases - transition from previous
                prev_phase_id = phase_ids[i - 1]
                prompt = self._build_phase_transition_prompt(prev_phase_id, phase_id)

            # Generate narrative (would use AI agent)
            narrative = self._generate_narrative_ai(prompt)

            transitions.append(NarrativeElement(
                element_type='phase_transition',
                content=narrative,
                location='before_phase',
                target_id=phase_id,
                metadata={'phase_index': i}
            ))

        return transitions

    def _build_phase_intro_prompt(self, phase_id: str) -> str:
        """Build prompt for phase introduction.

        Args:
            phase_id: Phase identifier

        Returns:
            Prompt string for AI generation
        """
        phase_data = self.hierarchy.get(phase_id, {})
        phase_title = phase_data.get('title', phase_id)
        spec_title = self.metadata.get('title', 'this specification')

        return f"""Generate a brief (2-3 sentences) introduction for the first phase of {spec_title}.

Phase: {phase_title}

Context:
- This is the opening phase of the implementation
- Set expectations for what will be built
- Explain why this phase comes first

Write in a clear, professional tone. Focus on the "why" and "what", not implementation details.
"""

    def _build_phase_transition_prompt(self, prev_phase_id: str, next_phase_id: str) -> str:
        """Build prompt for phase transition.

        Args:
            prev_phase_id: Previous phase ID
            next_phase_id: Next phase ID

        Returns:
            Prompt string for AI generation
        """
        prev_phase = self.hierarchy.get(prev_phase_id, {})
        next_phase = self.hierarchy.get(next_phase_id, {})

        prev_title = prev_phase.get('title', prev_phase_id)
        next_title = next_phase.get('title', next_phase_id)

        return f"""Generate a brief (2-3 sentences) transition from one phase to the next.

Previous Phase: {prev_title}
Next Phase: {next_title}

Context:
- Explain how the previous phase sets up this one
- Highlight the logical progression
- Maintain narrative flow

Write in a clear, professional tone. Connect the phases smoothly.
"""

    def generate_dependency_rationales(self) -> List[NarrativeElement]:
        """Generate explanations for task dependencies.

        Uses AI to explain why tasks depend on each other, making the
        technical architecture more understandable.

        Returns:
            List of NarrativeElement objects explaining dependencies

        Example:
            >>> enhancer = NarrativeEnhancer(spec_data)
            >>> rationales = enhancer.generate_dependency_rationales()
            >>> for rat in rationales:
            ...     print(f"Task {rat.target_id}: {rat.content}")
        """
        rationales = []

        for task_id, task_data in self.hierarchy.items():
            if task_id == 'spec-root':
                continue

            if task_data.get('type') not in ('task', 'subtask'):
                continue

            dependencies = task_data.get('dependencies', {})
            blocked_by = dependencies.get('blocked_by', [])

            # Only generate rationale if task has dependencies
            if len(blocked_by) > 0:
                prompt = self._build_dependency_rationale_prompt(task_id, blocked_by)
                narrative = self._generate_narrative_ai(prompt)

                rationales.append(NarrativeElement(
                    element_type='dependency_rationale',
                    content=narrative,
                    location='after_task_title',
                    target_id=task_id,
                    metadata={'dependency_count': len(blocked_by)}
                ))

        return rationales

    def _build_dependency_rationale_prompt(self, task_id: str, blocked_by: List[str]) -> str:
        """Build prompt for dependency rationale.

        Args:
            task_id: Task identifier
            blocked_by: List of task IDs this task depends on

        Returns:
            Prompt string for AI generation
        """
        task_data = self.hierarchy.get(task_id, {})
        task_title = task_data.get('title', task_id)

        dep_titles = []
        for dep_id in blocked_by[:3]:  # Limit to 3 for brevity
            dep_data = self.hierarchy.get(dep_id, {})
            dep_titles.append(dep_data.get('title', dep_id))

        deps_str = ', '.join(dep_titles)

        return f"""Explain in 1-2 sentences why this task depends on its prerequisites.

Task: {task_title}
Depends on: {deps_str}

Explain the technical or logical reason for this dependency. Keep it concise and clear.
"""

    def generate_implementation_suggestions(self) -> List[NarrativeElement]:
        """Generate AI suggestions for implementation order.

        Analyzes the spec and provides strategic suggestions about task ordering,
        parallelization, and prioritization.

        Returns:
            List of NarrativeElement objects with implementation suggestions

        Example:
            >>> enhancer = NarrativeEnhancer(spec_data)
            >>> suggestions = enhancer.generate_implementation_suggestions()
        """
        # Get phase information
        root = self.hierarchy.get('spec-root', {})
        phase_ids = root.get('children', [])

        suggestions = []

        for phase_id in phase_ids:
            phase_data = self.hierarchy.get(phase_id, {})
            phase_title = phase_data.get('title', phase_id)

            # Get phase tasks
            tasks = self._get_phase_tasks(phase_id)

            if len(tasks) > 0:
                prompt = self._build_implementation_suggestion_prompt(phase_title, tasks)
                narrative = self._generate_narrative_ai(prompt)

                suggestions.append(NarrativeElement(
                    element_type='implementation_suggestion',
                    content=narrative,
                    location='after_phase_intro',
                    target_id=phase_id,
                    metadata={'task_count': len(tasks)}
                ))

        return suggestions

    def _build_implementation_suggestion_prompt(
        self,
        phase_title: str,
        tasks: List[Tuple[str, Dict[str, Any]]]
    ) -> str:
        """Build prompt for implementation suggestions.

        Args:
            phase_title: Phase title
            tasks: List of (task_id, task_data) tuples

        Returns:
            Prompt string for AI generation
        """
        task_list = []
        for task_id, task_data in tasks[:5]:  # Limit to 5 for prompt size
            title = task_data.get('title', task_id)
            task_list.append(f"- {title}")

        tasks_str = '\n'.join(task_list)

        return f"""Provide a brief (2-3 sentences) strategic suggestion for implementing this phase.

Phase: {phase_title}

Key Tasks:
{tasks_str}

Suggest:
- Optimal starting point
- Parallel work opportunities
- Quick wins vs. foundational work

Keep it actionable and concise.
"""

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

        return tasks

    def _generate_narrative_ai(self, prompt: str, dry_run: bool = False) -> str:
        """Generate narrative using AI agent.

        Args:
            prompt: Prompt for AI generation
            dry_run: If True, return placeholder instead of calling AI

        Returns:
            Generated narrative text
        """
        if dry_run:
            return "[AI-generated narrative would appear here]"

        # Get agent priority from config
        agent_priority = get_agent_priority('sdd-render')
        available_agents = self._get_available_agents()

        # Filter priority list to only available agents
        enabled_available = [
            agent for agent in agent_priority
            if agent in available_agents
        ]

        if not enabled_available:
            # Fallback: return placeholder
            enabled_tools = get_enabled_tools('sdd-render')
            tool_names = ', '.join(enabled_tools.keys())
            return f"*AI narrative generation unavailable. Install {tool_names} for enhanced narratives.*"

        # Try agents in priority order until one succeeds
        for agent in enabled_available:
            try:
                timeout = get_timeout('sdd-render', 'narrative')

                response = self._invoke_agent(
                    agent,
                    prompt,
                    feature="narrative",
                    timeout=timeout,
                )

                if response.success:
                    return response.output.strip()

            except Exception:
                # Try next agent on unexpected errors
                continue

        # All agents failed
        return "*AI narrative generation failed*"

    def _get_available_agents(self) -> List[str]:
        """Check which AI agents are available.

        Returns:
            List of available agent names
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

    def enhance_spec_narrative(self) -> Dict[str, List[NarrativeElement]]:
        """Generate all narrative enhancements for the spec.

        Returns:
            Dictionary mapping enhancement_type to list of NarrativeElements

        Example:
            >>> enhancer = NarrativeEnhancer(spec_data)
            >>> narratives = enhancer.enhance_spec_narrative()
            >>> for ntype, elements in narratives.items():
            ...     print(f"{ntype}: {len(elements)} elements")
        """
        return {
            'phase_transitions': self.generate_phase_transitions(),
            'dependency_rationales': self.generate_dependency_rationales(),
            'implementation_suggestions': self.generate_implementation_suggestions()
        }

    def apply_narratives_to_markdown(
        self,
        base_markdown: str,
        narratives: Dict[str, List[NarrativeElement]]
    ) -> str:
        """Apply narrative enhancements to existing markdown.

        Args:
            base_markdown: Original markdown content
            narratives: Dictionary of narrative enhancements

        Returns:
            Enhanced markdown with narratives inserted

        Example:
            >>> enhancer = NarrativeEnhancer(spec_data)
            >>> narratives = enhancer.enhance_spec_narrative()
            >>> enhanced = enhancer.apply_narratives_to_markdown(base_md, narratives)
        """
        # TODO: Implement markdown insertion logic
        # Would need to parse markdown and insert narratives at appropriate locations
        # For now, return base markdown unchanged
        return base_markdown
