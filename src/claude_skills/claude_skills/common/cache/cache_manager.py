"""
File-based cache manager for AI consultation results.

Provides persistent caching with TTL support to reduce redundant AI consultations.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

try:
    from claude_skills.common.config import get_cache_config
    _CONFIG_AVAILABLE = True
except ImportError:
    _CONFIG_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheManager:
    """
    File-based cache manager with TTL support.

    Stores cache entries as JSON files in a configurable directory.
    Each entry includes the cached value, creation timestamp, and TTL.

    Features:
    - Atomic file operations to prevent corruption
    - Automatic TTL expiration
    - Graceful error handling (never crashes, degrades to no-cache)
    - Configurable cache directory

    Usage:
        cache = CacheManager()
        cache.set("my_key", {"data": "value"}, ttl_hours=24)
        result = cache.get("my_key")  # Returns {"data": "value"} or None if expired
    """

    DEFAULT_CACHE_DIR = Path.home() / ".cache" / "sdd-toolkit" / "consultations"
    DEFAULT_TTL_HOURS = 24
    CLEANUP_INTERVAL_HOURS = 1  # Run automatic cleanup every hour

    def __init__(self, cache_dir: Optional[Path] = None, auto_cleanup: Optional[bool] = None):
        """
        Initialize cache manager.

        Reads configuration from config.py if available, with fallback to defaults.

        Args:
            cache_dir: Custom cache directory path (overrides config, defaults to config or ~/.cache/sdd-toolkit/consultations/)
            auto_cleanup: Enable automatic cleanup of expired entries (overrides config, defaults to config or True)
        """
        # Load config if available
        if _CONFIG_AVAILABLE:
            config = get_cache_config()
            config_dir = config.get("directory")
            config_auto_cleanup = config.get("auto_cleanup", True)
        else:
            config_dir = None
            config_auto_cleanup = True

        # Apply parameters (parameters override config)
        self.cache_dir = cache_dir or self._get_cache_dir_from_config(config_dir)
        self.auto_cleanup = auto_cleanup if auto_cleanup is not None else config_auto_cleanup
        self._last_cleanup_time = 0
        self._ensure_cache_dir()

        # Run initial cleanup if auto_cleanup enabled
        if self.auto_cleanup:
            self._maybe_cleanup()

    def _get_cache_dir_from_config(self, config_dir: Optional[str]) -> Path:
        """Get cache directory from config or environment variable or use default."""
        # Environment variable takes precedence
        env_path = os.environ.get("SDD_CACHE_DIR")
        if env_path:
            return Path(env_path).expanduser()

        # Use config directory if provided
        if config_dir:
            return Path(config_dir).expanduser()

        # Fall back to default
        return self.DEFAULT_CACHE_DIR

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Cache directory ready: {self.cache_dir}")
        except Exception as e:
            logger.warning(f"Failed to create cache directory {self.cache_dir}: {e}")
            logger.warning("Cache operations will fail gracefully")

    def _get_cache_path(self, key: str) -> Path:
        """Get file path for a cache key."""
        # Sanitize key for filesystem (replace problematic characters)
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"{safe_key}.json"

    def _maybe_cleanup(self) -> None:
        """
        Run automatic cleanup if enough time has passed since last cleanup.

        This is called automatically on cache operations when auto_cleanup is enabled.
        Cleanup runs at most once per CLEANUP_INTERVAL_HOURS.
        """
        if not self.auto_cleanup:
            return

        now = time.time()
        interval_seconds = self.CLEANUP_INTERVAL_HOURS * 3600

        if now - self._last_cleanup_time >= interval_seconds:
            logger.debug("Running automatic cache cleanup")
            try:
                count = self.cleanup_expired()
                if count > 0:
                    logger.info(f"Automatic cleanup removed {count} expired entries")
                self._last_cleanup_time = now
            except Exception as e:
                logger.warning(f"Automatic cleanup failed: {e}")
                # Update last cleanup time anyway to avoid hammering on errors
                self._last_cleanup_time = now

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache if it exists and hasn't expired.

        Args:
            key: Cache key to retrieve

        Returns:
            Cached value if found and not expired, None otherwise
        """
        # Maybe run automatic cleanup
        self._maybe_cleanup()

        cache_path = self._get_cache_path(key)

        try:
            if not cache_path.exists():
                logger.debug(f"Cache miss: {key}")
                return None

            # Read cache entry
            with cache_path.open("r") as f:
                entry = json.load(f)

            # Check expiration
            created_at = entry.get("created_at")
            ttl_seconds = entry.get("ttl_seconds")

            if created_at and ttl_seconds:
                expired_at = created_at + ttl_seconds
                now = time.time()

                if now > expired_at:
                    logger.debug(f"Cache expired: {key}")
                    # Clean up expired entry
                    self.delete(key)
                    return None

            logger.debug(f"Cache hit: {key}")
            return entry.get("value")

        except Exception as e:
            logger.warning(f"Failed to read cache entry {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl_hours: Optional[float] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl_hours: Time to live in hours (defaults to 24 hours)
            metadata: Optional metadata for filtering (spec_id, review_type, model, etc.)

        Returns:
            True if successful, False if operation failed
        """
        # Maybe run automatic cleanup
        self._maybe_cleanup()

        if ttl_hours is None:
            ttl_hours = self.DEFAULT_TTL_HOURS

        cache_path = self._get_cache_path(key)

        try:
            # Create cache entry
            entry = {
                "key": key,
                "value": value,
                "created_at": time.time(),
                "ttl_seconds": ttl_hours * 3600,
                "expires_at_human": (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
            }

            # Add metadata if provided (for filtering support)
            if metadata:
                entry["metadata"] = metadata

            # Atomic write: write to temp file, then rename
            temp_path = cache_path.with_suffix(".tmp")
            with temp_path.open("w") as f:
                json.dump(entry, f, indent=2)

            # Atomic rename (overwrites existing file)
            temp_path.replace(cache_path)

            logger.debug(f"Cache set: {key} (TTL: {ttl_hours}h)")
            return True

        except Exception as e:
            logger.warning(f"Failed to write cache entry {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete cache entry.

        Args:
            key: Cache key to delete

        Returns:
            True if successful or entry didn't exist, False on error
        """
        cache_path = self._get_cache_path(key)

        try:
            if cache_path.exists():
                cache_path.unlink()
                logger.debug(f"Cache deleted: {key}")
            return True
        except Exception as e:
            logger.warning(f"Failed to delete cache entry {key}: {e}")
            return False

    def clear(self, spec_id: Optional[str] = None, review_type: Optional[str] = None) -> int:
        """
        Clear cache entries with optional filters.

        Args:
            spec_id: Filter by spec ID (clears only entries for this spec)
            review_type: Filter by review type ("fidelity", "plan", or None for all types)

        Returns:
            Number of entries deleted

        Examples:
            cache.clear()  # Clear all entries
            cache.clear(spec_id="my-spec-001")  # Clear all entries for my-spec-001
            cache.clear(review_type="fidelity")  # Clear all fidelity review entries
            cache.clear(spec_id="my-spec-001", review_type="plan")  # Clear plan reviews for my-spec-001
        """
        count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    # If filters specified, check if entry matches
                    if spec_id or review_type:
                        with cache_file.open("r") as f:
                            entry = json.load(f)

                        # Check if entry matches filters
                        if not self._matches_filters(entry, spec_id, review_type):
                            continue

                    # Delete matching entry
                    cache_file.unlink()
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete cache file {cache_file}: {e}")

            logger.info(f"Cache cleared: {count} entries deleted (spec_id={spec_id}, review_type={review_type})")
            return count

        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")
            return count

    def _matches_filters(self, entry: Dict[str, Any], spec_id: Optional[str], review_type: Optional[str]) -> bool:
        """
        Check if cache entry matches the specified filters.

        Args:
            entry: Cache entry dictionary
            spec_id: Spec ID filter (None to ignore)
            review_type: Review type filter (None to ignore)

        Returns:
            True if entry matches all specified filters

        Note:
            Uses the metadata field added in the cache entry for filtering.
            Entries without metadata are skipped when filters are applied.
        """
        # Get metadata from entry (added in set() method)
        metadata = entry.get("metadata", {})

        # If no metadata and filters are specified, skip this entry
        # (it's an old entry without metadata support)
        if (spec_id or review_type) and not metadata:
            return False

        # Extract spec_id from metadata
        entry_spec_id = metadata.get("spec_id")

        # Extract review_type from metadata
        entry_review_type = metadata.get("review_type")

        # Apply filters
        if spec_id and entry_spec_id != spec_id:
            return False

        if review_type and entry_review_type != review_type:
            return False

        return True

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats (total entries, expired entries, size, etc.)
        """
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            total_entries = len(cache_files)
            expired_entries = 0
            total_size_bytes = 0

            now = time.time()

            for cache_file in cache_files:
                try:
                    total_size_bytes += cache_file.stat().st_size

                    with cache_file.open("r") as f:
                        entry = json.load(f)

                    created_at = entry.get("created_at")
                    ttl_seconds = entry.get("ttl_seconds")

                    if created_at and ttl_seconds:
                        if now > (created_at + ttl_seconds):
                            expired_entries += 1

                except Exception as e:
                    logger.warning(f"Failed to read cache file {cache_file}: {e}")

            return {
                "cache_dir": str(self.cache_dir),
                "total_entries": total_entries,
                "expired_entries": expired_entries,
                "active_entries": total_entries - expired_entries,
                "total_size_bytes": total_size_bytes,
                "total_size_mb": round(total_size_bytes / (1024 * 1024), 2)
            }

        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {
                "cache_dir": str(self.cache_dir),
                "error": str(e)
            }

    def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries.

        Returns:
            Number of entries deleted
        """
        count = 0
        try:
            now = time.time()

            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with cache_file.open("r") as f:
                        entry = json.load(f)

                    created_at = entry.get("created_at")
                    ttl_seconds = entry.get("ttl_seconds")

                    if created_at and ttl_seconds:
                        if now > (created_at + ttl_seconds):
                            cache_file.unlink()
                            count += 1

                except Exception as e:
                    logger.warning(f"Failed to check/delete cache file {cache_file}: {e}")

            if count > 0:
                logger.info(f"Cleaned up {count} expired cache entries")

            return count

        except Exception as e:
            logger.warning(f"Failed to cleanup expired entries: {e}")
            return count
