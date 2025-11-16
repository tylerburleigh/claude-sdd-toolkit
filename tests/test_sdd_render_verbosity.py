"""Field filtering tests for sdd-render command."""

import argparse

from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    RENDER_SPEC_ESSENTIAL,
    RENDER_SPEC_STANDARD,
)


def _quiet():
    return argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)


def _verbose():
    return argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)


def test_render_quiet_mode_returns_minimal_fields():
    data = {
        'spec_id': 'demo-001',
        'output_path': '/tmp/specs/.human-readable/demo-001.md',
        'mode': 'enhanced',
        'enhancement_level': 'standard',
        'fallback_used': False,
        'fallback_reason': None,
        'model_override': None,
        'output_size': 2048,
        'task_count': 10,
    }

    result = prepare_output(data, _quiet(), RENDER_SPEC_ESSENTIAL, RENDER_SPEC_STANDARD)
    assert set(result.keys()) == RENDER_SPEC_ESSENTIAL


def test_render_verbose_mode_includes_diagnostics():
    data = {
        'spec_id': 'demo-001',
        'output_path': '/tmp/specs/.human-readable/demo-001.md',
        'mode': 'enhanced',
        'enhancement_level': 'standard',
        'fallback_used': True,
        'fallback_reason': 'timeout',
        'model_override': {'default': 'gpt-4'},
        'output_size': 4096,
        'task_count': 12,
    }

    result = prepare_output(data, _verbose(), RENDER_SPEC_ESSENTIAL, RENDER_SPEC_STANDARD)
    assert result['fallback_reason'] == 'timeout'
    assert result['output_size'] == 4096
