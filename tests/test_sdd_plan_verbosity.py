"""Field filtering tests for sdd-plan commands."""

import argparse

from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    PLAN_CREATE_ESSENTIAL,
    PLAN_CREATE_STANDARD,
    PLAN_ANALYZE_ESSENTIAL,
    PLAN_ANALYZE_STANDARD,
    PLAN_TEMPLATE_LIST_ESSENTIAL,
    PLAN_TEMPLATE_LIST_STANDARD,
    PLAN_TEMPLATE_SHOW_ESSENTIAL,
    PLAN_TEMPLATE_SHOW_STANDARD,
)


def _quiet():
    return argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)


def _verbose():
    return argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)


class TestPlanCreateVerbosity:
    def test_quiet_mode_limits_fields(self):
        data = {
            'success': True,
            'spec_id': 'demo-001',
            'spec_path': '/tmp/specs/pending/demo-001.json',
            'message': 'Created',
            'template': 'simple',
            'phase_count': 2,
            'estimated_hours': 8,
            'default_category': 'implementation',
        }

        result = prepare_output(data, _quiet(), PLAN_CREATE_ESSENTIAL, PLAN_CREATE_STANDARD)
        assert set(result.keys()) == PLAN_CREATE_ESSENTIAL

    def test_verbose_mode_retains_metadata(self):
        data = {
            'success': True,
            'spec_id': 'demo-001',
            'spec_path': '/tmp/specs/pending/demo-001.json',
            'message': 'Created',
            'template': 'simple',
            'phase_count': 2,
            'estimated_hours': 8,
            'default_category': 'implementation',
        }

        result = prepare_output(data, _verbose(), PLAN_CREATE_ESSENTIAL, PLAN_CREATE_STANDARD)
        assert 'template' in result
        assert result['phase_count'] == 2


class TestPlanAnalyzeVerbosity:
    def test_quiet_mode_shows_summary(self):
        data = {
            'directory': '/repo',
            'has_specs': True,
            'specs_directory': '/repo/specs',
            'documentation_available': False,
            'analysis_success': False,
            'analysis_error': 'not installed',
            'doc_stats': {'total_modules': 5},
        }

        result = prepare_output(data, _quiet(), PLAN_ANALYZE_ESSENTIAL, PLAN_ANALYZE_STANDARD)
        assert 'specs_directory' not in result
        assert result['documentation_available'] is False

    def test_verbose_mode_shows_doc_stats(self):
        data = {
            'directory': '/repo',
            'has_specs': True,
            'specs_directory': '/repo/specs',
            'documentation_available': True,
            'analysis_success': True,
            'analysis_error': None,
            'doc_stats': {'total_modules': 5},
        }

        result = prepare_output(data, _verbose(), PLAN_ANALYZE_ESSENTIAL, PLAN_ANALYZE_STANDARD)
        assert 'doc_stats' in result
        assert result['doc_stats']['total_modules'] == 5


class TestPlanTemplateVerbosity:
    def test_template_list_quiet_only_returns_templates(self):
        data = {
            'templates': [{'id': 'simple', 'phases': 2}],
            'count': 1,
            'usage_hint': 'sdd create <name> --template simple',
        }

        result = prepare_output(data, _quiet(), PLAN_TEMPLATE_LIST_ESSENTIAL, PLAN_TEMPLATE_LIST_STANDARD)
        assert set(result.keys()) == {'templates'}

    def test_template_show_verbose_keeps_message(self):
        data = {
            'template_id': 'simple',
            'template': {'name': 'Simple Feature'},
            'message': 'ok',
        }

        result = prepare_output(data, _verbose(), PLAN_TEMPLATE_SHOW_ESSENTIAL, PLAN_TEMPLATE_SHOW_STANDARD)
        assert result['message'] == 'ok'
