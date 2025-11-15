"""Tests for CLI verbosity control and quiet mode functionality.

Tests verify that:
1. Quiet mode suppresses informational output
2. Quiet mode preserves warnings and errors
3. Verbosity levels are correctly applied across different command types
"""

import pytest
import argparse
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from claude_skills.cli.sdd.verbosity import (
    VerbosityLevel,
    should_omit_empty_fields,
    should_include_debug_info,
    filter_output_fields
)
from claude_skills.cli.sdd.output_utils import (
    prepare_output,
    should_show_field,
    add_debug_info
)
from claude_skills.cli.sdd.options import (
    add_global_options,
    get_verbosity_level
)


class TestVerbosityLevel:
    """Test VerbosityLevel enum functionality."""

    def test_quiet_level_creation(self):
        """Test creating QUIET verbosity level."""
        assert VerbosityLevel.QUIET.value == "quiet"
        assert str(VerbosityLevel.QUIET) == "quiet"

    def test_normal_level_creation(self):
        """Test creating NORMAL verbosity level."""
        assert VerbosityLevel.NORMAL.value == "normal"
        assert str(VerbosityLevel.NORMAL) == "normal"

    def test_verbose_level_creation(self):
        """Test creating VERBOSE verbosity level."""
        assert VerbosityLevel.VERBOSE.value == "verbose"
        assert str(VerbosityLevel.VERBOSE) == "verbose"

    def test_from_args_quiet_flag(self):
        """Test parsing --quiet flag to QUIET level."""
        args = argparse.Namespace(quiet=True, verbose=False)
        level = VerbosityLevel.from_args(args)
        assert level == VerbosityLevel.QUIET

    def test_from_args_verbose_flag(self):
        """Test parsing --verbose flag to VERBOSE level."""
        args = argparse.Namespace(quiet=False, verbose=True)
        level = VerbosityLevel.from_args(args)
        assert level == VerbosityLevel.VERBOSE

    def test_from_args_no_flags(self):
        """Test parsing no flags defaults to NORMAL."""
        args = argparse.Namespace(quiet=False, verbose=False)
        level = VerbosityLevel.from_args(args)
        assert level == VerbosityLevel.NORMAL

    def test_from_args_missing_attributes(self):
        """Test that missing attributes default to False."""
        args = argparse.Namespace()
        level = VerbosityLevel.from_args(args)
        assert level == VerbosityLevel.NORMAL

    def test_from_args_both_flags_raises_error(self):
        """Test that both --quiet and --verbose raises ValueError."""
        args = argparse.Namespace(quiet=True, verbose=True)
        with pytest.raises(ValueError, match="Cannot specify both --quiet and --verbose"):
            VerbosityLevel.from_args(args)

    def test_from_config_normal(self):
        """Test loading verbosity from config with 'normal'."""
        config = {'output': {'default_verbosity': 'normal'}}
        level = VerbosityLevel.from_config(config)
        assert level == VerbosityLevel.NORMAL

    def test_from_config_quiet(self):
        """Test loading verbosity from config with 'quiet'."""
        config = {'output': {'default_verbosity': 'quiet'}}
        level = VerbosityLevel.from_config(config)
        assert level == VerbosityLevel.QUIET

    def test_from_config_verbose(self):
        """Test loading verbosity from config with 'verbose'."""
        config = {'output': {'default_verbosity': 'verbose'}}
        level = VerbosityLevel.from_config(config)
        assert level == VerbosityLevel.VERBOSE

    def test_from_config_missing_key(self):
        """Test loading from config with missing default_verbosity defaults to NORMAL."""
        config = {'output': {}}
        level = VerbosityLevel.from_config(config)
        assert level == VerbosityLevel.NORMAL

    def test_from_config_invalid_value(self):
        """Test loading invalid value from config falls back to NORMAL."""
        config = {'output': {'default_verbosity': 'invalid'}}
        level = VerbosityLevel.from_config(config)
        assert level == VerbosityLevel.NORMAL


