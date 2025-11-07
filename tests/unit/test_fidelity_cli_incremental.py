"""
Unit tests for fidelity review CLI --incremental flag.

Tests the new --incremental flag integration with FidelityReviewer.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import argparse

from claude_skills.sdd_fidelity_review.cli import _handle_fidelity_review, register_fidelity_review_command


class TestIncrementalFlagCLI:
    """Tests for --incremental flag in fidelity review CLI."""

    def test_incremental_flag_registered(self):
        """--incremental flag should be registered in argument parser."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        register_fidelity_review_command(subparsers)

        # Parse with --incremental flag
        args = parser.parse_args(['fidelity-review', 'test-spec', '--incremental', '--no-ai'])

        assert hasattr(args, 'incremental')
        assert args.incremental is True

    def test_incremental_flag_default_false(self):
        """--incremental flag should default to False when not provided."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        register_fidelity_review_command(subparsers)

        # Parse without --incremental flag
        args = parser.parse_args(['fidelity-review', 'test-spec', '--no-ai'])

        assert hasattr(args, 'incremental')
        assert args.incremental is False

    def test_incremental_flag_passed_to_reviewer(self):
        """--incremental flag should be passed to FidelityReviewer constructor."""
        # Create mock args with incremental=True
        args = Mock()
        args.spec_id = 'test-spec'
        args.incremental = True
        args.verbose = False
        args.no_ai = True  # Skip AI consultation for test

        # Mock FidelityReviewer
        with patch('claude_skills.sdd_fidelity_review.cli.FidelityReviewer') as MockReviewer:
            mock_reviewer = Mock()
            mock_reviewer.spec_data = {'title': 'Test'}
            mock_reviewer.spec_id = 'test-spec'
            mock_reviewer.generate_review_prompt.return_value = "Test prompt"
            MockReviewer.return_value = mock_reviewer

            # Call handler
            result = _handle_fidelity_review(args)

            # Verify FidelityReviewer was initialized with incremental=True
            MockReviewer.assert_called_once_with('test-spec', incremental=True)
            assert result == 0

    def test_incremental_false_passed_to_reviewer(self):
        """When --incremental is not set, incremental=False should be passed."""
        # Create mock args with incremental=False
        args = Mock()
        args.spec_id = 'test-spec'
        args.incremental = False
        args.verbose = False
        args.no_ai = True

        # Mock FidelityReviewer
        with patch('claude_skills.sdd_fidelity_review.cli.FidelityReviewer') as MockReviewer:
            mock_reviewer = Mock()
            mock_reviewer.spec_data = {'title': 'Test'}
            mock_reviewer.spec_id = 'test-spec'
            mock_reviewer.generate_review_prompt.return_value = "Test prompt"
            MockReviewer.return_value = mock_reviewer

            # Call handler
            result = _handle_fidelity_review(args)

            # Verify FidelityReviewer was initialized with incremental=False
            MockReviewer.assert_called_once_with('test-spec', incremental=False)
            assert result == 0

    def test_incremental_flag_help_text(self):
        """--incremental flag should have clear help text."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        register_fidelity_review_command(subparsers)

        # Get the fidelity-review subparser directly from actions
        fidelity_parser = None
        for action in parser._subparsers._actions:
            if hasattr(action, 'choices') and action.choices:
                if 'fidelity-review' in action.choices:
                    fidelity_parser = action.choices['fidelity-review']
                    break

        assert fidelity_parser is not None, "fidelity-review subcommand not found"

        # Get help text from subparser
        help_text = fidelity_parser.format_help()

        # Verify --incremental appears in help
        assert '--incremental' in help_text
        assert 'incremental mode' in help_text.lower()

    def test_incremental_flag_backward_compatible(self):
        """Existing usage without --incremental should continue to work."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        register_fidelity_review_command(subparsers)

        # Parse existing command pattern (no --incremental)
        args = parser.parse_args([
            'fidelity-review',
            'test-spec',
            '--phase', 'phase-1',
            '--no-ai'
        ])

        # Should parse successfully
        assert args.spec_id == 'test-spec'
        assert args.phase == 'phase-1'
        assert args.incremental is False  # Default

    def test_incremental_hasattr_check_handles_missing_attribute(self):
        """Handler should gracefully handle args without incremental attribute."""
        # Create args without incremental attribute (edge case)
        # Need to include all attributes that _handle_fidelity_review might check
        args = Mock()
        args.spec_id = 'test-spec'
        args.verbose = False
        args.no_ai = True
        # Don't set args.incremental - hasattr check should handle this

        # Remove incremental attribute to simulate missing attribute
        del args.incremental

        # Mock FidelityReviewer
        with patch('claude_skills.sdd_fidelity_review.cli.FidelityReviewer') as MockReviewer:
            mock_reviewer = Mock()
            mock_reviewer.spec_data = {'title': 'Test'}
            mock_reviewer.spec_id = 'test-spec'
            mock_reviewer.generate_review_prompt.return_value = "Test prompt"
            MockReviewer.return_value = mock_reviewer

            # Call handler
            result = _handle_fidelity_review(args)

            # Should default to False when attribute missing
            MockReviewer.assert_called_once_with('test-spec', incremental=False)
            assert result == 0
