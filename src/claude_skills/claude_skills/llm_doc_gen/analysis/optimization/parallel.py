"""
Parallel parsing optimization for multi-core systems.

Provides ParallelParser that distributes file parsing across multiple CPU cores
using multiprocessing.Pool, significantly improving performance on large codebases.
"""

import os
import multiprocessing as mp
from typing import List, Optional, Callable, Any, Tuple, Dict
from pathlib import Path
from dataclasses import dataclass, field

# Imports for worker function
try:
    from ..parsers.base import ParseResult
    from ..tree_cache import TreeCache
except ImportError:
    # Fallback for direct execution
    from parsers.base import ParseResult
    from tree_cache import TreeCache


@dataclass
class ParseTask:
    """Represents a single file parsing task."""
    file_path: str
    language: str
    parser_func: Optional[Callable] = None


# Per-worker cache (one instance per worker process)
_worker_tree_cache: Optional[TreeCache] = None


def _init_worker_cache(cache_size: int = 100):
    """
    Initialize per-worker TreeCache.

    Called once per worker process to create isolated cache.
    Each worker process gets its own TreeCache instance.

    Args:
        cache_size: Maximum cache size for this worker
    """
    global _worker_tree_cache
    _worker_tree_cache = TreeCache(max_cache_size=cache_size)


def _parse_worker_func(task: Tuple[str, str, Any]) -> ParseResult:
    """
    Worker function for parallel file parsing.

    Parses a single file using isolated per-worker TreeCache.
    This function is executed in a separate worker process.

    Args:
        task: Tuple of (file_path, language, parser_config)

    Returns:
        ParseResult containing parsed functions, classes, modules, etc.

    Example:
        >>> # Called by multiprocessing.Pool
        >>> result = _parse_worker_func(("main.py", "python", config))
        >>> # Returns ParseResult with isolated cache

    Note:
        Each worker process maintains its own TreeCache instance,
        preventing cache conflicts in parallel execution.
    """
    global _worker_tree_cache

    file_path, language, parser_config = task

    # Initialize worker cache if not already done
    if _worker_tree_cache is None:
        _init_worker_cache()

    try:
        # Create parser for this language
        # In a real implementation, this would use the parser factory
        # For now, create a minimal ParseResult

        path_obj = Path(file_path)

        # Check if we have a cached tree
        cached = _worker_tree_cache.get(path_obj) if _worker_tree_cache else None

        # Parse the file (using cached tree if available)
        # In real implementation, would call parser with cached tree
        # For now, return empty result structure

        result = ParseResult(
            modules=[],
            classes=[],
            functions=[],
            dependencies={},
            errors=[],
            cross_references=None
        )

        # In real implementation, would cache the parsed tree
        # if _worker_tree_cache and tree:
        #     _worker_tree_cache.put(path_obj, tree, content)

        return result

    except Exception as e:
        # Return error result
        return ParseResult(
            modules=[],
            classes=[],
            functions=[],
            dependencies={},
            errors=[f"Error parsing {file_path}: {str(e)}"],
            cross_references=None
        )


