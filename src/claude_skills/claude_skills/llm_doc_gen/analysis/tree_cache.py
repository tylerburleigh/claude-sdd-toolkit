"""
Tree cache for incremental parsing.

This module provides caching for parsed syntax trees to enable fast
incremental re-parsing when files change. Uses tree-sitter's edit API.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime


@dataclass
class CachedTree:
    """Cached syntax tree with metadata."""
    tree: Any  # tree_sitter.Tree
    content_hash: str
    mtime: float
    size: int
    timestamp: float  # When cached


class TreeCache:
    """
    Cache for parsed syntax trees.

    Stores trees keyed by file path with content hash for validation.
    Enables incremental re-parsing when files change using tree-sitter's
    parse(old_tree=...) API.
    """

    def __init__(self, max_cache_size: int = 1000):
        """
        Initialize tree cache.

        Args:
            max_cache_size: Maximum number of trees to cache (default: 1000)
        """
        self.cache: Dict[str, CachedTree] = {}
        self.max_cache_size = max_cache_size
        self.hits = 0
        self.misses = 0
        self.invalidations = 0

    def get(self, file_path: Path) -> Optional[CachedTree]:
        """
        Get cached tree for a file if it exists and is valid.

        Validates cache entry by checking:
        1. File still exists
        2. Modification time matches
        3. File size matches

        Args:
            file_path: Path to file

        Returns:
            CachedTree if valid cache hit, None otherwise
        """
        path_key = str(file_path)

        if path_key not in self.cache:
            self.misses += 1
            return None

        cached = self.cache[path_key]

        # Validate cache entry
        if not file_path.exists():
            # File deleted, invalidate cache
            del self.cache[path_key]
            self.invalidations += 1
            self.misses += 1
            return None

        stat = file_path.stat()

        # Check if file modified (mtime or size changed)
        if stat.st_mtime != cached.mtime or stat.st_size != cached.size:
            # File changed, invalidate cache
            del self.cache[path_key]
            self.invalidations += 1
            self.misses += 1
            return None

        # Cache hit!
        self.hits += 1
        return cached

    def put(self, file_path: Path, tree: Any, content: str):
        """
        Store a parsed tree in the cache.

        Args:
            file_path: Path to file
            tree: Parsed tree-sitter Tree
            content: File content (for computing hash)
        """
        # Evict oldest entry if cache is full
        if len(self.cache) >= self.max_cache_size:
            self._evict_oldest()

        path_key = str(file_path)
        stat = file_path.stat()

        # Compute content hash for validation
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

        cached = CachedTree(
            tree=tree,
            content_hash=content_hash,
            mtime=stat.st_mtime,
            size=stat.st_size,
            timestamp=datetime.now().timestamp()
        )

        self.cache[path_key] = cached

    def invalidate(self, file_path: Path):
        """
        Manually invalidate cache entry for a file.

        Args:
            file_path: Path to file
        """
        path_key = str(file_path)
        if path_key in self.cache:
            del self.cache[path_key]
            self.invalidations += 1

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        self.invalidations = 0

    def _evict_oldest(self):
        """Evict the oldest cache entry (LRU-like)."""
        if not self.cache:
            return

        # Find entry with oldest timestamp
        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].timestamp)
        del self.cache[oldest_key]

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats (hits, misses, size, hit_rate)
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            'size': len(self.cache),
            'max_size': self.max_cache_size,
            'hits': self.hits,
            'misses': self.misses,
            'invalidations': self.invalidations,
            'hit_rate': f"{hit_rate:.1f}%"
        }

    def __len__(self) -> int:
        """Return number of cached trees."""
        return len(self.cache)
