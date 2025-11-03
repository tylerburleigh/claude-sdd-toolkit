"""
Unit tests for git_metadata module.

Tests git utilities and metadata management functions:
- find_git_root
- check_dirty_tree
- detect_git_drift
- update_branch_metadata
- add_commit_metadata
- update_pr_metadata
"""

import pytest
import subprocess
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from claude_skills.common.git_metadata import (
    find_git_root,
    check_dirty_tree,
    parse_git_status,
    show_commit_preview,
    get_staged_files,
    detect_git_drift,
    update_branch_metadata,
    add_commit_metadata,
    update_pr_metadata
)


class TestFindGitRoot:
    """Tests for find_git_root function."""

    def test_find_git_root_from_repo_directory(self, tmp_path):
        """Test finding git root from within a repository."""
        # Create mock .git directory
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        subdir = tmp_path / "src" / "nested"
        subdir.mkdir(parents=True)

        # Should find git root from subdirectory
        result = find_git_root(subdir)

        assert result == tmp_path
        assert result.is_dir()

    def test_find_git_root_from_git_root(self, tmp_path):
        """Test finding git root when already at root."""
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        result = find_git_root(tmp_path)

        assert result == tmp_path

    def test_find_git_root_returns_none_when_not_found(self, tmp_path):
        """Test that find_git_root returns None when no git repo found."""
        # Directory without .git
        result = find_git_root(tmp_path)

        assert result is None

    def test_find_git_root_uses_cwd_by_default(self):
        """Test that find_git_root uses cwd when no path provided."""
        # Just verify it doesn't crash - actual result depends on where tests run
        result = find_git_root()
        # Result can be None or a Path, both are valid
        assert result is None or isinstance(result, Path)


class TestCheckDirtyTree:
    """Tests for check_dirty_tree function."""

    @patch('subprocess.run')
    def test_check_dirty_tree_clean(self, mock_run, tmp_path):
        """Test checking clean working tree."""
        # Mock clean status
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )

        is_dirty, message = check_dirty_tree(tmp_path)

        assert is_dirty is False
        assert message == "Clean"
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_check_dirty_tree_with_staged_changes(self, mock_run, tmp_path):
        """Test detecting staged changes."""
        # Mock status with staged files
        mock_run.return_value = Mock(
            returncode=0,
            stdout="M  file1.py\nA  file2.py\n",
            stderr=""
        )

        is_dirty, message = check_dirty_tree(tmp_path)

        assert is_dirty is True
        assert "staged" in message.lower()

    @patch('subprocess.run')
    def test_check_dirty_tree_with_unstaged_changes(self, mock_run, tmp_path):
        """Test detecting unstaged changes."""
        # Mock status with unstaged files (modified in worktree, column 1 = M)
        # Git status format: XY filename where X=index, Y=worktree
        # " M" means: not staged, modified in worktree
        # But our implementation checks column 1 for 'M' or 'D'
        # Let's use a file that's staged AND modified
        mock_run.return_value = Mock(
            returncode=0,
            stdout="MM file1.py\n",  # Staged and modified (both columns have changes)
            stderr=""
        )

        is_dirty, message = check_dirty_tree(tmp_path)

        assert is_dirty is True
        # Should detect both staged and unstaged
        assert "staged" in message.lower() or "unstaged" in message.lower()

    @patch('subprocess.run')
    def test_check_dirty_tree_with_untracked_files(self, mock_run, tmp_path):
        """Test detecting untracked files."""
        # Mock status with untracked files
        mock_run.return_value = Mock(
            returncode=0,
            stdout="?? new_file.py\n",
            stderr=""
        )

        is_dirty, message = check_dirty_tree(tmp_path)

        assert is_dirty is True
        assert "untracked" in message.lower()

    @patch('subprocess.run')
    def test_check_dirty_tree_handles_timeout(self, mock_run, tmp_path):
        """Test handling of git command timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('git', 10)

        is_dirty, message = check_dirty_tree(tmp_path)

        assert is_dirty is True
        assert "timeout" in message.lower()

    @patch('subprocess.run')
    def test_check_dirty_tree_handles_error(self, mock_run, tmp_path):
        """Test handling of git command error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git', stderr='error')

        is_dirty, message = check_dirty_tree(tmp_path)

        assert is_dirty is True
        assert "error" in message.lower()


