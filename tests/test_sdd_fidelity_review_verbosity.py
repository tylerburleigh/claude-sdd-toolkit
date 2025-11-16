"""Verbosity filtering tests for fidelity-review summaries."""

import argparse

from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    FIDELITY_REVIEW_ESSENTIAL,
    FIDELITY_REVIEW_STANDARD,
)


def _quiet():
    return argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)


def _verbose():
    return argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)


def test_fidelity_summary_quiet_fields():
    data = {
        'spec_id': 'demo-spec',
        'mode': 'full',
        'format': 'text',
        'artifacts': ['review.md', 'review.json'],
        'issue_counts': {'critical': 1},
        'models_consulted': {'count': 2},
        'consensus': {'verdict': 'approve', 'model_count': 2},
        'recommendation': 'APPROVE',
    }

    filtered = prepare_output(data, _quiet(), FIDELITY_REVIEW_ESSENTIAL, FIDELITY_REVIEW_STANDARD)
    assert set(filtered.keys()) == FIDELITY_REVIEW_ESSENTIAL
    assert filtered['artifacts'][0].endswith('review.md')
    assert filtered['recommendation'] == 'APPROVE'


def test_fidelity_summary_verbose_fields():
    data = {
        'spec_id': 'demo-spec',
        'mode': 'full',
        'format': 'json',
        'artifacts': ['review.json'],
        'issue_counts': {'critical': 1},
        'models_consulted': {'count': 2, 'tools': {'gemini': 'model-1'}},
        'consensus': {'verdict': 'approve', 'agreement_rate': 0.8},
        'scope': {'task': 'task-1'},
        'prompt_included': True,
        'recommendation': 'APPROVE',
    }

    filtered = prepare_output(data, _verbose(), FIDELITY_REVIEW_ESSENTIAL, FIDELITY_REVIEW_STANDARD)
    assert filtered['issue_counts']['critical'] == 1
    assert filtered['consensus']['verdict'] == 'approve'
