"""
Persistent caching for parse results using SQLite.

This module provides a persistent cache for storing parsed file results,
reducing redundant parsing when files haven't changed.
"""

import sqlite3
import hashlib
import json
import pickle
import gzip
from pathlib import Path
from typing import Optional, Any, Dict
from contextlib import contextmanager


class PersistentCache:
    """
    SQLite-backed persistent cache for parsed file results.

    Tracks file metadata (path, hash, modification time, size) and caches
    parse results to avoid re-parsing unchanged files. Supports dependency
    tracking and cascade invalidation.

    Schema:
        file_metadata: path (TEXT PRIMARY KEY), hash (TEXT), mtime (REAL), size (INTEGER)
        cached_results: file_hash (TEXT PRIMARY KEY), result_blob (BLOB)
        file_dependencies: file_path (TEXT), depends_on (TEXT), PRIMARY KEY (file_path, depends_on)
    """

    __slots__ = ('db_path', '_connection')

    def __init__(self, cache_dir: Path):
        """
        Initialize persistent cache.

        Args:
            cache_dir: Directory where cache database will be stored
        """
        self.db_path = cache_dir / "parse_cache.db"
        self._connection: Optional[sqlite3.Connection] = None

        # Ensure cache directory exists
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_schema()

    def _init_schema(self):
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # File metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_metadata (
                    path TEXT PRIMARY KEY,
                    hash TEXT NOT NULL,
                    mtime REAL NOT NULL,
                    size INTEGER NOT NULL
                )
            """)

            # Cached results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cached_results (
                    file_hash TEXT PRIMARY KEY,
                    result_blob BLOB NOT NULL
                )
            """)

            # File dependencies table (for cascade invalidation)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_dependencies (
                    file_path TEXT NOT NULL,
                    depends_on TEXT NOT NULL,
                    PRIMARY KEY (file_path, depends_on)
                )
            """)

            # Create index on hash for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_hash
                ON file_metadata(hash)
            """)

            # Create index on depends_on for faster reverse lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_depends_on
                ON file_dependencies(depends_on)
            """)

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Get database connection as context manager."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _compute_file_hash(self, file_path: Path) -> str:
        """
        Compute SHA-256 hash of file contents.

        Args:
            file_path: Path to file

        Returns:
            Hex digest of file hash
        """
        sha256 = hashlib.sha256()

        with open(file_path, 'rb') as f:
            # Read in chunks for memory efficiency with large files
            while chunk := f.read(8192):
                sha256.update(chunk)

        return sha256.hexdigest()

    def get_cached_result(self, file_path: Path) -> Optional[Any]:
        """
        Retrieve cached parse result if file hasn't changed.

        Args:
            file_path: Path to source file

        Returns:
            Cached parse result if available and file unchanged, None otherwise
        """
        if not file_path.exists():
            return None

        # Get current file metadata
        stat = file_path.stat()
        current_mtime = stat.st_mtime
        current_size = stat.st_size

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Check if we have cached metadata for this file
            cursor.execute(
                "SELECT hash, mtime, size FROM file_metadata WHERE path = ?",
                (str(file_path),)
            )
            row = cursor.fetchone()

            if not row:
                return None

            cached_hash, cached_mtime, cached_size = row

            # Quick check: if mtime and size match, file likely unchanged
            if cached_mtime == current_mtime and cached_size == current_size:
                # Retrieve cached result
                cursor.execute(
                    "SELECT result_blob FROM cached_results WHERE file_hash = ?",
                    (cached_hash,)
                )
                result_row = cursor.fetchone()

                if result_row:
                    # Decompress and deserialize cached result
                    compressed_data = result_row[0]
                    decompressed_data = gzip.decompress(compressed_data)
                    return pickle.loads(decompressed_data)

            # If mtime/size changed, verify with hash
            current_hash = self._compute_file_hash(file_path)

            if current_hash == cached_hash:
                # File content unchanged despite mtime/size change
                # Update metadata and return cached result
                cursor.execute(
                    """
                    UPDATE file_metadata
                    SET mtime = ?, size = ?
                    WHERE path = ?
                    """,
                    (current_mtime, current_size, str(file_path))
                )
                conn.commit()

                cursor.execute(
                    "SELECT result_blob FROM cached_results WHERE file_hash = ?",
                    (current_hash,)
                )
                result_row = cursor.fetchone()

                if result_row:
                    # Decompress and deserialize cached result
                    compressed_data = result_row[0]
                    decompressed_data = gzip.decompress(compressed_data)
                    return pickle.loads(decompressed_data)

            return None

    def store_result(self, file_path: Path, result: Any):
        """
        Store parse result in cache.

        Args:
            file_path: Path to source file
            result: Parse result to cache (should be a ParseResult with dependencies)
        """
        if not file_path.exists():
            return

        # Get file metadata
        stat = file_path.stat()
        file_hash = self._compute_file_hash(file_path)

        # Serialize and compress result
        pickled_data = pickle.dumps(result)
        result_blob = gzip.compress(pickled_data)

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Store/update file metadata
            cursor.execute(
                """
                INSERT OR REPLACE INTO file_metadata (path, hash, mtime, size)
                VALUES (?, ?, ?, ?)
                """,
                (str(file_path), file_hash, stat.st_mtime, stat.st_size)
            )

            # Store/update cached result
            cursor.execute(
                """
                INSERT OR REPLACE INTO cached_results (file_hash, result_blob)
                VALUES (?, ?)
                """,
                (file_hash, result_blob)
            )

            # Store dependencies if result has them
            if hasattr(result, 'dependencies') and result.dependencies:
                # First, clear old dependencies for this file
                cursor.execute(
                    "DELETE FROM file_dependencies WHERE file_path = ?",
                    (str(file_path),)
                )

                # Store new dependencies
                # dependencies is Dict[str, List[str]] mapping file paths to their imports
                for dep_file in result.dependencies.get(str(file_path), []):
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO file_dependencies (file_path, depends_on)
                        VALUES (?, ?)
                        """,
                        (str(file_path), dep_file)
                    )

            conn.commit()

    def invalidate_file(self, file_path: Path, cascade: bool = True):
        """
        Invalidate cache entry for a file.

        Args:
            file_path: Path to file to invalidate
            cascade: If True, also invalidate files that depend on this file
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Get file hash before deleting metadata
            cursor.execute(
                "SELECT hash FROM file_metadata WHERE path = ?",
                (str(file_path),)
            )
            row = cursor.fetchone()

            if row:
                file_hash = row[0]

                # Delete file metadata
                cursor.execute(
                    "DELETE FROM file_metadata WHERE path = ?",
                    (str(file_path),)
                )

                # Delete dependencies for this file
                cursor.execute(
                    "DELETE FROM file_dependencies WHERE file_path = ?",
                    (str(file_path),)
                )

                # Check if any other files use this hash
                cursor.execute(
                    "SELECT COUNT(*) FROM file_metadata WHERE hash = ?",
                    (file_hash,)
                )
                count = cursor.fetchone()[0]

                # If no other files use this hash, delete cached result
                if count == 0:
                    cursor.execute(
                        "DELETE FROM cached_results WHERE file_hash = ?",
                        (file_hash,)
                    )

                conn.commit()

            # Cascade invalidation to dependent files if requested
            if cascade:
                self._cascade_invalidation(file_path)

    def _cascade_invalidation(self, file_path: Path):
        """
        Invalidate files that depend on the given file.

        Args:
            file_path: Path to file whose dependents should be invalidated
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Find all files that depend on this file
            cursor.execute(
                "SELECT file_path FROM file_dependencies WHERE depends_on = ?",
                (str(file_path),)
            )
            dependent_files = [row[0] for row in cursor.fetchall()]

        # Recursively invalidate dependent files (without cascading further to avoid cycles)
        for dep_file_str in dependent_files:
            dep_file_path = Path(dep_file_str)
            self.invalidate_file(dep_file_path, cascade=False)

    def clear(self):
        """Clear all cached data."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM file_metadata")
            cursor.execute("DELETE FROM cached_results")
            cursor.execute("DELETE FROM file_dependencies")
            conn.commit()

    def get_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics (files_cached, results_cached, total_size_bytes, dependencies_tracked)
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM file_metadata")
            files_cached = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM cached_results")
            results_cached = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(LENGTH(result_blob)) FROM cached_results")
            total_size = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM file_dependencies")
            dependencies_tracked = cursor.fetchone()[0]

            return {
                'files_cached': files_cached,
                'results_cached': results_cached,
                'total_size_bytes': total_size,
                'dependencies_tracked': dependencies_tracked
            }

    def get_dependencies(self, file_path: Path) -> list[str]:
        """
        Get list of files that the given file depends on.

        Args:
            file_path: Path to file

        Returns:
            List of file paths that this file depends on
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT depends_on FROM file_dependencies WHERE file_path = ?",
                (str(file_path),)
            )

            return [row[0] for row in cursor.fetchall()]

    def get_dependents(self, file_path: Path) -> list[str]:
        """
        Get list of files that depend on the given file.

        Args:
            file_path: Path to file

        Returns:
            List of file paths that depend on this file
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT file_path FROM file_dependencies WHERE depends_on = ?",
                (str(file_path),)
            )

            return [row[0] for row in cursor.fetchall()]
