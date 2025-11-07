"""
Unit tests for cache CLI commands.
"""

import json
from unittest.mock import Mock, patch
import pytest

from claude_skills.common.cache.cli import handle_cache_info


def test_cache_info_json_output():
    """handle_cache_info should output JSON when args.json is True."""
    # Setup mocks
    mock_args = Mock()
    mock_args.json = True
    mock_args.debug = False

    mock_printer = Mock()

    mock_stats = {
        "cache_dir": "/test/cache",
        "total_entries": 10,
        "expired_entries": 2,
        "active_entries": 8,
        "total_size_bytes": 1024,
        "total_size_mb": 0.001
    }

    with patch('claude_skills.common.cache.cli.is_cache_enabled', return_value=True):
        with patch('claude_skills.common.cache.cli.CacheManager') as MockCache:
            mock_cache_instance = MockCache.return_value
            mock_cache_instance.get_stats.return_value = mock_stats

            with patch('builtins.print') as mock_print:
                exit_code = handle_cache_info(mock_args, mock_printer)

                # Verify JSON output
                assert exit_code == 0
                mock_print.assert_called_once()
                output_str = mock_print.call_args[0][0]
                output = json.loads(output_str)
                assert output['total_entries'] == 10
                assert output['active_entries'] == 8


def test_cache_info_human_readable_output():
    """handle_cache_info should output human-readable format when args.json is False."""
    # Setup mocks
    mock_args = Mock()
    mock_args.json = False
    mock_args.debug = False

    mock_printer = Mock()

    mock_stats = {
        "cache_dir": "/test/cache",
        "total_entries": 10,
        "expired_entries": 0,
        "active_entries": 10,
        "total_size_bytes": 2048,
        "total_size_mb": 0.002
    }

    with patch('claude_skills.common.cache.cli.is_cache_enabled', return_value=True):
        with patch('claude_skills.common.cache.cli.CacheManager') as MockCache:
            with patch('claude_skills.common.cache.cli.Path') as MockPath:
                mock_cache_instance = MockCache.return_value
                mock_cache_instance.get_stats.return_value = mock_stats

                # Mock Path to simulate cache directory exists
                mock_path_instance = MockPath.return_value
                mock_path_instance.exists.return_value = True
                mock_path_instance.is_dir.return_value = True

                exit_code = handle_cache_info(mock_args, mock_printer)

                # Verify human-readable output
                assert exit_code == 0
                mock_printer.header.assert_called()
                mock_printer.result.assert_called()
                mock_printer.success.assert_called_with("Cache directory is accessible")


def test_cache_info_cache_disabled():
    """handle_cache_info should warn when cache is disabled."""
    # Setup mocks
    mock_args = Mock()
    mock_args.json = False
    mock_args.debug = False

    mock_printer = Mock()

    with patch('claude_skills.common.cache.cli.is_cache_enabled', return_value=False):
        exit_code = handle_cache_info(mock_args, mock_printer)

        # Verify warning message
        assert exit_code == 1
        mock_printer.warning.assert_called_once()
        assert "disabled" in str(mock_printer.warning.call_args)


def test_cache_info_error_handling():
    """handle_cache_info should handle errors gracefully."""
    # Setup mocks
    mock_args = Mock()
    mock_args.json = False
    mock_args.debug = False

    mock_printer = Mock()

    with patch('claude_skills.common.cache.cli.is_cache_enabled', return_value=True):
        with patch('claude_skills.common.cache.cli.CacheManager') as MockCache:
            mock_cache_instance = MockCache.return_value
            mock_cache_instance.get_stats.side_effect = Exception("Disk error")

            exit_code = handle_cache_info(mock_args, mock_printer)

            # Verify error handling
            assert exit_code == 1
            mock_printer.error.assert_called_once()
            assert "Error getting cache info" in str(mock_printer.error.call_args)


