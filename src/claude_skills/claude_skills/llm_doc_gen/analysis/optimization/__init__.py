"""Optimization components for LLM documentation generation.

This package provides optimization utilities to improve performance and reduce
token usage during codebase analysis and documentation generation:

- filters: Content filtering to exclude irrelevant files/patterns
- parallel: Parallel processing for file analysis
- streaming: Streaming/chunked processing for large codebases
- cache: Caching mechanisms for AST parsing and analysis results
"""

from .filters import ContentFilter, should_process_file, FileSizeFilter, FileCountLimiter
from .parallel import ParallelProcessor, process_files_parallel
from .streaming import StreamingProcessor, process_in_chunks
from .cache import CacheManager, get_cached_result, set_cached_result

__all__ = [
    # Filters
    "ContentFilter",
    "should_process_file",
    "FileSizeFilter",
    "FileCountLimiter",
    # Parallel processing
    "ParallelProcessor",
    "process_files_parallel",
    # Streaming
    "StreamingProcessor",
    "process_in_chunks",
    # Cache
    "CacheManager",
    "get_cached_result",
    "set_cached_result",
]