class TestQuietMode:
    """Test quiet mode behavior - suppresses informational output."""

    def test_quiet_mode_omits_empty_fields(self):
        """Test that QUIET mode omits empty/null fields."""
        assert should_omit_empty_fields(VerbosityLevel.QUIET) is True

    def test_normal_mode_includes_empty_fields(self):
        """Test that NORMAL mode doesn't omit empty fields."""
        assert should_omit_empty_fields(VerbosityLevel.NORMAL) is False

    def test_verbose_mode_includes_empty_fields(self):
        """Test that VERBOSE mode doesn't omit empty fields."""
        assert should_omit_empty_fields(VerbosityLevel.VERBOSE) is False

    def test_quiet_mode_excludes_debug_info(self):
        """Test that QUIET mode doesn't include debug info."""
        assert should_include_debug_info(VerbosityLevel.QUIET) is False

    def test_normal_mode_excludes_debug_info(self):
        """Test that NORMAL mode doesn't include debug info."""
        assert should_include_debug_info(VerbosityLevel.NORMAL) is False

    def test_verbose_mode_includes_debug_info(self):
        """Test that VERBOSE mode includes debug info."""
        assert should_include_debug_info(VerbosityLevel.VERBOSE) is True

    def test_filter_output_quiet_omits_empty_values(self):
        """Test that filter_output_fields removes empty values in QUIET mode."""
        data = {
            'id': '123',
            'name': 'Task',
            'description': None,
            'tags': [],
            'metadata': {}
        }
        essential = {'id', 'name'}
        result = filter_output_fields(data, VerbosityLevel.QUIET, essential)

        # Essential non-empty fields should be included
        assert 'id' in result
        assert 'name' in result

        # Empty values should be omitted
        assert 'description' not in result
        assert 'tags' not in result
        assert 'metadata' not in result

    def test_filter_output_normal_includes_all_non_empty(self):
        """Test that filter_output_fields includes all non-empty in NORMAL mode."""
        data = {
            'id': '123',
            'name': 'Task',
            'description': None,
            'tags': [],
            'metadata': {'key': 'value'}
        }
        essential = {'id', 'name'}
        standard = {'metadata'}
        result = filter_output_fields(data, VerbosityLevel.NORMAL, essential, standard)

        # Essential and standard fields should be included
        assert 'id' in result
        assert 'name' in result
        assert 'metadata' in result

        # Other fields omitted
        assert 'description' not in result
        assert 'tags' not in result

    def test_filter_output_verbose_includes_everything(self):
        """Test that filter_output_fields includes all fields in VERBOSE mode."""
        data = {
            'id': '123',
            'name': 'Task',
            'description': None,
            'tags': [],
            'metadata': {},
            '_debug': {'timing': 123}
        }
        result = filter_output_fields(data, VerbosityLevel.VERBOSE, set(), set())

        # All fields should be included
        assert result == data


class TestPrepareOutput:
    """Test the prepare_output function for command handlers."""

    def test_prepare_output_quiet_mode(self):
        """Test prepare_output filters correctly in QUIET mode."""
        args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        data = {
            'spec_id': 'my-spec',
            'status': 'active',
            'title': 'My Spec',
            'total_tasks': 10,
            'metadata': {}  # empty
        }
        essential = {'spec_id', 'status', 'title'}
        standard = {'total_tasks', 'metadata'}

        result = prepare_output(data, args, essential, standard)

        # Essential non-empty fields included
        assert 'spec_id' in result
        assert 'status' in result
        assert 'title' in result

        # Empty metadata omitted
        assert 'metadata' not in result

    def test_prepare_output_normal_mode(self):
        """Test prepare_output includes standard fields in NORMAL mode."""
        args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        data = {
            'spec_id': 'my-spec',
            'status': 'active',
            'title': 'My Spec',
            'total_tasks': 10,
            'metadata': {}
        }
        essential = {'spec_id', 'status', 'title'}
        standard = {'total_tasks', 'metadata'}

        result = prepare_output(data, args, essential, standard)

        # All essential and standard fields included
        assert 'spec_id' in result
        assert 'status' in result
        assert 'title' in result
        assert 'total_tasks' in result
        assert 'metadata' in result

    def test_prepare_output_verbose_mode(self):
        """Test prepare_output includes everything in VERBOSE mode."""
        args = argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)
        data = {
            'spec_id': 'my-spec',
            'status': 'active',
            'title': 'My Spec',
            'total_tasks': 10,
            'metadata': {},
            '_debug': {'query_time': 15}
        }
        essential = {'spec_id', 'status', 'title'}
        standard = {'total_tasks', 'metadata'}

        result = prepare_output(data, args, essential, standard)

        # All fields included, including debug info
        assert result == data

    def test_prepare_output_missing_verbosity_defaults_normal(self):
        """Test prepare_output defaults to NORMAL if verbosity_level missing."""
        args = argparse.Namespace()
        data = {'id': '123', 'value': 'test'}

        result = prepare_output(data, args)

        # Should work with default NORMAL level
        assert 'id' in result
        assert 'value' in result


