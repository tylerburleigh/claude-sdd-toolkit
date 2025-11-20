"""Content filtering utilities for LLM documentation generation.

This module provides filters to exclude irrelevant files and reduce token usage
during codebase analysis.
"""

import os
import random
from enum import Enum
from pathlib import Path
from typing import Union, Optional, List, Dict, Callable
from collections import defaultdict


class FileSizeFilter:
    """Filter to skip files exceeding a size threshold.

    Large files are often generated code, minified assets, or bundled dependencies
    that don't provide useful documentation value but consume significant tokens.

    Args:
        max_size_bytes: Maximum file size in bytes. Files larger than this will be
            filtered out. Default is 500KB (500,000 bytes).

    Example:
        >>> filter = FileSizeFilter(max_size_bytes=100000)  # 100KB limit
        >>> filter.should_include("small_file.py")  # True if file < 100KB
        >>> filter.should_include("large_bundle.js")  # False if file > 100KB
    """

    def __init__(self, max_size_bytes: int = 500000):
        """Initialize the file size filter.

        Args:
            max_size_bytes: Maximum allowed file size in bytes (default: 500KB)
        """
        self.max_size_bytes = max_size_bytes

    def should_include(self, file_path: Union[str, Path]) -> bool:
        """Determine if a file should be included based on its size.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the file should be included (size <= threshold), False otherwise

        Raises:
            FileNotFoundError: If the file does not exist
            OSError: If there's an error accessing the file
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            # Directories and other non-file paths are excluded by default
            return False

        try:
            file_size = file_path.stat().st_size
            return file_size <= self.max_size_bytes
        except OSError as e:
            raise OSError(f"Error accessing file {file_path}: {e}")

    def get_file_size(self, file_path: Union[str, Path]) -> int:
        """Get the size of a file in bytes.

        Args:
            file_path: Path to the file

        Returns:
            File size in bytes

        Raises:
            FileNotFoundError: If the file does not exist
            OSError: If there's an error accessing the file
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            return 0

        try:
            return file_path.stat().st_size
        except OSError as e:
            raise OSError(f"Error accessing file {file_path}: {e}")


class FileCountLimiter:
    """Limiter to cap the number of files processed per directory.

    When directories contain many files, this filter prioritizes the most recently
    modified files up to a specified limit. This helps manage token usage when
    analyzing large directories.

    Args:
        max_files_per_dir: Maximum number of files to process per directory.
            Default is 100 files.

    Example:
        >>> limiter = FileCountLimiter(max_files_per_dir=50)
        >>> files = ["dir/file1.py", "dir/file2.py", ...]
        >>> included = limiter.filter_files(files)  # Returns up to 50 most recent
    """

    def __init__(self, max_files_per_dir: int = 100):
        """Initialize the file count limiter.

        Args:
            max_files_per_dir: Maximum number of files per directory (default: 100)
        """
        self.max_files_per_dir = max_files_per_dir
        self._directory_counts: Dict[str, int] = defaultdict(int)

    def filter_files(self, file_paths: List[Union[str, Path]]) -> List[Path]:
        """Filter a list of files, keeping only the most recent up to the limit per directory.

        Args:
            file_paths: List of file paths to filter

        Returns:
            Filtered list of file paths, prioritized by modification time within each directory

        Example:
            >>> limiter = FileCountLimiter(max_files_per_dir=2)
            >>> files = ["dir/old.py", "dir/new.py", "dir/newest.py"]
            >>> result = limiter.filter_files(files)
            >>> # Returns ["dir/newest.py", "dir/new.py"] (2 most recent)
        """
        # Group files by directory
        files_by_dir: Dict[str, List[Path]] = defaultdict(list)
        for file_path in file_paths:
            file_path = Path(file_path)
            if file_path.exists() and file_path.is_file():
                parent_dir = str(file_path.parent)
                files_by_dir[parent_dir].append(file_path)

        # Process each directory
        result = []
        for directory, files in files_by_dir.items():
            # Sort by modification time (most recent first)
            try:
                sorted_files = sorted(
                    files,
                    key=lambda f: f.stat().st_mtime,
                    reverse=True
                )
            except OSError:
                # If we can't stat some files, just use the unsorted list
                sorted_files = files

            # Take only up to max_files_per_dir
            selected_files = sorted_files[:self.max_files_per_dir]
            result.extend(selected_files)
            self._directory_counts[directory] = len(selected_files)

        return result

    def should_include(self, file_path: Union[str, Path], files_in_dir: Optional[List[Union[str, Path]]] = None) -> bool:
        """Determine if a file should be included based on directory file count.

        This method is useful when processing files one at a time. For batch processing,
        use filter_files() instead.

        Args:
            file_path: Path to the file to check
            files_in_dir: Optional list of all files in the same directory. If provided,
                the decision will be based on modification time ranking. If not provided,
                only the running count is checked.

        Returns:
            True if the file should be included, False otherwise
        """
        file_path = Path(file_path)
        if not file_path.exists() or not file_path.is_file():
            return False

        parent_dir = str(file_path.parent)

        # If we have the full directory listing, use filter_files for accurate ranking
        if files_in_dir is not None:
            filtered = self.filter_files(files_in_dir)
            return file_path in filtered

        # Otherwise, use running count (less accurate but works for streaming)
        if self._directory_counts[parent_dir] >= self.max_files_per_dir:
            return False

        self._directory_counts[parent_dir] += 1
        return True

    def reset(self):
        """Reset the directory counts.

        Useful when processing multiple batches or when you want to start fresh.
        """
        self._directory_counts.clear()

    def get_directory_stats(self) -> Dict[str, int]:
        """Get statistics about how many files were processed per directory.

        Returns:
            Dictionary mapping directory paths to file counts
        """
        return dict(self._directory_counts)