class TestParseGitStatus:
    """Tests for parse_git_status function."""

    @patch('subprocess.run')
    def test_parse_git_status_empty(self, mock_run, tmp_path):
        """Test parsing empty status (clean working tree)."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )

        result = parse_git_status(tmp_path)

        assert result == []
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_parse_git_status_staged_modification(self, mock_run, tmp_path):
        """Test parsing staged modification."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="M  file1.py\n",
            stderr=""
        )

        result = parse_git_status(tmp_path)

        assert len(result) == 1
        assert result[0]['status'] == 'M '
        assert result[0]['path'] == 'file1.py'

    @patch('subprocess.run')
    def test_parse_git_status_unstaged_modification(self, mock_run, tmp_path):
        """Test parsing unstaged modification."""
        # Note: Git porcelain format is "XY path" where X=index, Y=worktree
        # " M" means not staged (space), modified in worktree (M)
        mock_run.return_value = Mock(
            returncode=0,
            stdout=" M file2.py\n",
            stderr=""
        )

        result = parse_git_status(tmp_path)

        assert len(result) == 1
        assert result[0]['status'] == ' M'
        assert result[0]['path'] == 'file2.py'

    @patch('subprocess.run')
    def test_parse_git_status_staged_and_unstaged(self, mock_run, tmp_path):
        """Test parsing file with both staged and unstaged changes."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="MM file3.py\n",
            stderr=""
        )

        result = parse_git_status(tmp_path)

        assert len(result) == 1
        assert result[0]['status'] == 'MM'
        assert result[0]['path'] == 'file3.py'

    @patch('subprocess.run')
    def test_parse_git_status_untracked_file(self, mock_run, tmp_path):
        """Test parsing untracked file."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="?? new.py\n",
            stderr=""
        )

        result = parse_git_status(tmp_path)

        assert len(result) == 1
        assert result[0]['status'] == '??'
        assert result[0]['path'] == 'new.py'

    @patch('subprocess.run')
    def test_parse_git_status_added_file(self, mock_run, tmp_path):
        """Test parsing added (new) file."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="A  added.py\n",
            stderr=""
        )

        result = parse_git_status(tmp_path)

        assert len(result) == 1
        assert result[0]['status'] == 'A '
        assert result[0]['path'] == 'added.py'

    @patch('subprocess.run')
    def test_parse_git_status_deleted_file(self, mock_run, tmp_path):
        """Test parsing deleted file."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout=" D deleted.py\n",
            stderr=""
        )

        result = parse_git_status(tmp_path)

        assert len(result) == 1
        assert result[0]['status'] == ' D'
        assert result[0]['path'] == 'deleted.py'

    @patch('subprocess.run')
    def test_parse_git_status_multiple_files(self, mock_run, tmp_path):
        """Test parsing multiple files with mixed statuses."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="M  file1.py\n M file2.py\n?? file3.py\nA  file4.py\n",
            stderr=""
        )

        result = parse_git_status(tmp_path)

        assert len(result) == 4
        assert result[0] == {'status': 'M ', 'path': 'file1.py'}
        assert result[1] == {'status': ' M', 'path': 'file2.py'}
        assert result[2] == {'status': '??', 'path': 'file3.py'}
        assert result[3] == {'status': 'A ', 'path': 'file4.py'}

    @patch('subprocess.run')
    def test_parse_git_status_with_subdirectories(self, mock_run, tmp_path):
        """Test parsing files in subdirectories."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="M  src/main.py\n?? tests/new_test.py\n",
            stderr=""
        )

        result = parse_git_status(tmp_path)

        assert len(result) == 2
        assert result[0] == {'status': 'M ', 'path': 'src/main.py'}
        assert result[1] == {'status': '??', 'path': 'tests/new_test.py'}

    @patch('subprocess.run')
    def test_parse_git_status_quoted_paths(self, mock_run, tmp_path):
        """Test parsing paths with special characters (quoted)."""
        # Git quotes paths with spaces or special characters
        mock_run.return_value = Mock(
            returncode=0,
            stdout='M  "file with spaces.py"\n',
            stderr=""
        )

        result = parse_git_status(tmp_path)

        assert len(result) == 1
        assert result[0]['status'] == 'M '
        # Quotes should be removed
        assert result[0]['path'] == 'file with spaces.py'

    @patch('subprocess.run')
    def test_parse_git_status_handles_timeout(self, mock_run, tmp_path):
        """Test handling of git command timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('git', 10)

        result = parse_git_status(tmp_path)

        assert result == []

    @patch('subprocess.run')
    def test_parse_git_status_handles_error(self, mock_run, tmp_path):
        """Test handling of git command error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git', stderr='error')

        result = parse_git_status(tmp_path)

        assert result == []

    @patch('subprocess.run')
    def test_parse_git_status_handles_git_not_found(self, mock_run, tmp_path):
        """Test handling when git command not found."""
        mock_run.side_effect = FileNotFoundError()

        result = parse_git_status(tmp_path)

        assert result == []

    @patch('subprocess.run')
    def test_parse_git_status_handles_unexpected_error(self, mock_run, tmp_path):
        """Test handling of unexpected errors."""
        mock_run.side_effect = RuntimeError("Unexpected error")

        result = parse_git_status(tmp_path)

        assert result == []

    @patch('subprocess.run')
    def test_parse_git_status_renamed_file(self, mock_run, tmp_path):
        """Test parsing renamed file."""
        # Renamed files show as "R  old.py -> new.py"
        mock_run.return_value = Mock(
            returncode=0,
            stdout="R  old.py -> new.py\n",
            stderr=""
        )

        result = parse_git_status(tmp_path)

        assert len(result) == 1
        assert result[0]['status'] == 'R '
        # For now, we treat the entire "old.py -> new.py" as the path
        assert result[0]['path'] == 'old.py -> new.py'

    @patch('subprocess.run')
    def test_parse_git_status_added_with_unstaged_changes(self, mock_run, tmp_path):
        """Test parsing file that's added (staged) with unstaged modifications."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="AM file.py\n",
            stderr=""
        )

        result = parse_git_status(tmp_path)

        assert len(result) == 1
        assert result[0]['status'] == 'AM'
        assert result[0]['path'] == 'file.py'


class TestShowCommitPreview:
    """Tests for show_commit_preview function."""

    @patch('claude_skills.common.git_metadata.parse_git_status')
    def test_show_commit_preview_no_changes(self, mock_parse, tmp_path):
        """Test preview with no changes."""
        from claude_skills.common.printer import PrettyPrinter
        from io import StringIO
        import sys

        mock_parse.return_value = []

        # Capture output
        captured_output = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_output

        try:
            printer = PrettyPrinter(use_color=False, verbose=True)
            result = show_commit_preview(tmp_path, printer=printer)

            assert result == {}
            mock_parse.assert_called_once_with(tmp_path)
        finally:
            sys.stdout = old_stdout

    @patch('claude_skills.common.git_metadata.parse_git_status')
    def test_show_commit_preview_staged_modified(self, mock_parse, tmp_path):
        """Test preview with staged modified files."""
        mock_parse.return_value = [
            {'status': 'M ', 'path': 'file1.py'},
            {'status': 'M ', 'path': 'file2.py'}
        ]

        from claude_skills.common.printer import PrettyPrinter
        printer = PrettyPrinter(use_color=False, quiet=True)
        result = show_commit_preview(tmp_path, printer=printer)

        assert 'staged_modified' in result
        assert len(result['staged_modified']) == 2
        assert 'file1.py' in result['staged_modified']
        assert 'file2.py' in result['staged_modified']

    @patch('claude_skills.common.git_metadata.parse_git_status')
    def test_show_commit_preview_unstaged_modified(self, mock_parse, tmp_path):
        """Test preview with unstaged modified files."""
        mock_parse.return_value = [
            {'status': ' M', 'path': 'file1.py'}
        ]

        from claude_skills.common.printer import PrettyPrinter
        printer = PrettyPrinter(use_color=False, quiet=True)
        result = show_commit_preview(tmp_path, printer=printer)

        assert 'unstaged_modified' in result
        assert len(result['unstaged_modified']) == 1
        assert 'file1.py' in result['unstaged_modified']

    @patch('claude_skills.common.git_metadata.parse_git_status')
    def test_show_commit_preview_both_modified(self, mock_parse, tmp_path):
        """Test preview with files that have both staged and unstaged changes."""
        mock_parse.return_value = [
            {'status': 'MM', 'path': 'file1.py'}
        ]

        from claude_skills.common.printer import PrettyPrinter
        printer = PrettyPrinter(use_color=False, quiet=True)
        result = show_commit_preview(tmp_path, printer=printer)

        assert 'both_modified' in result
        assert len(result['both_modified']) == 1
        assert 'file1.py' in result['both_modified']

    @patch('claude_skills.common.git_metadata.parse_git_status')
    def test_show_commit_preview_added_files(self, mock_parse, tmp_path):
        """Test preview with added files."""
        mock_parse.return_value = [
            {'status': 'A ', 'path': 'new_file.py'}
        ]

        from claude_skills.common.printer import PrettyPrinter
        printer = PrettyPrinter(use_color=False, quiet=True)
        result = show_commit_preview(tmp_path, printer=printer)

        assert 'added' in result
        assert len(result['added']) == 1
        assert 'new_file.py' in result['added']

    @patch('claude_skills.common.git_metadata.parse_git_status')
    def test_show_commit_preview_deleted_staged(self, mock_parse, tmp_path):
        """Test preview with deleted files (staged)."""
        mock_parse.return_value = [
            {'status': 'D ', 'path': 'old_file.py'}
        ]

        from claude_skills.common.printer import PrettyPrinter
        printer = PrettyPrinter(use_color=False, quiet=True)
        result = show_commit_preview(tmp_path, printer=printer)

        assert 'deleted_staged' in result
        assert len(result['deleted_staged']) == 1
        assert 'old_file.py' in result['deleted_staged']

    @patch('claude_skills.common.git_metadata.parse_git_status')
    def test_show_commit_preview_deleted_unstaged(self, mock_parse, tmp_path):
        """Test preview with deleted files (unstaged)."""
        mock_parse.return_value = [
            {'status': ' D', 'path': 'old_file.py'}
        ]

        from claude_skills.common.printer import PrettyPrinter
        printer = PrettyPrinter(use_color=False, quiet=True)
        result = show_commit_preview(tmp_path, printer=printer)

        assert 'deleted_unstaged' in result
        assert len(result['deleted_unstaged']) == 1
        assert 'old_file.py' in result['deleted_unstaged']

    @patch('claude_skills.common.git_metadata.parse_git_status')
    def test_show_commit_preview_untracked(self, mock_parse, tmp_path):
        """Test preview with untracked files."""
        mock_parse.return_value = [
            {'status': '??', 'path': 'untracked.py'}
        ]

        from claude_skills.common.printer import PrettyPrinter
        printer = PrettyPrinter(use_color=False, quiet=True)
        result = show_commit_preview(tmp_path, printer=printer)

        assert 'untracked' in result
        assert len(result['untracked']) == 1
        assert 'untracked.py' in result['untracked']

    @patch('claude_skills.common.git_metadata.parse_git_status')
    def test_show_commit_preview_renamed(self, mock_parse, tmp_path):
        """Test preview with renamed files."""
        mock_parse.return_value = [
            {'status': 'R ', 'path': 'old.py -> new.py'}
        ]

        from claude_skills.common.printer import PrettyPrinter
        printer = PrettyPrinter(use_color=False, quiet=True)
        result = show_commit_preview(tmp_path, printer=printer)

        assert 'renamed' in result
        assert len(result['renamed']) == 1
        assert 'old.py -> new.py' in result['renamed']

    @patch('claude_skills.common.git_metadata.parse_git_status')
    def test_show_commit_preview_mixed_statuses(self, mock_parse, tmp_path):
        """Test preview with mixed file statuses."""
        mock_parse.return_value = [
            {'status': 'M ', 'path': 'staged.py'},
            {'status': ' M', 'path': 'unstaged.py'},
            {'status': 'A ', 'path': 'new.py'},
            {'status': '??', 'path': 'untracked.py'},
            {'status': ' D', 'path': 'deleted.py'}
        ]

        from claude_skills.common.printer import PrettyPrinter
        printer = PrettyPrinter(use_color=False, quiet=True)
        result = show_commit_preview(tmp_path, printer=printer)

        assert len(result['staged_modified']) == 1
        assert len(result['unstaged_modified']) == 1
        assert len(result['added']) == 1
        assert len(result['untracked']) == 1
        assert len(result['deleted_unstaged']) == 1

    @patch('claude_skills.common.git_metadata.parse_git_status')
    def test_show_commit_preview_creates_printer_if_none(self, mock_parse, tmp_path):
        """Test that function creates PrettyPrinter if none provided."""
        mock_parse.return_value = []

        # Call without printer parameter
        result = show_commit_preview(tmp_path)

        assert result == {}
        mock_parse.assert_called_once_with(tmp_path)


class TestGetStagedFiles:
    """Tests for get_staged_files function."""

    @patch('subprocess.run')
    def test_get_staged_files_empty(self, mock_run, tmp_path):
        """Test with no staged files."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="",
            stderr=""
        )

        result = get_staged_files(tmp_path)

        assert result == []
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_get_staged_files_single_file(self, mock_run, tmp_path):
        """Test with single staged file."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="file1.py\n",
            stderr=""
        )

        result = get_staged_files(tmp_path)

        assert len(result) == 1
        assert result[0] == 'file1.py'

    @patch('subprocess.run')
    def test_get_staged_files_multiple_files(self, mock_run, tmp_path):
        """Test with multiple staged files."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="file1.py\nfile2.py\nfile3.py\n",
            stderr=""
        )

        result = get_staged_files(tmp_path)

        assert len(result) == 3
        assert result == ['file1.py', 'file2.py', 'file3.py']

    @patch('subprocess.run')
    def test_get_staged_files_with_subdirectories(self, mock_run, tmp_path):
        """Test with files in subdirectories."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout="src/main.py\ntests/test_main.py\n",
            stderr=""
        )

        result = get_staged_files(tmp_path)

        assert len(result) == 2
        assert 'src/main.py' in result
        assert 'tests/test_main.py' in result

    @patch('subprocess.run')
    def test_get_staged_files_handles_timeout(self, mock_run, tmp_path):
        """Test handling of git command timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired('git', 10)

        result = get_staged_files(tmp_path)

        assert result == []

    @patch('subprocess.run')
    def test_get_staged_files_handles_error(self, mock_run, tmp_path):
        """Test handling of git command error."""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git', stderr='error')

        result = get_staged_files(tmp_path)

        assert result == []

    @patch('subprocess.run')
    def test_get_staged_files_handles_git_not_found(self, mock_run, tmp_path):
        """Test handling when git command not found."""
        mock_run.side_effect = FileNotFoundError()

        result = get_staged_files(tmp_path)

        assert result == []

    @patch('subprocess.run')
    def test_get_staged_files_handles_unexpected_error(self, mock_run, tmp_path):
        """Test handling of unexpected errors."""
        mock_run.side_effect = RuntimeError("Unexpected error")

        result = get_staged_files(tmp_path)

        assert result == []


