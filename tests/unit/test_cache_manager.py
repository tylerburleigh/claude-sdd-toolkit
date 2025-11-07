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


# ========================================================================
# Incremental State Tests
# ========================================================================


class TestIncrementalState:
    """Test suite for incremental state tracking functionality."""

    def test_get_incremental_state_empty(self, cache_manager):
        """Test getting incremental state when none exists."""
        spec_id = "test-spec-001"
        state = cache_manager.get_incremental_state(spec_id)

        assert state == {}
        assert isinstance(state, dict)

    def test_save_and_get_incremental_state(self, cache_manager):
        """Test save and retrieve cycle for incremental state."""
        spec_id = "test-spec-001"
        file_hashes = {
            "src/main.py": "abc123",
            "src/utils.py": "def456",
            "tests/test_main.py": "ghi789"
        }

        # Save state
        result = cache_manager.save_incremental_state(spec_id, file_hashes)
        assert result is True

        # Retrieve state
        retrieved = cache_manager.get_incremental_state(spec_id)
        assert retrieved == file_hashes

    def test_save_incremental_state_overwrites(self, cache_manager):
        """Test that saving state overwrites previous state."""
        spec_id = "test-spec-001"

        # Save initial state
        initial_hashes = {"src/main.py": "abc123"}
        cache_manager.save_incremental_state(spec_id, initial_hashes)

        # Overwrite with new state
        new_hashes = {"src/main.py": "xyz789", "src/new.py": "def456"}
        cache_manager.save_incremental_state(spec_id, new_hashes)

        # Should get new state, not initial
        retrieved = cache_manager.get_incremental_state(spec_id)
        assert retrieved == new_hashes

    def test_incremental_state_ttl(self, cache_manager):
        """Test incremental state respects TTL."""
        spec_id = "test-spec-001"
        file_hashes = {"src/main.py": "abc123"}

        # Save with very short TTL
        cache_manager.save_incremental_state(spec_id, file_hashes, ttl_hours=0.001)

        # Should exist immediately
        assert cache_manager.get_incremental_state(spec_id) == file_hashes

        # Wait for expiration
        time.sleep(4)

        # Should be expired now
        assert cache_manager.get_incremental_state(spec_id) == {}

    def test_incremental_state_default_ttl(self, cache_manager):
        """Test incremental state uses longer default TTL (7 days)."""
        spec_id = "test-spec-001"
        file_hashes = {"src/main.py": "abc123"}

        # Save without specifying TTL
        cache_manager.save_incremental_state(spec_id, file_hashes)

        # Verify the cache entry has the correct TTL (7 days = 168 hours)
        cache_key = f"incremental_state:{spec_id}"
        cache_path = cache_manager._get_cache_path(cache_key)

        with cache_path.open("r") as f:
            entry = json.load(f)

        expected_ttl_seconds = 168 * 3600  # 7 days in seconds
        assert entry["ttl_seconds"] == expected_ttl_seconds

    def test_incremental_state_multiple_specs(self, cache_manager):
        """Test incremental state for multiple specs are independent."""
        spec1 = "test-spec-001"
        spec2 = "test-spec-002"

        hashes1 = {"src/main.py": "abc123"}
        hashes2 = {"src/utils.py": "def456"}

        # Save state for both specs
        cache_manager.save_incremental_state(spec1, hashes1)
        cache_manager.save_incremental_state(spec2, hashes2)

        # Each should retrieve its own state
        assert cache_manager.get_incremental_state(spec1) == hashes1
        assert cache_manager.get_incremental_state(spec2) == hashes2

    def test_save_incremental_state_validates_input(self, cache_manager):
        """Test save_incremental_state validates input types."""
        spec_id = "test-spec-001"

        # Should reject non-dict input
        result = cache_manager.save_incremental_state(spec_id, "not a dict")
        assert result is False

        result = cache_manager.save_incremental_state(spec_id, ["list", "not", "dict"])
        assert result is False

        # Should accept valid dict
        result = cache_manager.save_incremental_state(spec_id, {})
        assert result is True

    def test_get_incremental_state_validates_cached_data(self, cache_manager):
        """Test get_incremental_state handles invalid cached data gracefully."""
        spec_id = "test-spec-001"

        # Manually corrupt the cache entry with non-dict value
        cache_key = f"incremental_state:{spec_id}"
        cache_manager.set(cache_key, "corrupted data", ttl_hours=24)

        # Should return empty dict instead of crashing
        state = cache_manager.get_incremental_state(spec_id)
        assert state == {}

    def test_incremental_state_includes_metadata(self, cache_manager):
        """Test incremental state entries include proper metadata."""
        spec_id = "test-spec-001"
        file_hashes = {"src/main.py": "abc123", "src/utils.py": "def456"}

        cache_manager.save_incremental_state(spec_id, file_hashes)

        # Read raw cache entry
        cache_key = f"incremental_state:{spec_id}"
        cache_path = cache_manager._get_cache_path(cache_key)

        with cache_path.open("r") as f:
            entry = json.load(f)

        # Verify metadata
        metadata = entry.get("metadata", {})
        assert metadata["spec_id"] == spec_id
        assert metadata["type"] == "incremental_state"
        assert metadata["file_count"] == 2
        assert "timestamp" in metadata


