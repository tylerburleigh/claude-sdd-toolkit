"""Centralized AI prompt templates for spec rendering.

This module provides all AI prompt templates used throughout the sdd-render
system, maintaining consistency in prompt engineering across different features.

Prompt Categories:
- Executive Summary Generation
- Narrative Enhancement
- Insight Extraction
- Risk Analysis
- Phase Planning
- Task Recommendations

All prompts follow best practices:
- Clear, specific instructions
- Structured output format
- Contextual information included
- Concise and actionable
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """A reusable AI prompt template.

    Attributes:
        name: Unique identifier for the prompt
        category: Category (summary, narrative, insight, risk, etc.)
        template: Template string with {placeholders}
        required_vars: List of required variable names
        optional_vars: List of optional variable names
        output_format: Expected output format description
        example_output: Example of expected output
    """
    name: str
    category: str
    template: str
    required_vars: List[str]
    optional_vars: List[str]
    output_format: str
    example_output: str


class AIPromptLibrary:
    """Central library of AI prompts for spec rendering.

    This class provides access to all AI prompts used in the sdd-render system,
    ensuring consistency and maintainability of prompt engineering.

    Usage:
        >>> library = AIPromptLibrary()
        >>> prompt = library.get_prompt('executive_summary')
        >>> filled = library.fill_prompt('executive_summary', spec_data=spec)
        >>> # Use filled prompt with AI agent
    """

    def __init__(self):
        """Initialize prompt library with all templates."""
        self.prompts: Dict[str, PromptTemplate] = {}
        self._load_all_prompts()

    def _load_all_prompts(self):
        """Load all prompt templates into the library."""
        # Executive Summary prompts
        self._register_executive_summary_prompts()

        # Narrative Enhancement prompts
        self._register_narrative_prompts()

        # Insight Extraction prompts
        self._register_insight_prompts()

        # Risk Analysis prompts
        self._register_risk_prompts()

        # Task Recommendation prompts
        self._register_task_prompts()

    def _register_executive_summary_prompts(self):
        """Register executive summary prompt templates."""
        self.prompts['executive_summary'] = PromptTemplate(
            name='executive_summary',
            category='summary',
            template="""Generate an executive summary for this software development specification.

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

## Spec Data (JSON)

```json
{spec_json}
```

## Current Metrics

{metrics_summary}

---

Please analyze the above spec data and generate the executive summary following the structure outlined.""",
            required_vars=['spec_json', 'metrics_summary'],
            optional_vars=[],
            output_format='Markdown with sections: Objectives, Scope, Key Phases, Critical Path, Estimated Effort, Major Risks, Next Steps',
            example_output="""## Objectives

This specification aims to implement a comprehensive user authentication system...

## Scope

Includes: OAuth 2.0 integration, JWT token management...
Excludes: Social media login, biometric authentication...

## Key Phases

- **Phase 1**: Foundation (8 hours) - Core authentication models and database schema
- **Phase 2**: API Layer (12 hours) - REST endpoints for login, logout, refresh
..."""
        )

    def _register_narrative_prompts(self):
        """Register narrative enhancement prompt templates."""
        self.prompts['phase_transition'] = PromptTemplate(
            name='phase_transition',
            category='narrative',
            template="""Generate a brief (2-3 sentences) transition from one phase to the next.

Previous Phase: {prev_phase_title}
Next Phase: {next_phase_title}

Context:
- Explain how the previous phase sets up this one
- Highlight the logical progression
- Maintain narrative flow

Write in a clear, professional tone. Connect the phases smoothly.""",
            required_vars=['prev_phase_title', 'next_phase_title'],
            optional_vars=[],
            output_format='2-3 sentences of transitional narrative',
            example_output='With the foundation in place from Phase 1, we now turn our attention to the API layer. This phase builds directly on the authentication models we created, exposing them through secure REST endpoints.'
        )

        self.prompts['phase_introduction'] = PromptTemplate(
            name='phase_introduction',
            category='narrative',
            template="""Generate a brief (2-3 sentences) introduction for the first phase.

Phase: {phase_title}
Spec: {spec_title}

Context:
- This is the opening phase of the implementation
- Set expectations for what will be built
- Explain why this phase comes first

