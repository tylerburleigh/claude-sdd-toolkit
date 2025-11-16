"""Verbosity tests for sdd-next field sets."""

import argparse

from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    FIND_SPECS_ESSENTIAL,
    FIND_SPECS_STANDARD,
    NEXT_TASK_ESSENTIAL,
    NEXT_TASK_STANDARD,
    TASK_INFO_ESSENTIAL,
    TASK_INFO_STANDARD,
    FIND_PATTERN_ESSENTIAL,
    FIND_PATTERN_STANDARD,
    FIND_TESTS_ESSENTIAL,
    FIND_TESTS_STANDARD,
    FIND_RELATED_FILES_ESSENTIAL,
    FIND_RELATED_FILES_STANDARD,
    VALIDATE_PATHS_ESSENTIAL,
    VALIDATE_PATHS_STANDARD,
    SPEC_STATS_ESSENTIAL,
    SPEC_STATS_STANDARD,
    DETECT_PROJECT_ESSENTIAL,
    DETECT_PROJECT_STANDARD,
    FIND_CIRCULAR_DEPS_ESSENTIAL,
    FIND_CIRCULAR_DEPS_STANDARD,
    VALIDATE_SPEC_ESSENTIAL,
    VALIDATE_SPEC_STANDARD,
)


def _args(level):
    return argparse.Namespace(verbosity_level=level)


class TestFindSpecsVerbosity:
    def test_find_specs_quiet_mode(self):
        data = {
            'specs_dir': '/workspace/specs',
            'exists': True,
            'auto_detected': True,
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), FIND_SPECS_ESSENTIAL, FIND_SPECS_STANDARD)
        assert set(result.keys()) == FIND_SPECS_ESSENTIAL


class TestNextTaskVerbosity:
    def test_next_task_quiet_mode(self):
        data = {
            'task_id': 'task-1-1',
            'title': 'Implement login',
            'status': 'pending',
            'file_path': 'src/auth/login.py',
            'estimated_hours': 4,
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), NEXT_TASK_ESSENTIAL, NEXT_TASK_STANDARD)
        assert set(result.keys()) == NEXT_TASK_ESSENTIAL


class TestTaskInfoVerbosity:
    def test_task_info_quiet_mode(self):
        data = {
            'type': 'task',
            'title': 'Implement login',
            'status': 'pending',
            'dependencies': {'blocked_by': [], 'blocks': []},
            'metadata': {'file_path': 'src/auth/login.py'},
            'parent': 'phase-1',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), TASK_INFO_ESSENTIAL, TASK_INFO_STANDARD)
        assert 'parent' not in result
        assert 'dependencies' in result


class TestFindPatternVerbosity:
    def test_find_pattern_quiet_mode(self):
        data = {
            'pattern': 'auth.*',
            'matches': [
                {'file': 'src/auth/login.py', 'line': 10, 'preview': 'auth.login'}
            ],
            'search_time_ms': 45,
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), FIND_PATTERN_ESSENTIAL, FIND_PATTERN_STANDARD)
        assert 'pattern' in result
        assert 'matches' in result
        assert 'search_time_ms' not in result


class TestFindTestsVerbosity:
    def test_find_tests_quiet_mode(self):
        data = {
            'test_files': ['tests/test_login.py'],
            'unmatched': ['tests/test_signup.py'],
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), FIND_TESTS_ESSENTIAL, FIND_TESTS_STANDARD)
        assert 'test_files' in result
        assert 'unmatched' not in result


class TestFindRelatedFilesVerbosity:
    def test_find_related_files_quiet_mode(self):
        data = {
            'task_id': 'task-3-1',
            'related_files': ['src/api/users.py', 'src/api/auth.py'],
            'file_types': ['api', 'tests'],
            'relationships': {'depends_on': ['src/api/base.py']},
        }
        result = prepare_output(
            data, _args(VerbosityLevel.QUIET), FIND_RELATED_FILES_ESSENTIAL, FIND_RELATED_FILES_STANDARD
        )
        assert 'related_files' in result
        assert 'file_types' not in result


class TestValidatePathsVerbosity:
    def test_validate_paths_quiet_mode(self):
        data = {
            'valid': True,
            'invalid_paths': [],
            'validated_count': 5,
            'warnings': ['ignored symlink'],
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), VALIDATE_PATHS_ESSENTIAL, VALIDATE_PATHS_STANDARD)
        assert set(result.keys()) == {'valid'}


class TestSpecStatsVerbosity:
    def test_spec_stats_normal_vs_quiet(self):
        data = {
            'spec_id': 'spec-10',
            'total_tasks': 20,
            'completed_tasks': 8,
            'percentage': 40,
            'phases': [{'id': 'phase-1', 'percentage': 100}],
            'task_types': {'task': 10},
            'estimated_hours': 100,
            'actual_hours': 40,
        }
        quiet_result = prepare_output(data, _args(VerbosityLevel.QUIET), SPEC_STATS_ESSENTIAL, SPEC_STATS_STANDARD)
        assert set(quiet_result.keys()) == SPEC_STATS_ESSENTIAL
        verbose_result = prepare_output(data, _args(VerbosityLevel.VERBOSE), SPEC_STATS_ESSENTIAL, SPEC_STATS_STANDARD)
        assert 'estimated_hours' in verbose_result


class TestDetectProjectVerbosity:
    def test_detect_project_quiet_mode(self):
        data = {
            'project_type': 'python',
            'language_version': '3.11',
        }
        result = prepare_output(
            data, _args(VerbosityLevel.QUIET),
            DETECT_PROJECT_ESSENTIAL, DETECT_PROJECT_STANDARD
        )
        assert set(result.keys()) == DETECT_PROJECT_ESSENTIAL


class TestFindCircularDepsVerbosity:
    def test_find_circular_deps_quiet_mode(self):
        data = {
            'has_cycles': True,
            'cycles': [['task-1', 'task-2']],
            'metadata': {'checked_at': 'now'},
        }
        result = prepare_output(
            data, _args(VerbosityLevel.QUIET),
            FIND_CIRCULAR_DEPS_ESSENTIAL, FIND_CIRCULAR_DEPS_STANDARD
        )
        assert 'metadata' not in result
        assert set(result.keys()) == FIND_CIRCULAR_DEPS_ESSENTIAL


class TestValidateSpecVerbosity:
    def test_validate_spec_quiet_mode(self):
        data = {
            'valid': False,
            'errors': ['missing phase'],
            'warnings': ['typo'],
            'spec_id': 'spec-1',
        }
        result = prepare_output(
            data, _args(VerbosityLevel.QUIET),
            VALIDATE_SPEC_ESSENTIAL, VALIDATE_SPEC_STANDARD
        )
        assert 'warnings' not in result
        assert set(result.keys()) == VALIDATE_SPEC_ESSENTIAL
