"""
Unit tests for setup_permissions.py three-tier git permission model.

Tests that dangerous git operations are correctly categorized into the ASK list
while safe operations remain in the ALLOW list.
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from io import StringIO

# Add cli/skills_dev to path for imports
cli_path = Path(__file__).parent.parent.parent.parent / "cli" / "skills_dev"
sys.path.insert(0, str(cli_path))

from setup_permissions import (
    GIT_READ_PERMISSIONS,
    GIT_WRITE_PERMISSIONS,
    GIT_DANGEROUS_PERMISSIONS,
    GIT_APPROVAL_PERMISSIONS,
    _prompt_for_git_permissions,
    cmd_update,
)


class TestGitPermissionConstants:
    """Tests for git permission constant definitions."""

    def test_git_dangerous_permissions_exists(self):
        """Test that GIT_DANGEROUS_PERMISSIONS constant is defined."""
        assert GIT_DANGEROUS_PERMISSIONS is not None
        assert isinstance(GIT_DANGEROUS_PERMISSIONS, list)
        assert len(GIT_DANGEROUS_PERMISSIONS) > 0

    def test_dangerous_permissions_include_force_operations(self):
        """Test that dangerous permissions include force push and clean operations."""
        expected_force_ops = [
            "Bash(git push --force:*)",
            "Bash(git push -f:*)",
            "Bash(git push --force-with-lease:*)",
            "Bash(git clean -f:*)",
            "Bash(git clean -fd:*)",
            "Bash(git clean -fx:*)"
        ]
        for op in expected_force_ops:
            assert op in GIT_DANGEROUS_PERMISSIONS, f"Missing force operation: {op}"

    def test_dangerous_permissions_include_history_rewriting(self):
        """Test that dangerous permissions include history rewriting operations."""
        expected_history_ops = [
            "Bash(git reset --hard:*)",
            "Bash(git reset --mixed:*)",
            "Bash(git reset:*)",
            "Bash(git rebase:*)",
            "Bash(git commit --amend:*)",
            "Bash(git filter-branch:*)",
            "Bash(git filter-repo:*)"
        ]
        for op in expected_history_ops:
            assert op in GIT_DANGEROUS_PERMISSIONS, f"Missing history rewriting operation: {op}"

    def test_dangerous_permissions_include_deletion_operations(self):
        """Test that dangerous permissions include deletion operations."""
        expected_deletion_ops = [
            "Bash(git branch -D:*)",
            "Bash(git push origin --delete:*)",
            "Bash(git tag -d:*)"
        ]
        for op in expected_deletion_ops:
            assert op in GIT_DANGEROUS_PERMISSIONS, f"Missing deletion operation: {op}"

    def test_dangerous_permissions_include_reflog_stash(self):
        """Test that dangerous permissions include reflog and stash operations."""
        expected_reflog_stash_ops = [
            "Bash(git reflog expire:*)",
            "Bash(git reflog delete:*)",
            "Bash(git stash drop:*)",
            "Bash(git stash clear:*)"
        ]
        for op in expected_reflog_stash_ops:
            assert op in GIT_DANGEROUS_PERMISSIONS, f"Missing reflog/stash operation: {op}"

    def test_write_permissions_exclude_dangerous_operations(self):
        """Test that GIT_WRITE_PERMISSIONS only includes safe operations."""
        # Safe operations should be in write permissions
        safe_ops = [
            "Bash(git checkout:*)",
            "Bash(git add:*)",
            "Bash(git commit:*)",
            "Bash(git mv:*)",
        ]
        for op in safe_ops:
            assert op in GIT_WRITE_PERMISSIONS, f"Missing safe operation: {op}"

        # Approval-required operations should live in separate list
        approval_ops = [
            "Bash(git push:*)",
            "Bash(git rm:*)",
            "Bash(gh pr create:*)",
        ]
        for op in approval_ops:
            assert op in GIT_APPROVAL_PERMISSIONS, f"Missing approval operation: {op}"
            assert op not in GIT_WRITE_PERMISSIONS

        # Dangerous operations should NOT be in write permissions
        assert "Bash(git push --force:*)" not in GIT_WRITE_PERMISSIONS
        assert "Bash(git reset --hard:*)" not in GIT_WRITE_PERMISSIONS
        assert "Bash(git rebase:*)" not in GIT_WRITE_PERMISSIONS


class TestPromptForGitPermissions:
    """Tests for _prompt_for_git_permissions function."""

    @patch('builtins.input')
    def test_returns_dict_with_allow_and_ask_keys(self, mock_input):
        """Test that function returns a dict with 'allow' and 'ask' keys."""
        mock_input.side_effect = ['n']  # Skip git integration
        mock_printer = MagicMock()

        result = _prompt_for_git_permissions(mock_printer)

        assert isinstance(result, dict)
        assert "allow" in result
        assert "ask" in result
        assert isinstance(result["allow"], list)
        assert isinstance(result["ask"], list)

    @patch('builtins.input')
    def test_read_only_git_integration(self, mock_input):
        """Test that read-only git adds permissions to allow list only."""
        mock_input.side_effect = ['y', 'n']  # Enable git, disable writes
        mock_printer = MagicMock()

        result = _prompt_for_git_permissions(mock_printer)

        # Should have read permissions in allow list
        assert len(result["allow"]) > 0
        for perm in GIT_READ_PERMISSIONS:
            assert perm in result["allow"]

        # Should not have any dangerous permissions in ask list
        assert len(result["ask"]) == 0

    @patch('builtins.input')
    def test_write_operations_adds_to_both_lists(self, mock_input):
        """Test that enabling writes adds safe ops to allow and dangerous to ask."""
        mock_input.side_effect = ['y', 'y']  # Enable git, enable writes
        mock_printer = MagicMock()

        result = _prompt_for_git_permissions(mock_printer)

        # Should have read + write permissions in allow list
        for perm in GIT_READ_PERMISSIONS:
            assert perm in result["allow"]
        for perm in GIT_WRITE_PERMISSIONS:
            assert perm in result["allow"]

        # Approval-required and dangerous permissions should be in ASK list
        for perm in GIT_APPROVAL_PERMISSIONS:
            assert perm in result["ask"]
        for perm in GIT_DANGEROUS_PERMISSIONS:
            assert perm in result["ask"]

    @patch('builtins.input')
    def test_skip_git_returns_empty_lists(self, mock_input):
        """Test that skipping git returns empty allow and ask lists."""
        mock_input.side_effect = ['n']  # Skip git integration
        mock_printer = MagicMock()

        result = _prompt_for_git_permissions(mock_printer)

        assert len(result["allow"]) == 0
        assert len(result["ask"]) == 0


class TestPermissionApplication:
    """Integration tests for permission application logic."""

    def test_dangerous_permissions_count(self):
        """Test that we have a reasonable number of dangerous permissions."""
        # Should have at least 21 dangerous operations defined
        assert len(GIT_DANGEROUS_PERMISSIONS) >= 21

    def test_no_overlap_between_write_and_dangerous(self):
        """Test that write and dangerous permissions don't overlap."""
        write_set = set(GIT_WRITE_PERMISSIONS)
        dangerous_set = set(GIT_DANGEROUS_PERMISSIONS)

        overlap = write_set.intersection(dangerous_set)
        assert len(overlap) == 0, f"Overlap found: {overlap}"

    def test_permission_patterns_are_valid(self):
        """Test that all permission patterns follow valid format."""
        all_permissions = (
            GIT_READ_PERMISSIONS +
            GIT_WRITE_PERMISSIONS +
            GIT_DANGEROUS_PERMISSIONS
        )

        for perm in all_permissions:
            # Should start with Bash(
            assert perm.startswith("Bash("), f"Invalid pattern: {perm}"
            # Should contain :*
            assert ":*)" in perm or ":*)" in perm, f"Invalid pattern: {perm}"
            # Should not contain invalid wildcards in the middle
            assert "* --" not in perm and " *:" not in perm, f"Invalid wildcard in pattern: {perm}"


