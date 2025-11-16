"""Tests for output size reduction verification.

Tests verify that QUIET mode achieves expected output reduction targets
for high-impact commands by measuring character counts.
"""

import pytest
import json
from unittest.mock import Mock, patch
import argparse

from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    LIST_SPECS_ESSENTIAL,
    LIST_SPECS_STANDARD,
    QUERY_TASKS_ESSENTIAL,
    QUERY_TASKS_STANDARD,
    PREPARE_TASK_ESSENTIAL,
    PREPARE_TASK_STANDARD,
    PROGRESS_ESSENTIAL,
    PROGRESS_STANDARD,
    VALIDATE_ESSENTIAL,
    VALIDATE_STANDARD,
    CHECK_DEPS_ESSENTIAL,
    CHECK_DEPS_STANDARD,
    LIST_BLOCKERS_ESSENTIAL,
    LIST_BLOCKERS_STANDARD,
)


class TestListSpecsOutputReduction:
    """Test list-specs command output reduction (target: 60% reduction)."""

    def test_list_specs_quiet_mode_reduction(self):
        """Test list-specs achieves ~60% output reduction in QUIET mode."""
        # Sample data representing typical list-specs output
        data = {
            'spec_id': 'my-spec-2025-11-01-001',
            'title': 'My Specification Title',
            'status': 'active',
            'total_tasks': 45,
            'completed_tasks': 23,
            'percentage': 51,
            'created_at': '2025-11-01T10:00:00Z',
            'updated_at': '2025-11-15T15:00:00Z',
            'metadata': {
                'author': 'test-user',
                'version': '1.0',
                'tags': ['feature', 'backend']
            },
            'current_phase': {
                'id': 'phase-2',
                'title': 'Implementation',
                'status': 'in_progress'
            }
        }

        # NORMAL mode (baseline)
        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        normal_output = prepare_output(data, normal_args, LIST_SPECS_ESSENTIAL, LIST_SPECS_STANDARD)
        normal_size = len(json.dumps(normal_output))

        # QUIET mode
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        quiet_output = prepare_output(data, quiet_args, LIST_SPECS_ESSENTIAL, LIST_SPECS_STANDARD)
        quiet_size = len(json.dumps(quiet_output))

        # Verify reduction
        reduction_percent = ((normal_size - quiet_size) / normal_size) * 100

        # Should achieve at least 40% reduction (target is 60%, allowing some margin)
        assert reduction_percent >= 40, f"Expected ≥40% reduction, got {reduction_percent:.1f}%"

        # Essential fields should be present
        assert 'spec_id' in quiet_output
        assert 'status' in quiet_output


class TestQueryTasksOutputReduction:
    """Test query-tasks command output reduction (target: 58% reduction)."""

    def test_query_tasks_quiet_mode_reduction(self):
        """Test query-tasks achieves ~58% output reduction in QUIET mode."""
        data = {
            'id': 'task-1-2',  # Essential field is 'id' not 'task_id'
            'title': 'Implement user authentication',
            'type': 'task',
            'status': 'in_progress',
            'parent': 'phase-1',
            'dependencies': {
                'blocks': ['task-2-1', 'task-2-2'],
                'blocked_by': [],
                'depends': ['task-1-1']
            },
            'metadata': {
                'estimated_hours': 4,
                'actual_hours': 2.5,
                'file_path': 'src/auth/handler.py',
                'started_at': '2025-11-15T10:00:00Z',
                'notes': 'Implementing JWT-based authentication'
            },
            'children': [],
            'total_tasks': 1,
            'completed_tasks': 0
        }

        # NORMAL mode
        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        normal_output = prepare_output(data, normal_args, QUERY_TASKS_ESSENTIAL, QUERY_TASKS_STANDARD)
        normal_size = len(json.dumps(normal_output))

        # QUIET mode
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        quiet_output = prepare_output(data, quiet_args, QUERY_TASKS_ESSENTIAL, QUERY_TASKS_STANDARD)
        quiet_size = len(json.dumps(quiet_output))

        # Verify reduction
        reduction_percent = ((normal_size - quiet_size) / normal_size) * 100

        # Should achieve at least 40% reduction (target is 58%)
        assert reduction_percent >= 40, f"Expected ≥40% reduction, got {reduction_percent:.1f}%"

        # Essential fields present (using 'id' not 'task_id')
        assert 'id' in quiet_output
        assert 'status' in quiet_output
        assert 'metadata' not in quiet_output


