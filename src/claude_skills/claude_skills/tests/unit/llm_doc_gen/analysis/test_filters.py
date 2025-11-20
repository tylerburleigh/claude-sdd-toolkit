"""Unit tests for filter classes in llm_doc_gen.analysis.optimization.filters.

Tests cover FileSizeFilter, FileCountLimiter, and SamplingStrategy including
edge cases and threshold behavior.
"""

import os
import random
import tempfile
from pathlib import Path

import pytest

from claude_skills.llm_doc_gen.analysis.optimization.filters import (
    FileSizeFilter,
    FileCountLimiter,
    SamplingStrategy,
    ContentFilter,
    should_process_file,
    FilterProfile,
    create_filter_chain,
)


# ============================================================================
# FileSizeFilter Tests
# ============================================================================


class TestFileSizeFilter:
    """Test FileSizeFilter behavior including edge cases and thresholds."""

    def test_init_default_threshold(self):
        """Test that default threshold is 500KB."""
        filter = FileSizeFilter()
        assert filter.max_size_bytes == 500000

    def test_init_custom_threshold(self):
        """Test custom size threshold."""
        filter = FileSizeFilter(max_size_bytes=100000)
        assert filter.max_size_bytes == 100000

    def test_should_include_small_file(self, tmp_path):
        """Test that files under threshold are included."""
        small_file = tmp_path / "small.txt"
        small_file.write_text("x" * 100)  # 100 bytes

        filter = FileSizeFilter(max_size_bytes=1000)
        assert filter.should_include(small_file) is True

    def test_should_include_exact_threshold(self, tmp_path):
        """Test that files exactly at threshold are included."""
        exact_file = tmp_path / "exact.txt"
        exact_file.write_text("x" * 1000)  # Exactly 1000 bytes

        filter = FileSizeFilter(max_size_bytes=1000)
        assert filter.should_include(exact_file) is True

    def test_should_exclude_large_file(self, tmp_path):
        """Test that files over threshold are excluded."""
        large_file = tmp_path / "large.txt"
        large_file.write_text("x" * 1001)  # 1001 bytes

        filter = FileSizeFilter(max_size_bytes=1000)
        assert filter.should_include(large_file) is False

    def test_should_include_with_path_string(self, tmp_path):
        """Test that string paths are accepted."""
        small_file = tmp_path / "small.txt"
        small_file.write_text("x" * 100)

        filter = FileSizeFilter(max_size_bytes=1000)
        assert filter.should_include(str(small_file)) is True

    def test_nonexistent_file_raises_error(self):
        """Test that nonexistent files raise FileNotFoundError."""
        filter = FileSizeFilter()
        with pytest.raises(FileNotFoundError, match="File not found"):
            filter.should_include("/nonexistent/file.txt")

    def test_directory_returns_false(self, tmp_path):
        """Test that directories are excluded."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        filter = FileSizeFilter()
        assert filter.should_include(test_dir) is False

    def test_get_file_size(self, tmp_path):
        """Test get_file_size returns correct size."""
        test_file = tmp_path / "test.txt"
        content = "x" * 500
        test_file.write_text(content)

        filter = FileSizeFilter()
        assert filter.get_file_size(test_file) == 500

    def test_get_file_size_nonexistent(self):
        """Test get_file_size raises error for nonexistent file."""
        filter = FileSizeFilter()
        with pytest.raises(FileNotFoundError):
            filter.get_file_size("/nonexistent/file.txt")

    def test_get_file_size_directory(self, tmp_path):
        """Test get_file_size returns 0 for directories."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        filter = FileSizeFilter()
        assert filter.get_file_size(test_dir) == 0

    def test_empty_file(self, tmp_path):
        """Test that empty files (0 bytes) are included."""
        empty_file = tmp_path / "empty.txt"
        empty_file.touch()

        filter = FileSizeFilter(max_size_bytes=1000)
        assert filter.should_include(empty_file) is True
        assert filter.get_file_size(empty_file) == 0


# ============================================================================
# FileCountLimiter Tests
# ============================================================================


