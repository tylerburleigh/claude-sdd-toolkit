"""
Unit tests for sdd_common.git_operations module.

Tests git operations: check_git_repo, get_current_branch, get_base_branch, get_remote_url.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

from claude_skills.common import (
    GitError,
    check_git_repo,
    get_current_branch,
    get_base_branch,
    get_remote_url,
)


class TestCheckGitRepo:
    """Tests for check_git_repo function."""

    @patch('subprocess.run')
    def test_check_git_repo_returns_true_when_in_repo(self, mock_run):
        """Test check_git_repo returns True when inside a git repository."""
        mock_run.return_value = MagicMock(returncode=0)

        result = check_git_repo()

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["git", "rev-parse", "--is-inside-work-tree"]

    @patch('subprocess.run')
    def test_check_git_repo_returns_false_when_not_in_repo(self, mock_run):
        """Test check_git_repo returns False when not in a git repository."""
        mock_run.return_value = MagicMock(returncode=1)

        result = check_git_repo()

        assert result is False

    @patch('subprocess.run')
    def test_check_git_repo_handles_file_not_found(self, mock_run):
        """Test check_git_repo handles FileNotFoundError gracefully."""
        mock_run.side_effect = FileNotFoundError("git not found")

        result = check_git_repo()

        assert result is False

    @patch('subprocess.run')
    def test_check_git_repo_handles_timeout(self, mock_run):
        """Test check_git_repo handles timeout gracefully."""
        mock_run.side_effect = subprocess.TimeoutExpired("git", 5)

        result = check_git_repo()

        assert result is False

    @patch('subprocess.run')
    def test_check_git_repo_with_custom_path(self, mock_run):
        """Test check_git_repo with a custom path."""
        mock_run.return_value = MagicMock(returncode=0)

        result = check_git_repo("/custom/path")

        assert result is True
        # Check that the cwd argument was set correctly
        assert mock_run.call_args[1]['cwd'] == Path("/custom/path").resolve()


class TestGetCurrentBranch:
    """Tests for get_current_branch function."""

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_current_branch_returns_branch_name(self, mock_run, mock_check):
        """Test get_current_branch returns the current branch name."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="main\n"
        )

        result = get_current_branch()

        assert result == "main"

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_current_branch_handles_feature_branch(self, mock_run, mock_check):
        """Test get_current_branch with a feature branch."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="feature/git-integration\n"
        )

        result = get_current_branch()

        assert result == "feature/git-integration"

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_current_branch_handles_detached_head(self, mock_run, mock_check):
        """Test get_current_branch handles detached HEAD state."""
        mock_check.return_value = True

        # First call returns "HEAD" (detached state)
        # Second call returns the commit SHA
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="HEAD\n"),
            MagicMock(returncode=0, stdout="abc123\n")
        ]

        result = get_current_branch()

        assert result == "detached-abc123"
        assert mock_run.call_count == 2

    @patch('claude_skills.common.git_operations.check_git_repo')
    def test_get_current_branch_raises_error_when_not_in_repo(self, mock_check):
        """Test get_current_branch raises GitError when not in a repository."""
        mock_check.return_value = False

        with pytest.raises(GitError, match="Not a git repository"):
            get_current_branch()

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_current_branch_raises_error_on_failure(self, mock_run, mock_check):
        """Test get_current_branch raises GitError when git command fails."""
        mock_check.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "git", stderr="fatal: not a git repository"
        )

        with pytest.raises(GitError, match="Failed to get current branch"):
            get_current_branch()

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_current_branch_raises_error_on_timeout(self, mock_run, mock_check):
        """Test get_current_branch raises GitError on timeout."""
        mock_check.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("git", 5)

        with pytest.raises(GitError, match="Git command timed out"):
            get_current_branch()


class TestGetBaseBranch:
    """Tests for get_base_branch function."""

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_base_branch_returns_main_when_exists(self, mock_run, mock_check):
        """Test get_base_branch returns 'main' when it exists."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="* feature/test\n  main\n  remotes/origin/main\n"
        )

        result = get_base_branch()

        assert result == "main"

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_base_branch_returns_master_when_main_not_exists(self, mock_run, mock_check):
        """Test get_base_branch returns 'master' when 'main' doesn't exist."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="* feature/test\n  master\n  remotes/origin/master\n"
        )

        result = get_base_branch()

        assert result == "master"

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_base_branch_prefers_main_over_master(self, mock_run, mock_check):
        """Test get_base_branch prefers 'main' when both exist."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="* feature/test\n  main\n  master\n  remotes/origin/main\n"
        )

        result = get_base_branch()

        assert result == "main"

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_base_branch_handles_remote_only_branches(self, mock_run, mock_check):
        """Test get_base_branch detects main even if only remote exists."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="* feature/test\n  remotes/origin/main\n  remotes/origin/HEAD -> origin/main\n"
        )

        result = get_base_branch()

        assert result == "main"

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_base_branch_raises_error_when_neither_exists(self, mock_run, mock_check):
        """Test get_base_branch raises error when neither main nor master exists."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="* develop\n  feature/test\n"
        )

        with pytest.raises(GitError, match="Could not determine base branch"):
            get_base_branch()

    @patch('claude_skills.common.git_operations.check_git_repo')
    def test_get_base_branch_raises_error_when_not_in_repo(self, mock_check):
        """Test get_base_branch raises GitError when not in a repository."""
        mock_check.return_value = False

        with pytest.raises(GitError, match="Not a git repository"):
            get_base_branch()

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_base_branch_raises_error_on_failure(self, mock_run, mock_check):
        """Test get_base_branch raises GitError when git command fails."""
        mock_check.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "git", stderr="fatal: not a git repository"
        )

        with pytest.raises(GitError, match="Failed to get base branch"):
            get_base_branch()