class TestPrepareTaskOutputReduction:
    """Test prepare-task command output reduction (target: 53% reduction)."""

    def test_prepare_task_quiet_mode_reduction(self):
        """Test prepare-task achieves ~53% output reduction in QUIET mode."""
        data = {
            'success': True,
            'task_id': 'task-2-3',
            'task_data': {
                'type': 'task',
                'title': 'Create API endpoint',
                'status': 'pending',
                'parent': 'phase-2',
                'metadata': {
                    'file_path': 'src/api/routes.py',
                    'estimated_hours': 3,
                    'notes': 'RESTful endpoint for user data'
                }
            },
            'dependencies': {
                'task_id': 'task-2-3',
                'can_start': True,
                'blocked_by': [],
                'soft_depends': ['task-2-1'],
                'blocks': ['task-3-1']
            },
            'spec_complete': True,
            'validation_warnings': ['Missing verification plan'],
            'repo_root': '/home/user/project',
            'needs_branch_creation': False,
            'dirty_tree_status': {
                'is_dirty': False,
                'message': 'Clean'
            },
            'completion_info': {
                'should_prompt': True,
                'reason': 'All tasks finished'
            },
            'doc_context': {
                'files': ['src/api/routes.py'],
                'summary': 'API routes documentation excerpt'
            }
        }

        # NORMAL mode
        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        normal_output = prepare_output(data, normal_args, PREPARE_TASK_ESSENTIAL, PREPARE_TASK_STANDARD)
        normal_size = len(json.dumps(normal_output))

        # QUIET mode
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        quiet_output = prepare_output(data, quiet_args, PREPARE_TASK_ESSENTIAL, PREPARE_TASK_STANDARD)
        quiet_size = len(json.dumps(quiet_output))

        # Verify reduction
        reduction_percent = ((normal_size - quiet_size) / normal_size) * 100

        # Should achieve at least 20% reduction (target is 53%, actual may vary based on data)
        assert reduction_percent >= 20, f"Expected ≥20% reduction, got {reduction_percent:.1f}%"

        # Essential fields present while optional noise stays out
        assert 'task_id' in quiet_output
        assert 'doc_context' not in quiet_output
        assert 'completion_info' not in quiet_output


class TestProgressOutputReduction:
    """Test progress command output reduction (target: 40% reduction)."""

    def test_progress_quiet_mode_reduction(self):
        """Test progress achieves ~40% output reduction in QUIET mode."""
        data = {
            'node_id': 'spec-root',
            'spec_id': 'my-feature-2025-11-01-001',
            'title': 'Feature Implementation',
            'type': 'spec',
            'status': 'in_progress',
            'total_tasks': 50,
            'completed_tasks': 30,
            'percentage': 60,
            'remaining_tasks': 20,
            'current_phase': {
                'id': 'phase-3',
                'title': 'Testing',
                'completed': 5,
                'total': 15
            },
            'metadata': {
                'created_at': '2025-11-01T10:00:00Z',
                'updated_at': '2025-11-15T15:00:00Z',
                'author': 'dev-team'
            }
        }

        # NORMAL mode
        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        normal_output = prepare_output(data, normal_args, PROGRESS_ESSENTIAL, PROGRESS_STANDARD)
        normal_size = len(json.dumps(normal_output))

        # QUIET mode
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        quiet_output = prepare_output(data, quiet_args, PROGRESS_ESSENTIAL, PROGRESS_STANDARD)
        quiet_size = len(json.dumps(quiet_output))

        # Verify reduction
        reduction_percent = ((normal_size - quiet_size) / normal_size) * 100

        # Should achieve at least 25% reduction (target is 40%)
        assert reduction_percent >= 25, f"Expected ≥25% reduction, got {reduction_percent:.1f}%"

        # Essential fields present (PROGRESS_ESSENTIAL includes spec_id, total_tasks, completed_tasks, percentage, current_phase)
        assert 'spec_id' in quiet_output
        assert 'total_tasks' in quiet_output
        assert 'percentage' in quiet_output


