"""Priority ranking for spec tasks.

This module provides multi-factor priority scoring for tasks in a spec,
enabling intelligent task ordering in rendered output. Priority is calculated
based on:
- Risk level (higher risk = higher priority)
- Dependency count (more blockers = lower initial priority)
- Estimated effort (hours)
- Task category (implementation vs verification)
- Blocking status (tasks blocking many others = higher priority)

The ranker helps identify which tasks should be tackled first based on
their impact, risk, and dependencies.
"""

from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class TaskCategory(Enum):
    """Task category types with associated priority weights."""
    IMPLEMENTATION = "implementation"
    VERIFICATION = "verification"
    DOCUMENTATION = "documentation"
    SETUP = "setup"
    UNKNOWN = "unknown"


# Priority weights for different task categories
CATEGORY_WEIGHTS = {
    TaskCategory.SETUP: 1.3,          # Setup tasks should go early
    TaskCategory.IMPLEMENTATION: 1.0,  # Normal priority
    TaskCategory.VERIFICATION: 0.9,    # Slightly lower (test after impl)
    TaskCategory.DOCUMENTATION: 0.7,   # Can be done later
    TaskCategory.UNKNOWN: 1.0         # Neutral weight
}

# Risk level weights (higher risk = higher priority)
RISK_WEIGHTS = {
    "critical": 1.5,
    "high": 1.3,
    "medium": 1.0,
    "low": 0.8,
    "none": 0.7
}


@dataclass
class TaskPriority:
    """Priority score and metadata for a task.

    Attributes:
        task_id: Task identifier
        score: Computed priority score (higher = more important)
        risk_factor: Contribution from risk level
        dependency_factor: Contribution from dependencies
        blocking_factor: Contribution from tasks this blocks
        effort_factor: Contribution from estimated effort
        category_factor: Contribution from task category
        rationale: Human-readable explanation of score
    """
    task_id: str
    score: float
    risk_factor: float
    dependency_factor: float
    blocking_factor: float
    effort_factor: float
    category_factor: float
    rationale: str