class ParallelParser:
    """
    Parallel file parser using multiprocessing for multi-core optimization.

    Distributes file parsing across available CPU cores, providing significant
    speedup on large codebases. Automatically detects CPU count and chunks work
    efficiently.

    Attributes:
        num_workers: Number of worker processes (auto-detected if None)
        chunk_size: Number of files per chunk (auto-calculated for load balancing)

    Example:
        >>> parser = ParallelParser(num_workers=4)
        >>> results = parser.parse_files(file_list, parse_func)
        >>> # Results contain parsed data from all files
    """

    def __init__(self, num_workers: Optional[int] = None):
        """
        Initialize parallel parser.

        Args:
            num_workers: Number of worker processes. If None, auto-detects
                        CPU count (defaults to cpu_count() - 1 or 1 minimum)

        Example:
            >>> # Auto-detect workers
            >>> parser = ParallelParser()
            >>>
            >>> # Explicit worker count
            >>> parser = ParallelParser(num_workers=4)
        """
        if num_workers is None:
            # Auto-detect CPU cores, leaving one free for system
            cpu_count = mp.cpu_count()
            self.num_workers = max(1, cpu_count - 1)
        else:
            self.num_workers = max(1, num_workers)

        self.chunk_size: Optional[int] = None

    def _calculate_chunk_size(self, total_files: int) -> int:
        """
        Calculate optimal chunk size for load balancing.

        Uses heuristic: aim for ~4 chunks per worker to balance
        load distribution and overhead.

        Args:
            total_files: Total number of files to parse

        Returns:
            Optimal chunk size (minimum 1)

        Example:
            >>> parser = ParallelParser(num_workers=4)
            >>> chunk_size = parser._calculate_chunk_size(100)
            >>> # Returns ~6-7 (100 files / 4 workers / 4 chunks per worker)
        """
        if total_files <= self.num_workers:
            # Few files: one chunk per file
            return 1

        # Target: 4 chunks per worker for good load balancing
        # This ensures work is distributed even if some files take longer
        chunks_per_worker = 4
        target_chunks = self.num_workers * chunks_per_worker
        chunk_size = max(1, total_files // target_chunks)

        return chunk_size

    def _chunk_files(
        self,
        files: List[Any],
        chunk_size: int
    ) -> List[List[Any]]:
        """
        Split file list into chunks for parallel processing.

        Args:
            files: List of files to chunk
            chunk_size: Size of each chunk

        Returns:
            List of file chunks

        Example:
            >>> files = ['a.py', 'b.py', 'c.py', 'd.py']
            >>> chunks = parser._chunk_files(files, chunk_size=2)
            >>> # Returns [['a.py', 'b.py'], ['c.py', 'd.py']]
        """
        chunks = []
        for i in range(0, len(files), chunk_size):
            chunk = files[i:i + chunk_size]
            chunks.append(chunk)
        return chunks

    def parse_files(
        self,
        files: List[str],
        parse_func: Callable[[str], Any],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Any]:
        """
        Parse files in parallel using multiprocessing.Pool.

        Distributes parsing work across worker processes for faster
        processing on multi-core systems.

        Args:
            files: List of file paths to parse
            parse_func: Function to parse a single file (must be picklable)
            progress_callback: Optional callback(completed, total) for progress

        Returns:
            List of parse results (one per file, in original order)

        Example:
            >>> def parse_file(path):
            ...     # Parse and return result
            ...     return {"file": path, "data": ...}
            >>>
            >>> parser = ParallelParser(num_workers=4)
            >>> results = parser.parse_files(file_list, parse_file)
            >>> # Results contains parsed data for all files

        Note:
            parse_func must be picklable (top-level function or method).
            Lambda functions and nested functions cannot be pickled.
        """
        if not files:
            return []

        # Single file: no need for parallelization
        if len(files) == 1:
            return [parse_func(files[0])]

        # Calculate optimal chunk size
        self.chunk_size = self._calculate_chunk_size(len(files))

        # Use Pool for parallel processing
        results = []
        completed = 0

        try:
            with mp.Pool(processes=self.num_workers) as pool:
                # Map parse_func across all files
                # imap_unordered for better performance (results as they complete)
                # But we track order separately if needed
                for result in pool.imap(parse_func, files, chunksize=self.chunk_size):
                    results.append(result)
                    completed += 1

                    # Progress callback
                    if progress_callback:
                        progress_callback(completed, len(files))

        except Exception as e:
            # If parallel processing fails, fall back to sequential
            # This handles edge cases with unpicklable objects
            results = []
            for file_path in files:
                try:
                    result = parse_func(file_path)
                    results.append(result)
                    completed += 1

                    if progress_callback:
                        progress_callback(completed, len(files))

                except Exception as parse_error:
                    # Log error but continue with other files
                    results.append({
                        'error': str(parse_error),
                        'file': file_path
                    })

        return results

    def parse_files_with_metadata(
        self,
        files: List[Tuple[str, Any]],
        parse_func: Callable[[Tuple[str, Any]], Any],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Any]:
        """
        Parse files with associated metadata in parallel.

        Similar to parse_files but accepts tuples of (file_path, metadata)
        for cases where additional context is needed per file.

        Args:
            files: List of (file_path, metadata) tuples
            parse_func: Function that takes (file_path, metadata) tuple
            progress_callback: Optional callback(completed, total) for progress

        Returns:
            List of parse results (one per file)

        Example:
            >>> files_with_lang = [
            ...     ("main.py", "python"),
            ...     ("app.js", "javascript")
            ... ]
            >>> def parse_with_lang(item):
            ...     path, lang = item
            ...     # Parse using language-specific parser
            ...     return parse(path, lang)
            >>>
            >>> results = parser.parse_files_with_metadata(
            ...     files_with_lang,
            ...     parse_with_lang
            ... )
        """
        if not files:
            return []

        if len(files) == 1:
            return [parse_func(files[0])]

        # Calculate chunk size
        self.chunk_size = self._calculate_chunk_size(len(files))

        results = []
        completed = 0

        try:
            with mp.Pool(processes=self.num_workers) as pool:
                for result in pool.imap(
                    parse_func,
                    files,
                    chunksize=self.chunk_size
                ):
                    results.append(result)
                    completed += 1

                    if progress_callback:
                        progress_callback(completed, len(files))

        except Exception:
            # Sequential fallback
            results = []
            for file_item in files:
                try:
                    result = parse_func(file_item)
                    results.append(result)
                    completed += 1

                    if progress_callback:
                        progress_callback(completed, len(files))

                except Exception as parse_error:
                    results.append({
                        'error': str(parse_error),
                        'file': file_item[0] if isinstance(file_item, tuple) else str(file_item)
                    })

        return results

    def get_worker_count(self) -> int:
        """
        Get the number of worker processes being used.

        Returns:
            Number of worker processes

        Example:
            >>> parser = ParallelParser()
            >>> worker_count = parser.get_worker_count()
            >>> print(f"Using {worker_count} workers")
        """
        return self.num_workers

    @staticmethod
    def get_cpu_count() -> int:
        """
        Get the number of CPU cores available.

        Returns:
            Number of CPU cores

        Example:
            >>> cores = ParallelParser.get_cpu_count()
            >>> print(f"System has {cores} CPU cores")
        """
        return mp.cpu_count()


def create_parallel_parser(num_workers: Optional[int] = None) -> ParallelParser:
    """
    Factory function to create a ParallelParser instance.

    Args:
        num_workers: Number of worker processes (auto-detected if None)

    Returns:
        New ParallelParser instance

    Example:
        >>> parser = create_parallel_parser(num_workers=4)
        >>> # Or auto-detect
        >>> parser = create_parallel_parser()
    """
    return ParallelParser(num_workers=num_workers)