class SamplingStrategy:
    """Sampling strategy for very large projects (10K+ files).

    For massive codebases, processing every file may be impractical. This class
    implements intelligent sampling to select a representative subset based on:
    - Recency (modification time)
    - Depth (directory depth in the tree)
    - Importance (customizable scoring function)

    Args:
        sample_rate: Fraction of files to include (0.0 to 1.0). Default is 0.1 (10%).
        seed: Random seed for reproducible sampling. If None, sampling is non-deterministic.
        importance_scorer: Optional function that takes a file path and returns an
            importance score (higher = more important). If provided, files are
            weighted by importance in addition to recency and depth.

    Example:
        >>> strategy = SamplingStrategy(sample_rate=0.1)
        >>> files = ["src/a.py", "src/b.py", ...]  # 10,000 files
        >>> sampled = strategy.sample_files(files)  # Returns ~1,000 files
    """

    def __init__(
        self,
        sample_rate: float = 0.1,
        seed: Optional[int] = None,
        importance_scorer: Optional[Callable[[Path], float]] = None
    ):
        """Initialize the sampling strategy.

        Args:
            sample_rate: Fraction of files to sample (default: 0.1 for 10%)
            seed: Random seed for reproducible sampling (default: None)
            importance_scorer: Optional function to score file importance
        """
        if not 0.0 <= sample_rate <= 1.0:
            raise ValueError(f"sample_rate must be between 0.0 and 1.0, got {sample_rate}")

        self.sample_rate = sample_rate
        self.seed = seed
        self.importance_scorer = importance_scorer

        if seed is not None:
            random.seed(seed)

    def sample_files(self, file_paths: List[Union[str, Path]]) -> List[Path]:
        """Sample a representative subset of files from a large collection.

        The sampling strategy combines:
        1. Recency: Files modified more recently are prioritized
        2. Depth: Files at different directory depths are represented
        3. Importance: Optional custom scoring for domain-specific importance

        Args:
            file_paths: List of file paths to sample from

        Returns:
            Sampled subset of file paths

        Example:
            >>> strategy = SamplingStrategy(sample_rate=0.2)
            >>> all_files = list_all_files()  # 10,000 files
            >>> sample = strategy.sample_files(all_files)  # ~2,000 files
        """
        # Convert to Path objects and filter valid files
        valid_files = []
        for file_path in file_paths:
            file_path = Path(file_path)
            if file_path.exists() and file_path.is_file():
                valid_files.append(file_path)

        if not valid_files:
            return []

        # Calculate target sample size
        target_size = max(1, int(len(valid_files) * self.sample_rate))

        # If sample rate would include everything, return all files
        if target_size >= len(valid_files):
            return valid_files

        # Score each file based on multiple criteria
        scored_files = []
        for file_path in valid_files:
            score = self._calculate_file_score(file_path)
            scored_files.append((file_path, score))

        # Sort by score (highest first) and take top N
        scored_files.sort(key=lambda x: x[1], reverse=True)
        sampled = [f[0] for f in scored_files[:target_size]]

        # Add some randomness to ensure variety across runs (if no seed)
        if self.seed is None and len(sampled) > 1:
            random.shuffle(sampled)

        return sampled

    def _calculate_file_score(self, file_path: Path) -> float:
        """Calculate a composite score for file importance.

        Args:
            file_path: Path to score

        Returns:
            Composite score combining recency, depth, and custom importance
        """
        score = 0.0

        # Recency score (40% weight)
        try:
            mtime = file_path.stat().st_mtime
            # Normalize to 0-1 range (recent = higher score)
            # Use a simple heuristic: files modified in last 30 days get higher scores
            recency_score = min(1.0, mtime / (2**31))  # Normalize timestamp
            score += recency_score * 0.4
        except OSError:
            pass

        # Depth score (30% weight)
        # Files at moderate depth (2-4 levels) are often more important than
        # very shallow (root) or very deep (nested) files
        depth = len(file_path.parts) - 1
        if 2 <= depth <= 4:
            depth_score = 1.0
        elif depth < 2:
            depth_score = 0.5
        else:
            depth_score = max(0.0, 1.0 - (depth - 4) * 0.1)
        score += depth_score * 0.3

        # Custom importance score (30% weight)
        if self.importance_scorer is not None:
            try:
                importance = self.importance_scorer(file_path)
                score += importance * 0.3
            except Exception:
                # If custom scorer fails, just skip this component
                pass

        return score

    def estimate_sample_size(self, total_files: int) -> int:
        """Estimate how many files would be sampled from a given total.

        Args:
            total_files: Total number of files available

        Returns:
            Estimated number of files that would be sampled

        Example:
            >>> strategy = SamplingStrategy(sample_rate=0.1)
            >>> strategy.estimate_sample_size(10000)
            1000
        """
        return max(1, int(total_files * self.sample_rate))

    def should_sample(self, current_count: int, total_count: int) -> bool:
        """Determine if the current file should be included based on position.

        This is useful for streaming scenarios where you're processing files
        one at a time and want to sample without loading everything into memory.

        Args:
            current_count: Current file index (0-based)
            total_count: Total number of files

        Returns:
            True if this file should be included in the sample

        Example:
            >>> strategy = SamplingStrategy(sample_rate=0.1)
            >>> for i in range(10000):
            ...     if strategy.should_sample(i, 10000):
            ...         process_file(files[i])
        """
        if total_count == 0:
            return False

        # Simple deterministic sampling based on position
        target_size = self.estimate_sample_size(total_count)
        interval = total_count / target_size if target_size > 0 else float('inf')

        return (current_count % int(interval)) == 0 if interval >= 1 else True


