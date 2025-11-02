"""Task grouping for alternative spec views.

This module provides smart grouping strategies to organize tasks by different
criteria beyond the default phase hierarchy:
- By file/directory (group related file modifications)
- By task category (implementation, verification, documentation)
- By risk level (critical, high, medium, low)
- By dependency relationships (independent groups that can be parallelized)

Multiple perspectives help teams understand the spec from different angles.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
from enum import Enum


class GroupingStrategy(Enum):
    """Available grouping strategies."""
    BY_FILE = "by_file"
    BY_CATEGORY = "by_category"
    BY_RISK = "by_risk"
    BY_DEPENDENCY = "by_dependency"
    BY_PHASE = "by_phase"  # Default hierarchy


@dataclass
class TaskGroup:
    """A group of related tasks.

    Attributes:
        name: Group identifier/label
        description: Human-readable description
        tasks: List of task IDs in this group
        metadata: Additional group information
    """
    name: str
    description: str
    tasks: List[str]
    metadata: Dict[str, Any]


class TaskGrouper:
    """Groups tasks by various criteria for alternative views.

    The grouper provides multiple ways to organize and view spec tasks,
    enabling different perspectives on the work:

    1. By File/Directory:
       - Groups tasks modifying the same file
       - Groups by directory/module
       - Helps identify hotspots and conflicts

    2. By Category:
       - Implementation tasks
       - Verification/testing tasks
       - Documentation tasks
       - Setup/configuration tasks

    3. By Risk Level:
       - Critical risk tasks
       - High risk tasks
       - Medium risk tasks
       - Low risk tasks

    4. By Dependencies:
       - Independent tasks (can be parallelized)
       - Sequential tasks (must be done in order)
       - Blocked tasks (waiting on dependencies)

    Attributes:
        spec_data: Complete JSON spec dictionary
        hierarchy: Task hierarchy from spec
        analyzer: Optional SpecAnalyzer instance

    Example:
        >>> from claude_skills.sdd_render import TaskGrouper, SpecAnalyzer
        >>> analyzer = SpecAnalyzer(spec_data)
        >>> grouper = TaskGrouper(spec_data, analyzer)
        >>> file_groups = grouper.group_by_file()
        >>> for group in file_groups:
        ...     print(f"{group.name}: {len(group.tasks)} tasks")
    """

    def __init__(self, spec_data: Dict[str, Any], analyzer: Optional[Any] = None):
        """Initialize task grouper.

        Args:
            spec_data: Complete JSON spec dictionary
            analyzer: Optional SpecAnalyzer instance
        """
        self.spec_data = spec_data
        self.hierarchy = spec_data.get('hierarchy', {})

        # Create analyzer if not provided
        if analyzer is None:
            from .spec_analyzer import SpecAnalyzer
            analyzer = SpecAnalyzer(spec_data)

        self.analyzer = analyzer

    def group_by_file(self, status_filter: Optional[str] = None) -> List[TaskGroup]:
        """Group tasks by file path.

        Tasks modifying the same file are grouped together. Tasks without
        file_path metadata are grouped under "Unspecified".

        Args:
            status_filter: Optional filter by status

        Returns:
            List of TaskGroup objects, one per file

        Example:
            >>> grouper = TaskGrouper(spec_data)
            >>> file_groups = grouper.group_by_file()
            >>> for group in file_groups:
            ...     print(f"{group.name}: {group.description}")
        """
        file_map: Dict[str, List[str]] = defaultdict(list)

        for task_id, task_data in self.hierarchy.items():
            if task_id == 'spec-root':
                continue

            # Filter by status if specified
            if status_filter and task_data.get('status') != status_filter:
                continue

            # Get file path from metadata
            metadata = task_data.get('metadata', {})
            file_path = metadata.get('file_path', 'Unspecified')

            if file_path:
                file_map[file_path].append(task_id)

        # Convert to TaskGroup objects
        groups = []
        for file_path, task_ids in sorted(file_map.items()):
            # Extract directory and filename for description
            if file_path != 'Unspecified':
                path_obj = Path(file_path)
                directory = str(path_obj.parent) if path_obj.parent != Path('.') else 'root'
                description = f"Tasks modifying {file_path}"
            else:
                directory = 'none'
                description = "Tasks without specified file path"

            groups.append(TaskGroup(
                name=file_path,
                description=description,
                tasks=task_ids,
                metadata={'directory': directory, 'task_count': len(task_ids)}
            ))

        return groups

    def group_by_directory(self, status_filter: Optional[str] = None) -> List[TaskGroup]:
        """Group tasks by directory.

        Similar to group_by_file but groups at directory level.

        Args:
            status_filter: Optional filter by status

        Returns:
            List of TaskGroup objects, one per directory

        Example:
            >>> grouper = TaskGrouper(spec_data)
            >>> dir_groups = grouper.group_by_directory()
        """
        dir_map: Dict[str, List[str]] = defaultdict(list)

        for task_id, task_data in self.hierarchy.items():
            if task_id == 'spec-root':
                continue

            # Filter by status if specified
            if status_filter and task_data.get('status') != status_filter:
                continue

            # Get file path and extract directory
            metadata = task_data.get('metadata', {})
            file_path = metadata.get('file_path', '')

            if file_path:
                directory = str(Path(file_path).parent)
                if directory == '.':
                    directory = 'root'
            else:
                directory = 'unspecified'

            dir_map[directory].append(task_id)

        # Convert to TaskGroup objects
        groups = []
        for directory, task_ids in sorted(dir_map.items()):
            description = f"Tasks in {directory}/" if directory != 'unspecified' else "Tasks without directory"

            groups.append(TaskGroup(
                name=directory,
                description=description,
                tasks=task_ids,
                metadata={'task_count': len(task_ids)}
            ))

        return groups

    def group_by_category(self, status_filter: Optional[str] = None) -> List[TaskGroup]:
        """Group tasks by category.

        Categories: implementation, verification, documentation, setup, etc.

        Args:
            status_filter: Optional filter by status

        Returns:
            List of TaskGroup objects, one per category

        Example:
            >>> grouper = TaskGrouper(spec_data)
            >>> category_groups = grouper.group_by_category()
            >>> for group in category_groups:
            ...     print(f"{group.name}: {len(group.tasks)} tasks")
        """
        category_map: Dict[str, List[str]] = defaultdict(list)

        for task_id, task_data in self.hierarchy.items():
            if task_id == 'spec-root':
                continue

            # Filter by status if specified
            if status_filter and task_data.get('status') != status_filter:
                continue

            # Get category from metadata
            metadata = task_data.get('metadata', {})
            category = metadata.get('task_category', 'uncategorized')

            category_map[category].append(task_id)

        # Convert to TaskGroup objects with descriptions
        category_descriptions = {
            'implementation': "Implementation tasks (code development)",
            'verification': "Verification tasks (testing, validation)",
            'documentation': "Documentation tasks (README, guides)",
            'setup': "Setup tasks (configuration, initialization)",
            'uncategorized': "Tasks without category"
        }

        groups = []
        for category, task_ids in sorted(category_map.items()):
            description = category_descriptions.get(category, f"{category.title()} tasks")

            groups.append(TaskGroup(
                name=category,
                description=description,
                tasks=task_ids,
                metadata={'task_count': len(task_ids)}
            ))

        return groups

    def group_by_risk(self, status_filter: Optional[str] = None) -> List[TaskGroup]:
        """Group tasks by risk level.

        Risk levels: critical, high, medium, low, none.

        Args:
            status_filter: Optional filter by status

        Returns:
            List of TaskGroup objects, one per risk level

        Example:
            >>> grouper = TaskGrouper(spec_data)
            >>> risk_groups = grouper.group_by_risk()
        """
        risk_map: Dict[str, List[str]] = defaultdict(list)

        for task_id, task_data in self.hierarchy.items():
            if task_id == 'spec-root':
                continue

            # Filter by status if specified
            if status_filter and task_data.get('status') != status_filter:
                continue

            # Get risk level from metadata
            metadata = task_data.get('metadata', {})
            risk_level = metadata.get('risk_level', 'none')

            risk_map[risk_level].append(task_id)

        # Convert to TaskGroup objects (ordered by risk severity)
        risk_order = ['critical', 'high', 'medium', 'low', 'none']
        risk_descriptions = {
            'critical': "Critical risk tasks (highest priority)",
            'high': "High risk tasks (significant attention needed)",
            'medium': "Medium risk tasks (standard management)",
            'low': "Low risk tasks (minimal risk)",
            'none': "Tasks with no specified risk"
        }

        groups = []
        for risk_level in risk_order:
            if risk_level in risk_map:
                task_ids = risk_map[risk_level]
                description = risk_descriptions.get(risk_level, f"{risk_level.title()} risk tasks")

                groups.append(TaskGroup(
                    name=risk_level,
                    description=description,
                    tasks=task_ids,
                    metadata={'risk_level': risk_level, 'task_count': len(task_ids)}
                ))

        return groups

    def group_by_dependency(self, pending_only: bool = True) -> List[TaskGroup]:
        """Group tasks by dependency status.

        Groups:
        - Independent: No dependencies, can start immediately
        - Partially blocked: Some dependencies, but some can proceed
        - Fully blocked: All dependencies unresolved
        - Sequential: Must be done in specific order

        Args:
            pending_only: Only consider pending tasks

        Returns:
            List of TaskGroup objects

        Example:
            >>> grouper = TaskGrouper(spec_data)
            >>> dep_groups = grouper.group_by_dependency()
            >>> independent = dep_groups[0]
            >>> print(f"{len(independent.tasks)} independent tasks")
        """
        # Get parallel waves from analyzer
        parallel_waves = self.analyzer.get_parallelizable_tasks(pending_only=pending_only)

        groups = []

        # Each wave becomes a group
        for i, wave in enumerate(parallel_waves, 1):
            groups.append(TaskGroup(
                name=f"Wave {i}",
                description=f"Tasks that can be executed in parallel (wave {i})",
                tasks=wave,
                metadata={'wave_number': i, 'task_count': len(wave)}
            ))

        return groups

    def group_by_status(self) -> List[TaskGroup]:
        """Group tasks by current status.

        Statuses: completed, in_progress, pending, blocked.

        Returns:
            List of TaskGroup objects

        Example:
            >>> grouper = TaskGrouper(spec_data)
            >>> status_groups = grouper.group_by_status()
        """
        status_map: Dict[str, List[str]] = defaultdict(list)

        for task_id, task_data in self.hierarchy.items():
            if task_id == 'spec-root':
                continue

            status = task_data.get('status', 'pending')
            status_map[status].append(task_id)

        # Convert to TaskGroup objects (ordered by workflow)
        status_order = ['pending', 'in_progress', 'blocked', 'completed']
        status_descriptions = {
            'pending': "Tasks not yet started",
            'in_progress': "Tasks currently being worked on",
            'blocked': "Tasks blocked by dependencies",
            'completed': "Tasks that are finished"
        }

        groups = []
        for status in status_order:
            if status in status_map:
                task_ids = status_map[status]
                description = status_descriptions.get(status, f"{status.title()} tasks")

                groups.append(TaskGroup(
                    name=status,
                    description=description,
                    tasks=task_ids,
                    metadata={'status': status, 'task_count': len(task_ids)}
                ))

        return groups

    def group_by_effort(self, status_filter: Optional[str] = None) -> List[TaskGroup]:
        """Group tasks by estimated effort.

        Effort categories:
        - Quick (< 1 hour)
        - Short (1-2 hours)
        - Medium (2-4 hours)
        - Long (4-8 hours)
        - Extended (> 8 hours)

        Args:
            status_filter: Optional filter by status

        Returns:
            List of TaskGroup objects

        Example:
            >>> grouper = TaskGrouper(spec_data)
            >>> effort_groups = grouper.group_by_effort()
        """
        effort_map: Dict[str, List[str]] = defaultdict(list)

        for task_id, task_data in self.hierarchy.items():
            if task_id == 'spec-root':
                continue

            # Filter by status if specified
            if status_filter and task_data.get('status') != status_filter:
                continue

            # Get estimated hours
            metadata = task_data.get('metadata', {})
            hours = metadata.get('estimated_hours', 2.0)

            # Categorize by effort
            if hours < 1:
                category = 'quick'
            elif hours < 2:
                category = 'short'
            elif hours < 4:
                category = 'medium'
            elif hours < 8:
                category = 'long'
            else:
                category = 'extended'

            effort_map[category].append(task_id)

        # Convert to TaskGroup objects
        effort_order = ['quick', 'short', 'medium', 'long', 'extended']
        effort_descriptions = {
            'quick': "Quick tasks (< 1 hour)",
            'short': "Short tasks (1-2 hours)",
            'medium': "Medium tasks (2-4 hours)",
            'long': "Long tasks (4-8 hours)",
            'extended': "Extended tasks (> 8 hours)"
        }

        groups = []
        for category in effort_order:
            if category in effort_map:
                task_ids = effort_map[category]
                description = effort_descriptions.get(category, f"{category.title()} tasks")

                groups.append(TaskGroup(
                    name=category,
                    description=description,
                    tasks=task_ids,
                    metadata={'effort_category': category, 'task_count': len(task_ids)}
                ))

        return groups

    def get_groups(self, strategy: GroupingStrategy, **kwargs) -> List[TaskGroup]:
        """Get task groups using specified strategy.

        Args:
            strategy: Grouping strategy to use
            **kwargs: Additional arguments passed to specific grouping method

        Returns:
            List of TaskGroup objects

        Example:
            >>> grouper = TaskGrouper(spec_data)
            >>> groups = grouper.get_groups(GroupingStrategy.BY_FILE)
        """
        strategy_map = {
            GroupingStrategy.BY_FILE: self.group_by_file,
            GroupingStrategy.BY_CATEGORY: self.group_by_category,
            GroupingStrategy.BY_RISK: self.group_by_risk,
            GroupingStrategy.BY_DEPENDENCY: self.group_by_dependency,
        }

        method = strategy_map.get(strategy)
        if method:
            return method(**kwargs)
        else:
            raise ValueError(f"Unknown grouping strategy: {strategy}")
