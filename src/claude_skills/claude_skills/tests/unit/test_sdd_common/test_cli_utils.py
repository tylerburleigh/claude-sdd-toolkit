"""
Unit tests for CLI utilities module.

Tests for helper functions including JSON formatting, ANSI code stripping,
and argument parser decorators.
"""

import argparse
import json
import pytest

from claude_skills.common.cli_utils import (
    strip_ansi_codes,
    format_json_output,
    add_format_flag,
)


class TestStripAnsiCodes:
    """Tests for strip_ansi_codes function."""

    def test_strip_basic_ansi_codes(self):
        """Test stripping basic ANSI color codes."""
        text = "\x1b[31mRed text\x1b[0m"
        assert strip_ansi_codes(text) == "Red text"

    def test_strip_multiple_ansi_codes(self):
        """Test stripping multiple ANSI codes."""
        text = "\x1b[1m\x1b[32mBold green\x1b[0m normal"
        assert strip_ansi_codes(text) == "Bold green normal"

    def test_no_ansi_codes(self):
        """Test text without ANSI codes remains unchanged."""
        text = "Plain text"
        assert strip_ansi_codes(text) == "Plain text"

    def test_empty_string(self):
        """Test empty string handling."""
        assert strip_ansi_codes("") == ""

    def test_rich_markup_not_stripped(self):
        """Test that Rich markup (not ANSI codes) is not affected."""
        text = "[bold]Text[/bold]"
        assert strip_ansi_codes(text) == "[bold]Text[/bold]"


class TestFormatJsonOutput:
    """Tests for format_json_output function."""

    def test_basic_dict_formatting(self):
        """Test basic dictionary formatting."""
        data = {"key": "value", "count": 5}
        result = format_json_output(data, compact=False)
        parsed = json.loads(result)
        assert parsed == data

    def test_compact_formatting(self):
        """Test compact JSON formatting."""
        data = {"a": 1, "b": 2}
        result = format_json_output(data, compact=True)
        assert "\n" not in result  # No newlines in compact mode
        assert json.loads(result) == data

    def test_pretty_formatting(self):
        """Test pretty-printed JSON formatting."""
        data = {"a": 1, "b": 2}
        result = format_json_output(data, compact=False)
        assert "\n" in result  # Newlines in pretty mode
        assert "  " in result  # Indentation present
        assert json.loads(result) == data

    def test_ansi_stripping_enabled(self):
        """Test ANSI codes are stripped when enabled."""
        data = {"status": "\x1b[32mcompleted\x1b[0m"}
        result = format_json_output(data, strip_ansi=True)
        parsed = json.loads(result)
        assert parsed["status"] == "completed"

    def test_ansi_stripping_disabled(self):
        """Test ANSI codes are preserved when disabled."""
        data = {"status": "\x1b[32mcompleted\x1b[0m"}
        result = format_json_output(data, strip_ansi=False)
        parsed = json.loads(result)
        assert "\x1b[32m" in parsed["status"]

    def test_nested_dict_ansi_stripping(self):
        """Test ANSI stripping in nested dictionaries."""
        data = {
            "outer": {
                "inner": "\x1b[31mred\x1b[0m"
            }
        }
        result = format_json_output(data, strip_ansi=True)
        parsed = json.loads(result)
        assert parsed["outer"]["inner"] == "red"

    def test_list_ansi_stripping(self):
        """Test ANSI stripping in lists."""
        data = {"items": ["\x1b[32mgreen\x1b[0m", "\x1b[31mred\x1b[0m"]}
        result = format_json_output(data, strip_ansi=True)
        parsed = json.loads(result)
        assert parsed["items"] == ["green", "red"]

    def test_mixed_types(self):
        """Test handling of mixed data types."""
        data = {
            "string": "text",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
            "list": [1, 2, 3],
            "nested": {"a": 1}
        }
        result = format_json_output(data)
        assert json.loads(result) == data


