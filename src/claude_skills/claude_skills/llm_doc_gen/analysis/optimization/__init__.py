"""Optimization components for LLM documentation generation.

This package provides optimization utilities to improve performance and reduce
token usage during codebase analysis and documentation generation:

- filters: Content filtering to exclude irrelevant files/patterns
- parallel: Parallel processing for file analysis (planned)
- streaming: Streaming/chunked processing for large codebases (planned)
- cache: Caching mechanisms for AST parsing and analysis results (planned)
"""

from .filters import (
    ContentFilter,
    should_process_file,
    FileSizeFilter,
    FileCountLimiter,
    SamplingStrategy,
    FilterProfile,
    create_filter_chain,
)

__all__ = [
    # Filters
    "ContentFilter",
    "should_process_file",
    "FileSizeFilter",
    "FileCountLimiter",
    "SamplingStrategy",
    "FilterProfile",
    "create_filter_chain",
    # Parallel processing (planned)
    # "ParallelProcessor",
    # "process_files_parallel",
    # Streaming (planned)
    # "StreamingProcessor",
    # "process_in_chunks",
    # Cache (planned)
    # "CacheManager",
    # "get_cached_result",
    # "set_cached_result",
]