def test_cache_info_with_expired_entries():
    """handle_cache_info should suggest cleanup when expired entries exist."""
    # Setup mocks
    mock_args = Mock()
    mock_args.json = False
    mock_args.debug = False

    mock_printer = Mock()

    mock_stats = {
        "cache_dir": "/test/cache",
        "total_entries": 10,
        "expired_entries": 3,
        "active_entries": 7,
        "total_size_bytes": 1024,
        "total_size_mb": 0.001
    }

    with patch('claude_skills.common.cache.cli.is_cache_enabled', return_value=True):
        with patch('claude_skills.common.cache.cli.CacheManager') as MockCache:
            with patch('claude_skills.common.cache.cli.Path') as MockPath:
                mock_cache_instance = MockCache.return_value
                mock_cache_instance.get_stats.return_value = mock_stats

                # Mock Path to simulate cache directory exists
                mock_path_instance = MockPath.return_value
                mock_path_instance.exists.return_value = True
                mock_path_instance.is_dir.return_value = True

                exit_code = handle_cache_info(mock_args, mock_printer)

                # Verify cleanup suggestion
                assert exit_code == 0
                # Check that action() was called with cleanup message
                action_calls = [call for call in mock_printer.action.call_args_list]
                assert any("cleanup" in str(call) for call in action_calls)


# Tests for cache clear command

def test_cache_clear_all_entries():
    """handle_cache_clear should clear all entries when no filters specified."""
    from claude_skills.common.cache.cli import handle_cache_clear

    mock_args = Mock()
    mock_args.spec_id = None
    mock_args.review_type = None
    mock_args.json = False
    mock_args.debug = False

    mock_printer = Mock()

    with patch('claude_skills.common.cache.cli.is_cache_enabled', return_value=True):
        with patch('claude_skills.common.cache.cli.CacheManager') as MockCache:
            mock_cache_instance = MockCache.return_value
            mock_cache_instance.clear.return_value = 5

            exit_code = handle_cache_clear(mock_args, mock_printer)

            # Verify clear was called without filters
            assert exit_code == 0
            mock_cache_instance.clear.assert_called_once_with(spec_id=None, review_type=None)
            mock_printer.success.assert_called_once()
            assert "5" in str(mock_printer.success.call_args)


def test_cache_clear_with_spec_filter():
    """handle_cache_clear should clear only entries matching spec_id filter."""
    from claude_skills.common.cache.cli import handle_cache_clear

    mock_args = Mock()
    mock_args.spec_id = "my-spec-001"
    mock_args.review_type = None
    mock_args.json = False
    mock_args.debug = False

    mock_printer = Mock()

    with patch('claude_skills.common.cache.cli.is_cache_enabled', return_value=True):
        with patch('claude_skills.common.cache.cli.CacheManager') as MockCache:
            mock_cache_instance = MockCache.return_value
            mock_cache_instance.clear.return_value = 3

            exit_code = handle_cache_clear(mock_args, mock_printer)

            # Verify clear was called with spec_id filter
            assert exit_code == 0
            mock_cache_instance.clear.assert_called_once_with(spec_id="my-spec-001", review_type=None)
            mock_printer.success.assert_called_once()
            mock_printer.result.assert_called()


def test_cache_clear_with_type_filter():
    """handle_cache_clear should clear only entries matching review_type filter."""
    from claude_skills.common.cache.cli import handle_cache_clear

    mock_args = Mock()
    mock_args.spec_id = None
    mock_args.review_type = "fidelity"
    mock_args.json = False
    mock_args.debug = False

    mock_printer = Mock()

    with patch('claude_skills.common.cache.cli.is_cache_enabled', return_value=True):
        with patch('claude_skills.common.cache.cli.CacheManager') as MockCache:
            mock_cache_instance = MockCache.return_value
            mock_cache_instance.clear.return_value = 2

            exit_code = handle_cache_clear(mock_args, mock_printer)

            # Verify clear was called with review_type filter
            assert exit_code == 0
            mock_cache_instance.clear.assert_called_once_with(spec_id=None, review_type="fidelity")
            mock_printer.success.assert_called_once()