class TestNonInteractiveMode:
    """Tests for non-interactive mode with CLI parameters."""

    @patch('setup_permissions.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('json.dump')
    @patch('sys.stdin')
    def test_non_interactive_flag_prevents_prompts(self, mock_stdin, mock_json_dump, mock_json_load, mock_file_open, mock_path):
        """Test that --non-interactive flag prevents interactive prompts."""
        mock_stdin.isatty.return_value = True  # Even with TTY, non-interactive flag should prevent prompts

        # Mock args
        mock_args = MagicMock()
        mock_args.project_root = "."
        mock_args.json = False
        mock_args.non_interactive = True
        mock_args.enable_git = False
        mock_args.git_write = False

        # Mock printer
        mock_printer = MagicMock()

        # Mock Path operations
        mock_path_instance = MagicMock()
        mock_path_instance.resolve.return_value = Path("/tmp/test")
        mock_path_instance.exists.return_value = True
        mock_path_instance.__truediv__ = lambda self, other: mock_path_instance
        mock_path.return_value = mock_path_instance

        # Mock existing settings
        mock_json_load.return_value = {"permissions": {"allow": [], "ask": [], "deny": []}}

        with patch('builtins.input') as mock_input:
            # This should NOT be called in non-interactive mode
            mock_input.side_effect = AssertionError("Prompt should not be called in non-interactive mode")

            # Should not raise AssertionError
            result = cmd_update(mock_args, mock_printer)

            # Verify input was never called
            mock_input.assert_not_called()

    @patch('setup_permissions.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('json.dump')
    @patch('sys.stdin')
    def test_tty_detection_triggers_non_interactive(self, mock_stdin, mock_json_dump, mock_json_load, mock_file_open, mock_path):
        """Test that non-TTY environment automatically triggers non-interactive mode."""
        mock_stdin.isatty.return_value = False  # No TTY available

        # Mock args without explicit non_interactive flag
        mock_args = MagicMock()
        mock_args.project_root = "."
        mock_args.json = False
        mock_args.non_interactive = False
        mock_args.enable_git = False
        mock_args.git_write = False

        # Mock printer
        mock_printer = MagicMock()

        # Mock Path operations
        mock_path_instance = MagicMock()
        mock_path_instance.resolve.return_value = Path("/tmp/test")
        mock_path_instance.exists.return_value = True
        mock_path_instance.__truediv__ = lambda self, other: mock_path_instance
        mock_path.return_value = mock_path_instance

        # Mock existing settings
        mock_json_load.return_value = {"permissions": {"allow": [], "ask": [], "deny": []}}

        with patch('builtins.input') as mock_input:
            # This should NOT be called when no TTY is available
            mock_input.side_effect = AssertionError("Prompt should not be called without TTY")

            # Should not raise AssertionError
            result = cmd_update(mock_args, mock_printer)

            # Verify input was never called
            mock_input.assert_not_called()

    @patch('setup_permissions.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('json.dump')
    @patch('sys.stdin')
    def test_enable_git_read_only(self, mock_stdin, mock_json_dump, mock_json_load, mock_file_open, mock_path):
        """Test that --enable-git without --git-write adds read-only permissions."""
        mock_stdin.isatty.return_value = False

        # Mock args
        mock_args = MagicMock()
        mock_args.project_root = "."
        mock_args.json = False
        mock_args.non_interactive = True
        mock_args.enable_git = True
        mock_args.git_write = False

        # Mock printer
        mock_printer = MagicMock()

        # Mock Path operations
        mock_path_instance = MagicMock()
        mock_path_instance.resolve.return_value = Path("/tmp/test")
        mock_path_instance.exists.return_value = True
        mock_path_instance.__truediv__ = lambda self, other: mock_path_instance
        mock_path.return_value = mock_path_instance

        # Mock existing settings
        mock_json_load.return_value = {"permissions": {"allow": [], "ask": [], "deny": []}}

        # Call function
        cmd_update(mock_args, mock_printer)

        # Verify json.dump was called
        assert mock_json_dump.called

        # Get the settings that were written
        written_settings = mock_json_dump.call_args[0][0]

        # Verify git read permissions were added to allow list
        for perm in GIT_READ_PERMISSIONS:
            assert perm in written_settings["permissions"]["allow"], f"Missing read permission: {perm}"

        # Verify no write or dangerous permissions in allow list
        for perm in GIT_WRITE_PERMISSIONS:
            assert perm not in written_settings["permissions"]["allow"], f"Write permission should not be in allow: {perm}"

        # Verify no dangerous operations in ask list
        assert len(written_settings["permissions"]["ask"]) == 0

    @patch('setup_permissions.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('json.dump')
    @patch('sys.stdin')
    def test_enable_git_with_write(self, mock_stdin, mock_json_dump, mock_json_load, mock_file_open, mock_path):
        """Test that --enable-git --git-write adds full permissions."""
        mock_stdin.isatty.return_value = False

        # Mock args
        mock_args = MagicMock()
        mock_args.project_root = "."
        mock_args.json = False
        mock_args.non_interactive = True
        mock_args.enable_git = True
        mock_args.git_write = True

        # Mock printer
        mock_printer = MagicMock()

        # Mock Path operations
        mock_path_instance = MagicMock()
        mock_path_instance.resolve.return_value = Path("/tmp/test")
        mock_path_instance.exists.return_value = True
        mock_path_instance.__truediv__ = lambda self, other: mock_path_instance
        mock_path.return_value = mock_path_instance

        # Mock existing settings
        mock_json_load.return_value = {"permissions": {"allow": [], "ask": [], "deny": []}}

        # Call function
        cmd_update(mock_args, mock_printer)

        # Get the settings that were written
        written_settings = mock_json_dump.call_args[0][0]

        # Verify git read and write permissions were added to allow list
        for perm in GIT_READ_PERMISSIONS:
            assert perm in written_settings["permissions"]["allow"], f"Missing read permission: {perm}"
        for perm in GIT_WRITE_PERMISSIONS:
            assert perm in written_settings["permissions"]["allow"], f"Missing write permission: {perm}"

        # Verify dangerous operations are in ask list
        for perm in GIT_APPROVAL_PERMISSIONS:
            assert perm in written_settings["permissions"]["ask"], f"Missing approval permission: {perm}"
        for perm in GIT_DANGEROUS_PERMISSIONS:
            assert perm in written_settings["permissions"]["ask"], f"Missing dangerous permission: {perm}"

    @patch('setup_permissions.Path')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.load')
    @patch('json.dump')
    @patch('sys.stdin')
    def test_no_git_permissions_when_disabled(self, mock_stdin, mock_json_dump, mock_json_load, mock_file_open, mock_path):
        """Test that no git permissions are added when --no-enable-git is used."""
        mock_stdin.isatty.return_value = False

        # Mock args
        mock_args = MagicMock()
        mock_args.project_root = "."
        mock_args.json = False
        mock_args.non_interactive = True
        mock_args.enable_git = False
        mock_args.git_write = False

        # Mock printer
        mock_printer = MagicMock()

        # Mock Path operations
        mock_path_instance = MagicMock()
        mock_path_instance.resolve.return_value = Path("/tmp/test")
        mock_path_instance.exists.return_value = True
        mock_path_instance.__truediv__ = lambda self, other: mock_path_instance
        mock_path.return_value = mock_path_instance

        # Mock existing settings
        mock_json_load.return_value = {"permissions": {"allow": [], "ask": [], "deny": []}}

        # Call function
        cmd_update(mock_args, mock_printer)

        # Get the settings that were written
        written_settings = mock_json_dump.call_args[0][0]

        # Verify no git permissions were added
        for perm in GIT_READ_PERMISSIONS:
            assert perm not in written_settings["permissions"]["allow"], f"Read permission should not be added: {perm}"
        for perm in GIT_WRITE_PERMISSIONS:
            assert perm not in written_settings["permissions"]["allow"], f"Write permission should not be added: {perm}"