Write in a clear, professional tone. Focus on the "why" and "what", not implementation details.""",
            required_vars=['phase_title', 'spec_title'],
            optional_vars=[],
            output_format='2-3 sentences introducing the phase',
            example_output='Phase 1 establishes the foundation for our authentication system. We begin here because all subsequent features depend on having a solid data model and core authentication primitives in place.'
        )

        self.prompts['dependency_rationale'] = PromptTemplate(
            name='dependency_rationale',
            category='narrative',
            template="""Explain in 1-2 sentences why this task depends on its prerequisites.

Task: {task_title}
Depends on: {dependencies}

Explain the technical or logical reason for this dependency. Keep it concise and clear.""",
            required_vars=['task_title', 'dependencies'],
            optional_vars=[],
            output_format='1-2 sentences explaining dependency rationale',
            example_output='This task requires the User model to be defined first, as the authentication service directly references user records for credential validation.'
        )

        self.prompts['implementation_suggestion'] = PromptTemplate(
            name='implementation_suggestion',
            category='narrative',
            template="""Provide a brief (2-3 sentences) strategic suggestion for implementing this phase.

Phase: {phase_title}

Key Tasks:
{task_list}

Suggest:
- Optimal starting point
- Parallel work opportunities
- Quick wins vs. foundational work

Keep it actionable and concise.""",
            required_vars=['phase_title', 'task_list'],
            optional_vars=[],
            output_format='2-3 sentences with implementation strategy',
            example_output='Start with the User model and database schema to establish the foundation. The authentication service and JWT utilities can then be developed in parallel by separate team members, as they have no interdependencies.'
        )

    def _register_insight_prompts(self):
        """Register insight extraction prompt templates."""
        self.prompts['bottleneck_analysis'] = PromptTemplate(
            name='bottleneck_analysis',
            category='insight',
            template="""Analyze this task for potential bottlenecks.

Task: {task_title}
Blocks: {blocked_tasks_count} other tasks
Estimated Effort: {estimated_hours} hours
Risk Level: {risk_level}

Identify:
- Why this is a bottleneck
- Impact if delayed
- Mitigation strategies

Keep response under 3 sentences.""",
            required_vars=['task_title', 'blocked_tasks_count', 'estimated_hours', 'risk_level'],
            optional_vars=[],
            output_format='3 sentences: reason, impact, mitigation',
            example_output='This task is a bottleneck because it establishes the authentication service that 12 other tasks depend on. Any delay here cascades throughout the entire project timeline. Mitigation: Allocate senior developer, break into smaller subtasks, and consider parallel mock implementation.'
        )

        self.prompts['quick_wins'] = PromptTemplate(
            name='quick_wins',
            category='insight',
            template="""Identify quick win opportunities in this task list.

Tasks:
{task_list}

For each quick win, note:
- Low effort (< 2 hours)
- High value (visible progress or unblocks others)
- Low risk

List up to 3 quick wins with brief justification.""",
            required_vars=['task_list'],
            optional_vars=[],
            output_format='List of 3 quick wins with justifications',
            example_output="""1. Create User model (1h): Simple data model, high value as it unblocks 5 other tasks
2. Add input validators (1.5h): Low complexity, immediately improves code quality
3. Write integration tests (1h): Straightforward, builds confidence in existing code"""
        )

    def _register_risk_prompts(self):
        """Register risk analysis prompt templates."""
        self.prompts['risk_assessment'] = PromptTemplate(
            name='risk_assessment',
            category='risk',
            template="""Assess risks for this task.

Task: {task_title}
Description: {task_description}
Dependencies: {dependency_count}
Complexity: {complexity_score}/10

Identify:
1. Technical risks (implementation challenges)
2. Dependency risks (blockers, external factors)
3. Timeline risks (estimation accuracy)

For each risk:
- Severity (Low/Medium/High/Critical)
- Mitigation strategy

Keep total response under 150 words.""",
            required_vars=['task_title', 'task_description', 'dependency_count', 'complexity_score'],
            optional_vars=[],
            output_format='Categorized risk list with severity and mitigation',
            example_output="""**Technical Risks:**
- OAuth integration complexity (High): Mitigate with proof-of-concept and library research

**Dependency Risks:**
- External OAuth provider availability (Medium): Implement graceful fallback and retry logic

**Timeline Risks:**
- Underestimated testing effort (Medium): Allocate buffer time for edge case testing"""
        )

    def _register_task_prompts(self):
        """Register task recommendation prompt templates."""
        self.prompts['next_task_recommendation'] = PromptTemplate(
            name='next_task_recommendation',
            category='task',
            template="""Recommend the next task to work on.

