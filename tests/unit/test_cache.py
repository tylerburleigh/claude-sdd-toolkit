"""
Consolidated unit tests for cache functionality.
Tests cache CRUD operations (Create, Read, Update, Delete) for AI response caching.
"""

import json
import time
import pytest
from pathlib import Path
from claude_skills.common.cache import (
    CacheManager,
    generate_cache_key,
    generate_fidelity_review_key,
    generate_plan_review_key,
    is_cache_key_valid
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory for tests."""
    cache_dir = tmp_path / "test_cache"
    return cache_dir


@pytest.fixture
def cache_manager(temp_cache_dir):
    """Create CacheManager instance with temporary directory."""
    return CacheManager(cache_dir=temp_cache_dir)


# ============================================================================
# CacheManager CRUD Operations Tests
# ============================================================================

class TestCacheCRUD:
    """Test cache Create, Read, Update, Delete operations."""

    def test_cache_manager_initialization(self, temp_cache_dir):
        """Test CacheManager creates cache directory."""
        cache = CacheManager(cache_dir=temp_cache_dir)
        assert temp_cache_dir.exists()
        assert temp_cache_dir.is_dir()

    def test_create_and_read(self, cache_manager):
        """Test CREATE and READ operations - set and get values."""
        key = "test_key"
        value = {"data": "test_value", "number": 42}

        # Create: Set value
        result = cache_manager.set(key, value, ttl_hours=24)
        assert result is True

        # Read: Get value
        cached = cache_manager.get(key)
        assert cached == value

    def test_read_nonexistent_key(self, cache_manager):
        """Test READ operation on non-existent key returns None."""
        result = cache_manager.get("nonexistent_key")
        assert result is None

    def test_update_existing_value(self, cache_manager):
        """Test UPDATE operation - modify cached value."""
        key = "update_test"
        original = {"version": 1, "data": "original"}
        updated = {"version": 2, "data": "updated"}

        # Create initial value
        cache_manager.set(key, original, ttl_hours=24)
        assert cache_manager.get(key) == original

        # Update value
        cache_manager.set(key, updated, ttl_hours=24)
        assert cache_manager.get(key) == updated

    def test_delete_operation(self, cache_manager):
        """Test DELETE operation - remove cache entries."""
        key = "delete_test"
        value = {"test": "data"}

        # Create
        cache_manager.set(key, value)
        assert cache_manager.get(key) == value

        # Delete
        result = cache_manager.delete(key)
        assert result is True
        assert cache_manager.get(key) is None

    def test_delete_nonexistent_key(self, cache_manager):
        """Test DELETE on non-existent key returns True (no error)."""
        result = cache_manager.delete("nonexistent_key")
        assert result is True  # Delete returns True even if key didn't exist

    def test_clear_all_entries(self, cache_manager):
        """Test clearing all cache entries."""
        # Create multiple entries
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


# ============================================================================
# TTL and Expiration Tests
# ============================================================================

class TestTTLExpiration:
    """Test TTL (Time To Live) expiration functionality."""

    def test_ttl_expiration(self, cache_manager):
        """Test TTL expiration - cached items expire after TTL."""
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

    def test_cleanup_expired_entries(self, cache_manager):
        """Test cleanup removes only expired entries."""
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

    def test_automatic_cleanup_disabled(self, temp_cache_dir):
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

    def test_automatic_cleanup_on_operations(self, temp_cache_dir):
        """Test automatic cleanup runs during normal operations."""
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

    def test_automatic_cleanup_interval(self, temp_cache_dir):
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

    def test_automatic_cleanup_initial(self, temp_cache_dir):
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


# ============================================================================
# Cache Statistics and Metadata Tests
# ============================================================================

class TestCacheStatistics:
    """Test cache statistics and metadata operations."""

    def test_get_stats(self, cache_manager):
        """Test cache statistics."""
        # Add some entries
        cache_manager.set("stats1", {"data": "x" * 100})
        cache_manager.set("stats2", {"data": "y" * 100})

        stats = cache_manager.get_stats()

        assert "cache_dir" in stats
        assert stats["total_entries"] == 2
        assert stats["active_entries"] >= 0
        assert stats["total_size_bytes"] > 0

    def test_atomic_write(self, cache_manager, temp_cache_dir):
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


# ============================================================================
# Data Integrity Tests
# ============================================================================

class TestDataIntegrity:
    """Test data integrity and error handling."""

    def test_key_sanitization(self, cache_manager):
        """Test keys with problematic characters are sanitized."""
        key = "test/key\\with/slashes"
        value = {"sanitized": True}

        # Should not crash
        cache_manager.set(key, value)
        result = cache_manager.get(key)
        assert result == value

    def test_graceful_error_handling(self, cache_manager):
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


# ============================================================================
# Cache Key Generation Tests
# ============================================================================

class TestCacheKeyGeneration:
    """Test cache key generation for deterministic caching."""

    def test_generate_cache_key_basic(self):
        """Test basic cache key generation."""
        key = generate_cache_key(spec_id="test-spec-001")

        # Should be valid hex string
        assert is_cache_key_valid(key)
        assert len(key) == 64  # SHA256 hex

    def test_generate_cache_key_deterministic(self):
        """Test cache keys are deterministic."""
        key1 = generate_cache_key(
            spec_id="test-spec-001",
            model="gemini",
            prompt_version="v1"
        )
        key2 = generate_cache_key(
            spec_id="test-spec-001",
            model="gemini",
            prompt_version="v1"
        )

        assert key1 == key2

    def test_generate_cache_key_different_specs(self):
        """Test different specs produce different keys."""
        key1 = generate_cache_key(spec_id="spec-001")
        key2 = generate_cache_key(spec_id="spec-002")

        assert key1 != key2

    def test_generate_cache_key_different_models(self):
        """Test different models produce different keys."""
        key1 = generate_cache_key(spec_id="test-spec", model="gemini")
        key2 = generate_cache_key(spec_id="test-spec", model="codex")

        assert key1 != key2

    def test_generate_cache_key_different_versions(self):
        """Test different prompt versions produce different keys."""
        key1 = generate_cache_key(spec_id="test-spec", prompt_version="v1")
        key2 = generate_cache_key(spec_id="test-spec", prompt_version="v2")

        assert key1 != key2

    def test_generate_cache_key_with_files(self, tmp_path):
        """Test cache key includes file contents."""
        # Create test files
        file1 = tmp_path / "test1.py"
        file1.write_text("def test1(): pass")

        file2 = tmp_path / "test2.py"
        file2.write_text("def test2(): pass")

        key1 = generate_cache_key(
            spec_id="test-spec",
            file_paths=[str(file1), str(file2)]
        )

        # Modify file content
        file1.write_text("def test1(): return 42")

        key2 = generate_cache_key(
            spec_id="test-spec",
            file_paths=[str(file1), str(file2)]
        )

        # Keys should be different
        assert key1 != key2

    def test_generate_cache_key_file_order_deterministic(self, tmp_path):
        """Test file order doesn't affect key (deterministic)."""
        file1 = tmp_path / "test1.py"
        file1.write_text("def test1(): pass")

        file2 = tmp_path / "test2.py"
        file2.write_text("def test2(): pass")

        key1 = generate_cache_key(
            spec_id="test-spec",
            file_paths=[str(file1), str(file2)]
        )

        key2 = generate_cache_key(
            spec_id="test-spec",
            file_paths=[str(file2), str(file1)]
        )

        # Keys should be the same regardless of file order
        assert key1 == key2

    def test_generate_cache_key_missing_file(self, tmp_path):
        """Test cache key generation handles missing files."""
        file1 = tmp_path / "test1.py"
        file1.write_text("def test1(): pass")

        missing_file = tmp_path / "missing.py"

        # Should handle gracefully (no exception)
        key = generate_cache_key(
            spec_id="test-spec",
            file_paths=[str(file1), str(missing_file)]
        )

        assert is_cache_key_valid(key)

    def test_generate_cache_key_with_extra_params(self):
        """Test cache key includes extra parameters."""
        key1 = generate_cache_key(
            spec_id="test-spec",
            extra_params={"scope": "full", "verbosity": "high"}
        )
        key2 = generate_cache_key(
            spec_id="test-spec",
            extra_params={"scope": "partial", "verbosity": "high"}
        )

        assert key1 != key2

    def test_generate_cache_key_extra_params_order(self):
        """Test extra param order doesn't affect key."""
        key1 = generate_cache_key(
            spec_id="test-spec",
            extra_params={"scope": "full", "verbosity": "high"}
        )
        key2 = generate_cache_key(
            spec_id="test-spec",
            extra_params={"verbosity": "high", "scope": "full"}
        )

        assert key1 == key2


# ============================================================================
# Specialized Key Generation Tests
# ============================================================================

class TestSpecializedKeyGeneration:
    """Test specialized key generation for different review types."""

    def test_generate_fidelity_review_key(self):
        """Test fidelity review key generation."""
        key = generate_fidelity_review_key(
            spec_id="test-spec-001",
            scope="full",
            target="spec-root"
        )

        assert is_cache_key_valid(key)
        assert len(key) == 64

    def test_generate_fidelity_review_key_different_scopes(self):
        """Test different scopes produce different keys."""
        key1 = generate_fidelity_review_key(spec_id="test-spec", scope="full", target="spec-root")
        key2 = generate_fidelity_review_key(spec_id="test-spec", scope="partial", target="spec-root")

        assert key1 != key2

    def test_generate_plan_review_key(self):
        """Test plan review key generation."""
        key = generate_plan_review_key(
            spec_id="test-spec-001",
            models=["gemini", "codex"]
        )

        assert is_cache_key_valid(key)
        assert len(key) == 64

    def test_generate_plan_review_key_models_order(self):
        """Test model order doesn't affect key."""
        key1 = generate_plan_review_key(
            spec_id="test-spec",
            models=["gemini", "codex"]
        )
        key2 = generate_plan_review_key(
            spec_id="test-spec",
            models=["codex", "gemini"]
        )

        # Should be the same (order-independent)
        assert key1 == key2

    def test_generate_plan_review_key_with_focus(self):
        """Test plan review key with focus areas."""
        key = generate_plan_review_key(
            spec_id="test-spec",
            models=["gemini"],
            review_focus=["security", "performance"]
        )

        assert is_cache_key_valid(key)

    def test_is_cache_key_valid(self):
        """Test cache key validation."""
        valid_key = generate_cache_key(spec_id="test-spec")
        assert is_cache_key_valid(valid_key)

        invalid_key = "not_a_valid_sha256_key"
        assert not is_cache_key_valid(invalid_key)


# ============================================================================
# Complex Integration Scenarios
# ============================================================================

class TestComplexScenarios:
    """Test complex cache scenarios and edge cases."""

    def test_generate_cache_key_complex_scenario(self, tmp_path):
        """Test cache key generation with multiple parameters."""
        file1 = tmp_path / "code.py"
        file1.write_text("# complex scenario")

        key = generate_cache_key(
            spec_id="phase5-agent-optimization",
            file_paths=[str(file1)],
            model="gemini-2.5-pro",
            prompt_version="v2",
            extra_params={
                "scope": "incremental",
                "review_type": "fidelity",
                "include_metrics": True
            }
        )

        assert is_cache_key_valid(key)
        assert len(key) == 64

        # Same inputs should produce same key
        key2 = generate_cache_key(
            spec_id="phase5-agent-optimization",
            file_paths=[str(file1)],
            model="gemini-2.5-pro",
            prompt_version="v2",
            extra_params={
                "review_type": "fidelity",
                "scope": "incremental",  # Different order
                "include_metrics": True
            }
        )

        assert key == key2

    def test_cache_performance_with_multiple_entries(self, cache_manager):
        """Test cache performance with many entries."""
        # Add 100 entries
        for i in range(100):
            cache_manager.set(f"key_{i}", {"index": i, "data": f"value_{i}"})

        # Verify all can be retrieved
        for i in range(100):
            value = cache_manager.get(f"key_{i}")
            assert value is not None
            assert value["index"] == i

        # Get stats
        stats = cache_manager.get_stats()
        assert stats["total_entries"] == 100

    def test_mixed_crud_operations(self, cache_manager):
        """Test mixed CRUD operations in sequence."""
        # Create
        cache_manager.set("user_1", {"name": "Alice", "role": "admin"})
        cache_manager.set("user_2", {"name": "Bob", "role": "user"})

        # Read
        assert cache_manager.get("user_1")["name"] == "Alice"

        # Update
        cache_manager.set("user_1", {"name": "Alice", "role": "super_admin"})
        assert cache_manager.get("user_1")["role"] == "super_admin"

        # Delete
        cache_manager.delete("user_2")
        assert cache_manager.get("user_2") is None

        # Verify first still exists
        assert cache_manager.get("user_1") is not None

        # Clear all
        cache_manager.clear()
        assert cache_manager.get("user_1") is None