class TestGetRemoteUrl:
    """Tests for get_remote_url function."""

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_remote_url_returns_url_for_origin(self, mock_run, mock_check):
        """Test get_remote_url returns URL for origin remote."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="https://github.com/user/repo.git\n"
        )

        result = get_remote_url()

        assert result == "https://github.com/user/repo.git"

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_remote_url_returns_ssh_url(self, mock_run, mock_check):
        """Test get_remote_url returns SSH URL."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="git@github.com:user/repo.git\n"
        )

        result = get_remote_url()

        assert result == "git@github.com:user/repo.git"

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_remote_url_with_custom_remote(self, mock_run, mock_check):
        """Test get_remote_url with a custom remote name."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="https://github.com/upstream/repo.git\n"
        )

        result = get_remote_url(remote="upstream")

        assert result == "https://github.com/upstream/repo.git"
        # Check that the remote argument was passed correctly
        args = mock_run.call_args[0][0]
        assert "upstream" in args

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_remote_url_returns_none_when_remote_not_exists(self, mock_run, mock_check):
        """Test get_remote_url returns None when remote doesn't exist."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(returncode=1)

        result = get_remote_url()

        assert result is None

    @patch('claude_skills.common.git_operations.check_git_repo')
    def test_get_remote_url_raises_error_when_not_in_repo(self, mock_check):
        """Test get_remote_url raises GitError when not in a repository."""
        mock_check.return_value = False

        with pytest.raises(GitError, match="Not a git repository"):
            get_remote_url()

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_remote_url_raises_error_on_timeout(self, mock_run, mock_check):
        """Test get_remote_url raises GitError on timeout."""
        mock_check.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired("git", 5)

        with pytest.raises(GitError, match="Git command timed out"):
            get_remote_url()

    @patch('claude_skills.common.git_operations.check_git_repo')
    @patch('subprocess.run')
    def test_get_remote_url_with_custom_path(self, mock_run, mock_check):
        """Test get_remote_url with a custom path."""
        mock_check.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="https://github.com/user/repo.git\n"
        )

        result = get_remote_url(path="/custom/path")

        assert result == "https://github.com/user/repo.git"
        # Check that the cwd argument was set correctly
        assert mock_run.call_args[1]['cwd'] == Path("/custom/path").resolve()
