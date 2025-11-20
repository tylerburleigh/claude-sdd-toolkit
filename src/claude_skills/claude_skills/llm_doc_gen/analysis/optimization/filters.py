"""Content filtering utilities for LLM documentation generation.

This module provides filters to exclude irrelevant files and reduce token usage
during codebase analysis.
"""

import os
from pathlib import Path
from typing import Union, Optional, List, Dict
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