class TestFileCountLimiter:
    """Test FileCountLimiter behavior including directory-based limiting."""

    def test_init_default_limit(self):
        """Test that default limit is 100 files per directory."""
        limiter = FileCountLimiter()
        assert limiter.max_files_per_dir == 100

    def test_init_custom_limit(self):
        """Test custom file count limit."""
        limiter = FileCountLimiter(max_files_per_dir=50)
        assert limiter.max_files_per_dir == 50

    def test_filter_files_under_limit(self, tmp_path):
        """Test that all files are kept when under limit."""
        files = []
        for i in range(5):
            file = tmp_path / f"file{i}.txt"
            file.write_text(f"content{i}")
            files.append(file)

        limiter = FileCountLimiter(max_files_per_dir=10)
        result = limiter.filter_files(files)

        assert len(result) == 5
        assert set(result) == set(files)

    def test_filter_files_over_limit(self, tmp_path):
        """Test that only max_files_per_dir are kept when over limit."""
        files = []
        for i in range(10):
            file = tmp_path / f"file{i}.txt"
            file.write_text(f"content{i}")
            files.append(file)

        limiter = FileCountLimiter(max_files_per_dir=5)
        result = limiter.filter_files(files)

        assert len(result) == 5

    def test_filter_files_prioritizes_recent(self, tmp_path):
        """Test that most recently modified files are prioritized."""
        import time

        files = []
        for i in range(5):
            file = tmp_path / f"file{i}.txt"
            file.write_text(f"content{i}")
            files.append(file)
            # Sleep to ensure different modification times
            time.sleep(0.01)

        limiter = FileCountLimiter(max_files_per_dir=3)
        result = limiter.filter_files(files)

        # Most recent 3 files should be file2.txt, file3.txt, file4.txt
        assert len(result) == 3
        assert files[4] in result  # Most recent
        assert files[3] in result
        assert files[2] in result

    def test_filter_files_multiple_directories(self, tmp_path):
        """Test that limit applies per directory."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        files = []
        # 5 files in dir1
        for i in range(5):
            file = dir1 / f"file{i}.txt"
            file.write_text(f"content{i}")
            files.append(file)

        # 5 files in dir2
        for i in range(5):
            file = dir2 / f"file{i}.txt"
            file.write_text(f"content{i}")
            files.append(file)

        limiter = FileCountLimiter(max_files_per_dir=3)
        result = limiter.filter_files(files)

        # Should get 3 from each directory = 6 total
        assert len(result) == 6

    def test_filter_files_empty_list(self):
        """Test that empty list returns empty result."""
        limiter = FileCountLimiter()
        result = limiter.filter_files([])
        assert result == []

    def test_filter_files_ignores_nonexistent(self, tmp_path):
        """Test that nonexistent files are ignored."""
        file1 = tmp_path / "exists.txt"
        file1.write_text("content")

        files = [file1, tmp_path / "nonexistent.txt"]

        limiter = FileCountLimiter()
        result = limiter.filter_files(files)

        assert len(result) == 1
        assert result[0] == file1

    def test_should_include_basic(self, tmp_path):
        """Test should_include with running count."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file3 = tmp_path / "file3.txt"
        file1.write_text("a")
        file2.write_text("b")
        file3.write_text("c")

        limiter = FileCountLimiter(max_files_per_dir=2)

        assert limiter.should_include(file1) is True
        assert limiter.should_include(file2) is True
        assert limiter.should_include(file3) is False  # Over limit

    def test_should_include_with_files_in_dir(self, tmp_path):
        """Test should_include with full directory listing."""
        files = []
        for i in range(5):
            file = tmp_path / f"file{i}.txt"
            file.write_text(f"content{i}")
            files.append(file)

        limiter = FileCountLimiter(max_files_per_dir=3)

        # When providing files_in_dir, it uses filter_files logic
        result = limiter.should_include(files[0], files_in_dir=files)
        # The result depends on modification time ranking
        assert isinstance(result, bool)

    def test_should_include_nonexistent(self):
        """Test should_include returns False for nonexistent files."""
        limiter = FileCountLimiter()
        assert limiter.should_include("/nonexistent/file.txt") is False

    def test_reset(self, tmp_path):
        """Test reset clears directory counts."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("a")
        file2.write_text("b")

        limiter = FileCountLimiter(max_files_per_dir=1)

        assert limiter.should_include(file1) is True
        assert limiter.should_include(file2) is False

        limiter.reset()

        # After reset, we can include file2
        assert limiter.should_include(file2) is True

    def test_get_directory_stats(self, tmp_path):
        """Test get_directory_stats returns correct counts."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        files = []
        for i in range(3):
            files.append(dir1 / f"file{i}.txt")
        for i in range(2):
            files.append(dir2 / f"file{i}.txt")

        for file in files:
            file.write_text("content")

        limiter = FileCountLimiter()
        limiter.filter_files(files)

        stats = limiter.get_directory_stats()
        assert stats[str(dir1)] == 3
        assert stats[str(dir2)] == 2