class TestCompareFileHashes:
    """Test suite for compare_file_hashes utility function."""

    def test_compare_no_changes(self):
        """Test comparison when no files changed."""
        old = {"src/main.py": "abc123", "src/utils.py": "def456"}
        new = {"src/main.py": "abc123", "src/utils.py": "def456"}

        result = CacheManager.compare_file_hashes(old, new)

        assert result["added"] == []
        assert result["modified"] == []
        assert result["removed"] == []
        assert result["unchanged"] == ["src/main.py", "src/utils.py"]

    def test_compare_added_files(self):
        """Test comparison detects added files."""
        old = {"src/main.py": "abc123"}
        new = {"src/main.py": "abc123", "src/new.py": "xyz789"}

        result = CacheManager.compare_file_hashes(old, new)

        assert result["added"] == ["src/new.py"]
        assert result["modified"] == []
        assert result["removed"] == []
        assert result["unchanged"] == ["src/main.py"]

    def test_compare_modified_files(self):
        """Test comparison detects modified files."""
        old = {"src/main.py": "abc123"}
        new = {"src/main.py": "xyz789"}

        result = CacheManager.compare_file_hashes(old, new)

        assert result["added"] == []
        assert result["modified"] == ["src/main.py"]
        assert result["removed"] == []
        assert result["unchanged"] == []

    def test_compare_removed_files(self):
        """Test comparison detects removed files."""
        old = {"src/main.py": "abc123", "src/old.py": "def456"}
        new = {"src/main.py": "abc123"}

        result = CacheManager.compare_file_hashes(old, new)

        assert result["added"] == []
        assert result["modified"] == []
        assert result["removed"] == ["src/old.py"]
        assert result["unchanged"] == ["src/main.py"]

    def test_compare_complex_scenario(self):
        """Test comparison with mixed changes."""
        old = {
            "src/main.py": "abc123",  # will be modified
            "src/old.py": "def456",   # will be removed
            "src/same.py": "ghi789"   # unchanged
        }
        new = {
            "src/main.py": "xyz123",  # modified
            "src/same.py": "ghi789",  # unchanged
            "src/new.py": "jkl012"    # added
        }

        result = CacheManager.compare_file_hashes(old, new)

        assert result["added"] == ["src/new.py"]
        assert result["modified"] == ["src/main.py"]
        assert result["removed"] == ["src/old.py"]
        assert result["unchanged"] == ["src/same.py"]

    def test_compare_empty_old_hashes(self):
        """Test comparison when no previous hashes exist."""
        old = {}
        new = {"src/main.py": "abc123", "src/utils.py": "def456"}

        result = CacheManager.compare_file_hashes(old, new)

        assert result["added"] == ["src/main.py", "src/utils.py"]
        assert result["modified"] == []
        assert result["removed"] == []
        assert result["unchanged"] == []

    def test_compare_empty_new_hashes(self):
        """Test comparison when all files removed."""
        old = {"src/main.py": "abc123", "src/utils.py": "def456"}
        new = {}

        result = CacheManager.compare_file_hashes(old, new)

        assert result["added"] == []
        assert result["modified"] == []
        assert result["removed"] == ["src/main.py", "src/utils.py"]
        assert result["unchanged"] == []

    def test_compare_both_empty(self):
        """Test comparison when both are empty."""
        result = CacheManager.compare_file_hashes({}, {})

        assert result["added"] == []
        assert result["modified"] == []
        assert result["removed"] == []
        assert result["unchanged"] == []

    def test_compare_results_sorted(self):
        """Test comparison results are sorted alphabetically."""
        old = {"z.py": "1", "a.py": "2"}
        new = {"m.py": "3", "b.py": "4"}

        result = CacheManager.compare_file_hashes(old, new)

        # Results should be sorted
        assert result["added"] == ["b.py", "m.py"]
        assert result["removed"] == ["a.py", "z.py"]