class TestShouldShowField:
    """Test the should_show_field helper function."""

    def test_should_show_essential_field_quiet_mode(self):
        """Test essential field shown in QUIET mode."""
        args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        assert should_show_field(args, 'id', '123', is_essential=True) is True

    def test_should_show_empty_essential_field_quiet_mode(self):
        """Test empty essential field not shown in QUIET mode."""
        args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        assert should_show_field(args, 'tags', [], is_essential=True) is False
        assert should_show_field(args, 'metadata', {}, is_essential=True) is False
        assert should_show_field(args, 'desc', None, is_essential=True) is False

    def test_should_show_non_essential_field_quiet_mode(self):
        """Test non-essential field hidden in QUIET mode."""
        args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        assert should_show_field(args, 'extra_info', 'value', is_essential=False) is False

    def test_should_show_standard_field_normal_mode(self):
        """Test standard field shown in NORMAL mode."""
        args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        assert should_show_field(args, 'count', 10, is_standard=True) is True

    def test_should_show_all_fields_verbose_mode(self):
        """Test all fields shown in VERBOSE mode."""
        args = argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)
        assert should_show_field(args, 'any_field', None, is_essential=False, is_standard=False) is True
        assert should_show_field(args, 'debug_info', {}, is_essential=False, is_standard=False) is True


class TestAddDebugInfo:
    """Test the add_debug_info function."""

    def test_add_debug_info_quiet_mode(self):
        """Test debug info not added in QUIET mode."""
        args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        data = {'id': '123', 'status': 'active'}
        debug = {'query_time_ms': 15, 'cache_hit': True}

        result = add_debug_info(data, args, debug)

        # Original data unchanged
        assert result == data
        assert '_debug' not in result

    def test_add_debug_info_normal_mode(self):
        """Test debug info not added in NORMAL mode."""
        args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        data = {'id': '123', 'status': 'active'}
        debug = {'query_time_ms': 15, 'cache_hit': True}

        result = add_debug_info(data, args, debug)

        # Debug info not added
        assert '_debug' not in result

    def test_add_debug_info_verbose_mode(self):
        """Test debug info added in VERBOSE mode."""
        args = argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)
        data = {'id': '123', 'status': 'active'}
        debug = {'query_time_ms': 15, 'cache_hit': True}

        result = add_debug_info(data, args, debug)

        # Debug info should be added
        assert '_debug' in result
        assert result['_debug'] == debug


class TestGlobalOptions:
    """Test global option parsing with verbosity."""

    def test_add_global_options_creates_quiet_flag(self):
        """Test that add_global_options creates --quiet flag."""
        parser = argparse.ArgumentParser()

        with patch('claude_skills.common.sdd_config.load_sdd_config') as mock_config:
            mock_config.return_value = {'output': {'default_mode': 'rich', 'json_compact': True}}
            add_global_options(parser)

        args = parser.parse_args(['--quiet'])
        assert args.quiet is True
        assert args.verbose is False

    def test_add_global_options_creates_verbose_flag(self):
        """Test that add_global_options creates --verbose flag."""
        parser = argparse.ArgumentParser()

        with patch('claude_skills.common.sdd_config.load_sdd_config') as mock_config:
            mock_config.return_value = {'output': {'default_mode': 'rich', 'json_compact': True}}
            add_global_options(parser)

        args = parser.parse_args(['--verbose'])
        assert args.verbose is True
        assert args.quiet is False

    def test_add_global_options_short_quiet_flag(self):
        """Test that -q shorthand works for --quiet."""
        parser = argparse.ArgumentParser()

        with patch('claude_skills.common.sdd_config.load_sdd_config') as mock_config:
            mock_config.return_value = {'output': {'default_mode': 'rich', 'json_compact': True}}
            add_global_options(parser)

        args = parser.parse_args(['-q'])
        assert args.quiet is True

    def test_add_global_options_short_verbose_flag(self):
        """Test that -v shorthand works for --verbose."""
        parser = argparse.ArgumentParser()

        with patch('claude_skills.common.sdd_config.load_sdd_config') as mock_config:
            mock_config.return_value = {'output': {'default_mode': 'rich', 'json_compact': True}}
            add_global_options(parser)

        args = parser.parse_args(['-v'])
        assert args.verbose is True

    def test_get_verbosity_level_from_args(self):
        """Test get_verbosity_level extracts level from parsed args."""
        args = argparse.Namespace(quiet=True, verbose=False)
        level = get_verbosity_level(args)
        assert level == VerbosityLevel.QUIET


