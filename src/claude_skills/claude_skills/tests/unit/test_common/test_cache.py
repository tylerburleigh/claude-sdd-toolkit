from __future__ import annotations

"""Exercises CacheManager CRUD behaviour, TTL, statistics, and key generation."""

import json
import time
from pathlib import Path
from typing import Dict

import pytest

from claude_skills.common.cache import (
    CacheManager,
    generate_cache_key,
    generate_fidelity_review_key,
    generate_plan_review_key,
    is_cache_key_valid,
)


pytestmark = pytest.mark.unit


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create temporary cache directory for tests."""
    cache_dir = tmp_path / "test_cache"
    return cache_dir


@pytest.fixture
def cache_manager(temp_cache_dir: Path) -> CacheManager:
    """Create CacheManager instance with temporary directory."""
    return CacheManager(cache_dir=temp_cache_dir)


# ============================================================================
# CacheManager CRUD Operations Tests
# ============================================================================


class TestCacheCRUD:
    """Test cache Create, Read, Update, Delete operations."""

    def test_cache_manager_initialization(self, temp_cache_dir: Path) -> None:
        cache = CacheManager(cache_dir=temp_cache_dir)
        assert temp_cache_dir.exists()
        assert temp_cache_dir.is_dir()

    def test_create_and_read(self, cache_manager: CacheManager) -> None:
        key = "test_key"
        value = {"data": "test_value", "number": 42}

        assert cache_manager.set(key, value, ttl_hours=24) is True
        cached = cache_manager.get(key)
        assert cached == value

    def test_read_nonexistent_key(self, cache_manager: CacheManager) -> None:
        assert cache_manager.get("nonexistent_key") is None

    def test_update_existing_value(self, cache_manager: CacheManager) -> None:
        key = "update_test"
        original = {"version": 1, "data": "original"}
        updated = {"version": 2, "data": "updated"}

        cache_manager.set(key, original, ttl_hours=24)
        assert cache_manager.get(key) == original

        cache_manager.set(key, updated, ttl_hours=24)
        assert cache_manager.get(key) == updated

    def test_delete_operation(self, cache_manager: CacheManager) -> None:
        key = "delete_test"
        value = {"test": "data"}

        cache_manager.set(key, value)
        assert cache_manager.get(key) == value

        assert cache_manager.delete(key) is True
        assert cache_manager.get(key) is None

    def test_delete_nonexistent_key(self, cache_manager: CacheManager) -> None:
        assert cache_manager.delete("nonexistent_key") is True

    def test_clear_all_entries(self, cache_manager: CacheManager) -> None:
        cache_manager.set("key1", {"data": 1})
        cache_manager.set("key2", {"data": 2})
        cache_manager.set("key3", {"data": 3})

        assert cache_manager.get("key1") is not None
        assert cache_manager.get("key2") is not None
        assert cache_manager.get("key3") is not None

        count = cache_manager.clear()
        assert count == 3

        assert cache_manager.get("key1") is None
        assert cache_manager.get("key2") is None
        assert cache_manager.get("key3") is None


# ============================================================================
# TTL and Expiration Tests
# ============================================================================


class TestTTLExpiration:
    """Test TTL (Time To Live) expiration functionality."""

    def test_ttl_expiration(self, cache_manager: CacheManager) -> None:
        key = "expiring_key"
        value = {"expires": "soon"}

        cache_manager.set(key, value, ttl_hours=0.001)
        assert cache_manager.get(key) == value

        time.sleep(4)
        assert cache_manager.get(key) is None

    def test_cleanup_expired_entries(self, cache_manager: CacheManager) -> None:
        cache_manager.set("expire1", {"data": 1}, ttl_hours=0.001)
        cache_manager.set("keep1", {"data": 2}, ttl_hours=24)

        time.sleep(4)
        count = cache_manager.cleanup_expired()
        assert count == 1
        assert cache_manager.get("expire1") is None
        assert cache_manager.get("keep1") == {"data": 2}

    def test_automatic_cleanup_disabled(self, temp_cache_dir: Path) -> None:
        cache = CacheManager(cache_dir=temp_cache_dir, auto_cleanup=False)
        cache.set("expired_key", {"data": 1}, ttl_hours=0.001)
        time.sleep(4)

        cache_files = list(temp_cache_dir.glob("*.json"))
        assert len(cache_files) == 1
        assert cache.get("expired_key") is None

    def test_automatic_cleanup_on_operations(self, temp_cache_dir: Path) -> None:
        cache = CacheManager(cache_dir=temp_cache_dir, auto_cleanup=True)
        cache.CLEANUP_INTERVAL_HOURS = 0.001

        cache.set("expired1", {"data": 1}, ttl_hours=0.001)
        time.sleep(4)
        cache._last_cleanup_time = 0
        cache.set("active1", {"data": 2}, ttl_hours=24)

        cache_files = list(temp_cache_dir.glob("*.json"))
        assert len(cache_files) == 1

    def test_automatic_cleanup_interval(self, temp_cache_dir: Path) -> None:
        cache = CacheManager(cache_dir=temp_cache_dir, auto_cleanup=True)
        cache.CLEANUP_INTERVAL_HOURS = 100

        cache.set("expired1", {"data": 1}, ttl_hours=0.001)
        time.sleep(4)

        cache.set("active1", {"data": 2})
        cache.get("active1")
        cache_files = list(temp_cache_dir.glob("*.json"))
        assert len(cache_files) == 2

    def test_automatic_cleanup_initial(self, temp_cache_dir: Path) -> None:
        cache1 = CacheManager(cache_dir=temp_cache_dir, auto_cleanup=False)
        cache1.set("expired1", {"data": 1}, ttl_hours=0.001)
        cache1.set("expired2", {"data": 2}, ttl_hours=0.001)

        time.sleep(4)
        cache2 = CacheManager(cache_dir=temp_cache_dir, auto_cleanup=True)
        cache_files = list(temp_cache_dir.glob("*.json"))
        assert len(cache_files) == 0


# ============================================================================
# Cache Statistics and Metadata Tests
# ============================================================================


class TestCacheStatistics:
    """Test cache statistics and metadata operations."""

    def test_get_stats(self, cache_manager: CacheManager) -> None:
        cache_manager.set("stats1", {"data": "x" * 100})
        cache_manager.set("stats2", {"data": "y" * 100})

        stats = cache_manager.get_stats()
        assert "cache_dir" in stats
        assert stats["total_entries"] == 2
        assert stats["active_entries"] >= 0
        assert stats["total_size_bytes"] > 0

    def test_atomic_write(self, cache_manager: CacheManager, temp_cache_dir: Path) -> None:
        cache_manager.set("atomic_test", {"atomic": True})
        tmp_files = list(temp_cache_dir.glob("*.tmp"))
        assert len(tmp_files) == 0
        json_files = list(temp_cache_dir.glob("*.json"))
        assert len(json_files) == 1


# ============================================================================
# Data Integrity Tests
# ============================================================================


class TestDataIntegrity:
    """Test data integrity and error handling."""

    def test_key_sanitization(self, cache_manager: CacheManager) -> None:
        key = "test/key\\with/slashes"
        value = {"sanitized": True}
        cache_manager.set(key, value)
        result = cache_manager.get(key)
        assert result == value

    def test_graceful_error_handling(self, cache_manager: CacheManager) -> None:
        key = "bad_value"

        class NonSerializable:
            pass

        assert cache_manager.set(key, NonSerializable()) is False
        assert cache_manager.get("other_key") is None


# ============================================================================
# Cache Key Generation Tests
# ============================================================================


class TestCacheKeyGeneration:
    """Test cache key generation for deterministic caching."""

    def test_generate_cache_key_basic(self) -> None:
        key = generate_cache_key(spec_id="test-spec-001")
        assert is_cache_key_valid(key)
        assert len(key) == 64

    def test_generate_cache_key_deterministic(self) -> None:
        key1 = generate_cache_key(spec_id="test-spec-001", model="gemini", prompt_version="v1")
        key2 = generate_cache_key(spec_id="test-spec-001", model="gemini", prompt_version="v1")
        assert key1 == key2

    def test_generate_cache_key_different_specs(self) -> None:
        key1 = generate_cache_key(spec_id="spec-001")
        key2 = generate_cache_key(spec_id="spec-002")
        assert key1 != key2

    def test_generate_cache_key_different_models(self) -> None:
        key1 = generate_cache_key(spec_id="test-spec", model="gemini")
        key2 = generate_cache_key(spec_id="test-spec", model="codex")
        assert key1 != key2

    def test_generate_cache_key_different_versions(self) -> None:
        key1 = generate_cache_key(spec_id="test-spec", prompt_version="v1")
        key2 = generate_cache_key(spec_id="test-spec", prompt_version="v2")
        assert key1 != key2

    def test_generate_cache_key_with_files(self, tmp_path: Path) -> None:
        file1 = tmp_path / "test1.py"
        file1.write_text("def test1(): pass")
        file2 = tmp_path / "test2.py"
        file2.write_text("def test2(): pass")

        key1 = generate_cache_key(spec_id="test-spec", file_paths=[str(file1), str(file2)])
        file1.write_text("def test1(): return 42")
        key2 = generate_cache_key(spec_id="test-spec", file_paths=[str(file1), str(file2)])
        assert key1 != key2

    def test_generate_cache_key_file_order_deterministic(self, tmp_path: Path) -> None:
        file1 = tmp_path / "test1.py"
        file2 = tmp_path / "test2.py"
        file1.write_text("def test1(): pass")
        file2.write_text("def test2(): pass")

        key1 = generate_cache_key(spec_id="test-spec", file_paths=[str(file1), str(file2)])
        key2 = generate_cache_key(spec_id="test-spec", file_paths=[str(file2), str(file1)])
        assert key1 == key2

    def test_generate_cache_key_missing_file(self, tmp_path: Path) -> None:
        file1 = tmp_path / "test1.py"
        file1.write_text("def test1(): pass")
        missing_file = tmp_path / "missing.py"

        key = generate_cache_key(spec_id="test-spec", file_paths=[str(file1), str(missing_file)])
        assert is_cache_key_valid(key)

    def test_generate_cache_key_with_extra_params(self) -> None:
        key1 = generate_cache_key(
            spec_id="test-spec",
            extra_params={"scope": "full", "verbosity": "high"},
        )
        key2 = generate_cache_key(
            spec_id="test-spec",
            extra_params={"scope": "partial", "verbosity": "high"},
        )
        assert key1 != key2

    def test_generate_cache_key_extra_params_order(self) -> None:
        key1 = generate_cache_key(
            spec_id="test-spec",
            extra_params={"scope": "full", "verbosity": "high"},
        )
        key2 = generate_cache_key(
            spec_id="test-spec",
            extra_params={"verbosity": "high", "scope": "full"},
        )
        assert key1 == key2


# ============================================================================
# Specialized Key Generation Tests
# ============================================================================


class TestSpecializedKeyGeneration:
    """Test specialized key generation for different review types."""

    def test_generate_fidelity_review_key(self) -> None:
        key = generate_fidelity_review_key(
            spec_id="test-spec-001",
            scope="full",
            target="spec-root",
        )
        assert is_cache_key_valid(key)
        assert len(key) == 64

    def test_generate_fidelity_review_key_different_scopes(self) -> None:
        key1 = generate_fidelity_review_key(spec_id="test-spec", scope="full", target="spec-root")
        key2 = generate_fidelity_review_key(spec_id="test-spec", scope="partial", target="spec-root")
        assert key1 != key2

    def test_generate_plan_review_key(self) -> None:
        key = generate_plan_review_key(
            spec_id="test-spec-001",
            models=["gemini", "codex"],
        )
        assert is_cache_key_valid(key)
        assert len(key) == 64

    def test_generate_plan_review_key_models_order(self) -> None:
        key1 = generate_plan_review_key(
            spec_id="test-spec",
            models=["gemini", "codex"],
        )
        key2 = generate_plan_review_key(
            spec_id="test-spec",
            models=["codex", "gemini"],
        )
        assert key1 == key2

    def test_generate_plan_review_key_with_focus(self) -> None:
        key = generate_plan_review_key(
            spec_id="test-spec",
            models=["gemini"],
            review_focus=["security", "performance"],
        )
        assert is_cache_key_valid(key)

    def test_is_cache_key_valid(self) -> None:
        valid_key = generate_cache_key(spec_id="test-spec")
        assert is_cache_key_valid(valid_key)
        assert not is_cache_key_valid("not_a_valid_sha256_key")


# ============================================================================
# Complex Integration Scenarios
# ============================================================================


class TestComplexScenarios:
    """Test complex cache scenarios and edge cases."""

    def test_generate_cache_key_complex_scenario(self, tmp_path: Path) -> None:
        file1 = tmp_path / "code.py"
        file1.write_text("# complex scenario")

        key = generate_cache_key(
            spec_id="phase5-agent-optimization",
            file_paths=[str(file1)],
            model="pro",
            prompt_version="v2",
            extra_params={
                "scope": "incremental",
                "review_type": "fidelity",
                "include_metrics": True,
            },
        )
        assert is_cache_key_valid(key)
        assert len(key) == 64

        key2 = generate_cache_key(
            spec_id="phase5-agent-optimization",
            file_paths=[str(file1)],
            model="pro",
            prompt_version="v2",
            extra_params={
                "review_type": "fidelity",
                "scope": "incremental",
                "include_metrics": True,
            },
        )
        assert key == key2

    def test_cache_performance_with_multiple_entries(self, cache_manager: CacheManager) -> None:
        for i in range(100):
            cache_manager.set(f"key_{i}", {"index": i, "data": f"value_{i}"})

        for i in range(100):
            value = cache_manager.get(f"key_{i}")
            assert value is not None
            assert value["index"] == i

        stats = cache_manager.get_stats()
        assert stats["total_entries"] == 100

    def test_mixed_crud_operations(self, cache_manager: CacheManager) -> None:
        cache_manager.set("user_1", {"name": "Alice", "role": "admin"})
        cache_manager.set("user_2", {"name": "Bob", "role": "user"})

        assert cache_manager.get("user_1")["name"] == "Alice"

        cache_manager.set("user_1", {"name": "Alice", "role": "super_admin"})
        assert cache_manager.get("user_1")["role"] == "super_admin"

        cache_manager.delete("user_2")
        assert cache_manager.get("user_2") is None

        assert cache_manager.get("user_1") is not None

        cache_manager.clear()
        assert cache_manager.get("user_1") is None


# ============================================================================
# Merge Results Tests
# ============================================================================


class TestCacheMergeResults:
    """Ported merge_results scenarios covering unchanged/changed/added/deleted paths."""

    def test_merge_all_unchanged(self) -> None:
        cached = {
            "src/main.py": {"functions": ["main"], "lines": 100},
            "src/utils.py": {"functions": ["helper"], "lines": 50},
            "src/config.py": {"functions": ["load_config"], "lines": 30},
        }
        fresh: Dict[str, Dict[str, object]] = {}
        changed_files: set[str] = set()

        result = CacheManager.merge_results(cached, fresh, changed_files)
        assert result == cached
        assert len(result) == 3

    def test_merge_all_changed(self) -> None:
        cached = {
            "src/main.py": {"functions": ["main"], "lines": 100},
            "src/utils.py": {"functions": ["helper"], "lines": 50},
        }
        fresh = {
            "src/main.py": {"functions": ["main", "init"], "lines": 120},
            "src/utils.py": {"functions": ["helper", "format"], "lines": 75},
        }
        changed_files = {"src/main.py", "src/utils.py"}

        result = CacheManager.merge_results(cached, fresh, changed_files)
        assert result == fresh
        assert result["src/main.py"]["lines"] == 120
        assert result["src/utils.py"]["lines"] == 75

    def test_merge_mixed_scenario(self) -> None:
        cached = {
            "src/main.py": {"functions": ["main"], "lines": 100},
            "src/utils.py": {"functions": ["helper"], "lines": 50},
            "src/config.py": {"functions": ["load_config"], "lines": 30},
        }
        fresh = {"src/main.py": {"functions": ["main", "init"], "lines": 120}}
        changed_files = {"src/main.py"}

        result = CacheManager.merge_results(cached, fresh, changed_files)
        assert len(result) == 3
        assert result["src/main.py"] == fresh["src/main.py"]
        assert result["src/utils.py"] == cached["src/utils.py"]
        assert result["src/config.py"] == cached["src/config.py"]

    def test_merge_new_files_added(self) -> None:
        cached = {
            "src/main.py": {"functions": ["main"], "lines": 100},
            "src/utils.py": {"functions": ["helper"], "lines": 50},
        }
        fresh = {"src/new_feature.py": {"functions": ["feature_func"], "lines": 80}}
        changed_files = {"src/new_feature.py"}

        result = CacheManager.merge_results(cached, fresh, changed_files)
        assert len(result) == 3
        assert "src/new_feature.py" in result
        assert result["src/new_feature.py"] == fresh["src/new_feature.py"]

    def test_merge_files_deleted(self) -> None:
        cached = {
            "src/main.py": {"functions": ["main"], "lines": 100},
            "src/utils.py": {"functions": ["helper"], "lines": 50},
            "src/old.py": {"functions": ["old_func"], "lines": 30},
        }
        fresh: Dict[str, Dict[str, object]] = {}
        changed_files = {"src/old.py"}

        result = CacheManager.merge_results(cached, fresh, changed_files)
        assert len(result) == 2
        assert "src/old.py" not in result

    def test_merge_empty_cache(self) -> None:
        cached: Dict[str, Dict[str, object]] = {}
        fresh = {
            "src/main.py": {"functions": ["main"], "lines": 100},
            "src/utils.py": {"functions": ["helper"], "lines": 50},
        }
        changed_files = {"src/main.py", "src/utils.py"}

        result = CacheManager.merge_results(cached, fresh, changed_files)
        assert result == fresh

    def test_merge_empty_fresh(self) -> None:
        cached = {
            "src/main.py": {"functions": ["main"], "lines": 100},
            "src/utils.py": {"functions": ["helper"], "lines": 50},
        }
        fresh: Dict[str, Dict[str, object]] = {}
        changed_files: set[str] = set()

        result = CacheManager.merge_results(cached, fresh, changed_files)
        assert result == cached

    def test_merge_both_empty(self) -> None:
        assert CacheManager.merge_results({}, {}, set()) == {}

    def test_merge_preserves_data_structure(self) -> None:
        cached = {
            "src/main.py": {
                "functions": [{"name": "main", "args": ["argc", "argv"], "returns": "int"}],
                "classes": [{"name": "App", "methods": ["run", "stop"]}],
                "imports": ["sys", "os"],
                "metadata": {"author": "Alice", "version": "1.0"},
            }
        }
        fresh: Dict[str, Dict[str, object]] = {}
        changed_files: set[str] = set()

        result = CacheManager.merge_results(cached, fresh, changed_files)
        assert result == cached
        assert result["src/main.py"]["functions"][0]["name"] == "main"

    def test_merge_overwrites_cached_with_fresh(self) -> None:
        cached = {
            "src/api.py": {"endpoints": ["/users", "/posts"], "version": "v1", "deprecated": False}
        }
        fresh = {
            "src/api.py": {
                "endpoints": ["/users", "/posts", "/comments"],
                "version": "v2",
                "deprecated": False,
                "new_field": "added",
            }
        }
        changed_files = {"src/api.py"}

        result = CacheManager.merge_results(cached, fresh, changed_files)
        assert result["src/api.py"] == fresh["src/api.py"]

    def test_merge_handles_generation_failure(self) -> None:
        cached = {
            "src/main.py": {"functions": ["main"], "lines": 100},
            "src/broken.py": {"functions": ["broken"], "lines": 50},
            "src/utils.py": {"functions": ["helper"], "lines": 30},
        }
        fresh = {"src/main.py": {"functions": ["main", "init"], "lines": 120}}
        changed_files = {"src/main.py", "src/broken.py"}

        result = CacheManager.merge_results(cached, fresh, changed_files)
        assert "src/main.py" in result
        assert "src/utils.py" in result
        assert "src/broken.py" not in result

    def test_merge_large_result_set(self) -> None:
        cached = {f"src/file{i}.py": {"lines": i} for i in range(1000)}
        fresh = {f"src/file{i}.py": {"lines": i * 2} for i in range(10)}
        changed_files = {f"src/file{i}.py" for i in range(10)}

        result = CacheManager.merge_results(cached, fresh, changed_files)
        assert len(result) == 1000
        for i in range(10):
            assert result[f"src/file{i}.py"]["lines"] == i * 2
        for i in range(10, 1000):
            assert result[f"src/file{i}.py"]["lines"] == i

    def test_merge_with_file_path_variations(self) -> None:
        cached = {
            "src/main.py": {"lines": 100},
            "./src/utils.py": {"lines": 50},
            "/abs/path/config.py": {"lines": 30},
        }
        fresh = {"src/main.py": {"lines": 120}}
        changed_files = {"src/main.py"}

        result = CacheManager.merge_results(cached, fresh, changed_files)
        assert "src/main.py" in result
        assert "./src/utils.py" in result
        assert "/abs/path/config.py" in result

    def test_merge_idempotence(self) -> None:
        cached = {
            "src/main.py": {"lines": 100},
            "src/utils.py": {"lines": 50},
        }
        fresh = {"src/main.py": {"lines": 120}}
        changed_files = {"src/main.py"}

        result1 = CacheManager.merge_results(cached, fresh, changed_files)
        result2 = CacheManager.merge_results(cached, fresh, changed_files)
        assert result1 == result2

    def test_merge_does_not_modify_inputs(self) -> None:
        cached = {
            "src/main.py": {"lines": 100},
            "src/utils.py": {"lines": 50},
        }
        fresh = {"src/main.py": {"lines": 120}}
        changed_files = {"src/main.py"}

        cached_copy = cached.copy()
        fresh_copy = fresh.copy()
        changed_copy = changed_files.copy()

        CacheManager.merge_results(cached, fresh, changed_files)

        assert cached == cached_copy
        assert fresh == fresh_copy
        assert changed_files == changed_copy


class TestCacheMergeIntegration:
    """Integration with compare_file_hashes workflow."""

    def test_merge_with_compare_file_hashes_workflow(self) -> None:
        old_hashes = {
            "src/main.py": "hash_a",
            "src/utils.py": "hash_b",
            "src/old.py": "hash_c",
        }
        new_hashes = {
            "src/main.py": "hash_a_modified",
            "src/utils.py": "hash_b",
            "src/new.py": "hash_d",
        }

        changes = CacheManager.compare_file_hashes(old_hashes, new_hashes)
        cached_results = {
            "src/main.py": {"docs": "old version"},
            "src/utils.py": {"docs": "unchanged"},
            "src/old.py": {"docs": "deleted file"},
        }
        fresh_results = {
            "src/main.py": {"docs": "new version"},
            "src/new.py": {"docs": "new file"},
        }
        changed_files = set(changes["added"] + changes["modified"] + changes["removed"])

        merged = CacheManager.merge_results(cached_results, fresh_results, changed_files)
        assert merged["src/main.py"]["docs"] == "new version"
        assert merged["src/utils.py"]["docs"] == "unchanged"
        assert merged["src/new.py"]["docs"] == "new file"
        assert "src/old.py" not in merged
        assert len(merged) == 3