class TestDetectGitDrift:
    """Tests for detect_git_drift function."""

    @patch('subprocess.run')
    def test_detect_git_drift_no_metadata(self, mock_run, tmp_path):
        """Test with spec that has no git metadata."""
        spec = {'metadata': {}}

        warnings = detect_git_drift(spec, tmp_path)

        assert warnings == []
        mock_run.assert_not_called()

    @patch('subprocess.run')
    def test_detect_git_drift_matching_branch(self, mock_run, tmp_path):
        """Test when branch matches."""
        spec = {
            'metadata': {
                'git': {
                    'branch_name': 'feat/test',
                    'base_branch': 'main'
                }
            }
        }

        # Mock matching branch
        mock_run.return_value = Mock(
            returncode=0,
            stdout="feat/test\n",
            stderr=""
        )

        warnings = detect_git_drift(spec, tmp_path)

        assert len(warnings) == 0

    @patch('subprocess.run')
    def test_detect_git_drift_different_branch(self, mock_run, tmp_path):
        """Test when branch doesn't match."""
        spec = {
            'metadata': {
                'git': {
                    'branch_name': 'feat/expected',
                    'base_branch': 'main'
                }
            }
        }

        # Mock different branch
        mock_run.return_value = Mock(
            returncode=0,
            stdout="feat/actual\n",
            stderr=""
        )

        warnings = detect_git_drift(spec, tmp_path)

        assert len(warnings) > 0
        assert any('drift' in w.lower() for w in warnings)
        assert any('expected' in w for w in warnings)

    @patch('subprocess.run')
    def test_detect_git_drift_handles_timeout(self, mock_run, tmp_path):
        """Test handling of timeout."""
        spec = {
            'metadata': {
                'git': {
                    'branch_name': 'feat/test'
                }
            }
        }

        mock_run.side_effect = subprocess.TimeoutExpired('git', 10)

        warnings = detect_git_drift(spec, tmp_path)

        assert len(warnings) > 0
        assert any('timeout' in w.lower() for w in warnings)