class TestQuietModeIntegration:
    """Integration tests for quiet mode functionality."""

    def test_quiet_mode_suppresses_informational_output(self):
        """Test quiet mode suppresses informational output while preserving warnings and errors.

        This is the main test for verify-2-1.
        """
        # Simulate a command output with various message types
        args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)

        # Command output with info, warning, and error data
        command_data = {
            # Essential data (should always show in QUIET)
            'task_id': 'task-1',
            'status': 'completed',

            # Informational data (should be omitted in QUIET)
            'task_title': 'My Task',
            'description': 'Task description',
            'started_at': '2025-11-15T10:00:00Z',

            # Empty fields (should be omitted in QUIET)
            'notes': None,
            'tags': [],

            # Warning/Error data (should show in QUIET)
            'warnings': ['Potential issue detected'],
            'errors': ['Critical failure'],  # Non-empty to be preserved
        }

        essential_fields = {'task_id', 'status', 'warnings', 'errors'}
        standard_fields = {
            'task_id', 'status', 'task_title', 'description',
            'started_at', 'warnings', 'errors', 'notes', 'tags'
        }

        result = prepare_output(command_data, args, essential_fields, standard_fields)

        # Essential data always shown
        assert 'task_id' in result
        assert result['task_id'] == 'task-1'
        assert 'status' in result
        assert result['status'] == 'completed'

        # Warnings and errors shown (when non-empty)
        assert 'warnings' in result
        assert result['warnings'] == ['Potential issue detected']
        assert 'errors' in result
        assert result['errors'] == ['Critical failure']

        # Informational data suppressed
        assert 'description' not in result
        assert 'started_at' not in result

        # Empty fields suppressed
        assert 'notes' not in result
        assert 'tags' not in result

    def test_quiet_mode_with_different_verbosity_levels(self):
        """Test that different verbosity levels handle same data differently."""
        data = {
            'spec_id': 'spec-1',
            'title': 'My Specification',
            'status': 'active',
            'total_tasks': 20,
            'completed_tasks': 10,
            'metadata': {'author': 'test-user'},
            'timestamp': '2025-11-15T10:00:00Z'
        }

        essential = {'spec_id', 'status'}
        standard = {'spec_id', 'status', 'title', 'total_tasks', 'completed_tasks', 'metadata'}

        # QUIET mode
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        quiet_result = prepare_output(data, quiet_args, essential, standard)
        assert set(quiet_result.keys()) <= essential  # Only essential fields

        # NORMAL mode
        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        normal_result = prepare_output(data, normal_args, essential, standard)
        assert set(quiet_result.keys()) < set(normal_result.keys())  # More fields than QUIET
        assert 'metadata' in normal_result

        # VERBOSE mode
        verbose_args = argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)
        verbose_data = {**data, '_debug': {'parse_time': 5}}
        verbose_result = prepare_output(verbose_data, verbose_args, essential, standard)
        assert set(normal_result.keys()) < set(verbose_result.keys())  # More fields than NORMAL
        assert '_debug' in verbose_result

    def test_quiet_mode_preserves_critical_error_messages(self):
        """Test that critical error messages are preserved in QUIET mode."""
        args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)

        data = {
            'success': False,
            'error_code': 'SPEC_NOT_FOUND',
            'error_message': 'Specification not found: my-spec',
            'timestamp': '2025-11-15T10:00:00Z',
            'debug_context': {'file': 'handler.py', 'line': 42}
        }

        essential = {'success', 'error_code', 'error_message'}
        standard = {'success', 'error_code', 'error_message', 'timestamp', 'debug_context'}

        result = prepare_output(data, args, essential, standard)

        # Error information preserved
        assert 'success' in result
        assert 'error_code' in result
        assert 'error_message' in result

        # Debug context and timestamp suppressed
        assert 'debug_context' not in result
        assert 'timestamp' not in result
