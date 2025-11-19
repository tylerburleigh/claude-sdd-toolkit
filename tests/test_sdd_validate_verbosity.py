"""Verbosity tests for sdd-validate field sets."""

import argparse

from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    VALIDATE_ESSENTIAL,
    VALIDATE_STANDARD,
    FIX_SPEC_ESSENTIAL,
    FIX_SPEC_STANDARD,
    STATS_ESSENTIAL,
    STATS_STANDARD,
    ANALYZE_DEPS_ESSENTIAL,
    ANALYZE_DEPS_STANDARD,
)


def _args(level):
    return argparse.Namespace(verbosity_level=level)


class TestValidateCommandVerbosity:
    def test_validate_quiet_mode(self):
        data = {
            'status': 'failed',
            'spec_id': 'spec-1',
            'errors': [{'id': 'err-1', 'message': 'Missing task'}],
            'warnings': [],
            'auto_fixable_issues': ['fix-1'],
            'schema': 'v2',
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), VALIDATE_ESSENTIAL, VALIDATE_STANDARD)
        assert 'schema' not in result
        assert 'errors' in result


class TestFixCommandVerbosity:
    def test_fix_quiet_mode(self):
        data = {
            'spec_id': 'spec-2',
            'applied_action_count': 3,
            'post_status': 'clean',
            'skipped_action_count': 1,
            'backup_path': '/tmp/spec.backup',
            'remaining_issues': ['issue'],
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), FIX_SPEC_ESSENTIAL, FIX_SPEC_STANDARD)
        assert set(result.keys()) == FIX_SPEC_ESSENTIAL


class TestStatsVerbosity:
    def test_stats_normal_mode(self):
        data = {
            'spec_id': 'spec-3',
            'totals': {'tasks': 30},
            'status_counts': {'pending': 10},
            'title': 'Spec title',
            'version': '1.0.0',
            'progress': 50,
        }
        result = prepare_output(data, _args(VerbosityLevel.NORMAL), STATS_ESSENTIAL, STATS_STANDARD)
        assert 'title' in result
        assert 'version' in result


class TestAnalyzeDepsVerbosity:
    def test_analyze_deps_quiet_mode(self):
        data = {
            'status': 'ok',
            'cycles': [],
            'orphaned': [],
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), ANALYZE_DEPS_ESSENTIAL, ANALYZE_DEPS_STANDARD)
        assert set(result.keys()) == ANALYZE_DEPS_ESSENTIAL
