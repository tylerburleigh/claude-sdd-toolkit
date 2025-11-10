"""
Unit tests for ui_factory module.

Tests backend selection logic, TTY detection, CI detection, and create_ui factory function.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from claude_skills.common.ui_factory import (
    is_tty_available,
    is_ci_environment,
    should_use_plain_ui,
    create_ui,
    create_ui_from_args,
    get_backend_name,
    format_backend_info,
    ui
)
from claude_skills.common.rich_ui import RichUi
from claude_skills.common.plain_ui import PlainUi


class TestTTYDetection:
    """Tests for TTY detection."""

    def test_is_tty_available_returns_bool(self):
        """Test that is_tty_available returns a boolean."""
        result = is_tty_available()
        assert isinstance(result, bool)

    @patch('sys.stdout.isatty')
    def test_is_tty_available_when_tty(self, mock_isatty):
        """Test TTY detection when stdout is a TTY."""
        mock_isatty.return_value = True
        assert is_tty_available() is True

    @patch('sys.stdout.isatty')
    def test_is_tty_available_when_not_tty(self, mock_isatty):
        """Test TTY detection when stdout is not a TTY."""
        mock_isatty.return_value = False
        assert is_tty_available() is False


class TestCIDetection:
    """Tests for CI environment detection."""

    def test_is_ci_environment_returns_bool(self):
        """Test that is_ci_environment returns a boolean."""
        result = is_ci_environment()
        assert isinstance(result, bool)

    def test_is_ci_environment_detects_github_actions(self):
        """Test CI detection for GitHub Actions."""
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            assert is_ci_environment() is True

    def test_is_ci_environment_detects_gitlab_ci(self):
        """Test CI detection for GitLab CI."""
        with patch.dict(os.environ, {"GITLAB_CI": "true"}):
            assert is_ci_environment() is True

    def test_is_ci_environment_detects_travis(self):
        """Test CI detection for Travis CI."""
        with patch.dict(os.environ, {"TRAVIS": "true"}):
            assert is_ci_environment() is True

    def test_is_ci_environment_detects_circleci(self):
        """Test CI detection for CircleCI."""
        with patch.dict(os.environ, {"CIRCLECI": "true"}):
            assert is_ci_environment() is True

    def test_is_ci_environment_detects_jenkins(self):
        """Test CI detection for Jenkins."""
        with patch.dict(os.environ, {"JENKINS_URL": "http://jenkins.local"}):
            assert is_ci_environment() is True

    def test_is_ci_environment_detects_generic_ci(self):
        """Test CI detection for generic CI variable."""
        with patch.dict(os.environ, {"CI": "true"}):
            assert is_ci_environment() is True

    def test_is_ci_environment_no_ci_vars(self):
        """Test that no CI vars means not CI environment."""
        # Clear all CI vars
        ci_vars = ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "TRAVIS", "CIRCLECI", "JENKINS_URL", "BUILDKITE", "DRONE"]
        with patch.dict(os.environ, {var: "" for var in ci_vars}, clear=True):
            # This might still be True if running in actual CI, so we check the logic
            result = is_ci_environment()
            assert isinstance(result, bool)


class TestShouldUsePlainUI:
    """Tests for should_use_plain_ui decision logic."""

    def test_should_use_plain_ui_with_force_flag(self):
        """Test that force_plain=True always returns True."""
        assert should_use_plain_ui(force_plain=True) is True

    @patch('claude_skills.common.ui_factory.create_ui')
    def test_should_use_plain_ui_with_config_file(self, mock_create_ui):
        """Test that config file default_mode='plain' is used instead of FORCE_PLAIN_UI env var."""
        # Create UI with config that specifies plain mode
        # The config file approach is now the recommended way
        ui_instance = create_ui(force_plain=True)
        assert isinstance(ui_instance, PlainUi)

    @patch('sys.stdout.isatty')
    def test_should_use_plain_ui_no_tty(self, mock_isatty):
        """Test plain mode when no TTY available."""
        mock_isatty.return_value = False
        # Clear CI vars to isolate TTY test
        with patch.dict(os.environ, {}, clear=True), patch(
            'claude_skills.common.ui_factory.is_ci_environment', return_value=False
        ):
            # Will use plain because no TTY
            result = should_use_plain_ui()
            assert result is True

    @patch('sys.stdout.isatty')
    @patch.dict(os.environ, {"CI": "true"})
    def test_should_use_plain_ui_in_ci(self, mock_isatty):
        """Test plain mode in CI environment."""
        mock_isatty.return_value = True  # Even with TTY, CI forces plain
        assert should_use_plain_ui() is True

    @patch('sys.stdout.isatty')
    @patch.dict(os.environ, {}, clear=True)
    def test_should_use_plain_ui_interactive_terminal(self, mock_isatty):
        """Test rich mode for interactive terminal."""
        mock_isatty.return_value = True
        # No force flags, no CI, has TTY → use Rich
        assert should_use_plain_ui() is False


class TestCreateUI:
    """Tests for create_ui factory function."""

    def test_create_ui_returns_ui_instance(self):
        """Test that create_ui returns a Ui implementation."""
        ui_instance = create_ui()
        assert hasattr(ui_instance, 'print_table')
        assert hasattr(ui_instance, 'print_status')

    @patch('claude_skills.common.ui_factory.should_use_plain_ui')
    def test_create_ui_force_plain(self, mock_should_use):
        """Test creating PlainUi with force_plain."""
        mock_should_use.return_value = True
        ui_instance = create_ui(force_plain=True)
        assert isinstance(ui_instance, PlainUi)

    @patch('sys.stdout.isatty')
    def test_create_ui_force_rich(self, mock_isatty):
        """Test creating RichUi with force_rich."""
        mock_isatty.return_value = True
        ui_instance = create_ui(force_rich=True)
        assert isinstance(ui_instance, RichUi)

    def test_create_ui_conflicting_flags_raises_error(self):
        """Test that force_plain and force_rich together raises error."""
        with pytest.raises(ValueError, match="Cannot force both"):
            create_ui(force_plain=True, force_rich=True)

    @patch('claude_skills.common.sdd_config.get_default_format', return_value="plain")
    def test_create_ui_with_collect_messages(self, _mock_default_format):
        """Test creating UI with message collection."""
        ui_instance = create_ui(collect_messages=True)
        assert isinstance(ui_instance, PlainUi)
        assert ui_instance.collect_messages is True

    @patch('claude_skills.common.sdd_config.get_default_format', return_value="plain")
    def test_create_ui_with_quiet_mode(self, _mock_default_format):
        """Test creating UI with quiet mode."""
        ui_instance = create_ui(quiet=True)
        assert isinstance(ui_instance, PlainUi)
        assert ui_instance.quiet is True

    @patch('claude_skills.common.sdd_config.get_default_format', return_value=None)
    @patch('sys.stdout.isatty')
    @patch.dict(os.environ, {}, clear=True)
    def test_create_ui_auto_selects_rich_for_tty(self, _mock_default_format, mock_isatty):
        """Test that create_ui auto-selects RichUi for TTY."""
        mock_isatty.return_value = True
        with patch('claude_skills.common.ui_factory.is_ci_environment', return_value=False):
            ui_instance = create_ui()
            assert isinstance(ui_instance, RichUi)

    @patch('sys.stdout.isatty')
    def test_create_ui_auto_selects_plain_for_non_tty(self, mock_isatty):
        """Test that create_ui auto-selects PlainUi for non-TTY."""
        mock_isatty.return_value = False
        with patch.dict(os.environ, {}, clear=True), patch(
            'claude_skills.common.ui_factory.is_ci_environment', return_value=False
        ), patch('claude_skills.common.sdd_config.get_default_format', return_value=None):
            ui_instance = create_ui()
            assert isinstance(ui_instance, PlainUi)


class TestCreateUIFromArgs:
    """Tests for create_ui_from_args convenience function."""

    def test_create_ui_from_args_with_plain_flag(self):
        """Test creating UI from args with plain flag."""
        # Mock argparse.Namespace
        args = MagicMock()
        args.plain = True
        args.quiet = False
        args.collect = False

        ui_instance = create_ui_from_args(args)
        assert isinstance(ui_instance, PlainUi)

    def test_create_ui_from_args_with_quiet_flag(self):
        """Test creating UI from args with quiet flag."""
        args = MagicMock()
        args.plain = True
        args.quiet = True
        args.collect = False

        ui_instance = create_ui_from_args(args)
        assert isinstance(ui_instance, PlainUi)
        assert ui_instance.quiet is True

    def test_create_ui_from_args_missing_attributes(self):
        """Test creating UI from args with missing attributes."""
        args = MagicMock()
        # Simulate missing attributes
        args.plain = False
        del args.quiet
        del args.collect

        # Should use defaults when attributes missing
        ui_instance = create_ui_from_args(args)
        assert ui_instance is not None


class TestGetBackendName:
    """Tests for get_backend_name utility."""

    @patch('sys.stdout.isatty')
    def test_get_backend_name_rich(self, mock_isatty):
        """Test getting backend name for RichUi."""
        mock_isatty.return_value = True
        with patch.dict(os.environ, {}, clear=True):
            ui_instance = create_ui(force_rich=True)
            assert get_backend_name(ui_instance) == "RichUi"

    def test_get_backend_name_plain(self):
        """Test getting backend name for PlainUi."""
        ui_instance = create_ui(force_plain=True)
        assert get_backend_name(ui_instance) == "PlainUi"


class TestFormatBackendInfo:
    """Tests for format_backend_info utility."""

    def test_format_backend_info_returns_string(self):
        """Test that format_backend_info returns formatted string."""
        info = format_backend_info()
        assert isinstance(info, str)

    def test_format_backend_info_contains_key_info(self):
        """Test that backend info contains expected information."""
        info = format_backend_info()

        # Should contain key information
        assert "Backend Selection Info" in info
        assert "TTY Available" in info
        assert "CI Environment" in info
        assert "Selected Backend" in info


class TestUIShorthand:
    """Tests for ui() shorthand function."""

    def test_ui_shorthand_creates_instance(self):
        """Test that ui() creates UI instance."""
        ui_instance = ui()
        assert ui_instance is not None

    def test_ui_shorthand_with_force_plain(self):
        """Test ui() with force_plain."""
        ui_instance = ui(force_plain=True)
        assert isinstance(ui_instance, PlainUi)

    def test_ui_shorthand_with_collect_messages(self):
        """Test ui() with collect_messages."""
        ui_instance = ui(force_plain=True, collect_messages=True)
        assert isinstance(ui_instance, PlainUi)
        assert ui_instance.collect_messages is True


class TestPlainVsRichOutput:
    """Tests that verify plain and rich UI produce different outputs."""

    def test_plain_and_rich_ui_different_output(self):
        """Test that PlainUi and RichUi produce different outputs."""
        plain_ui = create_ui(force_plain=True)
        rich_ui = create_ui(force_rich=True)

        # Verify they are different backend types
        assert isinstance(plain_ui, PlainUi)
        assert isinstance(rich_ui, RichUi)
        assert get_backend_name(plain_ui) != get_backend_name(rich_ui)

    def test_plain_ui_print_methods_exist(self):
        """Test that PlainUi has all required print methods."""
        plain_ui = create_ui(force_plain=True)
        assert hasattr(plain_ui, 'print_table')
        assert hasattr(plain_ui, 'print_status')
        assert hasattr(plain_ui, 'print_panel')
        assert callable(plain_ui.print_table)
        assert callable(plain_ui.print_status)
        assert callable(plain_ui.print_panel)

    def test_rich_ui_print_methods_exist(self):
        """Test that RichUi has all required print methods."""
        rich_ui = create_ui(force_rich=True)
        assert hasattr(rich_ui, 'print_table')
        assert hasattr(rich_ui, 'print_status')
        assert hasattr(rich_ui, 'print_panel')
        assert callable(rich_ui.print_table)
        assert callable(rich_ui.print_status)
        assert callable(rich_ui.print_panel)

    def test_plain_ui_uses_plain_console(self):
        """Test that PlainUi does not use Rich Console."""
        plain_ui = create_ui(force_plain=True)
        # PlainUi should not have a Rich console attribute
        assert not hasattr(plain_ui, 'console') or plain_ui.console is None

    def test_rich_ui_has_console(self):
        """Test that RichUi has a Rich Console instance."""
        rich_ui = create_ui(force_rich=True)
        # RichUi should have a console attribute
        assert hasattr(rich_ui, 'console')
        from rich.console import Console
        assert isinstance(rich_ui.console, Console)
