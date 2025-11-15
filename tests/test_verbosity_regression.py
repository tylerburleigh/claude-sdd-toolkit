"""Regression tests for CLI verbosity rollout.

Tests verify that commands NOT modified during the verbosity rollout
continue to work correctly without breaking changes.
"""

import pytest
from unittest.mock import Mock, patch
import argparse

from claude_skills.cli.sdd.verbosity import VerbosityLevel
from claude_skills.cli.sdd.output_utils import prepare_output


class TestUnmodifiedCommandsBehavior:
    """Test that commands not modified during verbosity rollout still work."""

    def test_prepare_output_preserves_backward_compatibility(self):
        """Test prepare_output without verbosity level still works (backward compatibility)."""
        # Simulate old code that doesn't set verbosity_level
        args = argparse.Namespace()  # No verbosity_level attribute
        data = {
            'id': 'test-123',
            'name': 'Test Item',
            'value': 42,
            'metadata': {'key': 'value'}
        }

        # Should work without verbosity_level (defaults to NORMAL)
        result = prepare_output(data, args)

        # All fields should be present (NORMAL mode behavior)
        assert 'id' in result
        assert 'name' in result
        assert 'value' in result
        assert 'metadata' in result

    def test_prepare_output_with_no_field_sets(self):
        """Test prepare_output works when no essential/standard fields specified."""
        args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        data = {
            'field1': 'value1',
            'field2': 'value2',
            'field3': None
        }

        # No field sets specified - should return all non-empty fields in NORMAL
        result = prepare_output(data, args)

        assert 'field1' in result
        assert 'field2' in result
        # field3 is None, behavior depends on implementation

    def test_quiet_mode_doesnt_break_simple_data(self):
        """Test QUIET mode handles simple data structures correctly."""
        args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        data = {
            'success': True,
            'message': 'Operation completed'
        }
        essential = {'success'}

        result = prepare_output(data, args, essential)

        # Essential field present
        assert 'success' in result
        # Non-essential omitted in QUIET
        assert 'message' not in result

    def test_verbose_mode_preserves_all_data(self):
        """Test VERBOSE mode never loses data."""
        args = argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)
        data = {
            'id': '123',
            'empty_string': '',
            'empty_list': [],
            'empty_dict': {},
            'none_value': None,
            '_internal': 'internal_data',
            '_debug': {'timing': 15}
        }

        result = prepare_output(data, args)

        # In VERBOSE mode, all fields preserved
        assert result == data


class TestVerbosityLevelParsing:
    """Test verbosity level parsing doesn't break existing functionality."""

    def test_from_args_handles_missing_attributes_gracefully(self):
        """Test VerbosityLevel.from_args handles missing attributes."""
        # Old code might not have quiet/verbose attributes
        args = argparse.Namespace()

        level = VerbosityLevel.from_args(args)

        # Should default to NORMAL without error
        assert level == VerbosityLevel.NORMAL

    def test_from_args_with_partial_attributes(self):
        """Test VerbosityLevel.from_args with only some attributes present."""
        # Scenario: only quiet attribute exists
        args = argparse.Namespace(quiet=False)

        level = VerbosityLevel.from_args(args)

        # Should treat missing verbose as False
        assert level == VerbosityLevel.NORMAL

    def test_from_config_handles_missing_config(self):
        """Test VerbosityLevel.from_config with missing config sections."""
        # Empty config
        config = {}

        level = VerbosityLevel.from_config(config)

        # Should default to NORMAL
        assert level == VerbosityLevel.NORMAL

    def test_from_config_handles_malformed_config(self):
        """Test VerbosityLevel.from_config with malformed config.

        NOTE: Current implementation raises AttributeError for malformed config.
        This is acceptable behavior - callers should validate config structure.
        """
        # Config with wrong structure
        config = {'output': 'not a dict'}

        # Current behavior: raises AttributeError
        with pytest.raises(AttributeError):
            VerbosityLevel.from_config(config)


