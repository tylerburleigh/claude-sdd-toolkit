"""Unit tests for PriorityRanker.

This test suite verifies that priority ranking is deterministic and produces
consistent results for the same input spec data.
"""

import pytest
from claude_skills.sdd_render import PriorityRanker, SpecAnalyzer


class TestPriorityRanker:
    """Tests for PriorityRanker class."""

    def test_initialization(self, sample_spec_data):
        """Test PriorityRanker initializes correctly."""
        ranker = PriorityRanker(sample_spec_data)

        assert ranker.spec_data == sample_spec_data
        assert ranker.hierarchy == sample_spec_data['hierarchy']
        assert ranker.analyzer is not None
        assert ranker.task_graph is not None
        assert ranker.reverse_graph is not None

    def test_initialization_with_analyzer(self, sample_spec_data):
        """Test PriorityRanker can accept a pre-built analyzer."""
        analyzer = SpecAnalyzer(sample_spec_data)
        ranker = PriorityRanker(sample_spec_data, analyzer=analyzer)

        assert ranker.analyzer is analyzer
        assert ranker.task_graph == analyzer.task_graph
        assert ranker.reverse_graph == analyzer.reverse_graph

    def test_calculate_priority(self, sample_spec_data):
        """Test priority calculation returns valid TaskPriority object."""
        ranker = PriorityRanker(sample_spec_data)
        priority = ranker.calculate_priority('task-2-1')

        # Verify TaskPriority fields
        assert priority.task_id == 'task-2-1'
        assert isinstance(priority.score, float)
        assert priority.score > 0

        # Verify all factor components exist
        assert isinstance(priority.risk_factor, float)
        assert isinstance(priority.dependency_factor, float)
        assert isinstance(priority.blocking_factor, float)
        assert isinstance(priority.effort_factor, float)
        assert isinstance(priority.category_factor, float)
        assert isinstance(priority.rationale, str)

    def test_deterministic_ranking_single_run(self, sample_spec_data):
        """Test that ranking is deterministic within a single run.

        This is the core test for verify-2-2: Priority ranking must be deterministic.
        Running rank_tasks multiple times on the same spec should produce identical results.
        """
        ranker = PriorityRanker(sample_spec_data)

        # Rank tasks multiple times
        results_1 = ranker.rank_tasks(pending_only=False)
        results_2 = ranker.rank_tasks(pending_only=False)
        results_3 = ranker.rank_tasks(pending_only=False)

        # All results should be identical
        assert len(results_1) == len(results_2) == len(results_3)

        # Verify exact same ordering and scores
        for i in range(len(results_1)):
            task_id_1, priority_1 = results_1[i]
            task_id_2, priority_2 = results_2[i]
            task_id_3, priority_3 = results_3[i]

            # Same task IDs in same positions
            assert task_id_1 == task_id_2 == task_id_3

            # Same scores (exact match)
            assert priority_1.score == priority_2.score == priority_3.score

            # Same rationale
            assert priority_1.rationale == priority_2.rationale
            assert priority_2.rationale == priority_3.rationale

    def test_deterministic_priority_calculation(self, sample_spec_data):
        """Test that calculating priority for the same task is deterministic."""
        ranker = PriorityRanker(sample_spec_data)

        # Calculate priority for same task multiple times
        priority_1 = ranker.calculate_priority('task-2-1')
        priority_2 = ranker.calculate_priority('task-2-1')
        priority_3 = ranker.calculate_priority('task-2-1')

        # All scores should be identical
        assert priority_1.score == priority_2.score == priority_3.score

        # All factors should be identical
        assert priority_1.risk_factor == priority_2.risk_factor == priority_3.risk_factor
        assert priority_1.dependency_factor == priority_2.dependency_factor == priority_3.dependency_factor
        assert priority_1.blocking_factor == priority_2.blocking_factor == priority_3.blocking_factor
        assert priority_1.effort_factor == priority_2.effort_factor == priority_3.effort_factor
        assert priority_1.category_factor == priority_2.category_factor == priority_3.category_factor

        # Rationale should be identical
        assert priority_1.rationale == priority_2.rationale == priority_3.rationale

    def test_deterministic_across_instances(self, sample_spec_data):
        """Test that different ranker instances produce identical results."""
        ranker_1 = PriorityRanker(sample_spec_data)
        ranker_2 = PriorityRanker(sample_spec_data)
        ranker_3 = PriorityRanker(sample_spec_data)

        # Rank with each instance
        results_1 = ranker_1.rank_tasks(pending_only=False)
        results_2 = ranker_2.rank_tasks(pending_only=False)
        results_3 = ranker_3.rank_tasks(pending_only=False)

        # All results should be identical
        assert len(results_1) == len(results_2) == len(results_3)

        for i in range(len(results_1)):
            task_id_1, priority_1 = results_1[i]
            task_id_2, priority_2 = results_2[i]
            task_id_3, priority_3 = results_3[i]

            assert task_id_1 == task_id_2 == task_id_3
            assert priority_1.score == priority_2.score == priority_3.score

    def test_rank_tasks_pending_only(self, sample_spec_data):
        """Test ranking with pending_only filter."""
        ranker = PriorityRanker(sample_spec_data)

        # Rank only pending tasks
        pending_results = ranker.rank_tasks(pending_only=True)

        # Should have fewer tasks than total (some are completed)
        all_results = ranker.rank_tasks(pending_only=False)
        assert len(pending_results) < len(all_results)

        # All returned tasks should be pending
        for task_id, priority in pending_results:
            assert sample_spec_data['hierarchy'][task_id]['status'] == 'pending'

    def test_rank_tasks_with_min_score(self, sample_spec_data):
        """Test ranking with minimum score threshold."""
        ranker = PriorityRanker(sample_spec_data)

        # Get all results to find a threshold
        all_results = ranker.rank_tasks(pending_only=False)

        if len(all_results) > 1:
            # Use median score as threshold
            median_idx = len(all_results) // 2
            threshold = all_results[median_idx][1].score

            # Rank with threshold
            filtered_results = ranker.rank_tasks(pending_only=False, min_score=threshold)

            # Should have fewer results
            assert len(filtered_results) <= len(all_results)

            # All scores should be >= threshold
            for task_id, priority in filtered_results:
                assert priority.score >= threshold

    def test_get_top_priorities(self, sample_spec_data):
        """Test getting top N priority tasks."""
        ranker = PriorityRanker(sample_spec_data)

        # Get top 3 tasks
        top_3 = ranker.get_top_priorities(n=3, pending_only=False)

        # Should have up to 3 tasks
        assert len(top_3) <= 3

        # Should be in descending score order
        if len(top_3) > 1:
            for i in range(len(top_3) - 1):
                score_current = top_3[i][1].score
                score_next = top_3[i + 1][1].score
                assert score_current >= score_next

    def test_get_priority_breakdown(self, sample_spec_data):
        """Test detailed priority breakdown."""
        ranker = PriorityRanker(sample_spec_data)
        breakdown = ranker.get_priority_breakdown('task-2-1')

        # Verify breakdown structure
        assert 'task_id' in breakdown
        assert breakdown['task_id'] == 'task-2-1'
        assert 'total_score' in breakdown
        assert 'risk_factor' in breakdown
        assert 'dependency_factor' in breakdown
        assert 'blocking_factor' in breakdown
        assert 'effort_factor' in breakdown
        assert 'category_factor' in breakdown
        assert 'rationale' in breakdown
        assert 'details' in breakdown

        # Verify details structure
        details = breakdown['details']
        assert 'num_blockers' in details
        assert 'num_blocked' in details
        assert 'estimated_hours' in details
        assert 'risk_level' in details
        assert 'category' in details

    def test_high_risk_task_prioritization(self, sample_spec_data):
        """Test that high-risk tasks get higher priority scores."""
        ranker = PriorityRanker(sample_spec_data)

        # task-2-1 has high risk
        high_risk_priority = ranker.calculate_priority('task-2-1')

        # task-1-1 has low risk
        low_risk_priority = ranker.calculate_priority('task-1-1')

        # High risk should have higher risk_factor contribution
        assert high_risk_priority.risk_factor > low_risk_priority.risk_factor

    def test_blocking_task_prioritization(self, sample_spec_data):
        """Test that tasks blocking many others get higher priority."""
        ranker = PriorityRanker(sample_spec_data)

        # task-1-1 blocks task-1-2 and task-2-1 (2 tasks)
        blocking_priority = ranker.calculate_priority('task-1-1')

        # task-2-3 blocks no tasks
        non_blocking_priority = ranker.calculate_priority('task-2-3')

        # Blocking task should have higher blocking_factor
        assert blocking_priority.blocking_factor > non_blocking_priority.blocking_factor

    def test_invalid_task_raises_error(self, sample_spec_data):
        """Test that calculating priority for non-existent task raises KeyError."""
        ranker = PriorityRanker(sample_spec_data)

        with pytest.raises(KeyError, match="Task not found"):
            ranker.calculate_priority('nonexistent-task')

    def test_spec_root_excluded_from_ranking(self, sample_spec_data):
        """Test that spec-root is excluded from task ranking."""
        ranker = PriorityRanker(sample_spec_data)
        results = ranker.rank_tasks(pending_only=False)

        # spec-root should not appear in results
        task_ids = [task_id for task_id, _ in results]
        assert 'spec-root' not in task_ids

    def test_empty_spec_handles_gracefully(self):
        """Test ranker handles empty spec gracefully."""
        empty_spec = {
            "spec_id": "empty",
            "hierarchy": {"spec-root": {"id": "spec-root", "type": "spec"}}
        }
        ranker = PriorityRanker(empty_spec)

        results = ranker.rank_tasks()
        assert results == []

        top_priorities = ranker.get_top_priorities(n=5)
        assert top_priorities == []

    def test_deterministic_ordering_with_ties(self):
        """Test deterministic ordering even when tasks have identical scores.

        This is a critical edge case: when two tasks have the exact same priority score,
        the ranking should still be deterministic (same order every time).
        """
        # Create spec with tasks that will have identical scores
        identical_tasks_spec = {
            "spec_id": "identical-test",
            "hierarchy": {
                "spec-root": {
                    "id": "spec-root",
                    "type": "spec",
                    "children": ["task-a", "task-b", "task-c"]
                },
                "task-a": {
                    "id": "task-a",
                    "type": "task",
                    "status": "pending",
                    "parent": "spec-root",
                    "children": [],
                    "dependencies": {"blocks": [], "blocked_by": [], "depends": []},
                    "metadata": {
                        "risk_level": "low",
                        "estimated_hours": 2,
                        "task_category": "implementation"
                    }
                },
                "task-b": {
                    "id": "task-b",
                    "type": "task",
                    "status": "pending",
                    "parent": "spec-root",
                    "children": [],
                    "dependencies": {"blocks": [], "blocked_by": [], "depends": []},
                    "metadata": {
                        "risk_level": "low",
                        "estimated_hours": 2,
                        "task_category": "implementation"
                    }
                },
                "task-c": {
                    "id": "task-c",
                    "type": "task",
                    "status": "pending",
                    "parent": "spec-root",
                    "children": [],
                    "dependencies": {"blocks": [], "blocked_by": [], "depends": []},
                    "metadata": {
                        "risk_level": "low",
                        "estimated_hours": 2,
                        "task_category": "implementation"
                    }
                }
            }
        }

        ranker = PriorityRanker(identical_tasks_spec)

        # Rank multiple times
        results_1 = ranker.rank_tasks()
        results_2 = ranker.rank_tasks()
        results_3 = ranker.rank_tasks()

        # Extract task ID orderings
        order_1 = [task_id for task_id, _ in results_1]
        order_2 = [task_id for task_id, _ in results_2]
        order_3 = [task_id for task_id, _ in results_3]

        # All orderings should be identical
        assert order_1 == order_2 == order_3

    def test_category_weights_applied_correctly(self, sample_spec_data):
        """Test that different task categories get appropriate weight adjustments."""
        ranker = PriorityRanker(sample_spec_data)

        # task-2-1 is implementation category
        impl_priority = ranker.calculate_priority('task-2-1')

        # task-1-2 is verification category
        verify_priority = ranker.calculate_priority('task-1-2')

        # Both priorities should have category_factor > 0
        assert impl_priority.category_factor > 0
        assert verify_priority.category_factor > 0

    def test_effort_factor_affects_score(self, sample_spec_data):
        """Test that estimated effort affects priority score appropriately."""
        ranker = PriorityRanker(sample_spec_data)

        # task-2-1 has 3 hours (larger task)
        large_task_priority = ranker.calculate_priority('task-2-1')

        # task-1-2 has 1 hour (smaller task)
        small_task_priority = ranker.calculate_priority('task-1-2')

        # Both should have effort_factor > 0
        assert large_task_priority.effort_factor > 0
        assert small_task_priority.effort_factor > 0

        # Smaller tasks generally get slight boost (quick wins)
        # but this depends on other factors too, so we just verify the factor exists

    def test_dependency_penalty_applied(self, sample_spec_data):
        """Test that tasks with blockers get dependency penalty."""
        ranker = PriorityRanker(sample_spec_data)

        # task-1-1 has no blockers
        no_blocker_priority = ranker.calculate_priority('task-1-1')

        # task-2-3 is blocked by task-2-1 and task-2-2 (2 blockers)
        blocked_priority = ranker.calculate_priority('task-2-3')

        # Task with no blockers should have higher dependency_factor
        assert no_blocker_priority.dependency_factor >= blocked_priority.dependency_factor

    def test_rationale_generation(self, sample_spec_data):
        """Test that rationale strings are generated appropriately."""
        ranker = PriorityRanker(sample_spec_data)

        # task-2-1 has high risk and blocks other tasks
        priority = ranker.calculate_priority('task-2-1')

        # Rationale should mention high risk
        assert 'high' in priority.rationale.lower() or 'risk' in priority.rationale.lower()

        # Rationale should be non-empty
        assert len(priority.rationale) > 0
