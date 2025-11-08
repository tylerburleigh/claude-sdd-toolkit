#!/usr/bin/env python3
"""
Unit tests for JSON output formatting utilities.

Tests the output_json() function and related JSON formatting utilities
in claude_skills.common.json_output module.
"""

import json
import sys
from io import StringIO
import pytest

from claude_skills.common.json_output import (
    output_json,
    format_json_output,
    print_json_output,
)


class TestOutputJson:
    """Test suite for output_json() function."""

    def test_output_json_pretty_print_default(self, capsys):
        """Test that output_json uses pretty-print by default."""
        data = {"status": "success", "count": 42}
        output_json(data)

        captured = capsys.readouterr()
        output = captured.out

        # Verify output is valid JSON
        parsed = json.loads(output)
        assert parsed == data

        # Verify it's pretty-printed (has newlines and indentation)
        assert "\n" in output
        assert "  " in output  # 2-space indentation

    def test_output_json_compact_mode(self, capsys):
        """Test that output_json compact mode produces minified output."""
        data = {"status": "success", "count": 42}
        output_json(data, compact=True)

        captured = capsys.readouterr()
        output = captured.out.strip()

        # Verify output is valid JSON
        parsed = json.loads(output)
        assert parsed == data

        # Verify it's compact (no extra whitespace)
        assert output == '{"status":"success","count":42}'

    def test_output_json_nested_data(self, capsys):
        """Test output_json with nested data structures."""
        data = {
            "task": {
                "id": "task-1-1",
                "title": "Example task",
                "metadata": {
                    "estimated_hours": 2.5,
                    "tags": ["test", "example"]
                }
            }
        }
        output_json(data)

        captured = capsys.readouterr()
        output = captured.out

        # Verify output is valid JSON
        parsed = json.loads(output)
        assert parsed == data

        # Verify nested structures are properly formatted
        assert "task" in output
        assert "metadata" in output
        assert "tags" in output

    def test_output_json_list_data(self, capsys):
        """Test output_json with list data."""
        data = [
            {"id": 1, "name": "first"},
            {"id": 2, "name": "second"},
            {"id": 3, "name": "third"}
        ]
        output_json(data)

        captured = capsys.readouterr()
        output = captured.out

        # Verify output is valid JSON
        parsed = json.loads(output)
        assert parsed == data

    def test_output_json_empty_dict(self, capsys):
        """Test output_json with empty dictionary."""
        data = {}
        output_json(data)

        captured = capsys.readouterr()
        output = captured.out.strip()

        assert output == "{}"

    def test_output_json_empty_list(self, capsys):
        """Test output_json with empty list."""
        data = []
        output_json(data)

        captured = capsys.readouterr()
        output = captured.out.strip()

        assert output == "[]"

    def test_output_json_unicode_characters(self, capsys):
        """Test output_json preserves Unicode characters."""
        data = {"message": "Hello 世界", "emoji": "🎉"}
        output_json(data)

        captured = capsys.readouterr()
        output = captured.out

        # Verify output is valid JSON
        parsed = json.loads(output)
        assert parsed == data

        # Verify Unicode is preserved (not escaped)
        assert "世界" in output
        assert "🎉" in output

    def test_output_json_special_values(self, capsys):
        """Test output_json with special JSON values."""
        data = {
            "null_value": None,
            "true_value": True,
            "false_value": False,
            "number": 123,
            "float": 45.67
        }
        output_json(data)

        captured = capsys.readouterr()
        output = captured.out

        # Verify output is valid JSON
        parsed = json.loads(output)
        assert parsed == data

        # Verify special values are properly formatted
        assert "null" in output
        assert "true" in output
        assert "false" in output

    def test_output_json_compact_vs_pretty_size(self, capsys):
        """Test that compact mode produces smaller output than pretty mode."""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "key": "value",
                        "items": [1, 2, 3, 4, 5]
                    }
                }
            }
        }

        # Pretty mode
        output_json(data, compact=False)
        pretty_output = capsys.readouterr().out

        # Compact mode
        output_json(data, compact=True)
        compact_output = capsys.readouterr().out

        # Compact should be significantly smaller
        assert len(compact_output) < len(pretty_output)

        # Both should produce same data when parsed
        assert json.loads(pretty_output) == json.loads(compact_output)