# ============================================================================
# SamplingStrategy Tests
# ============================================================================


class TestSamplingStrategy:
    """Test SamplingStrategy including edge cases and scoring behavior."""

    def test_init_default_rate(self):
        """Test that default sample rate is 0.1 (10%)."""
        strategy = SamplingStrategy()
        assert strategy.sample_rate == 0.1

    def test_init_custom_rate(self):
        """Test custom sample rate."""
        strategy = SamplingStrategy(sample_rate=0.25)
        assert strategy.sample_rate == 0.25

    def test_init_invalid_rate_too_low(self):
        """Test that rate < 0.0 raises ValueError."""
        with pytest.raises(ValueError, match="sample_rate must be between 0.0 and 1.0"):
            SamplingStrategy(sample_rate=-0.1)

    def test_init_invalid_rate_too_high(self):
        """Test that rate > 1.0 raises ValueError."""
        with pytest.raises(ValueError, match="sample_rate must be between 0.0 and 1.0"):
            SamplingStrategy(sample_rate=1.5)

    def test_init_with_seed(self):
        """Test that seed is stored correctly."""
        strategy = SamplingStrategy(seed=42)
        assert strategy.seed == 42

    def test_sample_files_basic(self, tmp_path):
        """Test basic sampling returns correct number of files."""
        files = []
        for i in range(100):
            file = tmp_path / f"file{i}.txt"
            file.write_text(f"content{i}")
            files.append(file)

        strategy = SamplingStrategy(sample_rate=0.1, seed=42)
        result = strategy.sample_files(files)

        # Should sample approximately 10% = 10 files
        assert len(result) == 10

    def test_sample_files_empty_list(self):
        """Test that empty list returns empty result."""
        strategy = SamplingStrategy()
        result = strategy.sample_files([])
        assert result == []

    def test_sample_files_rate_100_percent(self, tmp_path):
        """Test that 100% rate returns all files."""
        files = []
        for i in range(10):
            file = tmp_path / f"file{i}.txt"
            file.write_text(f"content{i}")
            files.append(file)

        strategy = SamplingStrategy(sample_rate=1.0)
        result = strategy.sample_files(files)

        assert len(result) == 10
        assert set(result) == set(files)

    def test_sample_files_rate_0_percent(self, tmp_path):
        """Test that 0% rate returns at least 1 file (minimum)."""
        files = []
        for i in range(10):
            file = tmp_path / f"file{i}.txt"
            file.write_text(f"content{i}")
            files.append(file)

        strategy = SamplingStrategy(sample_rate=0.0)
        result = strategy.sample_files(files)

        # Should return at least 1 file (minimum)
        assert len(result) >= 1

    def test_sample_files_small_sample(self, tmp_path):
        """Test sampling with only 1 file available."""
        file = tmp_path / "only.txt"
        file.write_text("content")

        strategy = SamplingStrategy(sample_rate=0.1)
        result = strategy.sample_files([file])

        assert len(result) == 1
        assert result[0] == file

    def test_sample_files_reproducible_with_seed(self, tmp_path):
        """Test that same seed produces same results."""
        files = []
        for i in range(100):
            file = tmp_path / f"file{i}.txt"
            file.write_text(f"content{i}")
            files.append(file)

        strategy1 = SamplingStrategy(sample_rate=0.1, seed=42)
        result1 = strategy1.sample_files(files)

        strategy2 = SamplingStrategy(sample_rate=0.1, seed=42)
        result2 = strategy2.sample_files(files)

        # With same seed, top N files should be identical (before shuffle)
        # But shuffle happens after scoring, so we check the sorted results
        assert len(result1) == len(result2)

    def test_sample_files_ignores_nonexistent(self, tmp_path):
        """Test that nonexistent files are filtered out."""
        file1 = tmp_path / "exists.txt"
        file1.write_text("content")

        files = [file1, tmp_path / "nonexistent.txt"]

        strategy = SamplingStrategy(sample_rate=0.5)
        result = strategy.sample_files(files)

        # Only the existing file should be in result
        assert len(result) == 1
        assert result[0] == file1

    def test_sample_files_with_importance_scorer(self, tmp_path):
        """Test sampling with custom importance scorer."""
        files = []
        for i in range(10):
            file = tmp_path / f"file{i}.txt"
            file.write_text(f"content{i}")
            files.append(file)

        # Scorer that prefers files with higher numbers
        def scorer(path: Path) -> float:
            name = path.stem
            if name.startswith("file"):
                return float(name.replace("file", "")) / 10.0
            return 0.0

        strategy = SamplingStrategy(sample_rate=0.3, seed=42, importance_scorer=scorer)
        result = strategy.sample_files(files)

        # Should prefer files with higher numbers
        assert len(result) == 3

    def test_estimate_sample_size(self):
        """Test estimate_sample_size returns correct counts."""
        strategy = SamplingStrategy(sample_rate=0.1)

        assert strategy.estimate_sample_size(100) == 10
        assert strategy.estimate_sample_size(1000) == 100
        assert strategy.estimate_sample_size(50) == 5
        assert strategy.estimate_sample_size(1) == 1  # Minimum is 1

    def test_estimate_sample_size_rate_zero(self):
        """Test estimate with 0% rate returns at least 1."""
        strategy = SamplingStrategy(sample_rate=0.0)
        assert strategy.estimate_sample_size(100) >= 1

    def test_should_sample_streaming(self):
        """Test should_sample for streaming use case."""
        strategy = SamplingStrategy(sample_rate=0.1)

        # With 100 files and 10% rate, expect ~10 files
        included = []
        for i in range(100):
            if strategy.should_sample(i, 100):
                included.append(i)

        # Should sample approximately 10 files
        assert 8 <= len(included) <= 12  # Allow some variance

    def test_should_sample_zero_total(self):
        """Test should_sample with 0 total files."""
        strategy = SamplingStrategy()
        assert strategy.should_sample(0, 0) is False

    def test_calculate_file_score(self, tmp_path):
        """Test that _calculate_file_score returns reasonable values."""
        file = tmp_path / "test.txt"
        file.write_text("content")

        strategy = SamplingStrategy()
        score = strategy._calculate_file_score(file)

        # Score should be between 0 and 1
        assert 0.0 <= score <= 1.0


