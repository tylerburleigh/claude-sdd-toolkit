"""Verbosity filtering tests for sdd-spec-mod outputs."""

import argparse

from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    SPEC_MOD_APPLY_ESSENTIAL,
    SPEC_MOD_APPLY_STANDARD,
    SPEC_MOD_DRY_RUN_ESSENTIAL,
    SPEC_MOD_DRY_RUN_STANDARD,
    SPEC_MOD_PARSE_REVIEW_ESSENTIAL,
    SPEC_MOD_PARSE_REVIEW_STANDARD,
)


def _quiet():
    return argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)


def _verbose():
    return argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)


class TestApplyModificationsVerbosity:
    def test_apply_quiet_mode_minimum_fields(self):
        data = {
            'success': True,
            'spec_id': 'demo',
            'total_operations': 5,
            'successful_operations': 5,
            'failed_operations': 0,
            'dry_run': False,
            'output_file': '/tmp/spec.json',
        }

        filtered = prepare_output(data, _quiet(), SPEC_MOD_APPLY_ESSENTIAL, SPEC_MOD_APPLY_STANDARD)
        assert set(filtered.keys()) == SPEC_MOD_APPLY_ESSENTIAL

    def test_apply_verbose_includes_summary(self):
        data = {
            'success': True,
            'spec_id': 'demo',
            'total_operations': 5,
            'successful_operations': 5,
            'failed_operations': 0,
            'dry_run': False,
            'output_file': '/tmp/spec.json',
            'operation_summary': {'update_node_field': 3},
            'source_file': '/tmp/mods.json',
        }

        filtered = prepare_output(data, _verbose(), SPEC_MOD_APPLY_ESSENTIAL, SPEC_MOD_APPLY_STANDARD)
        assert filtered['operation_summary']['update_node_field'] == 3
        assert filtered['output_file'].endswith('spec.json')


class TestDryRunVerbosity:
    def test_dry_run_quiet_mode(self):
        data = {
            'spec_id': 'demo',
            'dry_run': True,
            'operation_count': 3,
            'sample_operations': [{'operation': 'add_node'}],
        }

        filtered = prepare_output(data, _quiet(), SPEC_MOD_DRY_RUN_ESSENTIAL, SPEC_MOD_DRY_RUN_STANDARD)
        assert 'sample_operations' not in filtered

    def test_dry_run_verbose_mode(self):
        data = {
            'spec_id': 'demo',
            'dry_run': True,
            'operation_count': 3,
            'sample_operations': [{'operation': 'add_node'}],
            'source_file': '/tmp/mods.json',
        }

        filtered = prepare_output(data, _verbose(), SPEC_MOD_DRY_RUN_ESSENTIAL, SPEC_MOD_DRY_RUN_STANDARD)
        assert len(filtered['sample_operations']) == 1
        assert filtered['source_file'].endswith('mods.json')


class TestParseReviewVerbosity:
    def test_parse_review_quiet_fields(self):
        data = {
            'spec_id': 'demo',
            'suggestion_count': 2,
            'issues_total': 4,
            'recommendation': 'REVISE',
            'display_mode': 'save',
            'issues_by_severity': {'critical': 1},
        }

        filtered = prepare_output(data, _quiet(), SPEC_MOD_PARSE_REVIEW_ESSENTIAL, SPEC_MOD_PARSE_REVIEW_STANDARD)
        assert set(filtered.keys()) == SPEC_MOD_PARSE_REVIEW_ESSENTIAL

    def test_parse_review_verbose_fields(self):
        data = {
            'spec_id': 'demo',
            'suggestion_count': 2,
            'issues_total': 4,
            'recommendation': 'REVISE',
            'display_mode': 'save',
            'issues_by_severity': {'critical': 1},
            'output_file': '/tmp/suggestions.json',
            'review_file': '/tmp/review.md',
        }

        filtered = prepare_output(data, _verbose(), SPEC_MOD_PARSE_REVIEW_ESSENTIAL, SPEC_MOD_PARSE_REVIEW_STANDARD)
        assert filtered['output_file'].endswith('suggestions.json')
        assert filtered['issues_by_severity']['critical'] == 1
