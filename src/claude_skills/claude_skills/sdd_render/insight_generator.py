"""Insight generation for spec analysis.

This module generates actionable insights and recommendations from spec analysis:
- Risk warnings (high-risk tasks, bottlenecks, long critical paths)
- Time estimates (phase completion predictions, remaining effort)
- Suggested next steps (optimal task ordering, parallel opportunities)
- Dependency conflicts (circular dependencies, blocking issues)
- Phase completion predictions (estimated timeline, blockers)

Insights help teams make informed decisions about resource allocation,
risk mitigation, and project planning.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class InsightType(Enum):
    """Types of insights that can be generated."""
    RISK_WARNING = "risk_warning"
    TIME_ESTIMATE = "time_estimate"
    NEXT_STEP = "next_step"
    DEPENDENCY_CONFLICT = "dependency_conflict"
    PHASE_PREDICTION = "phase_prediction"
    OPTIMIZATION = "optimization"


class InsightSeverity(Enum):
    """Severity levels for insights."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Insight:
    """A single actionable insight.

    Attributes:
        type: Type of insight (risk, time estimate, etc.)
        severity: How critical this insight is
        title: Brief headline for the insight
        description: Detailed explanation
        recommendation: Suggested action to take
        affected_tasks: Task IDs related to this insight
        data: Additional structured data
    """
    type: InsightType
    severity: InsightSeverity
    title: str
    description: str
    recommendation: str
    affected_tasks: List[str]
    data: Dict[str, Any]


