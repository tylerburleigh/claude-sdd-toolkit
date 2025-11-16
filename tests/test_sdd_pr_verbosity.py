"""Verbosity field filtering tests for sdd-pr outputs."""

import argparse

from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    PR_CONTEXT_ESSENTIAL,
    PR_CONTEXT_STANDARD,
    PR_CREATE_ESSENTIAL,
    PR_CREATE_STANDARD,
)


def _quiet():
    return argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)


def _verbose():
    return argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)


class TestPrContextVerbosity:
    def test_quiet_mode_shows_counts_only(self):
        data = {
            'spec_id': 'spec-001',
            'mode': 'draft',
            'branch_name': 'feat/demo',
            'base_branch': 'main',
            'context_counts': {'commits': 3, 'tasks': 5},
            'diff_bytes': 2048,
            'repo_root': '/repo',
        }

        filtered = prepare_output(data, _quiet(), PR_CONTEXT_ESSENTIAL, PR_CONTEXT_STANDARD)
        assert set(filtered.keys()) == PR_CONTEXT_ESSENTIAL
        assert filtered['context_counts']['commits'] == 3

    def test_verbose_mode_includes_branch_metadata(self):
        data = {
            'spec_id': 'spec-001',
            'mode': 'draft',
            'branch_name': 'feat/demo',
            'base_branch': 'main',
            'context_counts': {'commits': 3, 'tasks': 5},
            'diff_bytes': 4096,
            'repo_root': '/repo',
        }

        filtered = prepare_output(data, _verbose(), PR_CONTEXT_ESSENTIAL, PR_CONTEXT_STANDARD)
        assert filtered['base_branch'] == 'main'
        assert filtered['diff_bytes'] == 4096


class TestPrCreateVerbosity:
    def test_quiet_mode_minimal_fields(self):
        data = {
            'success': True,
            'spec_id': 'spec-001',
            'pr_url': 'https://example.com/pr/1',
            'pr_number': 1,
            'branch_name': 'feat/demo',
            'base_branch': 'main',
            'pr_title': 'Demo',
        }

        filtered = prepare_output(data, _quiet(), PR_CREATE_ESSENTIAL, PR_CREATE_STANDARD)
        assert set(filtered.keys()) == PR_CREATE_ESSENTIAL
        assert filtered['pr_url'].endswith('/1')

    def test_verbose_mode_includes_diagnostics(self):
        data = {
            'success': False,
            'spec_id': 'spec-001',
            'pr_url': None,
            'pr_number': None,
            'branch_name': 'feat/demo',
            'base_branch': 'main',
            'pr_title': 'Demo',
            'error': 'missing description',
        }

        filtered = prepare_output(data, _verbose(), PR_CREATE_ESSENTIAL, PR_CREATE_STANDARD)
        assert filtered['error'] == 'missing description'
        assert filtered['branch_name'] == 'feat/demo'
