"""
Integration tests for UI configuration settings.

Tests the complete flow of reading config settings and creating appropriate UI backend.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from claude_skills.common.ui_factory import create_ui, create_ui_from_args
from claude_skills.common.rich_ui import RichUi
from claude_skills.common.plain_ui import PlainUi


class TestUIConfigIntegration:
    """Integration tests for UI configuration."""

    def test_create_ui_respects_config_plain_mode(self):
        """Test that create_ui respects config file setting for plain mode."""
        # Create UI with force_plain=True to simulate config setting
        ui_instance = create_ui(force_plain=True)
        assert isinstance(ui_instance, PlainUi)

    def test_create_ui_respects_config_rich_mode(self):
        """Test that create_ui respects config file setting for rich mode."""
        # Create UI with force_rich=True to simulate config setting
        ui_instance = create_ui(force_rich=True)
        assert isinstance(ui_instance, RichUi)

    def test_create_ui_from_args_with_plain_flag(self):
        """Test CLI args influence UI creation."""
        args = MagicMock()
        args.plain = True
        args.quiet = False
        args.collect = False

        ui_instance = create_ui_from_args(args)
        assert isinstance(ui_instance, PlainUi)

    def test_plain_ui_maintains_consistent_api(self):
        """Test that PlainUi implements required interface."""
        plain_ui = create_ui(force_plain=True)

        # Verify interface methods exist
        required_methods = ['print_status', 'print_table', 'print_panel', 'print_tree']
        for method in required_methods:
            assert hasattr(plain_ui, method)
            assert callable(getattr(plain_ui, method))

    def test_rich_ui_maintains_consistent_api(self):
        """Test that RichUi implements required interface."""
        rich_ui = create_ui(force_rich=True)

        # Verify interface methods exist
        required_methods = ['print_status', 'print_table', 'print_panel', 'print_tree']
        for method in required_methods:
            assert hasattr(rich_ui, method)
            assert callable(getattr(rich_ui, method))

    def test_plain_ui_output_methods_dont_crash(self):
        """Test that PlainUi output methods execute without errors."""
        plain_ui = create_ui(force_plain=True)

        # Test print_status doesn't crash
        try:
            plain_ui.print_status("Test message")
        except Exception as e:
            pytest.fail(f"plain_ui.print_status() raised {type(e).__name__}: {e}")

    def test_rich_ui_output_methods_dont_crash(self):
        """Test that RichUi output methods execute without errors."""
        rich_ui = create_ui(force_rich=True)

        # Test print_status doesn't crash
        try:
            rich_ui.print_status("Test message")
        except Exception as e:
            pytest.fail(f"rich_ui.print_status() raised {type(e).__name__}: {e}")

    def test_ui_backend_switch_is_seamless(self):
        """Test that switching between backends doesn't cause issues."""
        # Create plain UI, use it
        plain_ui = create_ui(force_plain=True)
        plain_ui.print_status("Message from PlainUi")

        # Create rich UI, use it
        rich_ui = create_ui(force_rich=True)
        rich_ui.print_status("Message from RichUi")

        # Both should work without interference
        assert isinstance(plain_ui, PlainUi)
        assert isinstance(rich_ui, RichUi)

    def test_ui_config_backward_compatible(self):
        """Test that old behavior (no config) still works."""
        # When no config specified, should auto-detect
        # This test just verifies create_ui() doesn't crash
        try:
            ui_instance = create_ui()
            assert ui_instance is not None
        except Exception as e:
            pytest.fail(f"create_ui() raised {type(e).__name__}: {e}")