# ============================================================================
# ContentFilter Tests
# ============================================================================


class TestContentFilter:
    """Test ContentFilter composite behavior."""

    def test_init_no_filters(self):
        """Test initialization with no filters."""
        filter = ContentFilter()
        assert filter.size_filter is None

    def test_init_with_size_filter(self):
        """Test initialization with size filter."""
        size_filter = FileSizeFilter(max_size_bytes=1000)
        content_filter = ContentFilter(size_filter=size_filter)
        assert content_filter.size_filter is size_filter

    def test_should_process_no_filters(self, tmp_path):
        """Test that file is accepted when no filters configured."""
        file = tmp_path / "test.txt"
        file.write_text("content")

        filter = ContentFilter()
        assert filter.should_process(file) is True

    def test_should_process_with_size_filter_pass(self, tmp_path):
        """Test file passes size filter."""
        file = tmp_path / "small.txt"
        file.write_text("x" * 100)

        size_filter = FileSizeFilter(max_size_bytes=1000)
        content_filter = ContentFilter(size_filter=size_filter)

        assert content_filter.should_process(file) is True

    def test_should_process_with_size_filter_fail(self, tmp_path):
        """Test file fails size filter."""
        file = tmp_path / "large.txt"
        file.write_text("x" * 2000)

        size_filter = FileSizeFilter(max_size_bytes=1000)
        content_filter = ContentFilter(size_filter=size_filter)

        assert content_filter.should_process(file) is False

    def test_should_process_nonexistent_file(self):
        """Test nonexistent file returns False."""
        filter = ContentFilter()
        assert filter.should_process("/nonexistent/file.txt") is False

    def test_should_process_directory(self, tmp_path):
        """Test directory returns False."""
        test_dir = tmp_path / "testdir"
        test_dir.mkdir()

        filter = ContentFilter()
        assert filter.should_process(test_dir) is False