def test_cache_clear_with_both_filters():
    """handle_cache_clear should clear only entries matching both filters."""
    from claude_skills.common.cache.cli import handle_cache_clear

    mock_args = Mock()
    mock_args.spec_id = "my-spec-001"
    mock_args.review_type = "plan"
    mock_args.json = False
    mock_args.debug = False

    mock_printer = Mock()

    with patch('claude_skills.common.cache.cli.is_cache_enabled', return_value=True):
        with patch('claude_skills.common.cache.cli.CacheManager') as MockCache:
            mock_cache_instance = MockCache.return_value
            mock_cache_instance.clear.return_value = 1

            exit_code = handle_cache_clear(mock_args, mock_printer)

            # Verify clear was called with both filters
            assert exit_code == 0
            mock_cache_instance.clear.assert_called_once_with(spec_id="my-spec-001", review_type="plan")
            mock_printer.success.assert_called_once()


def test_cache_clear_no_matches():
    """handle_cache_clear should warn when no entries match filters."""
    from claude_skills.common.cache.cli import handle_cache_clear

    mock_args = Mock()
    mock_args.spec_id = "nonexistent-spec"
    mock_args.review_type = None
    mock_args.json = False
    mock_args.debug = False

    mock_printer = Mock()

    with patch('claude_skills.common.cache.cli.is_cache_enabled', return_value=True):
        with patch('claude_skills.common.cache.cli.CacheManager') as MockCache:
            mock_cache_instance = MockCache.return_value
            mock_cache_instance.clear.return_value = 0

            exit_code = handle_cache_clear(mock_args, mock_printer)

            # Verify warning for no matches
            assert exit_code == 0
            mock_printer.warning.assert_called_once()
            assert "No cache entries" in str(mock_printer.warning.call_args)


def test_cache_clear_json_output():
    """handle_cache_clear should output JSON when args.json is True."""
    from claude_skills.common.cache.cli import handle_cache_clear

    mock_args = Mock()
    mock_args.spec_id = "my-spec-001"
    mock_args.review_type = "fidelity"
    mock_args.json = True
    mock_args.debug = False

    mock_printer = Mock()

    with patch('claude_skills.common.cache.cli.is_cache_enabled', return_value=True):
        with patch('claude_skills.common.cache.cli.CacheManager') as MockCache:
            mock_cache_instance = MockCache.return_value
            mock_cache_instance.clear.return_value = 3

            with patch('builtins.print') as mock_print:
                exit_code = handle_cache_clear(mock_args, mock_printer)

                # Verify JSON output
                assert exit_code == 0
                mock_print.assert_called_once()
                output_str = mock_print.call_args[0][0]
                output = json.loads(output_str)
                assert output['entries_deleted'] == 3
                assert output['filters']['spec_id'] == "my-spec-001"
                assert output['filters']['review_type'] == "fidelity"


def test_cache_clear_disabled():
    """handle_cache_clear should warn when cache is disabled."""
    from claude_skills.common.cache.cli import handle_cache_clear

    mock_args = Mock()
    mock_args.spec_id = None
    mock_args.review_type = None
    mock_args.json = False
    mock_args.debug = False

    mock_printer = Mock()

    with patch('claude_skills.common.cache.cli.is_cache_enabled', return_value=False):
        exit_code = handle_cache_clear(mock_args, mock_printer)

        # Verify warning and exit code
        assert exit_code == 1
        mock_printer.warning.assert_called_once()
        assert "disabled" in str(mock_printer.warning.call_args)


def test_cache_clear_error_handling():
    """handle_cache_clear should handle errors gracefully."""
    from claude_skills.common.cache.cli import handle_cache_clear

    mock_args = Mock()
    mock_args.spec_id = None
    mock_args.review_type = None
    mock_args.json = False
    mock_args.debug = False

    mock_printer = Mock()

    with patch('claude_skills.common.cache.cli.is_cache_enabled', return_value=True):
        with patch('claude_skills.common.cache.cli.CacheManager') as MockCache:
            mock_cache_instance = MockCache.return_value
            mock_cache_instance.clear.side_effect = Exception("Disk error")

            exit_code = handle_cache_clear(mock_args, mock_printer)

            # Verify error handling
            assert exit_code == 1
            mock_printer.error.assert_called_once()
            assert "Error clearing cache" in str(mock_printer.error.call_args)