class PriorityRanker:
    """Ranks tasks by priority using multi-factor scoring.

    The ranker analyzes task metadata and dependency relationships to
    compute a priority score for each task. Higher scores indicate tasks
    that should be addressed earlier.

    Priority Calculation:
        base_score = 100  # Starting point

        # Risk factor: Higher risk = higher priority
        risk_score = base_score * RISK_WEIGHTS[risk_level]

        # Dependency factor: More blockers = lower initial priority
        # (Can't start yet, so not urgent)
        dep_penalty = 10 * num_blockers
        dep_score = max(0, base_score - dep_penalty)

        # Blocking factor: Tasks blocking many others = higher priority
        # (Unblocking critical for project progress)
        blocking_bonus = 15 * num_blocked_tasks
        blocking_score = blocking_bonus

        # Effort factor: Prefer smaller tasks for quick wins
        # But don't penalize large tasks too much
        effort_score = max(20, 100 - (estimated_hours * 5))

        # Category factor: Weight by task type
        category_score = base_score * CATEGORY_WEIGHTS[category]

        # Final score (weighted sum)
        priority = (
            risk_score * 0.25 +
            dep_score * 0.20 +
            blocking_score * 0.30 +
            effort_score * 0.10 +
            category_score * 0.15
        )

    Attributes:
        spec_data: Complete JSON spec dictionary
        hierarchy: Task hierarchy from spec
        task_graph: Dependency graph from SpecAnalyzer

    Example:
        >>> from claude_skills.sdd_render import PriorityRanker, SpecAnalyzer
        >>> analyzer = SpecAnalyzer(spec_data)
        >>> ranker = PriorityRanker(spec_data, analyzer)
        >>> ranked = ranker.rank_tasks()
        >>> for task_id, priority in ranked[:5]:
        ...     print(f"{task_id}: {priority.score:.1f} - {priority.rationale}")
    """

    def __init__(self, spec_data: Dict[str, Any], analyzer: Optional[Any] = None):
        """Initialize ranker with spec data and optional analyzer.

        Args:
            spec_data: Complete JSON spec dictionary
            analyzer: Optional SpecAnalyzer instance (will create if not provided)
        """
        self.spec_data = spec_data
        self.hierarchy = spec_data.get('hierarchy', {})

        # Import SpecAnalyzer if not provided (avoid circular import)
        if analyzer is None:
            from .spec_analyzer import SpecAnalyzer
            analyzer = SpecAnalyzer(spec_data)

        self.analyzer = analyzer
        self.task_graph = analyzer.task_graph
        self.reverse_graph = analyzer.reverse_graph

    def _get_risk_weight(self, task_data: Dict[str, Any]) -> float:
        """Get risk weight for a task.

        Args:
            task_data: Task data from hierarchy

        Returns:
            Risk weight multiplier (higher = more risky)
        """
        metadata = task_data.get('metadata', {})
        risk_level = metadata.get('risk_level', 'none')

        # Normalize risk level string
        risk_level = risk_level.lower()

        return RISK_WEIGHTS.get(risk_level, RISK_WEIGHTS['none'])

    def _get_category_weight(self, task_data: Dict[str, Any]) -> Tuple[TaskCategory, float]:
        """Get category weight for a task.

        Args:
            task_data: Task data from hierarchy

        Returns:
            Tuple of (category enum, weight multiplier)
        """
        metadata = task_data.get('metadata', {})
        category_str = metadata.get('task_category', 'unknown')

        # Try to match category
        category = TaskCategory.UNKNOWN
        for cat in TaskCategory:
            if cat.value == category_str:
                category = cat
                break

        weight = CATEGORY_WEIGHTS.get(category, CATEGORY_WEIGHTS[TaskCategory.UNKNOWN])

        return category, weight

    def _get_estimated_hours(self, task_data: Dict[str, Any]) -> float:
        """Get estimated hours for a task.

        Args:
            task_data: Task data from hierarchy

        Returns:
            Estimated hours (default 2.0 if not specified)
        """
        metadata = task_data.get('metadata', {})
        return metadata.get('estimated_hours', 2.0)

    def _get_blocking_count(self, task_id: str) -> int:
        """Get number of tasks blocked by this task.

        Args:
            task_id: Task identifier

        Returns:
            Count of tasks that depend on this task
        """
        return len(self.task_graph.get(task_id, []))

    def _get_blocker_count(self, task_id: str) -> int:
        """Get number of tasks blocking this task.

        Args:
            task_id: Task identifier

        Returns:
            Count of tasks this task depends on
        """
        return len(self.reverse_graph.get(task_id, []))

    def calculate_priority(self, task_id: str) -> TaskPriority:
        """Calculate priority score for a specific task.

        Args:
            task_id: Task identifier

        Returns:
            TaskPriority object with score and breakdown

        Raises:
            KeyError: If task_id not found in hierarchy
        """
        if task_id not in self.hierarchy:
            raise KeyError(f"Task not found: {task_id}")

        task_data = self.hierarchy[task_id]

        # Base score
        base_score = 100.0

        # 1. Risk factor (25% weight)
        risk_weight = self._get_risk_weight(task_data)
        risk_score = base_score * risk_weight
        risk_factor = risk_score * 0.25

        # 2. Dependency factor (20% weight)
        # More blockers = lower initial priority (can't start yet)
        num_blockers = self._get_blocker_count(task_id)
        dep_penalty = 10.0 * num_blockers
        dep_score = max(0, base_score - dep_penalty)
        dependency_factor = dep_score * 0.20

        # 3. Blocking factor (30% weight)
        # Tasks blocking many others = higher priority
        num_blocked = self._get_blocking_count(task_id)
        blocking_bonus = 15.0 * num_blocked
        blocking_factor = blocking_bonus * 0.30

        # 4. Effort factor (10% weight)
        # Prefer smaller tasks for quick wins
        estimated_hours = self._get_estimated_hours(task_data)
        effort_score = max(20, 100 - (estimated_hours * 5))
        effort_factor = effort_score * 0.10

        # 5. Category factor (15% weight)
        category, category_weight = self._get_category_weight(task_data)
        category_score = base_score * category_weight
        category_factor = category_score * 0.15

        # Final priority score
        total_score = (
            risk_factor +
            dependency_factor +
            blocking_factor +
            effort_factor +
            category_factor
        )

        # Generate rationale
        rationale_parts = []

        if risk_weight > 1.0:
            rationale_parts.append(f"high risk ({task_data.get('metadata', {}).get('risk_level', 'unknown')})")

        if num_blocked >= 3:
            rationale_parts.append(f"blocks {num_blocked} tasks")
        elif num_blocked > 0:
            rationale_parts.append(f"blocks {num_blocked} task{'s' if num_blocked > 1 else ''}")

        if num_blockers > 0:
            rationale_parts.append(f"depends on {num_blockers} task{'s' if num_blockers > 1 else ''}")

        if estimated_hours < 1:
            rationale_parts.append("quick task")
        elif estimated_hours > 4:
            rationale_parts.append("large effort")

        if category == TaskCategory.SETUP:
            rationale_parts.append("setup task")

        rationale = ", ".join(rationale_parts) if rationale_parts else "standard priority"

        return TaskPriority(
            task_id=task_id,
            score=total_score,
            risk_factor=risk_factor,
            dependency_factor=dependency_factor,
            blocking_factor=blocking_factor,
            effort_factor=effort_factor,
            category_factor=category_factor,
            rationale=rationale
        )

    def rank_tasks(self,
                   pending_only: bool = True,
                   min_score: Optional[float] = None) -> List[Tuple[str, TaskPriority]]:
        """Rank all tasks by priority score.

        Args:
            pending_only: Only rank tasks with status='pending'
            min_score: Optional minimum score threshold

        Returns:
            List of (task_id, TaskPriority) tuples, sorted by score descending

        Example:
            >>> ranker = PriorityRanker(spec_data)
            >>> ranked = ranker.rank_tasks(pending_only=True)
            >>> top_task_id, top_priority = ranked[0]
            >>> print(f"Top priority: {top_task_id} ({top_priority.score:.1f})")
            >>> print(f"Reason: {top_priority.rationale}")
        """
        results = []

        for task_id in self.hierarchy:
            if task_id == 'spec-root':
                continue

            task_data = self.hierarchy[task_id]

            # Filter by status if requested
            if pending_only and task_data.get('status') != 'pending':
                continue

            # Calculate priority
            priority = self.calculate_priority(task_id)

            # Filter by minimum score if specified
            if min_score is not None and priority.score < min_score:
                continue

            results.append((task_id, priority))

        # Sort by score descending (highest priority first)
        results.sort(key=lambda x: x[1].score, reverse=True)

        return results

    def get_top_priorities(self, n: int = 5, pending_only: bool = True) -> List[Tuple[str, TaskPriority]]:
        """Get top N priority tasks.

        Args:
            n: Number of top tasks to return
            pending_only: Only consider pending tasks

        Returns:
            List of up to N (task_id, TaskPriority) tuples

        Example:
            >>> ranker = PriorityRanker(spec_data)
            >>> top_5 = ranker.get_top_priorities(5)
            >>> for task_id, priority in top_5:
            ...     print(f"{task_id}: {priority.score:.1f}")
        """
        ranked = self.rank_tasks(pending_only=pending_only)
        return ranked[:n]

    def get_priority_breakdown(self, task_id: str) -> Dict[str, Any]:
        """Get detailed priority breakdown for debugging/analysis.

        Args:
            task_id: Task identifier

        Returns:
            Dictionary with all priority factors and scores

        Example:
            >>> ranker = PriorityRanker(spec_data)
            >>> breakdown = ranker.get_priority_breakdown('task-2-1')
            >>> print(f"Risk factor: {breakdown['risk_factor']}")
            >>> print(f"Blocking factor: {breakdown['blocking_factor']}")
        """
        priority = self.calculate_priority(task_id)

        return {
            'task_id': task_id,
            'total_score': priority.score,
            'risk_factor': priority.risk_factor,
            'dependency_factor': priority.dependency_factor,
            'blocking_factor': priority.blocking_factor,
            'effort_factor': priority.effort_factor,
            'category_factor': priority.category_factor,
            'rationale': priority.rationale,
            'details': {
                'num_blockers': self._get_blocker_count(task_id),
                'num_blocked': self._get_blocking_count(task_id),
                'estimated_hours': self._get_estimated_hours(self.hierarchy[task_id]),
                'risk_level': self.hierarchy[task_id].get('metadata', {}).get('risk_level', 'none'),
                'category': self.hierarchy[task_id].get('metadata', {}).get('task_category', 'unknown')
            }
        }