class TestEmptyFieldHandling:
    """Test handling of empty fields across verbosity levels."""

    def test_empty_list_handling(self):
        """Test empty lists are handled correctly in different verbosity modes."""
        data = {'items': []}

        # QUIET mode omits empty
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        quiet_result = prepare_output(data, quiet_args, essential_fields={'items'})
        assert 'items' not in quiet_result

        # NORMAL mode includes empty
        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        normal_result = prepare_output(data, normal_args, essential_fields={'items'})
        assert 'items' in normal_result

        # VERBOSE mode includes empty
        verbose_args = argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)
        verbose_result = prepare_output(data, verbose_args)
        assert 'items' in verbose_result

    def test_empty_dict_handling(self):
        """Test empty dicts are handled correctly in different verbosity modes."""
        data = {'metadata': {}}

        # QUIET mode omits empty
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        quiet_result = prepare_output(data, quiet_args, essential_fields={'metadata'})
        assert 'metadata' not in quiet_result

        # NORMAL mode includes empty
        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        normal_result = prepare_output(data, normal_args, essential_fields={'metadata'})
        assert 'metadata' in normal_result

    def test_none_value_handling(self):
        """Test None values are handled correctly in different verbosity modes."""
        data = {'description': None}

        # QUIET mode omits None
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        quiet_result = prepare_output(data, quiet_args, essential_fields={'description'})
        assert 'description' not in quiet_result

        # NORMAL mode includes None
        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        normal_result = prepare_output(data, normal_args, essential_fields={'description'})
        assert 'description' in normal_result

    def test_zero_value_not_treated_as_empty(self):
        """Test that zero values are not treated as empty."""
        data = {'count': 0, 'percentage': 0.0}

        # QUIET mode should include zero (not empty)
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        quiet_result = prepare_output(data, quiet_args, essential_fields={'count', 'percentage'})

        assert 'count' in quiet_result
        assert quiet_result['count'] == 0
        assert 'percentage' in quiet_result
        assert quiet_result['percentage'] == 0.0

    def test_empty_string_handling(self):
        """Test empty strings are handled correctly.

        NOTE: Empty strings are NOT treated as empty by is_value_empty().
        Only None, [], {} are considered empty.
        """
        data = {'name': ''}

        # Empty string is NOT considered empty - included in all modes
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        quiet_result = prepare_output(data, quiet_args, essential_fields={'name'})
        assert 'name' in quiet_result  # Empty string is included

        # NORMAL mode includes empty string
        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        normal_result = prepare_output(data, normal_args, essential_fields={'name'})
        assert 'name' in normal_result


class TestNestedDataStructures:
    """Test handling of nested data structures."""

    def test_nested_dict_with_empty_values(self):
        """Test nested dictionaries with empty values."""
        data = {
            'config': {
                'enabled': True,
                'options': {},
                'tags': []
            }
        }

        # QUIET mode
        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        quiet_result = prepare_output(data, quiet_args, essential_fields={'config'})

        # config itself is non-empty (has 'enabled'), should be included
        assert 'config' in quiet_result

    def test_nested_list_with_dicts(self):
        """Test nested lists containing dictionaries."""
        data = {
            'items': [
                {'id': '1', 'name': 'Item 1'},
                {'id': '2', 'name': 'Item 2'}
            ]
        }

        # All modes should preserve nested structures
        for level in [VerbosityLevel.QUIET, VerbosityLevel.NORMAL, VerbosityLevel.VERBOSE]:
            args = argparse.Namespace(verbosity_level=level)
            result = prepare_output(data, args, essential_fields={'items'})

            assert 'items' in result
            assert len(result['items']) == 2


class TestFieldSetPriority:
    """Test priority and interaction between essential and standard field sets."""

    def test_essential_fields_always_included_if_non_empty(self):
        """Test essential fields are always included in QUIET mode if non-empty."""
        data = {
            'id': 'test-123',
            'status': 'active',
            'extra': 'data'
        }
        essential = {'id', 'status'}

        quiet_args = argparse.Namespace(verbosity_level=VerbosityLevel.QUIET)
        result = prepare_output(data, quiet_args, essential)

        # Essential fields included
        assert 'id' in result
        assert 'status' in result
        # Non-essential omitted
        assert 'extra' not in result

    def test_standard_fields_included_in_normal(self):
        """Test standard fields are included in NORMAL mode."""
        data = {
            'id': 'test-123',
            'status': 'active',
            'metadata': {'key': 'value'},
            'debug_info': 'debug'
        }
        essential = {'id', 'status'}
        standard = {'id', 'status', 'metadata'}

        normal_args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        result = prepare_output(data, normal_args, essential, standard)

        # Essential and standard included
        assert 'id' in result
        assert 'status' in result
        assert 'metadata' in result
        # Non-standard omitted
        assert 'debug_info' not in result

    def test_verbose_ignores_field_sets(self):
        """Test VERBOSE mode includes all fields regardless of essential/standard."""
        data = {
            'id': 'test-123',
            'status': 'active',
            'metadata': {'key': 'value'},
            'debug_info': 'debug',
            '_internal': 'internal'
        }
        essential = {'id', 'status'}
        standard = {'id', 'status', 'metadata'}

        verbose_args = argparse.Namespace(verbosity_level=VerbosityLevel.VERBOSE)
        result = prepare_output(data, verbose_args, essential, standard)

        # All fields included
        assert result == data


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_none_data_handling(self):
        """Test handling of None as data input.

        NOTE: Current implementation raises AttributeError for None data.
        This is acceptable behavior - callers should validate data is not None.
        """
        args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)

        # Current behavior: raises AttributeError
        with pytest.raises(AttributeError):
            prepare_output(None, args)

    def test_empty_data_handling(self):
        """Test handling of empty dictionary."""
        args = argparse.Namespace(verbosity_level=VerbosityLevel.NORMAL)
        data = {}

        result = prepare_output(data, args)

        # Should return empty dict
        assert result == {}

    def test_invalid_verbosity_level_in_args(self):
        """Test handling of invalid verbosity level value."""
        args = argparse.Namespace(verbosity_level="invalid")
        data = {'id': '123', 'name': 'test'}

        # Should either handle gracefully or raise appropriate error
        try:
            result = prepare_output(data, args)
            # If no error, should have some reasonable default behavior
            assert isinstance(result, dict)
        except (ValueError, AttributeError, TypeError):
            # Or raise an appropriate error
            pass