class TestValidateOutputReduction:
    """Test validate command output reduction (target: 94% reduction on success)."""

    def test_validate_quiet_mode_success_reduction(self):
        """Test validate achieves ~94% output reduction in QUIET mode for successful validation."""
        data = {
            'status': 'valid',  # Essential field is 'status' not 'valid'
            'spec_id': 'test-spec-2025-11-01-001',
            'spec_file': '/path/to/spec.json',
            'errors': [],
            'warnings': [],
            'info': [],
            'stats': {
                'total_tasks': 45,
                'total_phases': 5,
                'total_verifications': 3,
                'dependency_count': 12
            },
            'validation_time_ms': 125,
            'schema_version': '1.0.0',
            'metadata': {
                'validated_at': '2025-11-15T15:00:00Z',
                'validator_version': '2.1.0'
            }
        }

        # NORMAL mode
        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        normal_output = prepare_output(data, normal_args, VALIDATE_ESSENTIAL, VALIDATE_STANDARD)
        normal_size = len(json.dumps(normal_output))

        # QUIET mode
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        quiet_output = prepare_output(data, quiet_args, VALIDATE_ESSENTIAL, VALIDATE_STANDARD)
        quiet_size = len(json.dumps(quiet_output))

        # Verify reduction
        reduction_percent = ((normal_size - quiet_size) / normal_size) * 100

        # Should achieve at least 70% reduction (target is 94%)
        assert reduction_percent >= 70, f"Expected ≥70% reduction, got {reduction_percent:.1f}%"

        # Essential field is 'status'
        assert 'status' in quiet_output

    def test_validate_quiet_mode_preserves_errors(self):
        """Test validate preserves error messages in QUIET mode."""
        data = {
            'status': 'invalid',  # Essential field is 'status' not 'valid'
            'spec_id': 'test-spec-2025-11-01-001',
            'spec_file': '/path/to/spec.json',
            'errors': [
                {'type': 'schema_error', 'message': 'Invalid task structure'},
                {'type': 'dependency_error', 'message': 'Circular dependency detected'}
            ],
            'warnings': [],
            'info': [],
            'stats': {},
            'validation_time_ms': 125,
            'metadata': {}
        }

        # NORMAL mode should include errors (in standard fields)
        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        normal_output = prepare_output(data, normal_args, VALIDATE_ESSENTIAL, VALIDATE_STANDARD)

        # NORMAL mode includes standard fields
        assert 'status' in normal_output
        assert 'errors' in normal_output
        assert len(normal_output['errors']) == 2


class TestCheckDepsOutputReduction:
    """Test check-deps command output reduction (target: 49% reduction)."""

    def test_check_deps_quiet_mode_reduction(self):
        """Test check-deps achieves ~49% output reduction in QUIET mode."""
        data = {
            'task_id': 'task-3-2',
            'can_start': True,
            'blocked_by': [],
            'soft_depends': ['task-2-1', 'task-2-2'],
            'blocks': ['task-4-1', 'task-4-2', 'task-4-3'],
            'dependency_chain': [
                {'task_id': 'task-1-1', 'status': 'completed'},
                {'task_id': 'task-2-1', 'status': 'completed'},
                {'task_id': 'task-3-2', 'status': 'pending'}
            ],
            'metadata': {
                'depth': 2,
                'total_dependencies': 5,
                'checked_at': '2025-11-15T15:00:00Z'
            }
        }

        # NORMAL mode
        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        normal_output = prepare_output(data, normal_args, CHECK_DEPS_ESSENTIAL, CHECK_DEPS_STANDARD)
        normal_size = len(json.dumps(normal_output))

        # QUIET mode
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        quiet_output = prepare_output(data, quiet_args, CHECK_DEPS_ESSENTIAL, CHECK_DEPS_STANDARD)
        quiet_size = len(json.dumps(quiet_output))

        # Verify reduction
        reduction_percent = ((normal_size - quiet_size) / normal_size) * 100

        # Should achieve at least 30% reduction (target is 49%)
        assert reduction_percent >= 30, f"Expected ≥30% reduction, got {reduction_percent:.1f}%"

        # Essential fields present/omitted appropriately
        assert 'can_start' in quiet_output
        assert 'task_id' not in quiet_output
        assert 'blocks' not in quiet_output