class InsightGenerator:
    """Generates actionable insights from spec analysis.

    The generator combines data from SpecAnalyzer, PriorityRanker, and
    ComplexityScorer to produce high-level insights and recommendations.

    Insight Categories:

    1. Risk Warnings:
       - Critical path longer than 50% of total tasks
       - High-complexity tasks (complexity >= 7)
       - Bottleneck tasks blocking 5+ tasks
       - Tasks with many dependencies (>= 5 blockers)

    2. Time Estimates:
       - Remaining effort by phase
       - Phase completion predictions
       - Overall project timeline estimate
       - Variance in task size (risk indicator)

    3. Next Steps:
       - Recommended task ordering
       - Parallel work opportunities
       - Quick wins (low complexity, high value tasks)
       - Blockers to prioritize

    4. Dependency Conflicts:
       - Circular dependencies
       - Tasks with unresolved blockers
       - Orphaned tasks (no dependencies or dependents)

    5. Phase Predictions:
       - Estimated completion dates
       - Resource requirements
       - Risk factors per phase

    Attributes:
        spec_data: Complete JSON spec dictionary
        analyzer: SpecAnalyzer instance
        ranker: Optional PriorityRanker instance
        scorer: Optional ComplexityScorer instance

    Example:
        >>> from claude_skills.sdd_render import (
        ...     InsightGenerator, SpecAnalyzer, PriorityRanker, ComplexityScorer
        ... )
        >>> analyzer = SpecAnalyzer(spec_data)
        >>> ranker = PriorityRanker(spec_data, analyzer)
        >>> scorer = ComplexityScorer(spec_data, analyzer)
        >>> generator = InsightGenerator(spec_data, analyzer, ranker, scorer)
        >>> insights = generator.generate_all_insights()
        >>> for insight in insights:
        ...     print(f"{insight.severity.value.upper()}: {insight.title}")
    """

    def __init__(self,
                 spec_data: Dict[str, Any],
                 analyzer: Any,
                 ranker: Optional[Any] = None,
                 scorer: Optional[Any] = None):
        """Initialize insight generator.

        Args:
            spec_data: Complete JSON spec dictionary
            analyzer: SpecAnalyzer instance
            ranker: Optional PriorityRanker instance
            scorer: Optional ComplexityScorer instance
        """
        self.spec_data = spec_data
        self.hierarchy = spec_data.get('hierarchy', {})
        self.metadata = spec_data.get('metadata', {})
        self.analyzer = analyzer

        # Create ranker and scorer if not provided
        if ranker is None:
            from .priority_ranker import PriorityRanker
            ranker = PriorityRanker(spec_data, analyzer)
        self.ranker = ranker

        if scorer is None:
            from .complexity_scorer import ComplexityScorer
            scorer = ComplexityScorer(spec_data, analyzer)
        self.scorer = scorer

    def generate_all_insights(self) -> List[Insight]:
        """Generate all insights for the spec.

        Returns:
            List of Insight objects, sorted by severity (critical first)
        """
        insights = []

        # Generate each category of insights
        insights.extend(self._generate_risk_warnings())
        insights.extend(self._generate_time_estimates())
        insights.extend(self._generate_next_steps())
        insights.extend(self._generate_dependency_conflicts())
        insights.extend(self._generate_phase_predictions())
        insights.extend(self._generate_optimizations())

        # Sort by severity (critical > warning > info)
        severity_order = {
            InsightSeverity.CRITICAL: 0,
            InsightSeverity.WARNING: 1,
            InsightSeverity.INFO: 2
        }
        insights.sort(key=lambda x: severity_order[x.severity])

        return insights

    def _generate_risk_warnings(self) -> List[Insight]:
        """Generate risk-related warnings."""
        insights = []

        # Check for long critical path
        critical_path = self.analyzer.get_critical_path()
        total_tasks = len([t for t in self.hierarchy if t != 'spec-root'])

        if critical_path and len(critical_path) > total_tasks * 0.5:
            insights.append(Insight(
                type=InsightType.RISK_WARNING,
                severity=InsightSeverity.WARNING,
                title="Long critical path detected",
                description=f"Critical path contains {len(critical_path)} tasks "
                           f"({len(critical_path)/total_tasks*100:.0f}% of total). "
                           f"Any delay in these tasks will impact the entire project.",
                recommendation="Focus on critical path tasks first. Consider breaking "
                              "down large tasks to reduce risk.",
                affected_tasks=critical_path,
                data={'path_length': len(critical_path), 'percentage': len(critical_path)/total_tasks}
            ))

        # Check for high-complexity tasks
        high_complexity = self.scorer.get_high_complexity_tasks(threshold=7.0)
        if high_complexity:
            task_ids = [task_id for task_id, _ in high_complexity]
            insights.append(Insight(
                type=InsightType.RISK_WARNING,
                severity=InsightSeverity.WARNING,
                title=f"{len(high_complexity)} high-complexity tasks require extra attention",
                description=f"Found {len(high_complexity)} tasks with complexity >= 7/10. "
                           f"These tasks have high risk of delays or issues.",
                recommendation="Allocate experienced resources to high-complexity tasks. "
                              "Consider breaking them into smaller subtasks.",
                affected_tasks=task_ids,
                data={'count': len(high_complexity), 'tasks': high_complexity[:5]}
            ))

        # Check for major bottlenecks
        bottlenecks = self.analyzer.get_bottlenecks(min_dependents=5)
        if bottlenecks:
            task_ids = [task_id for task_id, _ in bottlenecks]
            top_bottleneck_id, top_count = bottlenecks[0]
            insights.append(Insight(
                type=InsightType.RISK_WARNING,
                severity=InsightSeverity.CRITICAL,
                title=f"Critical bottleneck: {top_bottleneck_id} blocks {top_count} tasks",
                description=f"Task {top_bottleneck_id} blocks {top_count} other tasks. "
                           f"Delays here will cascade throughout the project.",
                recommendation=f"Prioritize {top_bottleneck_id} immediately. "
                              f"Consider parallel alternatives for dependent tasks.",
                affected_tasks=task_ids,
                data={'bottlenecks': bottlenecks[:3]}
            ))

        return insights

    def _generate_time_estimates(self) -> List[Insight]:
        """Generate time and effort estimates."""
        insights = []

        # Calculate remaining effort
        total_hours = 0
        completed_hours = 0
        pending_hours = 0

        for task_id, task_data in self.hierarchy.items():
            if task_id == 'spec-root':
                continue

            metadata = task_data.get('metadata', {})
            hours = metadata.get('estimated_hours', 0)
            status = task_data.get('status', 'pending')

            total_hours += hours
            if status == 'completed':
                completed_hours += hours
            elif status == 'pending':
                pending_hours += hours

        if total_hours > 0:
            completion_pct = (completed_hours / total_hours) * 100

            insights.append(Insight(
                type=InsightType.TIME_ESTIMATE,
                severity=InsightSeverity.INFO,
                title=f"{pending_hours:.1f} hours of work remaining ({100-completion_pct:.0f}%)",
                description=f"Completed {completed_hours:.1f}h of {total_hours:.1f}h total. "
                           f"{pending_hours:.1f}h remaining across pending tasks.",
                recommendation="Allocate resources based on remaining effort. "
                              "Consider team capacity and timeline constraints.",
                affected_tasks=[],
                data={
                    'total_hours': total_hours,
                    'completed_hours': completed_hours,
                    'pending_hours': pending_hours,
                    'completion_percentage': completion_pct
                }
            ))

        return insights

    def _generate_next_steps(self) -> List[Insight]:
        """Generate recommended next steps."""
        insights = []

        # Get top priority tasks
        top_priorities = self.ranker.get_top_priorities(5, pending_only=True)

        if top_priorities:
            task_ids = [task_id for task_id, _ in top_priorities]
            top_task_id, top_priority = top_priorities[0]

            insights.append(Insight(
                type=InsightType.NEXT_STEP,
                severity=InsightSeverity.INFO,
                title=f"Recommended next task: {top_task_id}",
                description=f"Based on priority scoring, {top_task_id} should be tackled next. "
                           f"Priority score: {top_priority.score:.1f}. {top_priority.rationale}.",
                recommendation=f"Start with {top_task_id}, then consider: " +
                              ", ".join(task_ids[1:3]) if len(task_ids) > 1 else "",
                affected_tasks=task_ids,
                data={'top_priorities': [(tid, p.score) for tid, p in top_priorities]}
            ))

        # Find parallel opportunities
        parallel_groups = self.analyzer.get_parallelizable_tasks(pending_only=True)

        if parallel_groups and len(parallel_groups) > 0:
            first_wave = parallel_groups[0]
            if len(first_wave) >= 3:
                insights.append(Insight(
                    type=InsightType.OPTIMIZATION,
                    severity=InsightSeverity.INFO,
                    title=f"{len(first_wave)} tasks can be done in parallel",
                    description=f"The next wave has {len(first_wave)} tasks with no "
                               f"inter-dependencies. These can be parallelized.",
                    recommendation="Assign multiple team members to work on these tasks "
                                  "simultaneously to accelerate progress.",
                    affected_tasks=first_wave,
                    data={'wave_count': len(parallel_groups), 'first_wave_size': len(first_wave)}
                ))

        return insights

    def _generate_dependency_conflicts(self) -> List[Insight]:
        """Generate dependency conflict warnings."""
        insights = []

        # Check for circular dependencies
        stats = self.analyzer.get_stats()
        if stats.get('has_cycles'):
            insights.append(Insight(
                type=InsightType.DEPENDENCY_CONFLICT,
                severity=InsightSeverity.CRITICAL,
                title="Circular dependencies detected",
                description="The spec contains circular dependencies that prevent tasks "
                           "from being executed. This must be resolved before proceeding.",
                recommendation="Review dependency chains and break the cycles. "
                              "Use topological sort to identify problematic tasks.",
                affected_tasks=[],
                data={'stats': stats}
            ))

        # Find blocked tasks
        blocked_tasks = []
        for task_id, task_data in self.hierarchy.items():
            if task_id == 'spec-root':
                continue

            if task_data.get('status') == 'blocked':
                blocked_tasks.append(task_id)

        if blocked_tasks:
            insights.append(Insight(
                type=InsightType.DEPENDENCY_CONFLICT,
                severity=InsightSeverity.WARNING,
                title=f"{len(blocked_tasks)} tasks are currently blocked",
                description=f"These tasks cannot proceed due to unresolved dependencies: "
                           f"{', '.join(blocked_tasks[:5])}"
                           f"{' and more...' if len(blocked_tasks) > 5 else ''}",
                recommendation="Review blockers and determine if any can be resolved. "
                              "Consider working on alternative tasks in the meantime.",
                affected_tasks=blocked_tasks,
                data={'blocked_count': len(blocked_tasks)}
            ))

        return insights

    def _generate_phase_predictions(self) -> List[Insight]:
        """Generate phase completion predictions."""
        insights = []

        # Analyze each phase
        root = self.hierarchy.get('spec-root', {})
        phase_ids = root.get('children', [])

        for phase_id in phase_ids:
            phase_data = self.hierarchy.get(phase_id, {})
            if phase_data.get('type') != 'phase':
                continue

            total_tasks = phase_data.get('total_tasks', 0)
            completed_tasks = phase_data.get('completed_tasks', 0)
            status = phase_data.get('status', 'pending')

            if status == 'completed':
                continue

            # Estimate remaining effort for phase
            phase_hours = self._calculate_phase_effort(phase_id)

            if phase_hours['pending'] > 0:
                completion_pct = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

                severity = InsightSeverity.INFO
                if phase_hours['pending'] > 20:
                    severity = InsightSeverity.WARNING

                insights.append(Insight(
                    type=InsightType.PHASE_PREDICTION,
                    severity=severity,
                    title=f"{phase_data.get('title', phase_id)}: {phase_hours['pending']:.1f}h remaining",
                    description=f"Phase is {completion_pct:.0f}% complete "
                               f"({completed_tasks}/{total_tasks} tasks). "
                               f"{phase_hours['pending']:.1f}h of work remaining.",
                    recommendation="Track phase progress closely. Adjust resource allocation "
                                  "if completion timeline is at risk.",
                    affected_tasks=[],
                    data={
                        'phase_id': phase_id,
                        'completion_percentage': completion_pct,
                        'effort': phase_hours
                    }
                ))

        return insights

    def _generate_optimizations(self) -> List[Insight]:
        """Generate optimization suggestions."""
        insights = []

        # Find quick wins (low complexity, low effort, high priority)
        all_priorities = self.ranker.rank_tasks(pending_only=True)
        all_complexity = {task_id: complexity
                         for task_id, complexity in self.scorer.score_all_tasks(status_filter='pending')}

        quick_wins = []
        for task_id, priority in all_priorities[:20]:  # Check top 20 priorities
            complexity = all_complexity.get(task_id)
            if complexity and complexity.score <= 3.0 and complexity.effort_score <= 3.0:
                quick_wins.append((task_id, priority, complexity))

        if len(quick_wins) >= 3:
            task_ids = [task_id for task_id, _, _ in quick_wins[:5]]
            insights.append(Insight(
                type=InsightType.OPTIMIZATION,
                severity=InsightSeverity.INFO,
                title=f"{len(quick_wins)} quick wins available",
                description=f"Found {len(quick_wins)} tasks that are low complexity, "
                           f"low effort, but still valuable. These are excellent for building momentum.",
                recommendation="Knock out quick wins early to show progress and build confidence. "
                              f"Start with: {', '.join(task_ids[:3])}",
                affected_tasks=task_ids,
                data={'quick_wins': quick_wins[:5]}
            ))

        return insights

    def _calculate_phase_effort(self, phase_id: str) -> Dict[str, float]:
        """Calculate effort hours for a phase.

        Args:
            phase_id: Phase identifier

        Returns:
            Dictionary with 'total', 'completed', 'pending' effort hours
        """
        total_hours = 0.0
        completed_hours = 0.0
        pending_hours = 0.0

        # Recursively collect all tasks under this phase
        tasks = self._get_all_phase_tasks(phase_id)

        for task_id in tasks:
            task_data = self.hierarchy.get(task_id, {})
            metadata = task_data.get('metadata', {})
            hours = metadata.get('estimated_hours', 0)
            status = task_data.get('status', 'pending')

            total_hours += hours
            if status == 'completed':
                completed_hours += hours
            elif status == 'pending':
                pending_hours += hours

        return {
            'total': total_hours,
            'completed': completed_hours,
            'pending': pending_hours
        }

    def _get_all_phase_tasks(self, phase_id: str) -> List[str]:
        """Recursively get all task IDs under a phase.

        Args:
            phase_id: Phase identifier

        Returns:
            List of task IDs
        """
        phase_data = self.hierarchy.get(phase_id, {})
        children = phase_data.get('children', [])

        tasks = []
        for child_id in children:
            child_data = self.hierarchy.get(child_id, {})
            child_type = child_data.get('type', '')

            if child_type in ('task', 'subtask', 'verify'):
                tasks.append(child_id)
            elif child_type == 'group':
                # Recursively get tasks from group
                tasks.extend(self._get_all_phase_tasks(child_id))

        return tasks

    def get_insights_by_type(self, insight_type: InsightType) -> List[Insight]:
        """Get all insights of a specific type.

        Args:
            insight_type: Type of insights to retrieve

        Returns:
            List of matching insights
        """
        all_insights = self.generate_all_insights()
        return [i for i in all_insights if i.type == insight_type]

    def get_critical_insights(self) -> List[Insight]:
        """Get only critical severity insights.

        Returns:
            List of critical insights
        """
        all_insights = self.generate_all_insights()
        return [i for i in all_insights if i.severity == InsightSeverity.CRITICAL]