Available Tasks:
{task_list}

Consider:
- Dependencies (are prerequisites complete?)
- Priority (risk level, blocking status)
- Effort (quick wins vs. foundational work)
- Context (what was just completed?)

Recently Completed: {recent_task}

Recommend one task with brief (2-3 sentences) justification.""",
            required_vars=['task_list', 'recent_task'],
            optional_vars=[],
            output_format='Task ID + justification',
            example_output='**Recommended: task-2-3** (AuthService implementation)\n\nWith the User model now complete from task-2-1, the authentication service is the logical next step. This is a high-priority task that blocks 8 other tasks, and starting it now maintains development momentum.'
        )

        self.prompts['parallel_opportunities'] = PromptTemplate(
            name='parallel_opportunities',
            category='task',
            template="""Identify tasks that can be worked on in parallel.

Available Tasks:
{task_list}

Identify groups of 2-4 tasks that:
- Have no dependencies on each other
- Can be developed independently
- Are similar in scope (similar effort estimates)

List up to 3 parallel groups with justification.""",
            required_vars=['task_list'],
            optional_vars=[],
            output_format='List of parallel task groups',
            example_output="""**Group 1:** task-2-3 (AuthService), task-2-5 (Validators)
- Independent components, no shared dependencies

**Group 2:** task-3-1 (Login endpoint), task-3-2 (Logout endpoint)
- Similar API implementations, different developers can work simultaneously"""
        )

    def get_prompt(self, name: str) -> Optional[PromptTemplate]:
        """Get a prompt template by name.

        Args:
            name: Prompt template name

        Returns:
            PromptTemplate or None if not found

        Example:
            >>> library = AIPromptLibrary()
            >>> prompt = library.get_prompt('executive_summary')
            >>> print(prompt.template)
        """
        return self.prompts.get(name)

    def fill_prompt(self, name: str, **kwargs) -> Optional[str]:
        """Fill a prompt template with variables.

        Args:
            name: Prompt template name
            **kwargs: Variables to fill in the template

        Returns:
            Filled prompt string or None if template not found

        Raises:
            KeyError: If required variables are missing

        Example:
            >>> library = AIPromptLibrary()
            >>> prompt = library.fill_prompt(
            ...     'phase_transition',
            ...     prev_phase_title='Foundation',
            ...     next_phase_title='API Layer'
            ... )
            >>> print(prompt)
        """
        template = self.get_prompt(name)
        if not template:
            return None

        # Check required variables
        missing = [var for var in template.required_vars if var not in kwargs]
        if missing:
            raise KeyError(f"Missing required variables for prompt '{name}': {', '.join(missing)}")

        # Fill template
        try:
            return template.template.format(**kwargs)
        except KeyError as e:
            raise KeyError(f"Template variable {e} not provided for prompt '{name}'")

    def list_prompts(self, category: Optional[str] = None) -> List[str]:
        """List available prompt names, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            List of prompt names

        Example:
            >>> library = AIPromptLibrary()
            >>> narrative_prompts = library.list_prompts(category='narrative')
            >>> print(narrative_prompts)
            ['phase_transition', 'phase_introduction', 'dependency_rationale', ...]
        """
        if category:
            return [
                name for name, template in self.prompts.items()
                if template.category == category
            ]
        return list(self.prompts.keys())

    def get_categories(self) -> List[str]:
        """Get list of all prompt categories.

        Returns:
            List of unique category names

        Example:
            >>> library = AIPromptLibrary()
            >>> categories = library.get_categories()
            >>> print(categories)
            ['summary', 'narrative', 'insight', 'risk', 'task']
        """
        return list(set(template.category for template in self.prompts.values()))


# Global instance for convenience
_prompt_library = None


def get_prompt_library() -> AIPromptLibrary:
    """Get the global prompt library instance.

    Returns:
        AIPromptLibrary singleton instance

    Example:
        >>> from claude_skills.sdd_render.ai_prompts import get_prompt_library
        >>> library = get_prompt_library()
        >>> prompt = library.fill_prompt('executive_summary', **context)
    """
    global _prompt_library
    if _prompt_library is None:
        _prompt_library = AIPromptLibrary()
    return _prompt_library
