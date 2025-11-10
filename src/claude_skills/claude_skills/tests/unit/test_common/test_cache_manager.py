from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict

import pytest

from claude_skills.common.cache import cache_manager as cache_module
from claude_skills.common.cache.cache_manager import CacheManager


pytestmark = pytest.mark.unit


def _install_fake_time(monkeypatch: pytest.MonkeyPatch, start: float = 1_000.0) -> Callable[[float], None]:
    """
    Replace ``time.time`` inside the cache manager with a controllable clock.

    Returns a helper function that can be used to advance the clock by a number
    of seconds without sleeping.
    """

    current = {"value": start}

    def fake_time() -> float:
        return current["value"]

    def advance(seconds: float) -> None:
        current["value"] += seconds

    monkeypatch.setattr(cache_module.time, "time", fake_time)
    return advance


def _read_cache_entry(cache_dir: Path, key: str) -> Dict[str, object]:
    """Load the raw JSON payload stored for ``key`` to assert metadata."""
    cache_path = (cache_dir / key).with_suffix(".json")
    with cache_path.open("r") as handle:
        return json.load(handle)


def test_set_and_get_respects_ttl(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    advance = _install_fake_time(monkeypatch)
    cache = CacheManager(cache_dir=tmp_path, auto_cleanup=False)

    assert cache.set("example", {"value": 1}, ttl_hours=0.001) is True
    assert cache.get("example") == {"value": 1}

    advance(60.0 * 60.0)  # Advance 1 hour – well beyond the ttl

    assert cache.get("example") is None
    # Entry should be deleted when expired
    assert not (tmp_path / "example.json").exists()


def test_save_and_get_incremental_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    advance = _install_fake_time(monkeypatch)
    cache = CacheManager(cache_dir=tmp_path, auto_cleanup=False)

    state = {"src/main.py": "abc123", "src/utils.py": "def456"}
    assert cache.save_incremental_state("spec-1", state, ttl_hours=0.01) is True

    raw_entry = _read_cache_entry(tmp_path, "incremental_state:spec-1")
    assert raw_entry["metadata"]["spec_id"] == "spec-1"
    assert raw_entry["metadata"]["file_count"] == 2

    # Retrieve immediately
    assert cache.get_incremental_state("spec-1") == state

    # Advance past TTL to confirm expiry clears the state
    advance(60.0 * 60.0)
    assert cache.get_incremental_state("spec-1") == {}


def test_compare_file_hashes_identifies_differences() -> None:
    old = {"a.py": "1", "b.py": "2", "c.py": "3"}
    new = {"a.py": "1", "b.py": "22", "d.py": "4"}

    diff = CacheManager.compare_file_hashes(old, new)

    assert diff == {
        "added": ["d.py"],
        "modified": ["b.py"],
        "removed": ["c.py"],
        "unchanged": ["a.py"],
    }


def test_merge_results_prefers_fresh_for_changed_files() -> None:
    cached = {
        "a.py": {"status": "ok"},
        "b.py": {"status": "stale"},
        "c.py": {"status": "old"},
    }
    fresh = {
        "b.py": {"status": "updated"},
        "d.py": {"status": "new"},
    }
    merged = CacheManager.merge_results(cached, fresh, changed_files={"b.py", "d.py"})

    assert merged == {
        "a.py": {"status": "ok"},
        "b.py": {"status": "updated"},
        "c.py": {"status": "old"},
        "d.py": {"status": "new"},
    }


def test_cleanup_expired_removes_only_stale_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    advance = _install_fake_time(monkeypatch)
    cache = CacheManager(cache_dir=tmp_path, auto_cleanup=False)

    cache.set("fresh", {"status": "active"}, ttl_hours=1)
    cache.set("stale", {"status": "expired"}, ttl_hours=0.001)

    advance(10.0)  # Expire the short-lived entry without touching the long one

    removed = cache.cleanup_expired()
    assert removed == 1
    assert cache.get("stale") is None
    assert cache.get("fresh") == {"status": "active"}
    assert not (tmp_path / "stale.json").exists()


def test_cleanup_expired_skips_corrupt_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    advance = _install_fake_time(monkeypatch)
    cache = CacheManager(cache_dir=tmp_path, auto_cleanup=False)

    cache.set("valid-stale", {"value": 1}, ttl_hours=0.001)
    corrupt_path = cache._get_cache_path("corrupt")
    corrupt_path.write_text("this is not valid json")

    advance(10.0)

    removed = cache.cleanup_expired()
    assert removed == 1
    assert corrupt_path.exists(), "Corrupt file should be ignored, not deleted"


def test_clear_filters_by_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_time(monkeypatch)
    cache = CacheManager(cache_dir=tmp_path, auto_cleanup=False)

    cache.set(
        "spec-1:fidelity",
        {"result": "keep-or-delete"},
        metadata={"spec_id": "spec-1", "review_type": "fidelity"},
    )
    cache.set(
        "spec-1:plan",
        {"result": "plan"},
        metadata={"spec_id": "spec-1", "review_type": "plan"},
    )
    cache.set(
        "spec-2:fidelity",
        {"result": "other-spec"},
        metadata={"spec_id": "spec-2", "review_type": "fidelity"},
    )
    cache.set("legacy", {"result": "legacy-entry"})  # No metadata

    removed = cache.clear(spec_id="spec-1", review_type="fidelity")
    assert removed == 1
    assert cache.get("spec-1:fidelity") is None
    assert cache.get("spec-1:plan") == {"result": "plan"}
    assert cache.get("spec-2:fidelity") == {"result": "other-spec"}
    assert cache.get("legacy") == {"result": "legacy-entry"}


def test_clear_without_filters_removes_everything(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _install_fake_time(monkeypatch)
    cache = CacheManager(cache_dir=tmp_path, auto_cleanup=False)

    cache.set("one", {"value": 1})
    cache.set("two", {"value": 2})
    cache.set(
        "metadata-entry",
        {"value": 3},
        metadata={"spec_id": "spec-3", "review_type": "fidelity"},
    )

    removed = cache.clear()
    assert removed == 3
    assert cache.get("one") is None
    assert cache.get("two") is None
    assert cache.get("metadata-entry") is None


def test_get_stats_counts_expired_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    advance = _install_fake_time(monkeypatch)
    cache = CacheManager(cache_dir=tmp_path, auto_cleanup=False)

    cache.set("fresh", {"payload": 1}, ttl_hours=1)
    cache.set("soon-expired", {"payload": 2}, ttl_hours=0.001)

    advance(10.0)

    stats = cache.get_stats()
    assert stats["total_entries"] == 2
    assert stats["expired_entries"] == 1
    assert stats["active_entries"] == 1
    assert stats["total_size_bytes"] >= 0


def test_cache_dir_created(tmp_path: Path) -> None:
    custom_dir = tmp_path / "nested" / "cache-location"
    cache = CacheManager(cache_dir=custom_dir, auto_cleanup=False)

    assert cache.cache_dir == custom_dir
    assert custom_dir.exists()
    assert custom_dir.is_dir()


def test_atomic_write_leaves_no_temp_files(tmp_path: Path) -> None:
    cache = CacheManager(cache_dir=tmp_path, auto_cleanup=False)

    assert cache.set("atomic", {"value": True}) is True
    assert list(tmp_path.glob("*.tmp")) == []
    assert list(tmp_path.glob("*.json")) == [tmp_path / "atomic.json"]


def test_key_sanitization_round_trip(tmp_path: Path) -> None:
    cache = CacheManager(cache_dir=tmp_path, auto_cleanup=False)
    key = "path/with\\separators"

    assert cache.set(key, {"ok": True}) is True
    assert cache.get(key) == {"ok": True}
    # Ensure sanitized file exists on disk
    assert (tmp_path / "path_with_separators.json").exists()


def test_set_handles_non_serializable_value(tmp_path: Path) -> None:
    cache = CacheManager(cache_dir=tmp_path, auto_cleanup=False)

    class NonSerializable:
        pass

    assert cache.set("bad", NonSerializable()) is False
    assert cache.get("bad") is None


def test_auto_cleanup_disabled_retains_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    advance = _install_fake_time(monkeypatch, start=10_000.0)
    cache = CacheManager(cache_dir=tmp_path, auto_cleanup=False)

    cache.set("expired", {"value": 1}, ttl_hours=0.001)
    advance(10.0)

    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1  # File still present because cleanup disabled
    assert cache.get("expired") is None  # Lookup still respects TTL and removes entry


def test_auto_cleanup_runs_when_interval_passed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    advance = _install_fake_time(monkeypatch, start=10_000.0)
    cache = CacheManager(cache_dir=tmp_path, auto_cleanup=True)
    cache.CLEANUP_INTERVAL_HOURS = 0.0001  # ~0.36 seconds

    cache.set("expired", {"value": 1}, ttl_hours=0.0001)
    advance(10.0)  # Ensure entry expired well in the past

    cache._last_cleanup_time = 0
    cache.set("active", {"value": 2})

    files = list(tmp_path.glob("*.json"))
    assert files == [tmp_path / "active.json"]


def test_auto_cleanup_respects_interval(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    advance = _install_fake_time(monkeypatch, start=10_000.0)
    cache = CacheManager(cache_dir=tmp_path, auto_cleanup=True)
    cache.CLEANUP_INTERVAL_HOURS = 100  # Very large interval

    cache.set("expired", {"value": 1}, ttl_hours=0.0001)
    advance(10.0)

    # Because interval not elapsed, cleanup shouldn't run
    cache.set("active", {"value": 2})

    files = sorted(tmp_path.glob("*.json"))
    assert (tmp_path / "expired.json") in files
    assert (tmp_path / "active.json") in files


def test_auto_cleanup_on_initialization(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    advance = _install_fake_time(monkeypatch, start=10_000.0)
    first = CacheManager(cache_dir=tmp_path, auto_cleanup=False)
    first.set("expired", {"value": 1}, ttl_hours=0.0001)
    advance(10.0)

    # Second manager with auto_cleanup should remove expired entry on init
    CacheManager(cache_dir=tmp_path, auto_cleanup=True)
    assert list(tmp_path.glob("*.json")) == []
