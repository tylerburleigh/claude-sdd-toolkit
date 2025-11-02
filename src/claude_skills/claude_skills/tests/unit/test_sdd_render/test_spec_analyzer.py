"""Unit tests for SpecAnalyzer."""

import pytest
from claude_skills.sdd_render import SpecAnalyzer


class TestSpecAnalyzer:
    """Tests for SpecAnalyzer class."""

    def test_initialization(self, sample_spec_data):
        """Test SpecAnalyzer initializes correctly."""
        analyzer = SpecAnalyzer(sample_spec_data)

        assert analyzer.spec_data == sample_spec_data
        assert analyzer.hierarchy == sample_spec_data['hierarchy']
        assert isinstance(analyzer.task_graph, dict)
        assert isinstance(analyzer.reverse_graph, dict)

    def test_graph_building(self, sample_spec_data):
        """Test dependency graphs are built correctly."""
        analyzer = SpecAnalyzer(sample_spec_data)

        # Check forward graph (task-1-1 blocks task-1-2 and task-2-1)
        assert 'task-1-2' in analyzer.task_graph['task-1-1']
        assert 'task-2-1' in analyzer.task_graph['task-1-1']

        # Check reverse graph (task-2-3 is blocked by task-2-1 and task-2-2)
        assert 'task-2-1' in analyzer.reverse_graph['task-2-3']
        assert 'task-2-2' in analyzer.reverse_graph['task-2-3']

    def test_critical_path(self, sample_spec_data):
        """Test critical path detection correctly identifies longest dependency chain."""
        analyzer = SpecAnalyzer(sample_spec_data)
        critical_path = analyzer.get_critical_path()

        # Verify we got a path
        assert len(critical_path) > 0

        # First task should have no dependencies
        first_task = critical_path[0]
        assert len(analyzer.reverse_graph.get(first_task, [])) == 0

        # Path should be in valid execution order (all dependencies before dependents)
        for i, task_id in enumerate(critical_path[1:], 1):
            blockers = analyzer.reverse_graph.get(task_id, [])
            # All blockers should appear before this task in the path
            for blocker in blockers:
                if blocker in critical_path:
                    blocker_idx = critical_path.index(blocker)
                    assert blocker_idx < i, f"{blocker} should appear before {task_id}"

    def test_bottlenecks(self, sample_spec_data):
        """Test bottleneck detection identifies tasks blocking many others."""
        analyzer = SpecAnalyzer(sample_spec_data)
        bottlenecks = analyzer.get_bottlenecks(min_dependents=2)

        # Verify bottlenecks were found
        bottleneck_ids = [task_id for task_id, _ in bottlenecks]
        bottleneck_counts = {task_id: count for task_id, count in bottlenecks}

        # task-1-1 should be identified as a bottleneck
        assert 'task-1-1' in bottleneck_ids
        # Verify count is reasonable (>= 2 since that's our threshold)
        assert bottleneck_counts['task-1-1'] >= 2

    def test_topological_sort(self, sample_spec_data):
        """Test topological sort orders tasks correctly."""
        analyzer = SpecAnalyzer(sample_spec_data)
        topo_order = analyzer._topological_sort()

        # All tasks should be in the order
        task_ids = [t for t in sample_spec_data['hierarchy'].keys() if t != 'spec-root']
        assert len(topo_order) == len(task_ids)

        # Verify ordering: dependencies before dependents
        for i, task_id in enumerate(topo_order):
            dependents = analyzer.task_graph.get(task_id, [])
            for dependent in dependents:
                if dependent in topo_order:
                    dependent_idx = topo_order.index(dependent)
                    assert i < dependent_idx, f"{task_id} should come before {dependent}"

    def test_task_depth(self, sample_spec_data):
        """Test task depth calculation."""
        analyzer = SpecAnalyzer(sample_spec_data)

        # task-1-1 has no dependencies, depth should be 0
        depth_1_1 = analyzer.get_task_depth('task-1-1')
        assert depth_1_1 == 0

        # task-2-3 depends on task-2-1 and task-2-2, which depend on task-1-1 and task-1-2
        depth_2_3 = analyzer.get_task_depth('task-2-3')
        assert depth_2_3 >= 2  # At least 2 levels deep

    def test_parallelizable_tasks(self, sample_spec_data):
        """Test parallel task grouping."""
        analyzer = SpecAnalyzer(sample_spec_data)
        parallel_waves = analyzer.get_parallelizable_tasks(pending_only=False)

        # Should have multiple waves
        assert len(parallel_waves) > 0

        # First wave should include tasks with no dependencies
        first_wave = parallel_waves[0]
        for task_id in first_wave:
            blockers = analyzer.reverse_graph.get(task_id, [])
            # No blockers, or all blockers are completed
            for blocker in blockers:
                blocker_status = sample_spec_data['hierarchy'][blocker].get('status')
                assert blocker_status == 'completed'

    def test_stats(self, sample_spec_data):
        """Test statistics generation."""
        analyzer = SpecAnalyzer(sample_spec_data)
        stats = analyzer.get_stats()

        assert 'total_tasks' in stats
        assert 'total_dependencies' in stats
        assert 'max_fan_out' in stats
        assert 'max_fan_in' in stats
        assert 'has_cycles' in stats

        # Should have all tasks and phases (excluding spec-root)
        assert stats['total_tasks'] > 0  # Has tasks

        # Should not have cycles in this simple spec
        assert stats['has_cycles'] is False

    def test_empty_spec(self):
        """Test analyzer handles empty spec gracefully."""
        empty_spec = {
            "spec_id": "empty",
            "hierarchy": {"spec-root": {"id": "spec-root", "type": "spec"}}
        }
        analyzer = SpecAnalyzer(empty_spec)

        critical_path = analyzer.get_critical_path()
        assert critical_path == []

        bottlenecks = analyzer.get_bottlenecks()
        assert bottlenecks == []

        stats = analyzer.get_stats()
        assert stats['total_tasks'] == 0