class ContentFilter:
    """Composite filter for content filtering.

    Combines multiple filtering strategies (size, patterns, etc.) to determine
    which files should be processed during documentation generation.

    Args:
        size_filter: Optional FileSizeFilter to apply

    Example:
        >>> filter = ContentFilter(size_filter=FileSizeFilter(max_size_bytes=100000))
        >>> filter.should_process("src/main.py")  # True if passes all filters
    """

    def __init__(self, size_filter: Optional[FileSizeFilter] = None):
        """Initialize the composite filter.

        Args:
            size_filter: Optional FileSizeFilter instance. If None, no size filtering
                is applied.
        """
        self.size_filter = size_filter

    def should_process(self, file_path: Union[str, Path]) -> bool:
        """Determine if a file should be processed.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the file should be processed, False otherwise
        """
        file_path = Path(file_path)

        # Check if file exists
        if not file_path.exists() or not file_path.is_file():
            return False

        # Apply size filter if configured
        if self.size_filter is not None:
            try:
                if not self.size_filter.should_include(file_path):
                    return False
            except (FileNotFoundError, OSError):
                # If we can't access the file, exclude it
                return False

        return True


def should_process_file(
    file_path: Union[str, Path],
    max_size_bytes: Optional[int] = None
) -> bool:
    """Convenience function to check if a file should be processed.

    Args:
        file_path: Path to the file to check
        max_size_bytes: Optional maximum file size in bytes. If provided, files
            larger than this will be excluded.

    Returns:
        True if the file should be processed, False otherwise

    Example:
        >>> should_process_file("src/main.py", max_size_bytes=500000)
        True
        >>> should_process_file("dist/bundle.js", max_size_bytes=500000)
        False  # If bundle.js > 500KB
    """
    size_filter = FileSizeFilter(max_size_bytes) if max_size_bytes else None
    content_filter = ContentFilter(size_filter=size_filter)
    return content_filter.should_process(file_path)


