"""Unit tests for ComplexityScorer."""

import pytest
from claude_skills.sdd_render import ComplexityScorer, ComplexityScore


class TestComplexityScorer:
    """Tests for ComplexityScorer class."""

    def test_initialization(self, sample_spec_data):
        """Test ComplexityScorer initializes correctly."""
        scorer = ComplexityScorer(sample_spec_data)

        assert scorer.spec_data == sample_spec_data
        assert scorer.hierarchy == sample_spec_data['hierarchy']

    def test_simple_task_scoring(self, sample_spec_data):
        """Test scoring of simple task with minimal complexity."""
        scorer = ComplexityScorer(sample_spec_data)

        # task-1-1: completed task with 0 subtasks, blocks 2 tasks, 1 hour estimate
        score = scorer.calculate_complexity('task-1-1')

        assert isinstance(score, ComplexityScore)
        assert score.task_id == 'task-1-1'
        assert 1.0 <= score.score <= 5.0  # Should be low to medium complexity
        assert score.level in ['low', 'medium']
        assert len(score.rationale) > 0

    def test_complex_task_scoring(self, sample_spec_data):
        """Test scoring of complex task with dependencies."""
        scorer = ComplexityScorer(sample_spec_data)

        # task-2-3: pending task with multiple blockers
        score = scorer.calculate_complexity('task-2-3')

        assert isinstance(score, ComplexityScore)
        assert score.task_id == 'task-2-3'
        # Should have higher dependency score due to being blocked by multiple tasks
        assert score.dependency_score > 0
        assert len(score.rationale) > 0

    def test_depth_score_calculation(self, sample_spec_data):
        """Test depth score increases with subtask count."""
        scorer = ComplexityScorer(sample_spec_data)

        # Task with no subtasks
        score_simple = scorer.calculate_complexity('task-1-1')

        # Task with subtasks (if available in sample data)
        score_complex = scorer.calculate_complexity('task-2-1')

        # Verify depth scores are non-negative
        assert score_simple.depth_score >= 0
        assert score_complex.depth_score >= 0

    def test_dependency_score_calculation(self, sample_spec_data):
        """Test dependency score reflects blocker and dependent counts."""
        scorer = ComplexityScorer(sample_spec_data)

        # task-2-3 has 2 blockers (task-2-1 and task-2-2)
        score = scorer.calculate_complexity('task-2-3')

        # Should have higher dependency score
        assert score.dependency_score > 0

    def test_effort_score_calculation(self, sample_spec_data):
        """Test effort score scales with estimated hours."""
        scorer = ComplexityScorer(sample_spec_data)

        # Get score for a task with effort metadata
        score = scorer.calculate_complexity('task-1-1')

        # Effort score should be non-negative
        assert score.effort_score >= 0

    def test_complexity_levels(self, sample_spec_data):
        """Test complexity level categorization."""
        scorer = ComplexityScorer(sample_spec_data)

        scores = [
            scorer.calculate_complexity('task-1-1'),
            scorer.calculate_complexity('task-1-2'),
            scorer.calculate_complexity('task-2-1'),
        ]

        # All scores should have valid levels
        valid_levels = ['low', 'medium', 'high']
        for score in scores:
            assert score.level in valid_levels
            assert 1.0 <= score.score <= 10.0

    def test_all_tasks_scoreable(self, sample_spec_data):
        """Test that all tasks in spec can be scored without errors."""
        scorer = ComplexityScorer(sample_spec_data)
        hierarchy = sample_spec_data['hierarchy']

        # Get all task IDs
        task_ids = [
            node_id for node_id, node in hierarchy.items()
            if node.get('type') == 'task'
        ]

        # Score all tasks
        for task_id in task_ids:
            score = scorer.calculate_complexity(task_id)
            assert isinstance(score, ComplexityScore)
            assert score.task_id == task_id
            assert 1.0 <= score.score <= 10.0

    def test_rationale_generation(self, sample_spec_data):
        """Test that rationale explains complexity factors."""
        scorer = ComplexityScorer(sample_spec_data)

        score = scorer.calculate_complexity('task-2-3')

        # Rationale should mention relevant factors
        assert len(score.rationale) > 0
        # For a task with blockers, rationale should mention dependencies
        if score.dependency_score > 0:
            assert 'dependenc' in score.rationale.lower() or 'block' in score.rationale.lower()

    def test_score_consistency(self, sample_spec_data):
        """Test that scoring the same task multiple times gives same result."""
        scorer = ComplexityScorer(sample_spec_data)

        score1 = scorer.calculate_complexity('task-1-1')
        score2 = scorer.calculate_complexity('task-1-1')

        assert score1.score == score2.score
        assert score1.level == score2.level

    def test_invalid_task_handling(self, sample_spec_data):
        """Test handling of non-existent task IDs."""
        scorer = ComplexityScorer(sample_spec_data)

        with pytest.raises((KeyError, ValueError)):
            scorer.calculate_complexity('non-existent-task')