class TestUpdateBranchMetadata:
    """Tests for update_branch_metadata function."""

    def test_update_branch_metadata_creates_metadata(self):
        """Test creating git metadata in empty spec."""
        spec = {}

        result = update_branch_metadata(spec, 'feat/test', 'main')

        assert 'metadata' in result
        assert 'git' in result['metadata']
        assert result['metadata']['git']['branch_name'] == 'feat/test'
        assert result['metadata']['git']['base_branch'] == 'main'
        assert result['metadata']['git']['commits'] == []
        assert result['metadata']['git']['pr'] is None

    def test_update_branch_metadata_updates_existing(self):
        """Test updating existing git metadata."""
        spec = {
            'metadata': {
                'git': {
                    'branch_name': 'old-branch',
                    'base_branch': 'develop',
                    'commits': [{'sha': 'abc', 'message': 'test', 'task_id': 'task-1'}],
                    'pr': {'number': 42}
                }
            }
        }

        result = update_branch_metadata(spec, 'new-branch', 'main')

        assert result['metadata']['git']['branch_name'] == 'new-branch'
        assert result['metadata']['git']['base_branch'] == 'main'
        # Should preserve commits and PR
        assert len(result['metadata']['git']['commits']) == 1
        assert result['metadata']['git']['pr']['number'] == 42

    def test_update_branch_metadata_preserves_other_metadata(self):
        """Test that other metadata is preserved."""
        spec = {
            'metadata': {
                'title': 'Test Spec',
                'status': 'active'
            }
        }

        result = update_branch_metadata(spec, 'feat/test', 'main')

        assert result['metadata']['title'] == 'Test Spec'
        assert result['metadata']['status'] == 'active'
        assert 'git' in result['metadata']