class FilterProfile(Enum):
    """Predefined filter profiles for different use cases.

    Each profile represents a different balance between speed and completeness:
    - FAST: Aggressive filtering for quick analysis of large codebases
    - BALANCED: Moderate filtering for typical projects (default)
    - COMPLETE: Minimal filtering for comprehensive documentation

    Example:
        >>> filters = create_filter_chain(FilterProfile.FAST)
        >>> filters = create_filter_chain(FilterProfile.BALANCED)
        >>> filters = create_filter_chain(FilterProfile.COMPLETE)
    """

    FAST = "fast"
    BALANCED = "balanced"
    COMPLETE = "complete"


def create_filter_chain(
    profile: FilterProfile = FilterProfile.BALANCED,
    custom_size_limit: Optional[int] = None,
    custom_file_limit: Optional[int] = None,
    custom_sample_rate: Optional[float] = None,
) -> Dict[str, Union[FileSizeFilter, FileCountLimiter, SamplingStrategy, None]]:
    """Factory function to create a filter chain based on a profile.

    This function creates a consistent set of filters optimized for different
    use cases. You can override specific parameters while maintaining the
    overall profile characteristics.

    Args:
        profile: The filter profile to use (FAST, BALANCED, or COMPLETE)
        custom_size_limit: Override the profile's file size limit (bytes)
        custom_file_limit: Override the profile's file count limit per directory
        custom_sample_rate: Override the profile's sampling rate (0.0 to 1.0)

    Returns:
        Dictionary containing configured filter instances:
        - 'size_filter': FileSizeFilter instance or None
        - 'count_limiter': FileCountLimiter instance or None
        - 'sampling': SamplingStrategy instance or None

    Example:
        >>> # Use FAST profile for quick analysis
        >>> filters = create_filter_chain(FilterProfile.FAST)
        >>> size_filter = filters['size_filter']
        >>> count_limiter = filters['count_limiter']
        >>> sampling = filters['sampling']
        >>>
        >>> # Customize BALANCED profile
        >>> filters = create_filter_chain(
        ...     FilterProfile.BALANCED,
        ...     custom_size_limit=1_000_000  # 1MB instead of default
        ... )
    """
    # Define profile configurations
    profiles = {
        FilterProfile.FAST: {
            'size_limit': 200_000,      # 200KB - skip large files aggressively
            'file_limit': 50,            # 50 files per directory
            'sample_rate': 0.2,          # Sample 20% of files
        },
        FilterProfile.BALANCED: {
            'size_limit': 500_000,      # 500KB - default reasonable limit
            'file_limit': 100,           # 100 files per directory
            'sample_rate': None,         # No sampling for typical projects
        },
        FilterProfile.COMPLETE: {
            'size_limit': 2_000_000,    # 2MB - very permissive
            'file_limit': 500,           # 500 files per directory
            'sample_rate': None,         # No sampling
        },
    }

    # Get configuration for selected profile
    config = profiles[profile]

    # Apply custom overrides
    size_limit = custom_size_limit if custom_size_limit is not None else config['size_limit']
    file_limit = custom_file_limit if custom_file_limit is not None else config['file_limit']
    sample_rate = custom_sample_rate if custom_sample_rate is not None else config['sample_rate']

    # Create filter instances
    size_filter = FileSizeFilter(max_size_bytes=size_limit) if size_limit else None
    count_limiter = FileCountLimiter(max_files_per_dir=file_limit) if file_limit else None
    sampling = SamplingStrategy(sample_rate=sample_rate) if sample_rate else None

    return {
        'size_filter': size_filter,
        'count_limiter': count_limiter,
        'sampling': sampling,
    }
