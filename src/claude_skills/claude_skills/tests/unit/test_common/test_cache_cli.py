from __future__ import annotations

"""Unit tests for cache CLI behaviour."""

import json
from unittest.mock import Mock, patch

import pytest

from claude_skills.common.cache.cli import handle_cache_clear, handle_cache_info


pytestmark = pytest.mark.unit


def _make_args(**overrides):
    defaults = dict(
        json=False,
        compact=False,
        debug=False,
        spec_id=None,
        review_type=None,
    )
    defaults.update(overrides)
    return Mock(**defaults)


def test_cache_info_json_output():
    args = _make_args(json=True, compact=False)
    printer = Mock()
    stats = {
        "cache_dir": "/tmp/cache",
        "total_entries": 10,
        "expired_entries": 2,
        "active_entries": 8,
        "total_size_bytes": 1024,
        "total_size_mb": 0.001,
    }

    with patch("claude_skills.common.cache.cli.is_cache_enabled", return_value=True), patch(
        "claude_skills.common.cache.cli.CacheManager"
    ) as MockCache, patch("claude_skills.common.cache.cli.output_json") as mock_output:
        MockCache.return_value.get_stats.return_value = stats
        exit_code = handle_cache_info(args, printer)
        assert exit_code == 0
        mock_output.assert_called_once_with(stats, False)


def test_cache_info_human_readable_output():
    args = _make_args(json=False)
    printer = Mock()
    stats = {
        "cache_dir": "/tmp/cache",
        "total_entries": 10,
        "expired_entries": 0,
        "active_entries": 10,
        "total_size_bytes": 2048,
        "total_size_mb": 0.002,
    }

    with patch("claude_skills.common.cache.cli.is_cache_enabled", return_value=True), patch(
        "claude_skills.common.cache.cli.CacheManager"
    ) as MockCache, patch("claude_skills.common.cache.cli.Path") as MockPath:
        MockCache.return_value.get_stats.return_value = stats
        path_instance = MockPath.return_value
        path_instance.exists.return_value = True
        path_instance.is_dir.return_value = True

        exit_code = handle_cache_info(args, printer)

        assert exit_code == 0
        printer.header.assert_called()
        printer.result.assert_any_call("Location", stats["cache_dir"])
        printer.success.assert_called_with("Cache directory is accessible")


def test_cache_info_cache_disabled_json():
    args = _make_args(json=True, compact=True)
    printer = Mock()
    with patch("claude_skills.common.cache.cli.is_cache_enabled", return_value=False), patch(
        "claude_skills.common.cache.cli.output_json"
    ) as mock_output:
        exit_code = handle_cache_info(args, printer)
        assert exit_code == 1
        mock_output.assert_called_once()


def test_cache_info_cache_disabled_human():
    args = _make_args(json=False)
    printer = Mock()
    with patch("claude_skills.common.cache.cli.is_cache_enabled", return_value=False):
        exit_code = handle_cache_info(args, printer)
        assert exit_code == 1
        printer.warning.assert_called_once()


def test_cache_info_error_handling():
    args = _make_args(json=False)
    printer = Mock()
    with patch("claude_skills.common.cache.cli.is_cache_enabled", return_value=True), patch(
        "claude_skills.common.cache.cli.CacheManager"
    ) as MockCache:
        MockCache.return_value.get_stats.side_effect = Exception("Disk error")
        exit_code = handle_cache_info(args, printer)
        assert exit_code == 1
        printer.error.assert_called()


def test_cache_info_with_expired_entries():
    args = _make_args(json=False)
    printer = Mock()
    stats = {
        "cache_dir": "/tmp/cache",
        "total_entries": 10,
        "expired_entries": 3,
        "active_entries": 7,
        "total_size_bytes": 1024,
        "total_size_mb": 0.001,
    }

    with patch("claude_skills.common.cache.cli.is_cache_enabled", return_value=True), patch(
        "claude_skills.common.cache.cli.CacheManager"
    ) as MockCache, patch("claude_skills.common.cache.cli.Path") as MockPath:
        MockCache.return_value.get_stats.return_value = stats
        path_instance = MockPath.return_value
        path_instance.exists.return_value = True
        path_instance.is_dir.return_value = True

        exit_code = handle_cache_info(args, printer)
        assert exit_code == 0
        printer.action.assert_called_with("Run 'sdd cache cleanup' to remove expired entries")


def test_cache_clear_all_entries():
    args = _make_args()
    printer = Mock()

    with patch("claude_skills.common.cache.cli.is_cache_enabled", return_value=True), patch(
        "claude_skills.common.cache.cli.CacheManager"
    ) as MockCache:
        MockCache.return_value.clear.return_value = 5
        exit_code = handle_cache_clear(args, printer)
        assert exit_code == 0
        MockCache.return_value.clear.assert_called_once_with(spec_id=None, review_type=None)
        printer.success.assert_called_once()


def test_cache_clear_with_filters():
    args = _make_args(spec_id="spec-123", review_type="fidelity")
    printer = Mock()

    with patch("claude_skills.common.cache.cli.is_cache_enabled", return_value=True), patch(
        "claude_skills.common.cache.cli.CacheManager"
    ) as MockCache:
        MockCache.return_value.clear.return_value = 2
        exit_code = handle_cache_clear(args, printer)
        assert exit_code == 0
        MockCache.return_value.clear.assert_called_once_with(spec_id="spec-123", review_type="fidelity")
        printer.success.assert_called_once()


def test_cache_clear_json_output():
    args = _make_args(json=True, compact=True)
    printer = Mock()

    with patch("claude_skills.common.cache.cli.is_cache_enabled", return_value=True), patch(
        "claude_skills.common.cache.cli.CacheManager"
    ) as MockCache, patch("claude_skills.common.cache.cli.output_json") as mock_output:
        MockCache.return_value.clear.return_value = 3
        exit_code = handle_cache_clear(args, printer)
        assert exit_code == 0
        mock_output.assert_called_once()
        payload = mock_output.call_args.args[0]
        assert payload["entries_deleted"] == 3


def test_cache_clear_disabled() -> None:
    args = _make_args(json=False)
    printer = Mock()
    with patch("claude_skills.common.cache.cli.is_cache_enabled", return_value=False):
        exit_code = handle_cache_clear(args, printer)
        assert exit_code == 1
        printer.warning.assert_called_once()
