"""Verbosity tests for support skills (run-tests, code-doc, cache/context, plan-review)."""

import argparse

from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    RUN_TESTS_CHECK_TOOLS_ESSENTIAL,
    RUN_TESTS_CHECK_TOOLS_STANDARD,
    RUN_TESTS_CONSULT_ESSENTIAL,
    RUN_TESTS_CONSULT_STANDARD,
    RUN_TESTS_RUN_ESSENTIAL,
    RUN_TESTS_RUN_STANDARD,
    DOC_GENERATE_ESSENTIAL,
    DOC_GENERATE_STANDARD,
    DOC_VALIDATE_ESSENTIAL,
    DOC_VALIDATE_STANDARD,
    DOC_ANALYZE_ESSENTIAL,
    DOC_ANALYZE_STANDARD,
    CONTEXT_ESSENTIAL,
    CONTEXT_STANDARD,
    CACHE_CLEAR_ESSENTIAL,
    CACHE_CLEAR_STANDARD,
    CACHE_STATS_ESSENTIAL,
    CACHE_STATS_STANDARD,
    LIST_TOOLS_ESSENTIAL,
    LIST_TOOLS_STANDARD,
    PLAN_REVIEW_SUMMARY_ESSENTIAL,
    PLAN_REVIEW_SUMMARY_STANDARD,
)


def _quiet():
    return argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)


def _normal():
    return argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)


def _verbose():
    return argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)


class TestRunTestsVerbosity:
    def test_check_tools_quiet_mode(self):
        data = {
            'tools': ['pytest', 'coverage'],
            'available_count': 1,
            'available_tools': ['pytest'],
        }
        result = prepare_output(data, _quiet(), RUN_TESTS_CHECK_TOOLS_ESSENTIAL, RUN_TESTS_CHECK_TOOLS_STANDARD)
        assert 'tools' not in result
        assert set(result.keys()) == RUN_TESTS_CHECK_TOOLS_ESSENTIAL

    def test_consult_quiet_mode(self):
        data = {
            'status': 'error',
            'message': 'AssertionError',
            'details': 'stack trace',
        }
        result = prepare_output(data, _quiet(), RUN_TESTS_CONSULT_ESSENTIAL, RUN_TESTS_CONSULT_STANDARD)
        assert set(result.keys()) == RUN_TESTS_CONSULT_ESSENTIAL

    def test_run_verbose_mode(self):
        data = {
            'status': 'error',
            'message': 'pytest exited 1',
            'details': {'exit_code': 1},
        }
        result = prepare_output(data, _verbose(), RUN_TESTS_RUN_ESSENTIAL, RUN_TESTS_RUN_STANDARD)
        assert 'details' in result


class TestCodeDocVerbosity:
    def test_generate_quiet_mode(self):
        data = {
            'status': 'success',
            'project': 'sample',
            'output_dir': './docs',
            'format': 'markdown',
        }
        result = prepare_output(data, _quiet(), DOC_GENERATE_ESSENTIAL, DOC_GENERATE_STANDARD)
        assert set(result.keys()) == DOC_GENERATE_ESSENTIAL

    def test_validate_verbose_mode_includes_schema(self):
        data = {
            'status': 'error',
            'message': 'Schema mismatch',
            'schema': 'v2',
        }
        result = prepare_output(data, _verbose(), DOC_VALIDATE_ESSENTIAL, DOC_VALIDATE_STANDARD)
        assert 'schema' in result

    def test_analyze_normal_mode(self):
        data = {
            'status': 'success',
            'project': 'sample',
            'statistics': {'files': 100},
        }
        result = prepare_output(data, _normal(), DOC_ANALYZE_ESSENTIAL, DOC_ANALYZE_STANDARD)
        assert set(result.keys()) == DOC_ANALYZE_ESSENTIAL


class TestContextAndCacheVerbosity:
    def test_context_quiet_mode(self):
        data = {
            'context_percentage_used': 42,
            'context_length': 20000,
            'max_context': 32000,
        }
        result = prepare_output(data, _quiet(), CONTEXT_ESSENTIAL, CONTEXT_STANDARD)
        assert set(result.keys()) == CONTEXT_ESSENTIAL

    def test_cache_clear_quiet(self):
        data = {
            'entries_deleted': 21,
            'filters': {'spec': 'auth'},
        }
        result = prepare_output(data, _quiet(), CACHE_CLEAR_ESSENTIAL, CACHE_CLEAR_STANDARD)
        assert set(result.keys()) == CACHE_CLEAR_ESSENTIAL

    def test_cache_stats_verbose(self):
        data = {
            'total_entries': 50,
            'active_entries': 20,
            'cache_dir': '/tmp/cache',
            'expired_entries': 5,
            'total_size_mb': 12.3,
            'total_size_bytes': 12900000,
        }
        result = prepare_output(data, _verbose(), CACHE_STATS_ESSENTIAL, CACHE_STATS_STANDARD)
        assert 'cache_dir' in result
        assert 'expired_entries' in result


class TestPlanReviewVerbosity:
    def test_list_tools_quiet_mode(self):
        data = {
            'available_count': 2,
            'total': 3,
            'available': ['gemini', 'codex'],
            'unavailable': ['cursor'],
        }
        result = prepare_output(data, _quiet(), LIST_TOOLS_ESSENTIAL, LIST_TOOLS_STANDARD)
        assert set(result.keys()) == LIST_TOOLS_ESSENTIAL

    def test_list_tools_verbose_mode(self):
        data = {
            'available_count': 2,
            'total': 3,
            'available': ['gemini', 'codex'],
            'unavailable': ['cursor'],
        }
        result = prepare_output(data, _verbose(), LIST_TOOLS_ESSENTIAL, LIST_TOOLS_STANDARD)
        assert 'available' in result
        assert 'unavailable' in result

    def test_review_summary_quiet_mode(self):
        data = {
            'spec_id': 'demo',
            'review_type': 'full',
            'recommendation': 'APPROVE',
            'artifacts': ['review.md'],
            'issue_count': 2,
            'models_responded': 3,
            'models_requested': 4,
            'dry_run': False,
        }
        result = prepare_output(data, _quiet(), PLAN_REVIEW_SUMMARY_ESSENTIAL, PLAN_REVIEW_SUMMARY_STANDARD)
        assert set(result.keys()) == PLAN_REVIEW_SUMMARY_ESSENTIAL

    def test_review_summary_verbose_mode(self):
        data = {
            'spec_id': 'demo',
            'review_type': 'full',
            'recommendation': 'REVISE',
            'artifacts': ['review.md'],
            'issue_count': 5,
            'models_responded': 2,
            'models_requested': 4,
            'models_consulted': {'gemini': 'pro'},
            'failures': 1,
            'execution_time': 23.5,
            'consensus_level': 'moderate',
            'dimension_scores': {'clarity': 8},
            'dry_run': False,
        }
        result = prepare_output(data, _verbose(), PLAN_REVIEW_SUMMARY_ESSENTIAL, PLAN_REVIEW_SUMMARY_STANDARD)
        assert 'models_consulted' in result
        assert 'execution_time' in result
