"""Complexity scoring for spec tasks.

This module calculates complexity scores (1-10 scale) for tasks based on:
- Subtask depth (nested task hierarchies)
- Dependency count (number of blockers and dependents)
- Estimated effort (hours)
- File path patterns (number of files, scope of changes)

Complexity scores help:
- Identify tasks needing extra attention
- Support adaptive formatting (more detail for complex tasks)
- Guide resource allocation
- Estimate risk and uncertainty
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ComplexityScore:
    """Complexity score and breakdown for a task.

    Attributes:
        task_id: Task identifier
        score: Overall complexity (1-10, where 10 is most complex)
        depth_score: Contribution from subtask hierarchy depth (0-10)
        dependency_score: Contribution from dependencies (0-10)
        effort_score: Contribution from estimated hours (0-10)
        scope_score: Contribution from file scope/patterns (0-10)
        level: Human-readable complexity level
        rationale: Explanation of complexity factors
    """
    task_id: str
    score: float
    depth_score: float
    dependency_score: float
    effort_score: float
    scope_score: float
    level: str
    rationale: str


class ComplexityScorer:
    """Scores task complexity on 1-10 scale.

    The scorer analyzes multiple factors to determine how complex a task is:

    1. Depth Score (25% weight):
       - Tasks with many subtasks = more complex
       - Deep nesting = more coordination needed
       - Score = min(10, total_subtasks / 2)

    2. Dependency Score (30% weight):
       - More dependencies = more complex
       - Both blockers and dependents count
       - Score = min(10, (blockers + dependents) * 1.5)

    3. Effort Score (30% weight):
       - Longer tasks tend to be more complex
       - Accounts for uncertainty in estimates
       - Score = min(10, estimated_hours)

    4. Scope Score (15% weight):
       - Multiple files = broader scope
       - System-level changes = higher complexity
       - Score = min(10, file_count * 2)

    Final Score:
       complexity = (
           depth_score * 0.25 +
           dependency_score * 0.30 +
           effort_score * 0.30 +
           scope_score * 0.15
       )

    Complexity Levels:
       - 1-3: Low complexity (straightforward tasks)
       - 4-6: Medium complexity (requires planning)
       - 7-8: High complexity (significant effort)
       - 9-10: Very high complexity (risky, needs breakdown)

    Attributes:
        spec_data: Complete JSON spec dictionary
        hierarchy: Task hierarchy from spec
        task_graph: Dependency graph from analyzer

    Example:
        >>> from claude_skills.sdd_render import ComplexityScorer, SpecAnalyzer
        >>> analyzer = SpecAnalyzer(spec_data)
        >>> scorer = ComplexityScorer(spec_data, analyzer)
        >>> complexity = scorer.score_task('task-3-1')
        >>> print(f"Complexity: {complexity.score:.1f}/10 - {complexity.level}")
        >>> print(f"Reason: {complexity.rationale}")
    """

    def __init__(self, spec_data: Dict[str, Any], analyzer: Optional[Any] = None):
        """Initialize scorer with spec data and optional analyzer.

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

    def _calculate_depth_score(self, task_id: str) -> Tuple[float, int]:
        """Calculate complexity from subtask depth.

        Args:
            task_id: Task identifier

        Returns:
            Tuple of (depth_score 0-10, total_subtasks count)
        """
        task_data = self.hierarchy.get(task_id, {})

        # Count total subtasks (recursively)
        total_subtasks = self._count_subtasks(task_id)

        # Depth score: more subtasks = more complex
        # Each 2 subtasks adds 1 point (max 10)
        depth_score = min(10.0, total_subtasks / 2.0)

        return depth_score, total_subtasks

    def _count_subtasks(self, task_id: str) -> int:
        """Recursively count all subtasks under a task.

        Args:
            task_id: Task identifier

        Returns:
            Total count of subtasks (including nested)
        """
        task_data = self.hierarchy.get(task_id, {})
        children = task_data.get('children', [])

        if not children:
            return 0

        count = len(children)

        # Recursively count children's children
        for child_id in children:
            count += self._count_subtasks(child_id)

        return count

    def _calculate_dependency_score(self, task_id: str) -> Tuple[float, int, int]:
        """Calculate complexity from dependencies.

        Args:
            task_id: Task identifier

        Returns:
            Tuple of (dependency_score 0-10, blocker_count, dependent_count)
        """
        blockers = self.reverse_graph.get(task_id, [])
        dependents = self.task_graph.get(task_id, [])

        blocker_count = len(blockers)
        dependent_count = len(dependents)

        # Both blockers and dependents increase complexity
        # Each dependency adds 1.5 points (max 10)
        total_deps = blocker_count + dependent_count
        dependency_score = min(10.0, total_deps * 1.5)

        return dependency_score, blocker_count, dependent_count

    def _calculate_effort_score(self, task_id: str) -> Tuple[float, float]:
        """Calculate complexity from estimated effort.

        Args:
            task_id: Task identifier

        Returns:
            Tuple of (effort_score 0-10, estimated_hours)
        """
        task_data = self.hierarchy.get(task_id, {})
        metadata = task_data.get('metadata', {})

        estimated_hours = metadata.get('estimated_hours', 2.0)

        # Effort score: 1 hour = 1 point (max 10)
        effort_score = min(10.0, estimated_hours)

        return effort_score, estimated_hours

    def _calculate_scope_score(self, task_id: str) -> Tuple[float, int]:
        """Calculate complexity from file scope.

        Analyzes file_path metadata to determine scope:
        - Single file = simpler
        - Multiple files = more complex
        - System-level paths = higher complexity

        Args:
            task_id: Task identifier

        Returns:
            Tuple of (scope_score 0-10, file_count estimate)
        """
        task_data = self.hierarchy.get(task_id, {})
        metadata = task_data.get('metadata', {})

        file_path = metadata.get('file_path', '')

        if not file_path:
            # No file path specified - default to medium scope
            return 5.0, 0

        # Count how many files are implied
        file_count = self._estimate_file_count(file_path)

        # Scope score: each file adds 2 points (max 10)
        scope_score = min(10.0, file_count * 2.0)

        return scope_score, file_count

    def _estimate_file_count(self, file_path: str) -> int:
        """Estimate number of files from file_path string.

        Args:
            file_path: File path or pattern from metadata

        Returns:
            Estimated file count
        """
        if not file_path:
            return 0

        # Check for glob patterns or multiple paths
        if '*' in file_path:
            # Glob pattern - estimate based on wildcards
            return 3  # Conservative estimate

        if ',' in file_path:
            # Comma-separated paths
            paths = file_path.split(',')
            return len(paths)

        # Single file
        return 1

    def _get_complexity_level(self, score: float) -> str:
        """Convert numeric score to human-readable level.

        Args:
            score: Complexity score (1-10)

        Returns:
            Level string ('low', 'medium', 'high', 'very_high')
        """
        if score <= 3.0:
            return 'low'
        elif score <= 6.0:
            return 'medium'
        elif score <= 8.0:
            return 'high'
        else:
            return 'very_high'

    def score_task(self, task_id: str) -> ComplexityScore:
        """Calculate complexity score for a task.

        Args:
            task_id: Task identifier

        Returns:
            ComplexityScore object with score and breakdown

        Raises:
            KeyError: If task_id not found in hierarchy
        """
        if task_id not in self.hierarchy:
            raise KeyError(f"Task not found: {task_id}")

        # Calculate component scores
        depth_score, subtask_count = self._calculate_depth_score(task_id)
        dependency_score, blocker_count, dependent_count = self._calculate_dependency_score(task_id)
        effort_score, estimated_hours = self._calculate_effort_score(task_id)
        scope_score, file_count = self._calculate_scope_score(task_id)

        # Weighted average (weights sum to 1.0)
        weights = {
            'depth': 0.25,
            'dependency': 0.30,
            'effort': 0.30,
            'scope': 0.15
        }

        total_score = (
            depth_score * weights['depth'] +
            dependency_score * weights['dependency'] +
            effort_score * weights['effort'] +
            scope_score * weights['scope']
        )

        # Determine complexity level
        level = self._get_complexity_level(total_score)

        # Generate rationale
        rationale_parts = []

        if subtask_count > 0:
            rationale_parts.append(f"{subtask_count} subtask{'s' if subtask_count > 1 else ''}")

        total_deps = blocker_count + dependent_count
        if total_deps > 0:
            rationale_parts.append(f"{total_deps} {'dependency' if total_deps == 1 else 'dependencies'}")

        if estimated_hours >= 4:
            rationale_parts.append(f"{estimated_hours}h effort")
        elif estimated_hours <= 0.5:
            rationale_parts.append("quick task")

        if file_count > 1:
            rationale_parts.append(f"{file_count} files")

        rationale = ", ".join(rationale_parts) if rationale_parts else "standard complexity"

        return ComplexityScore(
            task_id=task_id,
            score=round(total_score, 1),
            depth_score=round(depth_score, 1),
            dependency_score=round(dependency_score, 1),
            effort_score=round(effort_score, 1),
            scope_score=round(scope_score, 1),
            level=level,
            rationale=rationale
        )

    def calculate_complexity(self, task_id: str) -> ComplexityScore:
        """Alias for score_task() for backward compatibility.

        Args:
            task_id: Task identifier

        Returns:
            ComplexityScore object with score and breakdown

        Raises:
            KeyError: If task_id not found in hierarchy
        """
        return self.score_task(task_id)

    def score_all_tasks(self, status_filter: Optional[str] = None) -> List[Tuple[str, ComplexityScore]]:
        """Score all tasks in the spec.

        Args:
            status_filter: Optional filter by status ('pending', 'in_progress', 'completed')

        Returns:
            List of (task_id, ComplexityScore) tuples, sorted by score descending

        Example:
            >>> scorer = ComplexityScorer(spec_data)
            >>> all_scored = scorer.score_all_tasks()
            >>> for task_id, complexity in all_scored[:5]:
            ...     print(f"{task_id}: {complexity.score}/10 ({complexity.level})")
        """
        results = []

        for task_id in self.hierarchy:
            if task_id == 'spec-root':
                continue

            task_data = self.hierarchy[task_id]

            # Filter by status if specified
            if status_filter and task_data.get('status') != status_filter:
                continue

            # Calculate complexity
            complexity = self.score_task(task_id)
            results.append((task_id, complexity))

        # Sort by score descending (most complex first)
        results.sort(key=lambda x: x[1].score, reverse=True)

        return results

    def get_high_complexity_tasks(self, threshold: float = 7.0) -> List[Tuple[str, ComplexityScore]]:
        """Get all tasks above a complexity threshold.

        Args:
            threshold: Minimum complexity score (default 7.0)

        Returns:
            List of (task_id, ComplexityScore) tuples for complex tasks

        Example:
            >>> scorer = ComplexityScorer(spec_data)
            >>> complex_tasks = scorer.get_high_complexity_tasks(threshold=7.0)
            >>> print(f"Found {len(complex_tasks)} high-complexity tasks")
            >>> for task_id, complexity in complex_tasks:
            ...     print(f"  {task_id}: {complexity.score}/10 - {complexity.rationale}")
        """
        all_scored = self.score_all_tasks()

        return [(task_id, score) for task_id, score in all_scored
                if score.score >= threshold]

    def get_complexity_stats(self) -> Dict[str, Any]:
        """Get aggregate complexity statistics for the spec.

        Returns:
            Dictionary with stats:
            - total_tasks: Total tasks scored
            - avg_complexity: Average complexity score
            - max_complexity: Highest complexity score
            - min_complexity: Lowest complexity score
            - distribution: Count of tasks by complexity level

        Example:
            >>> scorer = ComplexityScorer(spec_data)
            >>> stats = scorer.get_complexity_stats()
            >>> print(f"Average complexity: {stats['avg_complexity']:.1f}")
            >>> print(f"High complexity tasks: {stats['distribution']['high']}")
        """
        all_scored = self.score_all_tasks()

        if not all_scored:
            return {
                'total_tasks': 0,
                'avg_complexity': 0.0,
                'max_complexity': 0.0,
                'min_complexity': 0.0,
                'distribution': {'low': 0, 'medium': 0, 'high': 0, 'very_high': 0}
            }

        scores = [score.score for _, score in all_scored]
        levels = [score.level for _, score in all_scored]

        distribution = {
            'low': sum(1 for level in levels if level == 'low'),
            'medium': sum(1 for level in levels if level == 'medium'),
            'high': sum(1 for level in levels if level == 'high'),
            'very_high': sum(1 for level in levels if level == 'very_high')
        }

        return {
            'total_tasks': len(all_scored),
            'avg_complexity': round(sum(scores) / len(scores), 1),
            'max_complexity': round(max(scores), 1),
            'min_complexity': round(min(scores), 1),
            'distribution': distribution
        }