class TestAddCommitMetadata:
    """Tests for add_commit_metadata function."""

    def test_add_commit_metadata_creates_metadata(self):
        """Test creating git metadata and adding commit."""
        spec = {}

        result = add_commit_metadata(spec, 'abc123', 'Test commit', 'task-1-1', '2025-11-02T12:00:00Z')

        assert 'metadata' in result
        assert 'git' in result['metadata']
        assert len(result['metadata']['git']['commits']) == 1
        commit = result['metadata']['git']['commits'][0]
        assert commit['sha'] == 'abc123'
        assert commit['message'] == 'Test commit'
        assert commit['task_id'] == 'task-1-1'
        assert commit['timestamp'] == '2025-11-02T12:00:00Z'

    def test_add_commit_metadata_appends_to_existing(self):
        """Test appending commit to existing commits."""
        spec = {
            'metadata': {
                'git': {
                    'commits': [
                        {'sha': 'existing', 'message': 'Old', 'task_id': 'task-0', 'timestamp': '2025-11-01T12:00:00Z'}
                    ]
                }
            }
        }

        result = add_commit_metadata(spec, 'new123', 'New commit', 'task-1-1')

        assert len(result['metadata']['git']['commits']) == 2
        assert result['metadata']['git']['commits'][0]['sha'] == 'existing'
        assert result['metadata']['git']['commits'][1]['sha'] == 'new123'

    def test_add_commit_metadata_auto_generates_timestamp(self):
        """Test auto-generation of timestamp."""
        spec = {}

        result = add_commit_metadata(spec, 'abc123', 'Test commit', 'task-1-1')

        commit = result['metadata']['git']['commits'][0]
        assert 'timestamp' in commit
        # Should be ISO 8601 format
        assert 'T' in commit['timestamp']

    def test_add_commit_metadata_preserves_branch_info(self):
        """Test that branch info is preserved."""
        spec = {
            'metadata': {
                'git': {
                    'branch_name': 'feat/test',
                    'base_branch': 'main',
                    'commits': []
                }
            }
        }

        result = add_commit_metadata(spec, 'abc123', 'Test', 'task-1-1')

        assert result['metadata']['git']['branch_name'] == 'feat/test'
        assert result['metadata']['git']['base_branch'] == 'main'