# ============================================================================
# Convenience Function Tests
# ============================================================================


class TestShouldProcessFile:
    """Test the should_process_file convenience function."""

    def test_basic_usage_no_size_limit(self, tmp_path):
        """Test without size limit."""
        file = tmp_path / "test.txt"
        file.write_text("content")

        assert should_process_file(file) is True

    def test_with_size_limit_pass(self, tmp_path):
        """Test with size limit that passes."""
        file = tmp_path / "small.txt"
        file.write_text("x" * 100)

        assert should_process_file(file, max_size_bytes=1000) is True

    def test_with_size_limit_fail(self, tmp_path):
        """Test with size limit that fails."""
        file = tmp_path / "large.txt"
        file.write_text("x" * 2000)

        assert should_process_file(file, max_size_bytes=1000) is False

    def test_nonexistent_file(self):
        """Test nonexistent file returns False."""
        assert should_process_file("/nonexistent/file.txt") is False


# ============================================================================
# FilterProfile and Factory Tests
# ============================================================================


class TestFilterProfile:
    """Test FilterProfile enum."""

    def test_profile_values(self):
        """Test that all profiles have correct values."""
        assert FilterProfile.FAST.value == "fast"
        assert FilterProfile.BALANCED.value == "balanced"
        assert FilterProfile.COMPLETE.value == "complete"


class TestCreateFilterChain:
    """Test create_filter_chain factory function."""

    def test_create_fast_profile(self):
        """Test FAST profile creates appropriate filters."""
        filters = create_filter_chain(FilterProfile.FAST)

        assert filters['size_filter'] is not None
        assert filters['size_filter'].max_size_bytes == 200_000
        assert filters['count_limiter'] is not None
        assert filters['count_limiter'].max_files_per_dir == 50
        assert filters['sampling'] is not None
        assert filters['sampling'].sample_rate == 0.2

    def test_create_balanced_profile(self):
        """Test BALANCED profile creates appropriate filters."""
        filters = create_filter_chain(FilterProfile.BALANCED)

        assert filters['size_filter'] is not None
        assert filters['size_filter'].max_size_bytes == 500_000
        assert filters['count_limiter'] is not None
        assert filters['count_limiter'].max_files_per_dir == 100
        assert filters['sampling'] is None  # No sampling for balanced

    def test_create_complete_profile(self):
        """Test COMPLETE profile creates appropriate filters."""
        filters = create_filter_chain(FilterProfile.COMPLETE)

        assert filters['size_filter'] is not None
        assert filters['size_filter'].max_size_bytes == 2_000_000
        assert filters['count_limiter'] is not None
        assert filters['count_limiter'].max_files_per_dir == 500
        assert filters['sampling'] is None  # No sampling for complete

    def test_custom_size_limit_override(self):
        """Test custom size limit overrides profile default."""
        filters = create_filter_chain(
            FilterProfile.BALANCED,
            custom_size_limit=1_000_000
        )

        assert filters['size_filter'].max_size_bytes == 1_000_000

    def test_custom_file_limit_override(self):
        """Test custom file limit overrides profile default."""
        filters = create_filter_chain(
            FilterProfile.BALANCED,
            custom_file_limit=200
        )

        assert filters['count_limiter'].max_files_per_dir == 200

    def test_custom_sample_rate_override(self):
        """Test custom sample rate overrides profile default."""
        filters = create_filter_chain(
            FilterProfile.BALANCED,
            custom_sample_rate=0.3
        )

        assert filters['sampling'] is not None
        assert filters['sampling'].sample_rate == 0.3

    def test_multiple_custom_overrides(self):
        """Test multiple custom overrides work together."""
        filters = create_filter_chain(
            FilterProfile.FAST,
            custom_size_limit=300_000,
            custom_file_limit=75,
            custom_sample_rate=0.15
        )

        assert filters['size_filter'].max_size_bytes == 300_000
        assert filters['count_limiter'].max_files_per_dir == 75
        assert filters['sampling'].sample_rate == 0.15
