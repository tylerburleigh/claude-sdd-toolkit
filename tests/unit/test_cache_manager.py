"""
Unit tests for CacheManager.
"""

import json
import time
import pytest
from pathlib import Path
from claude_skills.common.cache import CacheManager


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory for tests."""
    cache_dir = tmp_path / "test_cache"
    return cache_dir


@pytest.fixture
def cache_manager(temp_cache_dir):
    """Create CacheManager instance with temporary directory."""
    return CacheManager(cache_dir=temp_cache_dir)


def test_cache_manager_initialization(temp_cache_dir):
    """Test CacheManager creates cache directory."""
    cache = CacheManager(cache_dir=temp_cache_dir)
    assert temp_cache_dir.exists()
    assert temp_cache_dir.is_dir()


def test_set_and_get(cache_manager):
    """Test basic set and get operations."""
    key = "test_key"
    value = {"data": "test_value", "number": 42}

    # Set value
    result = cache_manager.set(key, value, ttl_hours=24)
    assert result is True

    # Get value
    cached = cache_manager.get(key)
    assert cached == value


def test_get_nonexistent_key(cache_manager):
    """Test getting a key that doesn't exist."""
    result = cache_manager.get("nonexistent_key")
    assert result is None


def test_delete(cache_manager):
    """Test deleting cache entries."""
    key = "delete_test"
    value = {"test": "data"}

    # Set and verify
    cache_manager.set(key, value)
    assert cache_manager.get(key) == value

    # Delete and verify
    result = cache_manager.delete(key)
    assert result is True
    assert cache_manager.get(key) is None


def test_ttl_expiration(cache_manager):
    """Test TTL expiration."""
    key = "expiring_key"
    value = {"expires": "soon"}

    # Set with very short TTL (0.001 hours = 3.6 seconds)
    cache_manager.set(key, value, ttl_hours=0.001)

    # Should exist immediately
    assert cache_manager.get(key) == value

    # Wait for expiration (4 seconds to be safe)
    time.sleep(4)

    # Should be expired now
    assert cache_manager.get(key) is None


def test_clear_cache(cache_manager):
    """Test clearing all cache entries."""
    # Set multiple entries
    cache_manager.set("key1", {"data": 1})
    cache_manager.set("key2", {"data": 2})
    cache_manager.set("key3", {"data": 3})

    # Verify they exist
    assert cache_manager.get("key1") is not None
    assert cache_manager.get("key2") is not None
    assert cache_manager.get("key3") is not None

    # Clear cache
    count = cache_manager.clear()
    assert count == 3

    # Verify all gone
    assert cache_manager.get("key1") is None
    assert cache_manager.get("key2") is None
    assert cache_manager.get("key3") is None


def test_get_stats(cache_manager):
    """Test cache statistics."""
    # Add some entries
    cache_manager.set("stats1", {"data": "x" * 100})
    cache_manager.set("stats2", {"data": "y" * 100})

    stats = cache_manager.get_stats()

    assert "cache_dir" in stats
    assert stats["total_entries"] == 2
    assert stats["active_entries"] >= 0
    assert stats["total_size_bytes"] > 0


def test_cleanup_expired(cache_manager):
    """Test cleaning up expired entries."""
    # Add entry with short TTL
    cache_manager.set("expire1", {"data": 1}, ttl_hours=0.001)
    cache_manager.set("keep1", {"data": 2}, ttl_hours=24)

    # Wait for first to expire
    time.sleep(4)

    # Cleanup
    count = cache_manager.cleanup_expired()
    assert count == 1

    # Verify expired gone, active remains
    assert cache_manager.get("expire1") is None
    assert cache_manager.get("keep1") == {"data": 2}


def test_atomic_write(cache_manager, temp_cache_dir):
    """Test atomic write operations don't leave temp files."""
    key = "atomic_test"
    value = {"atomic": True}

    cache_manager.set(key, value)

    # Check no .tmp files left behind
    tmp_files = list(temp_cache_dir.glob("*.tmp"))
    assert len(tmp_files) == 0

    # Check .json file exists
    json_files = list(temp_cache_dir.glob("*.json"))
    assert len(json_files) == 1


def test_key_sanitization(cache_manager):
    """Test keys with problematic characters are sanitized."""
    key = "test/key\\with/slashes"
    value = {"sanitized": True}

    # Should not crash
    cache_manager.set(key, value)
    result = cache_manager.get(key)
    assert result == value


def test_graceful_error_handling(cache_manager):
    """Test cache operations fail gracefully on errors."""
    # Try to set non-serializable value
    key = "bad_value"

    # This should fail but not crash
    class NonSerializable:
        pass

    result = cache_manager.set(key, NonSerializable())
    assert result is False

    # Get should still work
    assert cache_manager.get("other_key") is None


def test_automatic_cleanup_disabled(temp_cache_dir):
    """Test cache manager with automatic cleanup disabled."""
    cache = CacheManager(cache_dir=temp_cache_dir, auto_cleanup=False)

    # Add expired entry
    cache.set("expired_key", {"data": 1}, ttl_hours=0.001)
    time.sleep(4)

    # Should still exist in filesystem (not automatically cleaned)
    cache_files = list(temp_cache_dir.glob("*.json"))
    assert len(cache_files) == 1

    # But get() should return None because it's expired
    assert cache.get("expired_key") is None


def test_automatic_cleanup_on_operations(temp_cache_dir):
    """Test automatic cleanup runs during normal operations."""
    # Create cache with very short cleanup interval
    cache = CacheManager(cache_dir=temp_cache_dir, auto_cleanup=True)
    cache.CLEANUP_INTERVAL_HOURS = 0.001  # ~3.6 seconds

    # Add expired entry
    cache.set("expired1", {"data": 1}, ttl_hours=0.001)
    time.sleep(4)

    # Add new entry - should trigger cleanup if interval passed
    cache._last_cleanup_time = 0  # Force cleanup on next operation
    cache.set("active1", {"data": 2}, ttl_hours=24)

    # After cleanup, only active entry should remain
    cache_files = list(temp_cache_dir.glob("*.json"))
    # Should have 1 file (active1), expired1 should be cleaned
    assert len(cache_files) == 1


def test_automatic_cleanup_interval(temp_cache_dir):
    """Test automatic cleanup respects interval."""
    cache = CacheManager(cache_dir=temp_cache_dir, auto_cleanup=True)
    cache.CLEANUP_INTERVAL_HOURS = 100  # Very long interval

    # Add expired entry
    cache.set("expired1", {"data": 1}, ttl_hours=0.001)
    time.sleep(4)

    # Perform operations - cleanup should not run yet (interval not passed)
    cache.set("active1", {"data": 2})
    cache.get("active1")

    # Expired entry should still be in filesystem
    cache_files = list(temp_cache_dir.glob("*.json"))
    assert len(cache_files) == 2  # Both expired1 and active1


def test_automatic_cleanup_initial(temp_cache_dir):
    """Test automatic cleanup runs on initialization."""
    # Create some expired entries directly
    cache1 = CacheManager(cache_dir=temp_cache_dir, auto_cleanup=False)
    cache1.set("expired1", {"data": 1}, ttl_hours=0.001)
    cache1.set("expired2", {"data": 2}, ttl_hours=0.001)

    time.sleep(4)

    # Now create new cache manager with auto_cleanup enabled
    # It should clean up expired entries on init
    cache2 = CacheManager(cache_dir=temp_cache_dir, auto_cleanup=True)

    # Both entries should be gone
    cache_files = list(temp_cache_dir.glob("*.json"))
    assert len(cache_files) == 0