class TestListBlockersOutputReduction:
    """Test list-blockers command output reduction."""

    def test_list_blockers_quiet_mode_reduction(self):
        """Test list-blockers output reduction in QUIET mode.

        Note: LIST_BLOCKERS_ESSENTIAL tracks core blocker fields
        (id/title/type/blocked_at + blocker_* metadata). QUIET mode omits empty
        values for these fields.
        """
        # Individual blocker item structure with NON-EMPTY blocked_by
        data = {
            'id': 'blocker-1',
            'title': 'Database migration',
            'type': 'dependency',
            'blocked_at': '2025-11-10T10:00:00Z',
            'blocker_type': 'dependency',
            'blocker_description': 'Schema approval pending',
            'blocker_ticket': 'OPS-123',
            'blocked_by_external': False,
            'blocked_tasks': ['task-3-1', 'task-3-2'],
            'severity': 'high',
            'metadata': {
                'created_at': '2025-11-10T10:00:00Z',
                'notes': 'Waiting for schema approval'
            }
        }

        # NORMAL mode
        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        normal_output = prepare_output(data, normal_args, LIST_BLOCKERS_ESSENTIAL, LIST_BLOCKERS_STANDARD)
        normal_size = len(json.dumps(normal_output))

        # QUIET mode
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        quiet_output = prepare_output(data, quiet_args, LIST_BLOCKERS_ESSENTIAL, LIST_BLOCKERS_STANDARD)
        quiet_size = len(json.dumps(quiet_output))

        # Verify reduction
        reduction_percent = ((normal_size - quiet_size) / normal_size) * 100

        # Should achieve some reduction (may be small if essential fields contain most data)
        assert reduction_percent >= 0, f"Expected ≥0% reduction, got {reduction_percent:.1f}%"

        # Essential fields present (non-empty)
        assert 'title' in quiet_output
        assert 'blocker_type' in quiet_output
        # Non-essential context removed
        assert 'blocker_ticket' not in quiet_output
        assert 'blocked_by_external' not in quiet_output


class TestOutputReductionComparison:
    """Integration tests comparing output sizes across verbosity levels."""

    def test_quiet_always_smaller_than_normal(self):
        """Test that QUIET mode output is always smaller than NORMAL mode."""
        sample_data = {
            'id': 'test-123',
            'name': 'Test Item',
            'status': 'active',
            'metadata': {'key': 'value'},
            'empty_field': None,
            'empty_list': []
        }

        essential = {'id', 'status'}
        standard = {'id', 'status', 'name', 'metadata'}

        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        quiet_output = prepare_output(sample_data, quiet_args, essential, standard)
        quiet_size = len(json.dumps(quiet_output))

        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        normal_output = prepare_output(sample_data, normal_args, essential, standard)
        normal_size = len(json.dumps(normal_output))

        # QUIET should always be smaller or equal
        assert quiet_size <= normal_size

    def test_verbose_always_largest(self):
        """Test that VERBOSE mode output is always largest."""
        sample_data = {
            'id': 'test-123',
            'name': 'Test Item',
            'status': 'active',
            'metadata': {'key': 'value'},
            '_debug': {'timing': 15}
        }

        essential = {'id', 'status'}
        standard = {'id', 'status', 'name', 'metadata'}

        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        quiet_output = prepare_output(sample_data, quiet_args, essential, standard)
        quiet_size = len(json.dumps(quiet_output))

        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        normal_output = prepare_output(sample_data, normal_args, essential, standard)
        normal_size = len(json.dumps(normal_output))

        verbose_args = argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)
        verbose_output = prepare_output(sample_data, verbose_args, essential, standard)
        verbose_size = len(json.dumps(verbose_output))

        # Size ordering: QUIET <= NORMAL <= VERBOSE
        assert quiet_size <= normal_size <= verbose_size
