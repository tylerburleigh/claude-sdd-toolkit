"""Verbosity tests for sdd-plan-review field sets."""

import argparse

from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    FORMAT_VERIFICATION_SUMMARY_ESSENTIAL,
    FORMAT_VERIFICATION_SUMMARY_STANDARD,
    FORMAT_PLAN_ESSENTIAL,
    FORMAT_PLAN_STANDARD,
)


def _args(level):
    return argparse.Namespace(verbosity_level=level)


class TestFormatVerificationSummaryVerbosity:
    def test_quiet_mode_only_returns_formatted_text(self):
        data = {
            'formatted': '# Summary',
            'spec_id': 'spec-1',
            'total_verifications': 3,
            'passed': 2,
            'failed': 1,
            'summary_type': 'full',
        }
        result = prepare_output(
            data, _args(VerbosityLevel.QUIET),
            FORMAT_VERIFICATION_SUMMARY_ESSENTIAL,
            FORMAT_VERIFICATION_SUMMARY_STANDARD
        )
        assert set(result.keys()) == FORMAT_VERIFICATION_SUMMARY_ESSENTIAL

    def test_verbose_mode_includes_counts(self):
        data = {
            'formatted': '# Summary',
            'spec_id': 'spec-1',
            'total_verifications': 3,
            'passed': 2,
            'failed': 1,
            'summary_type': 'full',
        }
        result = prepare_output(
            data, _args(VerbosityLevel.VERBOSE),
            FORMAT_VERIFICATION_SUMMARY_ESSENTIAL,
            FORMAT_VERIFICATION_SUMMARY_STANDARD
        )
        assert 'total_verifications' in result
        assert 'passed' in result
        assert 'failed' in result


class TestFormatPlanVerbosity:
    def test_format_plan_quiet_mode(self):
        data = {
            'formatted': 'Plan text',
            'plan_structure': ['phase-1', 'phase-2'],
            'sections': 5,
            'word_count': 1200,
        }
        result = prepare_output(data, _args(VerbosityLevel.QUIET), FORMAT_PLAN_ESSENTIAL, FORMAT_PLAN_STANDARD)
        assert set(result.keys()) == FORMAT_PLAN_ESSENTIAL
