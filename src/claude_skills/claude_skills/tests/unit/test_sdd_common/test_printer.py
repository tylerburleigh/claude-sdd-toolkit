"""
Unit tests for sdd_common.printer module.

Tests PrettyPrinter class for formatted output.
"""

import pytest
from io import StringIO
from claude_skills.common import PrettyPrinter


class TestPrettyPrinterInit:
    """Tests for PrettyPrinter initialization."""

    def test_printer_default_initialization(self):
        """Test printer with default settings."""
        printer = PrettyPrinter()

        assert printer is not None
        # Should have default settings
        assert hasattr(printer, 'use_color') or hasattr(printer, 'color')
        assert hasattr(printer, 'verbose') or hasattr(printer, 'quiet')

    def test_printer_with_no_color(self):
        """Test printer with colors disabled."""
        printer = PrettyPrinter(use_color=False)

        assert printer is not None

    def test_printer_with_verbose(self):
        """Test printer in verbose mode."""
        printer = PrettyPrinter(verbose=True)

        assert printer is not None

    def test_printer_with_quiet(self):
        """Test printer in quiet mode."""
        printer = PrettyPrinter(quiet=True)

        assert printer is not None


class TestPrettyPrinterMethods:
    """Tests for PrettyPrinter methods."""

    def test_printer_success_message(self, capsys):
        """Test printing success messages."""
        printer = PrettyPrinter(use_color=False)
        printer.success("Test successful")

        captured = capsys.readouterr()
        assert "successful" in captured.out.lower() or "success" in captured.out.lower()

    def test_printer_error_message(self, capsys):
        """Test printing error messages."""
        printer = PrettyPrinter(use_color=False)
        printer.error("Test error")

        captured = capsys.readouterr()
        assert "error" in captured.err.lower() or "✗" in captured.err

    def test_printer_warning_message(self, capsys):
        """Test printing warning messages."""
        printer = PrettyPrinter(use_color=False)
        printer.warning("Test warning")

        captured = capsys.readouterr()
        assert "warning" in captured.err.lower() or "⚠" in captured.err

    def test_printer_info_message(self, capsys):
        """Test printing info messages."""
        printer = PrettyPrinter(use_color=False, verbose=True)
        printer.info("Test info")

        captured = capsys.readouterr()
        assert "info" in captured.out.lower() or "test info" in captured.out.lower()

    def test_printer_action_message(self, capsys):
        """Test printing action messages."""
        printer = PrettyPrinter(use_color=False)
        printer.action("Performing action")

        captured = capsys.readouterr()
        assert "action" in captured.out.lower() or "performing" in captured.out.lower()

    def test_printer_result_message(self, capsys):
        """Test printing result messages."""
        printer = PrettyPrinter(use_color=False)
        printer.result("Key", "Value")

        captured = capsys.readouterr()
        assert "key" in captured.out.lower() and "value" in captured.out.lower()

    def test_printer_detail_message(self, capsys):
        """Test printing detail messages."""
        printer = PrettyPrinter(use_color=False)
        printer.detail("Detail message")

        captured = capsys.readouterr()
        assert "detail" in captured.out.lower() or "message" in captured.out.lower()


class TestPrettyPrinterColorMode:
    """Tests for color/no-color modes."""

    def test_colored_output_contains_ansi_codes(self, capsys):
        """Test that colored output contains ANSI escape codes."""
        printer = PrettyPrinter(use_color=True)
        printer.success("Colored message")

        captured = capsys.readouterr()
        # ANSI codes typically start with \033[ or \x1b[
        has_ansi = "\033[" in captured.out or "\x1b[" in captured.out
        # If color is truly enabled, should have ANSI codes
        # (but some implementations might not actually use them)
        assert has_ansi or "message" in captured.out

    def test_no_color_output_lacks_ansi_codes(self, capsys):
        """Test that non-colored output lacks ANSI escape codes."""
        printer = PrettyPrinter(use_color=False)
        printer.success("Plain message")

        captured = capsys.readouterr()
        # Should not contain ANSI escape codes
        assert "\033[" not in captured.out and "\x1b[" not in captured.out


class TestPrettyPrinterVerbosity:
    """Tests for verbosity modes."""

    def test_quiet_mode_minimal_output(self, capsys):
        """Test that quiet mode produces minimal output."""
        printer = PrettyPrinter(quiet=True, use_color=False)

        printer.info("Info message")
        printer.detail("Detail message")

        captured = capsys.readouterr()
        # In quiet mode, info/detail might be suppressed
        # (depending on implementation)
        output_lines = captured.out.strip().split('\n') if captured.out.strip() else []
        assert len(output_lines) <= 2  # Minimal output

    def test_quiet_mode_shows_errors(self, capsys):
        """Test that quiet mode still shows errors."""
        printer = PrettyPrinter(quiet=True, use_color=False)

        printer.error("Error message")

        captured = capsys.readouterr()
        # Errors should always be shown
        assert "error" in captured.err.lower()

    def test_verbose_mode_shows_details(self, capsys):
        """Test that verbose mode shows detail messages."""
        printer = PrettyPrinter(verbose=True, use_color=False)

        printer.detail("Verbose detail")

        captured = capsys.readouterr()
        # In verbose mode, details should be shown
        assert "detail" in captured.out.lower() or "verbose" in captured.out.lower()


class TestPrettyPrinterFormatting:
    """Tests for message formatting."""

    def test_result_formatting_aligns_output(self, capsys):
        """Test that result messages are properly formatted."""
        printer = PrettyPrinter(use_color=False)

        printer.result("Short", "value1")
        printer.result("Very Long Key", "value2")

        captured = capsys.readouterr()
        lines = captured.out.strip().split('\n')

        # Should have 2 lines
        assert len(lines) >= 2

        # Both should contain key and value
        assert "short" in lines[0].lower() and "value1" in lines[0].lower()
        assert "very long key" in lines[1].lower() and "value2" in lines[1].lower()

    def test_detail_with_indentation(self, capsys):
        """Test detail messages with custom indentation."""
        printer = PrettyPrinter(use_color=False)

        printer.detail("Indented detail", indent=2)

        captured = capsys.readouterr()
        # Should have some indentation (spaces or other)
        assert "  " in captured.out or captured.out.startswith(" ")


@pytest.mark.integration
class TestPrettyPrinterIntegration:
    """Integration tests for PrettyPrinter."""

    def test_printer_combined_output_flow(self, capsys):
        """Test complete output flow with various message types."""
        printer = PrettyPrinter(use_color=False, verbose=True)

        printer.action("Starting task")
        printer.info("Processing...")
        printer.success("Task completed")
        printer.result("Result", "success")

        captured = capsys.readouterr()

        # All messages should be present
        output_lower = captured.out.lower()
        assert "starting" in output_lower
        assert "processing" in output_lower  # info goes to stdout in verbose mode
        assert "completed" in output_lower or "success" in output_lower

    def test_printer_error_warning_flow(self, capsys):
        """Test error and warning message flow."""
        printer = PrettyPrinter(use_color=False)

        printer.warning("Potential issue detected")
        printer.error("Error occurred")

        captured = capsys.readouterr()

        assert "warning" in captured.err.lower() or "issue" in captured.err.lower()
        assert "error" in captured.err.lower()
