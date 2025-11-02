"""Unit tests for TaskGrouper.

This test suite verifies that task grouping strategies correctly
organize tasks and that every task is included in at least one group.
"""

import pytest
from claude_skills.sdd_render import TaskGrouper, SpecAnalyzer
from claude_skills.sdd_render.task_grouper import GroupingStrategy


class TestTaskGrouper:
    """Tests for TaskGrouper class."""

    def test_initialization(self, sample_spec_data):
        """Test TaskGrouper initializes correctly."""
        grouper = TaskGrouper(sample_spec_data)

        assert grouper.spec_data == sample_spec_data
        assert grouper.hierarchy == sample_spec_data['hierarchy']
        assert grouper.analyzer is not None

    def test_initialization_with_analyzer(self, sample_spec_data):
        """Test TaskGrouper can accept a pre-built analyzer."""
        analyzer = SpecAnalyzer(sample_spec_data)
        grouper = TaskGrouper(sample_spec_data, analyzer=analyzer)

        assert grouper.analyzer is analyzer

    def test_group_by_file(self, sample_spec_data):
        """Test grouping tasks by file path."""
        grouper = TaskGrouper(sample_spec_data)
        file_groups = grouper.group_by_file()

        # Should have multiple groups (different files)
        assert len(file_groups) > 0

        # Each group should have tasks
        for group in file_groups:
            assert len(group.tasks) > 0
            assert group.name  # Has a name
            assert group.description  # Has description
            assert 'task_count' in group.metadata

    def test_group_by_directory(self, sample_spec_data):
        """Test grouping tasks by directory."""
        grouper = TaskGrouper(sample_spec_data)
        dir_groups = grouper.group_by_directory()

        # Should have at least one group
        assert len(dir_groups) > 0

        # Each group should have tasks
        for group in dir_groups:
            assert len(group.tasks) > 0
            assert group.name
            assert group.description

    def test_group_by_category(self, sample_spec_data):
        """Test grouping tasks by category."""
        grouper = TaskGrouper(sample_spec_data)
        category_groups = grouper.group_by_category()

        # Should have at least one category
        assert len(category_groups) > 0

        # Verify categories are as expected
        category_names = [g.name for g in category_groups]
        assert 'implementation' in category_names or 'verification' in category_names

        # Each group should have tasks
        for group in category_groups:
            assert len(group.tasks) > 0

    def test_group_by_risk(self, sample_spec_data):
        """Test grouping tasks by risk level."""
        grouper = TaskGrouper(sample_spec_data)
        risk_groups = grouper.group_by_risk()

        # Should have at least one risk level
        assert len(risk_groups) > 0

        # Verify risk levels are ordered correctly
        risk_names = [g.name for g in risk_groups]
        risk_order = ['critical', 'high', 'medium', 'low', 'none']

        # Check that groups appear in correct order
        for i in range(len(risk_names) - 1):
            current_idx = risk_order.index(risk_names[i])
            next_idx = risk_order.index(risk_names[i + 1])
            assert current_idx < next_idx, "Risk groups should be ordered by severity"

    def test_group_by_dependency(self, sample_spec_data):
        """Test grouping tasks by dependency status."""
        grouper = TaskGrouper(sample_spec_data)
        dep_groups = grouper.group_by_dependency(pending_only=False)

        # Should have at least one wave
        assert len(dep_groups) > 0

        # Each wave should have tasks
        for group in dep_groups:
            assert len(group.tasks) > 0
            assert 'wave_number' in group.metadata
            assert group.name.startswith('Wave')

    def test_group_by_status(self, sample_spec_data):
        """Test grouping tasks by status."""
        grouper = TaskGrouper(sample_spec_data)
        status_groups = grouper.group_by_status()

        # Should have at least one status group
        assert len(status_groups) > 0

        # Verify statuses are as expected
        status_names = [g.name for g in status_groups]
        valid_statuses = ['pending', 'in_progress', 'blocked', 'completed']

        for status in status_names:
            assert status in valid_statuses

        # Check order
        status_order = ['pending', 'in_progress', 'blocked', 'completed']
        for i in range(len(status_names) - 1):
            current_idx = status_order.index(status_names[i])
            next_idx = status_order.index(status_names[i + 1])
            assert current_idx < next_idx, "Status groups should be ordered by workflow"

    def test_group_by_effort(self, sample_spec_data):
        """Test grouping tasks by estimated effort."""
        grouper = TaskGrouper(sample_spec_data)
        effort_groups = grouper.group_by_effort()

        # Should have at least one effort category
        assert len(effort_groups) > 0

        # Verify effort categories
        effort_names = [g.name for g in effort_groups]
        valid_efforts = ['quick', 'short', 'medium', 'long', 'extended']

        for effort in effort_names:
            assert effort in valid_efforts

        # Check order
        effort_order = ['quick', 'short', 'medium', 'long', 'extended']
        for i in range(len(effort_names) - 1):
            current_idx = effort_order.index(effort_names[i])
            next_idx = effort_order.index(effort_names[i + 1])
            assert current_idx < next_idx, "Effort groups should be ordered by duration"

    def test_complete_coverage(self, sample_spec_data):
        """Test that task grouping covers all tasks.

        This is the core test for verify-2-4: Every task should appear in
        at least one group for each grouping strategy.
        """
        grouper = TaskGrouper(sample_spec_data)

        # Get all task IDs (excluding spec-root and phases)
        all_task_ids = set()
        for task_id, task_data in sample_spec_data['hierarchy'].items():
            if task_id != 'spec-root':
                all_task_ids.add(task_id)

        # Test each grouping strategy for complete coverage
        grouping_methods = [
            ('by_file', grouper.group_by_file),
            ('by_directory', grouper.group_by_directory),
            ('by_category', grouper.group_by_category),
            ('by_risk', grouper.group_by_risk),
            ('by_status', grouper.group_by_status),
            ('by_effort', grouper.group_by_effort),
        ]

        for method_name, method in grouping_methods:
            groups = method()

            # Collect all tasks from all groups
            covered_tasks = set()
            for group in groups:
                covered_tasks.update(group.tasks)

            # Verify complete coverage
            assert covered_tasks == all_task_ids, \
                f"{method_name} grouping doesn't cover all tasks. " \
                f"Missing: {all_task_ids - covered_tasks}, " \
                f"Extra: {covered_tasks - all_task_ids}"

    def test_no_duplicate_coverage_within_strategy(self, sample_spec_data):
        """Test that tasks don't appear in multiple groups within the same strategy.

        For most grouping strategies, each task should appear in exactly one group.
        Exception: dependency grouping may overlap if tasks can be in multiple waves.
        """
        grouper = TaskGrouper(sample_spec_data)

        # Test strategies that should have no overlap
        no_overlap_methods = [
            ('by_file', grouper.group_by_file),
            ('by_directory', grouper.group_by_directory),
            ('by_category', grouper.group_by_category),
            ('by_risk', grouper.group_by_risk),
            ('by_status', grouper.group_by_status),
            ('by_effort', grouper.group_by_effort),
        ]

        for method_name, method in no_overlap_methods:
            groups = method()

            # Track which group each task belongs to
            task_groups = {}
            for group in groups:
                for task_id in group.tasks:
                    if task_id in task_groups:
                        pytest.fail(
                            f"{method_name}: Task {task_id} appears in multiple groups: "
                            f"{task_groups[task_id]} and {group.name}"
                        )
                    task_groups[task_id] = group.name

    def test_status_filter(self, sample_spec_data):
        """Test that status filtering works correctly."""
        grouper = TaskGrouper(sample_spec_data)

        # Group only pending tasks by file
        pending_file_groups = grouper.group_by_file(status_filter='pending')

        # Verify all returned tasks are pending
        for group in pending_file_groups:
            for task_id in group.tasks:
                task_status = sample_spec_data['hierarchy'][task_id].get('status')
                assert task_status == 'pending', \
                    f"Task {task_id} has status {task_status}, expected 'pending'"

        # Group only completed tasks by category
        completed_category_groups = grouper.group_by_category(status_filter='completed')

        # Verify all returned tasks are completed
        for group in completed_category_groups:
            for task_id in group.tasks:
                task_status = sample_spec_data['hierarchy'][task_id].get('status')
                assert task_status == 'completed', \
                    f"Task {task_id} has status {task_status}, expected 'completed'"

    def test_get_groups_with_strategy_enum(self, sample_spec_data):
        """Test the unified get_groups method with GroupingStrategy enum."""
        grouper = TaskGrouper(sample_spec_data)

        # Test BY_FILE strategy
        file_groups = grouper.get_groups(GroupingStrategy.BY_FILE)
        assert len(file_groups) > 0

        # Test BY_CATEGORY strategy
        category_groups = grouper.get_groups(GroupingStrategy.BY_CATEGORY)
        assert len(category_groups) > 0

        # Test BY_RISK strategy
        risk_groups = grouper.get_groups(GroupingStrategy.BY_RISK)
        assert len(risk_groups) > 0

        # Test BY_DEPENDENCY strategy (with pending_only=False to include all tasks)
        dep_groups = grouper.get_groups(GroupingStrategy.BY_DEPENDENCY, pending_only=False)
        assert len(dep_groups) > 0

    def test_invalid_grouping_strategy(self, sample_spec_data):
        """Test that invalid grouping strategy raises error."""
        grouper = TaskGrouper(sample_spec_data)

        # Create a fake strategy that doesn't exist
        with pytest.raises(ValueError, match="Unknown grouping strategy"):
            # Use a string that doesn't map to any strategy
            grouper.get_groups('invalid_strategy')

    def test_empty_spec_handles_gracefully(self):
        """Test grouper handles empty spec gracefully."""
        empty_spec = {
            "spec_id": "empty",
            "hierarchy": {"spec-root": {"id": "spec-root", "type": "spec"}}
        }
        grouper = TaskGrouper(empty_spec)

        # All grouping methods should return empty lists
        assert grouper.group_by_file() == []
        assert grouper.group_by_directory() == []
        assert grouper.group_by_category() == []
        assert grouper.group_by_risk() == []
        assert grouper.group_by_status() == []
        assert grouper.group_by_effort() == []
        assert grouper.group_by_dependency(pending_only=False) == []

    def test_task_group_dataclass(self, sample_spec_data):
        """Test TaskGroup dataclass structure."""
        grouper = TaskGrouper(sample_spec_data)
        groups = grouper.group_by_file()

        if groups:
            group = groups[0]

            # Verify TaskGroup has required attributes
            assert hasattr(group, 'name')
            assert hasattr(group, 'description')
            assert hasattr(group, 'tasks')
            assert hasattr(group, 'metadata')

            # Verify types
            assert isinstance(group.name, str)
            assert isinstance(group.description, str)
            assert isinstance(group.tasks, list)
            assert isinstance(group.metadata, dict)

    def test_metadata_consistency(self, sample_spec_data):
        """Test that group metadata is consistent and useful."""
        grouper = TaskGrouper(sample_spec_data)

        # File groups should have directory and task_count
        file_groups = grouper.group_by_file()
        for group in file_groups:
            assert 'directory' in group.metadata
            assert 'task_count' in group.metadata
            assert group.metadata['task_count'] == len(group.tasks)

        # Risk groups should have risk_level and task_count
        risk_groups = grouper.group_by_risk()
        for group in risk_groups:
            assert 'risk_level' in group.metadata
            assert 'task_count' in group.metadata
            assert group.metadata['task_count'] == len(group.tasks)

        # Effort groups should have effort_category and task_count
        effort_groups = grouper.group_by_effort()
        for group in effort_groups:
            assert 'effort_category' in group.metadata
            assert 'task_count' in group.metadata
            assert group.metadata['task_count'] == len(group.tasks)

    def test_group_descriptions_are_meaningful(self, sample_spec_data):
        """Test that group descriptions are human-readable and informative."""
        grouper = TaskGrouper(sample_spec_data)

        # All grouping methods should produce meaningful descriptions
        all_groups = (
            grouper.group_by_file() +
            grouper.group_by_directory() +
            grouper.group_by_category() +
            grouper.group_by_risk() +
            grouper.group_by_status() +
            grouper.group_by_effort()
        )

        for group in all_groups:
            # Description should not be empty
            assert group.description
            assert len(group.description) > 0

            # Description should be a sentence or phrase
            assert isinstance(group.description, str)

    def test_tasks_without_metadata_handled_gracefully(self):
        """Test that tasks without metadata fields are handled gracefully."""
        spec_with_minimal_metadata = {
            "spec_id": "minimal-test",
            "hierarchy": {
                "spec-root": {
                    "id": "spec-root",
                    "type": "spec",
                    "children": ["task-1"]
                },
                "task-1": {
                    "id": "task-1",
                    "type": "task",
                    "title": "Minimal Task",
                    "status": "pending",
                    "parent": "spec-root",
                    "children": [],
                    "dependencies": {"blocks": [], "blocked_by": [], "depends": []},
                    # No metadata field at all
                }
            }
        }

        grouper = TaskGrouper(spec_with_minimal_metadata)

        # All grouping methods should work without crashing
        assert len(grouper.group_by_file()) > 0  # Should go in "Unspecified"
        assert len(grouper.group_by_category()) > 0  # Should go in "uncategorized"
        assert len(grouper.group_by_risk()) > 0  # Should go in "none"
        assert len(grouper.group_by_effort()) > 0  # Should use default 2.0 hours