class TestAddFormatFlag:
    """Tests for add_format_flag decorator function."""

    def test_basic_usage(self):
        """Test adding format flag with default options."""
        parser = argparse.ArgumentParser()
        add_format_flag(parser)

        # Parse with default
        args = parser.parse_args([])
        assert args.format == 'text'

        # Parse with explicit json
        args = parser.parse_args(['--format', 'json'])
        assert args.format == 'json'

    def test_custom_choices(self):
        """Test custom format choices."""
        parser = argparse.ArgumentParser()
        add_format_flag(parser, choices=['json', 'table', 'csv'], default='table')

        # Parse with default
        args = parser.parse_args([])
        assert args.format == 'table'

        # Parse with custom choice
        args = parser.parse_args(['--format', 'csv'])
        assert args.format == 'csv'

    def test_custom_default(self):
        """Test custom default value."""
        parser = argparse.ArgumentParser()
        add_format_flag(parser, choices=['markdown', 'json'], default='markdown')

        args = parser.parse_args([])
        assert args.format == 'markdown'

    def test_custom_help_text(self):
        """Test custom help text."""
        parser = argparse.ArgumentParser()
        custom_help = "Choose your preferred output format"
        add_format_flag(parser, help_text=custom_help)

        # Verify help text is set (check action object)
        format_action = None
        for action in parser._actions:
            if '--format' in action.option_strings:
                format_action = action
                break

        assert format_action is not None
        assert format_action.help == custom_help

    def test_invalid_choice_raises_error(self):
        """Test that invalid format choice raises error."""
        parser = argparse.ArgumentParser()
        add_format_flag(parser, choices=['json', 'text'])

        with pytest.raises(SystemExit):  # argparse exits on invalid choice
            parser.parse_args(['--format', 'invalid'])

    def test_default_not_in_choices_raises_error(self):
        """Test that default value not in choices raises ValueError."""
        parser = argparse.ArgumentParser()

        with pytest.raises(ValueError, match="Default format.*must be one of"):
            add_format_flag(parser, choices=['json', 'text'], default='invalid')

    def test_with_subparsers(self):
        """Test add_format_flag works with subparsers."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()

        # Add a subcommand
        stats_parser = subparsers.add_parser('stats')
        add_format_flag(stats_parser, choices=['text', 'json', 'table'])

        # Parse subcommand with format
        args = parser.parse_args(['stats', '--format', 'table'])
        assert args.format == 'table'

    def test_returns_parser(self):
        """Test that function returns the parser for chaining."""
        parser = argparse.ArgumentParser()
        result = add_format_flag(parser)

        assert result is parser

    def test_auto_generated_help_text(self):
        """Test auto-generated help text format."""
        parser = argparse.ArgumentParser()
        add_format_flag(parser, choices=['json', 'xml', 'yaml'], default='json')

        # Find the format action
        format_action = None
        for action in parser._actions:
            if '--format' in action.option_strings:
                format_action = action
                break

        assert format_action is not None
        assert 'json, xml, yaml' in format_action.help
        assert 'default: json' in format_action.help

    def test_empty_choices_uses_default(self):
        """Test that None choices uses default ['text', 'json']."""
        parser = argparse.ArgumentParser()
        add_format_flag(parser)

        # Find the format action to check choices
        format_action = None
        for action in parser._actions:
            if '--format' in action.option_strings:
                format_action = action
                break

        assert format_action is not None
        assert format_action.choices == ['text', 'json']

    def test_multiple_format_variations(self):
        """Test common format variations from different tools."""
        # Test sdd_validate pattern
        parser1 = argparse.ArgumentParser()
        add_format_flag(parser1, choices=['markdown', 'json'], default='markdown')
        args1 = parser1.parse_args([])
        assert args1.format == 'markdown'

        # Test sdd_update pattern
        parser2 = argparse.ArgumentParser()
        add_format_flag(parser2, choices=['table', 'json', 'simple'], default='table')
        args2 = parser2.parse_args([])
        assert args2.format == 'table'

        # Test doc_query pattern
        parser3 = argparse.ArgumentParser()
        add_format_flag(parser3, choices=['text', 'json', 'dot'], default='text')
        args3 = parser3.parse_args([])
        assert args3.format == 'text'