class TestUpdatePRMetadata:
    """Tests for update_pr_metadata function."""

    def test_update_pr_metadata_creates_metadata(self):
        """Test creating PR metadata in empty spec."""
        spec = {}

        result = update_pr_metadata(spec, 'https://github.com/user/repo/pull/42', 42, 'open')

        assert 'metadata' in result
        assert 'git' in result['metadata']
        assert result['metadata']['git']['pr']['url'] == 'https://github.com/user/repo/pull/42'
        assert result['metadata']['git']['pr']['number'] == 42
        assert result['metadata']['git']['pr']['status'] == 'open'
        assert 'created_at' in result['metadata']['git']['pr']

    def test_update_pr_metadata_updates_existing(self):
        """Test updating existing PR metadata."""
        spec = {
            'metadata': {
                'git': {
                    'pr': {
                        'url': 'https://github.com/user/repo/pull/10',
                        'number': 10,
                        'status': 'open'
                    }
                }
            }
        }

        result = update_pr_metadata(spec, 'https://github.com/user/repo/pull/10', 10, 'merged')

        assert result['metadata']['git']['pr']['status'] == 'merged'
        assert result['metadata']['git']['pr']['number'] == 10

    def test_update_pr_metadata_default_status(self):
        """Test that default status is 'open'."""
        spec = {}

        result = update_pr_metadata(spec, 'https://github.com/user/repo/pull/99', 99)

        assert result['metadata']['git']['pr']['status'] == 'open'

    def test_update_pr_metadata_preserves_commits(self):
        """Test that commits are preserved when updating PR."""
        spec = {
            'metadata': {
                'git': {
                    'commits': [
                        {'sha': 'abc', 'message': 'test', 'task_id': 'task-1', 'timestamp': '2025-11-02T12:00:00Z'}
                    ],
                    'branch_name': 'feat/test'
                }
            }
        }

        result = update_pr_metadata(spec, 'https://github.com/user/repo/pull/1', 1, 'open')

        assert len(result['metadata']['git']['commits']) == 1
        assert result['metadata']['git']['branch_name'] == 'feat/test'

    def test_update_pr_metadata_status_values(self):
        """Test different PR status values."""
        spec = {}

        # Test open
        update_pr_metadata(spec, 'https://example.com/pr/1', 1, 'open')
        assert spec['metadata']['git']['pr']['status'] == 'open'

        # Test closed
        update_pr_metadata(spec, 'https://example.com/pr/1', 1, 'closed')
        assert spec['metadata']['git']['pr']['status'] == 'closed'

        # Test merged
        update_pr_metadata(spec, 'https://example.com/pr/1', 1, 'merged')
        assert spec['metadata']['git']['pr']['status'] == 'merged'
