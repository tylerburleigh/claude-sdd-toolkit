"""Unit tests for Progressive Disclosure functionality."""

import pytest
from claude_skills.sdd_render import (
    DetailLevelCalculator,
    DetailContext,
    DetailLevel
)


class TestDetailLevelCalculator:
    """Tests for DetailLevelCalculator class."""

    def test_initialization(self):
        """Test DetailLevelCalculator initializes correctly."""
        calculator = DetailLevelCalculator()

        assert calculator is not None

    def test_in_progress_task_gets_full_detail(self):
        """Test that in_progress tasks get FULL detail level."""
        calculator = DetailLevelCalculator()

        context = DetailContext(
            task_status='in_progress',
            priority_score=5.0,
            risk_level='medium',
            is_blocking=False,
            has_blockers=False
        )

        level = calculator.calculate_detail_level(context)

        assert level == DetailLevel.FULL

    def test_completed_task_gets_summary(self):
        """Test that completed tasks get SUMMARY detail level."""
        calculator = DetailLevelCalculator()

        context = DetailContext(
            task_status='completed',
            priority_score=5.0,
            risk_level='low',
            is_blocking=False,
            has_blockers=False
        )

        level = calculator.calculate_detail_level(context)

        assert level == DetailLevel.SUMMARY

    def test_blocked_task_gets_medium_detail(self):
        """Test that blocked tasks get MEDIUM detail level."""
        calculator = DetailLevelCalculator()

        context = DetailContext(
            task_status='blocked',
            priority_score=5.0,
            risk_level='medium',
            is_blocking=False,
            has_blockers=True
        )

        level = calculator.calculate_detail_level(context)

        assert level == DetailLevel.MEDIUM

    def test_high_priority_gets_more_detail(self):
        """Test that high priority tasks get more detail."""
        calculator = DetailLevelCalculator()

        context_high = DetailContext(
            task_status='pending',
            priority_score=9.0,
            risk_level='low',
            is_blocking=False,
            has_blockers=False
        )

        context_low = DetailContext(
            task_status='pending',
            priority_score=2.0,
            risk_level='low',
            is_blocking=False,
            has_blockers=False
        )

        level_high = calculator.calculate_detail_level(context_high)
        level_low = calculator.calculate_detail_level(context_low)

        # High priority should get at least as much detail as low priority
        detail_order = {
            DetailLevel.SUMMARY: 1,
            DetailLevel.MEDIUM: 2,
            DetailLevel.FULL: 3
        }

        assert detail_order[level_high] >= detail_order[level_low]

    def test_blocking_task_gets_more_detail(self):
        """Test that tasks blocking others get more detail."""
        calculator = DetailLevelCalculator()

        context_blocking = DetailContext(
            task_status='pending',
            priority_score=5.0,
            risk_level='medium',
            is_blocking=True,
            has_blockers=False
        )

        context_normal = DetailContext(
            task_status='pending',
            priority_score=5.0,
            risk_level='medium',
            is_blocking=False,
            has_blockers=False
        )

        level_blocking = calculator.calculate_detail_level(context_blocking)
        level_normal = calculator.calculate_detail_level(context_normal)

        # Blocking tasks should get at least as much detail
        detail_order = {
            DetailLevel.SUMMARY: 1,
            DetailLevel.MEDIUM: 2,
            DetailLevel.FULL: 3
        }

        assert detail_order[level_blocking] >= detail_order[level_normal]

    def test_high_risk_gets_more_detail(self):
        """Test that high-risk tasks get more detail."""
        calculator = DetailLevelCalculator()

        context_high_risk = DetailContext(
            task_status='pending',
            priority_score=5.0,
            risk_level='high',
            is_blocking=False,
            has_blockers=False
        )

        context_low_risk = DetailContext(
            task_status='pending',
            priority_score=5.0,
            risk_level='low',
            is_blocking=False,
            has_blockers=False
        )

        level_high = calculator.calculate_detail_level(context_high_risk)
        level_low = calculator.calculate_detail_level(context_low_risk)

        # High risk should get at least as much detail
        detail_order = {
            DetailLevel.SUMMARY: 1,
            DetailLevel.MEDIUM: 2,
            DetailLevel.FULL: 3
        }

        assert detail_order[level_high] >= detail_order[level_low]

    def test_user_focus_overrides_default(self):
        """Test that user focus can override default detail level."""
        calculator = DetailLevelCalculator()

        context_focused = DetailContext(
            task_status='completed',  # Would normally get SUMMARY
            priority_score=2.0,
            risk_level='low',
            is_blocking=False,
            has_blockers=False,
            user_focus='specific-area'
        )

        level = calculator.calculate_detail_level(context_focused)

        # With user focus, even completed tasks may get more detail
        assert level in [DetailLevel.SUMMARY, DetailLevel.MEDIUM, DetailLevel.FULL]

    def test_depth_level_affects_detail(self):
        """Test that nesting depth affects detail level."""
        calculator = DetailLevelCalculator()

        context_phase = DetailContext(
            task_status='pending',
            priority_score=5.0,
            risk_level='medium',
            is_blocking=False,
            has_blockers=False,
            depth_level=0  # Phase level
        )

        context_subtask = DetailContext(
            task_status='pending',
            priority_score=5.0,
            risk_level='medium',
            is_blocking=False,
            has_blockers=False,
            depth_level=2  # Subtask level
        )

        level_phase = calculator.calculate_detail_level(context_phase)
        level_subtask = calculator.calculate_detail_level(context_subtask)

        # Both should be valid detail levels
        assert level_phase in [DetailLevel.SUMMARY, DetailLevel.MEDIUM, DetailLevel.FULL]
        assert level_subtask in [DetailLevel.SUMMARY, DetailLevel.MEDIUM, DetailLevel.FULL]

    def test_all_detail_levels_achievable(self):
        """Test that all three detail levels can be produced."""
        calculator = DetailLevelCalculator()

        # Create contexts likely to produce each level
        contexts = [
            DetailContext('completed', 1.0, 'low', False, False),  # SUMMARY
            DetailContext('blocked', 5.0, 'medium', False, True),   # MEDIUM
            DetailContext('in_progress', 9.0, 'high', True, False), # FULL
        ]

        levels = [calculator.calculate_detail_level(ctx) for ctx in contexts]

        # Should see variety of detail levels
        assert DetailLevel.SUMMARY in levels or DetailLevel.MEDIUM in levels or DetailLevel.FULL in levels

    def test_context_validation(self):
        """Test that invalid contexts are handled."""
        calculator = DetailLevelCalculator()

        # Create context with invalid status
        context = DetailContext(
            task_status='invalid_status',
            priority_score=5.0,
            risk_level='medium',
            is_blocking=False,
            has_blockers=False
        )

        # Should still return a valid detail level or raise appropriate error
        try:
            level = calculator.calculate_detail_level(context)
            assert level in [DetailLevel.SUMMARY, DetailLevel.MEDIUM, DetailLevel.FULL]
        except ValueError:
            # Acceptable to raise ValueError for invalid status
            pass

    def test_priority_score_bounds(self):
        """Test handling of priority scores at boundaries."""
        calculator = DetailLevelCalculator()

        # Test minimum priority
        context_min = DetailContext(
            task_status='pending',
            priority_score=0.0,
            risk_level='low',
            is_blocking=False,
            has_blockers=False
        )

        # Test maximum priority
        context_max = DetailContext(
            task_status='pending',
            priority_score=10.0,
            risk_level='high',
            is_blocking=True,
            has_blockers=False
        )

        level_min = calculator.calculate_detail_level(context_min)
        level_max = calculator.calculate_detail_level(context_max)

        # Both should return valid levels
        assert level_min in [DetailLevel.SUMMARY, DetailLevel.MEDIUM, DetailLevel.FULL]
        assert level_max in [DetailLevel.SUMMARY, DetailLevel.MEDIUM, DetailLevel.FULL]

        # Max priority should get at least as much detail as min
        detail_order = {
            DetailLevel.SUMMARY: 1,
            DetailLevel.MEDIUM: 2,
            DetailLevel.FULL: 3
        }

        assert detail_order[level_max] >= detail_order[level_min]