class TestFormatJsonOutput:
    """Test suite for format_json_output() function."""

    def test_format_json_output_returns_string(self):
        """Test that format_json_output returns a string."""
        data = {"key": "value"}
        result = format_json_output(data)

        assert isinstance(result, str)
        assert json.loads(result) == data

    def test_format_json_output_pretty(self):
        """Test format_json_output pretty mode."""
        data = {"status": "success", "count": 42}
        result = format_json_output(data, compact=False)

        # Verify it's pretty-printed
        assert "\n" in result
        assert "  " in result
        assert json.loads(result) == data

    def test_format_json_output_compact(self):
        """Test format_json_output compact mode."""
        data = {"status": "success", "count": 42}
        result = format_json_output(data, compact=True)

        # Verify it's compact
        assert result == '{"status":"success","count":42}'
        assert json.loads(result) == data

    def test_format_json_output_sort_keys(self):
        """Test format_json_output with sort_keys."""
        data = {"z": 1, "a": 2, "m": 3}
        result = format_json_output(data, compact=True, sort_keys=True)

        # Verify keys are sorted
        assert result == '{"a":2,"m":3,"z":1}'


class TestPrintJsonOutput:
    """Test suite for print_json_output() function."""

    def test_print_json_output_pretty(self, capsys):
        """Test print_json_output with pretty mode."""
        data = {"key": "value"}
        print_json_output(data, compact=False)

        captured = capsys.readouterr()
        output = captured.out

        assert json.loads(output) == data
        assert "\n" in output

    def test_print_json_output_compact(self, capsys):
        """Test print_json_output with compact mode."""
        data = {"key": "value"}
        print_json_output(data, compact=True)

        captured = capsys.readouterr()
        output = captured.out.strip()

        assert output == '{"key":"value"}'


class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_output_json_with_non_serializable_raises_error(self):
        """Test that non-JSON-serializable data raises appropriate error."""
        # Functions are not JSON-serializable
        data = {"function": lambda x: x}

        with pytest.raises(TypeError):
            # Capture stdout to prevent error output during test
            import sys
            from io import StringIO
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            try:
                output_json(data)
            finally:
                sys.stdout = old_stdout

    def test_output_json_very_deep_nesting(self, capsys):
        """Test output_json with deeply nested structures."""
        # Create a deeply nested structure
        data = {"level": 0}
        current = data
        for i in range(1, 20):
            current["nested"] = {"level": i}
            current = current["nested"]

        output_json(data)
        captured = capsys.readouterr()
        output = captured.out

        # Verify output is valid JSON and matches input
        parsed = json.loads(output)
        assert parsed == data

    def test_output_json_large_numbers(self, capsys):
        """Test output_json with large numbers."""
        data = {
            "large_int": 9223372036854775807,  # max int64
            "large_float": 1.7976931348623157e+308,  # near max float
            "small_float": 2.2250738585072014e-308   # near min positive float
        }
        output_json(data)

        captured = capsys.readouterr()
        output = captured.out

        parsed = json.loads(output)
        assert parsed == data

    def test_output_json_string_with_quotes(self, capsys):
        """Test output_json with strings containing quotes."""
        data = {
            "single": "It's a test",
            "double": 'He said "hello"',
            "both": """It's a "test" """
        }
        output_json(data)

        captured = capsys.readouterr()
        output = captured.out

        parsed = json.loads(output)
        assert parsed == data

    def test_output_json_string_with_newlines(self, capsys):
        """Test output_json with strings containing newlines."""
        data = {"multiline": "Line 1\nLine 2\nLine 3"}
        output_json(data)

        captured = capsys.readouterr()
        output = captured.out

        parsed = json.loads(output)
        assert parsed == data
        assert parsed["multiline"] == "Line 1\nLine 2\nLine 3"


class TestBackwardCompatibility:
    """Test backward compatibility with sdd_update/cli.py pattern."""

    def test_output_json_matches_old_signature(self, capsys):
        """Test that output_json() signature matches the old pattern."""
        # Old pattern from sdd_update/cli.py: output_json(data, compact=False)
        data = {"test": "value"}

        # Should work with positional argument
        output_json(data)
        captured = capsys.readouterr()
        assert json.loads(captured.out) == data

        # Should work with keyword argument
        output_json(data, compact=True)
        captured = capsys.readouterr()
        assert json.loads(captured.out.strip()) == data

        # Should work with both
        output_json(data=data, compact=False)
        captured = capsys.readouterr()
        assert json.loads(captured.out) == data


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
